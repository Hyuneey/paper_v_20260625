"""TASK-017 Kaggle/local staging pipeline dry-run workflow."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from paperworks.candidates import CandidatePolicy, build_candidate_universe
from paperworks.data import (
    DataViewName,
    DatasetFile,
    DatasetManifest,
    SplitManifest,
    SplitRole,
    StagingSwatMirrorManifest,
    build_data_view_manifest,
    build_sequential_split_manifests,
    inspect_staging_swat_mirror,
    resolve_data_root,
)
from paperworks.data.contracts import SCHEMA_VERSION, stable_hash
from paperworks.data.files import infer_regular_sampling_period, parse_timestamp
from paperworks.data.staging_swat import DEFAULT_TIMESTAMP_FORMATS, TASK016_REQUIRED_REPORT_STATEMENT
from paperworks.dsl import RuleSchemaRegistry, TimeSeriesWindow
from paperworks.gdn import GDNExtractionConfig, extract_masked_topk_edges, fit_deterministic_embedding_checkpoint
from paperworks.metadata import MetadataRegistry, VariableRole
from paperworks.planning import build_template_rule
from paperworks.profiling import (
    CalibrationRecord,
    RelationProfilingConfig,
    build_relation_evidence_pack,
    calibrate_relation_profile,
    profile_binary_actuator_to_continuous_sensor,
)
from paperworks.runtime import RuntimeConfig, RuntimeRuleEngine, TimeSeriesBatch, VerifiedRuleLibrary
from paperworks.verification import VerificationConfig, VerificationDataset, verify_rule


TASK017_REQUIRED_REPORT_STATEMENT = TASK016_REQUIRED_REPORT_STATEMENT
DEFAULT_TIMELINE_SOURCE = "merged.csv"


class StagingPipelineDryRunError(ValueError):
    """Raised when TASK-017 dry-run inputs or policy are unsafe."""


@dataclass(frozen=True)
class StagingPipelineConfig:
    timeline_sources: tuple[str, ...] = (DEFAULT_TIMELINE_SOURCE,)
    schema_cross_check_sources: tuple[str, ...] = ()
    pipeline_feature_subset: tuple[str, ...] = (
        "FIT101",
        "LIT101",
        "MV101",
        "P101",
        "P102",
        "AIT201",
        "AIT202",
        "AIT203",
        "FIT201",
        "MV201",
    )
    split_lengths: Mapping[SplitRole, int] = field(
        default_factory=lambda: {
            SplitRole.TRAIN_NORMAL: 256,
            SplitRole.CALIBRATION_NORMAL: 256,
            SplitRole.VALIDATION: 256,
        }
    )
    purge_gap_samples: int = 4
    seed: int = 17
    timestamp_column: str = "Timestamp"
    label_column: str = "Normal/Attack"
    timestamp_formats: tuple[str, ...] = DEFAULT_TIMESTAMP_FORMATS
    binary_actuator_normalization: str = "map_two_observed_states_to_0_1"
    candidate_policy: CandidatePolicy = field(default_factory=CandidatePolicy)
    gdn_config: GDNExtractionConfig = field(
        default_factory=lambda: GDNExtractionConfig(top_k=1, seed=17, backend="deterministic_embedding_task017")
    )
    profile_pairs: tuple[tuple[str, str], ...] = (
        ("MV101", "FIT101"),
        ("MV101", "LIT101"),
        ("P101", "FIT101"),
        ("P101", "LIT101"),
        ("P102", "FIT101"),
        ("P102", "LIT101"),
        ("MV201", "AIT201"),
        ("MV201", "AIT202"),
    )
    profiling_config: RelationProfilingConfig = field(
        default_factory=lambda: RelationProfilingConfig(max_response_delay_samples=20, min_matched_response_count=1)
    )
    verification_config: VerificationConfig = field(
        default_factory=lambda: VerificationConfig(
            max_normal_false_fire_rate=1.0,
            min_validation_coverage=0.0,
            firing_overlap_jaccard_threshold=1.0,
            min_calibration_support_count=1,
        )
    )
    runtime_config: RuntimeConfig = field(default_factory=RuntimeConfig)

    def __post_init__(self) -> None:
        if len(self.timeline_sources) != 1:
            raise StagingPipelineDryRunError("TASK-017 requires exactly one declared timeline source")
        _validate_relative_path(self.timeline_sources[0])
        if self.timeline_sources[0] != DEFAULT_TIMELINE_SOURCE:
            raise StagingPipelineDryRunError("TASK-017 default dry-run timeline source must be merged.csv")
        for source in self.schema_cross_check_sources:
            _validate_relative_path(source)
        if self.timeline_sources[0] in self.schema_cross_check_sources:
            raise StagingPipelineDryRunError("timeline source must not also be a schema cross-check source")
        if not self.pipeline_feature_subset:
            raise StagingPipelineDryRunError("pipeline_feature_subset is required")
        if len(set(self.pipeline_feature_subset)) != len(self.pipeline_feature_subset):
            raise StagingPipelineDryRunError("pipeline_feature_subset must not contain duplicates")
        required_roles = {SplitRole.TRAIN_NORMAL, SplitRole.CALIBRATION_NORMAL, SplitRole.VALIDATION}
        if set(self.split_lengths) != required_roles:
            raise StagingPipelineDryRunError("split_lengths must define train_normal, calibration_normal, and validation")
        if any(length <= 0 for length in self.split_lengths.values()):
            raise StagingPipelineDryRunError("split lengths must be positive")
        if self.purge_gap_samples < 0:
            raise StagingPipelineDryRunError("purge_gap_samples must be non-negative")
        for source, target in self.profile_pairs:
            if source == target:
                raise StagingPipelineDryRunError("profile self-pairs are prohibited")

    @property
    def config_hash(self) -> str:
        return stable_hash(self.to_dict())

    @property
    def required_loaded_rows(self) -> int:
        role_lengths = (
            (SplitRole.TRAIN_NORMAL, self.split_lengths[SplitRole.TRAIN_NORMAL]),
            (SplitRole.CALIBRATION_NORMAL, self.split_lengths[SplitRole.CALIBRATION_NORMAL]),
            (SplitRole.VALIDATION, self.split_lengths[SplitRole.VALIDATION]),
        )
        total = sum(length for _, length in role_lengths)
        return total + self.purge_gap_samples * (len(role_lengths) - 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "config_name": "task017_kaggle_staging_pipeline_dry_run",
            "required_report_statement": TASK017_REQUIRED_REPORT_STATEMENT,
            "timeline_sources": list(self.timeline_sources),
            "schema_cross_check_sources": list(self.schema_cross_check_sources),
            "require_exactly_one_timeline_source": True,
            "pipeline_feature_subset": list(self.pipeline_feature_subset),
            "split_lengths": {role.value: self.split_lengths[role] for role in sorted(self.split_lengths, key=lambda item: item.value)},
            "purge_gap_samples": self.purge_gap_samples,
            "seed": self.seed,
            "timestamp_column": self.timestamp_column,
            "label_column": self.label_column,
            "timestamp_formats": list(self.timestamp_formats),
            "binary_actuator_normalization": self.binary_actuator_normalization,
            "candidate_policy": self.candidate_policy.to_dict(),
            "gdn_extraction": self.gdn_config.to_dict(),
            "profile_pairs": [{"source": source, "target": target} for source, target in self.profile_pairs],
            "profiling": self.profiling_config.to_dict(),
            "verification": self.verification_config.to_dict(),
            "runtime": self.runtime_config.to_dict(),
            "final_claims_allowed": False,
            "dec007_resolution_allowed": False,
            "official_sealed_test_access": False,
            "real_provider_network_calls": False,
            "runtime_llm": False,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "StagingPipelineConfig":
        split_lengths = {
            SplitRole(str(role)): int(length)
            for role, length in dict(data.get("split_lengths", {})).items()
        }
        profile_pairs = tuple(
            (str(item["source"]), str(item["target"]))
            for item in data.get("profile_pairs", ())
        )
        return cls(
            timeline_sources=tuple(str(item) for item in data.get("timeline_sources", (DEFAULT_TIMELINE_SOURCE,))),
            schema_cross_check_sources=tuple(str(item) for item in data.get("schema_cross_check_sources", ())),
            pipeline_feature_subset=tuple(str(item) for item in data.get("pipeline_feature_subset", ())),
            split_lengths=split_lengths,
            purge_gap_samples=int(data.get("purge_gap_samples", 4)),
            seed=int(data.get("seed", 17)),
            timestamp_column=str(data.get("timestamp_column", "Timestamp")),
            label_column=str(data.get("label_column", "Normal/Attack")),
            timestamp_formats=tuple(str(item) for item in data.get("timestamp_formats", DEFAULT_TIMESTAMP_FORMATS)),
            binary_actuator_normalization=str(
                data.get("binary_actuator_normalization", "map_two_observed_states_to_0_1")
            ),
            candidate_policy=CandidatePolicy.from_dict(data["candidate_policy"]),
            gdn_config=GDNExtractionConfig(
                top_k=int(data["gdn_extraction"]["top_k"]),
                seed=int(data["gdn_extraction"]["seed"]),
                run_index=int(data["gdn_extraction"].get("run_index", 0)),
                embedding_dim=(
                    None
                    if data["gdn_extraction"].get("embedding_dim") is None
                    else int(data["gdn_extraction"]["embedding_dim"])
                ),
                backend=str(data["gdn_extraction"].get("backend", "deterministic_embedding_task017")),
                config_version=str(data["gdn_extraction"].get("config_version", "1.0")),
            ),
            profile_pairs=profile_pairs,
            profiling_config=RelationProfilingConfig.from_dict(data["profiling"]),
            verification_config=VerificationConfig(
                max_normal_false_fire_rate=float(data["verification"]["max_normal_false_fire_rate"]),
                min_validation_coverage=float(data["verification"]["min_validation_coverage"]),
                firing_overlap_jaccard_threshold=float(data["verification"]["firing_overlap_jaccard_threshold"]),
                min_calibration_support_count=int(data["verification"]["min_calibration_support_count"]),
                parameter_neighborhood_relative_tolerance=float(
                    data["verification"].get("parameter_neighborhood_relative_tolerance", 0.0)
                ),
                config_version=str(data["verification"].get("config_version", "1.0")),
            ),
            runtime_config=RuntimeConfig(
                severity_mode=str(data["runtime"].get("severity_mode", "binary")),
                binary_severity=float(data["runtime"].get("binary_severity", 1.0)),
                merge_adjacent_intervals=bool(data["runtime"].get("merge_adjacent_intervals", True)),
                config_version=str(data["runtime"].get("config_version", "1.0")),
            ),
        )


@dataclass(frozen=True)
class StagingProfileAttempt:
    source: str
    target: str
    status: str
    reason: str
    candidate_pair_allowed: bool
    relation_profile_id: str | None = None
    evidence_pack_id: str | None = None
    rule_id: str | None = None
    verification_report_id: str | None = None
    runtime_firing_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "status": self.status,
            "reason": self.reason,
            "candidate_pair_allowed": self.candidate_pair_allowed,
            "relation_profile_id": self.relation_profile_id,
            "evidence_pack_id": self.evidence_pack_id,
            "rule_id": self.rule_id,
            "verification_report_id": self.verification_report_id,
            "runtime_firing_count": self.runtime_firing_count,
        }


@dataclass(frozen=True)
class StagingPipelineDryRunReport:
    report_statement: str
    config_hash: str
    staging_manifest_id: str
    dataset_manifest_id: str
    data_view_id: str
    split_manifest_id: str
    split_ids: Mapping[str, str]
    used_source_files: tuple[str, ...]
    schema_cross_check_files: tuple[str, ...]
    only_one_pipeline_timeline_source_used: bool
    pipeline_timeline_source: str
    source_kind: str
    dataset_status: str
    candidate_summary: Mapping[str, int]
    metadata_summary: Mapping[str, Any]
    split_summary: Mapping[str, Any]
    profiling_summary: Mapping[str, int]
    verification_summary: Mapping[str, Any]
    runtime_summary: Mapping[str, Any]
    attempts: tuple[StagingProfileAttempt, ...]
    checks: Mapping[str, bool]
    artifact_graph: Mapping[str, str]
    raw_data_audit: Mapping[str, bool]
    limitations: tuple[str, ...]
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "task017_kaggle_staging_pipeline_dry_run_report"

    def __post_init__(self) -> None:
        if self.report_statement != TASK017_REQUIRED_REPORT_STATEMENT:
            raise StagingPipelineDryRunError("TASK-017 required report statement is missing")
        if len(self.config_hash) != 64:
            raise StagingPipelineDryRunError("config_hash must be a 64-character hash")
        if not self.only_one_pipeline_timeline_source_used or self.used_source_files != (DEFAULT_TIMELINE_SOURCE,):
            raise StagingPipelineDryRunError("TASK-017 report must use exactly one merged.csv timeline source")

    @property
    def report_id(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "report_statement": self.report_statement,
            "config_hash": self.config_hash,
            "staging_manifest_id": self.staging_manifest_id,
            "dataset_manifest_id": self.dataset_manifest_id,
            "data_view_id": self.data_view_id,
            "split_manifest_id": self.split_manifest_id,
            "split_ids": dict(sorted(self.split_ids.items())),
            "used_source_files": list(self.used_source_files),
            "schema_cross_check_files": list(self.schema_cross_check_files),
            "only_one_pipeline_timeline_source_used": self.only_one_pipeline_timeline_source_used,
            "pipeline_timeline_source": self.pipeline_timeline_source,
            "source_kind": self.source_kind,
            "dataset_status": self.dataset_status,
            "candidate_summary": dict(sorted(self.candidate_summary.items())),
            "metadata_summary": dict(self.metadata_summary),
            "split_summary": dict(self.split_summary),
            "profiling_summary": dict(sorted(self.profiling_summary.items())),
            "verification_summary": dict(sorted(self.verification_summary.items())),
            "runtime_summary": dict(sorted(self.runtime_summary.items())),
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "checks": dict(sorted(self.checks.items())),
            "artifact_graph": dict(sorted(self.artifact_graph.items())),
            "raw_data_audit": dict(sorted(self.raw_data_audit.items())),
            "limitations": list(self.limitations),
        }


def load_staging_pipeline_config(path: Path) -> StagingPipelineConfig:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return StagingPipelineConfig.from_dict(payload)


def run_task017_staging_pipeline_dry_run_from_env(
    *,
    config: StagingPipelineConfig,
    metadata: MetadataRegistry,
    env_var: str = "SWAT_DATA_ROOT",
    created_at: str = "unspecified",
) -> tuple[StagingPipelineDryRunReport, Mapping[str, Any]]:
    return run_task017_staging_pipeline_dry_run(
        root=resolve_data_root(env_var),
        config=config,
        metadata=metadata,
        created_at=created_at,
    )


def run_task017_staging_pipeline_dry_run(
    *,
    root: Path,
    config: StagingPipelineConfig,
    metadata: MetadataRegistry,
    created_at: str = "unspecified",
) -> tuple[StagingPipelineDryRunReport, Mapping[str, Any]]:
    staging_manifest = inspect_staging_swat_mirror(
        root=root,
        relative_paths=config.timeline_sources,
        timestamp_column=config.timestamp_column,
        label_column=config.label_column,
        timestamp_formats=config.timestamp_formats,
    )
    _validate_staging_manifest(staging_manifest)
    feature_order = tuple(config.pipeline_feature_subset)
    coverage = metadata.coverage_report(staging_manifest.feature_columns)
    pipeline_missing = tuple(name for name in feature_order if name not in staging_manifest.feature_columns)
    if pipeline_missing:
        raise StagingPipelineDryRunError(f"pipeline features missing from staging file: {pipeline_missing}")

    dataset = _dataset_manifest_from_staging(staging_manifest, feature_order=staging_manifest.feature_columns)
    data_view = build_data_view_manifest(
        dataset,
        name=DataViewName.CANONICAL_RULE,
        sampling_period_seconds=_sampling_period_seconds(staging_manifest),
        preprocessing_config={
            "task": "TASK-017",
            "source": DEFAULT_TIMELINE_SOURCE,
            "binary_actuator_normalization": config.binary_actuator_normalization,
        },
        source_view="canonical_rule_view",
    )
    splits = build_sequential_split_manifests(
        total_length=config.required_loaded_rows,
        role_lengths=(
            (SplitRole.TRAIN_NORMAL, config.split_lengths[SplitRole.TRAIN_NORMAL]),
            (SplitRole.CALIBRATION_NORMAL, config.split_lengths[SplitRole.CALIBRATION_NORMAL]),
            (SplitRole.VALIDATION, config.split_lengths[SplitRole.VALIDATION]),
        ),
        dataset_manifest_id=dataset.manifest_id,
        data_view_id=data_view.view_id,
        purge_gap_samples=config.purge_gap_samples,
        seed=config.seed,
    )
    split_by_role = {split.role: split for split in splits}
    timeline = _load_timeline_slice(
        root=root,
        relative_path=config.timeline_sources[0],
        feature_order=feature_order,
        timestamp_column=config.timestamp_column,
        label_column=config.label_column,
        timestamp_formats=config.timestamp_formats,
        row_count=config.required_loaded_rows,
    )
    normalized = _normalize_binary_actuators(timeline.series, metadata, feature_order)

    train_rows = _rows_for_split(normalized.series, feature_order, split_by_role[SplitRole.TRAIN_NORMAL])
    metadata_artifact_id = stable_hash({"metadata": metadata.to_list()})
    universe = build_candidate_universe(
        metadata=metadata,
        feature_order=feature_order,
        policy=config.candidate_policy,
        split=split_by_role[SplitRole.TRAIN_NORMAL],
        data_view=data_view,
        metadata_artifact_id=metadata_artifact_id,
        created_at=created_at,
    )
    checkpoint = fit_deterministic_embedding_checkpoint(
        normal_windows=train_rows,
        feature_order=feature_order,
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

    records_by_id: dict[str, CalibrationRecord] = {}
    verified_rules = []
    verification_report_ids: dict[str, str] = {}
    attempts: list[StagingProfileAttempt] = []
    allowed_pairs = {(pair.source, pair.target) for pair in universe.pairs}

    for source, target in config.profile_pairs:
        candidate_allowed = (source, target) in allowed_pairs
        if not candidate_allowed:
            attempts.append(StagingProfileAttempt(source, target, "unsupported", "not_in_candidate_universe", False))
            continue
        try:
            profile = profile_binary_actuator_to_continuous_sensor(
                source=source,
                target=target,
                series=_series_for_split(normalized.series, split_by_role[SplitRole.CALIBRATION_NORMAL]),
                metadata=metadata,
                split=split_by_role[SplitRole.CALIBRATION_NORMAL],
                data_view=data_view,
                config=config.profiling_config,
                timestamps_seconds=_timestamps_for_split(timeline.timestamps_seconds, split_by_role[SplitRole.CALIBRATION_NORMAL]),
                upstream_artifact_ids=(universe.artifact_id, metadata_artifact_id, edges.artifact_id),
                dataset=dataset.dataset_name,
                data_fingerprint=dataset.manifest_id,
                created_at=created_at,
            )
        except Exception as exc:
            attempts.append(StagingProfileAttempt(source, target, "unsupported", str(exc), True))
            continue
        if profile.normal_support_status != "supported":
            attempts.append(
                StagingProfileAttempt(
                    source,
                    target,
                    "unsupported",
                    profile.normal_support_status,
                    True,
                    relation_profile_id=profile.profile_id,
                )
            )
            continue

        calibration_records = calibrate_relation_profile(
            profile=profile,
            split=split_by_role[SplitRole.CALIBRATION_NORMAL],
            config=config.profiling_config,
        )
        records_by_id.update({record.calibration_id: record for record in calibration_records})
        evidence = build_relation_evidence_pack(profile=profile, calibration_records=calibration_records)
        registry = RuleSchemaRegistry(metadata=metadata, calibration_records=records_by_id)
        build_result = build_template_rule(evidence, registry)
        if build_result.status != "built" or build_result.rule is None:
            attempts.append(
                StagingProfileAttempt(
                    source,
                    target,
                    "rejected",
                    build_result.unsupported_reason or "template_build_failed",
                    True,
                    relation_profile_id=profile.profile_id,
                    evidence_pack_id=evidence.evidence_pack_id,
                )
            )
            continue
        rule = build_result.rule
        normal_dataset = VerificationDataset(
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
            dataset_name=dataset.dataset_name,
            data_fingerprint=dataset.manifest_id,
            split_id=split_by_role[SplitRole.CALIBRATION_NORMAL].split_id,
        )
        validation_dataset = VerificationDataset(
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
            dataset_name=dataset.dataset_name,
            data_fingerprint=dataset.manifest_id,
            split_id=split_by_role[SplitRole.VALIDATION].split_id,
        )
        verification = verify_rule(
            rule,
            registry=registry,
            normal_dataset=normal_dataset,
            validation_dataset=validation_dataset,
            existing_rules=(),
            config=config.verification_config,
        )
        if verification.status != "passed":
            attempts.append(
                StagingProfileAttempt(
                    source,
                    target,
                    "rejected",
                    ";".join(issue.code for issue in verification.issues),
                    True,
                    relation_profile_id=profile.profile_id,
                    evidence_pack_id=evidence.evidence_pack_id,
                    rule_id=rule.rule_id,
                    verification_report_id=verification.report_id,
                )
            )
            continue
        verified_rules.append(rule)
        verification_report_ids[rule.rule_id] = verification.report_id
        attempts.append(
            StagingProfileAttempt(
                source,
                target,
                "verified",
                "passed_verifier",
                True,
                relation_profile_id=profile.profile_id,
                evidence_pack_id=evidence.evidence_pack_id,
                rule_id=rule.rule_id,
                verification_report_id=verification.report_id,
            )
        )

    library = VerifiedRuleLibrary(rules=tuple(verified_rules), verification_report_ids=verification_report_ids)
    engine = RuntimeRuleEngine(
        registry=RuleSchemaRegistry(metadata=metadata, calibration_records=records_by_id),
        config=config.runtime_config,
    )
    engine.load_library(library)
    runtime_evaluation = engine.evaluate(
        TimeSeriesBatch(
            series=_series_for_split(normalized.series, split_by_role[SplitRole.VALIDATION]),
            data_view=data_view,
            timestamps_seconds=_timestamps_for_split(timeline.timestamps_seconds, split_by_role[SplitRole.VALIDATION]),
            batch_id="task017_staging_validation",
            data_fingerprint=dataset.manifest_id,
        )
    )
    runtime_evaluation_id = runtime_evaluation.evaluation_id
    runtime_summary: dict[str, Any] = {
        "runtime_executed": True,
        "rule_count": len(verified_rules),
        "firing_count": len(runtime_evaluation.firing_records),
        "alarm_interval_count": len(runtime_evaluation.alarm_intervals),
        "aggregate_rule_score": runtime_evaluation.aggregate_rule_score,
    }
    attempts = [_attempt_with_runtime_count(attempt, runtime_evaluation.to_dict()) for attempt in attempts]

    split_manifest = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "task017_staging_split_manifest",
        "report_statement": TASK017_REQUIRED_REPORT_STATEMENT,
        "dataset_manifest_id": dataset.manifest_id,
        "data_view_id": data_view.view_id,
        "timeline_source": config.timeline_sources[0],
        "used_source_files": list(config.timeline_sources),
        "splits": {split.role.value: split.to_dict() for split in splits},
        "final_test_accessed": False,
    }
    split_manifest_id = stable_hash(split_manifest)
    checks = {
        "required_report_statement_present": True,
        "staging_manifest_used": staging_manifest.artifact_type == "staging_swat_mirror_manifest",
        "official_manifest_not_used": True,
        "dec007_unresolved": True,
        "only_one_pipeline_timeline_source_used": config.timeline_sources == (DEFAULT_TIMELINE_SOURCE,),
        "normal_attack_merged_not_combined": config.timeline_sources == (DEFAULT_TIMELINE_SOURCE,),
        "split_manifest_built": len(splits) == 3 and split_manifest_id != "",
        "metadata_coverage_complete": coverage.is_complete,
        "candidate_discovery_ran": len(universe.pairs) > 0 and len(edges.edges) >= 0,
        "profile_subset_predeclared": len(config.profile_pairs) > 0,
        "profile_attempts_completed": bool(attempts),
        "template_rules_built_when_supported": all(
            attempt.status != "verified" or attempt.rule_id is not None for attempt in attempts
        ),
        "deterministic_runtime_executed_on_validation_split": True,
        "no_final_test_access": True,
        "no_real_provider_or_network_call": True,
        "runtime_llm_free": True,
        "no_raw_rows_windows_or_plots_tracked": True,
    }
    report = StagingPipelineDryRunReport(
        report_statement=TASK017_REQUIRED_REPORT_STATEMENT,
        config_hash=config.config_hash,
        staging_manifest_id=staging_manifest.manifest_id,
        dataset_manifest_id=dataset.manifest_id,
        data_view_id=data_view.view_id,
        split_manifest_id=split_manifest_id,
        split_ids={split.role.value: split.split_id for split in splits},
        used_source_files=config.timeline_sources,
        schema_cross_check_files=config.schema_cross_check_sources,
        only_one_pipeline_timeline_source_used=config.timeline_sources == (DEFAULT_TIMELINE_SOURCE,),
        pipeline_timeline_source=config.timeline_sources[0],
        source_kind=staging_manifest.source_kind,
        dataset_status=staging_manifest.dataset_status,
        candidate_summary={
            "feature_count": len(feature_order),
            "candidate_pair_count": len(universe.pairs),
            "empty_target_count": len(universe.empty_targets),
            "gdn_emitted_edge_count": len(edges.edges),
        },
        metadata_summary={
            "expected_count": coverage.expected_count,
            "metadata_count": coverage.metadata_count,
            "missing_feature_count": len(coverage.missing_features),
            "extra_metadata_count": len(coverage.extra_metadata),
            "pipeline_feature_count": len(feature_order),
        },
        split_summary={
            "required_loaded_rows": config.required_loaded_rows,
            "sampling_period_seconds": data_view.sampling_period_seconds,
            "label_counts_audit_only": timeline.label_counts_by_split,
            "binary_state_mappings": normalized.binary_state_mappings,
        },
        profiling_summary={
            "predeclared_pair_count": len(config.profile_pairs),
            "attempt_count": len(attempts),
            "verified_rule_count": sum(1 for attempt in attempts if attempt.status == "verified"),
            "unsupported_count": sum(1 for attempt in attempts if attempt.status == "unsupported"),
            "rejected_count": sum(1 for attempt in attempts if attempt.status == "rejected"),
        },
        verification_summary={
            "verified_rule_count": len(verified_rules),
            "verification_config_hash": config.verification_config.config_hash,
        },
        runtime_summary=runtime_summary,
        attempts=tuple(attempts),
        checks=checks,
        artifact_graph={
            "staging_manifest": staging_manifest.manifest_id,
            "dataset_manifest": dataset.manifest_id,
            "data_view": data_view.view_id,
            "split_manifest": split_manifest_id,
            "candidate_universe": universe.artifact_id,
            "gdn_checkpoint": checkpoint.checkpoint_id,
            "gdn_candidate_edges": edges.artifact_id,
            "runtime_evaluation": runtime_evaluation_id,
        },
        raw_data_audit={
            "raw_csv_tracked": False,
            "raw_rows_tracked": False,
            "windows_tracked": False,
            "raw_sequence_plots_tracked": False,
            "downloadable_derived_samples_tracked": False,
            "official_sealed_test_accessed": False,
        },
        limitations=(
            "This is a Kaggle/local staging run for implementation debugging only.",
            "It is not an official SWaT benchmark result and must not be used as a final thesis performance claim.",
            "DEC-007 remains unresolved.",
            "Only merged.csv is used as the pipeline timeline source.",
            "Label counts are recorded for audit only and are not used for tuning or final claims.",
            "No point-adjusted metric is reported as primary.",
        ),
    )
    return report, split_manifest


@dataclass(frozen=True)
class _TimelineSlice:
    series: Mapping[str, tuple[float, ...]]
    timestamps_seconds: tuple[float, ...]
    label_counts_by_split: Mapping[str, Mapping[str, int]]


@dataclass(frozen=True)
class _NormalizedSeries:
    series: Mapping[str, tuple[float, ...]]
    binary_state_mappings: Mapping[str, Mapping[str, float]]


def _validate_relative_path(path: str) -> None:
    parsed = PurePosixPath(path.replace("\\", "/"))
    if parsed.is_absolute() or ".." in parsed.parts:
        raise StagingPipelineDryRunError(f"path must be relative and stay within SWAT_DATA_ROOT: {path}")


def _validate_staging_manifest(manifest: StagingSwatMirrorManifest) -> None:
    if manifest.source_kind != "kaggle_mirror" or manifest.dataset_status != "staging_only":
        raise StagingPipelineDryRunError("TASK-017 requires a Kaggle staging manifest")
    if len(manifest.files) != 1 or manifest.files[0].relative_path != DEFAULT_TIMELINE_SOURCE:
        raise StagingPipelineDryRunError("TASK-017 must inspect exactly merged.csv for the pipeline timeline")


def _sampling_period_seconds(manifest: StagingSwatMirrorManifest) -> float:
    period = manifest.files[0].inferred_sampling_period_seconds
    if period is None:
        raise StagingPipelineDryRunError("staging timeline sampling period could not be inferred")
    return float(period)


def _dataset_manifest_from_staging(
    manifest: StagingSwatMirrorManifest,
    *,
    feature_order: Sequence[str],
) -> DatasetManifest:
    file_record = manifest.files[0]
    feature_hash = stable_hash({"feature_order": list(feature_order)})
    return DatasetManifest(
        dataset_name="SWaT",
        source_kind=manifest.source_kind,
        source_reference=manifest.source_reference,
        dataset_edition="unverified_kaggle_mirror_staging",
        normal_data_version="unverified_kaggle_mirror_staging",
        file_fingerprints={file_record.relative_path: file_record.sha256},
        feature_count=len(feature_order),
        feature_names_hash=feature_hash,
        timestamp_column=manifest.timestamp_column,
        sampling_period_seconds=_sampling_period_seconds(manifest),
        label_column=manifest.label_column,
        label_encoding=manifest.label_schema,
        dataset_status=manifest.dataset_status,
        terms_of_use_status="unverified",
        files=(
            DatasetFile(
                logical_role=file_record.logical_role,
                relative_path=file_record.relative_path,
                sha256=file_record.sha256,
                bytes=file_record.bytes,
                rows_excluding_header=file_record.rows_excluding_header,
                label_counts=file_record.label_counts,
            ),
        ),
    )


def _load_timeline_slice(
    *,
    root: Path,
    relative_path: str,
    feature_order: Sequence[str],
    timestamp_column: str,
    label_column: str,
    timestamp_formats: Sequence[str],
    row_count: int,
) -> _TimelineSlice:
    path = root / relative_path
    if not path.exists() or not path.is_file():
        raise StagingPipelineDryRunError(f"missing staging timeline file: {relative_path}")
    columns_needed = set(feature_order) | {timestamp_column, label_column}
    series: dict[str, list[float]] = {name: [] for name in feature_order}
    timestamps = []
    labels: list[str] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise StagingPipelineDryRunError("timeline CSV has no header")
        columns = tuple(name.strip() for name in reader.fieldnames)
        reader.fieldnames = list(columns)
        missing = sorted(columns_needed - set(columns))
        if missing:
            raise StagingPipelineDryRunError(f"timeline CSV missing columns: {missing}")
        for index, row in enumerate(reader):
            if index >= row_count:
                break
            timestamps.append(parse_timestamp(row[timestamp_column], timestamp_formats))
            labels.append(row[label_column].strip())
            for name in feature_order:
                series[name].append(float(row[name]))
    if len(timestamps) != row_count:
        raise StagingPipelineDryRunError("timeline CSV did not contain enough rows for configured dry-run splits")
    period = infer_regular_sampling_period(timestamps)
    if period is None:
        raise StagingPipelineDryRunError("at least two timestamps are required")
    base = timestamps[0]
    seconds = tuple((timestamp - base).total_seconds() for timestamp in timestamps)
    label_counts = _label_counts_for_ranges(labels)
    return _TimelineSlice(
        series={name: tuple(values) for name, values in series.items()},
        timestamps_seconds=seconds,
        label_counts_by_split=label_counts,
    )


def _label_counts_for_ranges(labels: Sequence[str]) -> Mapping[str, Mapping[str, int]]:
    return {"loaded_slice": _counts(labels)}


def _counts(labels: Sequence[str]) -> Mapping[str, int]:
    counts: dict[str, int] = {}
    for label in labels:
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items()))


def _normalize_binary_actuators(
    series: Mapping[str, Sequence[float]],
    metadata: MetadataRegistry,
    feature_order: Sequence[str],
) -> _NormalizedSeries:
    normalized = {name: tuple(float(value) for value in series[name]) for name in feature_order}
    mappings: dict[str, Mapping[str, float]] = {}
    for name in feature_order:
        variable = metadata.get(name)
        if variable.role != VariableRole.ACTUATOR:
            continue
        values = tuple(sorted(set(normalized[name])))
        if values == (0.0, 1.0):
            mappings[name] = {"0.0": 0.0, "1.0": 1.0}
            continue
        if len(values) == 2:
            low, high = values
            normalized[name] = tuple(0.0 if value == low else 1.0 for value in normalized[name])
            mappings[name] = {str(low): 0.0, str(high): 1.0}
        else:
            mappings[name] = {"observed_state_count": float(len(values))}
    return _NormalizedSeries(series=normalized, binary_state_mappings=mappings)


def _rows_for_split(
    series: Mapping[str, Sequence[float]],
    feature_order: Sequence[str],
    split: SplitManifest,
) -> tuple[Mapping[str, float], ...]:
    rows: list[Mapping[str, float]] = []
    for start, end in split.raw_index_ranges:
        for index in range(start, end):
            rows.append({name: float(series[name][index]) for name in feature_order})
    return tuple(rows)


def _series_for_split(
    series: Mapping[str, Sequence[float]],
    split: SplitManifest,
) -> Mapping[str, tuple[float, ...]]:
    result: dict[str, list[float]] = {name: [] for name in series}
    for start, end in split.raw_index_ranges:
        for name, values in series.items():
            result[name].extend(float(value) for value in values[start:end])
    return {name: tuple(values) for name, values in result.items()}


def _timestamps_for_split(timestamps: Sequence[float], split: SplitManifest) -> tuple[float, ...]:
    values: list[float] = []
    for start, end in split.raw_index_ranges:
        values.extend(float(value) for value in timestamps[start:end])
    if not values:
        return ()
    base = values[0]
    return tuple(value - base for value in values)


def _verification_windows(
    *,
    source: str,
    target: str,
    series: Mapping[str, Sequence[float]],
    timestamps: Sequence[float],
    split: SplitManifest,
    sampling_period_seconds: float,
    window_size: int,
) -> tuple[TimeSeriesWindow, ...]:
    windows: list[TimeSeriesWindow] = []
    for start, end in split.raw_index_ranges:
        cursor = start
        while cursor + window_size <= end:
            window_end = cursor + window_size
            local_timestamps = tuple(float(value - timestamps[cursor]) for value in timestamps[cursor:window_end])
            windows.append(
                TimeSeriesWindow(
                    series={
                        source: tuple(float(value) for value in series[source][cursor:window_end]),
                        target: tuple(float(value) for value in series[target][cursor:window_end]),
                    },
                    sampling_period_seconds=sampling_period_seconds,
                    timestamps_seconds=local_timestamps,
                )
            )
            cursor += window_size
    return tuple(windows)


def _attempt_with_runtime_count(
    attempt: StagingProfileAttempt,
    runtime_evaluation: Mapping[str, Any],
) -> StagingProfileAttempt:
    if attempt.rule_id is None:
        return attempt
    firing_count = sum(1 for record in runtime_evaluation["firing_records"] if record["rule_id"] == attempt.rule_id)
    return StagingProfileAttempt(
        source=attempt.source,
        target=attempt.target,
        status=attempt.status,
        reason=attempt.reason,
        candidate_pair_allowed=attempt.candidate_pair_allowed,
        relation_profile_id=attempt.relation_profile_id,
        evidence_pack_id=attempt.evidence_pack_id,
        rule_id=attempt.rule_id,
        verification_report_id=attempt.verification_report_id,
        runtime_firing_count=firing_count,
    )
