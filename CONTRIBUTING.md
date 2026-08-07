# Contributing

Contributions are welcome when they preserve the benchmark's bounded public
identity.

## Good contributions

- synthetic case families with explicit subjects, purposes, permissions, and
  observable consequences;
- mutations with independent activation proof;
- stronger observation-boundary checks;
- tests that catch false receipts, purpose laundering, propagation loss, or
  false refusal; and
- clearer limitations and reproducibility records.

## Out of scope

- real personal data or private conversations;
- proprietary ontology definitions or internal mappings;
- claims that a benchmark pass proves general safety;
- hidden network calls in the deterministic harness; and
- weighted scores that allow usefulness to cancel an authority violation.

## Development

```bash
python3 -m venv .venv
.venv/bin/python -m pip install ".[dev]"
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
```

Pull requests should state the claimed scope, observable behavior, tests run,
and any new limitations.
