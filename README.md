# whats-going-on

Stage 1 coding-agent skill. It inspects a pasted ask, restates it in two sentences, picks at most one primary problem, classifies that problem on a 2×2 (analytical or conceptual × convergent or divergent), or abstains when the problem is not defined. It cites principles under `applied` when they decided a value, and it stops before diagnosis or solutions.

Later stages on the coordinator chain Halt until their playbooks exist.

## Install

One command for local Cursor, Claude Code, and Codex paths.

```bash
./scripts/install-local.sh --host all
```

Host-only. `./scripts/install-local.sh --host cursor|claude|codex`

Canonical skill directory. `skills/whats-going-on/`.

Do not copy `evals/` into any host skills path. Full matrix and marketplace flows. [docs/install.md](docs/install.md).

| Host | Preferred install |
|---|---|
| Cursor | `./scripts/install-local.sh --host cursor`, then Customize. Or local plugin under `~/.cursor/plugins/local/whats-going-on` |
| Claude Code | `./scripts/install-local.sh --host claude`, or `/plugin install whats-going-on --marketplace unfriction-ai/whats-going-on`. Invoke `/whats-going-on:whats-going-on` |
| Codex | `./scripts/install-local.sh --host codex`, or `codex plugin marketplace add unfriction-ai/whats-going-on` then `/plugins` (legacy `.codex/skills` on older builds only) |

Create the eval venv in the Evals section first. From the repo root, run `bash scripts/pr-gates.sh`. It wraps `whats_going_on_eval check` and `assert-canonical-skill.sh`.

```bash
bash scripts/pr-gates.sh
```

Product contract and worked cases. `skills/whats-going-on/README.md`.

## Invoke

```text
/whats-going-on

<paste the situation>
```

Claude Code plugin sessions use `/whats-going-on:whats-going-on`.

## Evals

Executable suite. `evals/whats-going-on/`. Sibling of the skill. Never installed with it.

```bash
cd evals/whats-going-on
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ../..
bash scripts/pr-gates.sh
```

Cursor live runs need the `agent` CLI on `PATH` and `agent login` or `CURSOR_API_KEY`. Claude and Codex are not wired yet.

## Verify

Maintainer harness for install, suite health, Case A, and Case F:

```bash
.cursor/skills/verify-whats-going-on/bin/wgo-verify launch
.cursor/skills/verify-whats-going-on/bin/wgo-verify doctor
.cursor/skills/verify-whats-going-on/bin/wgo-verify drive eval-suite-health
```

Feature map. `.cursor/skills/verify-whats-going-on/features/README.md`.

## License

Apache-2.0. See `LICENSE`.
