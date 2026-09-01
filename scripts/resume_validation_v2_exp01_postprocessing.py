"""Resume frozen EXP-01 after training, using twelve recovered checkpoints."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

from paperworks.gdn.upstream_candidate_backend_v1 import UpstreamGDNTrainingConfigV1
from paperworks.validation_v2.exp01_checkpoint_v2 import recover_existing_private_checkpoint_v2
from paperworks.validation_v2.exp01_execution_v2 import (
    Exp01ExecutionError,
    Exp01ViewInputV2,
    resume_exp01_postprocessing_v2,
)
from paperworks.validation_v2.exp01_recovery_v2 import (
    INTERRUPTED_ACCESS_COUNTERS,
    ORIGIN_TRAINING_CODE_AUTHORITY_HASH,
    ORIGIN_TRAINING_SOURCE_COMMIT,
    cumulative_access_counters_v2,
    expected_checkpoint_names_v2,
    verify_interrupted_checkpoint_recovery_receipt_v2,
)
from paperworks.validation_v2.exp01_relation_confirmation_v2 import (
    fit_and_confirm_arbitrary_union_v2,
)
from paperworks.validation_v2.exp01_scientific_v1 import (
    META_RESULT_HASH,
    STAT_RESULT_HASH,
    EXPECTED_SCHEDULE,
    ViewId,
)
from paperworks.validation_v2.hai_feature_adapter_v1 import (
    HAIFeatureAccessLedgerV1,
    load_authorized_hai_feature_frame_v1,
    resolve_hai_feature_root_capability_v1,
)
from paperworks.validation_v2.protocol_v1 import (
    ProtocolExecutionGuardV1,
    ProtocolOperationV1,
    build_validation_protocol_v1,
)
from paperworks.profiling.task039d1_execution_optimization_v1 import (
    verify_recovery_artifact_v1,
)
from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER


EXPECTED_CONTRACT_CONFLICT = "EXP01_FROZEN_CONTRACT_CONFLICT_PRIMARY_MASK_2_OF_3_VS_SHARED_ALL_SEEDS"
OPTIMIZATION_AUTHORITY_HASH = "6639c6c767af749775eed8cbd98dc43ccff8cf603ee8cdd009a169b45944bef0"


def _git_head(root: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _git_worktree_is_clean(root: Path) -> bool:
    return not subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=all"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _postprocessing_code_hash(root: Path) -> str:
    digest = sha256()
    paths = (
        "src/paperworks/gdn/exp01_upstream_backend_v2.py",
        "src/paperworks/profiling/task039d1_execution_optimization_v1.py",
        "src/paperworks/validation_v2/exp01_checkpoint_v2.py",
        "src/paperworks/validation_v2/exp01_execution_v2.py",
        "src/paperworks/validation_v2/exp01_recovery_v2.py",
        "src/paperworks/validation_v2/exp01_relation_confirmation_v2.py",
        "src/paperworks/validation_v2/exp01_scientific_v1.py",
        "src/paperworks/v6/continuous_step_protocol_v1.py",
        "scripts/resume_validation_v2_exp01_postprocessing.py",
    )
    for relative in paths:
        raw = (root / relative).read_bytes()
        digest.update(relative.encode("utf-8"))
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return digest.hexdigest()


def _load_frozen_comparator_results(
    root: Path,
) -> tuple[tuple[tuple[str, str], ...], tuple[tuple[str, str], ...]]:
    meta = json.loads((root / "docs/task_reports/TASK-039C_META_RESULT.json").read_text(encoding="utf-8"))
    stat = json.loads((root / "docs/task_reports/TASK-039C_STAT_RESULT.json").read_text(encoding="utf-8"))
    for name, document, expected in (
        ("META", meta, META_RESULT_HASH),
        ("STAT", stat, STAT_RESULT_HASH),
    ):
        replayed = stable_hash_v1({key: value for key, value in document.items() if key != "artifact_hash"})
        if document.get("artifact_hash") != expected or replayed != expected:
            raise RuntimeError(f"EXP01_FROZEN_{name}_AUTHORITY_REPLAY_REJECTED")
    meta_top20 = tuple(
        (str(row["source_identity"]), str(row["target_identity"]))
        for row in meta["top20_identities"]
    )
    stat_top20 = tuple((str(row["source"]), str(row["target"])) for row in stat["top20"])
    if len(meta_top20) != 20 or len(stat_top20) != 20:
        raise RuntimeError("EXP01_FROZEN_COMPARATOR_CARDINALITY_REJECTED")
    return meta_top20, stat_top20


def _load_optimization_authority(root: Path) -> dict[str, object]:
    path = root / "docs/task_reports/TASK-039D1R_EXECUTION_COMPLEXITY_RECEIPT.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    if verify_recovery_artifact_v1(document) != OPTIMIZATION_AUTHORITY_HASH:
        raise RuntimeError("EXP01_OPTIMIZATION_AUTHORITY_REPLAY_REJECTED")
    source_hashes = document.get("source_file_hashes")
    if not isinstance(source_hashes, dict):
        raise RuntimeError("EXP01_OPTIMIZATION_SOURCE_BINDING_REJECTED")
    for relative in (
        "src/paperworks/profiling/task039d1_execution_optimization_v1.py",
        "src/paperworks/v6/continuous_step_protocol_v1.py",
    ):
        expected = source_hashes.get(relative)
        observed = sha256((root / relative).read_bytes()).hexdigest()
        if expected != observed:
            raise RuntimeError("EXP01_OPTIMIZATION_SOURCE_BINDING_REJECTED")
    return {
        "task_id": "TASK-039D1R",
        "artifact_hash": OPTIMIZATION_AUTHORITY_HASH,
        "status": document["status"],
        "event_semantic_parity": document["event_semantic_parity"],
        "isolation_semantic_parity": document["isolation_semantic_parity"],
        "event_complexity_class": document["event_complexity_class"],
        "isolation_complexity_class": document["isolation_complexity_class"],
        "semantic_preserving_implementation_change": True,
        "scientific_formulas_changed": False,
        "scientific_configuration_changed": False,
        "protocol_changed": False,
    }


def _write_atomic(path: Path, document: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".partial")
    if path.exists() or partial.exists():
        raise RuntimeError("EXP01_RESUME_STALE_OR_EXISTING_OUTPUT_REJECTED")
    raw = (json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    with partial.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(partial, path)


def _assert_output_absent(path: Path) -> None:
    partial = path.with_suffix(path.suffix + ".partial")
    if path.exists() or partial.exists():
        raise RuntimeError("EXP01_RESUME_STALE_OR_EXISTING_OUTPUT_REJECTED")


def _preflight_checkpoint_set(
    private_root: Path,
    expected_receipt_hashes: object,
) -> tuple[str, ...]:
    if not isinstance(expected_receipt_hashes, list):
        raise RuntimeError("EXP01_RESUME_CHECKPOINT_RECEIPT_LIST_REJECTED")
    actual_names = {path.name for path in private_root.iterdir() if path.is_file()}
    if actual_names != set(expected_checkpoint_names_v2()):
        raise RuntimeError("EXP01_RESUME_CHECKPOINT_NAMESPACE_MISMATCH")
    config = UpstreamGDNTrainingConfigV1()
    observed = []
    for order, (arm, view, seed) in enumerate(EXPECTED_SCHEDULE, start=1):
        run_id = f"run_{order:02d}_{arm}_{view}_seed_{seed}"
        _, receipt, _ = recover_existing_private_checkpoint_v2(
            private_root=private_root,
            run_id=run_id,
            arm_id=arm,
            view_id=view,
            seed=seed,
            expected_code_authority_hash=ORIGIN_TRAINING_CODE_AUTHORITY_HASH,
            expected_training_config_hash=config.hyperparameter_hash,
        )
        observed.append(receipt.receipt_hash)
    if observed != expected_receipt_hashes:
        raise RuntimeError("EXP01_RESUME_CHECKPOINT_RECEIPT_SET_CHANGED")
    return tuple(observed)


def _compute_environment() -> dict[str, object]:
    import torch

    cuda_available = bool(torch.cuda.is_available())
    cudnn = getattr(torch.backends, "cudnn", None)
    host_gpu: dict[str, object] = {
        "host_gpu_available": False,
        "gpu_model": None,
        "driver_version": None,
        "driver_reported_cuda_version": None,
        "vram_total_mib": None,
        "vram_used_mib_at_receipt": None,
        "gpu_utilization_percent_at_receipt": None,
        "inventory_status": "NVIDIA_SMI_UNAVAILABLE",
    }
    try:
        query = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        fields = [item.strip() for item in query.stdout.splitlines()[0].split(",")]
        if len(fields) == 5:
            overview = subprocess.run(
                ["nvidia-smi"],
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout
            cuda_match = re.search(r"CUDA(?: UMD)? Version:\s*([0-9.]+)", overview)
            host_gpu = {
                "host_gpu_available": True,
                "gpu_model": fields[0],
                "driver_version": fields[1],
                "driver_reported_cuda_version": cuda_match.group(1) if cuda_match else None,
                "vram_total_mib": int(fields[2]),
                "vram_used_mib_at_receipt": int(fields[3]),
                "gpu_utilization_percent_at_receipt": int(fields[4]),
                "inventory_status": "NVIDIA_SMI_PASS",
            }
    except (FileNotFoundError, IndexError, OSError, subprocess.SubprocessError, ValueError):
        pass
    return {
        "python_version": platform.python_version(),
        "torch_version": str(torch.__version__),
        "torch_cuda_version": torch.version.cuda,
        "cuda_available": cuda_available,
        "compute_device": "cpu",
        **host_gpu,
        "dtype": "float32",
        "seed_set": [11, 23, 37],
        "deterministic_flags": {
            "deterministic_algorithms": bool(torch.are_deterministic_algorithms_enabled()),
            "cudnn_deterministic": bool(cudnn.deterministic) if cudnn is not None else False,
            "cudnn_benchmark": bool(cudnn.benchmark) if cudnn is not None else False,
        },
        "device_change_from_training": False,
        "gpu_used": False,
    }


def _attempt_counters(*, evaluator_calls: int, train4_calls: int) -> dict[str, int]:
    return {
        "train1_opens": 1,
        "train2_opens": 1,
        "train3_opens": evaluator_calls,
        "train4_opens": train4_calls,
        "test1_accesses": 0,
        "test2_accesses": 0,
        "heldout_accesses": 0,
        "label_accesses": 0,
        "provider_calls": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--expected-source-commit", required=True)
    parser.add_argument("--private-checkpoint-root", type=Path, required=True)
    parser.add_argument("--private-relation-ledger", type=Path, required=True)
    parser.add_argument("--checkpoint-recovery-receipt", type=Path, required=True)
    parser.add_argument("--public-receipt", type=Path, required=True)
    args = parser.parse_args()

    root = args.repository_root.resolve(strict=True)
    head = _git_head(root)
    if head != args.expected_source_commit:
        raise SystemExit("EXP01_RESUME_EXPECTED_SOURCE_COMMIT_MISMATCH")
    if not _git_worktree_is_clean(root):
        raise SystemExit("EXP01_RESUME_DIRTY_WORKTREE_REJECTED")
    private_root = args.private_checkpoint_root.resolve(strict=True)
    private_relation_ledger = args.private_relation_ledger.resolve()
    for private_path in (private_root, private_relation_ledger):
        try:
            private_path.relative_to(root)
        except ValueError:
            pass
        else:
            raise SystemExit("PRIVATE_EXP01_RESUME_OUTPUT_INSIDE_REPOSITORY_REJECTED")
    public_receipt = args.public_receipt.resolve()
    try:
        public_receipt.relative_to(root)
    except ValueError as error:
        raise SystemExit("PUBLIC_EXP01_RESUME_RECEIPT_OUTSIDE_REPOSITORY_REJECTED") from error
    _assert_output_absent(private_relation_ledger)
    _assert_output_absent(public_receipt)

    recovery_document = json.loads(
        args.checkpoint_recovery_receipt.resolve(strict=True).read_text(encoding="utf-8")
    )
    recovery_hash = verify_interrupted_checkpoint_recovery_receipt_v2(recovery_document)
    _preflight_checkpoint_set(
        private_root,
        recovery_document["checkpoint_receipt_hashes"],
    )
    # Replay every public authority before resolving the private-data capability.
    meta_top20, stat_top20 = _load_frozen_comparator_results(root)
    optimization_authority = _load_optimization_authority(root)
    code_hash = _postprocessing_code_hash(root)
    environment = _compute_environment()
    protocol = build_validation_protocol_v1(source_commit=head)
    guard = ProtocolExecutionGuardV1(protocol)
    ledger = HAIFeatureAccessLedgerV1(experiment_id="VALIDATION-V2-EXP-01-POSTPROCESSING-RESUME")
    capability = resolve_hai_feature_root_capability_v1(root)
    train1 = load_authorized_hai_feature_frame_v1(
        capability=capability,
        split_id="train1",
        operation=ProtocolOperationV1.CANDIDATE_LEARNING,
        protocol_guard=guard,
        ledger=ledger,
    )
    train2 = load_authorized_hai_feature_frame_v1(
        capability=capability,
        split_id="train2",
        operation=ProtocolOperationV1.CANDIDATE_LEARNING,
        protocol_guard=guard,
        ledger=ledger,
    )
    matrix1 = train1.numeric_matrix(P1_FEATURE_ORDER)
    matrix2 = train2.numeric_matrix(P1_FEATURE_ORDER)
    receipt1 = str(train1.receipt.to_dict()["receipt_hash"])
    receipt2 = str(train2.receipt.to_dict()["receipt_hash"])
    views = {
        ViewId.COMBINED: Exp01ViewInputV2(
            ViewId.COMBINED, (matrix1, matrix2), (receipt1, receipt2)
        ),
        ViewId.TRAIN1_ONLY: Exp01ViewInputV2(ViewId.TRAIN1_ONLY, (matrix1,), (receipt1,)),
        ViewId.TRAIN2_ONLY: Exp01ViewInputV2(ViewId.TRAIN2_ONLY, (matrix2,), (receipt2,)),
    }
    evaluator_calls = 0
    train4_provider_calls = 0

    def evaluator(pairs: tuple[tuple[str, str], ...]):
        nonlocal evaluator_calls
        evaluator_calls += 1
        if evaluator_calls != 1:
            raise RuntimeError("ARM_BLIND_RELATION_EVALUATOR_REENTRY_REJECTED")
        train3 = load_authorized_hai_feature_frame_v1(
            capability=capability,
            split_id="train3",
            operation=ProtocolOperationV1.RELATION_CONFIRMATION,
            protocol_guard=guard,
            ledger=ledger,
        )
        relation = fit_and_confirm_arbitrary_union_v2(
            candidate_pairs=pairs,
            train1_matrix=matrix1,
            train2_matrix=matrix2,
            train3_matrix=train3.numeric_matrix(P1_FEATURE_ORDER),
            feature_order=P1_FEATURE_ORDER,
            train1_read_receipt_hash=receipt1,
            train2_read_receipt_hash=receipt2,
            train3_read_receipt_hash=str(train3.receipt.to_dict()["receipt_hash"]),
        )
        _write_atomic(private_relation_ledger, dict(relation.private_ledger))
        return relation.outcome

    def train4_provider():
        nonlocal train4_provider_calls
        train4_provider_calls += 1
        if evaluator_calls != 1 or train4_provider_calls != 1:
            raise RuntimeError("TRAIN4_STAGE_ORDER_OR_REENTRY_REJECTED")
        train4 = load_authorized_hai_feature_frame_v1(
            capability=capability,
            split_id="train4",
            operation=ProtocolOperationV1.NORMAL_SANITY,
            protocol_guard=guard,
            ledger=ledger,
        )
        return (
            (train4.numeric_matrix(P1_FEATURE_ORDER),),
            str(train4.receipt.to_dict()["receipt_hash"]),
        )

    try:
        result = resume_exp01_postprocessing_v2(
            views=views,
            train4_provider=train4_provider,
            feature_order=P1_FEATURE_ORDER,
            private_checkpoint_root=private_root,
            checkpoint_origin_code_hash=ORIGIN_TRAINING_CODE_AUTHORITY_HASH,
            confirmation_evaluator=evaluator,
            meta_top20=meta_top20,
            stat_top20=stat_top20,
        )
    except Exp01ExecutionError as error:
        if str(error) != EXPECTED_CONTRACT_CONFLICT:
            raise
        resume_counters = _attempt_counters(
            evaluator_calls=evaluator_calls,
            train4_calls=train4_provider_calls,
        )
        terminal_content: dict[str, object] = {
            "schema": "paperworks.validation_v2.exp01_execution_terminal_receipt_v2",
            "schema_version": "2.0.0",
            "status": EXPECTED_CONTRACT_CONFLICT,
            "classification": "PREDECLARED_FAIL_CLOSED_INCOMPLETE_EXECUTION_NOT_NEGATIVE_RESULT",
            "training_source_commit": ORIGIN_TRAINING_SOURCE_COMMIT,
            "checkpoint_origin_code_authority_hash": ORIGIN_TRAINING_CODE_AUTHORITY_HASH,
            "checkpoint_recovery_receipt_hash": recovery_hash,
            "postprocessing_source_commit": head,
            "postprocessing_code_authority_hash": code_hash,
            "optimization_authority": optimization_authority,
            "training_reexecuted": False,
            "compute_environment": environment,
            "interrupted_attempt_access_counters": dict(INTERRUPTED_ACCESS_COUNTERS),
            "resume_attempt_access_counters": resume_counters,
            "cumulative_known_access_counters": cumulative_access_counters_v2(resume_counters),
            "feature_access_ledger": ledger.public_document(),
            "candidate_disposition": "GDN_CONTRIBUTION_UNRESOLVED_FAIL_CLOSED",
            "post_result_reranking": False,
            "claim_boundary": "NO_GDN_CONTRIBUTION_RESULT_AND_NO_DETECTION_PERFORMANCE_CLAIM",
            "redaction": "NO_PRIVATE_PATHS_VALUES_SCORES_LOSSES_OR_CHECKPOINT_BYTES",
        }
        terminal = {**terminal_content, "public_receipt_hash": stable_hash_v1(terminal_content)}
        _write_atomic(public_receipt, terminal)
        print(json.dumps({"status": terminal["status"], "receipt": terminal["public_receipt_hash"]}, sort_keys=True))
        return 2

    recovered_hashes = [item.receipt_hash for item in result.checkpoint_receipts]
    if recovered_hashes != recovery_document["checkpoint_receipt_hashes"]:
        raise RuntimeError("EXP01_RESUME_CHECKPOINT_RECEIPT_SET_CHANGED")
    resume_counters = dict(result.access_counters)
    public = result.public_document()
    public.update({
        "execution_mode": "CHECKPOINT_RESUME_POSTPROCESSING_V2",
        "training_source_commit": ORIGIN_TRAINING_SOURCE_COMMIT,
        "checkpoint_origin_code_authority_hash": ORIGIN_TRAINING_CODE_AUTHORITY_HASH,
        "checkpoint_recovery_receipt_hash": recovery_hash,
        "postprocessing_source_commit": head,
        "postprocessing_code_authority_hash": code_hash,
        "optimization_authority": optimization_authority,
        "training_reexecuted": False,
        "compute_environment": environment,
        "interrupted_attempt_access_counters": dict(INTERRUPTED_ACCESS_COUNTERS),
        "resume_attempt_access_counters": resume_counters,
        "cumulative_known_access_counters": cumulative_access_counters_v2(resume_counters),
        "feature_access_ledger": ledger.public_document(),
        "arm_blind_relation_evaluator_calls": evaluator_calls,
        "train4_provider_calls": train4_provider_calls,
        "scientific_configuration_changed": False,
        "semantic_preserving_implementation_change": True,
        "preregistration_changed": False,
        "result_driven_change": False,
    })
    public["public_receipt_hash"] = stable_hash_v1(public)
    _write_atomic(public_receipt, public)
    print(json.dumps({"status": public["status"], "result_hash": result.result_hash}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
