"""Challenge bias registry and the idle, clear, open, or answered wire."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any, Literal, assert_never, get_args

from .manifest import SKILL_DIR
from .smart import ASK_YOURSELF
from .wire import ContractViolation, Unresolved, ask_slot
from .worksheet import (
    QUESTION_SLOT,
    Complete,
    WorksheetAssessment,
    ask_row,
    load_registry as load_sheet_registry,
)

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
class Finding:
    bias: BiasId
    quote: str

    def __post_init__(self) -> None:
        if self.bias not in BIASES:
            raise ValueError(f"unknown bias {self.bias}")
        if not self.quote or self.quote != self.quote.strip() or "\n" in self.quote:
            raise ValueError("quote must be one non-empty line")
        if len(self.quote) > QUOTE_BUDGET:
            raise ValueError(f"quote is {len(self.quote)} characters, max {QUOTE_BUDGET}")
        if self.quote.startswith(LABEL) or self.quote.startswith(ASK_YOURSELF):
            raise ValueError("quote must not start with a probe or Challenge label")


def _check_findings(findings: tuple[Finding, ...]) -> None:
    indexes = [BIASES.index(finding.bias) for finding in findings]
    if indexes != sorted(set(indexes)):
        raise ValueError("findings must be distinct and in table order")
    norms = [" ".join(finding.quote.split()) for finding in findings]
    if len(set(norms)) != len(norms):
        raise ValueError("findings quotes must be distinct")


@dataclass(frozen=True)
class NotRun:
    """The sheet is not complete, so the wire value is null."""


@dataclass(frozen=True)
class Clear:
    """The sheet is complete and the round found nothing."""


@dataclass(frozen=True)
class Open:
    """Findings are in, and the paste has not consumed the round."""

    findings: tuple[Finding, ...]

    def __post_init__(self) -> None:
        if not self.findings:
            raise ValueError("open needs a finding")
        _check_findings(self.findings)

    @property
    def line(self) -> str:
        return render_line(self.findings)


@dataclass(frozen=True)
class Answered:
    """A pasted Challenge line consumed the round. It does not open again."""

    findings: tuple[Finding, ...]
    reply: str | None

    def __post_init__(self) -> None:
        if not self.findings:
            raise ValueError("answered needs a finding")
        _check_findings(self.findings)
        if self.reply is not None and (not self.reply.strip() or "\n" in self.reply):
            raise ValueError("reply must be one non-empty line or null")


ChallengeAssessment = NotRun | Clear | Open | Answered

_ROUND_KEYS = frozenset({"round", "findings", "reply"})
_ROUNDS = frozenset({"clear", "open", "answered"})


def render_line(findings: tuple[Finding, ...]) -> str:
    """The one Challenge line for these findings."""
    registry = load_registry()
    by_id = {bias.id: bias for bias in registry.biases}
    sides = tuple(by_id[finding.bias].other_side(finding.quote) for finding in findings)
    return " ".join((LABEL.strip(), *sides, registry.reply_line))


def operator_ask(sheet: WorksheetAssessment, challenge: ChallengeAssessment) -> str | None:
    """Clarification of the one operator-ask row, if any."""
    match challenge:
        case Open() as opened:
            if ask_row(sheet) is not None:
                raise AssertionError("open challenge and a worksheet ask both claim the slot")
            return opened.line
        case NotRun() | Clear() | Answered():
            return ask_row(sheet)
        case _ as unreachable:
            assert_never(unreachable)


def _move_holds(move: Move, quote: str, primary: str | None) -> bool:
    match move:
        case "drop_span":
            return primary is not None and quote in primary
        case "restore_span":
            return primary is not None and quote not in primary
        case "name_missing_party":
            return True
        case _ as unreachable:
            assert_never(unreachable)


def _dual_label(findings: tuple[Finding, ...]) -> str | None:
    norms = [" ".join(finding.quote.split()) for finding in findings]
    for earlier in range(len(findings)):
        for later in range(earlier + 1, len(findings)):
            left, right = norms[earlier], norms[later]
            if left in right or right in left:
                return f"{findings[later].bias} quote overlaps {findings[earlier].bias}"
    return None


def _parse_findings(
    raw: Any, primary: str | None
) -> tuple[Finding, ...] | ContractViolation:
    if not isinstance(raw, dict):
        return ContractViolation("challenge_schema", "findings must be a mapping")
    ids = tuple(raw)
    if any(not isinstance(bias_id, str) or bias_id not in BIASES for bias_id in ids):
        return ContractViolation("challenge_schema", "findings name an unknown bias")
    indexes = [BIASES.index(bias_id) for bias_id in ids]
    if indexes != sorted(indexes):
        return ContractViolation(
            "challenge_order", f"findings {list(ids)} are not in table order"
        )
    by_id = {bias.id: bias for bias in load_registry().biases}
    findings: list[Finding] = []
    for bias_id, quote in raw.items():
        if not isinstance(quote, str):
            return ContractViolation("challenge_schema", f"findings.{bias_id} must be a string")
        try:
            finding = Finding(bias_id, quote.strip())  # type: ignore[arg-type]
        except ValueError as exc:
            return ContractViolation("challenge_quote", str(exc))
        if not _move_holds(by_id[finding.bias].move, finding.quote, primary):
            return ContractViolation(
                "challenge_move",
                f"{finding.bias} quote fails {by_id[finding.bias].move} against the primary",
            )
        findings.append(finding)
    overlap = _dual_label(tuple(findings))
    if overlap is not None:
        return ContractViolation("challenge_dual", overlap)
    return tuple(findings)


def _label_rows(unresolved: tuple[Unresolved, ...]) -> list[int]:
    return [i for i, row in enumerate(unresolved) if row.clarification.startswith(LABEL)]


def _reject_label_rows(
    unresolved: tuple[Unresolved, ...], state: str
) -> ContractViolation | None:
    rows = _label_rows(unresolved)
    if not rows:
        return None
    return ContractViolation(
        "challenge_rows", f"unresolved[{rows[0]}] is a Challenge row while {state}"
    )


def _check_open_row(
    unresolved: tuple[Unresolved, ...], gap_count: int, line: str
) -> ContractViolation | None:
    rows = _label_rows(unresolved)
    if len(rows) != 1 or unresolved[rows[0]].clarification != line:
        return ContractViolation(
            "challenge_rows",
            "open needs one Challenge row equal to the rendered line",
        )
    place = ask_slot(len(unresolved), gap_count)
    if rows[0] != place:
        return ContractViolation(
            "challenge_place",
            f"unresolved[{rows[0]}] is the Challenge row, want unresolved[{place}]",
        )
    return None


def parse_challenge(
    raw: Mapping[str, Any],
    sheet: WorksheetAssessment,
    unresolved: tuple[Unresolved, ...],
    gap_count: int,
    primary: str | None,
) -> ChallengeAssessment | ContractViolation:
    if "challenge" not in raw:
        return ContractViolation("challenge_schema", "challenge is required")
    value = raw["challenge"]
    complete = isinstance(sheet, Complete)
    if value is None:
        if complete:
            return ContractViolation(
                "challenge_null_when_complete",
                "worksheet is complete, so challenge is a round",
            )
        return _reject_label_rows(unresolved, "NotRun") or NotRun()
    if not isinstance(value, dict):
        return ContractViolation("challenge_schema", "challenge must be null or a mapping")
    if not complete:
        return ContractViolation(
            "challenge_before_complete",
            "challenge is a round only when the worksheet is complete",
        )
    if set(value) != _ROUND_KEYS:
        return ContractViolation("challenge_schema", "challenge keys must be round, findings, reply")
    round_name = value.get("round")
    if round_name not in _ROUNDS:
        return ContractViolation("challenge_schema", "round must be clear, open, or answered")
    findings = _parse_findings(value.get("findings"), primary)
    if isinstance(findings, ContractViolation):
        return findings
    reply = value.get("reply")
    if round_name == "clear":
        if findings or reply is not None:
            return ContractViolation(
                "challenge_round", "clear findings must be empty and reply null"
            )
        return _reject_label_rows(unresolved, "Clear") or Clear()
    if not findings:
        return ContractViolation("challenge_round", f"{round_name} needs at least one finding")
    if round_name == "open":
        if reply is not None:
            return ContractViolation("challenge_round", "open reply must be null")
        try:
            opened = Open(findings)
        except ValueError as exc:
            return ContractViolation("challenge_schema", str(exc))
        return _check_open_row(unresolved, gap_count, opened.line) or opened
    if reply is not None:
        if not isinstance(reply, str):
            return ContractViolation(
                "challenge_schema", "answered reply must be a string or null"
            )
        reply = reply.strip()
    try:
        answered = Answered(findings, reply)
    except ValueError as exc:
        return ContractViolation("challenge_quote", str(exc))
    return _reject_label_rows(unresolved, "Answered") or answered


def _normalize_ws(text: str) -> str:
    return " ".join(text.split())


def _is_harness_line(line: str) -> bool:
    if line.startswith(LABEL) or line.startswith(ASK_YOURSELF):
        return True
    if line == load_sheet_registry().hand_back_line:
        return True
    for area in load_sheet_registry().areas:
        head, tail = area.probe_template.split(QUESTION_SLOT)
        if line.startswith(head) and line.endswith(tail) and len(line) > len(head) + len(tail):
            return True
    return False


def _paste_haystack(turn_input: str) -> str:
    kept = [line.strip() for line in turn_input.splitlines() if not _is_harness_line(line.strip())]
    return _normalize_ws("\n".join(kept))


def ungrounded_findings(
    challenge: ChallengeAssessment, turn_input: str
) -> tuple[BiasId, ...]:
    """Biases whose quote is absent from the paste once harness lines are removed."""
    match challenge:
        case Open(findings=findings) | Answered(findings=findings):
            haystack = _paste_haystack(turn_input)
            return tuple(
                finding.bias
                for finding in findings
                if _normalize_ws(finding.quote) not in haystack
            )
        case NotRun() | Clear():
            return ()
        case _ as unreachable:
            assert_never(unreachable)


def restated_line(challenge: ChallengeAssessment, turn_input: str) -> bool | None:
    """True when an answered round's pasted Challenge line matches the findings."""
    match challenge:
        case Answered(findings=findings):
            want = render_line(findings)
            found = [
                line.strip()
                for line in turn_input.splitlines()
                if line.strip().startswith(LABEL)
            ]
            return len(found) == 1 and found[0] == want
        case NotRun() | Clear() | Open():
            return None
        case _ as unreachable:
            assert_never(unreachable)


def challenge_prose(challenge: ChallengeAssessment) -> tuple[str, ...]:
    """Strings the solve-leak scan reads. Quotes and the reply stay in the paste."""
    match challenge:
        case Open() as opened:
            return (opened.line,)
        case NotRun() | Clear() | Answered():
            return ()
        case _ as unreachable:
            assert_never(unreachable)
