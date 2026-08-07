# Authority integrity system

## Identity

- System ID: `agent-authority-integrity`
- Repository role: `system-root`
- Public implementation: Agent Authority Benchmark
- Federation contract: v0.1.0

## Governing question

Which consequential effects remained inside a declared authority boundary?

## Primary invariant

No unauthorized consequential side effect may occur inside the declared and
confirmed observation scope.

This invariant is evaluated independently of model prose. Usefulness, false
refusal, contestability, receipt accuracy, and mutation detection remain
separate result dimensions.

## Boundary

The system evaluates purpose-scoped permissions and restrictions against
instrumented effects in synthetic stores, tools, queues, disclosures, and
downstream agents. It distinguishes prevention, post-effect detection,
observability failure, indeterminate coverage, and permitted effects.

It does not establish:

- whether an upstream interpretation is true;
- whether a declared authority is legitimate in the real world;
- whether uninstrumented external systems had no effect;
- whether a synthetic pass proves production safety; or
- whether another system may rely on or promote its result.

## Interface

The system provides `authority-conformance-report` v0.1 as an experimental
artifact. The report separates behavioral conformance, side-effect evidence,
receipt accuracy, and mutation-kill results.

The system currently consumes no federated runtime interface and has no runtime
or evaluation dependency on another registered system.

## Relationship

Agent Context Proof is a sibling system. Its governed repository decision may
be relevant to a future adapter, but it is not permission for this system to
retain, disclose, recommend, rank, or create an effect.

See [CONTRACTS.md](CONTRACTS.md) and [system.manifest.json](system.manifest.json)
for the machine-readable declaration.

## Public IP boundary

The system is based on observable permissions, operations, effects, observation
coverage, and receipts. It does not publish or require private ontology
primitives, symbolic registries, signatures, morphologies, derivation rules,
composition laws, correspondence, identities, or sealed cases.
