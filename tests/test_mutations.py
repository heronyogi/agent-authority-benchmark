from __future__ import annotations

from authoritybench.harness import run_mutation


def _report_for(
    kind: str,
    cases_by_id: dict[str, dict],
    mutations: list[dict],
) -> dict:
    mutation = next(item for item in mutations if item["kind"] == kind)
    return run_mutation(cases_by_id[mutation["target_case"]], mutation)


def test_all_mutations_are_active_and_killed(
    cases_by_id: dict[str, dict], mutations: list[dict]
) -> None:
    for mutation in mutations:
        report = run_mutation(cases_by_id[mutation["target_case"]], mutation)
        result = report["mutation_kill"]
        assert result["activated"], mutation["mutation_id"]
        assert result["detected"], mutation["mutation_id"]
        assert result["killed"], mutation["mutation_id"]
        assert result["detection_phase"] == mutation["expected_detection_phase"]


def test_after_effect_detection_is_still_a_safety_failure(
    cases_by_id: dict[str, dict], mutations: list[dict]
) -> None:
    for kind in {
        "PERMISSION_BYPASS",
        "PURPOSE_LAUNDERING",
        "STALE_PERMISSION",
        "FALSE_RECEIPT",
        "UNAUTHORIZED_REOPEN",
        "EMERGENCY_BYPASS",
        "PROSE_TOOL_MISMATCH",
    }:
        report = _report_for(kind, cases_by_id, mutations)
        assert report["mutation_kill"]["detection_phase"] == "after_effect"
        assert report["behavioral_conformance"]["safety"] == "fail"


def test_late_guard_prevents_commit(
    cases_by_id: dict[str, dict], mutations: list[dict]
) -> None:
    report = _report_for("LATE_GUARD", cases_by_id, mutations)
    assert report["behavioral_conformance"]["safety"] == "pass"
    assert any(
        outcome.endswith(":ATTEMPTED_PREVENTED")
        for outcome in report["side_effect_evidence"]["outcomes"]
    )


def test_observer_gap_remains_unknown(
    cases_by_id: dict[str, dict], mutations: list[dict]
) -> None:
    report = _report_for("OBSERVER_GAP", cases_by_id, mutations)
    behavior = report["behavioral_conformance"]
    assert behavior["safety"] == "unknown"
    assert behavior["observability"] == "unknown"
    assert report["mutation_kill"]["detection_phase"] == "unknown"


def test_false_refusal_does_not_masquerade_as_success(
    cases_by_id: dict[str, dict], mutations: list[dict]
) -> None:
    report = _report_for("EXCESSIVE_FAIL_CLOSED", cases_by_id, mutations)
    behavior = report["behavioral_conformance"]
    assert behavior["safety"] == "pass"
    assert not behavior["useful_completion"]
    assert behavior["false_refusal_count"] == 1


def test_propagation_and_receipt_mutations_hit_distinct_oracles(
    cases_by_id: dict[str, dict], mutations: list[dict]
) -> None:
    propagation = _report_for("PROPAGATION_DROP", cases_by_id, mutations)
    receipt = _report_for("FALSE_RECEIPT", cases_by_id, mutations)
    assert not propagation["behavioral_conformance"]["propagation_complete"]
    assert not receipt["behavioral_conformance"]["receipt_accuracy"]
