# Synthesized sketch: `challenge` leaf (step 10)

Working name `challenge` (leaf dir, wire key, row label `Challenge:`). Rename is a human choice touching those tokens + playbook row.

Not implemented. Bodies raise / TODO.

## 0. Usage excerpts

**Open (worksheet just completed, sunk cost + groupthink evidenced):**

```yaml
status: partial
challenge:
  round: open
  findings:
    sunk_cost: "We've already sunk four months into the Kafka migration"
    groupthink: "the whole team agrees we should finish it"
  reply: null
unresolved:
  - observation: "The definition rests on framings the paste does not test."
    reason: "The challenge round is open."
    clarification: "Challenge: … <rendered other-sides> … Reply under this line, or say \"I hold this framing.\""
```

**Answered (next turn):** `round: answered`, same findings, `reply` verbatim under the Challenge line, no Challenge row → `classified` when otherwise empty.

**Clear:** `{round: clear, findings: {}, reply: null}`, no row.

**Idle:** `challenge: null` while sheet not `Complete`.

## 1. Module map

| Layer | Path | Change |
|---|---|---|
| Leaf | `skills/whats-going-on/challenge/SKILL.md` (+ plugin mirror) | new — Biases SSOT |
| Playbook | `playbooks/define-the-problem.md` | step 10, `skills:`, Output key, ask-row prose |
| Coordinator | `SKILL.md` | Challenge replies = new facts; never `at` the ask row |
| Principle | `principle-dont-invent-problems` | quote rule + omit findings; `governs` unchanged |
| Eval | `whats_going_on_eval/challenge.py` | new deep module |
| Eval | `wire.py` | `ask_slot()` |
| Eval | `parse.py`, `worksheet.py`, `fixtures.py`, `grade.py`, `drift.py`, `manifest.py` | wire + SUITE_VERSION 4 |

No new principle. No new `WireKind`. `derive_status` / `partition_unresolved` semantics unchanged (Challenge row is an ordinary unresolved whose clarification is stripped via `operator_ask`).

## 2. Leaf table (SSOT)

| Bias | Move | Symptom in the paste | Other side |
|---|---|---|---|
| `anchoring` | `drop_span` | A number, date, estimate, or option arrives first and the ask treats it as given, with no alternative named. | "{quote}" may be the first figure or option you heard, not the right one. What would you ask if you had never seen it? |
| `confirmation_bias` | `restore_span` | The paste names the answer it expects, or cites only agreeing evidence, with nothing that could disagree. | "{quote}" is in the paste but not in the primary as framed. What would you expect if it were wrong, and have you looked? |
| `sunk_cost` | `drop_span` | Time, money, or effort already spent is given as a reason to continue. | "{quote}" counts what is already spent. If you were starting today, would you still choose this? |
| `groupthink` | `name_missing_party` | Agreement is given as the reason, with no dissent recorded. | "{quote}" leans on agreement. Who would disagree, and what would they say? |

Move checks (parse-time, against `problems[0].statement` when primary exists):

| Move | Rule |
|---|---|
| `drop_span` | quote is a substring of the primary |
| `restore_span` | quote is **not** a substring of the primary (paste-only signal) |
| `name_missing_party` | no primary-side membership check |

Quote: ≤160 chars, verbatim from paste; never from probe / Ask-yourself / Challenge lines. Findings: at most one per bias; **distinct quotes**; if a quote would also satisfy an earlier bias’s symptom ownership, only the earlier bias may claim it.

Reply sentence (## Reply): `Reply under this line, or say "I hold this framing."`

## 3. Types (`challenge.py`)

```python
BiasId = Literal["anchoring", "confirmation_bias", "sunk_cost", "groupthink"]
Move = Literal["drop_span", "restore_span", "name_missing_party"]
Round = Literal["clear", "open", "answered"]
LABEL = "Challenge: "
QUOTE_SLOT = "{quote}"
QUOTE_BUDGET = 160

@dataclass(frozen=True)
class Bias:
    id: BiasId
    move: Move
    symptom: str
    other_side_template: str  # QUOTE_SLOT once

@dataclass(frozen=True)
class Finding:
    bias: BiasId
    quote: str
    # post_init: budget, no LABEL/ASK_YOURSELF prefix

@dataclass(frozen=True)
class NotRun: ...
@dataclass(frozen=True)
class Clear: ...
@dataclass(frozen=True)
class Open:
    findings: tuple[Finding, ...]  # non-empty, table order, distinct quotes
    @property
    def line(self) -> str: ...  # LABEL + rendered other_sides + reply_line

@dataclass(frozen=True)
class Answered:
    findings: tuple[Finding, ...]
    reply: str | None

ChallengeAssessment = NotRun | Clear | Open | Answered

def ask_slot(row_count: int, gap_count: int) -> int: ...  # in wire.py
def operator_ask(sheet, challenge) -> str | None: ...
def parse_registry(text: str) -> Registry: ...
def parse_challenge(raw, sheet, unresolved, gap_count, primary: str | None) -> ChallengeAssessment | ContractViolation: ...
def ungrounded_findings(challenge, turn_input: str) -> tuple[BiasId, ...]: ...
def restated_line(challenge, turn_input: str) -> bool | None: ...
def challenge_prose(challenge) -> tuple[str, ...]: ...
```

`parse_challenge` enforces move∩primary rules when building Open/Answered findings; rejects dual-label overlaps; places Open row at `ask_slot`.

## 4. Playbook / coordinator (intent)

- `skills:` adds `challenge`; step 10 after worksheet.
- Output: `challenge: null | { round: clear|open|answered, findings: { <bias>: "…" }, reply: "…"|null }`
- Unresolved order sentence: concerns, then the one ask row (worksheet probe **or** Challenge line), then gaps.
- Select: Challenge replies are new facts (with Ask-yourself and worksheet probes).

## 5. Eval extension points

Hard fails: `challenge_ungrounded`, `challenge_restated`.  
Expect: `challenge: { round, biases }` iff worksheet stop is `complete`.  
Family: `challenged` derived from open/answered expects.  
`SUITE_VERSION` → 4. Every gold gains the key (`null` or `clear`).

Fixtures (min): multi-turn sunk+groupthink open→answered; anchor with SMART gaps still open; bare reply; clean complete; quote-only-in-probe.

Schema cases: **valid** null-while-asking, clear, open, answered; **invalid** missing key, before complete, null when complete, unknown bias, out of order, open without/misplaced/paraphrased row, answered with row, clear with findings, quote over budget, move/primary mismatch, dual-label, applied-at Challenge row.

## 6. Axes

| Choice | Decision |
|---|---|
| Trigger | Hard-wired: worksheet `Complete` (ask-slot free) |
| Stance | Experiment via `Other side` / `Symptom` columns |
| Output | Hard-wired: key + one ask row |
| Pipeline | Hard-wired: block one round (advisory = rejected shape) |
| Name, opt-in, tone, all-four, UI, cap-to-one-finding | Human |
