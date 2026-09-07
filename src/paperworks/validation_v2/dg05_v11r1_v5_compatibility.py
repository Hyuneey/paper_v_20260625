"""Derive a non-authoritative V5-shaped state from an approved V11R1 state."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .dg05_production_chain_v11 import self_hashed
from .dg05_production_chain_v2 import initialize_production_release_v5


class DG05V11R1V5CompatibilityError(ValueError):
    pass


def derive_v5_compatibility_state_v11r1(
    *, outer_release: Mapping[str, Any], outer_state: Mapping[str, Any],
    legacy_release_path: Path, predecessor_v4_manifest_path: Path,
    predecessor_v4_closure_path: Path, repository_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate legacy roots, then derive—not approve—a V5 validator state.

    The legacy release is never an access authority.  The only condition that
    permits a PRODUCTION-shaped inner state is the verified outer V11R1 exact
    approval.  This leaves the frozen V5 validator untouched.
    """
    if (outer_state.get("release_hash") != outer_release.get("self_hash")
            or outer_state.get("protected_access_authorized") is not True):
        raise DG05V11R1V5CompatibilityError("OUTER_V11R1_APPROVAL_REQUIRED")
    from .dg05_production_chain_v11 import load_self_hashed
    legacy = load_self_hashed(legacy_release_path, "dg05_production_release_manifest_v2")
    # This replay validates all legacy implementation and root bindings without
    # receiving, reading, or transferring any historical user approval.
    base = initialize_production_release_v5(
        release_manifest_path=legacy_release_path, repository_root=repository_root,
        predecessor_v4_manifest_path=predecessor_v4_manifest_path,
        predecessor_v4_closure_path=predecessor_v4_closure_path,
        expected_release_hash=legacy["self_hash"],
        authority_mode="PREACCESS_FROZEN_KERNEL_REHEARSAL",
        expected_executable_version=legacy["executable_version"],
    )
    compatible = self_hashed({
        "schema": "dg05_production_chain_state_v2",
        "state": "APPROVED_PRODUCTION_RELEASE_INITIALIZED",
        "release_manifest_hash": legacy["self_hash"],
        "predecessor_v4_manifest_hash": base["predecessor_v4_manifest_hash"],
        "authority_mode": "PRODUCTION",
        "data_access_mode": "PROTECTED_DATA_ACCESS_REQUIRES_EXACT_USER_APPROVAL",
        "execution_kernel_identity": base["execution_kernel_identity"],
        "protected_access_authorized": True,
        "implementation_authority_hash": base["implementation_authority_hash"],
        "transitive_implementation_authority_hash": base["transitive_implementation_authority_hash"],
        "nested_authority_hash": base["nested_authority_hash"],
        "attack_test_accesses": 0, "label_scenario_accesses": 0,
        "outer_v11r1_release_hash": outer_release["self_hash"],
        "outer_v11r1_state_hash": outer_state["self_hash"],
        "not_standalone_release": True, "not_user_approvable": True,
        "independent_protected_access_authority": False,
        "access_authority": "OUTER_V11R1_APPROVAL_IS_SOLE_ACCESS_AUTHORITY",
    })
    receipt = self_hashed({
        "schema": "dg05_v11r1_to_v5_compatibility_state_receipt_v1", "status": "PASS",
        "outer_release_hash": outer_release["self_hash"], "outer_state_hash": outer_state["self_hash"],
        "legacy_release_hash": legacy["self_hash"], "compatibility_state_hash": compatible["self_hash"],
        "historical_v10_approval_reused": False,
        "outer_v11r1_approval_sole_authority": True,
    })
    return compatible, receipt


__all__ = ["DG05V11R1V5CompatibilityError", "derive_v5_compatibility_state_v11r1"]
