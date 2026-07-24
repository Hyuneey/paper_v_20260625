"""Validate the complete TASK-038C parent prediction freeze."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from experiments.argos_reproduction.review_parent_registry import (
    ROOT,
    ReviewParentRegistryError,
    prediction_path,
    verify_hashed_report,
)
from experiments.argos_reproduction.expanded_kpi_cohort import sha256_file


def verify_parent_prediction_freeze(
    config: Mapping[str, Any],
) -> dict[str, Any]:
    manifest = verify_hashed_report(
        ROOT / str(config["reports"]["parent_predictions"])
    )
    if (
        manifest["status"] != "frozen_before_inner_label_access"
        or manifest["unique_parent_rule_count"]
        != int(config["counts"]["unique_parent_rules"])
        or manifest["logical_parent_record_count"]
        != int(config["counts"]["logical_executable_parents"])
        or not manifest["all_parent_predictions_frozen_before_label_access"]
    ):
        raise ReviewParentRegistryError("TASK038C_PARENT_FREEZE_INCOMPLETE")
    for row in manifest["records"]:
        path = prediction_path(config, row)
        if (
            not path.is_file()
            or sha256_file(path) != row["parent_prediction_hash"]
        ):
            raise ReviewParentRegistryError(
                "TASK038C_PARENT_PREDICTION_HASH_MISMATCH"
            )
    return manifest
