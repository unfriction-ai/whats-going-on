---
stage: structure-the-problem
command: /where-to-focus
aliases: [/break-it-down, /where-to-start]
consumes: problem_map
produces: issue_tree_candidates
skills: [carry-forward, issue-tree, mece, hypothesis, restate]
---

# Structure the problem

Propose one or more hypothesis-driven breakdowns of the defined problem. Drive each breakdown toward MECE. Stop before prioritizing or solving. The solver chooses which breakdowns, and which branches, to work in parallel.

## Gate

Entry needs only a problem statement. Stage-1 status does not matter.

Collect a governing statement from, in order:

1. Prior define-the-problem `smart_question` when it is a non-null string.
2. Else prior `main_question` when it is a non-null string.
3. Else a problem statement the current paste states outright (the asker's question, or a line labeled `The question` / `Main question`).

| Governing statement | Action |
|---|---|
| Non-blank string from any source above | Continue |
| None | Refuse. One sentence: state the main or SMART problem first. Do not build a tree. |

On continue, set `main_question` to the prior `main_question` when present, else to that governing statement. Set `smart_question` to the prior SMART string when present, else `null`. Prefer `smart_question` as `root_question` when it is non-null. Otherwise root on `main_question`. Never invent or sharpen a new governing question in this stage.

When the paste answers a prior selection ask (names breakdown ids and optional branch ids), fill `selected` from that answer and keep the prior `breakdowns` unless the paste also brings a new ask or new facts that restart define-the-problem.

## Steps

Run each step in order. Each step writes one note. Work silently. Keep the notes out of the reply.

| Step | Skill | Reads | Writes |
|---|---|---|---|
| 1 | `carry-forward` | prior result, paste | root question, classification snapshot, gate, prior selected |
| 2 | `restate` | input, ask note | restatement |
| 3 | `issue-tree` | root, classification, paste | 1–3 breakdown drafts at L1 |
| 4 | Depth (this playbook) | each breakdown | deepen only nodes that need it, ≤ level 3 |
| 5 | `mece` | every sibling set | ME / CE per set |
| 6 | `hypothesis` | every non-root node | subquestions, not answers |
| 7 | Compare (this playbook) | all breakdowns | drop duplicate frames; keep MECE-strong frames |
| 8 | Repair (this playbook) | MECE failures | one revise pass, or `needs_split` |
| 9 | Verdict (this playbook) | survivors | Verdict fields |

Step 2. Re-run `restate` on the current paste. When the paste is unchanged from the define-the-problem turn and a prior restatement is in hand, you may keep those two sentences.

Step 4. Level 3 is a ceiling, not a target. For each breakdown: start from L1 only. Run the MECE checks on that L1 set. Stop when L1 is MECE and every L1 node is already a testable work unit. Else expand only the nodes that fail MECE, stay too broad to test, or leave a named gap. Re-check MECE after each deepen. Never add a child past level 3.

Step 7. A second breakdown earns its place only when its `frame` cuts the root differently and still passes MECE. Drop a draft that only renames another.

Step 8. On any MECE fail after deepen: split, merge, or rephrase once. If a second pass still fails, mark that breakdown `needs_split` and add one Unresolved row whose `clarification` asks how to cut the failing set.

## Status

| Condition | status |
|---|---|
| Gate refused | `blocked` |
| At least one breakdown is `needs_split` after repair | `needs_split` |
| Every kept breakdown is `mece_pass` | `structured` |

## Verdict

```yaml
status: structured | needs_split | blocked

root_question: "SMART question if present, else main_question"
main_question: "carried word for word"
smart_question: "carried" | null

classification: null | { nature: analytical | conceptual, direction: convergent | divergent }

breakdowns:
  - id: A
    frame: "short label for this cut"
    depth_max_used: 1 | 2 | 3
    status: mece_pass | needs_split
    tree:
      id: root
      question: "{root_question}"
      level: 0
      children:
        - id: "A.1"
          question: "…"
          level: 1
          hypothesis: "…"
          children: []
    mece:
      - path: "A.tree.children"
        mutually_exclusive: pass | fail
        collectively_exhaustive: pass | fail
        note: "one line"

selected:
  breakdown_ids: []
  branch_ids: []
  parallel: false

unresolved:
  - observation: "…"
    reason: "…"
    clarification: "…"

applied:
  - name: principle-<name>
    at: status | root_question | breakdowns[<i>] | mece path | unresolved[<i>]
    changed: "The choice the principle changed, in one line"

stop: true
```

Always emit `root_question`, `main_question`, `smart_question`, `classification`, `breakdowns`, `selected`, `unresolved`, `applied`, and `stop`. Write `classification: null` when none was carried. On `blocked`, write `breakdowns: []`, empty `selected`, and one Unresolved row that asks for the main or SMART problem statement. On `structured` with empty `selected`, put exactly one selection ask in `unresolved` (ask slot). Its `clarification` is exactly: `Which breakdowns (and optional branch ids) do you want to work in parallel?` When the paste answers that ask, fill `selected.breakdown_ids` and optional `branch_ids`, set `parallel` true when more than one breakdown id or more than one branch id is chosen, and write `unresolved: []` for the ask. Keep MECE-cut rows if any breakdown is still `needs_split`.

`applied` lists only principles from the coordinator index that decided a value. Write `[]` when none did. Prefer citing `principle-dont-invent-problems` and `principle-dont-solve-yet` when they changed a node or blocked an answer.

## View

| Field | Label | When | Phrase |
|---|---|---|---|
| `root_question` | The question | not `blocked` | {root_question} |
| `root_question` | The question | `blocked` | There is no question to structure yet. |
| each breakdown | Breakdown {id}. {frame} | breakdown exists | indented list of `{node.id} {node.question}` through `depth_max_used` |
| failing `mece` note | MECE | any `fail` | Breakdown {id}, set {path}: {note} |
| `status` | Status | `structured` | Structured. Pick which breakdowns or branches to run in parallel. |
| `status` | Status | `needs_split` | Not MECE yet. One cut is still open. |
| `status` | Status | `blocked` | State the main or SMART problem first. |
| ask row `clarification` | no label | one open ask | {clarification} |

Lead with the question. Then each breakdown. Then any MECE fail lines. Then Status. Then, when there is one open ask, write that clarification as a bare line. Do not print `applied` or `stop` in the view.

## Output

In the default mode, write the title line `What's going on` as its own paragraph. Then write the two restatement sentences as one paragraph. Then write the view. Do not write a YAML fence.

In debug mode, write that same reply, then exactly one fenced `yaml` block of the Verdict, then nothing.

Use compact lists, never a table. Style each label as Present says. The ask line stays bare.

## Never

- Force depth to 3 when L1 or L2 is already MECE and testable.
- Overlap siblings or leave an uncovered path the paste still allows.
- Rank breakdowns, pick the work for the solver, or name a root cause as fact.
- Replace `main_question` wording, or root on a question the paste did not support.
- Invent a second breakdown that only renames the first.
- Recommend a fix, a plan, or a prioritized order.
- Run define-the-problem, prioritize-the-issues, or any later stage in the same reply.
- Write a YAML block outside debug.
- Write anything after the YAML block.
- Wrap the ask line in bold, quotes, or a bullet.
- Print `applied` or `stop` in the default view.
