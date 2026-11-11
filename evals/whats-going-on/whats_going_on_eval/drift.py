"""README ↔ fixtures ↔ SKILL contract equality checks."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .fixtures import REQUIRED_FAMILIES, Fixture, covered_families
from .grade import grade_gold, rubric_keys_match_doc
from .manifest import AGENT_MOUNT, assert_skill_tree_clean
from .parse import NATURES, DIRECTIONS, CONFIDENCES, STATUSES, parse_response, Response

CONTRACT_RE = re.compile(
    r"```yaml\n(status: classified \| partial \| needs_clarification \| not_a_problem\n.*?)```",
    re.DOTALL,
)

CASE_HEADER_RE = re.compile(r"### Case ([A-J])\.")


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

    if "README.md" in AGENT_MOUNT:
        problems.append(DriftProblem("mount", "README.md must not be in AGENT_MOUNT"))

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
