"""Load fixtures and derive families from expectation shape."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, assert_never

import yaml

from .challenge import (
    Answered,
    BIASES,
    BiasId,
    ChallengeAssessment,
    Clear,
    Finding,
    NotRun,
    Open,
)
from .parse import PREAMBLE_BUDGET, AtMostOne, Halt, Response, StructureResponse, parse_response
from .structure import STRUCTURE_STATUSES
from .wire import ContractViolation
from .smart import (
    REQUIRED_TO_PROPOSE,
    NoPrimary,
    Proposed,
    SmartLetter,
    SmartProposal,
    Withheld,
    in_card_order,
)
from .worksheet import (
    AREAS,
    AreaId,
    Asking,
    Complete,
    Filled,
    HandedBack,
    NotStarted,
    Stop,
    WorksheetAssessment,
)

Kind = Literal["abstain", "classify", "structure"]
Split = Literal["seed", "holdout"]

REQUIRED_FAMILIES = frozenset(
    {
        "clear_single",
        "ordinary_or_fyi",
        "vague_dissatisfaction",
        "solution_without_problem",
        "compound",
        "successive_asks",
        "challenged",
        "structure",
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
class SmartExpect:
    proposal: Literal["proposed", "withheld"]
    gaps: tuple[SmartLetter, ...]


CellExpectStatus = Literal["filled", "unknown", "not_yet", "i_am_decider"]


@dataclass(frozen=True)
class WorksheetExpect:
    stop: Stop
    cells: tuple[tuple[AreaId, CellExpectStatus], ...]


@dataclass(frozen=True)
class ChallengeExpect:
    round: Literal["clear", "open", "answered"] | None
    biases: tuple[BiasId, ...] = ()

    def __post_init__(self) -> None:
        if self.round is None:
            if self.biases:
                raise ValueError("a null challenge expect has no biases")
            return
        if self.round == "clear":
            if self.biases:
                raise ValueError("a clear challenge expect has no biases")
            return
        if not self.biases:
            raise ValueError(f"{self.round} challenge expect needs biases")
        if any(bias not in BIASES for bias in self.biases):
            raise ValueError("expect.challenge.biases names an unknown bias")
        indexes = [BIASES.index(bias) for bias in self.biases]
        if indexes != sorted(set(indexes)):
            raise ValueError("expect.challenge.biases must be distinct and in table order")


@dataclass(frozen=True)
class Expectation:
    kind: Kind
    statuses: tuple[str, ...]
    problems: AtMostOne[ExpectedProblem]
    unresolved: tuple[ExpectedUnresolved, ...]
    asks: tuple[tuple[re.Pattern[str], ...], ...]
    smart: SmartExpect | None
    worksheet: WorksheetExpect | None
    challenge: ChallengeExpect | None = None
    root_anchor: tuple[re.Pattern[str], ...] = ()
    min_breakdowns: int = 0
    selection_ask: bool = False


def _bias_ids(findings: tuple[Finding, ...]) -> tuple[BiasId, ...]:
    return tuple(finding.bias for finding in findings)


def challenge_matches(expect: ChallengeExpect | None, assessment: ChallengeAssessment) -> bool:
    if expect is None or expect.round is None:
        return isinstance(assessment, NotRun)
    match assessment:
        case Clear():
            return expect.round == "clear"
        case Open(findings=findings):
            return expect.round == "open" and _bias_ids(findings) == expect.biases
        case Answered(findings=findings):
            return expect.round == "answered" and _bias_ids(findings) == expect.biases
        case NotRun():
            return False
        case _ as unreachable:
            assert_never(unreachable)


def worksheet_matches(expect: WorksheetExpect | None, assessment: WorksheetAssessment) -> bool:
    if expect is None:
        return isinstance(assessment, NotStarted)
    match assessment:
        case NotStarted():
            return False
        case Asking(cells=cells):
            stop = "asking"
        case HandedBack(cells=cells):
            stop = "handed_back"
        case Complete(cells=cells):
            stop = "complete"
        case _ as unreachable:
            assert_never(unreachable)
    got = tuple(
        (cell.area, "filled" if isinstance(cell, Filled) else cell.status) for cell in cells
    )
    return expect.stop == stop and expect.cells == got


def smart_matches(expect: SmartExpect | None, proposal: SmartProposal) -> bool:
    match proposal:
        case NoPrimary():
            return expect is None
        case Withheld(gaps=gaps):
            return expect == SmartExpect("withheld", gaps)
        case Proposed(gaps=gaps):
            return expect == SmartExpect("proposed", gaps)
        case _ as unreachable:
            assert_never(unreachable)


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
    gold: Response | StructureResponse
    command: str = "/whats-going-on"


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
    if any(turn.expect.kind == "structure" for turn in turns):
        families.add("structure")

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
    for turn in turns:
        challenge = turn.expect.challenge
        if challenge is not None and challenge.round in ("open", "answered"):
            families.add("challenged")

    return frozenset(families)


def _flat_unresolved(turn: Turn) -> tuple[re.Pattern[str], ...]:
    out: list[re.Pattern[str]] = []
    for u in turn.expect.unresolved:
        out.extend(u.anchors)
    return tuple(out)


def _parse_expectation(raw: dict[str, Any]) -> Expectation:
    kind = raw.get("kind")
    if kind not in ("abstain", "classify", "structure"):
        raise ValueError("expect.kind must be abstain, classify, or structure")
    statuses = raw.get("statuses")
    if not isinstance(statuses, list) or not statuses:
        raise ValueError("expect.statuses must be a non-empty list")
    status_names = tuple(str(s) for s in statuses)
    if kind == "structure":
        return _parse_structure_expectation(raw, status_names)

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
        if "smart" in raw:
            raise ValueError("abstain expect must not set smart; the smart step needs a primary")
        if "worksheet" in raw:
            raise ValueError("abstain expect must not set worksheet")
        asks_raw = raw.get("asks") or []
        asks: list[tuple[re.Pattern[str], ...]] = []
        for i, item in enumerate(asks_raw):
            asks.append(_compile_anchor_list(item, f"asks[{i}]"))
        return Expectation(
            kind="abstain",
            statuses=status_names,
            problems=(),
            unresolved=tuple(unresolved),
            asks=tuple(asks),
            smart=None,
            worksheet=None,
            challenge=_parse_challenge_expect(raw, None),
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
    smart = _parse_smart_expect(raw.get("smart"))
    worksheet = _parse_worksheet_expect(raw, smart)
    return Expectation(
        kind="classify",
        statuses=status_names,
        problems=(primary,),
        unresolved=tuple(unresolved),
        asks=(),
        smart=smart,
        worksheet=worksheet,
        challenge=_parse_challenge_expect(raw, worksheet),
    )


def _parse_structure_expectation(raw: dict[str, Any], statuses: tuple[str, ...]) -> Expectation:
    allowed = {"kind", "statuses", "root_anchor", "min_breakdowns", "selection_ask"}
    extra = set(raw) - allowed
    if extra:
        raise ValueError(f"structure expect has unknown keys: {sorted(extra)}")
    if any(status not in STRUCTURE_STATUSES for status in statuses):
        raise ValueError("structure expect.statuses must be structured, needs_split, or blocked")
    blocked_only = set(statuses) <= {"blocked"}
    if "root_anchor" in raw:
        root_anchor = _compile_anchor_list(raw["root_anchor"], "expect.root_anchor")
    elif blocked_only:
        root_anchor = ()
    else:
        raise ValueError("expect.root_anchor is required unless status is blocked")
    if "min_breakdowns" in raw:
        min_breakdowns = raw["min_breakdowns"]
        if type(min_breakdowns) is not int or min_breakdowns < 0:
            raise ValueError("expect.min_breakdowns must be a non-negative integer")
    else:
        min_breakdowns = 0 if blocked_only else 1
    if "selection_ask" in raw:
        selection_ask = raw["selection_ask"]
        if type(selection_ask) is not bool:
            raise ValueError("expect.selection_ask must be true or false")
    else:
        selection_ask = statuses == ("structured",)
    return Expectation(
        kind="structure",
        statuses=statuses,
        problems=(),
        unresolved=(),
        asks=(),
        smart=None,
        worksheet=None,
        challenge=None,
        root_anchor=root_anchor,
        min_breakdowns=min_breakdowns,
        selection_ask=selection_ask,
    )


def _parse_command(raw: dict[str, Any]) -> str | None:
    if "command" not in raw:
        return None
    command = raw["command"]
    if (
        not isinstance(command, str)
        or not command.startswith("/")
        or any(ch.isspace() for ch in command)
    ):
        raise ValueError("turn.command must be a slash command")
    return command


def _parse_challenge_expect(
    raw: dict[str, Any], worksheet: WorksheetExpect | None
) -> ChallengeExpect | None:
    complete = worksheet is not None and worksheet.stop == "complete"
    if "challenge" not in raw:
        if complete:
            raise ValueError("expect.challenge is required when worksheet.stop is complete")
        return None
    value = raw["challenge"]
    if not complete:
        if value is None:
            return ChallengeExpect(None)
        raise ValueError("expect.challenge is set only when worksheet.stop is complete")
    if not isinstance(value, dict) or set(value) != {"round", "biases"}:
        raise ValueError("complete expect.challenge must be {round, biases}")
    round_name = value["round"]
    biases = value["biases"]
    if not isinstance(biases, list) or not all(isinstance(bias, str) for bias in biases):
        raise ValueError("expect.challenge.biases must be a list of bias ids")
    if round_name not in ("clear", "open", "answered"):
        raise ValueError("expect.challenge.round must be clear, open, or answered")
    return ChallengeExpect(round_name, tuple(biases))


def _parse_stop(raw: Any) -> Stop:
    if raw == "asking" or raw == "handed_back" or raw == "complete":
        return raw
    raise ValueError("expect.worksheet.stop must be asking, handed_back, or complete")


def _parse_cell_expect(area: str, raw: Any) -> CellExpectStatus:
    if raw == "filled" or raw == "unknown" or raw == "not_yet" or raw == "i_am_decider":
        return raw
    raise ValueError(f"expect.worksheet.cells.{area} must be filled or a skip status")


def _parse_worksheet_expect(raw: dict[str, Any], smart: SmartExpect) -> WorksheetExpect | None:
    present = "worksheet" in raw
    if smart.proposal != "proposed":
        if present:
            raise ValueError("expect.worksheet is set only when smart.proposal is proposed")
        return None
    body = raw.get("worksheet")
    if not isinstance(body, dict) or set(body) != {"stop", "cells"}:
        raise ValueError("proposed expect.worksheet must be {stop, cells}")
    cells = body["cells"]
    if not isinstance(cells, dict):
        raise ValueError("expect.worksheet.cells must be a mapping of area to status")
    keys = tuple(str(area) for area in cells)
    prefix = AREAS[: len(keys)]
    if keys != prefix:
        raise ValueError(
            f"expect.worksheet.cells {list(keys)} must be a prefix of {list(AREAS)}"
        )
    parsed = tuple((area, _parse_cell_expect(area, cells[area])) for area in prefix)
    return WorksheetExpect(stop=_parse_stop(body["stop"]), cells=parsed)


def _parse_smart_expect(raw: Any) -> SmartExpect:
    if not isinstance(raw, dict) or set(raw) != {"proposal", "gaps"}:
        raise ValueError("classify expect.smart must be {proposal, gaps}")
    proposal = raw["proposal"]
    gaps = raw["gaps"]
    if proposal not in ("proposed", "withheld"):
        raise ValueError("expect.smart.proposal must be proposed or withheld")
    if not isinstance(gaps, list) or not in_card_order(gaps):
        raise ValueError("expect.smart.gaps must be distinct SMART letters in card order")
    if (proposal == "withheld") != bool(REQUIRED_TO_PROPOSE.intersection(gaps)):
        raise ValueError("expect.smart.proposal is withheld exactly when a required letter is open")
    return SmartExpect(proposal=proposal, gaps=tuple(gaps))


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
    if isinstance(parsed, ContractViolation):
        raise ValueError(f"gold does not parse: {parsed.kind} {parsed.detail}".strip())
    if isinstance(parsed, Halt):
        raise ValueError("gold does not parse: halt")
    if not isinstance(parsed, (Response, StructureResponse)):
        assert_never(parsed)
    if len(parsed.view.restatement) > PREAMBLE_BUDGET:
        raise ValueError("gold restatement over budget")
    expect = _parse_expectation(raw["expect"])
    if expect.kind == "structure" and not isinstance(parsed, StructureResponse):
        raise ValueError("structure expect requires structure gold")
    if expect.kind != "structure" and isinstance(parsed, StructureResponse):
        raise ValueError("structure gold requires expect.kind structure")
    command = _parse_command(raw)
    if expect.kind == "structure" and command != "/where-to-focus":
        raise ValueError("structure turns must set command: /where-to-focus")
    return Turn(
        input=input_text,
        expect=expect,
        tripwires=_parse_tripwires(raw.get("tripwires")),
        restatement=restatement.strip(),
        gold_text=gold_text,
        gold=parsed,
        command=command or "/whats-going-on",
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
