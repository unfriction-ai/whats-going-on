# whats-going-on

Slice 1 coding-agent skill. Maps an unstructured ask onto a 2×2 (analytical or conceptual × convergent or divergent), abstains when a problem is not defined, and stops before diagnosis or solutions.

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

## License

Apache-2.0. See `LICENSE`.
