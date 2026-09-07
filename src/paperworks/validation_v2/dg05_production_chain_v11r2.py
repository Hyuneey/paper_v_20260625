"""DG05 V11R2 runtime-safety successor release gate.

V11R2 preserves V11R1 scientific roots and adds only runtime enforcement for
the closure/preflight/one-time-execution approval contract.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .dg05_production_chain_v11 import PREACCESS_MODE, REAL_MODE, file_hash, load_self_hashed, self_hashed, resolve_frozen_kernel_v11
from .dg05_production_chain_v11r1 import AUTHORITY_HASHES, V5_SHA256

PREDECESSOR_RELEASE = "9f2387cf7aa19134badf760a00c0002c6cbbee53230022ff48b395cf516ea314"
PREDECESSOR_CLOSURE = "ffdc02f92ae6bf87b5ac1880ad74f5a2be5f26d535dbfa71991b7dcc4f62a2f1"
PREDECESSOR_BINDING = "6f120cb262707b58b6e1e98971f105285185f8763955b0abfdd6a1c14c74ce66"


class DG05ProductionChainV11R2Error(ValueError):
    pass


def build_manifest(*, repository_root: Path, source_commit: str, implementation_paths: dict[str, Path]) -> dict[str, Any]:
    required = {"successor_gate", "unified_runner", "runtime_approval_guard", "execution_ledger", "shared_route_core",
                "resource_loader", "resource_materializer", "container_materializer", "resource_orchestrator",
                "production_executor", "terminal_chain", "v11_bridge", "v5_compatibility", "source_file_crosswalk",
                "postfreeze_metric_binding", "metric_primitives", "metric_surface", "metric_oracle", "v11_route",
                "v11_custodian", "scenario_adapter", "v5_kernel"}
    if set(implementation_paths) != required:
        raise DG05ProductionChainV11R2Error("V11R2_IMPLEMENTATION_CENSUS_REQUIRED")
    root = repository_root.resolve(); rows = []
    for name, path in sorted(implementation_paths.items()):
        resolved = path.resolve()
        if root not in resolved.parents or not resolved.is_file() or resolved.is_symlink():
            raise DG05ProductionChainV11R2Error("V11R2_IMPLEMENTATION_PATH_INVALID")
        rows.append({"logical_name": name, "relative_path": resolved.relative_to(root).as_posix(), "byte_hash": file_hash(resolved)})
    if next(row for row in rows if row["logical_name"] == "v5_kernel")["byte_hash"] != V5_SHA256 or resolve_frozen_kernel_v11(root)["source_byte_hash"] != V5_SHA256:
        raise DG05ProductionChainV11R2Error("FROZEN_V5_SCIENTIFIC_KERNEL_MUTATED")
    return self_hashed({"schema": "dg05_executable_v11r2_candidate_manifest_v1", "designation": "DG05_EXECUTABLE_V11R2",
                        "release_class": "RUNTIME_SAFETY_SUCCESSOR", "scientific_method_version": "UNCHANGED_FROM_V11R1",
                        "status": "CANDIDATE_AWAITING_EXACT_USER_APPROVAL", "approval_status": "NOT_APPROVED",
                        "implementation_source_commit": source_commit, "predecessor_release_hash": PREDECESSOR_RELEASE,
                        "predecessor_closure_hash": PREDECESSOR_CLOSURE, "predecessor_execution_binding_hash": PREDECESSOR_BINDING,
                        "predecessor_disposition": "APPROVED_NOT_EXECUTED_SUPERSEDED_RUNTIME_SAFETY_GUARD_INCOMPLETE",
                        "authority_hashes": AUTHORITY_HASHES, "scenario_authority_hash": AUTHORITY_HASHES["scenario_authority"],
                        "p1_authority_hash": AUTHORITY_HASHES["unified_p1"], "physical_custody_hash": AUTHORITY_HASHES["physical_custody"],
                        "implementation_authorities": rows, "frozen_v5_kernel_hash": V5_SHA256,
                        "frozen_kernel": resolve_frozen_kernel_v11(root), "same_runner_for_preaccess_and_real": True,
                        "heldout_predictions_observed": 0, "heldout_metrics_observed": 0})


def initialize(*, manifest_path: Path, expected_hash: str, repository_root: Path, mode: str,
               user_approved_release_hash: str | None) -> dict[str, Any]:
    manifest = load_self_hashed(manifest_path, "dg05_executable_v11r2_candidate_manifest_v1")
    if manifest["self_hash"] != expected_hash:
        raise DG05ProductionChainV11R2Error("V11R2_RELEASE_HASH_MISMATCH")
    if tuple(manifest.get(k) for k in ("predecessor_release_hash", "predecessor_closure_hash", "predecessor_execution_binding_hash")) != (PREDECESSOR_RELEASE, PREDECESSOR_CLOSURE, PREDECESSOR_BINDING):
        raise DG05ProductionChainV11R2Error("V11R2_PREDECESSOR_BINDING_MISMATCH")
    root = repository_root.resolve()
    for row in manifest["implementation_authorities"]:
        path = (root / row["relative_path"]).resolve()
        if root not in path.parents or not path.is_file() or file_hash(path) != row["byte_hash"]:
            raise DG05ProductionChainV11R2Error("V11R2_IMPLEMENTATION_BYTE_REPLAY_FAILED")
    if mode == PREACCESS_MODE:
        authorized = False
    elif mode == REAL_MODE:
        if user_approved_release_hash != manifest["self_hash"]:
            raise DG05ProductionChainV11R2Error("EXACT_V11R2_USER_APPROVAL_REQUIRED")
        authorized = True
    else:
        raise DG05ProductionChainV11R2Error("V11R2_MODE_REQUIRED")
    return self_hashed({"schema": "dg05_v11r2_initialized_state_v1", "mode": mode, "release_hash": manifest["self_hash"],
                        "release_manifest_hash": manifest["self_hash"], "protected_access_authorized": authorized,
                        "compatibility_authority": "OUTER_V11R2_APPROVAL_IS_SOLE_ACCESS_AUTHORITY",
                        "kernel": resolve_frozen_kernel_v11(root), "heldout_predictions": 0, "heldout_metrics": 0})


__all__ = ["DG05ProductionChainV11R2Error", "build_manifest", "initialize", "PREDECESSOR_RELEASE", "PREDECESSOR_CLOSURE", "PREDECESSOR_BINDING"]
