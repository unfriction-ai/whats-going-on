"""Load fixtures and derive families from expectation shape."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

from .parse import PREAMBLE_BUDGET, AtMostOne, Response, parse_response

Kind = Literal["abstain", "classify"]
Split = Literal["seed", "holdout"]

REQUIRED_FAMILIES = frozenset(
    {
        "clear_single",
        "ordinary_or_fyi",
        "vague_dissatisfaction",
        "solution_without_problem",
        "compound",
        "successive_asks",
    }
)


@dataclass(frozen=True)
class ExpectedProblem:
    anchors: tuple[re.Pattern[str], ...]
    quadrants: tuple[str, ...]


@dataclass(frozen=True)
class ExpectedUnresolved:
    anchors: tuple[re.Pattern[str], ...]


@dataclass(frozen=True)
class Expectation:
    kind: Kind
    statuses: tuple[str, ...]
    problems: AtMostOne[ExpectedProblem]
    unresolved: tuple[ExpectedUnresolved, ...]
    asks: tuple[tuple[re.Pattern[str], ...], ...]


@dataclass(frozen=True)
class Tripwires:
    invented: tuple[re.Pattern[str], ...]
    method_not_problem: tuple[re.Pattern[str], ...]
    solve_leak: tuple[re.Pattern[str], ...]


@dataclass(frozen=True)
class Turn:
    input: str
    expect: Expectation
    tripwires: Tripwires
    restatement: str
    gold_text: str
    gold: Response


@dataclass(frozen=True)
class Fixture:
    id: str
    split: Split
    families: frozenset[str]
    readme: str | None
    turns: tuple[Turn, ...]
    path: Path


def _compile_patterns(raw: Any, path: str) -> tuple[re.Pattern[str], ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError(f"{path} must be a list of regex strings")
    return tuple(re.compile(str(p), re.IGNORECASE) for p in raw)


def _compile_anchor_list(raw: Any, path: str) -> tuple[re.Pattern[str], ...]:
    pats = _compile_patterns(raw, path)
    if not pats:
        raise ValueError(f"{path} must be a non-empty list of regexes")
    return pats


def derive_families(fixture_id: str, turns: tuple[Turn, ...]) -> frozenset[str]:
    families: set[str] = set()
    if len(turns) > 1:
        families.add("successive_asks")

    classify_turns = [t for t in turns if t.expect.kind == "classify"]
    abstain_turns = [t for t in turns if t.expect.kind == "abstain"]

    for turn in classify_turns:
        if turn.tripwires.method_not_problem:
            families.add("solution_without_problem")
        if not turn.expect.unresolved:
            families.add("clear_single")
        elif not turn.tripwires.method_not_problem:
            families.add("compound")

    for turn in abstain_turns:
        if "not_a_problem" in turn.expect.statuses and not turn.expect.unresolved:
            families.add("ordinary_or_fyi")
        if "needs_clarification" in turn.expect.statuses:
            if turn.tripwires.invented or any(
                "rough" in p.pattern or "vague" in p.pattern for p in _flat_unresolved(turn)
            ):
                families.add("vague_dissatisfaction")
            if (turn.tripwires.invented and "solution" in fixture_id) or (
                "kubernetes" in fixture_id
            ):
                families.add("solution_without_problem")
            if not families.intersection(
                {"vague_dissatisfaction", "solution_without_problem", "ordinary_or_fyi"}
            ):
                if "not_a_problem" in turn.expect.statuses:
                    families.add("ordinary_or_fyi")
                else:
                    families.add("vague_dissatisfaction")

    if "kubernetes" in fixture_id or "solution-only" in fixture_id:
        families.add("solution_without_problem")
    if "ordinary" in fixture_id or "rename" in fixture_id or "fyi" in fixture_id:
        families.add("ordinary_or_fyi")

    return frozenset(families)


def _flat_unresolved(turn: Turn) -> tuple[re.Pattern[str], ...]:
    out: list[re.Pattern[str]] = []
    for u in turn.expect.unresolved:
        out.extend(u.anchors)
    return tuple(out)


def _parse_expectation(raw: dict[str, Any]) -> Expectation:
    kind = raw.get("kind")
    if kind not in ("abstain", "classify"):
        raise ValueError("expect.kind must be abstain or classify")
    statuses = raw.get("statuses")
    if not isinstance(statuses, list) or not statuses:
        raise ValueError("expect.statuses must be a non-empty list")

    unresolved_raw = raw.get("unresolved") or []
    unresolved: list[ExpectedUnresolved] = []
    for i, item in enumerate(unresolved_raw):
        if isinstance(item, dict) and "anchor" in item:
            unresolved.append(
                ExpectedUnresolved(_compile_anchor_list(item["anchor"], f"unresolved[{i}].anchor"))
            )
        else:
            raise ValueError(f"unresolved[{i}] must be {{anchor: [...]}}")

    if kind == "abstain":
        asks_raw = raw.get("asks") or []
        asks: list[tuple[re.Pattern[str], ...]] = []
        for i, item in enumerate(asks_raw):
            asks.append(_compile_anchor_list(item, f"asks[{i}]"))
        return Expectation(
            kind="abstain",
            statuses=tuple(str(s) for s in statuses),
            problems=(),
            unresolved=tuple(unresolved),
            asks=tuple(asks),
        )

    problems_raw = raw.get("problems")
    if not isinstance(problems_raw, list) or len(problems_raw) != 1:
        raise ValueError("classify expect.problems must hold exactly one primary problem")
    item = problems_raw[0]
    if not isinstance(item, dict):
        raise ValueError("problems[0] must be a mapping")
    quads = item.get("quadrants")
    if not isinstance(quads, list) or not quads:
        raise ValueError("problems[0].quadrants must be non-empty")
    primary = ExpectedProblem(
        anchors=_compile_anchor_list(item.get("anchor"), "problems[0].anchor"),
        quadrants=tuple(str(q) for q in quads),
    )
    return Expectation(
        kind="classify",
        statuses=tuple(str(s) for s in statuses),
        problems=(primary,),
        unresolved=tuple(unresolved),
        asks=(),
    )


def _parse_tripwires(raw: Any) -> Tripwires:
    raw = raw or {}
    return Tripwires(
        invented=_compile_patterns(raw.get("invented"), "tripwires.invented"),
        method_not_problem=_compile_patterns(
            raw.get("methodNotProblem"), "tripwires.methodNotProblem"
        ),
        solve_leak=_compile_patterns(raw.get("solveLeak"), "tripwires.solveLeak"),
    )


def _gold_response_text(restatement: str, gold_block: str) -> str:
    block = gold_block.strip()
    if not block.startswith("```"):
        block = f"```yaml\n{block}\n```"
    return f"{restatement.strip()}\n\n{block}"


def _parse_turn(raw: dict[str, Any]) -> Turn:
    input_text = raw.get("input")
    if not isinstance(input_text, str) or not input_text.strip():
        raise ValueError("turn.input must be a non-empty string")
    restatement = raw.get("restatement")
    if not isinstance(restatement, str) or not restatement.strip():
        raise ValueError("turn.restatement must be a non-empty string")
    gold_text = raw.get("gold")
    if not isinstance(gold_text, str) or not gold_text.strip():
        raise ValueError("turn.gold must be a non-empty string")
    gold_response_text = _gold_response_text(restatement, gold_text)
    parsed = parse_response(gold_response_text)
    if not isinstance(parsed, Response):
        raise ValueError(f"gold does not parse: {parsed.kind} {parsed.detail}")
    if len(parsed.preamble) > PREAMBLE_BUDGET:
        raise ValueError("gold preamble over budget")
    return Turn(
        input=input_text,
        expect=_parse_expectation(raw["expect"]),
        tripwires=_parse_tripwires(raw.get("tripwires")),
        restatement=restatement.strip(),
        gold_text=gold_text,
        gold=parsed,
    )


def load_fixture(path: Path) -> Fixture:
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a mapping")
    if "family" in data:
        raise ValueError(f"{path}: stored family field is forbidden; families are derived")
    turns_raw = data.get("turns")
    if not isinstance(turns_raw, list) or not turns_raw:
        raise ValueError(f"{path}: turns must be a non-empty list")
    turns = tuple(_parse_turn(t) for t in turns_raw)
    split: Split = "holdout" if "holdout" in path.parts else "seed"
    fixture_id = path.stem
    readme = data.get("readme")
    if readme is not None:
        readme = str(readme)
    return Fixture(
        id=fixture_id,
        split=split,
        families=derive_families(fixture_id, turns),
        readme=readme,
        turns=turns,
        path=path,
    )


def load_suite(fixtures_dir: Path) -> list[Fixture]:
    paths = sorted(fixtures_dir.glob("seed/*.yaml")) + sorted(
        fixtures_dir.glob("holdout/*.yaml")
    )
    if not paths:
        raise FileNotFoundError(f"no fixtures under {fixtures_dir}")
    return [load_fixture(p) for p in paths]


def covered_families(fixtures: list[Fixture]) -> frozenset[str]:
    out: set[str] = set()
    for f in fixtures:
        out |= set(f.families)
    return frozenset(out)
