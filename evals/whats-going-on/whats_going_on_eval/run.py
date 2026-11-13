from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import yaml

from .agents import (
    HostInvokeError,
    HostNotWired,
    build_prompt,
    host_load_problems,
    invoke,
    materialize_skill,
    nested_leaf_rels,
)
from .chain import load_chain
from .drift import check_suite
from .fixtures import load_suite
from .grade import FixtureRunResult, grade_run, summarize
from .invariance import InvarianceError, compare, invariance_payload, preamble_outcome_problems
from .manifest import (
    AGENTS,
    EVAL_DIR,
    FIXTURES_DIR,
    REPORTS_DIR,
    REPO_ROOT,
    RUBRIC_PATH,
    SCHEMA_CASES_DIR,
    SKILL_DIR,
    agent_mount,
    read_mount,
    skill_view_hash,
)
from .parse import Halt, Response, parse_response
from .runs import new_run_id, write_blind_compare, write_manifest, write_report, write_transcript


def cmd_check() -> int:
    fixtures = load_suite(FIXTURES_DIR)
    readme = (SKILL_DIR / "README.md").read_text()
    rubric_md = RUBRIC_PATH.read_text()
    problems = check_suite(
        fixtures,
        readme=readme,
        mode=load_chain(SKILL_DIR).mode,
        mount=read_mount(SKILL_DIR),
        rubric_md=rubric_md,
    )
    schema_problems = _check_schema_cases()
    problems_text = [f"{p.kind}: {p.detail}" for p in problems] + schema_problems
    problems_text.extend(preamble_outcome_problems())
    problems_text.extend(host_load_problems(SKILL_DIR, REPO_ROOT))

    if problems_text:
        print("check FAILED")
        for line in problems_text:
            print(f"  {line}")
        return 2

    families = sorted({fam for f in fixtures for fam in f.families})
    leaves = nested_leaf_rels(agent_mount(SKILL_DIR))
    print("check OK")
    print(f"  fixtures: {len(fixtures)}  skill_view: {skill_view_hash(SKILL_DIR)}")
    print(f"  families: {', '.join(families)}")
    print(f"  schema_cases: {_schema_case_count()} ok")
    print(f"  nested_leaves: {', '.join(Path(rel).parent.as_posix() for rel in leaves)}")
    return 0


def _schema_case_count() -> int:
    return len(list(SCHEMA_CASES_DIR.glob("*.yaml"))) + len(
        list(SCHEMA_CASES_DIR.glob("*.yml"))
    )


def _check_schema_cases() -> list[str]:
    if not SCHEMA_CASES_DIR.exists():
        return ["schema_cases: directory missing"]
    problems: list[str] = []
    for path in sorted(SCHEMA_CASES_DIR.glob("*.yaml")) + sorted(
        SCHEMA_CASES_DIR.glob("*.yml")
    ):
        doc = yaml.safe_load(path.read_text())
        if not isinstance(doc, dict) or "body" not in doc or "expect_ok" not in doc:
            problems.append(f"schema_cases/{path.name}: need expect_ok and body")
            continue
        text = doc["body"]
        if "```" not in str(text):
            text = f"```yaml\n{text}\n```"
        parsed = parse_response(str(text))
        want_halt = doc.get("wire") == "halt"
        if want_halt:
            ok = isinstance(parsed, Halt)
        else:
            ok = isinstance(parsed, Response)
        if bool(doc["expect_ok"]) != ok:
            if isinstance(parsed, Response):
                detail = "parsed_response"
            elif isinstance(parsed, Halt):
                detail = "parsed_halt"
            else:
                detail = parsed.kind
            problems.append(
                f"schema_cases/{path.name}: expect_ok={doc['expect_ok']} got {detail}"
            )
        elif ok and want_halt and "next_stage" in doc:
            assert isinstance(parsed, Halt)
            if parsed.next_stage != doc["next_stage"]:
                problems.append(
                    f"schema_cases/{path.name}: next_stage want {doc['next_stage']} got {parsed.next_stage}"
                )
        elif ok and "derived_status" in doc:
            assert isinstance(parsed, Response)
            if parsed.verdict.status != doc["derived_status"]:
                problems.append(
                    f"schema_cases/{path.name}: derived_status want {doc['derived_status']} got {parsed.verdict.status}"
                )
    if _schema_case_count() < 8:
        problems.append(
            f"schema_cases: need at least 8 cases (got {_schema_case_count()}); one valid and one invalid per status"
        )
    return problems


def cmd_run(args: argparse.Namespace) -> int:
    check_code = cmd_check()
    if check_code != 0:
        return check_code

    fixtures = load_suite(FIXTURES_DIR)
    if args.only:
        wanted = {x.strip() for x in args.only.split(",") if x.strip()}
        fixtures = [f for f in fixtures if f.id in wanted]
        if not fixtures:
            print(f"no fixtures matched --only {args.only}", file=sys.stderr)
            return 2

    if args.skill == "none":
        skill_src = None
    elif args.skill:
        skill_src = Path(args.skill)
    else:
        skill_src = SKILL_DIR

    run_id = args.resume or new_run_id(args.agent, skill_src)
    write_manifest(
        run_id,
        {
            "agent": args.agent,
            "repeat": args.repeat,
            "only": args.only,
            "judge": bool(args.judge),
            "skill": str(skill_src) if skill_src else "none",
        },
        skill_src,
    )

    results: list[FixtureRunResult] = []
    fixtures_by_id = {f.id: f for f in fixtures}

    try:
        for fixture in fixtures:
            for rep in range(1, args.repeat + 1):
                responses: list[str] = []
                workspace = materialize_skill(skill_src)
                try:
                    for turn_i, turn in enumerate(fixture.turns):
                        result = invoke(
                            agent=args.agent,
                            user_input=turn.input,
                            skill_src=skill_src,
                            session_workspace=workspace,
                        )
                        write_transcript(
                            run_id,
                            fixture.id,
                            rep,
                            turn_i,
                            prompt=build_prompt(turn.input),
                            response=result.text,
                        )
                        responses.append(result.text)
                finally:
                    shutil.rmtree(workspace, ignore_errors=True)
                results.append(grade_run(fixture, rep, responses))
    except HostNotWired as exc:
        print(str(exc), file=sys.stderr)
        print(
            "Tip: `python -m whats_going_on_eval check` and schema grading work without a host.",
            file=sys.stderr,
        )
        return 2
    except HostInvokeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    report = summarize(results, fixtures_by_id)
    write_report(
        run_id,
        {
            "run_id": run_id,
            "passed": report.passed,
            "hard_fail_count": report.hard_fail_count,
            "abstention_precision": report.abstention_precision,
            "mean_all": report.mean_all,
            "mean_seed": report.mean_seed,
            "mean_holdout": report.mean_holdout,
            "by_axis": report.by_axis,
            "by_family": report.by_family,
            "restatement_disagreement_rate": report.restatement_disagreement_rate,
        },
    )
    _print_report(run_id, report)
    return 0 if report.passed else 1


def cmd_grade(run_id: str) -> int:
    from .runs import run_dir

    fixtures = {f.id: f for f in load_suite(FIXTURES_DIR)}
    tdir = run_dir(run_id) / "transcripts"
    if not tdir.exists():
        print(f"no transcripts for {run_id}", file=sys.stderr)
        return 2

    grouped: dict[tuple[str, int], dict[int, str]] = {}
    for path in sorted(tdir.glob("*.json")):
        data = json.loads(path.read_text())
        key = (data["fixture_id"], int(data["repetition"]))
        grouped.setdefault(key, {})[int(data["turn"])] = data["response"]

    results: list[FixtureRunResult] = []
    for (fixture_id, rep), turns in sorted(grouped.items()):
        fixture = fixtures[fixture_id]
        responses = [turns[i] for i in range(len(fixture.turns))]
        results.append(grade_run(fixture, rep, responses))

    report = summarize(results, fixtures)
    write_report(
        run_id,
        {
            "run_id": run_id,
            "passed": report.passed,
            "hard_fail_count": report.hard_fail_count,
            "abstention_precision": report.abstention_precision,
            "mean_all": report.mean_all,
            "mean_seed": report.mean_seed,
            "mean_holdout": report.mean_holdout,
            "by_axis": report.by_axis,
            "by_family": report.by_family,
            "restatement_disagreement_rate": report.restatement_disagreement_rate,
            "regraded": True,
        },
    )
    _print_report(run_id, report)
    return 0 if report.passed else 1


def cmd_invariance(base: str, treat: str, noise: str | None) -> int:
    try:
        report = compare(base, treat, noise)
    except InvarianceError as exc:
        print(str(exc), file=sys.stderr)
        print(
            "invariance reads stored transcripts only. A live A/B needs a wired host.",
            file=sys.stderr,
        )
        return 2
    out = REPORTS_DIR / treat / "invariance.json"
    out.write_text(json.dumps(invariance_payload(report), indent=2) + "\n")
    status = "PASS" if report.passed else "FAIL"
    noise_text = "na" if report.disagreement_noise is None else f"{report.disagreement_noise:.2f}"
    print(
        f"invariance {status}  turns={report.turns}  "
        f"modal_mismatches={len(report.modal_mismatches)}  "
        f"contract_fail_base={report.contract_fail_base}  "
        f"contract_fail_treat={report.contract_fail_treat}  "
        f"disagreement={report.disagreement_treat:.2f}  noise={noise_text}"
    )
    print(f"wrote {out}")
    return 0 if report.passed else 1


def cmd_compare(run_a: str, run_b: str, *, blind: bool) -> int:
    if not blind:
        print("compare currently supports --blind only", file=sys.stderr)
        return 2
    path = write_blind_compare(run_a, run_b)
    print(f"wrote {path}")
    print("Hand this packet to /poteto-mode eval without revealing which run is which.")
    return 0


def _print_report(run_id: str, report) -> None:
    status = "PASS" if report.passed else "FAIL"
    print(
        f"run {run_id}  {status}  hard_fails={report.hard_fail_count}  "
        f"abstention_precision={report.abstention_precision:.2f}  "
        f"mean={report.mean_all:.2f} (seed {report.mean_seed:.2f}, holdout {report.mean_holdout:.2f})"
    )
    axis = "  ".join(
        f"{k}={v:.2f}" if v is not None else f"{k}=na" for k, v in report.by_axis.items()
    )
    print(f"axis  {axis}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="whats_going_on_eval",
        description="Executable evals for the whats-going-on skill",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser(
        "check",
        help="Drift, gold self-test, schema_cases, nested-leaf load (no agent)",
    )

    run_p = sub.add_parser("run", help="Invoke an agent host and grade")
    run_p.add_argument("--agent", choices=AGENTS, default="cursor")
    run_p.add_argument("--only", default="", help="Comma-separated fixture ids")
    run_p.add_argument("--repeat", type=int, default=1)
    run_p.add_argument("--judge", action="store_true")
    run_p.add_argument(
        "--skill",
        default="",
        help="Skill directory, or 'none' for no-skill baseline",
    )
    run_p.add_argument("--resume", default="", help="Resume an existing run id")

    grade_p = sub.add_parser("grade", help="Re-score a run from transcripts")
    grade_p.add_argument("run_id")

    inv_p = sub.add_parser(
        "invariance",
        help="Compare stored runs. Does not invoke a host.",
    )
    inv_p.add_argument("base")
    inv_p.add_argument("treat")
    inv_p.add_argument("--noise", default="", help="Second baseline run, for the noise floor")

    compare_p = sub.add_parser("compare", help="Blind A/B packet for poteto-mode eval")
    compare_p.add_argument("run_a")
    compare_p.add_argument("run_b")
    compare_p.add_argument("--blind", action="store_true", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    eval_root = str(EVAL_DIR)
    if eval_root not in sys.path:
        sys.path.insert(0, eval_root)

    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "check":
        return cmd_check()
    if args.cmd == "run":
        return cmd_run(args)
    if args.cmd == "grade":
        return cmd_grade(args.run_id)
    if args.cmd == "invariance":
        return cmd_invariance(args.base, args.treat, args.noise or None)
    if args.cmd == "compare":
        return cmd_compare(args.run_a, args.run_b, blind=args.blind)
    parser.error(f"unknown command {args.cmd}")
    return 2
