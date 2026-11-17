---
name: hypothesis
description: >-
  Rewrites issue-tree nodes into testable subquestions for the whats-going-on
  structure-the-problem playbook. Leaves the root wording untouched.
disable-model-invocation: true
---

# Hypothesis

Take every non-root node in every breakdown.

- If the node already asks a testable subquestion, keep it. Write `hypothesis` as what would have to be true for this branch to explain or settle the parent.
- If the node states a cause, fix, ranked pick, or answer as fact, rewrite `question` into a subquestion. Example: "Latency is the DB" becomes "Is p99 dominated by the DB tier?"
- Leave the root node's `question` untouched.

Do not add depth. Do not rank branches. Do not recommend a fix.
