"""Worksheet registry and assessment.

Areas, skips, the stop streak, and the hand-back line come from the leaf.
Cells, stop_for, and assess encode the walk. Fence parsing comes later.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Literal, assert_never, get_args

from .manifest import SKILL_DIR
from .smart import ASK_YOURSELF, NoPrimary, Proposed, SmartProposal, Withheld

AreaId = Literal["context_constraints", "success_criteria", "stakeholders", "scope_sources"]
AREAS: tuple[AreaId, ...] = get_args(AreaId)

SkipStatus = Literal["unknown", "not_yet", "i_am_decider"]
SKIP_STATUSES: tuple[SkipStatus, ...] = get_args(SkipStatus)

HAND_BACK_STREAK = 2
QUESTION_SLOT = "{question}"

_AREAS_HEADER_RE = re.compile(r"^\| Area \| Probe \|\n\|[-|]+\|\n", re.MULTILINE)
_AREA_ROW_RE = re.compile(r"^\| `(?P<area>[a-z_]+)` \| (?P<probe>.+?) \|$")
_SKIPS_HEADER_RE = re.compile(r"^\| Status \| Area \| Says \|\n\|[-|]+\|\n", re.MULTILINE)
_SKIP_ROW_RE = re.compile(
    r"^\| `(?P<status>[a-z_]+)` \| (?P<area>any|`[a-z_]+`) \| (?P<says>.+?) \|$"
)
_STOP_STREAK_RE = re.compile(
    r"also stop after (?P<n>\d+) skips in a row", re.IGNORECASE
)
_HAND_BACK_HEADER = "## Hand-back"


@dataclass(frozen=True)
class Area:
    id: AreaId
    label: str
    probe_template: str

    def probe(self, question: str) -> str:
        return self.probe_template.replace(QUESTION_SLOT, question)


@dataclass(frozen=True)
class Skip:
    status: SkipStatus
    only_at: AreaId | None
    says: str


@dataclass(frozen=True)
class Registry:
    areas: tuple[Area, ...]
    skips: tuple[Skip, ...]
    hand_back_line: str


def parse_registry(text: str) -> Registry:
    """Read Areas, Skips, Stop streak, and Hand-back from the leaf. Raise ValueError on drift."""
    areas = _parse_areas(text)
    skips = _parse_skips(text)
    _parse_stop_streak(text)
    hand_back = _parse_hand_back(text)
    return Registry(areas=areas, skips=skips, hand_back_line=hand_back)


def _parse_areas(text: str) -> tuple[Area, ...]:
    header = _AREAS_HEADER_RE.search(text)
    if header is None:
        raise ValueError("no worksheet Areas table (| Area | Probe |)")
    rows: list[tuple[str, str]] = []
    for line in text[header.end() :].splitlines():
        row = _AREA_ROW_RE.match(line)
        if row is None:
            break
        rows.append((row["area"], row["probe"]))
    ids = tuple(area for area, _probe in rows)
    if ids != AREAS:
        raise ValueError(f"worksheet areas list {list(ids)}, want {list(AREAS)}")
    areas: list[Area] = []
    labels: set[str] = set()
    for area_id, probe in rows:
        if QUESTION_SLOT not in probe:
            raise ValueError(f"probe for {area_id} lacks {QUESTION_SLOT}")
        if probe.count(QUESTION_SLOT) != 1:
            raise ValueError(f"probe for {area_id} must contain {QUESTION_SLOT} once")
        if probe.startswith(ASK_YOURSELF):
            raise ValueError(f"probe for {area_id} collides with SMART Ask yourself prefix")
        if ": " not in probe:
            raise ValueError(f"probe for {area_id} needs a label before ': '")
        label, _rest = probe.split(": ", 1)
        if not label.strip():
            raise ValueError(f"probe for {area_id} has an empty label")
        if label in labels:
            raise ValueError(f"duplicate probe label {label!r}")
        labels.add(label)
        areas.append(Area(id=area_id, label=label, probe_template=probe))  # type: ignore[arg-type]
    return tuple(areas)


def _parse_skips(text: str) -> tuple[Skip, ...]:
    header = _SKIPS_HEADER_RE.search(text)
    if header is None:
        raise ValueError("no worksheet Skips table (| Status | Area | Says |)")
    rows: list[Skip] = []
    statuses: list[str] = []
    for line in text[header.end() :].splitlines():
        row = _SKIP_ROW_RE.match(line)
        if row is None:
            break
        status = row["status"]
        statuses.append(status)
        area_cell = row["area"]
        only_at: AreaId | None
        if area_cell == "any":
            only_at = None
        else:
            area_id = area_cell.strip("`")
            if area_id not in AREAS:
                raise ValueError(f"skip only_at unknown area {area_id!r}")
            only_at = area_id  # type: ignore[assignment]
        says = row["says"].strip()
        if not says:
            raise ValueError(f"skip {status} has empty Says")
        if status not in SKIP_STATUSES:
            raise ValueError(f"unknown skip status {status!r}")
        rows.append(Skip(status=status, only_at=only_at, says=says))  # type: ignore[arg-type]
    if tuple(statuses) != SKIP_STATUSES:
        raise ValueError(f"worksheet skips list {statuses}, want {list(SKIP_STATUSES)}")
    return tuple(rows)


def _parse_stop_streak(text: str) -> None:
    match = _STOP_STREAK_RE.search(text)
    if match is None:
        raise ValueError("## Stop must state 'also stop after N skips in a row'")
    n = int(match["n"])
    if n != HAND_BACK_STREAK:
        raise ValueError(f"Stop streak {n}, want {HAND_BACK_STREAK}")


def _parse_hand_back(text: str) -> str:
    idx = text.find(_HAND_BACK_HEADER)
    if idx < 0:
        raise ValueError("missing ## Hand-back section")
    body = text[idx + len(_HAND_BACK_HEADER) :].lstrip("\n")
    lines: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            break
        if line.strip():
            lines.append(line.strip())
    if not lines:
        raise ValueError("## Hand-back has no sentence")
    hand_back = " ".join(lines)
    if hand_back.startswith(ASK_YOURSELF):
        raise ValueError("hand-back line must not start with Ask yourself: ")
    return hand_back


@cache
def load_registry(skill_dir: Path = SKILL_DIR) -> Registry:
    return parse_registry((skill_dir / "worksheet" / "SKILL.md").read_text(encoding="utf-8"))


def _collapse_casefold(text: str) -> str:
    return " ".join(text.split()).casefold()


@dataclass(frozen=True)
class Filled:
    area: AreaId
    text: str

    def __post_init__(self) -> None:
        if self.area not in AREAS:
            raise ValueError(f"unknown worksheet area {self.area!r}")
        if not self.text.strip():
            raise ValueError(f"{self.area} text is blank")
        normalized = _collapse_casefold(self.text)
        for skip in load_registry().skips:
            if normalized == _collapse_casefold(skip.says):
                raise ValueError(f"{self.area} text is a skip phrase")


@dataclass(frozen=True)
class Skipped:
    area: AreaId
    status: SkipStatus

    def __post_init__(self) -> None:
        if self.area not in AREAS:
            raise ValueError(f"unknown worksheet area {self.area!r}")
        if self.status not in SKIP_STATUSES:
            raise ValueError(f"unknown skip status {self.status!r}")
        for skip in load_registry().skips:
            if skip.status != self.status:
                continue
            if skip.only_at is not None and skip.only_at != self.area:
                raise ValueError(
                    f"skip {self.status} is only allowed on {skip.only_at}, not {self.area}"
                )
            return
        raise ValueError(f"skip status {self.status} is not in the registry")


Cell = Filled | Skipped


def _check_prefix(cells: tuple[Cell, ...]) -> None:
    if len(cells) > len(AREAS):
        raise ValueError(f"worksheet has {len(cells)} cells, want at most {len(AREAS)}")
    for index, cell in enumerate(cells):
        want = AREAS[index]
        if cell.area != want:
            raise ValueError(f"worksheet cell {index} is {cell.area}, want {want}")


@dataclass(frozen=True)
class NotStarted:
    """No proposed question. The wire sheet is null and there is no probe row."""


@dataclass(frozen=True)
class Asking:
    """A prefix of areas, with one probe still to ask."""

    cells: tuple[Cell, ...]
    question: str
    gaps_open: bool

    def __post_init__(self) -> None:
        if not self.question.strip():
            raise ValueError("Asking question must be non-empty")
        _check_prefix(self.cells)
        got = stop_for(self.cells, self.gaps_open)
        if got != "asking":
            raise ValueError(f"Asking requires stop asking, got {got}")

    @property
    def next_area(self) -> AreaId:
        return AREAS[len(self.cells)]

    @property
    def probe(self) -> str:
        return load_registry().areas[len(self.cells)].probe(self.question)


@dataclass(frozen=True)
class HandedBack:
    """Gaps are open and the last HAND_BACK_STREAK cells are skips."""

    cells: tuple[Cell, ...]

    def __post_init__(self) -> None:
        _check_prefix(self.cells)
        got = stop_for(self.cells, True)
        if got != "handed_back":
            raise ValueError(f"HandedBack requires stop handed_back, got {got}")

    @property
    def hand_back_line(self) -> str:
        return load_registry().hand_back_line


@dataclass(frozen=True)
class Complete:
    """Every area is filled or skipped."""

    cells: tuple[Cell, ...]

    def __post_init__(self) -> None:
        _check_prefix(self.cells)
        got = stop_for(self.cells, False)
        if got != "complete":
            raise ValueError(f"Complete requires stop complete, got {got}")


WorksheetAssessment = NotStarted | Asking | HandedBack | Complete
Stop = Literal["asking", "handed_back", "complete"]


def stop_for(cells: tuple[Cell, ...], gaps_open: bool) -> Stop:
    """The one stop rule. A full sheet is complete even when gaps stay open.

    A skip streak stops the walk only while gaps are open. Constructors check area order.
    """
    if len(cells) == len(AREAS):
        return "complete"
    if gaps_open and len(cells) >= HAND_BACK_STREAK:
        tail = cells[-HAND_BACK_STREAK:]
        if all(isinstance(cell, Skipped) for cell in tail):
            return "handed_back"
    return "asking"


def assess(proposal: SmartProposal, cells: tuple[Cell, ...]) -> WorksheetAssessment:
    match proposal:
        case NoPrimary() | Withheld():
            if cells:
                raise ValueError("worksheet cells require a proposed question")
            return NotStarted()
        case Proposed() as proposed:
            gaps_open = bool(proposed.gaps)
            match stop_for(cells, gaps_open):
                case "complete":
                    return Complete(cells)
                case "handed_back":
                    return HandedBack(cells)
                case "asking":
                    return Asking(cells, proposed.question, gaps_open)
                case _ as unreachable:
                    assert_never(unreachable)
        case _ as unreachable:
            assert_never(unreachable)
