---
name: classify-2x2
description: >-
  Classifies the primary problem for the whats-going-on define-the-problem
  playbook by nature (analytical or conceptual) and direction (convergent or
  divergent).
disable-model-invocation: true
---

# Classify 2x2

Take only the primary problem, a Defined row. Never classify an Unresolved row.

- **Nature.** Settles with data → `analytical`. Turns on ideas, judgment, or ways of working → `conceptual`.
- **Direction.** The ask *now* narrows to one answer or one or two fixes → `convergent`. Leaves many answers open → `divergent`.

Classify the current question only. Do not advance it to a later stage.

Write `nature` and `direction` inside `classification`. Write `confidence` (`high`, `medium`, or `low`), `why` (evidence for both dimensions), and `next_method` (the kind of reasoning to use next, not its result) beside `classification` on the problem item, never inside it. Do not rewrite the statement.
