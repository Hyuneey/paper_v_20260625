#!/usr/bin/env python
"""Execute TASK-039C-GDNP once from the clean compatibility-closed commit."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from paperworks.candidates.gdn_candidate_discovery_v1 import (  # noqa: E402
    GDNCandidateResultV1,
    GDNSeedGraphRecordV1,
    aggregate_and_rank_gdn_candidates_v1,
    project_seed_record_to_universe_v1,
)
from paperworks.gdn.gdn_remediation_environment_v1 import (  # noqa: E402
    CANDIDATE_FEATURE_ORDER_HASH,
    CANDIDATE_LEARNING_VIEW_ID,
    DETERMINISTIC_ENVIRONMENT,
    ExactGDNEnvironmentUnavailable,
    assert_public_payload_sanitized_v1,
    derive_frozen_p1_feature_order_from_headers_v1,
    verify_self_hash_v1,
)
from paperworks.gdn.pyg_port_compatibility_v1 import (  # noqa: E402
    BASE_COMMIT,
    COMPATIBILITY_STATUS,
    EXACT_ENVIRONMENT_RECEIPT_HASH,
    GDNPortCompatibilityError,
    HYPERPARAMETER_HASH,
    ORIGINAL_FIDELITY_RECEIPT_HASH,
    SOFTMAX_COMPATIBILITY_RECEIPT_HASH,
    WHEELHOUSE_RECEIPT_HASH,
    assert_gdnp_patch_scope_v1,
    verify_self_hashed_compatibility_artifact_v1,
)
from paperworks.gdn.upstream_candidate_backend_v1 import (  # noqa: E402
    ALLOWED_VALUE_FILES,
    FROZEN_SEEDS,
    NORMAL_CANDIDATE_FIT,
    TASK039C0_GDN_POLICY_HASH,
    TASK039C0_PAIR_UNIVERSE_HASH,
    TASK039C0_PROTOCOL_BUNDLE_HASH,
    UPSTREAM_GDN_COMMIT,
    UpstreamGDNDataBoundaryError,
    UpstreamGDNTrainingConfigV1,
    assert_identical_seed_hyperparameters_v1,
    authorize_gdn_data_request_v1,
    load_authorized_numeric_segments_v1,
    train_upstream_aligned_seed_v1,
    verify_pinned_upstream_checkout_v1,
)
from paperworks.v6.common import (  # noqa: E402
    canonical_json_v1,
    parse_iso_datetime,
    stable_hash_v1,
)

import run_task039c_gdn_compat as gdnc  # noqa: E402
import run_task039c_gdn_remediation as gdnr  # noqa: E402


TASK_ID = "TASK-039C-GDNP"
BRANCH = "task-039c-gdn-port-closure"
PHASE_A_COMMIT = "229cb29cfec567e6491515de34c495a863c6e5fa"
GDNR_IMPLEMENTATION_COMMIT = "914e5159e719271262c8caa5bf94a2a806efc589"
GDNR_RESULT_COMMIT = "6474816068aae786a490c634c28d665772bc2243"
GDNC_IMPLEMENTATION_COMMIT = "19249db6e0f15afb492d6930e9297bcdd9c63d2e"
GDNC_RESULT_COMMIT = BASE_COMMIT
COMPATIBILITY_RECEIPT_HASH = (
    "fe59877405b17c7268c800690c434b267056a3e8a0c7b50715cec8df12f61f44"
)
SOURCE_IDENTITY_HASH = "0af3f80f18a3eab59b9783af64d306c8d774eeb69b3a72c24c10048abd4ed234"
TARGET_IDENTITY_HASH = "063037980aae4f0eaf45fbebb59f2aa0a924fbad583f3818107a793dfe7248e7"

COMPATIBILITY_OUTPUT = ROOT / "docs/task_reports/TASK-039C_GDNP_COMPATIBILITY_RECEIPT.json"
MATRIX_OUTPUT = ROOT / "docs/task_reports/TASK-039C_GDNP_API_DRIFT_MATRIX.json"
INDEX_OUTPUT = ROOT / "docs/task_reports/TASK-039C_GDNP_INDEX_SEMANTICS_RECEIPT.json"
LEGACY_OUTPUT = ROOT / "docs/task_reports/TASK-039C_GDNP_LEGACY_ORACLE_RECEIPT.json"
ENVIRONMENT_OUTPUT = ROOT / "docs/task_reports/TASK-039C_GDNR_ENVIRONMENT_RECEIPT.json"
FIDELITY_OUTPUT = ROOT / "docs/task_reports/TASK-039C_GDN_FIDELITY.json"
RESULT_OUTPUT = ROOT / "docs/task_reports/TASK-039C_GDN_RESULT.json"
ACCESS_OUTPUT = ROOT / "docs/task_reports/TASK-039C_GDNP_DATA_ACCESS_AUDIT.json"
EXECUTION_OUTPUT = ROOT / "docs/task_reports/TASK-039C_GDNP_EXECUTION_RECEIPT.json"
REPORT_OUTPUT = ROOT / "docs/task_reports/TASK-039C_GDNP_REPORT.md"

PRIVATE_ATTEMPT_MARKER = "TASK-039C_GDNP_FINAL_ATTEMPT_MARKER.json"
PRIVATE_EXECUTION_STATE = "TASK-039C_GDNP_EXECUTION_STATE.json"
PRIVATE_OUTCOME = "TASK-039C_GDNP_PRIVATE_OUTCOME.json"
PRIVATE_FAILURE = "TASK-039C_GDNP_PRIVATE_FAILURE.json"

EXPECTED_DATA_FILES: Mapping[str, Mapping[str, Any]] = {
    "hai-23.05/hai-train1.csv": {
        "byte_size": 162418984,
        "sha256": "53007b0ba604fbf338e7ac2e08cd81d874b5d1388f3aecb213ddcba5bf2bec4a",
        "header_sha256": "95968d825d1c9caab778a857cec618b64674ec5a85d94e6952d99c2cab08d16a",
    },
    "hai-23.05/hai-train2.csv": {
        "byte_size": 169121615,
        "sha256": "0e520e82bf78a661ab19ce4967f3c766bd809820f457a9c90c365102d4534c56",
        "header_sha256": "95968d825d1c9caab778a857cec618b64674ec5a85d94e6952d99c2cab08d16a",
    },
}

ALLOWED_COMMIT_A_PATHS = frozenset(
    {
        "TASKS/TASK-039C_GDNP_PORT_COMPATIBILITY_CLOSURE.md",
        "docs/v6/GDN_PYG15_TO_PYG28_API_AUDIT.md",
        "docs/v6/GDN_GRAPH_LAYER_MATHEMATICAL_PARITY.md",
        "docs/v6/GDN_PORT_COMPATIBILITY_CLOSURE.md",
        "src/paperworks/gdn/upstream_candidate_backend_v1.py",
        "src/paperworks/gdn/pyg_port_compatibility_v1.py",
        "src/paperworks/gdn/pure_torch_graph_layer_reference_v1.py",
        "schemas/v6/gdn_api_drift_matrix_v1_schema.json",
        "schemas/v6/gdn_index_semantics_receipt_v1_schema.json",
        "schemas/v6/gdn_port_compatibility_closure_receipt_v1_schema.json",
        "schemas/v6/gdn_legacy_oracle_receipt_v1_schema.json",
        "schemas/v6/gdn_candidate_result_v1_schema.json",
        "schemas/v6/task039c_gdnp_data_access_audit_v1_schema.json",
        "schemas/v6/task039c_gdnp_execution_receipt_v1_schema.json",
        "scripts/audit_task039c_gdn_port.py",
        "scripts/run_task039c_gdnp.py",
        "tests/test_task039c_gdnp_api_audit.py",
        "tests/test_task039c_gdnp_graph_layer_forward.py",
        "tests/test_task039c_gdnp_graph_layer_backward.py",
        "tests/test_task039c_gdnp_full_model.py",
        "tests/test_task039c_gdnp_training_loop.py",
        "tests/test_task039c_gdnp_result.py",
        "docs/task_reports/TASK-039C_GDNP_API_DRIFT_MATRIX.json",
        "docs/task_reports/TASK-039C_GDNP_INDEX_SEMANTICS_RECEIPT.json",
        "docs/task_reports/TASK-039C_GDNP_COMPATIBILITY_RECEIPT.json",
        "docs/task_reports/TASK-039C_GDNP_LEGACY_ORACLE_RECEIPT.json",
    }
)


class GDNPExecutionError(ValueError):
    """Fail-closed execution or result error."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GDNPExecutionError(f"required artifact unavailable: {path.name}") from exc
    if not isinstance(value, dict):
        raise GDNPExecutionError(f"artifact must be an object: {path.name}")
    return value


def _self_hashed(content: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(content)
    return {**payload, "artifact_hash": stable_hash_v1(payload)}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json_v1(dict(payload)) + "\n", encoding="utf-8")


def _write_public(path: Path, payload: Mapping[str, Any]) -> None:
    assert_public_payload_sanitized_v1(payload)
    _write_json(path, payload)


def _created_at(value: str | None) -> str:
    observed = value or datetime.now(timezone.utc).isoformat()
    parse_iso_datetime(observed, "created_at")
    return observed


def _git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={ROOT.resolve().as_posix()}",
            "-C",
            str(ROOT),
            *args,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise GDNPExecutionError("Git execution-lineage verification failed")
    return result.stdout.strip() if result.returncode == 0 else ""


def _private_path(roots: Any, name: str) -> Path:
    path = (roots.private_root / name).resolve()
    if not path.is_relative_to(roots.private_root.resolve()):
        raise GDNPExecutionError("private path escaped its root")
    return path


def _compatibility_receipt() -> dict[str, Any]:
    receipt = _load_json(COMPATIBILITY_OUTPUT)
    if (
        verify_self_hashed_compatibility_artifact_v1(receipt)
        != COMPATIBILITY_RECEIPT_HASH
        or receipt.get("status") != COMPATIBILITY_STATUS
        or receipt.get("unresolved_compatibility_fields") != []
        or receipt.get("exact_environment_receipt_hash")
        != EXACT_ENVIRONMENT_RECEIPT_HASH
        or receipt.get("prior_fidelity_receipt_hash")
        != ORIGINAL_FIDELITY_RECEIPT_HASH
        or receipt.get("softmax_compatibility_receipt_hash")
        != SOFTMAX_COMPATIBILITY_RECEIPT_HASH
    ):
        raise GDNPExecutionError("compatibility-closure receipt identity mismatch")
    for path in (MATRIX_OUTPUT, INDEX_OUTPUT, LEGACY_OUTPUT):
        verify_self_hashed_compatibility_artifact_v1(_load_json(path))
    return receipt


def _changed_paths(base: str, head: str) -> tuple[str, ...]:
    return tuple(
        item.replace("\\", "/")
        for item in _git("diff", "--name-only", base, head).splitlines()
        if item
    )


def validate_commit_a(execution_commit: str) -> tuple[Any, dict[str, Any], dict[str, str]]:
    if _git("branch", "--show-current") != BRANCH:
        raise GDNPExecutionError("blocked_gdnp_lineage_mismatch")
    if _git("rev-parse", "HEAD") != execution_commit:
        raise GDNPExecutionError("execution commit is not current HEAD")
    if _git("rev-parse", "HEAD^") != BASE_COMMIT:
        raise GDNPExecutionError("blocked_gdnp_lineage_mismatch")
    if _git("status", "--porcelain=v1"):
        raise GDNPExecutionError("execution worktree or index is not clean")
    changed = set(_changed_paths(BASE_COMMIT, execution_commit))
    prohibited = sorted(changed.difference(ALLOWED_COMMIT_A_PATHS))
    if prohibited:
        raise GDNPExecutionError("failed_gdnp_patch_scope_violation: " + ", ".join(prohibited))
    patched_hash = assert_gdnp_patch_scope_v1(repository_root=ROOT)
    compatibility = _compatibility_receipt()
    if compatibility.get("patched_implementation_hash") != patched_hash:
        raise GDNPExecutionError("patched implementation binding changed")
    roots, environment = gdnc._validate_exact_environment()
    if environment.get("artifact_hash") != EXACT_ENVIRONMENT_RECEIPT_HASH:
        raise GDNPExecutionError("blocked_gdnp_environment_identity_mismatch")
    _, _, _, scientific_hashes = gdnr._validate_frozen_context()
    if UpstreamGDNTrainingConfigV1().hyperparameter_hash != HYPERPARAMETER_HASH:
        raise GDNPExecutionError("frozen hyperparameter hash changed")
    return roots, compatibility, scientific_hashes


def _stream_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _verify_authorized_files(data_root: Path) -> tuple[tuple[str, ...], list[dict[str, Any]]]:
    root = data_root.resolve(strict=True)
    records: list[dict[str, Any]] = []
    feature_orders: list[tuple[str, ...]] = []
    for relative in ALLOWED_VALUE_FILES:
        if relative not in EXPECTED_DATA_FILES:
            raise UpstreamGDNDataBoundaryError("authorized file identity is absent")
        path = (root / relative).resolve(strict=True)
        if not path.is_relative_to(root):
            raise UpstreamGDNDataBoundaryError("authorized file escaped HAI root")
        expected = EXPECTED_DATA_FILES[relative]
        observed_size = path.stat().st_size
        observed_sha = _stream_sha256(path)
        with path.open("rb") as handle:
            raw_header = handle.readline().rstrip(b"\r\n")
        header_sha = hashlib.sha256(raw_header).hexdigest()
        try:
            header = tuple(next(csv.reader([raw_header.decode("utf-8-sig")])))
        except (UnicodeDecodeError, csv.Error, StopIteration) as exc:
            raise UpstreamGDNDataBoundaryError("authorized HAI header is invalid") from exc
        feature_order = tuple(name for name in header if name.startswith("P1_"))
        if (
            observed_size != expected["byte_size"]
            or observed_sha != expected["sha256"]
            or header_sha != expected["header_sha256"]
        ):
            raise UpstreamGDNDataBoundaryError("authorized HAI file identity mismatch")
        feature_orders.append(feature_order)
        records.append(
            {
                "relative_path": relative,
                "byte_size": observed_size,
                "sha256": observed_sha,
                "header_sha256": header_sha,
                "file_identity_match": True,
                "header_identity_match": True,
            }
        )
    if len(set(feature_orders)) != 1:
        raise UpstreamGDNDataBoundaryError("authorized P1 feature orders differ")
    feature_order = feature_orders[0]
    if stable_hash_v1({"features": list(feature_order)}) != CANDIDATE_FEATURE_ORDER_HASH:
        raise UpstreamGDNDataBoundaryError("candidate feature-order hash changed")
    return feature_order, records


def _execution_state(
    *,
    status: str,
    execution_commit: str,
    created_at: str,
    train1_accessed: bool,
    train2_accessed: bool,
    feature_count: int,
    file_records: Sequence[Mapping[str, Any]],
    seeds_attempted: Sequence[int],
    seeds_completed: Sequence[int],
    ledger_hashes: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return _self_hashed(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039c_gdnp_private_execution_state_v1",
            "task_id": TASK_ID,
            "status": status,
            "execution_commit": execution_commit,
            "created_at": created_at,
            "train1_accessed": train1_accessed,
            "train2_accessed": train2_accessed,
            "feature_count": feature_count,
            "authorized_file_records": [dict(item) for item in file_records],
            "seeds_attempted": list(seeds_attempted),
            "seeds_completed": list(seeds_completed),
            "private_seed_ledger_hashes": [dict(item) for item in ledger_hashes],
            "seed_retry_count": 0,
        }
    )


def _write_state(roots: Any, state: Mapping[str, Any]) -> None:
    _write_json(_private_path(roots, PRIVATE_EXECUTION_STATE), state)


def _private_seed_ledger(record: GDNSeedGraphRecordV1) -> dict[str, Any]:
    pairs = tuple(sorted(record.candidate_similarities))
    return _self_hashed(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039c_gdnp_private_seed_ledger_v1",
            "task_id": TASK_ID,
            "seed": record.seed,
            "successful": record.successful,
            "epoch_count": record.epoch_count,
            "best_validation_loss": record.best_validation_loss,
            "hyperparameter_hash": record.hyperparameter_hash,
            "selected_edges": [
                {"source": source, "target": target}
                for source, target in record.selected_edges
            ],
            "candidate_similarities": [
                {
                    "source": source,
                    "target": target,
                    "upstream_graph_similarity": record.candidate_similarities[
                        (source, target)
                    ],
                }
                for source, target in pairs
            ],
            "raw_rows_included": False,
            "raw_windows_included": False,
            "node_embeddings_included": False,
            "checkpoint_included": False,
            "attack_information_included": False,
        }
    )


def _build_access_audit(
    *,
    status: str,
    execution_commit: str,
    train1_accessed: bool,
    train2_accessed: bool,
    feature_count: int,
    file_records: Sequence[Mapping[str, Any]],
    created_at: str,
) -> dict[str, Any]:
    content = {
        "schema_version": "1.0.0",
        "artifact_type": "task039c_gdnp_data_access_audit_v1",
        "task_id": TASK_ID,
        "status": status,
        "execution_code_commit": execution_commit,
        "compatibility_closure_receipt_hash": COMPATIBILITY_RECEIPT_HASH,
        "environment_receipt_hash": EXACT_ENVIRONMENT_RECEIPT_HASH,
        "process_id": "P1",
        "split_role": NORMAL_CANDIDATE_FIT,
        "candidate_learning_view_id": CANDIDATE_LEARNING_VIEW_ID,
        "candidate_feature_order_hash": CANDIDATE_FEATURE_ORDER_HASH,
        "feature_count": feature_count,
        "authorized_files": list(ALLOWED_VALUE_FILES),
        "authorized_file_records": [dict(item) for item in file_records],
        "train1_accessed": train1_accessed,
        "train2_accessed": train2_accessed,
        "train3_accessed": False,
        "train4_accessed": False,
        "test_accessed": False,
        "labels_accessed": False,
        "attacks_accessed": False,
        "private_label_custody_accessed": False,
        "p2_p3_p4_feature_values_accessed": False,
        "br2_pair_supervision_used": False,
        "meta_output_used": False,
        "stat_output_used": False,
        "raw_values_persisted": False,
        "raw_windows_persisted": False,
        "node_embeddings_persisted": False,
        "checkpoint_persisted": False,
        "absolute_paths_disclosed": False,
        "private_seed_ledgers_outside_git": True,
        "created_at": created_at,
    }
    assert_public_payload_sanitized_v1(content)
    return _self_hashed(content)


def _build_passing_result(
    *,
    execution_commit: str,
    environment: Mapping[str, Any],
    ranking: Sequence[Any],
    seed_records: Sequence[GDNSeedGraphRecordV1],
    ledger_hashes: Sequence[Mapping[str, Any]],
    data_access_audit_hash: str,
    created_at: str,
) -> dict[str, Any]:
    base = GDNCandidateResultV1(
        status="passed_task039c_gdn_candidate_discovery",
        phase_a_commit=PHASE_A_COMMIT,
        fidelity_receipt_hash=ORIGINAL_FIDELITY_RECEIPT_HASH,
        dependency_environment_fingerprint=str(
            environment["dependency_environment_fingerprint"]
        ),
        backend_classification="upstream_aligned_validated",
        source_count=12,
        target_count=12,
        real_hai_feature_access=True,
        seeds_attempted=FROZEN_SEEDS,
        seeds_completed=FROZEN_SEEDS,
        br2_pair_supervision_used=False,
        train3_accessed=False,
        train4_accessed=False,
        test_accessed=False,
        attention_used_for_primary_ranking=False,
        posthoc_xai_used=False,
        created_at=created_at,
        ranking=tuple(ranking),
        seed_records=tuple(seed_records),
    ).to_dict()
    payload = {key: value for key, value in base.items() if key != "artifact_hash"}
    payload.update(
        {
            "source_identity_hash": SOURCE_IDENTITY_HASH,
            "target_identity_hash": TARGET_IDENTITY_HASH,
            "candidate_learning_view_id": CANDIDATE_LEARNING_VIEW_ID,
            "environment_receipt_hash": EXACT_ENVIRONMENT_RECEIPT_HASH,
            "remediation_execution_commit": GDNR_IMPLEMENTATION_COMMIT,
            "compatibility_execution_commit": execution_commit,
            "compatibility_receipt_hash": COMPATIBILITY_RECEIPT_HASH,
            "compatibility_closure_receipt_hash": COMPATIBILITY_RECEIPT_HASH,
            "execution_code_commit": execution_commit,
            "private_seed_ledger_hashes": [dict(item) for item in ledger_hashes],
            "data_access_audit_ref": ACCESS_OUTPUT.name,
            "data_access_audit_hash": data_access_audit_hash,
            "train1_accessed": True,
            "train2_accessed": True,
            "labels_accessed": False,
            "attacks_accessed": False,
            "meta_output_used": False,
            "stat_output_used": False,
            "lineage_history": {
                "initial_gdn_status": "blocked_optional_dependency",
                "gdnr_environment_status": "passed_exact_gdn_environment_remediation",
                "gdnr_status": "failed_gdn_training",
                "gdnr_failure_seed": 11,
                "gdnr_ranking_produced": False,
                "gdnc_compatibility_correction_count": 1,
                "gdnc_compatibility_classification": "documented_non_scientific_api_adapter",
                "gdnc_final_attempt": True,
            },
            "gdnp_lineage_history": {
                "previous_status": "failed_gdn_final_attempt",
                "previous_result_commit": GDNC_RESULT_COMMIT,
                "compatibility_closure_status": COMPATIBILITY_STATUS,
                "node_dim_adapter_classification": "documented_non_scientific_api_adapter",
                "final_execution_attempt": True,
            },
        }
    )
    assert_public_payload_sanitized_v1(payload)
    return {**payload, "artifact_hash": stable_hash_v1(payload)}


def _build_execution_receipt(
    *,
    status: str,
    execution_commit: str,
    environment: Mapping[str, Any],
    scientific_hashes: Mapping[str, str],
    access: Mapping[str, Any],
    result: Mapping[str, Any],
    seeds_attempted: Sequence[int],
    seeds_completed: Sequence[int],
    seed_records: Sequence[Mapping[str, Any]],
    ledger_hashes: Sequence[Mapping[str, Any]],
    failure_stage: str | None,
    failure_type: str | None,
    failure_message: str | None,
    created_at: str,
) -> dict[str, Any]:
    passed = status == "passed_task039c_gdn_candidate_discovery"
    content = {
        "schema_version": "1.0.0",
        "artifact_type": "task039c_gdnp_execution_receipt_v1",
        "task_id": TASK_ID,
        "status": status,
        "execution_code_commit": execution_commit,
        "base_commit": BASE_COMMIT,
        "compatibility_closure_receipt_hash": COMPATIBILITY_RECEIPT_HASH,
        "environment_receipt_hash": EXACT_ENVIRONMENT_RECEIPT_HASH,
        "wheelhouse_receipt_hash": WHEELHOUSE_RECEIPT_HASH,
        "fidelity_receipt_hash": ORIGINAL_FIDELITY_RECEIPT_HASH,
        "protocol_bundle_hash": TASK039C0_PROTOCOL_BUNDLE_HASH,
        "gdn_policy_hash": TASK039C0_GDN_POLICY_HASH,
        "pair_universe_hash": TASK039C0_PAIR_UNIVERSE_HASH,
        "source_identity_hash": SOURCE_IDENTITY_HASH,
        "target_identity_hash": TARGET_IDENTITY_HASH,
        "candidate_learning_view_id": CANDIDATE_LEARNING_VIEW_ID,
        "candidate_feature_order_hash": CANDIDATE_FEATURE_ORDER_HASH,
        "upstream_commit": UPSTREAM_GDN_COMMIT,
        "dependency_environment_fingerprint": environment[
            "dependency_environment_fingerprint"
        ],
        "hyperparameter_hash": HYPERPARAMETER_HASH,
        "scientific_source_hashes": dict(scientific_hashes),
        "execution_commit_clean_at_start": True,
        "scientific_source_change_after_execution_start": False,
        "seed_order": list(FROZEN_SEEDS),
        "seeds_attempted": list(seeds_attempted),
        "seeds_completed": list(seeds_completed),
        "seed_retry_count": 0,
        "seed_records": [dict(item) for item in seed_records],
        "private_seed_ledger_hashes": [dict(item) for item in ledger_hashes],
        "aggregation_denominator": 3,
        "evaluated_candidate_count": int(result.get("evaluated_candidate_count", 0)) if passed else 0,
        "supported_candidate_count": int(result.get("supported_candidate_count", 0)) if passed else 0,
        "ranking_produced": passed,
        "ranking_hash": result.get("ranking_hash") if passed else None,
        "top10_count": len(result.get("top10", ())) if passed else 0,
        "top20_count": len(result.get("top20", ())) if passed else 0,
        "top40_count": len(result.get("top40", ())) if passed else 0,
        "candidate_shortfall": result.get("candidate_shortfall") if passed else None,
        "data_access_audit_hash": access["artifact_hash"],
        "gdn_result_artifact_hash": result.get("artifact_hash") if passed else None,
        "br2_pair_supervision_used": False,
        "meta_output_used": False,
        "stat_output_used": False,
        "attention_used_for_primary_ranking": False,
        "posthoc_xai_used": False,
        "checkpoint_persisted": False,
        "failure_stage": failure_stage,
        "failure_type": failure_type,
        "failure_message": failure_message,
        "recommendation": (
            "PROCEED_WITH_THREE_ARM_INTEGRATION"
            if passed
            else "KEEP_GDN_UNAVAILABLE_AND_PROCEED_WITH_META_STAT"
        ),
        "created_at": created_at,
    }
    assert_public_payload_sanitized_v1(content)
    return _self_hashed(content)


def _build_report(
    *,
    compatibility: Mapping[str, Any],
    access: Mapping[str, Any],
    execution: Mapping[str, Any],
    result: Mapping[str, Any] | None,
) -> str:
    passed = execution["status"] == "passed_task039c_gdn_candidate_discovery"
    lines = [
        "# TASK-039C-GDNP Port Compatibility Closure and GDN Candidate Discovery",
        "",
        f"Status: `{execution['status']}`",
        "",
        "The PyG 1.5 to 2.8 compatibility matrix has no unresolved rows. The existing sparse-softmax keyword adapter and explicit `node_dim=0` binding are classified as `documented_non_scientific_api_adapter`; model equations, learned graph construction, hyperparameters, data policy, and ranking are unchanged.",
        "",
        "## Compatibility",
        "",
        f"- Closure receipt: `{compatibility['artifact_hash']}`.",
        f"- Environment receipt: `{EXACT_ENVIRONMENT_RECEIPT_HASH}`.",
        f"- Fidelity receipt: `{ORIGINAL_FIDELITY_RECEIPT_HASH}`.",
        f"- Legacy oracle: `{compatibility['legacy_oracle_status']}` (nonblocking).",
        "- GraphLayer forward/backward, index/self-loop, GNNLayer, tiny full-GDN, and tiny training-loop gates passed before HAI access.",
        "",
        "## Execution",
        "",
        f"- Seeds attempted: `{execution['seeds_attempted']}`.",
        f"- Seeds completed: `{execution['seeds_completed']}`.",
        "- Seed retries: `0`.",
        f"- Evaluated candidates: `{execution['evaluated_candidate_count']}`.",
        f"- Supported candidates: `{execution['supported_candidate_count']}`.",
        f"- Ranking hash: `{execution['ranking_hash']}`.",
        f"- Data-access audit: `{access['artifact_hash']}`.",
        "",
        "## Data and claim boundary",
        "",
        f"Train1/train2 accessed: `{access['train1_accessed']}` / `{access['train2_accessed']}`. Train3, train4, test, labels, attacks, P2/P3/P4 values, BR2 pair outcomes, META output, and STAT output were not accessed. No checkpoint, state dictionary, raw row, raw window, or embedding was committed.",
        "",
        f"Recommended next path: `{execution['recommendation']}`.",
        "",
        "GDN output is learned-graph candidate evidence only. It does not establish causality, a confirmed relation, rule validity, anomaly performance, root cause, or GDN superiority.",
        "",
    ]
    if not passed:
        lines.insert(5, f"The final run failed closed at `{execution['failure_stage']}`; no candidate ranking was produced.")
    elif result is not None:
        lines.insert(5, "All three frozen seeds completed and the denominator-three ranking was produced once.")
    return "\n".join(lines)


def worker(args: argparse.Namespace) -> None:
    roots, compatibility, _ = validate_commit_a(args.execution_commit)
    _, environment = gdnc._validate_exact_environment()
    created_at = _created_at(args.created_at)
    attempted: list[int] = []
    completed: list[int] = []
    ledger_hashes: list[dict[str, Any]] = []
    public_seed_records: list[dict[str, Any]] = []
    file_records: list[dict[str, Any]] = []
    feature_count = 0
    train1_accessed = False
    train2_accessed = False
    stage = "pre_data_validation"
    try:
        bundle, pairs, fidelity, _ = gdnr._validate_frozen_context()
        source = verify_pinned_upstream_checkout_v1(Path(args.upstream_root))
        if source.to_dict() != fidelity.get("source_verification"):
            raise GDNPExecutionError("pinned upstream source receipt changed")
        authorize_gdn_data_request_v1(
            process_id="P1",
            split_role=NORMAL_CANDIDATE_FIT,
            relative_files=ALLOWED_VALUE_FILES,
            requested_feature_names=tuple(bundle.universe_policy.source_variables)
            + tuple(bundle.universe_policy.target_variables),
            prohibited_inputs=(),
        )
        train1_accessed = True
        train2_accessed = True
        stage = "verify_authorized_train1_train2_identities"
        _write_state(
            roots,
            _execution_state(
                status=stage,
                execution_commit=args.execution_commit,
                created_at=created_at,
                train1_accessed=True,
                train2_accessed=True,
                feature_count=0,
                file_records=(),
                seeds_attempted=attempted,
                seeds_completed=completed,
                ledger_hashes=ledger_hashes,
            ),
        )
        feature_order, file_records = _verify_authorized_files(roots.hai_data_root)
        feature_count = len(feature_order)
        if feature_order != derive_frozen_p1_feature_order_from_headers_v1(
            data_root=roots.hai_data_root
        ):
            raise UpstreamGDNDataBoundaryError("frozen feature-order verification differs")
        authorize_gdn_data_request_v1(
            process_id="P1",
            split_role=NORMAL_CANDIDATE_FIT,
            relative_files=ALLOWED_VALUE_FILES,
            requested_feature_names=feature_order,
            prohibited_inputs=(),
        )
        stage = "load_authorized_train1_train2"
        _write_state(
            roots,
            _execution_state(
                status=stage,
                execution_commit=args.execution_commit,
                created_at=created_at,
                train1_accessed=True,
                train2_accessed=True,
                feature_count=feature_count,
                file_records=file_records,
                seeds_attempted=attempted,
                seeds_completed=completed,
                ledger_hashes=ledger_hashes,
            ),
        )
        segments = load_authorized_numeric_segments_v1(
            local_root=roots.hai_data_root,
            relative_files=ALLOWED_VALUE_FILES,
            feature_order=feature_order,
            process_id="P1",
            split_role=NORMAL_CANDIDATE_FIT,
        )
        config = UpstreamGDNTrainingConfigV1()
        assert_identical_seed_hyperparameters_v1(
            {seed: config for seed in FROZEN_SEEDS}
        )
        seed_records: list[GDNSeedGraphRecordV1] = []
        for seed in FROZEN_SEEDS:
            stage = f"training_seed_{seed}"
            attempted.append(seed)
            _write_state(
                roots,
                _execution_state(
                    status=stage,
                    execution_commit=args.execution_commit,
                    created_at=created_at,
                    train1_accessed=True,
                    train2_accessed=True,
                    feature_count=feature_count,
                    file_records=file_records,
                    seeds_attempted=attempted,
                    seeds_completed=completed,
                    ledger_hashes=ledger_hashes,
                ),
            )
            print(f"TASK-039C-GDNP seed {seed} started", flush=True)
            trained = train_upstream_aligned_seed_v1(
                segments=segments,
                feature_order=feature_order,
                candidate_pairs=pairs,
                seed=seed,
                config=config,
            )
            projected = project_seed_record_to_universe_v1(
                seed=trained.seed,
                selected_model_edges=trained.selected_edges,
                model_similarities=trained.candidate_similarities,
                universe_pairs=pairs,
                hyperparameter_hash=trained.hyperparameter_hash,
                epoch_count=trained.epoch_count,
                best_validation_loss=trained.best_validation_loss,
            )
            private_ledger = _private_seed_ledger(projected)
            ledger_path = _private_path(
                roots, f"TASK-039C_GDNP_SEED_{seed}_PRIVATE_LEDGER.json"
            )
            if ledger_path.exists():
                raise GDNPExecutionError("GDNP seed ledger already exists")
            _write_json(ledger_path, private_ledger)
            seed_records.append(projected)
            completed.append(seed)
            ledger_hashes.append(
                {"seed": seed, "ledger_hash": private_ledger["artifact_hash"]}
            )
            public_seed_records.append(projected.to_dict())
            stage = f"completed_seed_{seed}"
            _write_state(
                roots,
                _execution_state(
                    status=stage,
                    execution_commit=args.execution_commit,
                    created_at=created_at,
                    train1_accessed=True,
                    train2_accessed=True,
                    feature_count=feature_count,
                    file_records=file_records,
                    seeds_attempted=attempted,
                    seeds_completed=completed,
                    ledger_hashes=ledger_hashes,
                ),
            )
            print(f"TASK-039C-GDNP seed {seed} completed", flush=True)
        stage = "aggregate_frozen_ranking"
        ranking = aggregate_and_rank_gdn_candidates_v1(
            universe_pairs=pairs,
            seed_records=seed_records,
        )
        provisional_access = _build_access_audit(
            status="passed_task039c_gdn_candidate_discovery",
            execution_commit=args.execution_commit,
            train1_accessed=True,
            train2_accessed=True,
            feature_count=feature_count,
            file_records=file_records,
            created_at=created_at,
        )
        result = _build_passing_result(
            execution_commit=args.execution_commit,
            environment=environment,
            ranking=ranking,
            seed_records=seed_records,
            ledger_hashes=ledger_hashes,
            data_access_audit_hash=provisional_access["artifact_hash"],
            created_at=created_at,
        )
        outcome = _self_hashed(
            {
                "schema_version": "1.0.0",
                "artifact_type": "task039c_gdnp_private_outcome_v1",
                "task_id": TASK_ID,
                "status": result["status"],
                "result": result,
                "access": provisional_access,
                "seeds_attempted": attempted,
                "seeds_completed": completed,
                "seed_records": public_seed_records,
                "private_seed_ledger_hashes": ledger_hashes,
                "feature_count": feature_count,
                "authorized_file_records": file_records,
                "train1_accessed": True,
                "train2_accessed": True,
                "created_at": created_at,
            }
        )
        _write_json(_private_path(roots, PRIVATE_OUTCOME), outcome)
        _write_state(
            roots,
            _execution_state(
                status=result["status"],
                execution_commit=args.execution_commit,
                created_at=created_at,
                train1_accessed=True,
                train2_accessed=True,
                feature_count=feature_count,
                file_records=file_records,
                seeds_attempted=attempted,
                seeds_completed=completed,
                ledger_hashes=ledger_hashes,
            ),
        )
    except Exception as exc:
        failure_status = (
            "failed_gdnp_data_boundary"
            if isinstance(exc, UpstreamGDNDataBoundaryError)
            else "failed_gdnp_real_gdn_execution"
        )
        failure = _self_hashed(
            {
                "schema_version": "1.0.0",
                "artifact_type": "task039c_gdnp_private_failure_v1",
                "task_id": TASK_ID,
                "status": failure_status,
                "failure_stage": stage,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "train1_accessed": train1_accessed,
                "train2_accessed": train2_accessed,
                "feature_count": feature_count,
                "authorized_file_records": file_records,
                "seeds_attempted": attempted,
                "seeds_completed": completed,
                "seed_records": public_seed_records,
                "private_seed_ledger_hashes": ledger_hashes,
                "seed_retry_count": 0,
                "created_at": created_at,
            }
        )
        _write_json(_private_path(roots, PRIVATE_FAILURE), failure)
        _write_state(
            roots,
            _execution_state(
                status=failure_status,
                execution_commit=args.execution_commit,
                created_at=created_at,
                train1_accessed=train1_accessed,
                train2_accessed=train2_accessed,
                feature_count=feature_count,
                file_records=file_records,
                seeds_attempted=attempted,
                seeds_completed=completed,
                ledger_hashes=ledger_hashes,
            ),
        )
        raise


def _finalize(
    *,
    roots: Any,
    execution_commit: str,
    created_at: str,
    worker_returncode: int,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None, str]:
    _, compatibility, scientific_hashes = validate_commit_a(execution_commit)
    _, environment = gdnc._validate_exact_environment()
    state_path = _private_path(roots, PRIVATE_EXECUTION_STATE)
    state = _load_json(state_path) if state_path.exists() else {}
    if state:
        verify_self_hash_v1(state)
    failure_stage: str | None = None
    failure_type: str | None = None
    failure_message: str | None = None
    result: dict[str, Any] | None = None
    if worker_returncode == 0:
        outcome = _load_json(_private_path(roots, PRIVATE_OUTCOME))
        verify_self_hash_v1(outcome)
        if outcome.get("status") != "passed_task039c_gdn_candidate_discovery":
            raise GDNPExecutionError("successful worker lacks passing outcome")
        result = dict(outcome["result"])
        verify_self_hash_v1(result)
        access = dict(outcome["access"])
        verify_self_hash_v1(access)
        attempted = tuple(int(item) for item in outcome["seeds_attempted"])
        completed = tuple(int(item) for item in outcome["seeds_completed"])
        seed_records = tuple(dict(item) for item in outcome["seed_records"])
        ledger_hashes = tuple(
            dict(item) for item in outcome["private_seed_ledger_hashes"]
        )
        status = "passed_task039c_gdn_candidate_discovery"
    else:
        failure_path = _private_path(roots, PRIVATE_FAILURE)
        failure = _load_json(failure_path) if failure_path.exists() else {}
        if failure:
            verify_self_hash_v1(failure)
        status = str(failure.get("status", "failed_gdnp_real_gdn_execution"))
        if status not in {
            "failed_gdnp_real_gdn_execution",
            "failed_gdnp_data_boundary",
            "blocked_gdnp_external_execution_interruption",
        }:
            status = "failed_gdnp_real_gdn_execution"
        attempted = tuple(int(item) for item in state.get("seeds_attempted", ()))
        completed = tuple(int(item) for item in state.get("seeds_completed", ()))
        seed_records = tuple(dict(item) for item in failure.get("seed_records", ()))
        ledger_hashes = tuple(
            dict(item) for item in state.get("private_seed_ledger_hashes", ())
        )
        failure_stage = str(
            failure.get("failure_stage", state.get("status", "worker_process"))
        )
        failure_type = str(failure.get("error_type", "WorkerProcessError"))
        failure_message = str(
            failure.get("error_message", "the final GDNP worker did not complete")
        )
        access = _build_access_audit(
            status=status,
            execution_commit=execution_commit,
            train1_accessed=bool(state.get("train1_accessed", False)),
            train2_accessed=bool(state.get("train2_accessed", False)),
            feature_count=int(state.get("feature_count", 0)),
            file_records=tuple(state.get("authorized_file_records", ())),
            created_at=created_at,
        )
    execution = _build_execution_receipt(
        status=status,
        execution_commit=execution_commit,
        environment=environment,
        scientific_hashes=scientific_hashes,
        access=access,
        result=result or {},
        seeds_attempted=attempted,
        seeds_completed=completed,
        seed_records=seed_records,
        ledger_hashes=ledger_hashes,
        failure_stage=failure_stage,
        failure_type=failure_type,
        failure_message=failure_message,
        created_at=created_at,
    )
    report = _build_report(
        compatibility=compatibility,
        access=access,
        execution=execution,
        result=result,
    )
    return access, execution, result, report


def execute(args: argparse.Namespace) -> None:
    created_at = _created_at(args.created_at)
    try:
        roots, _, _ = validate_commit_a(args.execution_commit)
    except ExactGDNEnvironmentUnavailable as exc:
        raise GDNPExecutionError("blocked_gdnp_environment_identity_mismatch") from exc
    marker_path = _private_path(roots, PRIVATE_ATTEMPT_MARKER)
    if marker_path.exists():
        raise GDNPExecutionError("the single GDNP real execution attempt is already consumed")
    marker = _self_hashed(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039c_gdnp_final_attempt_marker_v1",
            "task_id": TASK_ID,
            "execution_commit": args.execution_commit,
            "created_at": created_at,
            "final_attempt_authority_consumed": True,
            "seed_order": list(FROZEN_SEEDS),
            "seed_retry_count": 0,
        }
    )
    _write_json(marker_path, marker)
    environment = os.environ.copy()
    environment.update(DETERMINISTIC_ENVIRONMENT)
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "worker",
        "--execution-commit",
        args.execution_commit,
        "--upstream-root",
        args.upstream_root,
        "--created-at",
        created_at,
    ]
    process = subprocess.run(command, check=False, cwd=ROOT, env=environment)
    access, execution, result, report = _finalize(
        roots=roots,
        execution_commit=args.execution_commit,
        created_at=created_at,
        worker_returncode=process.returncode,
    )
    _write_public(ACCESS_OUTPUT, access)
    _write_public(EXECUTION_OUTPUT, execution)
    if execution["status"] == "passed_task039c_gdn_candidate_discovery":
        assert result is not None
        _write_public(RESULT_OUTPUT, result)
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(
        canonical_json_v1(
            {
                "status": execution["status"],
                "compatibility_closure_receipt_hash": COMPATIBILITY_RECEIPT_HASH,
                "execution_receipt_hash": execution["artifact_hash"],
                "gdn_result_artifact_hash": (
                    result["artifact_hash"] if result is not None else None
                ),
            }
        )
    )
    if execution["status"] != "passed_task039c_gdn_candidate_discovery":
        raise SystemExit(2)


def validate_pre_data(args: argparse.Namespace) -> None:
    roots, compatibility, scientific_hashes = validate_commit_a(args.execution_commit)
    del roots
    print(
        canonical_json_v1(
            {
                "status": COMPATIBILITY_STATUS,
                "compatibility_closure_receipt_hash": compatibility["artifact_hash"],
                "scientific_source_hash_count": len(scientific_hashes),
                "hyperparameter_hash": HYPERPARAMETER_HASH,
                "hai_feature_values_accessed": False,
            }
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate-pre-data")
    validate.add_argument("--execution-commit", required=True)
    validate.set_defaults(handler=validate_pre_data)
    execution = subparsers.add_parser("execute")
    execution.add_argument("--execution-commit", required=True)
    execution.add_argument("--upstream-root", required=True)
    execution.add_argument("--created-at")
    execution.set_defaults(handler=execute)
    worker_parser = subparsers.add_parser("worker", help=argparse.SUPPRESS)
    worker_parser.add_argument("--execution-commit", required=True)
    worker_parser.add_argument("--upstream-root", required=True)
    worker_parser.add_argument("--created-at", required=True)
    worker_parser.set_defaults(handler=worker)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        args.handler(args)
    except (GDNPExecutionError, GDNPortCompatibilityError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
