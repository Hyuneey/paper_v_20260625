#!/usr/bin/env python3
"""Run TASK-039BR2 with explicit public/private roots and frozen inputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from paperworks.data.contracts_v2 import DatasetManifestV2
from paperworks.feasibility.hai_continuous_step_v1 import (
    ALL_NORMAL_FILES,
    AUTHORIZED_VALUE_FILES,
    BR0_DECISION_HASH,
    BR0_READINESS_HASH,
    BR1_PROTOCOL_BUNDLE_HASH,
    DATASET_MANIFEST_ID,
    TASK039A_PROVENANCE_HASH,
    TASK039AR_EQUIVALENCE_HASH,
    HAIContinuousProcessFreezeV1,
    HAIContinuousStepError,
    TASK039BR2DataAccessAuditV1,
    TASK039BR2DataAccessLedger,
    TASK039BR2ExecutionInterpretationV1,
    TASK039BR2ExecutionReceiptV1,
    assert_public_payload_safe_v1,
    build_process_selection_v1,
    create_selected_splits_v1,
    create_selected_views_v1,
    execute_process_v1,
    validate_frozen_eligibility_v1,
    validate_frozen_inputs_v1,
    verify_normal_file_records_v1,
    verify_self_hash_v1,
    write_json_v1,
)
from paperworks.v6.common import CreationMetadataV1, stable_hash_v1


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--hai-root", required=True, type=Path)
    parser.add_argument("--private-output-root", required=True, type=Path)
    parser.add_argument("--public-output-root", required=True, type=Path)
    parser.add_argument("--source-exclusion-ledger", required=True, type=Path)
    parser.add_argument("--morphology-ledger", required=True, type=Path)
    parser.add_argument("--execution-code-commit", required=True)
    return parser.parse_args()


def _load(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HAIContinuousStepError(f"cannot load required input: {path.name}") from exc


def _assert_roots(repository: Path, data: Path, private: Path, public: Path) -> None:
    repository = repository.resolve()
    data = data.resolve()
    private = private.resolve()
    public = public.resolve()
    if data == repository or repository in data.parents or private == repository or repository in private.parents:
        raise HAIContinuousStepError("raw/private roots must remain outside the repository")
    if public != repository / "docs" / "task_reports":
        raise HAIContinuousStepError("public output root must be docs/task_reports")
    if data == private or data in private.parents or private in data.parents:
        raise HAIContinuousStepError("data and private output roots must be separate")


def _self_hashed_collection(artifact_type: str, records: list[Mapping[str, Any]]) -> dict[str, Any]:
    content = {
        "schema_version": "1.0.0",
        "artifact_type": artifact_type,
        "records": [dict(item) for item in records],
    }
    return {**content, "artifact_hash": stable_hash_v1(content)}


def _write_public(path: Path, document: Mapping[str, Any]) -> None:
    assert_public_payload_safe_v1(document)
    write_json_v1(path, document)


def main() -> int:
    args = _arguments()
    repository = args.repository_root.resolve()
    data_root = args.hai_root.resolve()
    private_root = args.private_output_root.resolve()
    public_root = args.public_output_root.resolve()
    _assert_roots(repository, data_root, private_root, public_root)
    if len(args.execution_code_commit) != 40:
        raise HAIContinuousStepError("execution_code_commit must be a full commit")

    config = _load(repository / "configs/v6/task039br2_hai_continuous_step_feasibility.json")
    dataset_document = _load(repository / "docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json")
    csv_report = _load(repository / "docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json")
    a_provenance = _load(repository / "docs/task_reports/TASK-039A_PROVENANCE_REPORT.json")
    ar_equivalence = _load(repository / "docs/task_reports/TASK-039AR_BYTE_EQUIVALENCE_REPORT.json")
    br0_decision = _load(repository / "docs/task_reports/TASK-039BR0_RELATION_FAMILY_DECISION.json")
    br0_readiness = _load(repository / "docs/task_reports/TASK-039BR0_CONTINUOUS_SOURCE_READINESS.json")
    br1_bundle = _load(repository / "docs/task_reports/TASK-039BR1_PROTOCOL_BUNDLE.json")
    br1_config = _load(repository / "configs/v6/task039br1_continuous_step_protocol.json")
    interpretation_document = _load(repository / "docs/task_reports/TASK-039BR2_EXECUTION_INTERPRETATION.json")
    source_ledger = _load(args.source_exclusion_ledger.resolve())
    morphology_ledger = _load(args.morphology_ledger.resolve())

    validate_frozen_inputs_v1(
        config=config,
        dataset_manifest=dataset_document,
        br0_decision=br0_decision,
        br0_readiness=br0_readiness,
        br1_bundle=br1_bundle,
        source_exclusion_ledger=source_ledger,
        morphology_ledger=morphology_ledger,
    )
    if (
        verify_self_hash_v1(a_provenance) != TASK039A_PROVENANCE_HASH
        or verify_self_hash_v1(ar_equivalence) != TASK039AR_EQUIVALENCE_HASH
        or verify_self_hash_v1(csv_report, "report_hash") != csv_report.get("report_hash")
        or br1_config.get("config_hash") != config["frozen_lineage"]["br1_config_hash"]
        or csv_report.get("all_headers_aligned") is not True
        or csv_report.get("feature_names_hash") != dataset_document.get("feature_names_hash")
    ):
        raise HAIContinuousStepError("blocked_frozen_artifact_identity_mismatch")
    interpretation = TASK039BR2ExecutionInterpretationV1.from_dict(interpretation_document)
    eligibility = validate_frozen_eligibility_v1(
        config=config,
        source_exclusion_ledger=source_ledger,
        morphology_ledger=morphology_ledger,
    )
    manifest = DatasetManifestV2.from_dict(dataset_document)
    verified = verify_normal_file_records_v1(
        data_root=data_root,
        manifest=manifest,
        csv_report=csv_report,
    )
    columns = {
        process: tuple(item["variable_name"] for item in eligibility[process]["sources"])
        + tuple(item["variable_name"] for item in eligibility[process]["targets"])
        for process in ("P1", "P3")
    }
    access_ledger = TASK039BR2DataAccessLedger(columns)
    created_at = str(config["execution_creation_timestamp"])
    creation = CreationMetadataV1(
        created_at=created_at,
        created_by="TASK-039BR2",
        code_commit=args.execution_code_commit,
        config_hash=str(config["config_hash"]),
    )

    p1 = execute_process_v1(
        process_id="P1",
        process_name="Boiler",
        eligibility=eligibility["P1"],
        data_root=data_root,
        verified_files=verified,
        ledger=access_ledger,
        creation_metadata=creation,
    )
    p3 = execute_process_v1(
        process_id="P3",
        process_name="Water Treatment",
        eligibility=eligibility["P3"],
        data_root=data_root,
        verified_files=verified,
        ledger=access_ledger,
        creation_metadata=creation,
    )

    private_root.mkdir(parents=True, exist_ok=False)
    private_documents = {
        "task039br2_p1_source_parameter_ledger.json": p1.source_ledger,
        "task039br2_p1_event_ledger.json": p1.event_ledger,
        "task039br2_p1_relation_ledger.json": p1.relation_ledger,
        "task039br2_p3_source_parameter_ledger.json": p3.source_ledger,
        "task039br2_p3_event_ledger.json": p3.event_ledger,
        "task039br2_p3_relation_ledger.json": p3.relation_ledger,
    }
    for name, document in private_documents.items():
        write_json_v1(private_root / name, document)

    selection_policy_hash = str(br1_bundle["process_selection_policy"]["artifact_hash"])
    selection = build_process_selection_v1(
        p1=p1.feasibility,
        p3=p3.feasibility,
        selection_policy_hash=selection_policy_hash,
        creation_metadata=creation,
    )
    access = TASK039BR2DataAccessAuditV1(
        AUTHORIZED_VALUE_FILES,
        tuple(sorted(access_ledger.opened_value_files)),
        access_ledger.authorized_columns_hash,
        False,
        False,
        False,
        False,
        access_ledger.normal_guard_feature_values_accessed,
        access_ledger.p2_p4_feature_values_accessed,
        access_ledger.prohibited_data_access_count,
        False,
        False,
        False,
        creation,
    )

    _write_public(public_root / "TASK-039BR2_P1_FEASIBILITY.json", p1.feasibility.to_dict())
    _write_public(public_root / "TASK-039BR2_P3_FEASIBILITY.json", p3.feasibility.to_dict())
    _write_public(public_root / "TASK-039BR2_PROCESS_SELECTION.json", selection.to_dict())
    _write_public(public_root / "TASK-039BR2_DATA_ACCESS_AUDIT.json", access.to_dict())

    selected_result = p1 if selection.selected_process_id == "P1" else p3
    process_freeze: HAIContinuousProcessFreezeV1 | None = None
    if selection.selection_status == "selected":
        selected_process = str(selection.selected_process_id)
        canonical, candidate = create_selected_views_v1(
            process_id=selected_process,
            process_feature_names=selected_result.process_feature_names,
            execution_code_commit=args.execution_code_commit,
            config_hash=str(config["config_hash"]),
            created_at=created_at,
        )
        row_counts = {item.relative_path: item.row_count for item in verified}
        fit_split, calibration_split, guard_split = create_selected_splits_v1(
            process_id=selected_process,
            canonical_view_id=canonical.view_id,
            row_counts=row_counts,
            execution_code_commit=args.execution_code_commit,
            config_hash=str(config["config_hash"]),
            created_at=created_at,
        )
        process_freeze = HAIContinuousProcessFreezeV1(
            DATASET_MANIFEST_ID,
            BR0_DECISION_HASH,
            BR1_PROTOCOL_BUNDLE_HASH,
            args.execution_code_commit,
            selected_process,
            "Boiler" if selected_process == "P1" else "Water Treatment",
            str(selection.excluded_process_id),
            selection.selection_reason,
            selection_policy_hash,
            p1.feasibility.artifact_hash,
            p3.feasibility.artifact_hash,
            str(selected_result.relation_ledger["artifact_hash"]),
            str(selected_result.source_ledger["artifact_hash"]),
            fit_split.split_id,
            calibration_split.split_id,
            guard_split.split_id,
            canonical.view_id,
            candidate.view_id,
            "pending_production_backend",
            "not_created",
            True,
            (
                "normal_only_feasibility_selection",
                "not_physical_causality",
                "not_rule_or_runtime_authority",
                "TASK-039C_candidate_universe_only",
            ),
            False,
            False,
            creation,
        )
        split_collection = _self_hashed_collection(
            "task039br2_selected_process_split_manifests_v2",
            [fit_split.to_dict(), calibration_split.to_dict(), guard_split.to_dict()],
        )
        gdn_content = {
            "schema_version": "1.0.0",
            "artifact_type": "task039br2_gdn_view_readiness_v1",
            "selected_process_id": selected_process,
            "production_backend": "unresolved",
            "gdn_view_status": "pending_production_backend",
            "downsampling_approved": False,
            "model_training_authorized": False,
            "candidate_mask_required": True,
        }
        gdn = {**gdn_content, "artifact_hash": stable_hash_v1(gdn_content)}
        _write_public(public_root / "TASK-039BR2_PROCESS_FREEZE.json", process_freeze.to_dict())
        _write_public(public_root / "TASK-039BR2_CANONICAL_RULE_VIEW_V2.json", canonical.to_dict())
        _write_public(public_root / "TASK-039BR2_CANDIDATE_LEARNING_VIEW_V2.json", candidate.to_dict())
        _write_public(public_root / "TASK-039BR2_SPLIT_MANIFESTS_V2.json", split_collection)
        _write_public(public_root / "TASK-039BR2_GDN_VIEW_READINESS.json", gdn)

    status = (
        "passed_hai_2305_continuous_step_single_process_freeze"
        if selection.selection_status == "selected"
        else selection.selection_status
    )
    private_hashes = tuple(str(document["artifact_hash"]) for document in private_documents.values())
    receipt = TASK039BR2ExecutionReceiptV1(
        "TASK-039BR2",
        status,
        args.execution_code_commit,
        str(config["config_hash"]),
        DATASET_MANIFEST_ID,
        BR0_DECISION_HASH,
        BR0_READINESS_HASH,
        BR1_PROTOCOL_BUNDLE_HASH,
        interpretation.artifact_hash,
        p1.feasibility.artifact_hash,
        p3.feasibility.artifact_hash,
        selection.artifact_hash,
        access.artifact_hash,
        private_hashes,
        selection.selected_process_id,
        process_freeze.artifact_hash if process_freeze else None,
        True,
        True,
        False,
        False,
        False,
        0,
        0,
        selection.task039c_authorized,
        creation,
    )
    _write_public(public_root / "TASK-039BR2_EXECUTION_RECEIPT.json", receipt.to_dict())
    print(json.dumps({"status": status, "receipt_hash": receipt.artifact_hash}, sort_keys=True))
    return 0 if status == "passed_hai_2305_continuous_step_single_process_freeze" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except HAIContinuousStepError as exc:
        print(json.dumps({"status": "failed", "reason": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(1)
