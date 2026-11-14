# Grounding: whats-going-on stage 1

## What exists

- `skills/whats-going-on/README.md` is the product contract and the seed answer key for stage 1 (`define-the-problem`).
- `skills/whats-going-on/SKILL.md` is the coordinator. It selects one stage per invoke, mounts a `## Principles` index, runs one playbook, and Halts when later stages have no playbook file.
- Stage 1 playbook and leaves live next to the coordinator: `playbooks/define-the-problem.md`, `ask`, `restate`, `separate`, `extract`, `clarity`, `classify-2x2`, and three `principle-*` leaves.
- Executable suite: `evals/whats-going-on/`. Sibling of the skill. Never installed with it. Measured runs mount the coordinator, each indexed principle, each shipped playbook, and the leaves those playbooks name. `README.md` and `design/` stay off the mount.
- Maintainer verify skill: `.cursor/skills/verify-whats-going-on/` (`wgo-verify`).
- Cross-host install. Cursor, Claude Code, Codex. Same skill body. Paths differ. See [docs/install.md](../../../docs/install.md).

## Behavioral contract (from the skill README)

Input is unstructured text or paste (bug, email, Slack, GitHub comment, incident notes, link plus context).

Pipeline for stage 1:

1. Inspect without assuming a problem exists.
2. Restate in exactly two sentences (who asks for what, then what is going on).
3. Separate situation, problem, proposed approach, and classification.
4. Extract zero or more candidates.
5. Sharpen one primary problem, the one the others wait on. Leave every other candidate in `unresolved`.
6. If that primary is undefined, abstain. Otherwise classify it on analytical/conceptual × convergent/divergent.
7. Cite principles under `applied` when they decided a value. Always emit `unresolved` and `applied` (use `[]` when empty).
8. Stop. No solving.

Output is the YAML contract in the skill README. `problems` has zero items or one item.

Invariants: identification before classification, one primary problem, valid abstention, snapshot not lifecycle, no solving.

## Eval requirements

Evaluations measure agent behavior under the skill, not opinions about the skill text.

Hard fail: classifying when no problem is established (abstention precision). Solving during classification is also a hard fail.

Test families:

| Family | Expected |
|---|---|
| Clear single problem | Identify and classify |
| Multiple independent problems | Classify the one primary. Defer the rest. |
| Ordinary request / FYI | `not_a_problem` or abstain |
| Vague dissatisfaction | `needs_clarification` |
| Proposed solution without demonstrated problem | Do not treat method as problem |
| Compound ask | One primary. Other parts stay unresolved. |
| Successive narrower asks | Reclassify as snapshot, not auto-lifecycle |

Rubric weights match `evals/whats-going-on/rubric.md`:

| Criterion | Weight |
|---|---|
| Problem detection | 25% |
| Correct abstention | 25% |
| Problem separation | 15% |
| 2×2 classification | 20% |
| Evidence and uncertainty | 15% |

Executable shape:

- Versioned fixtures with expected labels. Seed cases A–J match the skill README.
- Deterministic schema and hard-fail assertions (status, required fields, `applied` pointers, solve-leak).
- Optional LLM judge for softer axes is not wired yet (`judge_evidence` raises).
- Operator can run pstack-style blinded A/B via `/poteto-mode` eval when comparing skill revisions.
- `disable-model-invocation: true` so evals must invoke the skill explicitly.

## Design constraints that still hold

- Evals stay a sibling. Never copy `evals/` into a host skills path.
- No upstream `in-your-own-words` dependency. The restatement lives in `restate`.
- No typed `ask` YAML key. No gated keyword for the restatement step.
- No stored `family` field on fixtures. Families are derived from expectation shape.
- Stages 2–7 are named on the chain. They Halt until their playbooks exist.

## Upstream in-your-own-words

The ask and restatement steps take one idea from pstack `in-your-own-words`: restate the situation before you act. This skill does not call that skill and does not install it.

That skill is `disable-model-invocation: true`, so this one cannot invoke it. It also restates goals, which here would be a guess, and it assumes a problem exists, which contradicts abstention on an FYI. The two-sentence restatement in this skill is the owned form of that idea.
