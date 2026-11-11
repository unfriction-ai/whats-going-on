# Install whats-going-on

One skill body lives at `skills/whats-going-on/`. Host plugins and local installs point at that folder. Never copy `evals/` into a skills or plugin mount.

## Hosts

### Cursor

Preferred. Install the Cursor plugin (see root README once PR-B lands), or copy `skills/whats-going-on/` to `.cursor/skills/whats-going-on/` or `~/.cursor/skills/whats-going-on/`.

Invoke with `/whats-going-on`.

### Claude Code

Preferred. Install the Claude plugin from this repo's marketplace (see root README once PR-C lands), or copy the skill folder to `.claude/skills/whats-going-on/` or `~/.claude/skills/whats-going-on/`.

Plugin invoke is `/whats-going-on:whats-going-on`.

### Codex

Preferred user path. `~/.agents/skills/whats-going-on/`.

Preferred repo path. `.agents/skills/whats-going-on/`.

Legacy. `~/.codex/skills/whats-going-on/` and `.codex/skills/whats-going-on/` still work on older Codex builds. Prefer `.agents/skills`.

Plugin install via Codex `/plugins` lands with PR-D.

## Check the repo

```bash
bash scripts/assert-canonical-skill.sh
```

That script fails if a second real `SKILL.md` drifts from the canonical file, or if a host manifest references `evals/`.
