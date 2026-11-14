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

A requested method (a plan, a migration, a workshop) is Unresolved when the input never says what problem it solves. Its `clarification` asks what the method is meant to solve. "Move everything to Kubernetes" names a method, not a problem. "How do we grow a mentoring culture?" names its goal, so it is Defined.

"Things feel off" is a symptom, so it is Unresolved. "Error rate rose 12% since Tuesday. Why?" is Defined. A request for where to start on a symptom is still Unresolved. "Signups feel weak. Where do we start?" names no change, magnitude, or timeframe to start from.

Never invent facts, metrics, or causes to make a candidate Defined.
