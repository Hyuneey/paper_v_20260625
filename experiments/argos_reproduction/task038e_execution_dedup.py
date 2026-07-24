"""Physical execution identity, private source resolution, and reuse checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from experiments.argos_reproduction.expanded_kpi_cohort import (
    sha256_file,
    sha256_json,
)
from experiments.argos_reproduction.review_parent_registry import ROOT


def runtime_hash(config: Mapping[str, Any]) -> str:
    return sha256_json(
        {
            "runtime": config["runtime"],
            "image": config["image"],
            "isolation": config["isolation"],
            "source_hashes": {
                key: config["source_hashes"][key]
                for key in (
                    "runtime_runner",
                    "container_entrypoint",
                    "containerfile",
                    "requirements",
                )
            },
        }
    )


def physical_key(
    *,
    rule_hash: str,
    detector_variant: str,
    kpi_id: str,
    direction: str,
    outer_input_hash: str,
    frozen_runtime_hash: str,
) -> dict[str, str]:
    return {
        "rule_hash": rule_hash,
        "detector_variant": detector_variant,
        "kpi_id": kpi_id,
        "direction": direction,
        "outer_input_hash": outer_input_hash,
        "runtime_hash": frozen_runtime_hash,
    }


def physical_unit_id(key: Mapping[str, str]) -> str:
    return "PHYS-" + sha256_json(key)[:24]


def rule_path(
    config: Mapping[str, Any], source_kind: str, rule_hash: str, direction: str
) -> Path:
    if source_kind == "initial":
        return (
            ROOT
            / str(config["private_roots"]["task037d"])
            / "quarantine"
            / direction.lower()
            / f"{rule_hash}.py"
        )
    if source_kind == "repaired":
        return (
            ROOT
            / str(config["private_roots"]["task038b"])
            / "repaired_rules"
            / f"{rule_hash}.py"
        )
    if source_kind == "reviewed":
        return (
            ROOT
            / str(config["private_roots"]["task038c"])
            / "reviewed_rules"
            / f"{rule_hash}.py"
        )
    raise ValueError("TASK038E_RULE_SOURCE_KIND_INVALID")


def source_kind_from_origin(origin: str) -> str:
    if origin in (
        "initial_rule",
        "repair_identity",
        "no_review_needed_initial_identity",
    ):
        return "initial"
    if origin in ("repaired_rule", "no_review_needed_repaired_identity"):
        return "repaired"
    if origin in ("reviewed_initial_rule", "reviewed_repaired_rule"):
        return "reviewed"
    raise ValueError("TASK038E_OUTPUT_ORIGIN_INVALID")


def verify_rule_source(
    config: Mapping[str, Any], source_kind: str, rule_hash: str, direction: str
) -> None:
    path = rule_path(config, source_kind, rule_hash, direction)
    if not path.is_file() or sha256_file(path) != rule_hash:
        raise ValueError("TASK038E_PRIVATE_RULE_HASH_MISMATCH")


def existing_outer_prediction_path(
    config: Mapping[str, Any], slot_id: str
) -> Path:
    return (
        ROOT
        / str(config["private_roots"]["task037e"])
        / "outer"
        / "rule_predictions"
        / slot_id
        / "replay_1"
        / "output_labels.npy"
    )


def physical_prediction_path(
    config: Mapping[str, Any], unit_id: str, replay: int = 1
) -> Path:
    return (
        ROOT
        / str(config["private_roots"]["task038e"])
        / "physical_execution_units"
        / unit_id
        / f"replay_{replay}"
        / "output_labels.npy"
    )
