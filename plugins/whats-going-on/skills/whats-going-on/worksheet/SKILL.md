---
name: worksheet
description: >-
  Walks the solo Problem Statement Worksheet after a grounded SMART question
  for the whats-going-on define-the-problem playbook.
disable-model-invocation: true
---

# Worksheet

Fill the Problem Statement Worksheet from the paste only. Never invent cell text. `principle-dont-invent-problems` still bans fabricated facts in every string you emit. `problem_question` is the current `smart_question`. It is not a cell.

## Areas

| Area | Probe |
|---|---|
| `context_constraints` | Context and constraints: Around "{question}", what background or pressures shape how you solve it, and what cannot change? |
| `success_criteria` | Success criteria: For "{question}", what has to be true for the answer to count as success, and what would make it fail? |
| `stakeholders` | Stakeholders: Who can make or block the decision behind "{question}", and who must agree? Say "I am the decider" if that is you. |
| `scope_sources` | Scope and sources: For "{question}", what is in and out of scope, and where does evidence already exist? |

## Skips

| Status | Area | Says |
|---|---|---|
| `unknown` | any | I don't know |
| `not_yet` | any | Not yet |
| `i_am_decider` | `stakeholders` | I am the decider |

Recording (leaf prose the model follows; constructors still reject a skip phrase stored as a fill):

- `unknown` when the reply is empty, matches a short cousin (`i don't know`, `dont know`, `don't know`, `unknown`, `no idea`) with optional trailing period or at most 24 extra characters, or starts with `i don't know` / `don't know` at any length (drop trailing prose).
- `not_yet` for short cousins (`not yet`, `don't have it yet`, `dont have it yet`, `later`, `still gathering`) the same way, or starts with `not yet` at any length.
- `i_am_decider` only as a short cousin reply on stakeholders (`i am the decider`, `i'm the decider`, `i decide`, `i'm the decision maker`). A longer reply that merely mentions the phrase stays filled.

## Stop

Stop when every area is filled or skipped. When `smart_gaps` is not empty, also stop after 2 skips in a row.

## Hand-back

Answer the Ask yourself prompts in this fence. Then paste those answers with the Sheet lines so far.

## Steps

1. Run only when `smart_question` is a non-null proposed string. Otherwise leave the sheet unstarted.
2. Re-derive cells from the paste. Match each prior probe by its area label (text before `: `). Do not copy the previous fence.
3. Walk areas in table order. Stop at the first area with no reply in the paste.
4. Ask exactly one open area when the stop rule says asking. Put that probe as one Unresolved row immediately before the SMART gap suffix. Its `clarification` is the area probe with `{question}` replaced by this run's `smart_question`.
5. When the stop rule says handed back, put the Hand-back sentence as that row's `clarification` instead (exact text from ## Hand-back).
6. Never write a cell the paste did not answer.
