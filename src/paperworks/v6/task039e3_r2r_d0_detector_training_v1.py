"""Deterministic normal-only training plane for frozen D0 PCA-SPE V1.

The public helpers in this module are either fixed-authority factories or pure
numeric functions.  The sole real controller accepts no arguments, obtains
only the four authorized normal files through the task-owned selective helper,
and never exposes private paths or model parameters.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import sys
from types import ModuleType
from typing import Any, Mapping, NoReturn, Sequence
import weakref

from paperworks.v6.common import stable_hash_v1
from paperworks.v6 import task039e3_r2r_d0_detector_design_v1 as design_v1


TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D0-DETECTOR-NORMAL-TRAINING-AND-CALIBRATION-V1"
SCHEMA_VERSION = "1.0.0"
D0_TRAINING_VERSION = "TASK039E3_R2R_D0_PCA_SPE_NORMAL_TRAINING_V1"
DETECTOR_ID = "D0_PCA_SPE_V1"
DETECTOR_FAMILY = "PCA_RECONSTRUCTION_SPE"
NUMERIC_BACKEND = "NUMPY_LINEAR_ALGEBRA"

NORMAL_MODEL_FIT = "NORMAL_MODEL_FIT"
NORMAL_THRESHOLD_CALIBRATION = "NORMAL_THRESHOLD_CALIBRATION"
NORMAL_SANITY_EVALUATION = "NORMAL_SANITY_EVALUATION"

DESIGN_HASH = "357d19d02dee73273d52c7b147b5ddcfa11ead43a7198f2bf089ec78c2d8e174"
DESIGN_REPORT_HASH = "3ffcec30d2bc605bf0b4ca15f80fcc3ed40aa283b6ae913e767c0ad9db18ece7"
FEATURE_SCOPE_HASH = "4e9ba5a52733ae00f8cf755cda9918667c7065e0bc5b6eed2712aab97c3d6dd0"
INDEPENDENCE_HASH = "f430d3233790f4befa3baeb024cce90eef08051358bd13771de4d73126f59692"
DESIGN_READINESS_HASH = "533e62761efce660e1d10726268187c2a9ba5e0d2b0763814b64bd75b0473c4e"
DESIGN_BUNDLE_HASH = "8fa5ab4b81a4dad0f7d1d13bd356b3aad21a45e747cd3b047ada697450ce3034"
DESIGN_RECEIPT_HASH = "61299eba73c09faaf9396a6174ad487e4736c6271e274a2c18dd3cb60fd0c8b5"
DESIGN_CONFIG_HASH = "b931c872688117365f2d4418bd7e521a8cd281455eb92927d32d11276f621713"

DATASET_MANIFEST_ID = "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2"
OFFICIAL_SNAPSHOT_COMMIT = "2a814cebc9a66b06c9e5cd545e2d72e65d383737"
P1_FEATURE_ORDER = design_v1.P1_FEATURE_ORDER
P1_FEATURE_COUNT = 37
P1_FEATURE_SET_HASH = "6dea06e82c0d99f35a0d11c5e97503e8bb3a0fc8c1d9963b997986021fd23515"
P1_FEATURE_ORDER_HASH = "a612bdb9850ad0dd865dc62b23199bf2b696452c492e4aabe09fe554fa246d57"

STANDARDIZATION_SCALE_FLOOR = 1e-12
PCA_EXPLAINED_VARIANCE_TARGET = 0.95
NORMAL_CALIBRATION_ALPHA = 0.001
THRESHOLD_QUANTILE_NUMERATOR = 999
THRESHOLD_QUANTILE_DENOMINATOR = 1000
ALARM_COMPARISON_OPERATOR = "score > threshold"
ALARM_EPISODE_POLICY = "MAXIMAL_CONTIGUOUS_UNIQUE_ONE_SECOND_DECISION_INDICES_FILE_LOCAL"
NEGATIVE_EIGENVALUE_EPSILON_MULTIPLIER = 64
DIFFERENTIAL_SEMANTIC_CASES = 14


class D0TrainingError(RuntimeError):
    """Fixed-code fail-closed training or custody rejection."""

    def __init__(self, code: str) -> None:
        self.code = code if code in _FAILURE_CODES else "D0_TRAINING_BLOCKED_UNEXPECTED"
        super().__init__(self.code)


_FAILURE_CODES = frozenset(
    {
        "D0_TRAINING_BLOCKED_DESIGN_REPLAY",
        "D0_TRAINING_BLOCKED_GRANT_CUSTODY",
        "D0_TRAINING_BLOCKED_NUMPY_UNAVAILABLE",
        "D0_TRAINING_BLOCKED_NORMAL_FILE_CUSTODY",
        "D0_TRAINING_BLOCKED_FEATURE_SCHEMA",
        "D0_TRAINING_BLOCKED_NONFINITE_DATA",
        "D0_TRAINING_BLOCKED_NUMERIC_CONTRACT",
        "D0_TRAINING_BLOCKED_NEGATIVE_EIGENVALUE",
        "D0_TRAINING_BLOCKED_EXACT_TIED_CUTOFF",
        "D0_TRAINING_BLOCKED_STAGE_ORDER",
        "D0_TRAINING_BLOCKED_RETRY",
        "D0_TRAINING_BLOCKED_PRIVATE_WRITE",
        "D0_TRAINING_BLOCKED_LOCAL_BINDING",
        "D0_TRAINING_BLOCKED_UNEXPECTED",
    }
)


def _fail(code: str) -> NoReturn:
    raise D0TrainingError(code)


@dataclass(frozen=True)
class NormalFileIdentityV1:
    role: str
    relative_path: str
    sha256: str
    byte_size: int
    row_count: int


TRAIN1 = NormalFileIdentityV1(
    "NORMAL_TRAIN1_MODEL_FIT",
    "hai-23.05/hai-train1.csv",
    "53007b0ba604fbf338e7ac2e08cd81d874b5d1388f3aecb213ddcba5bf2bec4a",
    162_418_984,
    280_800,
)
TRAIN2 = NormalFileIdentityV1(
    "NORMAL_TRAIN2_MODEL_FIT",
    "hai-23.05/hai-train2.csv",
    "0e520e82bf78a661ab19ce4967f3c766bd809820f457a9c90c365102d4534c56",
    169_121_615,
    291_600,
)
TRAIN3 = NormalFileIdentityV1(
    "NORMAL_TRAIN3_THRESHOLD_CALIBRATION",
    "hai-23.05/hai-train3.csv",
    "bfcec2dc05adea103e7491546b0e28268faaa26d3cc717d10f4595c94b81e85d",
    72_774_793,
    126_000,
)
TRAIN4 = NormalFileIdentityV1(
    "NORMAL_TRAIN4_SANITY_EVALUATION_ONLY",
    "hai-23.05/hai-train4.csv",
    "56658c83657d42a65db982b864362e0d0ffeb96d1f7b357d5e76e3a5c522d940",
    114_494_940,
    198_000,
)
NORMAL_FILES = (TRAIN1, TRAIN2, TRAIN3, TRAIN4)


@dataclass(frozen=True)
class D0NormalTrainingGrantV1:
    artifact_type: str
    schema_version: str
    task_id: str
    training_version: str
    detector_id: str
    design_hash: str
    design_report_hash: str
    feature_scope_hash: str
    independence_hash: str
    design_readiness_hash: str
    design_bundle_hash: str
    design_receipt_hash: str
    design_config_hash: str
    dataset_manifest_id: str
    official_snapshot_commit: str
    normal_files: tuple[NormalFileIdentityV1, ...]
    test1_authorized: bool
    label_access_authorized: bool
    test2_authorized: bool
    d0_inner_execution_authorized: bool
    d2_authorized: bool
    outer_authorized: bool
    grant_hash: str


@dataclass(frozen=True, repr=False)
class D0PreprocessingArtifactV1:
    artifact_type: str
    schema_version: str
    detector_id: str
    design_hash: str
    feature_order_hash: str
    train1_sha256: str
    train2_sha256: str
    combined_row_count: int
    python_version: str
    numpy_version: str
    means_float_hex: tuple[str, ...]
    scales_float_hex: tuple[str, ...]
    artifact_hash: str


@dataclass(frozen=True, repr=False)
class D0PcaModelArtifactV1:
    artifact_type: str
    schema_version: str
    detector_id: str
    design_hash: str
    preprocessing_hash: str
    feature_order_hash: str
    train1_sha256: str
    train2_sha256: str
    fit_row_count: int
    python_version: str
    numpy_version: str
    selected_k: int
    explained_variance_target: float
    eigenvalues_float_hex: tuple[str, ...]
    retained_loadings_float_hex: tuple[tuple[str, ...], ...]
    labels_used: bool
    test_accessed: bool
    artifact_hash: str


@dataclass(frozen=True, repr=False)
class D0ThresholdArtifactV1:
    artifact_type: str
    schema_version: str
    detector_id: str
    design_hash: str
    model_hash: str
    train3_sha256: str
    calibration_row_count: int
    alpha: float
    upper_quantile: float
    q_index: int
    order_statistic_policy: str
    threshold_float_hex: str
    comparison_operator: str
    labels_used: bool
    test_used: bool
    artifact_hash: str


@dataclass(frozen=True)
class D0NormalTrainingResultV1:
    detector_id: str
    design_hash: str
    python_version: str
    numpy_version: str
    feature_count: int
    feature_set_hash: str
    feature_order_hash: str
    train_hash_matches: tuple[bool, bool, bool, bool]
    train_row_counts: tuple[int, int, int, int]
    preprocessing_content_hash: str
    selected_k: int
    residual_dimensions: int
    exact_tied_cutoff_encountered: bool
    model_content_hash: str
    threshold_content_hash: str
    threshold_q_index: int
    train4_point_alarm_count: int
    train4_alarm_episode_count: int
    train4_normal_far_episodes_per_hour: float
    model_fit_attempts: int
    threshold_calibration_attempts: int
    private_paths_exposed: int = 0
    private_values_exposed: int = 0

    def sanitized_payload(self) -> dict[str, Any]:
        return {
            "detector_id": self.detector_id,
            "design_hash": self.design_hash,
            "python_version": self.python_version,
            "numpy_version": self.numpy_version,
            "feature_count": self.feature_count,
            "feature_set_hash": self.feature_set_hash,
            "feature_order_hash": self.feature_order_hash,
            "train_hash_matches": list(self.train_hash_matches),
            "train_row_counts": list(self.train_row_counts),
            "preprocessing_content_hash": self.preprocessing_content_hash,
            "selected_k": self.selected_k,
            "residual_dimensions": self.residual_dimensions,
            "exact_tied_cutoff_encountered": self.exact_tied_cutoff_encountered,
            "model_content_hash": self.model_content_hash,
            "threshold_content_hash": self.threshold_content_hash,
            "threshold_q_index": self.threshold_q_index,
            "train4_point_alarm_count": self.train4_point_alarm_count,
            "train4_alarm_episode_count": self.train4_alarm_episode_count,
            "train4_normal_far_episodes_per_hour": self.train4_normal_far_episodes_per_hour,
            "model_fit_attempts": self.model_fit_attempts,
            "model_fit_retries": 0,
            "threshold_calibration_attempts": self.threshold_calibration_attempts,
            "threshold_calibration_retries": 0,
            "private_paths_exposed": self.private_paths_exposed,
            "private_values_exposed": self.private_values_exposed,
        }


_ISSUED_GRANTS: dict[int, tuple[weakref.ReferenceType[D0NormalTrainingGrantV1], str]] = {}
_ISSUED_PRIVATE_ARTIFACTS: dict[int, tuple[weakref.ReferenceType[Any], str]] = {}
_REAL_EXECUTION_STATE = "NOT_STARTED"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _canonical_document_hash(document: Mapping[str, Any], field: str = "artifact_hash") -> str:
    payload = dict(document)
    payload.pop(field, None)
    return stable_hash_v1(payload)


def _load_exact_public_document(relative_path: str, expected_hash: str, field: str = "artifact_hash") -> Mapping[str, Any]:
    try:
        path = _repo_root() / PurePosixPath(relative_path)
        if path.is_symlink() or not path.is_file():
            _fail("D0_TRAINING_BLOCKED_DESIGN_REPLAY")
        document = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            _fail("D0_TRAINING_BLOCKED_DESIGN_REPLAY")
        if document.get(field) != expected_hash or _canonical_document_hash(document, field) != expected_hash:
            _fail("D0_TRAINING_BLOCKED_DESIGN_REPLAY")
        return document
    except D0TrainingError:
        raise
    except BaseException:
        _fail("D0_TRAINING_BLOCKED_DESIGN_REPLAY")


def _replay_frozen_design_v1() -> None:
    issued_design = design_v1.build_d0_detector_design_v1()
    if design_v1.validate_d0_detector_design_v1(issued_design) != DESIGN_HASH:
        _fail("D0_TRAINING_BLOCKED_DESIGN_REPLAY")
    if (
        issued_design.feature_schema.ordered_features != P1_FEATURE_ORDER
        or issued_design.feature_schema.feature_set_hash != P1_FEATURE_SET_HASH
        or issued_design.feature_schema.feature_order_hash != P1_FEATURE_ORDER_HASH
    ):
        _fail("D0_TRAINING_BLOCKED_DESIGN_REPLAY")
    documents = (
        ("docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_DESIGN_V1_DESIGN.json", DESIGN_REPORT_HASH),
        ("docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_DESIGN_V1_FEATURE_SCOPE.json", FEATURE_SCOPE_HASH),
        ("docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_DESIGN_V1_INDEPENDENCE.json", INDEPENDENCE_HASH),
        ("docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_DESIGN_V1_READINESS.json", DESIGN_READINESS_HASH),
        ("docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_DESIGN_V1_BUNDLE.json", DESIGN_BUNDLE_HASH),
        ("docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_DESIGN_V1_RECEIPT.json", DESIGN_RECEIPT_HASH),
    )
    for relative, expected in documents:
        _load_exact_public_document(relative, expected)
    config = _load_exact_public_document(
        "configs/v6/task039e3_r2r_d0_pca_spe_detector_v1.json",
        DESIGN_CONFIG_HASH,
        "config_hash",
    )
    if design_v1.validate_d0_config_v1(config) != DESIGN_CONFIG_HASH:
        _fail("D0_TRAINING_BLOCKED_DESIGN_REPLAY")


def _grant_payload(value: D0NormalTrainingGrantV1) -> dict[str, Any]:
    payload = asdict(value)
    payload.pop("grant_hash", None)
    return payload


def _expected_grant_v1() -> D0NormalTrainingGrantV1:
    value = D0NormalTrainingGrantV1(
        artifact_type="task039e3_r2r_d0_normal_training_grant_v1",
        schema_version=SCHEMA_VERSION,
        task_id=TASK_ID,
        training_version=D0_TRAINING_VERSION,
        detector_id=DETECTOR_ID,
        design_hash=DESIGN_HASH,
        design_report_hash=DESIGN_REPORT_HASH,
        feature_scope_hash=FEATURE_SCOPE_HASH,
        independence_hash=INDEPENDENCE_HASH,
        design_readiness_hash=DESIGN_READINESS_HASH,
        design_bundle_hash=DESIGN_BUNDLE_HASH,
        design_receipt_hash=DESIGN_RECEIPT_HASH,
        design_config_hash=DESIGN_CONFIG_HASH,
        dataset_manifest_id=DATASET_MANIFEST_ID,
        official_snapshot_commit=OFFICIAL_SNAPSHOT_COMMIT,
        normal_files=NORMAL_FILES,
        test1_authorized=False,
        label_access_authorized=False,
        test2_authorized=False,
        d0_inner_execution_authorized=False,
        d2_authorized=False,
        outer_authorized=False,
        grant_hash="",
    )
    return replace(value, grant_hash=stable_hash_v1(_grant_payload(value)))


def _register_issued(registry: dict[int, tuple[weakref.ReferenceType[Any], str]], value: Any, artifact_hash: str) -> None:
    object_id = id(value)

    def cleanup(reference: weakref.ReferenceType[Any]) -> None:
        current = registry.get(object_id)
        if current is not None and current[0] is reference:
            registry.pop(object_id, None)

    registry[object_id] = (weakref.ref(value, cleanup), artifact_hash)


def issue_d0_normal_training_grant_v1() -> D0NormalTrainingGrantV1:
    """Replay exact frozen public authorities and issue one process-local grant."""

    _replay_frozen_design_v1()
    value = _expected_grant_v1()
    _register_issued(_ISSUED_GRANTS, value, value.grant_hash)
    return value


def validate_d0_normal_training_grant_v1(value: D0NormalTrainingGrantV1) -> str:
    if type(value) is not D0NormalTrainingGrantV1:
        _fail("D0_TRAINING_BLOCKED_GRANT_CUSTODY")
    expected = _expected_grant_v1()
    issued = _ISSUED_GRANTS.get(id(value))
    if (
        issued is None
        or issued[0]() is not value
        or issued[1] != value.grant_hash
        or value != expected
        or value.grant_hash != stable_hash_v1(_grant_payload(value))
    ):
        _fail("D0_TRAINING_BLOCKED_GRANT_CUSTODY")
    return value.grant_hash


def _np() -> Any:
    try:
        import numpy as np
    except BaseException:
        _fail("D0_TRAINING_BLOCKED_NUMPY_UNAVAILABLE")
    return np


def _require_matrix_float64(value: Any, *, columns: int = P1_FEATURE_COUNT) -> Any:
    np = _np()
    if type(value) is not np.ndarray or value.dtype != np.float64 or value.ndim != 2 or value.shape[1] != columns:
        _fail("D0_TRAINING_BLOCKED_NUMERIC_CONTRACT")
    if value.shape[0] < 1 or not bool(np.isfinite(value).all()):
        _fail("D0_TRAINING_BLOCKED_NONFINITE_DATA")
    return value


def fit_preprocessing_v1(train1: Any, train2: Any) -> tuple[Any, Any, Any]:
    """Fit frozen population preprocessing on train1 then train2 only."""

    np = _np()
    first = _require_matrix_float64(train1)
    second = _require_matrix_float64(train2)
    combined = np.concatenate((first, second), axis=0).astype(np.float64, copy=False)
    mu = np.mean(combined, axis=0, dtype=np.float64)
    sigma = np.std(combined, axis=0, ddof=0, dtype=np.float64)
    scale = np.maximum(sigma, np.float64(STANDARDIZATION_SCALE_FLOOR))
    standardized = (combined - mu) / scale
    if standardized.dtype != np.float64 or not bool(np.isfinite(standardized).all()):
        _fail("D0_TRAINING_BLOCKED_NONFINITE_DATA")
    return mu, scale, standardized


def covariance_v1(standardized: Any) -> Any:
    np = _np()
    values = _require_matrix_float64(standardized)
    covariance = (values.T @ values) / np.float64(values.shape[0])
    covariance = (covariance + covariance.T) / np.float64(2.0)
    if covariance.dtype != np.float64 or not bool(np.isfinite(covariance).all()):
        _fail("D0_TRAINING_BLOCKED_NUMERIC_CONTRACT")
    return covariance


def eigendecomposition_v1(covariance: Any) -> tuple[Any, Any]:
    np = _np()
    if type(covariance) is not np.ndarray or covariance.dtype != np.float64 or covariance.shape != (P1_FEATURE_COUNT, P1_FEATURE_COUNT):
        _fail("D0_TRAINING_BLOCKED_NUMERIC_CONTRACT")
    if not bool(np.isfinite(covariance).all()) or not bool(np.array_equal(covariance, covariance.T)):
        _fail("D0_TRAINING_BLOCKED_NUMERIC_CONTRACT")
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(-eigenvalues, kind="stable")
    values = eigenvalues[order].astype(np.float64, copy=False)
    vectors = eigenvectors[:, order].astype(np.float64, copy=False)
    total_variance = float(np.sum(values, dtype=np.float64))
    if not np.isfinite(total_variance) or total_variance <= 0.0:
        _fail("D0_TRAINING_BLOCKED_NUMERIC_CONTRACT")
    tolerance = (
        NEGATIVE_EIGENVALUE_EPSILON_MULTIPLIER
        * float(np.finfo(np.float64).eps)
        * max(1.0, total_variance)
    )
    if bool((values < -tolerance).any()):
        _fail("D0_TRAINING_BLOCKED_NEGATIVE_EIGENVALUE")
    values = np.maximum(values, np.float64(0.0))
    return values, vectors


def select_components_v1(eigenvalues: Any, eigenvectors: Any) -> tuple[int, Any]:
    np = _np()
    if (
        type(eigenvalues) is not np.ndarray
        or eigenvalues.dtype != np.float64
        or eigenvalues.shape != (P1_FEATURE_COUNT,)
        or type(eigenvectors) is not np.ndarray
        or eigenvectors.dtype != np.float64
        or eigenvectors.shape != (P1_FEATURE_COUNT, P1_FEATURE_COUNT)
        or not bool(np.isfinite(eigenvalues).all())
        or not bool(np.isfinite(eigenvectors).all())
        or bool((eigenvalues < 0.0).any())
    ):
        _fail("D0_TRAINING_BLOCKED_NUMERIC_CONTRACT")
    total = float(np.sum(eigenvalues, dtype=np.float64))
    if total <= 0.0:
        _fail("D0_TRAINING_BLOCKED_NUMERIC_CONTRACT")
    cumulative = np.cumsum(eigenvalues, dtype=np.float64) / np.float64(total)
    k = int(np.searchsorted(cumulative, np.float64(PCA_EXPLAINED_VARIANCE_TARGET), side="left")) + 1
    if k >= P1_FEATURE_COUNT:
        k = P1_FEATURE_COUNT - 1
    if k < 1 or k >= P1_FEATURE_COUNT:
        _fail("D0_TRAINING_BLOCKED_NUMERIC_CONTRACT")
    if eigenvalues[k - 1] == eigenvalues[k]:
        _fail("D0_TRAINING_BLOCKED_EXACT_TIED_CUTOFF")
    retained = eigenvectors[:, :k].copy()
    for column in range(k):
        loading = retained[:, column]
        anchor = int(np.argmax(np.abs(loading)))
        if loading[anchor] < 0.0:
            retained[:, column] = -loading
    return k, retained


def score_spe_v1(values: Any, mean: Any, scale: Any, retained_loadings: Any) -> Any:
    np = _np()
    matrix = _require_matrix_float64(values)
    if (
        type(mean) is not np.ndarray
        or mean.dtype != np.float64
        or mean.shape != (P1_FEATURE_COUNT,)
        or type(scale) is not np.ndarray
        or scale.dtype != np.float64
        or scale.shape != (P1_FEATURE_COUNT,)
        or type(retained_loadings) is not np.ndarray
        or retained_loadings.dtype != np.float64
        or retained_loadings.ndim != 2
        or retained_loadings.shape[0] != P1_FEATURE_COUNT
        or retained_loadings.shape[1] < 1
        or retained_loadings.shape[1] >= P1_FEATURE_COUNT
        or bool((scale <= 0.0).any())
    ):
        _fail("D0_TRAINING_BLOCKED_NUMERIC_CONTRACT")
    standardized = (matrix - mean) / scale
    projected = (standardized @ retained_loadings) @ retained_loadings.T
    residual = standardized - projected
    scores = np.sum(residual * residual, axis=1, dtype=np.float64)
    if scores.dtype != np.float64 or not bool(np.isfinite(scores).all()) or bool((scores < 0.0).any()):
        _fail("D0_TRAINING_BLOCKED_NUMERIC_CONTRACT")
    return scores


def threshold_q_index_v1(score_count: int) -> int:
    if type(score_count) is not int or score_count < 1:
        _fail("D0_TRAINING_BLOCKED_NUMERIC_CONTRACT")
    return (
        THRESHOLD_QUANTILE_NUMERATOR * score_count
        + THRESHOLD_QUANTILE_DENOMINATOR
        - 1
    ) // THRESHOLD_QUANTILE_DENOMINATOR - 1


def calibrate_threshold_v1(scores: Any) -> tuple[float, int]:
    np = _np()
    if type(scores) is not np.ndarray or scores.dtype != np.float64 or scores.ndim != 1 or scores.size < 1:
        _fail("D0_TRAINING_BLOCKED_NUMERIC_CONTRACT")
    if not bool(np.isfinite(scores).all()) or bool((scores < 0.0).any()):
        _fail("D0_TRAINING_BLOCKED_NUMERIC_CONTRACT")
    q_index = threshold_q_index_v1(int(scores.size))
    ordered = np.sort(scores, kind="stable")
    return float(ordered[q_index]), q_index


def strict_alarm_mask_v1(scores: Any, threshold: float) -> Any:
    np = _np()
    if type(scores) is not np.ndarray or scores.dtype != np.float64 or scores.ndim != 1:
        _fail("D0_TRAINING_BLOCKED_NUMERIC_CONTRACT")
    if type(threshold) is not float or not np.isfinite(threshold):
        _fail("D0_TRAINING_BLOCKED_NUMERIC_CONTRACT")
    return scores > np.float64(threshold)


def alarm_episodes_v1(alarm_indices: Sequence[int]) -> tuple[tuple[int, int], ...]:
    if any(type(value) is not int or value < 0 for value in alarm_indices):
        _fail("D0_TRAINING_BLOCKED_NUMERIC_CONTRACT")
    ordered = sorted(set(alarm_indices))
    if not ordered:
        return ()
    episodes: list[tuple[int, int]] = []
    start = previous = ordered[0]
    for value in ordered[1:]:
        if value != previous + 1:
            episodes.append((start, previous + 1))
            start = value
        previous = value
    episodes.append((start, previous + 1))
    return tuple(episodes)


def _artifact_payload(value: Any) -> dict[str, Any]:
    payload = asdict(value)
    payload.pop("artifact_hash", None)
    return payload


def _issue_private_artifact(value: Any) -> Any:
    artifact_hash = value.artifact_hash
    _register_issued(_ISSUED_PRIVATE_ARTIFACTS, value, artifact_hash)
    return value


def _validate_private_artifact(value: Any, expected_type: type[Any]) -> str:
    if type(value) is not expected_type:
        _fail("D0_TRAINING_BLOCKED_GRANT_CUSTODY")
    issued = _ISSUED_PRIVATE_ARTIFACTS.get(id(value))
    if (
        issued is None
        or issued[0]() is not value
        or issued[1] != value.artifact_hash
        or stable_hash_v1(_artifact_payload(value)) != value.artifact_hash
    ):
        _fail("D0_TRAINING_BLOCKED_GRANT_CUSTODY")
    return value.artifact_hash


def build_preprocessing_artifact_v1(mean: Any, scale: Any, *, numpy_version: str) -> D0PreprocessingArtifactV1:
    np = _np()
    if (
        type(mean) is not np.ndarray
        or mean.dtype != np.float64
        or mean.shape != (P1_FEATURE_COUNT,)
        or type(scale) is not np.ndarray
        or scale.dtype != np.float64
        or scale.shape != (P1_FEATURE_COUNT,)
        or not bool(np.isfinite(mean).all())
        or not bool(np.isfinite(scale).all())
        or bool((scale <= 0.0).any())
    ):
        _fail("D0_TRAINING_BLOCKED_NUMERIC_CONTRACT")
    value = D0PreprocessingArtifactV1(
        "task039e3_r2r_d0_preprocessing_artifact_v1",
        SCHEMA_VERSION,
        DETECTOR_ID,
        DESIGN_HASH,
        P1_FEATURE_ORDER_HASH,
        TRAIN1.sha256,
        TRAIN2.sha256,
        TRAIN1.row_count + TRAIN2.row_count,
        platform.python_version(),
        numpy_version,
        tuple(float(item).hex() for item in mean),
        tuple(float(item).hex() for item in scale),
        "",
    )
    value = replace(value, artifact_hash=stable_hash_v1(_artifact_payload(value)))
    return _issue_private_artifact(value)


def build_pca_model_artifact_v1(
    preprocessing: D0PreprocessingArtifactV1,
    eigenvalues: Any,
    retained_loadings: Any,
    selected_k: int,
    *,
    numpy_version: str,
) -> D0PcaModelArtifactV1:
    np = _np()
    _validate_private_artifact(preprocessing, D0PreprocessingArtifactV1)
    if (
        type(eigenvalues) is not np.ndarray
        or eigenvalues.dtype != np.float64
        or eigenvalues.shape != (P1_FEATURE_COUNT,)
        or type(retained_loadings) is not np.ndarray
        or retained_loadings.dtype != np.float64
        or retained_loadings.shape != (P1_FEATURE_COUNT, selected_k)
        or type(selected_k) is not int
        or not 1 <= selected_k < P1_FEATURE_COUNT
    ):
        _fail("D0_TRAINING_BLOCKED_NUMERIC_CONTRACT")
    value = D0PcaModelArtifactV1(
        "task039e3_r2r_d0_pca_model_artifact_v1",
        SCHEMA_VERSION,
        DETECTOR_ID,
        DESIGN_HASH,
        preprocessing.artifact_hash,
        P1_FEATURE_ORDER_HASH,
        TRAIN1.sha256,
        TRAIN2.sha256,
        TRAIN1.row_count + TRAIN2.row_count,
        platform.python_version(),
        numpy_version,
        selected_k,
        PCA_EXPLAINED_VARIANCE_TARGET,
        tuple(float(item).hex() for item in eigenvalues),
        tuple(
            tuple(float(item).hex() for item in retained_loadings[row, :])
            for row in range(P1_FEATURE_COUNT)
        ),
        False,
        False,
        "",
    )
    value = replace(value, artifact_hash=stable_hash_v1(_artifact_payload(value)))
    return _issue_private_artifact(value)


def build_threshold_artifact_v1(
    model: D0PcaModelArtifactV1,
    threshold: float,
    q_index: int,
) -> D0ThresholdArtifactV1:
    np = _np()
    _validate_private_artifact(model, D0PcaModelArtifactV1)
    if type(threshold) is not float or not np.isfinite(threshold) or type(q_index) is not int or q_index != threshold_q_index_v1(TRAIN3.row_count):
        _fail("D0_TRAINING_BLOCKED_NUMERIC_CONTRACT")
    value = D0ThresholdArtifactV1(
        "task039e3_r2r_d0_threshold_artifact_v1",
        SCHEMA_VERSION,
        DETECTOR_ID,
        DESIGN_HASH,
        model.artifact_hash,
        TRAIN3.sha256,
        TRAIN3.row_count,
        NORMAL_CALIBRATION_ALPHA,
        THRESHOLD_QUANTILE_NUMERATOR / THRESHOLD_QUANTILE_DENOMINATOR,
        q_index,
        "ceil(0.999*n)-1_zero_based_after_ascending_sort_no_interpolation",
        threshold.hex(),
        ALARM_COMPARISON_OPERATOR,
        False,
        False,
        "",
    )
    value = replace(value, artifact_hash=stable_hash_v1(_artifact_payload(value)))
    return _issue_private_artifact(value)


def _sha256_file(path: Path) -> tuple[str, int]:
    digest = sha256()
    byte_count = 0
    try:
        if path.is_symlink() or not path.is_file():
            _fail("D0_TRAINING_BLOCKED_NORMAL_FILE_CUSTODY")
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
                byte_count += len(block)
    except D0TrainingError:
        raise
    except BaseException:
        _fail("D0_TRAINING_BLOCKED_NORMAL_FILE_CUSTODY")
    return digest.hexdigest(), byte_count


def _validate_normal_file(path: Path, identity: NormalFileIdentityV1) -> None:
    observed_hash, observed_size = _sha256_file(path)
    if observed_hash != identity.sha256 or observed_size != identity.byte_size:
        _fail("D0_TRAINING_BLOCKED_NORMAL_FILE_CUSTODY")


def _parse_normal_frame(path: Path, identity: NormalFileIdentityV1) -> Any:
    np = _np()
    _validate_normal_file(path, identity)
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            header_line = stream.readline()
            header = tuple(next(csv.reader([header_line])))
            if len(header) != len(set(header)):
                _fail("D0_TRAINING_BLOCKED_FEATURE_SCHEMA")
            observed_p1_order = tuple(name for name in header if name.startswith("P1_"))
            if observed_p1_order != P1_FEATURE_ORDER:
                _fail("D0_TRAINING_BLOCKED_FEATURE_SCHEMA")
            indices = tuple(header.index(name) for name in P1_FEATURE_ORDER)
            values = np.loadtxt(
                stream,
                delimiter=",",
                dtype=np.float64,
                usecols=indices,
                ndmin=2,
            )
    except D0TrainingError:
        raise
    except BaseException:
        _fail("D0_TRAINING_BLOCKED_FEATURE_SCHEMA")
    if values.shape != (identity.row_count, P1_FEATURE_COUNT) or values.dtype != np.float64:
        _fail("D0_TRAINING_BLOCKED_FEATURE_SCHEMA")
    if not bool(np.isfinite(values).all()):
        _fail("D0_TRAINING_BLOCKED_NONFINITE_DATA")
    return values


def _load_materializer() -> ModuleType:
    try:
        path = _repo_root() / "scripts/local/materialize_hai_d0_normal_payload_v1.py"
        spec = importlib.util.spec_from_file_location("_task039e3_d0_normal_materializer", path)
        if spec is None or spec.loader is None:
            _fail("D0_TRAINING_BLOCKED_NORMAL_FILE_CUSTODY")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    except D0TrainingError:
        raise
    except BaseException:
        _fail("D0_TRAINING_BLOCKED_NORMAL_FILE_CUSTODY")


def _private_document(value: Any) -> dict[str, Any]:
    return asdict(value)


def _write_private_json_atomic(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() or path.is_symlink() or temporary.exists():
            _fail("D0_TRAINING_BLOCKED_PRIVATE_WRITE")
        payload = json.dumps(
            _private_document(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
        with temporary.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        os.replace(temporary, path)
    except D0TrainingError:
        raise
    except BaseException:
        _fail("D0_TRAINING_BLOCKED_PRIVATE_WRITE")


_BINDING_KEYS = frozenset(
    {
        "HAI_DATA_ROOT",
        "TASK039E3_UTILITY_NORMAL_ONLY_PRIVATE_REGISTRY_V1",
        "TASK039E3_UTILITY_NORMAL_ONLY_PRIVATE_LOCATOR_V1",
        "TASK039E3_UTILITY_SOURCE_CENSUS_SUPPLEMENT_PRIVATE_REGISTRY_V1",
        "TASK039E3_UTILITY_SOURCE_CENSUS_SUPPLEMENT_PRIVATE_LOCATOR_V1",
        "TASK039E3_D0_PCA_SPE_PREPROCESSING_V1",
        "TASK039E3_D0_PCA_SPE_MODEL_V1",
        "TASK039E3_D0_PCA_SPE_THRESHOLD_V1",
    }
)
_BINDING_PATTERN = re.compile(r"^([A-Z0-9_]+)='((?:[^']|'\"'\"')*)'$" )


def _decode_binding_value(raw: str) -> str:
    return raw.replace("'\"'\"'", "'")


def _encode_binding_value(raw: str) -> str:
    if not raw or "\n" in raw or "\r" in raw or "\x00" in raw:
        _fail("D0_TRAINING_BLOCKED_LOCAL_BINDING")
    return "'" + raw.replace("'", "'\"'\"'") + "'"


def _load_local_bindings() -> dict[str, str]:
    path = _repo_root() / ".env.custody.local"
    if not path.exists():
        return {}
    try:
        if path.is_symlink() or not path.is_file():
            _fail("D0_TRAINING_BLOCKED_LOCAL_BINDING")
        result: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            match = _BINDING_PATTERN.fullmatch(line)
            if match is None or match.group(1) not in _BINDING_KEYS or match.group(1) in result:
                _fail("D0_TRAINING_BLOCKED_LOCAL_BINDING")
            result[match.group(1)] = _decode_binding_value(match.group(2))
        return result
    except D0TrainingError:
        raise
    except BaseException:
        _fail("D0_TRAINING_BLOCKED_LOCAL_BINDING")


def _write_local_bindings(updates: Mapping[str, str]) -> None:
    if not updates or any(key not in _BINDING_KEYS for key in updates):
        _fail("D0_TRAINING_BLOCKED_LOCAL_BINDING")
    current = _load_local_bindings()
    current.update({key: str(value) for key, value in updates.items()})
    path = _repo_root() / ".env.custody.local"
    temporary = _repo_root() / ".env.custody.local.d0-training-v1.part"
    try:
        if temporary.exists() or temporary.is_symlink():
            _fail("D0_TRAINING_BLOCKED_LOCAL_BINDING")
        lines = [f"{key}={_encode_binding_value(current[key])}" for key in sorted(current)]
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write("\n".join(lines) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        os.replace(temporary, path)
    except D0TrainingError:
        raise
    except BaseException:
        _fail("D0_TRAINING_BLOCKED_LOCAL_BINDING")


def execute_d0_normal_training_and_calibration_v1() -> D0NormalTrainingResultV1:
    """Perform the one authorized normal-only fit/calibration/sanity sequence."""

    global _REAL_EXECUTION_STATE
    if _REAL_EXECUTION_STATE != "NOT_STARTED":
        _fail("D0_TRAINING_BLOCKED_RETRY")
    _REAL_EXECUTION_STATE = "ATTEMPTED"
    grant = issue_d0_normal_training_grant_v1()
    validate_d0_normal_training_grant_v1(grant)
    np = _np()
    materializer = _load_materializer()
    try:
        fit_cache = materializer.materialize_fit_payloads_v1(_repo_root())
        cache_root = fit_cache.cache_root
        train1_path = cache_root / PurePosixPath(TRAIN1.relative_path)
        train2_path = cache_root / PurePosixPath(TRAIN2.relative_path)
        train1 = _parse_normal_frame(train1_path, TRAIN1)
        train2 = _parse_normal_frame(train2_path, TRAIN2)
        mean, scale, standardized = fit_preprocessing_v1(train1, train2)
        del train1, train2
        covariance = covariance_v1(standardized)
        del standardized
        eigenvalues, eigenvectors = eigendecomposition_v1(covariance)
        selected_k, retained = select_components_v1(eigenvalues, eigenvectors)
        del covariance, eigenvectors
        numpy_version = str(np.__version__)
        preprocessing = build_preprocessing_artifact_v1(mean, scale, numpy_version=numpy_version)
        model = build_pca_model_artifact_v1(
            preprocessing,
            eigenvalues,
            retained,
            selected_k,
            numpy_version=numpy_version,
        )
        private_root = cache_root / ".d0_pca_spe_v1"
        prep_path = private_root / "preprocessing.json"
        model_path = private_root / "model.json"
        threshold_path = private_root / "threshold.json"
        _write_private_json_atomic(prep_path, preprocessing)
        _write_private_json_atomic(model_path, model)
        _REAL_EXECUTION_STATE = "MODEL_FROZEN"

        calibration_cache = materializer.materialize_calibration_payload_v1(_repo_root(), cache_root)
        if calibration_cache.cache_root != cache_root:
            _fail("D0_TRAINING_BLOCKED_NORMAL_FILE_CUSTODY")
        train3_path = cache_root / PurePosixPath(TRAIN3.relative_path)
        train3 = _parse_normal_frame(train3_path, TRAIN3)
        train3_scores = score_spe_v1(train3, mean, scale, retained)
        del train3
        threshold_value, q_index = calibrate_threshold_v1(train3_scores)
        del train3_scores
        threshold = build_threshold_artifact_v1(model, threshold_value, q_index)
        _write_private_json_atomic(threshold_path, threshold)
        _REAL_EXECUTION_STATE = "THRESHOLD_FROZEN"
        _write_local_bindings(
            {
                "HAI_DATA_ROOT": str(cache_root),
                "TASK039E3_D0_PCA_SPE_PREPROCESSING_V1": str(prep_path),
                "TASK039E3_D0_PCA_SPE_MODEL_V1": str(model_path),
                "TASK039E3_D0_PCA_SPE_THRESHOLD_V1": str(threshold_path),
            }
        )

        sanity_cache = materializer.materialize_train4_sanity_payload_v1(
            _repo_root(),
            cache_root,
            model_hash=model.artifact_hash,
            threshold_hash=threshold.artifact_hash,
        )
        if sanity_cache.cache_root != cache_root:
            _fail("D0_TRAINING_BLOCKED_NORMAL_FILE_CUSTODY")
        train4_path = cache_root / PurePosixPath(TRAIN4.relative_path)
        train4 = _parse_normal_frame(train4_path, TRAIN4)
        train4_scores = score_spe_v1(train4, mean, scale, retained)
        alarms = strict_alarm_mask_v1(train4_scores, threshold_value)
        alarm_indices = tuple(int(item) for item in np.flatnonzero(alarms))
        episodes = alarm_episodes_v1(alarm_indices)
        far = len(episodes) / (TRAIN4.row_count / 3600.0)
        _REAL_EXECUTION_STATE = "COMPLETE"
        return D0NormalTrainingResultV1(
            DETECTOR_ID,
            DESIGN_HASH,
            platform.python_version(),
            numpy_version,
            P1_FEATURE_COUNT,
            P1_FEATURE_SET_HASH,
            P1_FEATURE_ORDER_HASH,
            (True, True, True, True),
            (TRAIN1.row_count, TRAIN2.row_count, TRAIN3.row_count, TRAIN4.row_count),
            preprocessing.artifact_hash,
            selected_k,
            P1_FEATURE_COUNT - selected_k,
            False,
            model.artifact_hash,
            threshold.artifact_hash,
            q_index,
            len(alarm_indices),
            len(episodes),
            far,
            1,
            1,
        )
    except D0TrainingError:
        raise
    except BaseException:
        _fail("D0_TRAINING_BLOCKED_UNEXPECTED")


__all__ = [
    "D0NormalTrainingGrantV1",
    "D0PreprocessingArtifactV1",
    "D0PcaModelArtifactV1",
    "D0ThresholdArtifactV1",
    "D0NormalTrainingResultV1",
    "D0TrainingError",
    "DIFFERENTIAL_SEMANTIC_CASES",
    "issue_d0_normal_training_grant_v1",
    "validate_d0_normal_training_grant_v1",
    "fit_preprocessing_v1",
    "covariance_v1",
    "eigendecomposition_v1",
    "select_components_v1",
    "score_spe_v1",
    "threshold_q_index_v1",
    "calibrate_threshold_v1",
    "strict_alarm_mask_v1",
    "alarm_episodes_v1",
    "build_preprocessing_artifact_v1",
    "build_pca_model_artifact_v1",
    "build_threshold_artifact_v1",
    "execute_d0_normal_training_and_calibration_v1",
]
