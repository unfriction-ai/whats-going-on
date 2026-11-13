# Grounding: whats-going-on slice 1

## What exists

- `skills/whats-going-on/README.md` is the accepted product contract for slice 1.
- No `SKILL.md` yet. No eval fixtures yet. Repo otherwise empty aside from mission notes under `docs/missions/`.
- Cross-agent install target. Cursor, Claude Code, Codex. Same skill body, different install paths.

## Behavioral contract (from README)

Input is unstructured text or paste (bug, email, Slack, GitHub comment, incident notes, link plus context).

Pipeline:

1. Inspect without assuming a problem exists.
2. Separate situation, problem, proposed approach, and classification.
3. Extract zero or more problem candidates.
4. Sharpen one primary problem, the one that must be answered first. Leave every other candidate in `unresolved`.
5. If that primary is undefined, abstain. Otherwise classify it on analytical/conceptual × convergent/divergent.
6. Aggregate to `not_a_problem`, `needs_clarification`, `classified`, or `partial`.
7. Stop. No solving.

Output is the YAML contract in the README. `problems` has zero items or one item. Always emit `unresolved` and `stop`.

Invariants: identification before classification, one primary problem, valid abstention, snapshot not lifecycle, no solving.

## Eval requirements (from shared design chat)

Evaluations must measure agent behavior under the skill, not opinions about the skill text.

Hard fail: classifying when no problem is established (abstention precision).

Test families to cover:

| Family | Expected |
|---|---|
| Clear single problem | Identify and classify |
| Multiple independent problems | Classify the one primary. Defer the rest. |
| Ordinary request / FYI | `not_a_problem` or abstain |
| Vague dissatisfaction | `needs_clarification` |
| Proposed solution without demonstrated problem | Do not treat method as problem |
| Compound ask | One primary. Other parts stay unresolved. |
| Successive narrower asks | Reclassify as snapshot, not auto-lifecycle |

Rubric weights (proposed):

| Criterion | Weight |
|---|---|
| Problem detection | 25% |
| Correct abstention | 25% |
| Problem separation | 15% |
| 2×2 classification | 20% |
| Evidence and uncertainty | 15% |

Executable eval shape for slice 1:

- Versioned fixtures with expected labels.
- Deterministic schema and hard-fail assertions (status, required fields, solve-leak).
- Optional LLM judge for softer axes.
- Operator can also run pstack-style blinded A/B via `/poteto-mode` eval playbook when comparing skill revisions.
- `disable-model-invocation: true` so evals must invoke the skill explicitly.

## Constraints for the design

- One self-contained skill first. Framework reference + eval suite. No coordinating mode yet.
- Restatement may precede classification but must not invent a problem.
- README cases A–J are the seed gold set (already rewritten off the training course).
- Design for agent-readable instructions. Types and fixtures should make illegal outcomes hard.

## Upstream in-your-own-words

The ask and restatement steps take one idea from pstack `in-your-own-words`: restate the situation before you act. This skill does not call that skill and does not install it.

That skill is `disable-model-invocation: true`, so this one cannot invoke it. `AGENT_MOUNT` copies only `SKILL.md`, so an eval run would not see it. It also restates goals, which here would be a guess, and it assumes a problem exists, which contradicts abstention on an FYI. The preamble in this skill is the restatement. There is no new YAML key.
