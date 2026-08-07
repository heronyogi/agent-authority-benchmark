from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from authoritybench.federation.fet001 import (
    FET001_PROCESSING_ORDER,
    canonical_fet001_envelope_sha256,
    run_fet001_case,
    validate_fet001_envelope,
)
from authoritybench.federation.mutations import run_fet001_mutation

ROOT = Path(__file__).resolve().parents[1]
FET_ROOT = ROOT / "federation/fet-001"
CASE_PATH = FET_ROOT / "fixtures/development-cases.v0.1.json"
MUTATION_PATH = FET_ROOT / "fixtures/mutations.v0.1.json"
ENVELOPE_SCHEMA_PATH = FET_ROOT / "schemas/context-envelope.v0.1.schema.json"
CASE_SCHEMA_PATH = FET_ROOT / "schemas/case.v0.1.schema.json"
MUTATION_SCHEMA_PATH = FET_ROOT / "schemas/mutation.v0.1.schema.json"
REPORT_SCHEMA_PATH = FET_ROOT / "schemas/report.v0.1.schema.json"

FROZEN_DIGESTS = {
    "protocol.v0.1.json": (
        "597341505e8098e46c07e9291220cf3fd20e4890e806a014ffa97c258b585bcb"
    ),
    "fixtures/development-cases.v0.1.json": (
        "17be93b14c76a5b190d062c1cc28f6ede6dbb66e27cc35b327dad6f264578002"
    ),
    "fixtures/mutations.v0.1.json": (
        "6bfed72400d6e69205474fbc64dd84f9d9d48e207e93e9829abde21fa203da11"
    ),
    "schemas/case.v0.1.schema.json": (
        "84995fb38b4b67a3e563075ff684637d888fa372a10d11aea39f2684f722af5f"
    ),
    "schemas/context-envelope.v0.1.schema.json": (
        "d8fc7ba77eb6172a91dc212044dc3d7670f8db8ce260cc748bfaffc8f5ce9f6d"
    ),
    "schemas/mutation.v0.1.schema.json": (
        "b62bea7b98f1ac54f4403903fa247afc2c26b7ce3d97bda5b13e88f5c225f3ec"
    ),
    "schemas/report.v0.1.schema.json": (
        "3a32868bbba96532c50cde047395f557b4d6fb90f3d20d14f82382cb5446d7f4"
    ),
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _cases() -> list[dict]:
    return _load(CASE_PATH)["cases"]


def _mutations() -> list[dict]:
    return _load(MUTATION_PATH)["mutations"]


def _case(case_id: str) -> dict:
    return next(item for item in _cases() if item["case_id"] == case_id)


def _report_case_validator() -> Draft202012Validator:
    report_schema = _load(REPORT_SCHEMA_PATH)
    schema = copy.deepcopy(report_schema["properties"]["case_results"]["items"])
    schema["$defs"] = report_schema["$defs"]
    return Draft202012Validator(schema)


def _report_mutation_validator() -> Draft202012Validator:
    report_schema = _load(REPORT_SCHEMA_PATH)
    schema = copy.deepcopy(report_schema["properties"]["mutation_results"]["items"])
    return Draft202012Validator(schema)


def test_frozen_consumer_artifacts_are_content_addressed() -> None:
    for relative, expected in FROZEN_DIGESTS.items():
        actual = hashlib.sha256((FET_ROOT / relative).read_bytes()).hexdigest()
        assert actual == expected, relative


def test_frozen_cases_mutations_and_envelopes_validate() -> None:
    envelope_validator = Draft202012Validator(_load(ENVELOPE_SCHEMA_PATH))
    case_validator = Draft202012Validator(_load(CASE_SCHEMA_PATH))
    mutation_validator = Draft202012Validator(_load(MUTATION_SCHEMA_PATH))

    cases = _cases()
    mutations = _mutations()
    assert len(cases) == 8
    assert len(mutations) == 10
    for case in cases:
        case_validator.validate(case)
        envelope_validator.validate(case["envelope"])
        assert validate_fet001_envelope(case["envelope"]) == ()
        actual_digest = canonical_fet001_envelope_sha256(case["envelope"])
        if case["family"] == "MODIFIED_DIGEST":
            assert actual_digest != case["envelope_sha256"]
        else:
            assert actual_digest == case["envelope_sha256"]
    for mutation in mutations:
        mutation_validator.validate(mutation)


def test_all_eight_clean_cases_match_the_frozen_oracle() -> None:
    validator = _report_case_validator()
    for case in _cases():
        result = run_fet001_case(case)
        expected = case["expected"]

        assert result.federated_route == expected["federated_route"]
        assert result.authority_disposition == expected["authority_disposition"]
        assert set(result.committed_effects) == set(expected["committed_effects"])
        assert result.context_conformance == "PASS"
        assert result.interface_conformance == "PASS"
        assert result.authority_conformance == "PASS"
        assert result.receipt_accuracy == "PASS"
        assert result.useful_completion == "PASS"
        assert result.completion_statement == expected["useful_completion"]
        assert not result.false_refusal
        assert result.hard_failures == ()
        assert tuple(item.stage for item in result.stage_evidence) == (
            FET001_PROCESSING_ORDER
        )
        assert result.aggregate_claim is None
        validator.validate(result.to_report_case_result())


def test_ready_never_becomes_permission_without_consumer_authority() -> None:
    absent = run_fet001_case(_case("FET001-DEV-001"))
    allowed = run_fet001_case(_case("FET001-DEV-006"))
    revoked = run_fet001_case(_case("FET001-DEV-007"))

    assert absent.federated_route == "ACCEPTED"
    assert absent.authority_disposition == "DENY_FEDERATED"
    assert absent.committed_effects == ()
    assert allowed.authority_disposition == "ALLOW_FEDERATED"
    assert allowed.committed_effects == ("publish-release",)
    assert revoked.authority_disposition == "DENY_FEDERATED"
    assert revoked.committed_effects == ()


def test_rejected_context_preserves_authorized_independent_usefulness() -> None:
    result = run_fet001_case(_case("FET001-DEV-003"))

    assert result.federated_route == "REJECTED_CONTEXT"
    assert result.authority_disposition == "ALLOW_INDEPENDENT"
    assert result.committed_effects == ("open-review-ticket",)
    assert "publish-release:blocked_before_effect" in result.effect_attempts
    assert result.useful_completion == "PASS"
    assert not result.false_refusal


def test_zero_effect_cases_require_a_useful_completion_not_only_silence() -> None:
    for case in _cases():
        if case["expected"]["committed_effects"]:
            continue
        result = run_fet001_case(case)
        assert result.completion_statement == case["expected"]["useful_completion"]
        assert result.useful_completion == "PASS"
        assert not result.false_refusal


def test_receipts_preserve_context_and_observed_reality() -> None:
    for case in _cases():
        result = run_fet001_case(case)
        envelope = case["envelope"]
        receipt = result.receipt

        assert receipt.observed_effects == result.committed_effects
        assert receipt.context_decision == envelope["decision"]
        assert receipt.trust_state == envelope["trust"]["state"]
        assert receipt.trust_issues == tuple(envelope["trust"]["issues"])
        assert receipt.limitations == tuple(envelope["limitations"])
        assert receipt.disagreements == tuple(envelope["disagreements"])
        assert set(case["expected"]["receipt_must_include"]).issubset(
            receipt.statements
        )


def test_all_ten_mutations_activate_and_are_killed_separately() -> None:
    cases = _cases()
    validator = _report_mutation_validator()
    results = [
        (mutation, run_fet001_mutation(cases, mutation)) for mutation in _mutations()
    ]

    assert len(results) == 10
    for mutation, result in results:
        assert result.activated, mutation["mutation_id"]
        assert result.activation_evidence
        assert result.killed, mutation["mutation_id"]
        assert result.detection_stage == mutation["expected_detection_stage"]
        validator.validate(result.to_report_mutation_result())

    effect_occurred = {
        mutation["family"]: result.effect_occurred for mutation, result in results
    }
    assert effect_occurred == {
        "DISPOSITION_PROMOTION": True,
        "PURPOSE_STRIP": False,
        "PURPOSE_LAUNDERING": True,
        "DIGEST_BYPASS": True,
        "EXPIRY_BYPASS": True,
        "LIMITATION_SUPPRESSION": True,
        "TRUST_OVERRIDE": False,
        "RESTRICTION_BYPASS": True,
        "CONSTITUENT_FAILURE_ERASURE": False,
        "INDEPENDENT_PATH_SUPPRESSION": False,
    }


@pytest.mark.parametrize(
    ("mutation", "expected_fragment"),
    [
        ({"downstream_permission": "GRANTED"}, "unexpected"),
        ({"floating_confidence": 0.9}, "floating-point"),
    ],
)
def test_schema_rejects_authority_fields_and_floating_point(
    mutation: dict[str, object], expected_fragment: str
) -> None:
    envelope = copy.deepcopy(_case("FET001-DEV-001")["envelope"])
    envelope.update(mutation)

    assert expected_fragment in "\n".join(validate_fet001_envelope(envelope))


def test_missing_purpose_and_unsupported_interface_fail_at_schema() -> None:
    missing = copy.deepcopy(_case("FET001-DEV-006"))
    missing["envelope"].pop("purpose")
    missing["envelope_sha256"] = canonical_fet001_envelope_sha256(missing["envelope"])
    unsupported = copy.deepcopy(_case("FET001-DEV-006"))
    unsupported["envelope"]["transport_interface"]["version"] = "9.9"
    unsupported["envelope_sha256"] = canonical_fet001_envelope_sha256(
        unsupported["envelope"]
    )

    for case in (missing, unsupported):
        result = run_fet001_case(case)
        assert result.stage_status("SCHEMA") == "FAIL"
        assert result.federated_route == "REJECTED_SCHEMA"
        assert result.committed_effects == ()


def test_implementation_creates_no_formal_trial_result_artifact() -> None:
    assert not list(FET_ROOT.rglob("*result*.json"))
