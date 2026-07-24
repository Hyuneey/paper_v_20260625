"""Freeze exact TASK-038B Repair requests after failure replay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.expanded_kpi_cohort import (
    read_json,
    sha256_file,
    sha256_json,
    write_json,
)
from experiments.argos_reproduction.repair_failure_replay import (
    load_repair_population,
    verify_report_hash,
)
from experiments.argos_reproduction.safe_repair_adapter import build_repair_request


class RepairCallManifestError(RuntimeError):
    """Raised when the exact Repair call population is not frozen."""


def _runtime_error_text(private_error: Mapping[str, Any]) -> str:
    allowed = {
        "exception_type": private_error["exception_type"],
        "normalized_message": private_error["normalized_message"],
        "rule_line_number_if_available": private_error[
            "rule_line_number_if_available"
        ],
        "failure_stage": private_error["failure_stage"],
        "expected_output_contract": private_error["expected_output_contract"],
    }
    return json.dumps(
        allowed,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def build_provider_request(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    }


def freeze_repair_call_manifest(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    population = {
        item["initial_slot_id"]: item for item in load_repair_population(config)
    }
    replay_path = ROOT / str(config["reports"]["failure_replay"])
    replay_raw = read_json(replay_path)
    replay = verify_report_hash(replay_path, str(replay_raw["report_hash"]))
    if (
        replay["frozen_repair_population"] != 13
        or not replay["all_initial_failures_replayed"]
    ):
        raise RepairCallManifestError("TASK038B_REPLAY_NOT_COMPLETE")
    source_root = ROOT / str(config["sources"]["task037d_private_root"])
    private_root = ROOT / str(config["private_root"])
    records: list[dict[str, Any]] = []
    eligible = sorted(
        (
            item
            for item in replay["records"]
            if item["failure_reproducible"] is True
        ),
        key=lambda item: item["initial_slot_id"],
    )
    for request_order, replay_record in enumerate(eligible, start=1):
        slot_id = replay_record["initial_slot_id"]
        initial = population[slot_id]
        fixture = replay_record["failing_fixture"]
        rule_path = (
            source_root
            / "quarantine"
            / str(initial["direction"]).lower()
            / f"{initial['initial_rule_hash']}.py"
        )
        if sha256_file(rule_path) != initial["initial_rule_hash"]:
            raise RepairCallManifestError("TASK038B_INITIAL_RULE_HASH_MISMATCH")
        replay_root = private_root / "failure_replay" / slot_id / fixture
        error = read_json(replay_root / "sanitized_error.private.json")
        if sha256_json(error) != replay_record["sanitized_error_hash"]:
            raise RepairCallManifestError("TASK038B_SANITIZED_ERROR_HASH_MISMATCH")
        values_path = replay_root / "input_values.npy"
        if sha256_file(values_path) != replay_record["failing_input_hash"]:
            raise RepairCallManifestError("TASK038B_FAILING_INPUT_HASH_MISMATCH")
        values = np.asarray(
            np.load(values_path, allow_pickle=False), dtype=np.float64
        ).reshape(-1)
        request = build_repair_request(
            initial_slot_id=slot_id,
            current_rule_source=rule_path.read_text(encoding="utf-8"),
            current_rule_hash=str(initial["initial_rule_hash"]),
            runtime_error=_runtime_error_text(error),
            failing_values=values.tolist(),
            failing_artifact_hash=str(replay_record["failing_input_hash"]),
            split="generation",
        )
        provider_request = build_provider_request(
            request.system_prompt, request.user_prompt
        )
        complete_hash = sha256_json(provider_request)
        request_dir = private_root / "requests" / f"REPAIR-{slot_id}"
        write_json(request_dir / "complete_request.json", provider_request)
        records.append(
            {
                "repair_call_slot_id": f"REPAIR-{slot_id}",
                "initial_slot_id": slot_id,
                "initial_rule_hash": initial["initial_rule_hash"],
                "detector_variant": initial["detector_variant"],
                "kpi_id": initial["kpi_id"],
                "direction": initial["direction"],
                "initial_failure_status": initial["initial_runtime_status"],
                "failing_fixture": fixture,
                "target_chunk_hash": initial["target_chunk_hash"],
                "contrast_chunk_hash": initial["contrast_chunk_hash"],
                "failing_input_hash": replay_record["failing_input_hash"],
                "sanitized_error_category": replay_record[
                    "sanitized_error_category"
                ],
                "sanitized_error_hash": replay_record["sanitized_error_hash"],
                "system_prompt_hash": request.system_prompt_hash,
                "user_prompt_hash": request.user_prompt_hash,
                "complete_request_hash": complete_hash,
                "max_output_tokens": int(config["provider"]["max_output_tokens"]),
                "request_order": request_order,
                "repair_reuse_key": initial["repair_reuse_key"],
            }
        )
    request_hashes = [item["complete_request_hash"] for item in records]
    slot_ids = [item["initial_slot_id"] for item in records]
    if len(records) > 13:
        raise RepairCallManifestError("TASK038B_CALL_BUDGET_EXCEEDED")
    if len(set(slot_ids)) != len(slot_ids):
        raise RepairCallManifestError("TASK038B_DUPLICATE_INITIAL_SLOT")
    if len(set(request_hashes)) != len(request_hashes):
        raise RepairCallManifestError("TASK038B_DUPLICATE_REQUEST_HASH")
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038B",
        "artifact_type": "repair_call_manifest",
        "status": "exact_call_manifest_frozen",
        "maximum_call_count": 13,
        "authorized_call_count": len(records),
        "duplicate_initial_slot_ids": 0,
        "duplicate_request_hashes": 0,
        "retry_slots": 0,
        "replacement_slots": 0,
        "review_slots": 0,
        "call_order": "initial_slot_id_lexicographic",
        "failure_replay_hash": replay["report_hash"],
        "slots": records,
    }
    report["report_hash"] = sha256_json(report)
    write_json(ROOT / str(config["reports"]["call_manifest"]), report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038b_repair_execution.json",
    )
    args = parser.parse_args()
    report = freeze_repair_call_manifest((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "authorized_call_count": report["authorized_call_count"],
                "status": report["status"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
