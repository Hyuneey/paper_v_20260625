"""Private detector artifacts and sanitized tracked manifests for TASK-037B."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from experiments.argos_reproduction.detector_artifact_contract import validate_detector_manifest
from experiments.argos_reproduction.expanded_kpi_cohort import REPO_ROOT, sha256_file, sha256_json, write_json
from experiments.argos_reproduction.lstm_detector_threshold import binary_predictions


class DetectorArtifactError(RuntimeError):
    pass


def write_hashed_report(path: Path, report: dict[str, Any]) -> dict[str, Any]:
    if "report_hash" in report:
        raise DetectorArtifactError("TASK037B_REPORT_HASH_PRECLAIMED")
    report["report_hash"] = sha256_json(report)
    write_json(path, report)
    return report


def save_binary_prediction(scores: object, threshold: float, path: Path) -> dict[str, Any]:
    prediction = binary_predictions(scores, threshold)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, prediction, allow_pickle=False)
    return {
        "prediction_hash": sha256_file(path),
        "output_count": int(len(prediction)),
        "predicted_positive_count": int(np.sum(prediction)),
        "binary_domain": True,
        "finite": True,
    }


def load_binary_prediction(path: Path) -> np.ndarray:
    value = np.asarray(np.load(path, allow_pickle=False))
    if value.ndim != 1 or not np.all(np.isfinite(value)) or not np.all(np.isin(value, (0, 1))):
        raise DetectorArtifactError("TASK037B_PRIVATE_PREDICTION_INVALID")
    return value.astype(np.int8, copy=True)


def private_unit_root(config: Mapping[str, Any], variant: str, kpi_id: str, seed: int) -> Path:
    if variant not in ("LSTMADalpha", "LSTMADbeta"):
        raise DetectorArtifactError("TASK037B_VARIANT_INVALID")
    if "/" in kpi_id or "\\" in kpi_id:
        raise DetectorArtifactError("TASK037B_KPI_ID_INVALID")
    return (
        REPO_ROOT / str(config["private_root"]) / "detectors" / variant / kpi_id / str(seed)
    )


def environment_hash(config: Mapping[str, Any]) -> str:
    subject = {
        "runtime": config["runtime"],
        "image": config["image"],
        "isolation": config["isolation"],
        "easytsad_commit": config["lineage"]["easytsad_commit"],
    }
    return sha256_json(subject)


def config_hash(config: Mapping[str, Any]) -> str:
    return sha256_json(
        {
            "detector_arms": config["detector_arms"],
            "detector_configurations": config["detector_configurations"],
            "execution": config["execution"],
            "threshold": config["threshold"],
        }
    )


def build_final_manifest(
    config: Mapping[str, Any],
    *,
    variant: str,
    kpi_id: str,
    split_manifest_hash: str,
    threshold: float,
    threshold_protocol_hash: str,
    hashes: Mapping[str, str],
) -> dict[str, Any]:
    source_hashes = tuple(
        sorted((path, digest) for path, digest in config["source_file_hashes"].items())
    )
    document = {
        "detector_id": f"{variant}-{kpi_id}-{config['execution']['seeds'][0]}",
        "detector_family": "LSTMAD",
        "detector_variant": variant,
        "detector_role": "paper_aligned_family_sensitivity",
        "source_commit": config["lineage"]["easytsad_commit"],
        "source_file_hashes": source_hashes,
        "config_hash": config_hash(config),
        "environment_hash": environment_hash(config),
        "seed": int(config["execution"]["seeds"][0]),
        "kpi_id": kpi_id,
        "split_manifest_hash": split_manifest_hash,
        "checkpoint_hash": hashes["checkpoint_hash"],
        "normalization_hash": hashes["normalization_hash"],
        "generation_score_hash": hashes["generation_score_hash"],
        "inner_score_hash": hashes["inner_score_hash"],
        "outer_score_hash": hashes["outer_score_hash"],
        "generation_prediction_hash": hashes["generation_prediction_hash"],
        "inner_prediction_hash": hashes["inner_prediction_hash"],
        "outer_prediction_hash": hashes["outer_prediction_hash"],
        "threshold": float(threshold),
        "threshold_protocol_hash": threshold_protocol_hash,
        "incorrect_indices_generation_hash": hashes["incorrect_indices_generation_hash"],
        "artifact_status": "complete",
    }
    validate_detector_manifest(document)
    return document


def ensure_report_safe(value: object) -> None:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True).lower()
    prohibited = (
        "source_values", "target_values", "raw_score.npy", "best_network.pth",
        "private_argos_reproduction", "c:\\users\\", "testlabels",
    )
    if any(token in encoded for token in prohibited):
        raise DetectorArtifactError("TASK037B_TRACKED_REPORT_PRIVATE_CONTENT")


def hash_manifest_rows(rows: Sequence[Mapping[str, Any]]) -> str:
    return hashlib.sha256(
        json.dumps(list(rows), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()
