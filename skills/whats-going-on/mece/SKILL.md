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
2. **Collectively exhaustive.** No gaps. Together the branches cover every path that could still answer the parent, given the paste. The answer cannot hide in a branch you did not open.

Write one note per sibling set:

```yaml
path: "A.tree.children"   # or A.tree.children[0].children, etc.
mutually_exclusive: pass | fail
collectively_exhaustive: pass | fail
note: "one line on the overlap or the gap, or pass"
```

Judge from the paste and the parent question only. Do not invent coverage the input does not support. Do not rewrite nodes here.
