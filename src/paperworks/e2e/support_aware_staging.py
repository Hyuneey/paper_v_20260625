"""TASK-018 support-aware Kaggle/local staging slice selection."""

from __future__ import annotations

import csv
import json
import math
from array import array
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from paperworks.data import SplitRole, resolve_data_root
from paperworks.data.contracts import SCHEMA_VERSION, stable_hash
from paperworks.data.files import parse_timestamp
from paperworks.data.staging_swat import DEFAULT_TIMESTAMP_FORMATS, TASK016_REQUIRED_REPORT_STATEMENT
from paperworks.e2e.staging_dry_run import (
    DEFAULT_TIMELINE_SOURCE,
    StagingPipelineConfig,
    StagingPipelineDryRunReport,
    run_task017_staging_pipeline_dry_run,
)
from paperworks.metadata import MetadataRegistry


TASK018_REQUIRED_REPORT_STATEMENT = TASK016_REQUIRED_REPORT_STATEMENT


class SupportAwareStagingError(ValueError):
    """Raised when TASK-018 support-aware staging inputs are unsafe."""


@dataclass(frozen=True)
class SupportSliceSelectionPolicy:
    minimum_trigger_count: int
    minimum_matched_response_count: int
    maximum_right_censored_ratio: float
    allowed_source_variables: tuple[str, ...]
    allowed_target_variables: tuple[str, ...]
    maximum_slice_length: int
    search_step: int
    require_complete_pipeline_features: bool = True
    require_regular_sampling: bool = True
    labels_policy: str = "ignored_for_selection_audit_only"
    selection_strategy: str = "first_passing_slice_by_start_index"

    def __post_init__(self) -> None:
        if self.minimum_trigger_count <= 0:
            raise SupportAwareStagingError("minimum_trigger_count must be positive")
        if self.minimum_matched_response_count <= 0:
            raise SupportAwareStagingError("minimum_matched_response_count must be positive")
        if not 0.0 <= self.maximum_right_censored_ratio <= 1.0:
            raise SupportAwareStagingError("maximum_right_censored_ratio must be in [0, 1]")
        if not self.allowed_source_variables or not self.allowed_target_variables:
            raise SupportAwareStagingError("allowed source and target variables are required")
        if self.maximum_slice_length <= 0:
            raise SupportAwareStagingError("maximum_slice_length must be positive")
        if self.search_step <= 0:
            raise SupportAwareStagingError("search_step must be positive")
        if self.labels_policy != "ignored_for_selection_audit_only":
            raise SupportAwareStagingError("TASK-018 labels must be ignored for selection")
        if self.selection_strategy != "first_passing_slice_by_start_index":
            raise SupportAwareStagingError("unsupported support-aware selection strategy")

    def to_dict(self) -> dict[str, Any]:
        return {
            "minimum_trigger_count": self.minimum_trigger_count,
            "minimum_matched_response_count": self.minimum_matched_response_count,
            "maximum_right_censored_ratio": self.maximum_right_censored_ratio,
            "allowed_source_variables": list(self.allowed_source_variables),
            "allowed_target_variables": list(self.allowed_target_variables),
            "maximum_slice_length": self.maximum_slice_length,
            "search_step": self.search_step,
            "require_complete_pipeline_features": self.require_complete_pipeline_features,
            "require_regular_sampling": self.require_regular_sampling,
            "labels_policy": self.labels_policy,
            "selection_strategy": self.selection_strategy,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SupportSliceSelectionPolicy":
        return cls(
            minimum_trigger_count=int(data["minimum_trigger_count"]),
            minimum_matched_response_count=int(data["minimum_matched_response_count"]),
            maximum_right_censored_ratio=float(data["maximum_right_censored_ratio"]),
            allowed_source_variables=tuple(str(item) for item in data["allowed_source_variables"]),
            allowed_target_variables=tuple(str(item) for item in data["allowed_target_variables"]),
            maximum_slice_length=int(data["maximum_slice_length"]),
            search_step=int(data["search_step"]),
            require_complete_pipeline_features=bool(data.get("require_complete_pipeline_features", True)),
            require_regular_sampling=bool(data.get("require_regular_sampling", True)),
            labels_policy=str(data.get("labels_policy", "ignored_for_selection_audit_only")),
            selection_strategy=str(data.get("selection_strategy", "first_passing_slice_by_start_index")),
        )


@dataclass(frozen=True)
class SupportAwareStagingConfig:
    dry_run_config: StagingPipelineConfig
    selection_policy: SupportSliceSelectionPolicy
    timeline_source: str = DEFAULT_TIMELINE_SOURCE
    timestamp_column: str = "Timestamp"
    label_column: str = "Normal/Attack"
    timestamp_formats: tuple[str, ...] = DEFAULT_TIMESTAMP_FORMATS
    schema_version: str = SCHEMA_VERSION
    config_name: str = "task018_support_aware_staging"

    def __post_init__(self) -> None:
        if self.timeline_source != DEFAULT_TIMELINE_SOURCE:
            raise SupportAwareStagingError("TASK-018 must use merged.csv as the staging timeline source")
        _validate_relative_path(self.timeline_source)
        if self.dry_run_config.timeline_sources != (DEFAULT_TIMELINE_SOURCE,):
            raise SupportAwareStagingError("dry-run config must use exactly merged.csv")
        if self.dry_run_config.required_loaded_rows > self.selection_policy.maximum_slice_length:
            raise SupportAwareStagingError("dry-run slice length exceeds selection maximum_slice_length")
        pair_sources = {source for source, _ in self.dry_run_config.profile_pairs}
        pair_targets = {target for _, target in self.dry_run_config.profile_pairs}
        if not pair_sources <= set(self.selection_policy.allowed_source_variables):
            raise SupportAwareStagingError("profile pair sources must be allowed by selection policy")
        if not pair_targets <= set(self.selection_policy.allowed_target_variables):
            raise SupportAwareStagingError("profile pair targets must be allowed by selection policy")

    @property
    def config_hash(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "config_name": self.config_name,
            "required_report_statement": TASK018_REQUIRED_REPORT_STATEMENT,
            "timeline_source": self.timeline_source,
            "timestamp_column": self.timestamp_column,
            "label_column": self.label_column,
            "timestamp_formats": list(self.timestamp_formats),
            "dry_run": self.dry_run_config.to_dict(),
            "selection_policy": self.selection_policy.to_dict(),
            "governance": {
                "source_kind": "kaggle_mirror",
                "dataset_status": "staging_only",
                "local_root_env": "SWAT_DATA_ROOT",
                "use_staging_manifest": True,
                "official_swat_manifest_allowed": False,
                "dec007_resolution_allowed": False,
                "final_claims_allowed": False,
                "labels_used_for_selection": False,
                "real_provider_network_calls": False,
                "runtime_llm": False,
                "commit_raw_rows_windows_or_plots": False,
            },
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SupportAwareStagingConfig":
        return cls(
            dry_run_config=StagingPipelineConfig.from_dict(data["dry_run"]),
            selection_policy=SupportSliceSelectionPolicy.from_dict(data["selection_policy"]),
            timeline_source=str(data.get("timeline_source", DEFAULT_TIMELINE_SOURCE)),
            timestamp_column=str(data.get("timestamp_column", "Timestamp")),
            label_column=str(data.get("label_column", "Normal/Attack")),
            timestamp_formats=tuple(str(item) for item in data.get("timestamp_formats", DEFAULT_TIMESTAMP_FORMATS)),
            schema_version=str(data.get("schema_version", SCHEMA_VERSION)),
            config_name=str(data.get("config_name", "task018_support_aware_staging")),
        )


@dataclass(frozen=True)
class PairSupportSummary:
    source: str
    target: str
    trigger_count: int
    matched_response_count: int
    missing_response_count: int
    right_censored_count: int
    observed_source_state_count: int
    target_variance_summary: Mapping[str, float]
    passes_selection_criteria: bool

    @property
    def right_censored_ratio(self) -> float:
        if self.trigger_count == 0:
            return 0.0
        return self.right_censored_count / self.trigger_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "trigger_count": self.trigger_count,
            "matched_response_count": self.matched_response_count,
            "missing_response_count": self.missing_response_count,
            "right_censored_count": self.right_censored_count,
            "right_censored_ratio": self.right_censored_ratio,
            "observed_source_state_count": self.observed_source_state_count,
            "target_variance_summary": dict(self.target_variance_summary),
            "passes_selection_criteria": self.passes_selection_criteria,
        }


@dataclass(frozen=True)
class SliceSupportSummary:
    timeline_start_index: int
    loaded_range: tuple[int, int]
    calibration_range: tuple[int, int]
    loaded_missing_value_count: int
    calibration_missing_value_count: int
    loaded_regular_sampling: bool
    calibration_regular_sampling: bool
    inferred_sampling_period_seconds: float | None
    supported_pair_count: int
    total_trigger_count: int
    total_matched_response_count: int
    passes_selection_criteria: bool
    pair_summaries: tuple[PairSupportSummary, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "timeline_start_index": self.timeline_start_index,
            "loaded_range": list(self.loaded_range),
            "calibration_range": list(self.calibration_range),
            "loaded_missing_value_count": self.loaded_missing_value_count,
            "calibration_missing_value_count": self.calibration_missing_value_count,
            "loaded_regular_sampling": self.loaded_regular_sampling,
            "calibration_regular_sampling": self.calibration_regular_sampling,
            "inferred_sampling_period_seconds": self.inferred_sampling_period_seconds,
            "supported_pair_count": self.supported_pair_count,
            "total_trigger_count": self.total_trigger_count,
            "total_matched_response_count": self.total_matched_response_count,
            "passes_selection_criteria": self.passes_selection_criteria,
            "pair_summaries": [summary.to_dict() for summary in self.pair_summaries],
        }


@dataclass(frozen=True)
class SupportScanReport:
    report_statement: str
    config_hash: str
    used_source_files: tuple[str, ...]
    labels_used_for_selection: bool
    scanned_slice_count: int
    selected_slice: SliceSupportSummary | None
    selection_policy: Mapping[str, Any]
    checks: Mapping[str, bool]
    limitations: tuple[str, ...]
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "task018_support_scan_report"

    def __post_init__(self) -> None:
        if self.report_statement != TASK018_REQUIRED_REPORT_STATEMENT:
            raise SupportAwareStagingError("TASK-018 required report statement is missing")
        if self.used_source_files != (DEFAULT_TIMELINE_SOURCE,):
            raise SupportAwareStagingError("TASK-018 must use only merged.csv")
        if self.labels_used_for_selection:
            raise SupportAwareStagingError("labels must not be used for support-aware selection")

    @property
    def report_id(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "report_statement": self.report_statement,
            "config_hash": self.config_hash,
            "used_source_files": list(self.used_source_files),
            "labels_used_for_selection": self.labels_used_for_selection,
            "scanned_slice_count": self.scanned_slice_count,
            "selected_slice": self.selected_slice.to_dict() if self.selected_slice is not None else None,
            "selection_policy": dict(self.selection_policy),
            "checks": dict(sorted(self.checks.items())),
            "limitations": list(self.limitations),
        }


def load_support_aware_staging_config(path: Path) -> SupportAwareStagingConfig:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return SupportAwareStagingConfig.from_dict(payload)


def run_task018_support_aware_staging_from_env(
    *,
    config: SupportAwareStagingConfig,
    metadata: MetadataRegistry,
    env_var: str = "SWAT_DATA_ROOT",
    created_at: str = "unspecified",
) -> tuple[SupportScanReport, StagingPipelineDryRunReport, Mapping[str, Any]]:
    return run_task018_support_aware_staging(
        root=resolve_data_root(env_var),
        config=config,
        metadata=metadata,
        created_at=created_at,
    )


def run_task018_support_aware_staging(
    *,
    root: Path,
    config: SupportAwareStagingConfig,
    metadata: MetadataRegistry,
    created_at: str = "unspecified",
) -> tuple[SupportScanReport, StagingPipelineDryRunReport, Mapping[str, Any]]:
    scan_report = scan_support_aware_slice(root=root, config=config)
    if scan_report.selected_slice is None:
        selected_start = 0
    else:
        selected_start = scan_report.selected_slice.timeline_start_index
    dry_config = replace(config.dry_run_config, timeline_start_index=selected_start)
    dry_report, split_manifest = run_task017_staging_pipeline_dry_run(
        root=root,
        config=dry_config,
        metadata=metadata,
        created_at=created_at,
    )
    return scan_report, dry_report, split_manifest


def scan_support_aware_slice(*, root: Path, config: SupportAwareStagingConfig) -> SupportScanReport:
    series, timestamps_seconds, row_count = _read_support_columns(root=root, config=config)
    scanned = 0
    selected: SliceSupportSummary | None = None
    max_start = row_count - config.dry_run_config.required_loaded_rows
    if max_start < 0:
        raise SupportAwareStagingError("merged.csv does not contain enough rows for configured support-aware dry-run")
    for start in range(0, max_start + 1, config.selection_policy.search_step):
        scanned += 1
        summary = _summarize_slice(
            series=series,
            timestamps_seconds=timestamps_seconds,
            timeline_start_index=start,
            config=config,
        )
        if summary.passes_selection_criteria:
            selected = summary
            break
    checks = {
        "required_report_statement_present": True,
        "used_only_merged_csv": True,
        "labels_ignored_for_selection": True,
        "selection_policy_predeclared": True,
        "selected_slice_found": selected is not None,
        "selected_slice_has_supported_pair": selected is not None and selected.supported_pair_count > 0,
        "selected_slice_has_complete_pipeline_features": (
            selected is not None and selected.loaded_missing_value_count == 0
        ),
        "selected_slice_has_regular_sampling": selected is not None and selected.loaded_regular_sampling,
        "no_raw_rows_windows_or_plots_tracked": True,
        "dec007_unresolved": True,
    }
    return SupportScanReport(
        report_statement=TASK018_REQUIRED_REPORT_STATEMENT,
        config_hash=config.config_hash,
        used_source_files=(DEFAULT_TIMELINE_SOURCE,),
        labels_used_for_selection=False,
        scanned_slice_count=scanned,
        selected_slice=selected,
        selection_policy=config.selection_policy.to_dict(),
        checks=checks,
        limitations=(
            "This is a Kaggle/local staging run for implementation debugging only.",
            "It is not an official SWaT benchmark result and must not be used as a final thesis performance claim.",
            "Labels are ignored for support-aware slice selection.",
            "Only aggregate support summaries and index ranges are persisted.",
            "DEC-007 remains unresolved.",
        ),
    )


def _read_support_columns(
    *,
    root: Path,
    config: SupportAwareStagingConfig,
) -> tuple[Mapping[str, array], Sequence[float], int]:
    path = root / config.timeline_source
    if not path.exists() or not path.is_file():
        raise SupportAwareStagingError(f"missing staging timeline source: {config.timeline_source}")
    variables = tuple(
        sorted(
            set(config.selection_policy.allowed_source_variables)
            | set(config.selection_policy.allowed_target_variables)
            | set(config.dry_run_config.pipeline_feature_subset)
        )
    )
    values = {name: array("d") for name in variables}
    timestamps_seconds = array("d")
    first_timestamp = None
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise SupportAwareStagingError("merged.csv has no header")
        columns = tuple(name.strip() for name in reader.fieldnames)
        reader.fieldnames = list(columns)
        required = set(variables) | {config.timestamp_column}
        missing = sorted(required - set(columns))
        if missing:
            raise SupportAwareStagingError(f"merged.csv missing support scan columns: {missing}")
        for row in reader:
            timestamp = parse_timestamp(row[config.timestamp_column], config.timestamp_formats)
            if first_timestamp is None:
                first_timestamp = timestamp
            timestamps_seconds.append((timestamp - first_timestamp).total_seconds())
            for name in variables:
                cell = row[name].strip()
                values[name].append(float(cell) if cell else math.nan)
    row_count = len(next(iter(values.values()))) if values else 0
    return values, timestamps_seconds, row_count


def _summarize_slice(
    *,
    series: Mapping[str, Sequence[float]],
    timestamps_seconds: Sequence[float],
    timeline_start_index: int,
    config: SupportAwareStagingConfig,
) -> SliceSupportSummary:
    train_len = config.dry_run_config.split_lengths[SplitRole.TRAIN_NORMAL]
    calibration_len = config.dry_run_config.split_lengths[SplitRole.CALIBRATION_NORMAL]
    purge = config.dry_run_config.purge_gap_samples
    calibration_start = timeline_start_index + train_len + purge
    calibration_end = calibration_start + calibration_len
    loaded_start = timeline_start_index
    loaded_end = timeline_start_index + config.dry_run_config.required_loaded_rows
    loaded_missing = _missing_value_count(
        series=series,
        variables=config.dry_run_config.pipeline_feature_subset,
        start=loaded_start,
        end=loaded_end,
    )
    calibration_missing = _missing_value_count(
        series=series,
        variables=config.dry_run_config.pipeline_feature_subset,
        start=calibration_start,
        end=calibration_end,
    )
    loaded_regular, sampling_period = _regular_sampling_summary(
        timestamps_seconds=timestamps_seconds,
        start=loaded_start,
        end=loaded_end,
        tolerance=config.dry_run_config.profiling_config.timestamp_tolerance_seconds,
    )
    calibration_regular, _ = _regular_sampling_summary(
        timestamps_seconds=timestamps_seconds,
        start=calibration_start,
        end=calibration_end,
        tolerance=config.dry_run_config.profiling_config.timestamp_tolerance_seconds,
    )
    pair_summaries = tuple(
        _pair_support(
            source=source,
            target=target,
            source_values=series[source][calibration_start:calibration_end],
            source_state_values=series[source][loaded_start:loaded_end],
            target_values=series[target][calibration_start:calibration_end],
            config=config,
        )
        for source, target in config.dry_run_config.profile_pairs
    )
    supported_count = sum(1 for summary in pair_summaries if summary.passes_selection_criteria)
    complete_enough = not config.selection_policy.require_complete_pipeline_features or loaded_missing == 0
    regular_enough = not config.selection_policy.require_regular_sampling or (
        loaded_regular and calibration_regular
    )
    return SliceSupportSummary(
        timeline_start_index=timeline_start_index,
        loaded_range=(loaded_start, loaded_end),
        calibration_range=(calibration_start, calibration_end),
        loaded_missing_value_count=loaded_missing,
        calibration_missing_value_count=calibration_missing,
        loaded_regular_sampling=loaded_regular,
        calibration_regular_sampling=calibration_regular,
        inferred_sampling_period_seconds=sampling_period,
        supported_pair_count=supported_count,
        total_trigger_count=sum(summary.trigger_count for summary in pair_summaries),
        total_matched_response_count=sum(summary.matched_response_count for summary in pair_summaries),
        passes_selection_criteria=supported_count > 0 and complete_enough and regular_enough,
        pair_summaries=pair_summaries,
    )


def _pair_support(
    *,
    source: str,
    target: str,
    source_values: Sequence[float],
    source_state_values: Sequence[float],
    target_values: Sequence[float],
    config: SupportAwareStagingConfig,
) -> PairSupportSummary:
    source_states = tuple(sorted(set(float(value) for value in source_state_values if not math.isnan(float(value)))))
    normalized_source = _normalize_binary_source(source_values, source_states)
    trigger_count = 0
    matched_count = 0
    missing_count = 0
    censored_count = 0
    if normalized_source is not None:
        delay = config.dry_run_config.profiling_config.max_response_delay_samples
        floor = config.dry_run_config.profiling_config.response_delta_floor
        for index in range(1, len(normalized_source)):
            if normalized_source[index - 1] != 0.0 or normalized_source[index] != 1.0:
                continue
            if math.isnan(float(target_values[index - 1])):
                continue
            trigger_count += 1
            baseline = float(target_values[index - 1])
            max_index = index + delay
            search_end = min(max_index, len(target_values) - 1)
            matched = False
            for candidate_index in range(index, search_end + 1):
                if math.isnan(float(target_values[candidate_index])):
                    continue
                delta = float(target_values[candidate_index]) - baseline
                if delta > 0.0 and delta >= floor:
                    matched = True
                    break
            if matched:
                matched_count += 1
            elif max_index >= len(target_values):
                censored_count += 1
            else:
                missing_count += 1
    passes = (
        trigger_count >= config.selection_policy.minimum_trigger_count
        and matched_count >= config.selection_policy.minimum_matched_response_count
        and (
            trigger_count == 0
            or censored_count / trigger_count <= config.selection_policy.maximum_right_censored_ratio
        )
    )
    return PairSupportSummary(
        source=source,
        target=target,
        trigger_count=trigger_count,
        matched_response_count=matched_count,
        missing_response_count=missing_count,
        right_censored_count=censored_count,
        observed_source_state_count=len(source_states),
        target_variance_summary=_variance_summary(target_values),
        passes_selection_criteria=passes,
    )


def _normalize_binary_source(values: Sequence[float], states: Sequence[float]) -> tuple[float, ...] | None:
    if tuple(states) == (0.0, 1.0):
        return tuple(float(value) for value in values)
    if len(states) == 0:
        return None
    if len(states) != 2:
        return tuple(float(value) for value in values)
    low, high = states
    normalized = []
    for value in values:
        observed = float(value)
        if math.isnan(observed):
            normalized.append(math.nan)
        elif observed == low:
            normalized.append(0.0)
        else:
            normalized.append(1.0)
    return tuple(normalized)


def _variance_summary(values: Sequence[float]) -> dict[str, float]:
    if not values:
        return {"count": 0.0, "min": math.nan, "max": math.nan, "mean": math.nan, "variance": math.nan}
    observed = [float(value) for value in values if not math.isnan(float(value))]
    if not observed:
        return {"count": 0.0, "min": math.nan, "max": math.nan, "mean": math.nan, "variance": math.nan}
    mean = sum(observed) / len(observed)
    variance = sum((value - mean) ** 2 for value in observed) / len(observed)
    return {
        "count": float(len(observed)),
        "min": min(observed),
        "max": max(observed),
        "mean": mean,
        "variance": variance,
    }


def _missing_value_count(
    *,
    series: Mapping[str, Sequence[float]],
    variables: Sequence[str],
    start: int,
    end: int,
) -> int:
    return sum(
        1
        for name in variables
        for value in series[name][start:end]
        if math.isnan(float(value))
    )


def _regular_sampling_summary(
    *,
    timestamps_seconds: Sequence[float],
    start: int,
    end: int,
    tolerance: float,
) -> tuple[bool, float | None]:
    observed = timestamps_seconds[start:end]
    if len(observed) < 2:
        return False, None
    first_delta = float(observed[1]) - float(observed[0])
    if first_delta <= 0:
        return False, first_delta
    for index in range(2, len(observed)):
        delta = float(observed[index]) - float(observed[index - 1])
        if delta <= 0 or abs(delta - first_delta) > tolerance:
            return False, first_delta
    return True, first_delta


def _validate_relative_path(path: str) -> None:
    parsed = PurePosixPath(path.replace("\\", "/"))
    if parsed.is_absolute() or ".." in parsed.parts:
        raise SupportAwareStagingError(f"path must be relative and stay within SWAT_DATA_ROOT: {path}")
