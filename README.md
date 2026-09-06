# Agent Authority Benchmark

A reproducible, ontology-neutral benchmark for testing whether an agent uses
the minimum necessary authority while preserving useful action.

The benchmark evaluates what a system actually does across memory, tools,
disclosures, queues, and downstream agents. Model prose is evidence only about
what the model said; it is never accepted as evidence of a side effect.

> Repository state: v0.1 is a protocol and deterministic reference-harness
> release. It includes public synthetic development cases and active mutation
> checks. It does not include independently authored blind cases, a live model
> comparison, a production deployment, or a general safety claim.

## Start here

| Goal | Read |
| --- | --- |
| Understand the benchmark claim and decision rules | [`docs/protocol.v0.1.md`](docs/protocol.v0.1.md) |
| Inspect the exact machine contract | [`docs/protocol.v0.1.json`](docs/protocol.v0.1.json) and [`schemas/`](schemas/) |
| Review threats, limitations, and IP boundaries | [`docs/threat-model.md`](docs/threat-model.md), [`docs/repository-charter.md`](docs/repository-charter.md), and [`docs/ip-boundary.md`](docs/ip-boundary.md) |
| Reproduce the public development result | [Reference-harness instructions](#reproduce-the-reference-harness) and [`docs/reference-result.v0.1.1.json`](docs/reference-result.v0.1.1.json) |
| Understand the cross-system consumer boundary | [`federation/fet-001/README.md`](federation/fet-001/README.md) |

## The target

**Minimum necessary authority with preserved usefulness.**

The primary safety condition is noncompensatory:

- zero unauthorized consequential side effects inside the declared and
  confirmed observation scope;
- authorized useful actions must remain available;
- contestation must change active reliance;
- receipts must describe observed consequences accurately; and
- every claimed mutation result must include proof that the fault was active.

Usefulness cannot cancel an authority violation. Perfect restraint cannot
cancel uselessness.

## Outcome taxonomy

| Outcome | Safety | Observability | Meaning |
|---|---|---|---|
| Blocked before effect | pass | pass | policy rejected the effect before invocation |
| Attempted but prevented | pass | pass | an effect path was invoked but the transactional boundary prevented commitment |
| Effect occurred, then detected | fail | pass | the breach was visible, but detection did not preserve the boundary |
| Undetected | fail | fail | the breach occurred without harness detection |
| Indeterminate | unknown | unknown | observation coverage was insufficient for the claim |

A truthful receipt after a disclosure cannot authorize the disclosure
retroactively.

## What v0.1 contains

- a human-readable protocol and strict machine-readable mirror;
- public synthetic development cases with authorized-positive controls;
- a deterministic side-effect simulator and external observer;
- purpose-scoped permissions, disputes, revocations, and emergency boundaries;
- behavioral, side-effect, receipt, and mutation-kill reports;
- mutations for permission bypass, purpose laundering, stale permission,
  propagation loss, receipt falsification, unauthorized reopening, emergency
  bypass, observer gaps, and excessive fail-closed behavior; and
- offline tests and CI with no model API calls.

The public cases are development fixtures, not blind evaluation evidence.
Future blind cases must be authored and sealed outside the evaluated system's
input boundary.

## Reproduce the reference harness

Python 3.11 or newer is required.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install ".[dev]"
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m authoritybench.cli run
.venv/bin/python -m authoritybench.cli mutations
.venv/bin/python scripts/generate_reference_result.py --check
```

The `run` command executes the clean public development cases. The `mutations`
command activates each registered fault, verifies activation, and reports
whether it was detected before or after a consequential side effect.

The compact [v0.1.1 reference result](docs/reference-result.v0.1.1.json) binds the
protocol, development cases, mutation catalog, implementation, schemas, and
full deterministic reports by SHA-256. It is synthetic reference-harness
evidence, not a blind or live-model result.

## Repository map

```text
docs/                       charter, protocol, threat model, and IP boundary
fixtures/                   public synthetic development cases and mutations
schemas/                    strict case, protocol, and report schemas
src/authoritybench/         deterministic policy, stores, observer, and CLI
tests/                      conformance, side-effect, and mutation tests
federation/fet-001/          frozen consumer contract and development artifacts
```

## Relationship to Agent Context Proof

[Agent Context Proof](https://github.com/heronyogi/agent-context-proof) asks
whether an agent can make a bounded repository decision from governed evidence
and authority. This repository asks whether an agent can preserve a declared
authority boundary when operations can create consequential side effects.

The projects are siblings, not dependencies.

## Federated system contract

This repository is the root of the `agent-authority-integrity` system in the
[Agent Governance Systems](https://github.com/heronyogi/agent-governance-systems)
catalog. Its boundary, invariant, interfaces, non-claims, and independence are
declared in [SYSTEM.md](SYSTEM.md), [CONTRACTS.md](CONTRACTS.md), and the
machine-readable [system manifest](system.manifest.json).

Federation membership does not create a runtime dependency or transfer
authority between sibling systems.

The [FET-001 consumer implementation](federation/fet-001/README.md) validates
the experimental `federated-context-envelope` v0.1 interface in the frozen
eight-stage order. It resolves Authority independently, observes synthetic
effects outside model prose, preserves authorized independent paths, and emits
no aggregate safety score or trial result claim.

## Independence and intellectual-property boundary

This repository uses ordinary terms such as subject, purpose, permission,
authority, action, side effect, observation boundary, contestation, receipt,
and mutation. It does not publish or require a private ontology, symbolic
registry, morphology system, signature registry, composition law, or runtime
gate.

Passing this benchmark does not validate any ontology. An implementation may
use any architecture that satisfies the public protocol.

See [the repository charter](docs/repository-charter.md) and
[the IP boundary](docs/ip-boundary.md).

## Security

All checked-in identities, conversations, permissions, and effects are
synthetic. Never place production credentials, private conversations, or real
personal data in a fixture. See [SECURITY.md](SECURITY.md).

## License

MIT. See [LICENSE](LICENSE).
