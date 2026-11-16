---
stage: define-the-problem
consumes: none
produces: problem_map
skills: [ask, restate, separate, extract, clarity, smart, classify-2x2, worksheet]
---

# Define the problem

Find what needs resolving in the input. Sharpen one primary problem. Classify it only if it is defined. Then stop.

## Steps

Run each step in order. Each step writes one note. Work silently. Keep the notes out of the reply.

| Step | Skill | Reads | Writes |
|---|---|---|---|
| 1 | `ask` | input | ask note |
| 2 | `restate` | input, ask note | restatement |
| 3 | `separate` | input | separation |
| 4 | `extract` | input, separation | candidates |
| 5 | `clarity` | input, candidates | Defined and Unresolved rows |
| 6 | Primary (this playbook) | Defined rows | primary, deferred rows |
| 7 | `smart` | input, primary | SMART question, gap rows |
| 8 | `classify-2x2` | primary | classification |

Step 6. Of the Defined rows, pick the primary per `principle-read-the-room`. Turn each other Defined row into an Unresolved row. Its `observation` is the question as asked. Its `reason` says it is deferred until the primary problem is answered. Its `clarification` says when to ask it again. The primary's statement is the main question, the one to answer first. With no Defined rows, there is no primary, the main question is `null`, and steps 7 and 8 do not run.

Step 7. Propose one SMART question for the primary per `principle-make-it-smart`. Each open letter adds a gap row after the deferred rows. Step 8 classifies the primary, not the SMART question.

Repair. If the restatement disagrees with the primary or the Unresolved rows, discard it and run `restate` again. Never edit the sentences in place.

## Status

Fill `problems` and `unresolved` first. Set `status` last from this table:

| problems | unresolved | status |
|---|---|---|
| empty | empty | `not_a_problem` |
| empty | some | `needs_clarification` |
| one | empty | `classified` |
| one | some | `partial` |

## Output

Exactly two sentences of restatement, then exactly one fenced `yaml` block, then nothing.

Render the primary and its classification as the one `problems` item. Render every Unresolved row under `unresolved`. Drop internal ids.

```yaml
status: classified | partial | needs_clarification | not_a_problem

main_question: "The primary's statement, word for word" | null

problems:
  - statement: "Clear statement of what needs resolving"
    classification:
      nature: analytical | conceptual
      direction: convergent | divergent
    confidence: high | medium | low
    why: "Evidence for both dimensions"
    next_method: "Kind of reasoning to use next, not the answer"

smart_question: "The primary, carrying each met SMART letter's facts" | null

smart_gaps: [specific | measurable | actionable | relevant | time_bound]

unresolved:
  - observation: "What was said"
    reason: "Why this is not yet a defined problem"
    clarification: "What to ask next"

applied:
  - name: principle-<name>
    at: status | problems[0] | problems[0].classification | problems[0].confidence | smart_question | unresolved[<i>]
    changed: "The choice the principle changed, in one line"

stop: true
```

`problems` holds at most one item, the primary. An empty `problems` list is valid when status is `needs_clarification` or `not_a_problem`. Always emit `main_question`. Copy the primary's `statement` into it exactly. Write `null` when `problems` is empty. Always emit `smart_question` and `smart_gaps`. Write `null` and `[]` when there is no primary. Always emit `unresolved`, with any gap rows last. Write `[]` when it is empty. Always emit `applied`. Write `[]` when no principle decided a value.

## Never

- Put a second item in `problems`.
- Reword the primary's statement in `main_question`, or name a question there that `problems` does not hold.
- Put `smart_question` in `main_question`, or classify `smart_question`.
- Write a gap row without its card prompt word for word.
- Write anything after the YAML block.
