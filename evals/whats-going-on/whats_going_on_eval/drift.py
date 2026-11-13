"""README ↔ fixtures ↔ SKILL contract equality checks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from .fixtures import REQUIRED_FAMILIES, Expectation, Fixture, Tripwires, Turn, covered_families
from .grade import _restatement_fails, grade_gold, rubric_keys_match_doc
from .manifest import (
    RESTATEMENT_CASES_DIR,
    agent_mount,
    assert_chain_ok,
    assert_skill_tree_clean,
)
from .parse import (
    CONFIDENCES,
    DIRECTIONS,
    NATURES,
    NO_ASK,
    STATUSES,
    Response,
    parse_response,
)

CONTRACT_RE = re.compile(
    r"```yaml\n(status: classified \| partial \| needs_clarification \| not_a_problem\n.*?)```",
    re.DOTALL,
)

CASE_HEADER_RE = re.compile(r"### Case ([A-J])\.")

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
    skill: str,
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

    mount = agent_mount()
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

    problems.extend(_contract_drift(readme, skill))
    problems.extend(_enum_drift(readme))
    problems.extend(_seed_readme_drift(fixtures, readme))
    problems.extend(_gold_self_test(fixtures))
    problems.extend(_tripwire_vs_input(fixtures))
    problems.extend(_skill_contamination(fixtures, skill))
    problems.extend(_sentinel_sync(skill))
    problems.extend(_restatement_guard_self_test(RESTATEMENT_CASES_DIR))
    return problems


def _extract_contract(doc: str) -> str | None:
    match = CONTRACT_RE.search(doc)
    return match.group(1).strip() if match else None


def _contract_drift(readme: str, skill: str) -> list[DriftProblem]:
    r = _extract_contract(readme)
    s = _extract_contract(skill)
    out: list[DriftProblem] = []
    if r is None:
        out.append(DriftProblem("contract_drift", "README missing output contract block"))
    if s is None:
        out.append(DriftProblem("contract_drift", "SKILL.md missing output contract block"))
    if r is not None and s is not None and r != s:
        out.append(DriftProblem("contract_drift", "README and SKILL.md contract blocks differ"))
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


def _gold_self_test(fixtures: list[Fixture]) -> list[DriftProblem]:
    out: list[DriftProblem] = []
    for fixture in fixtures:
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


def _sentinel_sync(skill: str) -> list[DriftProblem]:
    problems: list[DriftProblem] = []
    if NO_ASK not in skill:
        problems.append(
            DriftProblem("sentinel_sync", "SKILL.md does not contain the restatement sentinel")
        )
    if _binds_sentinel_to_status(skill):
        problems.append(
            DriftProblem(
                "sentinel_status_binding",
                "SKILL.md binds the restatement sentinel to a status",
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


def _guard_turn(user_input: str) -> Turn:
    text = user_input.strip() or "Noted."
    gold = parse_response(
        "```yaml\nstatus: not_a_problem\nproblems: []\nunresolved: []\nstop: true\n```"
    )
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
    body = "status: not_a_problem\nproblems: []\nunresolved: []\nstop: true\n"
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
        text = f"```yaml\n{body}```" if not preamble.strip() else f"{preamble}\n\n```yaml\n{body}```"
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
            for fail in _restatement_fails(_guard_turn(user_input), parsed.preamble)
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


def _skill_contamination(fixtures: list[Fixture], skill: str) -> list[DriftProblem]:
    out: list[DriftProblem] = []
    for fixture in fixtures:
        for turn in fixture.turns:
            chunk = turn.input.strip()
            if len(chunk) < 40:
                continue
            for start in range(0, max(1, len(chunk) - 39)):
                excerpt = chunk[start : start + 40]
                if excerpt in skill:
                    out.append(
                        DriftProblem(
                            "skill_contaminated",
                            f"{fixture.id}: SKILL.md quotes fixture input {excerpt!r}",
                        )
                    )
                    break
    return out
