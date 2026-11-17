# Grounding: challenger session (define-the-problem extension)

## Problem we are extending

Stage 1 (`define-the-problem`) already sharpens one primary, proposes a SMART question, classifies on 2×2, and walks the Problem Statement Worksheet. After that hardening, the paste can still be warped by anchoring, confirmation bias, sunk cost, or groupthink. Intent (Emily/Marc): a bounded challenger ritual that argues the other perspective so blind spots get checked before the definition is treated as settled.

## Subsystem: coordinator (`skills/whats-going-on/SKILL.md`)

Owns stage selection, the principles index, the Output envelope (`applied` + `stop: true`), Halt for missing later stages, and the rule that Ask-yourself / worksheet answers are new facts that restart define-the-problem on ask+answers. Does not own stage-1 field layout. Measured mounts exclude `README.md` and `design/`. Plugin mirror under `plugins/whats-going-on/skills/whats-going-on/` must stay in sync with `skills/`.

## Subsystem: playbook (`playbooks/define-the-problem.md`)

Owns the ordered step table and the stage-1 YAML contract. Steps 1–9 today: ask → restate → separate → extract → clarity → primary → smart → classify-2x2 → worksheet. Status is derived last from emptiness of `problems` and `unresolved` (`classified` only when one primary and zero unresolved). Unresolved order invariant: concerns first, then worksheet ask row, then SMART gap rows. Never invent worksheet cell text. Never invent SMART facts. Dual mirror of the playbook file.

## Subsystem: leaf skills

Each leaf is `disable-model-invocation: true`, silent notes only; the playbook Output is the sole user-visible artifact.

| Leaf | Owns |
|---|---|
| ask / restate / separate / extract / clarity | early pipeline notes |
| classify-2x2 | quadrant on the primary |
| smart | Cards table SSOT; `smart_question` / `smart_gaps`; Ask-yourself gap rows |
| worksheet | Areas/Skips/Stop/Hand-back SSOT; cells; one ask row while open |
| principle-* | governed kinds; `applied[]` citations |

`principle-dont-invent-problems` governs `[problem, unresolved, classification, smart_question]`. Explicitly: never add a fact/metric/timeframe/cause/quadrant the input does not give. Worksheet cells omitted from `at` (no pointer). Any challenger prose that adds facts would violate this principle.

## Subsystem: eval wire (`evals/.../whats_going_on_eval/`)

- `parse.py`: `VERDICT_KEYS` closed set; unknown keys = schema violation; `derive_status`; `Verdict.concerns` strips worksheet ask + SMART gaps.
- `smart.py`: `NoPrimary | Withheld | Proposed`; gap rows must close unresolved in card order.
- `worksheet.py`: registry loaded from leaf; `AreaId` / skip statuses literals must match leaf tables (drift).
- `wire.py`: shared `Unresolved`, `ContractViolation`.
- `drift.py`: README ↔ fixtures ↔ playbook contract key equality; principle `governs`; worksheet/SMART registry drift.
- Fixtures under `fixtures/seed|holdout`; schema under `schema_cases/`; suite version bumps when wire changes.
- Pattern for prior extensions (SMART #23, worksheet #24–#28): leaf table as SSOT → Python registry/parser → playbook step + Output keys → gold/schema/README → SUITE_VERSION.

## Why the existing layering (from the record)

Commits and `design/synthesis.md` / SMART ship notes: stage-1 extensions are **deep leaves** whose tables are the single source of truth; the playbook only sequences them; the harness parses the leaf so drift fails `check`. Status stays a function of `problems`×`unresolved` emptiness — new work that should block “done” must appear as unresolved (or change that derivation deliberately). Inference: a challenger that only writes advisory prose outside unresolved cannot block `classified` without a new status rule; a challenger that always adds unresolved will false-stall clean pastes.

## Natural insertion points (risks)

Detail from [Grounding explore](e972925a-745d-48b2-b9c0-e931ac87fca9): unresolved order is **concerns → worksheet ask → SMART gap tail**. A new concern-prefix row needs no parser change but blocks `classified` while present. A new root key or a row after the worksheet ask requires parser/partition changes. Do not mutate SMART Cards or worksheet Areas tables from a challenger hypothesis.

1. **Silent note (ask/separate pattern)** — After clarity or primary; may only demote/withhold. Risk: invisible to `applied` if it changes nothing; demoting the only Defined row skips SMART+worksheet.
2. **Concern-prefix question** — One `{observation, reason, clarification}` before the worksheet ask; clarification must not collide with `Ask yourself: ` or worksheet probes/hand-back. Risk: standing row makes README `classified` unreachable; counts as a concern for abstention scoring.
3. **New principle only** — Cite within today’s `WireKind`. Risk: no ritual surface; cannot point at worksheet.
4. **Post–step-9 repair** — Drop ungrounded cells / withhold invented SMART. Risk: “sharpen” rewrite invents metrics.
5. **Later chain stage** — `consumes: problem_map`. Risk: Ask-yourself/worksheet answers **restart** define-the-problem, so a pre-classification challenger cannot live in stage 2.
6. **New root field + leaf (SMART/worksheet pattern)** — Closed `VERDICT_KEYS`; README↔playbook contract byte-identical; every gold grows the key; `solve_leak` must opt into scanning it. Deepest gradeable ritual; largest wiring blast radius.
7. **Trigger timing** — After worksheet complete (step 10) vs earlier when bias markers are loud: experiment to settle in fixtures.

## Wiring checklist (any new root key or playbook leaf)

Playbook + README contract (identical), `parse.py` `VERDICT_KEYS`/`Verdict`, `drift.py` guard body, all fixture golds, schema_cases, optional `WireKind`/`applied.at`/principle `governs`, `grade.py` prose fields, `fixtures.py` expects, plugin mirror via `scripts/assert-canonical-skill.sh`, bump `SUITE_VERSION` in `manifest.py` when mounts must invalidate. If a new unresolved role is not a concern-prefix row: also `partition_unresolved`, `ask_row`, worksheet probe place, `smart_gap_tail`.

## Experimental choices (settle in implement / fixtures; do not bake preference)

Trigger timing; opposite-framing vs assumption stress-test; dedicated block vs freeform; blocking unresolved vs advisory-only. Product choices left to human: ritual name, mandatory vs opt-in, tone, always-all-four-biases vs evidenced-only, UI beyond two-sentence+yaml.

## Invariants the design must not break

- No invented SMART facts or worksheet cells.
- Closed `VERDICT_KEYS` / drift / dual skill+plugin trees.
- `classified` ↔ empty unresolved still holds unless design explicitly changes derivation (and proves it).
- `applied.at` paths stay validated; new cite targets need coordinator table + principle `governs`.
- Restatement still exactly two sentences; no post-YAML chatter; no solving (`principle-dont-solve-yet`).
