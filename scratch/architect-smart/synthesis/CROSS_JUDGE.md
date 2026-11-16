# Arena cross-judge. SMART problem question (variant C)

Judge model is `claude-opus-5-5-medium` from the pool. The parent vendor check did not run because the parent model is unknown. This is a readonly judgment. No production code was written.

Goal under judgment. Stage 1 proposes one SMART problem question. The wire gains top-level `smart_question` and `smart_gaps`. Each open letter prompts the operator through an `unresolved` row. `principle-make-it-smart` and a `smart` skill own the rule. Answers update `smart_question` on the next run. `main_question` stays the primary statement.

Candidates, read end to end:

- candidate-1, prompt-keyed gap ledger. `origin/cursor/architect-smart-candidate-1-e351:scratch/architect-smart/candidates/1/DESIGN.md`.
- candidate-2, SmartAssessment. `origin/cursor/smart-gap-assessment-892d:scratch/architect-smart/candidates/2/DESIGN.md`.

Claims about existing code were checked against `feat-smart-problem-question`. `WireKind` sits in `principles.py:10`. The Select row for "new facts" sits in `SKILL.md:31`. Case J ("snapshot, not lifecycle") sits in `README.md:448`. `_classify_abstention` sits in `grade.py:257`. `SUITE_VERSION = 1` sits in `manifest.py:11`.

## Scores

| # | Criterion | C1 | C2 |
|---|---|---|---|
| 1 | Variant C fidelity | 5 | 5 |
| 2 | Illegal states unrepresentable | 4 | 5 |
| 3 | Single source of truth for letters and prompts | 4 | 5 |
| 4 | Fit with status, applied, main_question, snapshot machinery | 4 | 4 |
| 5 | Maintainer extendability, smaller public surface | 4 | 2 |
| 6 | Answer turn without carried SMART state | 5 | 3 |
| | Total | 26 | 24 |

### Evidence, candidate-1

1. Fidelity, 5. Top-level keys, gap rows as ordinary `unresolved` rows so `partial` falls out of the unchanged status table, classify runs on the primary, `Withheld` when Specific or Actionable is open, and a `smart_proposed_when_withheld` hard fail.
2. Illegal states, 4. The three-variant `SmartProposal` union removes "proposed while Specific is open" from callers, but only `parse_smart` enforces it, so a hand-built `Proposed(gaps=("specific",))` still constructs.
3. Single source, 4. The `## Cards` table in `smart/SKILL.md` owns letters and prompts and the README copy is drift-checked, but the required pair lives only in Python and prose, and the README restates all five prompts.
4. Fit, 4. It reuses the existing "new facts" Select row and leaves `derive_status` and the `main_question` check alone, but it misses that gap rows make `_classify_abstention` return 0.5 whenever a fixture expects no concern rows (`grade.py:258-261`), and it says `manifest.py` needs no change even though every gold moves.
5. Surface, 4. It adds one union on `Verdict`, one `SmartExpect` on fixtures, and `parse_smart`, `gap_letter`, `load_cards`, `lint_cards`, with a small `wire.py` split as the only extra structure.
6. Answer turn, 5. The next run's input is the earlier ask plus the answers, re-derived from scratch through the existing row, and a two-turn `case-l` fixture repeats the ask so fresh-session live evals exercise it.

### Evidence, candidate-2

1. Fidelity, 5. It meets the same contract and adds `classify-2x2` guidance so an answered deadline cannot flip the quadrant.
2. Illegal states, 5. `__post_init__` guards on `QuestionAbsent` and `QuestionProposed` plus a single constructor `assessment_from_gaps` make the illegal pair unconstructible, not just unparseable.
3. Single source, 5. One YAML Cards fence carries letter, prompt, and `required_to_propose`, the loader rejects any disagreement with `REQUIRED_TO_PROPOSE`, and nothing else restates the prompts.
4. Fit, 4. It catches the grader penalty with `partition_unresolved` and bumps `SUITE_VERSION`, but it adds a Select row that duplicates the existing "new facts" row and gates answers on the prior verdict's primary.
5. Surface, 2. `GroundedLetter`, `OpenLetter`, `LetterState`, `SmartGap`, `ExcerptSource`, `notes_for_turn`, and `assess` model the agent's reasoning, yet excerpts never reach the wire, so the parser and grader can never call that path and only simulation tests exercise it.
6. Answer turn, 3. It refuses the prior `smart_question` as evidence, but `notes_for_turn(prior_primary=...)` reads the previous fence and rejects answers when it is missing, which is carried state by another name and breaks in a fresh session.

## Recommendation

Base is candidate-1.

Candidate-1 is the base a maintainer can extend without breaking invariants. Its whole SMART surface on the eval side is one union, one fixture block, and one parse function. The answer story needs no new routing and no memory of the prior fence, which matches Case J. Candidate-2 is stronger on construction-time invariants and on prompt ownership. Those strengths are small, local, and portable. Its excerpt model is its largest part, and that part is unobservable on the wire, so it cannot be graded and should not ship. Per the Laziness Protocol, the smaller API wins the near tie on total score, and per Type System Discipline, the two type-level wins from candidate-2 should be grafted rather than inherited with the rest.

## Grafts from candidate-2

1. Partition gap rows out of concern scoring. Give `_classify_abstention` and `_abstention_score` only the non-gap rows, using candidate-1's `gap_letter` as the test. Without this, every classify fixture that gains a gap row loses half its abstention score (`grade.py:258-261`). This is a real regression candidate-1 misses.
2. Enforce the union at construction. Add `__post_init__` checks so `Withheld` requires a required letter in `gaps` and `Proposed` rejects one and a blank question. The parser then cannot be the only gate.
3. Put the required flag in the card registry. Add a `required` column to the `## Cards` table and have `load_cards` reject a mismatch with `REQUIRED_TO_PROPOSE`, so the Specific plus Actionable gate is visible beside the prompts.
4. Bump `SUITE_VERSION` to 2. Gold fences and statuses change, so old reports must stay labeled as suite 1.
5. Give a solved `smart_question` an owner. Add the new wire kind to `principle-dont-solve-yet`'s `governs` so a fix written into the SMART question can be cited, alongside the solve-leak prose field candidate-1 already adds.
6. Extend `_seed_readme_drift` to compare the SMART keys of each README case with its fixture gold.

Optional. Candidate-2's single citation site (cite `principle-make-it-smart` at `smart_question` or `smart_gaps[<i>]`, never on the projected row) is tidier than candidate-1's `governs: [smart_question, unresolved]`, which lets the principle be cited on deferred rows too. Take it only if the extra `at` form earns its place.

## Rejected from candidate-2

- The excerpt model (`notes_for_turn`, `assess`, `GroundedLetter`, `OpenLetter`, `LetterState`). Nothing on the wire carries excerpts, so this code is only reachable from tests.
- The `prior_primary` gate and the new Select row. The existing "new facts" row already routes answers, and re-deriving from ask plus answers needs no prior fence.
- The fixed `observation` and `reason` text in `gap_row`. Candidate-1 fixes only `clarification`, which keeps the parser link and still tells the operator what the input actually lacked.

## Open items for the picker

- Both candidates key gap rows on an exact prompt match. Candidate-1 prefixes `Ask yourself: `. Decide whether `gap_letter` tolerates whitespace and trailing punctuation before writing schema cases.
- Candidate-1 asks whether a pure why question (Case F) counts as actionable. Settle it in the `smart` leaf with a Case F example, or every diagnostic primary withholds `smart_question`.
