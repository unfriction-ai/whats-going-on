# Canonical skill integrity

Canonical skill integrity keeps every in-repo `whats-going-on` skill tree identical to `skills/whats-going-on/` and keeps host plugin manifests from mounting `evals/`.

## Sub-features

- `assert-hash` fails when any in-repo `whats-going-on/SKILL.md` drifts from the canonical hash.
- `assert-tree` fails when a non-canonical copy’s full tree differs from the canonical directory (dotfiles excluded).
- `assert-no-evals-mount` fails when a `plugin.json` or `marketplace.json` references `evals/`.
- `symlink-or-copy-ok` allows identical-hash copies. Symlinked skill dirs are skipped by the finder rather than resolved as a separate pass.

## How to get to it (user POV)

- From `docs/install.md`: `bash scripts/assert-canonical-skill.sh`. Root `README.md` points operators at `bash scripts/pr-gates.sh`, which runs the same assert.
- Through the harness: `wgo-verify drive canonical-skill-integrity`.

## Driving it with wgo-verify

Preconditions:

- Active launched instance with `wgo-verify doctor` green.
- Working tree contains `skills/whats-going-on/SKILL.md`.

- **Run assert.** Execute the integrity script. Run `wgo-verify drive canonical-skill-integrity`. Transcript ends with `canonical skill ok`.
- **Confirm no evals mount.** The drive also greps `plugin.json` and `marketplace.json` under `.cursor-plugin`, `.claude-plugin`, and `plugins/` and fails if `evals/` appears there.
- **Proof.** `artifacts/<run_id>/canonical-skill-integrity/assert.txt` and `proof.txt` record the entry and observable.

## Gotchas

- Editing only `plugins/whats-going-on/skills/whats-going-on/SKILL.md` without updating the canonical body fails this feature by design.
- Identical content at two paths is allowed; mismatched content is not.
- Skill README prose that mentions `evals/` is not a mount. Only host manifests are gated.
- This feature does not install into host home directories. Use `local-host-install` for that.
