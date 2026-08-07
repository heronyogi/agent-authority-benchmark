from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from authoritybench.harness import run_case
from authoritybench.result import build_reference_result


def _clean_pass(report: dict) -> bool:
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


def test_all_clean_cases_pass_and_reports_validate(
    project_root: Path, cases: list[dict]
) -> None:
    schema = json.loads(
        (project_root / "schemas" / "report.schema.json").read_text(encoding="utf-8")
    )
    validator = jsonschema.Draft202012Validator(schema)

    for case in cases:
        report = run_case(case)
        validator.validate(report)
        assert _clean_pass(report), case["case_id"]


def test_restricted_cases_preserve_usefulness_without_side_effect_overreach(
    cases: list[dict],
) -> None:
    for case in cases:
        if case["variant"] != "restricted":
            continue
        report = run_case(case)
        behavior = report["behavioral_conformance"]
        assert behavior["useful_completion"]
        assert behavior["safety"] == "pass"
        observed_ids = {
            effect["effect_id"]
            for effect in report["side_effect_evidence"]["observed_effects"]
        }
        unauthorized_ids = {
            effect["effect_id"]
            for effect in case["candidate_effects"]
            if effect["consequential"] and not effect["useful"]
        }
        assert observed_ids.isdisjoint(unauthorized_ids)


def test_authorized_positive_controls_act(cases: list[dict]) -> None:
    for case in cases:
        if case["variant"] != "authorized_positive":
            continue
        report = run_case(case)
        observed_ids = {
            effect["effect_id"]
            for effect in report["side_effect_evidence"]["observed_effects"]
        }
        assert set(case["required_useful_effect_ids"]) <= observed_ids
        assert report["behavioral_conformance"]["false_refusal_count"] == 0


def test_reports_are_deterministic(cases: list[dict]) -> None:
    for case in cases:
        assert run_case(case) == run_case(case)


def test_reference_result_is_current_and_valid(project_root: Path) -> None:
    existing = json.loads(
        (project_root / "docs" / "reference-result.v0.1.json").read_text(
            encoding="utf-8"
        )
    )
    schema = json.loads(
        (project_root / "schemas" / "reference-result.schema.json").read_text(
            encoding="utf-8"
        )
    )
    jsonschema.Draft202012Validator(schema).validate(existing)
    assert existing == build_reference_result(project_root)
