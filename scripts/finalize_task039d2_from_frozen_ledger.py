"""Finalize TASK-039D2 public results from the frozen private ledger only.

There is deliberately no dataset root argument and no HAI data loader.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Mapping

from paperworks.profiling.task039d2_result_recovery_v1 import (
    AUDIT_COMMIT,
    D1_ARM_SUMMARY_HASH,
    D1_FIT_RESULT_HASH,
    D1_PAIR_SUMMARY_HASH,
    D2_AUTHORIZATION_HASH,
    COMMIT_A_SCIENTIFIC_SOURCE_HASHES,
    DEFECT_CLASSIFICATION,
    ORIGINAL_COMMIT_A,
    ORIGINAL_FAILED_STATUS,
    PRIVATE_D2_LEDGER_HASH,
    PRIVATE_D2_LEDGER_NAME,
    RECOVERY_ARTIFACT_CLASSES,
    RECOVERY_CLASS_BY_TYPE,
    RECOVERY_STATUS,
    SCIENTIFIC_STATUS,
    TASK039D2RecoveryError,
    assert_reconstruction_invariance_v1,
    bind_exact_four_source_hash_schema_v1,
    build_arm_summary_from_frozen_ledger_v1,
    build_directional_summary_from_frozen_ledger_v1,
    build_execution_receipt_from_frozen_ledger_v1,
    build_failed_run_custody_v1,
    build_pair_summary_from_frozen_ledger_v1,
    build_recovery_data_access_audit_v1,
    build_recovery_receipt_v1,
    build_result_from_frozen_ledger_v1,
    load_d1_private_inputs_for_recovery_v1,
    load_json_object_v1,
    load_provenance_after_recovery_outcomes_frozen_v1,
    recovery_schema_examples_v1,
    schema_for_recovery_artifact_v1,
    validate_frozen_d2_ledger_v1,
    verify_d2_self_hash_v1,
    verify_recovery_self_hash_v1,
    verify_scientific_sources_unchanged_v1,
    write_public_json_v1,
)
from paperworks.v6.common import stable_hash_v1
from paperworks.v6.relation_profiling_protocol_v1 import verify_self_hash_v1


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"
AUTHORIZATION_PATH = REPORTS / "TASK-039D2_AUTHORIZATION.json"
CUSTODY_PATH = REPORTS / "TASK-039D2_FAILED_RUN_CUSTODY.json"
PROVENANCE_PATH = REPORTS / "TASK-039D0_PROVENANCE_ANALYSIS_VIEW.json"
CORRECTED_SCHEMA_PATH = ROOT / "schemas" / "v6" / "task039d2_real_execution_receipt_v1_schema.json"
BRANCH = "task-039d2r-result-contract-recovery"
PREP_MERGE_COMMIT = "0f4fa325e125abf15741e76603d989105c8ff92e"

RECOVERY_SCHEMA_FILES = {
    "task039d2_failed_run_custody_v1": "task039d2_failed_run_custody_v1_schema.json",
    "task039d2r_data_access_audit_v1": "task039d2r_data_access_audit_v1_schema.json",
    "task039d2_result_contract_recovery_receipt_v1": "task039d2_result_contract_recovery_receipt_v1_schema.json",
}

PUBLIC_OUTPUTS = {
    "access": "TASK-039D2_DATA_ACCESS_AUDIT.json",
    "directional": "TASK-039D2_DIRECTIONAL_CONFIRMATION_SUMMARY.json",
    "pair": "TASK-039D2_PAIR_CONFIRMATION_SUMMARY.json",
    "arm": "TASK-039D2_ARM_CONFIRMATION_SUMMARY.json",
    "result": "TASK-039D2_RESULT.json",
    "receipt": "TASK-039D2_EXECUTION_RECEIPT.json",
    "recovery": "TASK-039D2R_RESULT_CONTRACT_RECOVERY_RECEIPT.json",
    "report": "TASK-039D2_REPORT.md",
}


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schemas-only", action="store_true")
    parser.add_argument("--custody-only", action="store_true")
    parser.add_argument("--recovery-commit")
    return parser.parse_args()


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TASK039D2RecoveryError(f"required artifact unavailable: {path.name}") from exc
    if not isinstance(value, dict):
        raise TASK039D2RecoveryError(f"artifact must be an object: {path.name}")
    return value


def _git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.resolve().as_posix()}", "-C", str(ROOT), *args],
        capture_output=True, text=True, check=False,
    )
    if check and result.returncode:
        raise TASK039D2RecoveryError("Git recovery-lineage verification failed")
    return result.stdout.strip() if result.returncode == 0 else ""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _validate_authorization_before_roots() -> None:
    authorization = _load(AUTHORIZATION_PATH)
    verify_recovery_self_hash_v1(authorization)
    expected = {
        "artifact_hash": D2_AUTHORIZATION_HASH,
        "status": "authorized_task039d2_one_way_train3_confirmation",
        "readiness": "READY_FOR_TASK039D2",
        "candidate_count": 47,
        "input_directional_relations": "d1_fit_supported_only",
        "input_directional_relation_count": 45,
        "supported_pair_context_count": 25,
        "train3_feature_values_authorized": True,
        "train1_train2_feature_value_refitting_authorized": False,
        "train4_authorized": False,
        "test_labels_attacks_authorized": False,
        "br2_pair_results_authorized": False,
        "candidate_arm_evidence_visible_to_confirmation_engine": False,
        "parameter_retuning_authorized": False,
        "alternative_horizon_search_authorized": False,
        "opposite_target_direction_search_authorized": False,
        "rule_v2_authorized": False,
        "agent_authorized": False,
        "detector_runtime_authorized": False,
        "separate_clean_d2_execution_code_commit_required": True,
        "d2_executed_by_this_artifact": False,
    }
    if any(authorization.get(key) != value for key, value in expected.items()):
        raise TASK039D2RecoveryError("blocked_task039d2_authorization_mismatch")


def _validate_roots() -> tuple[Path, Path, Path]:
    values = (
        os.environ.get("TASK039D_PRIVATE_ROOT", ""),
        os.environ.get("TASK039D2_PRIVATE_ROOT", ""),
        os.environ.get("TASK039D2R_PRIVATE_ROOT", ""),
    )
    if any(not value or ".." in Path(value).parts for value in values):
        raise TASK039D2RecoveryError("recovery roots must be explicit and traversal-free")
    repository = ROOT.resolve(strict=True)
    d1 = Path(values[0]).resolve(strict=True)
    d2 = Path(values[1]).resolve(strict=True)
    candidate = Path(values[2])
    d2r = candidate.resolve(strict=candidate.exists())
    if len({d1, d2, d2r}) != 3 or any(path.is_relative_to(repository) or repository.is_relative_to(path) for path in (d1, d2, d2r)):
        raise TASK039D2RecoveryError("private recovery roots must be distinct and outside Git")
    return d1, d2, d2r


def _load_private_bindings() -> tuple[Any, dict[str, Any], Any]:
    d1_root, d2_root, d2r_root = _validate_roots()
    inputs = load_d1_private_inputs_for_recovery_v1(d1_root)
    ledger_path = (d2_root / PRIVATE_D2_LEDGER_NAME).resolve(strict=True)
    if ledger_path.parent != d2_root or {path.name for path in d2_root.iterdir() if path.is_file()} != {PRIVATE_D2_LEDGER_NAME}:
        raise TASK039D2RecoveryError("blocked_task039d2r_private_ledger_custody")
    ledger = _load(ledger_path)
    validation = validate_frozen_d2_ledger_v1(ledger, expected_d1_relations=inputs.relations)
    return inputs, ledger, (validation, d2r_root)


def _write_schemas() -> None:
    raw = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{ORIGINAL_COMMIT_A}:schemas/v6/task039d2_real_execution_receipt_v1_schema.json"],
        capture_output=True, check=False,
    )
    if raw.returncode:
        raise TASK039D2RecoveryError("Commit-A receipt schema unavailable")
    corrected = bind_exact_four_source_hash_schema_v1(json.loads(raw.stdout.decode("utf-8")))
    write_public_json_v1(CORRECTED_SCHEMA_PATH, corrected)
    examples = recovery_schema_examples_v1()
    if set(examples) != set(RECOVERY_SCHEMA_FILES) or {item.ARTIFACT_TYPE for item in RECOVERY_ARTIFACT_CLASSES} != set(examples):
        raise TASK039D2RecoveryError("recovery schema coverage mismatch")
    for artifact_type, filename in RECOVERY_SCHEMA_FILES.items():
        write_public_json_v1(
            ROOT / "schemas" / "v6" / filename,
            schema_for_recovery_artifact_v1(examples[artifact_type]),
        )


def create_custody() -> dict[str, Any]:
    _validate_authorization_before_roots()
    source_hashes = verify_scientific_sources_unchanged_v1(ROOT, ORIGINAL_COMMIT_A)
    _, _, joined = _load_private_bindings()
    validation, _ = joined
    original_tip = _git("rev-parse", "origin/task-039d2-train3-confirmation")
    custody = build_failed_run_custody_v1(
        original_branch_tip=original_tip, source_hashes=source_hashes, ledger_validation=validation,
    )
    write_public_json_v1(CUSTODY_PATH, custody)
    return custody


def _validate_public_d1() -> tuple[dict[str, Any], dict[str, Any]]:
    fit = _load(REPORTS / "TASK-039D1_FIT_RESULT.json")
    pair = _load(REPORTS / "TASK-039D1_PAIR_FIT_SUMMARY.json")
    arm = _load(REPORTS / "TASK-039D1_ARM_FIT_SUMMARY.json")
    for document, digest in ((fit, D1_FIT_RESULT_HASH), (pair, D1_PAIR_SUMMARY_HASH), (arm, D1_ARM_SUMMARY_HASH)):
        if verify_recovery_self_hash_v1(document) != digest:
            raise TASK039D2RecoveryError("failed_task039d2_private_input_binding")
    audit = _load(REPORTS / "TASK-039D1_FINAL_AUDIT.json")
    verify_recovery_self_hash_v1(audit)
    if audit.get("status") != "passed_task039d1_final_audit" or audit.get("readiness") != "READY_FOR_TASK039D2":
        raise TASK039D2RecoveryError("failed_task039d2_private_input_binding")
    return pair, arm


def _validate_schema(document: Mapping[str, Any]) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise TASK039D2RecoveryError("jsonschema is required from an existing verified environment") from exc
    artifact_type = str(document["artifact_type"])
    path = ROOT / "schemas" / "v6" / f"{artifact_type}_schema.json"
    schema = _load(path)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(document)


def _validate_recovery_commit(recovery_commit: str) -> None:
    if _git("branch", "--show-current") != BRANCH or _git("rev-parse", "HEAD") != recovery_commit:
        raise TASK039D2RecoveryError("recovery finalization requires exact Recovery Commit R")
    if _git("status", "--porcelain=v1"):
        raise TASK039D2RecoveryError("recovery finalization requires a clean worktree")
    _git("merge-base", "--is-ancestor", ORIGINAL_COMMIT_A, recovery_commit)
    verify_scientific_sources_unchanged_v1(ROOT, recovery_commit)
    for name in PUBLIC_OUTPUTS.values():
        if (REPORTS / name).exists():
            raise TASK039D2RecoveryError("authoritative public D2 output existed before finalization")


def _write_private_validation_binding(root: Path, custody_hash: str) -> None:
    if root.exists() and any(root.iterdir()):
        raise TASK039D2RecoveryError("D2R private root must be new or empty")
    root.mkdir(parents=True, exist_ok=True)
    content = {
        "artifact_type": "task039d2r_private_validation_binding_v1",
        "private_d2_ledger_hash": PRIVATE_D2_LEDGER_HASH,
        "record_count": 45,
        "failed_run_custody_hash": custody_hash,
        "private_contents_copied": False,
        "hai_values_accessed": False,
    }
    document = {**content, "artifact_hash": stable_hash_v1(content)}
    (root / "TASK039D2R_PRIVATE_VALIDATION_BINDING.json").write_text(
        json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n",
    )


def _report(
    *, directional: Mapping[str, Any], pair: Mapping[str, Any], arm: Mapping[str, Any],
    result: Mapping[str, Any], access: Mapping[str, Any], receipt: Mapping[str, Any], recovery: Mapping[str, Any],
) -> str:
    arms = {item["arm"]: item for item in arm["arms"]}
    overlap = arm["confirmed_pair_overlap"]
    return f"""# TASK-039D2 Recovered Result Report

Scientific status: `{result['status']}`

Recovery status: `{recovery['status']}`

TASK-039D2R repaired only the frozen receipt schema's one-key/four-key mismatch.
The four scientific Commit-A files remain byte-identical in Git. No HAI file
was opened and train3 was not reread. Public outcomes were reconstructed from
the original self-hashed 45-record private confirmation ledger.

## Calibration-confirmed candidates

- Directional confirmed/conflict: `{directional['confirmed_directional_count']}` / `{directional['conflict_directional_count']}`.
- Confirmed pairs / D1-supported pairs without confirmation: `{pair['pairs_with_confirmed_direction_count']}` / `{pair['d1_supported_pairs_without_confirmed_direction_count']}`.
- META: `{arms['META']['d2_confirmed_pair_count']}/20` pairs, `{arms['META']['directional_confirmation_count']}` directions.
- STAT: `{arms['STAT']['d2_confirmed_pair_count']}/20` pairs, `{arms['STAT']['directional_confirmation_count']}` directions.
- GDN: `{arms['GDN']['d2_confirmed_pair_count']}/20` pairs, `{arms['GDN']['directional_confirmation_count']}` directions.
- Confirmed union: `{overlap['confirmed_union_count']}`; shared by exactly two arms: `{overlap['shared_by_exactly_two_count']}`; all three: `{overlap['all_three']['count']}`.

These are calibration-confirmed normal delayed-response relation candidates,
not causal truth, ground truth, verified rules, root causes, or anomaly
performance. No candidate-method winner was selected.

## Recovery boundary

- Original scientific Commit A: `{receipt['execution_code_commit']}`.
- Result-contract Recovery Commit R: `{recovery['result_contract_recovery_commit']}`.
- Original failed status: `{recovery['original_failed_status']}`.
- Frozen private ledger: `{recovery['original_private_d2_ledger_hash']}`.
- Train3 reread / HAI values accessed during recovery: `false` / `false`.
- Scientific outcomes recomputed from HAI: `false`.
- Scientific code changed: `false`.
- Rule v2, Agent, detector/runtime authority: `false`.
- Required next task: `TASK-039D2-AUDIT`.
"""


def finalize(recovery_commit: str) -> None:
    _validate_authorization_before_roots()
    _validate_recovery_commit(recovery_commit)
    custody = _load(CUSTODY_PATH)
    verify_recovery_self_hash_v1(custody)
    if custody.get("status") != "verified_task039d2_failed_run_custody" or custody.get("private_ledger_hash") != PRIVATE_D2_LEDGER_HASH:
        raise TASK039D2RecoveryError("blocked_task039d2r_private_ledger_custody")
    d1_pair, d1_arm = _validate_public_d1()
    _, private_ledger, joined = _load_private_bindings()
    validation, d2r_private_root = joined
    if validation.confirmed_count != 42 or validation.conflict_count != 3:
        raise TASK039D2RecoveryError("failed_task039d2r_frozen_ledger_reconstruction")

    directional = build_directional_summary_from_frozen_ledger_v1(private_ledger)
    pair = build_pair_summary_from_frozen_ledger_v1(d1_pair_summary=d1_pair, directional_summary=directional)
    directional_path = REPORTS / PUBLIC_OUTPUTS["directional"]
    pair_path = REPORTS / PUBLIC_OUTPUTS["pair"]
    write_public_json_v1(directional_path, directional)
    write_public_json_v1(pair_path, pair)

    provenance = load_provenance_after_recovery_outcomes_frozen_v1(
        provenance_path=PROVENANCE_PATH, directional_path=directional_path, pair_path=pair_path,
        expected_directional_hash=directional["artifact_hash"], expected_pair_hash=pair["artifact_hash"],
    )
    arm = build_arm_summary_from_frozen_ledger_v1(
        d1_arm_summary=d1_arm, pair_summary=pair, directional_summary=directional, provenance=provenance,
    )
    assert_reconstruction_invariance_v1(directional=directional, pair=pair, arm=arm)
    access = build_recovery_data_access_audit_v1()
    result = build_result_from_frozen_ledger_v1(directional=directional, pair=pair, arm=arm, access=access)
    scientific_hashes = verify_scientific_sources_unchanged_v1(ROOT, ORIGINAL_COMMIT_A)
    receipt = build_execution_receipt_from_frozen_ledger_v1(
        scientific_source_hashes=scientific_hashes, directional=directional, pair=pair,
        arm=arm, result=result, access=access,
    )
    corrected_schema_hash = _sha256(CORRECTED_SCHEMA_PATH)
    for document in (directional, pair, arm, access, result, receipt):
        if document["artifact_type"].startswith("task039d2r_"):
            verify_recovery_self_hash_v1(document)
        else:
            verify_d2_self_hash_v1(document)
        _validate_schema(document)
    recovery = build_recovery_receipt_v1(
        recovery_commit=recovery_commit, custody_hash=custody["artifact_hash"],
        corrected_schema_hash=corrected_schema_hash, scientific_source_hashes=scientific_hashes,
        directional=directional, pair=pair, arm=arm, access=access,
        execution_receipt=receipt, result=result,
    )
    _validate_schema(recovery)
    _write_private_validation_binding(d2r_private_root, custody["artifact_hash"])

    for key, document in (
        ("access", access), ("arm", arm), ("result", result), ("receipt", receipt), ("recovery", recovery),
    ):
        write_public_json_v1(REPORTS / PUBLIC_OUTPUTS[key], document)
    (REPORTS / PUBLIC_OUTPUTS["report"]).write_text(
        _report(directional=directional, pair=pair, arm=arm, result=result, access=access, receipt=receipt, recovery=recovery),
        encoding="utf-8", newline="\n",
    )
    print(f"[TASK-039D2R] {SCIENTIFIC_STATUS}", flush=True)
    print(f"[TASK-039D2R] {RECOVERY_STATUS}", flush=True)


def main() -> int:
    args = _arguments()
    if args.schemas_only:
        _write_schemas()
        return 0
    if args.custody_only:
        create_custody()
        return 0
    if not args.recovery_commit:
        raise TASK039D2RecoveryError("--recovery-commit is required")
    finalize(args.recovery_commit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
