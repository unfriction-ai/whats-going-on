# whats-going-on

Slice 1 coding-agent skill. Maps an unstructured ask onto a 2×2 (analytical or conceptual × convergent or divergent), abstains when a problem is not defined, and stops before diagnosis or solutions.

## Install

Copy `skills/whats-going-on/` into your tool's skills path. Keep `SKILL.md` and its README together. Do not copy `evals/`.

| Tool | Typical location |
|---|---|
| Cursor | `.cursor/skills/whats-going-on/` or `~/.cursor/skills/whats-going-on/` |
| Claude Code | `.claude/skills/whats-going-on/` or `~/.claude/skills/whats-going-on/` |
| Codex | `.codex/skills/whats-going-on/` |

Full contract and worked cases. `skills/whats-going-on/README.md`.

## Invoke

```text
/whats-going-on

<paste the situation>
```

## Evals

Executable suite lives in `evals/whats-going-on/`. Sibling of the skill. Never installed with it. Measured runs mount only `SKILL.md`.

```bash
cd evals/whats-going-on
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m whats_going_on_eval check
```

`check` needs no agent. `run` needs a wired host CLI (stubbed until confirmed). Details in `evals/whats-going-on/README.md`.

## License

Apache-2.0. See `LICENSE`.
