---
name: mece
description: >-
  Runs mutually exclusive and collectively exhaustive checks on sibling sets for
  the whats-going-on structure-the-problem playbook.
disable-model-invocation: true
---

# MECE

For every set of sibling nodes in every breakdown, run both checks. Fail the set if either fails.

1. **Mutually exclusive.** No overlaps. Each possible cause, driver, option, or evidence path fits under exactly one branch. No double work.
2. **Collectively exhaustive.** No gaps for the **parent / root question's solution space**, not only the wording that happened to appear in the paste. Branches the root implies but the paste omits stay as open subquestions (with a hypothesis), not invented facts or metrics. `principle-dont-invent-problems` still blocks fake numbers and made-up incidents; it does **not** license marking price|volume CE-pass for "grow revenue" while acquisition / new markets / new products are absent.

Write one note per sibling set. The wire rejects `mece_pass` when any sibling set lacks a note, when a note path does not resolve, or when a known anti-example is self-attested as pass (meal-part + "meals"; traffic red+green with no yellow/amber; grow-revenue with only price|volume and CE pass).

```yaml
path: "A.tree.children"   # or A.tree.A.1.children for an L2 set
mutually_exclusive: pass | fail
collectively_exhaustive: pass | fail
note: "one line on the overlap or the gap, or pass"
```

`needs_split` requires at least one fail flag on a note **and** an unresolved clarification that asks how to cut.

Do not rewrite nodes here.
