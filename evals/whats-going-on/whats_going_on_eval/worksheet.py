"""Worksheet registry. Areas, skips, stop streak, and hand-back line from the leaf.

W1 ships load_registry only. assess / parse_worksheet land in later PRs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Literal, get_args

from .manifest import SKILL_DIR
from .smart import ASK_YOURSELF

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
