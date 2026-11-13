---
name: extract
description: >-
  Writes the candidate list for the whats-going-on define-the-problem playbook.
  One candidate per distinct question, compound asks split.
disable-model-invocation: true
---

# Extract

List one candidate per distinct question in the input and the separation.

- Split compound asks. "Why X, and how to stop X" is two candidates.
- Never merge two questions into one candidate.
- The same outage can yield "why did it fail?" and "what could prevent it from happening again?". Those are two candidates.

Write only the candidates. Do not judge whether each one is defined.
