#!/usr/bin/env python3
"""Acquire and audit only HAI 23.05 train1..train4 for VALIDATION V2."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
from types import ModuleType
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from paperworks.data.hai_normal_materialization_v2 import (  # noqa: E402
    BLOCKED_EGRESS,
    BLOCKED_EQUIVALENCE,
    BLOCKED_MATERIALIZATION,
    BLOCKED_METADATA,
    CANONICAL_HEADER_HASH,
    HAINormalMaterializationV2Error,
    NORMAL_SPLITS,
    PINNED_GIT_COMMIT,
    build_public_receipt,
    canonical_hash,
    fail,
    raw_specs,
    require_authorized_members,
    validate_public_receipt,
)
from paperworks.data.hai_provenance_v1 import (  # noqa: E402
    HAIProvenanceError,
    _read_header,
    audit_csv_structure,
)


PUBLIC_RECEIPT = ROOT / "research_control_center/validation_v2/receipts/HAI_NORMAL_ONLY_MATERIALIZATION_RECEIPT_V2.json"


def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        fail(BLOCKED_MATERIALIZATION)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _cache_root(repository_root: Path) -> Path:
    raw = os.environ.get("LOCALAPPDATA") if os.name == "nt" else os.environ.get("XDG_CACHE_HOME")
    base = Path(raw) if raw else Path.home() / ".cache"
    root = base / "paper_v_20260625" / "official_hai_2305" / f"snapshot_{PINNED_GIT_COMMIT[:12]}_validation_v2_normal_only"
    repository = repository_root.resolve()
    resolved = root.resolve()
    if resolved == repository or repository in resolved.parents or root.is_symlink():
        fail(BLOCKED_MATERIALIZATION)
    return root


def _git_head(repository_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repository_root,
        capture_output=True, text=True, check=False,
    )
    value = result.stdout.strip()
    if result.returncode != 0 or len(value) != 40 or set(value) - set("0123456789abcdef"):
        fail(BLOCKED_MATERIALIZATION)
    return value


def _code_hash() -> str:
    digest = sha256()
    for path in (
        ROOT / "src/paperworks/data/hai_normal_materialization_v2.py",
        Path(__file__).resolve(),
        ROOT / "scripts/local/materialize_hai_d0_normal_payload_v1.py",
        ROOT / "scripts/local/materialize_hai_inner_payload_v1.py",
    ):
        payload = path.read_bytes()
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\x00")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _atomic_json(path: Path, document: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    if temporary.exists() or path.is_symlink():
        fail(BLOCKED_MATERIALIZATION)
    with temporary.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(document, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _structural_audit(cache_root: Path) -> list[dict[str, Any]]:
    first_path = cache_root / PurePosixPath(NORMAL_SPLITS[0].relative_path)
    raw_header, canonical_header, _ = _read_header(first_path)
    if sha256(raw_header).hexdigest() != CANONICAL_HEADER_HASH:
        fail(BLOCKED_MATERIALIZATION)
    records: list[dict[str, Any]] = []
    for spec in NORMAL_SPLITS:
        path = cache_root / PurePosixPath(spec.relative_path)
        audit = audit_csv_structure(
            path,
            relative_path=spec.relative_path,
            expected_point_count=86,
            canonical_header=canonical_header,
            official_train_normal_description_verified=True,
            test_file_structural_only=False,
        )
        record = audit.to_dict()
        if (
            record["file_sha256"] != spec.sha256
            or record["byte_size"] != spec.size_bytes
            or record["row_count"] != spec.row_count
            or record["header_sha256"] != CANONICAL_HEADER_HASH
            or record["header_field_count"] != 87
            or record["timestamp_field"] != "timestamp"
            or record["nominal_timestamp_delta_seconds"] != 1.0
            or record["timestamps_strictly_increasing"] is not True
            or record["malformed_row_count"] != 0
            or record["inconsistent_field_count_rows"] != 0
            or record["ordered_header_matches_canonical"] is not True
            or record["expected_point_count_reconciled"] is not True
            or record["normal_file_status"] != "normal_only_verified"
        ):
            fail(BLOCKED_MATERIALIZATION)
        records.append({
            "symbolic_id": spec.symbolic_id,
            "relative_path": spec.relative_path,
            "sha256": record["file_sha256"],
            "size_bytes": record["byte_size"],
            "row_count": record["row_count"],
            "header_field_count": record["header_field_count"],
            "header_sha256": record["header_sha256"],
            "timestamp_field": record["timestamp_field"],
            "nominal_timestamp_delta_seconds": record["nominal_timestamp_delta_seconds"],
            "timestamps_strictly_increasing": record["timestamps_strictly_increasing"],
            "malformed_row_count": record["malformed_row_count"],
            "inconsistent_field_count_rows": record["inconsistent_field_count_rows"],
            "normal_file_status": record["normal_file_status"],
        })
    return records


def materialize_normal_only_v2(repository_root: Path, public_receipt: Path) -> dict[str, Any]:
    repository_root = repository_root.resolve()
    require_authorized_members(tuple(item.relative_path for item in NORMAL_SPLITS))
    cache_root = _cache_root(repository_root)
    try:
        legacy = _load_module(
            repository_root / "scripts/local/materialize_hai_d0_normal_payload_v1.py",
            "_validation_v2_normal_materialization_primitives",
        )
        try:
            legacy._materialize_specs(repository_root, cache_root, raw_specs())
        except legacy.D0NormalMaterializationError as exc:
            if exc.code == legacy.BLOCKED_CUSTODY:
                fail(BLOCKED_EQUIVALENCE)
            if exc.code in {legacy.BLOCKED_PATH, legacy.BLOCKED_STAGE}:
                fail(BLOCKED_MATERIALIZATION)
            # The cache root and fixed authority have already passed local
            # predicates.  The remaining historical generic failure is the
            # fail-closed result of both approved acquisition transports.
            fail(BLOCKED_EGRESS)
        structural = _structural_audit(cache_root)
        private_manifest: dict[str, Any] = {
            "schema_version": "hai_normal_only_private_materialization_manifest_v2",
            "status": "NORMAL_ONLY_MATERIALIZATION_READY",
            "cache_root": str(cache_root),
            "files": [
                {
                    "symbolic_id": spec.symbolic_id,
                    "absolute_path": str((cache_root / PurePosixPath(spec.relative_path)).resolve()),
                    "relative_path": spec.relative_path,
                    "sha256": spec.sha256,
                    "size_bytes": spec.size_bytes,
                }
                for spec in NORMAL_SPLITS
            ],
            "test1_accesses": 0,
            "test2_accesses": 0,
            "label_accesses": 0,
            "held_out_accesses": 0,
        }
        private_manifest["self_hash"] = canonical_hash(private_manifest)
        private_path = cache_root / ".validation_v2_normal_materialization_manifest.json"
        _atomic_json(private_path, private_manifest)
        receipt = build_public_receipt(
            execution_commit=_git_head(repository_root),
            code_hash=_code_hash(),
            private_manifest_hash=str(private_manifest["self_hash"]),
            structural_records=structural,
            created_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        )
        validate_public_receipt(receipt)
        _atomic_json(public_receipt, receipt)
        return receipt
    except HAINormalMaterializationV2Error:
        raise
    except HAIProvenanceError:
        fail(BLOCKED_MATERIALIZATION)
    except Exception as exc:
        name = type(exc).__name__
        message = str(exc)
        if "NETWORK" in message or "GIT_LFS" in message or name in {"URLError", "TimeoutError"}:
            fail(BLOCKED_EGRESS)
        if "CUSTODY" in message:
            fail(BLOCKED_EQUIVALENCE)
        fail(BLOCKED_MATERIALIZATION)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    parser.add_argument("--public-receipt", type=Path, default=PUBLIC_RECEIPT)
    args = parser.parse_args()
    try:
        receipt = materialize_normal_only_v2(args.repository_root, args.public_receipt)
    except HAINormalMaterializationV2Error as exc:
        print(exc.state)
        return 2
    print(f"NORMAL_ONLY_CUSTODY_READY receipt={receipt['self_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
