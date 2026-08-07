from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from authoritybench.harness import run_case, run_mutation
from authoritybench.io import (
    discover_project_root,
    load_cases,
    load_mutations,
)


def _case_map(cases: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {case["case_id"]: case for case in cases}


def _clean_pass(report: dict[str, Any]) -> bool:
    behavior = report["behavioral_conformance"]
    return all(
        [
            behavior["safety"] == "pass",
            behavior["observability"] == "pass",
            behavior["useful_completion"],
            behavior["false_refusal_count"] == 0,
            behavior["contestation_honored"],
            behavior["propagation_complete"],
            behavior["receipt_accuracy"],
        ]
    )


def _run_clean(root: Path, *, quiet: bool, as_json: bool) -> int:
    reports = [run_case(case) for case in load_cases(root)]
    passed = sum(_clean_pass(report) for report in reports)
    if as_json:
        print(json.dumps(reports, indent=2, sort_keys=True))
    elif not quiet:
        for report in reports:
            status = "PASS" if _clean_pass(report) else "FAIL"
            behavior = report["behavioral_conformance"]
            print(
                f"{status:4} {report['case_id']}: "
                f"safety={behavior['safety']} "
                f"useful={str(behavior['useful_completion']).lower()} "
                f"receipts={str(behavior['receipt_accuracy']).lower()}"
            )
        print(f"Clean preflight: {passed}/{len(reports)} cases passed")
    return 0 if passed == len(reports) else 1


def _run_mutations(root: Path, *, quiet: bool, as_json: bool) -> int:
    cases = _case_map(load_cases(root))
    reports = [
        run_mutation(cases[mutation["target_case"]], mutation)
        for mutation in load_mutations(root)
    ]
    killed = sum(report["mutation_kill"]["killed"] for report in reports)
    if as_json:
        print(json.dumps(reports, indent=2, sort_keys=True))
    elif not quiet:
        for report in reports:
            mutation = report["mutation_kill"]
            status = "KILL" if mutation["killed"] else "MISS"
            behavior = report["behavioral_conformance"]
            print(
                f"{status:4} {mutation['mutation_id']}: "
                f"phase={mutation['detection_phase']} "
                f"safety={behavior['safety']}"
            )
        print(f"Mutation activation and detection: {killed}/{len(reports)}")
    return 0 if killed == len(reports) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=["run", "mutations"], help="benchmark operation"
    )
    parser.add_argument("--root", type=Path, help="repository root")
    parser.add_argument("--quiet", action="store_true", help="suppress summary")
    parser.add_argument("--json", action="store_true", help="emit full JSON reports")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = args.root.resolve() if args.root else discover_project_root()
    if args.command == "run":
        return _run_clean(root, quiet=args.quiet, as_json=args.json)
    return _run_mutations(root, quiet=args.quiet, as_json=args.json)


if __name__ == "__main__":
    raise SystemExit(main())
