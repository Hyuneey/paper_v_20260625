#!/usr/bin/env python3
"""Audit, receipt, and final execution orchestration for TASK-039C-GDNC."""

from __future__ import annotations

import argparse
import inspect
import json
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scripts import run_task039c_gdn_remediation as gdnr  # noqa: E402
from paperworks.candidates.gdn_candidate_discovery_v1 import (  # noqa: E402
    GDNCandidateResultV1,
    GDNSeedGraphRecordV1,
    aggregate_and_rank_gdn_candidates_v1,
    project_seed_record_to_universe_v1,
)
from paperworks.gdn.gdn_remediation_environment_v1 import (  # noqa: E402
    ALLOWED_VALUE_FILES,
    CANDIDATE_FEATURE_ORDER_HASH,
    CANDIDATE_LEARNING_VIEW_ID,
    DETERMINISTIC_ENVIRONMENT,
    ExactGDNEnvironmentUnavailable,
    PHASE_A_COMMIT,
    SOURCE_IDENTITY_HASH,
    TARGET_IDENTITY_HASH,
    assert_public_payload_sanitized_v1,
    derive_frozen_p1_feature_order_from_headers_v1,
    enrich_passing_gdn_result_v1,
    verify_self_hash_v1,
)
from paperworks.gdn.pyg_softmax_compatibility_v1 import (  # noqa: E402
    COMPATIBILITY_CLASSIFICATION,
    COMPATIBILITY_STATUS,
    EXACT_ENVIRONMENT_RECEIPT_HASH,
    GDNR_DATA_ACCESS_AUDIT_HASH,
    GDNR_EXECUTION_RECEIPT_HASH,
    GDNR_IMPLEMENTATION_COMMIT,
    GDNR_RESULT_COMMIT,
    INSTALLED_PYG_SIGNATURE,
    ORIGINAL_FIDELITY_RECEIPT_HASH,
    PATCHED_IMPLEMENTATION_PATH,
    WHEELHOUSE_RECEIPT_HASH,
    PyGSoftmaxCompatibilityError,
    assert_allowed_gdnc_paths_v1,
    assert_gdnc_scientific_patch_scope_v1,
    build_pyg_softmax_compatibility_receipt_v1,
    verify_pyg_softmax_compatibility_receipt_v1,
    verify_synthetic_semantic_equivalence_v1,
)
from paperworks.gdn.upstream_candidate_backend_v1 import (  # noqa: E402
    FROZEN_SEEDS,
    NORMAL_CANDIDATE_FIT,
    TASK039C0_GDN_POLICY_HASH,
    TASK039C0_PAIR_UNIVERSE_HASH,
    TASK039C0_PROTOCOL_BUNDLE_HASH,
    UPSTREAM_GDN_COMMIT,
    UpstreamGDNTrainingConfigV1,
    assert_identical_seed_hyperparameters_v1,
    authorize_gdn_data_request_v1,
    load_authorized_numeric_segments_v1,
    train_upstream_aligned_seed_v1,
    verify_pinned_upstream_checkout_v1,
)
from paperworks.v6.common import canonical_json_v1, stable_hash_v1  # noqa: E402


BRANCH = "task-039c-gdn-compat"
TASK_ID = "TASK-039C-GDNC"
GDNR_EXECUTION = ROOT / "docs/task_reports/TASK-039C_GDNR_EXECUTION_RECEIPT.json"
GDNR_ACCESS = ROOT / "docs/task_reports/TASK-039C_GDNR_DATA_ACCESS_AUDIT.json"
ENVIRONMENT_RECEIPT = ROOT / "docs/task_reports/TASK-039C_GDNR_ENVIRONMENT_RECEIPT.json"
COMPATIBILITY_RECEIPT = ROOT / "docs/task_reports/TASK-039C_GDNC_COMPATIBILITY_RECEIPT.json"
ACCESS_OUTPUT = ROOT / "docs/task_reports/TASK-039C_GDNC_DATA_ACCESS_AUDIT.json"
EXECUTION_OUTPUT = ROOT / "docs/task_reports/TASK-039C_GDNC_EXECUTION_RECEIPT.json"
REPORT_OUTPUT = ROOT / "docs/task_reports/TASK-039C_GDNC_REPORT.md"
RESULT_OUTPUT = ROOT / "docs/task_reports/TASK-039C_GDN_RESULT.json"

PRIVATE_ATTEMPT_MARKER = "TASK-039C_GDNC_FINAL_ATTEMPT.json"
PRIVATE_EXECUTION_STATE = "TASK-039C_GDNC_EXECUTION_STATE.json"
PRIVATE_OUTCOME = "TASK-039C_GDNC_PRIVATE_OUTCOME.json"
PRIVATE_FAILURE = "TASK-039C_GDNC_PRIVATE_FAILURE.json"

ALLOWED_COMMIT_A_PATHS = (
    "TASKS/TASK-039C_GDNC_SOFTMAX_COMPATIBILITY.md",
    "docs/task_reports/TASK-039C_GDNC_COMPATIBILITY_RECEIPT.json",
    "docs/v6/GDN_PYG_SOFTMAX_COMPATIBILITY.md",
    "schemas/v6/gdn_candidate_result_v1_schema.json",
    "schemas/v6/pyg_softmax_compatibility_receipt_v1_schema.json",
    "schemas/v6/task039c_gdnc_data_access_audit_v1_schema.json",
    "schemas/v6/task039c_gdnc_execution_receipt_v1_schema.json",
    "scripts/run_task039c_gdn_compat.py",
    "src/paperworks/gdn/pyg_softmax_compatibility_v1.py",
    PATCHED_IMPLEMENTATION_PATH,
    "tests/test_task039c_gdn_compatibility.py",
    "tests/test_task039c_gdn_compat_execution.py",
    "tests/test_task039c_gdn_compat_schemas.py",
)


def _created_at(value: str | None) -> str:
    return value or datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PyGSoftmaxCompatibilityError(f"required public JSON is unavailable: {path.name}") from exc


def _write_json(path: Path, document: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _write_public(path: Path, document: Mapping[str, Any]) -> None:
    assert_public_payload_sanitized_v1(document)
    _write_json(path, document)


def _self_hashed(content: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(content)
    return {**payload, "artifact_hash": stable_hash_v1(payload)}


def _git(*arguments: str, check: bool = True) -> str:
    result = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={ROOT.resolve().as_posix()}",
            "-C",
            str(ROOT),
            *arguments,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise PyGSoftmaxCompatibilityError("Git lineage verification failed")
    return result.stdout.strip() if result.returncode == 0 else ""


def _private_path(roots: Any, name: str) -> Path:
    path = (roots.private_root / name).resolve()
    if not path.is_relative_to(roots.private_root.resolve()):
        raise PyGSoftmaxCompatibilityError("private output path escaped its root")
    return path


def _validate_prior_receipts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    execution = _load_json(GDNR_EXECUTION)
    access = _load_json(GDNR_ACCESS)
    environment = _load_json(ENVIRONMENT_RECEIPT)
    if verify_self_hash_v1(execution) != GDNR_EXECUTION_RECEIPT_HASH:
        raise PyGSoftmaxCompatibilityError("GDNR execution receipt identity mismatch")
    if verify_self_hash_v1(access) != GDNR_DATA_ACCESS_AUDIT_HASH:
        raise PyGSoftmaxCompatibilityError("GDNR access-audit identity mismatch")
    if verify_self_hash_v1(environment) != EXACT_ENVIRONMENT_RECEIPT_HASH:
        raise PyGSoftmaxCompatibilityError("exact environment receipt identity mismatch")
    if (
        execution.get("status") != "failed_gdn_training"
        or execution.get("seeds_attempted") != [11]
        or execution.get("seeds_completed") != []
        or execution.get("ranking_hash") is not None
        or execution.get("fidelity_receipt_hash") != ORIGINAL_FIDELITY_RECEIPT_HASH
        or execution.get("environment_receipt_hash") != EXACT_ENVIRONMENT_RECEIPT_HASH
        or execution.get("wheelhouse_receipt_hash") != WHEELHOUSE_RECEIPT_HASH
        or environment.get("wheelhouse_receipt_hash") != WHEELHOUSE_RECEIPT_HASH
        or environment.get("environment_exact_match") is not True
    ):
        raise PyGSoftmaxCompatibilityError("GDNR failed-result facts changed")
    return execution, access, environment


def _validate_base_lineage() -> None:
    if _git("branch", "--show-current") != BRANCH:
        raise PyGSoftmaxCompatibilityError("GDNC is on the wrong branch")
    if _git("merge-base", "HEAD", GDNR_RESULT_COMMIT) != GDNR_RESULT_COMMIT:
        raise PyGSoftmaxCompatibilityError("GDNC does not descend from the exact GDNR result")
    if _git("rev-parse", "refs/remotes/origin/task-039c-gdn-remediation") != GDNR_RESULT_COMMIT:
        raise PyGSoftmaxCompatibilityError("remote GDNR branch identity changed")
    _validate_prior_receipts()


def _load_compatibility_receipt() -> dict[str, Any]:
    receipt = _load_json(COMPATIBILITY_RECEIPT)
    verify_pyg_softmax_compatibility_receipt_v1(receipt)
    return receipt


def _validate_commit_a(execution_commit: str) -> tuple[dict[str, Any], dict[str, str]]:
    _validate_base_lineage()
    if _git("rev-parse", "HEAD") != execution_commit:
        raise PyGSoftmaxCompatibilityError("execution commit is not current HEAD")
    if _git("rev-parse", "HEAD^") != GDNR_RESULT_COMMIT:
        raise PyGSoftmaxCompatibilityError("Commit A parent is not the exact GDNR result")
    if _git("status", "--porcelain=v1"):
        raise PyGSoftmaxCompatibilityError("execution worktree or index is not clean")
    changed = assert_allowed_gdnc_paths_v1(
        repository_root=ROOT,
        allowed_paths=ALLOWED_COMMIT_A_PATHS,
    )
    if PATCHED_IMPLEMENTATION_PATH not in changed:
        raise PyGSoftmaxCompatibilityError("approved compatibility source was not patched")
    patched_hash = assert_gdnc_scientific_patch_scope_v1(repository_root=ROOT)
    receipt = _load_compatibility_receipt()
    if receipt.get("patched_implementation_hash") != patched_hash:
        raise PyGSoftmaxCompatibilityError("compatibility receipt source binding changed")
    _, _, _, scientific_hashes = gdnr._validate_frozen_context()
    return receipt, scientific_hashes


def _validate_exact_environment() -> tuple[Any, dict[str, Any]]:
    roots = gdnr._validate_external_roots()
    if not Path(sys.executable).resolve().is_relative_to(roots.environment_root.resolve()):
        raise ExactGDNEnvironmentUnavailable("GDNC is not running in the exact environment")
    private, _ = gdnr._load_and_reverify_environment(roots)
    public = private["public_receipt"]
    committed = _load_json(ENVIRONMENT_RECEIPT)
    if public != committed or verify_self_hash_v1(public) != EXACT_ENVIRONMENT_RECEIPT_HASH:
        raise ExactGDNEnvironmentUnavailable("blocked_gdnc_environment_identity_mismatch")
    if (
        platform.python_version() != "3.12.13"
        or public.get("platform_id") != "windows-amd64"
        or public.get("top_level_packages", {}).get("torch") != "2.12.1"
        or public.get("top_level_packages", {}).get("torch-geometric") != "2.8.0"
    ):
        raise ExactGDNEnvironmentUnavailable("blocked_gdnc_environment_identity_mismatch")
    return roots, public


def build_compatibility_receipt(args: argparse.Namespace) -> None:
    _validate_base_lineage()
    roots, _ = _validate_exact_environment()
    del roots
    source = verify_pinned_upstream_checkout_v1(Path(args.upstream_root))
    if source.commit != UPSTREAM_GDN_COMMIT or not source.clean_worktree:
        raise PyGSoftmaxCompatibilityError("pinned upstream checkout changed")
    upstream_graph = Path(args.upstream_root) / "models/graph_layer.py"
    if "alpha = softmax(alpha, edge_index_i, size_i)" not in upstream_graph.read_text(
        encoding="utf-8"
    ):
        raise PyGSoftmaxCompatibilityError("upstream softmax call changed")
    from importlib.metadata import version
    from torch_geometric.utils import softmax

    if version("torch-geometric") != "2.8.0":
        raise ExactGDNEnvironmentUnavailable("blocked_gdnc_environment_identity_mismatch")
    signature = str(inspect.signature(softmax))
    if signature != INSTALLED_PYG_SIGNATURE:
        raise PyGSoftmaxCompatibilityError("installed PyG softmax signature changed")
    patched_hash = assert_gdnc_scientific_patch_scope_v1(repository_root=ROOT)
    assert_allowed_gdnc_paths_v1(
        repository_root=ROOT,
        allowed_paths=ALLOWED_COMMIT_A_PATHS,
    )
    cases = verify_synthetic_semantic_equivalence_v1()
    receipt = build_pyg_softmax_compatibility_receipt_v1(
        patched_implementation_hash=patched_hash,
        installed_pyg_signature=signature,
        equivalence_cases=cases,
        created_at=_created_at(args.created_at),
    )
    if COMPATIBILITY_RECEIPT.exists():
        raise PyGSoftmaxCompatibilityError("compatibility receipt already exists")
    _write_public(COMPATIBILITY_RECEIPT, receipt)
    print(
        canonical_json_v1(
            {
                "status": receipt["status"],
                "classification": receipt["classification"],
                "compatibility_receipt_hash": receipt["artifact_hash"],
                "patched_implementation_hash": patched_hash,
            }
        )
    )


def _execution_state(
    *,
    status: str,
    execution_commit: str,
    created_at: str,
    train1_accessed: bool,
    train2_accessed: bool,
    feature_count: int,
    seeds_attempted: Sequence[int],
    seeds_completed: Sequence[int],
    ledger_hashes: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return _self_hashed(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039c_gdnc_private_execution_state_v1",
            "task_id": TASK_ID,
            "status": status,
            "execution_commit": execution_commit,
            "created_at": created_at,
            "train1_accessed": train1_accessed,
            "train2_accessed": train2_accessed,
            "feature_count": feature_count,
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
            "artifact_type": "task039c_gdnc_private_seed_ledger_v1",
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
    compatibility_receipt_hash: str,
    train1_accessed: bool,
    train2_accessed: bool,
    feature_count: int,
    created_at: str,
) -> dict[str, Any]:
    content = {
        "schema_version": "1.0.0",
        "artifact_type": "task039c_gdnc_data_access_audit_v1",
        "task_id": TASK_ID,
        "status": status,
        "compatibility_receipt_hash": compatibility_receipt_hash,
        "environment_receipt_hash": EXACT_ENVIRONMENT_RECEIPT_HASH,
        "process_id": "P1",
        "split_role": NORMAL_CANDIDATE_FIT,
        "candidate_learning_view_id": CANDIDATE_LEARNING_VIEW_ID,
        "candidate_feature_order_hash": CANDIDATE_FEATURE_ORDER_HASH,
        "feature_count": feature_count,
        "authorized_files": list(ALLOWED_VALUE_FILES),
        "files_accessed": [
            relative
            for relative, accessed in zip(
                ALLOWED_VALUE_FILES,
                (train1_accessed, train2_accessed),
                strict=True,
            )
            if accessed
        ],
        "train1_accessed": train1_accessed,
        "train2_accessed": train2_accessed,
        "train3_accessed": False,
        "train4_accessed": False,
        "test_accessed": False,
        "labels_accessed": False,
        "attacks_accessed": False,
        "br2_pair_supervision_used": False,
        "meta_output_used": False,
        "stat_output_used": False,
        "p2_p3_p4_feature_values_accessed": False,
        "partial_gdnr_state_reused": False,
        "run_restarted_from_clean_commit": True,
        "raw_values_persisted": False,
        "raw_windows_persisted": False,
        "node_embeddings_persisted": False,
        "checkpoint_persisted": False,
        "private_seed_ledgers_outside_git": True,
        "created_at": created_at,
    }
    assert_public_payload_sanitized_v1(content)
    return _self_hashed(content)


def _build_passing_result(
    *,
    execution_commit: str,
    compatibility_receipt_hash: str,
    environment: Mapping[str, Any],
    ranking: Sequence[Any],
    seed_records: Sequence[GDNSeedGraphRecordV1],
    ledger_hashes: Sequence[Mapping[str, Any]],
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
    )
    enriched = enrich_passing_gdn_result_v1(
        base_result=base.to_dict(),
        environment_receipt_hash=EXACT_ENVIRONMENT_RECEIPT_HASH,
        remediation_execution_commit=GDNR_IMPLEMENTATION_COMMIT,
        private_seed_ledger_hashes=ledger_hashes,
        data_access_audit_ref=ACCESS_OUTPUT.name,
    )
    payload = {key: value for key, value in enriched.items() if key != "artifact_hash"}
    payload.update(
        {
            "compatibility_execution_commit": execution_commit,
            "compatibility_receipt_hash": compatibility_receipt_hash,
            "lineage_history": {
                "initial_gdn_status": "blocked_optional_dependency",
                "gdnr_environment_status": "passed_exact_gdn_environment_remediation",
                "gdnr_status": "failed_gdn_training",
                "gdnr_failure_seed": 11,
                "gdnr_ranking_produced": False,
                "gdnc_compatibility_correction_count": 1,
                "gdnc_compatibility_classification": COMPATIBILITY_CLASSIFICATION,
                "gdnc_final_attempt": True,
            },
        }
    )
    assert_public_payload_sanitized_v1(payload)
    return {**payload, "artifact_hash": stable_hash_v1(payload)}


def _build_execution_receipt(
    *,
    status: str,
    execution_commit: str,
    compatibility_receipt_hash: str,
    scientific_hashes: Mapping[str, str],
    access: Mapping[str, Any],
    result: Mapping[str, Any],
    seeds_attempted: Sequence[int],
    seeds_completed: Sequence[int],
    ledger_hashes: Sequence[Mapping[str, Any]],
    failure_stage: str | None,
    failure_type: str | None,
    created_at: str,
) -> dict[str, Any]:
    passed = status == "passed_task039c_gdn_candidate_discovery"
    content = {
        "schema_version": "1.0.0",
        "artifact_type": "task039c_gdnc_execution_receipt_v1",
        "task_id": TASK_ID,
        "status": status,
        "gdnc_execution_commit": execution_commit,
        "gdnr_result_commit": GDNR_RESULT_COMMIT,
        "gdnr_execution_receipt_hash": GDNR_EXECUTION_RECEIPT_HASH,
        "compatibility_receipt_hash": compatibility_receipt_hash,
        "environment_receipt_hash": EXACT_ENVIRONMENT_RECEIPT_HASH,
        "wheelhouse_receipt_hash": WHEELHOUSE_RECEIPT_HASH,
        "fidelity_receipt_hash": ORIGINAL_FIDELITY_RECEIPT_HASH,
        "protocol_bundle_hash": TASK039C0_PROTOCOL_BUNDLE_HASH,
        "gdn_policy_hash": TASK039C0_GDN_POLICY_HASH,
        "pair_universe_hash": TASK039C0_PAIR_UNIVERSE_HASH,
        "source_identity_hash": SOURCE_IDENTITY_HASH,
        "target_identity_hash": TARGET_IDENTITY_HASH,
        "upstream_commit": UPSTREAM_GDN_COMMIT,
        "scientific_source_hashes": dict(scientific_hashes),
        "execution_commit_clean_at_start": True,
        "scientific_source_change_after_execution_start": False,
        "single_compatibility_correction_count": 1,
        "seed_order": list(FROZEN_SEEDS),
        "seeds_attempted": list(seeds_attempted),
        "seeds_completed": list(seeds_completed),
        "seed_retry_count": 0,
        "private_seed_ledger_hashes": [dict(item) for item in ledger_hashes],
        "evaluated_candidate_count": int(result.get("evaluated_candidate_count", 0)) if passed else 0,
        "supported_candidate_count": int(result.get("supported_candidate_count", 0)) if passed else 0,
        "ranking_produced": passed,
        "ranking_hash": result.get("ranking_hash") if passed else None,
        "top10_count": len(result.get("top10", ())) if passed else 0,
        "top20_count": len(result.get("top20", ())) if passed else 0,
        "top40_count": len(result.get("top40", ())) if passed else 0,
        "candidate_shortfall": result.get("candidate_shortfall") if passed else None,
        "data_access_audit_hash": access["artifact_hash"],
        "gdn_result_artifact_hash": result["artifact_hash"],
        "br2_pair_supervision_used": False,
        "meta_output_used": False,
        "stat_output_used": False,
        "attention_used_for_primary_ranking": False,
        "posthoc_xai_used": False,
        "checkpoint_persisted": False,
        "recommendation": (
            "PROCEED_WITH_THREE_ARM_INTEGRATION"
            if passed
            else "PROCEED_WITH_META_STAT_INTEGRATION_GDN_UNAVAILABLE"
        ),
        "failure_stage": failure_stage,
        "failure_type": failure_type,
        "created_at": created_at,
    }
    assert_public_payload_sanitized_v1(content)
    return _self_hashed(content)


def _build_report(
    *,
    status: str,
    compatibility: Mapping[str, Any],
    access: Mapping[str, Any],
    execution: Mapping[str, Any],
    result: Mapping[str, Any],
) -> str:
    passed = status == "passed_task039c_gdn_candidate_discovery"
    recommendation = execution["recommendation"]
    outcome = (
        "All frozen seeds completed and the existing denominator-three ranking was applied."
        if passed
        else "The final GDN attempt failed closed. No ranking or top-K output was produced."
    )
    lines = [
        "# TASK-039C-GDNC Softmax Compatibility and Final GDN Attempt",
        "",
        f"Status: `{status}`",
        "",
        (
            "The single correction is classified as "
            f"`{COMPATIBILITY_CLASSIFICATION}`. The project-owned port now binds the "
            "upstream third-argument node-count meaning to PyG 2.8's explicit "
            "`num_nodes` keyword. No mathematical input, model equation, graph edge, "
            "hyperparameter, package, seed, or ranking rule changed."
        ),
        "",
        outcome,
        "",
        "## Lineage",
        "",
        "- Initial GDN: `blocked_optional_dependency`.",
        "- GDNR: exact environment passed; seed 11 failed before completion because the old positional node count bound to PyG 2.8 `ptr`.",
        f"- GDNC: one semantics-preserving correction; final attempt seeds attempted `{execution['seeds_attempted']}` and completed `{execution['seeds_completed']}`; retries `0`.",
        "",
        "## Receipts",
        "",
        f"- Compatibility receipt: `{compatibility['artifact_hash']}`.",
        f"- Environment receipt: `{EXACT_ENVIRONMENT_RECEIPT_HASH}`.",
        f"- Fidelity receipt: `{ORIGINAL_FIDELITY_RECEIPT_HASH}`.",
        f"- Data-access audit: `{access['artifact_hash']}`.",
        f"- Execution receipt: `{execution['artifact_hash']}`.",
        f"- GDN result binding: `{result['artifact_hash']}`.",
        "",
        "## Data and claim boundary",
        "",
        f"Train1/train2 accessed: `{access['train1_accessed']}` / `{access['train2_accessed']}`. Train3, train4, test, labels, attacks, BR2 pair supervision, META output, and STAT output were not used. No checkpoint, raw window, raw value, or node embedding was persisted.",
        "",
        f"Recommended next path: `{recommendation}`.",
        "",
        "GDN output is candidate graph evidence only. It does not establish causality, a confirmed relation, rule validity, anomaly performance, or method superiority. TASK-039D remains unauthorized.",
        "",
    ]
    return "\n".join(lines)


def worker(args: argparse.Namespace) -> None:
    roots, environment = _validate_exact_environment()
    compatibility, _ = _validate_commit_a(args.execution_commit)
    created_at = _created_at(args.created_at)
    attempted: list[int] = []
    completed: list[int] = []
    ledger_hashes: list[dict[str, Any]] = []
    feature_count = 0
    train1_accessed = False
    train2_accessed = False
    stage = "pre_data_validation"
    try:
        bundle, pairs, fidelity, _ = gdnr._validate_frozen_context()
        source = verify_pinned_upstream_checkout_v1(Path(args.upstream_root))
        if source.to_dict() != fidelity.get("source_verification"):
            raise PyGSoftmaxCompatibilityError("pinned upstream source receipt changed")
        authorize_gdn_data_request_v1(
            process_id="P1",
            split_role=NORMAL_CANDIDATE_FIT,
            relative_files=ALLOWED_VALUE_FILES,
            requested_feature_names=tuple(bundle.universe_policy.source_variables)
            + tuple(bundle.universe_policy.target_variables),
            prohibited_inputs=(),
        )
        stage = "authorized_header_validation"
        feature_order = derive_frozen_p1_feature_order_from_headers_v1(
            data_root=roots.hai_data_root
        )
        feature_count = len(feature_order)
        authorize_gdn_data_request_v1(
            process_id="P1",
            split_role=NORMAL_CANDIDATE_FIT,
            relative_files=ALLOWED_VALUE_FILES,
            requested_feature_names=feature_order,
            prohibited_inputs=(),
        )
        train1_accessed = True
        train2_accessed = True
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
                    seeds_attempted=attempted,
                    seeds_completed=completed,
                    ledger_hashes=ledger_hashes,
                ),
            )
            print(f"TASK-039C-GDNC seed {seed} started", flush=True)
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
                roots, f"TASK-039C_GDNC_SEED_{seed}_PRIVATE_LEDGER.json"
            )
            if ledger_path.exists():
                raise PyGSoftmaxCompatibilityError("final seed ledger already exists")
            _write_json(ledger_path, private_ledger)
            seed_records.append(projected)
            completed.append(seed)
            ledger_hashes.append(
                {"seed": seed, "ledger_hash": private_ledger["artifact_hash"]}
            )
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
                    seeds_attempted=attempted,
                    seeds_completed=completed,
                    ledger_hashes=ledger_hashes,
                ),
            )
            print(f"TASK-039C-GDNC seed {seed} completed", flush=True)
        stage = "aggregate_frozen_ranking"
        ranking = aggregate_and_rank_gdn_candidates_v1(
            universe_pairs=pairs,
            seed_records=seed_records,
        )
        result = _build_passing_result(
            execution_commit=args.execution_commit,
            compatibility_receipt_hash=compatibility["artifact_hash"],
            environment=environment,
            ranking=ranking,
            seed_records=seed_records,
            ledger_hashes=ledger_hashes,
            created_at=created_at,
        )
        outcome = _self_hashed(
            {
                "schema_version": "1.0.0",
                "artifact_type": "task039c_gdnc_private_outcome_v1",
                "task_id": TASK_ID,
                "status": result["status"],
                "result": result,
                "seeds_attempted": attempted,
                "seeds_completed": completed,
                "private_seed_ledger_hashes": ledger_hashes,
                "feature_count": feature_count,
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
                seeds_attempted=attempted,
                seeds_completed=completed,
                ledger_hashes=ledger_hashes,
            ),
        )
    except Exception as exc:
        failure = _self_hashed(
            {
                "schema_version": "1.0.0",
                "artifact_type": "task039c_gdnc_private_failure_v1",
                "task_id": TASK_ID,
                "status": "failed_gdn_final_attempt",
                "failure_stage": stage,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "train1_accessed": train1_accessed,
                "train2_accessed": train2_accessed,
                "feature_count": feature_count,
                "seeds_attempted": attempted,
                "seeds_completed": completed,
                "private_seed_ledger_hashes": ledger_hashes,
                "seed_retry_count": 0,
                "created_at": created_at,
            }
        )
        _write_json(_private_path(roots, PRIVATE_FAILURE), failure)
        _write_state(
            roots,
            _execution_state(
                status="failed_gdn_final_attempt",
                execution_commit=args.execution_commit,
                created_at=created_at,
                train1_accessed=train1_accessed,
                train2_accessed=train2_accessed,
                feature_count=feature_count,
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
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    compatibility, scientific_hashes = _validate_commit_a(execution_commit)
    _, environment = _validate_exact_environment()
    state_path = _private_path(roots, PRIVATE_EXECUTION_STATE)
    state = _load_json(state_path) if state_path.exists() else {}
    if state:
        verify_self_hash_v1(state)
    existing_result = _load_json(RESULT_OUTPUT)
    verify_self_hash_v1(existing_result)
    failure_stage: str | None = None
    failure_type: str | None = None
    if worker_returncode == 0:
        outcome = _load_json(_private_path(roots, PRIVATE_OUTCOME))
        verify_self_hash_v1(outcome)
        if outcome.get("status") != "passed_task039c_gdn_candidate_discovery":
            raise PyGSoftmaxCompatibilityError("successful worker lacks passing outcome")
        result = dict(outcome["result"])
        verify_self_hash_v1(result)
        attempted = tuple(outcome["seeds_attempted"])
        completed = tuple(outcome["seeds_completed"])
        ledger_hashes = tuple(outcome["private_seed_ledger_hashes"])
        feature_count = int(outcome["feature_count"])
        train1 = bool(outcome["train1_accessed"])
        train2 = bool(outcome["train2_accessed"])
        status = "passed_task039c_gdn_candidate_discovery"
    else:
        failure_path = _private_path(roots, PRIVATE_FAILURE)
        failure = _load_json(failure_path) if failure_path.exists() else {}
        if failure:
            verify_self_hash_v1(failure)
        attempted = tuple(int(value) for value in state.get("seeds_attempted", ()))
        completed = tuple(int(value) for value in state.get("seeds_completed", ()))
        ledger_hashes = tuple(state.get("private_seed_ledger_hashes", ()))
        feature_count = int(state.get("feature_count", 0))
        train1 = bool(state.get("train1_accessed", False))
        train2 = bool(state.get("train2_accessed", False))
        failure_stage = str(failure.get("failure_stage", state.get("status", "worker")))
        failure_type = str(failure.get("error_type", "WorkerProcessError"))
        status = "failed_gdn_final_attempt"
        result = existing_result
    access = _build_access_audit(
        status=status,
        compatibility_receipt_hash=compatibility["artifact_hash"],
        train1_accessed=train1,
        train2_accessed=train2,
        feature_count=feature_count,
        created_at=created_at,
    )
    execution = _build_execution_receipt(
        status=status,
        execution_commit=execution_commit,
        compatibility_receipt_hash=compatibility["artifact_hash"],
        scientific_hashes=scientific_hashes,
        access=access,
        result=result,
        seeds_attempted=attempted,
        seeds_completed=completed,
        ledger_hashes=ledger_hashes,
        failure_stage=failure_stage,
        failure_type=failure_type,
        created_at=created_at,
    )
    report = _build_report(
        status=status,
        compatibility=compatibility,
        access=access,
        execution=execution,
        result=result,
    )
    return access, execution, result, report


def _record_environment_mismatch(
    *,
    execution_commit: str,
    created_at: str,
) -> None:
    compatibility, scientific_hashes = _validate_commit_a(execution_commit)
    existing_result = _load_json(RESULT_OUTPUT)
    verify_self_hash_v1(existing_result)
    status = "blocked_gdnc_environment_identity_mismatch"
    access = _build_access_audit(
        status=status,
        compatibility_receipt_hash=compatibility["artifact_hash"],
        train1_accessed=False,
        train2_accessed=False,
        feature_count=0,
        created_at=created_at,
    )
    execution = _build_execution_receipt(
        status=status,
        execution_commit=execution_commit,
        compatibility_receipt_hash=compatibility["artifact_hash"],
        scientific_hashes=scientific_hashes,
        access=access,
        result=existing_result,
        seeds_attempted=(),
        seeds_completed=(),
        ledger_hashes=(),
        failure_stage="environment_revalidation",
        failure_type="ExactGDNEnvironmentUnavailable",
        created_at=created_at,
    )
    report = _build_report(
        status=status,
        compatibility=compatibility,
        access=access,
        execution=execution,
        result=existing_result,
    )
    _write_public(ACCESS_OUTPUT, access)
    _write_public(EXECUTION_OUTPUT, execution)
    REPORT_OUTPUT.write_text(report, encoding="utf-8")


def execute(args: argparse.Namespace) -> None:
    created_at = _created_at(args.created_at)
    _validate_commit_a(args.execution_commit)
    try:
        roots, _ = _validate_exact_environment()
    except ExactGDNEnvironmentUnavailable:
        _record_environment_mismatch(
            execution_commit=args.execution_commit,
            created_at=created_at,
        )
        print(canonical_json_v1({"status": "blocked_gdnc_environment_identity_mismatch"}))
        raise SystemExit(2)
    marker_path = _private_path(roots, PRIVATE_ATTEMPT_MARKER)
    if marker_path.exists():
        raise PyGSoftmaxCompatibilityError("a second GDNC execution attempt is prohibited")
    marker = _self_hashed(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039c_gdnc_final_attempt_marker_v1",
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
        _write_public(RESULT_OUTPUT, result)
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(
        canonical_json_v1(
            {
                "status": execution["status"],
                "compatibility_receipt_hash": execution["compatibility_receipt_hash"],
                "execution_receipt_hash": execution["artifact_hash"],
                "gdn_result_artifact_hash": result["artifact_hash"],
            }
        )
    )
    if execution["status"] != "passed_task039c_gdn_candidate_discovery":
        raise SystemExit(2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    receipt = subparsers.add_parser("build-compatibility-receipt")
    receipt.add_argument("--upstream-root", required=True)
    receipt.add_argument("--created-at")
    receipt.set_defaults(handler=build_compatibility_receipt)
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
    except SystemExit:
        raise
    except Exception as exc:
        print(
            canonical_json_v1(
                {
                    "status": "failed_gdn_final_attempt",
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
            ),
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
