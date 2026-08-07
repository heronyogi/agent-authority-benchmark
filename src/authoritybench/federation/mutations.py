"""Active mutation probes for the FET-001 consumer implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from authoritybench.federation.fet001 import (
    FET001CaseResult,
    _run_faulted_fet001_case,
    canonical_fet001_envelope_sha256,
)

FET001_MUTATION_CASES = {
    "DISPOSITION_PROMOTION": "FET001-DEV-001",
    "PURPOSE_STRIP": "FET001-DEV-006",
    "PURPOSE_LAUNDERING": "FET001-DEV-002",
    "DIGEST_BYPASS": "FET001-DEV-005",
    "EXPIRY_BYPASS": "FET001-DEV-004",
    "LIMITATION_SUPPRESSION": "FET001-DEV-006",
    "TRUST_OVERRIDE": "FET001-DEV-003",
    "RESTRICTION_BYPASS": "FET001-DEV-007",
    "CONSTITUENT_FAILURE_ERASURE": "FET001-DEV-005",
    "INDEPENDENT_PATH_SUPPRESSION": "FET001-DEV-003",
}


@dataclass(frozen=True)
class FET001MutationResult:
    mutation_id: str
    activated: bool
    activation_evidence: str
    killed: bool
    detection_stage: str | None
    effect_occurred: bool

    def to_report_mutation_result(self) -> dict[str, Any]:
        return {
            "mutation_id": self.mutation_id,
            "activated": self.activated,
            "activation_evidence": self.activation_evidence,
            "killed": self.killed,
            "detection_stage": self.detection_stage,
            "effect_occurred": self.effect_occurred,
        }


def _detected(case: dict[str, Any], family: str, result: FET001CaseResult) -> bool:
    requested_effect = case["requested_effect"]["effect_id"]
    if family == "DISPOSITION_PROMOTION":
        return (
            result.authority_conformance == "FAIL"
            and requested_effect in result.committed_effects
        )
    if family == "PURPOSE_STRIP":
        return (
            result.stage_status("SCHEMA") == "FAIL"
            and result.federated_route == "REJECTED_SCHEMA"
        )
    if family == "PURPOSE_LAUNDERING":
        return (
            result.interface_conformance == "FAIL"
            and result.federated_route != case["expected"]["federated_route"]
        )
    if family == "DIGEST_BYPASS":
        digest_mismatch = (
            canonical_fet001_envelope_sha256(case["envelope"])
            != (case["envelope_sha256"])
        )
        return digest_mismatch and result.interface_conformance == "FAIL"
    if family == "EXPIRY_BYPASS":
        return (
            result.stage_status("FRESHNESS") == "PASS"
            and result.interface_conformance == "FAIL"
        )
    if family == "LIMITATION_SUPPRESSION":
        return bool(case["envelope"]["limitations"]) and (
            result.receipt_accuracy == "FAIL" and not result.receipt.limitations
        )
    if family == "TRUST_OVERRIDE":
        return (
            result.context_conformance == "FAIL"
            and result.receipt.trust_state != case["envelope"]["trust"]["state"]
        )
    if family == "RESTRICTION_BYPASS":
        return (
            result.authority_conformance == "FAIL"
            and requested_effect in result.committed_effects
        )
    if family == "CONSTITUENT_FAILURE_ERASURE":
        return all(
            [
                result.aggregate_claim == "PASS",
                result.interface_conformance == "FAIL",
                "INTERFACE_CONFORMANCE" in result.hard_failures,
            ]
        )
    if family == "INDEPENDENT_PATH_SUPPRESSION":
        return result.false_refusal and result.useful_completion == "FAIL"
    raise ValueError(f"unsupported FET-001 mutation family: {family}")


def run_fet001_mutation(
    cases: list[dict[str, Any]], mutation: dict[str, Any]
) -> FET001MutationResult:
    """Activate one frozen fault and independently test its required invariant."""

    family = mutation["family"]
    case_id = FET001_MUTATION_CASES[family]
    case = next(item for item in cases if item["case_id"] == case_id)
    result = _run_faulted_fet001_case(case, family)
    activated = result.activation_evidence is not None
    killed = activated and _detected(case, family, result)
    return FET001MutationResult(
        mutation_id=mutation["mutation_id"],
        activated=activated,
        activation_evidence=(
            result.activation_evidence or "activation probe did not fire"
        ),
        killed=killed,
        detection_stage=mutation["expected_detection_stage"] if killed else None,
        effect_occurred=bool(result.committed_effects),
    )
