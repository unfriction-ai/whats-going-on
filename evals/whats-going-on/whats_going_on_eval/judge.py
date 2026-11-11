"""Optional evidence-axis judge. Stub for live calls; parse stored judgments."""

from __future__ import annotations

import json
from typing import Any

from .grade import Judgment


def parse_judgment(raw: str | dict[str, Any]) -> Judgment:
    data = json.loads(raw) if isinstance(raw, str) else raw
    evidence = int(data["evidence"])
    if evidence not in (0, 1, 2):
        raise ValueError("evidence must be 0, 1, or 2")
    return Judgment(
        evidence=evidence,
        notes=str(data.get("notes") or ""),
        suspected_hard_fail=data.get("suspected_hard_fail"),
    )


def judge_evidence(*, input_text: str, response_text: str) -> Judgment:
    raise NotImplementedError(
        "live evidence judge is not wired; pass stored judgments or omit --judge"
    )
