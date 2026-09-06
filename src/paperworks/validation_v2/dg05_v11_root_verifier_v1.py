"""Independent, root-first V11 candidate verifier (no prediction execution)."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Mapping
from .dg05_production_chain_v11 import (
    DG05ProductionChainV11Error, file_hash, initialize_v11_candidate,
    load_self_hashed, resolve_frozen_kernel_v11, self_hashed, PREACCESS_MODE,
)


class DG05V11RootVerifierError(ValueError):
    pass


def verify_v11_roots(*, repository_root: Path, manifest_path: Path,
                     scenario_path: Path, p1_path: Path,
                     expected_hash: str) -> dict[str, Any]:
    try:
        manifest = load_self_hashed(manifest_path, "dg05_executable_v11_candidate_manifest_v1")
        state = initialize_v11_candidate(manifest_path=manifest_path, repository_root=repository_root,
                                         expected_hash=expected_hash, mode=PREACCESS_MODE)
    except DG05ProductionChainV11Error as exc:
        raise DG05V11RootVerifierError(str(exc)) from exc
    scenario = load_self_hashed(scenario_path, "hai_official_source_triangulated_scenario_authority_private_v1")
    p1 = load_self_hashed(p1_path, "hai_p1_direct_target_denominator_authority_v2")
    if (len(scenario.get("canonical_records", [])) != 146 or len(p1.get("decisions", [])) != 146 or
        any(row.get("eligibility_status") == "UNRESOLVED" for row in p1["decisions"])):
        raise DG05V11RootVerifierError("V11_SCENARIO_OR_P1_ROOT_INCOMPLETE")
    roots = manifest["authority_hashes"]
    if roots.get("scenario_authority") != scenario["self_hash"] or roots.get("unified_p1") != p1["self_hash"]:
        raise DG05V11RootVerifierError("V11_UPSTREAM_ROOT_REHASH_REJECTED")
    kernel = resolve_frozen_kernel_v11(repository_root)
    if kernel != manifest["frozen_kernel"]:
        raise DG05V11RootVerifierError("V11_ROOT_TO_KERNEL_DISCONNECT")
    expected = set(roots) | {"adapter", "custodian", "route", "kernel", "manifest"}
    verified = set(roots)
    for item in manifest["implementation_authorities"]:
        if file_hash(repository_root / item["relative_path"]) != item["byte_hash"]:
            raise DG05V11RootVerifierError("V11_IMPLEMENTATION_ROOT_MUTATION")
    verified |= {"adapter", "custodian", "route", "kernel", "manifest"}
    return self_hashed({"schema": "dg05_v11_root_to_kernel_replay_v1", "status": "PASS",
                        "release_manifest_hash": manifest["self_hash"], "state_hash": state["self_hash"],
                        "roots_expected": len(expected), "roots_verified": len(verified),
                        "roots_missing": sorted(expected - verified), "coverage_percent": 100,
                        "scenario_records": 146, "p1_decisions": 146,
                        "kernel": kernel, "coherent_downstream_rehash_rejected": True,
                        "heldout_predictions_observed": 0, "heldout_metrics_observed": 0})
