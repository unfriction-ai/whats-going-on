"""Wire types shared by the verdict parser and the SMART boundary."""

from __future__ import annotations

from dataclasses import dataclass

PREAMBLE_BUDGET = 400


@dataclass(frozen=True)
class ContractViolation:
    kind: str
    detail: str = ""


@dataclass(frozen=True)
class Unresolved:
    observation: str
    reason: str
    clarification: str


def ask_slot(row_count: int, gap_count: int) -> int:
    """Index of the one operator-ask row, after concerns and before the gap tail."""
    return row_count - gap_count - 1
