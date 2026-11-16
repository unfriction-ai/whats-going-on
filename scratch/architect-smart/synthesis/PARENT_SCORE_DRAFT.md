# Parent score draft (pre cross-judge)

Rubric 1-5. Evidence one line each.

| Criterion | C1 prompt-keyed | C2 SmartAssessment |
|---|---|---|
| 1 Variant C fidelity | 5. Top-level keys, gaps in unresolved, classify anyway, Specific+Actionable gate | 5. Same locked behavior |
| 2 Illegal states | 5. Proposed/Withheld/NoPrimary union in parse_smart | 5. QuestionProposed cannot hold required gaps |
| 3 Single source of truth | 5. Cards table + load_cards + README drift | 4. YAML Cards fence is stronger machine-parse, but letter casing Title Case diverges from usual snake wire |
| 4 Fit existing machinery | 5. Status untouched, answers = new facts, cites unresolved + smart_question | 4. Adds smart_gaps[i] applied paths and notes_for_turn prior_primary coupling |
| 5 Maintainer / interface depth | 5. Smaller eval surface, optional wire.py, soft gap grading | 3. Larger smart.py API (notes_for_turn, GroundedLetter, assess, project) |
| 6 Answer-turn without state | 5. Re-derive from ask+answers | 4. Same intent, but notes_for_turn models prior_primary explicitly |

Preliminary base lean: candidate 1.
Grafts from 2: `partition_unresolved` for grader concern scoring; optional `smart_gaps[<i>]` cite path if we want gap decisions off unresolved; Cards as loadable fence with required_to_propose flags.
