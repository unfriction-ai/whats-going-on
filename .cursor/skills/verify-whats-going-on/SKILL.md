---
name: verify-whats-going-on
description: >-
  Drive and prove the whats-going-on coding-agent skill (CLI eval harness,
  install scripts, and /whats-going-on classification contract). Use when
  verifying install, suite health, abstention, or compound classification
  against this repo's real commands and fixtures.
---

# Verify whats-going-on

Primary surface: the `/whats-going-on` agent skill (YAML problem-mapping output). Secondary: local host install and the sibling eval CLI under `evals/whats-going-on/`. There is no web UI or long-lived server.

Harness binary: `.cursor/skills/verify-whats-going-on/bin/wgo-verify` (executable). Prefer it over ad-hoc shell so HOME stays isolated and evidence lands in a fixed place.

```bash
VERIFY=".cursor/skills/verify-whats-going-on/bin/wgo-verify"
```

## Launch

Creates an isolated scratch (venv + disposable `HOME`), installs eval deps, and requires a green suite check before any drive.

```bash
$VERIFY launch
# ready when stdout ends with: launch OK run_id=... 
# and artifacts/<run_id>/launch-check.txt contains a line: check OK
```

Ready means `python -m whats_going_on_eval check` printed `check OK` (fixtures, gold self-test, schema_cases). A process that merely exists is not enough.

No server to keep alive. Keep the active run pointer (`scratch/current`) until cleanup.

Teardown: `$VERIFY cleanup` (see Cleanup).

## Doctor

Read-only. Run first whenever anything looks off.

```bash
$VERIFY doctor
# expect: doctor OK
# artifacts/<run_id>/doctor.txt must show home_isolated=ok, check OK, canonical skill ok
```

Doctor fails if `HOME` is not the scratch home, if the eval package or canonical `SKILL.md` is missing, or if `check` / `assert-canonical-skill.sh` fail. Never drive the operator's real `~/.cursor` / `~/.claude` / `~/.agents` install; refuse shared instances.

## Drive

Feature recipes live in `features/`. Use stable commands and fixture ids from this repo.

```bash
$VERIFY doctor
$VERIFY drive eval-suite-health
# or: canonical-skill-integrity | local-host-install | abstain-vague-ask | compound-classification
```

Cursor live invoke (`python -m whats_going_on_eval run --agent cursor …`) is wired when the `agent` CLI is on `PATH` and authenticated. Claude and Codex still raise `HostNotWired`. For `abstain-vague-ask` and `compound-classification`, the harness always grades fixture gold and records live status in `proof.txt` (`ok`, `unreachable_missing_cli`, `unreachable_missing_auth`, or `stubbed_HostNotWired`). Do not claim a live agent proof unless `proof.txt` says `live_run=ok`.

User-facing invoke shape (when a host is available):

```text
/whats-going-on

<paste the situation>
```

## Evidence

Proof root: `.cursor/skills/verify-whats-going-on/artifacts/<run_id>/`.

Standards:

- Exercise the real operator/user path named in the feature map (install script, assert script, `/whats-going-on` prompt + fixture), not private Python setters that bypass the CLI.
- Capture the action and the resulting state (command transcripts, `proof.txt`, graded JSON), not only a final OK line.
- Side effects: for install, prove `SKILL.md` exists on each host path and `evals/` is absent; for classification, prove status / problem counts and gold score `1.0`.
- Do not invent a fake agent response and call it a live proof. Missing `agent` CLI or auth is unreachable, not a pass.

## Cleanup

```bash
$VERIFY cleanup
# removes scratch/<run_id> (venv + disposable HOME) and the scratch/current pointer
# keeps artifacts/<run_id>/
```

Kill only what this run started. There is no daemon; do not `pkill` by name. Cleanup must never delete `artifacts/`.

## Helpers

| Command | Purpose |
|---|---|
| `$VERIFY launch` | Isolated scratch + ready-gate |
| `$VERIFY doctor` | Instance worth driving? |
| `$VERIFY drive <feature-id>` | One mapped feature + proof files |
| `$VERIFY cleanup` | Tear down scratch; keep evidence |
| `$VERIFY status` | Active run pointers |

Feature ids and recipes: `features/README.md`.
