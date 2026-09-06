"""Non-scientific V11 provenance bridge for the byte-frozen V5 schedule."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Callable, Mapping
from .dg05_production_chain_v11 import (
    PREACCESS_MODE, REAL_MODE, canonical_bytes, digest, resolve_frozen_kernel_v11, self_hashed,
)


class DG05ScheduleReleaseProvenanceBridgeV11Error(ValueError):
    pass


BRIDGE_SCHEMA = "v11_to_v5_schedule_compatibility_view_v1"
BRIDGE_ID = "V11_PROVENANCE_BRIDGE_TO_FROZEN_V5_SCHEDULE"


def _sha(value: Any, code: str) -> str:
    if type(value) is not str or len(value) != 64:
        raise DG05ScheduleReleaseProvenanceBridgeV11Error(code)
    return value


def derive_compatibility_view_v11(*, outer_release: Mapping[str, Any], outer_state: Mapping[str, Any],
                                  legacy_release: Mapping[str, Any], legacy_state: Mapping[str, Any],
                                  bridge_authority_hash: str, repository_root: Path) -> dict[str, Any]:
    """Derive an internal V5 validator view; it has no access authority itself."""
    if outer_state.get("release_manifest_hash") != outer_release.get("self_hash"):
        raise DG05ScheduleReleaseProvenanceBridgeV11Error("OUTER_V11_STATE_BINDING_REQUIRED")
    if outer_state.get("mode") not in {PREACCESS_MODE, REAL_MODE}:
        raise DG05ScheduleReleaseProvenanceBridgeV11Error("V11_EXECUTION_MODE_REQUIRED")
    if outer_state["mode"] == REAL_MODE and not outer_state.get("protected_access_authorized"):
        raise DG05ScheduleReleaseProvenanceBridgeV11Error("EXACT_V11_APPROVAL_REQUIRED_BEFORE_DELEGATION")
    kernel = resolve_frozen_kernel_v11(repository_root)
    _sha(bridge_authority_hash, "BRIDGE_AUTHORITY_HASH_REQUIRED")
    if legacy_state.get("release_manifest_hash") != legacy_release.get("self_hash"):
        raise DG05ScheduleReleaseProvenanceBridgeV11Error("LEGACY_COMPATIBILITY_ROOT_REQUIRED")
    return self_hashed({"schema": BRIDGE_SCHEMA, "bridge_id": BRIDGE_ID,
                        "not_standalone_release": True, "not_user_approvable": True,
                        "independent_protected_access_authority": False,
                        "outer_v11_release_hash": outer_release["self_hash"],
                        "outer_v11_state_hash": outer_state["self_hash"],
                        "legacy_v5_release_hash": legacy_release["self_hash"],
                        "legacy_v5_state_hash": legacy_state["self_hash"],
                        "frozen_v5_kernel": kernel, "bridge_authority_hash": bridge_authority_hash,
                        "authority_hashes": outer_release["authority_hashes"],
                        "execution_mode": outer_state["mode"],
                        "source_commit": outer_release["implementation_source_commit"],
                        "delegation_purpose": "V11_PROVENANCE_ONLY_COMPATIBILITY_DELEGATION"})


def invoke_frozen_v5_schedule_v11(*, repository_root: Path, outer_release: Mapping[str, Any],
                                  outer_state: Mapping[str, Any], legacy_release: Mapping[str, Any],
                                  legacy_state: Mapping[str, Any], bridge_authority_hash: str,
                                  schedule_kwargs: Mapping[str, Any]) -> tuple[Any, ...]:
    """Invoke the exact V5 callable once, then add only external provenance envelopes."""
    view = derive_compatibility_view_v11(outer_release=outer_release, outer_state=outer_state,
                                         legacy_release=legacy_release, legacy_state=legacy_state,
                                         bridge_authority_hash=bridge_authority_hash,
                                         repository_root=repository_root)
    kernel = resolve_frozen_kernel_v11(repository_root)
    from .dg05_production_route_v5 import execute_prediction_schedule_v5
    if schedule_kwargs.get("release", {}).get("self_hash") != legacy_release.get("self_hash"):
        raise DG05ScheduleReleaseProvenanceBridgeV11Error("V5_DELEGATE_RELEASE_SWAP")
    results = execute_prediction_schedule_v5(**dict(schedule_kwargs))
    receipts, _, _, _, inner_census = results
    cells = list(schedule_kwargs["census"].get("cells", ()))
    if len(receipts) != len(cells) or len({item.cell_id for item in receipts}) != len(receipts):
        raise DG05ScheduleReleaseProvenanceBridgeV11Error("V5_RECEIPT_CARDINALITY_MISMATCH")
    envelopes: list[dict[str, Any]] = []
    for receipt in receipts:
        if receipt.executable_manifest_hash != legacy_release["self_hash"]:
            raise DG05ScheduleReleaseProvenanceBridgeV11Error("V5_INNER_RECEIPT_RELEASE_MISMATCH")
        document = receipt.document()
        envelopes.append(self_hashed({"schema": "dg05_v11_prediction_provenance_envelope_v1",
            "v11_release_hash": outer_release["self_hash"], "v11_initialized_state_hash": outer_state["self_hash"],
            "bridge_authority_hash": bridge_authority_hash, "compatibility_view_hash": view["self_hash"],
            "inner_v5_receipt_hash": document["self_hash"], "cell_id": receipt.cell_id,
            "panel_id": receipt.panel_id, "file_id": receipt.file_id, "method_id": receipt.method_id,
            "prediction_hash": receipt.prediction_artifact_hash, "trace_hash": receipt.trace_artifact_hash,
            "frozen_v5_kernel_hash": kernel["source_byte_hash"],
            "source_commit": outer_release["implementation_source_commit"],
            "execution_mode": outer_state["mode"], "scientific_schedule_implementation": "DG05_V5_FROZEN_SCHEDULE"}))
    if len({row["cell_id"] for row in envelopes}) != len(envelopes):
        raise DG05ScheduleReleaseProvenanceBridgeV11Error("DUPLICATE_V11_ENVELOPE")
    schedule_envelope = self_hashed({"schema": "dg05_v11_schedule_execution_envelope_v1",
        "v11_release_hash": outer_release["self_hash"], "compatibility_view_hash": view["self_hash"],
        "bridge_authority_hash": bridge_authority_hash, "expected_cell_count": len(cells),
        "inner_v5_receipt_hashes": [r.document()["self_hash"] for r in receipts],
        "outer_v11_envelope_hashes": [r["self_hash"] for r in envelopes],
        "inner_v5_kernel_census_hash": inner_census["self_hash"],
        "fallback_count": 0, "delegation": BRIDGE_ID,
        "scenario_authority_hash": outer_release["authority_hashes"]["scenario_authority"],
        "p1_authority_hash": outer_release["authority_hashes"]["unified_p1"]})
    result_container = self_hashed({"schema": "dg05_v11_structural_result_container_v1",
        "synthetic_qualification_only": True, "v11_release_hash": outer_release["self_hash"],
        "schedule_envelope_hash": schedule_envelope["self_hash"],
        "inner_v5_receipt_hashes": schedule_envelope["inner_v5_receipt_hashes"],
        "scenario_authority_hash": schedule_envelope["scenario_authority_hash"],
        "p1_authority_hash": schedule_envelope["p1_authority_hash"],
        "metric_cells": 0, "heldout_prediction_cells": 0})
    return (*results, {"compatibility_view": view, "envelopes": envelopes,
                       "schedule_envelope": schedule_envelope, "result_container": result_container})
