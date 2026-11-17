"""SMART boundary: card registry, proposal union, and the two wire keys."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any, Literal, get_args

from .manifest import SKILL_DIR
from .wire import ContractViolation, Unresolved

SmartLetter = Literal["specific", "measurable", "actionable", "relevant", "time_bound"]
SMART_LETTERS: tuple[SmartLetter, ...] = get_args(SmartLetter)
REQUIRED_TO_PROPOSE: frozenset[SmartLetter] = frozenset({"specific", "actionable"})
ASK_YOURSELF = "Ask yourself: "

_CARDS_HEADER_RE = re.compile(r"^\| Letter \| Required \| Prompt \|\n\|[-|]+\|\n", re.MULTILINE)
_CARD_ROW_RE = re.compile(r"^\| `(?P<letter>[a-z_]+)` \| (?P<required>yes|no) \| (?P<prompt>.+?) \|$")


@dataclass(frozen=True)
class Card:
    letter: SmartLetter
    required: bool
    prompt: str

    @property
    def clarification(self) -> str:
        return ASK_YOURSELF + self.prompt


def in_card_order(letters: Sequence[str]) -> bool:
    """True when letters are distinct SMART letters listed in card order."""
    if not all(letter in SMART_LETTERS for letter in letters):
        return False
    indexes = [SMART_LETTERS.index(letter) for letter in letters]
    return indexes == sorted(set(indexes))


@dataclass(frozen=True)
class NoPrimary:
    """The smart step did not run. Wire: smart_question null, smart_gaps []."""


@dataclass(frozen=True)
class Withheld:
    """A required letter is open. Wire: smart_question null."""

    gaps: tuple[SmartLetter, ...]

    def __post_init__(self) -> None:
        if not in_card_order(self.gaps):
            raise ValueError(f"Withheld gaps must be distinct and in card order: {self.gaps}")
        if not REQUIRED_TO_PROPOSE.intersection(self.gaps):
            raise ValueError(f"Withheld needs an open required letter: {self.gaps}")


@dataclass(frozen=True)
class Proposed:
    question: str
    gaps: tuple[SmartLetter, ...]

    def __post_init__(self) -> None:
        if not self.question.strip():
            raise ValueError("Proposed question must be non-empty")
        if not in_card_order(self.gaps):
            raise ValueError(f"Proposed gaps must be distinct and in card order: {self.gaps}")
        if REQUIRED_TO_PROPOSE.intersection(self.gaps):
            raise ValueError(f"Proposed with a required letter open: {self.gaps}")


SmartProposal = NoPrimary | Withheld | Proposed


def parse_cards(text: str) -> tuple[Card, ...]:
    """Read the `Letter | Required | Prompt` table. Raise ValueError when it disagrees with the letter model."""
    header = _CARDS_HEADER_RE.search(text)
    if header is None:
        raise ValueError("no SMART cards table (| Letter | Required | Prompt |)")
    rows: list[tuple[str, bool, str]] = []
    for line in text[header.end() :].splitlines():
        row = _CARD_ROW_RE.match(line)
        if row is None:
            break
        rows.append((row["letter"], row["required"] == "yes", row["prompt"]))
    letters = tuple(letter for letter, _required, _prompt in rows)
    if letters != SMART_LETTERS:
        raise ValueError(f"SMART cards list {list(letters)}, want {list(SMART_LETTERS)}")
    required = frozenset(letter for letter, is_required, _prompt in rows if is_required)
    if required != REQUIRED_TO_PROPOSE:
        raise ValueError(
            f"SMART cards mark {sorted(required)} required, want {sorted(REQUIRED_TO_PROPOSE)}"
        )
    return tuple(
        Card(letter=letter, required=is_required, prompt=prompt)
        for letter, (_name, is_required, prompt) in zip(SMART_LETTERS, rows, strict=True)
    )


@cache
def load_cards(skill_dir: Path = SKILL_DIR) -> tuple[Card, ...]:
    return parse_cards((skill_dir / "smart" / "SKILL.md").read_text(encoding="utf-8"))


def gap_letter(clarification: str) -> SmartLetter | None:
    """The letter whose `Ask yourself: <prompt>` equals the clarification exactly, else None."""
    for card in load_cards():
        if clarification == card.clarification:
            return card.letter
    return None


def partition_unresolved(
    rows: tuple[Unresolved, ...],
) -> tuple[tuple[Unresolved, ...], tuple[Unresolved, ...]]:
    """Split rows into (concerns, SMART gap rows)."""
    concerns = tuple(row for row in rows if gap_letter(row.clarification) is None)
    gaps = tuple(row for row in rows if gap_letter(row.clarification) is not None)
    return concerns, gaps


def parse_smart(
    raw: Mapping[str, Any], has_primary: bool, unresolved: tuple[Unresolved, ...]
) -> SmartProposal | ContractViolation:
    if "smart_question" not in raw or "smart_gaps" not in raw:
        return ContractViolation("smart_schema", "smart_question and smart_gaps are required")
    question = raw["smart_question"]
    if question is not None:
        if not isinstance(question, str) or not question.strip():
            return ContractViolation("smart_schema", "smart_question must be a non-empty string or null")
        question = question.strip()
    gaps_raw = raw["smart_gaps"]
    if not isinstance(gaps_raw, list) or not all(gap in SMART_LETTERS for gap in gaps_raw):
        return ContractViolation(
            "smart_schema", f"smart_gaps must be a list drawn from {list(SMART_LETTERS)}"
        )
    if len(set(gaps_raw)) != len(gaps_raw):
        return ContractViolation("smart_schema", f"smart_gaps repeats a letter: {gaps_raw}")
    gaps: tuple[SmartLetter, ...] = tuple(gaps_raw)

    row_letters = tuple(gap_letter(row.clarification) for row in unresolved)
    gap_rows = tuple(letter for letter in row_letters if letter is not None)
    for row, letter in zip(unresolved, row_letters, strict=True):
        if letter is None and row.clarification.casefold().startswith(ASK_YOURSELF.casefold().rstrip()):
            return ContractViolation(
                "smart_gap_rows", f"Ask-yourself row matches no card prompt: {row.clarification!r}"
            )

    if not has_primary:
        if question is not None or gaps or gap_rows:
            return ContractViolation(
                "smart_without_primary", "no primary, so smart_question is null and smart_gaps is []"
            )
        return NoPrimary()

    if not in_card_order(gaps):
        return ContractViolation("smart_order", f"smart_gaps {list(gaps)} not in card order")
    if len(set(gap_rows)) != len(gap_rows) or set(gap_rows) != set(gaps):
        return ContractViolation(
            "smart_gap_rows", f"smart_gaps {list(gaps)} but Ask-yourself rows {list(gap_rows)}"
        )
    if row_letters[len(row_letters) - len(gaps) :] != gaps:
        return ContractViolation(
            "smart_gap_tail", "Ask-yourself rows must close unresolved, in card order"
        )

    if question is None:
        if not REQUIRED_TO_PROPOSE.intersection(gaps):
            return ContractViolation(
                "smart_withheld_without_reason",
                f"smart_question is null but no required letter {sorted(REQUIRED_TO_PROPOSE)} is open",
            )
        return Withheld(gaps=gaps)
    if REQUIRED_TO_PROPOSE.intersection(gaps):
        return ContractViolation(
            "smart_proposed_without_required",
            f"smart_question proposed while {sorted(REQUIRED_TO_PROPOSE.intersection(gaps))} is open",
        )
    return Proposed(question=question, gaps=gaps)
