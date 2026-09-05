"""Register prospective DG05 execution namespaces without real attack artifacts."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from paperworks.validation_v2.exp03b_contract_v1 import require
from paperworks.validation_v2.exp03b_custody_v1 import publish, replay, seal


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "research_control_center/validation_v2/dg05_exec_closure"
AUTHORITY_NAMES = (
    "DG05_EXECUTABLE_AUTHORITY_MANIFEST_V1.json",
    "FULL_PROCESS_SCOPE_AUTHORITY_V1.json",
    "P1_ELIGIBILITY_CUSTODIAN_V3.json",
    "DETECTOR_SUBAUTHORITY_REGISTRY_V1.json",
    "RULE_RUNTIME_SUBAUTHORITY_REGISTRY_V1.json",
    "METHOD_DISPATCH_REGISTRY_V1.json",
    "NESTED_AUTHORITY_REPLAY_BUNDLE_V1.json",
    "EXECUTION_STATE_MACHINE_AUTHORITY_V1.json",
    "EXPECTED_PREDICTION_CELL_CENSUS_AUTHORITY_V1.json",
    "PRODUCTION_ADAPTER_AUTHORITY_V1.json",
    "SYNTHETIC_DG05_REHEARSAL_V1.json",
    "INDEPENDENT_QA_AUTHORITY_V1.json",
    "DG05_EXECUTABLE_CLOSURE_AUTHORITY_V1.json",
)
FUTURE_NAMESPACES = (
    "PHYSICAL_FILE_AUTHORITIES_AFTER_DG05_V2",
    "TIMESTAMP_AUTHORITIES_AFTER_DG05_V2",
    "FEATURE_PROJECTION_AUTHORITIES_AFTER_DG05_V2",
    "PREDICTION_ARTIFACTS_AFTER_DG05_V2",
    "PREDICTION_AND_TRACE_RECEIPTS_AFTER_DG05_V2",
    "GLOBAL_PREDICTION_FREEZE_AFTER_DG05_V2",
    "LABEL_SCENARIO_LEASE_AFTER_GLOBAL_FREEZE",
    "SCENARIO_AUTHORITIES_AFTER_VALID_LEASE",
    "DENOMINATOR_AUTHORITIES_AFTER_VALID_LEASE",
    "RESULT_AUTHORITY_BYTES_AFTER_VALID_LEASE",
    "RESULT_INTEGRITY_RECEIPTS_AFTER_VALID_LEASE",
)


def document(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    replay(value)
    return value


def main() -> None:
    common = Path(
        subprocess.check_output(["git", "rev-parse", "--git-common-dir"], cwd=ROOT, text=True).strip()
    ).resolve()
    vault = common.parent.parent / "paper_v_20260625_private_vault"
    require(vault.is_dir() and not vault.is_symlink(), "EXISTING_PRIVATE_VAULT")
    parent_path = vault / "multipanel-pre-dg05-freeze-001/TASK_PRIVATE_VAULT_MANIFEST_V7.json"
    parent = document(parent_path)
    require(parent["self_hash"] == "8a377204b8d0e7e0213af8e1311de2d32d0179f5d8be1e41e48b32f543ff1ce8", "PARENT_MANIFEST")
    require(parent["storage_policy"] == "SINGLE_COPY_LOCAL_ONLY" and parent["second_copy_verified"] is False, "BACKUP_STATUS")

    public_authorities = []
    for name in AUTHORITY_NAMES:
        item = document(PUBLIC / name)
        public_authorities.append({"relative_authority": name, "self_hash": item["self_hash"]})

    prior_path = vault / "dg05-exec-authority-closure-001/TASK_PRIVATE_VAULT_MANIFEST_V2.json"
    prior = document(prior_path)
    require(prior["self_hash"] == "15e3e1a86b3ecb5997a9c53ca3c1e652e474797697c85cf6dc770e545ee6be93", "PRIOR_DG05_MANIFEST")
    manifest = seal({
        "schema": "task_private_vault_dg05_exec_closure_v3",
        "task": "DG05-EXEC-AUTHORITY-CLOSURE-001",
        "parent_manifest_hash": parent["self_hash"],
        "supersedes_private_manifest_hash": prior["self_hash"],
        "records": [],
        "public_authorities": public_authorities,
        "future_namespaces": list(FUTURE_NAMESPACES),
        "future_namespace_status": "PROSPECTIVE_NOT_MATERIALIZED_DG05_V2_REQUIRED",
        "real_attack_artifact_count": 0,
        "real_label_or_scenario_artifact_count": 0,
        "real_eligibility_artifact_count": 0,
        "provider_calls": 0,
        "storage_policy": "SINGLE_COPY_LOCAL_ONLY",
        "second_copy_verified": False,
    })
    destination = vault / "dg05-exec-authority-closure-001/TASK_PRIVATE_VAULT_MANIFEST_V3.json"
    publish(destination, manifest)
    require(document(destination) == manifest, "PRIVATE_MANIFEST_RESTORE")

    index = seal({
        "schema": "public_private_dg05_execution_index_v3",
        "task": "DG05-EXEC-AUTHORITY-CLOSURE-001",
        "status": "PROSPECTIVE_NAMESPACES_REGISTERED_NO_REAL_ATTACK_ARTIFACTS",
        "parent_private_manifest_hash": parent["self_hash"],
        "supersedes_private_manifest_hash": prior["self_hash"],
        "supersedes_public_index_hash": "e86bee6e854ef974bf3f7f061c62779b7ab60e7a53818ac9673e568da6d532b4",
        "private_manifest_hash": manifest["self_hash"],
        "public_authority_count": len(public_authorities),
        "prospective_namespace_count": len(FUTURE_NAMESPACES),
        "prospective_namespace_status": "NOT_MATERIALIZED_DG05_V2_REQUIRED",
        "real_attack_artifact_count": 0,
        "real_label_or_scenario_artifact_count": 0,
        "real_eligibility_artifact_count": 0,
        "private_paths_published": 0,
        "private_values_published": 0,
        "provider_calls": 0,
        "restore_read_hash_smoke": "PASS",
        "storage_policy": "SINGLE_COPY_LOCAL_ONLY",
        "second_copy_verified": False,
    })
    publish(PUBLIC / "PUBLIC_PRIVATE_DG05_EXECUTION_INDEX_V3.json", index)
    print(json.dumps({"status": "PRIVATE_VAULT_RESTORE_PASS", "private_manifest_hash": manifest["self_hash"], "index_hash": index["self_hash"]}, sort_keys=True))


if __name__ == "__main__":
    main()
