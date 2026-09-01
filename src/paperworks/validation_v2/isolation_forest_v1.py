"""Fixed normal-only IsolationForest baseline for VALIDATION V2.

This module owns only the estimator, score, calibration, and authority
contracts.  Label access, common-metric evaluation, and scientific artifact
custody remain separate capabilities.  Optional detector dependencies are
loaded lazily so the base package remains importable without scikit-learn.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import importlib.metadata
import json
import math
import pickle
from typing import Any, Mapping, Sequence

from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER


_HEX = set("0123456789abcdef")
_FEATURE_COUNT = 37
_AUTHORIZED_FEATURE_IDS = tuple(P1_FEATURE_ORDER)
_FIT_ROLES = ("NORMAL_FIT_PRIMARY", "NORMAL_FIT_SECONDARY")
_CALIBRATION_ROLE = "NORMAL_CONFIRMATION_CALIBRATION"
_VERSIONS = {
    "numpy": "2.5.2",
    "scipy": "1.18.1",
    "scikit-learn": "1.9.0",
    "joblib": "1.5.3",
    "threadpoolctl": "3.6.0",
    "narwhals": "2.25.0",
}
_PYTHON_VERSION = "3.12.13"
_PACKAGE_RECORD_HASHES = {
    "numpy": "1f14251e9bb0d5a485ee8e478d29d985f95fb029b209e7860518b84007fc5b6b",
    "scipy": "81c8365ace1c77966cab8d57bbb07015e35e60506a362c4cbb3e5307fcbea7d1",
    "scikit-learn": "d310b37f978622f1788a28f9e0badfb5cf5a95712b05a92a8c69366ba2808f7a",
    "joblib": "815a2f3b0ee265a98da65431de24b51c149ccff67e68cef587956fac51314004",
    "threadpoolctl": "ff8e876dc324cf340bc7f6cbc35e2c146594732e571da2469b015747744cd5a0",
    "narwhals": "60f0145f52d032bb91bc1703030c7b5bfe4d986f8a98bcd4f4a352d091233045",
}
_AUTHORIZED_FILES = {
    "NORMAL_FIT_PRIMARY": (
        "hai-train1.csv", "53007b0ba604fbf338e7ac2e08cd81d874b5d1388f3aecb213ddcba5bf2bec4a"
    ),
    "NORMAL_FIT_SECONDARY": (
        "hai-train2.csv", "0e520e82bf78a661ab19ce4967f3c766bd809820f457a9c90c365102d4534c56"
    ),
    "NORMAL_CONFIRMATION_CALIBRATION": (
        "hai-train3.csv", "bfcec2dc05adea103e7491546b0e28268faaa26d3cc717d10f4595c94b81e85d"
    ),
    "NORMAL_POLICY_SELECTION_SANITY": (
        "hai-train4.csv", "56658c83657d42a65db982b864362e0d0ffeb96d1f7b357d5e76e3a5c522d940"
    ),
    "DEVELOPMENT_ONLY": (
        "hai-test1.csv", "78c7f1d4de1f2ab9ccc2f8c719f80f831033543adb0c81d0d78f84f40838d4be"
    ),
}


class IsolationForestContractError(ValueError):
    """Raised when a detector input or authority binding fails closed."""


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _document_hash(value: Mapping[str, Any]) -> str:
    return sha256(_canonical_bytes(value)).hexdigest()


def _sha256_contiguous_array_v1(value: Any, *, prefix: bytes = b"") -> str:
    """Hash exact C-order array bytes without allocating a full bytes copy."""

    if type(prefix) is not bytes:
        raise IsolationForestContractError("array hash prefix must be exact bytes")
    try:
        view = memoryview(value)
    except TypeError as exc:
        raise IsolationForestContractError("array hash input must expose a buffer") from exc
    if not view.c_contiguous:
        raise IsolationForestContractError("array hash input must be C-contiguous")
    digest = sha256()
    digest.update(prefix)
    try:
        digest.update(view.cast("B"))
    except (TypeError, ValueError) as exc:
        raise IsolationForestContractError("array hash buffer cannot be byte-cast") from exc
    return digest.hexdigest()


def _require_hex64(value: str, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(char not in _HEX for char in value):
        raise IsolationForestContractError(f"{field} must be lowercase sha256 hex")


def _require_git_commit(value: str, field: str) -> None:
    if not isinstance(value, str) or len(value) != 40 or any(char not in _HEX for char in value):
        raise IsolationForestContractError(f"{field} must be a lowercase 40-character Git commit")


def _require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise IsolationForestContractError(f"{field} must be non-empty text")


def _numpy() -> Any:
    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover - exercised without optional environment
        raise IsolationForestContractError("optional dependency numpy is unavailable") from exc
    return np


def _isolation_forest_class() -> Any:
    try:
        from sklearn.ensemble import IsolationForest
    except ImportError as exc:  # pragma: no cover - exercised without optional environment
        raise IsolationForestContractError(
            "optional VALIDATION V2 detector dependencies are unavailable"
        ) from exc
    return IsolationForest


@dataclass(frozen=True)
class IsolationForestConfigV1:
    detector_id: str = "V2_ISOLATION_FOREST_FIXED_NORMAL_ONLY_V1"
    n_estimators: int = 256
    max_samples: int = 256
    max_features: float = 1.0
    bootstrap: bool = False
    contamination: str = "auto"
    random_state: int = 0
    n_jobs: int = 1
    verbose: int = 0
    warm_start: bool = False
    score_expression: str = "-estimator.score_samples(X)"
    threshold_numerator: int = 999
    threshold_denominator: int = 1000
    comparator: str = "score > threshold"

    def validate(self) -> None:
        strict_types = {
            "detector_id": str,
            "n_estimators": int,
            "max_samples": int,
            "max_features": float,
            "bootstrap": bool,
            "contamination": str,
            "random_state": int,
            "n_jobs": int,
            "verbose": int,
            "warm_start": bool,
            "score_expression": str,
            "threshold_numerator": int,
            "threshold_denominator": int,
            "comparator": str,
        }
        for field, expected_type in strict_types.items():
            if type(getattr(self, field)) is not expected_type:
                raise IsolationForestContractError(f"{field} has the wrong strict type")
        expected = IsolationForestConfigV1()
        if self != expected:
            raise IsolationForestContractError("detector config differs from the frozen V2 contract")

    def to_document(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema": "validation_v2_isolation_forest_config_v1",
            "detector_id": self.detector_id,
            "n_estimators": self.n_estimators,
            "max_samples": self.max_samples,
            "max_features": self.max_features,
            "bootstrap": self.bootstrap,
            "contamination": self.contamination,
            "random_state": self.random_state,
            "n_jobs": self.n_jobs,
            "verbose": self.verbose,
            "warm_start": self.warm_start,
            "score_expression": self.score_expression,
            "threshold_quantile": "0.999",
            "threshold_order_statistic": "NEAREST_RANK",
            "comparator": self.comparator,
        }

    @property
    def config_hash(self) -> str:
        return _document_hash(self.to_document())


@dataclass(frozen=True)
class DetectorEnvironmentReceiptV1:
    python_version: str
    package_records: tuple[tuple[str, str, str], ...]
    self_hash: str

    def body_document(self) -> dict[str, Any]:
        return {
            "schema": "validation_v2_detector_environment_receipt_v1",
            "python_version": self.python_version,
            "package_records": [
                {"package": package, "version": version, "record_sha256": record_hash}
                for package, version, record_hash in self.package_records
            ],
        }

    def to_document(self) -> dict[str, Any]:
        return {**self.body_document(), "self_hash": self.self_hash}


def build_detector_environment_receipt_v1() -> DetectorEnvironmentReceiptV1:
    import sys

    try:
        observed = tuple(
            (
                package,
                importlib.metadata.version(package),
                sha256((importlib.metadata.distribution(package).read_text("RECORD") or "").encode("utf-8")).hexdigest(),
            )
            for package in sorted(_VERSIONS)
        )
    except importlib.metadata.PackageNotFoundError as exc:
        raise IsolationForestContractError("optional detector dependency closure is unavailable") from exc
    expected = tuple(
        (package, _VERSIONS[package], _PACKAGE_RECORD_HASHES[package]) for package in sorted(_VERSIONS)
    )
    if observed != expected:
        raise IsolationForestContractError("detector dependency versions or RECORD hashes do not match")
    python_version = ".".join(str(item) for item in sys.version_info[:3])
    if python_version != _PYTHON_VERSION:
        raise IsolationForestContractError("Python version does not match the frozen detector environment")
    receipt = DetectorEnvironmentReceiptV1(
        python_version=python_version,
        package_records=observed,
        self_hash="",
    )
    return DetectorEnvironmentReceiptV1(
        python_version=receipt.python_version,
        package_records=receipt.package_records,
        self_hash=_document_hash(receipt.body_document()),
    )


@dataclass(frozen=True)
class NormalMatrixInputV1:
    file_id: str
    file_content_sha256: str
    split_role: str
    feature_ids: tuple[str, ...]
    values: Any
    labels_present: bool = False
    timestamps_present: bool = False
    attack_metadata_present: bool = False


@dataclass(frozen=True)
class MatrixBindingV1:
    file_id: str
    file_content_sha256: str
    split_role: str
    row_count: int
    feature_count: int
    matrix_sha256: str

    def to_document(self) -> dict[str, Any]:
        return {
            "file_id": self.file_id,
            "file_content_sha256": self.file_content_sha256,
            "split_role": self.split_role,
            "row_count": self.row_count,
            "feature_count": self.feature_count,
            "matrix_sha256": self.matrix_sha256,
        }


def _normalize_matrix_input(
    value: NormalMatrixInputV1,
    *,
    expected_role: str,
    expected_feature_ids: tuple[str, ...] | None = None,
) -> tuple[Any, MatrixBindingV1]:
    if not isinstance(value, NormalMatrixInputV1):
        raise IsolationForestContractError("matrix input must be NormalMatrixInputV1")
    _require_text(value.file_id, "file_id")
    _require_hex64(value.file_content_sha256, "file_content_sha256")
    if value.split_role != expected_role:
        raise IsolationForestContractError("matrix split role is not authorized")
    if expected_role not in _AUTHORIZED_FILES:
        raise IsolationForestContractError("matrix split role has no authorized file binding")
    expected_file_id, expected_file_hash = _AUTHORIZED_FILES[expected_role]
    if value.file_id != expected_file_id or value.file_content_sha256 != expected_file_hash:
        raise IsolationForestContractError("matrix file identity does not match its authorized split role")
    if type(value.labels_present) is not bool or type(value.timestamps_present) is not bool or type(value.attack_metadata_present) is not bool:
        raise IsolationForestContractError("presence flags must be strict booleans")
    if value.labels_present or value.timestamps_present or value.attack_metadata_present:
        raise IsolationForestContractError("labels, timestamps, and attack metadata are prohibited")
    if value.feature_ids != _AUTHORIZED_FEATURE_IDS:
        raise IsolationForestContractError("feature IDs differ from the approved ordered P1 authority")
    if expected_feature_ids is not None and value.feature_ids != expected_feature_ids:
        raise IsolationForestContractError("feature order differs from the fitted authority")

    np = _numpy()
    matrix = np.asarray(value.values, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[1] != _FEATURE_COUNT or matrix.shape[0] == 0:
        raise IsolationForestContractError("matrix must be non-empty rows by 37 features")
    if not bool(np.isfinite(matrix).all()):
        raise IsolationForestContractError("matrix contains non-finite values")
    matrix = np.ascontiguousarray(matrix, dtype=np.float64)
    matrix_hash = _sha256_contiguous_array_v1(
        matrix,
        prefix=_canonical_bytes({
            "shape": [int(matrix.shape[0]), int(matrix.shape[1])],
            "feature_ids": list(value.feature_ids),
        }),
    )
    return matrix, MatrixBindingV1(
        file_id=value.file_id,
        file_content_sha256=value.file_content_sha256,
        split_role=value.split_role,
        row_count=int(matrix.shape[0]),
        feature_count=int(matrix.shape[1]),
        matrix_sha256=matrix_hash,
    )


@dataclass(frozen=True)
class IsolationForestFitReceiptV1:
    detector_id: str
    source_commit: str
    preregistration_hash: str
    environment_hash: str
    config_hash: str
    feature_ids: tuple[str, ...]
    ordered_inputs: tuple[MatrixBindingV1, MatrixBindingV1]
    combined_fit_matrix_sha256: str
    combined_fit_rows: int
    effective_max_samples: int
    model_state_sha256: str
    self_hash: str

    def body_document(self) -> dict[str, Any]:
        return {
            "schema": "validation_v2_isolation_forest_fit_receipt_v1",
            "detector_id": self.detector_id,
            "source_commit": self.source_commit,
            "preregistration_hash": self.preregistration_hash,
            "environment_hash": self.environment_hash,
            "config_hash": self.config_hash,
            "feature_ids": list(self.feature_ids),
            "ordered_inputs": [item.to_document() for item in self.ordered_inputs],
            "combined_fit_matrix_sha256": self.combined_fit_matrix_sha256,
            "combined_fit_rows": self.combined_fit_rows,
            "effective_max_samples": self.effective_max_samples,
            "model_state_sha256": self.model_state_sha256,
        }

    def to_document(self) -> dict[str, Any]:
        return {**self.body_document(), "self_hash": self.self_hash}


@dataclass(frozen=True)
class IsolationForestModelV1:
    estimator: Any
    config: IsolationForestConfigV1
    fit_receipt: IsolationForestFitReceiptV1


def _model_state_hash(estimator: Any) -> str:
    try:
        payload = pickle.dumps(estimator, protocol=5)
    except (pickle.PickleError, TypeError, AttributeError) as exc:
        raise IsolationForestContractError("estimator cannot be canonically serialized") from exc
    return sha256(payload).hexdigest()


def fit_isolation_forest_v1(
    train1: NormalMatrixInputV1,
    train2: NormalMatrixInputV1,
    *,
    source_commit: str,
    preregistration_hash: str,
    environment: DetectorEnvironmentReceiptV1,
    config: IsolationForestConfigV1 | None = None,
) -> IsolationForestModelV1:
    _require_git_commit(source_commit, "source_commit")
    _require_hex64(preregistration_hash, "preregistration_hash")
    if environment.self_hash != _document_hash(environment.body_document()):
        raise IsolationForestContractError("environment receipt hash is invalid")
    expected_packages = tuple(
        (package, _VERSIONS[package], _PACKAGE_RECORD_HASHES[package]) for package in sorted(_VERSIONS)
    )
    if environment.python_version != _PYTHON_VERSION or environment.package_records != expected_packages:
        raise IsolationForestContractError("environment receipt is stale or mismatched")
    frozen_config = config or IsolationForestConfigV1()
    frozen_config.validate()
    first, first_binding = _normalize_matrix_input(train1, expected_role=_FIT_ROLES[0])
    second, second_binding = _normalize_matrix_input(
        train2, expected_role=_FIT_ROLES[1], expected_feature_ids=train1.feature_ids
    )
    np = _numpy()
    combined = np.ascontiguousarray(np.concatenate((first, second), axis=0), dtype=np.float64)
    if int(combined.shape[0]) < frozen_config.max_samples:
        raise IsolationForestContractError("combined fit cohort has fewer than 256 rows")
    combined_hash = _sha256_contiguous_array_v1(
        combined,
        prefix=_canonical_bytes({
            "ordered_matrix_hashes": [
                first_binding.matrix_sha256,
                second_binding.matrix_sha256,
            ]
        }),
    )
    estimator = _isolation_forest_class()(
        n_estimators=frozen_config.n_estimators,
        max_samples=frozen_config.max_samples,
        contamination=frozen_config.contamination,
        max_features=frozen_config.max_features,
        bootstrap=frozen_config.bootstrap,
        n_jobs=frozen_config.n_jobs,
        random_state=frozen_config.random_state,
        verbose=frozen_config.verbose,
        warm_start=frozen_config.warm_start,
    )
    estimator.fit(combined)
    if int(estimator.max_samples_) != frozen_config.max_samples:
        raise IsolationForestContractError("effective max_samples_ differs from the frozen authority")
    state_hash = _model_state_hash(estimator)
    provisional = IsolationForestFitReceiptV1(
        detector_id=frozen_config.detector_id,
        source_commit=source_commit,
        preregistration_hash=preregistration_hash,
        environment_hash=environment.self_hash,
        config_hash=frozen_config.config_hash,
        feature_ids=train1.feature_ids,
        ordered_inputs=(first_binding, second_binding),
        combined_fit_matrix_sha256=combined_hash,
        combined_fit_rows=int(combined.shape[0]),
        effective_max_samples=int(estimator.max_samples_),
        model_state_sha256=state_hash,
        self_hash="",
    )
    receipt = IsolationForestFitReceiptV1(
        **{**provisional.__dict__, "self_hash": _document_hash(provisional.body_document())}
    )
    return IsolationForestModelV1(estimator=estimator, config=frozen_config, fit_receipt=receipt)


def score_isolation_forest_v1(
    model: IsolationForestModelV1,
    value: NormalMatrixInputV1,
    *,
    expected_role: str,
    expected_fit_receipt_hash: str,
) -> tuple[Any, MatrixBindingV1]:
    if not isinstance(model, IsolationForestModelV1):
        raise IsolationForestContractError("model must be IsolationForestModelV1")
    model.config.validate()
    if model.fit_receipt.self_hash != _document_hash(model.fit_receipt.body_document()):
        raise IsolationForestContractError("fit receipt hash is invalid")
    _require_hex64(expected_fit_receipt_hash, "expected_fit_receipt_hash")
    if model.fit_receipt.self_hash != expected_fit_receipt_hash:
        raise IsolationForestContractError("fit receipt differs from the externally authorized identity")
    if model.fit_receipt.config_hash != model.config.config_hash:
        raise IsolationForestContractError("live config differs from the fitted authority")
    if _model_state_hash(model.estimator) != model.fit_receipt.model_state_sha256:
        raise IsolationForestContractError("live estimator state differs from the fitted authority")
    current_environment = build_detector_environment_receipt_v1()
    if current_environment.self_hash != model.fit_receipt.environment_hash:
        raise IsolationForestContractError("current environment differs from the fitted authority")
    if expected_role not in _AUTHORIZED_FILES:
        raise IsolationForestContractError("scoring role is not authorized")
    matrix, binding = _normalize_matrix_input(
        value, expected_role=expected_role, expected_feature_ids=model.fit_receipt.feature_ids
    )
    np = _numpy()
    scores = np.asarray(-model.estimator.score_samples(matrix), dtype=np.float64)
    if scores.ndim != 1 or scores.shape[0] != matrix.shape[0] or not bool(np.isfinite(scores).all()):
        raise IsolationForestContractError("estimator returned invalid scores")
    return scores, binding


@dataclass(frozen=True)
class IsolationForestThresholdReceiptV1:
    fit_receipt_hash: str
    calibration_input: MatrixBindingV1
    calibration_score_sha256: str
    score_count: int
    quantile: str
    nearest_rank: int
    threshold: float
    comparator: str
    self_hash: str

    def body_document(self) -> dict[str, Any]:
        return {
            "schema": "validation_v2_isolation_forest_threshold_receipt_v1",
            "fit_receipt_hash": self.fit_receipt_hash,
            "calibration_input": self.calibration_input.to_document(),
            "calibration_score_sha256": self.calibration_score_sha256,
            "score_count": self.score_count,
            "quantile": self.quantile,
            "nearest_rank": self.nearest_rank,
            "threshold": self.threshold,
            "comparator": self.comparator,
        }

    def to_document(self) -> dict[str, Any]:
        return {**self.body_document(), "self_hash": self.self_hash}


def calibrate_isolation_forest_threshold_v1(
    model: IsolationForestModelV1,
    train3: NormalMatrixInputV1,
    *,
    expected_fit_receipt_hash: str,
) -> IsolationForestThresholdReceiptV1:
    scores, binding = score_isolation_forest_v1(
        model,
        train3,
        expected_role=_CALIBRATION_ROLE,
        expected_fit_receipt_hash=expected_fit_receipt_hash,
    )
    np = _numpy()
    count = int(scores.shape[0])
    rank = math.ceil(model.config.threshold_numerator * count / model.config.threshold_denominator)
    threshold = float(np.sort(scores, kind="stable")[rank - 1])
    score_hash = _sha256_contiguous_array_v1(
        np.ascontiguousarray(scores, dtype=np.float64)
    )
    provisional = IsolationForestThresholdReceiptV1(
        fit_receipt_hash=model.fit_receipt.self_hash,
        calibration_input=binding,
        calibration_score_sha256=score_hash,
        score_count=count,
        quantile="0.999",
        nearest_rank=rank,
        threshold=threshold,
        comparator=model.config.comparator,
        self_hash="",
    )
    return IsolationForestThresholdReceiptV1(
        **{**provisional.__dict__, "self_hash": _document_hash(provisional.body_document())}
    )


def predict_isolation_forest_v1(
    model: IsolationForestModelV1,
    threshold: IsolationForestThresholdReceiptV1,
    value: NormalMatrixInputV1,
    *,
    expected_role: str,
    expected_fit_receipt_hash: str,
    expected_threshold_receipt_hash: str,
) -> tuple[Any, Any, MatrixBindingV1]:
    _require_hex64(expected_threshold_receipt_hash, "expected_threshold_receipt_hash")
    if threshold.self_hash != _document_hash(threshold.body_document()):
        raise IsolationForestContractError("threshold receipt hash is invalid")
    if threshold.self_hash != expected_threshold_receipt_hash:
        raise IsolationForestContractError("threshold differs from the externally authorized identity")
    if threshold.fit_receipt_hash != model.fit_receipt.self_hash:
        raise IsolationForestContractError("threshold is bound to a different fitted model")
    expected_rank = math.ceil(
        model.config.threshold_numerator * threshold.score_count / model.config.threshold_denominator
    )
    if (
        threshold.quantile != "0.999"
        or threshold.comparator != model.config.comparator
        or threshold.score_count < 1
        or threshold.nearest_rank != expected_rank
        or not math.isfinite(threshold.threshold)
        or threshold.calibration_input.split_role != _CALIBRATION_ROLE
        or threshold.calibration_input.file_id != _AUTHORIZED_FILES[_CALIBRATION_ROLE][0]
        or threshold.calibration_input.file_content_sha256 != _AUTHORIZED_FILES[_CALIBRATION_ROLE][1]
    ):
        raise IsolationForestContractError("threshold semantics differ from the frozen authority")
    scores, binding = score_isolation_forest_v1(
        model,
        value,
        expected_role=expected_role,
        expected_fit_receipt_hash=expected_fit_receipt_hash,
    )
    np = _numpy()
    alarms = np.asarray(scores > threshold.threshold, dtype=np.bool_)
    return scores, alarms, binding


__all__ = [
    "DetectorEnvironmentReceiptV1",
    "IsolationForestConfigV1",
    "IsolationForestContractError",
    "IsolationForestFitReceiptV1",
    "IsolationForestModelV1",
    "IsolationForestThresholdReceiptV1",
    "MatrixBindingV1",
    "NormalMatrixInputV1",
    "build_detector_environment_receipt_v1",
    "calibrate_isolation_forest_threshold_v1",
    "fit_isolation_forest_v1",
    "predict_isolation_forest_v1",
    "score_isolation_forest_v1",
]
