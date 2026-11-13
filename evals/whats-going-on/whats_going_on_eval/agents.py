"""Host agent invocation. Stub until a non-interactive CLI is confirmed."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .manifest import HOST_SKILL_DIR, INSTALL_SKILL_DIR, agent_mount


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


def nested_leaf_rels(mount: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(rel for rel in mount if rel.endswith("/SKILL.md"))


def host_load_problems(skill_src: Path, repo_root: Path) -> list[str]:
    try:
        mount = agent_mount(skill_src)
        problems: list[str] = []
        if not nested_leaf_rels(mount):
            problems.append("derived mount has no nested leaf skills")
        problems.extend(_materialized_mount_problems(skill_src, mount))
        problems.extend(_installed_mount_problems(skill_src, repo_root, mount))
        return problems
    except (OSError, RuntimeError, ValueError) as exc:
        return [f"host_load: {exc}"]


def _materialized_mount_problems(skill_src: Path, mount: tuple[str, ...]) -> list[str]:
    workspace = materialize_skill(skill_src)
    try:
        roots = tuple(
            (f"{host} mount", workspace / rel) for host, rel in HOST_SKILL_DIR.items()
        )
        return _mount_file_problems(skill_src, roots, mount, exact=True)
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def _installed_mount_problems(
    skill_src: Path,
    repo_root: Path,
    mount: tuple[str, ...],
) -> list[str]:
    missing_hosts = [host for host in HOST_SKILL_DIR if host not in INSTALL_SKILL_DIR]
    if missing_hosts:
        return [f"install path missing for {', '.join(missing_hosts)}"]
    home = Path(tempfile.mkdtemp(prefix="wgo-install-"))
    try:
        script = repo_root / "scripts" / "install-local.sh"
        proc = subprocess.run(
            ["bash", str(script), "--host", "all"],
            cwd=repo_root,
            env={**os.environ, "HOME": str(home)},
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout).strip().splitlines()
            tail = detail[-1] if detail else "no output"
            return [f"install-local exit {proc.returncode}: {tail}"]
        roots = tuple(
            (f"{host} install", home / rel) for host, rel in INSTALL_SKILL_DIR.items()
        )
        return _mount_file_problems(skill_src, roots, mount, exact=False)
    finally:
        shutil.rmtree(home, ignore_errors=True)


def _mount_file_problems(
    skill_src: Path,
    roots: tuple[tuple[str, Path], ...],
    mount: tuple[str, ...],
    *,
    exact: bool,
) -> list[str]:
    problems: list[str] = []
    expected = set(mount)
    for label, root in roots:
        if not root.is_dir():
            problems.append(f"{label} skill dir missing")
            continue
        found = {
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file()
        }
        for rel in sorted(expected - found):
            problems.append(f"{label} missing {rel}")
        if exact:
            for rel in sorted(found - expected):
                problems.append(f"{label} includes off-mount {rel}")
        for rel in sorted(expected & found):
            if (root / rel).read_bytes() != (skill_src / rel).read_bytes():
                problems.append(f"{label} differs {rel}")
    return problems


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
