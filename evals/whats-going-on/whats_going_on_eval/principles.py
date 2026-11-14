from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, get_args

import yaml

WireKind = Literal["status", "problem", "classification", "confidence", "unresolved"]
WIRE_KINDS: tuple[WireKind, ...] = get_args(WireKind)

_SECTION_RE = re.compile(
    r"^## Principles\s*\n(?P<body>(?:.*\n)*?)(?=^## |\Z)",
    re.MULTILINE,
)
_BULLET_RE = re.compile(
    r"^- (principle-[a-z0-9]+(?:-[a-z0-9]+)*) \u2014 \S.*$"
)
_FRONTMATTER_RE = re.compile(r"^---\s*\n(?P<body>.*?)\n---\s*\n", re.DOTALL)


@dataclass(frozen=True)
class Principle:
    name: str
    description: str
    governs: frozenset[WireKind]


@dataclass(frozen=True)
class PrincipleLint:
    kind: str
    detail: str


def principle_names(skill_dir: Path) -> tuple[str, ...]:
    names, _problems = _index(skill_dir)
    return names


def load_principles(skill_dir: Path) -> tuple[Principle, ...]:
    names, _problems = _index(skill_dir)
    loaded: list[Principle] = []
    for name in names:
        principle, problems = _load_leaf(skill_dir, name)
        if principle is not None and not problems:
            loaded.append(principle)
    return tuple(loaded)


def lint_principles(skill_dir: Path) -> tuple[PrincipleLint, ...]:
    names, problems = _index(skill_dir)
    found = list(problems)
    for name in names:
        _principle, leaf_problems = _load_leaf(skill_dir, name)
        found.extend(leaf_problems)
    return tuple(found)


def _coordinator(skill_dir: Path) -> str | None:
    path = skill_dir / "SKILL.md"
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def _index(skill_dir: Path) -> tuple[tuple[str, ...], tuple[PrincipleLint, ...]]:
    text = _coordinator(skill_dir)
    if text is None:
        return (), ()
    match = _SECTION_RE.search(text)
    if not match:
        return (), ()
    names: list[str] = []
    problems: list[PrincipleLint] = []
    for raw in match.group("body").splitlines():
        line = raw.strip()
        if not line or not line.startswith("-"):
            continue
        found = _BULLET_RE.fullmatch(line)
        if not found:
            problems.append(
                PrincipleLint(
                    "principle_index",
                    f"## Principles bullet must look like '- principle-<name> — …', got {line!r}",
                )
            )
            continue
        name = found.group(1)
        if name in names:
            problems.append(
                PrincipleLint("principle_index", f"## Principles repeats {name!r}")
            )
            continue
        names.append(name)
    if not names and not problems:
        problems.append(
            PrincipleLint("principle_index", "## Principles section has no principle bullets")
        )
    return tuple(names), tuple(problems)


def _load_leaf(
    skill_dir: Path, name: str
) -> tuple[Principle | None, tuple[PrincipleLint, ...]]:
    path = skill_dir / name / "SKILL.md"
    if not path.is_file():
        return None, (
            PrincipleLint(
                "missing_leaf",
                f"principle index names {name!r} but {name}/SKILL.md is missing",
            ),
        )
    text = path.read_text(encoding="utf-8")
    problems: list[PrincipleLint] = []
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return None, (
            PrincipleLint(
                "principle_frontmatter",
                f"{name}/SKILL.md is missing frontmatter",
            ),
        )
    loaded = yaml.safe_load(match.group("body")) or {}
    if not isinstance(loaded, dict):
        return None, (
            PrincipleLint(
                "principle_frontmatter",
                f"{name}/SKILL.md frontmatter must be a mapping",
            ),
        )
    data = loaded
    if data.get("disable-model-invocation") is not True:
        problems.append(
            PrincipleLint(
                "leaf_invocation",
                f"{name}/SKILL.md must set disable-model-invocation: true",
            )
        )
    if data.get("name") != name:
        problems.append(
            PrincipleLint(
                "principle_frontmatter",
                f"{name}/SKILL.md name is {data.get('name')!r}, want {name!r}",
            )
        )
    description = data.get("description")
    if not isinstance(description, str) or not description.strip():
        problems.append(
            PrincipleLint(
                "principle_frontmatter",
                f"{name}/SKILL.md description must be a non-empty string",
            )
        )
    governs = data.get("governs")
    if (
        not isinstance(governs, list)
        or not governs
        or not all(item in WIRE_KINDS for item in governs)
    ):
        problems.append(
            PrincipleLint(
                "principle_frontmatter",
                f"{name}/SKILL.md governs must be a non-empty list drawn from {list(WIRE_KINDS)}",
            )
        )
        governs = None
    if problems or governs is None or not isinstance(description, str):
        return None, tuple(problems)
    return (
        Principle(
            name=name,
            description=description.strip(),
            governs=frozenset(governs),
        ),
        (),
    )
