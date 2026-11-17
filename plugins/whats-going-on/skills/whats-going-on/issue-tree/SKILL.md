---
name: issue-tree
description: >-
  Drafts one to three L1 breakdown frames for the whats-going-on
  structure-the-problem playbook from the root question and classification.
disable-model-invocation: true
---

# Issue tree

Take the root question, the carried classification when present, and the paste.

Draft **1–3** breakdowns. Prefer 2 when two frames both cut the root differently. Emit 1 when a second frame would only restate the first. Never emit more than 3.

Each breakdown has:

- `id` — `A`, `B`, or `C`
- `frame` — a short label for the cut (for example by stack layer, by time behavior, by stakeholder, by decision criterion)
- `tree` — root node at level 0 whose `question` is the root question word for word, with **L1 children only** in this skill

L1 rules:

- Every child is a subquestion that advances the parent.
- When classification is present: analytical roots lean toward cause, driver, or evidence branches; conceptual toward option, criterion, or constraint. Divergent keeps several live branches. Convergent still decomposes.
- When classification is null: pick frames from the paste only. Do not invent a quadrant.
- Neither ranks nor picks a winner here.
- Use only facts from the paste and carried fields for hypotheses. Invent no metrics or incidents. Open branches the **root question** implies even when the paste is silent (e.g. acquisition under grow-revenue); that is CE coverage, not invention — see `mece`.

Write `depth_max_used: 1` on each draft. Leave `children: []` on every L1 node. Do not deepen here. Do not run MECE here. Do not answer the root.
