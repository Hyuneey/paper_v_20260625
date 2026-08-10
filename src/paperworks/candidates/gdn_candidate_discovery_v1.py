"""TASK-039C-GDN aggregation, ranking, and result contracts."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from paperworks.gdn.upstream_candidate_backend_v1 import (
    FROZEN_SEEDS,
    TASK039C0_GDN_POLICY_HASH,
    TASK039C0_PAIR_UNIVERSE_HASH,
    TASK039C0_PROTOCOL_BUNDLE_HASH,
    UPSTREAM_GDN_COMMIT,
)
from paperworks.v6.candidate_discovery_protocol_v1 import (
    GDNRankInputV1,
    derive_candidate_budget_views_v1,
    rank_gdn_candidates_v1,
)
from paperworks.v6.common import parse_iso_datetime, require_sha256, stable_hash_v1


PASS_STATUS = "passed_task039c_gdn_candidate_discovery"
BLOCKED_STATUSES = (
    "blocked_optional_dependency",
    "blocked_upstream_gdn_backend_unresolved",
)
FAILURE_STATUSES = (
    "failed_gdn_training",
    "failed_gdn_data_boundary",
    "failed_gdn_fidelity",
    "failed_gdn_candidate_contract",
    "failed_gdn_regression",
)


class GDNCandidateDiscoveryError(ValueError):
    """Raised when the frozen GDN ranking contract is violated."""


@dataclass(frozen=True)
class GDNSeedGraphRecordV1:
    seed: int
    successful: bool
    selected_edges: tuple[tuple[str, str], ...]
    candidate_similarities: Mapping[tuple[str, str], float]
    hyperparameter_hash: str
    epoch_count: int | None = None
    best_validation_loss: float | None = None
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        if self.seed not in FROZEN_SEEDS:
            raise GDNCandidateDiscoveryError("seed record is outside the frozen set")
        require_sha256(self.hyperparameter_hash, "hyperparameter_hash")
        if len(self.selected_edges) != len(set(self.selected_edges)):
            raise GDNCandidateDiscoveryError("seed learned graph contains duplicate edges")
        if self.successful:
            if self.failure_reason is not None:
                raise GDNCandidateDiscoveryError("successful seed cannot have a failure reason")
            if self.epoch_count is None or self.epoch_count <= 0:
                raise GDNCandidateDiscoveryError("successful seed requires an epoch count")
            if self.best_validation_loss is None or not math.isfinite(self.best_validation_loss):
                raise GDNCandidateDiscoveryError("successful seed requires finite validation loss")
        elif self.selected_edges or self.candidate_similarities or not self.failure_reason:
            raise GDNCandidateDiscoveryError("failed seed must retain only its failure record")
        for similarity in self.candidate_similarities.values():
            if not math.isfinite(float(similarity)):
                raise GDNCandidateDiscoveryError("candidate similarity must be finite")

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "seed": self.seed,
            "successful": self.successful,
            "selected_edge_count": len(self.selected_edges),
            "hyperparameter_hash": self.hyperparameter_hash,
            "epoch_count": self.epoch_count,
            "best_validation_loss": self.best_validation_loss,
            "failure_reason": self.failure_reason,
        }
        return result


@dataclass(frozen=True)
class GDNCandidateEvidenceV1:
    source: str
    target: str
    edge_selection_frequency: float
    median_upstream_graph_similarity: float
    selected_seed_count: int

    def __post_init__(self) -> None:
        if not self.source or not self.target or self.source == self.target:
            raise GDNCandidateDiscoveryError("candidate must be a directed non-self identity")
        if self.selected_seed_count not in (1, 2, 3):
            raise GDNCandidateDiscoveryError("only candidates selected by at least one seed are supported")
        if self.edge_selection_frequency != self.selected_seed_count / 3.0:
            raise GDNCandidateDiscoveryError("frequency denominator must remain three")
        if not math.isfinite(self.median_upstream_graph_similarity):
            raise GDNCandidateDiscoveryError("median upstream graph similarity must be finite")

    def to_dict(self, *, rank: int) -> dict[str, Any]:
        return {
            "rank": rank,
            "source": self.source,
            "target": self.target,
            "selected_seed_count": self.selected_seed_count,
            "edge_selection_frequency": self.edge_selection_frequency,
            "median_upstream_graph_similarity": self.median_upstream_graph_similarity,
        }


def project_seed_record_to_universe_v1(
    *,
    seed: int,
    selected_model_edges: Sequence[tuple[str, str]],
    model_similarities: Mapping[tuple[str, str], float],
    universe_pairs: Sequence[tuple[str, str]],
    hyperparameter_hash: str,
    epoch_count: int,
    best_validation_loss: float,
) -> GDNSeedGraphRecordV1:
    """Project graph relatedness to frozen source->target identities without reversal."""

    universe = frozenset(universe_pairs)
    if len(universe) != 144:
        raise GDNCandidateDiscoveryError("GDN projection requires the exact 144-pair universe")
    selected = tuple(sorted(pair for pair in set(selected_model_edges) if pair in universe))
    if any(pair not in universe for pair in selected):
        raise GDNCandidateDiscoveryError("projected learned edge escaped the common universe")
    similarities: dict[tuple[str, str], float] = {}
    for pair in universe:
        if pair not in model_similarities:
            raise GDNCandidateDiscoveryError("every common-universe pair requires upstream similarity")
        similarities[pair] = float(model_similarities[pair])
    return GDNSeedGraphRecordV1(
        seed=seed,
        successful=True,
        selected_edges=selected,
        candidate_similarities=similarities,
        hyperparameter_hash=hyperparameter_hash,
        epoch_count=epoch_count,
        best_validation_loss=best_validation_loss,
    )


def aggregate_and_rank_gdn_candidates_v1(
    *,
    universe_pairs: Sequence[tuple[str, str]],
    seed_records: Sequence[GDNSeedGraphRecordV1],
) -> tuple[GDNCandidateEvidenceV1, ...]:
    """Apply the frozen frequency, similarity, and identity ranking exactly."""

    universe = tuple(universe_pairs)
    if len(universe) != 144 or len(set(universe)) != 144:
        raise GDNCandidateDiscoveryError("the common GDN universe must contain 144 unique pairs")
    records = tuple(seed_records)
    if tuple(sorted(item.seed for item in records)) != FROZEN_SEEDS:
        raise GDNCandidateDiscoveryError("exactly seeds 11, 23, and 37 are required")
    if any(not item.successful for item in records):
        raise GDNCandidateDiscoveryError(
            "failed_gdn_training: seed failure makes the denominator-three result fail closed"
        )
    if len({item.hyperparameter_hash for item in records}) != 1:
        raise GDNCandidateDiscoveryError("per-seed hyperparameter variation is prohibited")
    universe_set = frozenset(universe)
    for item in records:
        if any(edge not in universe_set for edge in item.selected_edges):
            raise GDNCandidateDiscoveryError("seed result contains an out-of-universe edge")
        if frozenset(item.candidate_similarities) != universe_set:
            raise GDNCandidateDiscoveryError("seed similarities do not cover the common universe")
    supported: list[GDNCandidateEvidenceV1] = []
    for source, target in universe:
        count = sum((source, target) in set(item.selected_edges) for item in records)
        if count == 0:
            continue
        similarity = statistics.median(
            float(item.candidate_similarities[(source, target)]) for item in records
        )
        supported.append(
            GDNCandidateEvidenceV1(
                source=source,
                target=target,
                edge_selection_frequency=count / 3.0,
                median_upstream_graph_similarity=similarity,
                selected_seed_count=count,
            )
        )
    ranked_inputs = rank_gdn_candidates_v1(
        tuple(
            GDNRankInputV1(
                item.source,
                item.target,
                item.edge_selection_frequency,
                item.median_upstream_graph_similarity,
            )
            for item in supported
        )
    )
    evidence = {(item.source, item.target): item for item in supported}
    return tuple(evidence[(item.source, item.target)] for item in ranked_inputs)


def assert_supplementary_method_boundaries_v1(
    *, attention_used_for_primary_ranking: bool, posthoc_xai_used: bool
) -> None:
    if attention_used_for_primary_ranking:
        raise GDNCandidateDiscoveryError("attention is supplementary_graph_evidence only")
    if posthoc_xai_used:
        raise GDNCandidateDiscoveryError("post-hoc XAI is prohibited as a TASK-039C-GDN method")


@dataclass(frozen=True)
class GDNCandidateResultV1:
    status: str
    phase_a_commit: str
    fidelity_receipt_hash: str
    dependency_environment_fingerprint: str
    backend_classification: str
    source_count: int
    target_count: int
    real_hai_feature_access: bool
    seeds_attempted: tuple[int, ...]
    seeds_completed: tuple[int, ...]
    br2_pair_supervision_used: bool
    train3_accessed: bool
    train4_accessed: bool
    test_accessed: bool
    attention_used_for_primary_ranking: bool
    posthoc_xai_used: bool
    created_at: str
    blocking_reason: str | None = None
    ranking: tuple[GDNCandidateEvidenceV1, ...] = ()
    seed_records: tuple[GDNSeedGraphRecordV1, ...] = ()
    schema_version: str = "1.0.0"
    artifact_type: str = "gdn_candidate_result_v1"
    task_id: str = "TASK-039C-GDN"
    arm_id: str = "GDN"

    def __post_init__(self) -> None:
        if self.schema_version != "1.0.0" or self.artifact_type != "gdn_candidate_result_v1":
            raise GDNCandidateDiscoveryError("GDN result identity changed")
        if self.task_id != "TASK-039C-GDN" or self.arm_id != "GDN":
            raise GDNCandidateDiscoveryError("GDN arm identity changed")
        if len(self.phase_a_commit) != 40:
            raise GDNCandidateDiscoveryError("Phase-A commit must be a full Git SHA")
        require_sha256(self.fidelity_receipt_hash, "fidelity_receipt_hash")
        require_sha256(self.dependency_environment_fingerprint, "dependency_environment_fingerprint")
        if self.source_count != 12 or self.target_count != 12:
            raise GDNCandidateDiscoveryError("frozen source/target counts changed")
        if self.br2_pair_supervision_used or self.train3_accessed or self.train4_accessed or self.test_accessed:
            raise GDNCandidateDiscoveryError("GDN result crossed an anti-leakage boundary")
        assert_supplementary_method_boundaries_v1(
            attention_used_for_primary_ranking=self.attention_used_for_primary_ranking,
            posthoc_xai_used=self.posthoc_xai_used,
        )
        parse_iso_datetime(self.created_at, "created_at")
        if self.status in BLOCKED_STATUSES:
            if not self.blocking_reason:
                raise GDNCandidateDiscoveryError("blocked result requires an exact reason")
            if self.ranking or self.seed_records or self.real_hai_feature_access or self.seeds_attempted or self.seeds_completed:
                raise GDNCandidateDiscoveryError("blocked pre-data result cannot fabricate training or candidates")
        elif self.status == PASS_STATUS:
            if self.blocking_reason is not None or not self.real_hai_feature_access:
                raise GDNCandidateDiscoveryError("passing GDN result requires authorized real-data execution")
            if self.seeds_attempted != FROZEN_SEEDS or self.seeds_completed != FROZEN_SEEDS:
                raise GDNCandidateDiscoveryError("passing GDN result requires all three frozen seeds")
            if tuple(item.seed for item in self.seed_records) != FROZEN_SEEDS:
                raise GDNCandidateDiscoveryError("seed records must preserve frozen seed order")
            expected = aggregate_and_rank_gdn_candidates_v1(
                universe_pairs=tuple(self.seed_records[0].candidate_similarities),
                seed_records=self.seed_records,
            )
            if self.ranking != expected:
                raise GDNCandidateDiscoveryError("stored GDN ranking is not deterministic")
        elif self.status not in FAILURE_STATUSES:
            raise GDNCandidateDiscoveryError("unsupported GDN completion status")

    def _base_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "task_id": self.task_id,
            "arm_id": self.arm_id,
            "status": self.status,
            "phase_a_commit": self.phase_a_commit,
            "protocol_bundle_hash": TASK039C0_PROTOCOL_BUNDLE_HASH,
            "gdn_policy_hash": TASK039C0_GDN_POLICY_HASH,
            "pair_universe_hash": TASK039C0_PAIR_UNIVERSE_HASH,
            "upstream_commit": UPSTREAM_GDN_COMMIT,
            "fidelity_receipt_hash": self.fidelity_receipt_hash,
            "dependency_environment_fingerprint": self.dependency_environment_fingerprint,
            "backend_classification": self.backend_classification,
            "source_count": self.source_count,
            "target_count": self.target_count,
            "real_hai_feature_access": self.real_hai_feature_access,
            "seeds_attempted": list(self.seeds_attempted),
            "seeds_completed": list(self.seeds_completed),
            "br2_pair_supervision_used": self.br2_pair_supervision_used,
            "train3_accessed": self.train3_accessed,
            "train4_accessed": self.train4_accessed,
            "test_accessed": self.test_accessed,
            "attention_used_for_primary_ranking": self.attention_used_for_primary_ranking,
            "posthoc_xai_used": self.posthoc_xai_used,
            "created_at": self.created_at,
        }

    def _payload(self) -> dict[str, Any]:
        payload = self._base_payload()
        if self.status in BLOCKED_STATUSES:
            payload["blocking_reason"] = self.blocking_reason
        elif self.status == PASS_STATUS:
            ranking = [item.to_dict(rank=index) for index, item in enumerate(self.ranking, 1)]
            budget = derive_candidate_budget_views_v1(
                tuple((item.source, item.target) for item in self.ranking)
            )
            ranking_hash = stable_hash_v1(
                {"artifact_type": "gdn_candidate_ranking_v1", "ranking": ranking}
            )
            payload.update(
                {
                    "seed_records": [item.to_dict() for item in self.seed_records],
                    "evaluated_candidate_count": 144,
                    "supported_candidate_count": len(self.ranking),
                    "ranking": ranking,
                    "ranking_hash": ranking_hash,
                    "top10": [{"source": source, "target": target} for source, target in budget.top10],
                    "top20": [{"source": source, "target": target} for source, target in budget.top20],
                    "top40": [{"source": source, "target": target} for source, target in budget.top40],
                    "candidate_shortfall": {str(k): value for k, value in budget.candidate_shortfall.items()},
                }
            )
        else:
            payload["failure_reason"] = self.blocking_reason
        return payload

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "artifact_hash": self.artifact_hash}


def build_blocked_gdn_result_v1(
    *,
    status: str,
    phase_a_commit: str,
    fidelity_receipt_hash: str,
    dependency_environment_fingerprint: str,
    backend_classification: str,
    blocking_reason: str,
    created_at: str,
) -> GDNCandidateResultV1:
    if status not in BLOCKED_STATUSES:
        raise GDNCandidateDiscoveryError("blocked result builder requires a blocked status")
    return GDNCandidateResultV1(
        status=status,
        phase_a_commit=phase_a_commit,
        fidelity_receipt_hash=fidelity_receipt_hash,
        dependency_environment_fingerprint=dependency_environment_fingerprint,
        backend_classification=backend_classification,
        source_count=12,
        target_count=12,
        real_hai_feature_access=False,
        seeds_attempted=(),
        seeds_completed=(),
        br2_pair_supervision_used=False,
        train3_accessed=False,
        train4_accessed=False,
        test_accessed=False,
        attention_used_for_primary_ranking=False,
        posthoc_xai_used=False,
        blocking_reason=blocking_reason,
        created_at=created_at,
    )


__all__ = [
    "BLOCKED_STATUSES",
    "FAILURE_STATUSES",
    "GDNCandidateDiscoveryError",
    "GDNCandidateEvidenceV1",
    "GDNCandidateResultV1",
    "GDNSeedGraphRecordV1",
    "PASS_STATUS",
    "aggregate_and_rank_gdn_candidates_v1",
    "assert_supplementary_method_boundaries_v1",
    "build_blocked_gdn_result_v1",
    "project_seed_record_to_universe_v1",
]
