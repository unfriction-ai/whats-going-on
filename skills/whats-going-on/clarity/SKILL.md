---
name: clarity
description: >-
  Marks each candidate Defined or Unresolved for the whats-going-on
  define-the-problem playbook.
disable-model-invocation: true
---

# Clarity

For each candidate, ask: can you state what needs resolving using only facts in the input?

- **Defined.** Yes. Write `statement`, the clear statement of what needs resolving.
- **Unresolved.** No. Write `observation` (what was said), `reason` (why it is not yet a defined problem), and `clarification` (the missing piece to ask for).

Missing data to *solve* does not block Defined. Missing data to *identify* does.

"Things feel off" is a symptom, so it is Unresolved. "Error rate rose 12% since Tuesday. Why?" is Defined.

Never invent facts, metrics, or causes to make a candidate Defined.
