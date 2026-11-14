# Eval suite health

Eval suite health tells an operator whether the fixture set, gold answers, rubric keys, schema cases, principles table, and related offline gates still agree with the skill — before any agent is invoked.

## Sub-features

- `check-drift` fails when seed fixtures diverge from README cases, the principles table drifts from the coordinator index, or the skill tree is contaminated.
- `check-gold` requires every fixture gold response to score `1.0` under the grader with no hard fails.
- `check-schema` validates valid and invalid wire documents under `schema_cases/` (including `applied` pointer rules).
- `check-extras` also covers chain lint, restatement cases, preamble invariance, nested-leaf load, and a temp-home `install-local.sh` probe. These share the same `check` command.

## How to get to it (user POV)

- Offline gate: `cd evals/whats-going-on && source .venv/bin/activate && python -m whats_going_on_eval check`.
- The skill README Quick check runs that `check`, then a live `run --agent cursor --only case-a,case-f --repeat 1`. This feature covers only the offline `check`.
- Through the verification harness after launch: `wgo-verify drive eval-suite-health`.

## Driving it with wgo-verify

Preconditions:

- `wgo-verify launch` completed with `check OK` in `artifacts/<run_id>/launch-check.txt`.
- Prefer `wgo-verify doctor` before driving so HOME isolation and the assert script are confirmed.

- **Run check.** Execute the suite gate. Run `wgo-verify drive eval-suite-health`. Stdout and `artifacts/<run_id>/eval-suite-health/check.txt` contain a line `check OK`.
- **Confirm counts.** The same transcript reports fixture count, `skill_view` hash, families, `schema_cases: … ok`, and `nested_leaves:`.
- **Proof.** Open `artifacts/<run_id>/eval-suite-health/proof.txt`. It names `feature=eval-suite-health` and the entry command.

## Gotchas

- `check` needs no agent. Do not treat a green `check` as proof that a live host classified Case A or Case F.
- A dirty skill directory with unexpected top-level files fails drift (`answer-key contamination risk`).
- Exit code `2` is harness/drift error; do not confuse it with a graded hard-fail from `run`.
