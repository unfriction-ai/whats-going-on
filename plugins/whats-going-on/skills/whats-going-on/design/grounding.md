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
4. Per candidate, abstain if undefined, else classify on analytical/conceptual × convergent/divergent.
5. Aggregate to `not_a_problem` | `needs_clarification` | `classified` | `partial`.
6. Stop. No solving.

Output is the YAML contract in the README (`status`, `problems[]`, `unresolved[]`, `stop`).

Invariants: identification before classification, independent multi-problem classification, valid abstention, snapshot not lifecycle, no solving.

## Eval requirements (from shared design chat)

Evaluations must measure agent behavior under the skill, not opinions about the skill text.

Hard fail: classifying when no problem is established (abstention precision).

Test families to cover:

| Family | Expected |
|---|---|
| Clear single problem | Identify and classify |
| Multiple independent problems | Separate and classify each |
| Ordinary request / FYI | `not_a_problem` or abstain |
| Vague dissatisfaction | `needs_clarification` |
| Proposed solution without demonstrated problem | Do not treat method as problem |
| Compound ask | Split |
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
