"""Wire types shared by the verdict parser and the SMART boundary."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContractViolation:
    kind: str
    detail: str = ""


@dataclass(frozen=True)
class Unresolved:
    observation: str
    reason: str
    clarification: str
