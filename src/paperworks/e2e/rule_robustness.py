"""TASK-020 staging-only rule robustness and synthetic replay."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Sequence

from paperworks.candidates import build_candidate_universe
from paperworks.data import (
    DataViewManifest,
    DataViewName,
    SplitRole,
    build_data_view_manifest,
    build_sequential_split_manifests,
    resolve_data_root,
)
from paperworks.data.contracts import SCHEMA_VERSION, stable_hash
from paperworks.data.staging_swat import TASK016_REQUIRED_REPORT_STATEMENT, inspect_staging_swat_mirror
from paperworks.dsl import RuleAst, RuleSchemaRegistry
from paperworks.e2e.rule_evidence_audit import _report_payload
from paperworks.e2e.staging_dry_run import (
    DEFAULT_TIMELINE_SOURCE,
    StagingPipelineConfig,
    _NormalizedSeries,
    _TimelineSlice,
    _dataset_manifest_from_staging,
    _normalize_binary_actuators,
    _rows_for_split,
    _sampling_period_seconds,
    _series_for_split,
    _timestamps_for_split,
    _validate_staging_manifest,
    _verification_windows,
)
from paperworks.e2e.support_aware_staging import (
    PairSupportSummary,
    SliceSupportSummary,
    SupportAwareStagingConfig,
    _read_support_columns,
    _summarize_slice,
)
from paperworks.gdn import extract_masked_topk_edges, fit_deterministic_embedding_checkpoint
from paperworks.metadata import MetadataRegistry
from paperworks.planning import build_template_rule
from paperworks.profiling import (
    CalibrationRecord,
    RelationProfile,
    build_relation_evidence_pack,
    calibrate_relation_profile,
    profile_binary_actuator_to_continuous_sensor,
)
from paperworks.runtime import RuntimeRuleEngine, TimeSeriesBatch, VerifiedRuleLibrary
from paperworks.verification import VerificationDataset, VerificationReport, verify_rule


TASK020_REQUIRED_REPORT_STATEMENT = TASK016_REQUIRED_REPORT_STATEMENT
TASK020_ROBUSTNESS_ARTIFACT_TYPE = "task020_rule_robustness_report"
TASK020_REPLAY_ARTIFACT_TYPE = "task020_synthetic_violation_replay"


class RuleRobustnessError(ValueError):
    """Raised when TASK-020 robustness inputs are unsafe."""


@dataclass(frozen=True)
class PairRobustnessSummary:
    source: str
    target: str
    scanned_slice_count: int
    supported_slice_count: int
    trigger_count_total: int
    matched_response_count_total: int
    missing_response_count_total: int
    right_censored_count_total: int
    first_supported_start_indices: tuple[int, ...]

    @property
    def support_rate(self) -> float:
        if self.scanned_slice_count == 0:
            return 0.0
        return self.supported_slice_count / self.scanned_slice_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "scanned_slice_count": self.scanned_slice_count,
            "supported_slice_count": self.supported_slice_count,
            "support_rate": self.support_rate,
            "trigger_count_total": self.trigger_count_total,
            "matched_response_count_total": self.matched_response_count_total,
            "missing_response_count_total": self.missing_response_count_total,
            "right_censored_count_total": self.right_censored_count_total,
            "first_supported_start_indices": list(self.first_supported_start_indices),
        }


@dataclass(frozen=True)
class RuleStabilityObservation:
    timeline_start_index: int
    source: str
    target: str
    rule_id: str
    audited_rule_id: str | None
    rule_id_matches_audited: bool
    verifier_status: str
    verifier_report_id: str
    support_counts: Mapping[str, int]
    calibration_values: Mapping[str, float]
    calibration_support_counts: Mapping[str, int]
    normal_false_fire_rate: float
    validation_coverage: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "timeline_start_index": self.timeline_start_index,
            "source": self.source,
            "target": self.target,
            "rule_id": self.rule_id,
            "audited_rule_id": self.audited_rule_id,
            "rule_id_matches_audited": self.rule_id_matches_audited,
            "verifier_status": self.verifier_status,
            "verifier_report_id": self.verifier_report_id,
            "support_counts": dict(sorted(self.support_counts.items())),
            "calibration_values": dict(sorted(self.calibration_values.items())),
            "calibration_support_counts": dict(sorted(self.calibration_support_counts.items())),
            "normal_false_fire_rate": self.normal_false_fire_rate,
            "validation_coverage": self.validation_coverage,
        }


@dataclass(frozen=True)
class RuleRobustnessReport:
    report_statement: str
    task018_support_scan_report_id: str
    task018_dry_run_report_id: str
    task019_audit_report_id: str
    config_hash: str
    used_source_files: tuple[str, ...]
    labels_used_for_selection: bool
    scanned_slice_count: int
    passing_slice_count: int
    selected_timeline_start_index: int
    scan_policy: Mapping[str, Any]
    pair_summaries: tuple[PairRobustnessSummary, ...]
    stability_observations: tuple[RuleStabilityObservation, ...]
    stability_summary: Mapping[str, Any]
    checks: Mapping[str, bool]
    limitations: tuple[str, ...]
    created_at: str
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = TASK020_ROBUSTNESS_ARTIFACT_TYPE

    def __post_init__(self) -> None:
        if self.report_statement != TASK020_REQUIRED_REPORT_STATEMENT:
            raise RuleRobustnessError("TASK-020 required report statement is missing")
        if self.used_source_files != (DEFAULT_TIMELINE_SOURCE,):
            raise RuleRobustnessError("TASK-020 must use only merged.csv")
        if self.labels_used_for_selection:
            raise RuleRobustnessError("TASK-020 must not use labels for slice selection")

    @property
    def report_id(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "report_statement": self.report_statement,
            "task018_support_scan_report_id": self.task018_support_scan_report_id,
            "task018_dry_run_report_id": self.task018_dry_run_report_id,
            "task019_audit_report_id": self.task019_audit_report_id,
            "config_hash": self.config_hash,
            "used_source_files": list(self.used_source_files),
            "labels_used_for_selection": self.labels_used_for_selection,
            "scanned_slice_count": self.scanned_slice_count,
            "passing_slice_count": self.passing_slice_count,
            "selected_timeline_start_index": self.selected_timeline_start_index,
            "scan_policy": dict(self.scan_policy),
            "pair_summaries": [summary.to_dict() for summary in self.pair_summaries],
            "stability_observations": [observation.to_dict() for observation in self.stability_observations],
            "stability_summary": dict(self.stability_summary),
            "checks": dict(sorted(self.checks.items())),
            "limitations": list(self.limitations),
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class SyntheticReplayCase:
    rule_id: str
    source: str
    target: str
    max_response_delay_seconds: float
    min_response_magnitude: float
    synthetic_sample_count: int
    missing_response_firing_count: int
    expected_response_firing_count: int

    @property
    def missing_response_fired(self) -> bool:
        return self.missing_response_firing_count > 0

    @property
    def expected_response_suppressed(self) -> bool:
        return self.expected_response_firing_count == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "source": self.source,
            "target": self.target,
            "max_response_delay_seconds": self.max_response_delay_seconds,
            "min_response_magnitude": self.min_response_magnitude,
            "synthetic_sample_count": self.synthetic_sample_count,
            "missing_response_firing_count": self.missing_response_firing_count,
            "missing_response_fired": self.missing_response_fired,
            "expected_response_firing_count": self.expected_response_firing_count,
            "expected_response_suppressed": self.expected_response_suppressed,
            "synthetic_policy": "non_swat_constant_baseline_with_single_trigger",
        }


@dataclass(frozen=True)
class SyntheticReplayReport:
    report_statement: str
    task019_audit_report_id: str
    used_source_files: tuple[str, ...]
    cases: tuple[SyntheticReplayCase, ...]
    checks: Mapping[str, bool]
    limitations: tuple[str, ...]
    created_at: str
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = TASK020_REPLAY_ARTIFACT_TYPE

    def __post_init__(self) -> None:
        if self.report_statement != TASK020_REQUIRED_REPORT_STATEMENT:
            raise RuleRobustnessError("TASK-020 required report statement is missing")
        if self.used_source_files != ():
            raise RuleRobustnessError("synthetic replay must not use staging source files")
        if not self.cases:
            raise RuleRobustnessError("synthetic replay requires at least one case")

    @property
    def report_id(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "report_statement": self.report_statement,
            "task019_audit_report_id": self.task019_audit_report_id,
            "used_source_files": list(self.used_source_files),
            "case_count": len(self.cases),
            "cases": [case.to_dict() for case in self.cases],
            "checks": dict(sorted(self.checks.items())),
            "limitations": list(self.limitations),
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class _RebuiltRule:
    timeline_start_index: int
    profile: RelationProfile
    calibration_records: tuple[CalibrationRecord, ...]
    rule: RuleAst
    verification: VerificationReport


@dataclass(frozen=True)
class _StagingContext:
    config: StagingPipelineConfig
    metadata: MetadataRegistry
    feature_order: tuple[str, ...]
    dataset_manifest_id: str
    dataset_name: str
    sampling_period_seconds: float
    metadata_artifact_id: str
    support_series: Mapping[str, Sequence[float]]
    support_timestamps_seconds: Sequence[float]


def run_task020_from_env(
    *,
    config: SupportAwareStagingConfig,
    metadata: MetadataRegistry,
    support_scan_report_path: Path,
    dry_run_report_path: Path,
    rule_evidence_audit_path: Path,
    env_var: str = "SWAT_DATA_ROOT",
    reconstructed_task018_created_at: str = "2026-06-28T00:00:00+09:00",
    created_at: str = "unspecified",
    max_scan_slices: int | None = None,
    max_stability_rebuild_slices: int = 8,
) -> tuple[RuleRobustnessReport, SyntheticReplayReport]:
    return run_task020_rule_robustness(
        root=resolve_data_root(env_var),
        config=config,
        metadata=metadata,
        support_scan_report=_load_json(support_scan_report_path),
        dry_run_report=_load_json(dry_run_report_path),
        rule_evidence_audit=_load_json(rule_evidence_audit_path),
        reconstructed_task018_created_at=reconstructed_task018_created_at,
        created_at=created_at,
        max_scan_slices=max_scan_slices,
        max_stability_rebuild_slices=max_stability_rebuild_slices,
    )


def run_task020_rule_robustness(
    *,
    root: Path,
    config: SupportAwareStagingConfig,
    metadata: MetadataRegistry,
    support_scan_report: Mapping[str, Any],
    dry_run_report: Mapping[str, Any],
    rule_evidence_audit: Mapping[str, Any],
    reconstructed_task018_created_at: str,
    created_at: str = "unspecified",
    max_scan_slices: int | None = None,
    max_stability_rebuild_slices: int = 8,
) -> tuple[RuleRobustnessReport, SyntheticReplayReport]:
    support_payload = _report_payload(support_scan_report)
    dry_payload = _report_payload(dry_run_report)
    audit_payload = _report_payload(rule_evidence_audit)
    _validate_inputs(support_scan_report, dry_run_report, rule_evidence_audit, support_payload, dry_payload, audit_payload, config)

    series, timestamps_seconds, row_count = _read_support_columns(root=root, config=config)
    slice_summaries = _scan_slices(
        series=series,
        timestamps_seconds=timestamps_seconds,
        row_count=row_count,
        config=config,
        max_scan_slices=max_scan_slices,
    )
    pair_summaries = _pair_robustness_summaries(slice_summaries, config.dry_run_config.profile_pairs)
    passing_starts = tuple(summary.timeline_start_index for summary in slice_summaries if summary.passes_selection_criteria)
    selected_start = int(support_payload["selected_slice"]["timeline_start_index"])
    rebuild_starts = _stability_rebuild_starts(
        selected_start=selected_start,
        passing_starts=passing_starts,
        limit=max_stability_rebuild_slices,
    )
    context = _build_staging_context(
        root=root,
        config=config,
        metadata=metadata,
        support_series=series,
        support_timestamps_seconds=timestamps_seconds,
    )
    audited_rules = _audited_rule_map(audit_payload)
    rebuilt: list[_RebuiltRule] = []
    for start in rebuild_starts:
        rebuilt.extend(
            _rebuild_supported_rules_for_slice(
                context=context,
                timeline_start_index=start,
                created_at=reconstructed_task018_created_at,
            )
        )
    stability_observations = tuple(
        _stability_observation(item, audited_rules) for item in rebuilt
    )
    robustness = RuleRobustnessReport(
        report_statement=TASK020_REQUIRED_REPORT_STATEMENT,
        task018_support_scan_report_id=str(support_scan_report["report_id"]),
        task018_dry_run_report_id=str(dry_run_report["report_id"]),
        task019_audit_report_id=str(rule_evidence_audit["report_id"]),
        config_hash=config.config_hash,
        used_source_files=(DEFAULT_TIMELINE_SOURCE,),
        labels_used_for_selection=False,
        scanned_slice_count=len(slice_summaries),
        passing_slice_count=len(passing_starts),
        selected_timeline_start_index=selected_start,
        scan_policy={
            "timeline_source": DEFAULT_TIMELINE_SOURCE,
            "search_step": config.selection_policy.search_step,
            "maximum_slice_length": config.selection_policy.maximum_slice_length,
            "max_scan_slices": max_scan_slices,
            "stability_rebuild_strategy": "selected_slice_then_first_passing_starts_by_index",
            "max_stability_rebuild_slices": max_stability_rebuild_slices,
            "labels_policy": config.selection_policy.labels_policy,
            "selection_uses_anomaly_performance": False,
        },
        pair_summaries=pair_summaries,
        stability_observations=stability_observations,
        stability_summary=_stability_summary(stability_observations, audited_rules),
        checks={
            "required_report_statement_present": True,
            "used_only_merged_csv": True,
            "labels_not_used_for_slice_selection": True,
            "no_anomaly_performance_slice_selection": True,
            "staging_only": True,
            "dec007_unresolved": True,
            "no_final_test_access": dry_run_report["split_manifest"]["final_test_accessed"] is False,
            "official_manifest_not_used": dry_payload["checks"]["official_manifest_not_used"] is True,
            "runtime_llm_free": dry_payload["checks"]["runtime_llm_free"] is True,
            "no_raw_rows_windows_or_plots_tracked": True,
        },
        limitations=_limitations(),
        created_at=created_at,
    )
    selected_rebuilt = tuple(item for item in rebuilt if item.timeline_start_index == selected_start)
    replay = _synthetic_replay_report(
        rebuilt_rules=selected_rebuilt,
        audit_report_id=str(rule_evidence_audit["report_id"]),
        metadata=metadata,
        created_at=created_at,
    )
    return robustness, replay


def render_task020_report_markdown(
    robustness: RuleRobustnessReport,
    replay: SyntheticReplayReport,
) -> str:
    lines = [
        "# TASK-020 Completion Report",
        "",
        robustness.report_statement,
        "",
        "## Summary",
        "",
        f"- Robustness report ID: `{robustness.report_id}`",
        f"- Synthetic replay report ID: `{replay.report_id}`",
        f"- Scanned slices: {robustness.scanned_slice_count}",
        f"- Passing support-aware slices: {robustness.passing_slice_count}",
        f"- Stability observations: {len(robustness.stability_observations)}",
        f"- Synthetic replay cases: {len(replay.cases)}",
        "",
        "## Pair Support Frequency",
        "",
        "| Pair | Supported slices | Scanned slices | Support rate | Trigger total | Matched total |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for summary in robustness.pair_summaries:
        lines.append(
            f"| `{summary.source} -> {summary.target}` | {summary.supported_slice_count} | "
            f"{summary.scanned_slice_count} | {summary.support_rate:.6f} | "
            f"{summary.trigger_count_total} | {summary.matched_response_count_total} |"
        )
    lines.extend(
        [
            "",
            "## Synthetic Replay",
            "",
            "| Rule ID | Missing response fires | Expected response suppressed |",
            "|---|---:|---:|",
        ]
    )
    for case in replay.cases:
        lines.append(
            f"| `{case.rule_id}` | {str(case.missing_response_fired).lower()} | "
            f"{str(case.expected_response_suppressed).lower()} |"
        )
    lines.extend(
        [
            "",
            "## Checks",
            "",
            *[f"- `{key}`: {str(value).lower()}" for key, value in sorted(robustness.checks.items())],
            *[f"- `synthetic_replay.{key}`: {str(value).lower()}" for key, value in sorted(replay.checks.items())],
            "",
            "## Limitations",
            "",
            *[f"- {item}" for item in robustness.limitations],
            "",
        ]
    )
    return "\n".join(lines)


def _load_json(path: Path) -> Mapping[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _validate_inputs(
    support_report: Mapping[str, Any],
    dry_report: Mapping[str, Any],
    audit_report: Mapping[str, Any],
    support_payload: Mapping[str, Any],
    dry_payload: Mapping[str, Any],
    audit_payload: Mapping[str, Any],
    config: SupportAwareStagingConfig,
) -> None:
    for payload in (support_payload, dry_payload, audit_payload):
        if payload.get("report_statement") != TASK020_REQUIRED_REPORT_STATEMENT:
            raise RuleRobustnessError("required staging report statement missing from input")
    if support_payload.get("used_source_files") != [DEFAULT_TIMELINE_SOURCE]:
        raise RuleRobustnessError("support scan input must use only merged.csv")
    if dry_payload.get("used_source_files") != [DEFAULT_TIMELINE_SOURCE]:
        raise RuleRobustnessError("dry-run input must use only merged.csv")
    if audit_payload.get("used_source_files") != [DEFAULT_TIMELINE_SOURCE]:
        raise RuleRobustnessError("audit input must use only merged.csv")
    if support_payload.get("labels_used_for_selection") is not False:
        raise RuleRobustnessError("labels must not have been used for TASK-018 support selection")
    if config.timeline_source != DEFAULT_TIMELINE_SOURCE or config.dry_run_config.timeline_sources != (DEFAULT_TIMELINE_SOURCE,):
        raise RuleRobustnessError("TASK-020 config must use merged.csv only")
    if dry_report["split_manifest"]["final_test_accessed"] is not False:
        raise RuleRobustnessError("final test access is prohibited")
    for report in (support_report, dry_report, audit_report):
        if len(str(report.get("report_id", ""))) != 64:
            raise RuleRobustnessError("input report_id must be recorded")


def _scan_slices(
    *,
    series: Mapping[str, Sequence[float]],
    timestamps_seconds: Sequence[float],
    row_count: int,
    config: SupportAwareStagingConfig,
    max_scan_slices: int | None,
) -> tuple[SliceSupportSummary, ...]:
    max_start = row_count - config.dry_run_config.required_loaded_rows
    if max_start < 0:
        raise RuleRobustnessError("merged.csv does not contain enough rows for configured slices")
    summaries: list[SliceSupportSummary] = []
    for index, start in enumerate(range(0, max_start + 1, config.selection_policy.search_step)):
        if max_scan_slices is not None and index >= max_scan_slices:
            break
        summaries.append(
            _summarize_slice(
                series=series,
                timestamps_seconds=timestamps_seconds,
                timeline_start_index=start,
                config=config,
            )
        )
    return tuple(summaries)


def _pair_robustness_summaries(
    slice_summaries: Sequence[SliceSupportSummary],
    profile_pairs: Sequence[tuple[str, str]],
) -> tuple[PairRobustnessSummary, ...]:
    by_pair: dict[tuple[str, str], list[PairSupportSummary]] = {pair: [] for pair in profile_pairs}
    supported_starts: dict[tuple[str, str], list[int]] = {pair: [] for pair in profile_pairs}
    for summary in slice_summaries:
        for pair_summary in summary.pair_summaries:
            pair = (pair_summary.source, pair_summary.target)
            by_pair[pair].append(pair_summary)
            if pair_summary.passes_selection_criteria and len(supported_starts[pair]) < 10:
                supported_starts[pair].append(summary.timeline_start_index)
    result = []
    for source, target in profile_pairs:
        items = by_pair[(source, target)]
        result.append(
            PairRobustnessSummary(
                source=source,
                target=target,
                scanned_slice_count=len(items),
                supported_slice_count=sum(1 for item in items if item.passes_selection_criteria),
                trigger_count_total=sum(item.trigger_count for item in items),
                matched_response_count_total=sum(item.matched_response_count for item in items),
                missing_response_count_total=sum(item.missing_response_count for item in items),
                right_censored_count_total=sum(item.right_censored_count for item in items),
                first_supported_start_indices=tuple(supported_starts[(source, target)]),
            )
        )
    return tuple(result)


def _stability_rebuild_starts(
    *,
    selected_start: int,
    passing_starts: Sequence[int],
    limit: int,
) -> tuple[int, ...]:
    starts = [selected_start]
    for start in passing_starts:
        if start == selected_start or start in starts:
            continue
        starts.append(start)
        if len(starts) >= limit:
            break
    return tuple(starts[:limit])


def _build_staging_context(
    *,
    root: Path,
    config: SupportAwareStagingConfig,
    metadata: MetadataRegistry,
    support_series: Mapping[str, Sequence[float]],
    support_timestamps_seconds: Sequence[float],
) -> _StagingContext:
    staging_manifest = inspect_staging_swat_mirror(
        root=root,
        relative_paths=config.dry_run_config.timeline_sources,
        timestamp_column=config.dry_run_config.timestamp_column,
        label_column=config.dry_run_config.label_column,
        timestamp_formats=config.dry_run_config.timestamp_formats,
    )
    _validate_staging_manifest(staging_manifest)
    dataset = _dataset_manifest_from_staging(staging_manifest, feature_order=staging_manifest.feature_columns)
    return _StagingContext(
        config=config.dry_run_config,
        metadata=metadata,
        feature_order=tuple(config.dry_run_config.pipeline_feature_subset),
        dataset_manifest_id=dataset.manifest_id,
        dataset_name=dataset.dataset_name,
        sampling_period_seconds=_sampling_period_seconds(staging_manifest),
        metadata_artifact_id=stable_hash({"metadata": metadata.to_list()}),
        support_series=support_series,
        support_timestamps_seconds=support_timestamps_seconds,
    )


def _rebuild_supported_rules_for_slice(
    *,
    context: _StagingContext,
    timeline_start_index: int,
    created_at: str,
) -> tuple[_RebuiltRule, ...]:
    config = replace(context.config, timeline_start_index=timeline_start_index)
    data_view = _data_view_for_start(context, timeline_start_index)
    splits = build_sequential_split_manifests(
        total_length=config.required_loaded_rows,
        role_lengths=(
            (SplitRole.TRAIN_NORMAL, config.split_lengths[SplitRole.TRAIN_NORMAL]),
            (SplitRole.CALIBRATION_NORMAL, config.split_lengths[SplitRole.CALIBRATION_NORMAL]),
            (SplitRole.VALIDATION, config.split_lengths[SplitRole.VALIDATION]),
        ),
        dataset_manifest_id=context.dataset_manifest_id,
        data_view_id=data_view.view_id,
        purge_gap_samples=config.purge_gap_samples,
        seed=config.seed,
    )
    split_by_role = {split.role: split for split in splits}
    timeline = _timeline_slice_from_arrays(context, config)
    normalized = _normalize_binary_actuators(timeline.series, context.metadata, context.feature_order)
    train_rows = _rows_for_split(normalized.series, context.feature_order, split_by_role[SplitRole.TRAIN_NORMAL])
    universe = build_candidate_universe(
        metadata=context.metadata,
        feature_order=context.feature_order,
        policy=config.candidate_policy,
        split=split_by_role[SplitRole.TRAIN_NORMAL],
        data_view=data_view,
        metadata_artifact_id=context.metadata_artifact_id,
        created_at=created_at,
    )
    checkpoint = fit_deterministic_embedding_checkpoint(
        normal_windows=train_rows,
        feature_order=context.feature_order,
        split=split_by_role[SplitRole.TRAIN_NORMAL],
        data_view=data_view,
        config=config.gdn_config,
    )
    edges = extract_masked_topk_edges(
        candidate_universe=universe,
        checkpoint=checkpoint,
        config=config.gdn_config,
        split=split_by_role[SplitRole.TRAIN_NORMAL],
        data_view=data_view,
        created_at=created_at,
    )
    allowed_pairs = {(pair.source, pair.target) for pair in universe.pairs}
    records_by_id: dict[str, CalibrationRecord] = {}
    rebuilt: list[_RebuiltRule] = []
    for source, target in config.profile_pairs:
        if (source, target) not in allowed_pairs:
            continue
        profile = profile_binary_actuator_to_continuous_sensor(
            source=source,
            target=target,
            series=_series_for_split(normalized.series, split_by_role[SplitRole.CALIBRATION_NORMAL]),
            metadata=context.metadata,
            split=split_by_role[SplitRole.CALIBRATION_NORMAL],
            data_view=data_view,
            config=config.profiling_config,
            timestamps_seconds=_timestamps_for_split(
                timeline.timestamps_seconds,
                split_by_role[SplitRole.CALIBRATION_NORMAL],
            ),
            upstream_artifact_ids=(universe.artifact_id, context.metadata_artifact_id, edges.artifact_id),
            dataset=context.dataset_name,
            data_fingerprint=context.dataset_manifest_id,
            created_at=created_at,
        )
        if profile.normal_support_status != "supported":
            continue
        calibration_records = calibrate_relation_profile(
            profile=profile,
            split=split_by_role[SplitRole.CALIBRATION_NORMAL],
            config=config.profiling_config,
        )
        records_by_id.update({record.calibration_id: record for record in calibration_records})
        evidence = build_relation_evidence_pack(profile=profile, calibration_records=calibration_records)
        registry = RuleSchemaRegistry(metadata=context.metadata, calibration_records=records_by_id)
        build_result = build_template_rule(evidence, registry)
        if build_result.status != "built" or build_result.rule is None:
            continue
        rule = build_result.rule
        verification = verify_rule(
            rule,
            registry=registry,
            normal_dataset=VerificationDataset(
                split_role=SplitRole.CALIBRATION_NORMAL,
                windows=_verification_windows(
                    source=source,
                    target=target,
                    series=normalized.series,
                    timestamps=timeline.timestamps_seconds,
                    split=split_by_role[SplitRole.CALIBRATION_NORMAL],
                    sampling_period_seconds=data_view.sampling_period_seconds,
                    window_size=config.profiling_config.max_response_delay_samples + 2,
                ),
                dataset_name=context.dataset_name,
                data_fingerprint=context.dataset_manifest_id,
                split_id=split_by_role[SplitRole.CALIBRATION_NORMAL].split_id,
            ),
            validation_dataset=VerificationDataset(
                split_role=SplitRole.VALIDATION,
                windows=_verification_windows(
                    source=source,
                    target=target,
                    series=normalized.series,
                    timestamps=timeline.timestamps_seconds,
                    split=split_by_role[SplitRole.VALIDATION],
                    sampling_period_seconds=data_view.sampling_period_seconds,
                    window_size=config.profiling_config.max_response_delay_samples + 2,
                ),
                dataset_name=context.dataset_name,
                data_fingerprint=context.dataset_manifest_id,
                split_id=split_by_role[SplitRole.VALIDATION].split_id,
            ),
            existing_rules=(),
            config=config.verification_config,
        )
        rebuilt.append(
            _RebuiltRule(
                timeline_start_index=timeline_start_index,
                profile=profile,
                calibration_records=tuple(calibration_records),
                rule=rule,
                verification=verification,
            )
        )
    return tuple(rebuilt)


def _data_view_for_start(context: _StagingContext, timeline_start_index: int) -> DataViewManifest:
    payload = {
        "dataset_manifest_id": context.dataset_manifest_id,
        "name": DataViewName.CANONICAL_RULE.value,
        "sampling_period_seconds": context.sampling_period_seconds,
        "preprocessing_config": {
            "task": "TASK-017",
            "source": DEFAULT_TIMELINE_SOURCE,
            "binary_actuator_normalization": context.config.binary_actuator_normalization,
            "timeline_start_index": timeline_start_index,
        },
        "source_view": "canonical_rule_view",
    }
    return DataViewManifest(
        name=DataViewName.CANONICAL_RULE,
        sampling_period_seconds=context.sampling_period_seconds,
        preprocessing_config=payload["preprocessing_config"],
        upstream_dataset_manifest_id=context.dataset_manifest_id,
        fingerprint=stable_hash(payload),
        source_view="canonical_rule_view",
    )


def _timeline_slice_from_arrays(context: _StagingContext, config: StagingPipelineConfig) -> _TimelineSlice:
    start = config.timeline_start_index
    end = start + config.required_loaded_rows
    base_timestamp = float(context.support_timestamps_seconds[start])
    return _TimelineSlice(
        series={
            name: tuple(float(value) for value in context.support_series[name][start:end])
            for name in context.feature_order
        },
        timestamps_seconds=tuple(
            float(value) - base_timestamp for value in context.support_timestamps_seconds[start:end]
        ),
        label_counts_by_split={"loaded_slice": {}},
    )


def _audited_rule_map(audit_payload: Mapping[str, Any]) -> dict[tuple[str, str], str]:
    return {
        (str(card["source_variable"]), str(card["target_variable"])): str(card["rule_id"])
        for card in audit_payload["evidence_cards"]
    }


def _stability_observation(
    item: _RebuiltRule,
    audited_rules: Mapping[tuple[str, str], str],
) -> RuleStabilityObservation:
    pair = (item.profile.source, item.profile.target)
    audited_rule_id = audited_rules.get(pair)
    calibration_values = {record.parameter_name: record.value for record in item.calibration_records}
    calibration_support = {record.parameter_name: record.normal_support_count for record in item.calibration_records}
    metrics = item.verification.metrics
    return RuleStabilityObservation(
        timeline_start_index=item.timeline_start_index,
        source=item.profile.source,
        target=item.profile.target,
        rule_id=item.rule.rule_id,
        audited_rule_id=audited_rule_id,
        rule_id_matches_audited=audited_rule_id == item.rule.rule_id,
        verifier_status=item.verification.status,
        verifier_report_id=item.verification.report_id,
        support_counts={
            "trigger_count": item.profile.trigger_count,
            "matched_response_count": item.profile.matched_response_count,
            "missing_response_count": item.profile.missing_response_count,
            "right_censored_count": item.profile.right_censored_count,
        },
        calibration_values=calibration_values,
        calibration_support_counts=calibration_support,
        normal_false_fire_rate=float(metrics.get("normal_false_fire_rate", 0.0)),
        validation_coverage=float(metrics.get("validation_coverage", 0.0)),
    )


def _stability_summary(
    observations: Sequence[RuleStabilityObservation],
    audited_rules: Mapping[tuple[str, str], str],
) -> dict[str, Any]:
    by_pair: dict[tuple[str, str], list[RuleStabilityObservation]] = defaultdict(list)
    for observation in observations:
        by_pair[(observation.source, observation.target)].append(observation)
    pair_summary = {}
    for pair, audited_rule_id in sorted(audited_rules.items()):
        items = by_pair.get(pair, [])
        pair_key = f"{pair[0]}->{pair[1]}"
        pair_summary[pair_key] = {
            "audited_rule_id": audited_rule_id,
            "rebuilt_observation_count": len(items),
            "passed_verifier_count": sum(1 for item in items if item.verifier_status == "passed"),
            "unique_rule_ids": sorted({item.rule_id for item in items}),
            "audited_rule_id_seen": any(item.rule_id == audited_rule_id for item in items),
            "calibration_value_ranges": _calibration_ranges(items),
        }
    return {
        "audited_pair_count": len(audited_rules),
        "rebuilt_observation_count": len(observations),
        "pair_summary": pair_summary,
        "interpretation": "staging stability audit only; not a benchmark or performance claim",
    }


def _calibration_ranges(items: Sequence[RuleStabilityObservation]) -> dict[str, Mapping[str, float]]:
    values_by_name: dict[str, list[float]] = defaultdict(list)
    for item in items:
        for name, value in item.calibration_values.items():
            values_by_name[name].append(float(value))
    return {
        name: {"min": min(values), "max": max(values)}
        for name, values in sorted(values_by_name.items())
        if values
    }


def _synthetic_replay_report(
    *,
    rebuilt_rules: Sequence[_RebuiltRule],
    audit_report_id: str,
    metadata: MetadataRegistry,
    created_at: str,
) -> SyntheticReplayReport:
    cases = tuple(_synthetic_replay_case(item, metadata) for item in rebuilt_rules)
    checks = {
        "required_report_statement_present": True,
        "uses_synthetic_non_swat_series_only": True,
        "no_staging_source_files_used": True,
        "missing_response_cases_fire": all(case.missing_response_fired for case in cases),
        "expected_response_cases_do_not_fire": all(case.expected_response_suppressed for case in cases),
        "runtime_llm_free": True,
        "staging_only": True,
    }
    return SyntheticReplayReport(
        report_statement=TASK020_REQUIRED_REPORT_STATEMENT,
        task019_audit_report_id=audit_report_id,
        used_source_files=(),
        cases=cases,
        checks=checks,
        limitations=(
            "Synthetic replay uses non-SWaT mini time-series generated from DSL/calibration values.",
            "This verifies runtime plumbing for expected missing-response semantics only.",
            "It is not an official SWaT benchmark result and must not be used as a final thesis performance claim.",
        ),
        created_at=created_at,
    )


def _synthetic_replay_case(item: _RebuiltRule, metadata: MetadataRegistry) -> SyntheticReplayCase:
    rule = item.rule
    records_by_id = {record.calibration_id: record for record in item.calibration_records}
    verification_ids = {rule.rule_id: item.verification.report_id}
    engine = RuntimeRuleEngine(
        registry=RuleSchemaRegistry(metadata=metadata, calibration_records=records_by_id),
        config=StagingPipelineConfig().runtime_config,
    )
    engine.load_library(VerifiedRuleLibrary(rules=(rule,), verification_report_ids=verification_ids))
    data_view = _synthetic_data_view(rule.rule_id)
    missing_batch = _synthetic_batch(rule, data_view=data_view, missing_response=True)
    expected_batch = _synthetic_batch(rule, data_view=data_view, missing_response=False)
    missing_eval = engine.evaluate(missing_batch)
    expected_eval = engine.evaluate(expected_batch)
    return SyntheticReplayCase(
        rule_id=rule.rule_id,
        source=rule.source,
        target=rule.target,
        max_response_delay_seconds=rule.calibration_references["max_response_delay_seconds"].resolved_value,
        min_response_magnitude=rule.calibration_references["min_response_magnitude"].resolved_value,
        synthetic_sample_count=missing_batch.length,
        missing_response_firing_count=len(missing_eval.firing_records),
        expected_response_firing_count=len(expected_eval.firing_records),
    )


def _synthetic_data_view(rule_id: str) -> DataViewManifest:
    dataset_id = stable_hash({"dataset": "task020_synthetic_non_swat", "rule_id": rule_id})
    payload = {
        "dataset_manifest_id": dataset_id,
        "name": DataViewName.CANONICAL_RULE.value,
        "sampling_period_seconds": 1.0,
        "preprocessing_config": {"task": "TASK-020", "source": "synthetic_non_swat_rule_replay"},
        "source_view": "canonical_rule_view",
    }
    return DataViewManifest(
        name=DataViewName.CANONICAL_RULE,
        sampling_period_seconds=1.0,
        preprocessing_config=payload["preprocessing_config"],
        upstream_dataset_manifest_id=dataset_id,
        fingerprint=stable_hash(payload),
        source_view="canonical_rule_view",
    )


def _synthetic_batch(
    rule: RuleAst,
    *,
    data_view: DataViewManifest,
    missing_response: bool,
) -> TimeSeriesBatch:
    delay = rule.calibration_references["max_response_delay_seconds"].resolved_value
    magnitude = rule.calibration_references["min_response_magnitude"].resolved_value
    sample_count = max(5, int(math.ceil(delay)) + 3)
    source = [0.0] + [1.0] * (sample_count - 1)
    baseline = 100.0
    target = [baseline] * sample_count
    if not missing_response:
        response_index = min(sample_count - 1, 1 + max(0, int(math.floor(delay))))
        target[response_index] = baseline + magnitude + max(abs(magnitude) * 0.1, 1e-9)
        for index in range(response_index + 1, sample_count):
            target[index] = target[response_index]
    suffix = "missing_response" if missing_response else "expected_response"
    return TimeSeriesBatch(
        series={rule.source: tuple(source), rule.target: tuple(target)},
        data_view=data_view,
        timestamps_seconds=tuple(float(index) for index in range(sample_count)),
        batch_id=f"task020_synthetic_{suffix}_{rule.rule_id}",
        data_fingerprint=stable_hash({"synthetic": suffix, "rule_id": rule.rule_id}),
    )


def _limitations() -> tuple[str, ...]:
    return (
        "This is a Kaggle/local staging run for implementation debugging only.",
        "It is not an official SWaT benchmark result and must not be used as a final thesis performance claim.",
        "Rule stability is evaluated on predeclared support-aware staging slices, not final test data.",
        "Synthetic replay uses non-SWaT mini-series and validates runtime plumbing only.",
        "DEC-007 remains unresolved.",
        "No raw rows, windows, raw sequence plots, or downloadable derived samples are persisted.",
    )
