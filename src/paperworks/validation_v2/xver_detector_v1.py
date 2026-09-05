"""Schema-bound external re-instantiation of the frozen V2 PCA/IF methods.

This adapter changes only dataset/split/feature authority.  The mathematical
detector configurations are imported from the immutable HAI23 implementations.
It accepts already sealed normal feature projections and has no label, attack,
provider, or network interface.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
import pickle
from typing import Any, Mapping

from .pca_spe_v2 import PcaSpeConfigV2
from .isolation_forest_v1 import IsolationForestConfigV1


class ExternalDetectorError(ValueError):
    pass


def _bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest(value: Mapping[str, Any]) -> str:
    return sha256(_bytes(value)).hexdigest()


def _hex64(value: str, field: str) -> None:
    if type(value) is not str or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ExternalDetectorError(f"{field} must be lowercase sha256")


def _np() -> Any:
    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover
        raise ExternalDetectorError("NumPy is required") from exc
    return np


@dataclass(frozen=True)
class ExternalNormalMatrixV1:
    dataset_version: str
    split_id: str
    projection_hash: str
    feature_ids: tuple[str, ...]
    values: Any


@dataclass(frozen=True)
class ExternalMatrixBindingV1:
    dataset_version: str
    split_id: str
    projection_hash: str
    feature_order_hash: str
    row_count: int
    feature_count: int
    matrix_hash: str

    def document(self) -> dict[str, Any]:
        return dict(self.__dict__)


def normalize_external_matrix_v1(
    value: ExternalNormalMatrixV1, *, expected_version: str,
    expected_split: str, expected_features: tuple[str, ...]
) -> tuple[Any, ExternalMatrixBindingV1]:
    if type(value) is not ExternalNormalMatrixV1:
        raise ExternalDetectorError("typed external normal matrix required")
    if value.dataset_version != expected_version or value.split_id != expected_split:
        raise ExternalDetectorError("external dataset/split authority mismatch")
    _hex64(value.projection_hash, "projection_hash")
    if value.feature_ids != expected_features or len(expected_features) < 2 or len(set(expected_features)) != len(expected_features):
        raise ExternalDetectorError("feature authority/order mismatch")
    if any(not isinstance(item, str) or not item.startswith("P1_") for item in expected_features):
        raise ExternalDetectorError("non-P1 feature rejected")
    np = _np()
    matrix = np.ascontiguousarray(value.values, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape != (len(matrix), len(expected_features)) or len(matrix) == 0:
        raise ExternalDetectorError("invalid external matrix shape")
    if not bool(np.isfinite(matrix).all()):
        raise ExternalDetectorError("nonfinite external projection")
    feature_hash = sha256(_bytes({"feature_ids": list(expected_features)})).hexdigest()
    matrix_hash = sha256(memoryview(matrix).cast("B")).hexdigest()
    return matrix, ExternalMatrixBindingV1(
        expected_version, expected_split, value.projection_hash, feature_hash,
        int(matrix.shape[0]), int(matrix.shape[1]), matrix_hash,
    )


@dataclass(frozen=True)
class ExternalPcaModelV1:
    feature_ids: tuple[str, ...]
    mean: Any
    scale: Any
    loadings: Any
    fit_authority: Mapping[str, Any]


@dataclass(frozen=True)
class ExternalIfModelV1:
    feature_ids: tuple[str, ...]
    estimator: Any
    fit_authority: Mapping[str, Any]


def _pca_state_hash(mean: Any, scale: Any, loadings: Any) -> str:
    np = _np(); h = sha256()
    for value in (mean, scale, loadings):
        h.update(memoryview(np.ascontiguousarray(value, dtype=np.float64)).cast("B"))
    return h.hexdigest()


def fit_external_pca_v1(
    train1: ExternalNormalMatrixV1, train2: ExternalNormalMatrixV1, *,
    version: str, feature_ids: tuple[str, ...], source_commit: str,
    preregistration_hash: str,
) -> ExternalPcaModelV1:
    config = PcaSpeConfigV2(); config.validate(); _hex64(preregistration_hash, "preregistration_hash")
    first, b1 = normalize_external_matrix_v1(train1, expected_version=version, expected_split="train1", expected_features=feature_ids)
    second, b2 = normalize_external_matrix_v1(train2, expected_version=version, expected_split="train2", expected_features=feature_ids)
    np = _np(); matrix = np.concatenate((first, second), axis=0)
    mean = matrix.mean(axis=0); scale = np.maximum(matrix.std(axis=0, ddof=0), float.fromhex(config.scale_floor_hex))
    z = (matrix - mean) / scale
    covariance = (z.T @ z) / len(z); covariance = (covariance + covariance.T) / 2.0
    eigenvalues, vectors = np.linalg.eigh(covariance); order = np.argsort(-eigenvalues, kind="stable")
    eigenvalues = np.maximum(eigenvalues[order], 0.0); vectors = vectors[:, order]
    total = float(eigenvalues.sum())
    if not math.isfinite(total) or total <= 0:
        raise ExternalDetectorError("PCA has no positive variance")
    count = int(np.searchsorted(np.cumsum(eigenvalues) / total, .95, side="left")) + 1
    count = min(count, len(feature_ids) - 1)
    if count <= 0 or (count < len(eigenvalues) and eigenvalues[count - 1] == eigenvalues[count]):
        raise ExternalDetectorError("invalid or tied PCA component boundary")
    loadings = vectors[:, :count].copy()
    for column in range(count):
        anchor = int(np.argmax(np.abs(loadings[:, column])))
        if loadings[anchor, column] < 0: loadings[:, column] *= -1
    state_hash = _pca_state_hash(mean, scale, loadings)
    body = {
        "schema":"xver_pca_fit_authority_v1", "version":version, "source_commit":source_commit,
        "preregistration_hash":preregistration_hash, "method_config_hash":config.config_hash,
        "feature_ids":list(feature_ids), "inputs":[b1.document(), b2.document()],
        "fit_rows":int(len(matrix)), "component_count":count,
        "residual_dimension_count":len(feature_ids)-count, "model_state_hash":state_hash,
    }
    authority = {**body, "self_hash":digest(body)}
    return ExternalPcaModelV1(feature_ids, mean, scale, loadings, authority)


def score_external_pca_v1(model: ExternalPcaModelV1, value: ExternalNormalMatrixV1, *, split: str) -> tuple[Any, ExternalMatrixBindingV1]:
    matrix, binding = normalize_external_matrix_v1(value, expected_version=model.fit_authority["version"], expected_split=split, expected_features=model.feature_ids)
    np = _np(); z = (matrix-model.mean)/model.scale
    residual = z - (z @ model.loadings) @ model.loadings.T
    scores = np.einsum("ij,ij->i", residual, residual)
    if not bool(np.isfinite(scores).all()): raise ExternalDetectorError("invalid PCA scores")
    return scores, binding


def fit_external_if_v1(
    train1: ExternalNormalMatrixV1, train2: ExternalNormalMatrixV1, *,
    version: str, feature_ids: tuple[str, ...], source_commit: str,
    preregistration_hash: str,
) -> ExternalIfModelV1:
    config = IsolationForestConfigV1(); config.validate(); _hex64(preregistration_hash, "preregistration_hash")
    first, b1 = normalize_external_matrix_v1(train1, expected_version=version, expected_split="train1", expected_features=feature_ids)
    second, b2 = normalize_external_matrix_v1(train2, expected_version=version, expected_split="train2", expected_features=feature_ids)
    try:
        from sklearn.ensemble import IsolationForest
    except ImportError as exc:  # pragma: no cover
        raise ExternalDetectorError("scikit-learn is required") from exc
    np = _np(); matrix = np.concatenate((first,second),axis=0)
    estimator = IsolationForest(n_estimators=config.n_estimators,max_samples=config.max_samples,max_features=config.max_features,
        bootstrap=config.bootstrap,contamination=config.contamination,random_state=config.random_state,n_jobs=config.n_jobs,
        verbose=config.verbose,warm_start=config.warm_start).fit(matrix)
    state_hash = sha256(pickle.dumps(estimator, protocol=5)).hexdigest()
    body={"schema":"xver_if_fit_authority_v1","version":version,"source_commit":source_commit,
          "preregistration_hash":preregistration_hash,"method_config_hash":config.config_hash,
          "feature_ids":list(feature_ids),"inputs":[b1.document(),b2.document()],"fit_rows":int(len(matrix)),
          "effective_max_samples":int(estimator.max_samples_),"model_state_hash":state_hash}
    return ExternalIfModelV1(feature_ids,estimator,{**body,"self_hash":digest(body)})


def score_external_if_v1(model: ExternalIfModelV1, value: ExternalNormalMatrixV1, *, split: str) -> tuple[Any, ExternalMatrixBindingV1]:
    matrix,binding=normalize_external_matrix_v1(value,expected_version=model.fit_authority["version"],expected_split=split,expected_features=model.feature_ids)
    np=_np(); scores=np.asarray(-model.estimator.score_samples(matrix),dtype=np.float64)
    if scores.shape!=(len(matrix),) or not bool(np.isfinite(scores).all()): raise ExternalDetectorError("invalid IF scores")
    return scores,binding


def calibrate_external_v1(scores: Any, binding: ExternalMatrixBindingV1, *, fit_hash: str, config_hash: str) -> Mapping[str, Any]:
    _hex64(fit_hash,"fit_hash"); _hex64(config_hash,"config_hash"); np=_np()
    values=np.ascontiguousarray(scores,dtype=np.float64)
    if values.ndim!=1 or len(values)==0 or not bool(np.isfinite(values).all()): raise ExternalDetectorError("invalid calibration scores")
    rank=math.ceil(999*len(values)/1000); threshold=float(np.sort(values,kind="stable")[rank-1])
    body={"schema":"xver_detector_threshold_authority_v1","fit_hash":fit_hash,"config_hash":config_hash,
          "calibration_input":binding.document(),"score_hash":sha256(memoryview(values).cast("B")).hexdigest(),
          "score_count":len(values),"quantile":"0.999","order":"NEAREST_RANK_NO_INTERPOLATION",
          "nearest_rank":rank,"threshold_hex":threshold.hex(),"comparator":"score > threshold"}
    return {**body,"self_hash":digest(body)}


def alarm_burden_v1(scores: Any, threshold_hex: str, *, file_id: str) -> Mapping[str, Any]:
    np=_np(); alarms=np.asarray(scores>float.fromhex(threshold_hex),dtype=np.bool_)
    indexes=np.flatnonzero(alarms); episodes=int(len(indexes) and (1+np.sum(np.diff(indexes)>1)))
    return {"file_id":file_id,"row_count":int(len(alarms)),"alarm_seconds":int(alarms.sum()),"alarm_episodes":episodes}


__all__=["ExternalDetectorError","ExternalNormalMatrixV1","ExternalPcaModelV1","ExternalIfModelV1",
         "fit_external_pca_v1","score_external_pca_v1","fit_external_if_v1","score_external_if_v1",
         "calibrate_external_v1","alarm_burden_v1","normalize_external_matrix_v1","digest"]
