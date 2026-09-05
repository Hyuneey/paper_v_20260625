"""Pre-access initializer for the additive DG-05 executable V3 package."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping


class DG05ExecutableV3Error(ValueError):
    pass


_V2_NESTED_REPOSITORY_PATHS = {
    "detector_registry": "research_control_center/validation_v2/dg05_exec_closure/DETECTOR_SUBAUTHORITY_REGISTRY_V1.json",
    "dispatch_registry": "research_control_center/validation_v2/dg05_exec_closure/METHOD_DISPATCH_REGISTRY_V1.json",
    "full_process_scope": "research_control_center/validation_v2/dg05_exec_closure/FULL_PROCESS_SCOPE_AUTHORITY_V1.json",
    "p1_custodian_v3": "research_control_center/validation_v2/dg05_exec_closure/P1_ELIGIBILITY_CUSTODIAN_V3.json",
    "portfolio:00": "research_control_center/validation_v2/xver_normal/HAI22_T0_PORTFOLIO_AUTHORITY_V1.json",
    "portfolio:01": "research_control_center/validation_v2/xver_normal/provider_execution_v1/HAI21_T2_PORTFOLIO_AUTHORITY_V1.json",
    "portfolio:02": "research_control_center/validation_v2/xver_normal/provider_execution_v1/HAI22_T2_PORTFOLIO_AUTHORITY_V1.json",
    "portfolio:03": "research_control_center/validation_v2/dg04_xver_prep/T2_HELDOUT_CANDIDATE_PORTFOLIO_V1.json",
    "portfolio:04": "research_control_center/validation_v2/dg04_xver_prep/T0_HELDOUT_CANDIDATE_PORTFOLIO_V1.json",
    "portfolio:05": "research_control_center/validation_v2/core_v2a/authorities/V2A_FORMAL_V4_PORTFOLIO_AUTHORITY.json",
    "portfolio:06": "research_control_center/validation_v2/xver_normal/HAI21_T0_PORTFOLIO_AUTHORITY_V1.json",
    "rule_runtime_registry": "research_control_center/validation_v2/dg05_exec_closure/RULE_RUNTIME_SUBAUTHORITY_REGISTRY_V1.json",
    "scientific:attack_file_census": "research_control_center/validation_v2/multipanel_pre_dg05/ATTACK_FILE_CENSUS_AUTHORITIES_V1.json",
    "scientific:etapr": "research_control_center/validation_v2/multipanel_pre_dg05/ETAPR_MULTIFILE_CONFORMANCE_V2.json",
    "scientific:feature_allowlist_bundle": "research_control_center/validation_v2/multipanel_pre_dg05/ATTACK_FEATURE_ALLOWLIST_AUTHORITIES_V1.json",
    "scientific:fusion": "research_control_center/validation_v2/multipanel_pre_dg05/MULTIPANEL_METHOD_BUNDLE_AUTHORITY_V1.json",
    "scientific:global_custody_v2": "research_control_center/validation_v2/multipanel_pre_dg05/GLOBAL_PREDICTION_CUSTODY_AUTHORITY_V2.json",
    "scientific:method_bundle": "research_control_center/validation_v2/multipanel_pre_dg05/MULTIPANEL_METHOD_BUNDLE_AUTHORITY_V1.json",
    "scientific:metric": "research_control_center/validation_v2/multipanel_pre_dg05/MULTIPANEL_METRIC_AUTHORITY_V2.json",
    "scientific:p1_mapping_bundle_v2": "research_control_center/validation_v2/multipanel_pre_dg05/P1_MAPPING_AUTHORITIES_V1.json",
    "scientific:scientific_preregistration": "research_control_center/validation_v2/multipanel_pre_dg05/MULTIPANEL_PREREGISTRATION_V2.json",
    "scientific:statistical": "research_control_center/validation_v2/multipanel_pre_dg05/STATISTICAL_ANALYSIS_CONTRACT_V2.json",
}


def predecessor_v2_nested_repository_paths_v1(repository_root: Path) -> dict[str, Path]:
    paths = {name: repository_root / relative for name, relative in _V2_NESTED_REPOSITORY_PATHS.items()}
    execution = repository_root / "src/paperworks/validation_v2/dg05_execution_closure_v1.py"
    for name in ("denominator_builder", "fusion_runtime", "global_freeze_builder", "global_manifest_builder",
                 "prediction_adapter", "projection_adapter", "result_builder", "scenario_builder",
                 "state_machine", "timestamp_builder"):
        paths[f"implementation:{name}"] = execution
    paths["implementation:label_custodian"] = repository_root / "src/paperworks/validation_v2/dg05_label_custodian_v1.py"
    paths["implementation:result_verifier"] = repository_root / "src/paperworks/validation_v2/dg05_result_oracle_v1.py"
    return paths


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def _load(path: Path, schema: str) -> dict[str, Any]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("ascii"))
    if raw != _canonical(value) + b"\n" or value.get("schema") != schema:
        raise DG05ExecutableV3Error("CANONICAL_SCHEMA_REPLAY_FAILED")
    body = {k: v for k, v in value.items() if k != "self_hash"}
    if value.get("self_hash") != sha256(_canonical(body)).hexdigest():
        raise DG05ExecutableV3Error("SELF_HASH_REPLAY_FAILED")
    return value


def _replay_predecessor_v2(*, manifest_path: Path, closure_path: Path,
                           bundle_path: Path,
                           nested_paths: Mapping[str, Path]) -> dict[str, Any]:
    manifest = _load(manifest_path, "dg05_executable_authority_manifest_v1")
    closure = _load(closure_path, "dg05_executable_closure_authority_v1")
    bundle = _load(bundle_path, "dg05_nested_authority_replay_bundle_v1")
    if closure.get("executable_manifest_hash") != manifest["self_hash"]:
        raise DG05ExecutableV3Error("PREDECESSOR_MANIFEST_CLOSURE_MISMATCH")
    if manifest.get("nested_authority_replay_bundle_hash") != bundle["self_hash"]:
        raise DG05ExecutableV3Error("PREDECESSOR_NESTED_BUNDLE_MISMATCH")
    entries = {row["logical_name"]: row for row in bundle.get("entries", ())}
    if set(nested_paths) != set(entries):
        raise DG05ExecutableV3Error("PREDECESSOR_NESTED_PATH_CENSUS_MISMATCH")
    implementation_count = 0
    for logical_name, row in entries.items():
        path = nested_paths[logical_name]
        raw = path.read_bytes()
        if path.is_symlink() or sha256(raw).hexdigest() != row["artifact_byte_hash"]:
            raise DG05ExecutableV3Error(f"PREDECESSOR_NESTED_BYTE_MISMATCH:{logical_name}")
        schema = row.get("expected_schema")
        if schema is None:
            if not logical_name.startswith("implementation:"):
                raise DG05ExecutableV3Error("UNSCHEMATIZED_NONIMPLEMENTATION_AUTHORITY")
            if row["expected_authority_hash"] != row["artifact_byte_hash"]:
                raise DG05ExecutableV3Error("IMPLEMENTATION_AUTHORITY_BYTE_MISMATCH")
            implementation_count += 1
            continue
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DG05ExecutableV3Error("PREDECESSOR_NESTED_JSON_REQUIRED") from exc
        if value.get("schema") != schema and value.get("artifact_type") != schema:
            raise DG05ExecutableV3Error(f"PREDECESSOR_NESTED_SCHEMA_MISMATCH:{logical_name}")
        if raw != _canonical(value) + b"\n":
            raise DG05ExecutableV3Error(f"PREDECESSOR_NESTED_CANONICAL_MISMATCH:{logical_name}")
        authority_field = row.get("authority_field") or "self_hash"
        if value.get(authority_field) != row["expected_authority_hash"]:
            raise DG05ExecutableV3Error(f"PREDECESSOR_NESTED_AUTHORITY_MISMATCH:{logical_name}")
    return {"manifest_hash": manifest["self_hash"], "closure_hash": closure["self_hash"],
            "nested_bundle_hash": bundle["self_hash"], "nested_artifact_count": len(entries),
            "implementation_byte_count": implementation_count}


def initialize_dg05_executable_v3_preaccess(*, manifest_path: Path, closure_path: Path,
                                            nested_paths: Mapping[str, tuple[Path, str]],
                                            predecessor_manifest_path: Path,
                                            predecessor_closure_path: Path,
                                            predecessor_bundle_path: Path,
                                            predecessor_nested_paths: Mapping[str, Path],
                                            approved_manifest_hash: str | None) -> dict[str, Any]:
    """Replay V3 without granting attack access; approval must be a future hash."""
    manifest = _load(manifest_path, "dg05_executable_authority_manifest_v3")
    closure = _load(closure_path, "dg05_executable_closure_authority_v3")
    if manifest["self_hash"] != closure["executable_manifest_hash"]:
        raise DG05ExecutableV3Error("MANIFEST_CLOSURE_BINDING_MISMATCH")
    predecessor = _replay_predecessor_v2(
        manifest_path=predecessor_manifest_path, closure_path=predecessor_closure_path,
        bundle_path=predecessor_bundle_path, nested_paths=predecessor_nested_paths)
    if (predecessor["manifest_hash"] != manifest.get("predecessor_v2_manifest_hash")
            or predecessor["closure_hash"] != manifest.get("predecessor_v2_closure_hash")
            or predecessor["nested_bundle_hash"] != manifest.get("predecessor_v2_nested_bundle_hash")):
        raise DG05ExecutableV3Error("PREDECESSOR_V2_BINDING_MISMATCH")
    expected = {
        "contract": manifest["metric_surface_contract_hash"],
        "expected": manifest["expected_result_surface_hash"],
        "builder_support": manifest["builder_support_hash"],
        "verifier_support": manifest["verifier_support_hash"],
        "completeness": manifest["completeness_oracle_authority_hash"],
        "coverage": manifest["coverage_matrix_hash"],
        "mutation": manifest["mutation_receipt_hash"],
        "rehearsal": manifest["synthetic_rehearsal_hash"],
    }
    if set(nested_paths) != set(expected):
        raise DG05ExecutableV3Error("NESTED_AUTHORITY_CENSUS_MISMATCH")
    replayed = {}
    for key, (path, schema) in nested_paths.items():
        value = _load(path, schema)
        if value["self_hash"] != expected[key]:
            raise DG05ExecutableV3Error(f"NESTED_AUTHORITY_MISMATCH:{key}")
        replayed[key] = value["self_hash"]
    if approved_manifest_hash is None:
        status = "DG05_V3_USER_REAPPROVAL_REQUIRED"
        attack_access_authorized = False
    elif approved_manifest_hash != manifest["self_hash"]:
        raise DG05ExecutableV3Error("EXACT_V3_APPROVAL_HASH_REQUIRED")
    else:
        status = "DG05_V3_APPROVAL_HASH_REPLAYED"
        attack_access_authorized = True
    body = {"schema": "dg05_executable_v3_preaccess_state_v1", "state": status,
            "executable_manifest_hash": manifest["self_hash"], "closure_hash": closure["self_hash"],
            "nested_authorities": replayed, "predecessor_v2_replay": predecessor,
            "attack_access_authorized": attack_access_authorized,
            "attack_test_accesses": 0, "label_scenario_accesses": 0}
    return {**body, "self_hash": sha256(_canonical(body)).hexdigest()}


__all__ = ["DG05ExecutableV3Error", "initialize_dg05_executable_v3_preaccess",
           "predecessor_v2_nested_repository_paths_v1"]
