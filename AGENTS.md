# Repository instructions

- Keep the deterministic harness independent of OpenAI and all other model providers.
- Evaluate observable side effects, never model claims about side effects.
- Keep all checked-in subjects, conversations, permissions, and effects synthetic.
- Do not add private ontology symbols, registries, signatures, morphologies, formulas, or internal mappings.
- Treat public fixtures as development cases, not blind evidence.
- Never let usefulness compensate for an unauthorized consequential effect.
- Distinguish prevention, detection, remediation, and unknown observation coverage.
- Never commit credentials, private correspondence, sealed cases, or generated live-evaluation results.
- Before finishing a change, run `python -m pytest`, `python -m ruff check .`, and `python -m ruff format --check .` from the project environment.
