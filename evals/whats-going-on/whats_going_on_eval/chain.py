from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

CHAIN_SECTION_RE = re.compile(
    r"^## Chain\s*\n(?P<body>(?:.*\n)*?)(?=^## |\Z)",
    re.MULTILINE,
)
CHAIN_ITEM_RE = re.compile(r"^\d+\.\s+([a-z0-9-]+)\s*$", re.MULTILINE)
FRONTMATTER_RE = re.compile(r"^---\s*\n(?P<body>.*?)\n---\s*\n", re.DOTALL)

ChainMode = Literal["monolith", "playbooks"]


@dataclass(frozen=True)
class MonolithStage:
    name: Literal["define-the-problem"] = "define-the-problem"
    produces: Literal["problem_map"] = "problem_map"


@dataclass(frozen=True)
class ShippedStage:
    name: str
    playbook_rel: str
    skills: tuple[str, ...]
    consumes: str | None
    produces: str


@dataclass(frozen=True)
class UnshippedStage:
    name: str


Stage = MonolithStage | ShippedStage | UnshippedStage


@dataclass(frozen=True)
class Chain:
    skill_dir: Path
    stages: tuple[Stage, ...]
    mode: ChainMode


@dataclass(frozen=True)
class ChainProblem:
    kind: str
    detail: str


def load_chain(skill_dir: Path) -> Chain:
    playbooks = skill_dir / "playbooks"
    shipped = sorted(playbooks.glob("*.md")) if playbooks.is_dir() else []
    if not shipped:
        return Chain(
            skill_dir=skill_dir,
            mode="monolith",
            stages=(MonolithStage(),),
        )

    coordinator = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    order = _parse_chain_order(coordinator)
    by_stem = {path.stem: path for path in shipped}
    stages: list[Stage] = []
    for name in order:
        path = by_stem.get(name)
        if path is None:
            stages.append(UnshippedStage(name=name))
            continue
        meta = _parse_playbook_frontmatter(path)
        stages.append(
            ShippedStage(
                name=name,
                playbook_rel=f"playbooks/{path.name}",
                skills=tuple(meta.get("skills") or ()),
                consumes=meta.get("consumes"),
                produces=str(meta.get("produces") or ""),
            )
        )
    return Chain(skill_dir=skill_dir, mode="playbooks", stages=tuple(stages))


def derive_mount(chain: Chain) -> tuple[str, ...]:
    paths: list[str] = ["SKILL.md"]
    seen = {"SKILL.md"}
    for stage in chain.stages:
        if not isinstance(stage, ShippedStage):
            continue
        if stage.playbook_rel not in seen:
            paths.append(stage.playbook_rel)
            seen.add(stage.playbook_rel)
        for skill in stage.skills:
            rel = f"{skill}/SKILL.md"
            if rel not in seen:
                paths.append(rel)
                seen.add(rel)
    if "README.md" in seen:
        raise RuntimeError("README.md must not appear on the derived mount")
    return tuple(paths)


def lint_chain(chain: Chain) -> list[ChainProblem]:
    skill_dir = chain.skill_dir

    if not (skill_dir / "SKILL.md").is_file():
        return [ChainProblem("missing_coordinator", "SKILL.md is missing")]

    if not chain.stages:
        return [ChainProblem("empty_chain", "chain has no stages")]

    if chain.mode == "monolith":
        return _lint_monolith(chain)

    return _lint_playbooks(chain)


def _lint_monolith(chain: Chain) -> list[ChainProblem]:
    problems: list[ChainProblem] = []
    if chain.mode != "monolith":
        problems.append(
            ChainProblem("monolith_shape", f"expected mode monolith, got {chain.mode!r}")
        )
    if len(chain.stages) != 1 or not isinstance(chain.stages[0], MonolithStage):
        problems.append(
            ChainProblem(
                "monolith_shape",
                "monolith chain must be exactly one MonolithStage",
            )
        )
        return problems
    mount = derive_mount(chain)
    if mount != ("SKILL.md",):
        problems.append(
            ChainProblem("mount", f"monolith mount must be ('SKILL.md',), got {mount}")
        )
    return problems


def _lint_playbooks(chain: Chain) -> list[ChainProblem]:
    problems: list[ChainProblem] = []
    skill_dir = chain.skill_dir
    names = [stage.name for stage in chain.stages]

    if names[0] != "define-the-problem":
        problems.append(
            ChainProblem(
                "chain_head",
                f"chain must start with define-the-problem, got {names[0]!r}",
            )
        )

    for stage in chain.stages:
        if isinstance(stage, UnshippedStage):
            continue
        if isinstance(stage, MonolithStage):
            problems.append(
                ChainProblem(
                    "playbook_mode",
                    "playbooks mode must not contain a MonolithStage",
                )
            )
            continue
        path = skill_dir / stage.playbook_rel
        if not path.is_file():
            problems.append(
                ChainProblem("missing_playbook", f"missing playbook file {stage.playbook_rel}")
            )
            continue
        if not stage.produces:
            problems.append(
                ChainProblem(
                    "playbook_meta",
                    f"{stage.name}: frontmatter must set produces",
                )
            )
        for skill in stage.skills:
            leaf = skill_dir / skill / "SKILL.md"
            if not leaf.is_file():
                problems.append(
                    ChainProblem(
                        "missing_leaf",
                        f"{stage.name} names skill {skill!r} but {skill}/SKILL.md is missing",
                    )
                )
                continue
            text = leaf.read_text(encoding="utf-8")
            if "disable-model-invocation: true" not in text:
                problems.append(
                    ChainProblem(
                        "leaf_invocation",
                        f"{skill}/SKILL.md must set disable-model-invocation: true",
                    )
                )

    shipped = [stage for stage in chain.stages if isinstance(stage, ShippedStage)]
    for prev, cur in zip(shipped, shipped[1:]):
        if cur.consumes != prev.produces:
            problems.append(
                ChainProblem(
                    "consumes_produces",
                    f"{cur.name} consumes {cur.consumes!r} but {prev.name} produces {prev.produces!r}",
                )
            )

    if shipped and shipped[0].consumes not in (None, "none", ""):
        problems.append(
            ChainProblem(
                "chain_head",
                f"first shipped stage must consume nothing, got {shipped[0].consumes!r}",
            )
        )

    for orphan in _orphan_leaf_dirs(chain):
        problems.append(
            ChainProblem(
                "orphan_leaf",
                f"leaf directory {orphan!r} is not named by any shipped playbook",
            )
        )

    mount = derive_mount(chain)
    if "README.md" in mount:
        problems.append(ChainProblem("mount", "README.md must not be on the derived mount"))

    return problems


def named_skills(chain: Chain) -> frozenset[str]:
    return frozenset(
        skill
        for stage in chain.stages
        if isinstance(stage, ShippedStage)
        for skill in stage.skills
    )


def _orphan_leaf_dirs(chain: Chain) -> list[str]:
    named = named_skills(chain)
    reserved = {
        "playbooks",
        "design",
        "README.md",
        "SKILL.md",
    }
    orphans: list[str] = []
    for path in chain.skill_dir.iterdir():
        if path.name.startswith(".") or path.name in reserved:
            continue
        if path.is_dir() and (path / "SKILL.md").is_file() and path.name not in named:
            orphans.append(path.name)
    return sorted(orphans)


def _parse_chain_order(coordinator: str) -> tuple[str, ...]:
    match = CHAIN_SECTION_RE.search(coordinator)
    if not match:
        raise ValueError("coordinator SKILL.md is missing a ## Chain section")
    names = CHAIN_ITEM_RE.findall(match.group("body"))
    if not names:
        raise ValueError("## Chain section has no numbered stages")
    return tuple(names)


def _parse_playbook_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    data = yaml.safe_load(match.group("body")) or {}
    if not isinstance(data, dict):
        return {}
    skills = data.get("skills") or []
    if isinstance(skills, str):
        skills = [skills]
    consumes = data.get("consumes")
    if consumes in ("none", ""):
        consumes = None
    return {
        "skills": list(skills),
        "consumes": consumes,
        "produces": data.get("produces"),
    }
