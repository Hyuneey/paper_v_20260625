"""Hash-only V11R1 protected-resource runtime materialization.

The immutable custody receipt, not a workstation locator, is the scientific
identity. This module creates a private path-bearing runtime plan only after
replaying that receipt with exact SHA-256 checks. It does not parse containers
or CSV content.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .dg05_production_chain_v11 import digest, file_hash, self_hashed

_CUSTODY_SCHEMA = "hai22_kaggle_exact_payload_recovery_receipt_v1"
_CUSTODY_HASH = "46b1319363731aeb050133b92aee0f5d37db0879cb6066ceaee70191cdd3fbaa"
_CONTRACT_SCHEMA = "dg05_v11r1_protected_resource_materialization_contract_v1"
_PLAN_SCHEMA = "dg05_v11r1_protected_resource_plan_v1"


class DG05V11R1ResourceMaterializerError(ValueError):
    """Raised before any protected feature container may be opened."""


def _verify_self_hashed(value: Mapping[str, Any], schema: str) -> dict[str, Any]:
    if value.get("schema") != schema or value.get("self_hash") != digest(
        {key: item for key, item in value.items() if key != "self_hash"}
    ):
        raise DG05V11R1ResourceMaterializerError("RESOURCE_MATERIALIZATION_AUTHORITY_REPLAY_FAILED")
    return dict(value)


def load_exact_custody_receipt_v11r1(path: Path) -> dict[str, Any]:
    """Replay the frozen ten-file identity root without looking at payload rows."""
    value = _verify_self_hashed(json.loads(path.read_text(encoding="ascii")), _CUSTODY_SCHEMA)
    if (
        value["self_hash"] != _CUSTODY_HASH
        or value.get("total_verified") != 10
        or value.get("remaining_lfs_pointers") != 0
        or len(value.get("files", ())) != 10
    ):
        raise DG05V11R1ResourceMaterializerError("EXACT_PHYSICAL_CUSTODY_RECEIPT_REQUIRED")
    return value


def build_materialization_contract_v11r1(
    *, custody_receipt_path: Path, implementation_hash: str, source_commit: str
) -> dict[str, Any]:
    """Freeze portable lookup semantics and immutable expected byte identities."""
    receipt = load_exact_custody_receipt_v11r1(custody_receipt_path)
    entries = sorted(
        (
            {"panel_id": row["panel_id"], "file_id": row["file_id"], "sha256": row["actual_sha256"],
             "size": row["actual_size"], "repository_relative_path": row["repository_relative_path"]}
            for row in receipt["files"]
        ), key=lambda row: (row["panel_id"], row["file_id"]),
    )
    if len({(row["panel_id"], row["file_id"]) for row in entries}) != 10:
        raise DG05V11R1ResourceMaterializerError("PHYSICAL_CUSTODY_IDENTITY_BIJECTION_REQUIRED")
    return self_hashed({
        "schema": _CONTRACT_SCHEMA, "status": "PASS", "physical_custody_hash": receipt["self_hash"],
        "expected_files": entries, "entry_count": 10,
        "resource_materializer_implementation_hash": implementation_hash, "runtime_plan_schema": _PLAN_SCHEMA,
        "allowed_discovery": "FROZEN_RELATIVE_PATH_THEN_EXACT_SHA256_WITHIN_AUTHORIZED_ROOTS",
        "symlink_policy": "REJECT", "duplicate_copy_policy": "FROZEN_PATH_THEN_ROOT_PRIORITY_THEN_LEXICAL_RELATIVE_PATH",
        "compressed_container_policy": "RAW_GZIP_IDENTITY_THEN_POSTAPPROVAL_LOSSLESS_DECODE_ONLY",
        "heldout_parser_prohibition": True, "source_commit": source_commit,
    })


def _candidate_matches(*, root: Path, expected: Mapping[str, Any]) -> list[tuple[Path, bool]]:
    direct = root / str(expected["repository_relative_path"])
    candidates: Iterable[Path]
    if direct.is_file():
        candidates = (direct,)
    else:
        candidates = (candidate for candidate in root.rglob("*") if candidate.is_file()
                      and not candidate.is_symlink() and candidate.stat().st_size == expected["size"])
    result: list[tuple[Path, bool]] = []
    for candidate in candidates:
        if candidate.is_symlink() or candidate.stat().st_size != expected["size"]:
            continue
        if file_hash(candidate) == expected["sha256"]:
            result.append((candidate, candidate == direct))
    return result


def materialize_runtime_plan_v11r1(
    *, contract: Mapping[str, Any], authorized_roots: Iterable[Path]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Resolve private locators using only frozen paths or exact byte hashes."""
    contract = _verify_self_hashed(contract, _CONTRACT_SCHEMA)
    if contract.get("physical_custody_hash") != _CUSTODY_HASH or contract.get("entry_count") != 10:
        raise DG05V11R1ResourceMaterializerError("RESOURCE_MATERIALIZATION_CONTRACT_REQUIRED")
    roots = [Path(root).resolve() for root in authorized_roots]
    if not roots or any(not root.is_dir() for root in roots):
        raise DG05V11R1ResourceMaterializerError("AUTHORIZED_RESOURCE_ROOT_REQUIRED")
    rows: list[dict[str, Any]] = []
    public: list[dict[str, Any]] = []
    for expected in contract["expected_files"]:
        matches: list[tuple[Path, Path, bool]] = []
        for root in roots:
            for candidate, direct in _candidate_matches(root=root, expected=expected):
                matches.append((root, candidate, direct))
        if not matches:
            raise DG05V11R1ResourceMaterializerError(
                f"EXACT_CUSTODY_PAYLOAD_NOT_MATERIALIZED:{expected['panel_id']}:{expected['file_id']}"
            )
        matches.sort(key=lambda item: (not item[2], roots.index(item[0]), item[1].relative_to(item[0]).as_posix()))
        root, path, direct = matches[0]
        rows.append({**expected, "path": str(path),
                     "container_type": "GZIP" if str(expected["repository_relative_path"]).endswith(".gz") else "IDENTITY",
                     "classification": "PRIVATE_RUNTIME_LOCATOR"})
        public.append({"panel_id": expected["panel_id"], "file_id": expected["file_id"], "sha256": expected["sha256"],
                       "matching_copy_count": len(matches),
                       "selected_locator_reason": "FROZEN_REPOSITORY_RELATIVE_PATH" if direct else "EXACT_SHA256_AUTHORIZED_ROOT"})
    plan = self_hashed({"schema": _PLAN_SCHEMA,
                        "classification": "PRIVATE_RUNTIME_MATERIALIZATION_NOT_SCIENTIFIC_AUTHORITY_NOT_USER_APPROVAL_TARGET",
                        "physical_custody_hash": contract["physical_custody_hash"], "files": rows})
    receipt = self_hashed({
        "schema": "dg05_v11r1_resource_materialization_preflight_receipt_v1", "status": "PASS",
        "physical_custody_hash": contract["physical_custody_hash"],
        "aggregate_scientific_source_set_hash": digest([(row["panel_id"], row["file_id"], row["sha256"]) for row in public]),
        "expected_files": 10, "located_files": 10, "exact_hash_matches": 10, "missing": 0, "hash_mismatches": 0,
        "symlinks_accepted": 0, "filename_heuristic_selections": 0, "csv_parser_invocations": 0,
        "feature_rows_opened": 0, "feature_values_inspected": 0, "private_paths_published": False, "selected": public,
    })
    return plan, receipt


__all__ = ["DG05V11R1ResourceMaterializerError", "build_materialization_contract_v11r1",
           "load_exact_custody_receipt_v11r1", "materialize_runtime_plan_v11r1"]
