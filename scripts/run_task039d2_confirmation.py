"""Generate D2 schemas or execute one authorized train3 confirmation run."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Mapping

from paperworks.profiling.task039d1_fit_v1 import verify_d1_self_hash_v1
from paperworks.profiling.task039d2_real_execution_v1 import (
    ARTIFACT_CLASSES,
    AUDIT_COMMIT,
    BRANCH,
    D1_ARM_SUMMARY_HASH,
    D1_FIT_RESULT_HASH,
    D1_PAIR_SUMMARY_HASH,
    D2_AUTHORIZATION_HASH,
    PREP_COMMIT,
    PRIVATE_D2_NAME,
    STATUS,
    D2DataAccessStateV1,
    TASK039D2ExecutionError,
    build_arm_summary_v1,
    build_data_access_audit_v1,
    build_directional_summary_v1,
    build_execution_receipt_v1,
    build_pair_summary_v1,
    build_result_v1,
    confirm_relations_one_way_v1,
    d2_schema_examples_v1,
    expected_train3_identity_v1,
    load_authorized_train3_values_v1,
    load_d1_private_inputs_v1,
    load_provenance_after_outcomes_frozen_v1,
    schema_for_d2_artifact_v1,
    validate_authorization_v1,
    validate_external_roots_v1,
    verify_d2_self_hash_v1,
    write_json_v1,
)
from paperworks.profiling.task039d1_final_audit_v1 import verify_audit_self_hash_v1
from paperworks.profiling.task039d2_result_recovery_v1 import (
    bind_exact_four_source_hash_schema_v1,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"
AUTHORIZATION_PATH = REPORTS / "TASK-039D2_AUTHORIZATION.json"
PROVENANCE_PATH = REPORTS / "TASK-039D0_PROVENANCE_ANALYSIS_VIEW.json"

SCHEMA_FILES = {
    "task039d2_data_access_audit_v1": "task039d2_data_access_audit_v1_schema.json",
    "task039d2_directional_confirmation_summary_v1": "task039d2_directional_confirmation_summary_v1_schema.json",
    "task039d2_pair_confirmation_summary_v1": "task039d2_pair_confirmation_summary_v1_schema.json",
    "task039d2_arm_confirmation_summary_v1": "task039d2_arm_confirmation_summary_v1_schema.json",
    "task039d2_result_v1": "task039d2_result_v1_schema.json",
    "task039d2_real_execution_receipt_v1": "task039d2_real_execution_receipt_v1_schema.json",
}

PUBLIC_OUTPUTS = {
    "access": "TASK-039D2_DATA_ACCESS_AUDIT.json",
    "directional": "TASK-039D2_DIRECTIONAL_CONFIRMATION_SUMMARY.json",
    "pair": "TASK-039D2_PAIR_CONFIRMATION_SUMMARY.json",
    "arm": "TASK-039D2_ARM_CONFIRMATION_SUMMARY.json",
    "result": "TASK-039D2_RESULT.json",
    "receipt": "TASK-039D2_EXECUTION_RECEIPT.json",
    "report": "TASK-039D2_REPORT.md",
}

SCIENTIFIC_SOURCES = (
    "src/paperworks/profiling/task039d2_real_execution_v1.py",
    "src/paperworks/profiling/task039d2_confirmation_v1.py",
    "src/paperworks/profiling/task039d1_execution_optimization_v1.py",
    "src/paperworks/v6/relation_profiling_protocol_v1.py",
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
        raise TASK039D2ExecutionError(f"required artifact unavailable: {path.name}") from exc
    if not isinstance(value, dict):
        raise TASK039D2ExecutionError(f"artifact must be an object: {path.name}")
    return value


def _git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.resolve().as_posix()}", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode:
        raise TASK039D2ExecutionError("Git lineage verification failed")
    return result.stdout.strip() if result.returncode == 0 else ""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_schemas() -> None:
    examples = d2_schema_examples_v1()
    expected = {item.ARTIFACT_TYPE for item in ARTIFACT_CLASSES}
    if set(examples) != expected or set(SCHEMA_FILES) != expected:
        raise TASK039D2ExecutionError("D2 schema example coverage mismatch")
    for artifact_type, filename in SCHEMA_FILES.items():
        schema = schema_for_d2_artifact_v1(examples[artifact_type])
        if artifact_type == "task039d2_real_execution_receipt_v1":
            schema = bind_exact_four_source_hash_schema_v1(schema)
        write_json_v1(
            ROOT / "schemas" / "v6" / filename,
            schema,
            public=True,
        )


def _validate_commit_a(execution_commit: str) -> str:
    if len(execution_commit) != 40 or _git("branch", "--show-current") != BRANCH:
        raise TASK039D2ExecutionError("blocked_task039d2_d1_audit_promotion_mismatch")
    if _git("rev-parse", "HEAD") != execution_commit or _git("status", "--porcelain=v1"):
        raise TASK039D2ExecutionError("real D2 execution requires exact clean Commit A")
    _git("merge-base", "--is-ancestor", AUDIT_COMMIT, execution_commit)
    _git("merge-base", "--is-ancestor", PREP_COMMIT, execution_commit)
    if any((REPORTS / name).exists() for name in PUBLIC_OUTPUTS.values()):
        raise TASK039D2ExecutionError("real D2 result existed before execution")
    merge_commit = _git(
        "rev-list", "--merges", "--first-parent", "--max-count=1",
        f"{AUDIT_COMMIT}..{execution_commit}",
    )
    if len(merge_commit) != 40:
        raise TASK039D2ExecutionError("synthetic-prep merge commit is unavailable")
    return merge_commit


def _validate_public_inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    fit = _load_json(REPORTS / "TASK-039D1_FIT_RESULT.json")
    pair = _load_json(REPORTS / "TASK-039D1_PAIR_FIT_SUMMARY.json")
    arm = _load_json(REPORTS / "TASK-039D1_ARM_FIT_SUMMARY.json")
    for document, digest in (
        (fit, D1_FIT_RESULT_HASH),
        (pair, D1_PAIR_SUMMARY_HASH),
        (arm, D1_ARM_SUMMARY_HASH),
    ):
        if verify_d1_self_hash_v1(document) != digest:
            raise TASK039D2ExecutionError("failed_task039d2_private_input_binding")
    audit = _load_json(REPORTS / "TASK-039D1_FINAL_AUDIT.json")
    verify_audit_self_hash_v1(audit)
    if audit.get("status") != "passed_task039d1_final_audit" or audit.get("readiness") != "READY_FOR_TASK039D2":
        raise TASK039D2ExecutionError("blocked_task039d2_authorization_mismatch")
    return fit, pair, arm


def _report(
    *, directional: Mapping[str, Any], pair: Mapping[str, Any], arm: Mapping[str, Any],
    result: Mapping[str, Any], access: Mapping[str, Any], receipt: Mapping[str, Any],
) -> str:
    arms = {item["arm"]: item for item in arm["arms"]}
    overlap = arm["confirmed_pair_overlap"]
    return f"""# TASK-039D2 Report

Status: `{result['status']}`

TASK-039D2 applied the preregistered one-way train3 confirmation gate to the
exact 45 D1 fit-supported directional relation candidates. It performed no
refitting, retuning, alternative-horizon search, opposite-direction search, or
fallback. These are calibration-confirmed candidates, not causal relations,
rules, or anomaly-performance results.

## Scientific outcomes

- Confirmed/conflict directional relations: `{directional['confirmed_directional_count']}` / `{directional['conflict_directional_count']}`.
- Candidate pairs with at least one confirmed direction: `{pair['pairs_with_confirmed_direction_count']}`.
- D1-supported pairs without a confirmed direction: `{pair['d1_supported_pairs_without_confirmed_direction_count']}`.
- META: `{arms['META']['d2_confirmed_pair_count']}/20` confirmed pairs, `{arms['META']['directional_confirmation_count']}` confirmed directions.
- STAT: `{arms['STAT']['d2_confirmed_pair_count']}/20` confirmed pairs, `{arms['STAT']['directional_confirmation_count']}` confirmed directions.
- GDN: `{arms['GDN']['d2_confirmed_pair_count']}/20` confirmed pairs, `{arms['GDN']['directional_confirmation_count']}` confirmed directions.
- Confirmed union: `{overlap['confirmed_union_count']}`; shared by exactly two arms: `{overlap['shared_by_exactly_two_count']}`; all three: `{overlap['all_three']['count']}`.
- Candidate-method winner selected: `false`.

## Boundary and lineage

- D2 authorization: `{result['authorization_hash']}`.
- Execution-code commit: `{receipt['execution_code_commit']}`.
- Synthetic-prep merge: `{receipt['synthetic_prep_merge_commit']}`.
- Train3 accessed: `{str(access['train3_accessed']).lower()}`.
- Train1/train2 values accessed: `false`.
- Train4/test/labels/attacks accessed: `false`.
- D1 private ledgers accessed/modified: `true` / `false`.
- Candidate provenance visible during confirmation: `false`.
- BR2 pair results accessed: `false`.
- Rule v2, Agent, and runtime authority: `false`.
- Recommended next task: `TASK-039D2-AUDIT`.
"""


def execute(execution_commit: str) -> None:
    # The authorization is validated before any environment-root, private-ledger,
    # or dataset path is examined.
    authorization = _load_json(AUTHORIZATION_PATH)
    validate_authorization_v1(authorization)
    if authorization["artifact_hash"] != D2_AUTHORIZATION_HASH:
        raise TASK039D2ExecutionError("blocked_task039d2_authorization_mismatch")

    prep_merge_commit = _validate_commit_a(execution_commit)
    _, d1_pair, d1_arm = _validate_public_inputs()

    data_root, d1_private_root, d2_private_root = validate_external_roots_v1(
        repository_root=ROOT,
        data_root_value=os.environ.get("HAI_DATA_ROOT", ""),
        d1_private_value=os.environ.get("TASK039D_PRIVATE_ROOT", ""),
        d2_private_value=os.environ.get("TASK039D2_PRIVATE_ROOT", ""),
    )
    if d2_private_root.exists() and any(d2_private_root.iterdir()):
        raise TASK039D2ExecutionError("D2 private output root must be new or empty")
    d2_private_root.mkdir(parents=True, exist_ok=True)

    private_inputs = load_d1_private_inputs_v1(d1_private_root)
    print("[TASK-039D2] D1 private inputs verified: 45 relations", flush=True)
    expected_file = expected_train3_identity_v1(ROOT)
    state = D2DataAccessStateV1()
    values, file_record = load_authorized_train3_values_v1(
        data_root=data_root, expected=expected_file, state=state,
    )
    print("[TASK-039D2] authorized train3 file loaded", flush=True)

    outcome = confirm_relations_one_way_v1(values=values, private_inputs=private_inputs)
    private_ledger = outcome["ledger"]
    private_path = (d2_private_root / PRIVATE_D2_NAME).resolve()
    if not private_path.is_relative_to(d2_private_root.resolve()):
        raise TASK039D2ExecutionError("private output escaped D2 root")
    write_json_v1(private_path, private_ledger, public=False)
    print("[TASK-039D2] 45 one-way confirmations frozen", flush=True)

    directional = build_directional_summary_v1(private_ledger)
    pair = build_pair_summary_v1(d1_pair_summary=d1_pair, directional_summary=directional)
    directional_path = REPORTS / PUBLIC_OUTPUTS["directional"]
    pair_path = REPORTS / PUBLIC_OUTPUTS["pair"]
    write_json_v1(directional_path, directional, public=True)
    write_json_v1(pair_path, pair, public=True)
    print("[TASK-039D2] arm-blind directional and pair outcomes frozen", flush=True)

    provenance = load_provenance_after_outcomes_frozen_v1(
        provenance_path=PROVENANCE_PATH,
        directional_path=directional_path,
        pair_path=pair_path,
        expected_directional_hash=directional["artifact_hash"],
        expected_pair_hash=pair["artifact_hash"],
    )
    arm = build_arm_summary_v1(
        d1_arm_summary=d1_arm, pair_summary=pair,
        directional_summary=directional, provenance=provenance,
    )
    access = build_data_access_audit_v1(state=state, file_record=file_record)
    result = build_result_v1(
        directional=directional, pair=pair, arm=arm, access=access,
        private_ledger_hash=private_ledger["artifact_hash"],
    )
    source_hashes = {relative: _sha256(ROOT / relative) for relative in SCIENTIFIC_SOURCES}
    receipt = build_execution_receipt_v1(
        execution_code_commit=execution_commit,
        prep_merge_commit=prep_merge_commit,
        scientific_source_hashes=source_hashes,
        private_ledger_hash=private_ledger["artifact_hash"],
        directional=directional, pair=pair, arm=arm, result=result, access=access,
    )
    for document in (directional, pair, arm, access, result, receipt):
        verify_d2_self_hash_v1(document)
    for key, document in (("arm", arm), ("access", access), ("result", result), ("receipt", receipt)):
        write_json_v1(REPORTS / PUBLIC_OUTPUTS[key], document, public=True)
    (REPORTS / PUBLIC_OUTPUTS["report"]).write_text(
        _report(directional=directional, pair=pair, arm=arm, result=result, access=access, receipt=receipt),
        encoding="utf-8", newline="\n",
    )
    print(f"[TASK-039D2] {STATUS}", flush=True)


def main() -> int:
    args = _arguments()
    if args.schemas_only:
        _write_schemas()
        return 0
    if not args.execution_code_commit:
        raise TASK039D2ExecutionError("--execution-code-commit is required")
    execute(args.execution_code_commit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
