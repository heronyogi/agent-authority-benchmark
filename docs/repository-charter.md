# Repository charter

## Purpose

Agent Authority Benchmark tests whether an agent or agentic system uses the
minimum necessary authority while preserving useful action. It does so by
comparing declared permissions with instrumented side effects and by injecting
faults that should violate or weaken the boundary.

## Distinct identity

This project is not an extension of Agent Context Proof. Agent Context Proof
tests governed repository decisions over read-only evidence. Agent Authority
Benchmark tests state-changing operations across memory, tools, disclosures,
queues, and downstream agents.

The repositories may share research discipline and terminology, but neither is
a runtime dependency of the other.

## Public claim boundary

The strongest v0.1 claim is:

> The deterministic reference implementation preserved the declared authority
> boundary within its confirmed synthetic observation scope across the public
> development cases, and its mutation suite distinguished prevention,
> post-effect detection, failed observation, indeterminate coverage, and false
> refusal.

The project does not claim:

- independently authored blind evidence;
- live-model superiority;
- production safety, privacy, consent, or deletion guarantees;
- real-world legitimacy of any authority declaration;
- complete observation of external systems; or
- validation of an ontology or philosophical framework.

## Governing principles

1. Consequential side effects control the safety result.
2. Prose cannot override observed effects.
3. Usefulness and authority conformance are reported separately.
4. Detection after a breach is not prevention.
5. Unknown observation coverage remains unknown.
6. Permission is purpose-specific.
7. Contestation changes active reliance without rewriting history.
8. Mutation results require activation proof.
9. Public fixtures are development cases, not blind evidence.
10. Every claim is bounded to exact artifacts and an observation scope.

## Publication rule

New results must bind the protocol, cases, configuration, observer, mutation
catalog, and reporting rules used for the run. A result must preserve negative
findings and must not silently replace an indeterminate observation with a pass.
