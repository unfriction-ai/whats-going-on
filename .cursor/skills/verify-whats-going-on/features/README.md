# whats-going-on verification map

This directory is the maintained source for verifying user- and operator-facing behavior of whats-going-on. Read the index before driving, then use the matching feature file as the recipe.

## Baseline preconditions

- Launch with `.cursor/skills/verify-whats-going-on/bin/wgo-verify launch` so the eval venv and disposable `HOME` are under `scratch/<run_id>/`.
- Run `wgo-verify doctor` and require `home_isolated=ok`, `check OK`, and `canonical skill ok`.
- Never drive an install under the operator's real `$HOME`. Concurrent runs each get their own `scratch/<run_id>/`.
- Canonical skill body: `skills/whats-going-on/`. Eval suite: `evals/whats-going-on/` (never installed with the skill).
- Cursor live `run` is wired when the `agent` CLI is on `PATH`. Classification features always prove the fixture gold path; they record live status as `ok`, `unreachable_missing_cli`, or `stubbed_HostNotWired` for hosts that still lack an argv builder.

## Driving conventions

- Start every recipe from a launched, doctor-green instance unless its preconditions say otherwise.
- Prefer fixture ids (`case-a`, `case-f`), script paths, and CLI subcommands over free-form prompts.
- Treat every command as literal. Keep flags and fixture ids unchanged.
- Run all actions through `wgo-verify` when possible so evidence lands under `artifacts/<run_id>/`.
- After install mutations, leave proof artifacts; cleanup removes only scratch.

## Proof and skip reporting

- Capture the command transcript and the observable end state.
- Install proof includes host path listings and explicit absence of `evals/`.
- Classification proof includes the `/whats-going-on` prompt, gold response, and `gold-grade.json` with score `1.0`.
- Record the live path in `proof.txt` as `live_run=ok`, `live_run=unreachable_missing_cli`, `live_run=unreachable_missing_auth`, or `live_run=stubbed_HostNotWired`. Only `ok` counts as a live verified entry point.
- Record the feature id and entry point with every artifact.
- An unreachable entry point is a failure with the unmet precondition named in Gotchas — never weaken the journey.

## Feature entry contract

Each feature file starts with an H1 title and one paragraph describing the user-visible behavior. It then uses exactly four H2 sections in this order.

1. `Sub-features`
2. `How to get to it (user POV)`
3. `Driving it with wgo-verify`
4. `Gotchas`

## Features

- [Eval suite health](./eval-suite-health.md) — drift, gold self-test, schema_cases, principles table via `check`.
- [Canonical skill integrity](./canonical-skill-integrity.md) — identical skill trees; no evals in host mounts.
- [Local host install](./local-host-install.md) — Cursor, Claude, Codex install without copying evals.
- [Abstain on a vague ask](./abstain-vague-ask.md) — Case A needs_clarification without inventing metrics.
- [Split a compound ask](./compound-classification.md) — Case F one primary plus deferred prevention.
