# Install whats-going-on

One skill body lives at `skills/whats-going-on/`. Host plugins and local installs point at that folder. Never copy `evals/` into a skills or plugin mount.

## Hosts

### Cursor

Preferred. Local plugin for Customize.

```bash
mkdir -p ~/.cursor/plugins/local
rsync -a --delete \
  --include='.cursor-plugin/***' \
  --include='skills/***' \
  --exclude='*' \
  ./ ~/.cursor/plugins/local/whats-going-on/
```

Then open Cursor Customize and enable `whats-going-on`. Invoke with `/whats-going-on`.

Fallback. Copy `skills/whats-going-on/` to `.cursor/skills/whats-going-on/` or `~/.cursor/skills/whats-going-on/`.

### Claude Code

Preferred. One-step install on Claude Code 2.1.275 or later.

```text
/plugin install whats-going-on --marketplace unfriction-ai/whats-going-on
```

Or from the shell.

```bash
claude plugin marketplace add unfriction-ai/whats-going-on
claude plugin install whats-going-on@whats-going-on-marketplace
```

Local checkout without marketplace.

```bash
claude --plugin-dir /path/to/whats-going-on
```

Plugin invoke. `/whats-going-on:whats-going-on`.

Fallback. Copy the skill folder to `.claude/skills/whats-going-on/` or `~/.claude/skills/whats-going-on/`.

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
