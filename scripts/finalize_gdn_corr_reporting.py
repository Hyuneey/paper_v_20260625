#!/usr/bin/env python3
"""Close public GDN-CORR reporting gaps without scientific data access."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any, Mapping

from paperworks.v6.common import stable_hash_v1


OVERLAP_SOURCE = Path(
    "research_control_center/validation_v2/gdn_corr_001/hai_readiness/"
    "VALIDATION_OVERLAP_AUDIT.json"
)
OVERLAP_R2 = Path(
    "research_control_center/validation_v2/gdn_corr_001/hai_readiness/"
    "VALIDATION_OVERLAP_AUDIT_R2.json"
)
OVERLAP_REPORT = Path(
    "research_control_center/validation_v2/gdn_corr_001/hai_readiness/"
    "VALIDATION_OVERLAP_REPORTING_CORRECTION.md"
)
FUNCTIONAL_RECEIPT = Path(
    "research_control_center/validation_v2/gdn_corr_001/exp01c_gdn_hai/"
    "receipts/EXP01C_FUNCTIONAL_RECEIPT.json"
)
EXECUTION_BINDING = Path(
    "research_control_center/validation_v2/gdn_corr_001/exp01c_gdn_hai/"
    "contracts/EXP01C_EXECUTION_BINDING_R3.json"
)
ATTENTION_RECEIPT = Path(
    "research_control_center/validation_v2/gdn_corr_001/exp01c_gdn_hai/"
    "receipts/EXP01C_ATTENTION_HORIZON_BINDING_RECEIPT.json"
)
RESULT_BINDING_RECEIPT = Path(
    "research_control_center/validation_v2/gdn_corr_001/"
    "GDN_CORR_001_RESULT_BINDING_RECEIPT.json"
)
RESULT_CSVS = (
    Path(
        "research_control_center/validation_v2/gdn_corr_001/exp01b_r1/"
        "results/EXP01B_R1_CORRECTED_RESULTS.csv"
    ),
    Path(
        "research_control_center/validation_v2/gdn_corr_001/exp01b_r1/"
        "results/EXP01B_R1_RANDOM_CONTROL_RESULTS.csv"
    ),
    Path(
        "research_control_center/validation_v2/gdn_corr_001/exp01b_r1/"
        "results/EXP01B_R1_STABILITY_RESULTS.csv"
    ),
    Path(
        "research_control_center/validation_v2/gdn_corr_001/exp01c_gdn_hai/"
        "results/EXP01C_RANDOM_CONTROL_RESULTS.csv"
    ),
    Path(
        "research_control_center/validation_v2/gdn_corr_001/exp01c_gdn_hai/"
        "results/EXP01C_RANKING_RESULTS.csv"
    ),
    Path(
        "research_control_center/validation_v2/gdn_corr_001/exp01c_gdn_hai/"
        "results/EXP01C_STABILITY_RESULTS.csv"
    ),
)


class ReportingFinalizationError(RuntimeError):
    """Raised when an immutable reporting input or output is inconsistent."""


def _canonical(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            dict(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _load_self_hashed(path: Path, hash_field: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    expected = value.pop(hash_field, None)
    if expected != stable_hash_v1(value):
        raise ReportingFinalizationError(f"SELF_HASH_REPLAY_FAILED:{path.name}")
    value[hash_field] = expected
    return value


def _write_new(path: Path, value: Mapping[str, Any]) -> None:
    payload = _canonical(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise ReportingFinalizationError(f"OUTPUT_MISMATCH:{path.name}")
        return
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(descriptor)


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def finalize(root: Path) -> dict[str, Any]:
    source_path = root / OVERLAP_SOURCE
    source = _load_self_hashed(source_path, "audit_hash")
    corrected_runs = []
    corrected_count = 0
    for row in source["runs"]:
        corrected = dict(row)
        expected_location = (
            "TRAIN2" if row["view"] == "TRAIN2_ONLY" else row["validation_block_location"]
        )
        if expected_location != row["validation_block_location"]:
            corrected_count += 1
        corrected["validation_block_location"] = expected_location
        corrected_runs.append(corrected)
    overlap_r2 = {
        "schema": "paperworks.validation_v2.exp01b_validation_overlap_audit_r2",
        "status": "REPORTING_LOCATION_CORRECTED",
        "supersedes_audit_hash": source["audit_hash"],
        "correction_scope": "TRAIN2_ONLY_VALIDATION_BLOCK_LOCATION_LABEL",
        "corrected_row_count": corrected_count,
        "runs": corrected_runs,
        "scientific_values_recomputed": False,
        "scientific_conclusion_changed": False,
        "exp01b_v1_changed": False,
        "test1_accesses": 0,
        "label_accesses": 0,
        "test2_accesses": 0,
        "heldout_accesses": 0,
    }
    overlap_r2["audit_hash"] = stable_hash_v1(overlap_r2)
    _write_new(root / OVERLAP_R2, overlap_r2)

    functional = _load_self_hashed(root / FUNCTIONAL_RECEIPT, "receipt_hash")
    binding = _load_self_hashed(root / EXECUTION_BINDING, "binding_hash")
    horizons = [1, 5, 10, 30, 60]
    attention_receipt = {
        "schema": "paperworks.validation_v2.exp01c_attention_horizon_binding_receipt_v1",
        "experiment_id": "EXP-01C-GDN-HAI-V1",
        "status": "PASS_REPORTING_BINDING",
        "attention_source": "SHARED_ENCODER_POST_NORMALIZATION_ATTENTION",
        "head_specific": False,
        "horizons_seconds": horizons,
        "horizon_bindings": [
            {
                "horizon_seconds": horizon,
                "semantic": "SHARED_ENCODER_ATTENTION_NOT_HEAD_SPECIFIC",
                "same_shared_attention_evidence": True,
            }
            for horizon in horizons
        ],
        "functional_receipt_hash": functional["receipt_hash"],
        "execution_binding_hash": binding["binding_hash"],
        "attention_invariance_passed_runs": functional[
            "attention_invariance_passed_runs"
        ],
        "scientific_values_recomputed": False,
        "private_evidence_opened": False,
        "test1_accesses": 0,
        "label_accesses": 0,
        "test2_accesses": 0,
        "heldout_accesses": 0,
        "private_exposures": 0,
    }
    attention_receipt["receipt_hash"] = stable_hash_v1(attention_receipt)
    _write_new(root / ATTENTION_RECEIPT, attention_receipt)

    result_binding = {
        "schema": "paperworks.validation_v2.gdn_corr_001_result_binding_receipt_v1",
        "status": "PASS_PUBLIC_RESULT_HASH_BINDING",
        "artifacts": [
            {
                "artifact": path.name,
                "experiment": "EXP-01B-R1"
                if "exp01b_r1" in path.as_posix()
                else "EXP-01C-GDN-HAI-V1",
                "sha256": _file_sha256(root / path),
            }
            for path in RESULT_CSVS
        ],
        "artifact_count": len(RESULT_CSVS),
        "overlap_r2_hash": overlap_r2["audit_hash"],
        "attention_horizon_binding_hash": attention_receipt["receipt_hash"],
        "scientific_values_recomputed": False,
        "private_artifacts_opened": False,
        "test1_accesses": 0,
        "label_accesses": 0,
        "test2_accesses": 0,
        "heldout_accesses": 0,
        "private_exposures": 0,
    }
    result_binding["receipt_hash"] = stable_hash_v1(result_binding)
    _write_new(root / RESULT_BINDING_RECEIPT, result_binding)

    report = (
        "# 검증 블록 위치 표기 정정\n\n"
        "- 원본 overlap 감사의 `TRAIN2_ONLY` 세 행이 `TRAIN1`으로 표기된 보고 오류를 정정했다.\n"
        "- 겹침 개수, 비율, seed, 결론은 재계산하거나 변경하지 않았다.\n"
        "- 원본 감사는 이력 보존을 위해 수정하지 않았으며 R2가 현재-facing 표기 authority다.\n"
        "- test1/label/test2/held-out 접근은 모두 0이다.\n"
    )
    report_path = root / OVERLAP_REPORT
    if report_path.exists() and report_path.read_text(encoding="utf-8") != report:
        raise ReportingFinalizationError(f"OUTPUT_MISMATCH:{report_path.name}")
    if not report_path.exists():
        report_path.write_text(report, encoding="utf-8", newline="\n")

    return {
        "status": "PASS",
        "overlap_r2_hash": overlap_r2["audit_hash"],
        "attention_receipt_hash": attention_receipt["receipt_hash"],
        "result_binding_receipt_hash": result_binding["receipt_hash"],
        "scientific_values_recomputed": False,
        "test1_accesses": 0,
        "test2_accesses": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(
        json.dumps(
            finalize(args.root.resolve(strict=True)),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
