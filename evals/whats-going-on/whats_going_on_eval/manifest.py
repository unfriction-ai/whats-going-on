"""Mount allowlist, suite version, and host skill paths."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .chain import derive_mount, lint_chain, load_chain

SUITE_VERSION = 1

# Files that may exist under skills/whats-going-on/ in the repo.
SKILL_ROOT_ALLOWED = frozenset(
    {
        "README.md",
        "SKILL.md",
        "design",
        "playbooks",
    }
)

HOST_SKILL_DIR = {
    "cursor": ".cursor/skills/whats-going-on",
    "claude": ".claude/skills/whats-going-on",
    "codex": ".codex/skills/whats-going-on",
}

AGENTS = tuple(HOST_SKILL_DIR.keys())

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = REPO_ROOT / "skills" / "whats-going-on"
EVAL_DIR = REPO_ROOT / "evals" / "whats-going-on"
FIXTURES_DIR = EVAL_DIR / "fixtures"
SCHEMA_CASES_DIR = EVAL_DIR / "schema_cases"
RESTATEMENT_CASES_DIR = EVAL_DIR / "restatement_cases"
REPORTS_DIR = EVAL_DIR / "reports"
RUBRIC_PATH = EVAL_DIR / "rubric.md"


def agent_mount(skill_dir: Path | None = None) -> tuple[str, ...]:
    """Measured mount, derived from the chain. Never includes README.md."""

    root = skill_dir or SKILL_DIR
    mount = derive_mount(load_chain(root))
    if "README.md" in mount:
        raise RuntimeError("README.md must not be in the derived mount")
    return mount


def skill_view_hash(skill_dir: Path) -> str:
    h = hashlib.sha256()
    for rel in agent_mount(skill_dir):
        data = (skill_dir / rel).read_bytes()
        h.update(rel.encode())
        h.update(b"\0")
        h.update(data)
        h.update(b"\0")
    return h.hexdigest()[:12]


def hash_skill_source(skill_src: Path | None) -> str:
    if skill_src is None:
        return hashlib.sha256(b"skill:none").hexdigest()[:12]
    return skill_view_hash(skill_src)


def assert_skill_tree_clean(skill_dir: Path | None = None) -> None:
    root = skill_dir or SKILL_DIR
    unexpected: list[str] = []
    for path in root.iterdir():
        name = path.name
        if name.startswith("."):
            continue
        if name not in SKILL_ROOT_ALLOWED:
            unexpected.append(name)
    if unexpected:
        raise RuntimeError(
            f"skill directory has unexpected files (answer-key contamination risk): {unexpected}"
        )


def assert_chain_ok(skill_dir: Path | None = None) -> None:
    root = skill_dir or SKILL_DIR
    problems = lint_chain(load_chain(root))
    if problems:
        detail = "; ".join(f"{p.kind}: {p.detail}" for p in problems)
        raise RuntimeError(f"chain lint failed: {detail}")
