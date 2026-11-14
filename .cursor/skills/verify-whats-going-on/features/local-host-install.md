# Local host install

Local host install materializes the skill into Cursor, Claude Code, and Codex paths under `$HOME` without copying `evals/`.

## Sub-features

- `install-cursor` writes `~/.cursor/plugins/local/whats-going-on` with `.cursor-plugin` and `skills` only.
- `install-claude` writes `~/.claude/skills/whats-going-on`.
- `install-codex` writes `~/.agents/skills/whats-going-on`.
- `install-no-evals` guarantees `evals/` is absent on every destination.

## How to get to it (user POV)

- One command: `./scripts/install-local.sh --host all` (or `--host cursor|claude|codex`).
- Through the harness (isolated HOME): `wgo-verify drive local-host-install`.

## Driving it with wgo-verify

Preconditions:

- Active launched instance; `doctor` shows `home_isolated=ok`.
- Disposable `HOME` is `$WGO_SCRATCH/home` (set by launch). Never the operator's real home.

- **Install all hosts.** Run `wgo-verify drive local-host-install`. Stdout lists `installed cursor|claude|codex -> …` under the scratch home.
- **Confirm Cursor tree.** `HOME/.cursor/plugins/local/whats-going-on/skills/whats-going-on/SKILL.md` exists and `…/evals` does not.
- **Confirm Claude tree.** `HOME/.claude/skills/whats-going-on/SKILL.md` exists and `evals` does not.
- **Confirm Codex tree.** `HOME/.agents/skills/whats-going-on/SKILL.md` exists and `evals` does not.
- **Proof.** `artifacts/<run_id>/local-host-install/installed-tree.txt` lists the three `SKILL.md` paths and the scratch `HOME=`.

## Gotchas

- Driving install without an isolated `HOME` overwrites the operator's real plugin/skill dirs. Always use `wgo-verify launch` first.
- Re-running is idempotent (`rsync --delete`) inside the disposable home.
- Marketplace publish is out of scope for this script; do not treat marketplace install as verified here.
- Enabling the Cursor plugin in Customize UI is a manual host step outside this harness.
