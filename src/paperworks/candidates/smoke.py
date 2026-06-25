"""TASK-005 candidate feasibility smoke report generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from paperworks.candidates.universe import CandidatePolicy, CandidateUniverseArtifact, build_candidate_universe, candidate_mask
from paperworks.data import (
    DataViewManifest,
    DataViewName,
    DatasetManifest,
    SplitManifest,
    SplitRole,
    build_data_view_manifest,
)
from paperworks.data.contracts import stable_hash
from paperworks.gdn import (
    GDNEdgeArtifact,
    GDNExtractionConfig,
    TorchGDNTrainingConfig,
    extract_masked_topk_edges,
    fit_torch_gdn_embedding_checkpoint,
    message_passing_self_loops,
)
from paperworks.metadata import MetadataRegistry, VariableRole


class CandidateSmokeError(ValueError):
    """Raised when TASK-005 smoke configuration or artifacts are invalid."""


@dataclass(frozen=True)
class CandidateSmokeReport:
    config_hash: str
    candidate_policy_name: str
    pass_fail_gate: str
    passed: bool
    checks: Mapping[str, bool]
    required_report_statements: tuple[str, ...]
    dataset_manifest_id: str
    data_view_id: str
    split_name: str
    candidate_universe_id: str
    checkpoint_id: str
    edge_artifact_id: str
    feature_count: int
    candidate_pair_count: int
    emitted_edge_count: int
    empty_targets: tuple[str, ...]
    candidate_origin_distribution: Mapping[str, int]
    per_target_candidate_counts: Mapping[str, int]
    emitted_candidates: tuple[Mapping[str, Any], ...]
    negative_results: tuple[str, ...]
    phase_gate_recommendation: str
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "task005_candidate_feasibility_smoke_report",
            "config_hash": self.config_hash,
            "candidate_policy_name": self.candidate_policy_name,
            "pass_fail_gate": self.pass_fail_gate,
            "passed": self.passed,
            "checks": dict(self.checks),
            "required_report_statements": list(self.required_report_statements),
            "dataset_manifest_id": self.dataset_manifest_id,
            "data_view_id": self.data_view_id,
            "split_name": self.split_name,
            "candidate_universe_id": self.candidate_universe_id,
            "checkpoint_id": self.checkpoint_id,
            "edge_artifact_id": self.edge_artifact_id,
            "feature_count": self.feature_count,
            "candidate_pair_count": self.candidate_pair_count,
            "emitted_edge_count": self.emitted_edge_count,
            "empty_targets": list(self.empty_targets),
            "candidate_origin_distribution": dict(self.candidate_origin_distribution),
            "per_target_candidate_counts": dict(self.per_target_candidate_counts),
            "emitted_candidates": [dict(candidate) for candidate in self.emitted_candidates],
            "negative_results": list(self.negative_results),
            "phase_gate_recommendation": self.phase_gate_recommendation,
            "limitations": list(self.limitations),
        }

    @property
    def report_id(self) -> str:
        return stable_hash(self.to_dict())


def validate_task005_smoke_report(*, config: Mapping[str, Any], report: CandidateSmokeReport) -> None:
    """Validate required configured checks are present and passing."""

    expected_hash = stable_hash(dict(config))
    if report.config_hash != expected_hash:
        raise CandidateSmokeError("smoke report config_hash does not match config")
    missing = [name for name in config["pass_fail_gate"]["required_checks"] if name not in report.checks]
    if missing:
        raise CandidateSmokeError(f"smoke report missing required checks: {missing}")
    failing = [name for name in config["pass_fail_gate"]["required_checks"] if not report.checks[name]]
    if failing:
        raise CandidateSmokeError(f"smoke report failing required checks: {failing}")
    if not report.passed:
        raise CandidateSmokeError("smoke report did not pass")


def run_task005_smoke(
    *,
    config: Mapping[str, Any],
    metadata: MetadataRegistry,
    feature_order: Sequence[str],
    created_at: str = "unspecified",
) -> CandidateSmokeReport:
    _validate_task005_config(config)
    ordered_features = tuple(feature_order)
    config_hash = stable_hash(dict(config))
    dataset = _build_smoke_dataset_manifest(config=config, feature_order=ordered_features)
    data_view = build_data_view_manifest(
        dataset,
        name=DataViewName.CANONICAL_RULE,
        sampling_period_seconds=float(config["sampling_period_seconds"]),
        preprocessing_config={"task": "TASK-005", "fixture": "synthetic_normal"},
        source_view=str(config["source_view"]),
    )
    split = SplitManifest(
        dataset_manifest_id=dataset.manifest_id,
        data_view_id=data_view.view_id,
        role=SplitRole.TRAIN_NORMAL,
        raw_index_ranges=((0, 8),),
        purge_gap_samples=0,
        seed=int(config["gdn_extraction"]["seed"]),
    )

    policy = CandidatePolicy.from_dict(config["candidate_policy"])
    universe = build_candidate_universe(
        metadata=metadata,
        feature_order=ordered_features,
        policy=policy,
        split=split,
        data_view=data_view,
        metadata_artifact_id=stable_hash({"metadata": metadata.to_list()}),
        created_at=created_at,
    )
    training_config = TorchGDNTrainingConfig(
        seed=int(config["gdn_extraction"]["seed"]),
        embedding_dim=4,
        hidden_dim=8,
        epochs=5,
        learning_rate=0.02,
    )
    checkpoint = fit_torch_gdn_embedding_checkpoint(
        normal_windows=_synthetic_normal_windows(metadata=metadata, feature_order=ordered_features),
        candidate_universe=universe,
        split=split,
        data_view=data_view,
        config=training_config,
    )
    extraction_config = GDNExtractionConfig(
        top_k=int(config["gdn_extraction"]["top_k"]),
        seed=int(config["gdn_extraction"]["seed"]),
        run_index=int(config["gdn_extraction"]["run_index"]),
        backend=str(config["gdn_extraction"]["backend"]),
    )
    edges = extract_masked_topk_edges(
        candidate_universe=universe,
        checkpoint=checkpoint,
        config=extraction_config,
        split=split,
        data_view=data_view,
        created_at=created_at,
    )
    repeated_edges = extract_masked_topk_edges(
        candidate_universe=universe,
        checkpoint=checkpoint,
        config=extraction_config,
        split=split,
        data_view=data_view,
        created_at=created_at,
    )

    checks = _smoke_checks(
        config_hash=config_hash,
        config=config,
        universe=universe,
        edges=edges,
        repeated_edges=repeated_edges,
        data_view=data_view,
        dataset=dataset,
    )
    return CandidateSmokeReport(
        config_hash=config_hash,
        candidate_policy_name=str(config["candidate_policy_name"]),
        pass_fail_gate=str(config["pass_fail_gate"]["name"]),
        passed=all(checks.values()),
        checks=checks,
        required_report_statements=tuple(str(item) for item in config["pass_fail_gate"]["required_report_statements"]),
        dataset_manifest_id=dataset.manifest_id,
        data_view_id=data_view.view_id,
        split_name=split.role.value,
        candidate_universe_id=universe.artifact_id,
        checkpoint_id=checkpoint.checkpoint_id,
        edge_artifact_id=edges.artifact_id,
        feature_count=len(ordered_features),
        candidate_pair_count=len(universe.pairs),
        emitted_edge_count=len(edges.edges),
        empty_targets=universe.empty_targets,
        candidate_origin_distribution=_candidate_origin_distribution(universe),
        per_target_candidate_counts=universe.target_candidate_counts,
        emitted_candidates=_emitted_candidates(
            config_hash=config_hash,
            dataset_manifest_id=dataset.manifest_id,
            edges=edges,
        ),
        negative_results=_negative_results(universe),
        phase_gate_recommendation="proceed_to_phase_gate_review" if all(checks.values()) else "revise_candidate_discovery",
        limitations=(
            "This is a smoke feasibility result.",
            "This is not a final performance claim.",
            "This does not validate anomaly detection performance.",
            "Synthetic normal fixture was used; no raw SWaT rows were loaded.",
        ),
    )


def _validate_task005_config(config: Mapping[str, Any]) -> None:
    if config.get("candidate_policy_name") != "metadata_same_stage_only_smoke":
        raise CandidateSmokeError("TASK-005 requires candidate_policy_name=metadata_same_stage_only_smoke")
    origins = config.get("candidate_origins", {})
    if origins.get("metadata_same_stage") is not True:
        raise CandidateSmokeError("metadata_same_stage origin must be enabled")
    if origins.get("normal_statistical_top_m") is not False:
        raise CandidateSmokeError("normal_statistical_top_m must be disabled")
    if origins.get("type_compatible_fallback") is not False:
        raise CandidateSmokeError("type_compatible_fallback must be disabled")
    policy = config.get("candidate_policy", {})
    if policy.get("domain_same_stage") is not True:
        raise CandidateSmokeError("candidate_policy.domain_same_stage must be true")
    if int(policy.get("statistical_top_m", -1)) != 0:
        raise CandidateSmokeError("candidate_policy.statistical_top_m must be 0")
    if int(policy.get("fallback_min_candidates_per_target", -1)) != 0:
        raise CandidateSmokeError("candidate_policy.fallback_min_candidates_per_target must be 0")
    gate = config.get("pass_fail_gate", {})
    if gate.get("name") != "smoke_feasibility":
        raise CandidateSmokeError("pass_fail_gate.name must be smoke_feasibility")


def _build_smoke_dataset_manifest(*, config: Mapping[str, Any], feature_order: tuple[str, ...]) -> DatasetManifest:
    feature_names_hash = stable_hash({"feature_order": list(feature_order)})
    config_hash = stable_hash(dict(config))
    return DatasetManifest(
        dataset_name=str(config["dataset_name"]),
        source_kind="synthetic_smoke_fixture",
        source_reference="configs/candidates/task005_metadata_same_stage_only_smoke.json",
        dataset_edition="unverified",
        normal_data_version="synthetic_task005_fixture",
        file_fingerprints={"synthetic_task005_normal_fixture": config_hash},
        feature_count=len(feature_order),
        feature_names_hash=feature_names_hash,
        timestamp_column="synthetic_index",
        sampling_period_seconds=float(config["sampling_period_seconds"]),
        label_column="synthetic_label",
        label_encoding={"normal": "Normal", "attack": "Attack"},
        dataset_status=str(config["dataset_status"]),
        terms_of_use_status="unverified",
    )


def _synthetic_normal_windows(*, metadata: MetadataRegistry, feature_order: tuple[str, ...]) -> tuple[dict[str, float], ...]:
    rows: list[dict[str, float]] = []
    for time_index in range(8):
        row: dict[str, float] = {}
        for feature_index, name in enumerate(feature_order):
            variable = metadata.get(name)
            stage = float(variable.stage or 0)
            if variable.role == VariableRole.ACTUATOR:
                row[name] = float((time_index + feature_index) % 2)
            else:
                row[name] = stage + (time_index * 0.1) + (feature_index * 0.01)
        rows.append(row)
    return tuple(rows)


def _smoke_checks(
    *,
    config_hash: str,
    config: Mapping[str, Any],
    universe: CandidateUniverseArtifact,
    edges: GDNEdgeArtifact,
    repeated_edges: GDNEdgeArtifact,
    data_view: DataViewManifest,
    dataset: DatasetManifest,
) -> dict[str, bool]:
    mask = candidate_mask(universe)
    feature_index = {name: index for index, name in enumerate(universe.feature_order)}
    edge_keys = {(edge.source, edge.target) for edge in edges.edges}
    pair_keys = {(pair.source, pair.target) for pair in universe.pairs}
    required_statements = tuple(config["pass_fail_gate"]["required_report_statements"])
    return {
        "candidate_artifacts_generated": bool(universe.pairs) and bool(edges.edges),
        "all_exported_edges_in_candidate_universe": all(
            (edge.source, edge.target) in pair_keys
            and mask[feature_index[edge.target]][feature_index[edge.source]]
            for edge in edges.edges
        ),
        "no_candidate_self_edges": all(edge.source != edge.target for edge in edges.edges),
        "message_passing_self_loops_not_persisted_as_candidates": not any(
            edge.source == edge.target for edge in edges.edges
        )
        and len(message_passing_self_loops(universe.feature_order)) == edges.message_passing_self_loop_count,
        "same_seed_config_hash_stable": edges.artifact_id == repeated_edges.artifact_id and len(config_hash) == 64,
        "required_provenance_fields_present": _required_provenance_present(
            edges=edges,
            config_hash=config_hash,
            dataset_manifest_id=dataset.manifest_id,
        ),
        "no_test_or_attack_labels_used": edges.split_name == SplitRole.TRAIN_NORMAL.value
        and dataset.source_kind == "synthetic_smoke_fixture",
        "candidate_origins_match_metadata_same_stage_only_smoke": _origins_match_metadata_same_stage_only(universe),
        "required_report_statements_present": required_statements
        == (
            "This is a smoke feasibility result.",
            "This is not a final performance claim.",
            "This does not validate anomaly detection performance.",
        ),
        "source_view_and_sampling_period_match": edges.source_view == data_view.source_view
        and edges.sampling_period_seconds == data_view.sampling_period_seconds,
        "config_hash_present": len(config_hash) == 64,
    }


def _required_provenance_present(*, edges: GDNEdgeArtifact, config_hash: str, dataset_manifest_id: str) -> bool:
    if len(config_hash) != 64 or len(dataset_manifest_id) != 64:
        return False
    for edge in edges.edges:
        if not edge.candidate_origins:
            return False
        if not edge.source or not edge.target:
            return False
        if edge.rank <= 0 or edge.K < 0:
            return False
        if edge.embedding_similarity is None:
            return False
        if edge.seed is None:
            return False
        if len(edge.candidate_universe_id) != 64:
            return False
    return True


def _origins_match_metadata_same_stage_only(universe: CandidateUniverseArtifact) -> bool:
    return all(pair.origins == ("domain",) for pair in universe.pairs)


def _candidate_origin_distribution(universe: CandidateUniverseArtifact) -> dict[str, int]:
    counts: dict[str, int] = {}
    for pair in universe.pairs:
        for origin in pair.origins:
            counts[origin] = counts.get(origin, 0) + 1
    return dict(sorted(counts.items()))


def _emitted_candidates(
    *,
    config_hash: str,
    dataset_manifest_id: str,
    edges: GDNEdgeArtifact,
) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        {
            "source": edge.source,
            "target": edge.target,
            "rank": edge.rank,
            "score": edge.embedding_similarity,
            "seed": edge.seed,
            "K": edge.K,
            "candidate_origins": list(edge.candidate_origins),
            "candidate_universe_id": edge.candidate_universe_id,
            "feature_order_hash": edge.feature_order_hash,
            "source_view": edge.source_view,
            "sampling_period_seconds": edge.sampling_period_seconds,
            "checkpoint_id": edge.checkpoint_id,
            "config_hash": config_hash,
            "data_manifest_reference": dataset_manifest_id,
        }
        for edge in edges.edges
    )


def _negative_results(universe: CandidateUniverseArtifact) -> tuple[str, ...]:
    if not universe.empty_targets:
        return ("No empty targets under metadata_same_stage_only_smoke policy.",)
    return tuple(f"Empty target under metadata_same_stage_only_smoke policy: {target}" for target in universe.empty_targets)
