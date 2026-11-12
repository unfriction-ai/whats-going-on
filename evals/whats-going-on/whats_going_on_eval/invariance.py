from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from typing import Literal

from .manifest import REPORTS_DIR
from .parse import (
    NO_ASK,
    ContractViolation,
    Quadrant,
    Status,
    Verdict,
    parse_response,
)

CONTRACT_FAIL: Literal["contract_fail"] = "contract_fail"
TurnKey = tuple[str, int]


class InvarianceError(ValueError):
    pass


@dataclass(frozen=True, order=True)
class Outcome:
    status: Status
    problem_count: int
    quadrants: tuple[Quadrant, ...]

    @staticmethod
    def of(verdict: Verdict) -> Outcome:
        quadrants = tuple(sorted(problem.quadrant for problem in verdict.problems))
        return Outcome(
            status=verdict.status,
            problem_count=len(verdict.problems),
            quadrants=quadrants,
        )


OutcomeValue = Outcome | Literal["contract_fail"]


@dataclass(frozen=True)
class ContractFail:
    fixture_id: str
    turn: int
    side: str
    count: int


@dataclass(frozen=True)
class InvarianceReport:
    turns: int
    modal_mismatches: tuple[tuple[TurnKey, OutcomeValue, OutcomeValue], ...]
    contract_fails: tuple[ContractFail, ...]
    contract_fail_base: int
    contract_fail_treat: int
    contract_fail_noise: int | None
    disagreement_treat: float
    disagreement_noise: float | None
    passed: bool


def outcome_of_response(text: str) -> OutcomeValue:
    parsed = parse_response(text)
    if isinstance(parsed, ContractViolation):
        return CONTRACT_FAIL
    return Outcome.of(parsed.verdict)


def load_outcomes(run_id: str) -> dict[TurnKey, list[OutcomeValue]]:
    return {
        key: [outcome for _, outcome in rows]
        for key, rows in _load_rows(run_id).items()
    }


def compare(base: str, treat: str, noise: str | None) -> InvarianceReport:
    base_hash = _skill_hash(base)
    treat_hash = _skill_hash(treat)
    if base_hash == treat_hash:
        raise InvarianceError(
            f"refusing to compare {base} and {treat}: same skill_view_hash {base_hash}"
        )
    base_rows = _load_rows(base)
    treat_rows = _load_rows(treat)
    _require_same_shape(base_rows, treat_rows, base, treat)
    noise_rows = None
    if noise:
        noise_rows = _load_rows(noise)
        _require_same_shape(base_rows, noise_rows, base, noise)

    mismatches: list[tuple[TurnKey, OutcomeValue, OutcomeValue]] = []
    for key in sorted(base_rows):
        base_modal = _modal([outcome for _, outcome in base_rows[key]])
        treat_modal = _modal([outcome for _, outcome in treat_rows[key]])
        if (
            isinstance(base_modal, Outcome)
            and isinstance(treat_modal, Outcome)
            and base_modal != treat_modal
        ):
            mismatches.append((key, base_modal, treat_modal))

    base_fails, base_total = _contract_fails(base_rows, "base")
    treat_fails, treat_total = _contract_fails(treat_rows, "treat")
    noise_fails: tuple[ContractFail, ...] = ()
    noise_total: int | None = None
    if noise_rows is not None:
        noise_fails, noise_total = _contract_fails(noise_rows, "noise")

    disagreement_treat = _disagreement(base_rows, treat_rows)
    disagreement_noise = _disagreement(base_rows, noise_rows) if noise_rows is not None else None
    passed = (
        not mismatches
        and base_total == 0
        and treat_total == 0
        and (disagreement_noise is None or disagreement_treat <= disagreement_noise + 0.05)
    )
    return InvarianceReport(
        turns=len(base_rows),
        modal_mismatches=tuple(mismatches),
        contract_fails=base_fails + treat_fails + noise_fails,
        contract_fail_base=base_total,
        contract_fail_treat=treat_total,
        contract_fail_noise=noise_total,
        disagreement_treat=disagreement_treat,
        disagreement_noise=disagreement_noise,
        passed=passed,
    )


def preamble_outcome_problems() -> list[str]:
    asked = "Someone asks why checkout latency rose. Checkout latency rose."
    bare_yaml = _classified_text("")
    same = (
        outcome_of_response(_classified_text(asked)),
        outcome_of_response(_classified_text(f"{NO_ASK} Checkout latency rose.")),
        outcome_of_response(bare_yaml),
    )
    if any(not isinstance(item, Outcome) for item in same):
        return ["preamble property: sample response did not parse"]
    if len(set(same)) != 1:
        return ["outcome changed when only the preamble changed"]
    flipped = outcome_of_response(
        _classified_text(asked).replace("direction: convergent", "direction: divergent", 1)
    )
    base = same[0]
    if not isinstance(flipped, Outcome) or flipped == base:
        return ["quadrant flip did not change the outcome"]
    if flipped.status != base.status or flipped.problem_count != base.problem_count:
        return ["quadrant flip also changed status or problem count"]
    return []


def invariance_payload(report: InvarianceReport) -> dict[str, object]:
    return {
        "turns": report.turns,
        "modal_mismatch_count": len(report.modal_mismatches),
        "modal_mismatches": [
            {
                "fixture_id": key[0],
                "turn": key[1],
                "base": _label(base),
                "treat": _label(treat),
            }
            for key, base, treat in report.modal_mismatches
        ],
        "contract_fail_base": report.contract_fail_base,
        "contract_fail_treat": report.contract_fail_treat,
        "contract_fail_noise": report.contract_fail_noise,
        "contract_fails": [
            {
                "fixture_id": item.fixture_id,
                "turn": item.turn,
                "side": item.side,
                "count": item.count,
            }
            for item in report.contract_fails
        ],
        "disagreement_treat": report.disagreement_treat,
        "disagreement_noise": report.disagreement_noise,
        "passed": report.passed,
    }


def _classified_text(preamble: str) -> str:
    body = """```yaml
status: classified
problems:
  - statement: "Why did checkout latency rise?"
    classification:
      nature: analytical
      direction: convergent
    confidence: high
    why: "A measured change with a timeframe."
    next_method: "Compare telemetry before and after the change."
stop: true
```"""
    if not preamble.strip():
        return body
    return f"{preamble.strip()}\n\n{body}"


def _label(value: OutcomeValue) -> str:
    if isinstance(value, str):
        return value
    quads = ",".join(value.quadrants)
    return f"{value.status}|{value.problem_count}|{quads}"


def _modal(values: list[OutcomeValue]) -> OutcomeValue:
    counts = Counter(values)
    best = max(counts.values())
    winners = [value for value, count in counts.items() if count == best]

    def sort_key(value: OutcomeValue) -> tuple[object, ...]:
        if isinstance(value, str):
            return (0, value)
        return (1, value.status, value.problem_count, value.quadrants)

    winners.sort(key=sort_key)
    return winners[0]


def _skill_hash(run_id: str) -> str:
    path = REPORTS_DIR / run_id / "manifest.json"
    if not path.is_file():
        raise InvarianceError(f"{run_id}: manifest.json missing")
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or "skill_view_hash" not in data:
        raise InvarianceError(f"{run_id}: manifest has no skill_view_hash")
    return str(data["skill_view_hash"])


def _load_rows(run_id: str) -> dict[TurnKey, list[tuple[int, OutcomeValue]]]:
    tdir = REPORTS_DIR / run_id / "transcripts"
    if not tdir.is_dir():
        raise InvarianceError(f"{run_id}: no transcripts")
    grouped: dict[TurnKey, list[tuple[int, OutcomeValue]]] = {}
    for path in sorted(tdir.glob("*.json")):
        data = json.loads(path.read_text())
        key = (str(data["fixture_id"]), int(data["turn"]))
        rep = int(data["repetition"])
        grouped.setdefault(key, []).append((rep, outcome_of_response(str(data["response"]))))
    if not grouped:
        raise InvarianceError(f"{run_id}: no transcripts")
    for key, pairs in grouped.items():
        reps = [rep for rep, _ in pairs]
        if len(reps) != len(set(reps)):
            raise InvarianceError(f"{run_id}: duplicate repetition for {key}")
        pairs.sort(key=lambda item: item[0])
    return grouped


def _require_same_shape(
    left: dict[TurnKey, list[tuple[int, OutcomeValue]]],
    right: dict[TurnKey, list[tuple[int, OutcomeValue]]],
    left_id: str,
    right_id: str,
) -> None:
    if set(left) != set(right):
        raise InvarianceError(f"fixture turns differ between {left_id} and {right_id}")
    for key in left:
        left_reps = [rep for rep, _ in left[key]]
        right_reps = [rep for rep, _ in right[key]]
        if left_reps != right_reps:
            raise InvarianceError(
                f"repeat ids differ for {key[0]} turn {key[1]} between {left_id} and {right_id}"
            )


def _contract_fails(
    rows: dict[TurnKey, list[tuple[int, OutcomeValue]]], side: str
) -> tuple[tuple[ContractFail, ...], int]:
    found: list[ContractFail] = []
    total = 0
    for key in sorted(rows):
        count = sum(1 for _, outcome in rows[key] if outcome == CONTRACT_FAIL)
        total += count
        if count:
            found.append(ContractFail(fixture_id=key[0], turn=key[1], side=side, count=count))
    return tuple(found), total


def _disagreement(
    left: dict[TurnKey, list[tuple[int, OutcomeValue]]],
    right: dict[TurnKey, list[tuple[int, OutcomeValue]]],
) -> float:
    pairs = 0
    differ = 0
    for key in left:
        for (_, left_outcome), (_, right_outcome) in zip(left[key], right[key], strict=True):
            pairs += 1
            if left_outcome != right_outcome:
                differ += 1
    if pairs == 0:
        return 0.0
    return differ / pairs
