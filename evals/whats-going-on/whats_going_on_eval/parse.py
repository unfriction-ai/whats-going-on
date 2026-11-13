"""Boundary: raw agent text -> Response | Halt, or a ContractViolation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal, TypeVar

import yaml

NATURES = ("analytical", "conceptual")
DIRECTIONS = ("convergent", "divergent")
CONFIDENCES = ("high", "medium", "low")
STATUSES = ("classified", "partial", "needs_clarification", "not_a_problem")

Nature = Literal["analytical", "conceptual"]
Direction = Literal["convergent", "divergent"]
Confidence = Literal["high", "medium", "low"]
Status = Literal["classified", "partial", "needs_clarification", "not_a_problem"]
Quadrant = Literal[
    "analytical-convergent",
    "analytical-divergent",
    "conceptual-convergent",
    "conceptual-divergent",
]

PREAMBLE_BUDGET = 400

NO_ASK = "No ask is stated."

FENCE_RE = re.compile(r"```yaml\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

VERDICT_KEYS = frozenset({"status", "problems", "unresolved", "stop"})
HALT_KEYS = frozenset({"next_stage", "available", "stop"})

T = TypeVar("T")
AtMostOne = tuple[()] | tuple[T]


@dataclass(frozen=True)
class ClassifiedProblem:
    statement: str
    quadrant: Quadrant
    confidence: Confidence
    why: str
    next_method: str


Problems = AtMostOne[ClassifiedProblem]


@dataclass(frozen=True)
class Unresolved:
    observation: str
    reason: str
    clarification: str


@dataclass(frozen=True)
class Verdict:
    status: Status
    problems: Problems
    unresolved: tuple[Unresolved, ...]


@dataclass(frozen=True)
class Restatement:
    text: str
    ask_stated: bool


@dataclass(frozen=True)
class Response:
    preamble: str
    verdict: Verdict


@dataclass(frozen=True)
class Halt:
    """Coordinator refusal when the next playbook file is not shipped."""

    preamble: str
    next_stage: str
    available: Literal[False]
    stop: Literal[True]


Outcome = Response | Halt


@dataclass(frozen=True)
class ContractViolation:
    kind: str
    detail: str = ""


def derive_status(problems: Problems, unresolved: tuple[Unresolved, ...]) -> Status:
    has_p = len(problems) > 0
    has_u = len(unresolved) > 0
    if not has_p and not has_u:
        return "not_a_problem"
    if not has_p and has_u:
        return "needs_clarification"
    if has_p and not has_u:
        return "classified"
    return "partial"


def quadrant_of(nature: Nature, direction: Direction) -> Quadrant:
    return f"{nature}-{direction}"  # type: ignore[return-value]


def describe_violation(v: ContractViolation) -> str:
    if v.detail:
        return f"{v.kind}: {v.detail}"
    return v.kind


def parse_restatement(preamble: str) -> Restatement | None:
    text = preamble.strip()
    if not text:
        return None
    no_ask = NO_ASK in text
    return Restatement(text=text, ask_stated=not no_ask)


def parse_response(text: str) -> Outcome | ContractViolation:
    matches = list(FENCE_RE.finditer(text))
    if not matches:
        return ContractViolation("no_yaml_block")
    if len(matches) > 1:
        return ContractViolation("multiple_yaml_blocks", str(len(matches)))

    match = matches[0]
    preamble = text[: match.start()]
    trailing = text[match.end() :]
    if trailing.strip():
        return ContractViolation("content_after_stop", trailing.strip()[:80])
    if len(preamble.strip()) > PREAMBLE_BUDGET:
        return ContractViolation("preamble_over_budget", str(len(preamble.strip())))

    try:
        raw = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        return ContractViolation("invalid_yaml", str(exc))

    if not isinstance(raw, dict):
        return ContractViolation("schema", "root must be a mapping")

    return _validate_wire(raw, preamble.strip())


def _nonblank(value: Any, path: str) -> str | ContractViolation:
    if not isinstance(value, str) or not value.strip():
        return ContractViolation("schema", f"{path} must be a non-empty string")
    return value.strip()


def _validate_wire(raw: dict[str, Any], preamble: str) -> Outcome | ContractViolation:
    keys = set(raw)
    if "next_stage" in keys:
        unknown_halt = keys - HALT_KEYS
        if unknown_halt:
            return ContractViolation("schema", f"unknown keys: {sorted(unknown_halt)}")
        return _validate_halt(raw, preamble)

    unknown = keys - VERDICT_KEYS
    if unknown:
        return ContractViolation("schema", f"unknown keys: {sorted(unknown)}")

    if raw.get("stop") is not True:
        return ContractViolation("schema", "stop must be literal true")

    claimed = raw.get("status")
    if claimed not in STATUSES:
        return ContractViolation("schema", f"status must be one of {STATUSES}")

    problems_raw = raw.get("problems", [])
    unresolved_raw = raw.get("unresolved", [])
    if problems_raw is None:
        problems_raw = []
    if unresolved_raw is None:
        unresolved_raw = []
    if not isinstance(problems_raw, list):
        return ContractViolation("schema", "problems must be a list")
    if not isinstance(unresolved_raw, list):
        return ContractViolation("schema", "unresolved must be a list")
    if len(problems_raw) > 1:
        return ContractViolation(
            "schema", f"problems holds at most one primary problem, got {len(problems_raw)}"
        )

    problems_t: Problems = ()
    if problems_raw:
        primary = _parse_problem(problems_raw[0], "problems[0]")
        if isinstance(primary, ContractViolation):
            return primary
        problems_t = (primary,)

    unresolved: list[Unresolved] = []
    for i, item in enumerate(unresolved_raw):
        parsed = _parse_unresolved(item, f"unresolved[{i}]")
        if isinstance(parsed, ContractViolation):
            return parsed
        unresolved.append(parsed)

    unresolved_t = tuple(unresolved)
    derived = derive_status(problems_t, unresolved_t)
    if claimed != derived:
        return ContractViolation(
            "status_mismatch", f"claimed={claimed} derived={derived}"
        )

    return Response(
        preamble=preamble,
        verdict=Verdict(status=derived, problems=problems_t, unresolved=unresolved_t),
    )


def _validate_halt(raw: dict[str, Any], preamble: str) -> Halt | ContractViolation:
    if raw.get("stop") is not True:
        return ContractViolation("schema", "stop must be literal true")
    if raw.get("available") is not False:
        return ContractViolation("schema", "available must be literal false")
    next_stage = _nonblank(raw.get("next_stage"), "next_stage")
    if isinstance(next_stage, ContractViolation):
        return next_stage
    return Halt(
        preamble=preamble,
        next_stage=next_stage,
        available=False,
        stop=True,
    )


def _parse_problem(item: Any, path: str) -> ClassifiedProblem | ContractViolation:
    if not isinstance(item, dict):
        return ContractViolation("schema", f"{path} must be a mapping")
    statement = _nonblank(item.get("statement"), f"{path}.statement")
    if isinstance(statement, ContractViolation):
        return statement
    why = _nonblank(item.get("why"), f"{path}.why")
    if isinstance(why, ContractViolation):
        return why
    next_method = _nonblank(item.get("next_method"), f"{path}.next_method")
    if isinstance(next_method, ContractViolation):
        return next_method
    confidence = item.get("confidence")
    if confidence not in CONFIDENCES:
        return ContractViolation("schema", f"{path}.confidence invalid")

    classification = item.get("classification")
    if not isinstance(classification, dict):
        return ContractViolation("schema", f"{path}.classification must be a mapping")
    nature = classification.get("nature")
    direction = classification.get("direction")
    if nature not in NATURES or direction not in DIRECTIONS:
        return ContractViolation("schema", f"{path}.classification invalid")

    return ClassifiedProblem(
        statement=statement,
        quadrant=quadrant_of(nature, direction),
        confidence=confidence,
        why=why,
        next_method=next_method,
    )


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
