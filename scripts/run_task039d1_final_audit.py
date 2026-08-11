"""Execute the independent TASK-039D1 final audit replay."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Mapping

from paperworks.profiling.task039d1_execution_optimization_v1 import (
    audit_event_semantic_parity_v1,
    audit_isolation_semantic_parity_v1,
    audit_structural_complexity_v1,
    verify_recovery_artifact_v1,
)
from paperworks.profiling.task039d1_final_audit_v1 import (
    ABORTED_A1,
    ACCESS_AUDIT_HASH,
    ARM_SUMMARY_HASH,
    COMPLEXITY_RECEIPT_HASH,
    D0_PROTOCOL_BUNDLE_HASH,
    D1_AUTHORIZATION_HASH,
    DIRECTIONAL_LEDGER_HASH,
    EXECUTION_A2,
    EXECUTION_RECEIPT_HASH,
    FIT_RESULT_HASH,
    MAIN_COMMIT,
    PAIR_SUMMARY_HASH,
    PROFILING_IDENTITY_VIEW_HASH,
    PROVENANCE_ANALYSIS_VIEW_HASH,
    READINESS,
    RESULT_B2,
    SOURCE_LEDGER_HASH,
    STATUS,
    TARGET_LEDGER_HASH,
    TASK039D1FinalAuditError,
    audit_schema_examples_v1,
    build_d2_authorization_v1,
    build_final_audit_v1,
    replay_arm_summary_after_freeze_v1,
    replay_d1_independently_v1,
    schema_for_audit_artifact_v1,
    verify_audit_self_hash_v1,
    write_json_v1,
)
from paperworks.profiling.task039d1_fit_v1 import (
    DataAccessStateV1,
    assert_public_payload_safe_v1,
    load_authorized_fit_values_v1,
    load_expected_file_identities_v1,
    verify_d1_self_hash_v1,
)
from paperworks.v6.relation_profiling_protocol_v1 import verify_self_hash_v1


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"
BRANCH = "task-039d1-final-audit"
PRIVATE_NAMES = {
    "source": "TASK-039D1_SOURCE_PARAMETER_LEDGER.json",
    "target": "TASK-039D1_TARGET_PARAMETER_LEDGER.json",
    "directional": "TASK-039D1_DIRECTIONAL_FIT_LEDGER.json",
}
ALLOWED_AUDIT_PATHS = frozenset(
    {
        "src/paperworks/profiling/task039d1_final_audit_v1.py",
        "scripts/run_task039d1_final_audit.py",
        "schemas/v6/task039d1_final_audit_v1_schema.json",
        "schemas/v6/task039d2_authorization_v1_schema.json",
        "src/paperworks/v6/schema_registry_v1.py",
        "tests/test_task039c0_reports.py",
        "tests/test_task039d0_relation_profiling_protocol.py",
        "tests/test_task039d1_fit_contracts.py",
        "tests/test_task039d1_reporting.py",
        "tests/test_task039d1r_recovery_receipts.py",
        "tests/test_task039p1c_schema_and_boundaries.py",
        "tests/test_task039d1_final_audit_contracts.py",
        "tests/test_task039d1_independent_replay.py",
        "tests/test_task039d2_authorization.py",
        "docs/task_reports/TASK-039D1_FINAL_AUDIT.json",
        "docs/task_reports/TASK-039D1_FINAL_AUDIT.md",
        "docs/task_reports/TASK-039D2_AUTHORIZATION.json",
    }
)


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.resolve().as_posix()}", "-C", str(ROOT), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise TASK039D1FinalAuditError("Git lineage verification failed")
    return result.stdout.rstrip()


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TASK039D1FinalAuditError(f"required artifact unavailable: {path.name}") from exc
    if not isinstance(value, dict):
        raise TASK039D1FinalAuditError("artifact must be an object")
    return value


def _validate_git_and_patch_scope() -> None:
    if _git("branch", "--show-current") != BRANCH or _git("rev-parse", "HEAD") != RESULT_B2:
        raise TASK039D1FinalAuditError("failed_task039d1_commit_separation")
    if _git("rev-parse", f"{RESULT_B2}^") != EXECUTION_A2:
        raise TASK039D1FinalAuditError("failed_task039d1_commit_separation")
    if _git("rev-parse", f"{EXECUTION_A2}^") != ABORTED_A1:
        raise TASK039D1FinalAuditError("failed_task039d1_commit_separation")
    if _git("rev-parse", "origin/main") != MAIN_COMMIT:
        raise TASK039D1FinalAuditError("failed_task039d1_commit_separation")
    b2_changed = tuple(_git("diff", "--name-only", EXECUTION_A2, RESULT_B2).splitlines())
    expected_b2 = (
        "docs/task_reports/TASK-039D1_ARM_FIT_SUMMARY.json",
        "docs/task_reports/TASK-039D1_DATA_ACCESS_AUDIT.json",
        "docs/task_reports/TASK-039D1_EXECUTION_RECEIPT.json",
        "docs/task_reports/TASK-039D1_FIT_RESULT.json",
        "docs/task_reports/TASK-039D1_PAIR_FIT_SUMMARY.json",
        "docs/task_reports/TASK-039D1_REPORT.md",
    )
    if b2_changed != expected_b2:
        raise TASK039D1FinalAuditError("failed_task039d1_commit_separation")
    changed = {
        item.replace("\\", "/")
        for item in _git("status", "--porcelain=v1", "--untracked-files=all").splitlines()
        if item
    }
    paths = {item[3:] for item in changed}
    if paths - ALLOWED_AUDIT_PATHS:
        raise TASK039D1FinalAuditError("audit patch exceeds task-owned paths")
    frozen_delta = _git(
        "diff", "--name-only", ABORTED_A1, EXECUTION_A2, "--",
        "src/paperworks/v6/continuous_step_protocol_v1.py",
        "src/paperworks/v6/relation_profiling_protocol_v1.py",
        "configs/v6/task039d0_relation_profiling_protocol.json",
    )
    if frozen_delta:
        raise TASK039D1FinalAuditError("D0 policy changed during recovery")


def _validate_external_roots() -> tuple[Path, Path, Path]:
    data_raw = os.environ.get("HAI_DATA_ROOT", "")
    original_raw = os.environ.get("TASK039D_PRIVATE_ROOT", "")
    audit_raw = os.environ.get("TASK039D_AUDIT_PRIVATE_ROOT", "")
    if not data_raw or not original_raw or not audit_raw:
        raise TASK039D1FinalAuditError("all audit roots must be explicit")
    repository = ROOT.resolve(strict=True)
    data_root = Path(data_raw).resolve(strict=True)
    original_root = Path(original_raw).resolve(strict=True)
    audit_candidate = Path(audit_raw)
    audit_root = audit_candidate.resolve(strict=audit_candidate.exists())
    roots = (data_root, original_root, audit_root)
    if len(set(roots)) != 3 or any(root.is_relative_to(repository) for root in roots):
        raise TASK039D1FinalAuditError("audit roots must be distinct and outside Git")
    if any(repository.is_relative_to(root) for root in roots):
        raise TASK039D1FinalAuditError("audit roots may not contain Git")
    original_names = {path.name for path in original_root.iterdir() if path.is_file()}
    if original_names != set(PRIVATE_NAMES.values()):
        raise TASK039D1FinalAuditError("failed_task039d1_private_ledger_audit")
    if audit_root.exists() and any(audit_root.iterdir()):
        raise TASK039D1FinalAuditError("audit private root must be new or empty")
    return data_root, original_root, audit_root


def _validate_public_before_replay() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    fit = _load(REPORTS / "TASK-039D1_FIT_RESULT.json")
    pair = _load(REPORTS / "TASK-039D1_PAIR_FIT_SUMMARY.json")
    access = _load(REPORTS / "TASK-039D1_DATA_ACCESS_AUDIT.json")
    for document, expected in (
        (fit, FIT_RESULT_HASH), (pair, PAIR_SUMMARY_HASH), (access, ACCESS_AUDIT_HASH),
    ):
        if verify_d1_self_hash_v1(document) != expected:
            raise TASK039D1FinalAuditError("public D1 artifact hash mismatch")
    if (
        fit["candidate_count"] != 47
        or fit["directional_opportunity_count"] != 94
        or fit["pair_fit_supported_count"] != 25
        or fit["directional_fit_supported_count"] != 45
        or fit["direction_unstable_count"] != 17
        or fit["fit_unsupported_directional_count"] != 32
    ):
        raise TASK039D1FinalAuditError("public D1 result count mismatch")
    forbidden = (
        "train3_accessed", "train4_accessed", "test_accessed", "labels_accessed",
        "attacks_accessed", "p2_p3_p4_values_accessed", "br2_pair_results_accessed",
        "candidate_arm_evidence_visible_during_profiling", "raw_values_persisted",
        "raw_windows_persisted", "event_timestamps_publicly_persisted",
        "absolute_local_paths_persisted",
    )
    if any(access[name] for name in forbidden) or access["prohibited_access_count"] != 0:
        raise TASK039D1FinalAuditError("failed_task039d1_data_boundary_audit")
    return fit, pair, access


def _validate_complexity_receipt() -> dict[str, Any]:
    receipt = _load(REPORTS / "TASK-039D1R_EXECUTION_COMPLEXITY_RECEIPT.json")
    if verify_recovery_artifact_v1(receipt) != COMPLEXITY_RECEIPT_HASH:
        raise TASK039D1FinalAuditError("complexity receipt hash mismatch")
    for relative, expected in receipt["source_file_hashes"].items():
        observed = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        if observed != expected:
            raise TASK039D1FinalAuditError("complexity receipt source binding mismatch")
    audit_event_semantic_parity_v1()
    audit_isolation_semantic_parity_v1()
    complexity = audit_structural_complexity_v1()
    if (
        receipt["scientific_formulas_changed"]
        or receipt["d0_policies_changed"]
        or receipt["unresolved_execution_complexity_defects"]
        or complexity["event_extraction_complexity_class"] != "linear_in_sequence_length"
    ):
        raise TASK039D1FinalAuditError("complexity recovery audit failed")
    return receipt


def _load_original_private(original_root: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    expected = {
        "source": (SOURCE_LEDGER_HASH, 12),
        "target": (TARGET_LEDGER_HASH, 12),
        "directional": (DIRECTIONAL_LEDGER_HASH, 94),
    }
    for key, filename in PRIVATE_NAMES.items():
        document = _load(original_root / filename)
        digest, count = expected[key]
        if verify_d1_self_hash_v1(document) != digest or document["record_count"] != count:
            raise TASK039D1FinalAuditError("failed_task039d1_private_ledger_audit")
        for record in document["records"]:
            verify_d1_self_hash_v1(record)
        result[key] = document
    return result


def _report(audit: Mapping[str, Any], authorization: Mapping[str, Any]) -> str:
    return f"""# TASK-039D1 Final Audit

Status: `{audit['status']}`
Readiness: `{audit['readiness']}`

The independent train1/train2 replay reproduced the D1 fit-supported normal
delayed-response relation candidates. It does not establish confirmation,
causality, method superiority, rule validity, or anomaly performance.

## Independent replay

- Source records: `12` (`12` supported, `0` unsupported).
- Target records: `12`.
- Directional results: `45` fit-supported, `17` direction-unstable, `32` fit-unsupported.
- Pair results: `25` fit-supported, `22` unsupported.
- Pair-summary hash reproduced: `{audit['pair_replay']['pair_summary_hash']}`.
- Original private ledger hashes and all normalized records reproduced exactly.
- Provenance was loaded only after private replay ledgers and pair outcomes were frozen.

## Fit-only arm summaries

- META: `16/20`, yield `0.80`, `29` directions.
- STAT: `17/20`, yield `0.85`, `33` directions.
- GDN: `5/20`, yield `0.25`, `7` directions.
- Shared-pair invariance: `true`; winner selected: `false`.

## Boundaries and authorization

- Train1/train2 accessed by audit: `true` / `true`.
- Train3/train4/test/labels/attacks accessed: `false`.
- BR2 pair outcomes accessed: `false`.
- Rule v2 authorized: `false`.
- D2 executed: `false`.
- D2 authorization hash: `{authorization['artifact_hash']}`.
- A separate clean D2 execution-code commit is required before train3 access.

## Regression audit

- Audit/D1R/D1: `52` passing tests.
- D0, C0, META, STAT, and three-arm integration: `145` passing tests
  (`1` expected skip).
- BR1/BR2, HAI provenance, TASK-032, candidate, and relation suites: `255`
  passing tests.
- Exact GDN environment: `87` passing tests and `1` expected skip; the four
  diagnostics require the intentionally absent external GDN checkout or the
  historical GDNC execution branch.
- Minimal guarded discovery: `645` runnable tests, `53` classified optional
  imports, `9` expected missing-external/dependency diagnostics, and `1`
  historical inventory mismatch caused by additive audit files.
- Exact-environment guarded discovery: `967` runnable tests, `16` classified
  optional pytest imports, and only the corresponding external-checkout,
  historical-branch, optional-import-order, and additive-inventory diagnostics.
- Python compilation, `242` public JSON documents, `118` v6 schemas, `110`
  registered schemas, public/private self-hashes, both `pip check` runs,
  diff checks, and public boundary scans passed.

No unexplained scientific regression was found.
"""


def execute() -> dict[str, str]:
    _validate_git_and_patch_scope()
    data_root, original_root, audit_root = _validate_external_roots()
    _validate_complexity_receipt()
    _, original_pair, _ = _validate_public_before_replay()
    originals = _load_original_private(original_root)

    bundle = _load(REPORTS / "TASK-039D0_PROTOCOL_BUNDLE.json")
    authorization = _load(REPORTS / "TASK-039D1_AUTHORIZATION.json")
    identity = _load(REPORTS / "TASK-039D0_PROFILING_IDENTITY_VIEW.json")
    for document in (bundle, authorization, identity):
        verify_self_hash_v1(document)
    if (
        bundle["artifact_hash"] != D0_PROTOCOL_BUNDLE_HASH
        or authorization["artifact_hash"] != D1_AUTHORIZATION_HASH
        or identity["artifact_hash"] != PROFILING_IDENTITY_VIEW_HASH
    ):
        raise TASK039D1FinalAuditError("frozen D0 identity mismatch")

    state = DataAccessStateV1()
    expected_files = load_expected_file_identities_v1(ROOT)
    fit_values, file_records = load_authorized_fit_values_v1(
        data_root=data_root,
        expected_file_identities=expected_files,
        state=state,
    )
    bindings = {Path(item["relative_path"]).name: item["sha256"] for item in file_records}
    print("[TASK-039D1-AUDIT] authorized_fit_files_loaded_2_of_2", flush=True)
    replay = replay_d1_independently_v1(
        identity_view_document=identity,
        fit_values=fit_values,
        fit_file_bindings=bindings,
        original_source_ledger=originals["source"],
        original_target_ledger=originals["target"],
        original_directional_ledger=originals["directional"],
        original_pair_summary=original_pair,
        audit_private_root=audit_root,
        progress_callback=lambda message: print(f"[TASK-039D1-AUDIT] {message}", flush=True),
    )
    del fit_values

    # This is the first provenance read in the audit execution.
    provenance = _load(REPORTS / "TASK-039D0_PROVENANCE_ANALYSIS_VIEW.json")
    original_arm = _load(REPORTS / "TASK-039D1_ARM_FIT_SUMMARY.json")
    if verify_d1_self_hash_v1(original_arm) != ARM_SUMMARY_HASH:
        raise TASK039D1FinalAuditError("original arm-summary hash mismatch")
    arm_summary = replay_arm_summary_after_freeze_v1(
        pair_summary=replay["pair_summary"],
        provenance_document=provenance,
        original_arm_summary=original_arm,
        directional_ledger=replay["directional_ledger"],
    )

    execution_receipt = _load(REPORTS / "TASK-039D1_EXECUTION_RECEIPT.json")
    if verify_d1_self_hash_v1(execution_receipt) != EXECUTION_RECEIPT_HASH:
        raise TASK039D1FinalAuditError("execution receipt hash mismatch")

    d2 = build_d2_authorization_v1()
    data_boundary = {
        "dataset_file_identities_verified": True,
        "train1_accessed": state.train1_accessed,
        "train2_accessed": state.train2_accessed,
        "train3_accessed": False,
        "train4_accessed": False,
        "test_accessed": False,
        "labels_accessed": False,
        "attacks_accessed": False,
        "br2_pair_results_accessed": False,
        "candidate_arm_evidence_visible_during_replay": False,
        "provenance_loaded_after_replay_freeze": True,
        "raw_values_publicly_persisted": False,
        "raw_windows_publicly_persisted": False,
        "event_timestamps_publicly_persisted": False,
        "absolute_paths_publicly_persisted": False,
        "prohibited_access_count": state.prohibited_access_count,
    }
    audit_source_hash = hashlib.sha256(
        (ROOT / "src/paperworks/profiling/task039d1_final_audit_v1.py").read_bytes()
    ).hexdigest()
    audit = build_final_audit_v1(
        replay=replay,
        arm_summary=arm_summary,
        data_access_state=data_boundary,
        d2_authorization_hash=d2["artifact_hash"],
        audit_source_hash=audit_source_hash,
    )
    for document in (d2, audit):
        assert_public_payload_safe_v1(document)
        verify_audit_self_hash_v1(document)
    write_json_v1(REPORTS / "TASK-039D2_AUTHORIZATION.json", d2)
    write_json_v1(REPORTS / "TASK-039D1_FINAL_AUDIT.json", audit)
    (REPORTS / "TASK-039D1_FINAL_AUDIT.md").write_text(
        _report(audit, d2), encoding="utf-8", newline="\n"
    )
    write_json_v1(
        ROOT / "schemas/v6/task039d1_final_audit_v1_schema.json",
        schema_for_audit_artifact_v1(audit),
    )
    write_json_v1(
        ROOT / "schemas/v6/task039d2_authorization_v1_schema.json",
        schema_for_audit_artifact_v1(d2),
    )
    return {
        "status": STATUS,
        "readiness": READINESS,
        "audit_hash": audit["artifact_hash"],
        "d2_authorization_hash": d2["artifact_hash"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schemas-only", action="store_true")
    args = parser.parse_args()
    if args.schemas_only:
        audit, d2 = audit_schema_examples_v1()
        write_json_v1(
            ROOT / "schemas/v6/task039d1_final_audit_v1_schema.json",
            schema_for_audit_artifact_v1(audit),
        )
        write_json_v1(
            ROOT / "schemas/v6/task039d2_authorization_v1_schema.json",
            schema_for_audit_artifact_v1(d2),
        )
        print(json.dumps({"schemas_written": 2}, sort_keys=True))
        return 0
    print(json.dumps(execute(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
