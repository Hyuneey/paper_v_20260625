"""Build the private TASK-039E3 utility numeric-reference registry once.

The script never discovers inputs.  Both the exact E1 ledger and the exact
output file are mandatory absolute paths; the public executable-equivalence
artifact is also explicit.  The output contains private normal-derived numeric
values and must remain outside Git.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from paperworks.v6.task039e3_r2r_utility_protocol_v2 import (
    build_private_numeric_registry_v2,
)


def _absolute_file(value: str, label: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise ValueError(f"{label} must be an absolute path")
    resolved = path.resolve(strict=True)
    if not resolved.is_file() or resolved.is_symlink():
        raise ValueError(f"{label} must be an existing regular non-link file")
    return resolved


def _new_output(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise ValueError("output private registry must be an absolute path")
    parent = path.parent.resolve(strict=True)
    if parent.is_symlink() or not parent.is_dir():
        raise ValueError("output parent must be an existing regular directory")
    result = parent / path.name
    if result.exists() or result.is_symlink():
        raise ValueError("output private registry must not already exist")
    repository_root = Path(__file__).resolve().parents[1]
    try:
        result.relative_to(repository_root)
    except ValueError:
        pass
    else:
        raise ValueError("output private registry must remain outside Git")
    return result


def build_registry_file_v2(
    *,
    e1_private_ledger: Path,
    executable_equivalence: Path,
    output_private_registry: Path,
) -> str:
    e1 = json.loads(e1_private_ledger.read_text(encoding="utf-8"))
    equivalence = json.loads(executable_equivalence.read_text(encoding="utf-8"))
    registry = build_private_numeric_registry_v2(e1, equivalence)
    output_private_registry.write_text(
        json.dumps(registry, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        errors="strict",
    )
    return str(registry["artifact_hash"])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--e1-private-ledger", required=True)
    parser.add_argument("--executable-equivalence", required=True)
    parser.add_argument("--output-private-registry", required=True)
    args = parser.parse_args(argv)
    e1 = _absolute_file(args.e1_private_ledger, "E1 private ledger")
    equivalence = _absolute_file(args.executable_equivalence, "executable equivalence")
    output = _new_output(args.output_private_registry)
    if output == e1 or output == equivalence:
        raise ValueError("output private registry must be distinct from every input")
    print(
        build_registry_file_v2(
            e1_private_ledger=e1,
            executable_equivalence=equivalence,
            output_private_registry=output,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
