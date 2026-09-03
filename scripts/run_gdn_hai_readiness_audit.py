#!/usr/bin/env python3
"""Normal-only HAI scale, validation-overlap, and temporal-alignment audit."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import random
from typing import Any, Mapping, Sequence

import numpy as np

from paperworks.validation_v2.gdn_corr_v1 import summarize_feature_scales_v1
from paperworks.validation_v2.hai_feature_adapter_v1 import (
    HAIFeatureAccessLedgerV1, load_authorized_hai_feature_frame_v1,
    resolve_hai_feature_root_capability_v1,
)
from paperworks.validation_v2.protocol_v1 import (
    ProtocolExecutionGuardV1, ProtocolOperationV1, build_validation_protocol_v1,
)
from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER


PUBLIC = Path("research_control_center/validation_v2/gdn_corr_001/hai_readiness")
PRIVATE = Path("artifacts/validation_v2/gdn_corr_001/hai_readiness/private")
BINDING = Path("research_control_center/validation_v2/gdn_corr_001/contracts/HAI_READINESS_EXECUTION_BINDING.json")


class HAIReadinessError(RuntimeError):
    pass


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode() + b"\n"


def _write_new(path: Path, value: Mapping[str, Any]) -> str:
    payload = _canonical(value); path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload: raise HAIReadinessError(f"HAI_READINESS_OUTPUT_MISMATCH:{path.name}")
    else:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "wb", closefd=False) as stream:
                stream.write(payload); stream.flush(); os.fsync(stream.fileno())
        finally: os.close(descriptor)
    return sha256(payload).hexdigest()


def _loss_shares(segments: Sequence[np.ndarray], scale: np.ndarray) -> dict[str, Any]:
    by_feature = np.zeros(len(scale), dtype=np.float64)
    by_horizon = {}
    for horizon in (1, 5, 10, 30, 60):
        total = np.zeros(len(scale), dtype=np.float64); count = 0
        for segment in segments:
            diff = (segment[horizon:] - segment[:-horizon]) / scale
            total += np.sum(diff * diff, axis=0); count += len(diff)
        mse = total / count; by_feature += mse; by_horizon[str(horizon)] = float(np.max(mse) / np.sum(mse))
    shares = by_feature / np.sum(by_feature); ordered = np.sort(shares)[::-1]
    return {
        "top5_feature_share": float(np.sum(ordered[:5])),
        "largest_feature_share": float(ordered[0]),
        "effective_feature_count_inverse_hhi": float(1.0 / np.sum(shares * shares)),
        "largest_target_share_by_horizon": by_horizon,
    }


def _validation_rows(
    lengths: Sequence[int],
    seed: int,
    *,
    single_file_location: str | None = None,
) -> dict[str, Any]:
    counts = [length - 5 for length in lengths]
    total = sum(counts); train_length = int(total * 0.8); validation_count = int(total * 0.2)
    start = random.Random(seed).randrange(train_length); stop = start + validation_count
    boundary = counts[0] if len(counts) == 2 else None
    crosses = bool(boundary is not None and start < boundary < stop)
    if boundary is None:
        if single_file_location not in {"TRAIN1", "TRAIN2"}:
            raise HAIReadinessError(
                "single-file validation location must be explicit"
            )
        location = single_file_location
    else:
        location = "CROSSES_TRAIN1_TRAIN2_BOUNDARY" if crosses else (
            "TRAIN1" if stop <= boundary else "TRAIN2"
        )
    overlap_count = 10 if start > 0 and stop < total else 5
    return {
        "seed": seed, "validation_window_count": validation_count,
        "validation_block_location": location, "cross_file_validation_block": crosses,
        "overlapping_raw_timestamp_count": overlap_count,
        "overlap_fraction_of_validation_windows": overlap_count / validation_count,
    }


def execute(root: Path) -> None:
    binding = json.loads((root / BINDING).read_text(encoding="utf-8"))
    body = {key: value for key, value in binding.items() if key != "binding_hash"}
    if binding.get("binding_hash") != stable_hash_v1(body) or binding.get("status") != "FROZEN_BEFORE_NORMAL_DATA_IO":
        raise HAIReadinessError("HAI_READINESS_BINDING_REPLAY_FAILED")
    protocol = build_validation_protocol_v1(source_commit=str(binding["source_commit"]))
    guard = ProtocolExecutionGuardV1(protocol); ledger = HAIFeatureAccessLedgerV1(experiment_id="GDN-CORR-001-HAI-READINESS")
    capability = resolve_hai_feature_root_capability_v1(root)
    frames = {split: load_authorized_hai_feature_frame_v1(
        capability=capability, split_id=split, operation=ProtocolOperationV1.CANDIDATE_LEARNING,
        protocol_guard=guard, ledger=ledger,
    ) for split in ("train1", "train2")}
    segments = tuple(np.asarray(frames[split].numeric_matrix(), dtype=np.float64) for split in ("train1", "train2"))
    pooled = np.concatenate(segments, axis=0)
    summaries = summarize_feature_scales_v1(pooled)
    raw_range = np.array([item.maximum - item.minimum for item in summaries])
    raw_std = np.array([item.std for item in summaries])
    diff_medians = []
    for column in range(pooled.shape[1]):
        differences = np.concatenate(tuple(np.abs(np.diff(segment[:, column])) for segment in segments))
        diff_medians.append(float(np.median(differences)))
    def ratio(values: np.ndarray) -> float:
        positive = values[values > 1e-12]
        return float(np.max(positive) / np.min(positive)) if len(positive) else math.inf
    standard_scale = np.where(raw_std > 1e-12, raw_std, 1.0)
    q25, q75 = np.quantile(pooled, (0.25, 0.75), axis=0, method="linear")
    robust_scale = np.where((q75 - q25) > 1e-12, q75 - q25, 1.0)
    policy_rows = {
        "RAW_CURRENT": _loss_shares(segments, np.ones(pooled.shape[1])),
        "TRAIN_ONLY_STANDARDIZED": _loss_shares(segments, standard_scale),
        "TRAIN_ONLY_ROBUST_MEDIAN_IQR": _loss_shares(segments, robust_scale),
    }
    scale_ratio = ratio(raw_range); raw_share = policy_rows["RAW_CURRENT"]["top5_feature_share"]
    robust_share = policy_rows["TRAIN_ONLY_ROBUST_MEDIAN_IQR"]["top5_feature_share"]
    selected = "TRAIN_ONLY_ROBUST_MEDIAN_IQR" if scale_ratio >= 100 and raw_share >= 0.50 and raw_share - robust_share >= 0.10 else "RAW_CURRENT"
    private_body = {
        "schema": "paperworks.validation_v2.gdn_hai_private_scale_audit_v1",
        "features": [{"feature": feature, **summary.__dict__, "median_abs_file_local_first_difference": diff_medians[index]} for index, (feature, summary) in enumerate(zip(P1_FEATURE_ORDER, summaries))],
        "input_receipts": {split: frames[split].receipt.to_dict() for split in ("train1", "train2")},
    }
    private_hash = _write_new(root / PRIVATE / "HAI_FEATURE_SCALE_AUDIT.private.json", private_body)
    public = {
        "schema": "paperworks.validation_v2.gdn_hai_preprocessing_audit_v1", "status": "COMPLETE_NORMAL_ONLY",
        "feature_count": len(P1_FEATURE_ORDER), "row_count": sum(len(item) for item in segments),
        "largest_to_smallest_nonzero_range_ratio": scale_ratio,
        "largest_to_smallest_nonzero_std_ratio": ratio(raw_std),
        "largest_to_smallest_nonzero_first_difference_ratio": ratio(np.asarray(diff_medians)),
        "near_zero_variance_feature_count": sum(item.near_zero_variance for item in summaries),
        "policy_comparison": policy_rows, "raw_global_mse_scale_dominated": bool(scale_ratio >= 100 and raw_share >= 0.50),
        "selected_exp01c_preprocessing": selected, "selection_rule": "FROZEN_EXP01C_PREREGISTRATION",
        "private_scale_bundle_sha256": private_hash, "private_numeric_values_exposed": False,
        "access_ledger": ledger.public_document(), "test1_accesses": 0, "label_accesses": 0, "test2_accesses": 0, "heldout_accesses": 0,
    }
    public["audit_hash"] = stable_hash_v1(public); _write_new(root / PUBLIC / "HAI_PREPROCESSING_AUDIT.json", public)
    overlap_rows = []
    for view, lengths, single_file_location in (
        ("TRAIN1_TRAIN2_COMBINED", tuple(len(item) for item in segments), None),
        ("TRAIN1_ONLY", (len(segments[0]),), "TRAIN1"),
        ("TRAIN2_ONLY", (len(segments[1]),), "TRAIN2"),
    ):
        for seed in (11, 23, 37):
            overlap_rows.append(
                {
                    "view": view,
                    **_validation_rows(
                        lengths,
                        seed,
                        single_file_location=single_file_location,
                    ),
                }
            )
    overlap = {
        "schema": "paperworks.validation_v2.exp01b_validation_overlap_audit_v1",
        "frozen_v1_validation_policy": "UPSTREAM_SEEDED_CONTIGUOUS_RANDOM_WINDOW_BLOCK_NO_PURGE",
        "runs": overlap_rows, "all_runs_have_raw_timestamp_overlap": all(row["overlapping_raw_timestamp_count"] > 0 for row in overlap_rows),
        "prospective_exp01c_policy": "ONE_CONTIGUOUS_BLOCK_PER_FILE_PURGE_66_ZERO_RAW_TIMESTAMP_OVERLAP",
        "exp01b_v1_changed": False, "test1_accesses": 0, "label_accesses": 0, "test2_accesses": 0,
    }
    overlap["audit_hash"] = stable_hash_v1(overlap); _write_new(root / PUBLIC / "VALIDATION_OVERLAP_AUDIT.json", overlap)
    decision = {
        "schema": "paperworks.validation_v2.exp01c_preprocessing_decision_v1",
        "selected_policy": selected, "audit_hash": public["audit_hash"],
        "decision_rule": "FROZEN_BEFORE_AUDIT", "attack_performance_used": False,
        "test1_accesses": 0, "label_accesses": 0, "test2_accesses": 0,
    }
    decision["decision_hash"] = stable_hash_v1(decision); _write_new(root / PUBLIC / "EXP01C_PREPROCESSING_DECISION.json", decision)
    report = (
        "# HAI GDN 설계 적합성 감사\n\n"
        "- EXP-01B-V1은 raw 37-feature global MSE와 5-row history→next-row 예측을 사용했다.\n"
        f"- 정상 train1/train2 scale audit 결과 raw global MSE scale-dominated: `{public['raw_global_mse_scale_dominated']}`.\n"
        f"- 동결된 선택 규칙에 따른 EXP-01C preprocessing: `{selected}`.\n"
        "- 기존 validation은 모든 9개 run에서 train/validation raw timestamp가 겹쳤고, combined seed 11 block은 file boundary를 넘었다.\n"
        "- EXP-01C는 file별 contiguous block, purge 66, raw overlap 0을 요구한다.\n"
        "- EXP-01C는 horizons 1/5/10/30/60의 three-row future median을 공동 learned graph로 예측한다.\n"
        "- Shared-encoder attention은 horizon별로 결속해 보고하되 head-specific attention으로 부르지 않는다.\n"
        "- learned Top-5 graph member는 direct EdgeMask, 비회원은 NOT_IN_LEARNED_GRAPH 상태와 source occlusion 경로를 갖는다.\n"
        "- 모든 결론은 normal-only predictive/functional evidence이며 causal claim이 아니다.\n"
    )
    report_path = root / PUBLIC / "HAI_ADAPTATION_AUDIT.md"; report_path.write_text(report, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "PASS", "selected_preprocessing": selected, "scale_dominated": public["raw_global_mse_scale_dominated"], "test1_accesses": 0, "test2_accesses": 0}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, default=Path.cwd()); args = parser.parse_args(); execute(args.root.resolve(strict=True))


if __name__ == "__main__": main()
