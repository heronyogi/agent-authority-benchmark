import copy

import pytest
from test_fet001_consumer import _case, _report_case_validator

from authoritybench.federation.fet001 import run_fet001_case, validate_fet001_envelope
from authoritybench.harness import run_case, run_mutation


def test_incomplete_scope_cannot_report_observed_safety_pass(cases: list[dict]) -> None:
    for original in cases:
        case = copy.deepcopy(original)
        case["observation_scope"]["complete"] = False
        report = run_case(case)
        assert report["behavioral_conformance"]["observability"] == "unknown"
        assert report["behavioral_conformance"]["safety"] == "unknown"
        assert "confirmed observation scope" not in report["bounded_claim"]


def test_known_violation_stays_failure_with_incomplete_scope(
    cases_by_id: dict[str, dict], mutations: list[dict]
) -> None:
    mutation = next(item for item in mutations if item["kind"] == "PERMISSION_BYPASS")
    case = copy.deepcopy(cases_by_id[mutation["target_case"]])
    case["observation_scope"]["complete"] = False
    report = run_mutation(case, mutation)
    assert report["behavioral_conformance"]["observability"] == "unknown"
    assert report["behavioral_conformance"]["safety"] == "fail"


@pytest.mark.parametrize("field", list(_case("FET001-DEV-001")["envelope"]))
def test_every_missing_envelope_member_retains_schema_rejection(field: str) -> None:
    case = _case("FET001-DEV-001")
    del case["envelope"][field]
    assert validate_fet001_envelope(case["envelope"])
    result = run_fet001_case(case)
    assert result.federated_route == "REJECTED_SCHEMA"
    assert result.stage_status("CONTEXT") == "NOT_EVALUATED"
    assert result.committed_effects == ()
    assert "Schema rejected" in result.receipt.statements
    _report_case_validator().validate(result.to_report_case_result())
    if field == "decision":
        assert result.receipt.context_decision is None
    if field == "trust":
        assert result.receipt.trust_state is None


@pytest.mark.parametrize("value", [None, [], 4, "invalid", {"state": []}])
@pytest.mark.parametrize("field", ["decision", "trust", "limitations", "disagreements"])
def test_malformed_receipt_metadata_does_not_break_rejection(
    field: str, value: object
) -> None:
    case = _case("FET001-DEV-001")
    case["envelope"][field] = value
    if not validate_fet001_envelope(case["envelope"]):
        return  # Empty disagreements is valid; its positive case is frozen separately.
    result = run_fet001_case(case)
    assert result.federated_route == "REJECTED_SCHEMA"
    assert result.committed_effects == ()
    _report_case_validator().validate(result.to_report_case_result())


@pytest.mark.parametrize("value", [None, [], 4, "invalid"])
def test_non_object_envelope_returns_inspectable_rejection(value: object) -> None:
    case = _case("FET001-DEV-001")
    case["envelope"] = value
    result = run_fet001_case(case)
    assert result.federated_route == "REJECTED_SCHEMA"
    assert result.receipt.context_decision is None
    assert result.receipt.trust_issues is None
    assert result.committed_effects == ()


@pytest.mark.parametrize("field", ["created_at", "expires_at"])
def test_impossible_calendar_timestamp_rejects_before_freshness(field: str) -> None:
    case = _case("FET001-DEV-001")
    case["envelope"][field] = "2026-02-30T00:00:00Z"
    result = run_fet001_case(case)
    assert result.federated_route == "REJECTED_SCHEMA"
    assert result.stage_status("FRESHNESS") == "NOT_EVALUATED"


def test_schema_rejection_keeps_separately_authorized_independent_path() -> None:
    case = _case("FET001-DEV-003")
    del case["envelope"]["decision"]
    result = run_fet001_case(case)
    assert result.federated_route == "REJECTED_SCHEMA"
    assert result.authority_disposition == "ALLOW_INDEPENDENT"
    assert result.committed_effects == ("open-review-ticket",)
    assert result.receipt.context_decision is None
