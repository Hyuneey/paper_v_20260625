"""Run the independent TASK-039D2 train3 audit replay."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Mapping

from paperworks.profiling.task039d2_final_audit_v1 import (
    ARM_SUMMARY_HASH,
    AUDIT_PREP_COMMIT,
    AUTHORITATIVE_MAIN,
    CORRECTED_SCHEMA_HASH,
    DATA_ACCESS_AUDIT_HASH,
    D2_AUTHORIZATION_HASH,
    D2_RESULT_HASH,
    DIRECTIONAL_SUMMARY_HASH,
    EXECUTION_RECEIPT_HASH,
    FAILED_RUN_CUSTODY_HASH,
    PAIR_SUMMARY_HASH,
    PRIVATE_D2_LEDGER_NAME,
    READINESS,
    RECOVERED_RESULT_B,
    RECOVERY_COMMIT_R,
    RECOVERY_RECEIPT_HASH,
    STATUS,
    TASK039D2FinalAuditError,
    audit_schema_examples_v1,
    build_e0_authorization_v1,
    build_final_audit_v1,
    build_independent_input_set_v1,
    load_json_object_v1,
    load_frozen_audit_replay_v1,
    load_train3_for_independent_audit_v1,
    reconstruct_post_freeze_arm_audit_v1,
    replay_train3_independently_v1,
    schema_for_audit_artifact_v1,
    verify_train3_manifest_identity_v1,
    verify_audit_self_hash_v1,
    write_json_v1,
)
from paperworks.profiling.task039d2_result_recovery_v1 import (
    COMMIT_A_SCIENTIFIC_SOURCE_HASHES,
    D1_DIRECTIONAL_LEDGER_HASH,
    D1_FIT_RESULT_HASH,
    D1_PAIR_SUMMARY_HASH,
    D1_SOURCE_LEDGER_HASH,
    D1_TARGET_LEDGER_HASH,
    ORIGINAL_COMMIT_A,
    PRIVATE_D2_LEDGER_HASH,
    load_d1_private_inputs_for_recovery_v1,
    validate_frozen_d2_ledger_v1,
    verify_recovery_self_hash_v1,
    verify_scientific_sources_unchanged_v1,
)
from paperworks.v6.common import stable_hash_v1


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"
BRANCH = "task-039d2-final-audit"
SCHEMA_FILES = {
    "task039d2_final_audit_v1": "task039d2_final_audit_v1_schema.json",
    "task039e0_authorization_v1": "task039e0_authorization_v1_schema.json",
}
EXPECTED_PUBLIC_HASHES = {
    "TASK-039D2_DIRECTIONAL_CONFIRMATION_SUMMARY.json": DIRECTIONAL_SUMMARY_HASH,
    "TASK-039D2_PAIR_CONFIRMATION_SUMMARY.json": PAIR_SUMMARY_HASH,
    "TASK-039D2_ARM_CONFIRMATION_SUMMARY.json": ARM_SUMMARY_HASH,
    "TASK-039D2_RESULT.json": D2_RESULT_HASH,
    "TASK-039D2_DATA_ACCESS_AUDIT.json": DATA_ACCESS_AUDIT_HASH,
    "TASK-039D2_EXECUTION_RECEIPT.json": EXECUTION_RECEIPT_HASH,
    "TASK-039D2R_RESULT_CONTRACT_RECOVERY_RECEIPT.json": RECOVERY_RECEIPT_HASH,
    "TASK-039D2_FAILED_RUN_CUSTODY.json": FAILED_RUN_CUSTODY_HASH,
}


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schemas-only", action="store_true")
    parser.add_argument("--audit-commit")
    parser.add_argument("--finalize-from-audit-ledger", action="store_true")
    parser.add_argument("--finalization-commit")
    return parser.parse_args()


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.resolve().as_posix()}", "-C", str(ROOT), *args],
        check=False, capture_output=True, text=True,
    )
    if result.returncode:
        raise TASK039D2FinalAuditError("Git audit-lineage verification failed")
    return result.stdout.rstrip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_blob_sha256(commit: str, relative_path: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{commit}:{relative_path}"],
        check=False, capture_output=True,
    )
    if result.returncode:
        raise TASK039D2FinalAuditError("Git blob unavailable")
    return hashlib.sha256(result.stdout).hexdigest()


def write_schemas() -> None:
    examples = audit_schema_examples_v1()
    if {item["artifact_type"] for item in examples} != set(SCHEMA_FILES):
        raise TASK039D2FinalAuditError("audit schema coverage mismatch")
    for item in examples:
        write_json_v1(
            ROOT / "schemas" / "v6" / SCHEMA_FILES[item["artifact_type"]],
            schema_for_audit_artifact_v1(item),
        )


def _validate_roots() -> tuple[Path, Path, Path, Path]:
    names = (
        "HAI_DATA_ROOT", "TASK039D_PRIVATE_ROOT", "TASK039D2_PRIVATE_ROOT",
        "TASK039D2_AUDIT_PRIVATE_ROOT",
    )
    raw = tuple(os.environ.get(name, "") for name in names)
    if any(not value or ".." in Path(value).parts for value in raw):
        raise TASK039D2FinalAuditError("all audit roots must be explicit")
    data, d1, d2 = (Path(value).resolve(strict=True) for value in raw[:3])
    candidate = Path(raw[3])
    audit = candidate.resolve(strict=candidate.exists())
    roots = (data, d1, d2, audit)
    repository = ROOT.resolve(strict=True)
    if len(set(roots)) != 4 or any(
        root.is_relative_to(repository) or repository.is_relative_to(root)
        for root in roots
    ):
        raise TASK039D2FinalAuditError("audit roots must be distinct and outside Git")
    if audit.exists() and any(audit.iterdir()):
        raise TASK039D2FinalAuditError("audit private root must be new or empty")
    return roots


def _validate_lineage(audit_commit: str) -> None:
    if _git("branch", "--show-current") != BRANCH or _git("rev-parse", "HEAD") != audit_commit:
        raise TASK039D2FinalAuditError("audit requires exact clean Audit Commit A")
    if _git("status", "--porcelain=v1"):
        raise TASK039D2FinalAuditError("audit requires a clean worktree")
    if _git("rev-parse", "origin/main") != AUTHORITATIVE_MAIN:
        raise TASK039D2FinalAuditError("authoritative main changed")
    for commit in (RECOVERED_RESULT_B, AUDIT_PREP_COMMIT):
        _git("merge-base", "--is-ancestor", commit, audit_commit)
    if _git("rev-parse", f"{RECOVERY_COMMIT_R}^") != ORIGINAL_COMMIT_A:
        raise TASK039D2FinalAuditError("D2R lineage mismatch")
    if _git("rev-parse", f"{RECOVERED_RESULT_B}^") != RECOVERY_COMMIT_R:
        raise TASK039D2FinalAuditError("D2R result lineage mismatch")
    for commit in (ORIGINAL_COMMIT_A, RECOVERY_COMMIT_R, RECOVERED_RESULT_B, audit_commit):
        if verify_scientific_sources_unchanged_v1(ROOT, commit) != COMMIT_A_SCIENTIFIC_SOURCE_HASHES:
            raise TASK039D2FinalAuditError("failed_task039d2_recovery_audit")
    if _git_blob_sha256(
        RECOVERED_RESULT_B,
        "schemas/v6/task039d2_real_execution_receipt_v1_schema.json",
    ) != CORRECTED_SCHEMA_HASH:
        raise TASK039D2FinalAuditError("corrected receipt schema identity mismatch")
    for name in ("TASK-039D2_FINAL_AUDIT.json", "TASK-039D2_FINAL_AUDIT.md", "TASK-039E0_AUTHORIZATION.json"):
        if (REPORTS / name).exists():
            raise TASK039D2FinalAuditError("audit result existed before train3 replay")


def _validate_public_history() -> dict[str, dict[str, Any]]:
    documents: dict[str, dict[str, Any]] = {}
    for name, expected in EXPECTED_PUBLIC_HASHES.items():
        document = load_json_object_v1(REPORTS / name)
        if verify_recovery_self_hash_v1(document) != expected:
            raise TASK039D2FinalAuditError("public D2 artifact hash mismatch")
        documents[name] = document
    recovery = documents["TASK-039D2R_RESULT_CONTRACT_RECOVERY_RECEIPT.json"]
    custody = documents["TASK-039D2_FAILED_RUN_CUSTODY.json"]
    receipt = documents["TASK-039D2_EXECUTION_RECEIPT.json"]
    if (
        recovery["status"] != "passed_task039d2r_result_contract_recovery"
        or recovery["defect_classification"] != "non_scientific_result_contract_schema_defect"
        or recovery["train3_reread"] is not False
        or recovery["scientific_code_changed"] is not False
        or recovery["scientific_outcomes_recomputed_from_hai"] is not False
        or custody["scientific_computation_completed_before_schema_failure"] is not True
        or custody["result_contract_validation_failure_stage"] != "post_scientific_public_execution_receipt_schema_validation"
        or receipt["execution_code_commit"] != ORIGINAL_COMMIT_A
        or receipt["scientific_source_hashes"] != COMMIT_A_SCIENTIFIC_SOURCE_HASHES
    ):
        raise TASK039D2FinalAuditError("failed_task039d2_recovery_audit")
    original_access = documents["TASK-039D2_DATA_ACCESS_AUDIT.json"]["original_scientific_run"]
    recovery_access = documents["TASK-039D2_DATA_ACCESS_AUDIT.json"]["recovery_finalization"]
    if (
        original_access != {
            "attacks_accessed": False,
            "br2_pair_results_accessed": False,
            "candidate_provenance_visible_during_confirmation": False,
            "d1_private_ledgers_accessed": True,
            "d1_private_ledgers_modified": False,
            "labels_accessed": False,
            "test_accessed": False,
            "train1_feature_values_accessed": False,
            "train2_feature_values_accessed": False,
            "train3_accessed": True,
            "train4_accessed": False,
        }
        or recovery_access["train3_reread"] is not False
        or recovery_access["hai_feature_values_accessed"] is not False
        or recovery_access["train1_train2_train4_test_labels_attacks_accessed"] is not False
    ):
        raise TASK039D2FinalAuditError("failed_task039d2_data_boundary_audit")
    authorization = load_json_object_v1(REPORTS / "TASK-039D2_AUTHORIZATION.json")
    if verify_recovery_self_hash_v1(authorization) != D2_AUTHORIZATION_HASH:
        raise TASK039D2FinalAuditError("D2 authorization mismatch")
    return documents


def _validate_private(d1_root: Path, d2_root: Path) -> tuple[Any, dict[str, Any]]:
    inputs = load_d1_private_inputs_for_recovery_v1(d1_root)
    if {path.name for path in d2_root.iterdir() if path.is_file()} != {PRIVATE_D2_LEDGER_NAME}:
        raise TASK039D2FinalAuditError("failed_task039d2_private_ledger_audit")
    ledger = load_json_object_v1(d2_root / PRIVATE_D2_LEDGER_NAME)
    validation = validate_frozen_d2_ledger_v1(ledger, expected_d1_relations=inputs.relations)
    if validation.confirmed_count != 42 or validation.conflict_count != 3:
        raise TASK039D2FinalAuditError("failed_task039d2_private_ledger_audit")
    return inputs, ledger


def _validate_pair_and_arm(
    *, replay: Mapping[str, Any], arm_audit: Any,
    public: Mapping[str, Mapping[str, Any]],
) -> None:
    original_pair = public["TASK-039D2_PAIR_CONFIRMATION_SUMMARY.json"]
    d1_pair = load_json_object_v1(REPORTS / "TASK-039D1_PAIR_FIT_SUMMARY.json")
    if verify_recovery_self_hash_v1(d1_pair) != D1_PAIR_SUMMARY_HASH:
        raise TASK039D2FinalAuditError("D1 pair summary mismatch")
    outcomes = replay["outcomes"]
    directions_by_pair: dict[tuple[str, str], list[Any]] = {}
    for item in outcomes.directions:
        directions_by_pair.setdefault(item.pair, []).append(item)
    expected_records = []
    for item in d1_pair["pair_outcomes"]:
        pair = (item["source"], item["target"])
        directions = directions_by_pair.get(pair, [])
        expected_records.append({
            "source": pair[0], "target": pair[1],
            "d1_fit_supported_pair": item["pair_fit_status"] == "fit_supported_pair",
            "d2_evaluated_direction_count": len(directions),
            "has_d2_confirmed_directional_relation": any(direction.status == "calibration_confirmed" for direction in directions),
        })
    if expected_records != original_pair["pair_records"]:
        raise TASK039D2FinalAuditError("failed_task039d2_record_level_parity")
    if len(arm_audit.pair_partition.confirmed_pairs) != 23 or len(arm_audit.pair_partition.conflict_pairs) != 2:
        raise TASK039D2FinalAuditError("failed_task039d2_record_level_parity")
    metrics = {item.arm: item for item in arm_audit.arm_metrics}
    expected = {
        "META": (16, 15, 28, 29, 7, 9),
        "STAT": (17, 17, 32, 33, 8, 8),
        "GDN": (5, 3, 5, 7, 3, 3),
    }
    for arm, values in expected.items():
        item = metrics[arm]
        observed = (
            item.fit_supported_pair_count, item.confirmed_pair_count,
            item.confirmed_direction_count, item.fit_supported_direction_count,
            item.confirmed_source_count, item.confirmed_target_count,
        )
        if observed != values:
            raise TASK039D2FinalAuditError("failed_task039d2_arm_metric_reconstruction")
    confirmed = arm_audit.pair_partition.confirmed_pairs
    provenance = load_json_object_v1(REPORTS / "TASK-039D0_PROVENANCE_ANALYSIS_VIEW.json")
    provenance_by_pair = {
        (item["source"], item["target"]): tuple(item["origin_arms"])
        for item in provenance["candidates"]
    }
    membership = {pair: provenance_by_pair[pair] for pair in confirmed}
    decomposition = {
        "META_only": sum(arms == ("META",) for arms in membership.values()),
        "STAT_only": sum(arms == ("STAT",) for arms in membership.values()),
        "GDN_only": sum(arms == ("GDN",) for arms in membership.values()),
        "META+STAT_only": sum(set(arms) == {"META", "STAT"} for arms in membership.values()),
        "META+GDN_only": sum(set(arms) == {"META", "GDN"} for arms in membership.values()),
        "STAT+GDN_only": sum(set(arms) == {"STAT", "GDN"} for arms in membership.values()),
        "all_three": sum(set(arms) == {"META", "STAT", "GDN"} for arms in membership.values()),
    }
    if decomposition != {
        "META_only": 4, "STAT_only": 5, "GDN_only": 2,
        "META+STAT_only": 11, "META+GDN_only": 0,
        "STAT+GDN_only": 1, "all_three": 0,
    }:
        raise TASK039D2FinalAuditError("failed_task039d2_arm_metric_reconstruction")


def _validate_schema(document: Mapping[str, Any]) -> None:
    from jsonschema import Draft202012Validator
    schema = load_json_object_v1(
        ROOT / "schemas" / "v6" / SCHEMA_FILES[str(document["artifact_type"])]
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(document)


def _report(audit: Mapping[str, Any], authorization: Mapping[str, Any]) -> str:
    metrics = audit["arm_metrics"]
    return f"""# TASK-039D2 Final Audit

Status: `{audit['status']}`

Readiness: `{audit['readiness']}`

The independent train3 replay reproduced all 45 frozen one-way confirmation
records: 42 calibration-confirmed directions and 3 conflicts. The resulting
47-pair view contains 23 pairs with at least one confirmed direction and 2
D1-supported pairs without confirmation.

## Method-specific descriptive metrics

- META: `{metrics['META']['confirmed_pairs']}/20` confirmed pairs and `{metrics['META']['confirmed_directions']}/{metrics['META']['fit_supported_directions']}` confirmed directions.
- STAT: `{metrics['STAT']['confirmed_pairs']}/20` confirmed pairs and `{metrics['STAT']['confirmed_directions']}/{metrics['STAT']['fit_supported_directions']}` confirmed directions.
- GDN: `{metrics['GDN']['confirmed_pairs']}/20` confirmed pairs and `{metrics['GDN']['confirmed_directions']}/{metrics['GDN']['fit_supported_directions']}` confirmed directions.

Under `continuous_step_delayed_response_v1`, STAT retains more top-20
candidates through train3 than META or GDN; META also has high fit-to-confirmation
transfer, while GDN has lower confirmed yield. This measures alignment with
this specific relation family, not general candidate-discovery or GDN quality.

## Scientific and authority boundaries

- The D2R recovery was a non-scientific result-contract repair; scientific sources remained unchanged.
- Original D2 train3 access: `true`; recovery reread: `false`; audit replay access: `true`.
- Train1/train2/train4/test/labels/attacks and BR2 pair results accessed by audit: `false`.
- Arm provenance was joined only after audit outcomes froze; retuning, search, and fallback: `false`.
- E0 authorization hash: `{authorization['artifact_hash']}`.
- E0 authorizes protocol design only. LLM execution, Rule v2, Agent, detector/runtime, and real rule generation remain unauthorized.

The confirmed items are normal delayed-response relation candidates. They are
not causal truth, root causes, verified executable rules, or detector gains.
"""


def execute(audit_commit: str) -> dict[str, str]:
    _validate_lineage(audit_commit)
    data_root, d1_root, d2_root, audit_root = _validate_roots()
    public = _validate_public_history()
    d1_inputs, d2_ledger = _validate_private(d1_root, d2_root)
    input_set = build_independent_input_set_v1(
        source_document=d1_inputs.source_document,
        target_document=d1_inputs.target_document,
        directional_document=d1_inputs.directional_document,
    )
    if len(input_set.directional_inputs) != 45:
        raise TASK039D2FinalAuditError("failed_task039d2_private_ledger_audit")
    verify_train3_manifest_identity_v1(ROOT)
    values, access = load_train3_for_independent_audit_v1(data_root=data_root)
    print("[TASK-039D2-AUDIT] train3_authorized_view_loaded", flush=True)
    replay = replay_train3_independently_v1(
        input_set=input_set, values=values, original_ledger=d2_ledger,
        audit_private_root=audit_root,
        progress_callback=lambda message: print(f"[TASK-039D2-AUDIT] {message}", flush=True),
    )
    del values
    if replay["confirmed_count"] != 42 or replay["conflict_count"] != 3:
        raise TASK039D2FinalAuditError("failed_task039d2_independent_train3_replay")

    # This is deliberately the first provenance load in the audit.
    provenance = load_json_object_v1(REPORTS / "TASK-039D0_PROVENANCE_ANALYSIS_VIEW.json")
    arm_audit = reconstruct_post_freeze_arm_audit_v1(
        outcomes=replay["outcomes"], provenance_document=provenance,
    )
    _validate_pair_and_arm(replay=replay, arm_audit=arm_audit, public=public)
    if access["row_count"] != 126000:
        raise TASK039D2FinalAuditError("failed_task039d2_data_boundary_audit")

    authorization = build_e0_authorization_v1()
    audit = build_final_audit_v1(
        replay=replay, arm_audit=arm_audit, audit_commit=audit_commit,
        audit_private_ledger_hash=replay["audit_private_ledger_hash"],
        e0_authorization_hash=authorization["artifact_hash"],
    )
    for document in (audit, authorization):
        verify_audit_self_hash_v1(document)
        _validate_schema(document)
    write_json_v1(REPORTS / "TASK-039D2_FINAL_AUDIT.json", audit)
    write_json_v1(REPORTS / "TASK-039E0_AUTHORIZATION.json", authorization)
    (REPORTS / "TASK-039D2_FINAL_AUDIT.md").write_text(
        _report(audit, authorization), encoding="utf-8", newline="\n",
    )
    return {"audit_hash": audit["artifact_hash"], "authorization_hash": authorization["artifact_hash"]}


def finalize_from_frozen_audit_ledger(
    *, audit_commit: str, finalization_commit: str,
) -> dict[str, str]:
    if (
        _git("branch", "--show-current") != BRANCH
        or _git("rev-parse", "HEAD") != finalization_commit
        or _git("status", "--porcelain=v1")
    ):
        raise TASK039D2FinalAuditError("frozen-ledger finalization requires a clean commit")
    _git("merge-base", "--is-ancestor", audit_commit, finalization_commit)
    if verify_scientific_sources_unchanged_v1(ROOT, finalization_commit) != COMMIT_A_SCIENTIFIC_SOURCE_HASHES:
        raise TASK039D2FinalAuditError("failed_task039d2_recovery_audit")
    raw = tuple(os.environ.get(name, "") for name in (
        "TASK039D_PRIVATE_ROOT", "TASK039D2_PRIVATE_ROOT", "TASK039D2_AUDIT_PRIVATE_ROOT",
    ))
    if any(not value for value in raw):
        raise TASK039D2FinalAuditError("private roots must be explicit")
    d1_root, d2_root, audit_root = (Path(value).resolve(strict=True) for value in raw)
    repository = ROOT.resolve(strict=True)
    if len({d1_root, d2_root, audit_root}) != 3 or any(
        path.is_relative_to(repository) or repository.is_relative_to(path)
        for path in (d1_root, d2_root, audit_root)
    ):
        raise TASK039D2FinalAuditError("private roots must remain outside Git")
    for name in ("TASK-039D2_FINAL_AUDIT.json", "TASK-039D2_FINAL_AUDIT.md", "TASK-039E0_AUTHORIZATION.json"):
        if (REPORTS / name).exists():
            raise TASK039D2FinalAuditError("audit result already exists")
    public = _validate_public_history()
    d1_inputs, d2_ledger = _validate_private(d1_root, d2_root)
    input_set = build_independent_input_set_v1(
        source_document=d1_inputs.source_document,
        target_document=d1_inputs.target_document,
        directional_document=d1_inputs.directional_document,
    )
    replay = load_frozen_audit_replay_v1(
        input_set=input_set, original_ledger=d2_ledger,
        audit_private_root=audit_root,
    )
    if replay["confirmed_count"] != 42 or replay["conflict_count"] != 3:
        raise TASK039D2FinalAuditError("failed_task039d2_independent_train3_replay")
    provenance = load_json_object_v1(REPORTS / "TASK-039D0_PROVENANCE_ANALYSIS_VIEW.json")
    arm_audit = reconstruct_post_freeze_arm_audit_v1(
        outcomes=replay["outcomes"], provenance_document=provenance,
    )
    _validate_pair_and_arm(replay=replay, arm_audit=arm_audit, public=public)
    authorization = build_e0_authorization_v1()
    audit = build_final_audit_v1(
        replay=replay, arm_audit=arm_audit, audit_commit=audit_commit,
        audit_private_ledger_hash=replay["audit_private_ledger_hash"],
        e0_authorization_hash=authorization["artifact_hash"],
    )
    audit["findings_by_severity"]["IMPORTANT_NONBLOCKING"].append(
        "post_freeze_tuple_list_accounting_assertion_corrected_without_train3_reread"
    )
    audit = {key: value for key, value in audit.items() if key != "artifact_hash"}
    audit["artifact_hash"] = stable_hash_v1(audit)
    for document in (audit, authorization):
        verify_audit_self_hash_v1(document)
        _validate_schema(document)
    write_json_v1(REPORTS / "TASK-039D2_FINAL_AUDIT.json", audit)
    write_json_v1(REPORTS / "TASK-039E0_AUTHORIZATION.json", authorization)
    (REPORTS / "TASK-039D2_FINAL_AUDIT.md").write_text(
        _report(audit, authorization), encoding="utf-8", newline="\n",
    )
    return {"audit_hash": audit["artifact_hash"], "authorization_hash": authorization["artifact_hash"]}


def main() -> int:
    args = _args()
    if args.schemas_only:
        write_schemas()
        return 0
    if args.finalize_from_audit_ledger:
        if not args.audit_commit or not args.finalization_commit:
            raise TASK039D2FinalAuditError("both audit and finalization commits are required")
        result = finalize_from_frozen_audit_ledger(
            audit_commit=args.audit_commit, finalization_commit=args.finalization_commit,
        )
        print(f"[TASK-039D2-AUDIT] {STATUS}", flush=True)
        print(f"[TASK-039D2-AUDIT] {READINESS}", flush=True)
        print(json.dumps(result, sort_keys=True), flush=True)
        return 0
    if not args.audit_commit:
        raise TASK039D2FinalAuditError("--audit-commit is required")
    result = execute(args.audit_commit)
    print(f"[TASK-039D2-AUDIT] {STATUS}", flush=True)
    print(f"[TASK-039D2-AUDIT] {READINESS}", flush=True)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
