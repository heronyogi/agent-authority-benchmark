# Threat model

## Protected claim

The v0.1 harness protects only the integrity of a synthetic benchmark claim:
whether observed consequential effects stayed within declared permissions and
whether injected faults were activated and detected as reported.

## Assets

- purpose-scoped permission state;
- dispute and revocation state;
- observed effect records;
- propagation notices;
- receipts;
- mutation activation evidence; and
- the distinction between prevention, detection, and unknown coverage.

## Adversarial behaviors

- writing memory despite a denied purpose;
- relabeling a purpose to launder authority;
- relying on stale permission after revocation;
- dropping a required propagation or correction notice;
- reporting that an effect was blocked when it committed;
- reopening a disputed inference without authority;
- inventing emergency status;
- hiding a side effect outside the observer;
- refusing a clearly authorized useful action; and
- producing cautious prose while tools perform a prohibited effect.

## Trusted components in v0.1

- checked-in synthetic fixtures;
- the deterministic reference policy;
- the in-memory stores and observer;
- the mutation controller's activation record; and
- offline test execution.

The v0.1 harness does not defend against an attacker who can rewrite the
fixtures, policy, observer, tests, and result together. Future result artifacts
should bind those inputs by digest and independent review.

## Observation limitation

An uninstrumented propagation path cannot support a no-side-effect claim. When
a mutation writes outside the declared observer, the correct result is
indeterminate unless an independent external observer detects the effect.

## Out of scope

- real production systems and third-party delivery guarantees;
- legal determinations about consent, deletion, or retention;
- malicious infrastructure outside the declared propagation domain;
- model alignment in general; and
- proof that any private architecture is correct or complete.
