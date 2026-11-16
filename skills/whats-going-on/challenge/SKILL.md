---
name: challenge
description: >-
  Argues the other side of a finished definition, one bounded round, from
  quotes in the paste only, for the whats-going-on define-the-problem playbook.
disable-model-invocation: true
---

# Challenge

Run one round that argues the other side of the definition. Quote the paste word for word.
Never add a fact. `principle-dont-invent-problems` still bans fabricated facts in every string.

## Biases

| Bias | Move | Symptom in the paste | Other side |
|---|---|---|---|
| `anchoring` | `drop_span` | A number, date, estimate, or option arrives first and the ask treats it as given, with no alternative named. | "{quote}" may be the first figure or option you heard, not the right one. What would you ask if you had never seen it? |
| `confirmation_bias` | `restore_span` | The paste names the answer it expects, or cites only agreeing evidence, with nothing that could disagree. | "{quote}" is in the paste but not in the primary as framed. What would you expect if it were wrong, and have you looked? |
| `sunk_cost` | `drop_span` | Time, money, or effort already spent is given as a reason to continue. | "{quote}" counts what is already spent. If you were starting today, would you still choose this? |
| `groupthink` | `name_missing_party` | Agreement is given as the reason, with no dissent recorded. | "{quote}" leans on agreement. Who would disagree, and what would they say? |

## Quote

One clause from the paste, word for word, at most 160 characters. Never quote a probe line,
an `Ask yourself:` line, or the Challenge line. Worksheet replies are paste.

## Reply

Reply under this line, or say "I hold this framing."

## Steps

1. Run only when the worksheet is complete. Otherwise write `challenge: null`.
2. For each bias in table order, look for its symptom. Record a finding only with a quote.
   At most one finding per bias. Never record a bias the paste does not show. Quotes across
   findings must be distinct. If a quote would also fit an earlier bias, only the earlier bias keeps it.
3. No findings: `round: clear`. Add no row.
4. Findings, and no line in the paste starts with `Challenge: `: `round: open`. Add one Unresolved
   row in the ask slot, before the SMART gap rows. Its `clarification` is `Challenge: `, then each
   finding's Other side with `{quote}` filled, in table order, then the Reply sentence, joined by spaces.
5. Findings, and the paste has a `Challenge: ` line: `round: answered`. Copy the text under that line
   into `reply`, or `null` when there is none. Add no row. Do not open a second round.
6. Never change `problems`, `smart_question`, `worksheet`, or any other row.
