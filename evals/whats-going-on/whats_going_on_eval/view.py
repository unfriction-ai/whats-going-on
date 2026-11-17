"""Human view of a problem definition. The Verdict fence is not part of this wire."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Protocol

from .challenge import LABEL, ChallengeAssessment, operator_ask
from .smart import ASK_YOURSELF
from .wire import PREAMBLE_BUDGET, ContractViolation
from .worksheet import QUESTION_SLOT, Registry, WorksheetAssessment, load_registry

Mode = Literal["default", "debug"]

StatusPhrase = Literal[
    "Not defined yet",
    "Partly defined",
    "Defined",
    "Not a problem",
]

STATUS_PHRASE: dict[str, StatusPhrase] = {
    "needs_clarification": "Not defined yet",
    "partial": "Partly defined",
    "classified": "Defined",
    "not_a_problem": "Not a problem",
}

TITLE = "What's going on"

_NO_QUESTION = frozenset(
    {
        "There is no question yet.",
        "There is no question.",
    }
)
_QUESTION_LABELS = frozenset({"the question", "main question"})
_STATUS_LABELS = frozenset({"status"})
_PHRASES_LONGEST_FIRST = tuple(sorted(STATUS_PHRASE.values(), key=len, reverse=True))
_ASK_HEADS = (ASK_YOURSELF.strip(), LABEL.strip())

_YAML_FENCE = re.compile(r"```yaml", re.IGNORECASE)
_STATUS_DUMP = re.compile(r"\A[ \t]*status[ \t]*:")
_BULLET = re.compile(r"^(?:[-*]|\d+[.)])\s+")


@dataclass(frozen=True)
class View:
    restatement: str
    status_phrase: str | None
    main_question: str | None
    ask_line: str | None
    body: str


@dataclass(frozen=True)
class ViewFail:
    kind: str
    detail: str = ""


class _VerdictView(Protocol):
    status: str
    main_question: str | None
    worksheet: WorksheetAssessment
    challenge: ChallengeAssessment


def split_human(text: str) -> tuple[str, str]:
    """Opening paragraph, then the rest of the human text.

    A leading title line is the continue marker, not the restatement.
    """
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text.strip()) if part.strip()]
    if paragraphs and " ".join(paragraphs[0].split()).casefold() == TITLE.casefold():
        paragraphs = paragraphs[1:]
    if not paragraphs:
        return "", ""
    return paragraphs[0], "\n\n".join(paragraphs[1:])


def read_view(restatement: str, body: str) -> View:
    return View(
        restatement=restatement,
        status_phrase=_shown_status(body),
        main_question=_line_under_label(body, _QUESTION_LABELS),
        ask_line=_shown_ask(body),
        body=body,
    )


def parse_view(text: str) -> View | ContractViolation:
    """Default wire. A YAML fence or a leading ``status:`` dump is a violation."""
    if _YAML_FENCE.search(text):
        return ContractViolation("yaml_fence")
    if _STATUS_DUMP.search(text):
        return ContractViolation("status_dump")
    restatement, body = split_human(text)
    if len(restatement) > PREAMBLE_BUDGET:
        return ContractViolation("preamble_over_budget", str(len(restatement)))
    return read_view(restatement, body)


def view_agrees(view: View, verdict: _VerdictView) -> list[ViewFail]:
    """Hard fails for the status phrase, the main question, and the ask line.

    A missing label is not a fail. Today's gold replies have an empty view body.
    """
    fails: list[ViewFail] = []
    expected_phrase = STATUS_PHRASE.get(verdict.status)
    if view.status_phrase is not None and view.status_phrase != expected_phrase:
        fails.append(
            ViewFail("view_status", f"shown {view.status_phrase!r} verdict {expected_phrase!r}")
        )
    if view.main_question is not None and not _question_agrees(
        view.main_question, verdict.main_question
    ):
        fails.append(
            ViewFail(
                "view_main_question",
                f"shown {view.main_question!r} verdict {verdict.main_question!r}",
            )
        )
    if view.ask_line is not None:
        expected_ask = operator_ask(verdict.worksheet, verdict.challenge)
        if view.ask_line != expected_ask:
            fails.append(
                ViewFail("view_ask", f"shown {view.ask_line!r} verdict {expected_ask!r}")
            )
    return fails


def default_mode_problems() -> list[str]:
    """Observable default-wire checks. A fence is rejected. A human reply parses."""
    problems: list[str] = []
    fenced = "Someone asks why latency rose.\n\n```yaml\nstatus: classified\nstop: true\n```"
    fenced_parsed = parse_view(fenced)
    if not isinstance(fenced_parsed, ContractViolation) or fenced_parsed.kind != "yaml_fence":
        problems.append(f"default view accepted a yaml fence ({fenced_parsed!r})")

    dumped = parse_view("status: classified\nmain_question: null\n")
    if not isinstance(dumped, ContractViolation) or dumped.kind != "status_dump":
        problems.append(f"default view accepted a leading status dump ({dumped!r})")

    heading = parse_view("Status\n\nNot defined yet\n")
    if isinstance(heading, ContractViolation):
        problems.append(f"default view rejected a Status heading ({heading.kind})")

    clean = parse_view(
        "What's going on\n\n"
        "Someone asks why checkout latency rose.\n\n"
        "## The question\n"
        "Why did checkout latency rise?\n\n"
        "STATUS\n"
        "Not defined yet. A problem cannot be named until the next ask is answered.\n\n"
        "Ask yourself: What would done look like?\n"
    )
    if isinstance(clean, ContractViolation):
        problems.append(f"default view rejected a human reply ({clean.kind})")
        return problems
    if clean.restatement != "Someone asks why checkout latency rose.":
        problems.append(f"default view restatement {clean.restatement!r}")
    if clean.status_phrase != "Not defined yet":
        problems.append(f"default view status phrase {clean.status_phrase!r}")
    if clean.main_question != "Why did checkout latency rise?":
        problems.append(f"default view main question {clean.main_question!r}")
    if clean.ask_line != "Ask yourself: What would done look like?":
        problems.append(f"default view ask line {clean.ask_line!r}")
    return problems


def _shown_status(body: str) -> str | None:
    labeled = _line_under_label(body, _STATUS_LABELS)
    if labeled is not None:
        return _phrase_in(labeled) or labeled
    return _phrase_in(body)


def _phrase_in(text: str) -> str | None:
    best: tuple[int, int, str] | None = None
    for phrase in _PHRASES_LONGEST_FIRST:
        start = 0
        while True:
            index = text.find(phrase, start)
            if index < 0:
                break
            end = index + len(phrase)
            before = text[index - 1] if index else ""
            after = text[end] if end < len(text) else ""
            if not before.isalnum() and not after.isalnum():
                candidate = (index, -len(phrase), phrase)
                if best is None or candidate < best:
                    best = candidate
                break
            start = index + 1
    if best is None:
        return None
    return best[2]


def _line_under_label(text: str, labels: frozenset[str]) -> str | None:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        head, inline = _split_label(line)
        if head not in labels:
            continue
        if inline:
            return inline
        for later in lines[index + 1 :]:
            if later.strip():
                return later.strip()
        return ""
    return None


def _split_label(line: str) -> tuple[str, str]:
    text = re.sub(r"^#+\s*", "", line.strip())
    text = text.strip("*_` ")
    if ":" in text:
        head, tail = text.split(":", 1)
        key = " ".join(head.strip("*_` ").split()).casefold()
        return key, tail.strip()
    key = " ".join(text.strip("*_` ").split()).casefold()
    return key, ""


def _shown_ask(body: str) -> str | None:
    if not body.strip():
        return None
    registry = load_registry()
    hand_back = registry.hand_back_line
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        candidate = _BULLET.sub("", line).strip()
        if (
            candidate.startswith(_ASK_HEADS)
            or candidate == hand_back
            or _is_probe(candidate, registry)
        ):
            return line
    return None


def _is_probe(line: str, registry: Registry) -> bool:
    for area in registry.areas:
        head, tail = area.probe_template.split(QUESTION_SLOT)
        if not line.startswith(head) or not line.endswith(tail):
            continue
        middle = line[len(head) : len(line) - len(tail)] if tail else line[len(head) :]
        if middle.strip():
            return True
    return False


def _question_agrees(shown: str, verdict_question: str | None) -> bool:
    if verdict_question is None:
        return shown in _NO_QUESTION
    return shown == verdict_question
