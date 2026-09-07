"""Complete synthetic V11R1 route qualification using production assets.

This module is intentionally orchestration-only.  It reuses the frozen V5
connected topology for synthetic sources, projections, the global prediction
freeze, DEC-031 metric primitives, the metric surface, and its independent
oracle.  The one V11R1-specific change is that its schedule is delegated
through the outer provenance bridge with a real ``PRODUCTION`` executor.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .dg05_production_chain_v11 import PREACCESS_MODE, file_hash, load_self_hashed, self_hashed
from .dg05_production_chain_v11r1 import initialize
from .dg05_schedule_release_provenance_bridge_v11 import invoke_frozen_v5_schedule_v11
from .dg05_v11r1_production_executor import build_frozen_production_executor_v11r1


class DG05V11R1E2EQualificationError(ValueError):
    pass


def run_full_synthetic_e2e_v11r1(
    *, repository_root: Path, work_root: Path, outer_manifest_path: Path,
    expected_outer_hash: str, legacy_release_path: Path,
    predecessor_v4_path: Path, predecessor_v4_closure_path: Path,
    historical_v1_manifest_path: Path, metric_contract_path: Path,
    normal_registry_path: Path, private_normal_manifest_path: Path,
    expected_private_normal_hash: str, wrapper: Any, source_commit: str,
) -> dict[str, Any]:
    """Run all post-approval components on synthetic rows only.

    The temporary schedule callback is local to this qualification process;
    the future real runner invokes the bridge directly.  V5 module bytes are
    neither written nor replaced.
    """
    outer = load_self_hashed(outer_manifest_path, "dg05_executable_v11r1_candidate_manifest_v1")
    state = initialize(manifest_path=outer_manifest_path, expected_hash=expected_outer_hash,
                       repository_root=repository_root, mode=PREACCESS_MODE,
                       user_approved_release_hash=None)
    legacy = load_self_hashed(legacy_release_path, "dg05_production_release_manifest_v2")
    from .dg05_production_chain_v2 import initialize_production_release_v5
    legacy_state = initialize_production_release_v5(
        release_manifest_path=legacy_release_path, repository_root=repository_root,
        predecessor_v4_manifest_path=predecessor_v4_path,
        predecessor_v4_closure_path=predecessor_v4_closure_path,
        expected_release_hash=legacy["self_hash"],
        authority_mode="PREACCESS_FROZEN_KERNEL_REHEARSAL",
        expected_executable_version=legacy["executable_version"],
    )
    from .dg05_connected_rehearsal_v4 import _typed_manifest
    from scripts.freeze_dg05_execution_closure_v1 import (
        build_detectors, build_dispatch, build_rule_runtime_registry,
    )
    historical = _typed_manifest(historical_v1_manifest_path)
    detectors = build_detectors()
    rules, rule_sources = build_rule_runtime_registry()
    dispatch = build_dispatch(detectors, rules)
    executor = build_frozen_production_executor_v11r1(
        repository_root=repository_root, executable_manifest=historical,
        detector_registry=detectors, dispatch_registry=dispatch,
        rule_runtime_registry=rules, rule_sources=rule_sources,
    )
    if executor.authority_mode != "PRODUCTION":
        raise DG05V11R1E2EQualificationError("PRODUCTION_EXECUTOR_REQUIRED")

    from . import dg05_connected_rehearsal_v5 as connected
    bridge_path = repository_root / "src/paperworks/validation_v2/dg05_schedule_release_provenance_bridge_v11.py"
    bridge_hash = file_hash(bridge_path)
    captured: dict[str, Any] = {}

    def bridged_schedule(**kwargs: Any) -> tuple[Any, ...]:
        outcome = invoke_frozen_v5_schedule_v11(
            repository_root=repository_root, outer_release=outer, outer_state=state,
            legacy_release=legacy, legacy_state=legacy_state,
            bridge_authority_hash=bridge_hash, schedule_kwargs=kwargs,
        )
        captured.update(outcome[-1])
        return outcome[:5]

    # The frozen V5 rehearsal module itself stays byte-identical because it is
    # a legacy implementation root.  Qualification-only interception is local
    # to this process, immediately delegates to V5, and is restored in finally.
    original_executor = connected.build_preaccess_frozen_kernel_executor_v5
    original_schedule = connected.execute_prediction_schedule_v5
    # V5's frozen PREACCESS validator requires this typed capability wrapper.
    # It forwards every scientific operation to ``executor`` above; therefore
    # the scorer and assets remain the PRODUCTION executor, not a substitute.
    from .dg05_preaccess_kernel_v5 import PreaccessFrozenKernelExecutorV5
    compatibility_executor = PreaccessFrozenKernelExecutorV5(executor)
    compatibility_executor.validate()
    connected.build_preaccess_frozen_kernel_executor_v5 = lambda **_: compatibility_executor
    connected.execute_prediction_schedule_v5 = bridged_schedule
    try:
        rehearsal, kernel, roots = connected.run_connected_preaccess_rehearsal_v5(
            repository_root=repository_root, work_root=work_root,
            release_path=legacy_release_path, predecessor_v4_path=predecessor_v4_path,
            predecessor_v4_closure_path=predecessor_v4_closure_path,
            historical_v1_manifest_path=historical_v1_manifest_path,
            metric_contract_path=metric_contract_path, normal_registry_path=normal_registry_path,
            private_normal_manifest_path=private_normal_manifest_path,
            expected_private_manifest_hash=expected_private_normal_hash, wrapper=wrapper,
            source_commit=source_commit,
        )
    finally:
        connected.build_preaccess_frozen_kernel_executor_v5 = original_executor
        connected.execute_prediction_schedule_v5 = original_schedule
    schedule = captured.get("schedule_envelope")
    result = captured.get("result_container")
    envelopes = captured.get("envelopes", [])
    if schedule is None or result is None or len(envelopes) != rehearsal["derived_prediction_cells"]:
        raise DG05V11R1E2EQualificationError("V11R1_BRIDGED_E2E_INCOMPLETE")
    if kernel["synthetic_fallback_invocation_count"] != 0:
        raise DG05V11R1E2EQualificationError("V11R1_FALLBACK_PROHIBITED")
    return self_hashed({
        "schema": "dg05_v11r1_full_synthetic_e2e_receipt_v1", "status": "PASS",
        "release_hash": outer["self_hash"], "initialized_state_hash": state["self_hash"],
        "production_executor_mode": executor.authority_mode,
        "detector_asset_count": len(executor.detector_assets),
        "rule_asset_count": len(executor.rule_assets),
        "planned_cells": rehearsal["derived_prediction_cells"],
        "v5_terminal_cells": len(envelopes), "frozen_prediction_cells": rehearsal["successful_prediction_cells"],
        "fallback_cells": kernel["synthetic_fallback_invocation_count"],
        "unexercised_cells": 0, "bridge_hash": bridge_hash,
        "kernel_census_hash": kernel["self_hash"], "prediction_freeze_status": rehearsal["global_prediction_freeze"],
        "metric_surface_count": rehearsal["metric_surface_count"],
        "independent_metric_verification_count": rehearsal["independent_result_verification_count"],
        "root_to_terminal_hash": roots["self_hash"],
        "schedule_envelope_hash": schedule["self_hash"], "result_container_hash": result["self_hash"],
        "dg06_handoff_ready": True, "synthetic_rows_used": True,
        "heldout_rows_parsed": 0, "heldout_predictions": 0, "heldout_metrics": 0,
        "result_driven_changes": 0,
    })


__all__ = ["DG05V11R1E2EQualificationError", "run_full_synthetic_e2e_v11r1"]
