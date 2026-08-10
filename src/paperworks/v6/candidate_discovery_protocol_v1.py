"""Frozen P1 candidate-discovery protocol for TASK-039C0.

This module defines identity, policy, access, and integration contracts only.
It does not read HAI values, discover candidates, train a graph model, or
grant relation-calibration, rule, verifier, runtime, detector, outer, or
sealed authority.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, fields
from enum import Enum
from types import MappingProxyType
from typing import Any, ClassVar, Mapping, NamedTuple, Sequence, TypeVar

from paperworks.v6.common import (
    CreationMetadataV1,
    V6_FOUNDATION_SCHEMA_VERSION,
    V6FoundationError,
    reject_unknown_fields,
    require_finite,
    require_sha256,
    stable_hash_v1,
)


AUTHORITATIVE_MAIN_COMMIT = "1a55b1aabcfcd4c2a21dc881a9c5d20b6c5c5d81"
DATASET_MANIFEST_ID = "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2"
PROCESS_FREEZE_HASH = "f263d23ceda5ab5ff3c7459e56669ab1dadd7d30cd2243ad8971301990a86325"
BR1_PROTOCOL_BUNDLE_HASH = "5e57e1103b95d8cb24bf55f9ff85a989773dbe05816479dc79c493de044a7bbd"
CANDIDATE_LEARNING_VIEW_ID = "eaa77f331bf79cc6887ccddcfff8818880c1a93c16ebc6fdd2d06a1c8db37eca"
CANONICAL_RULE_VIEW_ID = "d7bcc2b06aedd627db78a0dc104dd6fec5a171f0a2be773180e48ca3e8e52f57"
NORMAL_CANDIDATE_FIT_SPLIT_ID = "cf02e3474a0ade49aec518a886fef0fb0c405b311d827f593fdc207cfad9ab7a"
NORMAL_RELATION_CALIBRATION_SPLIT_ID = "c9e31a99364c0db11f4ad958a93de90ac065661c5171bf8601e2861a5706bba5"
NORMAL_GUARD_SPLIT_ID = "0a09b9171925a24d1955023c41a2b1d9b54682b68ad4c5715943908ff80f0923"
RELATION_FAMILY_ID = "continuous_step_delayed_response_v1"
P1D_FIDELITY_REPORT_HASH = "ee6a332346ee85cf264f23d00f884a9b3ad5d66951affba85cfc300897356370"
TASK039A_REFERENCE_INVENTORY_HASH = "e629f202456abe531e3fa43e3447e686f0936c35b42f6ab9364a4cad83e5a8cc"
TASK039BR0_SOURCE_SUMMARY_HASH = "d4de3e10da9855cc17ebe0e6e9231daa9a6f692f28753567e61c9cd01315a0e1"
UPSTREAM_GDN_REPOSITORY = "https://github.com/d-ailin/GDN"
UPSTREAM_GDN_COMMIT = "9853899da860682669a134e4af315d036aab4eca"

FIT_VALUE_FILES = (
    "hai-23.05/hai-train1.csv",
    "hai-23.05/hai-train2.csv",
)
STATISTICAL_HORIZONS = (1, 5, 10, 30, 60)
GDN_SEEDS = (11, 23, 37)
APPROVED_SOURCE_ROLES = (
    "control_command",
    "actuator_state",
    "actuator_feedback",
)
BR2_PAIR_LEVEL_ARTIFACTS = (
    "BR2_private_relation_ledger",
    "BR2_directional_fit_records",
    "BR2_calibration_confirmation_records",
    "BR2_fit_supported_pair_identities",
    "BR2_confirmed_pair_identities",
    "BR2_target_response_values",
    "BR2_selected_horizons",
    "BR2_pair_level_consistency",
    "BR2_pair_level_effect_ratios",
)


class CandidateDiscoveryProtocolError(V6FoundationError):
    """Raised when a TASK-039C0 protocol boundary is violated."""


class CandidateArmV1(str, Enum):
    META = "META"
    STAT = "STAT"
    GDN = "GDN"


class MetadataEvidenceTierV1(str, Enum):
    M1_EXPLICIT = "M1_EXPLICIT"
    M2_GRAPH_ADJACENT = "M2_GRAPH_ADJACENT"
    M3_SUBSYSTEM_SUPPORTED = "M3_SUBSYSTEM_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"


class StatisticalCandidateStatusV1(str, Enum):
    CROSS_FILE_SIGN_STABLE = "cross_file_sign_stable"
    DIRECTION_UNSTABLE = "direction_unstable"


class GDNArmStatusV1(str, Enum):
    PASSED = "passed"
    BLOCKED_OPTIONAL_DEPENDENCY = "blocked_optional_dependency"
    BLOCKED_UPSTREAM_BACKEND = "blocked_upstream_gdn_backend_unresolved"
    FAILED_TRAINING = "failed_gdn_training"


def _json_value(value: Any) -> Any:
    if isinstance(value, CreationMetadataV1):
        return value.to_dict()
    if isinstance(value, _CandidateProtocolArtifact):
        return value.to_dict()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    return value


ArtifactT = TypeVar("ArtifactT", bound="_CandidateProtocolArtifact")


class _CandidateProtocolArtifact:
    ARTIFACT_TYPE: ClassVar[str]
    TUPLE_FIELDS: ClassVar[frozenset[str]] = frozenset()

    def _validate_artifact_identity(self) -> None:
        if getattr(self, "schema_version") != V6_FOUNDATION_SCHEMA_VERSION:
            raise CandidateDiscoveryProtocolError("schema_version must be 1.0.0")
        if getattr(self, "artifact_type") != self.ARTIFACT_TYPE:
            raise CandidateDiscoveryProtocolError(
                "artifact_type does not match the protocol contract"
            )

    def _content_dict(self) -> dict[str, Any]:
        return {item.name: _json_value(getattr(self, item.name)) for item in fields(self)}

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        result = self._content_dict()
        result["artifact_hash"] = self.artifact_hash
        return result

    @classmethod
    def from_dict(cls: type[ArtifactT], data: Mapping[str, Any]) -> ArtifactT:
        allowed = frozenset(item.name for item in fields(cls)) | {"artifact_hash"}
        try:
            reject_unknown_fields(data, allowed, cls.ARTIFACT_TYPE)
        except V6FoundationError as exc:
            raise CandidateDiscoveryProtocolError(str(exc)) from exc
        kwargs = {item.name: data[item.name] for item in fields(cls)}
        for name in cls.TUPLE_FIELDS:
            kwargs[name] = tuple(kwargs[name])
        if "creation_metadata" in kwargs:
            kwargs["creation_metadata"] = CreationMetadataV1.from_dict(
                kwargs["creation_metadata"]
            )
        result = cls(**kwargs)
        supplied_hash = data.get("artifact_hash")
        if supplied_hash is not None and supplied_hash != result.artifact_hash:
            raise CandidateDiscoveryProtocolError(
                "artifact_hash does not match protocol content"
            )
        return result


def _require_exact_tuple(
    observed: tuple[Any, ...], expected: tuple[Any, ...], field_name: str
) -> None:
    if observed != expected:
        raise CandidateDiscoveryProtocolError(f"{field_name} is not frozen")


def _require_sorted_unique(values: tuple[str, ...], field_name: str) -> None:
    if not values or values != tuple(sorted(values)) or len(values) != len(set(values)):
        raise CandidateDiscoveryProtocolError(
            f"{field_name} must be a non-empty sorted unique tuple"
        )


def _identity_records(
    *,
    process_id: str,
    variables: Sequence[str],
    roles: Sequence[str],
    metadata_refs: Sequence[str],
) -> list[dict[str, str]]:
    if len(variables) != len(roles) or len(variables) != len(metadata_refs):
        raise CandidateDiscoveryProtocolError("identity fields have unequal lengths")
    result = []
    for variable, role, metadata_ref in zip(variables, roles, metadata_refs):
        if not variable or not variable.startswith(f"{process_id}_"):
            raise CandidateDiscoveryProtocolError("candidate identity is outside P1")
        require_sha256(metadata_ref, "metadata_record_hash")
        result.append(
            {
                "variable_name": variable,
                "semantic_role": role,
                "metadata_record_hash": metadata_ref,
            }
        )
    return result


def candidate_identity_list_hash_v1(
    *,
    identity_kind: str,
    process_id: str,
    variables: Sequence[str],
    roles: Sequence[str],
    metadata_refs: Sequence[str],
) -> str:
    """Hash ordered, role-bound and metadata-bound candidate identities."""

    if identity_kind not in {"source", "target"}:
        raise CandidateDiscoveryProtocolError("identity_kind is invalid")
    return stable_hash_v1(
        {
            "identity_type": f"candidate_{identity_kind}_identity_list_v1",
            "process_id": process_id,
            "records": _identity_records(
                process_id=process_id,
                variables=variables,
                roles=roles,
                metadata_refs=metadata_refs,
            ),
        }
    )


def eligible_pair_records_v1(
    source_variables: Sequence[str], target_variables: Sequence[str]
) -> tuple[tuple[str, str], ...]:
    """Return the ordered identity-only directed source-target cross product."""

    return tuple(
        (source, target)
        for source in source_variables
        for target in target_variables
        if source != target
    )


def eligible_pair_universe_hash_v1(
    *, process_id: str, relation_family: str, pairs: Sequence[tuple[str, str]]
) -> str:
    return stable_hash_v1(
        {
            "identity_type": "eligible_directed_candidate_pair_universe_v1",
            "process_id": process_id,
            "relation_family": relation_family,
            "records": [
                {"source_variable": source, "target_variable": target}
                for source, target in pairs
            ],
        }
    )


@dataclass(frozen=True)
class CandidateUniversePolicyV1(_CandidateProtocolArtifact):
    dataset_manifest_id: str
    selected_process_id: str
    selected_process_name: str
    process_freeze_hash: str
    br1_protocol_bundle_hash: str
    candidate_learning_view_id: str
    canonical_rule_view_id: str
    normal_candidate_fit_split_id: str
    normal_relation_calibration_split_id: str
    normal_guard_split_id: str
    relation_family: str
    source_variables: tuple[str, ...]
    source_semantic_roles: tuple[str, ...]
    source_metadata_refs: tuple[str, ...]
    target_variables: tuple[str, ...]
    target_semantic_roles: tuple[str, ...]
    target_metadata_refs: tuple[str, ...]
    source_identity_list_hash: str
    target_identity_list_hash: str
    eligible_pair_universe_hash: str
    eligible_pair_count: int
    source_target_overlap_count: int
    identity_ordering: str
    pair_ordering: str
    out_of_universe_candidates_rejected: bool
    real_data_accessed: bool
    final_candidate_universe_created: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = "candidate_universe_policy_v1"

    ARTIFACT_TYPE = "candidate_universe_policy_v1"
    TUPLE_FIELDS = frozenset(
        {
            "source_variables",
            "source_semantic_roles",
            "source_metadata_refs",
            "target_variables",
            "target_semantic_roles",
            "target_metadata_refs",
        }
    )

    def __post_init__(self) -> None:
        self._validate_artifact_identity()
        lineage = (
            (self.dataset_manifest_id, DATASET_MANIFEST_ID),
            (self.process_freeze_hash, PROCESS_FREEZE_HASH),
            (self.br1_protocol_bundle_hash, BR1_PROTOCOL_BUNDLE_HASH),
            (self.candidate_learning_view_id, CANDIDATE_LEARNING_VIEW_ID),
            (self.canonical_rule_view_id, CANONICAL_RULE_VIEW_ID),
            (self.normal_candidate_fit_split_id, NORMAL_CANDIDATE_FIT_SPLIT_ID),
            (
                self.normal_relation_calibration_split_id,
                NORMAL_RELATION_CALIBRATION_SPLIT_ID,
            ),
            (self.normal_guard_split_id, NORMAL_GUARD_SPLIT_ID),
        )
        if any(observed != expected for observed, expected in lineage):
            raise CandidateDiscoveryProtocolError("candidate-universe lineage mismatch")
        if (
            self.selected_process_id != "P1"
            or self.selected_process_name != "Boiler"
            or self.relation_family != RELATION_FAMILY_ID
        ):
            raise CandidateDiscoveryProtocolError("P1 relation-family freeze changed")
        _require_sorted_unique(self.source_variables, "source_variables")
        _require_sorted_unique(self.target_variables, "target_variables")
        if len(self.source_variables) != 12 or len(self.target_variables) != 12:
            raise CandidateDiscoveryProtocolError("frozen P1 identity count changed")
        if any(role not in APPROVED_SOURCE_ROLES for role in self.source_semantic_roles):
            raise CandidateDiscoveryProtocolError("source role is not approved")
        if any(role != "process_sensor" for role in self.target_semantic_roles):
            raise CandidateDiscoveryProtocolError("target role must be process_sensor")
        source_hash = candidate_identity_list_hash_v1(
            identity_kind="source",
            process_id="P1",
            variables=self.source_variables,
            roles=self.source_semantic_roles,
            metadata_refs=self.source_metadata_refs,
        )
        target_hash = candidate_identity_list_hash_v1(
            identity_kind="target",
            process_id="P1",
            variables=self.target_variables,
            roles=self.target_semantic_roles,
            metadata_refs=self.target_metadata_refs,
        )
        if source_hash != self.source_identity_list_hash:
            raise CandidateDiscoveryProtocolError("source identity binding mismatch")
        if target_hash != self.target_identity_list_hash:
            raise CandidateDiscoveryProtocolError("target identity binding mismatch")
        pairs = eligible_pair_records_v1(self.source_variables, self.target_variables)
        overlap = len(set(self.source_variables) & set(self.target_variables))
        if self.source_target_overlap_count != overlap:
            raise CandidateDiscoveryProtocolError("source-target overlap count mismatch")
        if self.eligible_pair_count != len(pairs):
            raise CandidateDiscoveryProtocolError("eligible pair count mismatch")
        pair_hash = eligible_pair_universe_hash_v1(
            process_id="P1", relation_family=self.relation_family, pairs=pairs
        )
        if self.eligible_pair_universe_hash != pair_hash:
            raise CandidateDiscoveryProtocolError("candidate pair-universe hash mismatch")
        if (
            self.identity_ordering != "lexicographic_variable_name"
            or self.pair_ordering != "source_then_target_lexicographic"
            or not self.out_of_universe_candidates_rejected
            or self.real_data_accessed
            or self.final_candidate_universe_created
        ):
            raise CandidateDiscoveryProtocolError("candidate-universe boundary changed")

    @property
    def pair_set(self) -> frozenset[tuple[str, str]]:
        return frozenset(
            eligible_pair_records_v1(self.source_variables, self.target_variables)
        )


def assert_candidate_in_universe_v1(
    universe: CandidateUniversePolicyV1, source: str, target: str
) -> None:
    if (source, target) not in universe.pair_set:
        raise CandidateDiscoveryProtocolError("candidate is outside frozen universe")


@dataclass(frozen=True)
class CandidateBudgetPolicyV1(_CandidateProtocolArtifact):
    primary_k: int
    sensitivity_k: tuple[int, ...]
    one_ranking_per_arm: bool
    reranking_for_k_prohibited: bool
    padding_prohibited: bool
    shorter_supported_list_allowed: bool
    candidate_shortfall_required: bool
    primary_downstream_view: str
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = "candidate_budget_policy_v1"

    ARTIFACT_TYPE = "candidate_budget_policy_v1"
    TUPLE_FIELDS = frozenset({"sensitivity_k"})

    def __post_init__(self) -> None:
        self._validate_artifact_identity()
        if self.primary_k != 20 or self.sensitivity_k != (10, 40):
            raise CandidateDiscoveryProtocolError("candidate budget changed")
        if not all(
            (
                self.one_ranking_per_arm,
                self.reranking_for_k_prohibited,
                self.padding_prohibited,
                self.shorter_supported_list_allowed,
                self.candidate_shortfall_required,
            )
        ):
            raise CandidateDiscoveryProtocolError("budget safety policy weakened")
        if self.primary_downstream_view != "top20":
            raise CandidateDiscoveryProtocolError("primary candidate budget changed")


class CandidateBudgetViewsV1(NamedTuple):
    top10: tuple[tuple[str, str], ...]
    top20: tuple[tuple[str, str], ...]
    top40: tuple[tuple[str, str], ...]
    candidate_shortfall: Mapping[int, int]


def derive_candidate_budget_views_v1(
    ranking: Sequence[tuple[str, str]],
) -> CandidateBudgetViewsV1:
    normalized = tuple((str(source), str(target)) for source, target in ranking)
    if len(normalized) != len(set(normalized)):
        raise CandidateDiscoveryProtocolError("candidate ranking contains duplicates")
    views = {k: normalized[:k] for k in (10, 20, 40)}
    shortfall = MappingProxyType({k: max(0, k - len(normalized)) for k in (10, 20, 40)})
    return CandidateBudgetViewsV1(views[10], views[20], views[40], shortfall)


@dataclass(frozen=True)
class MetadataCandidatePolicyV1(_CandidateProtocolArtifact):
    task_id: str
    allowed_evidence: tuple[str, ...]
    reference_artifact_refs: tuple[str, ...]
    evidence_tiers: tuple[str, ...]
    official_graph_claim_boundary: str
    ranking_order: tuple[str, ...]
    prohibited_inputs: tuple[str, ...]
    feature_values_used: bool
    llm_relation_invention_allowed: bool
    unsupported_pairs_padded: bool
    candidate_discovery_executed: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = "metadata_candidate_policy_v1"

    ARTIFACT_TYPE = "metadata_candidate_policy_v1"
    TUPLE_FIELDS = frozenset(
        {"allowed_evidence", "reference_artifact_refs", "evidence_tiers", "ranking_order", "prohibited_inputs"}
    )

    def __post_init__(self) -> None:
        self._validate_artifact_identity()
        if self.task_id != "TASK-039C-META":
            raise CandidateDiscoveryProtocolError("metadata arm identity changed")
        _require_exact_tuple(
            self.evidence_tiers,
            tuple(item.value for item in MetadataEvidenceTierV1),
            "metadata evidence tiers",
        )
        _require_exact_tuple(
            self.ranking_order,
            (
                "evidence_tier",
                "independent_official_reference_count_desc",
                "canonical_source_identity",
                "canonical_target_identity",
            ),
            "metadata ranking order",
        )
        if self.official_graph_claim_boundary != "weak_relation_reference_not_causal_truth":
            raise CandidateDiscoveryProtocolError("official graph claim boundary changed")
        if any((self.feature_values_used, self.llm_relation_invention_allowed, self.unsupported_pairs_padded, self.candidate_discovery_executed)):
            raise CandidateDiscoveryProtocolError("metadata arm crossed execution boundary")
        required_prohibited = {"HAI_feature_values", "BR2_pair_results", "statistical_association", "GDN_output", "LLM_semantic_guessing"}
        if not required_prohibited.issubset(self.prohibited_inputs):
            raise CandidateDiscoveryProtocolError("metadata prohibited inputs incomplete")
        for ref in self.reference_artifact_refs:
            require_sha256(ref, "metadata reference")


class MetadataRankInputV1(NamedTuple):
    source: str
    target: str
    evidence_tier: str
    independent_reference_count: int


def rank_metadata_candidates_v1(
    entries: Sequence[MetadataRankInputV1],
) -> tuple[MetadataRankInputV1, ...]:
    tier_order = {item.value: index for index, item in enumerate(MetadataEvidenceTierV1)}
    for entry in entries:
        if entry.evidence_tier not in tier_order or entry.independent_reference_count < 0:
            raise CandidateDiscoveryProtocolError("metadata ranking input is invalid")
    return tuple(
        sorted(
            entries,
            key=lambda item: (
                tier_order[item.evidence_tier],
                -item.independent_reference_count,
                item.source,
                item.target,
            ),
        )
    )


@dataclass(frozen=True)
class StatisticalCandidatePolicyV1(_CandidateProtocolArtifact):
    task_id: str
    allowed_value_files: tuple[str, ...]
    allowed_process_id: str
    normal_candidate_fit_split_id: str
    source_difference_formula: str
    target_difference_formula: str
    horizons_seconds: tuple[int, ...]
    correlation_formula: str
    cross_file_pairs_allowed: bool
    sign_stability_rule: str
    stability_strength_formula: str
    selected_horizon_rule: str
    statistical_candidate_score_formula: str
    no_stable_horizon_status: str
    no_stable_horizon_score: float
    ranking_order: tuple[str, ...]
    arbitrary_minimum_correlation_threshold: float | None
    causal_claim_allowed: bool
    candidate_discovery_executed: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = "statistical_candidate_policy_v1"

    ARTIFACT_TYPE = "statistical_candidate_policy_v1"
    TUPLE_FIELDS = frozenset({"allowed_value_files", "horizons_seconds", "ranking_order"})

    def __post_init__(self) -> None:
        self._validate_artifact_identity()
        if self.task_id != "TASK-039C-STAT" or self.allowed_process_id != "P1":
            raise CandidateDiscoveryProtocolError("statistical arm identity changed")
        _require_exact_tuple(self.allowed_value_files, FIT_VALUE_FILES, "STAT value files")
        _require_exact_tuple(self.horizons_seconds, STATISTICAL_HORIZONS, "STAT horizons")
        if self.normal_candidate_fit_split_id != NORMAL_CANDIDATE_FIT_SPLIT_ID:
            raise CandidateDiscoveryProtocolError("STAT split binding changed")
        if (
            self.source_difference_formula != "dx(t)=x(t)-x(t-1)"
            or self.target_difference_formula != "dy(t)=y(t)-y(t-1)"
            or self.correlation_formula != "corr(dx(t),dy(t+h))_within_file"
            or self.cross_file_pairs_allowed
            or self.sign_stability_rule != "finite_same_nonzero_sign_in_train1_and_train2"
            or self.stability_strength_formula != "min(abs(r_train1),abs(r_train2))"
            or self.selected_horizon_rule != "max_stability_strength_then_shortest_horizon"
            or self.statistical_candidate_score_formula != "stability_strength(h_stat)"
            or self.no_stable_horizon_status != "direction_unstable"
            or self.no_stable_horizon_score != 0.0
        ):
            raise CandidateDiscoveryProtocolError("statistical formula changed")
        _require_exact_tuple(
            self.ranking_order,
            (
                "stable_before_unstable",
                "statistical_candidate_score_desc",
                "selected_horizon_asc",
                "source_lexicographic",
                "target_lexicographic",
            ),
            "STAT ranking order",
        )
        if self.arbitrary_minimum_correlation_threshold is not None or self.causal_claim_allowed or self.candidate_discovery_executed:
            raise CandidateDiscoveryProtocolError("statistical claim or execution boundary changed")


class StatisticalHorizonSelectionV1(NamedTuple):
    status: str
    selected_horizon: int | None
    score: float
    train1_correlation: float | None
    train2_correlation: float | None


def select_statistical_horizon_v1(
    correlations: Mapping[int, tuple[float, float]],
) -> StatisticalHorizonSelectionV1:
    if tuple(sorted(correlations)) != STATISTICAL_HORIZONS:
        raise CandidateDiscoveryProtocolError("all frozen statistical horizons are required")
    stable: list[tuple[float, int, float, float]] = []
    for horizon in STATISTICAL_HORIZONS:
        train1 = require_finite(correlations[horizon][0], "r_train1")
        train2 = require_finite(correlations[horizon][1], "r_train2")
        if train1 != 0.0 and train2 != 0.0 and train1 * train2 > 0.0:
            stable.append((min(abs(train1), abs(train2)), horizon, train1, train2))
    if not stable:
        return StatisticalHorizonSelectionV1(
            StatisticalCandidateStatusV1.DIRECTION_UNSTABLE.value,
            None,
            0.0,
            None,
            None,
        )
    score, horizon, train1, train2 = min(stable, key=lambda item: (-item[0], item[1]))
    return StatisticalHorizonSelectionV1(
        StatisticalCandidateStatusV1.CROSS_FILE_SIGN_STABLE.value,
        horizon,
        score,
        train1,
        train2,
    )


class StatisticalRankInputV1(NamedTuple):
    source: str
    target: str
    selection: StatisticalHorizonSelectionV1


def rank_statistical_candidates_v1(
    entries: Sequence[StatisticalRankInputV1],
) -> tuple[StatisticalRankInputV1, ...]:
    return tuple(
        sorted(
            entries,
            key=lambda item: (
                item.selection.status != StatisticalCandidateStatusV1.CROSS_FILE_SIGN_STABLE.value,
                -item.selection.score,
                item.selection.selected_horizon if item.selection.selected_horizon is not None else math.inf,
                item.source,
                item.target,
            ),
        )
    )


@dataclass(frozen=True)
class GDNCandidatePolicyV1(_CandidateProtocolArtifact):
    task_id: str
    upstream_repository: str
    upstream_commit: str
    p1d_fidelity_report_hash: str
    required_fidelity_artifact: str
    required_fidelity_class: str
    fidelity_checks: tuple[str, ...]
    smoke_backends_allowed_as_gdn: bool
    allowed_value_files: tuple[str, ...]
    allowed_process_id: str
    candidate_learning_view_id: str
    normal_candidate_fit_split_id: str
    full_p1_context_allowed: bool
    output_projection: str
    primary_graph_signal: str
    graph_direction_claim_boundary: str
    seeds: tuple[int, ...]
    identical_architecture_and_hyperparameters_across_seeds: bool
    downstream_quality_tuning_allowed: bool
    edge_selection_frequency_formula: str
    secondary_signal: str
    ranking_order: tuple[str, ...]
    attention_evidence_role: str
    attention_causal_claim_allowed: bool
    post_hoc_xai_primary: bool
    allowed_statuses: tuple[str, ...]
    silent_fallback_allowed: bool
    candidate_discovery_executed: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = "gdn_candidate_policy_v1"

    ARTIFACT_TYPE = "gdn_candidate_policy_v1"
    TUPLE_FIELDS = frozenset(
        {"fidelity_checks", "allowed_value_files", "seeds", "ranking_order", "allowed_statuses"}
    )

    def __post_init__(self) -> None:
        self._validate_artifact_identity()
        if (
            self.task_id != "TASK-039C-GDN"
            or self.upstream_repository != UPSTREAM_GDN_REPOSITORY
            or self.upstream_commit != UPSTREAM_GDN_COMMIT
            or self.p1d_fidelity_report_hash != P1D_FIDELITY_REPORT_HASH
            or self.required_fidelity_artifact != "UpstreamGDNFidelityReceipt"
            or self.required_fidelity_class != "upstream_aligned_validated"
        ):
            raise CandidateDiscoveryProtocolError("GDN fidelity lineage changed")
        _require_exact_tuple(self.allowed_value_files, FIT_VALUE_FILES, "GDN value files")
        _require_exact_tuple(self.seeds, GDN_SEEDS, "GDN seeds")
        _require_exact_tuple(
            self.allowed_statuses,
            tuple(item.value for item in GDNArmStatusV1),
            "GDN statuses",
        )
        _require_exact_tuple(
            self.ranking_order,
            (
                "edge_selection_frequency_desc",
                "median_upstream_graph_similarity_desc",
                "source_lexicographic",
                "target_lexicographic",
            ),
            "GDN ranking order",
        )
        if (
            self.allowed_process_id != "P1"
            or self.candidate_learning_view_id != CANDIDATE_LEARNING_VIEW_ID
            or self.normal_candidate_fit_split_id != NORMAL_CANDIDATE_FIT_SPLIT_ID
            or not self.full_p1_context_allowed
            or self.output_projection != "exact_common_source_target_universe"
            or self.primary_graph_signal != "learned_topk_graph_and_node_embedding_similarity"
            or self.graph_direction_claim_boundary != "graph_relatedness_projected_to_semantic_source_target_not_causality"
            or not self.identical_architecture_and_hyperparameters_across_seeds
            or self.downstream_quality_tuning_allowed
            or self.edge_selection_frequency_formula != "selected_seed_count/3"
            or self.secondary_signal != "median_upstream_graph_similarity_across_seeds"
            or self.attention_evidence_role != "supplementary_graph_evidence"
            or self.attention_causal_claim_allowed
            or self.post_hoc_xai_primary
            or self.smoke_backends_allowed_as_gdn
            or self.silent_fallback_allowed
            or self.candidate_discovery_executed
        ):
            raise CandidateDiscoveryProtocolError("GDN scientific boundary changed")
        required_checks = {
            "pinned_upstream_source_hashes",
            "architecture_identity",
            "graph_construction_semantics",
            "node_embedding_usage",
            "topk_learned_graph_semantics",
            "prediction_loss_training_path",
            "preprocessing",
            "optimizer_configuration",
            "hyperparameter_provenance",
            "no_hidden_project_scientific_modification",
        }
        if not required_checks.issubset(self.fidelity_checks):
            raise CandidateDiscoveryProtocolError("GDN fidelity checks are incomplete")


class GDNRankInputV1(NamedTuple):
    source: str
    target: str
    edge_selection_frequency: float
    median_upstream_graph_similarity: float


def rank_gdn_candidates_v1(
    entries: Sequence[GDNRankInputV1],
) -> tuple[GDNRankInputV1, ...]:
    for entry in entries:
        frequency = require_finite(entry.edge_selection_frequency, "edge frequency")
        require_finite(entry.median_upstream_graph_similarity, "GDN similarity")
        if frequency not in {0.0, 1.0 / 3.0, 2.0 / 3.0, 1.0}:
            raise CandidateDiscoveryProtocolError("edge frequency must derive from three seeds")
    return tuple(
        sorted(
            entries,
            key=lambda item: (
                -item.edge_selection_frequency,
                -item.median_upstream_graph_similarity,
                item.source,
                item.target,
            ),
        )
    )


@dataclass(frozen=True)
class CandidateArmResultContractV1(_CandidateProtocolArtifact):
    arm_ids: tuple[str, ...]
    common_universe_required: bool
    one_deterministic_ranking_required: bool
    budget_views: tuple[int, ...]
    supported_candidate_only: bool
    candidate_shortfall_required: bool
    method_specific_score_only: bool
    cross_arm_score_prohibited: bool
    required_provenance_fields: tuple[str, ...]
    meta_stat_statuses: tuple[str, ...]
    gdn_statuses: tuple[str, ...]
    raw_hai_values_allowed: bool
    result_created: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = "candidate_arm_result_contract_v1"

    ARTIFACT_TYPE = "candidate_arm_result_contract_v1"
    TUPLE_FIELDS = frozenset(
        {"arm_ids", "budget_views", "required_provenance_fields", "meta_stat_statuses", "gdn_statuses"}
    )

    def __post_init__(self) -> None:
        self._validate_artifact_identity()
        _require_exact_tuple(self.arm_ids, ("META", "STAT", "GDN"), "candidate arms")
        _require_exact_tuple(self.budget_views, (10, 20, 40), "candidate result budgets")
        _require_exact_tuple(
            self.meta_stat_statuses,
            ("passed", "candidate_shortfall", "failed"),
            "META/STAT statuses",
        )
        _require_exact_tuple(self.gdn_statuses, tuple(item.value for item in GDNArmStatusV1), "GDN statuses")
        _require_exact_tuple(
            self.required_provenance_fields,
            (
                "candidate_universe_ref",
                "origin_arm",
                "rank",
                "method_evidence_refs",
                "candidate_shortfall",
            ),
            "candidate result provenance",
        )
        if not all(
            (
                self.common_universe_required,
                self.one_deterministic_ranking_required,
                self.supported_candidate_only,
                self.candidate_shortfall_required,
                self.method_specific_score_only,
                self.cross_arm_score_prohibited,
            )
        ):
            raise CandidateDiscoveryProtocolError("arm-result contract weakened")
        if self.raw_hai_values_allowed or self.result_created:
            raise CandidateDiscoveryProtocolError("C0 created an arm result")


@dataclass(frozen=True)
class CandidateIntegrationPolicyV1(_CandidateProtocolArtifact):
    task_id: str
    primary_k: int
    union_arms: tuple[str, ...]
    gdn_included_only_when_passed: bool
    deduplication_identity: tuple[str, ...]
    retained_provenance_fields: tuple[str, ...]
    merged_numerical_score_allowed: bool
    cross_method_union_ranking_allowed: bool
    integration_operation: str
    downstream_task: str
    downstream_evaluation_dimensions: tuple[str, ...]
    br2_confirmed_relations_as_ground_truth_allowed: bool
    integration_executed: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = "candidate_integration_policy_v1"

    ARTIFACT_TYPE = "candidate_integration_policy_v1"
    TUPLE_FIELDS = frozenset(
        {"union_arms", "deduplication_identity", "retained_provenance_fields", "downstream_evaluation_dimensions"}
    )

    def __post_init__(self) -> None:
        self._validate_artifact_identity()
        if self.task_id != "TASK-039C-INTEGRATE" or self.primary_k != 20:
            raise CandidateDiscoveryProtocolError("integration identity changed")
        _require_exact_tuple(self.union_arms, ("META", "STAT", "GDN"), "integration arms")
        _require_exact_tuple(self.deduplication_identity, ("source_variable", "target_variable"), "integration identity")
        _require_exact_tuple(
            self.retained_provenance_fields,
            (
                "origin_arms",
                "META_rank_evidence",
                "STAT_rank_evidence",
                "GDN_rank_evidence",
                "candidate_universe_ref",
            ),
            "integration provenance",
        )
        if (
            not self.gdn_included_only_when_passed
            or self.merged_numerical_score_allowed
            or self.cross_method_union_ranking_allowed
            or self.integration_operation != "set_union_with_provenance"
            or self.downstream_task != "TASK-039D"
            or self.br2_confirmed_relations_as_ground_truth_allowed
            or self.integration_executed
        ):
            raise CandidateDiscoveryProtocolError("integration boundary changed")
        required_dimensions = {
            "confirmed_relation_yield_at_20",
            "distinct_confirmed_source_coverage_at_20",
            "distinct_confirmed_target_coverage_at_20",
            "normal_relation_transfer_at_20",
            "candidate_shortfall",
            "cross_arm_overlap",
        }
        if set(self.downstream_evaluation_dimensions) != required_dimensions:
            raise CandidateDiscoveryProtocolError("downstream planning fields changed")


class ArmCandidateV1(NamedTuple):
    source: str
    target: str
    evidence_refs: tuple[str, ...]


class IntegratedCandidateV1(NamedTuple):
    source: str
    target: str
    origin_arms: tuple[str, ...]
    meta_rank: int | None
    stat_rank: int | None
    gdn_rank: int | None
    evidence_refs: Mapping[str, tuple[str, ...]]


def integrate_candidate_union_v1(
    *,
    universe: CandidateUniversePolicyV1,
    meta_top20: Sequence[ArmCandidateV1],
    stat_top20: Sequence[ArmCandidateV1],
    gdn_top20: Sequence[ArmCandidateV1] | None,
) -> tuple[IntegratedCandidateV1, ...]:
    """Build an unscored set union in stable arm encounter order."""

    if any(len(items) > 20 for items in (meta_top20, stat_top20, gdn_top20 or ())):
        raise CandidateDiscoveryProtocolError("integration accepts top20 views only")
    by_pair: dict[tuple[str, str], dict[str, Any]] = {}
    for arm, items in (("META", meta_top20), ("STAT", stat_top20), ("GDN", gdn_top20 or ())):
        seen_in_arm: set[tuple[str, str]] = set()
        for rank, entry in enumerate(items, start=1):
            assert_candidate_in_universe_v1(universe, entry.source, entry.target)
            for evidence_ref in entry.evidence_refs:
                require_sha256(evidence_ref, "method evidence reference")
            pair = (entry.source, entry.target)
            if pair in seen_in_arm:
                raise CandidateDiscoveryProtocolError("arm ranking contains duplicate pair")
            seen_in_arm.add(pair)
            state = by_pair.setdefault(
                pair,
                {"arms": [], "ranks": {}, "evidence": {}},
            )
            state["arms"].append(arm)
            state["ranks"][arm] = rank
            state["evidence"][arm] = tuple(entry.evidence_refs)
    return tuple(
        IntegratedCandidateV1(
            source,
            target,
            tuple(state["arms"]),
            state["ranks"].get("META"),
            state["ranks"].get("STAT"),
            state["ranks"].get("GDN"),
            MappingProxyType(dict(state["evidence"])),
        )
        for (source, target), state in by_pair.items()
    )


@dataclass(frozen=True)
class TASK039C0DataAccessPolicyV1(_CandidateProtocolArtifact):
    arm_ids: tuple[str, ...]
    allowed_process_ids: tuple[str, ...]
    prohibited_process_ids: tuple[str, ...]
    meta_value_files: tuple[str, ...]
    stat_value_files: tuple[str, ...]
    gdn_value_files: tuple[str, ...]
    prohibited_value_files: tuple[str, ...]
    br2_pair_level_artifacts: tuple[str, ...]
    br2_pair_level_access_mode: str
    allowed_br2_source_reuse_fields: tuple[str, ...]
    prohibited_br2_source_reuse_fields: tuple[str, ...]
    train3_reserved_for_relation_calibration: bool
    train4_reserved_for_normal_guard: bool
    real_hai_feature_values_accessed: bool
    candidate_discovery_executed: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = "task039c0_data_access_policy_v1"

    ARTIFACT_TYPE = "task039c0_data_access_policy_v1"
    TUPLE_FIELDS = frozenset(
        {
            "arm_ids",
            "allowed_process_ids",
            "prohibited_process_ids",
            "meta_value_files",
            "stat_value_files",
            "gdn_value_files",
            "prohibited_value_files",
            "br2_pair_level_artifacts",
            "allowed_br2_source_reuse_fields",
            "prohibited_br2_source_reuse_fields",
        }
    )

    def __post_init__(self) -> None:
        self._validate_artifact_identity()
        _require_exact_tuple(self.arm_ids, ("META", "STAT", "GDN"), "data-access arms")
        _require_exact_tuple(self.allowed_process_ids, ("P1",), "allowed process")
        _require_exact_tuple(self.prohibited_process_ids, ("P2", "P3", "P4"), "prohibited processes")
        _require_exact_tuple(self.meta_value_files, (), "META feature files")
        _require_exact_tuple(self.stat_value_files, FIT_VALUE_FILES, "STAT feature files")
        _require_exact_tuple(self.gdn_value_files, FIT_VALUE_FILES, "GDN feature files")
        _require_exact_tuple(self.br2_pair_level_artifacts, BR2_PAIR_LEVEL_ARTIFACTS, "BR2 pair-level artifacts")
        if (
            self.br2_pair_level_access_mode != "lineage_hash_verification_only"
            or not self.train3_reserved_for_relation_calibration
            or not self.train4_reserved_for_normal_guard
            or self.real_hai_feature_values_accessed
            or self.candidate_discovery_executed
        ):
            raise CandidateDiscoveryProtocolError("C0 data boundary changed")
        required_allowed = {"source_identity", "semantic_role", "eligibility_status"}
        required_prohibited = {"source_step_threshold", "stability_tolerance", "event_count", "event_timestamp"}
        if set(self.allowed_br2_source_reuse_fields) != required_allowed or set(self.prohibited_br2_source_reuse_fields) != required_prohibited:
            raise CandidateDiscoveryProtocolError("BR2 source reuse boundary changed")


def authorize_candidate_arm_value_access_v1(
    policy: TASK039C0DataAccessPolicyV1,
    *,
    arm: str,
    process_id: str,
    relative_file: str,
) -> None:
    if process_id not in policy.allowed_process_ids:
        raise CandidateDiscoveryProtocolError("candidate arm process access prohibited")
    allowed = {
        "META": policy.meta_value_files,
        "STAT": policy.stat_value_files,
        "GDN": policy.gdn_value_files,
    }
    if arm not in allowed or relative_file not in allowed[arm]:
        raise CandidateDiscoveryProtocolError("candidate arm feature access prohibited")


def authorize_br2_pair_artifact_use_v1(
    policy: TASK039C0DataAccessPolicyV1,
    *,
    artifact_kind: str,
    requested_mode: str,
) -> None:
    if (
        artifact_kind not in policy.br2_pair_level_artifacts
        or requested_mode != "lineage_hash_verification"
    ):
        raise CandidateDiscoveryProtocolError("BR2 relation-result access prohibited")


@dataclass(frozen=True)
class TASK039C0ParallelBranchPlanV1(_CandidateProtocolArtifact):
    protocol_branch: str
    parallel_branches: tuple[str, ...]
    base_commit_policy: str
    all_initial_refs_must_equal: bool
    empty_commits_prohibited: bool
    create_only_after_passing_protocol_commit: bool
    branch_creation_recorded_in_git_refs: bool
    main_merge_authorized: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = "task039c0_parallel_branch_plan_v1"

    ARTIFACT_TYPE = "task039c0_parallel_branch_plan_v1"
    TUPLE_FIELDS = frozenset({"parallel_branches"})

    def __post_init__(self) -> None:
        self._validate_artifact_identity()
        if self.protocol_branch != "task-039c0-candidate-protocol":
            raise CandidateDiscoveryProtocolError("protocol branch identity changed")
        _require_exact_tuple(
            self.parallel_branches,
            (
                "task-039c-meta",
                "task-039c-stat",
                "task-039c-gdn",
                "task-039c-review",
                "task-039c-integration",
            ),
            "parallel branches",
        )
        if (
            self.base_commit_policy != "exact_git_commit_containing_this_protocol_bundle"
            or not self.all_initial_refs_must_equal
            or not self.empty_commits_prohibited
            or not self.create_only_after_passing_protocol_commit
            or not self.branch_creation_recorded_in_git_refs
            or self.main_merge_authorized
        ):
            raise CandidateDiscoveryProtocolError("parallel branch plan changed")


@dataclass(frozen=True)
class CandidateDiscoveryProtocolBundleV1(_CandidateProtocolArtifact):
    task_id: str
    status: str
    authoritative_main_commit: str
    selected_process_id: str
    selected_process_name: str
    universe_policy: CandidateUniversePolicyV1
    budget_policy: CandidateBudgetPolicyV1
    metadata_policy: MetadataCandidatePolicyV1
    statistical_policy: StatisticalCandidatePolicyV1
    gdn_policy: GDNCandidatePolicyV1
    arm_result_contract: CandidateArmResultContractV1
    integration_policy: CandidateIntegrationPolicyV1
    data_access_policy: TASK039C0DataAccessPolicyV1
    parallel_branch_plan: TASK039C0ParallelBranchPlanV1
    authorized_future_work: tuple[str, ...]
    prohibited_authority: tuple[str, ...]
    real_hai_feature_access: bool
    candidate_discovery_executed: bool
    final_candidate_universe_created: bool
    task039d_authorized: bool
    main_merge_authorized: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = "candidate_discovery_protocol_bundle_v1"

    ARTIFACT_TYPE = "candidate_discovery_protocol_bundle_v1"
    TUPLE_FIELDS = frozenset({"authorized_future_work", "prohibited_authority"})

    def __post_init__(self) -> None:
        self._validate_artifact_identity()
        if (
            self.task_id != "TASK-039C0"
            or self.status != "passed_task039c0_candidate_discovery_protocol_freeze"
            or self.authoritative_main_commit != AUTHORITATIVE_MAIN_COMMIT
            or self.selected_process_id != "P1"
            or self.selected_process_name != "Boiler"
        ):
            raise CandidateDiscoveryProtocolError("C0 bundle identity changed")
        if any(
            (
                self.real_hai_feature_access,
                self.candidate_discovery_executed,
                self.final_candidate_universe_created,
                self.task039d_authorized,
                self.main_merge_authorized,
            )
        ):
            raise CandidateDiscoveryProtocolError("C0 authority boundary crossed")
        required_authorized = {
            "P1_candidate_discovery",
            "candidate_ranking",
            "graph_evidence",
            "candidate_set_integration",
        }
        required_prohibited = {
            "TASK-039D_relation_calibration",
            "Rule_v2",
            "rule_construction",
            "Agent_calls",
            "detector_execution",
            "runtime_execution",
            "attack_or_test_access",
            "outer_validation",
            "sealed_evaluation",
        }
        if set(self.authorized_future_work) != required_authorized or set(self.prohibited_authority) != required_prohibited:
            raise CandidateDiscoveryProtocolError("C0 authority declarations incomplete")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CandidateDiscoveryProtocolBundleV1":
        allowed = frozenset(item.name for item in fields(cls)) | {"artifact_hash"}
        try:
            reject_unknown_fields(data, allowed, cls.ARTIFACT_TYPE)
        except V6FoundationError as exc:
            raise CandidateDiscoveryProtocolError(str(exc)) from exc
        nested: Mapping[str, type[_CandidateProtocolArtifact]] = {
            "universe_policy": CandidateUniversePolicyV1,
            "budget_policy": CandidateBudgetPolicyV1,
            "metadata_policy": MetadataCandidatePolicyV1,
            "statistical_policy": StatisticalCandidatePolicyV1,
            "gdn_policy": GDNCandidatePolicyV1,
            "arm_result_contract": CandidateArmResultContractV1,
            "integration_policy": CandidateIntegrationPolicyV1,
            "data_access_policy": TASK039C0DataAccessPolicyV1,
            "parallel_branch_plan": TASK039C0ParallelBranchPlanV1,
        }
        kwargs = {item.name: data[item.name] for item in fields(cls)}
        for name, artifact_class in nested.items():
            kwargs[name] = artifact_class.from_dict(kwargs[name])
        kwargs["authorized_future_work"] = tuple(kwargs["authorized_future_work"])
        kwargs["prohibited_authority"] = tuple(kwargs["prohibited_authority"])
        kwargs["creation_metadata"] = CreationMetadataV1.from_dict(kwargs["creation_metadata"])
        result = cls(**kwargs)
        if data.get("artifact_hash") is not None and data["artifact_hash"] != result.artifact_hash:
            raise CandidateDiscoveryProtocolError("artifact_hash does not match bundle")
        return result


def _normalize_identity_inputs(
    source_entries: Sequence[Mapping[str, str]],
    target_entries: Sequence[Mapping[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    sources = sorted(
        (
            {
                "variable_name": str(item["variable_name"]),
                "semantic_role": str(item["semantic_role"]),
                "metadata_record_hash": str(item["metadata_record_hash"]),
            }
            for item in source_entries
        ),
        key=lambda item: item["variable_name"],
    )
    targets = sorted(
        (
            {
                "variable_name": str(item["variable_name"]),
                "semantic_role": "process_sensor",
                "metadata_record_hash": str(item["metadata_record_hash"]),
            }
            for item in target_entries
        ),
        key=lambda item: item["variable_name"],
    )
    return sources, targets


def default_candidate_discovery_config_content_v1(
    *,
    source_entries: Sequence[Mapping[str, str]],
    target_entries: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    """Return the unhashed C0 config from tracked public identity inputs."""

    sources, targets = _normalize_identity_inputs(source_entries, target_entries)
    source_variables = tuple(item["variable_name"] for item in sources)
    source_roles = tuple(item["semantic_role"] for item in sources)
    source_refs = tuple(item["metadata_record_hash"] for item in sources)
    target_variables = tuple(item["variable_name"] for item in targets)
    target_roles = tuple(item["semantic_role"] for item in targets)
    target_refs = tuple(item["metadata_record_hash"] for item in targets)
    source_hash = candidate_identity_list_hash_v1(
        identity_kind="source", process_id="P1", variables=source_variables, roles=source_roles, metadata_refs=source_refs
    )
    target_hash = candidate_identity_list_hash_v1(
        identity_kind="target", process_id="P1", variables=target_variables, roles=target_roles, metadata_refs=target_refs
    )
    pairs = eligible_pair_records_v1(source_variables, target_variables)
    pair_hash = eligible_pair_universe_hash_v1(
        process_id="P1", relation_family=RELATION_FAMILY_ID, pairs=pairs
    )
    return {
        "schema_version": "1.0.0",
        "artifact_type": "task039c0_candidate_discovery_protocol_config",
        "task_id": "TASK-039C0",
        "authoritative_main_commit": AUTHORITATIVE_MAIN_COMMIT,
        "frozen_lineage": {
            "dataset_manifest_id": DATASET_MANIFEST_ID,
            "selected_process_id": "P1",
            "selected_process_name": "Boiler",
            "process_freeze_hash": PROCESS_FREEZE_HASH,
            "br1_protocol_bundle_hash": BR1_PROTOCOL_BUNDLE_HASH,
            "candidate_learning_view_id": CANDIDATE_LEARNING_VIEW_ID,
            "canonical_rule_view_id": CANONICAL_RULE_VIEW_ID,
            "normal_candidate_fit_split_id": NORMAL_CANDIDATE_FIT_SPLIT_ID,
            "normal_relation_calibration_split_id": NORMAL_RELATION_CALIBRATION_SPLIT_ID,
            "normal_guard_split_id": NORMAL_GUARD_SPLIT_ID,
        },
        "common_universe": {
            "relation_family": RELATION_FAMILY_ID,
            "source_identities": sources,
            "target_identities": targets,
            "source_identity_list_hash": source_hash,
            "target_identity_list_hash": target_hash,
            "eligible_pair_universe_hash": pair_hash,
            "eligible_pair_count": len(pairs),
            "source_target_overlap_count": len(set(source_variables) & set(target_variables)),
            "pair_ordering": "source_then_target_lexicographic",
        },
        "candidate_budgets": {
            "primary_k": 20,
            "sensitivity_k": [10, 40],
            "single_ranking_reused": True,
            "padding_prohibited": True,
            "candidate_shortfall_required": True,
        },
        "metadata_policy": {
            "evidence_tiers": [item.value for item in MetadataEvidenceTierV1],
            "feature_values_used": False,
            "official_graph_claim_boundary": "weak_relation_reference_not_causal_truth",
            "cross_method_inputs_prohibited": True,
        },
        "statistical_policy": {
            "allowed_value_files": list(FIT_VALUE_FILES),
            "horizons_seconds": list(STATISTICAL_HORIZONS),
            "statistic": "within_file_Pearson_corr_dx_dy_lag",
            "sign_stability": "finite_same_nonzero_sign_in_train1_and_train2",
            "score": "min(abs(r_train1),abs(r_train2))",
            "arbitrary_minimum_threshold": None,
        },
        "gdn_policy": {
            "upstream_repository": UPSTREAM_GDN_REPOSITORY,
            "upstream_commit": UPSTREAM_GDN_COMMIT,
            "p1d_fidelity_report_hash": P1D_FIDELITY_REPORT_HASH,
            "required_fidelity_class": "upstream_aligned_validated",
            "seeds": list(GDN_SEEDS),
            "allowed_value_files": list(FIT_VALUE_FILES),
            "smoke_backend_allowed": False,
            "attention_role": "supplementary_graph_evidence",
            "post_hoc_xai_primary": False,
        },
        "arm_data_permissions": {
            "META": [],
            "STAT": list(FIT_VALUE_FILES),
            "GDN": list(FIT_VALUE_FILES),
            "allowed_process_ids": ["P1"],
            "prohibited_process_ids": ["P2", "P3", "P4"],
            "train3_train4_test_labels_prohibited": True,
        },
        "br2_anti_leakage": {
            "pair_level_artifacts": list(BR2_PAIR_LEVEL_ARTIFACTS),
            "allowed_use": "lineage_hash_verification_only",
            "pair_ranking_or_selection_use": False,
            "allowed_source_level_fields": ["source_identity", "semantic_role", "eligibility_status"],
            "prohibited_source_level_fields": ["source_step_threshold", "stability_tolerance", "event_count", "event_timestamp"],
        },
        "integration_policy": {
            "operation": "set_union_with_provenance",
            "primary_input": "top20",
            "merged_numerical_score": False,
            "cross_method_union_ranking": False,
            "gdn_included_only_when_passed": True,
        },
        "authority_boundary": {
            "real_hai_feature_access": False,
            "candidate_discovery_executed": False,
            "final_candidate_universe_created": False,
            "task039d_authorized": False,
            "rule_v2_created": False,
            "agent_calls": 0,
            "detector_execution": False,
            "runtime_execution": False,
            "attack_test_outer_sealed_access": False,
        },
    }


def build_default_candidate_discovery_bundle_v1(
    *, config: Mapping[str, Any], created_at: str = "2026-08-10T00:00:00+09:00"
) -> CandidateDiscoveryProtocolBundleV1:
    config_hash = str(config["config_hash"])
    require_sha256(config_hash, "config_hash")
    common = config["common_universe"]
    sources = common["source_identities"]
    targets = common["target_identities"]
    metadata = CreationMetadataV1(
        created_at=created_at,
        created_by="TASK-039C0",
        code_commit=AUTHORITATIVE_MAIN_COMMIT,
        config_hash=config_hash,
    )
    universe = CandidateUniversePolicyV1(
        DATASET_MANIFEST_ID,
        "P1",
        "Boiler",
        PROCESS_FREEZE_HASH,
        BR1_PROTOCOL_BUNDLE_HASH,
        CANDIDATE_LEARNING_VIEW_ID,
        CANONICAL_RULE_VIEW_ID,
        NORMAL_CANDIDATE_FIT_SPLIT_ID,
        NORMAL_RELATION_CALIBRATION_SPLIT_ID,
        NORMAL_GUARD_SPLIT_ID,
        RELATION_FAMILY_ID,
        tuple(item["variable_name"] for item in sources),
        tuple(item["semantic_role"] for item in sources),
        tuple(item["metadata_record_hash"] for item in sources),
        tuple(item["variable_name"] for item in targets),
        tuple(item["semantic_role"] for item in targets),
        tuple(item["metadata_record_hash"] for item in targets),
        str(common["source_identity_list_hash"]),
        str(common["target_identity_list_hash"]),
        str(common["eligible_pair_universe_hash"]),
        int(common["eligible_pair_count"]),
        int(common["source_target_overlap_count"]),
        "lexicographic_variable_name",
        "source_then_target_lexicographic",
        True,
        False,
        False,
        metadata,
    )
    budget = CandidateBudgetPolicyV1(20, (10, 40), True, True, True, True, True, "top20", metadata)
    meta = MetadataCandidatePolicyV1(
        "TASK-039C-META",
        (
            "official_HAI_technical_manual",
            "official_P1_process_physical_graph",
            "reviewed_variable_role_metadata",
            "official_subsystem_equipment_membership",
            "reviewed_manual_semantic_mappings",
        ),
        (TASK039A_REFERENCE_INVENTORY_HASH, TASK039BR0_SOURCE_SUMMARY_HASH, PROCESS_FREEZE_HASH),
        tuple(item.value for item in MetadataEvidenceTierV1),
        "weak_relation_reference_not_causal_truth",
        (
            "evidence_tier",
            "independent_official_reference_count_desc",
            "canonical_source_identity",
            "canonical_target_identity",
        ),
        ("HAI_feature_values", "BR2_pair_results", "statistical_association", "GDN_output", "LLM_semantic_guessing"),
        False,
        False,
        False,
        False,
        metadata,
    )
    stat = StatisticalCandidatePolicyV1(
        "TASK-039C-STAT",
        FIT_VALUE_FILES,
        "P1",
        NORMAL_CANDIDATE_FIT_SPLIT_ID,
        "dx(t)=x(t)-x(t-1)",
        "dy(t)=y(t)-y(t-1)",
        STATISTICAL_HORIZONS,
        "corr(dx(t),dy(t+h))_within_file",
        False,
        "finite_same_nonzero_sign_in_train1_and_train2",
        "min(abs(r_train1),abs(r_train2))",
        "max_stability_strength_then_shortest_horizon",
        "stability_strength(h_stat)",
        "direction_unstable",
        0.0,
        (
            "stable_before_unstable",
            "statistical_candidate_score_desc",
            "selected_horizon_asc",
            "source_lexicographic",
            "target_lexicographic",
        ),
        None,
        False,
        False,
        metadata,
    )
    gdn = GDNCandidatePolicyV1(
        "TASK-039C-GDN",
        UPSTREAM_GDN_REPOSITORY,
        UPSTREAM_GDN_COMMIT,
        P1D_FIDELITY_REPORT_HASH,
        "UpstreamGDNFidelityReceipt",
        "upstream_aligned_validated",
        (
            "pinned_upstream_source_hashes",
            "architecture_identity",
            "graph_construction_semantics",
            "node_embedding_usage",
            "topk_learned_graph_semantics",
            "prediction_loss_training_path",
            "preprocessing",
            "optimizer_configuration",
            "hyperparameter_provenance",
            "no_hidden_project_scientific_modification",
        ),
        False,
        FIT_VALUE_FILES,
        "P1",
        CANDIDATE_LEARNING_VIEW_ID,
        NORMAL_CANDIDATE_FIT_SPLIT_ID,
        True,
        "exact_common_source_target_universe",
        "learned_topk_graph_and_node_embedding_similarity",
        "graph_relatedness_projected_to_semantic_source_target_not_causality",
        GDN_SEEDS,
        True,
        False,
        "selected_seed_count/3",
        "median_upstream_graph_similarity_across_seeds",
        (
            "edge_selection_frequency_desc",
            "median_upstream_graph_similarity_desc",
            "source_lexicographic",
            "target_lexicographic",
        ),
        "supplementary_graph_evidence",
        False,
        False,
        tuple(item.value for item in GDNArmStatusV1),
        False,
        False,
        metadata,
    )
    arm_result = CandidateArmResultContractV1(
        ("META", "STAT", "GDN"),
        True,
        True,
        (10, 20, 40),
        True,
        True,
        True,
        True,
        ("candidate_universe_ref", "origin_arm", "rank", "method_evidence_refs", "candidate_shortfall"),
        ("passed", "candidate_shortfall", "failed"),
        tuple(item.value for item in GDNArmStatusV1),
        False,
        False,
        metadata,
    )
    integration = CandidateIntegrationPolicyV1(
        "TASK-039C-INTEGRATE",
        20,
        ("META", "STAT", "GDN"),
        True,
        ("source_variable", "target_variable"),
        ("origin_arms", "META_rank_evidence", "STAT_rank_evidence", "GDN_rank_evidence", "candidate_universe_ref"),
        False,
        False,
        "set_union_with_provenance",
        "TASK-039D",
        (
            "confirmed_relation_yield_at_20",
            "distinct_confirmed_source_coverage_at_20",
            "distinct_confirmed_target_coverage_at_20",
            "normal_relation_transfer_at_20",
            "candidate_shortfall",
            "cross_arm_overlap",
        ),
        False,
        False,
        metadata,
    )
    access = TASK039C0DataAccessPolicyV1(
        ("META", "STAT", "GDN"),
        ("P1",),
        ("P2", "P3", "P4"),
        (),
        FIT_VALUE_FILES,
        FIT_VALUE_FILES,
        (
            "hai-23.05/hai-train3.csv",
            "hai-23.05/hai-train4.csv",
            "hai-23.05/hai-test*.csv",
            "hai-23.05/label-test*.csv",
            "hai-23.05/summary_label*.txt",
        ),
        BR2_PAIR_LEVEL_ARTIFACTS,
        "lineage_hash_verification_only",
        ("source_identity", "semantic_role", "eligibility_status"),
        ("source_step_threshold", "stability_tolerance", "event_count", "event_timestamp"),
        True,
        True,
        False,
        False,
        metadata,
    )
    branch_plan = TASK039C0ParallelBranchPlanV1(
        "task-039c0-candidate-protocol",
        (
            "task-039c-meta",
            "task-039c-stat",
            "task-039c-gdn",
            "task-039c-review",
            "task-039c-integration",
        ),
        "exact_git_commit_containing_this_protocol_bundle",
        True,
        True,
        True,
        True,
        False,
        metadata,
    )
    return CandidateDiscoveryProtocolBundleV1(
        "TASK-039C0",
        "passed_task039c0_candidate_discovery_protocol_freeze",
        AUTHORITATIVE_MAIN_COMMIT,
        "P1",
        "Boiler",
        universe,
        budget,
        meta,
        stat,
        gdn,
        arm_result,
        integration,
        access,
        branch_plan,
        ("P1_candidate_discovery", "candidate_ranking", "graph_evidence", "candidate_set_integration"),
        (
            "TASK-039D_relation_calibration",
            "Rule_v2",
            "rule_construction",
            "Agent_calls",
            "detector_execution",
            "runtime_execution",
            "attack_or_test_access",
            "outer_validation",
            "sealed_evaluation",
        ),
        False,
        False,
        False,
        False,
        False,
        metadata,
    )


__all__ = [
    "AUTHORITATIVE_MAIN_COMMIT",
    "ArmCandidateV1",
    "BR1_PROTOCOL_BUNDLE_HASH",
    "CandidateArmResultContractV1",
    "CandidateArmV1",
    "CandidateBudgetPolicyV1",
    "CandidateBudgetViewsV1",
    "CandidateDiscoveryProtocolBundleV1",
    "CandidateDiscoveryProtocolError",
    "CandidateIntegrationPolicyV1",
    "CandidateUniversePolicyV1",
    "GDNCandidatePolicyV1",
    "GDNArmStatusV1",
    "GDNRankInputV1",
    "IntegratedCandidateV1",
    "MetadataCandidatePolicyV1",
    "MetadataEvidenceTierV1",
    "MetadataRankInputV1",
    "StatisticalCandidatePolicyV1",
    "StatisticalCandidateStatusV1",
    "StatisticalHorizonSelectionV1",
    "StatisticalRankInputV1",
    "TASK039C0DataAccessPolicyV1",
    "TASK039C0ParallelBranchPlanV1",
    "assert_candidate_in_universe_v1",
    "authorize_br2_pair_artifact_use_v1",
    "authorize_candidate_arm_value_access_v1",
    "build_default_candidate_discovery_bundle_v1",
    "candidate_identity_list_hash_v1",
    "default_candidate_discovery_config_content_v1",
    "derive_candidate_budget_views_v1",
    "eligible_pair_records_v1",
    "eligible_pair_universe_hash_v1",
    "integrate_candidate_union_v1",
    "rank_gdn_candidates_v1",
    "rank_metadata_candidates_v1",
    "rank_statistical_candidates_v1",
    "select_statistical_horizon_v1",
]
