---
name: principle-make-it-smart
description: >-
  Applies when a whats-going-on stage proposes a SMART question for the primary
  or asks about a missing SMART letter. Propose only what the input grounds.
governs: [smart_question, unresolved]
disable-model-invocation: true
---

# Make it SMART

## Rule

A SMART letter is met only when the input states it. Check each card in the `smart` leaf against the input, never against what a sensible team would probably want.

- `specific` is met when the primary names the one problem plainly enough that a newcomer could pick it out.
- `measurable` is met when the input says what the answer looks like once it is solved: a figure, a chosen option, a go or no-go call, a found cause, or a stated end state. A goal word such as healthy or better is not a sign of done.
- `actionable` is met when the primary points to something the team can do: decide, choose, change, build, or find a cause with evidence it can reach.
- `relevant` is met when the input names who decides or what is at stake for them, such as a review, a budget, a launch call, or the asker owning the choice.
- `time_bound` is met when the input gives a date or window by which the answer is needed. When something happened is not a deadline.

Ask about an open letter instead of filling it. Propose `smart_question` only when `specific` and `actionable` are both met. Without them, a SMART question would be a guess at the problem, so withhold it and let the gap rows ask.

An answer to an Ask-yourself question is a new fact. On the next run, derive the SMART question again from the earlier ask plus the answers. Carry nothing over from the earlier `smart_question`.

## When

Each time you check the primary against the cards, write `smart_question`, or write a gap row.

## Cite or omit

Cite at `smart_question` when this rule made you withhold it or held it to the input's facts. Cite at `unresolved[<i>]` when it turned an open letter into a gap row instead of a guess. Omit it when every letter was plainly met.

## Failure signature

`smart_question` carries a metric, a deadline, or a decider the input never gives. `smart_question` is filled while `specific` or `actionable` is open. A gap row paraphrases the card prompt. `smart_question` replaces the primary in `main_question` or gets classified.

## Distinct from

`principle-dont-invent-problems` decides whether a problem exists and keeps invented facts out of every value. `principle-dont-solve-yet` keeps fixes out of the SMART question. This rule decides which letters are met and whether to propose the question at all.
