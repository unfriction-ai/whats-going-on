# Challenger session (synthesized)

## Problem

Stage 1 already hardens one primary, a SMART question, a 2×2, and a worksheet. The paste can still carry anchoring, confirmation bias, sunk cost, or groupthink. Intent (Emily/Marc): a bounded challenger ritual that argues the other side before the definition is treated as settled — without inventing SMART facts or worksheet cells, and without breaking the closed wire / status / dual-tree contracts documented in `grounding.md`.

Non-obvious constraints: `derive_status` is pure `problems` × `unresolved`; unresolved order is concerns → one operator ask → SMART gap tail; invention ban is structural (substring checks), not tripwire-only; Ask-yourself / worksheet / Challenge answers restart define-the-problem as new facts.

## Usage (caller's view)

Operator still sees exactly two restatement sentences, one YAML fence ending in `applied` + `stop: true`, nothing after.

| Sheet state | Wire | Unresolved | Status effect |
|---|---|---|---|
| Not complete | `challenge: null` | unchanged | none |
| Complete, no evidenced bias | `{round: clear, findings: {}, reply: null}` | no Challenge row | stays `classified` if otherwise empty |
| Complete, evidenced bias(es), no prior Challenge line | `{round: open, findings: {…}, reply: null}` + one `Challenge:` ask row | `partial` |
| Complete, Challenge line pasted | `{round: answered, findings: {…}, reply: …}` | no Challenge row | back to `classified` if otherwise empty |

Findings quote the paste verbatim. Other-side text is rendered from the leaf table — never free prose. One round only; never reopens.

Harness:

```python
challenge = parse_challenge(raw, sheet, unresolved, gap_count, primary_statement)
# Verdict.challenge: NotRun | Clear | Open | Answered
# derive_status unchanged
ungrounded_findings(challenge, turn.input)
restated_line(challenge, turn.input)  # Answered idempotence
```

## Shape

**Base: arena candidate 1** (blocking one-round ask in the shared operator-ask slot). See Synthesis decision.

Public surface: one leaf `challenge/`, playbook step 10, one wire key `challenge`, one parse module. Behind it: Biases table SSOT, quote grounding, ask-slot placement, round semantics, primary-side move checks (graft), distinct-quote rule (graft).

Domain union: `NotRun | Clear | Open | Answered`. Constructors require findings in table order, quotes within budget, Open/Answered non-empty.

Ask ownership: `wire.ask_slot()` is the single index of the operator ask. Worksheet probe and Challenge line share it; they never both open (challenge runs only on `Complete`). `operator_ask(sheet, challenge)` is what `concerns` and `_resolve_at` strip. Unresolved prose becomes: concerns, then the one ask row, then gaps.

No new principle. No new `WireKind`. `principle-dont-invent-problems` gains a quote rule sentence; omit-cite extends to findings (no `at` on challenge). Challenge never edits `problems`, `smart_question`, or worksheet cells.

Bias ids (closed): `anchoring`, `confirmation_bias`, `sunk_cost`, `groupthink`.

## Synthesis decision

Base: [Architect sketch C1](55a711c4-c310-4ad2-b1e2-7fd28d632ee2) — recommended by [Cross-judge](dc770888-399a-4f1a-ae61-3884a5edca57) 27/30 vs 21/30. Parent vendor check did not run (unknown parent); judge seat was first pool entry.

Picker agreement: C1 is the only shape that meets the brief’s planted-blind-spot success bar (contrary case + named biases + one revision ask that actually holds `classified` back). Clean pastes stay clear via quote-gated findings. `derive_status` untouched.

Grafts from [Architect sketch C2](69c2202a-97ba-4886-8081-9a5c6626e6aa):

1. **Move column** on the Biases table (`drop_span` | `restore_span` | `name_missing_party`) with primary-side checks at parse time — confirmation can flag paste evidence the primary dropped.
2. **Distinct quotes / no dual-label** — findings must use distinct quotes; a quote that would also satisfy an earlier bias’s mark/symptom is owned by the earlier bias only.
3. **Valid-form schema cases** — clear / open / answered / null-while-asking, not only invalids.

Rejected from C2 as the base: advisory-only (no revision ask; biased defs reach `classified`); `confirmation` rename; bare `digit` mark as anchoring (false drama on clean pastes with numbers); first-grounded-only single reading (kept C1 multi-finding in one Challenge line).

Rejected from C1: inventing a new cite target; free-prose other_side; running beside an open worksheet ask.

## Tradeoffs accepted

- We accept fixed templates over free sparring, in exchange for invention only possible in a quote we substring-check.
- We accept late trigger (after worksheet complete), in exchange for one ask per turn and shared ask-slot exclusivity.
- We accept one extra turn on evidenced pastes, in exchange for gating “settled” (`classified`).
- We accept hard-wiring blocking (not a fixture flag), in exchange for meeting the revision-ask success criterion; advisory is a rejected shape, not a mode.
- We accept N templated questions inside one Challenge row when multiple biases evidence, in exchange for one operator turn; cap-to-one-finding remains an open human question.

## Alternatives considered

- **Advisory reading on `classified` (C2)** — smaller surface, pure unresolved semantics. Lost: no next ask; does not stop a biased definition from counting as settled.
- **Separate chain stage** — keeps stage 1 untouched. Lost: cannot gate stage-1 `classified`; answers restart define-the-problem anyway; two hops per round.
- **Principle-only rewrite of primary/SMART** — no new key. Lost: invisible ritual; highest invention risk.
- **Parallel to worksheet / one row per bias** — earliest catch. Lost: multiple open asks; false stalls; temporal decomposition.

## Open questions and risks (for you)

1. Ritual display name: keep wire/leaf `challenge`, or rename before gold is written?
2. Mandatory when evidenced (as sketched) vs opt-in Select signal?
3. Tone of the `Other side` / Reply sentences (table-only edits)?
4. Evidenced-only (default) vs always address all four (needs quote-less templates — rejected in this sketch)?
5. Cap findings to one (first in table order) for a stricter “single ask,” or keep multi-finding in one line?
6. Any UI beyond two-sentence + YAML?
7. Risk: over-detecting groupthink from ordinary “we decided” — holdout near-misses needed.
8. Risk: `Challenge:` label matching like worksheet probes — edited labels vs dropped labels (see C1 open questions).

## Next implementation step

After sign-off: write `skills/whats-going-on/challenge/SKILL.md` (Biases with Move + Symptom + Other side, Quote, Reply) and `challenge.parse_registry` + drift self-check, before touching `VERDICT_KEYS` or golds.
