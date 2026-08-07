from __future__ import annotations

from pathlib import Path

import pytest

from authoritybench.io import load_cases, load_mutations


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def cases(project_root: Path) -> list[dict]:
    return load_cases(project_root)


@pytest.fixture(scope="session")
def cases_by_id(cases: list[dict]) -> dict[str, dict]:
    return {case["case_id"]: case for case in cases}


@pytest.fixture(scope="session")
def mutations(project_root: Path) -> list[dict]:
    return load_mutations(project_root)
