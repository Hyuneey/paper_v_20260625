"""Register private provider and post-provider artifacts without publishing paths."""
import json
import subprocess
from pathlib import Path

from xver_execution_common import ROOT, PUB, private_root, document, publish, seal, require, sha256_file


PUBLIC = PUB / "provider_execution_v1"


def main():
    result = document(PUBLIC / "XVER_T2_PROVIDER_EXECUTION_RESULT_V1.json")
    common = Path(subprocess.check_output(["git", "rev-parse", "--git-common-dir"], cwd=ROOT, text=True).strip()).resolve()
    vault = common.parent.parent / "paper_v_20260625_private_vault"
    parent_path = vault / "hai-xver-normal-prep-001/TASK_PRIVATE_VAULT_MANIFEST_V2.json"
    parent = document(parent_path)
    require(parent["storage_policy"] == "SINGLE_COPY_LOCAL_ONLY" and not parent["second_copy_verified"], "BACKUP_STATUS")
    for row in parent["records"]:
        require(sha256_file(Path(row["path"])) == row["sha256"], "PARENT_PRIVATE_REPLAY")
    records = []
    for namespace in ("provider_t2_v1", "provider_t2_v2"):
        base = private_root() / namespace
        if not base.exists():
            continue
        for path in sorted(p for p in base.rglob("*") if p.is_file()):
            require(not path.is_symlink() and path.resolve().is_relative_to(private_root().resolve()), "PRIVATE_NAMESPACE")
            records.append({
                "path": str(path.resolve()), "symbolic_id": path.relative_to(private_root()).as_posix(),
                "kind": "ABORTED_PRETRANSPORT_RECEIPT" if namespace == "provider_t2_v1" else "XVER_T2_PROVIDER_OR_POSTPROVIDER_CUSTODY",
                "sha256": sha256_file(path), "bytes": path.stat().st_size,
            })
    require(len(records) > result["combined"]["calls"] * 3, "PRIVATE_PROVIDER_CUSTODY_INCOMPLETE")
    manifest = seal({
        "schema": "task_private_vault_xver_t2_execution_v1",
        "task": "XVER-T2-PROVIDER-EXEC-001", "parent_manifest_hash": parent["self_hash"],
        "records": records, "provider_calls": result["combined"]["calls"],
        "credential_dispatch_reads": result["combined"]["calls"], "attack_accesses": 0,
        "storage_policy": "SINGLE_COPY_LOCAL_ONLY", "second_copy_verified": False,
        "future_namespaces": ["MULTIPANEL_PREDICTIONS_AFTER_FREEZE", "SCENARIO_ELIGIBILITY_AFTER_DG05"],
    })
    destination = vault / "xver-t2-provider-exec-001/TASK_PRIVATE_VAULT_MANIFEST_V1.json"
    publish(destination, manifest)
    restored = document(destination)
    for row in restored["records"]:
        require(sha256_file(Path(row["path"])) == row["sha256"], "PRIVATE_RESTORE_HASH")
    index = seal({
        "schema": "public_xver_t2_execution_private_index_v1",
        "private_manifest_hash": manifest["self_hash"], "parent_manifest_hash": parent["self_hash"],
        "record_count": len(records), "provider_calls": result["combined"]["calls"],
        "credential_dispatch_reads": result["combined"]["calls"], "attack_accesses": 0,
        "storage_policy": "SINGLE_COPY_LOCAL_ONLY", "second_copy_verified": False,
        "restore_read_hash_smoke": "PASS", "private_paths_published": 0,
    })
    publish(PUBLIC / "PUBLIC_PRIVATE_T2_EXECUTION_INDEX_V1.json", index)
    print(json.dumps({"status": "PRIVATE_VAULT_RESTORE_PASS", "record_count": len(records), "index_hash": index["self_hash"]}))


if __name__ == "__main__":
    main()
