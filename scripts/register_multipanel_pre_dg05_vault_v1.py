"""Register private pre-DG05 custody without publishing paths or payloads."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from paperworks.validation_v2.exp03b_contract_v1 import require
from paperworks.validation_v2.exp03b_custody_v1 import publish, replay, seal
from xver_execution_common import PUB, ROOT, private_root, sha256_file


PUBLIC = ROOT / "research_control_center/validation_v2/multipanel_pre_dg05"
TASK_ID = "MULTIPANEL-PRE-DG05-FREEZE-001"
FUTURE_NAMESPACES = (
    "ATTACK_FEATURE_ONLY_PROJECTIONS_AFTER_DG05",
    "HAI23_TEST2_ALL_METHOD_PREDICTIONS",
    "HAI22_ALL_METHOD_PREDICTIONS",
    "HAI21_ALL_METHOD_PREDICTIONS",
    "GLOBAL_PREDICTION_MANIFEST",
    "ONE_SHOT_LABEL_SCENARIO_LEASE",
    "METHOD_BLIND_P1_ELIGIBILITY",
    "RESULT_AND_INDEPENDENT_QA_ARTIFACTS",
)


def document(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    replay(value)
    return value


def main() -> None:
    common = Path(
        subprocess.check_output(
            ["git", "rev-parse", "--git-common-dir"], cwd=ROOT, text=True
        ).strip()
    ).resolve()
    vault = common.parent.parent / "paper_v_20260625_private_vault"
    require(vault.is_dir() and not vault.is_symlink(), "EXISTING_PRIVATE_VAULT")

    parent_path = vault / "xver-t2-provider-exec-001/TASK_PRIVATE_VAULT_MANIFEST_V1.json"
    parent = document(parent_path)
    require(
        parent["storage_policy"] == "SINGLE_COPY_LOCAL_ONLY"
        and parent["second_copy_verified"] is False,
        "PARENT_BACKUP_STATUS",
    )

    detector_result = document(PUBLIC / "DETECTOR_EXECUTION_RESULT_V1.json")
    detector_root = private_root() / "multipanel_pre_dg05_v1"
    expected = ("HAI22_PCA.pkl", "HAI22_IF.pkl", "HAI21_PCA.pkl", "HAI21_IF.pkl")
    records = []
    for name in expected:
        path = detector_root / name
        require(path.is_file() and not path.is_symlink(), "PRIVATE_DETECTOR_OBJECT")
        require(path.resolve().is_relative_to(private_root().resolve()), "PRIVATE_NAMESPACE")
        records.append(
            {
                "path": str(path.resolve()),
                "symbolic_id": f"multipanel_pre_dg05_v1/{name}",
                "kind": "EXTERNAL_NORMAL_ONLY_DETECTOR_AUTHORITY",
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )

    authority_names = (
        "HAI23_DETECTOR_PRIVATE_HASH_BINDING_V1.json",
        "HAI23_DETECTOR_REPLAY_AUTHORITY_V1.json",
        "HAI22_DETECTOR_AUTHORITY_V1.json",
        "HAI21_DETECTOR_AUTHORITY_V1.json",
        "MULTIPANEL_METHOD_BUNDLE_AUTHORITY_V1.json",
        "MULTIPANEL_METRIC_AUTHORITY_V1.json",
        "P1_ELIGIBILITY_CUSTODIAN_AUTHORITY_V1.json",
        "GLOBAL_PREDICTION_CUSTODY_AUTHORITY_V1.json",
        "STATISTICAL_ANALYSIS_CONTRACT_V1.json",
        "MULTIPANEL_PREREGISTRATION_V1.json",
    )
    public_authorities = []
    for name in authority_names:
        item = document(PUBLIC / name)
        public_authorities.append({"relative_authority": name, "self_hash": item["self_hash"]})

    manifest = seal(
        {
            "schema": "task_private_vault_multipanel_pre_dg05_v2",
            "task": TASK_ID,
            "parent_manifest_hash": parent["self_hash"],
            "records": records,
            "public_authorities": public_authorities,
            "future_namespaces": list(FUTURE_NAMESPACES),
            "future_namespace_status": "PROSPECTIVE_NOT_MATERIALIZED",
            "detector_authority_hashes": detector_result["authorities"],
            "attack_accesses": 0,
            "test_accesses": 0,
            "label_or_scenario_accesses": 0,
            "provider_calls": 0,
            "storage_policy": "SINGLE_COPY_LOCAL_ONLY",
            "second_copy_verified": False,
        }
    )
    destination = vault / "multipanel-pre-dg05-freeze-001/TASK_PRIVATE_VAULT_MANIFEST_V2.json"
    publish(destination, manifest)
    restored = document(destination)
    require(restored == manifest, "PRIVATE_MANIFEST_RESTORE")
    for row in restored["records"]:
        require(sha256_file(Path(row["path"])) == row["sha256"], "PRIVATE_OBJECT_RESTORE")

    index = seal(
        {
            "schema": "public_private_multipanel_pre_dg05_index_v2",
            "task": TASK_ID,
            "private_manifest_hash": manifest["self_hash"],
            "parent_manifest_hash": parent["self_hash"],
            "actual_private_record_count": len(records),
            "prospective_namespace_count": len(FUTURE_NAMESPACES),
            "prospective_namespace_status": "NOT_MATERIALIZED_PRE_DG05",
            "public_authority_count": len(public_authorities),
            "storage_policy": "SINGLE_COPY_LOCAL_ONLY",
            "second_copy_verified": False,
            "restore_read_hash_smoke": "PASS",
            "private_paths_published": 0,
            "private_values_published": 0,
            "attack_accesses": 0,
            "test_accesses": 0,
            "label_or_scenario_accesses": 0,
            "provider_calls": 0,
        }
    )
    publish(PUBLIC / "PUBLIC_PRIVATE_MULTIPANEL_INDEX_V2.json", index)
    print(
        json.dumps(
            {
                "status": "PRIVATE_VAULT_RESTORE_PASS",
                "actual_private_records": len(records),
                "prospective_namespaces": len(FUTURE_NAMESPACES),
                "index_hash": index["self_hash"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
