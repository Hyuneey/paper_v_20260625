"""Bind the twelve completed EXP-01 checkpoints after an interrupted attempt."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from paperworks.gdn.upstream_candidate_backend_v1 import UpstreamGDNTrainingConfigV1
from paperworks.validation_v2.exp01_checkpoint_v2 import recover_existing_private_checkpoint_v2
from paperworks.validation_v2.exp01_recovery_v2 import (
    ORIGIN_TRAINING_CODE_AUTHORITY_HASH,
    ORIGIN_TRAINING_SOURCE_COMMIT,
    build_interrupted_checkpoint_recovery_receipt_v2,
    expected_checkpoint_names_v2,
)
from paperworks.validation_v2.exp01_scientific_v1 import EXPECTED_SCHEDULE
from paperworks.v6.common import stable_hash_v1


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


def _write_atomic(path: Path, document: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".partial")
    if path.exists() or partial.exists():
        raise RuntimeError("EXP01_RECOVERY_STALE_OR_EXISTING_OUTPUT_REJECTED")
    raw = (json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    with partial.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(partial, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--expected-source-commit", required=True)
    parser.add_argument("--private-checkpoint-root", type=Path, required=True)
    parser.add_argument("--private-manifest", type=Path, required=True)
    parser.add_argument("--public-receipt", type=Path, required=True)
    args = parser.parse_args()

    root = args.repository_root.resolve(strict=True)
    head = _git_head(root)
    if head != args.expected_source_commit:
        raise SystemExit("EXP01_RECOVERY_EXPECTED_SOURCE_COMMIT_MISMATCH")
    if not _git_worktree_is_clean(root):
        raise SystemExit("EXP01_RECOVERY_DIRTY_WORKTREE_REJECTED")
    private_root = args.private_checkpoint_root.resolve(strict=True)
    private_manifest = args.private_manifest.resolve()
    for private_path in (private_root, private_manifest):
        try:
            private_path.relative_to(root)
        except ValueError:
            pass
        else:
            raise SystemExit("PRIVATE_EXP01_RECOVERY_OUTPUT_INSIDE_REPOSITORY_REJECTED")
    public_receipt = args.public_receipt.resolve()
    try:
        public_receipt.relative_to(root)
    except ValueError as error:
        raise SystemExit("PUBLIC_EXP01_RECOVERY_RECEIPT_OUTSIDE_REPOSITORY_REJECTED") from error

    expected_names = set(expected_checkpoint_names_v2())
    actual_names = {path.name for path in private_root.iterdir() if path.is_file()}
    if actual_names != expected_names:
        raise SystemExit("EXP01_RECOVERY_CHECKPOINT_NAMESPACE_MISMATCH")
    training_config = UpstreamGDNTrainingConfigV1()
    receipts = []
    private_rows = []
    for order, (arm, view, seed) in enumerate(EXPECTED_SCHEDULE, start=1):
        run_id = f"run_{order:02d}_{arm}_{view}_seed_{seed}"
        path, receipt, _ = recover_existing_private_checkpoint_v2(
            private_root=private_root,
            run_id=run_id,
            arm_id=arm,
            view_id=view,
            seed=seed,
            expected_code_authority_hash=ORIGIN_TRAINING_CODE_AUTHORITY_HASH,
            expected_training_config_hash=training_config.hyperparameter_hash,
        )
        receipts.append(receipt)
        private_rows.append({**receipt.to_dict(), "private_path": str(path)})

    public = build_interrupted_checkpoint_recovery_receipt_v2(
        checkpoint_receipts=receipts,
        snapshot_source_commit=head,
    )
    private_content: dict[str, object] = {
        "schema": "paperworks.validation_v2.exp01_interrupted_checkpoint_private_manifest_v2",
        "schema_version": "2.0.0",
        "training_source_commit": ORIGIN_TRAINING_SOURCE_COMMIT,
        "snapshot_source_commit": head,
        "checkpoint_root": str(private_root),
        "checkpoints": private_rows,
        "public_receipt_self_hash": public["receipt_self_hash"],
    }
    private = {**private_content, "manifest_self_hash": stable_hash_v1(private_content)}
    _write_atomic(private_manifest, private)
    _write_atomic(public_receipt, public)
    print(json.dumps({
        "status": public["status"],
        "checkpoint_count": public["checkpoint_count"],
        "receipt_self_hash": public["receipt_self_hash"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
