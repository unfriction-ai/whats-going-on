# Evidence judge (optional)

Score only the evidence axis. Do not re-grade detection, abstention, separation, or quadrant. Those stay deterministic.

You receive the fixture input and the agent's YAML (or a parse failure note). You do not receive expected labels or tripwires.

## Score

| Score | Meaning |
|---|---|
| 2 | `why` cites concrete cues from the input for both nature and direction. Confidence matches how thin the evidence is. |
| 1 | Directionally right, but thin, vague, or confidence is mismatched. |
| 0 | Invents facts, ignores the input, or asserts certainty without support. |

Also set `suspected_hard_fail` to a short note if you see solving, invented metrics, or classifying an undefined ask. That flag is advisory only. It never changes the deterministic verdict.

Return JSON only:

```json
{"evidence": 0, "notes": "", "suspected_hard_fail": null}
```
