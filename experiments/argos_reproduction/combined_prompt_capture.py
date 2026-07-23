"""Freeze TASK-037D target/contrast pairs and exact pinned combined prompts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.detector_error_support_audit import (
    audit_support,
    load_generation_cells,
)
from experiments.argos_reproduction.error_conditioned_target_selection import (
    enumerate_distinct_targets,
    evenly_distributed_targets,
    sanitized_target,
    save_private_chunk,
)
from experiments.argos_reproduction.error_contrast_matching import (
    contrast_pool,
    match_contrast,
    matching_policy_hash,
)
from experiments.argos_reproduction.expanded_kpi_cohort import (
    read_json,
    sha256_file,
    sha256_json,
    write_json,
)
from experiments.argos_reproduction.prompt_capture import (
    extract_string_constant,
    serialize_chunk_like_argos,
)


class CombinedPromptCaptureError(RuntimeError):
    """Raised when the pinned combined prompt cannot be frozen exactly."""


TEMPLATE_NAMES = {
    "FN": "DETECTION_AGENT_V3_COMBINED_FN_PROMPT_TEMPLATE",
    "FP": "DETECTION_AGENT_V3_COMBINED_FP_PROMPT_TEMPLATE",
}
CONTRAST_HEADERS = {
    "FN": "##### NORMAL DATA 0 \n",
    "FP": "##### ABNORMAL DATA 0\n",
}


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def verify_pinned_sources(config: Mapping[str, Any]) -> None:
    for relative, expected in config["pinned_source_hashes"].items():
        if sha256_file(ROOT / relative) != expected:
            raise CombinedPromptCaptureError("TASK037D_PINNED_SOURCE_HASH_MISMATCH")


def combined_system_prompt(
    config: Mapping[str, Any], direction: str
) -> dict[str, str]:
    if direction not in TEMPLATE_NAMES:
        raise CombinedPromptCaptureError("TASK037D_DIRECTION_INVALID")
    source = ROOT / str(config["sources"]["prompt_source"])
    template = extract_string_constant(source, TEMPLATE_NAMES[direction])
    prompt = template.format(chunk_size=int(config["design"]["chunk_size"])).strip()
    return {
        "template_name": TEMPLATE_NAMES[direction],
        "template_hash": _sha256_text(template),
        "system_prompt": prompt,
        "system_prompt_hash": _sha256_text(prompt),
    }


def _rows(chunk: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {"value": float(value), "label": int(label), "index": int(index)}
        for value, label, index in zip(
            chunk["values"], chunk["labels"], chunk["indices"]
        )
    ]


def build_combined_request(
    config: Mapping[str, Any],
    direction: str,
    target: Mapping[str, Any],
    contrast: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, str]]:
    prompt = combined_system_prompt(config, direction)
    target_text = serialize_chunk_like_argos(_rows(target))
    contrast_text = serialize_chunk_like_argos(_rows(contrast))
    user = (
        "##### DATA 0\n"
        + target_text
        + "\n"
        + CONTRAST_HEADERS[direction]
        + contrast_text
        + "\n"
    )
    request = {
        "messages": [
            {"role": "system", "content": prompt["system_prompt"]},
            {"role": "user", "content": user},
        ]
    }
    return request, {
        "system_prompt_template_hash": prompt["template_hash"],
        "system_prompt_hash": prompt["system_prompt_hash"],
        "user_prompt_hash": _sha256_text(user),
        "complete_request_hash": sha256_json(request),
    }


def prepare_error_conditioned_requests(config_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    config = read_json(config_path)
    verify_pinned_sources(config)
    base_support = audit_support(config_path)
    support_by_key = {
        (row["detector_variant"], row["kpi_id"], row["direction"]): dict(row)
        for row in base_support["cells"]
    }
    cells = load_generation_cells(config)
    private_root = ROOT / str(config["private_root"])
    chunk_size = int(config["design"]["chunk_size"])
    maximum = int(config["design"]["maximum_target_chunks_per_cell"])
    target_rows: list[dict[str, Any]] = []
    slots: list[dict[str, Any]] = []
    for cell in cells:
        for direction in config["directions"]:
            key = (cell.variant, cell.kpi_id, direction)
            support = support_by_key[key]
            candidates = enumerate_distinct_targets(cell, direction, chunk_size)
            selected = evenly_distributed_targets(candidates, maximum)
            support["eligible_target_chunk_count"] = len(candidates)
            support["registered_slot_count"] = len(selected)
            if support["support_state"] == "not_applicable_zero_detector_error":
                selected = ()
            elif not selected:
                support["support_state"] = "insufficient_distinct_target_chunks"
            else:
                pool = contrast_pool(cell, direction, chunk_size)
                if not pool:
                    support["support_state"] = "insufficient_contrast_support"
                    selected = ()
                else:
                    support["support_state"] = "eligible"
            support["registered_slot_count"] = len(selected)
            for target_rank, target in enumerate(selected, start=1):
                contrast = match_contrast(target, contrast_pool(cell, direction, chunk_size))
                slot_id = (
                    f"ERRRULE-{cell.variant}-{cell.kpi_id}-{direction}-{target_rank}"
                )
                target_path = private_root / "targets/target_chunks" / f"{slot_id}.npz"
                contrast_path = private_root / "targets/contrast_chunks" / f"{slot_id}.npz"
                save_private_chunk(target_path, target)
                save_private_chunk(contrast_path, contrast)
                request, hashes = build_combined_request(config, direction, target, contrast)
                request_path = private_root / "requests" / slot_id / "complete_request.json"
                write_json(request_path, request)
                if sha256_json(read_json(request_path)) != hashes["complete_request_hash"]:
                    raise CombinedPromptCaptureError("TASK037D_REQUEST_HASH_MISMATCH")
                target_record = {
                    "slot_id": slot_id,
                    "detector_variant": cell.variant,
                    "kpi_id": cell.kpi_id,
                    "direction": direction,
                    **sanitized_target(target, target_rank),
                    "contrast_start": int(contrast["start"]),
                    "contrast_end": int(contrast["end"]),
                    "contrast_chunk_hash": str(contrast["hash"]),
                    "target_prediction_hash": cell.prediction_hash,
                    "target_segment_manifest_hash": cell.segment_manifest_hash,
                    "split_manifest_hash": cell.split_manifest_hash,
                    "generation_only": True,
                    "target_contrast_overlap": False,
                    "matching_policy_hash": matching_policy_hash(),
                }
                target_rows.append(target_record)
                slots.append(
                    {
                        **target_record,
                        **hashes,
                        "max_output_tokens": int(config["provider"]["max_output_tokens"]),
                        "previous_rule_history_present": False,
                        "repair_or_review_prompt_present": False,
                    }
                )
    enriched_support = {
        **{key: value for key, value in base_support.items() if key not in ("cells", "report_hash")},
        "cells": [support_by_key[key] for key in sorted(support_by_key)],
    }
    enriched_support["eligible_cell_count"] = sum(
        row["support_state"] == "eligible" for row in enriched_support["cells"]
    )
    enriched_support["registered_slot_count"] = len(slots)
    enriched_support["report_hash"] = sha256_json(enriched_support)
    write_json(ROOT / str(config["reports"]["support"]), enriched_support)
    target_manifest = {
        "schema_version": "1.0",
        "task_id": "TASK-037D",
        "artifact_type": "target_contrast_manifest",
        "status": "frozen",
        "chunk_size": chunk_size,
        "matching_policy_hash": matching_policy_hash(),
        "record_count": len(target_rows),
        "records": target_rows,
        "raw_chunks_tracked": False,
        "inner_accessed": False,
        "outer_accessed": False,
        "test_accessed": False,
    }
    target_manifest["report_hash"] = sha256_json(target_manifest)
    write_json(ROOT / str(config["reports"]["targets"]), target_manifest)
    request_manifest = {
        "schema_version": "1.0",
        "task_id": "TASK-037D",
        "artifact_type": "error_conditioned_request_manifest",
        "status": "frozen",
        "slot_order": [item["slot_id"] for item in slots],
        "registered_slot_count": len(slots),
        "maximum_request_upper_bound": int(
            config["design"]["maximum_total_provider_calls"]
        ),
        "provider": config["provider"]["provider"],
        "model": config["provider"]["model"],
        "slots": slots,
        "temperature_parameter_sent": False,
        "provider_seed_sent": False,
        "previous_rule_history_present": False,
        "raw_prompts_tracked": False,
    }
    request_manifest["report_hash"] = sha256_json(request_manifest)
    write_json(ROOT / str(config["reports"]["requests"]), request_manifest)
    expected = int(config["design"]["exact_frozen_slot_count"])
    if len(slots) > int(config["design"]["maximum_total_provider_calls"]):
        raise CombinedPromptCaptureError("TASK037D_REQUEST_UPPER_BOUND_EXCEEDED")
    if expected not in (0, len(slots)):
        raise CombinedPromptCaptureError("TASK037D_EXACT_SLOT_COUNT_MISMATCH")
    return target_manifest, request_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task037d_error_conditioned_rules.json",
    )
    args = parser.parse_args()
    targets, requests = prepare_error_conditioned_requests((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "target_count": targets["record_count"],
                "registered_slot_count": requests["registered_slot_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
