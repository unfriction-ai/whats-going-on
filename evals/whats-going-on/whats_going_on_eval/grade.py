"""Scoring policy: hard fails, deterministic axes, suite summary."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from .fixtures import Expectation, ExpectedProblem, Fixture, Turn, _gold_response_text
from .parse import (
    ClassifiedProblem,
    ContractViolation,
    Halt,
    Response,
    Verdict,
    parse_response,
    parse_restatement,
)

RUBRIC: dict[str, float] = {
    "detection": 0.25,
    "abstention": 0.25,
    "separation": 0.15,
    "classification": 0.20,
    "evidence": 0.15,
}

assert abs(sum(RUBRIC.values()) - 1.0) < 1e-9

Axis = Literal["detection", "abstention", "separation", "classification", "evidence"]

RESTATEMENT_CLASSIFIES = (
    re.compile(r"\b(analytical|conceptual|convergent|divergent|quadrant)\b", re.I),
    re.compile(r"\bthe (real |actual |underlying |core )?(problem|issue|cause) (is|was)\b", re.I),
)
RESTATEMENT_SPECULATES = (
    re.compile(
        r"\b(probably|likely|presumably|seems? to (want|need)|sounds like|their goal)\b",
        re.I,
    ),
)

GLOBAL_SOLVE_LEAK: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(i|we) (would )?recommend\b", re.I),
    re.compile(r"\byou should\b", re.I),
    re.compile(r"\bthe root cause (is|was)\b", re.I),
    re.compile(r"^\s*(\d+[.)]|[-*])\s+\S", re.M),
)


@dataclass(frozen=True)
class HardFail:
    kind: str
    detail: str = ""


@dataclass(frozen=True)
class Judgment:
    evidence: int  # 0|1|2
    notes: str
    suspected_hard_fail: str | None


@dataclass(frozen=True)
class TurnResult:
    hard_fails: tuple[HardFail, ...]
    axes: dict[str, float | None]  # None = N/A
    score: float
    judgment: Judgment | None
    restatement_agreement: Literal["agree", "disagree", "n/a"] = "n/a"


@dataclass(frozen=True)
class FixtureRunResult:
    fixture_id: str
    repetition: int
    turns: tuple[TurnResult, ...]
    score: float


def describe_hard_fail(h: HardFail) -> str:
    return f"{h.kind}: {h.detail}" if h.detail else h.kind


def grade_turn(
    turn: Turn, text: str, judgment: Judgment | None = None
) -> TurnResult:
    parsed = parse_response(text)
    if isinstance(parsed, ContractViolation):
        return TurnResult(
            hard_fails=(HardFail("contract", f"{parsed.kind} {parsed.detail}".strip()),),
            axes={k: None for k in RUBRIC},
            score=0.0,
            judgment=judgment,
        )
    if isinstance(parsed, Halt):
        return TurnResult(
            hard_fails=(HardFail("contract", "unexpected_halt"),),
            axes={k: None for k in RUBRIC},
            score=0.0,
            judgment=judgment,
        )

    hard_fails = list(_hard_fails(turn, parsed, text))
    axes = _score_axes(turn.expect, parsed.verdict, judgment)
    score = 0.0 if hard_fails else _weighted(axes)
    return TurnResult(
        hard_fails=tuple(hard_fails),
        axes=axes,
        score=score,
        judgment=judgment,
        restatement_agreement=restatement_agreement(turn, parsed),
    )


def grade_run(
    fixture: Fixture,
    repetition: int,
    responses: list[str],
    judgments: list[Judgment | None] | None = None,
) -> FixtureRunResult:
    if judgments is None:
        judgments = [None] * len(responses)
    if len(responses) != len(fixture.turns):
        raise ValueError("response count must equal turn count")
    turns = tuple(
        grade_turn(turn, text, judgment)
        for turn, text, judgment in zip(fixture.turns, responses, judgments, strict=True)
    )
    score = sum(t.score for t in turns) / len(turns) if turns else 0.0
    return FixtureRunResult(
        fixture_id=fixture.id, repetition=repetition, turns=turns, score=score
    )


def grade_gold(fixture: Fixture) -> list[TurnResult]:
    return [
        grade_turn(turn, _gold_response_text(turn.restatement, turn.gold_text))
        for turn in fixture.turns
    ]


def _hard_fails(turn: Turn, response: Response, text: str) -> list[HardFail]:
    fails: list[HardFail] = []
    verdict = response.verdict

    if turn.expect.kind == "abstain" and verdict.problems:
        fails.append(
            HardFail(
                "classified_without_problem",
                "; ".join(p.statement for p in verdict.problems),
            )
        )

    for problem in verdict.problems:
        for pat in turn.tripwires.method_not_problem:
            if pat.search(problem.statement):
                fails.append(
                    HardFail("method_as_problem", f"{pat.pattern!r} in {problem.statement!r}")
                )

    for pat in turn.tripwires.invented:
        if pat.search(text):
            fails.append(HardFail("invented_detail", pat.pattern))

    prose_fields = {
        "preamble": response.preamble,
        "why": " ".join(p.why for p in verdict.problems),
        "next_method": " ".join(p.next_method for p in verdict.problems),
        "clarification": " ".join(u.clarification for u in verdict.unresolved),
        "changed": " ".join(a.changed for a in verdict.applied),
    }
    leak_pats = list(GLOBAL_SOLVE_LEAK) + list(turn.tripwires.solve_leak)
    for field, content in prose_fields.items():
        for pat in leak_pats:
            if content and pat.search(content):
                fails.append(HardFail("solve_leak", f"{field}: {pat.pattern}"))
    fails.extend(_restatement_fails(turn, response.preamble))
    return fails


def _restatement_fails(turn: Turn, preamble: str) -> list[HardFail]:
    text = preamble.strip()
    if not text:
        return [HardFail("restatement_missing")]
    fails: list[HardFail] = []
    if any(pat.search(text) for pat in RESTATEMENT_CLASSIFIES):
        fails.append(HardFail("restatement_classifies"))
    if any(pat.search(text) and not pat.search(turn.input) for pat in RESTATEMENT_SPECULATES):
        fails.append(HardFail("restatement_speculates"))
    return fails


def restatement_agreement(turn: Turn, response: Response) -> Literal["agree", "disagree", "n/a"]:
    parsed = parse_restatement(response.preamble)
    if parsed is None:
        return "n/a"
    status = response.verdict.status
    if not parsed.ask_stated and status in ("classified", "partial"):
        return "disagree"
    if status == "not_a_problem" and parsed.ask_stated:
        return "disagree"
    return "agree"


def _score_axes(
    expect: Expectation, verdict: Verdict, judgment: Judgment | None
) -> dict[str, float | None]:
    detection = 1.0 if verdict.status in expect.statuses else 0.0

    if expect.kind == "abstain":
        separation = None
        classification = None
        abstention = _abstention_score(expect, verdict)
    else:
        pair = _primary_pair(expect, verdict)
        separation = 1.0 if pair else 0.0
        classification = _classification_score(pair)
        abstention = _classify_abstention(expect, verdict)

    if judgment is None:
        evidence: float | None = None
    else:
        evidence = judgment.evidence / 2.0

    return {
        "detection": detection,
        "abstention": abstention,
        "separation": separation,
        "classification": classification,
        "evidence": evidence,
    }


def _abstention_score(expect: Expectation, verdict: Verdict) -> float:
    if verdict.problems:
        return 0.0
    parts: list[float] = []
    if expect.unresolved:
        matched = 0
        for exp in expect.unresolved:
            for actual in verdict.unresolved:
                blob = f"{actual.observation} {actual.reason}"
                if all(p.search(blob) for p in exp.anchors):
                    matched += 1
                    break
        parts.append(matched / len(expect.unresolved))
    if expect.asks:
        clar = " ".join(u.clarification for u in verdict.unresolved)
        ask_hits = sum(1 for ask in expect.asks if all(p.search(clar) for p in ask))
        parts.append(ask_hits / len(expect.asks) if expect.asks else 1.0)
    if not parts:
        return 1.0 if not verdict.problems else 0.0
    return sum(parts) / len(parts)


def _classify_abstention(expect: Expectation, verdict: Verdict) -> float:
    if not expect.unresolved:
        if not verdict.unresolved:
            return 1.0
        return 0.5
    matched = 0
    for exp in expect.unresolved:
        for actual in verdict.unresolved:
            blob = f"{actual.observation} {actual.reason}"
            if all(p.search(blob) for p in exp.anchors):
                matched += 1
                break
    return matched / len(expect.unresolved)


def _primary_pair(
    expect: Expectation, verdict: Verdict
) -> tuple[ExpectedProblem, ClassifiedProblem] | None:
    if not expect.problems or not verdict.problems:
        return None
    expected, actual = expect.problems[0], verdict.problems[0]
    if all(p.search(actual.statement) for p in expected.anchors):
        return expected, actual
    return None


def _classification_score(pair: tuple[ExpectedProblem, ClassifiedProblem] | None) -> float:
    if pair is None:
        return 0.0
    expected, actual = pair
    if actual.quadrant in expected.quadrants:
        return 1.0
    if actual.quadrant.split("-")[0] == expected.quadrants[0].split("-")[0]:
        return 0.5
    return 0.0


def _weighted(axes: dict[str, float | None]) -> float:
    scored = {k: v for k, v in axes.items() if v is not None}
    if not scored:
        return 0.0
    weight_sum = sum(RUBRIC[k] for k in scored)
    return sum(RUBRIC[k] * scored[k] for k in scored) / weight_sum


@dataclass(frozen=True)
class SuiteReport:
    hard_fail_count: int
    abstention_precision: float
    mean_all: float
    mean_seed: float
    mean_holdout: float
    by_axis: dict[str, float | None]
    by_family: dict[str, float]
    results: tuple[FixtureRunResult, ...]
    passed: bool
    restatement_disagreement_rate: float


def summarize(
    results: list[FixtureRunResult], fixtures_by_id: dict[str, Fixture]
) -> SuiteReport:
    hard = sum(len(t.hard_fails) for r in results for t in r.turns)

    abstain_total = 0
    abstain_ok = 0
    for r in results:
        fixture = fixtures_by_id[r.fixture_id]
        for turn, turn_result in zip(fixture.turns, r.turns, strict=True):
            if turn.expect.kind != "abstain":
                continue
            abstain_total += 1
            if not any(h.kind == "classified_without_problem" for h in turn_result.hard_fails):
                abstain_ok += 1

    precision = abstain_ok / abstain_total if abstain_total else 1.0

    def mean_for(split: str | None) -> float:
        scores = [
            r.score
            for r in results
            if split is None or fixtures_by_id[r.fixture_id].split == split
        ]
        return sum(scores) / len(scores) if scores else 0.0

    axis_vals: dict[str, list[float]] = {k: [] for k in RUBRIC}
    for r in results:
        for t in r.turns:
            for k, v in t.axes.items():
                if v is not None:
                    axis_vals[k].append(v)
    by_axis = {
        k: (sum(vs) / len(vs) if vs else None) for k, vs in axis_vals.items()
    }

    family_scores: dict[str, list[float]] = {}
    for r in results:
        for fam in fixtures_by_id[r.fixture_id].families:
            family_scores.setdefault(fam, []).append(r.score)
    by_family = {k: sum(v) / len(v) for k, v in sorted(family_scores.items())}

    labels = [t.restatement_agreement for r in results for t in r.turns]
    compared = [label for label in labels if label != "n/a"]
    disagreement_rate = (
        sum(1 for label in compared if label == "disagree") / len(compared) if compared else 0.0
    )

    passed = hard == 0  # graft: only hard fails gate

    return SuiteReport(
        hard_fail_count=hard,
        abstention_precision=precision,
        mean_all=mean_for(None),
        mean_seed=mean_for("seed"),
        mean_holdout=mean_for("holdout"),
        by_axis=by_axis,
        by_family=by_family,
        results=tuple(results),
        passed=passed,
        restatement_disagreement_rate=disagreement_rate,
    )


def rubric_keys_match_doc(rubric_md: str) -> list[str]:
    """Require backtick-wrapped grader keys in rubric.md to equal RUBRIC keys."""
    found = set(re.findall(r"`(detection|abstention|separation|classification|evidence)`", rubric_md))
    missing = [k for k in RUBRIC if k not in found]
    extra = sorted(found - set(RUBRIC))
    problems: list[str] = []
    if missing:
        problems.append(f"rubric.md missing grader keys: {missing}")
    if extra:
        problems.append(f"rubric.md has unknown keys: {extra}")
    return problems
