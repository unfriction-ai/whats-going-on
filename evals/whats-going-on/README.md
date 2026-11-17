# whats-going-on evals

Measures agent behavior under `skills/whats-going-on/`. This tree is a sibling of the skill directory. It is never installed with the skill. Measured runs mount the coordinator `SKILL.md`, each principle the coordinator index names, each shipped playbook, and the leaf skills those playbooks name. `check` derives that mount from the coordinator's `## Chain` and `## Principles`. `README.md` and `design/` stay off the mount.

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
# No agent. Drift, gold self-test, schema_cases (including applied), principles table, nested-leaf load.
python -m whats_going_on_eval check

# README quick check (Cursor agent CLI + auth).
python -m whats_going_on_eval run --agent cursor --only case-a,case-f --repeat 1

# Release-style Cursor run with repeats.
python -m whats_going_on_eval run --agent cursor --repeat 3

# Re-grade stored transcripts after a harness fix (no new host invoke).
python -m whats_going_on_eval run --agent cursor --resume <runId>
python -m whats_going_on_eval grade <runId>

# Older skill revision or no-skill baseline.
python -m whats_going_on_eval run --agent cursor --skill /tmp/wgo-old/skills/whats-going-on
python -m whats_going_on_eval run --agent cursor --skill none

# Compare stored runs. Does not invoke a host. Live A/B needs a wired host.
python -m whats_going_on_eval invariance <baseRun> <treatRun> --noise <baseRun2>

# Blind A/B packet for /poteto-mode eval.
python -m whats_going_on_eval compare <runA> <runB> --blind
```

Exit 0: no hard fails. Exit 1: hard fail. Exit 2: harness or drift error.

Hard fails gate the run. Score is informational. The report splits seed and holdout. Verdict YAML must include `smart_question`, `smart_gaps`, and `applied` (use `null`, `[]`, and `[]` when empty). Halt blocks must not include `applied`. Proposing a `smart_question` where the fixture expects it withheld is the hard fail `smart_proposed_when_withheld`. SMART gap rows, the `unresolved` rows whose `clarification` is `Ask yourself: ` plus a card prompt, do not count toward the `abstention` axis.

`--judge` is accepted on the run manifest. It does not call a live evidence judge yet.

## Layout

| Path | Role |
|---|---|
| `fixtures/seed/` | README cases A–L |
| `fixtures/holdout/` | Never quoted in README or SKILL.md |
| `schema_cases/` | Valid and invalid wire documents. `expect_kind` pins the violation an invalid case must raise |
| `rubric.md` | Weights. Criterion names must equal grader keys |
| `judge.md` | Evidence axis only |
| `reports/` | Run artifacts (gitignored) |

## Adding a fixture

Copy the nearest file under `fixtures/holdout/`. Do not store a `family` field. Families are derived from expectation shape. A classify turn sets `expect.smart` to `{proposal: proposed | withheld, gaps: [...]}`, and the gold must agree with it. An abstain turn has no `smart` block. List only concern rows under `expect.unresolved`, not SMART gap rows. A structure turn sets `expect.kind` to `structure` and `command` to `/where-to-focus`. Put `structured`, `needs_split`, or `blocked` in `statuses`. Run `check`. Gold must score 1.0.

## Host wiring

`run` prepares a temp workspace with the derived mount only. `run --agent cursor` invokes the Cursor agent CLI in that workspace under a scratch `HOME` (login keychain linked) with a 600s timeout, then grades stdout. Claude and Codex still stop before a live invoke (`HostNotWired`). `check` and `grade` work without a host.

`check` copies that mount into a temp workspace for each host. It also runs `scripts/install-local.sh --host all` with `HOME` set to a temp directory. `check` fails when a nested leaf is missing from the workspace or from the install. `README.md` and `design/` stay off the workspace. The install still contains them, because they ship in the package and stay off the mount.
