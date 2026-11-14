# Synthesized design: whats-going-on stage 1

## Problem

Stage 1 needs one installable skill that maps unstructured asks onto the README contract, plus an eval suite that measures agent behavior under that skill. The README is both the human guide and the answer key, so fixtures must not ship inside the copied skill folder. Abstention precision is a hard fail. Solving during classification is a hard fail.

## Synthesis decision

Base: arena candidate 1 ([Architect sketch candidate 1](aef90085-3e9b-48a7-9714-6215cac4db21)), recommended by [Cross-judge](5896744d-dd53-4a2c-a510-5bdf14db4882) (27/30 vs 26/30).

Grafts from candidate 2 ([Architect sketch candidate 2](48f695b1-9a61-4218-841c-4d59d263c06e)):

1. Sibling eval tree at `evals/whats-going-on/`. Mount allowlist excludes README. Skill directory must not contain unexpected files at eval time.
2. Families derived from expectation shape. Rubric criterion names must equal grader keys.
3. `schema_cases/` regression set for parse and status derivation.

Rejected from C1: evals inside the skill folder, stored family tags, undefined score threshold as a gate.

Rejected from C2: hard-fail on preamble, Case J as four fresh workspaces, global digit-run hard fail, three-file agent read path.

Later ships kept the sibling eval tree and derived families. They replaced the monolith skill with a coordinator plus playbooks (#11), required one primary and `unresolved` (#12), wired Cursor invoke with an isolated HOME (#14–#15), and added principle leaves plus an `applied` wire (#16–#18).

## Usage (caller's view)

Skill user:

```text
/whats-going-on

<paste>
```

Exactly two restatement sentences, one YAML block that ends with `applied` then `stop: true`, then nothing.

Operator:

```text
python -m whats_going_on_eval check
python -m whats_going_on_eval run --agent cursor --only case-a,case-f --repeat 1
python -m whats_going_on_eval run --agent cursor --repeat 3
python -m whats_going_on_eval grade <runId>
python -m whats_going_on_eval compare <runA> <runB> --blind
```

`run --agent cursor` needs the `agent` CLI on `PATH` and an authenticated session (`agent login` or `CURSOR_API_KEY`). Claude and Codex still raise `HostNotWired`. Exit 0: no hard fails. Exit 1: hard fail. Exit 2: harness or drift error. Score is informational. Hard fails gate the run.

Maintainer drive of the same contract:

```text
.cursor/skills/verify-whats-going-on/bin/wgo-verify launch
.cursor/skills/verify-whats-going-on/bin/wgo-verify doctor
.cursor/skills/verify-whats-going-on/bin/wgo-verify drive eval-suite-health
```

## Shape

```text
skills/whats-going-on/          # installable
  README.md                     # human contract. Not mounted in measured runs.
  SKILL.md                      # coordinator: chain, principles index, Halt
  playbooks/define-the-problem.md
  principle-*/SKILL.md
  ask/ restate/ separate/ extract/ clarity/ classify-2x2/
  design/                       # design notes. Not mounted.

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
    manifest.py                 # derived mount, hosts, suite version
    principles.py               # principle registry from the coordinator index
    parse.py                    # raw text -> Verdict | violation
    fixtures.py                 # load, derive families
    drift.py                    # README ↔ fixtures ↔ skill contract
    grade.py                    # hard fails + deterministic axes
    judge.py                    # evidence axis (not wired yet)
    agents.py                   # Cursor invoke; Claude/Codex HostNotWired
    runs.py                     # transcripts and reports
    run.py                      # check | run | grade | compare | invariance

.cursor/skills/verify-whats-going-on/   # maintainer harness (not in CI)
```

Status is derived from whether `problems` and `unresolved` are empty. Parser rejects a claimed status that disagrees. Fixture turns are tagged `abstain` or `classify`. Classifying on an abstain turn is a hard fail. Gold answers must score 1.0 under `check`. Verdicts must include `applied`. Halt blocks must not.

Measured mounts include nested leaves and principles. They exclude `README.md` and `design/`.

## Tradeoffs accepted

- Exactly two restatement sentences. Missing, classifying, or speculating preamble hard-fails.
- Case J is successive asks across invocations. Live `run` uses a fresh Cursor session per turn with that turn's prompt only.
- Only hard fails gate the exit code. Score is for comparing revisions.
- Python eval harness. No Bun required for operators.
- Cursor invoke is wired with a scratch HOME (login keychain linked). Claude and Codex stay unwired until those CLIs are confirmed.
- Stages 2–7 Halt with `available: false` until playbooks ship.

## Open questions and risks

- Host CLIs for non-interactive Claude Code and Codex against a temp skill dir.
- Soft evidence judge (`--judge`) is stored on the run manifest and does not call a live judge yet.
- Case J turn 4 refers to "these three initiatives" without listing them. Fixture expects conceptual convergent per the skill README.

## Next implementation step

Shipped through #19: coordinator and stage-1 playbook, principles and `applied`, Cursor live invoke with isolation, sibling eval package, and the maintainer verify skill. Keep Claude and Codex unwired until their CLIs are confirmed. Wire the evidence judge only when it can fail a run for a real evidence miss.
