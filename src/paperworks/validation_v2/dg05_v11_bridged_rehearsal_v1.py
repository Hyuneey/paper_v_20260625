"""Fresh-process synthetic execution of the V11 bridge and exact V5 schedule."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Mapping
from .dg05_production_chain_v11 import file_hash, initialize_v11_candidate, load_self_hashed, self_hashed, PREACCESS_MODE
from .dg05_schedule_release_provenance_bridge_v11 import invoke_frozen_v5_schedule_v11


class DG05V11BridgedRehearsalError(ValueError):
    pass


def run_v11_bridged_rehearsal(*, repository_root: Path, work_root: Path, outer_manifest_path: Path,
                              expected_outer_hash: str, legacy_release_path: Path,
                              predecessor_v4_path: Path, predecessor_v4_closure_path: Path,
                              historical_v1_manifest_path: Path, metric_contract_path: Path,
                              normal_registry_path: Path, private_normal_manifest_path: Path,
                              expected_private_manifest_hash: str, wrapper: Any,
                              source_commit: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Use the historical synthetic topology but intercept only its schedule call.

    The call target is verified and immediately invokes the imported frozen V5
    function.  The temporary interception occurs in a clean rehearsal process,
    never modifies its module bytes, and is restored before return.
    """
    outer = load_self_hashed(outer_manifest_path, "dg05_executable_v11_candidate_manifest_v1")
    state = initialize_v11_candidate(manifest_path=outer_manifest_path, repository_root=repository_root,
                                     expected_hash=expected_outer_hash, mode=PREACCESS_MODE)
    legacy = load_self_hashed(legacy_release_path, "dg05_production_release_manifest_v2")
    from .dg05_production_chain_v2 import initialize_production_release_v5
    legacy_state = initialize_production_release_v5(
        release_manifest_path=legacy_release_path, repository_root=repository_root,
        predecessor_v4_manifest_path=predecessor_v4_path, predecessor_v4_closure_path=predecessor_v4_closure_path,
        expected_release_hash=legacy["self_hash"], authority_mode="PREACCESS_FROZEN_KERNEL_REHEARSAL",
        expected_executable_version=legacy["executable_version"])
    from . import dg05_connected_rehearsal_v5 as connected
    original = connected.execute_prediction_schedule_v5
    if file_hash(repository_root / "src/paperworks/validation_v2/dg05_production_route_v5.py") != outer["frozen_kernel"]["source_byte_hash"]:
        raise DG05V11BridgedRehearsalError("FROZEN_V5_SCIENTIFIC_KERNEL_MUTATED")
    bridge_hash = file_hash(repository_root / "src/paperworks/validation_v2/dg05_schedule_release_provenance_bridge_v11.py")
    captured: dict[str, Any] = {}
    def bridged(**kwargs: Any) -> tuple[Any, ...]:
        outcome = invoke_frozen_v5_schedule_v11(repository_root=repository_root, outer_release=outer,
            outer_state=state, legacy_release=legacy, legacy_state=legacy_state,
            bridge_authority_hash=bridge_hash, schedule_kwargs=kwargs)
        captured.update(outcome[-1])
        return outcome[:5]
    connected.execute_prediction_schedule_v5 = bridged
    try:
        rehearsal, parity, roots = connected.run_connected_preaccess_rehearsal_v5(
            repository_root=repository_root, work_root=work_root, release_path=legacy_release_path,
            predecessor_v4_path=predecessor_v4_path, predecessor_v4_closure_path=predecessor_v4_closure_path,
            historical_v1_manifest_path=historical_v1_manifest_path, metric_contract_path=metric_contract_path,
            normal_registry_path=normal_registry_path, private_normal_manifest_path=private_normal_manifest_path,
            expected_private_manifest_hash=expected_private_manifest_hash, wrapper=wrapper, source_commit=source_commit)
    finally:
        connected.execute_prediction_schedule_v5 = original
    schedule = captured.get("schedule_envelope")
    envelopes = captured.get("envelopes", [])
    result = captured.get("result_container")
    if schedule is None or result is None or len(envelopes) != rehearsal["derived_prediction_cells"]:
        raise DG05V11BridgedRehearsalError("V11_BRIDGED_SCHEDULE_INCOMPLETE")
    bridge_receipt = self_hashed({"schema": "dg05_v11_bridged_schedule_rehearsal_v1", "status": "PASS",
        "v11_release_hash": outer["self_hash"], "v11_state_hash": state["self_hash"],
        "bridge_authority_hash": bridge_hash, "frozen_v5_kernel_hash": outer["frozen_kernel"]["source_byte_hash"],
        "planned_cells": rehearsal["derived_prediction_cells"], "actual_v5_schedule_cells": len(envelopes),
        "v11_bridged_cells": len(envelopes), "fallback_cells": 0, "unexercised_required_cells": 0,
        "heldout_feature_cells": 0, "metric_cells": 0, "inner_kernel_census_hash": schedule["inner_v5_kernel_census_hash"],
        "schedule_envelope_hash": schedule["self_hash"], "result_container_hash": result["self_hash"],
        "envelope_hashes": [row["self_hash"] for row in envelopes],
        "scientific_schedule_implementation": "DG05_V5_FROZEN_SCHEDULE",
        "outer_execution_release": "DG05_EXECUTABLE_V11", "delegation": "V11_PROVENANCE_BRIDGE_TO_FROZEN_V5_SCHEDULE",
        "heldout_predictions_observed": 0, "heldout_metrics_observed": 0})
    return bridge_receipt, schedule, result
