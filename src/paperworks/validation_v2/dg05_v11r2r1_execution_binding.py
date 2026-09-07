"""Typed Phase-A execution-binding contract for the V11R2R1 successor.

The binding is a distinct, non-approvable artifact.  A candidate release may
reference it by self-hash, but it cannot be substituted for a release manifest
or reconstructed from a release hash alone.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from .dg05_production_chain_v11 import digest, file_hash, load_self_hashed, self_hashed
from .dg05_production_chain_v11r1 import V5_SHA256


SCHEMA = "dg05_v11r2r3_execution_binding_manifest_v1"


class DG05V11R2R1ExecutionBindingError(ValueError):
    pass


def build_execution_binding_v11r2r1(*, repository_root: Path, implementation_source_commit: str,
                                    implementation_authorities: Sequence[Mapping[str, Any]],
                                    authority_hashes: Mapping[str, str], predecessor_release_hash: str,
                                    predecessor_closure_hash: str, predecessor_execution_binding_hash: str) -> dict[str, Any]:
    """Freeze the full reachable implementation census before qualification."""
    root = repository_root.resolve()
    rows = _validated_rows(root=root, rows=implementation_authorities)
    if not isinstance(implementation_source_commit, str) or len(implementation_source_commit) != 40:
        raise DG05V11R2R1ExecutionBindingError("IMPLEMENTATION_SOURCE_COMMIT_REQUIRED")
    if not all(isinstance(value, str) and len(value) == 64 for value in authority_hashes.values()):
        raise DG05V11R2R1ExecutionBindingError("AUTHORITY_HASH_CENSUS_REQUIRED")
    if not any(row["logical_name"] == "v5_kernel" and row["byte_hash"] == V5_SHA256 for row in rows):
        raise DG05V11R2R1ExecutionBindingError("FROZEN_V5_SCIENTIFIC_KERNEL_MUTATED")
    return self_hashed({
        "schema": SCHEMA,
        "designation": "DG05_EXECUTABLE_V11R2R3",
        "status": "PREACCESS_EXECUTION_BINDING",
        "not_user_approvable": True,
        "implementation_source_commit": implementation_source_commit,
        "predecessor_release_hash": predecessor_release_hash,
        "predecessor_closure_hash": predecessor_closure_hash,
        "predecessor_execution_binding_hash": predecessor_execution_binding_hash,
        "authority_hashes": dict(sorted(authority_hashes.items())),
        "implementation_authorities": rows,
        "frozen_v5_kernel_hash": V5_SHA256,
        "implementation_census_hash": digest(rows),
    })


def replay_execution_binding_v11r2r1(*, repository_root: Path, binding_path: Path,
                                     candidate_manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Replay serialized Phase A and compare it to the candidate exactly."""
    binding = load_self_hashed(binding_path, SCHEMA)
    if binding.get("status") != "PREACCESS_EXECUTION_BINDING" or binding.get("not_user_approvable") is not True:
        raise DG05V11R2R1ExecutionBindingError("EXECUTION_BINDING_STATUS_REQUIRED")
    if binding["self_hash"] != candidate_manifest.get("execution_binding_hash"):
        raise DG05V11R2R1ExecutionBindingError("EXECUTION_BINDING_HASH_MISMATCH")
    keys = ("designation", "implementation_source_commit", "authority_hashes", "frozen_v5_kernel_hash",
            "predecessor_release_hash", "predecessor_closure_hash", "predecessor_execution_binding_hash")
    if any(binding.get(key) != candidate_manifest.get(key) for key in keys):
        raise DG05V11R2R1ExecutionBindingError("EXECUTION_BINDING_LINEAGE_MISMATCH")
    candidate_rows = candidate_manifest.get("implementation_authorities")
    if binding.get("implementation_authorities") != candidate_rows:
        raise DG05V11R2R1ExecutionBindingError("EXECUTION_BINDING_IMPLEMENTATION_CENSUS_MISMATCH")
    rows = _validated_rows(root=repository_root.resolve(), rows=binding["implementation_authorities"])
    if binding.get("implementation_census_hash") != digest(rows):
        raise DG05V11R2R1ExecutionBindingError("EXECUTION_BINDING_CENSUS_HASH_MISMATCH")
    if binding.get("frozen_v5_kernel_hash") != V5_SHA256:
        raise DG05V11R2R1ExecutionBindingError("FROZEN_V5_SCIENTIFIC_KERNEL_MUTATED")
    return self_hashed({
        "schema": "dg05_v11r2r3_execution_binding_replay_receipt_v1",
        "status": "PASS",
        "execution_binding_hash": binding["self_hash"],
        "implementation_source_commit": binding["implementation_source_commit"],
        "implementation_count": len(rows),
        "implementation_census_hash": binding["implementation_census_hash"],
        "frozen_v5_kernel_hash": V5_SHA256,
        "authority_hashes": binding["authority_hashes"],
        "private_paths_published": False,
    })


def _validated_rows(*, root: Path, rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise DG05V11R2R1ExecutionBindingError("IMPLEMENTATION_CENSUS_REQUIRED")
    result: list[dict[str, str]] = []
    names: set[str] = set()
    paths: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {"logical_name", "relative_path", "byte_hash"}:
            raise DG05V11R2R1ExecutionBindingError("IMPLEMENTATION_CENSUS_REQUIRED")
        name, relative, expected = row["logical_name"], row["relative_path"], row["byte_hash"]
        if not isinstance(name, str) or not isinstance(relative, str) or not isinstance(expected, str) or len(expected) != 64:
            raise DG05V11R2R1ExecutionBindingError("IMPLEMENTATION_CENSUS_REQUIRED")
        path = (root / relative).resolve()
        if name in names or relative in paths or root not in path.parents or path.is_symlink() or not path.is_file() or file_hash(path) != expected:
            raise DG05V11R2R1ExecutionBindingError("IMPLEMENTATION_BYTE_REPLAY_FAILED")
        names.add(name); paths.add(relative)
        result.append({"logical_name": name, "relative_path": relative, "byte_hash": expected})
    if not result:
        raise DG05V11R2R1ExecutionBindingError("IMPLEMENTATION_CENSUS_REQUIRED")
    return sorted(result, key=lambda row: row["logical_name"])


__all__ = ["SCHEMA", "DG05V11R2R1ExecutionBindingError", "build_execution_binding_v11r2r1", "replay_execution_binding_v11r2r1"]
