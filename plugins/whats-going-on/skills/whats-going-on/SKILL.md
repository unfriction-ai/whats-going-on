---
name: whats-going-on
description: >-
  Coordinates a problem-solving chain over a pasted ask, message, or situation.
  Runs exactly one stage playbook per invocation, then stops. Stage 1 sharpens
  at most one primary problem and classifies it as analytical or conceptual and
  convergent or divergent, or abstains. Use when the user invokes
  /whats-going-on with a bug, email, Slack thread, incident notes, or similar
  text, or with "continue" after a prior result.
disable-model-invocation: true
---

# What's going on

Select one stage, run its playbook, emit its Output, stop.

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
| No prior result, or the message brings a new ask or new facts | define-the-problem |
| The message asks to continue from the latest result | the stage after the one that produced that result |
| Anything else | define-the-problem |

The latest result is the last fenced `yaml` block you emitted that has a `status` key. A block with a `status` key comes from define-the-problem. Continue carries its one primary problem forward. New material restarts at define-the-problem. Prior classifications do not advance on their own.

## Run

1. Look for `playbooks/<stage>.md` next to this file. If it is missing, follow Halt and stop.
2. Read the playbook. Read each skill its `skills` list names at `<skill>/SKILL.md` next to this file.
3. Work through the playbook steps silently. Emit only the playbook's Output.

## Halt

When the selected stage has no playbook file, write one plain sentence that says the stage is not available yet. Then write exactly one fenced `yaml` block with `next_stage` set to that stage, then nothing:

```yaml
next_stage: structure-the-problem
available: false
stop: true
```

Give no diagnosis, options, or recommendations.

## Never

- Run more than one playbook in one reply.
- Write the restatement outside the `restate` skill.
- Diagnose, list options, or recommend beyond the running playbook's Output.
- Write anything after the YAML block.
