---
stage: define-the-problem
consumes: none
produces: problem_map
skills: [ask, restate, separate, extract, clarity, classify-2x2]
---

# Define the problem

Find what needs resolving in the input. Sharpen one primary problem. Classify it only if it is defined. Then stop. Do not diagnose or solve.

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
| 7 | `classify-2x2` | primary | classification |

Step 6. Of the Defined rows, pick the one that must be answered first. A question the others depend on goes first, such as a why before a how to prevent. Turn each other Defined row into an Unresolved row. Its `observation` is the question as asked. Its `reason` says it is deferred until the primary problem is answered. Its `clarification` says when to ask it again. With no Defined rows, there is no primary and step 7 does not run.

Repair. If the restatement disagrees with the primary or the Unresolved rows, discard it and run `restate` again. Never edit the sentences in place. Never add a problem to make them match.

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

applied:
  - name: principle-<name>
    at: status | problems[0] | problems[0].classification | problems[0].confidence | unresolved[<i>]
    changed: "The choice the principle changed, in one line"

stop: true
```

`problems` holds at most one item, the primary. An empty `problems` list is valid when status is `needs_clarification` or `not_a_problem`. Always emit `unresolved`. Write `[]` when it is empty. Always emit `applied`. Write `[]` when no principle decided a value.

## Never

- Put a second item in `problems`.
- Invent facts, metrics, or causes to make a candidate defined.
- Diagnose, list options, brainstorm, plan, or recommend. `next_method` names a kind of reasoning, not its result.
- Write anything after the YAML block.
