---
name: carry-forward
description: >-
  Loads a governing problem statement for the whats-going-on
  structure-the-problem playbook. Gate passes on main or SMART text alone.
disable-model-invocation: true
---

# Carry forward

Read the latest define-the-problem view or debug Verdict when present, plus the current paste.

**Gate pass** when any of these is a non-blank string:

1. Prior `smart_question`
2. Prior `main_question`
3. A problem statement the paste states outright (the asker's question, or a line labeled `The question` / `Main question`)

Stage-1 `status` does not matter. `classified`, `partial`, open worksheet asks, and SMART gaps do not block.

**Gate fail** when none of those strings exist. Write gate refused. Do not invent a statement.

On pass:

1. Set `main_question` to the prior `main_question` when present, else to the governing statement from the paste.
2. Set `smart_question` to the prior SMART string when present, else `null`. Do not invent a SMART rewrite here.
3. Set `root_question` to `smart_question` when it is non-null. Otherwise set it to `main_question`.
4. Copy `problems[0].classification` (`nature`, `direction`) when present. Otherwise write `classification: null`.
5. When the paste answers a prior selection ask, parse breakdown ids and optional branch ids into `selected`. Leave `selected` empty when it does not.

On fail, write no root and `classification: null`.

Do not rewrite the governing question. Do not classify. Do not build branches.
