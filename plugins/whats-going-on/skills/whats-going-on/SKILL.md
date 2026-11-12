---
name: whats-going-on
description: >-
  Maps a pasted ask, message, or situation into zero or more defined problems
  and classifies each as analytical or conceptual and convergent or divergent,
  abstaining when a problem is not defined. Stops before diagnosis or solutions.
  Use when the user invokes /whats-going-on with a bug, email, Slack thread,
  incident notes, or similar text.
disable-model-invocation: true
---

# What's going on (slice 1: problem mapping)

Find what needs resolving in the input. Classify only what is defined. Then stop.

## Procedure

Work through these silently. Output only the result under Output.

1. **Ask.** Does anyone need something understood, decided, or resolved? Note who asks for what, in their own terms. A request for a method (plan, workshop, dashboard, migration) is the ask as said. Do not swap in the question you think is behind it. A concern with no request means no ask is stated. An FYI or a plain notice with nothing to decide is `not_a_problem`.
2. **Restate.** Write the two restatement sentences now, under the rules in Output. Then set them aside. Steps 3 to 7 work from the input, never from your restatement.
3. **Separate** situation, problem, proposed approach, and classification. A proposed method (workshop, spreadsheet, migration, plan) is never the problem. Ask what question that method is meant to answer.
4. **Extract** one candidate per distinct question. Split compound asks. "Why X, and how to stop X" is two candidates.
5. **Clarity test, per candidate.** Can you state what needs resolving using only facts in the input? If not, put it in `unresolved` with the missing piece as the clarification. Missing data to *solve* does not block classification. Missing data to *identify* does.
6. **Classify, per defined candidate, independently.**
   - Nature: settles with data → `analytical`. Turns on ideas, judgment, or ways of working → `conceptual`.
   - Direction: the ask *now* narrows to one answer or one or two fixes → `convergent`. Leaves many answers open → `divergent`.
   - Classify the current question only. Do not advance it to a later stage.
7. **Aggregate.** Fill `problems` and `unresolved` first. Set `status` last from this table:

   | problems | unresolved | status |
   |---|---|---|
   | empty | empty | `not_a_problem` |
   | empty | some | `needs_clarification` |
   | some | empty | `classified` |
   | some | some | `partial` |

## Output

Exactly two sentences of restatement, then exactly one fenced `yaml` block, then nothing.

1. **The ask.** Who asks for what, in the asker's terms. If nothing is asked, write exactly `No ask is stated.`
2. **The situation.** What is going on, in plain words, using only facts in the input. If the input includes a link you could not open, say so here.

The restatement only reports. It names no problem, cause, quadrant, or fix. Those belong to the YAML. Do not guess goals or intent. "Probably," "seems to want," and "likely" mean you are guessing. When the input defines no problem, a thin restatement is correct. Filling the gap is invention.

If the restatement and the lists disagree, rewrite the restatement. Never add a problem to make them match.

```yaml
status: classified | partial | needs_clarification | not_a_problem

problems:
  - statement: "Clear statement of what needs resolving"
    classification:
      nature: analytical | conceptual
      direction: convergent | divergent
    confidence: high | medium | low
    why: "Evidence for both dimensions"
    next_method: "Kind of reasoning to use next, not the answer"

unresolved:
  - observation: "What was said"
    reason: "Why this is not yet a defined problem"
    clarification: "What to ask next"

stop: true
```

An empty `problems` list is valid when status is `needs_clarification` or `not_a_problem`.
Omit `unresolved` when it would be empty, or set it to `[]`.

## Never

- Invent facts, metrics, or causes to make a candidate classifiable.
- Diagnose, list options, brainstorm, plan, or recommend. `next_method` names a kind of reasoning, not its result.
- Write anything after the YAML block.

## Contrast pairs

- "Things feel off" is a symptom. "Error rate rose 12% since Tuesday. Why?" is a defined problem.
- "We should run a workshop" is a proposed method. "What is causing the timeouts?" may be the question behind it.
- The same outage can yield "why did it fail?" (analytical, convergent) and "what approaches could prevent recurrence?" (conceptual, divergent). Classify each ask on its own.
- "Can we get a dashboard for signups?" restates as "Someone asks for a signups dashboard." Not "Someone wants to know why signups fell."
