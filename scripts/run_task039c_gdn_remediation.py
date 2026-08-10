#!/usr/bin/env python3
"""Build receipts and execute the single bounded TASK-039C-GDNR attempt."""

from __future__ import annotations

import argparse
import hashlib
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
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from paperworks.candidates.gdn_candidate_discovery_v1 import (  # noqa: E402
    GDNCandidateResultV1,
    GDNSeedGraphRecordV1,
    aggregate_and_rank_gdn_candidates_v1,
    project_seed_record_to_universe_v1,
)
from paperworks.gdn.gdn_remediation_environment_v1 import (  # noqa: E402
    ALLOWED_VALUE_FILES,
    BLOCKED_GDN_COMMIT,
    CANDIDATE_FEATURE_ORDER_HASH,
    CANDIDATE_LEARNING_VIEW_ID,
    DETERMINISTIC_ENVIRONMENT,
    ExactGDNEnvironmentUnavailable,
    ExternalRemediationRootsV1,
    FIDELITY_RECEIPT_HASH,
    GDNRDataBoundaryError,
    GDNRRemediationError,
    GDNRResultContractError,
    GDNRSourceChangeError,
    GDNRTrainingError,
    PHASE_A_COMMIT,
    REMEDIATION_BRANCH,
    REQUIRED_TOP_LEVEL_PACKAGES,
    REVIEW_COMMIT,
    SOURCE_IDENTITY_HASH,
    TARGET_IDENTITY_HASH,
    assert_public_payload_sanitized_v1,
    build_private_environment_receipt_v1,
    build_private_wheelhouse_receipt_v1,
    build_sanitized_wheelhouse_receipt_v1,
    derive_frozen_p1_feature_order_from_headers_v1,
    enrich_passing_gdn_result_v1,
    inspect_wheelhouse_v1,
    load_verified_private_environment_receipt_v1,
    verify_exact_current_environment_v1,
    verify_self_hash_v1,
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
from paperworks.v6.candidate_discovery_protocol_v1 import (  # noqa: E402
    CandidateDiscoveryProtocolBundleV1,
)
from paperworks.v6.common import canonical_json_v1, stable_hash_v1  # noqa: E402


C0_BUNDLE = ROOT / "docs/task_reports/TASK-039C0_PROTOCOL_BUNDLE.json"
FIDELITY_RECEIPT = ROOT / "docs/task_reports/TASK-039C_GDN_FIDELITY.json"
GDN_CONFIG = ROOT / "configs/v6/task039c_gdn_backend_v1.json"
CANDIDATE_VIEW = ROOT / "docs/task_reports/TASK-039BR2_CANDIDATE_LEARNING_VIEW_V2.json"
ENVIRONMENT_OUTPUT = ROOT / "docs/task_reports/TASK-039C_GDNR_ENVIRONMENT_RECEIPT.json"
ACCESS_OUTPUT = ROOT / "docs/task_reports/TASK-039C_GDNR_DATA_ACCESS_AUDIT.json"
EXECUTION_OUTPUT = ROOT / "docs/task_reports/TASK-039C_GDNR_EXECUTION_RECEIPT.json"
RESULT_OUTPUT = ROOT / "docs/task_reports/TASK-039C_GDN_RESULT.json"
REPORT_OUTPUT = ROOT / "docs/task_reports/TASK-039C_GDNR_REPORT.md"

PRIVATE_WHEELHOUSE_RECEIPT = "TASK-039C_GDNR_WHEELHOUSE_PRIVATE_RECEIPT.json"
PRIVATE_ENVIRONMENT_RECEIPT = "TASK-039C_GDNR_ENVIRONMENT_PRIVATE_RECEIPT.json"
PRIVATE_ATTEMPT_MARKER = "TASK-039C_GDNR_EXECUTION_ATTEMPT.json"
PRIVATE_EXECUTION_STATE = "TASK-039C_GDNR_EXECUTION_STATE.json"
PRIVATE_OUTCOME = "TASK-039C_GDNR_PRIVATE_OUTCOME.json"

SCIENTIFIC_FILES = (
    "configs/v6/task039c_gdn_backend_v1.json",
    "src/paperworks/candidates/gdn_candidate_discovery_v1.py",
    "src/paperworks/gdn/upstream_candidate_backend_v1.py",
)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GDNRResultContractError(f"required JSON is unavailable: {path.name}") from exc


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
        raise GDNRSourceChangeError("Git execution-lineage verification failed")
    return result.stdout.strip() if result.returncode == 0 else ""


def _git_show_json(commit: str, relative_path: str) -> dict[str, Any]:
    text = _git("show", f"{commit}:{relative_path}")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise GDNRSourceChangeError("review authorization document is invalid") from exc


def _git_blob_sha256(commit: str, relative_path: str) -> str:
    result = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={ROOT.resolve().as_posix()}",
            "-C",
            str(ROOT),
            "show",
            f"{commit}:{relative_path}",
        ],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise GDNRSourceChangeError("canonical Git source bytes are unavailable")
    return hashlib.sha256(result.stdout).hexdigest()


def _created_at(value: str | None) -> str:
    return value or datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _validate_execution_lineage(execution_commit: str) -> None:
    if _git("branch", "--show-current") != REMEDIATION_BRANCH:
        raise GDNRSourceChangeError("remediation execution is on the wrong branch")
    if _git("rev-parse", "HEAD") != execution_commit:
        raise GDNRSourceChangeError("worktree is not at the declared Commit A")
    if _git("merge-base", "HEAD", BLOCKED_GDN_COMMIT) != BLOCKED_GDN_COMMIT:
        raise GDNRSourceChangeError("blocked GDN result is not the exact remediation base")
    if _git("rev-parse", "refs/remotes/origin/task-039c-gdn") != BLOCKED_GDN_COMMIT:
        raise GDNRSourceChangeError("remote blocked GDN branch identity changed")
    if _git("rev-parse", "refs/remotes/origin/task-039c-review") != REVIEW_COMMIT:
        raise GDNRSourceChangeError("remote independent-review identity changed")
    if _git("status", "--porcelain=v1"):
        raise GDNRSourceChangeError("execution worktree or index is not clean")
    review = _git_show_json(
        REVIEW_COMMIT, "docs/task_reports/TASK-039C_PARALLEL_REVIEW.json"
    )
    verify_self_hash_v1(review)
    if (
        review.get("status")
        != "passed_task039c_parallel_review_gdn_remediation_recommended"
        or review.get("gdn_remediation_recommendation")
        != "READY_FOR_BOUNDED_GDN_ENVIRONMENT_REMEDIATION"
        or review.get("finding_counts", {}).get("BLOCKING") != 0
    ):
        raise GDNRSourceChangeError("independent review does not authorize remediation")
    changed = _git("diff", "--name-only", BLOCKED_GDN_COMMIT, "HEAD", "--", *SCIENTIFIC_FILES)
    if changed:
        raise GDNRSourceChangeError("frozen scientific implementation changed")


def _validate_frozen_context() -> tuple[
    CandidateDiscoveryProtocolBundleV1,
    tuple[tuple[str, str], ...],
    dict[str, Any],
    dict[str, str],
]:
    bundle = CandidateDiscoveryProtocolBundleV1.from_dict(_load_json(C0_BUNDLE))
    if (
        bundle.artifact_hash != TASK039C0_PROTOCOL_BUNDLE_HASH
        or bundle.gdn_policy.artifact_hash != TASK039C0_GDN_POLICY_HASH
        or bundle.universe_policy.eligible_pair_universe_hash
        != TASK039C0_PAIR_UNIVERSE_HASH
        or bundle.universe_policy.source_identity_list_hash != SOURCE_IDENTITY_HASH
        or bundle.universe_policy.target_identity_list_hash != TARGET_IDENTITY_HASH
        or bundle.universe_policy.candidate_learning_view_id != CANDIDATE_LEARNING_VIEW_ID
        or bundle.selected_process_id != "P1"
        or len(bundle.universe_policy.source_variables) != 12
        or len(bundle.universe_policy.target_variables) != 12
        or bundle.universe_policy.eligible_pair_count != 144
    ):
        raise GDNRSourceChangeError("frozen C0 identity bundle changed")
    pairs = tuple(
        (source, target)
        for source in bundle.universe_policy.source_variables
        for target in bundle.universe_policy.target_variables
    )
    if len(pairs) != 144 or len(set(pairs)) != 144:
        raise GDNRSourceChangeError("frozen pair universe cannot be reconstructed")
    fidelity = _load_json(FIDELITY_RECEIPT)
    if (
        verify_self_hash_v1(fidelity) != FIDELITY_RECEIPT_HASH
        or fidelity.get("status") != "passed_upstream_gdn_fidelity"
        or fidelity.get("backend_classification") != "upstream_aligned_validated"
        or fidelity.get("smoke_backend_used") is not False
        or fidelity.get("real_hai_feature_values_accessed") is not False
    ):
        raise GDNRSourceChangeError("frozen fidelity receipt changed")
    if fidelity.get("implementation_sha256") != _git_blob_sha256(
        BLOCKED_GDN_COMMIT,
        "src/paperworks/gdn/upstream_candidate_backend_v1.py",
    ):
        raise GDNRSourceChangeError("fidelity implementation binding changed")
    view = _load_json(CANDIDATE_VIEW)
    if (
        verify_self_hash_v1(view) != CANDIDATE_LEARNING_VIEW_ID
        or view.get("feature_order_hash") != CANDIDATE_FEATURE_ORDER_HASH
        or view.get("process_scope") != ["P1"]
        or view.get("view_kind") != "candidate_learning"
    ):
        raise GDNRSourceChangeError("frozen P1 candidate-learning view changed")
    config = _load_json(GDN_CONFIG)
    config_hash = str(config.pop("config_hash", ""))
    if stable_hash_v1(config) != config_hash:
        raise GDNRSourceChangeError("frozen GDN config self-hash changed")
    scientific_hashes = {
        relative: _git_blob_sha256("HEAD", relative) for relative in SCIENTIFIC_FILES
    }
    return bundle, pairs, fidelity, scientific_hashes


def _validate_external_roots(*, require_existing: bool = True) -> ExternalRemediationRootsV1:
    return ExternalRemediationRootsV1.from_environment(
        repository_root=ROOT,
        require_existing=require_existing,
    )


def _private_path(roots: ExternalRemediationRootsV1, name: str) -> Path:
    path = (roots.private_root / name).resolve()
    if not path.is_relative_to(roots.private_root):
        raise GDNRResultContractError("private output path escaped its root")
    return path


def verify_wheelhouse(args: argparse.Namespace) -> None:
    _validate_execution_lineage(args.execution_commit)
    _validate_frozen_context()
    roots = _validate_external_roots()
    records = inspect_wheelhouse_v1(roots.wheelhouse_root)
    public = build_sanitized_wheelhouse_receipt_v1(
        records, created_at=_created_at(args.created_at)
    )
    private = build_private_wheelhouse_receipt_v1(
        public_receipt=public,
        wheelhouse_root=roots.wheelhouse_root,
    )
    output = _private_path(roots, PRIVATE_WHEELHOUSE_RECEIPT)
    if output.exists():
        raise ExactGDNEnvironmentUnavailable("wheelhouse was already verified once")
    _write_json(output, private)
    print(
        canonical_json_v1(
            {
                "status": public["status"],
                "wheel_count": public["wheel_count"],
                "wheelhouse_receipt_hash": public["artifact_hash"],
            }
        )
    )


def _load_private_wheelhouse_receipt(
    roots: ExternalRemediationRootsV1,
) -> dict[str, Any]:
    document = _load_json(_private_path(roots, PRIVATE_WHEELHOUSE_RECEIPT))
    verify_self_hash_v1(document)
    if document.get("wheelhouse_root") != str(roots.wheelhouse_root):
        raise ExactGDNEnvironmentUnavailable("private wheelhouse root changed")
    public = document.get("public_receipt")
    if not isinstance(public, Mapping):
        raise ExactGDNEnvironmentUnavailable("sanitized wheelhouse receipt is absent")
    verify_self_hash_v1(public)
    assert_public_payload_sanitized_v1(public)
    return document


def verify_environment(args: argparse.Namespace) -> None:
    _validate_execution_lineage(args.execution_commit)
    _validate_frozen_context()
    roots = _validate_external_roots()
    if not Path(sys.executable).resolve().is_relative_to(roots.environment_root):
        raise ExactGDNEnvironmentUnavailable("verification is not running inside the new environment")
    wheelhouse = _load_private_wheelhouse_receipt(roots)
    receipt, installed, freeze_lines = verify_exact_current_environment_v1(
        public_wheelhouse_receipt=wheelhouse["public_receipt"],
        fidelity_receipt_hash=FIDELITY_RECEIPT_HASH,
        created_at=_created_at(args.created_at),
    )
    public = receipt.to_dict()
    private = build_private_environment_receipt_v1(
        public_receipt=public,
        roots=roots,
        installed_packages=installed,
        freeze_lines=freeze_lines,
    )
    output = _private_path(roots, PRIVATE_ENVIRONMENT_RECEIPT)
    if output.exists():
        raise ExactGDNEnvironmentUnavailable("exact environment was already verified once")
    _write_json(output, private)
    print(
        canonical_json_v1(
            {
                "status": public["status"],
                "environment_receipt_hash": public["artifact_hash"],
                "dependency_environment_fingerprint": public[
                    "dependency_environment_fingerprint"
                ],
            }
        )
    )


def record_environment_block(args: argparse.Namespace) -> None:
    """Record the one terminal environment block without HAI access."""

    if re.fullmatch(r"[A-Za-z0-9_.:-]+", args.reason_code) is None:
        raise GDNRResultContractError("environment block reason code is not sanitized")
    _validate_execution_lineage(args.execution_commit)
    _, _, _, scientific_hashes = _validate_frozen_context()
    roots = _validate_external_roots(require_existing=False)
    roots.private_root.mkdir(parents=True, exist_ok=True)
    marker_path = _private_path(roots, PRIVATE_ATTEMPT_MARKER)
    if marker_path.exists():
        raise GDNRResultContractError("a second remediation attempt is prohibited")
    created_at = _created_at(args.created_at)
    marker = _self_hashed(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039c_gdnr_single_attempt_marker_v1",
            "task_id": "TASK-039C-GDNR",
            "execution_commit": args.execution_commit,
            "created_at": created_at,
            "single_attempt_authority_consumed": True,
            "terminal_status": args.status,
        }
    )
    _write_json(marker_path, marker)
    empty_manifest_hash = stable_hash_v1(
        {"artifact_type": "task039c_gdn_wheel_manifest_v1", "wheels": []}
    )
    unavailable_hash = stable_hash_v1(
        {
            "artifact_type": "task039c_gdn_unavailable_environment_marker_v1",
            "status": args.status,
            "reason_code": args.reason_code,
        }
    )
    environment_content = {
        "schema_version": "1.0.0",
        "artifact_type": "task039c_gdn_environment_receipt_v1",
        "task_id": "TASK-039C-GDNR",
        "status": args.status,
        "python_version": platform.python_version(),
        "platform_id": f"{platform.system().lower()}-{platform.machine().lower()}",
        "top_level_packages": dict(REQUIRED_TOP_LEVEL_PACKAGES),
        "wheel_count": 0,
        "wheel_manifest": [],
        "sanitized_wheel_manifest_hash": empty_manifest_hash,
        "wheelhouse_receipt_hash": unavailable_hash,
        "installed_package_freeze_hash": unavailable_hash,
        "installed_package_count": 0,
        "pip_version": "unverified",
        "pip_check_status": "not_run",
        "dependency_environment_fingerprint": unavailable_hash,
        "fidelity_receipt_hash": FIDELITY_RECEIPT_HASH,
        "torch_runtime_version": "unavailable",
        "cpu_execution_available": False,
        "gpu_or_cuda_required": False,
        "unapproved_pyg_extensions_installed": False,
        "wheelhouse_installed_distribution_match": False,
        "deterministic_environment": dict(DETERMINISTIC_ENVIRONMENT),
        "environment_exact_match": False,
        "environment_root_disclosed": False,
        "blocking_reason": args.reason_code,
        "created_at": created_at,
    }
    environment = _self_hashed(environment_content)
    access = _build_access_audit(
        status=args.status,
        environment_receipt_hash=environment["artifact_hash"],
        train1_accessed=False,
        train2_accessed=False,
        feature_count=0,
        created_at=created_at,
    )
    existing_result = _load_json(RESULT_OUTPUT)
    verify_self_hash_v1(existing_result)
    execution = _build_execution_receipt(
        status=args.status,
        execution_commit=args.execution_commit,
        environment=environment,
        scientific_hashes=scientific_hashes,
        access_audit=access,
        result=existing_result,
        seeds_attempted=(),
        seeds_completed=(),
        private_seed_ledger_hashes=(),
        created_at=created_at,
    )
    report = _build_report(
        status=args.status,
        environment=environment,
        result=existing_result,
        access=access,
        execution=execution,
        blocking_reason="the exact approved environment could not be established",
    )
    _write_public(ENVIRONMENT_OUTPUT, environment)
    _write_public(ACCESS_OUTPUT, access)
    _write_public(EXECUTION_OUTPUT, execution)
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(
        canonical_json_v1(
            {
                "status": args.status,
                "environment_receipt_hash": environment["artifact_hash"],
                "existing_blocked_gdn_result_preserved": True,
            }
        )
    )


def _load_and_reverify_environment(
    roots: ExternalRemediationRootsV1,
) -> tuple[dict[str, Any], dict[str, Any]]:
    private = load_verified_private_environment_receipt_v1(
        _private_path(roots, PRIVATE_ENVIRONMENT_RECEIPT), roots=roots
    )
    wheelhouse = _load_private_wheelhouse_receipt(roots)
    stored = private["public_receipt"]
    observed, _, _ = verify_exact_current_environment_v1(
        public_wheelhouse_receipt=wheelhouse["public_receipt"],
        fidelity_receipt_hash=FIDELITY_RECEIPT_HASH,
        created_at=str(stored["created_at"]),
    )
    if observed.to_dict() != stored:
        raise ExactGDNEnvironmentUnavailable("exact environment changed after verification")
    return private, wheelhouse


def _execution_state(
    *,
    status: str,
    execution_commit: str,
    created_at: str,
    train1_accessed: bool,
    train2_accessed: bool,
    seeds_attempted: Sequence[int],
    seeds_completed: Sequence[int],
    private_seed_ledger_hashes: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return _self_hashed(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039c_gdn_private_execution_state_v1",
            "task_id": "TASK-039C-GDNR",
            "status": status,
            "execution_commit": execution_commit,
            "created_at": created_at,
            "train1_accessed": train1_accessed,
            "train2_accessed": train2_accessed,
            "seeds_attempted": list(seeds_attempted),
            "seeds_completed": list(seeds_completed),
            "private_seed_ledger_hashes": [
                dict(item) for item in private_seed_ledger_hashes
            ],
        }
    )


def _write_execution_state(
    roots: ExternalRemediationRootsV1, document: Mapping[str, Any]
) -> None:
    _write_json(_private_path(roots, PRIVATE_EXECUTION_STATE), document)


def _private_seed_ledger(
    record: GDNSeedGraphRecordV1,
) -> dict[str, Any]:
    pairs = tuple(sorted(record.candidate_similarities))
    return _self_hashed(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039c_gdn_private_seed_ledger_v1",
            "task_id": "TASK-039C-GDNR",
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
    environment_receipt_hash: str,
    train1_accessed: bool,
    train2_accessed: bool,
    feature_count: int,
    created_at: str,
) -> dict[str, Any]:
    content = {
        "schema_version": "1.0.0",
        "artifact_type": "task039c_gdnr_data_access_audit_v1",
        "task_id": "TASK-039C-GDNR",
        "status": status,
        "environment_receipt_hash": environment_receipt_hash,
        "process_id": "P1",
        "split_role": NORMAL_CANDIDATE_FIT,
        "candidate_learning_view_id": CANDIDATE_LEARNING_VIEW_ID,
        "candidate_feature_order_hash": CANDIDATE_FEATURE_ORDER_HASH,
        "feature_count": feature_count,
        "authorized_files": list(ALLOWED_VALUE_FILES),
        "files_accessed": [
            relative
            for relative, accessed in zip(
                ALLOWED_VALUE_FILES, (train1_accessed, train2_accessed), strict=True
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
        "raw_values_persisted": False,
        "raw_windows_persisted": False,
        "node_embeddings_persisted": False,
        "checkpoint_persisted": False,
        "private_seed_ledgers_outside_git": True,
        "created_at": created_at,
    }
    assert_public_payload_sanitized_v1(content)
    return _self_hashed(content)


def _build_execution_receipt(
    *,
    status: str,
    execution_commit: str,
    environment: Mapping[str, Any],
    scientific_hashes: Mapping[str, str],
    access_audit: Mapping[str, Any],
    result: Mapping[str, Any],
    seeds_attempted: Sequence[int],
    seeds_completed: Sequence[int],
    private_seed_ledger_hashes: Sequence[Mapping[str, Any]],
    created_at: str,
) -> dict[str, Any]:
    content: dict[str, Any] = {
        "schema_version": "1.0.0",
        "artifact_type": "task039c_gdnr_execution_receipt_v1",
        "task_id": "TASK-039C-GDNR",
        "status": status,
        "blocked_gdn_base_commit": BLOCKED_GDN_COMMIT,
        "phase_a_commit": PHASE_A_COMMIT,
        "remediation_execution_commit": execution_commit,
        "protocol_bundle_hash": TASK039C0_PROTOCOL_BUNDLE_HASH,
        "gdn_policy_hash": TASK039C0_GDN_POLICY_HASH,
        "pair_universe_hash": TASK039C0_PAIR_UNIVERSE_HASH,
        "source_identity_hash": SOURCE_IDENTITY_HASH,
        "target_identity_hash": TARGET_IDENTITY_HASH,
        "fidelity_receipt_hash": FIDELITY_RECEIPT_HASH,
        "environment_receipt_hash": environment["artifact_hash"],
        "dependency_environment_fingerprint": environment[
            "dependency_environment_fingerprint"
        ],
        "wheelhouse_receipt_hash": environment["wheelhouse_receipt_hash"],
        "scientific_source_hashes": dict(scientific_hashes),
        "execution_commit_clean_at_start": True,
        "scientific_source_change_after_execution_start": False,
        "seeds_attempted": list(seeds_attempted),
        "seeds_completed": list(seeds_completed),
        "private_seed_ledger_hashes": [
            dict(item) for item in private_seed_ledger_hashes
        ],
        "evaluated_candidate_count": int(result.get("evaluated_candidate_count", 0)),
        "supported_candidate_count": int(result.get("supported_candidate_count", 0)),
        "ranking_hash": result.get("ranking_hash"),
        "data_access_audit_hash": access_audit["artifact_hash"],
        "result_artifact_hash": result["artifact_hash"],
        "attention_used_for_primary_ranking": False,
        "posthoc_xai_used": False,
        "br2_pair_supervision_used": False,
        "meta_output_used": False,
        "stat_output_used": False,
        "checkpoint_persisted": False,
        "created_at": created_at,
    }
    assert_public_payload_sanitized_v1(content)
    return _self_hashed(content)


def _build_report(
    *,
    status: str,
    environment: Mapping[str, Any],
    result: Mapping[str, Any],
    access: Mapping[str, Any],
    execution: Mapping[str, Any],
    blocking_reason: str | None = None,
) -> str:
    lines = [
        "# TASK-039C-GDNR Exact Environment Remediation and GDN Execution",
        "",
        f"Status: `{status}`",
        "",
        "The only authorized dependency-remediation attempt used CPython 3.12.13 on Windows AMD64 with exact `torch==2.12.1`, `torch-geometric==2.8.0`, and `jsonschema[format-nongpl]==4.26.0`. Wheels were acquired as binaries, rehashed, and installed offline into an external environment.",
        "",
    ]
    if status == "passed_task039c_gdn_candidate_discovery":
        lines.extend(
            [
                "The frozen upstream-aligned backend completed seeds 11, 23, and 37 sequentially on CPU. The result projects learned graph evidence onto the exact 144-pair P1 universe and applies one unpadded deterministic ranking.",
                "",
                f"Supported candidates: `{result['supported_candidate_count']}`. Top-10/20/40 counts: `{len(result['top10'])}/{len(result['top20'])}/{len(result['top40'])}`.",
                f"Ranking hash: `{result['ranking_hash']}`.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                f"The run failed closed: {blocking_reason or 'the frozen execution did not complete'}. No ranking or top-K result was produced.",
                "",
            ]
        )
    lines.extend(
        [
            "Only train1 and train2 in the frozen P1 candidate-learning view were authorized. Train3, train4, test, labels, attacks, BR2 pair supervision, META output, and STAT output were not used. No checkpoint, raw row, raw window, or node embedding was persisted publicly or privately.",
            "",
            f"Environment receipt hash: `{environment['artifact_hash']}`.",
            f"Wheelhouse receipt hash: `{environment['wheelhouse_receipt_hash']}`.",
            f"Fidelity receipt hash: `{FIDELITY_RECEIPT_HASH}`.",
            f"Data-access audit hash: `{access['artifact_hash']}`.",
            f"Execution receipt hash: `{execution['artifact_hash']}`.",
            "",
            "This is graph candidate evidence only. It does not establish causality, a confirmed relation, rule validity, anomaly performance, or GDN superiority. TASK-039D remains unauthorized.",
            "",
        ]
    )
    report = "\n".join(lines)
    assert_public_payload_sanitized_v1(report)
    return report


def _build_failure_result(
    *,
    status: str,
    execution_commit: str,
    environment: Mapping[str, Any],
    train1_accessed: bool,
    train2_accessed: bool,
    seeds_attempted: Sequence[int],
    seeds_completed: Sequence[int],
    created_at: str,
) -> dict[str, Any]:
    content = {
        "schema_version": "1.0.0",
        "artifact_type": "gdn_candidate_result_v1",
        "task_id": "TASK-039C-GDN",
        "arm_id": "GDN",
        "status": status,
        "phase_a_commit": PHASE_A_COMMIT,
        "protocol_bundle_hash": TASK039C0_PROTOCOL_BUNDLE_HASH,
        "gdn_policy_hash": TASK039C0_GDN_POLICY_HASH,
        "pair_universe_hash": TASK039C0_PAIR_UNIVERSE_HASH,
        "source_identity_hash": SOURCE_IDENTITY_HASH,
        "target_identity_hash": TARGET_IDENTITY_HASH,
        "candidate_learning_view_id": CANDIDATE_LEARNING_VIEW_ID,
        "upstream_commit": UPSTREAM_GDN_COMMIT,
        "fidelity_receipt_hash": FIDELITY_RECEIPT_HASH,
        "environment_receipt_hash": environment["artifact_hash"],
        "dependency_environment_fingerprint": environment[
            "dependency_environment_fingerprint"
        ],
        "remediation_execution_commit": execution_commit,
        "backend_classification": "upstream_aligned_validated",
        "source_count": 12,
        "target_count": 12,
        "real_hai_feature_access": train1_accessed or train2_accessed,
        "seeds_attempted": list(seeds_attempted),
        "seeds_completed": list(seeds_completed),
        "br2_pair_supervision_used": False,
        "train1_accessed": train1_accessed,
        "train2_accessed": train2_accessed,
        "train3_accessed": False,
        "train4_accessed": False,
        "test_accessed": False,
        "labels_accessed": False,
        "attacks_accessed": False,
        "meta_output_used": False,
        "stat_output_used": False,
        "attention_used_for_primary_ranking": False,
        "posthoc_xai_used": False,
        "failure_reason": "frozen execution failed closed; no ranking was produced",
        "created_at": created_at,
    }
    assert_public_payload_sanitized_v1(content)
    return _self_hashed(content)


def worker(args: argparse.Namespace) -> None:
    roots = _validate_external_roots()
    created_at = _created_at(args.created_at)
    attempted: list[int] = []
    completed: list[int] = []
    ledger_hashes: list[dict[str, Any]] = []
    train1_accessed = False
    train2_accessed = False
    feature_count = 0
    try:
        _validate_execution_lineage(args.execution_commit)
        bundle, pairs, fidelity, scientific_hashes = _validate_frozen_context()
        environment_private, _ = _load_and_reverify_environment(roots)
        environment = environment_private["public_receipt"]
        source = verify_pinned_upstream_checkout_v1(Path(args.upstream_root))
        if source.to_dict() != fidelity.get("source_verification"):
            raise GDNRSourceChangeError("pinned upstream source receipt changed")
        authorize_gdn_data_request_v1(
            process_id="P1",
            split_role=NORMAL_CANDIDATE_FIT,
            relative_files=ALLOWED_VALUE_FILES,
            requested_feature_names=tuple(bundle.universe_policy.source_variables)
            + tuple(bundle.universe_policy.target_variables),
            prohibited_inputs=(),
        )
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
        _write_execution_state(
            roots,
            _execution_state(
                status="loading_authorized_train1_train2",
                execution_commit=args.execution_commit,
                created_at=created_at,
                train1_accessed=train1_accessed,
                train2_accessed=train2_accessed,
                seeds_attempted=attempted,
                seeds_completed=completed,
                private_seed_ledger_hashes=ledger_hashes,
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
            attempted.append(seed)
            _write_execution_state(
                roots,
                _execution_state(
                    status=f"training_seed_{seed}",
                    execution_commit=args.execution_commit,
                    created_at=created_at,
                    train1_accessed=True,
                    train2_accessed=True,
                    seeds_attempted=attempted,
                    seeds_completed=completed,
                    private_seed_ledger_hashes=ledger_hashes,
                ),
            )
            print(f"TASK-039C-GDNR seed {seed} started", flush=True)
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
                roots, f"TASK-039C_GDNR_SEED_{seed}_PRIVATE_LEDGER.json"
            )
            if ledger_path.exists():
                raise GDNRTrainingError("private seed ledger already exists")
            _write_json(ledger_path, private_ledger)
            seed_records.append(projected)
            completed.append(seed)
            ledger_hashes.append(
                {"seed": seed, "ledger_hash": private_ledger["artifact_hash"]}
            )
            os.environ["PYTHONHASHSEED"] = DETERMINISTIC_ENVIRONMENT["PYTHONHASHSEED"]
            _write_execution_state(
                roots,
                _execution_state(
                    status=f"completed_seed_{seed}",
                    execution_commit=args.execution_commit,
                    created_at=created_at,
                    train1_accessed=True,
                    train2_accessed=True,
                    seeds_attempted=attempted,
                    seeds_completed=completed,
                    private_seed_ledger_hashes=ledger_hashes,
                ),
            )
            print(f"TASK-039C-GDNR seed {seed} completed", flush=True)
        ranking = aggregate_and_rank_gdn_candidates_v1(
            universe_pairs=pairs,
            seed_records=seed_records,
        )
        base = GDNCandidateResultV1(
            status="passed_task039c_gdn_candidate_discovery",
            phase_a_commit=PHASE_A_COMMIT,
            fidelity_receipt_hash=FIDELITY_RECEIPT_HASH,
            dependency_environment_fingerprint=environment[
                "dependency_environment_fingerprint"
            ],
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
            ranking=ranking,
            seed_records=tuple(seed_records),
        )
        result = enrich_passing_gdn_result_v1(
            base_result=base.to_dict(),
            environment_receipt_hash=environment["artifact_hash"],
            remediation_execution_commit=args.execution_commit,
            private_seed_ledger_hashes=ledger_hashes,
            data_access_audit_ref=ACCESS_OUTPUT.name,
        )
        access = _build_access_audit(
            status=str(result["status"]),
            environment_receipt_hash=environment["artifact_hash"],
            train1_accessed=True,
            train2_accessed=True,
            feature_count=feature_count,
            created_at=created_at,
        )
        execution = _build_execution_receipt(
            status=str(result["status"]),
            execution_commit=args.execution_commit,
            environment=environment,
            scientific_hashes=scientific_hashes,
            access_audit=access,
            result=result,
            seeds_attempted=attempted,
            seeds_completed=completed,
            private_seed_ledger_hashes=ledger_hashes,
            created_at=created_at,
        )
        report = _build_report(
            status=str(result["status"]),
            environment=environment,
            result=result,
            access=access,
            execution=execution,
        )
        outcome = _self_hashed(
            {
                "schema_version": "1.0.0",
                "artifact_type": "task039c_gdnr_private_outcome_v1",
                "task_id": "TASK-039C-GDNR",
                "status": result["status"],
                "environment": environment,
                "access": access,
                "execution": execution,
                "result": result,
                "report": report,
            }
        )
        _write_json(_private_path(roots, PRIVATE_OUTCOME), outcome)
        _write_execution_state(
            roots,
            _execution_state(
                status="passed_task039c_gdn_candidate_discovery",
                execution_commit=args.execution_commit,
                created_at=created_at,
                train1_accessed=True,
                train2_accessed=True,
                seeds_attempted=attempted,
                seeds_completed=completed,
                private_seed_ledger_hashes=ledger_hashes,
            ),
        )
    except Exception as exc:
        failure_status = (
            exc.status if isinstance(exc, GDNRRemediationError) else "failed_gdn_training"
        )
        private_failure = _self_hashed(
            {
                "schema_version": "1.0.0",
                "artifact_type": "task039c_gdnr_private_failure_v1",
                "task_id": "TASK-039C-GDNR",
                "status": failure_status,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "train1_accessed": train1_accessed,
                "train2_accessed": train2_accessed,
                "feature_count": feature_count,
                "seeds_attempted": attempted,
                "seeds_completed": completed,
                "private_seed_ledger_hashes": ledger_hashes,
                "created_at": created_at,
            }
        )
        _write_json(_private_path(roots, PRIVATE_OUTCOME), private_failure)
        _write_execution_state(
            roots,
            _execution_state(
                status=failure_status,
                execution_commit=args.execution_commit,
                created_at=created_at,
                train1_accessed=train1_accessed,
                train2_accessed=train2_accessed,
                seeds_attempted=attempted,
                seeds_completed=completed,
                private_seed_ledger_hashes=ledger_hashes,
            ),
        )
        raise


def _finalize_worker_outcome(
    *,
    roots: ExternalRemediationRootsV1,
    execution_commit: str,
    created_at: str,
    worker_returncode: int,
) -> dict[str, Any]:
    environment_private, _ = _load_and_reverify_environment(roots)
    environment = environment_private["public_receipt"]
    _, _, _, scientific_hashes = _validate_frozen_context()
    outcome_path = _private_path(roots, PRIVATE_OUTCOME)
    state_path = _private_path(roots, PRIVATE_EXECUTION_STATE)
    state = _load_json(state_path) if state_path.exists() else {}
    if state:
        verify_self_hash_v1(state)
    if worker_returncode == 0 and outcome_path.exists():
        outcome = _load_json(outcome_path)
        verify_self_hash_v1(outcome)
        if outcome.get("status") != "passed_task039c_gdn_candidate_discovery":
            raise GDNRResultContractError("successful worker lacks passing outcome")
        for field in ("environment", "access", "execution", "result"):
            verify_self_hash_v1(outcome[field])
            assert_public_payload_sanitized_v1(outcome[field])
        if outcome["environment"] != environment:
            raise GDNRResultContractError("worker environment binding changed")
        report = str(outcome["report"])
        assert_public_payload_sanitized_v1(report)
        return outcome
    attempted = tuple(int(value) for value in state.get("seeds_attempted", ()))
    completed = tuple(int(value) for value in state.get("seeds_completed", ()))
    ledger_hashes = tuple(state.get("private_seed_ledger_hashes", ()))
    train1 = bool(state.get("train1_accessed", False))
    train2 = bool(state.get("train2_accessed", False))
    feature_count = 0
    failure_status = str(state.get("status", "failed_gdn_training"))
    if failure_status not in {
        "failed_gdn_training",
        "failed_gdn_data_boundary",
        "failed_gdn_remediation_requires_scientific_change",
        "failed_gdn_result_contract",
    }:
        failure_status = "failed_gdn_training"
    result = _build_failure_result(
        status=failure_status,
        execution_commit=execution_commit,
        environment=environment,
        train1_accessed=train1,
        train2_accessed=train2,
        seeds_attempted=attempted,
        seeds_completed=completed,
        created_at=created_at,
    )
    access = _build_access_audit(
        status=failure_status,
        environment_receipt_hash=environment["artifact_hash"],
        train1_accessed=train1,
        train2_accessed=train2,
        feature_count=feature_count,
        created_at=created_at,
    )
    execution = _build_execution_receipt(
        status=failure_status,
        execution_commit=execution_commit,
        environment=environment,
        scientific_hashes=scientific_hashes,
        access_audit=access,
        result=result,
        seeds_attempted=attempted,
        seeds_completed=completed,
        private_seed_ledger_hashes=ledger_hashes,
        created_at=created_at,
    )
    report = _build_report(
        status=failure_status,
        environment=environment,
        result=result,
        access=access,
        execution=execution,
        blocking_reason="the single frozen worker did not complete all three seeds",
    )
    return _self_hashed(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039c_gdnr_private_outcome_v1",
            "task_id": "TASK-039C-GDNR",
            "status": failure_status,
            "environment": environment,
            "access": access,
            "execution": execution,
            "result": result,
            "report": report,
        }
    )


def execute(args: argparse.Namespace) -> None:
    _validate_execution_lineage(args.execution_commit)
    _validate_frozen_context()
    roots = _validate_external_roots()
    if not Path(sys.executable).resolve().is_relative_to(roots.environment_root):
        raise ExactGDNEnvironmentUnavailable("execution is not running inside the exact environment")
    _load_and_reverify_environment(roots)
    marker_path = _private_path(roots, PRIVATE_ATTEMPT_MARKER)
    if marker_path.exists():
        raise GDNRResultContractError("a second remediation execution attempt is prohibited")
    created_at = _created_at(args.created_at)
    marker = _self_hashed(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039c_gdnr_single_attempt_marker_v1",
            "task_id": "TASK-039C-GDNR",
            "execution_commit": args.execution_commit,
            "created_at": created_at,
            "single_attempt_authority_consumed": True,
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
    result = subprocess.run(command, check=False, cwd=ROOT, env=environment)
    outcome = _finalize_worker_outcome(
        roots=roots,
        execution_commit=args.execution_commit,
        created_at=created_at,
        worker_returncode=result.returncode,
    )
    _write_public(ENVIRONMENT_OUTPUT, outcome["environment"])
    _write_public(ACCESS_OUTPUT, outcome["access"])
    _write_public(EXECUTION_OUTPUT, outcome["execution"])
    _write_public(RESULT_OUTPUT, outcome["result"])
    REPORT_OUTPUT.write_text(str(outcome["report"]), encoding="utf-8")
    print(
        canonical_json_v1(
            {
                "status": outcome["status"],
                "environment_receipt_hash": outcome["environment"]["artifact_hash"],
                "result_artifact_hash": outcome["result"]["artifact_hash"],
            }
        )
    )
    if outcome["status"] != "passed_task039c_gdn_candidate_discovery":
        raise SystemExit(2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    wheelhouse = subparsers.add_parser("verify-wheelhouse")
    wheelhouse.add_argument("--execution-commit", required=True)
    wheelhouse.add_argument("--created-at")
    wheelhouse.set_defaults(handler=verify_wheelhouse)
    environment = subparsers.add_parser("verify-environment")
    environment.add_argument("--execution-commit", required=True)
    environment.add_argument("--created-at")
    environment.set_defaults(handler=verify_environment)
    blocked = subparsers.add_parser("record-environment-block")
    blocked.add_argument("--execution-commit", required=True)
    blocked.add_argument(
        "--status",
        required=True,
        choices=(
            "blocked_exact_gdn_environment_unavailable",
            "blocked_exact_gdn_environment_missing_unapproved_extension",
        ),
    )
    blocked.add_argument("--reason-code", required=True)
    blocked.add_argument("--created-at")
    blocked.set_defaults(handler=record_environment_block)
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
    except GDNRRemediationError as exc:
        print(f"{exc.status}: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
