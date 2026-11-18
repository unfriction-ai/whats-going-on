# Claude Skill tool first invoke

The first `/whats-going-on` on Claude runs when that host sends the slash through the Skill tool. The coordinator `SKILL.md` omits `disable-model-invocation`. Leaf skills and principles keep the flag.

## Sub-features

- `coordinator-omits-flag` makes `python -m whats_going_on_eval check` fail when the coordinator frontmatter sets `disable-model-invocation: true`.
- `skill-tool-accepts-user-skill` launches `whats-going-on` through the Skill tool and returns a stage view.
- `skill-tool-accepts-namespaced` launches `whats-going-on:whats-going-on` through the Skill tool.
- `leaves-keep-flag` keeps `disable-model-invocation: true` on leaf skills and principles.

## How to get to it (user POV)

- In Claude for Mac, type `/whats-going-on` as the first message of a chat, then the ask. Desktop routes that slash through the Skill tool.
- On the CLI, `claude -p` with a prompt that names the Skill tool calls the same tool.

## Driving it with wgo-verify

`wgo-verify drive` does not register this feature. Its launches use an isolated `HOME` and never call the operator's Claude. Run the commands below on the operator machine after the coordinator in this repo omits the flag.

Preconditions:

- `bash scripts/pr-gates.sh` prints `PR gates: all 2 passed`.
- `./scripts/install-local.sh --host claude` has copied `skills/whats-going-on/` to `~/.claude/skills/whats-going-on`.
- `~/.claude/plugins/cache/whats-going-on-marketplace/whats-going-on/0.1.0/skills/whats-going-on/SKILL.md` omits `disable-model-invocation`. That file is the installed plugin `whats-going-on@whats-going-on-marketplace` 0.1.0. Patch it by hand. `install-local.sh` does not write it.

- **Check the coordinator.** From `evals/whats-going-on`, run `python -m whats_going_on_eval check`. Expect `check OK`.
- **Invoke either name.** Run `claude -p --dangerously-skip-permissions -- "Use the Skill tool to invoke whats-going-on (or whats-going-on:whats-going-on) with: Checkout latency rose 40%."`
- **Invoke the plugin name.** Run `claude -p --dangerously-skip-permissions -- "Use the Skill tool to invoke whats-going-on:whats-going-on with: Checkout latency rose 40%. Do not invoke the un-namespaced whats-going-on skill."`
- **Confirm acceptance.** Save both stdout streams in `artifacts/claude-skill-tool-after-fix.txt`. The file has a stage view or the plugin classification. It has no line `cannot be used with Skill tool due to disable-model-invocation`.

## Gotchas

- This recipe writes the operator's real `~/.claude`. Other features require `wgo-verify launch` and a scratch `HOME`.
- The proof is the CLI Skill-tool transcript. The Claude for Mac window is untested. Desktop and this CLI share the Skill tool, and the CLI can still pick a different skill install than the Desktop chat.
- The either-name prompt launched the user skill at `~/.claude/skills/whats-going-on` (`Launching skill: whats-going-on`, `success: true`). That tree matches the canonical skill.
- The plugin-name prompt launched `whats-going-on:whats-going-on` (`success: true`). The cache body is still published slice 1, with only the flag line removed. A marketplace update from `unfriction-ai/whats-going-on` restores the flag and the refusal.
- The same one-line flag removal is also on the marketplace checkout `~/.claude/plugins/marketplaces/whats-going-on-marketplace/skills/whats-going-on/SKILL.md`. That git worktree is dirty.
- Leaf skills still set the flag. A Skill-tool call of a leaf refuses. This recipe invokes the coordinator only.
