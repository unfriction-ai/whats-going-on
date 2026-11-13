# whats-going-on evals

Measures agent behavior under `skills/whats-going-on/`. This tree is a sibling of the skill directory. It is never installed with the skill. Measured runs mount the coordinator `SKILL.md`, each shipped playbook, and the leaf skills those playbooks name. `check` derives that mount from the coordinator's `## Chain`. `README.md` and `design/` stay off the mount.

Requires Python 3.11+ and PyYAML.

```bash
cd evals/whats-going-on
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m whats_going_on_eval check
```

## Commands

```bash
# No agent. Drift, gold self-test, schema_cases, and nested-leaf load.
python -m whats_going_on_eval check

# README quick check (needs a wired host CLI).
python -m whats_going_on_eval run --agent cursor --only case-a,case-f --repeat 1

# Release-style run with repeats and optional evidence judge.
python -m whats_going_on_eval run --agent claude --repeat 3 --judge

# Older skill revision or no-skill baseline.
python -m whats_going_on_eval run --agent claude --skill /tmp/wgo-old/skills/whats-going-on
python -m whats_going_on_eval run --agent claude --skill none

# Re-grade stored transcripts after a harness fix.
python -m whats_going_on_eval grade <runId>

# Compare stored runs. Does not invoke a host. Live A/B needs a wired host.
python -m whats_going_on_eval invariance <baseRun> <treatRun> --noise <baseRun2>

# Blind A/B packet for /poteto-mode eval.
python -m whats_going_on_eval compare <runA> <runB> --blind
```

Exit 0: no hard fails. Exit 1: hard fail. Exit 2: harness or drift error.

Hard fails gate the run. Score is informational. The report splits seed and holdout.

## Layout

| Path | Role |
|---|---|
| `fixtures/seed/` | README cases A–J |
| `fixtures/holdout/` | Never quoted in README or SKILL.md |
| `schema_cases/` | Valid and invalid wire documents for status derivation |
| `rubric.md` | Weights. Criterion names must equal grader keys |
| `judge.md` | Evidence axis only |
| `reports/` | Run artifacts (gitignored) |

## Adding a fixture

Copy the nearest file under `fixtures/holdout/`. Do not store a `family` field. Families are derived from expectation shape. Run `check`. Gold must score 1.0.

## Host wiring

`run` prepares a temp workspace with the derived mount only. `run --agent cursor` invokes the Cursor agent CLI in that workspace and grades its stdout. Claude and Codex still stop before a live invoke. `check` and `grade` work without a host.

`check` copies that mount into a temp workspace for each host. It also runs `scripts/install-local.sh --host all` with `HOME` set to a temp directory. `check` fails when a nested leaf is missing from the workspace or from the install. `README.md` and `design/` stay off the workspace. The install still contains them, because they ship in the package and stay off the mount.
