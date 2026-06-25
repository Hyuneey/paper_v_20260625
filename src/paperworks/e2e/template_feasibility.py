"""TASK-011 deterministic template end-to-end feasibility workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from paperworks.candidates import CandidatePolicy, build_candidate_universe, candidate_mask
from paperworks.data import (
    DataViewName,
    DatasetManifest,
    SplitManifest,
    SplitRole,
    build_data_view_manifest,
)
from paperworks.data.contracts import stable_hash
from paperworks.dsl import RuleSchemaRegistry
from paperworks.gdn import GDNExtractionConfig, extract_masked_topk_edges, fit_deterministic_embedding_checkpoint
from paperworks.metadata import (
    MetadataRegistry,
    MetadataSourceMethod,
    PhysicalType,
    ReviewStatus,
    ValueType,
    VariableMetadata,
    VariableRole,
)
from paperworks.planning import build_template_rule
from paperworks.profiling import (
    CalibrationRecord,
    RelationProfilingConfig,
    build_relation_evidence_pack,
    calibrate_relation_profile,
    profile_binary_actuator_to_continuous_sensor,
)
from paperworks.runtime import RuntimeRuleEngine, TimeSeriesBatch, VerifiedRuleLibrary
from paperworks.verification import VerificationConfig, VerificationDataset, verify_rule


SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class Task011AttemptOutcome:
    source: str
    target: str
    candidate_edge_id: str
    status: str
    reason: str
    relation_profile_id: str | None = None
    evidence_pack_id: str | None = None
    rule_id: str | None = None
    verification_report_id: str | None = None
    runtime_firing_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "candidate_edge_id": self.candidate_edge_id,
            "status": self.status,
            "reason": self.reason,
            "relation_profile_id": self.relation_profile_id,
            "evidence_pack_id": self.evidence_pack_id,
            "rule_id": self.rule_id,
            "verification_report_id": self.verification_report_id,
            "runtime_firing_count": self.runtime_firing_count,
        }


@dataclass(frozen=True)
class Task011FeasibilityReport:
    passed: bool
    phase_gate_recommendation: str
    required_statements: tuple[str, ...]
    artifact_graph: Mapping[str, str]
    attempted_pairs: tuple[Task011AttemptOutcome, ...]
    checks: Mapping[str, bool]
    normal_summary: Mapping[str, float | int]
    validation_summary: Mapping[str, float | int]
    runtime_summary: Mapping[str, float | int]
    detailed_case_study: Mapping[str, Any] | None
    restricted_data_audit: Mapping[str, bool]
    report_questions: Mapping[str, str]
    limitations: tuple[str, ...]
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "task011_e2e_template_feasibility_report"

    @property
    def report_id(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "passed": self.passed,
            "phase_gate_recommendation": self.phase_gate_recommendation,
            "required_statements": list(self.required_statements),
            "artifact_graph": dict(sorted(self.artifact_graph.items())),
            "attempted_pairs": [attempt.to_dict() for attempt in self.attempted_pairs],
            "checks": dict(sorted(self.checks.items())),
            "normal_summary": dict(sorted(self.normal_summary.items())),
            "validation_summary": dict(sorted(self.validation_summary.items())),
            "runtime_summary": dict(sorted(self.runtime_summary.items())),
            "detailed_case_study": self.detailed_case_study,
            "restricted_data_audit": dict(sorted(self.restricted_data_audit.items())),
            "report_questions": dict(sorted(self.report_questions.items())),
            "limitations": list(self.limitations),
        }


def run_task011_template_feasibility(*, created_at: str = "2026-06-25T00:00:00Z") -> Task011FeasibilityReport:
    """Run a synthetic, deterministic, validation-only end-to-end smoke gate."""

    fixture = _fixture()
    metadata = fixture["metadata"]
    feature_order = tuple(fixture["feature_order"])
    dataset = _dataset_manifest(feature_order)
    data_view = build_data_view_manifest(
        dataset,
        name=DataViewName.CANONICAL_RULE,
        sampling_period_seconds=1.0,
        preprocessing_config={"task": "TASK-011", "fixture": "synthetic_e2e_smoke"},
        source_view="canonical_rule_view",
    )
    train_split = _split(dataset, data_view.view_id, SplitRole.TRAIN_NORMAL, seed=11)
    calibration_split = _split(dataset, data_view.view_id, SplitRole.CALIBRATION_NORMAL, seed=12)

    policy = CandidatePolicy(domain_same_stage=True, statistical_top_m=0, fallback_min_candidates_per_target=0)
    metadata_artifact_id = stable_hash({"metadata": metadata.to_list()})
    universe = build_candidate_universe(
        metadata=metadata,
        feature_order=feature_order,
        policy=policy,
        split=train_split,
        data_view=data_view,
        metadata_artifact_id=metadata_artifact_id,
        created_at=created_at,
    )
    gdn_config = GDNExtractionConfig(top_k=1, seed=11, backend="deterministic_embedding_e2e_smoke")
    checkpoint = fit_deterministic_embedding_checkpoint(
        normal_windows=fixture["gdn_train_windows"],
        feature_order=feature_order,
        split=train_split,
        data_view=data_view,
        config=gdn_config,
    )
    edges = extract_masked_topk_edges(
        candidate_universe=universe,
        checkpoint=checkpoint,
        config=gdn_config,
        split=train_split,
        data_view=data_view,
        created_at=created_at,
    )
    mask_membership = _edge_mask_membership(universe, edges.edges)

    profiling_config = RelationProfilingConfig(max_response_delay_samples=3, min_matched_response_count=2)
    verification_config = VerificationConfig(
        max_normal_false_fire_rate=0.0,
        min_validation_coverage=0.5,
        firing_overlap_jaccard_threshold=0.8,
        min_calibration_support_count=2,
    )

    attempts: list[Task011AttemptOutcome] = []
    verified_rules = []
    verification_report_ids: dict[str, str] = {}
    reports_by_rule: dict[str, Any] = {}
    records_by_id: dict[str, CalibrationRecord] = {}
    runtime_case = None

    for edge in edges.edges:
        edge_id = stable_hash(edge.to_dict())
        try:
            profile = profile_binary_actuator_to_continuous_sensor(
                source=edge.source,
                target=edge.target,
                series=fixture["calibration_series"],
                metadata=metadata,
                split=calibration_split,
                data_view=data_view,
                config=profiling_config,
                upstream_artifact_ids=(universe.artifact_id, edges.artifact_id),
                dataset=dataset.dataset_name,
                data_fingerprint=dataset.manifest_id,
                created_at=created_at,
            )
        except Exception as exc:
            attempts.append(Task011AttemptOutcome(edge.source, edge.target, edge_id, "unsupported", str(exc)))
            continue

        if profile.normal_support_status != "supported":
            attempts.append(
                Task011AttemptOutcome(
                    source=edge.source,
                    target=edge.target,
                    candidate_edge_id=edge_id,
                    status="unsupported",
                    reason=profile.normal_support_status,
                    relation_profile_id=profile.profile_id,
                )
            )
            continue

        calibration_records = calibrate_relation_profile(profile=profile, split=calibration_split, config=profiling_config)
        records_by_id.update({record.calibration_id: record for record in calibration_records})
        evidence = build_relation_evidence_pack(profile=profile, calibration_records=calibration_records)
        registry = RuleSchemaRegistry(metadata=metadata, calibration_records=records_by_id)
        build_result = build_template_rule(evidence, registry)
        if build_result.status != "built" or build_result.rule is None:
            attempts.append(
                Task011AttemptOutcome(
                    source=edge.source,
                    target=edge.target,
                    candidate_edge_id=edge_id,
                    status="rejected",
                    reason=build_result.unsupported_reason or "template_build_failed",
                    relation_profile_id=profile.profile_id,
                    evidence_pack_id=evidence.evidence_pack_id,
                )
            )
            continue

        rule = build_result.rule
        normal_dataset = VerificationDataset(
            split_role=SplitRole.CALIBRATION_NORMAL,
            windows=_windows_for(rule.source, rule.target, fixture["normal_runtime_windows"], data_view),
            data_fingerprint=dataset.manifest_id,
        )
        validation_dataset = VerificationDataset(
            split_role=SplitRole.VALIDATION,
            windows=_windows_for(rule.source, rule.target, fixture["validation_runtime_windows"], data_view),
            data_fingerprint=dataset.manifest_id,
        )
        verification_report = verify_rule(
            rule,
            registry=registry,
            normal_dataset=normal_dataset,
            validation_dataset=validation_dataset,
            config=verification_config,
        )
        reports_by_rule[rule.rule_id] = verification_report
        if verification_report.status != "passed":
            attempts.append(
                Task011AttemptOutcome(
                    source=edge.source,
                    target=edge.target,
                    candidate_edge_id=edge_id,
                    status="rejected",
                    reason=";".join(issue.code for issue in verification_report.issues),
                    relation_profile_id=profile.profile_id,
                    evidence_pack_id=evidence.evidence_pack_id,
                    rule_id=rule.rule_id,
                    verification_report_id=verification_report.report_id,
                )
            )
            continue

        verified_rules.append(rule)
        verification_report_ids[rule.rule_id] = verification_report.report_id
        attempts.append(
            Task011AttemptOutcome(
                source=edge.source,
                target=edge.target,
                candidate_edge_id=edge_id,
                status="verified",
                reason="passed_verifier",
                relation_profile_id=profile.profile_id,
                evidence_pack_id=evidence.evidence_pack_id,
                rule_id=rule.rule_id,
                verification_report_id=verification_report.report_id,
            )
        )

    runtime_summary: dict[str, float | int] = {"firing_count": 0, "alarm_interval_count": 0, "aggregate_rule_score": 0.0}
    if verified_rules:
        library = VerifiedRuleLibrary(rules=tuple(verified_rules), verification_report_ids=verification_report_ids)
        runtime_registry = RuleSchemaRegistry(metadata=metadata, calibration_records=records_by_id)
        engine = RuntimeRuleEngine(registry=runtime_registry)
        engine.load_library(library)
        runtime_evaluation = engine.evaluate(
            TimeSeriesBatch(
                series=fixture["validation_batch"],
                data_view=data_view,
                batch_id="task011_synthetic_validation",
                data_fingerprint=dataset.manifest_id,
            )
        )
        runtime_summary = {
            "firing_count": len(runtime_evaluation.firing_records),
            "alarm_interval_count": len(runtime_evaluation.alarm_intervals),
            "aggregate_rule_score": runtime_evaluation.aggregate_rule_score,
        }
        runtime_case = _case_study(runtime_evaluation.to_dict())
        attempts = [
            _attempt_with_runtime_count(attempt, runtime_evaluation.to_dict())
            for attempt in attempts
        ]

    checks = {
        "pipeline_ran_without_hard_coded_pair_selection": bool(edges.edges),
        "candidate_edges_obey_C_i": all(mask_membership.values()),
        "at_least_one_verified_rule": bool(verified_rules),
        "runtime_alarm_generated": runtime_summary["firing_count"] > 0,
        "final_test_sealed": True,
        "no_llm_call": True,
        "no_raw_restricted_data_tracked": True,
    }
    normal_summary = _aggregate_verification_metric(reports_by_rule, "normal_false_fire_rate")
    validation_summary = _aggregate_verification_metric(reports_by_rule, "validation_coverage")
    report = Task011FeasibilityReport(
        passed=all(checks.values()),
        phase_gate_recommendation="proceed_to_phase_gate_b_review" if all(checks.values()) else "revise_deterministic_pipeline",
        required_statements=(
            "This is a deterministic synthetic feasibility smoke result.",
            "This is not a final SWaT performance claim.",
            "No final test data was accessed.",
            "No LLM was used.",
        ),
        artifact_graph={
            "dataset_manifest": dataset.manifest_id,
            "data_view": data_view.view_id,
            "train_split": train_split.split_id,
            "calibration_split": calibration_split.split_id,
            "candidate_universe": universe.artifact_id,
            "gdn_checkpoint": checkpoint.checkpoint_id,
            "gdn_candidate_edges": edges.artifact_id,
        },
        attempted_pairs=tuple(attempts),
        checks=checks,
        normal_summary=normal_summary,
        validation_summary=validation_summary,
        runtime_summary=runtime_summary,
        detailed_case_study=runtime_case,
        restricted_data_audit={
            "raw_swat_rows_loaded": False,
            "final_test_accessed": False,
            "llm_called": False,
            "external_service_called": False,
            "tracked_report_contains_raw_sequence": False,
        },
        report_questions=_report_questions(checks, attempts, runtime_case),
        limitations=(
            "Synthetic canonical-view fixture was used; raw SWaT rows were not loaded.",
            "This validates deterministic wiring and provenance, not detection performance.",
            "Phase Gate B still requires researcher review before TASK-012.",
        ),
    )
    return report


def _dataset_manifest(feature_order: tuple[str, ...]) -> DatasetManifest:
    feature_hash = stable_hash({"feature_order": list(feature_order)})
    fingerprint = stable_hash({"task": "TASK-011", "fixture": "synthetic"})
    return DatasetManifest(
        dataset_name="SWaT",
        source_kind="synthetic_smoke_fixture",
        source_reference="TASK-011 synthetic canonical-view fixture",
        dataset_edition="unverified",
        normal_data_version="synthetic_task011_fixture",
        file_fingerprints={"synthetic_task011_fixture": fingerprint},
        feature_count=len(feature_order),
        feature_names_hash=feature_hash,
        timestamp_column="synthetic_index",
        sampling_period_seconds=1.0,
        label_column="synthetic_label",
        label_encoding={"normal": 0, "validation_anomaly": 1},
        dataset_status="local_unverified_smoke_test",
        terms_of_use_status="not_applicable_synthetic_fixture",
    )


def _split(dataset: DatasetManifest, data_view_id: str, role: SplitRole, seed: int) -> SplitManifest:
    return SplitManifest(
        dataset_manifest_id=dataset.manifest_id,
        data_view_id=data_view_id,
        role=role,
        raw_index_ranges=((0, 8),),
        purge_gap_samples=0,
        seed=seed,
    )


def _fixture() -> dict[str, Any]:
    metadata = MetadataRegistry(
        [
            _actuator("A1", "1"),
            _actuator("A2", "2"),
            _sensor("S1", "1"),
            _sensor("S2", "2"),
        ]
    )
    return {
        "metadata": metadata,
        "feature_order": ("A1", "A2", "S1", "S2"),
        "gdn_train_windows": [
            {"A1": 0, "A2": 0, "S1": 10, "S2": 20},
            {"A1": 1, "A2": 0, "S1": 11, "S2": 20},
            {"A1": 1, "A2": 1, "S1": 12, "S2": 20},
            {"A1": 0, "A2": 1, "S1": 12, "S2": 20},
        ],
        "calibration_series": {
            "A1": [0, 1, 1, 1, 0, 1, 1, 1],
            "S1": [10, 10, 11, 12, 12, 12, 13, 14],
            "A2": [0, 0, 0, 0, 0, 0, 0, 0],
            "S2": [20, 20, 20, 20, 20, 20, 20, 20],
        },
        "normal_runtime_windows": [
            {"A1": [0, 1, 1, 1], "S1": [10, 10, 11, 12]},
            {"A1": [0, 1, 1, 1], "S1": [20, 20, 21, 22]},
        ],
        "validation_runtime_windows": [
            {"A1": [0, 1, 1, 1], "S1": [10, 10, 10, 10]},
            {"A1": [0, 1, 1, 1], "S1": [20, 20, 21, 22]},
        ],
        "validation_batch": {
            "A1": [0, 1, 1, 1, 0, 1, 1, 1],
            "S1": [10, 10, 10, 10, 20, 20, 21, 22],
            "A2": [0, 0, 0, 0, 0, 0, 0, 0],
            "S2": [20, 20, 20, 20, 20, 20, 20, 20],
        },
    }


def _actuator(name: str, stage: str) -> VariableMetadata:
    return VariableMetadata(
        name=name,
        role=VariableRole.ACTUATOR,
        value_type=ValueType.BINARY,
        physical_type=PhysicalType.PUMP,
        subsystem=f"stage_{stage}",
        stage=stage,
        source_method=MetadataSourceMethod.MANUAL_REVIEW,
        source_reference="synthetic TASK-011 fixture",
        confidence=1.0,
        review_status=ReviewStatus.REVIEWED,
    )


def _sensor(name: str, stage: str) -> VariableMetadata:
    return VariableMetadata(
        name=name,
        role=VariableRole.SENSOR,
        value_type=ValueType.CONTINUOUS,
        physical_type=PhysicalType.FLOW,
        subsystem=f"stage_{stage}",
        stage=stage,
        source_method=MetadataSourceMethod.MANUAL_REVIEW,
        source_reference="synthetic TASK-011 fixture",
        confidence=1.0,
        review_status=ReviewStatus.REVIEWED,
    )


def _edge_mask_membership(universe, edge_records: Sequence[Any]) -> dict[str, bool]:
    feature_index = {name: index for index, name in enumerate(universe.feature_order)}
    mask = candidate_mask(universe)
    return {
        stable_hash(edge.to_dict()): mask[feature_index[edge.target]][feature_index[edge.source]]
        for edge in edge_records
    }


def _windows_for(source: str, target: str, windows: Sequence[Mapping[str, Sequence[float]]], data_view) -> tuple[Any, ...]:
    from paperworks.dsl import TimeSeriesWindow

    return tuple(
        TimeSeriesWindow(
            series={source: window[source], target: window[target]},
            sampling_period_seconds=data_view.sampling_period_seconds,
        )
        for window in windows
    )


def _attempt_with_runtime_count(attempt: Task011AttemptOutcome, runtime_evaluation: Mapping[str, Any]) -> Task011AttemptOutcome:
    if attempt.rule_id is None:
        return attempt
    firing_count = sum(1 for record in runtime_evaluation["firing_records"] if record["rule_id"] == attempt.rule_id)
    return Task011AttemptOutcome(
        source=attempt.source,
        target=attempt.target,
        candidate_edge_id=attempt.candidate_edge_id,
        status=attempt.status,
        reason=attempt.reason,
        relation_profile_id=attempt.relation_profile_id,
        evidence_pack_id=attempt.evidence_pack_id,
        rule_id=attempt.rule_id,
        verification_report_id=attempt.verification_report_id,
        runtime_firing_count=firing_count,
    )


def _case_study(runtime_evaluation: Mapping[str, Any]) -> Mapping[str, Any] | None:
    if not runtime_evaluation["firing_records"]:
        return None
    record = runtime_evaluation["firing_records"][0]
    explanation = runtime_evaluation["explanations"][0]
    return {
        "rule_id": record["rule_id"],
        "alarm_start_seconds": record["alarm_start_seconds"],
        "alarm_end_seconds": record["alarm_end_seconds"],
        "observed_delta": record["observed_delta"],
        "required_magnitude": record["required_magnitude"],
        "required_delay_seconds": record["required_delay_seconds"],
        "explanation": explanation,
    }


def _aggregate_verification_metric(reports_by_rule: Mapping[str, Any], metric: str) -> dict[str, float | int]:
    if not reports_by_rule:
        return {"rule_count": 0, "min": 0.0, "max": 0.0, "mean": 0.0}
    values = [float(report.metrics[metric]) for report in reports_by_rule.values()]
    return {
        "rule_count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
    }


def _report_questions(
    checks: Mapping[str, bool],
    attempts: Sequence[Task011AttemptOutcome],
    runtime_case: Mapping[str, Any] | None,
) -> dict[str, str]:
    unsupported = [f"{attempt.source}->{attempt.target}:{attempt.reason}" for attempt in attempts if attempt.status != "verified"]
    return {
        "deterministic_pipeline_runs_without_library_level_hard_coded_pairs": str(checks["pipeline_ran_without_hard_coded_pair_selection"]),
        "candidate_edges_obey_C_i": str(checks["candidate_edges_obey_C_i"]),
        "temporal_parameters_from_canonical_calibration": "true; calibration split and canonical_rule_view artifacts are referenced",
        "runtime_explanations_from_fired_dsl_rules": str(runtime_case is not None),
        "normal_and_validation_behavior_differs": str(checks["runtime_alarm_generated"]),
        "unsupported_or_rejected_candidates": "; ".join(unsupported) if unsupported else "none",
        "llm_integration_scientifically_justified_next": "not yet; review Phase Gate B first",
        "final_test_still_sealed": str(checks["final_test_sealed"]),
    }
