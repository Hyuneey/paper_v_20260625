"""Append-only V11R1 terminal-state, DG-05 package, and DG-06 handoff helpers.

These helpers bind existing frozen results; they neither score a row nor
implement a metric.  They make retry disposition and post-schedule lineage
explicit for the future approved invocation.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .dg05_production_chain_v11 import canonical_bytes, self_hashed


class DG05V11R1TerminalChainError(ValueError):
    pass


_ORDER = ("READY", "REAL_EXECUTION_STARTED", "PREDICTION_CONTACT_OCCURRED",
          "PREDICTIONS_FROZEN", "METRICS_FROZEN", "TERMINAL_COMPLETE",
          "TERMINAL_FAILED_AFTER_SCIENTIFIC_CONTACT")


def next_execution_state_v11r1(*, release_hash: str, execution_binding_hash: str,
                                physical_source_set_hash: str, output_namespace: str,
                                predecessor: Mapping[str, Any] | None, state: str) -> dict[str, Any]:
    """Create a hash-bound transition; no state can be overwritten in place."""
    if state not in _ORDER or not all(type(value) is str and len(value) == 64
                                      for value in (release_hash, execution_binding_hash, physical_source_set_hash)):
        raise DG05V11R1TerminalChainError("EXECUTION_STATE_BINDING_REQUIRED")
    if not output_namespace:
        raise DG05V11R1TerminalChainError("EXECUTION_OUTPUT_NAMESPACE_REQUIRED")
    if predecessor is not None:
        old = predecessor.get("state")
        if old not in _ORDER or (old in {"TERMINAL_COMPLETE", "TERMINAL_FAILED_AFTER_SCIENTIFIC_CONTACT"}
                                 or _ORDER.index(state) <= _ORDER.index(old)):
            raise DG05V11R1TerminalChainError("EXECUTION_STATE_TRANSITION_REJECTED")
        if any(predecessor.get(key) != value for key, value in {
            "release_hash": release_hash, "execution_binding_hash": execution_binding_hash,
            "physical_source_set_hash": physical_source_set_hash, "output_namespace": output_namespace,
        }.items()):
            raise DG05V11R1TerminalChainError("EXECUTION_STATE_ROOT_SWAP")
    return self_hashed({"schema": "dg05_v11r1_execution_state_v1", "state": state,
                        "release_hash": release_hash, "execution_binding_hash": execution_binding_hash,
                        "physical_source_set_hash": physical_source_set_hash,
                        "output_namespace": output_namespace,
                        "predecessor_state_hash": None if predecessor is None else predecessor["self_hash"],
                        "retry_policy": "PRECONTACT_ONLY_RETRY;SCIENCE_CONTACT_TERMINAL"})


def write_new_state_v11r1(path: Path, state: Mapping[str, Any]) -> None:
    if path.exists():
        raise DG05V11R1TerminalChainError("EXECUTION_STATE_APPEND_ONLY_CONFLICT")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(dict(state)) + b"\n")


def build_terminal_package_v11r1(*, release_hash: str, terminal_state: Mapping[str, Any],
                                 physical_custody_hash: str, projection_timestamp_hash: str,
                                 private_asset_custody_hash: str, prediction_freeze_hash: str,
                                 scenario_authority_hash: str, p1_authority_hash: str,
                                 metric_primitives_hashes: Mapping[str, str], metric_surface_hashes: Mapping[str, str],
                                 independent_metric_verification_hashes: Mapping[str, str],
                                 root_to_terminal_hash: str) -> dict[str, Any]:
    if terminal_state.get("state") != "TERMINAL_COMPLETE" or terminal_state.get("release_hash") != release_hash:
        raise DG05V11R1TerminalChainError("TERMINAL_COMPLETE_STATE_REQUIRED")
    return self_hashed({"schema": "dg05_terminal_result_package_v1", "status": "TERMINAL_COMPLETE",
                        "release_hash": release_hash, "execution_state_hash": terminal_state["self_hash"],
                        "physical_custody_hash": physical_custody_hash,
                        "projection_timestamp_aggregate_hash": projection_timestamp_hash,
                        "private_production_asset_custody_hash": private_asset_custody_hash,
                        "prediction_freeze_hash": prediction_freeze_hash,
                        "scenario_authority_hash": scenario_authority_hash, "p1_authority_hash": p1_authority_hash,
                        "metric_primitives": dict(sorted(metric_primitives_hashes.items())),
                        "metric_surfaces": dict(sorted(metric_surface_hashes.items())),
                        "independent_metric_verifications": dict(sorted(independent_metric_verification_hashes.items())),
                        "root_to_terminal_hash": root_to_terminal_hash})


def build_dg06_handoff_v1(*, terminal_package: Mapping[str, Any], scientific_preregistration_hash: str) -> dict[str, Any]:
    if terminal_package.get("schema") != "dg05_terminal_result_package_v1" or terminal_package.get("status") != "TERMINAL_COMPLETE":
        raise DG05V11R1TerminalChainError("DG05_TERMINAL_PACKAGE_REQUIRED")
    return self_hashed({"schema": "dg06_input_handoff_v1", "status": "READY_FOR_DG06",
                        "dg05_terminal_result_package_hash": terminal_package["self_hash"],
                        "dg05_release_hash": terminal_package["release_hash"],
                        "metric_surface_hashes": terminal_package["metric_surfaces"],
                        "independent_metric_verification_hashes": terminal_package["independent_metric_verifications"],
                        "scenario_authority_hash": terminal_package["scenario_authority_hash"],
                        "p1_authority_hash": terminal_package["p1_authority_hash"],
                        "scientific_preregistration_hash": scientific_preregistration_hash,
                        "immutable_input_only": True, "may_rerun_predictions": False,
                        "may_change_metrics": False, "may_change_denominator": False})


__all__ = ["DG05V11R1TerminalChainError", "next_execution_state_v11r1", "write_new_state_v11r1",
           "build_terminal_package_v11r1", "build_dg06_handoff_v1"]
