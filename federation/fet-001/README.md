# FET-001 consumer implementation

This directory contains the offline consumer implementation artifacts for the
frozen FET-001 v0.1 protocol. The Authority system accepts
`federated-context-envelope` v0.1 as bounded Context input; acceptance never
creates permission for an effect.

## Processing boundary

The implementation preserves the frozen order:

1. schema;
2. integrity;
3. freshness;
4. scope;
5. Context;
6. Authority;
7. effect; and
8. receipt.

Schema through Context failures reject only the federated route. Authority is
resolved independently for the exact synthetic subject, purpose, effect, and
audience. An independent path remains available only when its evidence and
authority do not depend on the rejected envelope.

Effect attempts and commitments are recorded by a deterministic observer
outside any model prose. Receipts are checked against those observations and
must preserve producer trust issues, limitations, and disagreements.

## Canonical artifacts

The protocol mirror, eight development cases, ten mutations, and four schemas
are byte-identical copies of the frozen catalog artifacts. In particular, the
consumed envelope schema has SHA-256
`d8fc7ba77eb6172a91dc212044dc3d7670f8db8ce260cc748bfaffc8f5ce9f6d`,
the same content address published by the producer implementation.

The fixtures are public development cases, not blind evidence. The mutation
runner proves activation and keeps detection stage separate from whether an
effect already occurred.

## Non-claim

This change implements and tests the consumer. It does not publish a FET-001
trial report, claim an experimental pass, open the development-execution gate,
run a model or provider API, use production data, create a real external
effect, or publish a sealed case.
