---
name: smart
description: >-
  Checks the primary against the five SMART cards and proposes one SMART
  problem question for the whats-going-on define-the-problem playbook.
disable-model-invocation: true
---

# SMART

Check the primary against each card in order. Use only facts in the input. `principle-make-it-smart` decides when a letter is met and when to withhold the question.

## Cards

| Letter | Required | Prompt |
|---|---|---|
| `specific` | yes | Would someone new to this know exactly which problem it is? |
| `measurable` | no | How will we know it is solved? |
| `actionable` | yes | Does it point to something we can do? |
| `relevant` | no | Does it matter to the people who will decide? |
| `time_bound` | no | By when does it need to be solved? |

## Steps

1. For each card, mark the letter met or open.
2. For each open letter, write one Unresolved row. Its `observation` says what the input leaves out. Its `reason` names the letter and what the input lacks. Its `clarification` is `Ask yourself: ` plus the card's prompt, word for word.
3. Put the gap rows after every other Unresolved row, in card order.
4. List the open letters in `smart_gaps`, in card order. Write `[]` when every letter is met.
5. When a required letter is open, `smart_question` is `null`. Otherwise rewrite the primary so it carries each met letter's facts from the input, and write that as `smart_question`. When the primary already carries them, copy it word for word.

A why or diagnostic primary points to something we can do: find the cause with evidence we can reach. "Why did staging go down last night?" meets `actionable`. A why about something outside our reach, with nothing named that we would do with the answer, does not.

The primary stays the primary. `main_question` keeps the primary's statement, and `classify-2x2` classifies the primary, never `smart_question`.

With no primary, skip this step. `smart_question` is `null` and `smart_gaps` is `[]`.
