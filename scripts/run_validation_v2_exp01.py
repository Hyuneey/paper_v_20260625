"""Run the frozen EXP-01 matrix after all upstream authorities are present."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

from paperworks.validation_v2.exp01_execution_v2 import Exp01ViewInputV2, execute_exp01_matrix_v2
from paperworks.validation_v2.exp01_relation_confirmation_v2 import fit_and_confirm_arbitrary_union_v2
from paperworks.validation_v2.exp01_scientific_v1 import (
    META_RESULT_HASH,
    STAT_RESULT_HASH,
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
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER
from paperworks.v6.common import stable_hash_v1


def _git_head(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True,
    )
    return result.stdout.strip()


def _git_worktree_is_clean(root: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=all"],
        check=True,
        capture_output=True,
        text=True,
    )
    return not result.stdout.strip()


def _code_hash(root: Path) -> str:
    digest = sha256()
    paths = (
        "src/paperworks/gdn/exp01_upstream_backend_v2.py",
        "src/paperworks/validation_v2/exp01_checkpoint_v2.py",
        "src/paperworks/validation_v2/exp01_execution_v2.py",
        "src/paperworks/validation_v2/exp01_relation_confirmation_v2.py",
        "src/paperworks/validation_v2/exp01_scientific_v1.py",
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
    """Replay the exact tracked META/STAT authorities used by the preregistration."""

    meta_path = root / "docs/task_reports/TASK-039C_META_RESULT.json"
    stat_path = root / "docs/task_reports/TASK-039C_STAT_RESULT.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    stat = json.loads(stat_path.read_text(encoding="utf-8"))
    for name, document, expected in (
        ("META", meta, META_RESULT_HASH),
        ("STAT", stat, STAT_RESULT_HASH),
    ):
        observed = document.get("artifact_hash")
        replayed = stable_hash_v1(
            {key: value for key, value in document.items() if key != "artifact_hash"}
        )
        if observed != expected or replayed != expected:
            raise RuntimeError(f"EXP01_FROZEN_{name}_AUTHORITY_REPLAY_REJECTED")
    meta_top20 = tuple(
        (str(row["source_identity"]), str(row["target_identity"]))
        for row in meta["top20_identities"]
    )
    stat_top20 = tuple(
        (str(row["source"]), str(row["target"])) for row in stat["top20"]
    )
    if len(meta_top20) != 20 or len(stat_top20) != 20:
        raise RuntimeError("EXP01_FROZEN_COMPARATOR_CARDINALITY_REJECTED")
    return meta_top20, stat_top20


def _write_atomic(path: Path, document: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    if path.exists() or temporary.exists():
        raise RuntimeError("EXP01_STALE_OR_EXISTING_OUTPUT_REJECTED")
    raw = (json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    with temporary.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--expected-source-commit", required=True)
    parser.add_argument("--private-checkpoint-root", type=Path, required=True)
    parser.add_argument("--private-relation-ledger", type=Path, required=True)
    parser.add_argument("--public-receipt", type=Path, required=True)
    args = parser.parse_args()
    root = args.repository_root.resolve(strict=True)
    private_root = args.private_checkpoint_root.resolve()
    private_relation_ledger = args.private_relation_ledger.resolve()
    for private_path in (private_root, private_relation_ledger):
        try:
            private_path.relative_to(root)
        except ValueError:
            pass
        else:
            raise SystemExit("PRIVATE_EXP01_OUTPUT_INSIDE_REPOSITORY_REJECTED")
    head = _git_head(root)
    if args.expected_source_commit != head:
        raise SystemExit("EXP01_EXPECTED_SOURCE_COMMIT_MISMATCH")
    if not _git_worktree_is_clean(root):
        raise SystemExit("EXP01_DIRTY_WORKTREE_REJECTED")
    # Replay every tracked non-data authority before resolving a private-data
    # capability.  A missing or mutated comparator therefore causes zero
    # scientific file opens.
    meta_top20, stat_top20 = _load_frozen_comparator_results(root)
    protocol = build_validation_protocol_v1(source_commit=head)
    guard = ProtocolExecutionGuardV1(protocol)
    ledger = HAIFeatureAccessLedgerV1(experiment_id="VALIDATION-V2-EXP-01")
    capability = resolve_hai_feature_root_capability_v1(root)
    train1 = load_authorized_hai_feature_frame_v1(
        capability=capability, split_id="train1", operation=ProtocolOperationV1.CANDIDATE_LEARNING,
        protocol_guard=guard, ledger=ledger,
    )
    train2 = load_authorized_hai_feature_frame_v1(
        capability=capability, split_id="train2", operation=ProtocolOperationV1.CANDIDATE_LEARNING,
        protocol_guard=guard, ledger=ledger,
    )
    matrix1 = train1.numeric_matrix(P1_FEATURE_ORDER)
    matrix2 = train2.numeric_matrix(P1_FEATURE_ORDER)
    receipt1 = str(train1.receipt.to_dict()["receipt_hash"])
    receipt2 = str(train2.receipt.to_dict()["receipt_hash"])
    views = {
        ViewId.COMBINED: Exp01ViewInputV2(ViewId.COMBINED, (matrix1, matrix2), (receipt1, receipt2)),
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
        # train3 is opened here, after the exact Phase-A union is known.  No
        # precomputed candidate-order artifact is required.
        train3 = load_authorized_hai_feature_frame_v1(
            capability=capability, split_id="train3",
            operation=ProtocolOperationV1.RELATION_CONFIRMATION,
            protocol_guard=guard, ledger=ledger,
        )
        relation = fit_and_confirm_arbitrary_union_v2(
            candidate_pairs=pairs,
            train1_matrix=matrix1, train2_matrix=matrix2,
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
            capability=capability, split_id="train4", operation=ProtocolOperationV1.NORMAL_SANITY,
            protocol_guard=guard, ledger=ledger,
        )
        return (
            (train4.numeric_matrix(P1_FEATURE_ORDER),),
            str(train4.receipt.to_dict()["receipt_hash"]),
        )

    result = execute_exp01_matrix_v2(
        views=views,
        train4_provider=train4_provider,
        feature_order=P1_FEATURE_ORDER,
        private_checkpoint_root=private_root,
        code_authority_hash=_code_hash(root),
        confirmation_evaluator=evaluator,
        meta_top20=meta_top20,
        stat_top20=stat_top20,
    )
    public = result.public_document()
    public["source_commit"] = head
    public["feature_access_ledger"] = ledger.public_document()
    public["arm_blind_relation_evaluator_calls"] = evaluator_calls
    public["train4_provider_calls"] = train4_provider_calls
    public["public_receipt_hash"] = stable_hash_v1(public)
    _write_atomic(args.public_receipt, public)
    print(json.dumps({"status": public["status"], "result_hash": result.result_hash}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
