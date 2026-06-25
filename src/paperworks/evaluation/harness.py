"""Restricted evaluation harness and PA-free metric utilities."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from paperworks.data import SplitRole
from paperworks.data.contracts import SCHEMA_VERSION, stable_hash


class EvaluationError(ValueError):
    """Raised when evaluation policy, metrics, or provenance are invalid."""


@dataclass(frozen=True)
class EvaluationMetric:
    name: str
    value: float | int | None
    scope: str
    primary: bool
    point_adjusted: bool = False

    def __post_init__(self) -> None:
        if not self.name:
            raise EvaluationError("metric name is required")
        if self.primary and self.point_adjusted:
            raise EvaluationError("point-adjusted metrics cannot be primary")
        if self.scope not in {"point", "event", "range", "candidate", "rule", "audit"}:
            raise EvaluationError(f"unsupported metric scope: {self.scope}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvaluationConfig:
    config_name: str
    thresholds_frozen: bool
    candidate_k_frozen: bool
    prompt_config_frozen: bool
    fusion_weights_frozen: bool = True
    point_adjusted_supplementary_enabled: bool = False
    primary_metric_names: tuple[str, ...] = ("pa_free_precision", "pa_free_recall", "pa_free_f1")
    supplementary_metric_names: tuple[str, ...] = ()
    config_version: str = "1.0"

    def __post_init__(self) -> None:
        if not self.config_name:
            raise EvaluationError("config_name is required")
        if any(name.startswith("point_adjusted") for name in self.primary_metric_names):
            raise EvaluationError("point-adjusted metrics cannot be primary")

    @property
    def config_hash(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["primary_metric_names"] = list(self.primary_metric_names)
        data["supplementary_metric_names"] = list(self.supplementary_metric_names)
        return data


@dataclass(frozen=True)
class EvaluationProtocol:
    dataset_name: str
    dataset_status: str
    terms_of_use_status: str
    dataset_manifest_id: str
    split_manifest_ids: Mapping[str, str]
    dec007_resolved: bool
    final_test_access_approved: bool
    config: EvaluationConfig
    protocol_version: str = "1.0"

    def __post_init__(self) -> None:
        if len(self.dataset_manifest_id) != 64:
            raise EvaluationError("dataset_manifest_id must be a 64-character hash")
        for split_name, split_id in self.split_manifest_ids.items():
            if len(split_id) != 64:
                raise EvaluationError(f"split manifest id for {split_name} must be a 64-character hash")
        if self.final_test_access_approved and not self.dec007_resolved:
            raise EvaluationError("final test access cannot be approved while DEC-007 is unresolved")

    @property
    def protocol_hash(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol_version": self.protocol_version,
            "dataset_name": self.dataset_name,
            "dataset_status": self.dataset_status,
            "terms_of_use_status": self.terms_of_use_status,
            "dataset_manifest_id": self.dataset_manifest_id,
            "split_manifest_ids": dict(sorted(self.split_manifest_ids.items())),
            "dec007_resolved": self.dec007_resolved,
            "final_test_access_approved": self.final_test_access_approved,
            "config": self.config.to_dict(),
            "config_hash": self.config.config_hash,
        }


@dataclass(frozen=True)
class SealedTestAudit:
    requested_split_role: SplitRole
    final_test_accessed: bool
    final_test_access_approved: bool
    dec007_resolved: bool
    config_frozen: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "requested_split_role": self.requested_split_role.value,
            "final_test_accessed": self.final_test_accessed,
            "final_test_access_approved": self.final_test_access_approved,
            "dec007_resolved": self.dec007_resolved,
            "config_frozen": self.config_frozen,
        }


@dataclass(frozen=True)
class EvaluationReport:
    dataset: str
    split_role: SplitRole
    primary_metrics: tuple[EvaluationMetric, ...]
    supplementary_metrics: tuple[EvaluationMetric, ...]
    protocol_hash: str
    config_hash: str
    artifact_provenance: Mapping[str, str]
    sealed_test_audit: SealedTestAudit
    manifest_checks: Mapping[str, bool]
    limitations: tuple[str, ...]
    code_commit: str | None
    created_at: str
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "evaluation_report"

    def __post_init__(self) -> None:
        if any(metric.point_adjusted for metric in self.primary_metrics):
            raise EvaluationError("primary metrics must be PA-free")
        if self.sealed_test_audit.final_test_accessed and not self.sealed_test_audit.final_test_access_approved:
            raise EvaluationError("sealed final test was accessed without approval")
        if len(self.protocol_hash) != 64 or len(self.config_hash) != 64:
            raise EvaluationError("protocol_hash and config_hash must be 64-character hashes")

    @property
    def report_id(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "dataset": self.dataset,
            "split_role": self.split_role.value,
            "primary_metrics": [metric.to_dict() for metric in self.primary_metrics],
            "supplementary_metrics": [metric.to_dict() for metric in self.supplementary_metrics],
            "protocol_hash": self.protocol_hash,
            "config_hash": self.config_hash,
            "artifact_provenance": dict(sorted(self.artifact_provenance.items())),
            "sealed_test_audit": self.sealed_test_audit.to_dict(),
            "manifest_checks": dict(sorted(self.manifest_checks.items())),
            "limitations": list(self.limitations),
            "code_commit": self.code_commit,
            "created_at": self.created_at,
        }


def validate_config_frozen(config: EvaluationConfig) -> None:
    if not (
        config.thresholds_frozen
        and config.candidate_k_frozen
        and config.prompt_config_frozen
        and config.fusion_weights_frozen
    ):
        raise EvaluationError("evaluation config must be frozen before evaluation")


def validate_artifact_provenance(artifact_provenance: Mapping[str, str]) -> None:
    required = {
        "dataset_manifest",
        "split_manifest",
        "config",
        "runtime_or_prediction_artifact",
    }
    missing = sorted(required - set(artifact_provenance))
    if missing:
        raise EvaluationError(f"missing artifact provenance fields: {missing}")
    for key, value in artifact_provenance.items():
        if len(value) != 64:
            raise EvaluationError(f"artifact provenance value for {key} must be a 64-character hash")


def assert_final_test_access_allowed(protocol: EvaluationProtocol, split_role: SplitRole) -> SealedTestAudit:
    config_frozen = _config_is_frozen(protocol.config)
    final_test_accessed = split_role == SplitRole.TEST
    audit = SealedTestAudit(
        requested_split_role=split_role,
        final_test_accessed=final_test_accessed,
        final_test_access_approved=protocol.final_test_access_approved,
        dec007_resolved=protocol.dec007_resolved,
        config_frozen=config_frozen,
    )
    if not final_test_accessed:
        return audit
    if not protocol.dec007_resolved:
        raise EvaluationError("DEC-007 must be resolved before final test access")
    if not protocol.final_test_access_approved:
        raise EvaluationError("final test access is not approved")
    validate_config_frozen(protocol.config)
    return audit


def evaluate_point_predictions(
    *,
    labels: Sequence[int | bool],
    predictions: Sequence[int | bool],
    scores: Sequence[float] | None,
    split_role: SplitRole,
    protocol: EvaluationProtocol,
    artifact_provenance: Mapping[str, str],
    code_commit: str | None = None,
    created_at: str = "unspecified",
) -> EvaluationReport:
    audit = assert_final_test_access_allowed(protocol, split_role)
    if split_role != SplitRole.TEST:
        validate_config_frozen(protocol.config)
    validate_artifact_provenance(artifact_provenance)
    primary = list(compute_pa_free_point_metrics(labels, predictions))
    if scores is not None:
        primary.append(EvaluationMetric("auroc", compute_auroc(labels, scores), "point", primary=True))
        primary.append(EvaluationMetric("auprc", compute_auprc(labels, scores), "point", primary=True))

    supplementary: list[EvaluationMetric] = []
    if protocol.config.point_adjusted_supplementary_enabled:
        supplementary.extend(compute_point_adjusted_supplement(labels, predictions))

    manifest_checks = {
        "dataset_manifest_present": bool(protocol.dataset_manifest_id),
        "split_manifest_present": bool(protocol.split_manifest_ids),
        "config_frozen": _config_is_frozen(protocol.config),
        "dec007_resolved": protocol.dec007_resolved,
        "final_test_access_approved": protocol.final_test_access_approved,
    }
    limitations = _limitations(protocol, split_role)
    return EvaluationReport(
        dataset=protocol.dataset_name,
        split_role=split_role,
        primary_metrics=tuple(primary),
        supplementary_metrics=tuple(supplementary),
        protocol_hash=protocol.protocol_hash,
        config_hash=protocol.config.config_hash,
        artifact_provenance=artifact_provenance,
        sealed_test_audit=audit,
        manifest_checks=manifest_checks,
        limitations=limitations,
        code_commit=code_commit,
        created_at=created_at,
    )


def compute_pa_free_point_metrics(
    labels: Sequence[int | bool],
    predictions: Sequence[int | bool],
) -> tuple[EvaluationMetric, ...]:
    y_true, y_pred = _binary_vectors(labels, predictions)
    tp = sum(1 for truth, pred in zip(y_true, y_pred) if truth and pred)
    fp = sum(1 for truth, pred in zip(y_true, y_pred) if not truth and pred)
    fn = sum(1 for truth, pred in zip(y_true, y_pred) if truth and not pred)
    tn = sum(1 for truth, pred in zip(y_true, y_pred) if not truth and not pred)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return (
        EvaluationMetric("pa_free_tp", tp, "point", primary=True),
        EvaluationMetric("pa_free_fp", fp, "point", primary=True),
        EvaluationMetric("pa_free_fn", fn, "point", primary=True),
        EvaluationMetric("pa_free_tn", tn, "point", primary=True),
        EvaluationMetric("pa_free_precision", precision, "point", primary=True),
        EvaluationMetric("pa_free_recall", recall, "point", primary=True),
        EvaluationMetric("pa_free_f1", f1, "point", primary=True),
    )


def compute_auroc(labels: Sequence[int | bool], scores: Sequence[float]) -> float | None:
    y_true = _binary_labels(labels)
    if len(y_true) != len(scores):
        raise EvaluationError("labels and scores must have equal length")
    positive_count = sum(y_true)
    negative_count = len(y_true) - positive_count
    if positive_count == 0 or negative_count == 0:
        return None
    ranks = _average_ranks(scores)
    positive_rank_sum = sum(rank for truth, rank in zip(y_true, ranks) if truth)
    return (positive_rank_sum - positive_count * (positive_count + 1) / 2) / (positive_count * negative_count)


def compute_auprc(labels: Sequence[int | bool], scores: Sequence[float]) -> float | None:
    y_true = _binary_labels(labels)
    if len(y_true) != len(scores):
        raise EvaluationError("labels and scores must have equal length")
    positive_count = sum(y_true)
    if positive_count == 0:
        return None
    ordered = sorted(zip(scores, y_true), key=lambda item: item[0], reverse=True)
    tp = 0
    fp = 0
    precision_sum = 0.0
    for _, truth in ordered:
        if truth:
            tp += 1
            precision_sum += tp / (tp + fp)
        else:
            fp += 1
    return precision_sum / positive_count


def compute_point_adjusted_supplement(
    labels: Sequence[int | bool],
    predictions: Sequence[int | bool],
) -> tuple[EvaluationMetric, ...]:
    y_true, y_pred = _binary_vectors(labels, predictions)
    adjusted = list(y_pred)
    for start, end in _positive_ranges(y_true):
        if any(adjusted[index] for index in range(start, end)):
            for index in range(start, end):
                adjusted[index] = True
    metrics = compute_pa_free_point_metrics(y_true, adjusted)
    return tuple(
        EvaluationMetric(
            name=f"point_adjusted_{metric.name.removeprefix('pa_free_')}",
            value=metric.value,
            scope=metric.scope,
            primary=False,
            point_adjusted=True,
        )
        for metric in metrics
    )


def compute_range_iou(
    truth_ranges: Sequence[tuple[int, int]],
    predicted_ranges: Sequence[tuple[int, int]],
) -> EvaluationMetric:
    truth = _range_points(truth_ranges)
    predicted = _range_points(predicted_ranges)
    union = truth | predicted
    value = (len(truth & predicted) / len(union)) if union else 1.0
    return EvaluationMetric("range_iou", value, "range", primary=True)


def _binary_vectors(
    labels: Sequence[int | bool],
    predictions: Sequence[int | bool],
) -> tuple[tuple[bool, ...], tuple[bool, ...]]:
    y_true = _binary_labels(labels)
    y_pred = _binary_labels(predictions)
    if len(y_true) != len(y_pred):
        raise EvaluationError("labels and predictions must have equal length")
    return y_true, y_pred


def _binary_labels(values: Sequence[int | bool]) -> tuple[bool, ...]:
    labels: list[bool] = []
    for value in values:
        if value not in (0, 1, False, True):
            raise EvaluationError("binary labels must be 0/1 or bool")
        labels.append(bool(value))
    return tuple(labels)


def _average_ranks(scores: Sequence[float]) -> tuple[float, ...]:
    indexed = sorted(enumerate(float(score) for score in scores), key=lambda item: item[1])
    ranks = [0.0] * len(scores)
    cursor = 0
    while cursor < len(indexed):
        tie_end = cursor + 1
        while tie_end < len(indexed) and indexed[tie_end][1] == indexed[cursor][1]:
            tie_end += 1
        average_rank = (cursor + 1 + tie_end) / 2
        for index in range(cursor, tie_end):
            ranks[indexed[index][0]] = average_rank
        cursor = tie_end
    return tuple(ranks)


def _positive_ranges(labels: Sequence[bool]) -> tuple[tuple[int, int], ...]:
    ranges: list[tuple[int, int]] = []
    start: int | None = None
    for index, value in enumerate(labels):
        if value and start is None:
            start = index
        elif not value and start is not None:
            ranges.append((start, index))
            start = None
    if start is not None:
        ranges.append((start, len(labels)))
    return tuple(ranges)


def _range_points(ranges: Sequence[tuple[int, int]]) -> set[int]:
    points: set[int] = set()
    for start, end in ranges:
        if start < 0 or end < start:
            raise EvaluationError(f"invalid range: {(start, end)}")
        points.update(range(start, end))
    return points


def _config_is_frozen(config: EvaluationConfig) -> bool:
    return (
        config.thresholds_frozen
        and config.candidate_k_frozen
        and config.prompt_config_frozen
        and config.fusion_weights_frozen
    )


def _limitations(protocol: EvaluationProtocol, split_role: SplitRole) -> tuple[str, ...]:
    limitations: list[str] = []
    if not protocol.dec007_resolved:
        limitations.append("DEC-007 is unresolved; final SWaT evaluation is prohibited.")
    if split_role != SplitRole.TEST:
        limitations.append("Report was generated on a non-test split or synthetic fixture; it is not a final benchmark claim.")
    if protocol.dataset_status != "official_verified":
        limitations.append("Dataset provenance is not marked official_verified.")
    if protocol.terms_of_use_status != "verified":
        limitations.append("Dataset terms-of-use status is not verified.")
    return tuple(limitations)
