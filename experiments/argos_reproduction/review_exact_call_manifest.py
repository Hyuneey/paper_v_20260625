"""Freeze exact TASK-038C Review requests after trigger computation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.expanded_kpi_cohort import (
    read_json,
    sha256_json,
    write_json,
)
from experiments.argos_reproduction.review_parent_registry import (
    parent_rule_path,
    verify_hashed_report,
    write_hashed_report,
)
from experiments.argos_reproduction.review_regression_samples import (
    RegressionSample,
)
from experiments.argos_reproduction.safe_review_adapter import (
    build_review_request,
)


def _samples(payload: dict[str, Any]) -> tuple[RegressionSample, ...]:
    return tuple(
        RegressionSample(
            start=int(row["start"]),
            end=int(row["end"]),
            values=tuple(float(value) for value in row["values"]),
            labels=tuple(int(value) for value in row["labels"]),
            detector_predictions=tuple(
                int(value) for value in row["detector_predictions"]
            ),
            rule_predictions=tuple(int(value) for value in row["rule_predictions"]),
            combined_predictions=tuple(
                int(value) for value in row["combined_predictions"]
            ),
        )
        for row in payload["windows"]
    )


def freeze_exact_review_manifest(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    trigger = verify_hashed_report(ROOT / str(config["reports"]["trigger"]))
    required = [
        row for row in trigger["records"] if row["review_trigger"] == "review_required"
    ]
    required.sort(
        key=lambda row: (
            0 if row["branch_id"] == "A2" else 1,
            row["initial_slot_id"],
        )
    )
    private_root = ROOT / str(config["private_roots"]["task038c"])
    slots: list[dict[str, Any]] = []
    for order, row in enumerate(required, start=1):
        branch_key = str(row["branch_key"])
        evidence_path = (
            private_root
            / "regression_evidence"
            / f"{branch_key}.private.json"
        )
        evidence = read_json(evidence_path)
        if evidence["evidence_hash"] != row["regression_evidence_hash"]:
            raise RuntimeError("TASK038C_REGRESSION_EVIDENCE_HASH_MISMATCH")
        rule_path = parent_rule_path(config, row)
        request = build_review_request(
            branch_id=str(row["branch_id"]),
            initial_slot_id=str(row["initial_slot_id"]),
            current_rule_source=rule_path.read_text(encoding="utf-8"),
            current_rule_hash=str(row["parent_rule_hash"]),
            combined_metrics=row["parent_combined_metrics"],
            detector_metrics=row["detector_metrics"],
            regression_samples=_samples(evidence),
        )
        request_payload = {
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ]
        }
        prompt_payload_hash = sha256_json(request_payload)
        branch_request_hash = sha256_json(
            {
                "branch_id": row["branch_id"],
                "review_call_slot_id": request.request_id,
                "prompt_payload_hash": prompt_payload_hash,
            }
        )
        request_dir = private_root / "requests" / request.request_id
        write_json(request_dir / "complete_request.json", request_payload)
        write_json(request_dir / "request.private.json", request.private_dict())
        slots.append(
            {
                "review_call_slot_id": request.request_id,
                "branch_id": row["branch_id"],
                "initial_slot_id": row["initial_slot_id"],
                "detector_variant": row["detector_variant"],
                "kpi_id": row["kpi_id"],
                "direction": row["direction"],
                "parent_type": row["parent_type"],
                "parent_rule_hash": row["parent_rule_hash"],
                "parent_prediction_hash": row["parent_prediction_hash"],
                "detector_prediction_hash": row["detector_prediction_hash"],
                "inner_label_hash": row["inner_label_hash"],
                "parent_combined_prediction_hash": row[
                    "parent_combined_prediction_hash"
                ],
                "detector_point_F1": row["detector_metrics"]["point_f1"],
                "parent_combined_point_F1": row["parent_combined_metrics"][
                    "point_f1"
                ],
                "review_trigger": row["review_trigger"],
                "regression_window_count": row["regression_window_count"],
                "regression_evidence_hash": row["regression_evidence_hash"],
                "system_prompt_hash": request.system_prompt_hash,
                "prompt_payload_hash": prompt_payload_hash,
                "branch_request_hash": branch_request_hash,
                "max_output_tokens": config["provider"]["max_output_tokens"],
                "request_order": order,
            }
        )
    if len({row["review_call_slot_id"] for row in slots}) != len(slots):
        raise RuntimeError("TASK038C_DUPLICATE_REVIEW_CALL_SLOT")
    if len({row["branch_request_hash"] for row in slots}) != len(slots):
        raise RuntimeError("TASK038C_DUPLICATE_BRANCH_REQUEST_HASH")
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038C",
        "artifact_type": "review_call_manifest",
        "status": "exact_call_manifest_frozen",
        "trigger_report_hash": trigger["report_hash"],
        "total_branch_parents": trigger["total_branch_parents"],
        "review_required_count": len(slots),
        "no_review_needed_count": trigger["no_review_needed_count"],
        "A2_nonapplicable_count": config["counts"]["A2_nonapplicable"],
        "maximum_calls": config["counts"]["logical_executable_parents"],
        "duplicate_review_call_slot_ids": 0,
        "duplicate_branch_request_hashes": 0,
        "automatic_retry_slots": 0,
        "replacement_slots": 0,
        "request_order": config["review_policy"]["request_order"],
        "slots": slots,
    }
    report = write_hashed_report(
        ROOT / str(config["reports"]["call_manifest"]), report
    )
    approval_path = ROOT / str(config["provider"]["approval_path"])
    approval = read_json(approval_path)
    exact = len(slots)
    approval.update(
        {
            "maximum_requests": exact,
            "maximum_total_declared_input_tokens": exact * 20000,
            "maximum_total_declared_output_tokens": exact * 6000,
            "exact_count_frozen": True,
            "call_manifest_hash": report["report_hash"],
        }
    )
    write_json(approval_path, approval)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038c_review_inner_experiment.json",
    )
    args = parser.parse_args()
    report = freeze_exact_review_manifest((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "review_required": report["review_required_count"],
                "no_review_needed": report["no_review_needed_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
