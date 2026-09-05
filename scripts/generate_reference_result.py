from __future__ import annotations

import argparse
import json
from pathlib import Path

from authoritybench.io import discover_project_root
from authoritybench.result import build_reference_result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve() if args.root else discover_project_root()
    generated = build_reference_result(root)
    target = root / "docs" / "reference-result.v0.1.1.json"

    if args.check:
        existing = json.loads(target.read_text(encoding="utf-8"))
        if existing != generated:
            print("reference result is stale")
            return 1
        print("reference result is current")
        return 0

    print(json.dumps(generated, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
