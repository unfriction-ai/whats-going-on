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

1. **Inspect.** Does anyone need something understood, decided, or resolved? An FYI or a plain notice with nothing to decide is `not_a_problem`.
2. **Separate** situation, problem, proposed approach, and classification. A proposed method (workshop, spreadsheet, migration, plan) is never the problem. Ask what question that method is meant to answer.
3. **Extract** one candidate per distinct question. Split compound asks. "Why X, and how to stop X" is two candidates.
4. **Clarity test, per candidate.** Can you state what needs resolving using only facts in the input? If not, put it in `unresolved` with the missing piece as the clarification. Missing data to *solve* does not block classification. Missing data to *identify* does.
5. **Classify, per defined candidate, independently.**
   - Nature: settles with data → `analytical`. Turns on ideas, judgment, or ways of working → `conceptual`.
   - Direction: the ask *now* narrows to one answer or one or two fixes → `convergent`. Leaves many answers open → `divergent`.
   - Classify the current question only. Do not advance it to a later stage.
6. **Aggregate.** Fill `problems` and `unresolved` first. Set `status` last from this table:

   | problems | unresolved | status |
   |---|---|---|
   | empty | empty | `not_a_problem` |
   | empty | some | `needs_clarification` |
   | some | empty | `classified` |
   | some | some | `partial` |

## Output

At most two sentences of restatement, then exactly one fenced `yaml` block, then nothing.
If the input includes a link you could not open, say so in the restatement.

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
