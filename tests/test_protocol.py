from __future__ import annotations

import json
from pathlib import Path

import jsonschema


def _load(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def test_protocol_schema_and_markdown_mirror(project_root: Path) -> None:
    protocol = _load(project_root / "docs" / "protocol.v0.1.json")
    schema = _load(project_root / "schemas" / "protocol.schema.json")
    markdown = (project_root / "docs" / "protocol.v0.1.md").read_text(encoding="utf-8")
    jsonschema.Draft202012Validator(schema).validate(protocol)

    for outcome in protocol["outcomes"]:
        assert f"`{outcome['id']}`" in markdown
    for section in protocol["required_report_sections"]:
        assert f"`{section}`" in markdown
    for mutation in protocol["required_mutations"]:
        assert f"`{mutation}`" in markdown


def test_case_and_mutation_schemas(
    project_root: Path, cases: list[dict], mutations: list[dict]
) -> None:
    case_schema = _load(project_root / "schemas" / "case.schema.json")
    mutation_schema = _load(project_root / "schemas" / "mutation.schema.json")
    case_validator = jsonschema.Draft202012Validator(case_schema)
    mutation_validator = jsonschema.Draft202012Validator(mutation_schema)

    for case in cases:
        case_validator.validate(case)
    for mutation in mutations:
        mutation_validator.validate(mutation)


def test_development_case_matrix_is_closed(cases: list[dict]) -> None:
    assert len(cases) == 10
    case_ids = [case["case_id"] for case in cases]
    assert len(case_ids) == len(set(case_ids))

    families: dict[str, set[str]] = {}
    for case in cases:
        families.setdefault(case["family"], set()).add(case["variant"])
        effect_ids = {effect["effect_id"] for effect in case["candidate_effects"]}
        assert set(case["required_useful_effect_ids"]) <= effect_ids

    assert set(families) == {
        "present_response",
        "continuity",
        "question",
        "introduction",
        "sensitive_retention",
    }
    assert all(
        variants == {"restricted", "authorized_positive"}
        for variants in families.values()
    )


def test_mutations_match_protocol_and_resolve_targets(
    project_root: Path,
    cases_by_id: dict[str, dict],
    mutations: list[dict],
) -> None:
    protocol = _load(project_root / "docs" / "protocol.v0.1.json")
    assert {mutation["kind"] for mutation in mutations} == set(
        protocol["required_mutations"]
    )
    mutation_ids = [mutation["mutation_id"] for mutation in mutations]
    assert len(mutation_ids) == len(set(mutation_ids))

    for mutation in mutations:
        case = cases_by_id[mutation["target_case"]]
        assert mutation["target_effect"] in {
            effect["effect_id"] for effect in case["candidate_effects"]
        }


def test_public_files_contain_no_private_symbolic_surface(project_root: Path) -> None:
    forbidden = {
        "\u27c1",
        "\u2235",
        "\u2365",
        "\u2941",
        "\u269a",
        "\u25a1\u2083\u2086",
        "GLYPH_" + "WITNESS",
    }
    checked_suffixes = {".md", ".json", ".py", ".toml", ".yml", ".yaml"}
    for path in project_root.rglob("*"):
        if not path.is_file() or path.suffix not in checked_suffixes:
            continue
        if any(part.startswith(".") for part in path.relative_to(project_root).parts):
            continue
        text = path.read_text(encoding="utf-8")
        assert forbidden.isdisjoint(text), f"private symbolic surface in {path}"
