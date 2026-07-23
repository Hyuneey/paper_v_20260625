"""Fail-closed frozen prediction loader for TASK-037C."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Any, Mapping

import numpy as np

from experiments.argos_reproduction.diagnostic_binary_fusion import (
    DETECTOR_VARIANTS,
    RULE_ARMS,
    binary_vector,
)
from experiments.argos_reproduction.expanded_kpi_cohort import (
    REPO_ROOT,
    read_json,
    sha256_file,
    sha256_json,
)


class FrozenPredictionError(RuntimeError):
    """Raised when frozen lineage or private prediction integrity fails."""


@dataclass(frozen=True)
class FrozenPredictionInputs:
    kpi_ids: tuple[str, ...]
    split_hashes: Mapping[str, str]
    detector_predictions: Mapping[tuple[str, str, str], np.ndarray]
    rule_predictions: Mapping[tuple[str, str, str], np.ndarray]
    detector_hashes: Mapping[tuple[str, str, str], str]
    rule_hashes: Mapping[tuple[str, str, str], str]
    source_records: tuple[Mapping[str, Any], ...]
    inner_rule_recovery: Mapping[str, Any]


def verified_report(path: Path, expected_hash: str | None = None) -> dict[str, Any]:
    report = read_json(path)
    subject = dict(report)
    recorded = subject.pop("report_hash", None)
    if not isinstance(recorded, str) or recorded != sha256_json(subject):
        raise FrozenPredictionError("TASK037C_REPORT_SELF_HASH_MISMATCH")
    if expected_hash is not None and recorded != expected_hash:
        raise FrozenPredictionError("TASK037C_REPORT_LINEAGE_HASH_MISMATCH")
    return report


def verify_private_manifest(document: Mapping[str, Any], hash_field: str) -> None:
    subject = dict(document)
    recorded = subject.pop(hash_field, None)
    if not isinstance(recorded, str) or recorded != sha256_json(subject):
        raise FrozenPredictionError("TASK037C_PRIVATE_MANIFEST_HASH_MISMATCH")


def verify_commit_lineage(lineage: Mapping[str, str]) -> None:
    for name, commit in sorted(lineage.items()):
        if not isinstance(commit, str) or len(commit) != 40:
            raise FrozenPredictionError(f"TASK037C_COMMIT_INVALID_{name.upper()}")
        exists = subprocess.run(
            ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        if exists.returncode != 0:
            raise FrozenPredictionError(f"TASK037C_COMMIT_MISSING_{name.upper()}")
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        if ancestor.returncode != 0:
            raise FrozenPredictionError(f"TASK037C_COMMIT_NOT_ANCESTOR_{name.upper()}")


def validate_frozen_matrix(config: Mapping[str, Any]) -> None:
    matrix = config.get("matrix", {})
    if tuple(matrix.get("detector_variants", ())) != DETECTOR_VARIANTS:
        raise FrozenPredictionError("TASK037C_DETECTOR_MATRIX_CHANGED")
    if tuple(matrix.get("rule_arms", ())) != RULE_ARMS:
        raise FrozenPredictionError("TASK037C_RULE_MATRIX_CHANGED")
    if tuple(matrix.get("operators", ())) != ("fn_union_max", "fp_intersection_min"):
        raise FrozenPredictionError("TASK037C_OPERATOR_MATRIX_CHANGED")
    if int(matrix.get("fusion_arm_count", -1)) != 16:
        raise FrozenPredictionError("TASK037C_FUSION_ARM_COUNT_CHANGED")
    selection = config.get("selection_policy", {})
    if not selection or any(value is not False for value in selection.values()):
        raise FrozenPredictionError("TASK037C_SELECTION_POLICY_CHANGED")


def _load_hashed_prediction(path: Path, expected_hash: str, name: str) -> np.ndarray:
    if not path.is_file():
        raise FrozenPredictionError("TASK037C_FROZEN_PREDICTION_MISSING")
    actual = sha256_file(path)
    if actual != expected_hash:
        raise FrozenPredictionError("TASK037C_FROZEN_PREDICTION_HASH_MISMATCH")
    value = np.load(path, allow_pickle=False)
    try:
        return binary_vector(value, name)
    finally:
        del value


def _assert_no_test_artifacts(config: Mapping[str, Any]) -> None:
    roots = [
        REPO_ROOT / str(config["sources"]["task035b_private_root"]),
        REPO_ROOT / str(config["sources"]["task037b_private_root"]),
    ]
    prohibited_relative = (
        "TestLabels",
        "test_prediction.npy",
        "test_score.npy",
        "sealed_test",
    )
    for root in roots:
        if not root.is_dir():
            raise FrozenPredictionError("TASK037C_PRIVATE_ROOT_MISSING")
        for name in prohibited_relative:
            if any(root.rglob(name)):
                raise FrozenPredictionError("TASK037C_TEST_ARTIFACT_DISCOVERED")


def load_frozen_predictions(config: Mapping[str, Any]) -> FrozenPredictionInputs:
    """Load predictions only. This function has no label path or label argument."""

    validate_frozen_matrix(config)
    verify_commit_lineage(config["lineage"])
    _assert_no_test_artifacts(config)

    reports = {
        name: verified_report(
            REPO_ROOT / str(config["sources"][name]),
            str(config["report_hashes"][name]),
        )
        for name in (
            "kpi_manifest",
            "primary_panel_freeze",
            "selection_freeze",
            "task035b_outer_validation",
            "detector_artifact_manifest",
            "detector_threshold_freeze",
            "task037b_outer_validation",
        )
    }
    kpi_rows = {row["kpi_id"]: row for row in reports["kpi_manifest"]["per_kpi"]}
    kpi_ids = tuple(sorted(kpi_rows))
    if len(kpi_ids) != 10:
        raise FrozenPredictionError("TASK037C_KPI_COUNT_MISMATCH")
    split_hashes = {kpi: str(kpi_rows[kpi]["split_manifest_hash"]) for kpi in kpi_ids}

    panel_rows = {
        row["kpi_id"]: row for row in reports["primary_panel_freeze"]["per_kpi"]
    }
    selection_rows = {
        row["kpi_id"]: row for row in reports["selection_freeze"]["per_kpi"]
    }
    if set(panel_rows) != set(kpi_ids) or set(selection_rows) != set(kpi_ids):
        raise FrozenPredictionError("TASK037C_RULE_KPI_SET_MISMATCH")

    task035b_root = REPO_ROOT / str(config["sources"]["task035b_private_root"])
    outer_rule_manifest = read_json(
        task035b_root / "manifests/outer_prediction_freeze.private.json"
    )
    verify_private_manifest(outer_rule_manifest, "manifest_hash")
    if outer_rule_manifest.get("selection_freeze_hash") != reports["selection_freeze"]["report_hash"]:
        raise FrozenPredictionError("TASK037C_RULE_SELECTION_BINDING_MISMATCH")
    outer_rule_expected = {
        (row["kpi_id"], arm["arm"]): arm["prediction_sha256"]
        for row in outer_rule_manifest["per_kpi"]
        for arm in row["arms"]
    }

    detector_rows = {
        (row["detector_variant"], row["kpi_id"]): row
        for row in reports["detector_artifact_manifest"]["records"]
    }
    if len(detector_rows) != 20:
        raise FrozenPredictionError("TASK037C_DETECTOR_UNIT_COUNT_MISMATCH")
    if {key[0] for key in detector_rows} != set(DETECTOR_VARIANTS):
        raise FrozenPredictionError("TASK037C_DETECTOR_VARIANTS_MISMATCH")
    if len({row["detector_id"] for row in detector_rows.values()}) != 20:
        raise FrozenPredictionError("TASK037C_DETECTOR_IDS_NOT_DISTINCT")

    detector_predictions: dict[tuple[str, str, str], np.ndarray] = {}
    detector_hashes: dict[tuple[str, str, str], str] = {}
    source_records: list[Mapping[str, Any]] = []
    task037b_root = REPO_ROOT / str(config["sources"]["task037b_private_root"])
    seed = int(config["detector_seed"])
    for variant in DETECTOR_VARIANTS:
        for kpi in kpi_ids:
            row = detector_rows.get((variant, kpi))
            if row is None or row["split_manifest_hash"] != split_hashes[kpi]:
                raise FrozenPredictionError("TASK037C_DETECTOR_SPLIT_BINDING_MISMATCH")
            for split in ("inner", "outer"):
                expected = str(row[f"{split}_prediction_hash"])
                path = (
                    task037b_root
                    / "detectors"
                    / variant
                    / kpi
                    / str(seed)
                    / "predictions"
                    / f"{split}_prediction.npy"
                )
                key = (split, variant, kpi)
                detector_predictions[key] = _load_hashed_prediction(
                    path, expected, "detector"
                )
                detector_hashes[key] = expected
                source_records.append(
                    {
                        "source_type": "detector_prediction",
                        "split": split,
                        "detector_variant": variant,
                        "kpi_id": kpi,
                        "prediction_hash": expected,
                        "split_manifest_hash": split_hashes[kpi],
                    }
                )

    rule_predictions: dict[tuple[str, str, str], np.ndarray] = {}
    rule_hashes: dict[tuple[str, str, str], str] = {}
    recovered_records: list[dict[str, Any]] = []
    for kpi in kpi_ids:
        selected = {
            row["rule_sha256"]: row for row in panel_rows[kpi]["selected_rules"]
        }
        if len(selected) != 10:
            raise FrozenPredictionError("TASK037C_PANEL_RULE_COUNT_MISMATCH")
        individual: dict[str, np.ndarray] = {}
        for rule_hash, tracked in selected.items():
            expected = str(tracked["inner_runtime_prediction_hash"])
            path = (
                task035b_root
                / "inner"
                / "primary_panel_predictions"
                / rule_hash
                / "replay_1"
                / "output_labels.npy"
            )
            individual[rule_hash] = _load_hashed_prediction(path, expected, "rule")
        for arm in RULE_ARMS:
            member_hashes = tuple(selection_rows[kpi][arm]["rule_hashes"])
            if not member_hashes or any(value not in individual for value in member_hashes):
                raise FrozenPredictionError("TASK037C_INNER_ARM_MEMBER_MISSING")
            lengths = {len(individual[value]) for value in member_hashes}
            if len(lengths) != 1:
                raise FrozenPredictionError("TASK037C_INNER_ARM_LENGTH_MISMATCH")
            vector = np.maximum.reduce([individual[value] for value in member_hashes]).astype(
                np.int8, copy=False
            )
            key = ("inner", kpi, arm)
            rule_predictions[key] = vector.copy()
            recovered_records.append(
                {
                    "kpi_id": kpi,
                    "rule_arm": arm,
                    "member_rule_hashes": list(member_hashes),
                    "source_prediction_hashes": [
                        selected[value]["inner_runtime_prediction_hash"]
                        for value in member_hashes
                    ],
                    "recovery_method": "exact_or_of_hash_verified_frozen_inner_rule_predictions",
                    "labels_loaded": False,
                }
            )

            outer_expected = outer_rule_expected.get((kpi, arm))
            if outer_expected is None:
                raise FrozenPredictionError("TASK037C_OUTER_RULE_HASH_MISSING")
            outer_path = (
                task035b_root / "outer" / "frozen_arm_predictions" / kpi / f"{arm}.npy"
            )
            outer_key = ("outer", kpi, arm)
            rule_predictions[outer_key] = _load_hashed_prediction(
                outer_path, outer_expected, "rule"
            )
            rule_hashes[outer_key] = outer_expected
            source_records.append(
                {
                    "source_type": "rule_arm_prediction",
                    "split": "outer",
                    "rule_arm": arm,
                    "kpi_id": kpi,
                    "prediction_hash": outer_expected,
                    "selection_freeze_hash": reports["selection_freeze"]["report_hash"],
                    "split_manifest_hash": split_hashes[kpi],
                }
            )

    for kpi in kpi_ids:
        for split in ("inner", "outer"):
            lengths = {
                len(detector_predictions[(split, variant, kpi)])
                for variant in DETECTOR_VARIANTS
            }
            lengths.update(
                len(rule_predictions[(split, kpi, arm)]) for arm in RULE_ARMS
            )
            if len(lengths) != 1:
                raise FrozenPredictionError("TASK037C_SOURCE_PREDICTION_LENGTH_MISMATCH")

    if all(
        detector_hashes[("outer", "LSTMADalpha", kpi)]
        == detector_hashes[("outer", "LSTMADbeta", kpi)]
        for kpi in kpi_ids
    ):
        raise FrozenPredictionError("TASK037C_DETECTOR_VARIANTS_COLLAPSED")

    return FrozenPredictionInputs(
        kpi_ids=kpi_ids,
        split_hashes=split_hashes,
        detector_predictions=detector_predictions,
        rule_predictions=rule_predictions,
        detector_hashes=detector_hashes,
        rule_hashes=rule_hashes,
        source_records=tuple(source_records),
        inner_rule_recovery={
            "status": "recovered_without_inference",
            "arm_count": len(recovered_records),
            "records": recovered_records,
            "labels_loaded": False,
        },
    )
