# Synthesized design. SMART variant C

## Synthesis decision

Base: candidate-1 (prompt-keyed gap ledger).
Cross-judge: [Cross-judge SMART designs](bc-cea740e5-7aae-43f8-977a-abf7810a23d9), 26 vs 24 for candidate-1.
Parent score agreed.

## Grafts from candidate-2

1. `partition_unresolved` / `gap_letter` so SMART gap rows do not halve abstention scores in `grade.py`.
2. `__post_init__` on `Withheld` / `Proposed` so the Specific+Actionable gate holds at construction, not only in `parse_smart`.
3. `required` column on the Cards table. `load_cards` rejects mismatch with `REQUIRED_TO_PROPOSE`.
4. `SUITE_VERSION` → 2.
5. `principle-dont-solve-yet` governs gains `smart_question`.
6. `_seed_readme_drift` compares SMART keys on README cases vs fixture gold.

Optional graft skipped: `smart_gaps[<i>]` citation path. Keep candidate-1 cite sites (`smart_question`, `unresolved[<i>]` for gap rows) so deferred rows stay distinguishable by the Ask-yourself clarification prefix.

## Rejected from candidate-2

Excerpt model (`notes_for_turn`, `GroundedLetter`, …). Extra Select row / `prior_primary` gate. Fixed observation/reason templates for gap rows.

## Picker decisions on open items

- `gap_letter` match is exact on `Ask yourself: <prompt>` with no whitespace/punctuation fuzz. Schema cases pin that.
- A why / diagnostic primary counts as Actionable. The `smart` leaf says so with a Case F style example.

## Shape to implement

Follow candidate-1 `DESIGN.md` plus the grafts above. Data shape first:

```text
SmartProposal = NoPrimary | Withheld(gaps) | Proposed(question, gaps)
SmartLetter = specific | measurable | actionable | relevant | time-bound
REQUIRED_TO_PROPOSE = {specific, actionable}
```

Wire: `smart_question`, `smart_gaps` on every verdict. Gap rows last in `unresolved`, clarification exact card prompt with `Ask yourself: ` prefix. `main_question` unchanged. Answers are new facts on the next define-the-problem run.

## Next implementation step

1. `smart/SKILL.md` Cards table with `required` column.
2. `principle-make-it-smart/SKILL.md`.
3. `whats_going_on_eval/smart.py` with construction-checked union + `parse_smart` + `gap_letter` + `load_cards`.
4. Wire `parse.py` / `principles.py` / schema cases.
5. Playbook + coordinator + README + fixture golds + canonical sync.
6. `python -m whats_going_on_eval check` and `bash scripts/pr-gates.sh`.
