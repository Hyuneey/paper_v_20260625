"""Separately versioned, normal-only PCA-SPE reference detector for V2.

This is prospective VALIDATION V2 code. It neither imports nor rewrites PILOT
V1 artifacts and has no label, test2, provider, or network interface.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import math
from typing import Any, Mapping

from .isolation_forest_v1 import (
    DetectorEnvironmentReceiptV1,
    MatrixBindingV1,
    NormalMatrixInputV1,
    _normalize_matrix_input,
    build_detector_environment_receipt_v1,
)


PCA_SPE_V2_DETECTOR_ID = "V2_D0_PCA_SPE_NORMAL_ONLY_V1"
PCA_SPE_V2_FIT_ROLES = ("NORMAL_FIT_PRIMARY", "NORMAL_FIT_SECONDARY")
PCA_SPE_V2_CALIBRATION_ROLE = "NORMAL_CONFIRMATION_CALIBRATION"
_HEX = frozenset("0123456789abcdef")


class PcaSpeV2ContractError(ValueError):
    pass


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _hash(value: Mapping[str, Any]) -> str:
    return sha256(_canonical(value)).hexdigest()


def _sha(value: object, name: str) -> None:
    if type(value) is not str or len(value) != 64 or set(value) - _HEX:
        raise PcaSpeV2ContractError(f"{name} must be lowercase sha256")


def _commit(value: object) -> None:
    if type(value) is not str or len(value) != 40 or set(value) - _HEX:
        raise PcaSpeV2ContractError("source_commit must be lowercase Git commit")


def _numpy() -> Any:
    try:
        import numpy as np
    except ImportError as error:  # pragma: no cover
        raise PcaSpeV2ContractError("NumPy is required for PCA-SPE V2") from error
    return np


@dataclass(frozen=True)
class PcaSpeConfigV2:
    detector_id: str = PCA_SPE_V2_DETECTOR_ID
    explained_variance_numerator: int = 95
    explained_variance_denominator: int = 100
    population_ddof: int = 0
    scale_floor_hex: str = float(1e-12).hex()
    threshold_numerator: int = 999
    threshold_denominator: int = 1000
    quantile_policy: str = "NEAREST_RANK_NO_INTERPOLATION"
    comparator: str = "score > threshold"
    solver: str = "NUMPY_LINALG_EIGH_SYMMETRIC_POPULATION_COVARIANCE"

    def validate(self) -> None:
        if self != PcaSpeConfigV2():
            raise PcaSpeV2ContractError("PCA-SPE config differs from the frozen V2 contract")

    def to_document(self) -> dict[str, Any]:
        self.validate()
        return {"schema": "paperworks.validation_v2.pca_spe_config_v2", **self.__dict__}

    @property
    def config_hash(self) -> str:
        return _hash(self.to_document())


@dataclass(frozen=True)
class PcaSpeFitReceiptV2:
    detector_id: str
    source_commit: str
    preregistration_hash: str
    config_hash: str
    environment_hash: str
    numpy_version: str
    ordered_inputs: tuple[MatrixBindingV1, MatrixBindingV1]
    combined_fit_rows: int
    feature_count: int
    component_count: int
    residual_dimension_count: int
    model_state_hash: str
    receipt_hash: str = ""

    def payload(self) -> dict[str, Any]:
        return {
            "combined_fit_rows": self.combined_fit_rows,
            "component_count": self.component_count,
            "config_hash": self.config_hash,
            "detector_id": self.detector_id,
            "environment_hash": self.environment_hash,
            "feature_count": self.feature_count,
            "model_state_hash": self.model_state_hash,
            "numpy_version": self.numpy_version,
            "ordered_inputs": [item.to_document() for item in self.ordered_inputs],
            "preregistration_hash": self.preregistration_hash,
            "residual_dimension_count": self.residual_dimension_count,
            "schema": "paperworks.validation_v2.pca_spe_fit_receipt_v2",
            "schema_version": "1.0.0",
            "source_commit": self.source_commit,
        }


@dataclass(frozen=True)
class PcaSpeModelV2:
    config: PcaSpeConfigV2
    feature_ids: tuple[str, ...]
    mean: Any
    scale: Any
    eigenvalues: Any
    retained_loadings: Any
    fit_receipt: PcaSpeFitReceiptV2


def _array_document(values: Any) -> dict[str, Any]:
    np = _numpy()
    array = np.ascontiguousarray(values, dtype=np.float64)
    return {
        "dtype": "float64", "shape": list(array.shape),
        "values_hex": [float(item).hex() for item in array.ravel(order="C")],
    }


def _model_state_hash(model: PcaSpeModelV2) -> str:
    return _hash({
        "eigenvalues": _array_document(model.eigenvalues),
        "feature_ids": list(model.feature_ids),
        "mean": _array_document(model.mean),
        "retained_loadings": _array_document(model.retained_loadings),
        "scale": _array_document(model.scale),
        "schema": "paperworks.validation_v2.pca_spe_private_state_hash_v2",
    })


def _validate_model(model: PcaSpeModelV2, *, expected_fit_receipt_hash: str) -> None:
    if type(model) is not PcaSpeModelV2:
        raise PcaSpeV2ContractError("typed PCA-SPE V2 model required")
    model.config.validate()
    _sha(expected_fit_receipt_hash, "expected_fit_receipt_hash")
    receipt = model.fit_receipt
    current_environment = build_detector_environment_receipt_v1()
    if (
        receipt.receipt_hash != _hash(receipt.payload())
        or receipt.receipt_hash != expected_fit_receipt_hash
        or receipt.config_hash != model.config.config_hash
        or receipt.model_state_hash != _model_state_hash(model)
        or receipt.environment_hash != current_environment.self_hash
        or receipt.component_count != int(model.retained_loadings.shape[1])
        or receipt.residual_dimension_count != len(model.feature_ids) - receipt.component_count
    ):
        raise PcaSpeV2ContractError("PCA-SPE model authority replay mismatch")


def fit_pca_spe_v2(
    train1: NormalMatrixInputV1,
    train2: NormalMatrixInputV1,
    *,
    source_commit: str,
    preregistration_hash: str,
    environment: DetectorEnvironmentReceiptV1,
    config: PcaSpeConfigV2 | None = None,
) -> PcaSpeModelV2:
    _commit(source_commit)
    _sha(preregistration_hash, "preregistration_hash")
    frozen = config or PcaSpeConfigV2()
    frozen.validate()
    if type(environment) is not DetectorEnvironmentReceiptV1:
        raise PcaSpeV2ContractError("typed detector environment receipt required")
    current_environment = build_detector_environment_receipt_v1()
    if environment != current_environment:
        raise PcaSpeV2ContractError("detector environment receipt is stale or mismatched")
    first, first_binding = _normalize_matrix_input(train1, expected_role=PCA_SPE_V2_FIT_ROLES[0])
    second, second_binding = _normalize_matrix_input(
        train2, expected_role=PCA_SPE_V2_FIT_ROLES[1], expected_feature_ids=train1.feature_ids,
    )
    np = _numpy()
    matrix = np.ascontiguousarray(np.concatenate((first, second), axis=0), dtype=np.float64)
    mean = np.asarray(matrix.mean(axis=0), dtype=np.float64)
    observed_scale = np.asarray(matrix.std(axis=0, ddof=0), dtype=np.float64)
    scale = np.maximum(observed_scale, float.fromhex(frozen.scale_floor_hex))
    standardized = np.ascontiguousarray((matrix - mean) / scale, dtype=np.float64)
    covariance = np.asarray((standardized.T @ standardized) / standardized.shape[0], dtype=np.float64)
    covariance = np.asarray((covariance + covariance.T) / 2.0, dtype=np.float64)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(-eigenvalues, kind="stable")
    eigenvalues = np.maximum(np.asarray(eigenvalues[order], dtype=np.float64), 0.0)
    eigenvectors = np.asarray(eigenvectors[:, order], dtype=np.float64)
    total = float(eigenvalues.sum())
    if not math.isfinite(total) or total <= 0.0:
        raise PcaSpeV2ContractError("PCA covariance has no positive total variance")
    target = frozen.explained_variance_numerator / frozen.explained_variance_denominator
    component_count = int(np.searchsorted(np.cumsum(eigenvalues) / total, target, side="left")) + 1
    if component_count >= matrix.shape[1]:
        component_count = matrix.shape[1] - 1
    if component_count <= 0:
        raise PcaSpeV2ContractError("PCA must retain at least one component and one residual dimension")
    if component_count < len(eigenvalues) and eigenvalues[component_count - 1] == eigenvalues[component_count]:
        raise PcaSpeV2ContractError("PCA component cutoff splits an exact eigenvalue tie")
    retained = np.asarray(eigenvectors[:, :component_count], dtype=np.float64)
    for column in range(component_count):
        anchor = int(np.argmax(np.abs(retained[:, column])))
        if retained[anchor, column] < 0.0:
            retained[:, column] *= -1.0
    for array in (mean, scale, eigenvalues, retained):
        array.setflags(write=False)
    provisional_model = PcaSpeModelV2(
        config=frozen, feature_ids=train1.feature_ids, mean=mean, scale=scale,
        eigenvalues=eigenvalues, retained_loadings=retained,
        fit_receipt=PcaSpeFitReceiptV2(
            detector_id=frozen.detector_id, source_commit=source_commit,
            preregistration_hash=preregistration_hash, config_hash=frozen.config_hash,
            environment_hash=environment.self_hash, numpy_version=np.__version__,
            ordered_inputs=(first_binding, second_binding),
            combined_fit_rows=int(matrix.shape[0]), feature_count=int(matrix.shape[1]),
            component_count=component_count,
            residual_dimension_count=int(matrix.shape[1]) - component_count,
            model_state_hash="0" * 64,
        ),
    )
    state_hash = _model_state_hash(provisional_model)
    receipt_base = replace(provisional_model.fit_receipt, model_state_hash=state_hash)
    receipt = replace(receipt_base, receipt_hash=_hash(receipt_base.payload()))
    return replace(provisional_model, fit_receipt=receipt)


def score_pca_spe_v2(
    model: PcaSpeModelV2,
    value: NormalMatrixInputV1,
    *,
    expected_role: str,
    expected_fit_receipt_hash: str,
) -> tuple[Any, MatrixBindingV1]:
    _validate_model(model, expected_fit_receipt_hash=expected_fit_receipt_hash)
    matrix, binding = _normalize_matrix_input(
        value, expected_role=expected_role, expected_feature_ids=model.feature_ids,
    )
    np = _numpy()
    standardized = np.ascontiguousarray((matrix - model.mean) / model.scale, dtype=np.float64)
    reconstruction = (standardized @ model.retained_loadings) @ model.retained_loadings.T
    residual = standardized - reconstruction
    scores = np.asarray(np.sum(residual * residual, axis=1), dtype=np.float64)
    if scores.ndim != 1 or not bool(np.isfinite(scores).all()) or bool((scores < 0.0).any()):
        raise PcaSpeV2ContractError("PCA-SPE scoring produced invalid values")
    scores.setflags(write=False)
    return scores, binding


@dataclass(frozen=True)
class PcaSpeThresholdReceiptV2:
    fit_receipt_hash: str
    calibration_input: MatrixBindingV1
    calibration_score_hash: str
    score_count: int
    nearest_rank: int
    threshold_hex: str
    comparator: str
    receipt_hash: str = ""

    def payload(self) -> dict[str, Any]:
        return {
            "calibration_input": self.calibration_input.to_document(),
            "calibration_score_hash": self.calibration_score_hash,
            "comparator": self.comparator,
            "fit_receipt_hash": self.fit_receipt_hash,
            "nearest_rank": self.nearest_rank,
            "quantile": "0.999",
            "score_count": self.score_count,
            "schema": "paperworks.validation_v2.pca_spe_threshold_receipt_v2",
            "schema_version": "1.0.0",
            "threshold_hex": self.threshold_hex,
        }


def calibrate_pca_spe_threshold_v2(
    model: PcaSpeModelV2,
    train3: NormalMatrixInputV1,
    *,
    expected_fit_receipt_hash: str,
) -> PcaSpeThresholdReceiptV2:
    scores, binding = score_pca_spe_v2(
        model, train3, expected_role=PCA_SPE_V2_CALIBRATION_ROLE,
        expected_fit_receipt_hash=expected_fit_receipt_hash,
    )
    np = _numpy()
    count = int(scores.shape[0])
    rank = math.ceil(model.config.threshold_numerator * count / model.config.threshold_denominator)
    threshold = float(np.sort(scores, kind="stable")[rank - 1])
    base = PcaSpeThresholdReceiptV2(
        fit_receipt_hash=model.fit_receipt.receipt_hash, calibration_input=binding,
        calibration_score_hash=sha256(np.ascontiguousarray(scores).tobytes(order="C")).hexdigest(),
        score_count=count, nearest_rank=rank, threshold_hex=threshold.hex(),
        comparator=model.config.comparator,
    )
    return replace(base, receipt_hash=_hash(base.payload()))


def strict_alarm_mask_pca_spe_v2(scores: Any, threshold: float) -> Any:
    np = _numpy()
    values = np.asarray(scores, dtype=np.float64)
    if values.ndim != 1 or not bool(np.isfinite(values).all()) or not math.isfinite(threshold):
        raise PcaSpeV2ContractError("alarm comparison inputs are invalid")
    result = np.asarray(values > threshold, dtype=np.bool_)
    result.setflags(write=False)
    return result


def predict_pca_spe_v2(
    model: PcaSpeModelV2,
    threshold: PcaSpeThresholdReceiptV2,
    value: NormalMatrixInputV1,
    *,
    expected_role: str,
    expected_fit_receipt_hash: str,
    expected_threshold_receipt_hash: str,
) -> tuple[Any, Any, MatrixBindingV1]:
    _sha(expected_threshold_receipt_hash, "expected_threshold_receipt_hash")
    expected_rank = math.ceil(model.config.threshold_numerator * threshold.score_count / model.config.threshold_denominator)
    if (
        threshold.receipt_hash != _hash(threshold.payload())
        or threshold.receipt_hash != expected_threshold_receipt_hash
        or threshold.fit_receipt_hash != expected_fit_receipt_hash
        or threshold.nearest_rank != expected_rank
        or threshold.comparator != "score > threshold"
        or threshold.calibration_input.split_role != PCA_SPE_V2_CALIBRATION_ROLE
    ):
        raise PcaSpeV2ContractError("PCA-SPE threshold authority replay mismatch")
    try:
        threshold_value = float.fromhex(threshold.threshold_hex)
    except (TypeError, ValueError) as error:
        raise PcaSpeV2ContractError("PCA-SPE threshold encoding is invalid") from error
    scores, binding = score_pca_spe_v2(
        model, value, expected_role=expected_role,
        expected_fit_receipt_hash=expected_fit_receipt_hash,
    )
    return scores, strict_alarm_mask_pca_spe_v2(scores, threshold_value), binding


__all__ = [
    "PCA_SPE_V2_CALIBRATION_ROLE", "PCA_SPE_V2_DETECTOR_ID", "PCA_SPE_V2_FIT_ROLES",
    "PcaSpeConfigV2", "PcaSpeFitReceiptV2", "PcaSpeModelV2", "PcaSpeThresholdReceiptV2",
    "PcaSpeV2ContractError", "calibrate_pca_spe_threshold_v2", "fit_pca_spe_v2",
    "predict_pca_spe_v2", "score_pca_spe_v2", "strict_alarm_mask_pca_spe_v2",
]
