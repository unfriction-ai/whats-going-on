"""Feed crafted stage-2 verdicts to the real parser and print what it returns."""

import copy
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from whats_going_on_eval.parse import parse_response  # noqa: E402
from whats_going_on_eval.structure import StructureResponse  # noqa: E402

BASE = yaml.safe_load(
    yaml.safe_load((ROOT / "schema_cases" / "valid-structure-structured.yaml").read_text())["body"]
)


def run(label, doc):
    text = "```yaml\n" + yaml.safe_dump(doc, sort_keys=False) + "```"
    parsed = parse_response(text)
    if isinstance(parsed, StructureResponse):
        print(f"{label}: ACCEPTED status={parsed.verdict.status}")
    else:
        print(f"{label}: REJECTED {parsed.kind} {parsed.detail}")


def node(nid, q, level, children=()):
    return {"id": nid, "question": q, "level": level, "hypothesis": q.rstrip("?") + ".", "children": list(children)}


def one_breakdown(children, mece, depth=1, status="mece_pass", root=None):
    doc = copy.deepcopy(BASE)
    root = root or doc["root_question"]
    doc["breakdowns"] = [
        {
            "id": "A",
            "frame": "probe",
            "depth_max_used": depth,
            "status": status,
            "tree": {"id": "root", "question": root, "level": 0, "children": children},
            "mece": mece,
        }
    ]
    doc["applied"] = []
    return doc


PASS = lambda path, note="pass": {  # noqa: E731
    "path": path, "mutually_exclusive": "pass", "collectively_exhaustive": "pass", "note": note,
}

probe = sys.argv[1] if len(sys.argv) > 1 else "none"

if probe == "meals":
    doc = one_breakdown(
        [
            node("A.1", "Is breakfast the problem?", 1),
            node("A.2", "Is lunch the problem?", 1),
            node("A.3", "Are meals the problem?", 1),
        ],
        [PASS("A.tree.children", "Breakfast, lunch, and meals do not overlap.")],
    )
    run("breakfast+lunch+meals marked mece_pass", doc)

elif probe == "traffic":
    doc = one_breakdown(
        [node("A.1", "Is the light green?", 1), node("A.2", "Is the light red?", 1)],
        [PASS("A.tree.children", "Green and red cover the light.")],
    )
    run("green+red (no yellow) marked mece_pass", doc)

elif probe == "no-notes":
    doc = one_breakdown(
        [node("A.1", "Is the pool rejecting?", 1), node("A.2", "Is upstream slow?", 1)],
        [],
    )
    run("mece_pass with zero mece notes", doc)

elif probe == "unchecked-l2":
    doc = one_breakdown(
        [
            node("A.1", "Is the pool rejecting?", 1, [
                node("A.1.1", "Is max too low?", 2),
                node("A.1.2", "Is max too low for peak?", 2),
            ]),
            node("A.2", "Is upstream slow?", 1),
        ],
        [PASS("A.tree.children")],
        depth=2,
    )
    run("L2 sibling set with no mece note", doc)

elif probe == "bogus-path":
    doc = one_breakdown(
        [node("A.1", "Is the pool rejecting?", 1), node("A.2", "Is upstream slow?", 1)],
        [PASS("Z.nowhere[9]")],
    )
    run("mece note path that resolves to nothing", doc)

elif probe == "single-child":
    doc = one_breakdown(
        [node("A.1", "Is something wrong with checkout?", 1)],
        [PASS("A.tree.children")],
    )
    run("one-child sibling set marked mece_pass", doc)

elif probe == "leaf-root":
    doc = one_breakdown([], [], depth=0)
    run("root with zero children, depth 0", doc)
    doc = one_breakdown([], [PASS("A.tree.children")], depth=1)
    run("root with zero children, depth 1", doc)

elif probe == "dup-ids":
    doc = one_breakdown(
        [node("A.1", "Is the pool rejecting?", 1), node("A.1", "Is upstream slow?", 1)],
        [PASS("A.tree.children")],
    )
    run("two sibling nodes share id A.1", doc)

elif probe == "needs-split-no-ask":
    doc = one_breakdown(
        [node("A.1", "Is the pool rejecting?", 1), node("A.2", "Is upstream slow?", 1)],
        [PASS("A.tree.children")],
        status="needs_split",
    )
    doc["status"] = "needs_split"
    doc["unresolved"] = []
    run("needs_split with all-pass notes and no unresolved row", doc)

elif probe == "needs-split-fail-no-cut":
    doc = one_breakdown(
        [node("A.1", "Is the pool rejecting?", 1), node("A.2", "Is upstream slow?", 1)],
        [
            {
                "path": "A.tree.children",
                "mutually_exclusive": "fail",
                "collectively_exhaustive": "pass",
                "note": "Overlap on the timeout path.",
            }
        ],
        status="needs_split",
    )
    doc["status"] = "needs_split"
    doc["unresolved"] = []
    run("needs_split with fail note but no cut ask", doc)

elif probe == "price-volume":
    doc = one_breakdown(
        [
            node("A.1", "Should we raise price?", 1),
            node("A.2", "Should we raise volume?", 1),
        ],
        [PASS("A.tree.children", "Price and volume cover revenue growth.")],
        root="How should we grow revenue next quarter?",
    )
    doc["root_question"] = "How should we grow revenue next quarter?"
    doc["main_question"] = "How should we grow revenue next quarter?"
    doc["smart_question"] = None
    doc["breakdowns"][0]["tree"]["question"] = doc["root_question"]
    run("grow-revenue CE pass on price|volume only", doc)

elif probe == "selected-ghost":
    doc = copy.deepcopy(BASE)
    doc["selected"] = {"breakdown_ids": ["Z"], "branch_ids": ["Q.9"], "parallel": False}
    doc["unresolved"] = []
    run("selected ids that name no breakdown or node", doc)

elif probe == "dup-frames":
    doc = copy.deepcopy(BASE)
    doc["breakdowns"][1] = copy.deepcopy(doc["breakdowns"][0])
    doc["breakdowns"][1]["frame"] = "By tier"
    run("second breakdown = first renamed, same id A", doc)

elif probe != "none":
    raise SystemExit(f"unknown probe {probe}")
