# Observation and rejection integrity

Incomplete declared observation scope now produces unknown observability and,
absent a known violation, unknown safety. An observed violation remains a safety
failure even when coverage is incomplete. Useful completion remains a separate
measure of observed effects.

The FET-001 consumer now emits and scores a receipt after schema rejection even
when producer metadata is missing, malformed, or the envelope is not an object.
Absent or malformed metadata is represented as unavailable (`None`), rather than
invented READY/trust data or an empty list claiming there were no limitations.
Typed metadata is descriptive and does not bypass schema or integrity rejection.
The original case remains the raw input record. Impossible calendar timestamps
are rejected at SCHEMA before freshness evaluation.

An independently authorized fallback still operates after federated rejection.
The public frozen fixtures, digests, wire schema, and expected trial results are
unchanged. New synthetic regressions are separate from that historical trial.

The deterministic public harness was rerun as `reference-result.v0.1.1.json`
to bind the repaired source. The original v0.1 result is retained unchanged.
This successor is an offline replay, not a new model or independent trial.
