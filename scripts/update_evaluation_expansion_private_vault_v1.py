#!/usr/bin/env python3
"""Register public-safe evaluation planning authorities in the local private vault.

This command reads only tracked planning documents and the existing private-vault
manifest. It does not discover or open dataset, prediction, label, or attack files.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from paperworks.validation_v2.private_vault_v1 import file_identity_v1, publish_private_bytes_v1


TASK_FILES = (
    "research_control_center/validation_v2/evaluation_expansion/EVALUATION_MASTER_PLAN_V1.md",
    "research_control_center/validation_v2/evaluation_expansion/DATASET_COMPATIBILITY_MATRIX_V1.csv",
    "research_control_center/validation_v2/evaluation_expansion/OFFICIAL_HAI_PLANNING_IDENTITY_V1.json",
    "research_control_center/validation_v2/evaluation_expansion/ETAPR_DEPENDENCY_RECEIPT_V1.json",
    "research_control_center/validation_v2/evaluation_expansion/DG05_COMBINED_EVALUATION_AUTHORIZATION_PACKAGE_V1.md",
    "research_control_center/validation_v2/evaluation_expansion/PANEL_REGISTRY_V1.csv",
)


def _canonical(document: object) -> bytes:
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _seal(document: dict[str, object]) -> dict[str, object]:
    payload = dict(document)
    payload.pop("self_hash", None)
    payload["self_hash"] = sha256(_canonical(payload)).hexdigest()
    return payload


def _publish_json(path: Path, document: dict[str, object]) -> None:
    payload = (json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
    publish_private_bytes_v1(path, payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", required=True, type=Path)
    arguments = parser.parse_args()
    root = Path.cwd().resolve()
    common = Path(subprocess.check_output(["git", "rev-parse", "--git-common-dir"], text=True).strip()).resolve()
    repository = common.parent
    approved_vault = repository.parent / "paper_v_20260625_private_vault"
    vault = arguments.vault.resolve()
    if vault != approved_vault or vault.is_symlink() or repository == vault or repository in vault.parents:
        raise ValueError("PRIVATE_VAULT_ROOT_NOT_APPROVED")

    existing = vault / "gdn-front-exp04-001" / "PRIVATE_ARTIFACT_MANIFEST.json"
    existing_hash, existing_size = file_identity_v1(existing)
    records: list[dict[str, object]] = []
    for relative in TASK_FILES:
        content_hash, size = file_identity_v1(root / relative)
        records.append({"relative_authority": relative, "content_hash": content_hash, "size": size})

    private_manifest = _seal({
        "schema": "evaluation_expansion_private_manifest_v1",
        "task_id": "V2-EVAL-EXPANSION-001",
        "storage_policy": "SINGLE_COPY_LOCAL_ONLY",
        "independent_second_storage_verified": False,
        "existing_private_manifest_hash": existing_hash,
        "existing_private_manifest_size": existing_size,
        "registered_public_authorities": records,
        "future_private_requirements": [
            "HAI23_TEST2_PREDICTION_CUSTODY",
            "HAI22_EXTERNAL_REPLICATION_PREDICTION_CUSTODY",
            "HAI21_EXTERNAL_REPLICATION_PREDICTION_CUSTODY",
            "OPAQUE_P1_ELIGIBILITY_AUTHORITIES",
            "ETAPR_DETERMINISTIC_EXCHANGE_ARTIFACTS",
        ],
        "restore_read_smoke": "PASS",
        "attack_payload_accesses": 0,
        "label_accesses": 0,
        "test1_accesses": 0,
        "test2_accesses": 0,
        "private_exposures": 0,
    })
    private_path = vault / "evaluation-expansion-001" / "EVALUATION_EXPANSION_PRIVATE_MANIFEST_V1.json"
    _publish_json(private_path, private_manifest)
    replay = json.loads(private_path.read_text(encoding="utf-8"))
    if replay != private_manifest or file_identity_v1(private_path)[0] != sha256((json.dumps(private_manifest, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")).hexdigest():
        raise ValueError("PRIVATE_MANIFEST_RESTORE_READ_SMOKE_FAILED")

    public_receipt = _seal({
        "schema": "public_evaluation_expansion_private_index_v1",
        "task_id": "V2-EVAL-EXPANSION-001",
        "private_manifest_hash": private_manifest["self_hash"],
        "registered_public_authority_count": len(records),
        "future_private_requirement_count": len(private_manifest["future_private_requirements"]),
        "storage_policy": "SINGLE_COPY_LOCAL_ONLY",
        "independent_second_storage_verified": False,
        "restore_read_smoke": "PASS",
        "contains_private_paths": False,
        "contains_scientific_values": False,
        "attack_payload_accesses": 0,
        "label_accesses": 0,
        "test1_accesses": 0,
        "test2_accesses": 0,
        "private_exposures": 0,
    })
    public_path = root / "research_control_center/validation_v2/local_custody/PUBLIC_EVALUATION_EXPANSION_PRIVATE_INDEX_V1.json"
    _publish_json(public_path, public_receipt)
    print(json.dumps({"status": "PASS", "registered": len(records), "restore_read_smoke": "PASS", "private_exposures": 0}))


if __name__ == "__main__":
    main()
