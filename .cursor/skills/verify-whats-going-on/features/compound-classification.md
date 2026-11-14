# Split a compound ask

Split a compound ask is the Case F user journey: one paste with two questions yields one primary problem under status `partial` and the dependent ask deferred under `unresolved`. The skill stops before diagnosis or prevention plans.

## Sub-features

- `split-one-primary` returns exactly one entry under `problems` with status `partial`.
- `split-why-analytical-convergent` classifies the outage-why ask as analytical + convergent.
- `split-prevent-deferred` keeps the prevention-options ask in `unresolved` until the why is answered.
- `split-no-solve` does not state a root cause or recommend a prevention plan in this slice.
- `split-applied` cites `principle-read-the-room` at the primary and the deferred row when those citations decided the values.

## How to get to it (user POV)

- Invoke the skill with the Case F paste:

```text
/whats-going-on

From the director of engineering after a staging outage:
"I want to know exactly why staging went down last night, and I want three realistic
ways to stop this class of failure, ranked by how likely they are to work."
```

- Fixture id for the harness: `case-f` under `evals/whats-going-on/fixtures/seed/`.

## Driving it with wgo-verify

Preconditions:

- Active launched instance with `doctor` green.
- Fixture `case-f` present in the seed suite.
- Cursor live `run` needs the `agent` CLI on `PATH` and an authenticated session (`agent login` or `CURSOR_API_KEY`). Without those the drive still grades gold and records the live path as unreachable.

- **Submit the compound ask (contract path).** Run `wgo-verify drive compound-classification`. The harness grades the Case F gold response.
- **Confirm split.** `artifacts/<run_id>/compound-classification/gold-grade.json` shows `gold_status=partial`, `problem_count=1`, scores `1.0`, empty `hard_fails`.
- **Confirm prompt.** `prompt.txt` includes both the “why staging went down” and “ways to stop” asks under `/whats-going-on`.
- **Live path status.** `proof.txt` records one of `live_run=ok`, `live_run=stubbed_HostNotWired` (non-cursor hosts), `live_run=unreachable_missing_cli`, or `live_run=unreachable_missing_auth`. When `live_run=ok`, also keep the graded report under `evals/whats-going-on/reports/<run_id>/`.
- **Proof.** Keep `gold-grade.json`, `prompt.txt`, `gold-response.txt`, and `proof.txt`.

## Gotchas

- Emitting two `problems` rows fails the one-primary contract even if both quadrants look right.
- Collapsing both asks into one classified quadrant without deferring prevention also fails Case F.
- Producing a root-cause narrative or a ranked prevention list in this slice is a solve-leak hard fail.
- Gold-only proof covers the fixture contract. Live proof needs `live_run=ok` plus the agent transcript and graded report.
