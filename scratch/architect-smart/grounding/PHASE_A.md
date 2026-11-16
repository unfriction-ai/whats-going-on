# Phase A grounding. SMART slice (variant C)

## Goal

Ship variant C. After the primary is chosen, propose one grounded `smart_question`, list `smart_gaps`, prompt missing SMART letters via `unresolved`, and update the proposal when answers arrive. Keep `main_question` as today's primary statement.

## Subsystems

### 1. Canonical skill tree (`skills/whats-going-on/`)

Coordinator `SKILL.md` indexes principles and runs one playbook. Stage 1 playbook `playbooks/define-the-problem.md` steps: ask → restate → separate → extract → clarity → primary → classify-2x2. Output is two restatement sentences plus one YAML verdict. Plugin and host installs are rsync copies of this tree (`scripts/assert-canonical-skill.sh`). Edit canonical first, then sync copies.

Existing principles:
- `principle-dont-invent-problems` (problem, unresolved, classification)
- `principle-read-the-room` (problem, unresolved, classification)
- `principle-dont-solve-yet` (problem, unresolved)

### 2. Eval wire (`evals/whats-going-on/whats_going_on_eval/`)

`parse.py` owns `Verdict`, `VERDICT_KEYS`, `main_question` must equal `problems[0].statement`. `principles.py` owns `WireKind` and leaf `governs` validation. Applied `at` paths resolve via `_resolve_at`. Drift checks README contract keys against `VERDICT_KEYS`. Schema cases under `schema_cases/` and gold under fixtures must stay valid.

### 3. Prototype decision (locked)

From `scratch/smart-prototype/variants/C-soft-skill.md`:
- New leaf `smart/SKILL.md` after primary, before classify.
- New principle `principle-make-it-smart`.
- Wire fields `smart_question` and `smart_gaps`.
- Gaps mirror into `unresolved` with Ask-yourself prompts.
- Classify primary anyway. Gaps → status `partial` under the existing status table.
- Never invent SMART letters. Ground in input facts only.
- Propose only when Specific + Actionable both pass. Else `smart_question: null`.

### 4. Invariants that must survive

- Identification before classification. SMART does not invent a primary.
- One primary. `main_question` still copies statement word for word.
- Abstention on undefined concerns unchanged.
- No solving. SMART refines the question, not the answer.
- `dont-invent-problems` still blocks fabricated metrics/timeframes in the proposal.

### 5. Consumer / maintainer

Consumer (operator of `/whats-going-on`): sees a SMART proposal and clear prompts for missing letters. Continues with answers and gets an updated `smart_question`.

Maintainer: one new skill leaf, one new principle leaf, schema + fixture updates, canonical sync. Applied citations can point at `smart_question`.

## Files likely touched

- `skills/whats-going-on/smart/SKILL.md` (new)
- `skills/whats-going-on/principle-make-it-smart/SKILL.md` (new)
- `skills/whats-going-on/playbooks/define-the-problem.md`
- `skills/whats-going-on/SKILL.md`
- `skills/whats-going-on/README.md`
- `evals/whats-going-on/whats_going_on_eval/parse.py`
- `evals/whats-going-on/whats_going_on_eval/principles.py`
- `evals/whats-going-on/schema_cases/*`
- seed/holdout fixture gold YAML
- `plugins/whats-going-on/skills/whats-going-on/` (sync)
- possibly `.agents/skills/whats-going-on/` if present as copy

## Non-goals

- Rewriting `main_question` into SMART (variant B rejected).
- Five separate principle leaves.
- Gating classification on full SMART.
- Shipping the throwaway prototype runner.
