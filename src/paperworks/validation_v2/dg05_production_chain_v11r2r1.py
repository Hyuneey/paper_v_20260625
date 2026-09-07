"""V11R2R1 successor release gate.

This module owns release identity and the exact approval triple. It contains
no resource, model, normal-bundle, projection, or schedule logic: both real
modes must obtain that evidence from ``dg05_v11r2r1_preflight``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .dg05_production_chain_v11 import (
    PREACCESS_MODE,
    REAL_MODE,
    file_hash,
    load_self_hashed,
    resolve_frozen_kernel_v11,
    self_hashed,
)
from .dg05_production_chain_v11r1 import AUTHORITY_HASHES, V5_SHA256

PREACCESS_FROZEN_KERNEL_REHEARSAL = "PREACCESS_FROZEN_KERNEL_REHEARSAL"
REAL_PREFLIGHT_ONLY = "REAL_PREFLIGHT_ONLY"

PREDECESSOR_RELEASE = "5d030770c7d817fd61be108dea09ce4af12c7749d3d9120cb5bb00ec8fdd4560"
PREDECESSOR_BINDING = "11ebae408e3449bc845e1009b949bf8f508307679ac9fba74277e48f54c0608f"
PREDECESSOR_CLOSURE = "20b697bcb217e84171823fdc3142e7906863ad4dccdef088f1b347eafe02ca8e"

# This is deliberately a closed *implementation* census.  Adding a helper to
# a future real route requires a successor release, rather than silently
# expanding an already approved executable surface.
_REQUIRED_IMPLEMENTATIONS = frozenset({
    "successor_gate", "successor_runner", "complete_preflight", "preflight_receipt",
    "execution_binding", "execution_ledger",
    "shared_route_core", "resource_loader", "resource_materializer",
    "container_materializer", "resource_orchestrator", "production_executor",
    "execution_closure", "normal_source", "normal_materializer",
    "v5_compatibility", "v11_bridge", "v5_kernel",
    "source_file_crosswalk", "postfreeze_metric_binding", "metric_primitives",
    "metric_surface", "metric_oracle", "terminal_chain",
    "legacy_v11_route", "legacy_v11_custodian", "metric_contract", "multipanel_custody",
    "crosswalk_reconciliation",
    "runtime_plan_normalizer",
})


class DG05ProductionChainV11R2R1Error(ValueError):
    """A release-bound V11R2R1 gate rejected its input."""


def build_manifest(
    *,
    repository_root: Path,
    source_commit: str,
    implementation_paths: dict[str, Path],
    execution_binding_hash: str,
    source_file_crosswalk_hash: str,
) -> dict[str, Any]:
    """Build a candidate only after the separately serialized binding exists."""
    if not isinstance(execution_binding_hash, str) or len(execution_binding_hash) != 64:
        raise DG05ProductionChainV11R2R1Error("EXECUTION_BINDING_HASH_REQUIRED")
    if not isinstance(source_file_crosswalk_hash, str) or len(source_file_crosswalk_hash) != 64:
        raise DG05ProductionChainV11R2R1Error("SOURCE_FILE_CROSSWALK_HASH_REQUIRED")
    if set(implementation_paths) != _REQUIRED_IMPLEMENTATIONS:
        raise DG05ProductionChainV11R2R1Error("V11R2R1_COMPLETE_IMPLEMENTATION_CENSUS_REQUIRED")
    root = repository_root.resolve()
    rows: list[dict[str, str]] = []
    for name, path in sorted(implementation_paths.items()):
        resolved = path.resolve()
        if root not in resolved.parents or resolved.is_symlink() or not resolved.is_file():
            raise DG05ProductionChainV11R2R1Error("IMPLEMENTATION_PATH_INVALID")
        rows.append(
            {
                "logical_name": name,
                "relative_path": resolved.relative_to(root).as_posix(),
                "byte_hash": file_hash(resolved),
            }
        )
    if not any(row["logical_name"] == "v5_kernel" and row["byte_hash"] == V5_SHA256 for row in rows):
        raise DG05ProductionChainV11R2R1Error("FROZEN_V5_SCIENTIFIC_KERNEL_MUTATED")
    return self_hashed(
        {
            "schema": "dg05_executable_v11r2r2_candidate_manifest_v1",
            "designation": "DG05_EXECUTABLE_V11R2R2",
            "release_class": "RUNTIME_PLAN_CANONICAL_ORDER_NORMALIZATION_SUCCESSOR",
            "scientific_method_version": "UNCHANGED_FROM_V11R1",
            "status": "CANDIDATE_AWAITING_EXACT_USER_APPROVAL",
            "approval_status": "NOT_APPROVED",
            "implementation_source_commit": source_commit,
            "execution_binding_hash": execution_binding_hash,
            "predecessor_release_hash": PREDECESSOR_RELEASE,
            "predecessor_execution_binding_hash": PREDECESSOR_BINDING,
            "predecessor_closure_hash": PREDECESSOR_CLOSURE,
            "predecessor_disposition": "APPROVED_ONE_SHOT_CONSUMED_TERMINAL_FAILED_AFTER_SCIENTIFIC_CONTACT_BEFORE_FEATURE_ROW_PARSING",
            "authority_hashes": AUTHORITY_HASHES,
            "scenario_authority_hash": AUTHORITY_HASHES["scenario_authority"],
            "p1_authority_hash": AUTHORITY_HASHES["unified_p1"],
            "physical_custody_hash": AUTHORITY_HASHES["physical_custody"],
            "source_file_crosswalk_hash": source_file_crosswalk_hash,
            "implementation_authorities": rows,
            "frozen_v5_kernel_hash": V5_SHA256,
            "frozen_kernel": resolve_frozen_kernel_v11(root),
            "same_runner_for_preaccess_and_real": True,
            "heldout_rows_observed": 0,
            "heldout_predictions_observed": 0,
            "heldout_metrics_observed": 0,
        }
    )


def load_candidate(*, manifest_path: Path, expected_hash: str, repository_root: Path) -> dict[str, Any]:
    manifest = load_self_hashed(manifest_path, "dg05_executable_v11r2r2_candidate_manifest_v1")
    if manifest["self_hash"] != expected_hash:
        raise DG05ProductionChainV11R2R1Error("RELEASE_HASH_MISMATCH")
    if (
        manifest.get("predecessor_release_hash"),
        manifest.get("predecessor_execution_binding_hash"),
        manifest.get("predecessor_closure_hash"),
    ) != (PREDECESSOR_RELEASE, PREDECESSOR_BINDING, PREDECESSOR_CLOSURE):
        raise DG05ProductionChainV11R2R1Error("PREDECESSOR_BINDING_MISMATCH")
    root = repository_root.resolve()
    for row in manifest["implementation_authorities"]:
        path = (root / row["relative_path"]).resolve()
        if root not in path.parents or path.is_symlink() or not path.is_file() or file_hash(path) != row["byte_hash"]:
            raise DG05ProductionChainV11R2R1Error("IMPLEMENTATION_REPLAY_FAILED")
    if resolve_frozen_kernel_v11(root)["source_byte_hash"] != V5_SHA256:
        raise DG05ProductionChainV11R2R1Error("FROZEN_V5_SCIENTIFIC_KERNEL_MUTATED")
    return manifest


def verify_runtime_approval_v11r2r1(
    *,
    manifest: Mapping[str, Any],
    final_closure_path: Path,
    approved_release_hash: str | None,
    approved_final_closure_hash: str | None,
    approved_execution_binding_hash: str | None,
) -> dict[str, Any]:
    """Replay the exact user-approved release/closure/binding tuple."""
    release_hash = manifest.get("self_hash")
    binding_hash = manifest.get("execution_binding_hash")
    if approved_release_hash != release_hash:
        raise DG05ProductionChainV11R2R1Error("EXACT_V11R2R1_USER_APPROVAL_REQUIRED")
    if approved_execution_binding_hash != binding_hash:
        raise DG05ProductionChainV11R2R1Error("EXACT_V11R2R1_EXECUTION_BINDING_APPROVAL_REQUIRED")
    closure = load_self_hashed(
        final_closure_path,
        "dg05_v11r2r1_final_e2e_fresh_process_closure_receipt_v1",
    )
    if approved_final_closure_hash != closure.get("self_hash"):
        raise DG05ProductionChainV11R2R1Error("EXACT_V11R2R1_FINAL_CLOSURE_APPROVAL_REQUIRED")
    required = {
        "release_hash": release_hash,
        "execution_binding_hash": binding_hash,
        "implementation_source_commit": manifest.get("implementation_source_commit"),
        "v5_kernel_hash": V5_SHA256,
    }
    if any(closure.get(key) != value for key, value in required.items()):
        raise DG05ProductionChainV11R2R1Error("FINAL_CLOSURE_BINDING_MISMATCH")
    if closure.get("status") != "PASS" or not closure.get("full_synthetic_route_pass"):
        raise DG05ProductionChainV11R2R1Error("FINAL_CLOSURE_PASS_REQUIRED")
    if any(closure.get(key) != 0 for key in ("heldout_rows_parsed", "heldout_predictions", "heldout_metrics")):
        raise DG05ProductionChainV11R2R1Error("FINAL_CLOSURE_CONTACT_REJECTED")
    return self_hashed(
        {
        "schema": "dg05_v11r2r2_runtime_approval_replay_v1",
            "status": "PASS",
            "release_hash": release_hash,
            "final_closure_hash": closure["self_hash"],
            "execution_binding_hash": binding_hash,
            "implementation_source_commit": manifest["implementation_source_commit"],
            "v5_kernel_hash": V5_SHA256,
            "protected_source_access": False,
        }
    )


def initialize(
    *,
    manifest_path: Path,
    expected_hash: str,
    repository_root: Path,
    mode: str,
    user_approved_release_hash: str | None,
) -> dict[str, Any]:
    """Initialize shared-route state; exact triple replay occurs in the runner."""
    manifest = load_candidate(manifest_path=manifest_path, expected_hash=expected_hash, repository_root=repository_root)
    if mode in (PREACCESS_MODE, PREACCESS_FROZEN_KERNEL_REHEARSAL):
        authorized = False
    elif mode == REAL_MODE:
        if user_approved_release_hash != manifest["self_hash"]:
            raise DG05ProductionChainV11R2R1Error("EXACT_V11R2R1_USER_APPROVAL_REQUIRED")
        authorized = True
    else:
        raise DG05ProductionChainV11R2R1Error("MODE_REQUIRED")
    return self_hashed(
        {
            "schema": "dg05_v11r2r2_initialized_state_v1",
            "mode": mode,
            "release_hash": manifest["self_hash"],
            # The frozen V11 provenance bridge consumes this historical field
            # name; it is an exact alias, not an independent release root.
            "release_manifest_hash": manifest["self_hash"],
            "execution_binding_hash": manifest["execution_binding_hash"],
            "protected_access_authorized": authorized,
            "compatibility_authority": "OUTER_V11R2R1_APPROVAL_IS_SOLE_ACCESS_AUTHORITY",
            "kernel": resolve_frozen_kernel_v11(repository_root),
            "heldout_predictions": 0,
            "heldout_metrics": 0,
        }
    )


__all__ = [
    "DG05ProductionChainV11R2R1Error",
    "PREACCESS_FROZEN_KERNEL_REHEARSAL",
    "REAL_PREFLIGHT_ONLY",
    "build_manifest",
    "initialize",
    "load_candidate",
    "verify_runtime_approval_v11r2r1",
]
