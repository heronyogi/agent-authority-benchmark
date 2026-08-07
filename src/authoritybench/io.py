from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def discover_project_root(start: Path | None = None) -> Path:
    candidate = (start or Path.cwd()).resolve()
    for directory in (candidate, *candidate.parents):
        if (
            (directory / "pyproject.toml").is_file()
            and (directory / "fixtures").is_dir()
            and (directory / "docs" / "protocol.v0.1.json").is_file()
        ):
            return directory
    raise FileNotFoundError(
        "Could not find an Agent Authority Benchmark checkout. "
        "Run from the repository or pass --root."
    )


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_cases(root: Path) -> list[dict[str, Any]]:
    return load_json(root / "fixtures" / "development-cases.v0.1.json")


def load_mutations(root: Path) -> list[dict[str, Any]]:
    return load_json(root / "fixtures" / "mutations.v0.1.json")
