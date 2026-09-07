"""V11R2 runtime approval and no-contact-preflight verification.

This module is deliberately limited to replaying immutable documents.  It
never opens a protected source, materializes a container, or invokes a
scientific route.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .dg05_production_chain_v11 import load_self_hashed, self_hashed
from .dg05_production_chain_v11r1 import V5_SHA256


class DG05V11R2RuntimeApprovalError(ValueError):
    pass


def _require_hash(value: object, code: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise DG05V11R2RuntimeApprovalError(code)
    return value


def verify_runtime_approval_v11r2(*, manifest: Mapping[str, Any], final_closure_path: Path,
                                  approved_release_hash: str | None,
                                  approved_final_closure_hash: str | None,
                                  approved_execution_binding_hash: str | None) -> dict[str, Any]:
    """Verify the three exact user-approved roots before resource routing."""
    release_hash = _require_hash(manifest.get("self_hash"), "V11R2_RELEASE_HASH_REQUIRED")
    binding_hash = _require_hash(manifest.get("execution_binding_hash"), "V11R2_EXECUTION_BINDING_REQUIRED")
    if approved_release_hash != release_hash:
        raise DG05V11R2RuntimeApprovalError("EXACT_V11R2_USER_APPROVAL_REQUIRED")
    if approved_execution_binding_hash != binding_hash:
        raise DG05V11R2RuntimeApprovalError("EXACT_V11R2_EXECUTION_BINDING_APPROVAL_REQUIRED")
    closure = load_self_hashed(final_closure_path, "dg05_v11r2_final_e2e_fresh_process_closure_receipt_v1")
    closure_hash = _require_hash(closure.get("self_hash"), "V11R2_FINAL_CLOSURE_HASH_REQUIRED")
    if approved_final_closure_hash != closure_hash:
        raise DG05V11R2RuntimeApprovalError("EXACT_V11R2_FINAL_CLOSURE_APPROVAL_REQUIRED")
    required = {
        "release_hash": release_hash,
        "execution_binding_hash": binding_hash,
        "implementation_source_commit": manifest.get("implementation_source_commit"),
        "v5_kernel_hash": V5_SHA256,
    }
    if any(closure.get(key) != value for key, value in required.items()):
        raise DG05V11R2RuntimeApprovalError("V11R2_FINAL_CLOSURE_BINDING_MISMATCH")
    if closure.get("status") != "PASS" or closure.get("metric_pipeline_pass") is not True or closure.get("full_synthetic_route_pass") is not True:
        raise DG05V11R2RuntimeApprovalError("V11R2_FINAL_CLOSURE_PASS_REQUIRED")
    if any(closure.get(key) != 0 for key in ("heldout_rows_parsed", "heldout_predictions", "heldout_metrics")):
        raise DG05V11R2RuntimeApprovalError("V11R2_FINAL_CLOSURE_CONTACT_REJECTED")
    return self_hashed({"schema": "dg05_v11r2_runtime_approval_replay_v1", "status": "PASS",
                        "release_hash": release_hash, "final_closure_hash": closure_hash,
                        "execution_binding_hash": binding_hash,
                        "implementation_source_commit": manifest["implementation_source_commit"],
                        "v5_kernel_hash": V5_SHA256, "protected_source_access": False})


def build_real_preflight_receipt_v11r2(*, approval_replay: Mapping[str, Any],
                                        resource_preflight: Mapping[str, Any],
                                        materialization_contract_hash: str, crosswalk_hash: str,
                                        scenario_authority_hash: str, p1_authority_hash: str,
                                        physical_source_set_hash: str) -> dict[str, Any]:
    """Create the required no-contact receipt after all preflight replays pass."""
    if approval_replay.get("status") != "PASS" or resource_preflight.get("status") != "PASS":
        raise DG05V11R2RuntimeApprovalError("V11R2_PREFLIGHT_REPLAY_REQUIRED")
    return self_hashed({"schema": "dg05_v11r2_real_preflight_receipt_v1",
                        "status": "REAL_PREFLIGHT_PASS_NO_FEATURE_ACCESS",
                        "release_hash": approval_replay["release_hash"],
                        "final_closure_hash": approval_replay["final_closure_hash"],
                        "execution_binding_hash": approval_replay["execution_binding_hash"],
                        "implementation_source_commit": approval_replay["implementation_source_commit"],
                        "v5_kernel_hash": V5_SHA256,
                        "physical_custody_hash": resource_preflight["physical_custody_hash"],
                        "physical_source_set_hash": physical_source_set_hash,
                        "resource_materialization_contract_hash": materialization_contract_hash,
                        "source_file_crosswalk_hash": crosswalk_hash,
                        "scenario_authority_hash": scenario_authority_hash,
                        "p1_authority_hash": p1_authority_hash,
                        "production_asset_census": {"detectors": 6, "rules": 7},
                        "heldout_rows_parsed": 0, "heldout_predictions": 0,
                        "heldout_metrics": 0, "execution_consumed": False})


def verify_real_preflight_receipt_v11r2(*, receipt_path: Path, approval_replay: Mapping[str, Any],
                                         physical_custody_hash: str, materialization_contract_hash: str,
                                         crosswalk_hash: str, scenario_authority_hash: str,
                                         p1_authority_hash: str) -> dict[str, Any]:
    receipt = load_self_hashed(receipt_path, "dg05_v11r2_real_preflight_receipt_v1")
    expected = {"release_hash": approval_replay["release_hash"], "final_closure_hash": approval_replay["final_closure_hash"],
                "execution_binding_hash": approval_replay["execution_binding_hash"], "physical_custody_hash": physical_custody_hash,
                "resource_materialization_contract_hash": materialization_contract_hash, "source_file_crosswalk_hash": crosswalk_hash,
                "scenario_authority_hash": scenario_authority_hash, "p1_authority_hash": p1_authority_hash,
                "v5_kernel_hash": V5_SHA256}
    if receipt.get("status") != "REAL_PREFLIGHT_PASS_NO_FEATURE_ACCESS" or any(receipt.get(k) != v for k, v in expected.items()):
        raise DG05V11R2RuntimeApprovalError("V11R2_PREFLIGHT_RECEIPT_BINDING_MISMATCH")
    if any(receipt.get(key) != 0 for key in ("heldout_rows_parsed", "heldout_predictions", "heldout_metrics")):
        raise DG05V11R2RuntimeApprovalError("V11R2_PREFLIGHT_CONTACT_REJECTED")
    return receipt


__all__ = ["DG05V11R2RuntimeApprovalError", "verify_runtime_approval_v11r2",
           "build_real_preflight_receipt_v11r2", "verify_real_preflight_receipt_v11r2"]
