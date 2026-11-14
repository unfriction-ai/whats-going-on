# Synthesized design: identify-ask + restatement

## Problem

Add an explicit identify-ask and plain-English restatement step to `/whats-going-on` in the spirit of pstack `in-your-own-words`, without changing classification outcomes and without inventing problems on vague or FYI input.

## Synthesis decision

Base: candidate 1 ([Restate design candidate A](2171fbec-1526-4b4a-bd0e-e597c3d462d0)), recommended by [Cross-judge restatement designs](2c5f8312-cf4f-4894-8ebc-5e933b9545ee) (12/12 vs 7/12).

Grafts from candidate 2 ([Restate design candidate B](e770fd01-9e74-42b6-a89e-64779ad809a7)):

1. Host-free property test: two texts that differ only in the preamble share the same `Outcome`; a quadrant flip does not.
2. Separate `contract_fail` counters from outcome mismatches in invariance reporting.
3. Output repair rule: if restatement and lists disagree, rewrite the restatement; never add a problem. Drift-check that `SKILL.md` does not bind `No ask is stated.` to a status.

Rejected from C2: typed `ask` YAML key, `actual_ask` iff classified/partial coupling, deleting the preamble restatement slot.

Rejected as a dependency: upstream `in-your-own-words` (one sentence, assumes a problem, invents goals, not on the derived mount, `disable-model-invocation: true`). Keep the idea. Credit it in `grounding.md`.

Rejected: a separate keyword/mode that gates the step (two ways to do one task).

## Usage

Same invoke: `/whats-going-on` plus paste. Exactly two restatement sentences, then the YAML. No typed `ask` key.

## Shape

`ask` and `restate` are stage leaves under the coordinator. The wire for a stage-1 verdict is `{status, problems, unresolved, applied, stop}`. Halt blocks use `{next_stage, available, stop}` and must not include `applied`.

## Shipped

#8 required the two-sentence restatement, fixture `restatement:` fields, parse/grade/drift guards, and `restatement_cases/`. Later PRs kept that contract when the skill split into playbooks and when `applied` joined the wire (#11, #17).
