# Rubric: whats-going-on slice 1

Criterion names must equal grader keys in `grade.py` (`RUBRIC`). Weights sum to 1.0.

| Criterion | Key | Weight | Owner |
|---|---|---|---|
| Problem detection | `detection` | 0.25 | deterministic |
| Correct abstention | `abstention` | 0.25 | deterministic |
| Problem separation | `separation` | 0.15 | deterministic |
| 2×2 classification | `classification` | 0.20 | deterministic |
| Evidence and uncertainty | `evidence` | 0.15 | judge only |

Hard fail (gates the run, independent of score):

- Classifying when no problem is established (`kind: abstain` turn with any `problems`).
- Output contract violation (missing YAML, content after stop, status mismatch).
- Treating a proposed method as the problem (`methodNotProblem` tripwire).
- Invented detail (`invented` tripwire).
- Solve leak (global patterns plus per-fixture `solveLeak`).

Only hard fails change the exit code. Score compares skill revisions. Without `--judge`, the evidence axis is N/A and other weights renormalize.
