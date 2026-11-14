---
name: principle-dont-invent-problems
description: >-
  Applies when a whats-going-on stage decides whether a concern is a problem,
  whether to classify it, or how sure to be. Do not invent a problem the input
  does not support.
governs: [problem, unresolved, classification]
disable-model-invocation: true
---

# Do not invent problems

## Rule

A concern is a problem only when you can state what needs resolving using facts in the input. Identify before you classify. Never classify an Unresolved row.

Missing data to *solve* does not block a problem. Missing data to *identify* does. When identification is blocked, abstain. Leave the concern in `unresolved` and ask for the missing piece. Abstaining is a valid result, not a failure.

Never add a fact, a metric, a timeframe, a cause, or a quadrant the input does not give. Never add a problem so that the restatement, the primary, and `unresolved` agree.

## When

Each time a concern could become a Defined row, and each time you are about to classify.

## Cite or omit

Cite at `unresolved[<i>]` when this rule kept a concern unresolved that you could have defined by filling a gap. Cite at `problems[0]` when it made you drop a detail from the statement. Cite at `problems[0].classification` when it held a quadrant to what the input supports. Omit it when the input defined the problem plainly and nothing tempted you to fill a gap.

## Failure signature

A statement or `why` uses a number, a timeframe, or a cause that does not appear in the input. A vague symptom gets a quadrant. A requested method is classified as if it were its own problem.

## Distinct from

`principle-read-the-room` picks among problems that are already defined. `principle-dont-solve-yet` limits how far you go once a problem is defined. This rule decides whether a problem exists at all.
