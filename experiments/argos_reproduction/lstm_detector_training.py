"""Commit-A generation/inner execution and freeze for TASK-037B."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Mapping

import numpy as np

REPO_ROOT_BOOTSTRAP = Path(__file__).resolve().parents[2]
if str(REPO_ROOT_BOOTSTRAP) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_BOOTSTRAP))

from experiments.argos_reproduction.detector_error_segments import (
    build_error_segments,
    private_segment_manifest,
    segment_counts,
    segments_by_category,
)
from experiments.argos_reproduction.expanded_kpi_cohort import (
    REPO_ROOT,
    git_clean_commit,
    read_json,
    sha256_file,
    sha256_json,
    write_json,
)
from experiments.argos_reproduction.kpi_detector_split_guard import (
    load_frozen_splits,
    load_split_labels_after_freeze,
    materialize_split_values,
)
from experiments.argos_reproduction.lstm_detector_artifacts import (
    config_hash,
    ensure_report_safe,
    environment_hash,
    private_unit_root,
    save_binary_prediction,
    write_hashed_report,
)
from experiments.argos_reproduction.lstm_detector_scoring import (
    exact_replay,
    inspect_frozen_image,
    load_aligned_score,
    score_execution_unit,
    train_execution_unit,
)
from experiments.argos_reproduction.lstm_detector_threshold import (
    select_inner_threshold,
)


class DetectorTrainingError(RuntimeError):
    pass


def _verify_report(path: Path) -> dict[str, Any]:
    report = read_json(path)
    subject = dict(report)
    expected = subject.pop("report_hash", None)
    if expected != sha256_json(subject):
        raise DetectorTrainingError("TASK037B_LINEAGE_REPORT_HASH_MISMATCH")
    return report


def verify_task037a_lineage(config: Mapping[str, Any]) -> dict[str, Any]:
    required = str(config["lineage"]["task037a_commit"])
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", required, "origin/main"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if ancestor.returncode != 0:
        raise DetectorTrainingError("TASK037B_MISSING_TASK037A_ORIGIN_LINEAGE")
    readiness = _verify_report(REPO_ROOT / str(config["sources"]["task037a_readiness"]))
    source = _verify_report(REPO_ROOT / str(config["sources"]["task037a_source_alignment"]))
    environment = _verify_report(REPO_ROOT / str(config["sources"]["task037a_environment"]))
    smoke = _verify_report(REPO_ROOT / str(config["sources"]["task037a_smoke"]))
    if readiness["status"] != "unresolved_variant_ambiguity_with_dual_arm_freeze":
        raise DetectorTrainingError("TASK037B_TASK037A_STATUS_INVALID")
    if source["easytsad"]["source_commit"] != config["lineage"]["easytsad_commit"]:
        raise DetectorTrainingError("TASK037B_EASYTSAD_COMMIT_MISMATCH")
    for relative, expected in config["source_file_hashes"].items():
        if sha256_file(REPO_ROOT / "external/easytsad" / relative) != expected:
            raise DetectorTrainingError("TASK037B_EASYTSAD_SOURCE_HASH_MISMATCH")
    if environment["status"] != "passed" or smoke["status"] != "passed":
        raise DetectorTrainingError("TASK037B_TASK037A_PREFLIGHT_NOT_PASSED")
    if tuple(item["variant"] for item in smoke["variants"]) != ("LSTMADalpha", "LSTMADbeta"):
        raise DetectorTrainingError("TASK037B_SMOKE_VARIANTS_INVALID")
    if config["split_policy"]["training_label_policy"] != "contaminated_training":
        raise DetectorTrainingError("TASK037B_TRAINING_POLICY_INVALID")
    return {
        "task037a_commit": required,
        "readiness_report_hash": readiness["report_hash"],
        "source_report_hash": source["report_hash"],
        "environment_report_hash": environment["report_hash"],
        "smoke_report_hash": smoke["report_hash"],
    }


def _require_units(config: Mapping[str, Any]) -> tuple[str, ...]:
    variants = tuple(item["detector_id"] for item in config["detector_arms"])
    if variants != ("LSTMADalpha", "LSTMADbeta"):
        raise DetectorTrainingError("TASK037B_EXACT_DUAL_ARM_REQUIRED")
    if config["execution"].get("variant_selection") is not False:
        raise DetectorTrainingError("TASK037B_VARIANT_SELECTION_PROHIBITED")
    if tuple(config["execution"]["seeds"]) != (20260723,):
        raise DetectorTrainingError("TASK037B_SEED_FREEZE_INVALID")
    return variants


def _score_pair(
    config: Mapping[str, Any],
    image: Mapping[str, Any],
    *,
    kpi_id: str,
    variant: str,
    split: str,
    values_path: Path,
    unit_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    first = score_execution_unit(
        config, image, kpi_id=kpi_id, variant=variant, split=split, replay=1,
        values_path=values_path, unit_root=unit_root,
    )
    second = score_execution_unit(
        config, image, kpi_id=kpi_id, variant=variant, split=split, replay=2,
        values_path=values_path, unit_root=unit_root,
    )
    if first.get("status") != "scored" or second.get("status") != "scored":
        raise DetectorTrainingError(f"TASK037B_{split.upper()}_SCORE_FAILED")
    if not exact_replay(first, second):
        raise DetectorTrainingError("TASK037B_DETERMINISTIC_INFERENCE_FAILURE")
    return first, second


def _score_summary(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: result[key]
        for key in (
            "input_count", "raw_score_count", "aligned_score_count", "missing_prefix_count",
            "alignment_policy", "aligned_score_sha256", "score_min", "score_max",
            "score_mean", "score_std", "input_hash",
        )
    }


def run_fit_and_inner(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    implementation_commit = git_clean_commit()
    lineage = verify_task037a_lineage(config)
    variants = _require_units(config)
    frozen_splits = load_frozen_splits(config)
    image = inspect_frozen_image(config)
    seed = int(config["execution"]["seeds"][0])
    training_rows: list[dict[str, Any]] = []
    threshold_rows: list[dict[str, Any]] = []
    segment_rows: list[dict[str, Any]] = []
    artifact_rows: list[dict[str, Any]] = []
    compatibility: dict[str, dict[str, dict[str, list[list[int]]]]] = {
        variant: {"FN": {}, "FP": {}} for variant in variants
    }
    for variant in variants:
        for frozen in frozen_splits:
            unit_root = private_unit_root(config, variant, frozen.kpi_id, seed)
            generation_values = unit_root / "inputs/generation.npy"
            inner_values = unit_root / "inputs/inner.npy"
            generation_meta = materialize_split_values(
                config, frozen, "generation", generation_values
            )
            inner_meta = materialize_split_values(config, frozen, "inner", inner_values)
            trained = train_execution_unit(
                config, image, kpi_id=frozen.kpi_id, variant=variant,
                values_path=generation_values, unit_root=unit_root,
            )
            if trained.get("status") != "trained":
                raise DetectorTrainingError("TASK037B_FAILED_DETECTOR_TRAINING")
            generation_first, _ = _score_pair(
                config, image, kpi_id=frozen.kpi_id, variant=variant,
                split="generation", values_path=generation_values, unit_root=unit_root,
            )
            inner_first, _ = _score_pair(
                config, image, kpi_id=frozen.kpi_id, variant=variant,
                split="inner", values_path=inner_values, unit_root=unit_root,
            )
            generation_scores = load_aligned_score(unit_root, "generation")
            inner_scores = load_aligned_score(unit_root, "inner")
            inner_freeze = {
                "split": "inner",
                "kpi_id": frozen.kpi_id,
                "variant": variant,
                "score_hash": inner_first["aligned_score_sha256"],
                "prediction_frozen_before_labels": True,
            }
            inner_labels = load_split_labels_after_freeze(
                config, frozen, "inner", prediction_freeze=inner_freeze
            )
            threshold = select_inner_threshold(inner_scores, inner_labels)
            threshold.update(
                {
                    "detector_variant": variant,
                    "kpi_id": frozen.kpi_id,
                    "seed": seed,
                    "checkpoint_hash": trained["checkpoint_sha256"],
                    "inner_score_hash": inner_first["aligned_score_sha256"],
                    "inner_label_hash": __import__("hashlib").sha256(inner_labels.tobytes()).hexdigest(),
                    "labels_loaded_after_score_freeze": True,
                }
            )
            threshold_hash = sha256_json(threshold)
            threshold["threshold_record_hash"] = threshold_hash
            threshold_path = unit_root / "threshold/inner_threshold.private.json"
            write_json(threshold_path, threshold)
            generation_prediction_path = unit_root / "predictions/generation_prediction.npy"
            inner_prediction_path = unit_root / "predictions/inner_prediction.npy"
            generation_prediction_meta = save_binary_prediction(
                generation_scores, threshold["selected_threshold"], generation_prediction_path
            )
            inner_prediction_meta = save_binary_prediction(
                inner_scores, threshold["selected_threshold"], inner_prediction_path
            )
            generation_prediction = np.asarray(
                np.load(generation_prediction_path, allow_pickle=False), dtype=np.int8
            )
            generation_freeze = {
                "split": "generation",
                "kpi_id": frozen.kpi_id,
                "variant": variant,
                "prediction_hash": generation_prediction_meta["prediction_hash"],
                "prediction_frozen_before_labels": True,
            }
            generation_labels = load_split_labels_after_freeze(
                config, frozen, "generation", prediction_freeze=generation_freeze
            )
            grouped = segments_by_category(
                build_error_segments(generation_labels.tolist(), generation_prediction.tolist())
            )
            segment_manifest = private_segment_manifest(
                grouped,
                kpi_id=frozen.kpi_id,
                variant=variant,
                prediction_hash=generation_prediction_meta["prediction_hash"],
                threshold_hash=threshold_hash,
            )
            segment_path = unit_root / "error_segments/generation.private.json"
            write_json(segment_path, segment_manifest)
            counts = segment_counts(grouped)
            compatibility[variant]["FN"][frozen.kpi_id] = [list(item) for item in grouped["FN"]]
            compatibility[variant]["FP"][frozen.kpi_id] = [list(item) for item in grouped["FP"]]
            compatibility_root = (
                REPO_ROOT / str(config["private_root"]) / "argos_compatibility" / variant
            )
            train_labels = compatibility_root / "TrainLabels" / f"{frozen.kpi_id}.npy"
            train_labels.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(generation_prediction_path, train_labels)
            training_rows.append(
                {
                    "detector_variant": variant,
                    "kpi_id": frozen.kpi_id,
                    "seed": seed,
                    "terminal_status": "trained_and_scored",
                    "checkpoint_hash": trained["checkpoint_sha256"],
                    "normalization_hash": trained["normalization_sha256"],
                    "generation": _score_summary(generation_first),
                    "inner": _score_summary(inner_first),
                    "generation_input_count": generation_meta["input_count"],
                    "inner_input_count": inner_meta["input_count"],
                    "training_label_policy": "contaminated_training",
                    "filtered_generation_count": 0,
                    "retained_generation_count": generation_meta["input_count"],
                    "labels_mounted": False,
                    "deterministic_generation_replay": True,
                    "deterministic_inner_replay": True,
                }
            )
            threshold_rows.append(threshold)
            segment_rows.append(
                {
                    "detector_variant": variant,
                    "kpi_id": frozen.kpi_id,
                    **{
                        f"{category}_{field}": value
                        for category, values in counts.items()
                        for field, value in values.items()
                    },
                    "segment_manifest_hash": segment_manifest["segment_manifest_hash"],
                    "interval_semantics": "half_open",
                }
            )
            artifact_rows.append(
                {
                    "detector_variant": variant,
                    "kpi_id": frozen.kpi_id,
                    "seed": seed,
                    "split_manifest_hash": frozen.split_manifest_hash,
                    "checkpoint_hash": trained["checkpoint_sha256"],
                    "normalization_hash": trained["normalization_sha256"],
                    "generation_score_hash": generation_first["aligned_score_sha256"],
                    "inner_score_hash": inner_first["aligned_score_sha256"],
                    "generation_prediction_hash": generation_prediction_meta["prediction_hash"],
                    "inner_prediction_hash": inner_prediction_meta["prediction_hash"],
                    "threshold": threshold["selected_threshold"],
                    "threshold_protocol_hash": threshold["threshold_protocol_hash"],
                    "incorrect_indices_generation_hash": segment_manifest["segment_manifest_hash"],
                    "outer_score_hash": None,
                    "outer_prediction_hash": None,
                    "artifact_status": "inner_frozen_outer_pending",
                }
            )
    for variant in variants:
        target = (
            REPO_ROOT / str(config["private_root"]) / "argos_compatibility" /
            variant / "IncorrectIndices/train.json"
        )
        write_json(target, compatibility[variant])
        if (target.parent.parent / "TestLabels").exists():
            raise DetectorTrainingError("TASK037B_TESTLABELS_CREATION_PROHIBITED")
    common = {
        "schema_version": "1.0",
        "task_id": "TASK-037B",
        "execution_code_commit": implementation_commit,
        "task037a_lineage": lineage,
        "image": image,
        "detector_variants": list(variants),
        "variant_selection_performed": False,
        "test_values_accessed": False,
        "test_labels_accessed": False,
        "provider_calls": 0,
        "fusion_performed": False,
    }
    training_report = write_hashed_report(
        REPO_ROOT / str(config["reports"]["training"]),
        {
            **common,
            "artifact_type": "detector_training_report",
            "status": "checkpoint_and_inner_scores_frozen",
            "execution_unit_count": len(training_rows),
            "units": training_rows,
        },
    )
    threshold_report = write_hashed_report(
        REPO_ROOT / str(config["reports"]["threshold_freeze"]),
        {
            **common,
            "artifact_type": "inner_threshold_freeze",
            "status": "frozen",
            "selection_split": "inner",
            "outer_metrics_seen": False,
            "variant_selection_performed": False,
            "records": threshold_rows,
        },
    )
    segment_report = write_hashed_report(
        REPO_ROOT / str(config["reports"]["error_segments"]),
        {
            **common,
            "artifact_type": "generation_error_segment_report",
            "status": "complete",
            "rule_generation_performed": False,
            "raw_positions_tracked": False,
            "records": segment_rows,
        },
    )
    artifact_report = write_hashed_report(
        REPO_ROOT / str(config["reports"]["artifact_manifest"]),
        {
            **common,
            "artifact_type": "detector_artifact_manifest",
            "status": "inner_frozen_outer_pending",
            "config_hash": config_hash(config),
            "environment_hash": environment_hash(config),
            "records": artifact_rows,
            "raw_artifacts_tracked": False,
        },
    )
    for report in (training_report, threshold_report, segment_report, artifact_report):
        ensure_report_safe(report)
    receipt = {
        "schema_version": "1.0",
        "task_id": "TASK-037B",
        "stage": "inner_freeze",
        "implementation_commit": implementation_commit,
        "training_report_hash": training_report["report_hash"],
        "threshold_report_hash": threshold_report["report_hash"],
        "segment_report_hash": segment_report["report_hash"],
        "artifact_report_hash": artifact_report["report_hash"],
        "outer_values_accessed": False,
        "outer_labels_accessed": False,
        "test_accessed": False,
    }
    receipt["receipt_hash"] = sha256_json(receipt)
    write_json(REPO_ROOT / str(config["private_root"]) / "manifests/inner_freeze.private.json", receipt)
    return {
        "status": "inner_frozen_outer_pending",
        "execution_units": len(training_rows),
        "training_report_hash": training_report["report_hash"],
        "threshold_report_hash": threshold_report["report_hash"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", default="configs/argos_reproduction/task037b_dual_lstm_detector_validation.json"
    )
    args = parser.parse_args()
    result = run_fit_and_inner((REPO_ROOT / args.config).resolve())
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
