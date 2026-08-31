"""Create the public, execution-disabling VALIDATION V2 Stage-2 Commit-A manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from paperworks.validation_v2.stage2_freeze_v1 import (  # noqa: E402
    build_stage2_commit_a_manifest_v1,
    persist_stage2_commit_a_manifest_v1,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fileset",
        type=Path,
        default=REPOSITORY_ROOT / "research_control_center/validation_v2/STAGE2_COMMIT_A_FILESET.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPOSITORY_ROOT / "research_control_center/validation_v2/STAGE2_COMMIT_A_MANIFEST.json",
    )
    arguments = parser.parse_args()
    fileset = json.loads(arguments.fileset.read_text(encoding="utf-8"))
    if set(fileset) != {"schema", "schema_version", "source_base_commit", "groups"}:
        raise ValueError("STAGE2_FILESET_FIELDS_INVALID")
    if fileset["schema"] != "paperworks.validation_v2.stage2_commit_a_fileset_v1" or fileset["schema_version"] != "1.0.0":
        raise ValueError("STAGE2_FILESET_SCHEMA_INVALID")
    bindings: list[tuple[str, str, tuple[str, ...]]] = []
    for group in fileset["groups"]:
        if set(group) != {"role", "experiment_ids", "paths"}:
            raise ValueError("STAGE2_FILESET_GROUP_FIELDS_INVALID")
        experiment_ids = tuple(sorted(set(group["experiment_ids"])))
        for path in group["paths"]:
            bindings.append((path, group["role"], experiment_ids))
    paths = [item[0] for item in bindings]
    if len(paths) != len(set(paths)):
        raise ValueError("STAGE2_FILESET_DUPLICATE_PATH")
    manifest = build_stage2_commit_a_manifest_v1(
        REPOSITORY_ROOT,
        source_base_commit=fileset["source_base_commit"],
        file_bindings=tuple(bindings),
    )
    persist_stage2_commit_a_manifest_v1(manifest, arguments.output)
    print(f"PASS: {len(manifest.tracked_files)} files; manifest={manifest.manifest_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
