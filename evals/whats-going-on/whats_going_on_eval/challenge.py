"""Challenge bias registry and the idle or clear wire."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any, Literal, assert_never, get_args

from .manifest import SKILL_DIR
from .smart import ASK_YOURSELF
from .wire import ContractViolation
from .worksheet import Complete, WorksheetAssessment, ask_row, load_registry as load_sheet_registry

BiasId = Literal["anchoring", "confirmation_bias", "sunk_cost", "groupthink"]
BIASES: tuple[BiasId, ...] = get_args(BiasId)

Move = Literal["drop_span", "restore_span", "name_missing_party"]
MOVES: tuple[Move, ...] = get_args(Move)

LABEL = "Challenge: "
QUOTE_SLOT = "{quote}"
QUOTE_BUDGET = 160

_BIASES_HEADER_RE = re.compile(
    r"^\| Bias \| Move \| Symptom in the paste \| Other side \|\n\|[-|]+\|\n",
    re.MULTILINE,
)
_BIAS_ROW_RE = re.compile(
    r"^\| `(?P<bias>[a-z_]+)` \| `(?P<move>[a-z_]+)` \| (?P<symptom>.+?) \| (?P<template>.+?) \|$"
)
_QUOTE_HEADER = "## Quote"
_REPLY_HEADER = "## Reply"
_BUDGET_RE = re.compile(r"at most (?P<n>\d+) characters", re.IGNORECASE)


@dataclass(frozen=True)
class Bias:
    id: BiasId
    move: Move
    symptom: str
    other_side_template: str

    def other_side(self, quote: str) -> str:
        return self.other_side_template.replace(QUOTE_SLOT, quote)


@dataclass(frozen=True)
class Registry:
    biases: tuple[Bias, ...]
    reply_line: str
    quote_budget: int


def parse_registry(text: str) -> Registry:
    """Read Biases, Quote, and Reply from the leaf. Raise ValueError on drift."""
    biases = _parse_biases(text)
    budget = _parse_quote_budget(text)
    reply = _parse_reply(text)
    _check_cross_registry(biases)
    return Registry(biases=biases, reply_line=reply, quote_budget=budget)


def _parse_biases(text: str) -> tuple[Bias, ...]:
    header = _BIASES_HEADER_RE.search(text)
    if header is None:
        raise ValueError(
            "no challenge Biases table (| Bias | Move | Symptom in the paste | Other side |)"
        )
    rows: list[Bias] = []
    ids: list[str] = []
    for line in text[header.end() :].splitlines():
        row = _BIAS_ROW_RE.match(line)
        if row is None:
            break
        bias_id = row["bias"]
        move = row["move"]
        symptom = row["symptom"].strip()
        template = row["template"].strip()
        ids.append(bias_id)
        if bias_id not in BIASES:
            raise ValueError(f"unknown challenge bias {bias_id!r}")
        if move not in MOVES:
            raise ValueError(f"unknown challenge move {move!r}")
        if not symptom:
            raise ValueError(f"bias {bias_id} has empty symptom")
        if template.count(QUOTE_SLOT) != 1:
            raise ValueError(f"bias {bias_id} Other side must contain {QUOTE_SLOT} once")
        if template.startswith(ASK_YOURSELF):
            raise ValueError(f"bias {bias_id} Other side collides with Ask yourself prefix")
        if template.startswith(LABEL):
            raise ValueError(f"bias {bias_id} Other side collides with Challenge label")
        rows.append(
            Bias(
                id=bias_id,  # type: ignore[arg-type]
                move=move,  # type: ignore[arg-type]
                symptom=symptom,
                other_side_template=template,
            )
        )
    if tuple(ids) != BIASES:
        raise ValueError(f"challenge biases list {ids}, want {list(BIASES)}")
    return tuple(rows)


def _parse_quote_budget(text: str) -> int:
    idx = text.find(_QUOTE_HEADER)
    if idx < 0:
        raise ValueError("missing ## Quote section")
    body = text[idx + len(_QUOTE_HEADER) :]
    next_header = body.find("\n## ")
    section = body if next_header < 0 else body[:next_header]
    match = _BUDGET_RE.search(section)
    if match is None:
        raise ValueError("## Quote must state 'at most N characters'")
    n = int(match["n"])
    if n != QUOTE_BUDGET:
        raise ValueError(f"Quote budget {n}, want {QUOTE_BUDGET}")
    return n


def _parse_reply(text: str) -> str:
    idx = text.find(_REPLY_HEADER)
    if idx < 0:
        raise ValueError("missing ## Reply section")
    body = text[idx + len(_REPLY_HEADER) :].lstrip("\n")
    lines: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            break
        if line.strip():
            lines.append(line.strip())
    if not lines:
        raise ValueError("## Reply has no sentence")
    reply = " ".join(lines)
    if reply.startswith(ASK_YOURSELF):
        raise ValueError("reply line must not start with Ask yourself: ")
    if reply.startswith(LABEL):
        raise ValueError("reply line must not start with Challenge: ")
    return reply


def _check_cross_registry(biases: tuple[Bias, ...]) -> None:
    sheet = load_sheet_registry()
    labels = {area.label for area in sheet.areas}
    challenge_label = LABEL.rstrip(": ")
    if challenge_label in labels:
        raise ValueError(f"Challenge label {challenge_label!r} collides with a worksheet area label")
    for bias in biases:
        before_colon = bias.other_side_template.split(": ", 1)[0]
        if before_colon in labels:
            raise ValueError(
                f"bias {bias.id} Other side label {before_colon!r} collides with a worksheet area"
            )


@cache
def load_registry(skill_dir: Path = SKILL_DIR) -> Registry:
    return parse_registry((skill_dir / "challenge" / "SKILL.md").read_text(encoding="utf-8"))


@dataclass(frozen=True)
class NotRun:
    """The sheet is not complete, so the wire value is null."""


@dataclass(frozen=True)
class Clear:
    """The sheet is complete and the round found nothing."""


ChallengeAssessment = NotRun | Clear

_CLEAR_KEYS = frozenset({"round", "findings", "reply"})
_REJECTED_ROUNDS = frozenset({"open", "answered"})


def operator_ask(sheet: WorksheetAssessment, challenge: ChallengeAssessment) -> str | None:
    """Clarification of the one operator-ask row, if any."""
    match challenge:
        case NotRun() | Clear():
            return ask_row(sheet)
        case _ as unreachable:
            assert_never(unreachable)


def parse_challenge(
    raw: Mapping[str, Any],
    sheet: WorksheetAssessment,
) -> ChallengeAssessment | ContractViolation:
    if "challenge" not in raw:
        return ContractViolation("challenge_schema", "challenge is required")
    value = raw["challenge"]
    complete = isinstance(sheet, Complete)
    if value is None:
        if complete:
            return ContractViolation(
                "challenge_null_when_complete",
                "worksheet is complete, so challenge is the clear round",
            )
        return NotRun()
    if not isinstance(value, dict):
        return ContractViolation("challenge_schema", "challenge must be null or a mapping")
    round_name = value.get("round")
    if round_name in _REJECTED_ROUNDS:
        return ContractViolation("challenge_round", f"round {round_name} is rejected")
    if set(value) != _CLEAR_KEYS:
        return ContractViolation("challenge_schema", "challenge keys must be round, findings, reply")
    if round_name != "clear":
        return ContractViolation("challenge_schema", "round must be clear")
    if not complete:
        return ContractViolation(
            "challenge_before_complete",
            "challenge is clear only when the worksheet is complete",
        )
    if value["findings"] != {}:
        return ContractViolation("challenge_schema", "clear findings must be empty")
    if value["reply"] is not None:
        return ContractViolation("challenge_schema", "clear reply must be null")
    return Clear()
