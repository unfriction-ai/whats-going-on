"""Host agent invocation. Stub until a non-interactive CLI is confirmed."""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .manifest import HOST_SKILL_DIR, agent_mount


@dataclass(frozen=True)
class InvokeResult:
    text: str
    workspace: Path


class HostNotWired(RuntimeError):
    """Raised when the operator asks for a live agent run before CLIs are wired."""


def materialize_skill(skill_src: Path | None) -> Path:
    workspace = Path(tempfile.mkdtemp(prefix="wgo-eval-"))
    mount = agent_mount(skill_src) if skill_src is not None else ()
    for rel in HOST_SKILL_DIR.values():
        dest = workspace / rel
        dest.mkdir(parents=True, exist_ok=True)
        if skill_src is None:
            continue
        for name in mount:
            src = skill_src / name
            out = dest / name
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, out)
    return workspace


def build_prompt(user_input: str) -> str:
    return f"/whats-going-on\n\n{user_input.strip()}\n"


def invoke(
    *,
    agent: str,
    user_input: str,
    skill_src: Path | None,
    session_workspace: Path | None = None,
) -> InvokeResult:
    if agent not in HOST_SKILL_DIR:
        raise ValueError(f"unknown agent {agent!r}; choose from {sorted(HOST_SKILL_DIR)}")
    workspace = session_workspace or materialize_skill(skill_src)
    prompt = build_prompt(user_input)
    raise HostNotWired(
        f"live invoke for host {agent!r} is not wired yet. "
        f"Workspace prepared at {workspace} with prompt length {len(prompt)}. "
        "Use `check`, `grade`, or `--replay` until a host CLI is confirmed."
    )
