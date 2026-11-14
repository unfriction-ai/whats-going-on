---
name: principle-read-the-room
description: >-
  Applies when a whats-going-on stage chooses which problem comes next and
  classifies it. Deal with the problem the others wait on, and classify it as
  it stands now.
governs: [problem, unresolved, classification]
disable-model-invocation: true
---

# Read the room

## Rule

Sharpen one primary problem, the one the others wait on. A question the others depend on goes first, such as a why before a how to prevent. Every other concern waits in `unresolved` until the primary is answered.

Classify that problem as it stands now. The quadrant names the current reasoning objective, not a permanent property of the situation. Do not advance it to a later stage. More information alone does not flip a quadrant. A changed question does.

## When

Each time two or more rows are Defined, and each time you classify the primary.

## Cite or omit

Cite at `problems[0]` when this rule chose the primary over another Defined row. Cite at `unresolved[<i>]` when it deferred a Defined row behind the primary. Cite at `problems[0].classification` when it held the quadrant to the current ask instead of a later one. Omit it when only one row was ever Defined and its quadrant was plain.

## Failure signature

Two items appear in `problems`. The primary is the easiest question to answer instead of the one the others depend on. A why is classified as the convergent fix that would follow it.

## Distinct from

`principle-dont-invent-problems` decides whether a row is a problem at all. `principle-dont-solve-yet` stops you from answering the primary. This rule orders the problems that exist and fixes the moment you classify.
