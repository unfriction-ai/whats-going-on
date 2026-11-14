# Abstain on a vague ask

Abstain on a vague ask is the Case A user journey: paste a symptom-only concern, get `needs_clarification`, and stop without inventing metrics or proposing where to look first.

## Sub-features

- `abstain-status` returns `status: needs_clarification` with an empty `problems` list.
- `abstain-clarify` asks for change, magnitude, and timeframe (or equivalent clarity).
- `abstain-no-invent` does not invent crash, retention, churn, store-rank, ANR, or rating details.
- `abstain-no-solve` does not recommend investigation steps or fixes.
- `abstain-applied` cites `principle-dont-invent-problems` when that citation kept the concern unresolved.

## How to get to it (user POV)

- Invoke the skill with the Case A paste:

```text
/whats-going-on

Slack from a product owner:
"Mobile is in a rough place right now and every eng has a different theory.
Can you help me figure out where we should even look first?"
```

- Fixture id for the harness: `case-a` under `evals/whats-going-on/fixtures/seed/`.

## Driving it with wgo-verify

Preconditions:

- Active launched instance with `doctor` green.
- Fixture `case-a` present in the seed suite.
- Cursor live `run` needs the `agent` CLI on `PATH` and an authenticated session (`agent login` or `CURSOR_API_KEY`). Without those the drive still grades gold and records the live path as unreachable.

- **Submit the vague ask (contract path).** Run `wgo-verify drive abstain-vague-ask`. The harness grades the Case A gold response.
- **Confirm status.** `artifacts/<run_id>/abstain-vague-ask/gold-grade.json` shows `gold_status=needs_clarification`, `problem_count=0`, `scores` all `1.0`, and empty `hard_fails`.
- **Confirm prompt.** `prompt.txt` starts with `/whats-going-on` and includes the mobile “rough place” paste.
- **Live path status.** `proof.txt` records one of `live_run=ok`, `live_run=stubbed_HostNotWired` (non-cursor hosts), `live_run=unreachable_missing_cli`, or `live_run=unreachable_missing_auth`. When `live_run=ok`, also keep the graded report under `evals/whats-going-on/reports/<run_id>/`.
- **Proof.** Keep `gold-grade.json`, `prompt.txt`, `gold-response.txt`, and `proof.txt`.

## Gotchas

- Inventing crash rates or “look at X first” is a hard fail for this fixture even if status is correct.
- `check OK` alone is not a Case A user-path proof; drive this feature (or a live `run`) explicitly.
- Gold-only proof covers the fixture contract. Live proof needs `live_run=ok` plus the agent transcript and graded report.
- Missing change/magnitude/timeframe clarity in the clarification text fails the README Quick check intent.
