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

## Future context adapter

A future adapter may accept a versioned governed-context artifact from a
context-integrity system. Acceptance would mean only that the artifact met the
adapter's structural and provenance rules. It would not establish:

- truth beyond the producer's claim boundary;
- purpose-specific permission for an effect;
- permission to widen the subject, audience, purpose, or retention period; or
- authority to suppress uncertainty, limitations, expiry, or disagreement.

The authority-integrity system must independently establish the authority for
every tested effect.

## Failure behavior

An absent, expired, incompatible, disputed, or unverifiable upstream artifact
cannot be silently promoted. The system may continue through an independent
path only when that path has sufficient authority and evidence of its own.

The federation-wide rules live in
[Agent Governance Systems](https://github.com/heronyogi/agent-governance-systems).
