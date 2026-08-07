# Federation contracts

## Current dependency surface

This repository is independently runnable. Its manifest declares no federated
runtime-system or evaluation-system dependency.

## Provided artifact

`authority-conformance-report` v0.1 is experimental. A report is meaningful
only with the exact protocol, cases, permissions, observer, mutation catalog,
and declared observation scope used to produce it.

The artifact does not grant permission to another system. A consumer remains
responsible for its own purpose, authority, compatibility checks, and
consequential effects.

## FET-001 context consumer

The experimental FET-001 consumer accepts `federated-context-envelope` v0.1
from a context-integrity system. Acceptance means only that the artifact met
the frozen schema, integrity, freshness, scope, and Context rules. It does not
establish:

- truth beyond the producer's claim boundary;
- purpose-specific permission for an effect;
- permission to widen the subject, audience, purpose, or retention period; or
- authority to suppress uncertainty, limitations, expiry, or disagreement.

The authority-integrity system must independently establish the authority for
every tested effect.

The implementation and its content-addressed public artifacts are documented
in [federation/fet-001](federation/fet-001/README.md). They create no federated
runtime dependency and no FET-001 result claim.

## Failure behavior

An absent, expired, incompatible, disputed, or unverifiable upstream artifact
cannot be silently promoted. The system may continue through an independent
path only when that path has sufficient authority and evidence of its own.

The federation-wide rules live in
[Agent Governance Systems](https://github.com/heronyogi/agent-governance-systems).
