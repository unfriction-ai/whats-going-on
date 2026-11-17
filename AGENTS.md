# Agent rules (whats-going-on)

Mistake classes from MECE interrogate. Drop a row when the mistake can no longer compile past the wire.

| Rule | Enforcement |
| --- | --- |
| Every sibling set has a resolving `mece` note; bogus paths fail | `structure.py` → `mece_notes` (`invalid-structure-mece-missing-notes`, `bogus-path`, `unchecked-l2`) |
| `needs_split` needs ≥1 fail flag **and** unresolved clarification containing `cut` | `structure.py` → `mece_status` + `status_constraints` (`needs-split-no-fail-note`, `needs-split-no-cut-ask`) |
| Self-attested ME/CE on meal-part+meals or red+green (no yellow) fails | `structure.py` → `mece_anti_example` (`mece-meals-overlap`, `mece-traffic-incomplete`); also ≥2 children / unique ids |
| Grow-revenue CE cannot pass on price\|volume alone | `structure.py` → `mece_ce_scope` + `mece/SKILL.md` CE scope (`mece-price-volume-ce`) |

Prove: `python3 -m whats_going_on_eval check` and `python3 probes/probe_structure.py <probe>`.
