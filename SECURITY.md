# Security policy

## Scope

Agent Authority Benchmark is a synthetic research harness. It is not a
production authorization service, privacy control, consent manager, deletion
system, or security boundary.

## Reporting a vulnerability

Please use GitHub's private vulnerability-reporting channel when available.
Do not open a public issue containing credentials, private data, unpublished
blind cases, or an exploit against a deployed third-party system.

## Test-data boundary

- Use synthetic subjects and artifacts only.
- Do not copy private correspondence into fixtures.
- Do not connect the reference harness to production memory or messaging
  systems.
- Do not use mutation fixtures against systems you do not own or control.
- Treat the `sealed/` and `results/` paths as local-only.

## Bounded claims

A clean report means only that the reference harness observed no unauthorized
consequential side effect inside its declared observation scope for that run.
It is not evidence about uninstrumented systems, real-world legitimacy,
production security, or all possible failures.
