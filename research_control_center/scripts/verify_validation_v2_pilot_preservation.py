from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


class PreservationError(RuntimeError):
    """Raised when an immutable PILOT V1 path differs from its authority."""


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout


def verify(root: Path, manifest_path: Path) -> tuple[int, int]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    authority = manifest["authority_commit"]
    expected_tree = manifest["authority_tree"]
    actual_tree = _git(root, "show", "-s", "--format=%T", authority).strip()
    if actual_tree != expected_tree:
        raise PreservationError("authority tree identity differs")

    raw = _git(root, "ls-tree", "-r", "-z", authority)
    entries = [entry for entry in raw.split("\0") if entry]
    if len(entries) != manifest["tracked_blob_count"]:
        raise PreservationError("authority blob count differs")

    authority_paths: set[str] = set()
    for entry in entries:
        metadata, path = entry.split("\t", 1)
        _mode, object_type, _expected_object = metadata.split(" ", 2)
        if object_type == "blob":
            authority_paths.add(path)

    changed: list[str] = []
    diff = _git(root, "diff", "--name-status", "--no-renames", authority, "--")
    for line in diff.splitlines():
        if not line:
            continue
        status, path = line.split("\t", 1)
        # Additive VALIDATION V2 and RCC files are allowed. Every path that
        # already existed in the authority tree must remain byte-identical.
        if path in authority_paths and status != "A":
            changed.append(path)

    if changed:
        preview = ", ".join(changed[:5])
        raise PreservationError(
            f"immutable PILOT V1 paths differ count={len(changed)} preview={preview}"
        )
    return len(authority_paths), len(entries)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(
            "research_control_center/validation_v2/"
            "PILOT_V1_PRESERVATION_MANIFEST.json"
        ),
    )
    args = parser.parse_args()
    root = args.repo_root.resolve()
    manifest = args.manifest
    if not manifest.is_absolute():
        manifest = root / manifest
    checked, entries = verify(root, manifest)
    print(
        "PILOT_V1_PRESERVATION_PASS "
        f"checked_blobs={checked} authority_entries={entries}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
