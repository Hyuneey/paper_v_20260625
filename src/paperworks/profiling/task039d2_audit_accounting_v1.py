"""Independent accounting checks for a future TASK-039D2 result audit.

The functions in this module consume already-parsed immutable values.  They do
not open files, replay the production confirmation engine, or grant this
preparation branch access to train3 or a private D1 ledger.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from paperworks.v6.common import (
    V6_FOUNDATION_SCHEMA_VERSION,
    require_finite,
    require_sha256,
    stable_hash_v1,
)
from paperworks.v6.relation_profiling_protocol_v1 import (
    FROZEN_SOURCES,
    FROZEN_TARGETS,
    HORIZONS,
)

from .task039d2_audit_reference_v1 import (
    CONFIRMATION_POLICY_HASH,
    D2DirectionalInputSetV1,
    EXPECTED_D2_DIRECTIONAL_INPUT_COUNT,
    EXPECTED_D2_SUPPORTED_PAIR_COUNT,
    METHOD_COMPARISON_POLICY_HASH,
    SyntheticDirectionalAuditReplayV1,
    TASK039D2AuditPreparationError,
    reconstruct_confirmation_gate_reference_v1,
)


ARMS = ("META", "STAT", "GDN")
CONFIRMATION_STATUSES = ("calibration_confirmed", "calibration_conflict")
PRIVATE_CONFIRMATION_LEDGER_ARTIFACT_TYPE = (
    "task039d2_private_confirmation_ledger_v1"
)
PRIVATE_CONFIRMATION_RECORD_ARTIFACT_TYPE = (
    "task039d2_private_confirmation_record_v1"
)


def _require_nonnegative_integer(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TASK039D2AuditPreparationError(
            f"{field_name} must be a non-negative integer"
        )


def _require_pair(source: str, target: str) -> tuple[str, str]:
    if source not in FROZEN_SOURCES or target not in FROZEN_TARGETS:
        raise TASK039D2AuditPreparationError(
            "candidate pair is outside the frozen P1 identities"
        )
    return source, target


def _without_hash(document: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in document.items() if key != "artifact_hash"}


@dataclass(frozen=True)
class AuditedDirectionOutcomeV1:
    """Parsed D2 direction outcome with no method-arm provenance fields."""

    input_binding_hash: str
    d1_source_parameter_record_hash: str
    d1_target_parameter_record_hash: str
    d1_directional_record_hash: str
    source: str
    source_step_direction: str
    target: str
    target_response_direction: str
    selected_horizon_seconds: int
    usable_response_count: int
    right_censored_count: int
    source_direction_unchanged: bool
    selected_consistency: float
    opposite_consistency: float
    robust_effect_ratio: float
    status: str
    record_hash: str

    def __post_init__(self) -> None:
        for field_name in (
            "input_binding_hash",
            "d1_source_parameter_record_hash",
            "d1_target_parameter_record_hash",
            "d1_directional_record_hash",
            "record_hash",
        ):
            require_sha256(getattr(self, field_name), field_name)
        _require_pair(self.source, self.target)
        if self.source_step_direction not in {"step_up", "step_down"}:
            raise TASK039D2AuditPreparationError("invalid frozen source direction")
        if self.target_response_direction not in {"increase", "decrease"}:
            raise TASK039D2AuditPreparationError("invalid frozen target direction")
        if self.selected_horizon_seconds not in HORIZONS:
            raise TASK039D2AuditPreparationError("invalid frozen selected horizon")
        _require_nonnegative_integer(
            self.usable_response_count, "usable_response_count"
        )
        _require_nonnegative_integer(
            self.right_censored_count, "right_censored_count"
        )
        selected = require_finite(self.selected_consistency, "selected_consistency")
        opposite = require_finite(self.opposite_consistency, "opposite_consistency")
        effect = require_finite(self.robust_effect_ratio, "robust_effect_ratio")
        if not 0.0 <= selected <= 1.0 or not 0.0 <= opposite <= 1.0:
            raise TASK039D2AuditPreparationError("consistency must be a probability")
        if effect < 0.0:
            raise TASK039D2AuditPreparationError(
                "robust effect ratio must be non-negative"
            )
        if self.status not in CONFIRMATION_STATUSES:
            raise TASK039D2AuditPreparationError("unknown D2 confirmation status")
        if not isinstance(self.source_direction_unchanged, bool):
            raise TASK039D2AuditPreparationError(
                "source_direction_unchanged must be boolean"
            )

    @property
    def pair(self) -> tuple[str, str]:
        return self.source, self.target

    @property
    def identity(self) -> tuple[str, str, str]:
        return self.source, self.target, self.source_step_direction


@dataclass(frozen=True)
class FrozenD2OutcomeSetV1:
    """Verified direction outcomes frozen before method provenance is joined."""

    directions: tuple[AuditedDirectionOutcomeV1, ...]
    private_ledger_hash: str
    input_set_binding_hash: str
    outcomes_frozen: bool = True
    provenance_joined: bool = False

    def __post_init__(self) -> None:
        require_sha256(self.private_ledger_hash, "private_ledger_hash")
        require_sha256(self.input_set_binding_hash, "input_set_binding_hash")
        if len(self.directions) != EXPECTED_D2_DIRECTIONAL_INPUT_COUNT:
            raise TASK039D2AuditPreparationError(
                "verified D2 outcome set must contain exactly 45 directions"
            )
        if len({item.identity for item in self.directions}) != len(self.directions):
            raise TASK039D2AuditPreparationError("duplicate verified D2 direction")
        if len({item.pair for item in self.directions}) != EXPECTED_D2_SUPPORTED_PAIR_COUNT:
            raise TASK039D2AuditPreparationError(
                "verified D2 outcomes must cover exactly 25 supported pairs"
            )
        if self.outcomes_frozen is not True or self.provenance_joined is not False:
            raise TASK039D2AuditPreparationError(
                "D2 outcomes must freeze before method provenance"
            )


@dataclass(frozen=True)
class PairConfirmationPartitionV1:
    """Pair status derived only after every direction status has frozen."""

    confirmed_pairs: frozenset[tuple[str, str]]
    conflict_pairs: frozenset[tuple[str, str]]

    def __post_init__(self) -> None:
        if self.confirmed_pairs & self.conflict_pairs:
            raise TASK039D2AuditPreparationError(
                "confirmed and conflict pair partitions must be disjoint"
            )
        if len(self.confirmed_pairs | self.conflict_pairs) != (
            EXPECTED_D2_SUPPORTED_PAIR_COUNT
        ):
            raise TASK039D2AuditPreparationError(
                "pair partition must contain exactly 25 supported pairs"
            )
        for source, target in self.confirmed_pairs | self.conflict_pairs:
            _require_pair(source, target)


@dataclass(frozen=True)
class DirectionConfirmationPartitionV1:
    """Exact confirmed/conflict partition over the 45 frozen directions."""

    confirmed_directions: frozenset[tuple[str, str, str]]
    conflict_directions: frozenset[tuple[str, str, str]]

    def __post_init__(self) -> None:
        if self.confirmed_directions & self.conflict_directions:
            raise TASK039D2AuditPreparationError(
                "confirmed and conflict direction partitions must be disjoint"
            )
        if len(self.confirmed_directions | self.conflict_directions) != (
            EXPECTED_D2_DIRECTIONAL_INPUT_COUNT
        ):
            raise TASK039D2AuditPreparationError(
                "direction partition must contain exactly 45 D2 inputs"
            )


@dataclass(frozen=True)
class ArmTop20ProvenanceV1:
    """Post-outcome arm membership; no score, rank, tier, or horizon is accepted."""

    arm: str
    pairs: frozenset[tuple[str, str]]

    def __post_init__(self) -> None:
        if self.arm not in ARMS:
            raise TASK039D2AuditPreparationError("unknown frozen discovery arm")
        if len(self.pairs) != 20:
            raise TASK039D2AuditPreparationError(
                "each frozen arm provenance set must contain exactly top-20 pairs"
            )
        for source, target in self.pairs:
            _require_pair(source, target)


@dataclass(frozen=True)
class ArmMetricReplayV1:
    arm: str
    fit_supported_pair_count: int
    pair_fit_support_yield: float
    confirmed_pair_count: int
    confirmed_relation_yield: float
    pair_transfer: float
    fit_supported_direction_count: int
    confirmed_direction_count: int
    directional_transfer: float
    confirmed_source_count: int
    confirmed_source_rate: float
    confirmed_target_count: int
    confirmed_target_rate: float

    def __post_init__(self) -> None:
        if self.arm not in ARMS:
            raise TASK039D2AuditPreparationError("unknown arm metric")
        for field_name in (
            "fit_supported_pair_count",
            "confirmed_pair_count",
            "fit_supported_direction_count",
            "confirmed_direction_count",
            "confirmed_source_count",
            "confirmed_target_count",
        ):
            _require_nonnegative_integer(getattr(self, field_name), field_name)
        for field_name in (
            "pair_fit_support_yield",
            "confirmed_relation_yield",
            "pair_transfer",
            "directional_transfer",
            "confirmed_source_rate",
            "confirmed_target_rate",
        ):
            value = require_finite(getattr(self, field_name), field_name)
            if not 0.0 <= value <= 1.0:
                raise TASK039D2AuditPreparationError(
                    f"{field_name} must be a probability"
                )


@dataclass(frozen=True)
class CrossArmOverlapV1:
    unique_meta: frozenset[tuple[str, str]]
    unique_stat: frozenset[tuple[str, str]]
    unique_gdn: frozenset[tuple[str, str]]
    shared_two_arms: frozenset[tuple[str, str]]
    shared_all_applicable_arms: frozenset[tuple[str, str]]

    def __post_init__(self) -> None:
        categories = (
            self.unique_meta,
            self.unique_stat,
            self.unique_gdn,
            self.shared_two_arms,
            self.shared_all_applicable_arms,
        )
        for index, left in enumerate(categories):
            for right in categories[index + 1 :]:
                if left & right:
                    raise TASK039D2AuditPreparationError(
                        "cross-arm overlap categories must be disjoint"
                    )


@dataclass(frozen=True)
class PostFreezeArmAuditV1:
    outcomes: FrozenD2OutcomeSetV1
    direction_partition: DirectionConfirmationPartitionV1
    pair_partition: PairConfirmationPartitionV1
    arm_metrics: tuple[ArmMetricReplayV1, ...]
    overlap: CrossArmOverlapV1
    provenance_joined_after_outcomes_froze: bool = True

    def __post_init__(self) -> None:
        if self.provenance_joined_after_outcomes_froze is not True:
            raise TASK039D2AuditPreparationError(
                "method provenance may join only after D2 outcomes freeze"
            )
        if {item.arm for item in self.arm_metrics} != set(ARMS):
            raise TASK039D2AuditPreparationError("all three arm metrics are required")


@dataclass(frozen=True)
class CommitABSeparationV1:
    """Future audit receipt for immutable implementation A and result-only B."""

    commit_a: str
    commit_b: str
    commit_b_first_parent: str
    commit_a_scientific_tree_hash: str
    commit_b_scientific_tree_hash: str
    commit_b_changed_paths: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "commit_a",
            "commit_b",
            "commit_b_first_parent",
        ):
            if not re.fullmatch(r"[0-9a-f]{40}", getattr(self, field_name)):
                raise TASK039D2AuditPreparationError(
                    f"{field_name} must be a lowercase Git SHA-1"
                )
        for field_name in (
            "commit_a_scientific_tree_hash",
            "commit_b_scientific_tree_hash",
        ):
            require_sha256(getattr(self, field_name), field_name)
        if self.commit_a == self.commit_b:
            raise TASK039D2AuditPreparationError("Commit A and B must be distinct")
        if self.commit_b_first_parent != self.commit_a:
            raise TASK039D2AuditPreparationError(
                "Commit B must descend directly from frozen Commit A"
            )
        if self.commit_a_scientific_tree_hash != self.commit_b_scientific_tree_hash:
            raise TASK039D2AuditPreparationError(
                "Commit B must not modify scientific implementation"
            )
        allowed_prefix = "docs/task_reports/TASK-039D2"
        if not self.commit_b_changed_paths or any(
            not path.replace("\\", "/").startswith(allowed_prefix)
            for path in self.commit_b_changed_paths
        ):
            raise TASK039D2AuditPreparationError(
                "Commit B may add only TASK-039D2 result/report artifacts"
            )


def verify_private_confirmation_ledger_v1(
    document: Mapping[str, Any],
    *,
    input_set: D2DirectionalInputSetV1,
) -> FrozenD2OutcomeSetV1:
    """Verify a supplied in-memory ledger and every exact D1 hash binding."""

    allowed_top_level = {
        "schema_version",
        "artifact_type",
        "confirmation_policy_hash",
        "input_set_binding_hash",
        "records",
        "real_hai_values_embedded",
        "d1_private_records_embedded",
        "method_provenance_embedded",
        "artifact_hash",
    }
    if set(document) != allowed_top_level:
        raise TASK039D2AuditPreparationError(
            "private confirmation ledger fields are not closed"
        )
    if document["schema_version"] != V6_FOUNDATION_SCHEMA_VERSION:
        raise TASK039D2AuditPreparationError("confirmation ledger schema mismatch")
    if document["artifact_type"] != PRIVATE_CONFIRMATION_LEDGER_ARTIFACT_TYPE:
        raise TASK039D2AuditPreparationError("confirmation ledger type mismatch")
    if document["confirmation_policy_hash"] != CONFIRMATION_POLICY_HASH:
        raise TASK039D2AuditPreparationError("confirmation policy hash mismatch")
    if document["input_set_binding_hash"] != input_set.binding_hash:
        raise TASK039D2AuditPreparationError("D2 input set binding mismatch")
    if (
        document["real_hai_values_embedded"] is not False
        or document["d1_private_records_embedded"] is not False
        or document["method_provenance_embedded"] is not False
    ):
        raise TASK039D2AuditPreparationError(
            "confirmation ledger violates data or outcome-first boundary"
        )
    ledger_hash = require_sha256(document["artifact_hash"], "artifact_hash")
    if stable_hash_v1(_without_hash(document)) != ledger_hash:
        raise TASK039D2AuditPreparationError(
            "private confirmation ledger self-hash mismatch"
        )
    raw_records = document["records"]
    if not isinstance(raw_records, list) or len(raw_records) != (
        EXPECTED_D2_DIRECTIONAL_INPUT_COUNT
    ):
        raise TASK039D2AuditPreparationError(
            "private confirmation ledger must contain exactly 45 records"
        )
    expected = {
        item.identity: item for item in input_set.directional_inputs
    }
    outcomes: list[AuditedDirectionOutcomeV1] = []
    seen_record_hashes: set[str] = set()
    allowed_record_fields = {
        "schema_version",
        "artifact_type",
        "input_binding_hash",
        "d1_source_parameter_record_hash",
        "d1_target_parameter_record_hash",
        "d1_directional_record_hash",
        "source",
        "source_step_direction",
        "target",
        "target_response_direction",
        "selected_horizon_seconds",
        "usable_response_count",
        "right_censored_count",
        "source_direction_unchanged",
        "selected_consistency",
        "opposite_consistency",
        "robust_effect_ratio",
        "fit_parameters_reused_without_retuning",
        "alternative_horizon_search_performed",
        "opposite_direction_search_performed",
        "lower_ranked_fallback_used",
        "status",
        "artifact_hash",
    }
    for raw_record in raw_records:
        if not isinstance(raw_record, Mapping) or set(raw_record) != allowed_record_fields:
            raise TASK039D2AuditPreparationError(
                "private confirmation record fields are not closed"
            )
        if raw_record["schema_version"] != V6_FOUNDATION_SCHEMA_VERSION:
            raise TASK039D2AuditPreparationError("confirmation record schema mismatch")
        if raw_record["artifact_type"] != PRIVATE_CONFIRMATION_RECORD_ARTIFACT_TYPE:
            raise TASK039D2AuditPreparationError("confirmation record type mismatch")
        record_hash = require_sha256(raw_record["artifact_hash"], "artifact_hash")
        if record_hash in seen_record_hashes:
            raise TASK039D2AuditPreparationError("duplicate confirmation record hash")
        if stable_hash_v1(_without_hash(raw_record)) != record_hash:
            raise TASK039D2AuditPreparationError(
                "private confirmation record self-hash mismatch"
            )
        seen_record_hashes.add(record_hash)
        identity = (
            raw_record["source"],
            raw_record["target"],
            raw_record["source_step_direction"],
        )
        relation = expected.get(identity)
        if relation is None:
            raise TASK039D2AuditPreparationError(
                "confirmation record is not an exact D1 directional input"
            )
        exact_bindings = {
            "input_binding_hash": relation.binding_hash,
            "d1_source_parameter_record_hash": (
                relation.d1_source_parameter_record_hash
            ),
            "d1_target_parameter_record_hash": (
                relation.d1_target_parameter_record_hash
            ),
            "d1_directional_record_hash": relation.d1_directional_record_hash,
            "target_response_direction": relation.target_response_direction,
            "selected_horizon_seconds": relation.selected_horizon_seconds,
        }
        if any(raw_record[key] != value for key, value in exact_bindings.items()):
            raise TASK039D2AuditPreparationError(
                "confirmation record changed an immutable D1 binding"
            )
        if (
            raw_record["fit_parameters_reused_without_retuning"] is not True
            or raw_record["alternative_horizon_search_performed"] is not False
            or raw_record["opposite_direction_search_performed"] is not False
            or raw_record["lower_ranked_fallback_used"] is not False
        ):
            raise TASK039D2AuditPreparationError(
                "confirmation record reports retuning or search"
            )
        expected_confirmed = reconstruct_confirmation_gate_reference_v1(
            usable_response_count=raw_record["usable_response_count"],
            source_direction_unchanged=raw_record["source_direction_unchanged"],
            selected_consistency=raw_record["selected_consistency"],
            opposite_consistency=raw_record["opposite_consistency"],
            robust_effect_ratio=raw_record["robust_effect_ratio"],
            fit_parameters_reused_without_retuning=(
                raw_record["fit_parameters_reused_without_retuning"]
            ),
        )
        expected_status = (
            "calibration_confirmed"
            if expected_confirmed
            else "calibration_conflict"
        )
        if raw_record["status"] != expected_status:
            raise TASK039D2AuditPreparationError(
                "confirmation status does not match the independent frozen gate"
            )
        outcomes.append(
            AuditedDirectionOutcomeV1(
                input_binding_hash=raw_record["input_binding_hash"],
                d1_source_parameter_record_hash=(
                    raw_record["d1_source_parameter_record_hash"]
                ),
                d1_target_parameter_record_hash=(
                    raw_record["d1_target_parameter_record_hash"]
                ),
                d1_directional_record_hash=raw_record["d1_directional_record_hash"],
                source=raw_record["source"],
                source_step_direction=raw_record["source_step_direction"],
                target=raw_record["target"],
                target_response_direction=raw_record["target_response_direction"],
                selected_horizon_seconds=raw_record["selected_horizon_seconds"],
                usable_response_count=raw_record["usable_response_count"],
                right_censored_count=raw_record["right_censored_count"],
                source_direction_unchanged=raw_record[
                    "source_direction_unchanged"
                ],
                selected_consistency=raw_record["selected_consistency"],
                opposite_consistency=raw_record["opposite_consistency"],
                robust_effect_ratio=raw_record["robust_effect_ratio"],
                status=raw_record["status"],
                record_hash=record_hash,
            )
        )
    if {item.identity for item in outcomes} != set(expected):
        raise TASK039D2AuditPreparationError(
            "confirmation ledger is not an exact partition of D1 inputs"
        )
    return FrozenD2OutcomeSetV1(
        directions=tuple(outcomes),
        private_ledger_hash=ledger_hash,
        input_set_binding_hash=input_set.binding_hash,
    )


def derive_pair_confirmation_partition_v1(
    outcomes: FrozenD2OutcomeSetV1,
) -> PairConfirmationPartitionV1:
    """A pair confirms iff at least one of its frozen directions confirms."""

    grouped: dict[tuple[str, str], list[AuditedDirectionOutcomeV1]] = {}
    for outcome in outcomes.directions:
        grouped.setdefault(outcome.pair, []).append(outcome)
    confirmed = frozenset(
        pair
        for pair, directions in grouped.items()
        if any(item.status == "calibration_confirmed" for item in directions)
    )
    conflicts = frozenset(set(grouped) - set(confirmed))
    return PairConfirmationPartitionV1(confirmed, conflicts)


def derive_direction_confirmation_partition_v1(
    outcomes: FrozenD2OutcomeSetV1,
) -> DirectionConfirmationPartitionV1:
    confirmed = frozenset(
        item.identity
        for item in outcomes.directions
        if item.status == "calibration_confirmed"
    )
    conflict = frozenset(
        item.identity
        for item in outcomes.directions
        if item.status == "calibration_conflict"
    )
    return DirectionConfirmationPartitionV1(confirmed, conflict)


def verify_synthetic_replay_matches_outcomes_v1(
    *,
    replayed: Sequence[SyntheticDirectionalAuditReplayV1],
    outcomes: FrozenD2OutcomeSetV1,
) -> None:
    """Require an exact field-for-field match to the independent replay."""

    replay_items = tuple(replayed)
    if len(replay_items) != EXPECTED_D2_DIRECTIONAL_INPUT_COUNT:
        raise TASK039D2AuditPreparationError(
            "independent replay must contain exactly 45 directions"
        )
    by_identity = {item.identity: item for item in outcomes.directions}
    replay_identities = {
        (item.source, item.target, item.source_step_direction)
        for item in replay_items
    }
    if len(replay_identities) != len(replay_items) or replay_identities != set(
        by_identity
    ):
        raise TASK039D2AuditPreparationError(
            "independent replay identities do not match the frozen outcomes"
        )
    for replay in replay_items:
        identity = (replay.source, replay.target, replay.source_step_direction)
        outcome = by_identity[identity]
        expected = {
            "input_binding_hash": replay.input_binding_hash,
            "d1_source_parameter_record_hash": (
                replay.d1_source_parameter_record_hash
            ),
            "d1_target_parameter_record_hash": (
                replay.d1_target_parameter_record_hash
            ),
            "d1_directional_record_hash": replay.d1_directional_record_hash,
            "target_response_direction": replay.target_response_direction,
            "selected_horizon_seconds": replay.selected_horizon_seconds,
            "usable_response_count": replay.usable_response_count,
            "right_censored_count": replay.right_censored_count,
            "source_direction_unchanged": True,
            "selected_consistency": replay.selected_consistency,
            "opposite_consistency": replay.opposite_consistency,
            "robust_effect_ratio": replay.robust_effect_ratio,
            "status": replay.status,
        }
        if any(getattr(outcome, key) != value for key, value in expected.items()):
            raise TASK039D2AuditPreparationError(
                "completed D2 outcome does not match independent synthetic replay"
            )


def reconstruct_arm_metrics_v1(
    *,
    outcomes: FrozenD2OutcomeSetV1,
    arm_provenance: Sequence[ArmTop20ProvenanceV1],
) -> PostFreezeArmAuditV1:
    """Join arm membership only after outcomes freeze and rebuild D0 metrics."""

    if outcomes.outcomes_frozen is not True or outcomes.provenance_joined is not False:
        raise TASK039D2AuditPreparationError(
            "outcomes must freeze before arm provenance is supplied"
        )
    provenance = tuple(arm_provenance)
    if len(provenance) != len(ARMS) or {item.arm for item in provenance} != set(ARMS):
        raise TASK039D2AuditPreparationError(
            "exactly one top-20 provenance set per arm is required"
        )
    partition = derive_pair_confirmation_partition_v1(outcomes)
    supported_pairs = {item.pair for item in outcomes.directions}
    directions_by_pair: dict[tuple[str, str], list[AuditedDirectionOutcomeV1]] = {}
    for outcome in outcomes.directions:
        directions_by_pair.setdefault(outcome.pair, []).append(outcome)
    confirmed_pair_sets: dict[str, frozenset[tuple[str, str]]] = {}
    metrics: list[ArmMetricReplayV1] = []
    for arm_set in provenance:
        fit_pairs = set(arm_set.pairs) & supported_pairs
        confirmed_pairs = fit_pairs & set(partition.confirmed_pairs)
        fit_directions = [
            direction
            for pair in fit_pairs
            for direction in directions_by_pair[pair]
        ]
        confirmed_directions = [
            item
            for item in fit_directions
            if item.status == "calibration_confirmed"
        ]
        sources = {source for source, _ in confirmed_pairs}
        targets = {target for _, target in confirmed_pairs}
        confirmed_pair_sets[arm_set.arm] = frozenset(confirmed_pairs)
        metrics.append(
            ArmMetricReplayV1(
                arm=arm_set.arm,
                fit_supported_pair_count=len(fit_pairs),
                pair_fit_support_yield=len(fit_pairs) / 20.0,
                confirmed_pair_count=len(confirmed_pairs),
                confirmed_relation_yield=len(confirmed_pairs) / 20.0,
                pair_transfer=(
                    len(confirmed_pairs) / len(fit_pairs) if fit_pairs else 0.0
                ),
                fit_supported_direction_count=len(fit_directions),
                confirmed_direction_count=len(confirmed_directions),
                directional_transfer=(
                    len(confirmed_directions) / len(fit_directions)
                    if fit_directions
                    else 0.0
                ),
                confirmed_source_count=len(sources),
                confirmed_source_rate=len(sources) / 12.0,
                confirmed_target_count=len(targets),
                confirmed_target_rate=len(targets) / 12.0,
            )
        )
    membership: dict[tuple[str, str], frozenset[str]] = {}
    for arm, pairs in confirmed_pair_sets.items():
        for pair in pairs:
            membership[pair] = membership.get(pair, frozenset()) | {arm}
    overlap = CrossArmOverlapV1(
        unique_meta=frozenset(pair for pair, arms in membership.items() if arms == {"META"}),
        unique_stat=frozenset(pair for pair, arms in membership.items() if arms == {"STAT"}),
        unique_gdn=frozenset(pair for pair, arms in membership.items() if arms == {"GDN"}),
        shared_two_arms=frozenset(pair for pair, arms in membership.items() if len(arms) == 2),
        shared_all_applicable_arms=frozenset(
            pair for pair, arms in membership.items() if arms == set(ARMS)
        ),
    )
    return PostFreezeArmAuditV1(
        outcomes=outcomes,
        direction_partition=derive_direction_confirmation_partition_v1(outcomes),
        pair_partition=partition,
        arm_metrics=tuple(sorted(metrics, key=lambda item: ARMS.index(item.arm))),
        overlap=overlap,
    )


def assert_audit_preparation_data_boundary_v1(
    *,
    real_hai_access: bool,
    train3_access: bool,
    d1_private_ledger_access: bool,
    d2_authorization_supplied: object | None = None,
) -> None:
    """Fail closed even when a real D2 authorization object is supplied."""

    if d2_authorization_supplied is not None:
        raise TASK039D2AuditPreparationError(
            "D2 authorization never grants audit-preparation real execution"
        )
    if real_hai_access or train3_access or d1_private_ledger_access:
        raise TASK039D2AuditPreparationError(
            "TASK-039D2-AUDIT-PREP is synthetic-only"
        )


def audit_completed_d2_from_files_v1(*_args: object, **_kwargs: object) -> None:
    """Permanent no-I/O guard for this preparation branch."""

    raise TASK039D2AuditPreparationError(
        "real D2 auditing is not authorized on task-039d2-audit-prep"
    )


__all__ = [
    "ARMS",
    "ArmMetricReplayV1",
    "ArmTop20ProvenanceV1",
    "AuditedDirectionOutcomeV1",
    "CommitABSeparationV1",
    "CrossArmOverlapV1",
    "DirectionConfirmationPartitionV1",
    "FrozenD2OutcomeSetV1",
    "METHOD_COMPARISON_POLICY_HASH",
    "PRIVATE_CONFIRMATION_LEDGER_ARTIFACT_TYPE",
    "PRIVATE_CONFIRMATION_RECORD_ARTIFACT_TYPE",
    "PairConfirmationPartitionV1",
    "PostFreezeArmAuditV1",
    "assert_audit_preparation_data_boundary_v1",
    "audit_completed_d2_from_files_v1",
    "derive_pair_confirmation_partition_v1",
    "derive_direction_confirmation_partition_v1",
    "verify_synthetic_replay_matches_outcomes_v1",
    "reconstruct_arm_metrics_v1",
    "verify_private_confirmation_ledger_v1",
]
