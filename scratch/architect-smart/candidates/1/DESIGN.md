# Candidate 1. Prompt-keyed gap ledger

Goal. Stage 1 of `/whats-going-on` proposes one SMART problem question from the ask, after the primary is chosen and before it is classified. The output gains `smart_question` and `smart_gaps`. Each missing SMART letter becomes an `unresolved` row that asks the operator an "Ask yourself" question. When the operator answers, the next run updates `smart_question`. `main_question` stays the primary's statement.

Shape in one sentence. The SMART card table in `smart/SKILL.md` is the only list of letters and prompts. An `unresolved` row is a SMART gap exactly when its `clarification` is `Ask yourself: <card prompt>`. `smart_gaps` is an index the parser checks against those rows. Answering a gap is new facts, so the next run re-derives everything from the input and carries no SMART state.

## Problem

Stage 1 today runs `ask → restate → separate → extract → clarity → primary → classify-2x2` and emits `{status, main_question, problems, unresolved, applied, stop}`. The parser (`parse.py`) derives `status` from whether `problems` and `unresolved` are empty, requires `main_question == problems[0].statement`, and resolves every `applied[].at` through `_resolve_at` to a `WireKind` that the cited principle must `govern`. Drift (`drift.py`) ties the README contract block keys to `VERDICT_KEYS`, the README principles table to the coordinator index and each leaf's `governs`, and the seed fixtures to README Cases A to J.

The shape is non-obvious for four reasons.

1. Variant C routes gaps through `unresolved`, which already carries deferred Defined rows and undefined concerns. A gap row must be distinguishable from those rows without a new key on `unresolved`, or the parser cannot check `smart_gaps` against anything.
2. The five SMART prompts are user-facing text that must appear in the skill leaf, in the README, and in every gap row. That is a hand-synced list waiting to drift.
3. "Update `smart_question` when answered" sounds like lifecycle state. Stage 1 is a snapshot, not a lifecycle (README Case J), and live eval runs use a fresh session per turn.
4. Gap rows make `unresolved` non-empty, so the existing status table turns many `classified` cases into `partial`. Variant C accepts that. It changes seed golds and README cases, and it must not touch abstention.

Constraints honored. Canonical skill at `skills/whats-going-on/`, plugin copy synced and checked by `scripts/assert-canonical-skill.sh`. Mount stays derived (`chain.derive_mount`), so a new leaf only needs to appear in the playbook `skills` list and a new principle only in the coordinator index. Invariants: don't invent, one primary, abstention unchanged, no solving.

## Usage (caller's view)

### Skill user, first turn

```text
/whats-going-on

From a teammate after a messy on-call week:
"We hired three new people onto the platform squad.
How do we build a healthy on-call culture over the next year?"
```

```yaml
status: partial

main_question: "What approaches could build a healthy on-call culture on the platform squad over the next year?"

problems:
  - statement: "What approaches could build a healthy on-call culture on the platform squad over the next year?"
    classification:
      nature: conceptual
      direction: divergent
    confidence: high
    why: "Culture and norms are conceptual. The ask invites many possible moves."
    next_method: "Broad exploration of approaches before any narrowing. Do not brainstorm the list in this slice."

smart_question: "What approaches could build a healthy on-call culture on the platform squad over the next year?"

smart_gaps: [measurable, relevant]

unresolved:
  - observation: "The ask says healthy but not what healthy looks like"
    reason: "SMART measurable is missing. The input gives no sign of done."
    clarification: "Ask yourself: How will we know it is solved?"
  - observation: "The ask does not say who decides on on-call changes"
    reason: "SMART relevant is missing. The input names no decider or stake."
    clarification: "Ask yourself: Does it matter to the people who will decide?"

applied:
  - name: principle-make-it-smart
    at: unresolved[0]
    changed: "Asked for a sign of done instead of treating healthy as measurable."
  - name: principle-dont-invent-problems
    at: smart_question
    changed: "Kept the SMART question to the input's own scope instead of adding a metric."

stop: true
```

The primary is classified anyway. `status` is `partial` only because gap rows sit in `unresolved`.

### Skill user, answering a gap

```text
/whats-going-on

Healthy means nobody carries more than one week of pages a month. The platform lead decides.
```

The coordinator's Select table already routes "new facts" to define-the-problem. The new rule says the input for that run is the earlier ask plus these answers. The run re-derives from scratch:

```yaml
status: classified
main_question: "What approaches could build a healthy on-call culture on the platform squad over the next year?"
problems: [ ...same primary, same quadrant... ]
smart_question: "What approaches could the platform lead adopt so nobody on the platform squad carries more than one week of pages a month within the next year?"
smart_gaps: []
unresolved: []
applied: []
stop: true
```

`main_question` did not move. `smart_question` absorbed the answers because they are now input facts.

### Skill user, Specific or Actionable missing

Input: `EU customers keep saying our pricing page is confusing. Is it?`

```yaml
status: partial
main_question: "Is the pricing page confusing to EU customers?"
problems: [ ...classified primary... ]
smart_question: null
smart_gaps: [measurable, actionable, time-bound]
unresolved:
  - { observation: "...", reason: "SMART measurable is missing. ...", clarification: "Ask yourself: How will we know it is solved?" }
  - { observation: "...", reason: "SMART actionable is missing. ...", clarification: "Ask yourself: Does it point to something we can do?" }
  - { observation: "...", reason: "SMART time-bound is missing. ...", clarification: "Ask yourself: By when does it need to be solved?" }
applied:
  - name: principle-make-it-smart
    at: smart_question
    changed: "Withheld the SMART question because the ask points to nothing we can do yet."
stop: true
```

`smart_gaps` and the gap rows both follow card order (specific, measurable, actionable, relevant, time-bound). The parser rejects any other order.

### Abstention, unchanged

Case A (vague) and Case I (FYI) emit `smart_question: null` and `smart_gaps: []`. The smart step never runs without a primary. No gap rows appear, so `needs_clarification` and `not_a_problem` derive exactly as today.

### Eval call sites

`grade.py` reads the proposal as one typed value:

```python
match response.verdict.smart:
    case NoPrimary():
        ...
    case Withheld(gaps=gaps):
        ...
    case Proposed(question=q, gaps=gaps):
        prose_fields["smart_question"] = q
    case _ as unreachable:
        assert_never(unreachable)
```

Fixture YAML gains one optional block per turn:

```yaml
expect:
  kind: classify
  statuses: [partial]
  problems: [...]
  unresolved: [...]
  smart:
    proposal: proposed      # proposed | withheld
    gaps: [measurable, relevant]
```

`drift.py` gains one call, and the README key check needs no edit because it already compares against `VERDICT_KEYS`:

```python
problems.extend(_smart_cards_drift(readme))
```

Operator commands do not change: `python -m whats_going_on_eval check`, then `run --agent cursor --only case-d,case-k --repeat 1`.

## Shape

### Data first

One registry, parsed from the leaf. The card table in `skills/whats-going-on/smart/SKILL.md` is the source of truth:

```markdown
## Cards

| Letter | Prompt |
|---|---|
| `specific` | Would someone new to this know exactly which problem it is? |
| `measurable` | How will we know it is solved? |
| `actionable` | Does it point to something we can do? |
| `relevant` | Does it matter to the people who will decide? |
| `time-bound` | By when does it need to be solved? |
```

New eval module `whats_going_on_eval/smart.py` owns everything about SMART on the eval side:

```python
SmartLetter = Literal["specific", "measurable", "actionable", "relevant", "time-bound"]
SMART_LETTERS: tuple[SmartLetter, ...] = get_args(SmartLetter)
REQUIRED_TO_PROPOSE: frozenset[SmartLetter] = frozenset({"specific", "actionable"})
ASK_YOURSELF = "Ask yourself: "


@dataclass(frozen=True)
class Card:
    letter: SmartLetter
    prompt: str


@dataclass(frozen=True)
class NoPrimary:
    """Smart step did not run. Wire: smart_question null, smart_gaps []."""


@dataclass(frozen=True)
class Withheld:
    """Specific or actionable is missing. Wire: smart_question null."""
    gaps: tuple[SmartLetter, ...]  # card order, non-empty, intersects REQUIRED_TO_PROPOSE


@dataclass(frozen=True)
class Proposed:
    question: str
    gaps: tuple[SmartLetter, ...]  # card order, disjoint from REQUIRED_TO_PROPOSE


SmartProposal = NoPrimary | Withheld | Proposed


@dataclass(frozen=True)
class SmartLint:
    kind: str
    detail: str


def load_cards(skill_dir: Path) -> tuple[Card, ...]:
    """Parse `## Cards` in smart/SKILL.md. Letters must equal SMART_LETTERS in order."""
    raise NotImplementedError


def lint_cards(skill_dir: Path) -> tuple[SmartLint, ...]:
    raise NotImplementedError


def gap_letter(row: Unresolved, cards: tuple[Card, ...]) -> SmartLetter | None:
    """The letter whose `Ask yourself: <prompt>` equals row.clarification, else None."""
    raise NotImplementedError


def parse_smart(
    raw: Mapping[str, Any],
    problems: Problems,
    unresolved: tuple[Unresolved, ...],
) -> SmartProposal | ContractViolation:
    """
    Boundary for the two SMART keys. Rules, each a ContractViolation kind:
      smart_schema       keys missing, smart_gaps not a list of SmartLetter, duplicates
      smart_order        smart_gaps not in card order
      smart_without_primary  problems empty and (question not null or gaps non-empty)
      smart_gap_rows     set(smart_gaps) != {gap_letter(r) for r in unresolved if not None},
                         or two rows share a letter
      smart_gap_tail     gap rows are not a contiguous suffix of unresolved in card order
      smart_proposed_without_required   question not null and gaps ∩ REQUIRED_TO_PROPOSE
      smart_withheld_without_reason     question null, primary present, gaps ∩ REQUIRED empty
    """
    raise NotImplementedError
```

`smart.py` imports `Unresolved`, `Problems`, and `ContractViolation` from a small `wire.py` split out of `parse.py`, so `parse.py → smart.py` stays acyclic with top-level imports. If that split feels heavy, `smart.py` can take `clarifications: tuple[str, ...]` instead of rows. The sketch prefers rows for readable errors.

### Changes to existing eval types

```python
# parse.py
VERDICT_KEYS = frozenset({
    "status", "main_question", "problems", "smart_question", "smart_gaps",
    "unresolved", "applied", "stop",
})

@dataclass(frozen=True)
class Verdict:
    status: Status
    main_question: str | None
    problems: Problems
    smart: SmartProposal
    unresolved: tuple[Unresolved, ...]
    applied: tuple[Applied, ...]

# principles.py
WireKind = Literal["status", "problem", "classification", "confidence", "smart_question", "unresolved"]

# parse._resolve_at gains one arm:
#   "smart_question" resolves to kind "smart_question" when problems is non-empty, else None.
#   Gap rows keep resolving as "unresolved[<i>]" with kind "unresolved".

# fixtures.py
@dataclass(frozen=True)
class SmartExpect:
    proposal: Literal["proposed", "withheld"]
    gaps: tuple[SmartLetter, ...]

@dataclass(frozen=True)
class Expectation:
    ...                         # unchanged fields
    smart: SmartExpect | None   # None on abstain turns; required on classify turns
```

Order inside `_validate_wire` is load-bearing. Problems and unresolved parse first. `derive_status` runs unchanged. `_parse_main_question` runs unchanged. `parse_smart` runs next, then `_parse_applied`. Status needs no SMART awareness because gap rows are ordinary `unresolved` rows, so the locked "gaps make it partial" rule falls out of the existing table.

### Flow through the playbook

```text
| 6 | Primary (this playbook) | Defined rows        | primary, deferred rows |
| 7 | `smart`                 | input, primary      | smart note, gap rows   |
| 8 | `classify-2x2`          | primary             | classification         |
```

Step 7 checks the primary against each card using only input facts. A letter is met only when the input states it. Each unmet letter writes one Unresolved row whose `clarification` is `Ask yourself: ` plus the card prompt, word for word. Gap rows go after deferred rows, in card order. With `specific` or `actionable` unmet, `smart_question` is `null`. Otherwise it is the primary rewritten to carry every met letter's input facts. With no primary, step 7 does not run. Step 8 classifies the primary, never `smart_question`.

### Who owns which rule

| Rule | Owner | Others point at it |
|---|---|---|
| Letters, prompts, card order | `smart/SKILL.md` `## Cards` | README table (drift-checked), parser via `load_cards` |
| Proposal mechanics, `Ask yourself:` row form, gap rows last | `smart/SKILL.md` | playbook step 7 names it |
| When a letter counts as met, when to withhold | `principle-make-it-smart` | `smart` leaf says "per principle-make-it-smart" |
| Never add a letter's fact the input lacks | `principle-dont-invent-problems` | `make-it-smart` says "inventing is that principle's call" |
| `main_question` is the primary statement | playbook Output, parser | unchanged |
| Answers are new facts | coordinator Select table | README Case L |

`principle-make-it-smart` frontmatter: `governs: [smart_question, unresolved]`. `principle-dont-invent-problems` gains `smart_question` in `governs`, so it can be cited when it kept a letter's fact out of the SMART question. The README principles table must match both, and existing drift enforces that.

### Module map

Skill side (canonical, then `rsync` to `plugins/whats-going-on/skills/whats-going-on/`, then `scripts/assert-canonical-skill.sh`):

| Path | Change |
|---|---|
| `smart/SKILL.md` | New leaf. Frontmatter `disable-model-invocation: true`. `## Cards` table, step mechanics, row form, ordering, no solving |
| `principle-make-it-smart/SKILL.md` | New principle. Rule, When, Cite or omit, Failure signature, Distinct from |
| `principle-dont-invent-problems/SKILL.md` | `governs` adds `smart_question`. One Cite line for `smart_question` |
| `SKILL.md` | Principles index adds one bullet. `at` table adds `smart_question`. Select table adds the answer rule |
| `playbooks/define-the-problem.md` | `skills` adds `smart`. Step 7 row and paragraph. Output contract adds two keys. Never adds "classify `smart_question`" and "write a gap row without its card prompt" |
| `README.md` | Contract block, principles table, a short SMART section with the card table, golds of Cases B to H re-derived, new Case K (withheld) and Case L (answer turn) |

Eval side:

| Path | Change |
|---|---|
| `whats_going_on_eval/smart.py` | New. Registry, `SmartProposal`, `parse_smart`, `gap_letter`, `lint_cards` |
| `whats_going_on_eval/wire.py` | New, small. `Unresolved`, `Problems`, `ClassifiedProblem`, `ContractViolation` moved out of `parse.py` |
| `parse.py` | `VERDICT_KEYS`, `Verdict.smart`, `_resolve_at` arm, one call to `parse_smart` |
| `principles.py` | `WireKind` adds `smart_question` |
| `fixtures.py` | `SmartExpect`, parse `expect.smart`, require it on classify turns |
| `grade.py` | Hard fail `smart_proposed_when_withheld`, `smart_question` added to solve-leak prose fields, informational `smart_agreement` on `TurnResult` and `SuiteReport` |
| `drift.py` | `_smart_cards_drift(readme)` compares README card table to `load_cards(SKILL_DIR)`. `lint_cards` folded into `check_suite`. `_guard_turn` gold and restatement guard body gain the two keys |
| `schema_cases/` | Valid: proposed with gaps, proposed no gaps, withheld. Invalid: one per `parse_smart` violation kind, plus `smart_question` on a Halt |
| `fixtures/seed/case-*.yaml` | Golds gain the two keys and any gap rows. `expect.smart` added |
| `fixtures/seed/case-k.yaml`, `case-l.yaml` | New. Withheld, and a two-turn answer case whose turn 2 input repeats turn 1 plus the answers |

`manifest.py` needs no change. The mount and the clean-tree allowlist derive from the playbook `skills` list and the principle index.

### Grading

`smart_proposed_when_withheld` is the one new hard fail. It fires when the fixture says `proposal: withheld` and the agent emitted a question. It mirrors `classified_without_problem`: proposing over a missing specific or actionable is the SMART form of inventing. Gap-set agreement is soft. SMART judgment on measurable and relevant is genuinely fuzzy, so `smart_agreement` (Jaccard of expected and actual gaps, plus proposal match) is reported, not gated, and adds no rubric axis. `rubric.md` and `RUBRIC` stay as they are.

The existing `invented` tripwires already scan the whole response text, `smart_question` included. Fixtures that tempt a made-up deadline or metric add a tripwire such as `by end of Q\d` or `\d+%`.

### Interface depth

The public surface added to the eval package is one union (`SmartProposal`) on `Verdict` and one `SmartExpect` on fixtures. `parse_smart` hides card loading, prompt matching, letter set equality, ordering, the specific-plus-actionable rule, and the no-primary rule. Graders never see the two raw keys or match prompts themselves. On the skill side the operator sees two keys and ordinary `unresolved` rows they already know how to read.

### Invariants and where they live

- One primary. Unchanged. `problems` holds at most one item.
- `main_question == problems[0].statement`. Unchanged parser check. `smart_question` never replaces it.
- No invention. Types cannot stop a made-up deadline, so the rule lives in `principle-dont-invent-problems`, `invented` tripwires, and the withheld hard fail.
- Specific plus actionable required. Encoded in the union. A `Proposed` with either letter in `gaps` cannot be constructed by the parser.
- Abstention unchanged. Smart step needs a primary. `smart_without_primary` rejects any SMART output on abstain turns, and abstain golds stay byte-identical except for the two keys.
- No solving. `smart_question` joins the solve-leak prose fields. A question that names a fix fails the same patterns `next_method` does.
- Idempotent updates. Each run derives `smart_question` from the input only. Running the same input twice gives the same gaps. A crash between turns leaves nothing to reconcile.

### What it deliberately does not do

- No per-letter status map on the wire. Met letters are implicit (all letters minus `smart_gaps`).
- No new key on `unresolved` rows. The prompt is the key.
- No SMART state carried between turns. The answer rule re-derives.
- No SMART rewriting of `main_question`, and no classifying of `smart_question`.
- No new rubric axis.

## Synthesis decision

To be filled by arena.

## Tradeoffs accepted

- We accept that many cases that were `classified` become `partial`, in exchange for the locked rule that every gap prompts the operator through the existing status table with zero parser change to `derive_status`.
- We accept that the gap row's `clarification` text is fixed by the card, in exchange for a parser-checkable link between `smart_gaps` and `unresolved` without a new row key. An agent that paraphrases the prompt fails the contract, which is the point.
- We accept a strict wire order (gap rows last, card order), in exchange for predictable `unresolved[<i>]` indices in `applied` and golds that diff cleanly. This looks like over-constraint. It removes a class of "same answer, different order" grading noise.
- We accept that `smart_question` may equal `main_question` word for word when the primary already carries every letter the input gives. That looks redundant. It keeps the rule "always emit `smart_question`" free of a special case.
- We accept soft grading of the gap set, in exchange for not hard-failing reasonable disagreement about measurable and relevant.
- We accept a small `wire.py` split, in exchange for keeping SMART logic in one module with top-level imports only.

## Alternatives considered

1. **Nested `smart:` object on `problems[0]` with a per-letter map** (`{specific: met, measurable: gap, ...}`). Rejected on interface depth. It exposes five fields the caller must read to learn two facts, duplicates the gap set between the map and `unresolved`, and conflicts with the locked top-level `smart_question` and `smart_gaps` fields. The status table cannot see it.
2. **Tag gap rows with a new `smart_gap: <letter>` key on `unresolved`.** Rejected as a hand-synced pair. The letter would live in the tag, in `smart_gaps`, and implicitly in the prompt text, and all three could disagree. Keying on the prompt removes two of the three copies.
3. **A separate stage or playbook for SMART** (`define-the-problem` then `make-it-smart` via "continue"). Rejected. It breaks "exactly one playbook per reply" for the common path, puts SMART after classification instead of before, and turns an answer into a stage advance, which is the lifecycle the README rejects.
4. **Carry SMART state forward and patch it on answers** (store prior gaps, remove answered letters). Rejected per make-operations-idempotent. The next run would depend on the previous run's output instead of the input, and live eval turns run in fresh sessions with no prior output to patch.
5. **Gaps outside `unresolved`, status untouched.** Rejected because variant C locks gaps into `unresolved` and wants `partial`. Listed so a reader sees it was a real option.

## Open questions and risks

- Does "Does it point to something we can do?" mark a pure why question (Case F, "Why did staging go down last night?") as actionable? If not, every diagnostic primary withholds `smart_question`. The sketch assumes an investigation counts as something we can do. Should the `smart` leaf say so with a Case F example?
- Will agents copy the prompt verbatim after `Ask yourself: `? The contract hard-fails a paraphrase. Should `gap_letter` tolerate whitespace and trailing punctuation differences, or stay exact?
- Should relevant count as met when the asker is plainly the decider (Case C, a design lead saying "let's lock")? The sketch says yes, because the input names who decides. Is that inventing?
- Gold churn. Cases B to H likely gain gap rows and flip to `partial`. Do we accept that README Cases B to E stop being `classified` examples, or add a new SMART-complete case so `classified` stays illustrated?
- The answer rule leans on the chat holding the earlier ask. In a fresh chat with only the answers, the run sees no ask and should abstain. Is that acceptable, or should the README tell operators to paste the ask again?
- `PREAMBLE_BUDGET` is unaffected, but YAML length grows by up to five rows. Does any host truncate?

## Next implementation step

Write `smart/SKILL.md` with the `## Cards` table and `whats_going_on_eval/smart.py` with `load_cards`, `lint_cards`, and `parse_smart`, plus the schema cases that pin every violation kind, before touching any fixture gold.

## Principles applied in this sketch

- model-the-domain chose a three-variant `SmartProposal` union over a nullable question plus a free list, which deletes the "proposed but specific missing" branch everywhere.
- type-system-discipline put `SmartLetter` as a `Literal` derived from the card registry and pushed all raw-key checks into `parse_smart` at the wire boundary.
- encode-lessons-in-structure replaced the prose rule "keep `smart_gaps` in sync with the gap rows" with a parser equality check, and replaced "keep the README prompts in sync" with `_smart_cards_drift`.
- redesign-from-first-principles kept status derivation untouched by making gap rows ordinary `unresolved` rows, as if SMART gaps had always been one more kind of open concern.
- make-operations-idempotent turned "update `smart_question` on answers" into re-derivation from input, with no carried state.
