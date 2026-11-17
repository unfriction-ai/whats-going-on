---
name: principle-dont-solve-yet
description: >-
  Applies when a whats-going-on stage is about to diagnose, brainstorm, or
  recommend. Stop once the problem is identified.
governs: [problem, unresolved, smart_question]
disable-model-invocation: true
---

# Do not solve yet

## Rule

State what needs resolving, then stop. Do not hunt a root cause, list options as answers, brainstorm solutions, plan, or recommend beyond the running playbook's Output.

An issue tree is allowed only when the running playbook produces one. Nodes stay hypotheses or subquestions, not settled causes or picks.

`next_method` names a kind of reasoning, not its result. An `unresolved` row asks for what is missing to identify or structure the problem, not for a fix.

## When

Each time you write a statement, a `why`, a `next_method`, a `smart_question`, or a `clarification`, and each time the input already proposes a fix.

## Cite or omit

Cite at `problems[0]` when this rule kept a cause, an option, or an answer out of the statement, `why`, or `next_method`. Cite at `unresolved[<i>]` when it kept a requested fix or plan as an open question instead of answering it. Cite at `smart_question` when it kept a fix or an option out of the SMART question. Omit it when nothing in the input or your notes pulled toward an answer.

## Failure signature

The reply names a likely cause as fact, lists fixes or ranked options, or gives a plan. An issue-tree node states the answer instead of a subquestion. `next_method` reads as an answer, such as "roll back the deploy", instead of a kind of reasoning, such as "compare error rates before and after the deploy".

## Distinct from

`principle-dont-invent-problems` stops you from adding facts to reach a problem. `principle-read-the-room` picks which problem to sharpen. This rule stops you once the problem is sharp.
