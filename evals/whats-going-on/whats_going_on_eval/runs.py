"""Append-only run artifacts under reports/."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .manifest import REPORTS_DIR, SUITE_VERSION, skill_view_hash


def new_run_id(agent: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    return f"{stamp}-{agent}-{skill_view_hash()}"


def run_dir(run_id: str) -> Path:
    path = REPORTS_DIR / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_manifest(run_id: str, payload: dict[str, Any]) -> Path:
    path = run_dir(run_id) / "manifest.json"
    payload = {
        **payload,
        "suite_version": SUITE_VERSION,
        "skill_view_hash": skill_view_hash(),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n")
    return path


def write_transcript(
    run_id: str,
    fixture_id: str,
    repetition: int,
    turn: int,
    *,
    prompt: str,
    response: str,
) -> Path:
    path = run_dir(run_id) / "transcripts" / f"{fixture_id}__r{repetition}__t{turn}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return path  # idempotent: do not overwrite
    path.write_text(
        json.dumps(
            {
                "fixture_id": fixture_id,
                "repetition": repetition,
                "turn": turn,
                "prompt": prompt,
                "response": response,
            },
            indent=2,
        )
        + "\n"
    )
    return path


def write_report(run_id: str, report: dict[str, Any]) -> Path:
    path = run_dir(run_id) / "report.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    return path


def load_report(run_id: str) -> dict[str, Any]:
    return json.loads((run_dir(run_id) / "report.json").read_text())


def write_blind_compare(run_a: str, run_b: str) -> Path:
    """Export an X/Y packet for the poteto-mode eval playbook."""
    a = load_report(run_a)
    b = load_report(run_b)
    packet = {
        "X": {"run_id": run_a, "report": a},
        "Y": {"run_id": run_b, "report": b},
        "note": "Labels X/Y are blind. Do not reveal which skill revision is which.",
    }
    out = REPORTS_DIR / f"compare-{run_a}-vs-{run_b}-blind.json"
    out.write_text(json.dumps(packet, indent=2) + "\n")
    return out


def result_to_dict(obj: Any) -> Any:
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    return obj
