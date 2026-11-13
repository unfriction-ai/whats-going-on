---
name: separate
description: >-
  Writes the separation note for the whats-going-on define-the-problem playbook.
  Splits the input into situation, problem, and proposed approach.
disable-model-invocation: true
---

# Separate

Sort what the input says into three parts:

- **Situation.** What is happening or what someone said.
- **Problem.** What needs to be understood, decided, or resolved.
- **Proposed approach.** What someone thinks should be done.

A proposed method (workshop, spreadsheet, migration, plan) is never the problem. Ask what question that method is meant to answer.

"We should run a workshop" is a proposed method. "What is causing the timeouts?" may be the question behind it.

Write only the separation. Do not split compound questions. `extract` does that.
