---
name: whats-going-on
description: >-
  Coordinates a problem-solving chain over a pasted ask, message, or situation.
  Runs exactly one stage playbook per invocation, then stops. Stage 1 sharpens
  at most one primary problem and classifies it. Stage 2
  (/where-to-focus, /break-it-down, /where-to-start) builds MECE issue-tree
  breakdowns for the solver to pick. Use when the user invokes /whats-going-on,
  /where-to-focus, /break-it-down, or /where-to-start with a bug, email, Slack
  thread, incident notes, or similar text, or with "continue" after a prior
  result.
---

# What's going on

Select one stage, run its playbook, present its Output, stop.

## Chain

1. define-the-problem
2. structure-the-problem
3. prioritize-the-issues
4. develop-the-workplan
5. conduct-analyses
6. synthesize-findings
7. develop-recommendations

## Select

| When | Stage |
|---|---|
| Invocation is `/where-to-focus`, `/break-it-down`, or `/where-to-start` | structure-the-problem |
| No prior result, or the message brings a new ask or new facts | define-the-problem |
| The message asks to continue from the latest result | the stage after the one that produced that result |
| Anything else | define-the-problem |

The latest result is the last stage view you wrote, or the last debug fence that has a `status` key.

A define-the-problem view opens with the title line `What's going on`, then a restatement. It includes the label `The question` or the label `Main question`. A structure-the-problem view opens the same way and includes one or more `Breakdown` labels, or Status that says Structured or Not MECE yet. A fence with `breakdowns` is from structure-the-problem. A fence with a `status` key and `problems` is from define-the-problem.

Continue carries `main_question` forward word for word. New material that is not an answer to a structure-the-problem selection or MECE-cut ask restarts at define-the-problem. Prior classifications do not advance on their own. Answers to `Ask yourself:` questions, worksheet probes, and Challenge replies are new facts. Run define-the-problem on the earlier ask plus those answers. Answers to the structure-the-problem selection ask, or to a MECE-cut ask, continue structure-the-problem.

## Principles

Read each principle below before any playbook step. The file is `<name>/SKILL.md` next to this file. Apply a principle only after reading it.

- principle-dont-invent-problems — deciding whether a concern is a problem, whether to classify it, or how sure to be.
- principle-read-the-room — deciding which problem comes next, and classifying it as it stands now.
- principle-dont-solve-yet — deciding to stop at identification instead of diagnosing or recommending.
- principle-make-it-smart — deciding which SMART letters the input meets, and whether to propose the SMART question.

## Run

1. Read each principle named above.
2. Look for `playbooks/<stage>.md` next to this file. If it is missing, follow Halt and stop.
3. Read the playbook. Read each skill its `skills` list names at `<skill>/SKILL.md` next to this file.
4. Work through the playbook steps silently. Write only the playbook's Output, following Present.

## Present

Read the invocation once, before the reply.

Treat the mode as debug in any of these cases.

- The invocation includes `--debug`.
- One line is only the word `debug`.
- The message says `show debug`.

Otherwise the mode is default. An unknown flag is default.

Pick the layout from formatting instructions already in the context. Do not branch on a product name.

- When those instructions say that markdown is rendered, use markdown. Write each label as a `##` heading. Use `-` lists. Do not use a table.
- When those instructions say plain text or a terminal, use plain. Write each label in capital letters on its own line. Use `-` lists. Do not use a table.
- When they say nothing about formatting, use portable. Write each label in bold on its own line. Use `-` lists. Do not use a table, HTML, or a heading marker. The ask line stays a bare line.

Do not use ANSI color on the status phrase or the ask line. Use ANSI elsewhere in the plain layout only when the instructions say color is on. When color is unknown or off, use no ANSI.

Write the reply in this order.

1. The title line `What's going on`, as its own paragraph. It is the continue marker.
2. The restatement, as the next paragraph.
3. The view from the playbook view map. Lead with the question. Keep the view compact.
4. In the default mode, stop. Do not write a YAML fence. Do not write `applied` or `stop`.
5. In debug mode, add exactly one fenced `yaml` block of the Verdict, then nothing.

The one open ask is a bare line. Copy its clarification exactly. Do not wrap that line, `Ask yourself:`, or `Challenge:` in bold, quotes, or a bullet.

## Output envelope

In debug, every Verdict `yaml` block ends with `applied`, then `stop: true`. List each principle that decided a value in the Verdict. Cite nothing you did not apply. Write `applied: []` when no principle decided a value. The default view does not include this block.

```yaml
applied:
  - name: principle-dont-invent-problems
    at: unresolved[0]
    changed: "Kept the concern unresolved instead of naming a metric the input never gives."
stop: true
```

`name` is a principle from the index. `at` is the path of the value it decided, and the path sets the kind of that value:

| `at` | kind |
|---|---|
| `status` | `status` |
| `problems[0]` | `problem` |
| `problems[0].classification` | `classification` |
| `problems[0].confidence` | `confidence` |
| `smart_question` | `smart_question` |
| `unresolved[<i>]` | `unresolved` |

Point only at a row you emitted, and at `smart_question` only when there is a primary. Never point at the ask row. That row is a worksheet probe or the Challenge line. Cite a principle only at a kind its `governs` list names. `changed` says in one line of at most 200 characters what the principle made you choose. It does not diagnose or recommend.

## Halt

When the selected stage has no playbook file, write one plain sentence that says the stage is not available yet. Give no diagnosis, options, or recommendations.

In the default mode, stop after that sentence.

In debug mode, add exactly one fenced `yaml` block, then nothing. Set `next_stage` to the selected stage's kebab name:

```yaml
next_stage: prioritize-the-issues
available: false
stop: true
```

A debug Halt block has no `applied` key.

## Never

- Run more than one playbook in one reply.
- Write the restatement outside the `restate` skill.
- Write a YAML block outside debug.
- Write anything after the YAML block.
- Write `applied` or `stop` in the default view.
- Wrap `Ask yourself:` or `Challenge:` in bold, quotes, or a bullet.
