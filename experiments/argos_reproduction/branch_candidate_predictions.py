"""Verify frozen prediction references for every TASK-038D branch candidate."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from experiments.argos_reproduction.branch_output_registry import (
    BranchRegistryError,
    ROOT,
)
from experiments.argos_reproduction.expanded_kpi_cohort import sha256_file
from experiments.argos_reproduction.review_parent_registry import verify_hashed_report


def initial_prediction_path(config: Mapping[str, Any], slot_id: str) -> Path:
    return (
        ROOT
        / str(config["private_roots"]["task037e"])
        / "inner"
        / "rule_predictions"
        / slot_id
        / "replay_1"
        / "output_labels.npy"
    )


def parent_prediction_path(
    config: Mapping[str, Any], slot_id: str, repaired: bool
) -> Path:
    if not repaired:
        return initial_prediction_path(config, slot_id)
    return (
        ROOT
        / str(config["private_roots"]["task038c"])
        / "parent_inner_predictions"
        / slot_id
        / "replay_1"
        / "output_labels.npy"
    )


def reviewed_prediction_path(config: Mapping[str, Any], call_id: str) -> Path:
    return (
        ROOT
        / str(config["private_roots"]["task038c"])
        / "reviewed_inner_predictions"
        / call_id
        / "replay_1"
        / "output_labels.npy"
    )


def detector_prediction_path(
    config: Mapping[str, Any], variant: str, kpi_id: str
) -> Path:
    return (
        ROOT
        / str(config["private_roots"]["task037b"])
        / "detectors"
        / variant
        / kpi_id
        / "20260723"
        / "predictions"
        / "inner_prediction.npy"
    )


def label_path(config: Mapping[str, Any], kpi_id: str) -> Path:
    return (
        ROOT
        / str(config["private_roots"]["task035b"])
        / "inner"
        / "per_kpi_labels"
        / f"{kpi_id}.npy"
    )


def load_binary(path: Path) -> np.ndarray:
    value = np.asarray(np.load(path, allow_pickle=False))
    if (
        value.ndim != 1
        or not np.all(np.isfinite(value))
        or not np.all(np.isin(value, (0, 1)))
    ):
        raise BranchRegistryError("TASK038D_BINARY_PREDICTION_INVALID")
    return value.astype(np.int8, copy=True)


def _maps(config: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    sources = config["sources"]
    hashes = config["source_hashes"]
    initial = verify_hashed_report(
        ROOT / str(sources["task037e_inner_predictions"]),
        str(hashes["task037e_inner_predictions"]),
    )
    parents = verify_hashed_report(
        ROOT / str(sources["task038c_parent_predictions"]),
        str(hashes["task038c_parent_predictions"]),
    )
    reviewed = verify_hashed_report(
        ROOT / str(sources["task038c_reviewed_predictions"]),
        str(hashes["task038c_reviewed_predictions"]),
    )
    return (
        {row["slot_id"]: row for row in initial["records"]},
        {
            (row["branch_id"], row["initial_slot_id"]): row
            for row in parents["records"]
        },
        {
            (row["branch_id"], row["initial_slot_id"]): row
            for row in reviewed["records"]
        },
    )


def candidate_prediction_reference(
    config: Mapping[str, Any],
    candidate: Mapping[str, Any],
    maps: tuple[dict[str, Any], ...] | None = None,
) -> tuple[dict[str, Any], Path]:
    initial, parents, reviewed = maps or _maps(config)
    branch = candidate["branch_id"]
    slot = candidate["initial_slot_id"]
    origin = candidate["output_origin"]
    if origin in ("initial_rule", "repair_identity"):
        source = initial[slot]
        path = initial_prediction_path(config, slot)
        expected_hash = source["inner_prediction_hash"]
        input_hash = source["inner_input_hash"]
        length = source["prediction_length"]
        positive = source["predicted_positive_count"]
        manifest_hash = config["source_hashes"]["task037e_inner_predictions"]
        source_name = "TASK037E_initial"
    elif origin in (
        "repaired_rule",
        "no_review_needed_initial_identity",
        "no_review_needed_repaired_identity",
    ):
        source = parents[(branch if branch in ("A2", "A3") else "A3", slot)]
        repaired = origin in ("repaired_rule", "no_review_needed_repaired_identity")
        path = parent_prediction_path(config, slot, repaired)
        expected_hash = source["parent_prediction_hash"]
        input_hash = source["inner_input_hash"]
        length = source["prediction_length"]
        positive = source["predicted_positive_count"]
        manifest_hash = config["source_hashes"]["task038c_parent_predictions"]
        source_name = "TASK038C_parent"
    else:
        source = reviewed[(branch, slot)]
        call_id = candidate["Review_call_slot_id_or_null"]
        path = reviewed_prediction_path(config, call_id)
        expected_hash = source["reviewed_prediction_hash"]
        input_hash = source["inner_input_hash"]
        length = source["prediction_length"]
        positive = source["predicted_positive_count"]
        manifest_hash = config["source_hashes"]["task038c_reviewed_predictions"]
        source_name = "TASK038C_reviewed"
    if source.get("reviewed_rule_hash", source.get("parent_rule_hash", source.get("rule_sha256"))) != candidate["output_rule_hash"]:
        raise BranchRegistryError("TASK038D_RULE_PREDICTION_LINEAGE_MISMATCH")
    if not path.is_file() or sha256_file(path) != expected_hash:
        raise BranchRegistryError("TASK038D_PREDICTION_RECOVERY_REQUIRED_OR_MISMATCH")
    array = load_binary(path)
    if len(array) != int(length) or int(np.sum(array)) != int(positive):
        raise BranchRegistryError("TASK038D_PREDICTION_CONTRACT_MISMATCH")
    return (
        {
            "branch_id": branch,
            "initial_slot_id": slot,
            "detector_variant": candidate["detector_variant"],
            "kpi_id": candidate["kpi_id"],
            "direction": candidate["direction"],
            "output_origin": origin,
            "output_rule_hash": candidate["output_rule_hash"],
            "inner_input_hash": input_hash,
            "inner_prediction_hash": expected_hash,
            "prediction_length": length,
            "predicted_positive_count": positive,
            "prediction_source": source_name,
            "expected_manifest_hash": manifest_hash,
            "hash_verified": True,
        },
        path,
    )


def verify_detector_references(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    manifest = verify_hashed_report(
        ROOT / str(config["sources"]["task037b_detector_manifest"]),
        str(config["source_hashes"]["task037b_detector_manifest"]),
    )
    threshold = verify_hashed_report(
        ROOT / str(config["sources"]["task037b_threshold_freeze"]),
        str(config["source_hashes"]["task037b_threshold_freeze"]),
    )
    threshold_by_key = {
        (row["detector_variant"], row["kpi_id"]): row for row in threshold["records"]
    }
    records: list[dict[str, Any]] = []
    for row in manifest["records"]:
        key = (row["detector_variant"], row["kpi_id"])
        frozen = threshold_by_key[key]
        path = detector_prediction_path(config, *key)
        if not path.is_file() or sha256_file(path) != row["inner_prediction_hash"]:
            raise BranchRegistryError("TASK038D_DETECTOR_PREDICTION_HASH_MISMATCH")
        records.append(
            {
                "detector_variant": key[0],
                "kpi_id": key[1],
                "detector_prediction_hash": row["inner_prediction_hash"],
                "inner_label_hash": frozen["inner_label_hash"],
                "threshold_hash": frozen["threshold_record_hash"],
                "checkpoint_hash": row["checkpoint_hash"],
                "split_manifest_hash": row["split_manifest_hash"],
                "hash_verified": True,
            }
        )
    if len(records) != 20:
        raise BranchRegistryError("TASK038D_DETECTOR_REFERENCE_COUNT_MISMATCH")
    return records


def verify_label_hash(path: Path, expected: str) -> np.ndarray:
    value = load_binary(path)
    if hashlib.sha256(value.tobytes()).hexdigest() != expected:
        raise BranchRegistryError("TASK038D_INNER_LABEL_HASH_MISMATCH")
    return value
