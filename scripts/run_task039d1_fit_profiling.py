"""Freeze schemas or execute TASK-039D1 from its clean Commit A."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Mapping

from paperworks.profiling.task039d1_fit_v1 import (
    ARTIFACT_CLASSES,
    AUTHORIZED_RELATIVE_FILES,
    BASE_COMMIT,
    BRANCH,
    D0_CONFIG_HASH,
    D0_PROTOCOL_BUNDLE_HASH,
    D1_AUTHORIZATION_HASH,
    PRIVATE_DIRECTIONAL_LEDGER_NAME,
    PRIVATE_SOURCE_LEDGER_NAME,
    PRIVATE_TARGET_LEDGER_NAME,
    PROFILING_IDENTITY_VIEW_HASH,
    PROVENANCE_ANALYSIS_VIEW_HASH,
    RESULT_PATH_NAMES,
    STATUS,
    DataAccessStateV1,
    TASK039D1DirectionalFitLedgerBindingV1,
    TASK039D1Error,
    TASK039D1SourceParameterLedgerBindingV1,
    TASK039D1TargetParameterLedgerBindingV1,
    build_arm_fit_summary_v1,
    build_data_access_audit_v1,
    build_execution_receipt_v1,
    build_fit_result_v1,
    d1_schema_examples_v1,
    evaluate_arm_blind_fit_v1,
    ledger_binding_v1,
    load_authorized_fit_values_v1,
    load_expected_file_identities_v1,
    load_provenance_after_outcomes_frozen_v1,
    schema_for_d1_artifact_v1,
    source_file_sha256_v1,
    validate_external_roots_v1,
    verify_d1_self_hash_v1,
    write_json_v1,
)
from paperworks.profiling.task039d1_execution_optimization_v1 import (
    ABORTED_COMMIT_A1,
    RECOVERY_BRANCH,
    RECOVERY_STATUS,
    verify_recovery_artifact_v1,
)
from paperworks.v6.relation_profiling_protocol_v1 import verify_self_hash_v1


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"
IDENTITY_PATH = REPORTS / "TASK-039D0_PROFILING_IDENTITY_VIEW.json"
PROVENANCE_PATH = REPORTS / "TASK-039D0_PROVENANCE_ANALYSIS_VIEW.json"
COMPLEXITY_RECEIPT_PATH = REPORTS / "TASK-039D1R_EXECUTION_COMPLEXITY_RECEIPT.json"
ABORTED_RECORD_PATH = REPORTS / "TASK-039D1_ABORTED_EXECUTION_RECORD.json"

SCHEMA_FILES = {
    "task039d1_source_parameter_ledger_binding_v1": "task039d1_source_parameter_ledger_binding_v1_schema.json",
    "task039d1_target_parameter_ledger_binding_v1": "task039d1_target_parameter_ledger_binding_v1_schema.json",
    "task039d1_directional_fit_ledger_binding_v1": "task039d1_directional_fit_ledger_binding_v1_schema.json",
    "task039d1_pair_fit_summary_v1": "task039d1_pair_fit_summary_v1_schema.json",
    "task039d1_fit_result_v1": "task039d1_fit_result_v1_schema.json",
    "task039d1_arm_fit_summary_v1": "task039d1_arm_fit_summary_v1_schema.json",
    "task039d1_data_access_audit_v1": "task039d1_data_access_audit_v1_schema.json",
    "task039d1_execution_receipt_v1": "task039d1_execution_receipt_v1_schema.json",
}

ALLOWED_COMMIT_A2_PATHS = frozenset(
    {
        "TASKS/TASK-039D1R_COMPLEXITY_RECOVERY.md",
        "docs/task_reports/TASK-039D1R_EXECUTION_COMPLEXITY_RECEIPT.json",
        "docs/task_reports/TASK-039D1_ABORTED_EXECUTION_RECORD.json",
        "src/paperworks/profiling/task039d1_fit_v1.py",
        "src/paperworks/profiling/task039d1_execution_optimization_v1.py",
        "scripts/run_task039d1_fit_profiling.py",
        "scripts/audit_task039d1r_complexity.py",
        "schemas/v6/task039d1_aborted_execution_record_v1_schema.json",
        "schemas/v6/task039d1_execution_complexity_receipt_v1_schema.json",
        "schemas/v6/task039d1_execution_receipt_v1_schema.json",
        "src/paperworks/v6/schema_registry_v1.py",
        "tests/test_task039c0_reports.py",
        "tests/test_task039d0_relation_profiling_protocol.py",
        "tests/test_task039p1c_schema_and_boundaries.py",
        "tests/test_task039d1_fit_contracts.py",
        "tests/test_task039d1r_event_optimization.py",
        "tests/test_task039d1r_isolation_optimization.py",
        "tests/test_task039d1r_hot_path.py",
        "tests/test_task039d1r_recovery_receipts.py",
    }
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schemas-only", action="store_true")
    parser.add_argument("--execution-code-commit")
    return parser.parse_args()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TASK039D1Error(f"required artifact unavailable: {path.name}") from exc
    if not isinstance(value, dict):
        raise TASK039D1Error(f"artifact must be an object: {path.name}")
    return value


def _git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.resolve().as_posix()}", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode:
        raise TASK039D1Error("Git lineage verification failed")
    return result.stdout.strip() if result.returncode == 0 else ""


def _validate_frozen_d0() -> tuple[dict[str, Any], dict[str, Any]]:
    bundle = _load_json(REPORTS / "TASK-039D0_PROTOCOL_BUNDLE.json")
    authorization = _load_json(REPORTS / "TASK-039D1_AUTHORIZATION.json")
    identity = _load_json(IDENTITY_PATH)
    provenance = _load_json(PROVENANCE_PATH)
    config = _load_json(ROOT / "configs/v6/task039d0_relation_profiling_protocol.json")
    for document in (bundle, authorization, identity, provenance, config):
        verify_self_hash_v1(document)
    if (
        bundle["artifact_hash"] != D0_PROTOCOL_BUNDLE_HASH
        or authorization["artifact_hash"] != D1_AUTHORIZATION_HASH
        or identity["artifact_hash"] != PROFILING_IDENTITY_VIEW_HASH
        or provenance["artifact_hash"] != PROVENANCE_ANALYSIS_VIEW_HASH
        or config["artifact_hash"] != D0_CONFIG_HASH
        or bundle["status"] != "passed_task039d0_relation_profiling_protocol_freeze"
        or bundle["real_hai_feature_access"]
        or not authorization["real_fit_profiling_authorized"]
        or authorization["train3_authorized"]
        or authorization["train4_authorized"]
        or authorization["candidate_arm_evidence_visible_to_profiler"]
    ):
        raise TASK039D1Error("blocked_task039d1_authorization_mismatch")
    expected_components = {
        "source_scale_policy": "47831757a6f66e0c860a0589391f610aa99213291278861a8c5f260a7fe54233",
        "event_policy": "1f07a72b380b9ffb2ceb42e029517ef42716145062a57b1770d118b9db252342",
        "target_response_policy": "4b007b9511152396e03722ad8ce0e9cf659ebef2760cef5110414e4ce4bcbeaf",
        "direction_selection_policy": "0026c57f83502f67b1a0d055b22eec42ac08e05eeb6709ffe9cb55ee28d5839b",
        "fit_gate_policy": "da2442ad641aa035c37e738bd8a20521f3e5b46a1801f02fee8dbdcba3520344",
        "confirmation_policy": "83419f6acefaeb21ebc329d5ff9df8563e9636da72ad5367318a172df8fb0b27",
        "method_comparison_policy": "0ccc7a97a5e9b3fe1e5a8a54828ec8f8f7e6482c62eb63f7df62d804c8cae39e",
        "numeric_evidence_policy": "2cdc0b12724f549a165d7fad870b69b602d4eb0c2e0006dcd1780c88c2b8fcbc",
    }
    if any(bundle[name]["artifact_hash"] != digest for name, digest in expected_components.items()):
        raise TASK039D1Error("blocked_task039d1_authorization_mismatch")
    return identity, authorization


def _validate_commit_a(execution_commit: str) -> None:
    if len(execution_commit) != 40:
        raise TASK039D1Error("execution-code commit must be a full SHA")
    if _git("branch", "--show-current") != RECOVERY_BRANCH:
        raise TASK039D1Error("blocked_task039d1_d0_promotion_mismatch")
    if (
        _git("rev-parse", "HEAD") != execution_commit
        or _git("rev-parse", "HEAD^") != ABORTED_COMMIT_A1
    ):
        raise TASK039D1Error("blocked_task039d1_d0_promotion_mismatch")
    if _git("status", "--porcelain=v1"):
        raise TASK039D1Error("real execution requires a clean Commit A")
    changed = {
        item.replace("\\", "/")
        for item in _git("diff", "--name-only", ABORTED_COMMIT_A1, execution_commit).splitlines()
        if item
    }
    prohibited = sorted(changed - ALLOWED_COMMIT_A2_PATHS)
    if prohibited:
        raise TASK039D1Error("failed_task039d1_protocol_compliance: " + ", ".join(prohibited))
    existing = [name for name in RESULT_PATH_NAMES if (REPORTS / name).exists()]
    if existing:
        raise TASK039D1Error("D1 real-result file existed before execution")


def _validate_recovery_receipts() -> tuple[dict[str, Any], dict[str, Any]]:
    complexity = _load_json(COMPLEXITY_RECEIPT_PATH)
    aborted = _load_json(ABORTED_RECORD_PATH)
    verify_recovery_artifact_v1(complexity)
    verify_recovery_artifact_v1(aborted)
    if (
        complexity.get("status") != RECOVERY_STATUS
        or complexity.get("original_aborted_commit_a") != ABORTED_COMMIT_A1
        or complexity.get("d0_protocol_bundle_hash") != D0_PROTOCOL_BUNDLE_HASH
        or complexity.get("d1_authorization_hash") != D1_AUTHORIZATION_HASH
        or complexity.get("scientific_formulas_changed")
        or complexity.get("d0_policies_changed")
        or complexity.get("unresolved_execution_complexity_defects")
        or complexity.get("hai_values_accessed_during_recovery_implementation")
        or aborted.get("original_d1_commit_a") != ABORTED_COMMIT_A1
        or aborted.get("private_ledgers_produced")
        or aborted.get("scientific_outcomes_frozen")
        or aborted.get("aborted_outputs_reused")
    ):
        raise TASK039D1Error("failed_task039d1r_recovery_boundary")
    return complexity, aborted


def _write_schemas() -> None:
    examples = d1_schema_examples_v1()
    expected_types = {item.ARTIFACT_TYPE for item in ARTIFACT_CLASSES}
    if set(examples) != expected_types or set(SCHEMA_FILES) != expected_types:
        raise TASK039D1Error("D1 schema example coverage mismatch")
    for artifact_type, filename in SCHEMA_FILES.items():
        write_json_v1(
            ROOT / "schemas/v6" / filename,
            schema_for_d1_artifact_v1(examples[artifact_type]),
            public=True,
        )


def _private_output_path(private_root: Path, name: str) -> Path:
    path = (private_root / name).resolve()
    if not path.is_relative_to(private_root.resolve()):
        raise TASK039D1Error("private artifact path escaped root")
    return path


def _report(
    *, fit: Mapping[str, Any], arm: Mapping[str, Any], access: Mapping[str, Any],
    receipt: Mapping[str, Any], recovery: Mapping[str, Any], aborted: Mapping[str, Any]
) -> str:
    arm_by_name = {item["arm"]: item for item in arm["arms"]}
    failures = fit["other_failure_counts"]
    return f"""# TASK-039D1 Report

Status: `{fit['status']}`

Recovery preflight: `{recovery['status']}`. The historical A1 execution at
`{aborted['original_d1_commit_a']}` was aborted without frozen scientific
outcomes or private ledgers. No partial scientific state was reused.

TASK-039D1 executed the common arm-blind normal relation fit protocol once for
the exact 47-pair cohort. The result describes fit-supported normal
delayed-response relation candidates; it does not establish confirmation,
causality, physical truth, rule validity, anomaly performance, or method
superiority.

## Scientific outcomes

- Source parameters supported/unsupported: `{fit['source_parameter_supported_count']}` / `{fit['source_parameter_unsupported_count']}`.
- Pair fit-supported/unsupported: `{fit['pair_fit_supported_count']}` / `{fit['pair_fit_unsupported_count']}`.
- Directional fit-supported: `{fit['directional_fit_supported_count']}` of `94`.
- Direction-unstable: `{fit['direction_unstable_count']}`.
- Fit-unsupported directional: `{fit['fit_unsupported_directional_count']}`.
- Source-parameter unsupported directional opportunities: `{failures['insufficient_nontrivial_amplitudes']}`.
- Selected-candidate fit-gate failures: `{failures['fit_gate_not_satisfied']}`.

Fit-only arm summaries are descriptive and reuse each shared pair outcome:

- META: `{arm_by_name['META']['pair_fit_supported_count']}/20` pairs (`{arm_by_name['META']['pair_fit_support_yield']}`), `{arm_by_name['META']['directional_fit_supported_count']}` directions.
- STAT: `{arm_by_name['STAT']['pair_fit_supported_count']}/20` pairs (`{arm_by_name['STAT']['pair_fit_support_yield']}`), `{arm_by_name['STAT']['directional_fit_supported_count']}` directions.
- GDN: `{arm_by_name['GDN']['pair_fit_supported_count']}/20` pairs (`{arm_by_name['GDN']['pair_fit_support_yield']}`), `{arm_by_name['GDN']['directional_fit_supported_count']}` directions.

No candidate-method winner was selected.

## Protocol validity and boundaries

- Exact D0 bundle: `{receipt['d0_protocol_bundle_hash']}`.
- Commit A: `{receipt['execution_code_commit']}`.
- Profiling identities: `47`; directional opportunities: `94`.
- Arm evidence visible during scientific profiling: `false`.
- Shared-pair D1 outcome invariant: `true`.
- Lower-ranked fallback used: `false`.
- Train1/train2 accessed: `{str(access['train1_accessed']).lower()}` / `{str(access['train2_accessed']).lower()}`.
- Train3/train4/test/labels/attacks accessed: `false`.
- BR2 pair results accessed: `false`.
- Raw values, windows, event timestamps, and absolute paths persisted publicly: `false`.
- Merged or cross-arm score used: `false`.
- Rule v2 authorized: `false`.
- TASK-039D2 authorized: `false`.

The required next task is `TASK-039D1-AUDIT`. No D2 authorization artifact was
created.
"""


def execute(execution_commit: str) -> None:
    _validate_commit_a(execution_commit)
    recovery, aborted = _validate_recovery_receipts()
    identity, _ = _validate_frozen_d0()
    expected_files = load_expected_file_identities_v1(ROOT)
    data_raw = os.environ.get("HAI_DATA_ROOT", "")
    private_raw = os.environ.get("TASK039D_PRIVATE_ROOT", "")
    data_root, private_root = validate_external_roots_v1(
        repository_root=ROOT,
        data_root_value=data_raw,
        private_root_value=private_raw,
    )
    if private_root.exists() and any(private_root.iterdir()):
        raise TASK039D1Error("private output root must be new or empty")
    private_root.mkdir(parents=True, exist_ok=True)

    state = DataAccessStateV1()
    fit_values, file_records = load_authorized_fit_values_v1(
        data_root=data_root,
        expected_file_identities=expected_files,
        state=state,
    )
    print("[TASK-039D1] authorized_fit_files_loaded_2_of_2", flush=True)
    fit_file_bindings = {
        Path(item["relative_path"]).name: str(item["sha256"]) for item in file_records
    }
    outcomes = evaluate_arm_blind_fit_v1(
        identity_view_document=identity,
        fit_values=fit_values,
        fit_file_bindings=fit_file_bindings,
        execution_code_commit=execution_commit,
        progress_callback=lambda message: print(f"[TASK-039D1] {message}", flush=True),
    )
    del fit_values

    private_documents = (
        (PRIVATE_SOURCE_LEDGER_NAME, outcomes["source_ledger"]),
        (PRIVATE_TARGET_LEDGER_NAME, outcomes["target_ledger"]),
        (PRIVATE_DIRECTIONAL_LEDGER_NAME, outcomes["directional_ledger"]),
    )
    for name, document in private_documents:
        path = _private_output_path(private_root, name)
        if path.exists():
            raise TASK039D1Error("private D1 ledger already exists")
        write_json_v1(path, document, public=False)
        verify_d1_self_hash_v1(_load_json(path))

    source_binding = ledger_binding_v1(
        TASK039D1SourceParameterLedgerBindingV1,
        ledger=outcomes["source_ledger"],
    )
    target_binding = ledger_binding_v1(
        TASK039D1TargetParameterLedgerBindingV1,
        ledger=outcomes["target_ledger"],
    )
    directional_binding = ledger_binding_v1(
        TASK039D1DirectionalFitLedgerBindingV1,
        ledger=outcomes["directional_ledger"],
    )
    access = build_data_access_audit_v1(state=state, file_records=file_records)
    fit = build_fit_result_v1(
        outcomes=outcomes,
        source_binding=source_binding,
        target_binding=target_binding,
        directional_binding=directional_binding,
        data_access_audit=access,
    )
    pair = outcomes["pair_summary"]

    access_path = REPORTS / "TASK-039D1_DATA_ACCESS_AUDIT.json"
    pair_path = REPORTS / "TASK-039D1_PAIR_FIT_SUMMARY.json"
    fit_path = REPORTS / "TASK-039D1_FIT_RESULT.json"
    write_json_v1(access_path, access.to_dict(), public=True)
    write_json_v1(pair_path, pair.to_dict(), public=True)
    write_json_v1(fit_path, fit.to_dict(), public=True)

    provenance = load_provenance_after_outcomes_frozen_v1(
        provenance_path=PROVENANCE_PATH,
        frozen_pair_summary_path=pair_path,
        expected_pair_summary_hash=pair.artifact_hash,
    )
    arm = build_arm_fit_summary_v1(
        pair_summary_document=pair.to_dict(),
        provenance_document=provenance,
    )
    arm_path = REPORTS / "TASK-039D1_ARM_FIT_SUMMARY.json"
    write_json_v1(arm_path, arm.to_dict(), public=True)

    source_hashes = {
        "src/paperworks/profiling/task039d1_fit_v1.py": source_file_sha256_v1(
            ROOT / "src/paperworks/profiling/task039d1_fit_v1.py"
        ),
        "src/paperworks/v6/relation_profiling_protocol_v1.py": source_file_sha256_v1(
            ROOT / "src/paperworks/v6/relation_profiling_protocol_v1.py"
        ),
        "src/paperworks/profiling/task039d1_execution_optimization_v1.py": source_file_sha256_v1(
            ROOT / "src/paperworks/profiling/task039d1_execution_optimization_v1.py"
        ),
    }
    receipt = build_execution_receipt_v1(
        execution_code_commit=execution_commit,
        scientific_source_hashes=source_hashes,
        source_binding=source_binding,
        target_binding=target_binding,
        directional_binding=directional_binding,
        pair_summary=pair,
        fit_result=fit,
        arm_summary=arm,
        data_access=access,
    )
    receipt_path = REPORTS / "TASK-039D1_EXECUTION_RECEIPT.json"
    write_json_v1(receipt_path, receipt.to_dict(), public=True)
    (REPORTS / "TASK-039D1_REPORT.md").write_text(
        _report(
            fit=fit.to_dict(),
            arm=arm.to_dict(),
            access=access.to_dict(),
            receipt=receipt.to_dict(),
            recovery=recovery,
            aborted=aborted,
        ),
        encoding="utf-8",
        newline="\n",
    )
    for path in (access_path, pair_path, fit_path, arm_path, receipt_path):
        verify_d1_self_hash_v1(_load_json(path))
    print(json.dumps({
        "status": STATUS,
        "source_ledger_hash": outcomes["source_ledger"]["artifact_hash"],
        "target_ledger_hash": outcomes["target_ledger"]["artifact_hash"],
        "directional_ledger_hash": outcomes["directional_ledger"]["artifact_hash"],
        "pair_summary_hash": pair.artifact_hash,
        "fit_result_hash": fit.artifact_hash,
        "arm_fit_summary_hash": arm.artifact_hash,
        "data_access_audit_hash": access.artifact_hash,
        "execution_receipt_hash": receipt.artifact_hash,
    }, sort_keys=True))


def main() -> int:
    args = _arguments()
    if args.schemas_only:
        _write_schemas()
        return 0
    if not args.execution_code_commit:
        raise TASK039D1Error("--execution-code-commit is required")
    execute(args.execution_code_commit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
