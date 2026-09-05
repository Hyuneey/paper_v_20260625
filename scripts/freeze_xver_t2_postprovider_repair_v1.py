"""Freeze a serialization-only post-provider replay repair."""
import json
from xver_execution_common import ROOT, PUB, document, head, publish, seal, require, sha256_file


def main():
    freeze = document(PUB / "provider_execution_v1/XVER_T2_PROVIDER_EXECUTION_FREEZE_V3.json")
    old_hash = freeze["implementation_hashes"]["scripts/finalize_xver_t2_provider_v1.py"]
    new_hash = sha256_file(ROOT / "scripts/finalize_xver_t2_provider_v1.py")
    require(old_hash != new_hash, "REPAIR_NOT_REQUIRED")
    value = seal({
        "schema": "xver_t2_postprovider_repair_v1",
        "status": "ENGINEERING_REPLAY_REPAIR_APPROVED_BY_TASK_FAILURE_POLICY",
        "provider_execution_freeze_hash": freeze["self_hash"],
        "provider_execution_authority_hash": freeze["self_hash"],
        "issue": "JSON_TUPLE_TO_ARRAY_CANONICALIZATION_COMPARISON",
        "old_finalizer_hash": old_hash,
        "new_finalizer_hash": new_hash,
        "source_commit": head(),
        "comparison_change": "PYTHON_NATIVE_EQUALITY_TO_CANONICAL_DIGEST_EQUALITY",
        "scientific_method_changed": False,
        "provider_outputs_changed": False,
        "provider_calls_added": 0,
        "attack_accesses": 0,
    })
    publish(PUB / "provider_execution_v1/XVER_T2_POSTPROVIDER_REPAIR_V1.json", value)
    print(json.dumps({"status": "POSTPROVIDER_REPAIR_FROZEN", "hash": value["self_hash"]}))


if __name__ == "__main__":
    main()
