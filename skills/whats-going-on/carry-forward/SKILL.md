---
name: carry-forward
description: >-
  Loads the prior define-the-problem result for the whats-going-on
  structure-the-problem playbook. Picks the root question and enforces the gate.
disable-model-invocation: true
---

# Carry forward

Read the latest define-the-problem view or debug Verdict, plus the current paste.

- **Gate pass.** Prior `status` is `classified` or `partial`, and `main_question` is a non-null string. Continue.
- **Gate fail.** Anything else. Write gate refused. Do not invent a primary.

On pass:

1. Copy `main_question` word for word.
2. Copy `smart_question` as carried, or `null`.
3. Set `root_question` to `smart_question` when it is a non-null string. Otherwise set it to `main_question`.
4. Copy `problems[0].classification` (`nature`, `direction`) when present.
5. When the paste answers a prior selection ask, parse breakdown ids and optional branch ids into `selected`. Leave `selected` empty when it does not.

On fail, write no root and no classification snapshot.

Do not rewrite the governing question. Do not classify. Do not build branches.
