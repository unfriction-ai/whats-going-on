"""Mount allowlist, suite version, and host skill paths."""

from __future__ import annotations

import hashlib
from pathlib import Path

SUITE_VERSION = 1

# Files that may exist under skills/whats-going-on/ in the repo.
SKILL_ROOT_ALLOWED = frozenset(
    {
        "README.md",
        "SKILL.md",
        "design",
    }
)

# Strict subset copied into measured eval workspaces. README stays off that disk.
AGENT_MOUNT: tuple[str, ...] = ("SKILL.md",)

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

assert "README.md" not in AGENT_MOUNT
assert set(AGENT_MOUNT) <= {"README.md", "SKILL.md"} | set(AGENT_MOUNT)


def skill_view_hash(skill_dir: Path) -> str:
    h = hashlib.sha256()
    for rel in AGENT_MOUNT:
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
