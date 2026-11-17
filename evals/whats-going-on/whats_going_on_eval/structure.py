"""Stage-2 structure-the-problem wire. Parsed at the debug boundary."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cache
from typing import Any, Literal, Never

from .manifest import SKILL_DIR
from .principles import load_principles
from .view import View
from .wire import ContractViolation, Unresolved

StructureStatus = Literal["structured", "needs_split", "blocked"]
BreakdownStatus = Literal["mece_pass", "needs_split"]
PassFail = Literal["pass", "fail"]
Nature = Literal["analytical", "conceptual"]
Direction = Literal["convergent", "divergent"]
Depth = Literal[1, 2, 3]

STRUCTURE_STATUSES = ("structured", "needs_split", "blocked")
NATURES = ("analytical", "conceptual")
DIRECTIONS = ("convergent", "divergent")
BREAKDOWN_STATUSES = ("mece_pass", "needs_split")
PASS_FAIL = ("pass", "fail")
MAX_BREAKDOWNS = 3
MAX_LEVEL = 3
CHANGED_BUDGET = 200

SELECTION_ASK = (
    "Which breakdowns (and optional branch ids) do you want to work in parallel?"
)
CUT_ASK_RE = re.compile(r"\bcut\b", re.IGNORECASE)

# Anti-example patterns: self-attested ME/CE that the wire must reject.
_MEALS_OVERLAP_RE = re.compile(
    r"\b(breakfast|lunch|dinner|brunch|supper)\b", re.IGNORECASE
)
_MEALS_PARENT_RE = re.compile(r"\bmeals?\b", re.IGNORECASE)
_TRAFFIC_COLOR_RE = re.compile(r"\b(red|green|yellow|amber)\b", re.IGNORECASE)
_GROW_REVENUE_RE = re.compile(r"\bgrow\b.*\brevenue\b|\brevenue\b.*\bgrowth\b", re.IGNORECASE)
_PRICE_VOLUME_RE = re.compile(r"\b(price|pricing|asp|arpu|volume|units|quantity)\b", re.IGNORECASE)
_ACQUISITION_SPACE_RE = re.compile(
    r"\b(acquir|new\s+customer|new\s+market|new\s+product|channel|segment)\b",
    re.IGNORECASE,
)

STRUCTURE_VERDICT_KEYS = frozenset(
    {
        "status",
        "root_question",
        "main_question",
        "smart_question",
        "classification",
        "breakdowns",
        "selected",
        "unresolved",
        "applied",
        "stop",
    }
)
BREAKDOWN_KEYS = frozenset(
    {"id", "frame", "depth_max_used", "status", "tree", "mece"}
)
NODE_REQUIRED = frozenset({"id", "question", "level", "children"})
NODE_ALLOWED = NODE_REQUIRED | {"hypothesis"}
MECE_KEYS = frozenset(
    {"path", "mutually_exclusive", "collectively_exhaustive", "note"}
)
SELECTED_KEYS = frozenset({"breakdown_ids", "branch_ids", "parallel"})
APPLIED_KEYS = frozenset({"name", "at", "changed"})
CLASSIFICATION_KEYS = frozenset({"nature", "direction"})

_AT_RE = re.compile(
    r"^(?:status|root_question"
    r"|unresolved\[(?P<unresolved>0|[1-9][0-9]*)\]"
    r"|breakdowns\[(?P<breakdown>0|[1-9][0-9]*)\])$"
)


@dataclass(frozen=True)
class TreeNode:
    id: str
    question: str
    level: int
    hypothesis: str | None
    children: tuple[TreeNode, ...]


@dataclass(frozen=True)
class MeceNote:
    path: str
    mutually_exclusive: PassFail
    collectively_exhaustive: PassFail
    note: str


@dataclass(frozen=True)
class Breakdown:
    id: str
    frame: str
    depth_max_used: Depth
    status: BreakdownStatus
    tree: TreeNode
    mece: tuple[MeceNote, ...]


@dataclass(frozen=True)
class Selected:
    breakdown_ids: tuple[str, ...]
    branch_ids: tuple[str, ...]
    parallel: bool


@dataclass(frozen=True)
class ClassificationSnap:
    nature: Nature
    direction: Direction


@dataclass(frozen=True)
class StructureApplied:
    name: str
    at: str
    changed: str


@dataclass(frozen=True)
class StructureVerdict:
    status: StructureStatus
    root_question: str | None
    main_question: str | None
    smart_question: str | None
    classification: ClassificationSnap | None
    breakdowns: tuple[Breakdown, ...]
    selected: Selected
    unresolved: tuple[Unresolved, ...]
    applied: tuple[StructureApplied, ...]


@dataclass(frozen=True)
class StructureResponse:
    view: View
    verdict: StructureVerdict


def parse_structure(raw: dict[str, Any], view: View) -> StructureResponse | ContractViolation:
    unknown = set(raw) - STRUCTURE_VERDICT_KEYS
    if unknown:
        return ContractViolation("schema", f"unknown keys: {sorted(unknown)}")
    missing = STRUCTURE_VERDICT_KEYS - set(raw)
    if missing:
        return ContractViolation("schema", f"missing keys: {sorted(missing)}")
    if raw.get("stop") is not True:
        return ContractViolation("schema", "stop must be literal true")

    claimed = raw.get("status")
    if claimed not in STRUCTURE_STATUSES:
        return ContractViolation("schema", f"status must be one of {STRUCTURE_STATUSES}")

    questions = _parse_questions(raw, claimed)
    if isinstance(questions, ContractViolation):
        return questions
    root_question, main_question, smart_question = questions

    classification = _parse_classification(raw["classification"])
    if isinstance(classification, ContractViolation):
        return classification

    breakdowns = _parse_breakdowns(raw["breakdowns"], root_question)
    if isinstance(breakdowns, ContractViolation):
        return breakdowns

    derived = _derive_status(breakdowns)
    if claimed != derived:
        return ContractViolation(
            "status_mismatch", f"claimed={claimed} derived={derived}"
        )

    selected = _parse_selected(raw["selected"])
    if isinstance(selected, ContractViolation):
        return selected

    unresolved = _parse_unresolved_list(raw["unresolved"])
    if isinstance(unresolved, ContractViolation):
        return unresolved

    constraint = _status_constraints(derived, selected, unresolved, breakdowns)
    if isinstance(constraint, ContractViolation):
        return constraint

    applied = _parse_applied(raw["applied"], len(breakdowns), len(unresolved))
    if isinstance(applied, ContractViolation):
        return applied

    return StructureResponse(
        view=view,
        verdict=StructureVerdict(
            status=derived,
            root_question=root_question,
            main_question=main_question,
            smart_question=smart_question,
            classification=classification,
            breakdowns=breakdowns,
            selected=selected,
            unresolved=unresolved,
            applied=applied,
        ),
    )


def _derive_status(breakdowns: tuple[Breakdown, ...]) -> StructureStatus:
    if not breakdowns:
        return "blocked"
    if any(item.status == "needs_split" for item in breakdowns):
        return "needs_split"
    return "structured"


def _parse_questions(
    raw: dict[str, Any], claimed: str
) -> tuple[str | None, str | None, str | None] | ContractViolation:
    main = _text_or_null(raw["main_question"], "main_question")
    if isinstance(main, ContractViolation):
        return main
    smart = _text_or_null(raw["smart_question"], "smart_question")
    if isinstance(smart, ContractViolation):
        return smart
    root_raw = raw["root_question"]
    if claimed == "blocked":
        if root_raw is None:
            return None, main, smart
        root = _nonblank(root_raw, "root_question")
        if isinstance(root, ContractViolation):
            return root
        return root, main, smart
    if main is None:
        return ContractViolation("schema", "main_question must be a non-empty string")
    root = _nonblank(root_raw, "root_question")
    if isinstance(root, ContractViolation):
        return root
    expected = smart if smart is not None else main
    if root != expected:
        return ContractViolation(
            "root_question_mismatch",
            f"root_question={root!r} expected={expected!r}",
        )
    return root, main, smart


def _parse_classification(raw: Any) -> ClassificationSnap | None | ContractViolation:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        return ContractViolation("schema", "classification must be a mapping or null")
    if set(raw) != CLASSIFICATION_KEYS:
        return ContractViolation("schema", "classification keys must be nature, direction")
    nature = raw["nature"]
    direction = raw["direction"]
    if nature not in NATURES or direction not in DIRECTIONS:
        return ContractViolation("schema", "classification invalid")
    return ClassificationSnap(nature=nature, direction=direction)


def _parse_breakdowns(
    raw: Any, root_question: str | None
) -> tuple[Breakdown, ...] | ContractViolation:
    if not isinstance(raw, list):
        return ContractViolation("schema", "breakdowns must be a list")
    if len(raw) > MAX_BREAKDOWNS:
        return ContractViolation(
            "schema", f"breakdowns holds at most {MAX_BREAKDOWNS}, got {len(raw)}"
        )
    if raw and root_question is None:
        return ContractViolation(
            "schema", "root_question is required when breakdowns is non-empty"
        )
    out: list[Breakdown] = []
    seen_ids: set[str] = set()
    for i, item in enumerate(raw):
        parsed = _parse_breakdown(item, f"breakdowns[{i}]", root_question or "")
        if isinstance(parsed, ContractViolation):
            return parsed
        if parsed.id in seen_ids:
            return ContractViolation(
                "tree_ids", f"duplicate breakdown id {parsed.id!r}"
            )
        seen_ids.add(parsed.id)
        out.append(parsed)
    return tuple(out)


def _parse_breakdown(
    item: Any, path: str, root_question: str
) -> Breakdown | ContractViolation:
    if not isinstance(item, dict):
        return ContractViolation("schema", f"{path} must be a mapping")
    if set(item) != BREAKDOWN_KEYS:
        return ContractViolation(
            "schema",
            f"{path} keys must be id, frame, depth_max_used, status, tree, mece",
        )
    breakdown_id = _nonblank(item.get("id"), f"{path}.id")
    if isinstance(breakdown_id, ContractViolation):
        return breakdown_id
    frame = _nonblank(item.get("frame"), f"{path}.frame")
    if isinstance(frame, ContractViolation):
        return frame
    depth = item.get("depth_max_used")
    if isinstance(depth, bool) or not isinstance(depth, int) or depth not in (1, 2, 3):
        return ContractViolation("schema", f"{path}.depth_max_used must be 1, 2, or 3")
    status = item.get("status")
    if status not in BREAKDOWN_STATUSES:
        return ContractViolation("schema", f"{path}.status must be mece_pass or needs_split")
    tree = _parse_node(item.get("tree"), f"{path}.tree", 0, root_question, True)
    if isinstance(tree, ContractViolation):
        return tree
    mece = _parse_mece(item.get("mece"), f"{path}.mece", status)
    if isinstance(mece, ContractViolation):
        return mece
    deepest = _max_level(tree)
    if depth != deepest:
        return ContractViolation(
            "schema", f"{path}.depth_max_used {depth} != max level {deepest}"
        )
    lint = _validate_breakdown_mece(breakdown_id, status, tree, mece, root_question)
    if isinstance(lint, ContractViolation):
        return lint
    return Breakdown(
        id=breakdown_id,
        frame=frame,
        depth_max_used=depth,
        status=status,
        tree=tree,
        mece=mece,
    )


def _parse_node(
    raw: Any, path: str, depth: int, root_question: str, is_root: bool
) -> TreeNode | ContractViolation:
    if depth > MAX_LEVEL:
        return ContractViolation("schema", f"{path} exceeds level {MAX_LEVEL}")
    if not isinstance(raw, dict):
        return ContractViolation("schema", f"{path} must be a mapping")
    unknown = set(raw) - NODE_ALLOWED
    if unknown:
        return ContractViolation("schema", f"{path} unknown keys: {sorted(unknown)}")
    missing = NODE_REQUIRED - set(raw)
    if missing:
        return ContractViolation("schema", f"{path} missing keys: {sorted(missing)}")
    node_id = _nonblank(raw.get("id"), f"{path}.id")
    if isinstance(node_id, ContractViolation):
        return node_id
    question = _nonblank(raw.get("question"), f"{path}.question")
    if isinstance(question, ContractViolation):
        return question
    if is_root and question != root_question:
        return ContractViolation("schema", f"{path}.question must equal root_question")
    level = raw.get("level")
    if isinstance(level, bool) or not isinstance(level, int):
        return ContractViolation("schema", f"{path}.level must be an integer")
    if level != depth:
        return ContractViolation("schema", f"{path}.level must be {depth}")
    hypothesis = _parse_hypothesis(raw, path, is_root)
    if isinstance(hypothesis, ContractViolation):
        return hypothesis
    children_raw = raw.get("children")
    if not isinstance(children_raw, list):
        return ContractViolation("schema", f"{path}.children must be a list")
    children: list[TreeNode] = []
    for i, child in enumerate(children_raw):
        parsed = _parse_node(
            child, f"{path}.children[{i}]", depth + 1, root_question, False
        )
        if isinstance(parsed, ContractViolation):
            return parsed
        children.append(parsed)
    return TreeNode(
        id=node_id,
        question=question,
        level=level,
        hypothesis=hypothesis,
        children=tuple(children),
    )


def _parse_hypothesis(raw: dict[str, Any], path: str, is_root: bool) -> str | None | ContractViolation:
    if "hypothesis" not in raw or raw["hypothesis"] is None:
        if is_root:
            return None
        return ContractViolation("schema", f"{path}.hypothesis must be a non-empty string")
    return _nonblank(raw["hypothesis"], f"{path}.hypothesis")


def _parse_mece(
    raw: Any, path: str, status: BreakdownStatus
) -> tuple[MeceNote, ...] | ContractViolation:
    if not isinstance(raw, list):
        return ContractViolation("schema", f"{path} must be a list")
    notes: list[MeceNote] = []
    seen_paths: set[str] = set()
    for i, item in enumerate(raw):
        note = _parse_mece_note(item, f"{path}[{i}]")
        if isinstance(note, ContractViolation):
            return note
        if note.path in seen_paths:
            return ContractViolation("mece_notes", f"duplicate mece path {note.path}")
        seen_paths.add(note.path)
        if status == "mece_pass" and (
            note.mutually_exclusive != "pass" or note.collectively_exhaustive != "pass"
        ):
            return ContractViolation(
                "schema", f"{path}[{i}] must pass when breakdown status is mece_pass"
            )
        notes.append(note)
    return tuple(notes)


def _parse_mece_note(item: Any, path: str) -> MeceNote | ContractViolation:
    if not isinstance(item, dict):
        return ContractViolation("schema", f"{path} must be a mapping")
    if set(item) != MECE_KEYS:
        return ContractViolation(
            "schema",
            f"{path} keys must be path, mutually_exclusive, collectively_exhaustive, note",
        )
    note_path = _nonblank(item.get("path"), f"{path}.path")
    if isinstance(note_path, ContractViolation):
        return note_path
    exclusive = item.get("mutually_exclusive")
    exhaustive = item.get("collectively_exhaustive")
    if exclusive not in PASS_FAIL or exhaustive not in PASS_FAIL:
        return ContractViolation("schema", f"{path} pass/fail invalid")
    note = _nonblank(item.get("note"), f"{path}.note")
    if isinstance(note, ContractViolation):
        return note
    return MeceNote(
        path=note_path,
        mutually_exclusive=exclusive,
        collectively_exhaustive=exhaustive,
        note=note,
    )


def _sibling_set_paths(
    breakdown_id: str, root: TreeNode
) -> dict[str, tuple[TreeNode, ...]]:
    """Map wire path → children for every parent that has children."""
    out: dict[str, tuple[TreeNode, ...]] = {}

    def walk(node: TreeNode, path: str) -> None:
        if node.children:
            out[path] = node.children
            for child in node.children:
                walk(child, f"{breakdown_id}.tree.{child.id}.children")

    walk(root, f"{breakdown_id}.tree.children")
    return out


def _collect_ids(node: TreeNode) -> list[str]:
    ids = [node.id]
    for child in node.children:
        ids.extend(_collect_ids(child))
    return ids


def _anti_example_lint(
    children: tuple[TreeNode, ...], *, where: str
) -> ContractViolation | None:
    texts = [c.question for c in children]
    has_meal_part = any(_MEALS_OVERLAP_RE.search(t) for t in texts)
    has_meals_parent = any(_MEALS_PARENT_RE.search(t) for t in texts)
    if has_meal_part and has_meals_parent:
        return ContractViolation(
            "mece_anti_example",
            f"{where}: meal parts and 'meals' cannot share a sibling set (ME fail)",
        )
    colors = {
        m.group(1).lower()
        for t in texts
        for m in [_TRAFFIC_COLOR_RE.search(t)]
        if m
    }
    if colors and colors <= {"red", "green"} and "yellow" not in colors and "amber" not in colors:
        return ContractViolation(
            "mece_anti_example",
            f"{where}: red+green without yellow/amber is not CE for a traffic light",
        )
    return None


def _grow_revenue_ce_lint(
    root_question: str, children: tuple[TreeNode, ...], *, where: str
) -> ContractViolation | None:
    if not _GROW_REVENUE_RE.search(root_question):
        return None
    texts = [c.question for c in children]
    if not texts:
        return None
    if not all(_PRICE_VOLUME_RE.search(t) for t in texts):
        return None
    if any(_ACQUISITION_SPACE_RE.search(t) for t in texts):
        return None
    return ContractViolation(
        "mece_ce_scope",
        f"{where}: grow-revenue CE cannot pass on price|volume alone; "
        "keep acquisition/new markets as open branches (see mece.md)",
    )


def _validate_breakdown_mece(
    breakdown_id: str,
    status: BreakdownStatus,
    tree: TreeNode,
    notes: tuple[MeceNote, ...],
    root_question: str,
) -> ContractViolation | None:
    if not tree.children:
        return ContractViolation(
            "tree_shape",
            f"breakdown {breakdown_id}: root must have at least two children",
        )

    ids = _collect_ids(tree)
    if len(ids) != len(set(ids)):
        return ContractViolation(
            "tree_ids", f"breakdown {breakdown_id}: node ids must be unique"
        )

    sibling_sets = _sibling_set_paths(breakdown_id, tree)
    for path, kids in sibling_sets.items():
        if len(kids) < 2:
            return ContractViolation(
                "tree_shape",
                f"{path}: sibling set must have at least two children",
            )
        anti = _anti_example_lint(kids, where=path)
        if anti is not None:
            return anti
        if path == f"{breakdown_id}.tree.children":
            ce = _grow_revenue_ce_lint(root_question, kids, where=path)
            if ce is not None and status == "mece_pass":
                root_note = next((n for n in notes if n.path == path), None)
                if (
                    root_note is not None
                    and root_note.collectively_exhaustive == "pass"
                ):
                    return ce

    note_paths = {n.path for n in notes}
    bogus = sorted(note_paths - set(sibling_sets))
    if bogus:
        return ContractViolation(
            "mece_notes",
            f"breakdown {breakdown_id}: mece path does not resolve to a sibling "
            f"set: {bogus}",
        )
    missing = sorted(set(sibling_sets) - note_paths)
    if missing:
        return ContractViolation(
            "mece_notes",
            f"breakdown {breakdown_id}: every sibling set needs a mece note; "
            f"missing {missing}",
        )

    has_fail = any(
        n.mutually_exclusive == "fail" or n.collectively_exhaustive == "fail"
        for n in notes
    )
    if status == "mece_pass":
        if has_fail:
            return ContractViolation(
                "mece_status",
                f"breakdown {breakdown_id}: mece_pass forbids a fail flag",
            )
    else:
        if not has_fail:
            return ContractViolation(
                "mece_status",
                f"breakdown {breakdown_id}: needs_split requires at least one "
                "fail flag",
            )
    return None


def _max_level(node: TreeNode) -> int:
    deepest = node.level
    for child in node.children:
        deepest = max(deepest, _max_level(child))
    return deepest


def _parse_selected(raw: Any) -> Selected | ContractViolation:
    if not isinstance(raw, dict):
        return ContractViolation("schema", "selected must be a mapping")
    if set(raw) != SELECTED_KEYS:
        return ContractViolation(
            "schema", "selected keys must be breakdown_ids, branch_ids, parallel"
        )
    breakdown_ids = _parse_ids(raw.get("breakdown_ids"), "selected.breakdown_ids")
    if isinstance(breakdown_ids, ContractViolation):
        return breakdown_ids
    branch_ids = _parse_ids(raw.get("branch_ids"), "selected.branch_ids")
    if isinstance(branch_ids, ContractViolation):
        return branch_ids
    parallel = raw.get("parallel")
    if not isinstance(parallel, bool):
        return ContractViolation("schema", "selected.parallel must be a bool")
    want = len(breakdown_ids) > 1 or len(branch_ids) > 1
    if parallel is not want:
        return ContractViolation(
            "schema", f"selected.parallel must be {str(want).lower()}"
        )
    return Selected(
        breakdown_ids=breakdown_ids, branch_ids=branch_ids, parallel=parallel
    )


def _parse_ids(raw: Any, path: str) -> tuple[str, ...] | ContractViolation:
    if not isinstance(raw, list):
        return ContractViolation("schema", f"{path} must be a list")
    ids: list[str] = []
    for i, item in enumerate(raw):
        value = _nonblank(item, f"{path}[{i}]")
        if isinstance(value, ContractViolation):
            return value
        ids.append(value)
    return tuple(ids)


def _status_constraints(
    status: StructureStatus,
    selected: Selected,
    unresolved: tuple[Unresolved, ...],
    breakdowns: tuple[Breakdown, ...],
) -> ContractViolation | None:
    if status == "blocked":
        if selected.breakdown_ids or selected.branch_ids:
            return ContractViolation("schema", "blocked selected ids must be empty")
        if not unresolved:
            return ContractViolation("schema", "blocked needs an unresolved row")
        return None
    if status == "structured":
        if (
            not selected.breakdown_ids
            and not selected.branch_ids
        ):
            clarifications = tuple(row.clarification for row in unresolved)
            if clarifications != (SELECTION_ASK,):
                return ContractViolation(
                    "schema",
                    "structured with an empty selection needs exactly one "
                    "selection ask",
                )
        return None
    if status == "needs_split":
        if selected.breakdown_ids or selected.branch_ids or selected.parallel:
            return ContractViolation(
                "status_constraints", "needs_split forbids pre-filled selected"
            )
        if not unresolved:
            return ContractViolation(
                "status_constraints",
                "needs_split requires an unresolved cut ask",
            )
        if not any(CUT_ASK_RE.search(u.clarification) for u in unresolved):
            return ContractViolation(
                "status_constraints",
                "needs_split unresolved must include a cut ask "
                "(clarification containing 'cut')",
            )
        if not any(b.status == "needs_split" for b in breakdowns):
            return ContractViolation(
                "status_constraints",
                "needs_split requires at least one breakdown with status "
                "needs_split",
            )
        return None
    _: Never = status
    return ContractViolation("schema", f"unknown status {status}")


def _parse_unresolved_list(raw: Any) -> tuple[Unresolved, ...] | ContractViolation:
    if not isinstance(raw, list):
        return ContractViolation("schema", "unresolved must be a list")
    rows: list[Unresolved] = []
    for i, item in enumerate(raw):
        parsed = _parse_unresolved(item, f"unresolved[{i}]")
        if isinstance(parsed, ContractViolation):
            return parsed
        rows.append(parsed)
    return tuple(rows)


def _parse_unresolved(item: Any, path: str) -> Unresolved | ContractViolation:
    if not isinstance(item, dict):
        return ContractViolation("schema", f"{path} must be a mapping")
    observation = _nonblank(item.get("observation"), f"{path}.observation")
    if isinstance(observation, ContractViolation):
        return observation
    reason = _nonblank(item.get("reason"), f"{path}.reason")
    if isinstance(reason, ContractViolation):
        return reason
    clarification = _nonblank(item.get("clarification"), f"{path}.clarification")
    if isinstance(clarification, ContractViolation):
        return clarification
    return Unresolved(
        observation=observation, reason=reason, clarification=clarification
    )


def _parse_applied(
    raw: Any, breakdown_count: int, unresolved_count: int
) -> tuple[StructureApplied, ...] | ContractViolation:
    if not isinstance(raw, list):
        return ContractViolation("schema", "applied must be a list")
    known = _principle_names()
    out: list[StructureApplied] = []
    for i, item in enumerate(raw):
        path = f"applied[{i}]"
        if not isinstance(item, dict):
            return ContractViolation("schema", f"{path} must be a mapping")
        if set(item) != APPLIED_KEYS:
            return ContractViolation("schema", f"{path} keys must be name, at, changed")
        name = _nonblank(item.get("name"), f"{path}.name")
        if isinstance(name, ContractViolation):
            return name
        at = _nonblank(item.get("at"), f"{path}.at")
        if isinstance(at, ContractViolation):
            return at
        changed = _nonblank(item.get("changed"), f"{path}.changed")
        if isinstance(changed, ContractViolation):
            return changed
        if name not in known:
            return ContractViolation("principle_unknown", f"{path}.name {name!r}")
        match = _AT_RE.fullmatch(at)
        if match is None:
            return ContractViolation("principle_at", f"{path}.at {at!r} does not resolve")
        unresolved_at = match["unresolved"]
        breakdown_at = match["breakdown"]
        if unresolved_at is not None and int(unresolved_at) >= unresolved_count:
            return ContractViolation("principle_at", f"{path}.at {at!r} does not resolve")
        if breakdown_at is not None and int(breakdown_at) >= breakdown_count:
            return ContractViolation("principle_at", f"{path}.at {at!r} does not resolve")
        if len(changed) > CHANGED_BUDGET:
            return ContractViolation(
                "principle_changed",
                f"{path}.changed is {len(changed)} chars, max {CHANGED_BUDGET}",
            )
        out.append(StructureApplied(name=name, at=at, changed=changed))
    return tuple(out)


@cache
def _principle_names() -> frozenset[str]:
    return frozenset(principle.name for principle in load_principles(SKILL_DIR))


def _text_or_null(value: Any, path: str) -> str | None | ContractViolation:
    if value is None:
        return None
    return _nonblank(value, path)


def _nonblank(value: Any, path: str) -> str | ContractViolation:
    if not isinstance(value, str) or not value.strip():
        return ContractViolation("schema", f"{path} must be a non-empty string")
    return value.strip()
