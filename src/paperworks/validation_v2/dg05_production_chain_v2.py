"""Prospective V5 release authority with separate data and kernel modes."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .dg05_preaccess_kernel_v5 import (
    PREACCESS_DATA_ACCESS_MODE_V5,
    PREACCESS_EXECUTION_MODE_V5,
)
from .dg05_production_chain_v1 import (
    REQUIRED_IMPLEMENTATION_ROLES_V4,
    REQUIRED_NESTED_AUTHORITY_ROLES_V1,
    ProductionReleaseImplementationV1,
    digest_v1,
    file_sha256_v1,
    load_canonical_self_hashed_v1,
    self_hashed_v1,
)


class DG05ProductionChainV2Error(ValueError):
    pass


REQUIRED_IMPLEMENTATION_ROLES_V5 = REQUIRED_IMPLEMENTATION_ROLES_V4 | frozenset(
    {
        "preaccess_kernel_adapter",
        "production_kernel_parity",
        "root_to_result_verifier",
        "projection_parser",
        "release_freezer_core",
        "connected_rehearsal_support",
        "historical_authority_factory",
        "frozen_asset_loader",
        "upstream_intermediate_verifier",
        "metric_surface_core",
        "multipanel_custody_contract",
        "etapr_exchange",
        "formal_v4_runtime",
        "metric_oracle_core",
        "multipanel_etapr",
        "multipanel_metrics",
        "external_detector_kernel",
        "numeric_binding_contract",
        "exp03b_contract",
    }
)


def _sha(value: Any, code: str) -> str:
    if type(value) is not str or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise DG05ProductionChainV2Error(code)
    return value


def build_production_release_manifest_v5(
    *, repository_root: Path, predecessor_v4_manifest_path: Path,
    predecessor_v4_closure_path: Path, implementation_paths: Mapping[str, Path],
    nested_authority_hashes: Mapping[str, str], semantic_binding_hash: str,
    normal_burden_source_registry_hash: str, source_commit: str,
    scientific_preregistration_hash: str, historical_execution_kernel_hash: str,
    executable_version: str = "DG05_EXECUTABLE_V5",
    superseded_candidate_hash: str | None = None,
) -> dict[str, Any]:
    predecessor = load_canonical_self_hashed_v1(
        predecessor_v4_manifest_path, "dg05_production_release_manifest_v1")
    closure = load_canonical_self_hashed_v1(
        predecessor_v4_closure_path, "dg05_executable_closure_authority_v4")
    if closure.get("executable_manifest_hash") != predecessor["self_hash"]:
        raise DG05ProductionChainV2Error("PREDECESSOR_V4_BINDING_MISMATCH")
    root = repository_root.resolve()
    implementations = []
    for logical_name, path in sorted(implementation_paths.items()):
        resolved = path.resolve()
        if root not in resolved.parents or not resolved.is_file() or resolved.is_symlink():
            raise DG05ProductionChainV2Error("IMPLEMENTATION_PATH_OUTSIDE_REPOSITORY")
        implementations.append(ProductionReleaseImplementationV1(
            logical_name, resolved.relative_to(root).as_posix(), file_sha256_v1(resolved)).document())
    if {row["logical_name"] for row in implementations} != REQUIRED_IMPLEMENTATION_ROLES_V5:
        raise DG05ProductionChainV2Error("COMPLETE_V5_IMPLEMENTATION_CENSUS_REQUIRED")
    if set(nested_authority_hashes) != REQUIRED_NESTED_AUTHORITY_ROLES_V1:
        raise DG05ProductionChainV2Error("COMPLETE_NESTED_AUTHORITY_CENSUS_REQUIRED")
    for value in (
        semantic_binding_hash, normal_burden_source_registry_hash,
        scientific_preregistration_hash, historical_execution_kernel_hash,
        *nested_authority_hashes.values(),
    ):
        _sha(value, "SHA256_AUTHORITY_REQUIRED")
    if type(source_commit) is not str or len(source_commit) != 40:
        raise DG05ProductionChainV2Error("SOURCE_COMMIT_REQUIRED")
    if executable_version not in {"DG05_EXECUTABLE_V5", "DG05_EXECUTABLE_V6", "DG05_EXECUTABLE_V7"}:
        raise DG05ProductionChainV2Error("SUPPORTED_EXECUTABLE_VERSION_REQUIRED")
    if executable_version in {"DG05_EXECUTABLE_V6", "DG05_EXECUTABLE_V7"}:
        _sha(superseded_candidate_hash, "SUPERSEDED_V5_CANDIDATE_HASH_REQUIRED")
    elif superseded_candidate_hash is not None:
        raise DG05ProductionChainV2Error("V5_CANNOT_SUPERSEDE_ITSELF")
    return self_hashed_v1({
        "schema": "dg05_production_release_manifest_v2",
        "executable_version": executable_version,
        "approval_status": "DG05_PRODUCTION_RELEASE_USER_REAPPROVAL_REQUIRED",
        "readiness": "READY_FOR_USER_REAPPROVAL",
        "predecessor_v4_manifest_hash": predecessor["self_hash"],
        "predecessor_v4_closure_hash": closure["self_hash"],
        "semantic_binding_status": "APPROVED",
        "semantic_binding_hash": semantic_binding_hash,
        "normal_burden_source_status": "COMPLETE",
        "normal_burden_source_registry_hash": normal_burden_source_registry_hash,
        "scientific_preregistration_hash": scientific_preregistration_hash,
        "historical_execution_kernel_hash": historical_execution_kernel_hash,
        "superseded_candidate_hash": superseded_candidate_hash,
        "superseded_candidate_disposition": (
            "UNAPPROVED_FAILED_INDEPENDENT_RELEASE_QUALIFICATION"
            if superseded_candidate_hash is not None else None
        ),
        "nested_authority_hashes": dict(sorted(nested_authority_hashes.items())),
        "implementation_authorities": implementations,
        "decision_binding": "DEC-031",
        "source_commit": source_commit,
        "attack_test_accesses": 0,
        "label_scenario_accesses": 0,
        "provider_calls": 0,
        "credential_reads": 0,
    })


def initialize_production_release_v5(
    *, release_manifest_path: Path, repository_root: Path,
    predecessor_v4_manifest_path: Path, predecessor_v4_closure_path: Path,
    expected_release_hash: str, authority_mode: str,
    user_approved_release_hash: str | None = None,
    expected_executable_version: str = "DG05_EXECUTABLE_V5",
) -> dict[str, Any]:
    release = load_canonical_self_hashed_v1(
        release_manifest_path, "dg05_production_release_manifest_v2")
    predecessor = load_canonical_self_hashed_v1(
        predecessor_v4_manifest_path, "dg05_production_release_manifest_v1")
    closure = load_canonical_self_hashed_v1(
        predecessor_v4_closure_path, "dg05_executable_closure_authority_v4")
    if (
        release.get("self_hash") != expected_release_hash
        or release.get("predecessor_v4_manifest_hash") != predecessor["self_hash"]
        or release.get("predecessor_v4_closure_hash") != closure["self_hash"]
        or closure.get("executable_manifest_hash") != predecessor["self_hash"]
        or release.get("executable_version") != expected_executable_version
        or expected_executable_version not in {"DG05_EXECUTABLE_V5", "DG05_EXECUTABLE_V6", "DG05_EXECUTABLE_V7"}
        or release.get("readiness") != "READY_FOR_USER_REAPPROVAL"
    ):
        raise DG05ProductionChainV2Error("V5_RELEASE_ROOT_REPLAY_FAILED")
    root = repository_root.resolve()
    names = []
    for row in release.get("implementation_authorities", ()):
        path = (root / row["relative_path"]).resolve()
        if root not in path.parents or not path.is_file() or path.is_symlink() or file_sha256_v1(path) != row["byte_hash"]:
            raise DG05ProductionChainV2Error("V5_IMPLEMENTATION_BYTE_REPLAY_FAILED")
        names.append(row["logical_name"])
    if set(names) != REQUIRED_IMPLEMENTATION_ROLES_V5 or len(names) != len(set(names)):
        raise DG05ProductionChainV2Error("V5_IMPLEMENTATION_CENSUS_FAILED")
    if authority_mode == PREACCESS_EXECUTION_MODE_V5:
        state = "PREACCESS_FROZEN_KERNEL_RELEASE_INITIALIZED"
        protected = False
        data_access = PREACCESS_DATA_ACCESS_MODE_V5
    elif authority_mode == "PRODUCTION":
        if user_approved_release_hash != release["self_hash"]:
            raise DG05ProductionChainV2Error("EXACT_V5_USER_APPROVAL_REQUIRED")
        state = "APPROVED_PRODUCTION_RELEASE_INITIALIZED"
        protected = True
        data_access = "PROTECTED_DATA_ACCESS_REQUIRES_EXACT_USER_APPROVAL"
    else:
        raise DG05ProductionChainV2Error("V5_AUTHORITY_MODE_REQUIRED")
    return self_hashed_v1({
        "schema": "dg05_production_chain_state_v2",
        "state": state,
        "release_manifest_hash": release["self_hash"],
        "predecessor_v4_manifest_hash": predecessor["self_hash"],
        "authority_mode": authority_mode,
        "data_access_mode": data_access,
        "execution_kernel_identity": "FROZEN_PRODUCTION_SCIENTIFIC_KERNEL_V1",
        "protected_access_authorized": protected,
        "implementation_authority_hash": digest_v1(release["implementation_authorities"]),
        "nested_authority_hash": digest_v1(release["nested_authority_hashes"]),
        "attack_test_accesses": 0,
        "label_scenario_accesses": 0,
    })


__all__ = [
    "DG05ProductionChainV2Error",
    "REQUIRED_IMPLEMENTATION_ROLES_V5",
    "build_production_release_manifest_v5",
    "initialize_production_release_v5",
]
