"""Deterministic candidate-universe builder.

The mask orientation is target-major: mask[target_index][source_index].
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

from paperworks.data import DataViewManifest, SplitManifest, SplitRole, assert_split_permitted
from paperworks.data.contracts import SCHEMA_VERSION, stable_hash
from paperworks.metadata import MetadataRegistry, ValueType, VariableMetadata, VariableRole


class CandidateUniverseError(ValueError):
    """Raised when candidate-universe inputs or policies are invalid."""


class CandidateTargetStatus(str, Enum):
    SUPPORTED_WITH_CANDIDATES = "supported_with_candidates"
    UNSUPPORTED_EMPTY_SET = "unsupported_empty_set"
    EXPANDED_BY_CONFIGURED_FALLBACK = "expanded_by_configured_fallback"


@dataclass(frozen=True)
class CandidatePolicy:
    """Explicit policy for building a target-specific candidate universe."""

    policy_version: str = "1.0"
    source_roles: tuple[VariableRole, ...] = (VariableRole.ACTUATOR,)
    source_value_types: tuple[ValueType, ...] = (ValueType.BINARY,)
    target_roles: tuple[VariableRole, ...] = (VariableRole.SENSOR,)
    target_value_types: tuple[ValueType, ...] = (ValueType.CONTINUOUS,)
    domain_same_stage: bool = True
    statistical_top_m: int = 0
    statistical_max_lag_samples: int = 0
    fallback_min_candidates_per_target: int = 0

    def __post_init__(self) -> None:
        if not self.policy_version:
            raise CandidateUniverseError("policy_version is required")
        if self.statistical_top_m < 0:
            raise CandidateUniverseError("statistical_top_m must be non-negative")
        if self.statistical_max_lag_samples < 0:
            raise CandidateUniverseError("statistical_max_lag_samples must be non-negative")
        if self.fallback_min_candidates_per_target < 0:
            raise CandidateUniverseError("fallback_min_candidates_per_target must be non-negative")
        if not self.source_roles or not self.source_value_types or not self.target_roles or not self.target_value_types:
            raise CandidateUniverseError("source and target type policies must be non-empty")

    @property
    def statistical_enabled(self) -> bool:
        return self.statistical_top_m > 0

    @property
    def fallback_enabled(self) -> bool:
        return self.fallback_min_candidates_per_target > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_version": self.policy_version,
            "source_roles": [item.value for item in self.source_roles],
            "source_value_types": [item.value for item in self.source_value_types],
            "target_roles": [item.value for item in self.target_roles],
            "target_value_types": [item.value for item in self.target_value_types],
            "domain_same_stage": self.domain_same_stage,
            "statistical_top_m": self.statistical_top_m,
            "statistical_max_lag_samples": self.statistical_max_lag_samples,
            "fallback_min_candidates_per_target": self.fallback_min_candidates_per_target,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CandidatePolicy":
        return cls(
            policy_version=str(data.get("policy_version", "1.0")),
            source_roles=tuple(VariableRole(str(item)) for item in data["source_roles"]),
            source_value_types=tuple(ValueType(str(item)) for item in data["source_value_types"]),
            target_roles=tuple(VariableRole(str(item)) for item in data["target_roles"]),
            target_value_types=tuple(ValueType(str(item)) for item in data["target_value_types"]),
            domain_same_stage=bool(data.get("domain_same_stage", True)),
            statistical_top_m=int(data.get("statistical_top_m", 0)),
            statistical_max_lag_samples=int(data.get("statistical_max_lag_samples", 0)),
            fallback_min_candidates_per_target=int(data.get("fallback_min_candidates_per_target", 0)),
        )


@dataclass(frozen=True)
class CandidatePair:
    source: str
    target: str
    allowed: bool
    origins: tuple[str, ...]
    origin_scores: Mapping[str, float] = field(default_factory=dict)
    policy_version: str = "1.0"
    metadata_artifact_id: str = ""
    normal_summary_artifact_id: str | None = None
    feature_order_hash: str = ""

    def __post_init__(self) -> None:
        if not self.source or not self.target:
            raise CandidateUniverseError("source and target are required")
        if self.source == self.target:
            raise CandidateUniverseError("candidate self-edges are prohibited")
        if self.allowed and not self.origins:
            raise CandidateUniverseError("allowed candidates must have at least one origin")
        if len(self.feature_order_hash) != 64:
            raise CandidateUniverseError("feature_order_hash must be a 64-character hash")
        if self.normal_summary_artifact_id is not None and len(self.normal_summary_artifact_id) != 64:
            raise CandidateUniverseError("normal_summary_artifact_id must be a 64-character hash")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["origins"] = list(self.origins)
        data["origin_scores"] = dict(self.origin_scores)
        return data


@dataclass(frozen=True)
class CandidateUniverseArtifact:
    dataset_manifest_id: str
    split_name: str
    source_view: str
    sampling_period_seconds: float
    metadata_artifact_id: str
    policy_version: str
    policy: Mapping[str, Any]
    feature_order: tuple[str, ...]
    feature_order_hash: str
    pairs: tuple[CandidatePair, ...]
    target_status: Mapping[str, CandidateTargetStatus]
    target_candidate_counts: Mapping[str, int]
    empty_targets: tuple[str, ...]
    normal_summary_artifact_id: str | None = None
    code_commit: str | None = None
    created_at: str = "unspecified"
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "candidate_universe"

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise CandidateUniverseError(f"unsupported schema_version: {self.schema_version}")
        if self.artifact_type != "candidate_universe":
            raise CandidateUniverseError("artifact_type must be candidate_universe")
        if len(self.dataset_manifest_id) != 64:
            raise CandidateUniverseError("dataset_manifest_id must be a 64-character hash")
        if len(self.metadata_artifact_id) != 64:
            raise CandidateUniverseError("metadata_artifact_id must be a 64-character hash")
        if len(self.feature_order_hash) != 64:
            raise CandidateUniverseError("feature_order_hash must be a 64-character hash")
        if self.sampling_period_seconds <= 0:
            raise CandidateUniverseError("sampling_period_seconds must be positive")
        if self.normal_summary_artifact_id is not None and len(self.normal_summary_artifact_id) != 64:
            raise CandidateUniverseError("normal_summary_artifact_id must be a 64-character hash")
        if not self.feature_order:
            raise CandidateUniverseError("feature_order is required")
        feature_set = set(self.feature_order)
        for pair in self.pairs:
            if pair.source not in feature_set or pair.target not in feature_set:
                raise CandidateUniverseError("candidate pair is not aligned to feature_order")
            if pair.feature_order_hash != self.feature_order_hash:
                raise CandidateUniverseError("candidate pair feature_order_hash mismatch")
        for target in self.feature_order:
            if target not in self.target_status:
                raise CandidateUniverseError(f"missing target status for {target}")
            if target not in self.target_candidate_counts:
                raise CandidateUniverseError(f"missing target candidate count for {target}")

    @property
    def artifact_id(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "dataset_manifest_id": self.dataset_manifest_id,
            "split_name": self.split_name,
            "source_view": self.source_view,
            "sampling_period_seconds": self.sampling_period_seconds,
            "metadata_artifact_id": self.metadata_artifact_id,
            "normal_summary_artifact_id": self.normal_summary_artifact_id,
            "policy_version": self.policy_version,
            "policy": dict(self.policy),
            "feature_order": list(self.feature_order),
            "feature_order_hash": self.feature_order_hash,
            "pairs": [pair.to_dict() for pair in self.pairs],
            "target_status": {key: value.value for key, value in self.target_status.items()},
            "target_candidate_counts": dict(self.target_candidate_counts),
            "empty_targets": list(self.empty_targets),
            "code_commit": self.code_commit,
            "created_at": self.created_at,
        }


def build_candidate_universe(
    *,
    metadata: MetadataRegistry,
    feature_order: Sequence[str],
    policy: CandidatePolicy,
    split: SplitManifest,
    data_view: DataViewManifest,
    metadata_artifact_id: str,
    normal_data: Mapping[str, Sequence[float]] | None = None,
    normal_summary_artifact_id: str | None = None,
    code_commit: str | None = None,
    created_at: str = "unspecified",
) -> CandidateUniverseArtifact:
    """Build a deterministic candidate universe aligned to feature_order."""

    assert_split_permitted(split.role, "train_candidate_learner")
    ordered_features = tuple(feature_order)
    _validate_feature_order(ordered_features, metadata)
    if len(metadata_artifact_id) != 64:
        raise CandidateUniverseError("metadata_artifact_id must be a 64-character hash")
    if policy.statistical_enabled:
        if normal_data is None:
            raise CandidateUniverseError("normal_data is required when statistical_top_m is enabled")
        if split.role != SplitRole.TRAIN_NORMAL:
            raise CandidateUniverseError("statistical candidates require train_normal split")
        _validate_normal_data(normal_data, ordered_features)

    feature_order_hash = stable_hash({"feature_order": list(ordered_features)})
    pair_builders: dict[tuple[str, str], dict[str, Any]] = {}
    fallback_expanded_targets: set[str] = set()

    for target in ordered_features:
        target_meta = metadata.get(target)
        if not _is_target_compatible(target_meta, policy):
            continue
        for source in ordered_features:
            if source == target:
                continue
            source_meta = metadata.get(source)
            if not _is_source_compatible(source_meta, policy):
                continue
            if policy.domain_same_stage and _same_stage_or_subsystem(source_meta, target_meta):
                _add_origin(pair_builders, source, target, "domain")

        if policy.statistical_enabled and normal_data is not None:
            scores = _statistical_scores_for_target(
                target=target,
                feature_order=ordered_features,
                metadata=metadata,
                policy=policy,
                normal_data=normal_data,
            )
            for source, score in scores[: policy.statistical_top_m]:
                _add_origin(pair_builders, source, target, "stat", score)

    if policy.fallback_enabled:
        for target in ordered_features:
            target_meta = metadata.get(target)
            if not _is_target_compatible(target_meta, policy):
                continue
            current_count = sum(1 for (_, pair_target) in pair_builders if pair_target == target)
            if current_count >= policy.fallback_min_candidates_per_target:
                continue
            for source in ordered_features:
                if current_count >= policy.fallback_min_candidates_per_target:
                    break
                if source == target:
                    continue
                source_meta = metadata.get(source)
                if not _is_source_compatible(source_meta, policy):
                    continue
                key = (source, target)
                if key not in pair_builders:
                    _add_origin(pair_builders, source, target, "fallback")
                    fallback_expanded_targets.add(target)
                    current_count += 1

    pairs = tuple(
        CandidatePair(
            source=source,
            target=target,
            allowed=True,
            origins=tuple(sorted(data["origins"])),
            origin_scores=dict(sorted(data["origin_scores"].items())),
            policy_version=policy.policy_version,
            metadata_artifact_id=metadata_artifact_id,
            normal_summary_artifact_id=normal_summary_artifact_id,
            feature_order_hash=feature_order_hash,
        )
        for (source, target), data in sorted(pair_builders.items(), key=lambda item: (item[0][1], item[0][0]))
    )

    counts: dict[str, int] = {target: 0 for target in ordered_features}
    for pair in pairs:
        counts[pair.target] += 1

    statuses: dict[str, CandidateTargetStatus] = {}
    for target in ordered_features:
        if counts[target] == 0:
            statuses[target] = CandidateTargetStatus.UNSUPPORTED_EMPTY_SET
        elif target in fallback_expanded_targets:
            statuses[target] = CandidateTargetStatus.EXPANDED_BY_CONFIGURED_FALLBACK
        else:
            statuses[target] = CandidateTargetStatus.SUPPORTED_WITH_CANDIDATES

    return CandidateUniverseArtifact(
        dataset_manifest_id=split.dataset_manifest_id,
        split_name=split.role.value,
        source_view=data_view.source_view or data_view.name.value,
        sampling_period_seconds=data_view.sampling_period_seconds,
        metadata_artifact_id=metadata_artifact_id,
        normal_summary_artifact_id=normal_summary_artifact_id,
        policy_version=policy.policy_version,
        policy=policy.to_dict(),
        feature_order=ordered_features,
        feature_order_hash=feature_order_hash,
        pairs=pairs,
        target_status=statuses,
        target_candidate_counts=counts,
        empty_targets=tuple(target for target in ordered_features if counts[target] == 0),
        code_commit=code_commit,
        created_at=created_at,
    )


def candidate_mask(artifact: CandidateUniverseArtifact) -> tuple[tuple[bool, ...], ...]:
    """Return target-major boolean mask: mask[target_index][source_index]."""

    index = {name: position for position, name in enumerate(artifact.feature_order)}
    matrix = [[False for _ in artifact.feature_order] for _ in artifact.feature_order]
    for pair in artifact.pairs:
        matrix[index[pair.target]][index[pair.source]] = pair.allowed
    return tuple(tuple(row) for row in matrix)


def indexed_candidates_by_target(artifact: CandidateUniverseArtifact) -> Mapping[str, tuple[int, ...]]:
    """Return source indexes per target, aligned to artifact.feature_order."""

    index = {name: position for position, name in enumerate(artifact.feature_order)}
    by_target: dict[str, list[int]] = {target: [] for target in artifact.feature_order}
    for pair in artifact.pairs:
        by_target[pair.target].append(index[pair.source])
    return {target: tuple(sorted(indexes)) for target, indexes in by_target.items()}


def _validate_feature_order(feature_order: tuple[str, ...], metadata: MetadataRegistry) -> None:
    if not feature_order:
        raise CandidateUniverseError("feature_order is required")
    if len(set(feature_order)) != len(feature_order):
        raise CandidateUniverseError("feature_order must not contain duplicates")
    missing = [name for name in feature_order if name not in metadata]
    if missing:
        raise CandidateUniverseError(f"metadata missing for feature_order entries: {missing}")


def _validate_normal_data(normal_data: Mapping[str, Sequence[float]], feature_order: tuple[str, ...]) -> None:
    lengths: set[int] = set()
    for name in feature_order:
        if name not in normal_data:
            raise CandidateUniverseError(f"normal_data missing feature: {name}")
        values = normal_data[name]
        if len(values) < 2:
            raise CandidateUniverseError("normal_data series must contain at least two samples")
        lengths.add(len(values))
    if len(lengths) != 1:
        raise CandidateUniverseError("normal_data series must have equal lengths")


def _is_source_compatible(metadata: VariableMetadata, policy: CandidatePolicy) -> bool:
    return metadata.role in policy.source_roles and metadata.value_type in policy.source_value_types


def _is_target_compatible(metadata: VariableMetadata, policy: CandidatePolicy) -> bool:
    return metadata.role in policy.target_roles and metadata.value_type in policy.target_value_types


def _same_stage_or_subsystem(source: VariableMetadata, target: VariableMetadata) -> bool:
    return (
        (source.stage is not None and source.stage == target.stage)
        or (source.subsystem is not None and source.subsystem == target.subsystem)
    )


def _add_origin(
    pair_builders: dict[tuple[str, str], dict[str, Any]],
    source: str,
    target: str,
    origin: str,
    score: float | None = None,
) -> None:
    builder = pair_builders.setdefault((source, target), {"origins": set(), "origin_scores": {}})
    builder["origins"].add(origin)
    if score is not None:
        builder["origin_scores"][origin] = score


def _statistical_scores_for_target(
    *,
    target: str,
    feature_order: tuple[str, ...],
    metadata: MetadataRegistry,
    policy: CandidatePolicy,
    normal_data: Mapping[str, Sequence[float]],
) -> list[tuple[str, float]]:
    scores: list[tuple[str, float]] = []
    for source in feature_order:
        if source == target:
            continue
        if not _is_source_compatible(metadata.get(source), policy):
            continue
        score = _max_abs_lagged_pearson(
            source_values=normal_data[source],
            target_values=normal_data[target],
            max_lag_samples=policy.statistical_max_lag_samples,
        )
        if not math.isnan(score):
            scores.append((source, score))
    return sorted(scores, key=lambda item: (-item[1], item[0]))


def _max_abs_lagged_pearson(
    *,
    source_values: Sequence[float],
    target_values: Sequence[float],
    max_lag_samples: int,
) -> float:
    best = math.nan
    for lag in range(max_lag_samples + 1):
        if lag == 0:
            source_slice = source_values
            target_slice = target_values
        else:
            source_slice = source_values[:-lag]
            target_slice = target_values[lag:]
        score = _abs_pearson(source_slice, target_slice)
        if not math.isnan(score) and (math.isnan(best) or score > best):
            best = score
    return best


def _abs_pearson(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        return math.nan
    left_values = [float(item) for item in left]
    right_values = [float(item) for item in right]
    left_mean = sum(left_values) / len(left_values)
    right_mean = sum(right_values) / len(right_values)
    numerator = sum((l_value - left_mean) * (r_value - right_mean) for l_value, r_value in zip(left_values, right_values))
    left_denom = math.sqrt(sum((l_value - left_mean) ** 2 for l_value in left_values))
    right_denom = math.sqrt(sum((r_value - right_mean) ** 2 for r_value in right_values))
    denominator = left_denom * right_denom
    if denominator == 0:
        return math.nan
    return abs(numerator / denominator)
