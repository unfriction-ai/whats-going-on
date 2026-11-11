# whats-going-on

Slice 1 coding-agent skill. Maps an unstructured ask onto a 2×2 (analytical or conceptual × convergent or divergent), abstains when a problem is not defined, and stops before diagnosis or solutions.

## Install

Canonical skill directory. `skills/whats-going-on/`.

Do not copy `evals/` into any host skills path. Full matrix. [docs/install.md](docs/install.md).

| Host | Preferred install |
|---|---|
| Cursor | Plugin (coming next) or copy to `.cursor/skills/whats-going-on/` / `~/.cursor/skills/whats-going-on/` |
| Claude Code | Plugin (coming next) or copy to `.claude/skills/whats-going-on/` / `~/.claude/skills/whats-going-on/` |
| Codex | Copy to `~/.agents/skills/whats-going-on/` or `.agents/skills/whats-going-on/` (legacy `.codex/skills` still works on older builds) |

```bash
bash scripts/assert-canonical-skill.sh
```

Product contract and worked cases. `skills/whats-going-on/README.md`.

## Invoke

```text
/whats-going-on

<paste the situation>
```

Claude Code plugin sessions use `/whats-going-on:whats-going-on` once the Claude plugin is installed.

## Evals

Executable suite. `evals/whats-going-on/`. Sibling of the skill. Never installed with it.

```bash
cd evals/whats-going-on
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m whats_going_on_eval check
```

## License

Apache-2.0. See `LICENSE`.
