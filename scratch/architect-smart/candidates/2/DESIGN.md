# SMART gap assessment, candidate 2

This design makes an open SMART letter a `SmartGap`. The verdict stores one `SmartAssessment` built from those gaps. `smart_question`, `smart_gaps`, and the matching `unresolved` rows are projections of that assessment. Variant C is unchanged. `main_question` stays the primary statement.

## Problem

Stage 1 picks at most one primary, copies `problems[0].statement` into `main_question`, and derives `status` from whether `problems` and `unresolved` are empty. `parse_response` rejects any other shape. Variant C inserts a SMART pass after that primary is chosen and before `classify-2x2`. The pass writes `smart_question` and `smart_gaps`. Each missing letter asks the operator one fixed prompt, as an `unresolved` row. Specific and Actionable must both be grounded or `smart_question` is null. The agent never invents a letter. Classify still runs on the primary, so gap rows become `partial` through the status table that already exists. Abstention stays abstention, because the pass does not run without a primary.

The non-obvious part is ownership. The prompt, the gap list, and the `unresolved` row all name the same letter. The repo already fails the build when README contract keys drift from `VERDICT_KEYS`, and when a principle's `governs` list drifts from the leaf. A SMART design has to give the letter that same single owner, or the next edit will update one list and leave the others.

## Usage (caller's view)

The operator pastes an ask. The reply is still two restatement sentences, one fenced `yaml` block, and nothing after it. `main_question` is the problem to answer first. `smart_question` is the SMART wording of that same problem, or null. `smart_gaps` lists the letters still open, in card order. Each open letter has one `unresolved` row whose `clarification` is that letter's prompt.

A vague ask still has no primary. The SMART pass does not run. Case A stays `needs_clarification`, and its clarification stays the clarity question.

```yaml
status: needs_clarification
main_question: null
smart_question: null
smart_gaps: []
problems: []
unresolved:
  - observation: "Mobile is in a rough place; eng has competing theories"
    reason: "No measurable change, magnitude, or timeframe. Competing theories are not yet a defined question."
    clarification: "What changed, by how much, and since when? What decision are you trying to make?"
applied:
  - name: principle-dont-invent-problems
    at: unresolved[0]
    changed: "Kept the concern unresolved instead of naming a metric or cause the input never gives."
stop: true
```

Classify still runs when letters are open. This fence illustrates the staging outage. It is an example, and the fixtures stay as they are until implementation. Specific and Actionable have excerpts in the ask. This illustration leaves Measurable, Relevant, and Time-bound without excerpts. The prevention ask remains a separate unresolved row. `main_question` is still the primary statement, word for word.

```yaml
status: partial
main_question: "Why did staging go down last night?"
smart_question: "Why did staging go down last night?"
smart_gaps:
  - Measurable
  - Relevant
  - Time-bound
problems:
  - statement: "Why did staging go down last night?"
    classification:
      nature: analytical
      direction: convergent
    confidence: high
    why: "The ask wants an exact reason. Evidence should converge on what happened."
    next_method: "Evidence-based incident diagnosis. Finish this before prevention options."
unresolved:
  - observation: "The director also wants three realistic ways to stop this class of failure, ranked by likelihood"
    reason: "Deferred until the primary problem is answered. Prevention options depend on why staging went down."
    clarification: "Ask about prevention again once the cause of the outage is settled."
  - observation: "The primary does not ground Measurable."
    reason: "That SMART letter is still open."
    clarification: "How will we know it is solved?"
  - observation: "The primary does not ground Relevant."
    reason: "That SMART letter is still open."
    clarification: "Does it matter to the people who will decide?"
  - observation: "The primary does not ground Time-bound."
    reason: "That SMART letter is still open."
    clarification: "By when does it need to be solved?"
applied:
  - name: principle-read-the-room
    at: problems[0]
    changed: "Picked the why as primary because the prevention options depend on its answer."
  - name: principle-make-it-smart
    at: smart_gaps[0]
    changed: "Left Measurable open instead of inventing a done condition."
  - name: principle-make-it-smart
    at: smart_gaps[1]
    changed: "Left Relevant open instead of inventing a decision-maker."
  - name: principle-make-it-smart
    at: smart_gaps[2]
    changed: "Left Time-bound open instead of inventing a deadline."
stop: true
```

The operator answers the Measurable and Time-bound prompts. "We will know it is solved when the review names one cause that matches the logs. We need that before Thursday's exec review." The next invocation is define-the-problem again, on the same primary. `classify-2x2` still classifies that primary statement. The new excerpts enter `smart_question` because the operator said them. Relevant stays open. The prevention row stays.

```yaml
main_question: "Why did staging go down last night?"
smart_question: "Why did staging go down last night, settled by one cause that matches the logs, before Thursday's exec review?"
smart_gaps:
  - Relevant
```

The eval reads `verdict.smart`.

```python
outcome = parse_response(text)
assert isinstance(outcome, Response)
assessment = outcome.verdict.smart
wire = project(assessment)
```

A test that simulates the Thursday answer calls the same function the skill describes.

```python
notes = notes_for_turn(
    primary="Why did staging go down last night?",
    prior_primary="Why did staging go down last night?",
    ask_excerpts=(
        GroundedLetter("Specific", "staging went down last night", "ask"),
        GroundedLetter("Actionable", "exactly why", "ask"),
    ),
    answers=(
        ("Measurable", "one cause that matches the logs"),
        ("Time-bound", "before Thursday's exec review"),
    ),
    cards=load_cards(SKILL_DIR),
)
assessment = assess(
    primary="Why did staging go down last night?",
    notes=notes,
    draft="Why did staging go down last night, settled by one cause that matches the logs, before Thursday's exec review?",
    cards=load_cards(SKILL_DIR),
)
```

`draft` is the agent's sentence. `assess` keeps it only when Specific and Actionable are grounded. The agent writes the English.

## Shape

The object that changes is a gap. A card registry defines the five letters, their order, their prompts, and which two are required. `notes_for_turn` and `parse_smart` are the only adapters into `assessment_from_gaps`. That function is the only constructor of a `SmartAssessment`. Per principle-model-the-domain, each letter is a slot in that ordered registry. The playbook, the parser, and the grader all read the slot.

Per principle-redesign-from-first-principles, the assessment is a field of `Verdict` from the start of this design. Status derivation, `main_question` equality, and the one-primary limit stay where they are.

### Module map

```text
skills/whats-going-on/                         # canonical tree, the only one to edit by hand
  SKILL.md                                     # Select row, principle index, at table
  README.md                                    # contract block and principles table
  playbooks/define-the-problem.md              # smart is step 7, classify is step 8
  smart/SKILL.md                               # Cards fence plus the step procedure
  principle-make-it-smart/SKILL.md             # letter grounding
  principle-dont-solve-yet/SKILL.md            # governs gains smart
  classify-2x2/SKILL.md                        # one sentence, classify the primary statement

evals/whats-going-on/whats_going_on_eval/
  smart.py                                     # registry, notes, assessment, projections
  parse.py                                     # VERDICT_KEYS, Verdict.smart, check order
  principles.py                                # WireKind gains smart
  grade.py                                     # concerns exclude gap rows
  drift.py                                     # embedded gold gains the two keys
  invariance.py                                # embedded gold gains the two keys
  manifest.py                                  # SUITE_VERSION becomes 2

plugins/whats-going-on/skills/whats-going-on/  # rsync of the canonical tree
.agents/skills/whats-going-on/                 # rsync of the canonical tree
```

Agent path. The playbook names step 7, `smart/SKILL.md` runs it, and the principle leaf is the rule it cites. Eval path. `parse.py` calls `parse_smart`, which calls `assessment_from_gaps`. Grader path. `grade.py` calls `partition_unresolved`. None of these paths needs a fourth file. Per principle-minimize-reader-load and principle-laziness-protocol, the assessment is a field on the one `Verdict`, and excerpts stay off the wire.

`assert_skill_tree_clean` already allows a directory named by the playbook `skills` list or by the principle index. Adding `smart` to the playbook list and `principle-make-it-smart` to the index is what mounts both files. `derive_mount` will pick them up. README stays off the mount.

### How a letter is read

Five cards, in fixed order. A gap is a card with no excerpt. An answer names a letter and replaces that slot. The parser matches an `unresolved` row to a card by exact prompt. The grader uses that same match to hide gap rows from the concern scorer. Five entries are the whole set, so the access is a scan of the registry. No index is added later.

`project` is the inverse of the two wire fields. Tests use it. `Verdict.smart` stays the assessment. Per principle-boundary-discipline, callers inside the eval read that assessment and trust it.

### Types and signatures

Bodies are not implemented. Cards load from `smart/SKILL.md`. Prompt sentences exist only in that fence. `REQUIRED_TO_PROPOSE` is the locked pair, and the loader rejects a fence whose required flags differ.

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .parse import ContractViolation, Problems, Unresolved

SmartLetter = Literal["Specific", "Measurable", "Actionable", "Relevant", "Time-bound"]
SMART_LETTERS: tuple[SmartLetter, ...] = (
    "Specific",
    "Measurable",
    "Actionable",
    "Relevant",
    "Time-bound",
)
REQUIRED_TO_PROPOSE: frozenset[SmartLetter] = frozenset({"Specific", "Actionable"})
ExcerptSource = Literal["ask", "answer"]


@dataclass(frozen=True)
class SmartCard:
    letter: SmartLetter
    prompt: str
    required_to_propose: bool


@dataclass(frozen=True)
class GroundedLetter:
    letter: SmartLetter
    text: str
    source: ExcerptSource

    def __post_init__(self) -> None:
        """Reject a blank excerpt. The caller leaves the letter open instead."""
        raise NotImplementedError("not implemented")


@dataclass(frozen=True)
class OpenLetter:
    letter: SmartLetter


LetterState = GroundedLetter | OpenLetter


@dataclass(frozen=True)
class SmartGap:
    letter: SmartLetter


@dataclass(frozen=True)
class NoPrimary:
    """No primary. The wire question is null and the wire gaps are empty."""


@dataclass(frozen=True)
class QuestionAbsent:
    """A primary exists. Specific, Actionable, or both are open. The question is null."""

    gaps: tuple[SmartGap, ...]

    def __post_init__(self) -> None:
        """Reject gaps that include none of the required letters."""
        raise NotImplementedError("not implemented")


@dataclass(frozen=True)
class QuestionProposed:
    """A primary exists. Both required letters are grounded. The question is non-empty."""

    question: str
    gaps: tuple[SmartGap, ...]

    def __post_init__(self) -> None:
        """Reject a blank question and any required letter still in gaps."""
        raise NotImplementedError("not implemented")


SmartAssessment = NoPrimary | QuestionAbsent | QuestionProposed


def load_cards(skill_dir: Path) -> tuple[SmartCard, ...]:
    """Read the Cards fence. Fail if the letters differ from SMART_LETTERS.

    Fail if the required flags differ from REQUIRED_TO_PROPOSE.
    Fail if any prompt is blank. Cache the successful tuple.
    """
    raise NotImplementedError("not implemented")


def gap_row(card: SmartCard) -> Unresolved:
    """The only template for a SMART unresolved row.

    observation is "The primary does not ground <letter>."
    reason is "That SMART letter is still open."
    clarification is card.prompt, copied exactly.
    """
    raise NotImplementedError("not implemented")


def notes_for_turn(
    primary: str | None,
    prior_primary: str | None,
    ask_excerpts: tuple[GroundedLetter, ...],
    answers: tuple[tuple[SmartLetter, str], ...],
    cards: tuple[SmartCard, ...],
) -> tuple[LetterState, ...] | ContractViolation:
    """Build one state per card.

    A missing primary rejects excerpts and answers and returns five open
    letters. A present primary whose prior_primary differs, or is missing,
    rejects a non-empty answers tuple and uses ask_excerpts only. An
    unchanged primary applies excerpts, then answers in order. The later
    pair for a letter replaces the earlier one. A blank answer text is a
    violation. An unknown or duplicate letter is a violation.
    """
    raise NotImplementedError("not implemented")


def assessment_from_gaps(
    has_primary: bool,
    draft: str | None,
    gaps: tuple[SmartGap, ...],
    cards: tuple[SmartCard, ...],
) -> SmartAssessment | ContractViolation:
    """The only constructor of a SmartAssessment.

    Check has_primary before the required-letter test. Empty gaps and a null
    draft with no primary return NoPrimary. A draft or any gap with no primary
    is a violation. Gaps must be known letters, unique, and in card order.
    With a primary, any required letter in gaps requires a null draft and
    returns QuestionAbsent. With a primary, no required letter in gaps
    requires a non-blank draft and returns QuestionProposed. Empty gaps with
    a primary are QuestionProposed, never NoPrimary.
    """
    raise NotImplementedError("not implemented")


def assess(
    primary: str | None,
    notes: tuple[LetterState, ...],
    draft: str | None,
    cards: tuple[SmartCard, ...],
) -> SmartAssessment | ContractViolation:
    """Turn notes into gaps in card order, then call assessment_from_gaps.

    Notes must contain each card once. The caller supplies draft.
    """
    raise NotImplementedError("not implemented")


def project(assessment: SmartAssessment) -> tuple[str | None, tuple[SmartLetter, ...]]:
    """Return the wire question and the wire gap letters, in card order."""
    raise NotImplementedError("not implemented")


def partition_unresolved(
    rows: tuple[Unresolved, ...],
    cards: tuple[SmartCard, ...],
) -> tuple[tuple[Unresolved, ...], tuple[Unresolved, ...]]:
    """Return concern rows, then SMART rows.

    A row is a SMART row when its clarification equals a card prompt.
    """
    raise NotImplementedError("not implemented")


def parse_smart(
    raw_question: object,
    raw_gaps: object,
    problems: Problems,
    unresolved: tuple[Unresolved, ...],
    cards: tuple[SmartCard, ...],
) -> SmartAssessment | ContractViolation:
    """Parse the two wire fields and the projected rows.

    Call assessment_from_gaps with has_primary taken from problems.
    Every gap's gap_row(card) must equal exactly one unresolved row.
    Every unresolved row whose clarification is a card prompt must be that gap.
    Other unresolved rows are left alone.
    """
    raise NotImplementedError("not implemented")
```

`project` matches on the three variants and ends with `assert_never` so a fourth variant fails the type check. `assessment_from_gaps` is the gate both the notes path and the YAML path use. Per principle-type-system-discipline, `QuestionProposed` cannot hold an open Specific or Actionable, and `NoPrimary` cannot hold a question. Per principle-encode-lessons-in-structure, the required pair is `REQUIRED_TO_PROPOSE`, and a fence that disagrees fails the load.

`Verdict.smart` holds the assessment. `project` is what turns it back into the two wire fields. `WireKind` gains `"smart"`. `_resolve_at` maps `smart_question` to `smart` on every verdict, and `smart_gaps[<i>]` to `smart` when that index is inside `project(assessment)[1]`. A dotted path under `smart_question` fails `principle_at`. Halt wires keep `HALT_KEYS`.

`principle-make-it-smart` governs `smart` only. `principle-dont-solve-yet` governs `problem`, `unresolved`, and `smart`, so a fix written into the SMART question has an owner. Letter grounding stays with `principle-make-it-smart`. A citation of `principle-dont-invent-problems` at `smart_question` is `principle_governs`.

### Skill instructions

`smart/SKILL.md` frontmatter sets `name: smart`, `disable-model-invocation: true`, and a one-sentence description of the step. The Cards section is this fence and nothing else that restates the prompts.

```yaml
letters:
  - letter: Specific
    required_to_propose: true
    prompt: "Would someone new to this know exactly which problem it is?"
  - letter: Measurable
    required_to_propose: false
    prompt: "How will we know it is solved?"
  - letter: Actionable
    required_to_propose: true
    prompt: "Does it point to something we can do?"
  - letter: Relevant
    required_to_propose: false
    prompt: "Does it matter to the people who will decide?"
  - letter: Time-bound
    required_to_propose: false
    prompt: "By when does it need to be solved?"
```

The procedure in that file is `notes_for_turn`, then `assess`.

1. If there is no primary, emit `smart_question: null` and `smart_gaps: []`. Do not add a card prompt to `unresolved`. Stop the step.
2. If the latest define-the-problem verdict exists and its primary statement equals this turn's primary, start from excerpts in the original ask and pass answers only for letters that were open. If the statement differs, pass an empty answers tuple and take excerpts from the current input only. `notes_for_turn` rejects answers on a changed primary.
3. A letter is grounded only by a verbatim excerpt from the ask, marked `ask`, or from an answer to that letter's prompt, marked `answer`. Do not use the prior `smart_question` as an excerpt.
4. Pass a draft sentence only when Specific and Actionable both have excerpts. Otherwise pass null. The draft may use the primary statement and the grounded excerpts. It may not add a fact from an open letter.
5. Render `smart_gaps` from the open letters, in card order. For each open letter, append the `unresolved` row from `gap_row`. Leave deferred rows in place.
6. Cite `principle-make-it-smart` at `smart_question` when the rule kept the question null or stripped an invented detail. Cite it at `smart_gaps[<i>]` when the rule kept that letter open. Do not also cite it on the projected `unresolved` row. Omit it when the step did not run, and when the question copies a plainly grounded primary.

`principle-make-it-smart/SKILL.md` follows the house shape. `governs: [smart]`. `disable-model-invocation: true`.

Rule. Ground each letter from the ask or from an answer to that letter's prompt. Both Specific and Actionable are required before a question. If either is open, the question is null. Never add a metric, a date, a person, or an action the excerpt does not contain. Never rewrite `main_question`.

When. Each time a primary exists and the step writes `smart_question` or `smart_gaps`.

Cite or omit. As the procedure above.

Failure signature. The question names a number, a deadline, or a cause the text never gave. A letter is absent from `smart_gaps` even though no excerpt supports it. The question is set while Specific or Actionable is listed. `main_question` changes to the SMART wording.

Distinct from. `principle-dont-invent-problems` decides whether a problem exists. `principle-read-the-room` picks the primary. `principle-dont-solve-yet` stops a fix from being written into the question.

The coordinator index bullet uses the em dash `principles.py` already requires.

```text
- principle-make-it-smart — deciding whether the primary can be stated as a SMART question, and which letters stay open.
```

`principle-dont-solve-yet` adds `smart` to `governs`. Its When line includes writing `smart_question`. Its Cite line adds a citation at `smart_question` when the rule kept a fix, a cause, or a plan out of that question. The README principles table gains the new row, and the dont-solve-yet governs cell gains `smart`, or `_principles_drift` fails.

`classify-2x2/SKILL.md` gains one sentence. Classify `problems[0].statement`. Ignore `smart_question` and `smart_gaps`. A deadline that arrives as an answer must not flip the quadrant unless step 6 changed the primary statement. That keeps principle-read-the-room's rule that more information alone does not flip a quadrant.

### Playbook and coordinator

Playbook frontmatter `skills` becomes `[ask, restate, separate, extract, clarity, smart, classify-2x2]`.

The step table inserts smart after primary and moves classify to step 8.

| Step | Skill | Reads | Writes |
|---|---|---|---|
| 6 | Primary | Defined rows | primary, deferred rows |
| 7 | `smart` | primary, input, latest verdict when the message answers a gap | smart assessment |
| 8 | `classify-2x2` | primary statement | classification |

Step 7 runs only when step 6 produced a primary. Step 8 runs whenever a primary exists, including when the assessment is `QuestionAbsent`. The repair paragraph is unchanged. A restatement that answers a SMART prompt still disagrees with the unresolved rows, and the playbook already discards it.

The status table is not edited. Gap rows are unresolved rows, so a primary with any open letter derives `partial` unless other unresolved rows already made that true. A fully grounded primary with no deferred rows stays `classified`.

The output contract gains the two fields directly under `main_question`. README and the playbook stay byte-identical on that block, or `_contract_drift` fails. The keys then equal `VERDICT_KEYS`.

```yaml
status: classified | partial | needs_clarification | not_a_problem

main_question: "The primary's statement, word for word" | null

smart_question: "SMART wording of that same primary" | null

smart_gaps:
  - Specific | Measurable | Actionable | Relevant | Time-bound

problems:
```

The rest of the block is today's `problems`, `unresolved`, `applied`, and `stop`. The Never list gains three lines. Do not copy `smart_question` into `main_question`. Do not skip classify because a letter is open. Do not emit a card prompt except as `gap_row` for a listed gap.

The coordinator Select table gains a row above continue. If the latest result is define-the-problem and the message answers one of its open SMART prompts without naming a different problem, run define-the-problem again. Continue still advances the chain. The new row is first so an answer cannot Halt into stage 2. Step 6 still picks the primary. If it picks a different statement, `notes_for_turn` refuses the old answers.

The coordinator `at` table gains two rows.

| `at` | kind |
|---|---|
| `smart_question` | `smart` |
| `smart_gaps[<i>]` | `smart` |

### Parser check order

`VERDICT_KEYS` gains `smart_question` and `smart_gaps`. `HALT_KEYS` stay as they are. For a verdict fence, `_validate_wire` keeps today's order through `main_question`, then parses SMART, then parses `applied`.

1. Unknown keys, `stop`, `status`, `problems`, and `unresolved` stay as they are.
2. Derived status must equal the claimed status. Gap rows already count here.
3. `main_question` must equal the primary statement, or be null when `problems` is empty.
4. `smart_question` and `smart_gaps` are required. `parse_smart` either returns the assessment or a `schema` violation.
5. `applied` resolves `smart_gaps[<i>]` against that assessment.

An invalid fixture that already fails at step 2 or step 3 does not need the new keys. An invalid fixture that fails inside `applied` must include a legal SMART projection, or it will fail at step 4 before the `expect_kind` under test. Halt fixtures stay free of both keys.

`SUITE_VERSION` becomes 2. Gold fences change, and some classified fixtures become `partial` once a real letter is open. Old run reports stay labeled as suite 1.

New schema cases, one behavior each.

- Primary, null question, gaps contain Specific, matching `gap_row`, derived `partial`.
- Primary, non-null question, gaps are Measurable then Time-bound, matching rows, derived `partial` when those rows are the only unresolved rows.
- No primary, null question, empty gaps, no card prompt in `unresolved`.
- Question set while Specific is a gap.
- Null question while neither Specific nor Actionable is a gap, with a primary.
- Unknown letter, duplicate letter, and letters out of card order.
- Gap with no matching row, and a card prompt in `unresolved` with no gap.
- Empty `problems` with a non-empty `smart_gaps`.
- `principle-make-it-smart` at `smart_question` accepted, and the same name at `unresolved[0]` rejected.
- `principle-dont-solve-yet` at `smart_question` accepted, and `principle-dont-invent-problems` at `smart_question` rejected.

### Grader

`partition_unresolved` runs before anchor matching. `_abstention_score` and `_classify_abstention` see concern rows only. A SMART-only extra row does not produce the 0.5 penalty that an unexpected concern row produces. `verdict.status` is still the detection input, so a fixture whose gold becomes `partial` must list `partial` in `expect.statuses`. Concern anchors stay the deferred problems. They do not gain card prompts.

`prose_fields` adds `smart_question` from `project`, so `GLOBAL_SOLVE_LEAK` covers the new sentence. Invented-detail tripwires already scan the whole reply, which includes the question. Card prompts are questions, and the locked five do not match the solve-leak patterns. A prompt edit that says "you should" would start failing gold. That is acceptable.

Family derivation reads fixture expectations. SMART rows stay out of `expect.unresolved`, so `clear_single` and `compound` stay stable.

`_seed_readme_drift` also compares `project(gold.smart)` for the README case and the fixture gold. A README that shows a different question or a different gap list fails drift.

Every verdict gold under `fixtures/`, `schema_cases/`, `drift.py`, and `invariance.py` gains the two keys. The implementer judges excerpts per fixture. This design does not pre-label which current cases are fully grounded.

### Canonical copies

Edit `skills/whats-going-on/` only. Rsync that directory onto `plugins/whats-going-on/skills/whats-going-on/` and `.agents/skills/whats-going-on/`. `scripts/assert-canonical-skill.sh` diffs those trees and fails on a hand-edited copy. Host installs stay on `scripts/install-local.sh`, which already excludes `evals/`.

### Invariants the types hold

- No primary is `NoPrimary`. Question null, gaps empty, no card prompt in `unresolved`. Abstention is unchanged.
- A question exists only as `QuestionProposed`, which requires both Specific and Actionable to be absent from `gaps`.
- `smart_gaps` is exactly the open letters, in registry order, with no duplicates and no unknown names.
- Each gap has one `unresolved` row equal to `gap_row`. The five prompt sentences are reserved.
- `main_question` is still compared to `problems[0].statement` and is never taken from `smart_question`.
- `problems` still holds at most one item. The SMART wording stays outside `problems`.
- Classify still receives the primary statement when the assessment is `QuestionAbsent`.
- `notes_for_turn` takes excerpts and answers. The signature has no prior question, so an invented sentence cannot become the next excerpt.

Per principle-foundational-thinking, these variants come before the playbook prose. The skill procedure names `NoPrimary`, `QuestionAbsent`, and `QuestionProposed`.

### Interface depth

The operator sees two fields and five prompts. The agent runs one step and cites one principle at `smart_question` or `smart_gaps[<i>]`. The eval caller keeps calling `parse_response` and reads `verdict.smart`.

Hidden behind that interface are card order, the required pair, the row template, the restart rule for answers, and the refusal to treat a prior question as evidence. The status table stays visible because operators and the grader already depend on it. Per principle-experience-first, the two questions sit next to each other in the fence so the operator can answer a gap without mistaking the SMART wording for a new primary.

### Idempotence and shared state

`notes_for_turn` with the same arguments returns the same notes, including when the same answer pair is repeated. A second different text for one letter replaces the first. A crash mid-reply leaves no file. The next turn reads the last complete fence, or the ask alone when no fence parsed. Per principle-make-operations-idempotent, the step derives from the current ask, the current primary, and the answers in hand.

One invocation writes one fence. Nothing else stores the assessment. Per principle-separate-before-serializing-shared-state, there is no shared write target and no lock to add. A side file of excerpts was considered and rejected below.

### Red-flag screen

- Shallow module. One step produces the assessment. Callers do not pre-check Specific and Actionable themselves.
- Information leakage. Prompt text lives in the Cards fence. Python reads it. `Verdict` does not re-export the wire strings.
- Temporal decomposition. The first pass and the answer fold both go through `notes_for_turn` and `assessment_from_gaps`. There is no separate validate module.
- Pass-through. `parse.py` adapts a fence into `parse_smart`. It does not forward the assessment unchanged to another parser.
- Split ownership. The assessment owns the letter. The unresolved row is a checked copy. `derive_status` still owns status.
- Two ways. `assessment_from_gaps` is the only constructor. Hand-built YAML that skips `gap_row` fails parse.
- Importable internals. The card regex and the required-letter helper stay private to `smart.py`. Tests import the functions listed above.
- Hand-synced list. Letter order is `SMART_LETTERS`. The fence must match it. Contract keys stay glued to `VERDICT_KEYS` by the drift check that already exists.

## Synthesis decision

Arena fills this section. This runner does not pick a base.

## Tradeoffs accepted

- We accept a second null state, `NoPrimary` versus `QuestionAbsent`, in exchange for a question that cannot appear on an abstention.
- We accept generic card prompts, with no interpolation of the primary, in exchange for a clarification string the parser can match exactly.
- We accept re-reading the ask on every turn, in exchange for keeping invented wording out of the next turn's evidence.
- We accept that some fixtures move from `classified` to `partial`, in exchange for leaving the status table as the only status rule.
- We accept citations of `principle-make-it-smart` on `smart_gaps[<i>]` alone, in exchange for one citation site per decision.
- We accept that a subtle invented phrase with no tripwire token can still score, in exchange for not adding a sixth rubric axis. Structural lies fail parse. The residual matches the residual the suite already has for problem statements.

## Alternatives considered

Optional strings on `Verdict` lost. `smart_question: str | None` and `smart_gaps: tuple[str, ...]` would leave Specific and Actionable as a comment in the skill. Every caller would re-check the gate, and the unresolved prompt would be a second list with no owner. The public interface would be smaller by one type and would hide nothing.

A sibling `SmartVerdict` parsed beside `Verdict` lost. Grade, drift, and fixtures would thread a second object through a fence that is still one mapping. The extra type would hide the YAML adapter and would expose a pairing rule every caller must remember. `Verdict.smart` keeps one parse result.

Persisting excerpts on the wire lost. The next turn could trust a prior invention without reading the ask. The operator would read spans that do not help them answer. `notes_for_turn` has no parameter for the prior question, so the signature leaves that path out.

A new status, or holding classify until all five letters are grounded, lost. Both contradict the locked rule that classify runs on the primary and that gaps become `partial` through the existing table. They also give status a second owner.

## Open questions and risks

- Which current `classified` fixtures have an excerpt for each letter? The answer changes gold status, and it is a reading of each input.
- Should a later answer that contradicts an earlier answer for the same letter replace it, as `notes_for_turn` does, or should the contradiction reopen the letter?
- Should the grader hard-fail when `smart_question` introduces a digit or a month name that the input and the answers do not contain? Parse cannot see the ask, and this design leaves that class of invention to tripwires and to the principle.

## Next implementation step

Write the Cards fence and `assessment_from_gaps` first, then reject an illegal `smart_question` and `smart_gaps` pair inside `parse_response` before any playbook prose beyond the step row.
