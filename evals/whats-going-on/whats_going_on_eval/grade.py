"""Scoring policy: hard fails, deterministic axes, suite summary."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import Literal, assert_never

from .challenge import challenge_prose, operator_ask, restated_line, ungrounded_findings
from .fixtures import Expectation, ExpectedProblem, Fixture, Turn, _gold_response_text
from .parse import (
    ClassifiedProblem,
    Halt,
    Response,
    Verdict,
    parse_response,
    parse_restatement,
)
from .smart import NoPrimary, Proposed, Withheld
from .view import STATUS_PHRASE, Mode, default_mode_problems, parse_view, view_agrees
from .wire import ContractViolation
from .worksheet import ungrounded_cells, worksheet_prose

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
    turn: Turn,
    text: str,
    judgment: Judgment | None = None,
    *,
    mode: Mode = "debug",
) -> TurnResult:
    """Debug grades the Verdict fence. Default grades the human view."""
    match mode:
        case "debug":
            return _grade_debug_turn(turn, text, judgment)
        case "default":
            return _grade_default_turn(turn, text, judgment)
        case _ as unreachable:
            assert_never(unreachable)


def _grade_debug_turn(
    turn: Turn, text: str, judgment: Judgment | None
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


def _grade_default_turn(
    turn: Turn, text: str, judgment: Judgment | None
) -> TurnResult:
    """Accept a human view. A fence is a contract fail. Outcome axes stay unscored."""
    parsed = parse_view(text)
    if isinstance(parsed, ContractViolation):
        hard_fails = (HardFail("contract", f"{parsed.kind} {parsed.detail}".strip()),)
    else:
        hard_fails = tuple(_restatement_fails(turn, parsed.restatement))
    return TurnResult(
        hard_fails=hard_fails,
        axes={k: None for k in RUBRIC},
        score=0.0,
        judgment=judgment,
    )


def grade_run(
    fixture: Fixture,
    repetition: int,
    responses: list[str],
    judgments: list[Judgment | None] | None = None,
    *,
    mode: Mode = "debug",
) -> FixtureRunResult:
    if judgments is None:
        judgments = [None] * len(responses)
    if len(responses) != len(fixture.turns):
        raise ValueError("response count must equal turn count")
    turns = tuple(
        grade_turn(turn, text, judgment, mode=mode)
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
        "preamble": response.view.restatement,
        "why": " ".join(p.why for p in verdict.problems),
        "next_method": " ".join(p.next_method for p in verdict.problems),
        "clarification": " ".join(u.clarification for u in verdict.unresolved),
        "changed": " ".join(a.changed for a in verdict.applied),
    }
    match verdict.smart:
        case NoPrimary() | Withheld():
            pass
        case Proposed(question=question):
            prose_fields["smart_question"] = question
            if turn.expect.smart is not None and turn.expect.smart.proposal == "withheld":
                fails.append(HardFail("smart_proposed_when_withheld", question))
        case _ as unreachable:
            assert_never(unreachable)

    leak_pats = list(GLOBAL_SOLVE_LEAK) + list(turn.tripwires.solve_leak)
    scanned = list(prose_fields.items())
    scanned.extend(("worksheet", content) for content in worksheet_prose(verdict.worksheet))
    scanned.extend(("challenge", content) for content in challenge_prose(verdict.challenge))
    for field, content in scanned:
        for pat in leak_pats:
            if content and pat.search(content):
                fails.append(HardFail("solve_leak", f"{field}: {pat.pattern}"))
    for cell in ungrounded_cells(verdict.worksheet, turn.input):
        fails.append(HardFail("worksheet_ungrounded", cell.area))
    for bias in ungrounded_findings(verdict.challenge, turn.input):
        fails.append(HardFail("challenge_ungrounded", bias))
    if restated_line(verdict.challenge, turn.input) is False:
        fails.append(HardFail("challenge_restated"))
    fails.extend(_restatement_fails(turn, response.view.restatement))
    fails.extend(
        HardFail(fail.kind, fail.detail) for fail in view_agrees(response.view, response.verdict)
    )
    return fails


def _restatement_fails(turn: Turn, restatement: str) -> list[HardFail]:
    text = restatement.strip()
    if not text:
        return [HardFail("restatement_missing")]
    fails: list[HardFail] = []
    if any(pat.search(text) for pat in RESTATEMENT_CLASSIFIES):
        fails.append(HardFail("restatement_classifies"))
    if any(pat.search(text) and not pat.search(turn.input) for pat in RESTATEMENT_SPECULATES):
        fails.append(HardFail("restatement_speculates"))
    return fails


def restatement_agreement(turn: Turn, response: Response) -> Literal["agree", "disagree", "n/a"]:
    parsed = parse_restatement(response.view.restatement)
    if parsed is None:
        return "n/a"
    status = response.verdict.status
    if not parsed.ask_stated and status in ("classified", "partial"):
        return "disagree"
    if status == "not_a_problem" and parsed.ask_stated:
        return "disagree"
    return "agree"


def presentation_problems(fixtures: list[Fixture]) -> list[str]:
    problems = list(default_mode_problems())
    problems.extend(_default_grade_problems(fixtures))
    problems.extend(_split_problems(fixtures))
    problems.extend(_agreement_problems(fixtures))
    return problems


def _default_grade_problems(fixtures: list[Fixture]) -> list[str]:
    """Default grading accepts a human view and still rejects a fence."""
    turn = next((item for fixture in fixtures for item in fixture.turns), None)
    if turn is None:
        return ["no turn to grade in default mode"]
    shown = next(
        phrase
        for phrase in STATUS_PHRASE.values()
        if phrase != STATUS_PHRASE[turn.gold.verdict.status]
    )
    human = (
        "What's going on\n\n"
        "Someone asks why checkout latency rose.\n\n"
        "The question\n"
        "A different question than the verdict.\n\n"
        "Status\n"
        f"{shown}.\n\n"
        "The real problem is the pool.\n"
    )
    problems: list[str] = []
    default = grade_turn(turn, human, mode="default")
    kinds = [fail.kind for fail in default.hard_fails]
    if "contract" in kinds:
        problems.append(f"default grade rejected a human reply ({kinds})")
    if "restatement_classifies" in kinds:
        problems.append("default grade read a classifying phrase in the view body")
    if any(kind.startswith("view_") for kind in kinds):
        problems.append(f"default grade pinned a view field without a verdict ({kinds})")
    fenced = grade_turn(turn, human + "\n```yaml\nstatus: classified\n```\n", mode="default")
    if not any(
        fail.kind == "contract" and fail.detail.startswith("yaml_fence")
        for fail in fenced.hard_fails
    ):
        problems.append(
            "default grade accepted a yaml fence ("
            + ", ".join(fail.kind for fail in fenced.hard_fails)
            + ")"
        )
    classifying = grade_turn(
        turn,
        "What's going on\n\nThe real problem is the pool.\n\nStatus\nNot defined yet.\n",
        mode="default",
    )
    if not any(fail.kind == "restatement_classifies" for fail in classifying.hard_fails):
        problems.append("default grade missed a classifying restatement")
    debug = grade_turn(turn, human, mode="debug")
    if not any(
        fail.kind == "contract" and fail.detail.startswith("no_yaml_block")
        for fail in debug.hard_fails
    ):
        problems.append("debug grade did not require a yaml fence")
    return problems


def _split_problems(fixtures: list[Fixture]) -> list[str]:
    turn = next(
        (
            item
            for fixture in fixtures
            for item in fixture.turns
            if not any(pat.search(item.restatement) for pat in RESTATEMENT_CLASSIFIES)
        ),
        None,
    )
    if turn is None:
        return ["no gold restatement is free of classifying words"]
    parsed = parse_response(
        _gold_response_text(
            f"{turn.restatement}\n\nThe real problem is the pool.",
            turn.gold_text,
        )
    )
    if not isinstance(parsed, Response):
        detail = parsed.kind if isinstance(parsed, ContractViolation) else type(parsed).__name__
        return [f"view split sample did not parse ({detail})"]
    problems: list[str] = []
    if parsed.view.restatement != turn.restatement:
        problems.append(f"view split restatement {parsed.view.restatement!r}")
    if parsed.view.body != "The real problem is the pool.":
        problems.append(f"view split body {parsed.view.body!r}")
    opening = [fail.kind for fail in _restatement_fails(turn, parsed.view.restatement)]
    if "restatement_classifies" in opening:
        problems.append("restatement grader read the view body")
    whole = [
        fail.kind
        for fail in _restatement_fails(
            turn, f"{parsed.view.restatement}\n\n{parsed.view.body}"
        )
    ]
    if "restatement_classifies" not in whole:
        problems.append("classifying view body did not trip the grader when it was included")
    return problems


def _agreement_problems(fixtures: list[Fixture]) -> list[str]:
    problems: list[str] = []
    for fixture in fixtures:
        for turn in fixture.turns:
            fails = view_agrees(turn.gold.view, turn.gold.verdict)
            if fails:
                problems.append(f"{fixture.id} gold view disagrees: {fails[0].kind}")
                return problems

    turn = fixtures[0].turns[0]
    verdict = turn.gold.verdict
    expected = STATUS_PHRASE[verdict.status]
    wrong = next(phrase for phrase in STATUS_PHRASE.values() if phrase != expected)
    if not any(
        fail.kind == "view_status"
        for fail in view_agrees(replace(turn.gold.view, status_phrase=wrong), verdict)
    ):
        problems.append("view_agrees accepted a status phrase that disagrees")

    if verdict.main_question is None:
        matching = "There is no question yet."
        differing = "Why did checkout latency rise?"
    else:
        matching = verdict.main_question
        differing = "A different question than the verdict."
    if view_agrees(replace(turn.gold.view, main_question=matching), verdict):
        problems.append("view_agrees rejected a main question that matches")
    if not any(
        fail.kind == "view_main_question"
        for fail in view_agrees(replace(turn.gold.view, main_question=differing), verdict)
    ):
        problems.append("view_agrees accepted a main question that disagrees")

    asked = next(
        (
            item
            for fixture in fixtures
            for item in fixture.turns
            if operator_ask(item.gold.verdict.worksheet, item.gold.verdict.challenge)
        ),
        None,
    )
    if asked is None:
        problems.append("no gold turn has an ask line to agree with")
        return problems
    ask = operator_ask(asked.gold.verdict.worksheet, asked.gold.verdict.challenge)
    if view_agrees(replace(asked.gold.view, ask_line=ask), asked.gold.verdict):
        problems.append("view_agrees rejected an ask line that matches")
    if not any(
        fail.kind == "view_ask"
        for fail in view_agrees(
            replace(asked.gold.view, ask_line="Ask yourself: This is not the verdict ask."),
            asked.gold.verdict,
        )
    ):
        problems.append("view_agrees accepted an ask line that disagrees")
    return problems


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
    concerns = verdict.concerns
    if not expect.unresolved:
        if not concerns:
            return 1.0
        return 0.5
    matched = 0
    for exp in expect.unresolved:
        for actual in concerns:
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
