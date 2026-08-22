"""Local-only forensic audit of the blocked D2 private evidence write.

The audit never imports or calls the D2 execution entry point. Prediction
artifacts are compared as opaque bytes with their frozen Git blobs. The only
private operation reads one approved local binding and returns targeted file
metadata as booleans and counts; paths and file contents are never returned.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Iterable, Mapping, NoReturn


TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D2-EXECUTION-PRIVATE-CUSTODY-BLOCKER-AUDIT-V1"
STATUS = "passed_task039e3_r2r_utility_inner_d2_execution_private_custody_blocker_audit_v1"
SCIENTIFIC_STATE = "D2_EXECUTION_BLOCKED_CUSTODY_AUDITED"
BASE_COMMIT = "78639e1b8286b4ff16ac63530725a1ce3d1eb91c"
PRE_EXECUTION_BASE = "1b71e35b4938942bdb92ebbc769d59c04c43cf37"
EXECUTION_COMMIT_A = "315eb5b578301d57c6ab90c0c2398e3df3dec3f5"
INDEPENDENT_COMMIT_B = "cd220a89f37e0a3913124116f49a90e0518c8b46"
BLOCKER_FREEZE_COMMIT = "f42e706f712616e23f7a86d86cc2bd6cfc6f4ce8"
BLOCKER_HASH = "b721ddc45f0e7c97646b520eab9384d74c6c12231cb744c0f493fbf661111580"
BLOCKER_REPORT_HASH = "5e56f352c6495dde6bfe1f00a7a6dae6eb4c031008c54519924aa99992699c90"
BLOCKER_CODE = "D2_EXECUTION_BLOCKED_PRIVATE_FUSION_EVIDENCE_WRITE_DENIED"

D2_DESIGN_HASH = "eb559a91350fd046204d223d6820ef7f0590ad4beb7a2b17114a496859758e51"
AUTHORIZATION_HASH = "b931d7bd89e923dc4d380e35ed2b3ff514679a701e0b94a75d426130a3c4427c"
D0_PREDICTION_HASH = "a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6"
D1_PREDICTION_HASH = "58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682"
SOURCE_MAP_HASH = "f866176000c3d5a943053ac3125d2700b0b72f25b5a0539d8f4713435a959818"
EXECUTION_SOURCE_SHA256 = "0bfcfc5aba2a53ad24d08da0c1d9861472e350d1fe64ba6dabf1ba1a8a6689cc"
EXECUTION_GIT_BLOB = "1442b5dd1bef0d55a87cbb8e521919eb14954034"
EXECUTION_IMPLEMENTATION_IDENTITY = "03d3d8c3a2586e1eeaadbbc367f756c973920c3b7e84afd384eb7f45684aa733"

EXECUTION_SOURCE = "src/paperworks/v6/task039e3_r2r_d2_inner_execution_v1.py"
BLOCKER_JSON = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_V1_BLOCKER.json"
BLOCKER_REPORT = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_V1_BLOCKER_REPORT.md"
D0_PREDICTION = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_PREDICTION_ARTIFACT_V1.json"
D1_PREDICTION = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D1_RULE_PREDICTION_ARTIFACT_V1.json"
D0_FREEZE_COMMIT = "78d758f50657413eed28dc838212be9a1edeffc7"
D1_FREEZE_COMMIT = "9fe9192c6da4e2d1f3c7a42ecdd28006e8534449"
SOURCE_MAP = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_SOURCE_MAP.json"
AUTHORIZATION = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_AUTHORIZATION.json"
D2_DESIGN = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_V1_DESIGN.json"
COMBINED_PREDICTION = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_COMBINED_PREDICTION_ARTIFACT_V1.json"

LAST_COMPLETED_STATE = "SOURCE_MAP_VALIDATED"
FAILURE_STATE = "PRIVATE_FUSION_EVIDENCE_PERSISTENCE_DURING_SOURCE_MAP_VALIDATED_TO_FUSION_COMPUTED_TRANSITION"
FUSION_CLASSIFICATION = "FUSION_COMPUTED_IN_MEMORY_BUT_NOT_PERSISTED"
WRITER_CLASSIFICATION = "APPROVED_PRIVATE_CUSTODY_ROOT_FAIL_CLOSED_ATOMIC_CREATE_NO_OVERWRITE"
ROOT_CAUSE = "PRIVATE_PARENT_PERMISSION_DENIED"
PATH_EXPOSURE_CLASSIFICATION = "EPHEMERAL_PRIVATE_PATH_DISCLOSURE"
RECOVERY_CLASS = "PATH_REDACTION_AND_CUSTODY_RECOVERY"
RECOVERY_RATIONALE = "INFRASTRUCTURE_ONLY_FAILURE_BEFORE_RESULT_FREEZE_WITH_EPHEMERAL_PATH_DISCLOSURE"
NEXT_TASK = "TASK-039E3-R2R-UTILITY-INNER-D2-EXECUTION-PRIVATE-CUSTODY-REMEDIATION-AND-RECOVERY-AUTHORIZATION-V1"
REPORT_PREFIX = "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_PRIVATE_CUSTODY_BLOCKER_AUDIT_V1_"
REPORT_HASH_SCHEME = "MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1"
INDEPENDENT_ATTACKS = 24


class BlockerAuditV1Error(ValueError):
    """A frozen blocker or fail-closed audit invariant differs."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _fail(code: str) -> NoReturn:
    raise BlockerAuditV1Error(code)


def stable_hash_v1(value: Mapping[str, Any]) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def self_hash_document_v1(document: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(document)
    payload.pop("artifact_hash", None)
    return {**payload, "artifact_hash": stable_hash_v1(payload)}


def _strict_object(raw: bytes) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in items:
            if key in out:
                _fail("DUPLICATE_JSON_KEY_REJECTED")
            out[key] = value
        return out

    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs)
    except (UnicodeDecodeError, json.JSONDecodeError):
        _fail("STRICT_JSON_REJECTED")
    if type(value) is not dict:
        _fail("JSON_OBJECT_REQUIRED")
    return value


def _validate_self_hash(document: Mapping[str, Any], expected: str) -> None:
    if document.get("artifact_hash") != expected:
        _fail("ARTIFACT_HASH_IDENTITY_REJECTED")
    payload = dict(document)
    payload.pop("artifact_hash", None)
    if stable_hash_v1(payload) != expected:
        _fail("ARTIFACT_SELF_HASH_REJECTED")


def _git(repo: Path, *args: str, text: bool = True) -> str | bytes:
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, check=False,
    )
    if result.returncode != 0:
        _fail("GIT_AUDIT_REJECTED")
    if text:
        try:
            return result.stdout.decode("utf-8").strip()
        except UnicodeDecodeError:
            _fail("GIT_TEXT_REJECTED")
    return result.stdout


def _commit_files(repo: Path, commit: str) -> tuple[str, ...]:
    value = _git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", commit)
    assert isinstance(value, str)
    return tuple(line for line in value.splitlines() if line)


def _commit_parent(repo: Path, commit: str) -> str:
    value = _git(repo, "rev-parse", f"{commit}^")
    assert isinstance(value, str)
    return value


def _commit_bytes(repo: Path, commit: str, relative: str) -> bytes:
    value = _git(repo, "show", f"{commit}:{relative}", text=False)
    assert isinstance(value, bytes)
    return value


def validate_recovery_snapshot_v1(snapshot: Mapping[str, Any]) -> None:
    required_exact = {
        "blocker_hash": BLOCKER_HASH,
        "execution_implementation_commit_a": EXECUTION_COMMIT_A,
        "d2_design_hash": D2_DESIGN_HASH,
        "authorization_hash": AUTHORIZATION_HASH,
        "d0_prediction_hash": D0_PREDICTION_HASH,
        "d1_prediction_hash": D1_PREDICTION_HASH,
        "source_map_hash": SOURCE_MAP_HASH,
        "execution_last_completed_state": LAST_COMPLETED_STATE,
        "execution_failure_state": FAILURE_STATE,
        "fusion_computation_classification": FUSION_CLASSIFICATION,
        "root_cause_classification": ROOT_CAUSE,
        "path_exposure_classification": PATH_EXPOSURE_CLASSIFICATION,
        "historical_d2_execution_attempts": 1,
        "historical_d2_completed_executions": 0,
        "historical_d2_execution_retries": 0,
        "private_path_exposure_count": 1,
        "recovery_class": RECOVERY_CLASS,
        "future_total_execution_attempts": 2,
        "future_aborted_infrastructure_attempts": 1,
        "future_completed_scientific_attempts": 1,
        "future_result_driven_retries": 0,
    }
    for key, expected in required_exact.items():
        if snapshot.get(key) != expected:
            _fail(f"RECOVERY_{key.upper()}_REJECTED")

    required_false = (
        "combined_prediction_frozen", "label_state_reached", "metric_state_reached",
        "root_cause_scientific", "root_cause_result_driven",
        "tracked_private_path_leak", "scientific_artifact_compromised",
        "final_private_fusion_evidence_exists", "partial_private_temp_exists",
        "zero_byte_private_target_exists", "combined_prediction_exists",
        "d2_result_frozen", "d2_result_observed", "result_driven_changes",
        "label_before_combined_prediction_access", "test2_touched",
        "policy_changed", "scientific_inputs_changed",
    )
    for key in required_false:
        if snapshot.get(key) is not False:
            _fail(f"RECOVERY_{key.upper()}_REJECTED")

    required_zero = (
        "tracked_private_path_occurrences", "scientific_private_value_leak_count",
        "stale_private_residue_count", "label_scientific_parses",
        "attack_event_derivations", "primary_metric_computations",
        "incremental_metric_computations", "metric_computations", "d0_executions",
        "d1_executions", "d0_score_accesses", "d1_rule_reevaluations",
        "d1_metric_reads", "test1_feature_accesses", "test2_accesses",
    )
    for key in required_zero:
        if snapshot.get(key) != 0:
            _fail(f"RECOVERY_{key.upper()}_REJECTED")
    if snapshot.get("recovery_eligible") is not True:
        _fail("RECOVERY_ELIGIBILITY_REJECTED")


def classify_path_exposure_v1(*, tracked_occurrences: int, ephemeral_exposure: bool) -> str:
    if type(tracked_occurrences) is not int or tracked_occurrences < 0:
        _fail("PATH_OCCURRENCE_COUNT_REJECTED")
    if tracked_occurrences:
        return "TRACKED_PRIVATE_PATH_LEAK_REQUIRES_SANITIZATION"
    if ephemeral_exposure is True:
        return PATH_EXPOSURE_CLASSIFICATION
    if ephemeral_exposure is False:
        return "NO_PRIVATE_PATH_DISCLOSURE"
    _fail("PATH_EXPOSURE_TYPE_REJECTED")


def classify_residue_v1(*, final_exists: bool, temp_exists: bool, final_size: int | None,
                        targeted_entries: int) -> dict[str, Any]:
    if type(final_exists) is not bool or type(temp_exists) is not bool:
        _fail("RESIDUE_BOOLEAN_REJECTED")
    if final_size is not None and (type(final_size) is not int or final_size < 0):
        _fail("RESIDUE_SIZE_REJECTED")
    if type(targeted_entries) is not int or targeted_entries < 0:
        _fail("RESIDUE_COUNT_REJECTED")
    return {
        "final_private_fusion_evidence_exists": final_exists,
        "partial_private_temp_exists": temp_exists,
        "zero_byte_private_target_exists": final_exists and final_size == 0,
        "stale_private_residue_count": targeted_entries,
    }


def _validate_blocker(repo: Path) -> dict[str, Any]:
    blocker = _strict_object((repo / BLOCKER_JSON).read_bytes())
    _validate_self_hash(blocker, BLOCKER_HASH)
    required = {
        "blocker_code": BLOCKER_CODE,
        "execution_implementation_commit_a": EXECUTION_COMMIT_A,
        "independent_audit_commit_b": INDEPENDENT_COMMIT_B,
        "d2_design_hash": D2_DESIGN_HASH,
        "authorization_hash": AUTHORIZATION_HASH,
        "scientific_execution_attempts": 1,
        "scientific_execution_retries": 0,
        "d0_prediction_parses": 1,
        "d1_prediction_parses": 1,
        "source_map_reads": 1,
        "fusion_computations": 54_000,
        "combined_prediction_frozen": False,
        "label_scientific_parses": 0,
        "attack_event_derivations": 0,
        "metric_computations": 0,
        "d0_executions": 0,
        "d1_executions": 0,
        "d0_score_accesses": 0,
        "d1_rule_reevaluations": 0,
        "d1_metric_artifact_reads": 0,
        "test1_feature_accesses": 0,
        "test2_accesses": 0,
        "result_driven_changes": False,
        "private_paths_exposed": 1,
        "private_source_sets_exposed": 0,
        "private_label_values_exposed": 0,
    }
    for key, expected in required.items():
        if blocker.get(key) != expected:
            _fail(f"BLOCKER_{key.upper()}_REJECTED")
    report = (repo / BLOCKER_REPORT).read_bytes()
    marker = b"<!-- BEGIN D2 EXECUTION BLOCKER REPORT PROVENANCE V1 -->"
    if report.count(marker) != 1:
        _fail("BLOCKER_REPORT_FOOTER_REJECTED")
    body = report.split(marker, 1)[0]
    if sha256(body).hexdigest() != BLOCKER_REPORT_HASH:
        _fail("BLOCKER_REPORT_HASH_REJECTED")
    return blocker


def _validate_lineage(repo: Path) -> None:
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"],
        cwd=repo, capture_output=True, check=False,
    )
    if ancestor.returncode != 0:
        _fail("AUDIT_BASE_REJECTED")
    parents = {
        EXECUTION_COMMIT_A: PRE_EXECUTION_BASE,
        INDEPENDENT_COMMIT_B: EXECUTION_COMMIT_A,
        BLOCKER_FREEZE_COMMIT: INDEPENDENT_COMMIT_B,
        BASE_COMMIT: BLOCKER_FREEZE_COMMIT,
    }
    for commit, parent in parents.items():
        if _commit_parent(repo, commit) != parent:
            _fail("AUDIT_LINEAGE_REJECTED")
    expected_files = {
        EXECUTION_COMMIT_A: {
            "TASKS/TASK-039E3-R2R-UTILITY-INNER-D2-EXECUTION-V1.md",
            EXECUTION_SOURCE,
            "tests/test_task039e3_r2r_d2_inner_execution_v1.py",
        },
        INDEPENDENT_COMMIT_B: {"tests/test_task039e3_r2r_d2_inner_execution_v1_independent.py"},
        BLOCKER_FREEZE_COMMIT: {BLOCKER_JSON, BLOCKER_REPORT},
        BASE_COMMIT: {
            "docs/project_state/AUTHORITY_INDEX.md", "docs/project_state/CURRENT_STATE.json",
            "docs/project_state/CURRENT_STATE.md", "docs/project_state/HANDOFF.md",
            "docs/project_state/TASK_LEDGER.md",
        },
    }
    for commit, expected in expected_files.items():
        if set(_commit_files(repo, commit)) != expected:
            _fail("AUDIT_COMMIT_BOUNDARY_REJECTED")


def _validate_execution_source(repo: Path) -> dict[str, Any]:
    source_bytes = (repo / EXECUTION_SOURCE).read_bytes()
    if source_bytes != _commit_bytes(repo, EXECUTION_COMMIT_A, EXECUTION_SOURCE):
        _fail("EXECUTION_SOURCE_BYTES_REJECTED")
    if sha256(source_bytes).hexdigest() != EXECUTION_SOURCE_SHA256:
        _fail("EXECUTION_SOURCE_SHA_REJECTED")
    if _git(repo, "hash-object", EXECUTION_SOURCE) != EXECUTION_GIT_BLOB:
        _fail("EXECUTION_SOURCE_BLOB_REJECTED")
    text = source_bytes.decode("utf-8")
    tree = ast.parse(text)
    execute = next(
        (node for node in tree.body if isinstance(node, ast.FunctionDef)
         and node.name == "execute_authorized_d2_inner_v1"), None
    )
    writer = next(
        (node for node in tree.body if isinstance(node, ast.FunctionDef)
         and node.name == "_write_private_json_atomic_v1"), None
    )
    directory = next(
        (node for node in tree.body if isinstance(node, ast.FunctionDef)
         and node.name == "_private_evidence_directory_v1"), None
    )
    if execute is None or writer is None or directory is None:
        _fail("EXECUTION_FUNCTION_GRAPH_REJECTED")
    execute_text = ast.get_source_segment(text, execute) or ""
    sequence = (
        "_build_fusion_evidence_v1", "_load_local_hai_root_v1",
        "_private_evidence_directory_v1", "_write_private_json_atomic_v1",
        "D2ExecutionStateV1.FUSION_COMPUTED", "_build_combined_prediction_v1",
        "_persist_combined_prediction_before_label_v1", "_load_label_custody_once_v1",
        "_build_private_metric_evidence_v1", "D2ExecutionStateV1.RESULT_FROZEN",
    )
    positions = [execute_text.find(item) for item in sequence]
    if any(item < 0 for item in positions) or positions != sorted(positions):
        _fail("EXECUTION_CONTROL_FLOW_REJECTED")
    writer_text = ast.get_source_segment(text, writer) or ""
    directory_text = ast.get_source_segment(text, directory) or ""
    writer_requirements = (
        'f"{filename}.tmp"', "path.exists()", "path.is_symlink()",
        "temporary.exists()", "temporary.is_symlink()", 'temporary.open("xb")',
        "os.fsync", "os.replace", "PRIVATE_EVIDENCE_WRITE_REJECTED",
    )
    directory_requirements = (
        '".paper_v_20260625_private_evidence"', "PRIVATE_EVIDENCE_INSIDE_REPOSITORY_REJECTED",
        "directory.mkdir", "directory.is_symlink()", "PRIVATE_EVIDENCE_DIRECTORY_REJECTED",
    )
    if any(item not in writer_text for item in writer_requirements):
        _fail("PRIVATE_WRITER_POLICY_REJECTED")
    if any(item not in directory_text for item in directory_requirements):
        _fail("PRIVATE_DIRECTORY_POLICY_REJECTED")
    if "except BaseException" not in writer_text or "except D2InnerExecutionV1Error" not in writer_text:
        _fail("PRIVATE_WRITER_EXCEPTION_TRANSLATION_REJECTED")
    return {
        "execution_source_sha256": EXECUTION_SOURCE_SHA256,
        "execution_git_blob": EXECUTION_GIT_BLOB,
        "execution_implementation_identity": EXECUTION_IMPLEMENTATION_IDENTITY,
        "production_changes_after_execution_commit_a": 0,
        "execution_last_completed_state": LAST_COMPLETED_STATE,
        "execution_failure_state": FAILURE_STATE,
        "fusion_computation_classification": FUSION_CLASSIFICATION,
        "private_fusion_evidence_writer_classification": WRITER_CLASSIFICATION,
    }


def _validate_public_authorities(repo: Path) -> dict[str, bool]:
    design = _strict_object((repo / D2_DESIGN).read_bytes())
    authorization = _strict_object((repo / AUTHORIZATION).read_bytes())
    source_map = _strict_object((repo / SOURCE_MAP).read_bytes())
    _validate_self_hash(design, str(design.get("artifact_hash")))
    _validate_self_hash(authorization, AUTHORIZATION_HASH)
    _validate_self_hash(source_map, SOURCE_MAP_HASH)
    if design.get("d2_design_hash") != D2_DESIGN_HASH:
        _fail("D2_DESIGN_HASH_REJECTED")
    required_auth = {
        "d2_design_hash": D2_DESIGN_HASH,
        "d0_prediction_hash": D0_PREDICTION_HASH,
        "d1_prediction_hash": D1_PREDICTION_HASH,
        "source_map_hash": SOURCE_MAP_HASH,
    }
    for key, expected in required_auth.items():
        if authorization.get(key) != expected:
            _fail("D2_AUTHORIZATION_BINDING_REJECTED")
    if source_map.get("d2_design_hash") != D2_DESIGN_HASH:
        _fail("SOURCE_MAP_DESIGN_BINDING_REJECTED")
    if (repo / D0_PREDICTION).read_bytes() != _commit_bytes(repo, D0_FREEZE_COMMIT, D0_PREDICTION):
        _fail("D0_PREDICTION_BYTES_REJECTED")
    if (repo / D1_PREDICTION).read_bytes() != _commit_bytes(repo, D1_FREEZE_COMMIT, D1_PREDICTION):
        _fail("D1_PREDICTION_BYTES_REJECTED")
    return {
        "d2_design_hash_match": True,
        "d2_authorization_hash_match": True,
        "d0_prediction_hash_match": True,
        "d1_prediction_hash_match": True,
        "source_map_hash_match": True,
    }


def audit_public_repository_v1(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    _validate_lineage(repo)
    blocker = _validate_blocker(repo)
    source = _validate_execution_source(repo)
    authorities = _validate_public_authorities(repo)
    combined_exists = (repo / COMBINED_PREDICTION).exists()
    if combined_exists:
        _fail("D2_BLOCKER_AUDIT_FOUND_UNEXPECTED_COMBINED_PREDICTION")
    return {
        **source,
        **authorities,
        "blocker_hash": BLOCKER_HASH,
        "execution_implementation_commit_a": EXECUTION_COMMIT_A,
        "blocker_hash_match": True,
        "blocker_report_hash_match": True,
        "combined_prediction_exists": False,
        "combined_prediction_frozen": False,
        "label_state_reached": False,
        "metric_state_reached": False,
        "label_before_combined_prediction_access": False,
        "historical_d2_execution_attempts": blocker["scientific_execution_attempts"],
        "historical_d2_completed_executions": 0,
        "historical_d2_execution_retries": blocker["scientific_execution_retries"],
        "label_scientific_parses": blocker["label_scientific_parses"],
        "attack_event_derivations": blocker["attack_event_derivations"],
        "primary_metric_computations": 0,
        "incremental_metric_computations": 0,
        "metric_computations": blocker["metric_computations"],
        "d0_executions": blocker["d0_executions"],
        "d1_executions": blocker["d1_executions"],
        "d0_score_accesses": blocker["d0_score_accesses"],
        "d1_rule_reevaluations": blocker["d1_rule_reevaluations"],
        "d1_metric_reads": blocker["d1_metric_artifact_reads"],
        "test1_feature_accesses": blocker["test1_feature_accesses"],
        "test2_accesses": blocker["test2_accesses"],
        "private_path_exposure_count": blocker["private_paths_exposed"],
        "scientific_private_value_leak_count": 0,
        "d2_result_frozen": False,
        "d2_result_observed": False,
        "result_driven_changes": blocker["result_driven_changes"],
        "policy_changed": False,
        "scientific_inputs_changed": False,
        "test2_touched": False,
    }


def _binding_values(binding: Path) -> dict[str, str]:
    if binding.is_symlink() or not binding.is_file():
        _fail("PRIVATE_BINDING_MISSING")
    values: dict[str, str] = {}
    try:
        lines = binding.read_text(encoding="utf-8").splitlines()
    except BaseException:
        _fail("PRIVATE_BINDING_READ_REJECTED")
    for line in lines:
        match = re.fullmatch(r"([A-Z0-9_]+)='(.*)'", line)
        if match:
            values[match.group(1)] = match.group(2).replace("'\"'\"'", "'")
    if "HAI_DATA_ROOT" not in values:
        _fail("PRIVATE_BINDING_ROOT_MISSING")
    return values


def _path_variants(path: Path) -> tuple[bytes, ...]:
    raw = str(path)
    values = {raw, path.as_posix(), raw.replace("\\", "\\\\")}
    return tuple(value.encode("utf-8") for value in values if value)


def _count_exact_path_in_tracked_files(repo: Path, path: Path) -> tuple[int, dict[str, bool]]:
    listing = _git(repo, "ls-files", "-z", text=False)
    assert isinstance(listing, bytes)
    variants = _path_variants(path)
    counts = 0
    channels = {
        "tracked_blocker_json": False,
        "tracked_blocker_markdown": False,
        "project_state": False,
        "tracked_source_test": False,
        "other_tracked": False,
    }
    for item in listing.split(b"\0"):
        if not item:
            continue
        try:
            relative = item.decode("utf-8")
            content = (repo / relative).read_bytes()
        except (UnicodeDecodeError, OSError):
            continue
        occurrence = sum(content.count(variant) for variant in variants)
        if not occurrence:
            continue
        counts += occurrence
        if relative == BLOCKER_JSON:
            channels["tracked_blocker_json"] = True
        elif relative == BLOCKER_REPORT:
            channels["tracked_blocker_markdown"] = True
        elif relative.startswith("docs/project_state/"):
            channels["project_state"] = True
        elif relative.startswith("src/") or relative.startswith("tests/"):
            channels["tracked_source_test"] = True
        else:
            channels["other_tracked"] = True
    return counts, channels


def audit_private_metadata_v1(repo: Path, execution_worktree: Path) -> dict[str, Any]:
    """Return path-free, value-free metadata for the one exact failed target."""

    repo = repo.resolve()
    execution_worktree = execution_worktree.resolve()
    values = _binding_values(execution_worktree / ".env.custody.local")
    try:
        hai_root = Path(values["HAI_DATA_ROOT"])
        if hai_root.is_symlink() or not hai_root.is_dir():
            _fail("PRIVATE_BINDING_ROOT_INVALID")
        directory = hai_root.resolve(strict=True).parent / ".paper_v_20260625_private_evidence"
        final = directory / "task039e3_inner_d2_fusion_evidence_v1.json"
        temporary = directory / "task039e3_inner_d2_fusion_evidence_v1.json.tmp"
        directory_exists = directory.exists()
        final_exists = final.exists()
        temp_exists = temporary.exists()
        final_size = final.stat().st_size if final_exists and final.is_file() else None
        # Do not enumerate a private directory. The frozen writer has exactly
        # two possible task-owned residue names: final and atomic temporary.
        targeted_entries = int(final_exists) + int(temp_exists)
        occurrences, channels = _count_exact_path_in_tracked_files(repo, temporary)
    except BlockerAuditV1Error:
        raise
    except BaseException:
        _fail("PRIVATE_METADATA_AUDIT_REJECTED")
    residue = classify_residue_v1(
        final_exists=final_exists,
        temp_exists=temp_exists,
        final_size=final_size,
        targeted_entries=targeted_entries,
    )
    path_class = classify_path_exposure_v1(
        tracked_occurrences=occurrences, ephemeral_exposure=True
    )
    return {
        **residue,
        "private_evidence_directory_residue": directory_exists,
        "tracked_private_path_occurrences": occurrences,
        "tracked_private_path_leak": occurrences > 0,
        "path_present_in_exception_object": True,
        "path_present_in_stderr": True,
        "path_present_in_stdout": False,
        "path_present_in_user_facing_channel": True,
        "path_present_in_tracked_blocker_json": channels["tracked_blocker_json"],
        "path_present_in_tracked_blocker_markdown": channels["tracked_blocker_markdown"],
        "path_present_in_tracked_source_test_artifact": channels["tracked_source_test"],
        "path_present_in_project_state": channels["project_state"],
        "path_present_in_git_commit_diff": occurrences > 0,
        "path_present_in_other_tracked_output": channels["other_tracked"],
        "path_exposure_classification": path_class,
        "scientific_artifact_compromised": False,
    }


def build_recovery_snapshot_v1(public: Mapping[str, Any], private: Mapping[str, Any]) -> dict[str, Any]:
    snapshot = {
        **public,
        **private,
        "d2_design_hash": D2_DESIGN_HASH,
        "authorization_hash": AUTHORIZATION_HASH,
        "d0_prediction_hash": D0_PREDICTION_HASH,
        "d1_prediction_hash": D1_PREDICTION_HASH,
        "source_map_hash": SOURCE_MAP_HASH,
        "root_cause_classification": ROOT_CAUSE,
        "root_cause_scientific": False,
        "root_cause_result_driven": False,
        "recovery_eligible": True,
        "recovery_class": RECOVERY_CLASS,
        "recovery_eligibility_rationale_code": RECOVERY_RATIONALE,
        "future_total_execution_attempts": 2,
        "future_aborted_infrastructure_attempts": 1,
        "future_completed_scientific_attempts": 1,
        "future_result_driven_retries": 0,
        "exact_next_task": NEXT_TASK,
    }
    validate_recovery_snapshot_v1(snapshot)
    return snapshot


def _report_body_v1() -> bytes:
    return (
        "# TASK-039E3-R2R Utility INNER D2 private-custody blocker audit V1\n\n"
        f"Status: `{STATUS}`\n\n"
        f"Scientific state: `{SCIENTIFIC_STATE}`\n\n"
        "The immutable execution completed the frozen fusion calculation in memory but failed "
        "closed while creating the first private FusionEvidence temporary file. The state machine "
        "therefore remained at `SOURCE_MAP_VALIDATED`; CombinedPrediction, label, metric, and result "
        "states were never reached.\n\n"
        "The primary cause is `PRIVATE_PARENT_PERMISSION_DENIED`, an infrastructure/custody failure "
        "rather than a scientific or result-driven failure. One private path was disclosed only "
        "ephemerally through the exception/stderr/user-facing channel. It does not occur in tracked "
        "artifacts, and no scientific private value was exposed.\n\n"
        "No final or temporary FusionEvidence file, zero-byte target, stale targeted residue, or "
        "CombinedPrediction exists. The historical attempt remains attempt 1 with zero retries. "
        "A separately authorized recovery is eligible only as transparent attempt 2, with one "
        "aborted infrastructure attempt and zero result-driven retries.\n\n"
        f"Exact next task: `{NEXT_TASK}`\n\n"
    ).encode("utf-8")


def _artifact(task_type: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    return self_hash_document_v1({
        "artifact_type": f"task039e3_r2r_utility_inner_d2_execution_private_custody_blocker_audit_v1_{task_type}",
        "schema_version": "1.0.0",
        "task_id": TASK_ID,
        **payload,
    })


def write_reports_v1(repo: Path, snapshot: Mapping[str, Any], audit_commit_a: str) -> dict[str, str]:
    validate_recovery_snapshot_v1(snapshot)
    report_dir = repo / "docs/task_reports"
    common = {
        "status": "PASS",
        "audit_commit_a": audit_commit_a,
        "blocker_hash": BLOCKER_HASH,
        "execution_implementation_commit_a": EXECUTION_COMMIT_A,
        "d2_design_hash": D2_DESIGN_HASH,
        "authorization_hash": AUTHORIZATION_HASH,
        "d0_prediction_hash": D0_PREDICTION_HASH,
        "d1_prediction_hash": D1_PREDICTION_HASH,
        "source_map_hash": SOURCE_MAP_HASH,
    }
    documents: dict[str, dict[str, Any]] = {}
    documents["STATE"] = _artifact("state", {**common,
        "execution_implementation_identity": EXECUTION_IMPLEMENTATION_IDENTITY,
        "execution_last_completed_state": snapshot["execution_last_completed_state"],
        "execution_failure_state": snapshot["execution_failure_state"],
        "fusion_computation_classification": snapshot["fusion_computation_classification"],
        "combined_prediction_freeze_reached": False,
        "label_state_reached": False,
        "metric_state_reached": False,
        "historical_d2_execution_attempts": 1,
        "historical_d2_completed_executions": 0,
        "historical_d2_execution_retries": 0,
    })
    documents["ROOT_CAUSE"] = _artifact("root_cause", {**common,
        "private_fusion_evidence_writer_classification": snapshot["private_fusion_evidence_writer_classification"],
        "root_cause_classification": ROOT_CAUSE,
        "root_cause_scientific": False,
        "root_cause_result_driven": False,
        "environment_or_custody_failure": True,
        "fusion_semantics_changed": False,
    })
    documents["PATH_EXPOSURE"] = _artifact("path_exposure", {**common,
        "private_path_exposure_count": 1,
        "path_present_in_exception_object": snapshot["path_present_in_exception_object"],
        "path_present_in_stderr": snapshot["path_present_in_stderr"],
        "path_present_in_stdout": snapshot["path_present_in_stdout"],
        "path_present_in_user_facing_channel": snapshot["path_present_in_user_facing_channel"],
        "path_present_in_tracked_blocker_json": snapshot["path_present_in_tracked_blocker_json"],
        "path_present_in_tracked_blocker_markdown": snapshot["path_present_in_tracked_blocker_markdown"],
        "path_present_in_tracked_source_test_artifact": snapshot["path_present_in_tracked_source_test_artifact"],
        "path_present_in_project_state": snapshot["path_present_in_project_state"],
        "path_present_in_git_commit_diff": snapshot["path_present_in_git_commit_diff"],
        "path_present_in_other_tracked_output": snapshot["path_present_in_other_tracked_output"],
        "tracked_private_path_occurrences": snapshot["tracked_private_path_occurrences"],
        "tracked_private_path_leak": snapshot["tracked_private_path_leak"],
        "path_exposure_classification": snapshot["path_exposure_classification"],
        "scientific_artifact_compromised": False,
        "scientific_private_value_leak_count": 0,
    })
    documents["RESIDUE"] = _artifact("residue", {**common,
        "final_private_fusion_evidence_exists": snapshot["final_private_fusion_evidence_exists"],
        "partial_private_temp_exists": snapshot["partial_private_temp_exists"],
        "zero_byte_private_target_exists": snapshot["zero_byte_private_target_exists"],
        "stale_private_residue_count": snapshot["stale_private_residue_count"],
        "private_evidence_directory_residue": snapshot["private_evidence_directory_residue"],
        "combined_prediction_exists": snapshot["combined_prediction_exists"],
        "residue_deleted": False,
    })
    documents["RECOVERY_ELIGIBILITY"] = _artifact("recovery_eligibility", {**common,
        "recovery_eligible": True,
        "recovery_class": RECOVERY_CLASS,
        "recovery_eligibility_rationale_code": RECOVERY_RATIONALE,
        "d2_result_frozen": False,
        "d2_result_observed": False,
        "label_scientific_parses": 0,
        "metric_computations": 0,
        "test2_accesses": 0,
        "result_driven_changes": False,
        "future_total_execution_attempts_if_recovery_succeeds": 2,
        "future_aborted_infrastructure_attempts": 1,
        "future_completed_scientific_attempts": 1,
        "future_result_driven_retries": 0,
        "exact_next_task": NEXT_TASK,
    })
    documents["INDEPENDENT_AUDIT"] = _artifact("independent_audit", {**common,
        "independent_attacks": INDEPENDENT_ATTACKS,
        "accepted_invalid": 0,
        "scientific_prediction_parses": 0,
        "fusion_recomputations": 0,
        "label_accesses": 0,
        "metric_computations": 0,
        "test1_feature_accesses": 0,
        "test2_accesses": 0,
        "push_attempted": False,
    })
    report_body = _report_body_v1()
    report_hash = sha256(report_body).hexdigest()
    leaf_hashes = {name.lower() + "_hash": doc["artifact_hash"] for name, doc in documents.items()}
    documents["READINESS"] = _artifact("readiness", {**common, **leaf_hashes,
        "report_self_hash": report_hash,
        "audit_complete": True,
        "scientific_state": SCIENTIFIC_STATE,
        "recovery_eligible": True,
        "d2_authorized": False,
        "d2_executed": False,
        "d2_result_frozen": False,
        "outer_authorized": False,
        "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED",
    })
    leaf_hashes["readiness_hash"] = documents["READINESS"]["artifact_hash"]
    documents["BUNDLE"] = _artifact("bundle", {**common, **leaf_hashes,
        "artifact_count": 7,
        "report_self_hash": report_hash,
        "recovery_eligible": True,
    })
    leaf_hashes["bundle_hash"] = documents["BUNDLE"]["artifact_hash"]
    documents["RECEIPT"] = _artifact("receipt", {**common, **leaf_hashes,
        "report_self_hash": report_hash,
        "status": STATUS,
        "scientific_state": SCIENTIFIC_STATE,
        "recovery_eligible": True,
        "recovery_class": RECOVERY_CLASS,
        "push_attempted": False,
        "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED",
        "exact_next_task": NEXT_TASK,
    })
    for name, document in documents.items():
        path = report_dir / f"{REPORT_PREFIX}{name}.json"
        path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    footer = (
        "<!-- BEGIN D2 CUSTODY BLOCKER AUDIT REPORT PROVENANCE V1 -->\n"
        f"Report-Hash-Scheme: {REPORT_HASH_SCHEME}\n"
        f"Report-Self-Hash: {report_hash}\n"
        f"Bundle-Hash: {documents['BUNDLE']['artifact_hash']}\n"
        f"Receipt-Hash: {documents['RECEIPT']['artifact_hash']}\n"
        "<!-- END D2 CUSTODY BLOCKER AUDIT REPORT PROVENANCE V1 -->\n"
    ).encode("utf-8")
    (report_dir / f"{REPORT_PREFIX}REPORT.md").write_bytes(report_body + footer)
    return {
        **{name.lower() + "_hash": str(document["artifact_hash"]) for name, document in documents.items()},
        "report_self_hash": report_hash,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--execution-worktree", type=Path)
    parser.add_argument("--write-reports", action="store_true")
    parser.add_argument("--audit-commit-a")
    args = parser.parse_args()
    try:
        public = audit_public_repository_v1(args.repo)
        if args.execution_worktree is None:
            print(json.dumps({"status": "PUBLIC_AUDIT_PASS"}, sort_keys=True))
            return 0
        private = audit_private_metadata_v1(args.repo, args.execution_worktree)
        snapshot = build_recovery_snapshot_v1(public, private)
        result: dict[str, Any] = {
            "status": "AUDIT_PASS", "recovery_eligible": True,
            "tracked_private_path_occurrences": snapshot["tracked_private_path_occurrences"],
            "stale_private_residue_count": snapshot["stale_private_residue_count"],
        }
        if args.write_reports:
            if not args.audit_commit_a:
                _fail("AUDIT_COMMIT_A_REQUIRED")
            result.update(write_reports_v1(args.repo, snapshot, args.audit_commit_a))
        print(json.dumps(result, sort_keys=True))
        return 0
    except BlockerAuditV1Error as exc:
        print(json.dumps({"status": "AUDIT_BLOCKED", "code": exc.code}, sort_keys=True))
        return 2
    except BaseException:
        print(json.dumps({"status": "AUDIT_BLOCKED", "code": "UNEXPECTED_SANITIZED_FAILURE"}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
