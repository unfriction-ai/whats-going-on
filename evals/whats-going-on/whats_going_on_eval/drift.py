"""README ↔ fixtures ↔ SKILL contract equality checks."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from pathlib import Path

import yaml

from .chain import ChainMode
from .fixtures import (
    REQUIRED_FAMILIES,
    Expectation,
    Fixture,
    Tripwires,
    Turn,
    _gold_response_text,
    challenge_matches,
    covered_families,
    smart_matches,
    worksheet_matches,
)
from .challenge import (
    Answered,
    Finding,
    Open,
    render_line,
    restated_line,
    ungrounded_findings,
)
from .grade import _restatement_fails, grade_gold, grade_turn, rubric_keys_match_doc
from .manifest import (
    RESTATEMENT_CASES_DIR,
    SKILL_DIR,
    assert_chain_ok,
    assert_skill_tree_clean,
)
from .principles import load_principles, principle_names
from .smart import load_cards, parse_cards
from .worksheet import AREAS, QUESTION_SLOT, load_registry
from .parse import (
    CONFIDENCES,
    DIRECTIONS,
    NATURES,
    NO_ASK,
    STATUSES,
    VERDICT_KEYS,
    Response,
    parse_response,
)

CONTRACT_RE = re.compile(
    r"```yaml\n(status: classified \| partial \| needs_clarification \| not_a_problem\n.*?)```",
    re.DOTALL,
)
CONTRACT_KEY_RE = re.compile(r"^([a-z_]+):", re.MULTILINE)

CONTRACT_OWNER: dict[ChainMode, str] = {
    "monolith": "SKILL.md",
    "playbooks": "playbooks/define-the-problem.md",
}
SENTINEL_OWNER: dict[ChainMode, str] = {
    "monolith": "SKILL.md",
    "playbooks": "restate/SKILL.md",
}

CASE_HEADER_RE = re.compile(r"### Case ([A-L])\.")

README_PRINCIPLES_RE = re.compile(
    r"^## Principles\s*\n(?P<body>(?:.*\n)*?)(?=^## |\Z)",
    re.MULTILINE,
)
README_PRINCIPLE_ROW_RE = re.compile(
    r"^\| `(principle-[a-z0-9-]+)` \|.*\| (?P<governs>[^|]+) \|$"
)

_STATUS_WORD_RE = re.compile(
    r"\b(not_a_problem|needs_clarification|classified|partial|abstain)\b"
)

_RESTATEMENT_FAILS = frozenset(
    {"restatement_missing", "restatement_classifies", "restatement_speculates"}
)

_REQUIRED_RESTATEMENT_CASES = frozenset(
    {
        "classifies.yaml",
        "names-problem.yaml",
        "speculates.yaml",
        "quoted-think.yaml",
        "empty.yaml",
        "sentinel-ok.yaml",
    }
)


@dataclass(frozen=True)
class DriftProblem:
    kind: str
    detail: str


def check_suite(
    fixtures: list[Fixture],
    *,
    readme: str,
    mode: ChainMode,
    mount: dict[str, str],
    rubric_md: str,
) -> list[DriftProblem]:
    problems: list[DriftProblem] = []

    try:
        assert_skill_tree_clean()
    except RuntimeError as exc:
        problems.append(DriftProblem("skill_tree", str(exc)))

    try:
        assert_chain_ok()
    except RuntimeError as exc:
        problems.append(DriftProblem("chain", str(exc)))

    if "README.md" in mount:
        problems.append(DriftProblem("mount", "README.md must not be in the derived mount"))
    if not mount:
        problems.append(DriftProblem("mount", "derived mount is empty"))

    covered = covered_families(fixtures)
    missing = sorted(REQUIRED_FAMILIES - covered)
    if missing:
        problems.append(DriftProblem("family_uncovered", f"missing families: {missing}"))

    problems.extend(
        DriftProblem("rubric_binding", p) for p in rubric_keys_match_doc(rubric_md)
    )

    contract_rel = CONTRACT_OWNER[mode]
    sentinel_rel = SENTINEL_OWNER[mode]
    for rel in (contract_rel, sentinel_rel):
        if rel not in mount:
            problems.append(DriftProblem("mount", f"{rel} is not on the derived mount"))
    if contract_rel in mount:
        problems.extend(_contract_drift(readme, contract_rel, mount[contract_rel]))
    if sentinel_rel in mount:
        problems.extend(_sentinel_sync(sentinel_rel, mount[sentinel_rel]))
    problems.extend(_enum_drift(readme))
    problems.extend(_principles_drift(readme))
    problems.extend(_smart_cards_drift(readme))
    problems.extend(_seed_readme_drift(fixtures, readme))
    problems.extend(_gold_self_test(fixtures))
    problems.extend(_tripwire_vs_input(fixtures))
    problems.extend(_skill_contamination(fixtures, mount))
    problems.extend(_restatement_guard_self_test(RESTATEMENT_CASES_DIR))
    problems.extend(_challenge_grade_self_test(fixtures))
    return problems


def _extract_contract(doc: str) -> str | None:
    match = CONTRACT_RE.search(doc)
    return match.group(1).strip() if match else None


def _contract_drift(readme: str, owner_rel: str, owner: str) -> list[DriftProblem]:
    r = _extract_contract(readme)
    s = _extract_contract(owner)
    out: list[DriftProblem] = []
    if r is None:
        out.append(DriftProblem("contract_drift", "README missing output contract block"))
    if s is None:
        out.append(DriftProblem("contract_drift", f"{owner_rel} missing output contract block"))
    if r is not None and s is not None and r != s:
        out.append(
            DriftProblem("contract_drift", f"README and {owner_rel} contract blocks differ")
        )
    if s is not None:
        keys = frozenset(CONTRACT_KEY_RE.findall(s))
        if keys != VERDICT_KEYS:
            out.append(
                DriftProblem(
                    "contract_drift",
                    f"{owner_rel} contract keys {sorted(keys)} != parser keys {sorted(VERDICT_KEYS)}",
                )
            )
    for label, block in (("README", r), (owner_rel, s)):
        named = [area for area in AREAS if block is not None and area in block]
        if named:
            out.append(
                DriftProblem(
                    "contract_drift", f"{label} contract names worksheet areas {named}, want <id>"
                )
            )
    return out


def _enum_drift(readme: str) -> list[DriftProblem]:
    contract = _extract_contract(readme) or ""
    out: list[DriftProblem] = []
    for name, values in (
        ("status", STATUSES),
        ("nature", NATURES),
        ("direction", DIRECTIONS),
        ("confidence", CONFIDENCES),
    ):
        for value in values:
            if value not in contract:
                out.append(
                    DriftProblem("enum_drift", f"README contract missing {name} value {value}")
                )
    return out


def _principles_drift(readme: str) -> list[DriftProblem]:
    section = README_PRINCIPLES_RE.search(readme)
    if section is None:
        return [DriftProblem("principles_drift", "README missing ## Principles table")]
    rows: dict[str, frozenset[str]] = {}
    for line in section.group("body").splitlines():
        row = README_PRINCIPLE_ROW_RE.match(line)
        if row:
            rows[row.group(1)] = frozenset(re.findall(r"`([a-z_]+)`", row.group("governs")))
    out: list[DriftProblem] = []
    index = principle_names(SKILL_DIR)
    if tuple(rows) != index:
        out.append(
            DriftProblem(
                "principles_drift",
                f"README principles {list(rows)} differ from the index {list(index)}",
            )
        )
    for principle in load_principles(SKILL_DIR):
        governs = rows.get(principle.name)
        if governs is not None and governs != principle.governs:
            out.append(
                DriftProblem(
                    "principles_drift",
                    f"README governs for {principle.name} is {sorted(governs)}, "
                    f"leaf says {sorted(principle.governs)}",
                )
            )
    return out


def _case_blocks(readme: str) -> dict[str, dict[str, str]]:
    """Map case letter -> {input, yaml} extracted from README."""
    cases: dict[str, dict[str, str]] = {}
    parts = CASE_HEADER_RE.split(readme)
    i = 1
    while i + 1 < len(parts):
        letter = parts[i]
        body = parts[i + 1]
        input_m = re.search(r"\*\*Input\*\*\s*\n\n```text\n(.*?)```", body, re.DOTALL)
        yaml_m = re.search(
            r"\*\*Expected result(?: \(typical\))?\*\*\s*\n\n```yaml\n(.*?)```",
            body,
            re.DOTALL,
        )
        entry: dict[str, str] = {}
        if input_m:
            entry["input"] = input_m.group(1)
        if yaml_m:
            entry["yaml"] = yaml_m.group(1)
        if letter == "J":
            entry["table"] = body
        cases[letter] = entry
        i += 2
    return cases


def _normalize_ws(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def _seed_readme_drift(fixtures: list[Fixture], readme: str) -> list[DriftProblem]:
    cases = _case_blocks(readme)
    out: list[DriftProblem] = []
    for fixture in fixtures:
        if not fixture.readme:
            continue
        letter = fixture.readme
        case = cases.get(letter)
        if case is None:
            out.append(DriftProblem("readme_drift", f"{fixture.id}: README Case {letter} missing"))
            continue
        if letter == "J":
            for turn in fixture.turns:
                if turn.input.strip() not in case.get("table", ""):
                    out.append(
                        DriftProblem(
                            "readme_drift",
                            f"{fixture.id}: turn input not found in Case J table: {turn.input[:40]!r}",
                        )
                    )
            continue
        if "input" in case:
            if _normalize_ws(fixture.turns[0].input) != _normalize_ws(case["input"]):
                out.append(
                    DriftProblem("readme_drift", f"{fixture.id}: input differs from README Case {letter}")
                )
        if "yaml" in case:
            readme_gold = parse_response(f"```yaml\n{case['yaml']}\n```")
            if not isinstance(readme_gold, Response):
                out.append(
                    DriftProblem(
                        "readme_drift",
                        f"{fixture.id}: README gold does not parse: {readme_gold.kind}",
                    )
                )
                continue
            fixture_gold = fixture.turns[0].gold
            if (
                fixture_gold.verdict.status != readme_gold.verdict.status
                or len(fixture_gold.verdict.problems) != len(readme_gold.verdict.problems)
                or len(fixture_gold.verdict.unresolved) != len(readme_gold.verdict.unresolved)
            ):
                out.append(
                    DriftProblem(
                        "readme_drift",
                        f"{fixture.id}: gold shape differs from README Case {letter}",
                    )
                )
            elif fixture_gold.verdict.smart != readme_gold.verdict.smart:
                out.append(
                    DriftProblem(
                        "readme_drift",
                        f"{fixture.id}: gold SMART question or gaps differ from README Case {letter}",
                    )
                )
            else:
                for a, b in zip(
                    fixture_gold.verdict.problems, readme_gold.verdict.problems, strict=True
                ):
                    if a.quadrant != b.quadrant or a.statement != b.statement:
                        out.append(
                            DriftProblem(
                                "readme_drift",
                                f"{fixture.id}: gold problem differs from README Case {letter}",
                            )
                        )
                        break
    return out


def _smart_cards_drift(readme: str) -> list[DriftProblem]:
    try:
        skill_cards = load_cards(SKILL_DIR)
        readme_cards = parse_cards(readme)
    except ValueError as exc:
        return [DriftProblem("smart_cards", str(exc))]
    if readme_cards != skill_cards:
        return [DriftProblem("smart_cards", "README SMART cards differ from smart/SKILL.md")]
    return []


def _gold_self_test(fixtures: list[Fixture]) -> list[DriftProblem]:
    out: list[DriftProblem] = []
    for fixture in fixtures:
        for i, turn in enumerate(fixture.turns):
            if not smart_matches(turn.expect.smart, turn.gold.verdict.smart):
                out.append(
                    DriftProblem(
                        "gold_smart_mismatch",
                        f"{fixture.id} turn {i}: gold SMART {turn.gold.verdict.smart} vs expect {turn.expect.smart}",
                    )
                )
            if not worksheet_matches(turn.expect.worksheet, turn.gold.verdict.worksheet):
                out.append(
                    DriftProblem(
                        "gold_worksheet_mismatch",
                        f"{fixture.id} turn {i}: gold worksheet vs expect {turn.expect.worksheet}",
                    )
                )
            if not challenge_matches(turn.expect.challenge, turn.gold.verdict.challenge):
                out.append(
                    DriftProblem(
                        "gold_challenge_mismatch",
                        f"{fixture.id} turn {i}: gold challenge vs expect {turn.expect.challenge}",
                    )
                )
        results = grade_gold(fixture)
        for i, result in enumerate(results):
            if result.hard_fails or result.score < 1.0 - 1e-9:
                out.append(
                    DriftProblem(
                        "gold_not_perfect",
                        f"{fixture.id} turn {i}: score={result.score:.3f} fails={[h.kind for h in result.hard_fails]}",
                    )
                )
    return out


def _tripwire_vs_input(fixtures: list[Fixture]) -> list[DriftProblem]:
    out: list[DriftProblem] = []
    for fixture in fixtures:
        for i, turn in enumerate(fixture.turns):
            for pat in turn.tripwires.invented:
                if pat.search(turn.input):
                    out.append(
                        DriftProblem(
                            "tripwire_matches_input",
                            f"{fixture.id} turn {i}: invented {pat.pattern!r} matches input",
                        )
                    )
    return out


def _span_around_no_ask(text: str, no_ask_at: int) -> str:
    after_sentinel = no_ask_at + len(NO_ASK)
    prev_stop = max(text.rfind(mark, 0, no_ask_at) for mark in ".?!")
    next_stop = re.search(r"[.!?]", text[after_sentinel:])
    end = after_sentinel + next_stop.end() if next_stop else len(text)
    begin = 0 if prev_stop < 0 else prev_stop + 1
    return text[begin:end]


def _binds_sentinel_to_status(text: str) -> bool:
    start = 0
    while True:
        index = text.find(NO_ASK, start)
        if index < 0:
            return False
        if _STATUS_WORD_RE.search(_span_around_no_ask(text, index)):
            return True
        start = index + len(NO_ASK)


def _sentinel_sync(owner_rel: str, owner: str) -> list[DriftProblem]:
    problems: list[DriftProblem] = []
    if NO_ASK not in owner:
        problems.append(
            DriftProblem("sentinel_sync", f"{owner_rel} does not contain the restatement sentinel")
        )
    if _binds_sentinel_to_status(owner):
        problems.append(
            DriftProblem(
                "sentinel_status_binding",
                f"{owner_rel} binds the restatement sentinel to a status",
            )
        )
    bound = f"If you write {NO_ASK} then status is not_a_problem."
    free = f"If nothing is asked, write exactly {NO_ASK}"
    if not _binds_sentinel_to_status(bound):
        problems.append(
            DriftProblem("sentinel_status_binding", "detector missed a sentinel-to-status rule")
        )
    if _binds_sentinel_to_status(free):
        problems.append(
            DriftProblem(
                "sentinel_status_binding",
                "detector flagged a sentinel that does not set a status",
            )
        )
    return problems


_GUARD_BODY = (
    "status: not_a_problem\nmain_question: null\nproblems: []\n"
    "smart_question: null\nsmart_gaps: []\nworksheet: null\nchallenge: null\n"
    "unresolved: []\napplied: []\nstop: true\n"
)


def _guard_turn(user_input: str) -> Turn:
    text = user_input.strip() or "Noted."
    gold = parse_response(f"```yaml\n{_GUARD_BODY}```")
    if not isinstance(gold, Response):
        raise RuntimeError("guard gold failed to parse")
    return Turn(
        input=text,
        expect=Expectation(
            kind="abstain",
            statuses=("not_a_problem",),
            problems=(),
            unresolved=(),
            asks=(),
            smart=None,
            worksheet=None,
        ),
        tripwires=Tripwires(invented=(), method_not_problem=(), solve_leak=()),
        restatement=f"{NO_ASK} Noted.",
        gold_text="unused",
        gold=gold,
    )


def _restatement_guard_self_test(cases_dir: Path) -> list[DriftProblem]:
    if not cases_dir.is_dir():
        return [DriftProblem("restatement_guard", f"missing {cases_dir.name}/")]
    paths = sorted(cases_dir.glob("*.yaml"))
    problems: list[DriftProblem] = []
    missing = sorted(_REQUIRED_RESTATEMENT_CASES - {path.name for path in paths})
    if missing:
        problems.append(DriftProblem("restatement_guard", f"missing cases: {missing}"))
    for path in paths:
        doc = yaml.safe_load(path.read_text())
        if not isinstance(doc, dict) or "preamble" not in doc or "expect_fail" not in doc:
            problems.append(
                DriftProblem("restatement_guard", f"{path.name}: need preamble and expect_fail")
            )
            continue
        preamble = doc["preamble"]
        if not isinstance(preamble, str):
            problems.append(DriftProblem("restatement_guard", f"{path.name}: preamble must be a string"))
            continue
        expected = doc["expect_fail"]
        if expected is not None and expected not in _RESTATEMENT_FAILS:
            problems.append(
                DriftProblem("restatement_guard", f"{path.name}: unknown expect_fail {expected!r}")
            )
            continue
        text = f"```yaml\n{_GUARD_BODY}```" if not preamble.strip() else f"{preamble}\n\n```yaml\n{_GUARD_BODY}```"
        parsed = parse_response(text)
        if not isinstance(parsed, Response):
            problems.append(
                DriftProblem(
                    "restatement_guard",
                    f"{path.name}: case response did not parse ({parsed.kind})",
                )
            )
            continue
        user_input = doc.get("input")
        if not isinstance(user_input, str):
            problems.append(DriftProblem("restatement_guard", f"{path.name}: input must be a string"))
            continue
        kinds = [
            fail.kind
            for fail in _restatement_fails(_guard_turn(user_input), parsed.view.restatement)
        ]
        want = [] if expected is None else [expected]
        if kinds != want:
            problems.append(
                DriftProblem(
                    "restatement_guard",
                    f"{path.name}: want {want} got {kinds}",
                )
            )
    return problems


def _challenge_grade_self_test(fixtures: list[Fixture]) -> list[DriftProblem]:
    problems: list[DriftProblem] = []
    finding = Finding("sunk_cost", "four months already spent")
    opened = Open((finding,))
    line = render_line((finding,))
    only_line = f"See the note.\n{line}\n"
    if ungrounded_findings(opened, only_line) != ("sunk_cost",):
        problems.append(
            DriftProblem("challenge_grade", "a quote that exists only on the Challenge line stayed grounded")
        )
    if ungrounded_findings(opened, "We noted four months already spent in the plan.") != ():
        problems.append(DriftProblem("challenge_grade", "a paste quote was marked ungrounded"))
    probe = (
        'Context and constraints: Around "four months already spent", what background or '
        "pressures shape how you solve it, and what cannot change?"
    )
    if ungrounded_findings(opened, probe) != ("sunk_cost",):
        problems.append(DriftProblem("challenge_grade", "a quote that exists only on a probe line stayed grounded"))
    answered = Answered((finding,), None)
    if restated_line(answered, f"We noted four months already spent in the plan.\n{line}\n") is not True:
        problems.append(DriftProblem("challenge_grade", "a matching Challenge line was not idempotent"))
    paraphrased = "We noted four months already spent in the plan.\nChallenge: rethink this.\n"
    if restated_line(answered, paraphrased) is not False:
        problems.append(DriftProblem("challenge_grade", "a paraphrased Challenge line was accepted"))
    if restated_line(opened, only_line) is not None:
        problems.append(DriftProblem("challenge_grade", "restated_line ran on an open round"))

    sunk = next((fixture for fixture in fixtures if fixture.id == "challenge-sunk-groupthink"), None)
    if sunk is None:
        problems.append(DriftProblem("challenge_grade", "missing fixture challenge-sunk-groupthink"))
        return problems
    open_turn = next(
        (turn for turn in sunk.turns if turn.expect.challenge and turn.expect.challenge.round == "open"),
        None,
    )
    answered_turn = next(
        (
            turn
            for turn in sunk.turns
            if turn.expect.challenge and turn.expect.challenge.round == "answered"
        ),
        None,
    )
    if open_turn is None or not isinstance(open_turn.gold.verdict.challenge, Open):
        problems.append(DriftProblem("challenge_grade", "sunk fixture has no open gold"))
        return problems
    quote = open_turn.gold.verdict.challenge.findings[0].quote
    blanked = replace(open_turn, input=open_turn.input.replace(quote, ""))
    blanked_kinds = [
        fail.kind
        for fail in grade_turn(
            blanked, _gold_response_text(open_turn.restatement, open_turn.gold_text)
        ).hard_fails
    ]
    if "challenge_ungrounded" not in blanked_kinds:
        problems.append(
            DriftProblem("challenge_grade", f"blanked open quote did not fail ungrounded: {blanked_kinds}")
        )
    if answered_turn is None or not isinstance(answered_turn.gold.verdict.challenge, Answered):
        problems.append(DriftProblem("challenge_grade", "sunk fixture has no answered gold"))
        return problems
    want = render_line(answered_turn.gold.verdict.challenge.findings)
    if want not in answered_turn.input:
        problems.append(DriftProblem("challenge_grade", "answered input is missing its Challenge line"))
        return problems
    mutated = replace(
        answered_turn, input=answered_turn.input.replace(want, "Challenge: not the rendered line")
    )
    mutated_kinds = [
        fail.kind
        for fail in grade_turn(
            mutated, _gold_response_text(answered_turn.restatement, answered_turn.gold_text)
        ).hard_fails
    ]
    if "challenge_restated" not in mutated_kinds:
        problems.append(
            DriftProblem("challenge_grade", f"paraphrased line did not fail restated: {mutated_kinds}")
        )
    return problems


def _strip_emitted_probe_scaffold(text: str) -> str:
    scaffolds = [area.probe_template.split(QUESTION_SLOT) for area in load_registry().areas]
    lines: list[str] = []
    for line in text.splitlines():
        for head, tail in scaffolds:
            if len(line) > len(head) + len(tail) and line.startswith(head) and line.endswith(tail):
                line = line[len(head) : len(line) - len(tail)]
                break
        lines.append(line)
    return "\n".join(lines)


def _skill_contamination(fixtures: list[Fixture], mount: dict[str, str]) -> list[DriftProblem]:
    out: list[DriftProblem] = []
    for fixture in fixtures:
        for turn in fixture.turns:
            chunk = _strip_emitted_probe_scaffold(turn.input.strip())
            chunk = "\n".join(
                line for line in chunk.splitlines() if not line.strip().startswith("Challenge: ")
            )
            if len(chunk) < 40:
                continue
            for rel, text in mount.items():
                for start in range(0, max(1, len(chunk) - 39)):
                    excerpt = chunk[start : start + 40]
                    if excerpt in text:
                        out.append(
                            DriftProblem(
                                "skill_contaminated",
                                f"{fixture.id}: {rel} quotes fixture input {excerpt!r}",
                            )
                        )
                        break
    return out
