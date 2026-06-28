"""TASK-019 staging-only verified rule evidence audit."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Sequence

from paperworks.candidates import build_candidate_universe
from paperworks.data import DataViewName, SplitRole, build_data_view_manifest, build_sequential_split_manifests, resolve_data_root
from paperworks.data.contracts import SCHEMA_VERSION, stable_hash
from paperworks.data.staging_swat import TASK016_REQUIRED_REPORT_STATEMENT, inspect_staging_swat_mirror
from paperworks.dsl import RuleAst, RuleSchemaRegistry
from paperworks.e2e.staging_dry_run import (
    DEFAULT_TIMELINE_SOURCE,
    StagingPipelineConfig,
    _dataset_manifest_from_staging,
    _load_timeline_slice,
    _normalize_binary_actuators,
    _rows_for_split,
    _sampling_period_seconds,
    _series_for_split,
    _timestamps_for_split,
    _validate_staging_manifest,
    _verification_windows,
)
from paperworks.e2e.support_aware_staging import SupportAwareStagingConfig
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


TASK019_REQUIRED_REPORT_STATEMENT = TASK016_REQUIRED_REPORT_STATEMENT
TASK019_ARTIFACT_TYPE = "task019_rule_evidence_audit"


class RuleEvidenceAuditError(ValueError):
    """Raised when TASK-019 audit inputs are unsafe or inconsistent."""


@dataclass(frozen=True)
class RuleEvidenceCard:
    source_variable: str
    target_variable: str
    source_metadata: Mapping[str, Any]
    target_metadata: Mapping[str, Any]
    relation_type: str
    trigger_count: int
    matched_response_count: int
    missing_response_count: int
    right_censored_count: int
    calibration_parameters: Mapping[str, Mapping[str, Any]]
    rule_id: str
    rule_ast_summary: Mapping[str, Any]
    verifier_report_id: str
    normal_false_fire_summary: Mapping[str, int | float]
    validation_coverage_summary: Mapping[str, int | float]
    runtime_firing_count: int
    staging_plumbing_artifact_only: bool
    human_review_notes: str
    relation_profile_id: str
    evidence_pack_id: str

    def __post_init__(self) -> None:
        if not self.staging_plumbing_artifact_only:
            raise RuleEvidenceAuditError("TASK-019 cards must be marked staging-only")
        if self.human_review_notes != "":
            raise RuleEvidenceAuditError("human_review_notes must be an empty reviewer-owned field")

    @property
    def card_id(self) -> str:
        return stable_hash(self.to_dict(include_card_id=False))

    def to_dict(self, *, include_card_id: bool = True) -> dict[str, Any]:
        data = {
            "source_variable": self.source_variable,
            "target_variable": self.target_variable,
            "source_metadata": dict(self.source_metadata),
            "target_metadata": dict(self.target_metadata),
            "relation_type": self.relation_type,
            "trigger_count": self.trigger_count,
            "matched_response_count": self.matched_response_count,
            "missing_response_count": self.missing_response_count,
            "right_censored_count": self.right_censored_count,
            "calibration_parameters": {
                key: dict(value) for key, value in sorted(self.calibration_parameters.items())
            },
            "rule_id": self.rule_id,
            "rule_ast_summary": dict(self.rule_ast_summary),
            "verifier_report_id": self.verifier_report_id,
            "normal_false_fire_summary": dict(sorted(self.normal_false_fire_summary.items())),
            "validation_coverage_summary": dict(sorted(self.validation_coverage_summary.items())),
            "runtime_firing_count": self.runtime_firing_count,
            "staging_plumbing_artifact_only": self.staging_plumbing_artifact_only,
            "human_review_notes": self.human_review_notes,
            "relation_profile_id": self.relation_profile_id,
            "evidence_pack_id": self.evidence_pack_id,
        }
        if include_card_id:
            return {"card_id": self.card_id, **data}
        return data


@dataclass(frozen=True)
class RuleEvidenceAuditReport:
    report_statement: str
    task018_support_scan_report_id: str
    task018_dry_run_report_id: str
    task018_config_hash: str
    selected_timeline_start_index: int
    selected_loaded_range: tuple[int, int]
    selected_calibration_range: tuple[int, int]
    used_source_files: tuple[str, ...]
    evidence_cards: tuple[RuleEvidenceCard, ...]
    checks: Mapping[str, bool]
    limitations: tuple[str, ...]
    reconstructed_task018_created_at: str
    created_at: str
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = TASK019_ARTIFACT_TYPE

    def __post_init__(self) -> None:
        if self.report_statement != TASK019_REQUIRED_REPORT_STATEMENT:
            raise RuleEvidenceAuditError("TASK-019 required report statement is missing")
        if self.used_source_files != (DEFAULT_TIMELINE_SOURCE,):
            raise RuleEvidenceAuditError("TASK-019 must use only merged.csv")
        if not self.evidence_cards:
            raise RuleEvidenceAuditError("TASK-019 requires at least one verified rule evidence card")
        if not all(card.staging_plumbing_artifact_only for card in self.evidence_cards):
            raise RuleEvidenceAuditError("all TASK-019 evidence cards must be staging-only")

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
            "task018_config_hash": self.task018_config_hash,
            "selected_timeline_start_index": self.selected_timeline_start_index,
            "selected_loaded_range": list(self.selected_loaded_range),
            "selected_calibration_range": list(self.selected_calibration_range),
            "used_source_files": list(self.used_source_files),
            "verified_rule_count": len(self.evidence_cards),
            "evidence_cards": [card.to_dict() for card in self.evidence_cards],
            "checks": dict(sorted(self.checks.items())),
            "limitations": list(self.limitations),
            "reconstructed_task018_created_at": self.reconstructed_task018_created_at,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class _ReconstructedVerifiedEvidence:
    profile: RelationProfile
    calibration_records: tuple[CalibrationRecord, ...]
    rule: RuleAst
    verification: VerificationReport
    evidence_pack_id: str


def run_task019_rule_evidence_audit_from_env(
    *,
    config: SupportAwareStagingConfig,
    metadata: MetadataRegistry,
    support_scan_report_path: Path,
    dry_run_report_path: Path,
    env_var: str = "SWAT_DATA_ROOT",
    reconstructed_task018_created_at: str = "2026-06-28T00:00:00+09:00",
    created_at: str = "unspecified",
) -> RuleEvidenceAuditReport:
    return run_task019_rule_evidence_audit(
        root=resolve_data_root(env_var),
        config=config,
        metadata=metadata,
        support_scan_report=_load_json_report(support_scan_report_path),
        dry_run_report=_load_json_report(dry_run_report_path),
        reconstructed_task018_created_at=reconstructed_task018_created_at,
        created_at=created_at,
    )


def run_task019_rule_evidence_audit(
    *,
    root: Path,
    config: SupportAwareStagingConfig,
    metadata: MetadataRegistry,
    support_scan_report: Mapping[str, Any],
    dry_run_report: Mapping[str, Any],
    reconstructed_task018_created_at: str,
    created_at: str = "unspecified",
) -> RuleEvidenceAuditReport:
    support_payload = _report_payload(support_scan_report)
    dry_payload = _report_payload(dry_run_report)
    _validate_task018_inputs(support_scan_report, dry_run_report, support_payload, dry_payload, config)

    selected = support_payload["selected_slice"]
    selected_start = int(selected["timeline_start_index"])
    dry_config = replace(config.dry_run_config, timeline_start_index=selected_start)
    reconstructed = _reconstruct_verified_evidence(
        root=root,
        config=dry_config,
        metadata=metadata,
        created_at=reconstructed_task018_created_at,
    )
    verified_attempts = tuple(attempt for attempt in dry_payload["attempts"] if attempt["status"] == "verified")
    _assert_reconstructed_matches_task018(reconstructed, verified_attempts)

    runtime_firing_counts = _runtime_firing_counts(
        root=root,
        config=dry_config,
        metadata=metadata,
        reconstructed=tuple(reconstructed),
        created_at=reconstructed_task018_created_at,
    )
    cards = tuple(
        _evidence_card(
            item=item,
            metadata=metadata,
            verification_config=dry_config.verification_config.to_dict(),
            runtime_firing_count=runtime_firing_counts[item.rule.rule_id],
        )
        for item in reconstructed
    )
    checks = {
        "required_report_statement_present": True,
        "used_only_merged_csv": dry_payload["used_source_files"] == [DEFAULT_TIMELINE_SOURCE],
        "support_scan_labels_not_used": support_payload["labels_used_for_selection"] is False,
        "dec007_unresolved": True,
        "no_final_test_access": dry_run_report["split_manifest"]["final_test_accessed"] is False,
        "official_manifest_not_used": dry_payload["checks"]["official_manifest_not_used"] is True,
        "no_raw_rows_windows_or_plots_tracked": dry_payload["checks"]["no_raw_rows_windows_or_plots_tracked"] is True,
        "no_threshold_k_prompt_rule_tuning": True,
        "runtime_llm_free": dry_payload["checks"]["runtime_llm_free"] is True,
        "verified_rule_ids_match_task018": True,
        "verification_report_ids_match_task018": True,
        "human_review_notes_fields_blank": all(card.human_review_notes == "" for card in cards),
        "staging_plumbing_artifact_only": all(card.staging_plumbing_artifact_only for card in cards),
    }
    return RuleEvidenceAuditReport(
        report_statement=TASK019_REQUIRED_REPORT_STATEMENT,
        task018_support_scan_report_id=str(support_scan_report["report_id"]),
        task018_dry_run_report_id=str(dry_run_report["report_id"]),
        task018_config_hash=config.config_hash,
        selected_timeline_start_index=selected_start,
        selected_loaded_range=tuple(int(value) for value in selected["loaded_range"]),
        selected_calibration_range=tuple(int(value) for value in selected["calibration_range"]),
        used_source_files=(DEFAULT_TIMELINE_SOURCE,),
        evidence_cards=cards,
        checks=checks,
        limitations=(
            "This is a Kaggle/local staging run for implementation debugging only.",
            "It is not an official SWaT benchmark result and must not be used as a final thesis performance claim.",
            "Evidence cards are aggregate human-review aids, not performance or explanation-quality claims.",
            "DEC-007 remains unresolved.",
            "No raw rows, windows, raw sequence plots, or downloadable derived samples are persisted.",
        ),
        reconstructed_task018_created_at=reconstructed_task018_created_at,
        created_at=created_at,
    )


def render_rule_evidence_audit_markdown(report: RuleEvidenceAuditReport) -> str:
    lines = [
        "# TASK-019 Rule Evidence Audit",
        "",
        report.report_statement,
        "",
        "## Summary",
        "",
        f"- Report ID: `{report.report_id}`",
        f"- TASK-018 support scan report ID: `{report.task018_support_scan_report_id}`",
        f"- TASK-018 dry-run report ID: `{report.task018_dry_run_report_id}`",
        f"- Selected loaded range: `{list(report.selected_loaded_range)}`",
        f"- Selected calibration range: `{list(report.selected_calibration_range)}`",
        f"- Verified rule evidence cards: {len(report.evidence_cards)}",
        "",
        "## Evidence Cards",
        "",
    ]
    for card in report.evidence_cards:
        normal = card.normal_false_fire_summary
        validation = card.validation_coverage_summary
        source_meta = card.source_metadata
        target_meta = card.target_metadata
        calibration_lines = [
            f"  - `{name}`: {details['value']} {details['unit']} (support={details['normal_support_count']})"
            for name, details in sorted(card.calibration_parameters.items())
        ]
        lines.extend(
            [
                f"### {card.rule_id}",
                "",
                f"- Pair: `{card.source_variable} -> {card.target_variable}`",
                f"- Source metadata: role=`{source_meta['role']}`, value_type=`{source_meta['value_type']}`, stage=`{source_meta.get('stage')}`",
                f"- Target metadata: role=`{target_meta['role']}`, value_type=`{target_meta['value_type']}`, stage=`{target_meta.get('stage')}`",
                f"- Relation type: `{card.relation_type}`",
                f"- Trigger/matched/missing/right-censored: {card.trigger_count}/{card.matched_response_count}/{card.missing_response_count}/{card.right_censored_count}",
                "- Calibration parameters:",
                *calibration_lines,
                f"- Rule AST summary: family=`{card.rule_ast_summary['rule_family']}`, trigger=`changed_to`, response=`response_missing(increase_within)`",
                f"- Normal false fires: {normal['normal_false_fire_count']} / {normal['normal_window_count']} ({normal['normal_false_fire_rate']})",
                f"- Validation coverage: {validation['validation_fire_count']} / {validation['validation_window_count']} ({validation['validation_coverage']})",
                f"- Runtime firing count: {card.runtime_firing_count}",
                f"- Verifier report ID: `{card.verifier_report_id}`",
                f"- Staging/plumbing artifact only: `{str(card.staging_plumbing_artifact_only).lower()}`",
                "- Human-review notes:",
                "",
            ]
        )
    lines.extend(
        [
            "## Checks",
            "",
            *[f"- `{key}`: {str(value).lower()}" for key, value in sorted(report.checks.items())],
            "",
            "## Limitations",
            "",
            *[f"- {item}" for item in report.limitations],
            "",
        ]
    )
    return "\n".join(lines)


def _load_json_report(path: Path) -> Mapping[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _report_payload(report: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = report.get("report")
    if not isinstance(payload, Mapping):
        raise RuleEvidenceAuditError("report JSON must contain a report object")
    return payload


def _validate_task018_inputs(
    support_report: Mapping[str, Any],
    dry_report: Mapping[str, Any],
    support_payload: Mapping[str, Any],
    dry_payload: Mapping[str, Any],
    config: SupportAwareStagingConfig,
) -> None:
    if support_payload.get("report_statement") != TASK019_REQUIRED_REPORT_STATEMENT:
        raise RuleEvidenceAuditError("support scan report statement mismatch")
    if dry_payload.get("report_statement") != TASK019_REQUIRED_REPORT_STATEMENT:
        raise RuleEvidenceAuditError("dry-run report statement mismatch")
    if support_payload.get("used_source_files") != [DEFAULT_TIMELINE_SOURCE]:
        raise RuleEvidenceAuditError("support scan must use only merged.csv")
    if dry_payload.get("used_source_files") != [DEFAULT_TIMELINE_SOURCE]:
        raise RuleEvidenceAuditError("dry-run must use only merged.csv")
    if support_payload.get("labels_used_for_selection") is not False:
        raise RuleEvidenceAuditError("support scan labels must be ignored for selection")
    selected = support_payload.get("selected_slice")
    if not isinstance(selected, Mapping):
        raise RuleEvidenceAuditError("TASK-018 support scan has no selected slice")
    selected_start = int(selected["timeline_start_index"])
    dry_start = int(dry_payload["split_summary"]["timeline_start_index"])
    if selected_start != dry_start:
        raise RuleEvidenceAuditError("TASK-018 selected slice and dry-run start index differ")
    if config.dry_run_config.timeline_sources != (DEFAULT_TIMELINE_SOURCE,):
        raise RuleEvidenceAuditError("TASK-019 config must use merged.csv dry-run source")
    if dry_report["split_manifest"]["final_test_accessed"] is not False:
        raise RuleEvidenceAuditError("TASK-019 cannot audit a run that accessed final test")
    if len(str(support_report.get("report_id", ""))) != 64 or len(str(dry_report.get("report_id", ""))) != 64:
        raise RuleEvidenceAuditError("TASK-018 report ids must be recorded")


def _reconstruct_verified_evidence(
    *,
    root: Path,
    config: StagingPipelineConfig,
    metadata: MetadataRegistry,
    created_at: str,
) -> tuple[_ReconstructedVerifiedEvidence, ...]:
    staging_manifest = inspect_staging_swat_mirror(
        root=root,
        relative_paths=config.timeline_sources,
        timestamp_column=config.timestamp_column,
        label_column=config.label_column,
        timestamp_formats=config.timestamp_formats,
    )
    _validate_staging_manifest(staging_manifest)
    feature_order = tuple(config.pipeline_feature_subset)
    dataset = _dataset_manifest_from_staging(staging_manifest, feature_order=staging_manifest.feature_columns)
    data_view = build_data_view_manifest(
        dataset,
        name=DataViewName.CANONICAL_RULE,
        sampling_period_seconds=_sampling_period_seconds(staging_manifest),
        preprocessing_config={
            "task": "TASK-017",
            "source": DEFAULT_TIMELINE_SOURCE,
            "binary_actuator_normalization": config.binary_actuator_normalization,
            "timeline_start_index": config.timeline_start_index,
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
        start_index=config.timeline_start_index,
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
    allowed_pairs = {(pair.source, pair.target) for pair in universe.pairs}
    records_by_id: dict[str, CalibrationRecord] = {}
    reconstructed: list[_ReconstructedVerifiedEvidence] = []
    for source, target in config.profile_pairs:
        if (source, target) not in allowed_pairs:
            continue
        profile = profile_binary_actuator_to_continuous_sensor(
            source=source,
            target=target,
            series=_series_for_split(normalized.series, split_by_role[SplitRole.CALIBRATION_NORMAL]),
            metadata=metadata,
            split=split_by_role[SplitRole.CALIBRATION_NORMAL],
            data_view=data_view,
            config=config.profiling_config,
            timestamps_seconds=_timestamps_for_split(
                timeline.timestamps_seconds,
                split_by_role[SplitRole.CALIBRATION_NORMAL],
            ),
            upstream_artifact_ids=(universe.artifact_id, metadata_artifact_id, edges.artifact_id),
            dataset=dataset.dataset_name,
            data_fingerprint=dataset.manifest_id,
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
        registry = RuleSchemaRegistry(metadata=metadata, calibration_records=records_by_id)
        build_result = build_template_rule(evidence, registry)
        if build_result.status != "built" or build_result.rule is None:
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
            continue
        reconstructed.append(
            _ReconstructedVerifiedEvidence(
                profile=profile,
                calibration_records=tuple(calibration_records),
                rule=rule,
                verification=verification,
                evidence_pack_id=evidence.evidence_pack_id,
            )
        )
    return tuple(reconstructed)


def _runtime_firing_counts(
    *,
    root: Path,
    config: StagingPipelineConfig,
    metadata: MetadataRegistry,
    reconstructed: Sequence[_ReconstructedVerifiedEvidence],
    created_at: str,
) -> Counter[str]:
    staging_manifest = inspect_staging_swat_mirror(
        root=root,
        relative_paths=config.timeline_sources,
        timestamp_column=config.timestamp_column,
        label_column=config.label_column,
        timestamp_formats=config.timestamp_formats,
    )
    feature_order = tuple(config.pipeline_feature_subset)
    dataset = _dataset_manifest_from_staging(staging_manifest, feature_order=staging_manifest.feature_columns)
    data_view = build_data_view_manifest(
        dataset,
        name=DataViewName.CANONICAL_RULE,
        sampling_period_seconds=_sampling_period_seconds(staging_manifest),
        preprocessing_config={
            "task": "TASK-017",
            "source": DEFAULT_TIMELINE_SOURCE,
            "binary_actuator_normalization": config.binary_actuator_normalization,
            "timeline_start_index": config.timeline_start_index,
            "audit_created_at": created_at,
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
        start_index=config.timeline_start_index,
        row_count=config.required_loaded_rows,
    )
    normalized = _normalize_binary_actuators(timeline.series, metadata, feature_order)
    records_by_id = {
        record.calibration_id: record
        for item in reconstructed
        for record in item.calibration_records
    }
    verification_report_ids = {item.rule.rule_id: item.verification.report_id for item in reconstructed}
    library = VerifiedRuleLibrary(
        rules=tuple(item.rule for item in reconstructed),
        verification_report_ids=verification_report_ids,
    )
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
            batch_id="task019_staging_validation_audit",
            data_fingerprint=dataset.manifest_id,
        )
    )
    return Counter(record.rule_id for record in runtime_evaluation.firing_records)


def _assert_reconstructed_matches_task018(
    reconstructed: Sequence[_ReconstructedVerifiedEvidence],
    verified_attempts: Sequence[Mapping[str, Any]],
) -> None:
    reconstructed_rule_ids = {item.rule.rule_id for item in reconstructed}
    expected_rule_ids = {str(attempt["rule_id"]) for attempt in verified_attempts}
    if reconstructed_rule_ids != expected_rule_ids:
        raise RuleEvidenceAuditError(
            f"reconstructed rule IDs differ from TASK-018: {sorted(reconstructed_rule_ids)} != {sorted(expected_rule_ids)}"
        )
    reconstructed_verification_ids = {item.verification.report_id for item in reconstructed}
    expected_verification_ids = {str(attempt["verification_report_id"]) for attempt in verified_attempts}
    if reconstructed_verification_ids != expected_verification_ids:
        raise RuleEvidenceAuditError("reconstructed verifier report IDs differ from TASK-018")


def _evidence_card(
    *,
    item: _ReconstructedVerifiedEvidence,
    metadata: MetadataRegistry,
    verification_config: Mapping[str, Any],
    runtime_firing_count: int,
) -> RuleEvidenceCard:
    profile = item.profile
    metrics = item.verification.metrics
    return RuleEvidenceCard(
        source_variable=profile.source,
        target_variable=profile.target,
        source_metadata=metadata.get(profile.source).to_dict(),
        target_metadata=metadata.get(profile.target).to_dict(),
        relation_type=profile.relation_type,
        trigger_count=profile.trigger_count,
        matched_response_count=profile.matched_response_count,
        missing_response_count=profile.missing_response_count,
        right_censored_count=profile.right_censored_count,
        calibration_parameters=_calibration_parameter_summary(item.calibration_records),
        rule_id=item.rule.rule_id,
        rule_ast_summary=_rule_ast_summary(item.rule),
        verifier_report_id=item.verification.report_id,
        normal_false_fire_summary={
            "normal_window_count": metrics["normal_window_count"],
            "normal_false_fire_count": metrics["normal_false_fire_count"],
            "normal_false_fire_rate": metrics["normal_false_fire_rate"],
            "max_allowed_normal_false_fire_rate": verification_config["max_normal_false_fire_rate"],
        },
        validation_coverage_summary={
            "validation_window_count": metrics["validation_window_count"],
            "validation_fire_count": metrics["validation_fire_count"],
            "validation_coverage": metrics["validation_coverage"],
            "min_required_validation_coverage": verification_config["min_validation_coverage"],
        },
        runtime_firing_count=runtime_firing_count,
        staging_plumbing_artifact_only=True,
        human_review_notes="",
        relation_profile_id=profile.profile_id,
        evidence_pack_id=item.evidence_pack_id,
    )


def _calibration_parameter_summary(records: Sequence[CalibrationRecord]) -> dict[str, Mapping[str, Any]]:
    return {
        record.parameter_name: {
            "calibration_record_id": record.calibration_id,
            "value": record.value,
            "unit": record.unit,
            "method": record.method,
            "quantile_or_config": dict(record.quantile_or_config),
            "normal_support_count": record.normal_support_count,
            "relation_profile_id": record.relation_profile_id,
            "calibration_split_id": record.calibration_split_id,
        }
        for record in sorted(records, key=lambda item: item.parameter_name)
    }


def _rule_ast_summary(rule: RuleAst) -> dict[str, Any]:
    return {
        "schema_version": rule.schema_version,
        "rule_family": rule.rule_family,
        "source": rule.source,
        "target": rule.target,
        "relation_type": rule.relation_type,
        "trigger_predicate": rule.trigger_predicate.to_dict(),
        "response_predicate": {
            "predicate": rule.response_predicate.predicate,
            "expected_response": {
                "predicate": rule.response_predicate.expected_response.predicate,
                "variable": rule.response_predicate.expected_response.variable,
                "min_magnitude_parameter": "min_response_magnitude",
                "max_delay_seconds_parameter": "max_response_delay_seconds",
            },
        },
        "calibration_reference_ids": {
            key: value.calibration_record_id for key, value in sorted(rule.calibration_references.items())
        },
        "calibrated_values": {
            key: value.resolved_value for key, value in sorted(rule.calibration_references.items())
        },
        "candidate_pair_artifact_id": rule.candidate_pair_artifact_id,
        "metadata_artifact_id": rule.metadata_artifact_id,
        "planner_provenance": rule.planner_provenance.to_dict(),
        "description_template": rule.description_template,
    }
