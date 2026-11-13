# Synthesized design: whats-going-on slice 1

## Problem

Slice 1 needs one installable skill that maps unstructured asks onto the README contract, plus an eval suite that measures agent behavior under that skill. The README is both the human tutorial and the answer key, so fixtures must not ship inside the copied skill folder. Abstention precision is a hard fail. Solving during classification is a hard fail.

## Synthesis decision

Base: arena candidate 1 ([Architect sketch candidate 1](aef90085-3e9b-48a7-9714-6215cac4db21)), recommended by [Cross-judge](5896744d-dd53-4a2c-a510-5bdf14db4882) (27/30 vs 26/30).

Grafts from candidate 2 ([Architect sketch candidate 2](48f695b1-9a61-4218-841c-4d59d263c06e)):

1. Sibling eval tree at `evals/whats-going-on/`. Mount allowlist excludes README. Skill directory must not contain unexpected files at eval time.
2. Families derived from expectation shape. Rubric criterion names must equal grader keys.
3. `schema_cases/` regression set for parse and status derivation.

Rejected from C1: evals inside the skill folder, stored family tags, undefined score threshold as a gate.

Rejected from C2: hard-fail on preamble, Case J as four fresh workspaces, global digit-run hard fail, three-file agent read path.

## Usage (caller's view)

Skill user:

```text
/whats-going-on

<paste>
```

Optional restatement (≤400 chars), one YAML block, then stop.

Operator:

```text
python -m whats_going_on_eval check
python -m whats_going_on_eval run --only case-a,case-f
python -m whats_going_on_eval run --repeat 3 --judge
python -m whats_going_on_eval grade <runId>
python -m whats_going_on_eval compare <runA> <runB> --blind
```

Exit 0: no hard fails. Exit 1: hard fail. Exit 2: harness or drift error. Score is informational. Hard fails gate the run.

## Shape

```text
skills/whats-going-on/          # installable. Agent mount: SKILL.md only.
  README.md                     # human contract. Not mounted in measured runs.
  SKILL.md
  design/

evals/whats-going-on/           # never installed with the skill
  README.md
  requirements.txt
  rubric.md
  judge.md
  fixtures/seed/ case-a … case-j
  fixtures/holdout/
  schema_cases/
  whats_going_on_eval/
    __main__.py
    manifest.py                 # AGENT_MOUNT, hosts, suite version
    parse.py                    # raw text -> Verdict | violation
    fixtures.py                 # load, derive families
    drift.py                    # README ↔ fixtures ↔ SKILL contract
    grade.py                    # hard fails + deterministic axes
    judge.py                    # evidence axis only
    agents.py                   # host invoke (stub until CLIs wired)
    runs.py                     # transcripts and reports
    run.py                      # check | run | grade | compare
```

Status is derived from whether `problems` and `unresolved` are empty. Parser rejects a claimed status that disagrees. Fixture turns are tagged `abstain` or `classify`. Classifying on an abstain turn is a hard fail. Gold answers must score 1.0 under `check`.

## Tradeoffs accepted

- Bounded preamble allowed. Matches README restatement and "link not read."
- Case J is one continuing session. Tests lifecycle leakage.
- Only hard fails gate exit code. Score is for comparing revisions.
- Python eval harness. No Bun required for operators.
- Claude and Codex invoke stay unwired until those CLIs are confirmed. `check` and schema grading run without a host.

## Open questions and risks

- Host CLIs for non-interactive Claude Code and Codex against a temp skill dir. Cursor uses the agent CLI.
- Whether hosts still load `~/.cursor/skills` during measured runs.
- Case J turn 4 refers to "these three initiatives" without listing them. Fixture expects conceptual convergent per README.

## Next implementation step

Done: `SKILL.md`, sibling eval package, parse, grade, fixtures A–J plus holdouts, drift check, schema_cases, operator README. `python -m whats_going_on_eval check` passes. Cursor `agents.invoke` calls the agent CLI. Claude and Codex stay unwired.
