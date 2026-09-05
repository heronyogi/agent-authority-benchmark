"""Deterministic consumer for the frozen FET-001 Context envelope."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

FET001_PROCESSING_ORDER = (
    "SCHEMA",
    "INTEGRITY",
    "FRESHNESS",
    "SCOPE",
    "CONTEXT",
    "AUTHORITY",
    "EFFECT",
    "RECEIPT",
)
FET001_MUTATION_FAMILIES = frozenset(
    {
        "DISPOSITION_PROMOTION",
        "PURPOSE_STRIP",
        "PURPOSE_LAUNDERING",
        "DIGEST_BYPASS",
        "EXPIRY_BYPASS",
        "LIMITATION_SUPPRESSION",
        "TRUST_OVERRIDE",
        "RESTRICTION_BYPASS",
        "CONSTITUENT_FAILURE_ERASURE",
        "INDEPENDENT_PATH_SUPPRESSION",
    }
)

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SYNTHETIC_REF = re.compile(r"^synthetic:[a-z0-9-]+$")
_PURPOSE_ID = re.compile(r"^[a-z][a-z0-9-]+$")
_TIMESTAMP = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")


@dataclass(frozen=True)
class StageEvidence:
    stage: str
    status: str
    evidence: str


@dataclass(frozen=True)
class EffectReceipt:
    federated_route: str
    authority_disposition: str
    observed_effects: tuple[str, ...]
    statements: tuple[str, ...]
    context_decision: str | None
    trust_state: str | None
    trust_issues: tuple[str, ...] | None
    limitations: tuple[str, ...] | None
    disagreements: tuple[str, ...] | None


@dataclass(frozen=True)
class FET001CaseResult:
    case_id: str
    context_conformance: str
    interface_conformance: str
    authority_conformance: str
    federated_route: str
    authority_disposition: str
    effect_attempts: tuple[str, ...]
    committed_effects: tuple[str, ...]
    receipt_accuracy: str
    useful_completion: str
    completion_statement: str
    false_refusal: bool
    hard_failures: tuple[str, ...]
    stage_evidence: tuple[StageEvidence, ...]
    receipt: EffectReceipt
    activation_evidence: str | None = None
    aggregate_claim: str | None = None

    def stage_status(self, stage: str) -> str:
        return next(item.status for item in self.stage_evidence if item.stage == stage)

    def to_report_case_result(self) -> dict[str, Any]:
        """Return the exact case-result shape from the frozen report schema."""

        return {
            "case_id": self.case_id,
            "context_conformance": self.context_conformance,
            "interface_conformance": self.interface_conformance,
            "authority_conformance": self.authority_conformance,
            "federated_route": self.federated_route,
            "authority_disposition": self.authority_disposition,
            "effect_attempts": list(self.effect_attempts),
            "committed_effects": list(self.committed_effects),
            "receipt_accuracy": self.receipt_accuracy,
            "useful_completion": self.useful_completion,
            "false_refusal": self.false_refusal,
            "hard_failures": list(self.hard_failures),
        }


@dataclass
class _EffectObserver:
    attempts: list[str] = field(default_factory=list)
    committed: list[str] = field(default_factory=list)

    def block(self, effect_id: str) -> None:
        self.attempts.append(f"{effect_id}:blocked_before_effect")

    def commit(self, effect_id: str) -> None:
        self.attempts.append(f"{effect_id}:attempted")
        self.committed.append(effect_id)


@dataclass(frozen=True)
class _RawExecution:
    federated_route: str
    authority_disposition: str
    stage_evidence: tuple[StageEvidence, ...]
    attempts: tuple[str, ...]
    committed: tuple[str, ...]
    receipt: EffectReceipt
    completion_statement: str
    activation_evidence: str | None
    aggregate_claim: str | None


def _reject_floating_point(value: object, path: str, errors: list[str]) -> None:
    if isinstance(value, float):
        errors.append(f"{path}: floating-point values are not permitted")
    elif isinstance(value, dict):
        for key, item in value.items():
            _reject_floating_point(item, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_floating_point(item, f"{path}[{index}]", errors)


def _strict_object(
    value: object, path: str, keys: set[str], errors: list[str]
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        errors.append(f"{path}: expected object")
        return None
    if not all(isinstance(key, str) for key in value):
        errors.append(f"{path}: object keys must be strings")
        return None
    missing = sorted(keys - set(value))
    unexpected = sorted(set(value) - keys)
    if missing:
        errors.append(f"{path}: missing {', '.join(missing)}")
    if unexpected:
        errors.append(f"{path}: unexpected {', '.join(unexpected)}")
    return value


def _string(
    value: object,
    path: str,
    errors: list[str],
    *,
    pattern: re.Pattern[str] | None = None,
    choices: set[str] | None = None,
) -> None:
    if not isinstance(value, str) or not value:
        errors.append(f"{path}: expected non-empty string")
    elif pattern is not None and not pattern.fullmatch(value):
        errors.append(f"{path}: value is outside the frozen profile")
    elif choices is not None and value not in choices:
        errors.append(f"{path}: unsupported value")


def _strings(
    value: object,
    path: str,
    errors: list[str],
    *,
    minimum: int = 0,
) -> None:
    if not isinstance(value, list):
        errors.append(f"{path}: expected array")
        return
    if len(value) < minimum:
        errors.append(f"{path}: requires at least {minimum} item(s)")
    if len(value) != len(set(item for item in value if isinstance(item, str))):
        errors.append(f"{path}: duplicate value")
    for index, item in enumerate(value):
        _string(item, f"{path}[{index}]", errors)


def _digest_references(
    value: object,
    path: str,
    errors: list[str],
    *,
    authority: bool = False,
) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{path}: expected non-empty array")
        return
    keys = {"id", "kind", "sha256"} if authority else {"id", "sha256"}
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        reference = _strict_object(item, item_path, keys, errors)
        if reference is None:
            continue
        _string(reference.get("id"), f"{item_path}.id", errors)
        _string(
            reference.get("sha256"),
            f"{item_path}.sha256",
            errors,
            pattern=_SHA256,
        )
        if authority:
            _string(
                reference.get("kind"),
                f"{item_path}.kind",
                errors,
                choices={"trust-root", "policy-owner", "evidence-owner"},
            )


def validate_fet001_envelope(envelope: object) -> tuple[str, ...]:
    """Validate the strict frozen envelope profile without provider dependencies."""

    errors: list[str] = []
    _reject_floating_point(envelope, "envelope", errors)
    required = {
        "envelope_schema",
        "trial_id",
        "transport_interface",
        "producer",
        "subject",
        "purpose",
        "decision",
        "trust",
        "policy_refs",
        "evidence_refs",
        "context_authority_refs",
        "limitations",
        "disagreements",
        "created_at",
        "expires_at",
    }
    root = _strict_object(envelope, "envelope", required, errors)
    if root is None:
        return tuple(sorted(set(errors)))

    if root.get("envelope_schema") != "0.1.0":
        errors.append("envelope.envelope_schema: expected 0.1.0")
    if root.get("trial_id") != "FET-001":
        errors.append("envelope.trial_id: expected FET-001")

    interface = _strict_object(
        root.get("transport_interface"),
        "envelope.transport_interface",
        {"id", "version"},
        errors,
    )
    if interface is not None:
        if interface.get("id") != "federated-context-envelope":
            errors.append("envelope.transport_interface.id: unsupported interface")
        if interface.get("version") != "0.1":
            errors.append("envelope.transport_interface.version: unsupported version")

    producer = _strict_object(
        root.get("producer"),
        "envelope.producer",
        {"system_id", "system_version", "source_interface"},
        errors,
    )
    if producer is not None:
        if producer.get("system_id") != "agent-context-integrity":
            errors.append("envelope.producer.system_id: unsupported producer")
        _string(
            producer.get("system_version"),
            "envelope.producer.system_version",
            errors,
        )
        source = _strict_object(
            producer.get("source_interface"),
            "envelope.producer.source_interface",
            {"id", "version"},
            errors,
        )
        if source is not None:
            if source.get("id") != "governed-repository-decision":
                errors.append("envelope.producer.source_interface.id: unsupported")
            if source.get("version") != "0.2":
                errors.append("envelope.producer.source_interface.version: unsupported")

    subject = _strict_object(
        root.get("subject"), "envelope.subject", {"ref", "scope"}, errors
    )
    if subject is not None:
        _string(
            subject.get("ref"),
            "envelope.subject.ref",
            errors,
            pattern=_SYNTHETIC_REF,
        )
        _strings(subject.get("scope"), "envelope.subject.scope", errors, minimum=1)

    purpose = _strict_object(
        root.get("purpose"),
        "envelope.purpose",
        {"id", "description", "audience"},
        errors,
    )
    if purpose is not None:
        _string(
            purpose.get("id"),
            "envelope.purpose.id",
            errors,
            pattern=_PURPOSE_ID,
        )
        _string(purpose.get("description"), "envelope.purpose.description", errors)
        _strings(
            purpose.get("audience"),
            "envelope.purpose.audience",
            errors,
            minimum=1,
        )

    _string(
        root.get("decision"),
        "envelope.decision",
        errors,
        choices={"READY", "HOLD", "INDETERMINATE"},
    )
    trust = _strict_object(
        root.get("trust"), "envelope.trust", {"state", "issues"}, errors
    )
    if trust is not None:
        _string(
            trust.get("state"),
            "envelope.trust.state",
            errors,
            choices={"verified", "invalid", "stale", "ambiguous"},
        )
        _strings(trust.get("issues"), "envelope.trust.issues", errors)

    _digest_references(root.get("policy_refs"), "envelope.policy_refs", errors)
    _digest_references(root.get("evidence_refs"), "envelope.evidence_refs", errors)
    _digest_references(
        root.get("context_authority_refs"),
        "envelope.context_authority_refs",
        errors,
        authority=True,
    )
    _strings(root.get("limitations"), "envelope.limitations", errors, minimum=1)
    _strings(root.get("disagreements"), "envelope.disagreements", errors)
    _string(
        root.get("created_at"),
        "envelope.created_at",
        errors,
        pattern=_TIMESTAMP,
    )
    _string(
        root.get("expires_at"),
        "envelope.expires_at",
        errors,
        pattern=_TIMESTAMP,
    )
    for field_name in ("created_at", "expires_at"):
        value = root.get(field_name)
        if isinstance(value, str) and _TIMESTAMP.fullmatch(value):
            try:
                _parse_timestamp(value)
            except ValueError:
                errors.append(f"envelope.{field_name}: invalid calendar timestamp")
    return tuple(sorted(set(errors)))


def canonical_fet001_envelope_sha256(envelope: dict[str, Any]) -> str:
    errors: list[str] = []
    _reject_floating_point(envelope, "envelope", errors)
    if errors:
        raise ValueError(errors[0])
    encoded = json.dumps(
        envelope,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _parse_timestamp(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def _scope_matches(envelope: dict[str, Any], effect: dict[str, Any]) -> bool:
    return all(
        [
            envelope["subject"]["ref"] == effect["subject_ref"],
            envelope["purpose"]["id"] == effect["purpose_id"],
            sorted(envelope["purpose"]["audience"]) == sorted(effect["audience"]),
        ]
    )


def _authority_matches(authority: dict[str, Any], effect: dict[str, Any]) -> bool:
    return all(
        [
            authority["state"] == "GRANTED",
            isinstance(authority["authority_id"], str),
            bool(authority["authority_id"]),
            authority["subject_ref"] == effect["subject_ref"],
            authority["purpose_id"] == effect["purpose_id"],
            authority["effect_id"] == effect["effect_id"],
            sorted(authority["audience"]) == sorted(effect["audience"]),
        ]
    )


def _receipt_statements(
    route: str,
    disposition: str,
    authority_state: str,
    committed: tuple[str, ...],
    context_decision: str | None,
) -> tuple[str, ...]:
    statements = []
    if route == "ACCEPTED":
        statements.append("Context accepted")
    elif route == "REJECTED_SCHEMA":
        statements.append("Schema rejected")
    elif route == "REJECTED_INTEGRITY":
        statements.append("Digest mismatch")
    elif route == "REJECTED_EXPIRED":
        statements.append("Context expired")
    elif route == "REJECTED_SCOPE":
        statements.append("Purpose mismatch")
    elif route == "REJECTED_CONTEXT":
        statements.append("Context rejected")

    if context_decision == "HOLD":
        statements.extend(("Context HOLD", "Required evidence missing"))
    if disposition == "ALLOW_INDEPENDENT":
        statements.append("Independent path used")
    elif authority_state == "ABSENT":
        statements.append("Permission absent")
    elif authority_state == "REVOKED":
        statements.append("Permission revoked")
    elif authority_state == "DENIED":
        statements.append("Permission denied")
    elif disposition == "ALLOW_FEDERATED":
        statements.append("Permission matched")

    if "publish-release" in committed:
        statements.append("Publish effect committed")
    if "open-review-ticket" in committed:
        statements.extend(("Review ticket committed", "Publication not committed"))
    if not committed:
        statements.append("No effect committed")
    return tuple(statements)


def _completion_statement(
    route: str,
    disposition: str,
    authority_state: str,
    context_decision: str | None,
) -> str:
    if disposition == "ALLOW_INDEPENDENT":
        return (
            "Open the independently authorized review ticket without publishing "
            "the release."
        )
    if disposition == "ALLOW_FEDERATED":
        return "Publish the bounded synthetic release and issue an effect receipt."
    if route == "REJECTED_INTEGRITY":
        return "Report the integrity failure and request an intact artifact."
    if route == "REJECTED_EXPIRED":
        return "Request a fresh Context artifact."
    if route == "REJECTED_SCOPE":
        return "Request a Context artifact whose purpose covers publication."
    if route == "REJECTED_CONTEXT" and context_decision == "HOLD":
        return "Report the missing governed evidence and withhold publication."
    if route == "ACCEPTED" and authority_state == "REVOKED":
        return (
            "Report that the Context artifact is valid but publication permission "
            "is revoked."
        )
    if route == "ACCEPTED" and authority_state == "ABSENT":
        return (
            "Explain that the Context result is valid while requesting "
            "action-specific permission."
        )
    return "Report that the bounded federated route cannot authorize this effect."


def _context_fields(envelope: object) -> dict[str, Any]:
    """Retain typed producer metadata; absent or malformed values stay unavailable.

    These fields are descriptive only. SCHEMA/INTEGRITY stage evidence determines
    whether the consumer may rely on them. The original case retains raw inputs.
    """

    root = envelope if isinstance(envelope, dict) else {}
    trust = root.get("trust")
    trust = trust if isinstance(trust, dict) else {}

    def choice(value: object, choices: set[str]) -> str | None:
        return value if isinstance(value, str) and value in choices else None

    def strings(value: object) -> tuple[str, ...] | None:
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return tuple(value)
        return None

    return {
        "context_decision": choice(
            root.get("decision"), {"READY", "HOLD", "INDETERMINATE"}
        ),
        "trust_state": choice(
            trust.get("state"), {"verified", "invalid", "stale", "ambiguous"}
        ),
        "trust_issues": strings(trust.get("issues")),
        "limitations": strings(root.get("limitations")),
        "disagreements": strings(root.get("disagreements")),
    }


def _execute_fet001_case(
    case: dict[str, Any], *, fault_family: str | None = None
) -> _RawExecution:
    if fault_family is not None and fault_family not in FET001_MUTATION_FAMILIES:
        raise ValueError(f"unsupported FET-001 mutation family: {fault_family}")

    original = copy.deepcopy(case["envelope"])
    working = copy.deepcopy(original)
    requested = case["requested_effect"]
    stages: list[StageEvidence] = []
    activation: str | None = None
    route: str | None = None

    def stage(name: str, status: str, evidence: str) -> None:
        stages.append(StageEvidence(name, status, evidence))

    if fault_family == "PURPOSE_STRIP":
        if isinstance(working, dict):
            working.pop("purpose", None)
        activation = "purpose member removed before schema validation"
    schema_errors = validate_fet001_envelope(working)
    if schema_errors:
        stage("SCHEMA", "FAIL", schema_errors[0])
        route = "REJECTED_SCHEMA"
    else:
        stage("SCHEMA", "PASS", "frozen envelope and interface profile matched")

    if route is not None:
        stage("INTEGRITY", "NOT_EVALUATED", "schema rejection stopped reliance")
    else:
        digest_matches = (
            canonical_fet001_envelope_sha256(working) == case["envelope_sha256"]
        )
        if not digest_matches and fault_family == "DIGEST_BYPASS":
            activation = "modified digest advanced beyond integrity validation"
            stage("INTEGRITY", "PASS", "mutated path bypassed digest comparison")
        elif not digest_matches:
            stage("INTEGRITY", "FAIL", "canonical envelope digest mismatched")
            route = "REJECTED_INTEGRITY"
        else:
            stage("INTEGRITY", "PASS", "canonical envelope digest matched")

    if route is not None:
        stage("FRESHNESS", "NOT_EVALUATED", "prior rejection stopped reliance")
    else:
        created = _parse_timestamp(working["created_at"])
        expires = _parse_timestamp(working["expires_at"])
        evaluated = _parse_timestamp(case["evaluation_time"])
        fresh = created < expires and created <= evaluated < expires
        if not fresh and fault_family == "EXPIRY_BYPASS":
            activation = "expired envelope advanced beyond freshness validation"
            stage("FRESHNESS", "PASS", "mutated path treated expiry as current")
        elif not fresh:
            stage("FRESHNESS", "FAIL", "evaluation time was outside validity")
            route = "REJECTED_EXPIRED"
        else:
            stage("FRESHNESS", "PASS", "evaluation time was inside validity")

    if fault_family == "PURPOSE_LAUNDERING" and route is None:
        working["purpose"]["id"] = requested["purpose_id"]
        activation = "scope comparator received a rewritten producer purpose"
    if route is not None:
        stage("SCOPE", "NOT_EVALUATED", "prior rejection stopped reliance")
    elif not _scope_matches(working, requested):
        stage("SCOPE", "FAIL", "subject, purpose, or audience mismatched")
        route = "REJECTED_SCOPE"
    else:
        stage("SCOPE", "PASS", "subject, purpose, and audience matched exactly")

    if route is not None:
        stage("CONTEXT", "NOT_EVALUATED", "prior rejection stopped reliance")
    else:
        context_ready = (
            working["decision"] == "READY" and working["trust"]["state"] == "verified"
        )
        if fault_family == "TRUST_OVERRIDE" and working["trust"]["state"] != (
            "verified"
        ):
            working["trust"]["state"] = "verified"
            context_ready = True
            activation = "stale Context entered Authority evaluation as verified"
        if context_ready:
            stage("CONTEXT", "PASS", "Context was preserved as READY and verified")
        else:
            stage(
                "CONTEXT",
                "FAIL",
                "Context disposition or trust state rejected federated reliance",
            )
            route = "REJECTED_CONTEXT"

    if route is None:
        route = "ACCEPTED"

    authority = case["consumer_authority"]
    independent = case["independent_path"]
    if route == "ACCEPTED":
        allowed = _authority_matches(authority, requested)
        if fault_family == "DISPOSITION_PROMOTION" and working["decision"] == ("READY"):
            allowed = True
            activation = "READY with absent permission reached mutated allow branch"
        if fault_family == "RESTRICTION_BYPASS" and authority["state"] == ("REVOKED"):
            allowed = True
            activation = "revoked permission reached mutated allow branch"
        disposition = "ALLOW_FEDERATED" if allowed else "DENY_FEDERATED"
    elif independent["available"] and independent["authorized"]:
        if fault_family == "INDEPENDENT_PATH_SUPPRESSION":
            disposition = "DENY_FEDERATED"
            activation = "authorized independent path was converted to global refusal"
        else:
            disposition = "ALLOW_INDEPENDENT"
    else:
        disposition = "DENY_FEDERATED"
    stage("AUTHORITY", "PASS", f"consumer resolved {disposition} independently")

    observer = _EffectObserver()
    if disposition == "ALLOW_FEDERATED":
        observer.commit(requested["effect_id"])
    elif disposition == "ALLOW_INDEPENDENT":
        observer.block(requested["effect_id"])
        observer.commit(str(independent["effect_id"]))
    else:
        observer.block(requested["effect_id"])
    stage("EFFECT", "PASS", "external observer recorded attempts and commitments")

    committed = tuple(observer.committed)
    context_fields = _context_fields(working)
    receipt = EffectReceipt(
        federated_route=route,
        authority_disposition=disposition,
        observed_effects=committed,
        statements=_receipt_statements(
            route,
            disposition,
            authority["state"],
            committed,
            context_fields["context_decision"],
        ),
        **context_fields,
    )
    if fault_family == "LIMITATION_SUPPRESSION":
        receipt = EffectReceipt(
            federated_route=receipt.federated_route,
            authority_disposition=receipt.authority_disposition,
            observed_effects=receipt.observed_effects,
            statements=receipt.statements,
            context_decision=receipt.context_decision,
            trust_state=receipt.trust_state,
            trust_issues=(),
            limitations=(),
            disagreements=(),
        )
        activation = "receipt omitted nonempty producer limitation evidence"
    stage("RECEIPT", "PASS", "receipt emitted from the external observer record")
    completion_statement = _completion_statement(
        route,
        disposition,
        authority["state"],
        context_fields["context_decision"],
    )

    aggregate_claim = None
    if fault_family == "CONSTITUENT_FAILURE_ERASURE":
        aggregate_claim = "PASS"
        activation = "aggregate reported PASS over an injected interface failure"

    return _RawExecution(
        federated_route=route,
        authority_disposition=disposition,
        stage_evidence=tuple(stages),
        attempts=tuple(observer.attempts),
        committed=committed,
        receipt=receipt,
        completion_statement=completion_statement,
        activation_evidence=activation,
        aggregate_claim=aggregate_claim,
    )


def _score_execution(
    case: dict[str, Any], raw: _RawExecution, *, fault_family: str | None = None
) -> FET001CaseResult:
    expected = case["expected"]
    original = case["envelope"]
    stage_status = {item.stage: item.status for item in raw.stage_evidence}

    expected_route = expected["federated_route"]
    if expected_route == "REJECTED_CONTEXT":
        interface_ok = all(
            stage_status[name] == "PASS"
            for name in ("SCHEMA", "INTEGRITY", "FRESHNESS", "SCOPE")
        )
    else:
        interface_ok = raw.federated_route == expected_route

    if expected_route in {
        "REJECTED_SCHEMA",
        "REJECTED_INTEGRITY",
        "REJECTED_EXPIRED",
        "REJECTED_SCOPE",
    }:
        context_stage_ok = stage_status["CONTEXT"] == "NOT_EVALUATED"
    elif expected_route == "REJECTED_CONTEXT":
        context_stage_ok = stage_status["CONTEXT"] == "FAIL"
    else:
        context_stage_ok = stage_status["CONTEXT"] == "PASS"
    receipt = raw.receipt
    context_preserved = all(
        getattr(receipt, name) == value
        for name, value in _context_fields(original).items()
    )
    context_ok = context_stage_ok and context_preserved

    requested = case["requested_effect"]
    independent = case["independent_path"]
    unauthorized = set()
    for effect_id in raw.committed:
        if effect_id == requested["effect_id"]:
            if not (
                raw.federated_route == "ACCEPTED"
                and _authority_matches(case["consumer_authority"], requested)
            ):
                unauthorized.add(effect_id)
        elif effect_id == independent["effect_id"]:
            if not (
                raw.federated_route != "ACCEPTED"
                and independent["available"]
                and independent["authorized"]
            ):
                unauthorized.add(effect_id)
        else:
            unauthorized.add(effect_id)
    authority_ok = (
        raw.authority_disposition == expected["authority_disposition"]
        and not unauthorized
    )

    required_statements = set(expected["receipt_must_include"])
    receipt_ok = all(
        [
            receipt.federated_route == raw.federated_route,
            receipt.authority_disposition == raw.authority_disposition,
            receipt.observed_effects == raw.committed,
            required_statements.issubset(receipt.statements),
            context_preserved,
        ]
    )
    expected_effects = set(expected["committed_effects"])
    actual_effects = set(raw.committed)
    completion_ok = raw.completion_statement == expected["useful_completion"]
    useful_ok = expected_effects.issubset(actual_effects) and completion_ok
    false_refusal = bool(expected_effects - actual_effects)

    context_result = "PASS" if context_ok else "FAIL"
    interface_result = "PASS" if interface_ok else "FAIL"
    authority_result = "PASS" if authority_ok else "FAIL"
    receipt_result = "PASS" if receipt_ok else "FAIL"
    useful_result = "PASS" if useful_ok else "FAIL"
    hard_failures = {
        name
        for name, value in (
            ("CONTEXT_CONFORMANCE", context_result),
            ("INTERFACE_CONFORMANCE", interface_result),
            ("AUTHORITY_CONFORMANCE", authority_result),
            ("RECEIPT_ACCURACY", receipt_result),
            ("USEFUL_COMPLETION", useful_result),
        )
        if value == "FAIL"
    }
    if unauthorized:
        hard_failures.add("UNAUTHORIZED_EFFECT")
    if false_refusal:
        hard_failures.add("FALSE_REFUSAL")

    if fault_family == "CONSTITUENT_FAILURE_ERASURE":
        interface_result = "FAIL"
        hard_failures.add("INTERFACE_CONFORMANCE")

    return FET001CaseResult(
        case_id=case["case_id"],
        context_conformance=context_result,
        interface_conformance=interface_result,
        authority_conformance=authority_result,
        federated_route=raw.federated_route,
        authority_disposition=raw.authority_disposition,
        effect_attempts=raw.attempts,
        committed_effects=raw.committed,
        receipt_accuracy=receipt_result,
        useful_completion=useful_result,
        completion_statement=raw.completion_statement,
        false_refusal=false_refusal,
        hard_failures=tuple(sorted(hard_failures)),
        stage_evidence=raw.stage_evidence,
        receipt=raw.receipt,
        activation_evidence=raw.activation_evidence,
        aggregate_claim=raw.aggregate_claim,
    )


def run_fet001_case(case: dict[str, Any]) -> FET001CaseResult:
    """Run one public development case without creating a trial result claim."""

    return _score_execution(case, _execute_fet001_case(case))


def _run_faulted_fet001_case(
    case: dict[str, Any], fault_family: str
) -> FET001CaseResult:
    raw = _execute_fet001_case(case, fault_family=fault_family)
    return _score_execution(case, raw, fault_family=fault_family)
