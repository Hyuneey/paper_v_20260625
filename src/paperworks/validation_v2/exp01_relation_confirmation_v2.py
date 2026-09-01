"""Arm-blind train3 confirmation adapter for EXP-01.

The adapter deliberately exposes only the canonical candidate union to the
scientific relation evaluator.  Arm provenance is joined only after the
decision partition has been frozen and hashed.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import statistics
from typing import Any, Callable, Mapping, Sequence

from paperworks.validation_v2.exp01_scientific_v1 import (
    CandidateUnionAuthorityV1,
    ConfirmationReceiptV1,
    ProfilingSubmissionV1,
    build_confirmation_receipt_v1,
    build_profiling_submission_v1,
)
from paperworks.v6.common import require_sha256, stable_hash_v1
from paperworks.profiling.task039d1_execution_optimization_v1 import (
    classify_all_source_isolation_indexed_v1,
    extract_sustained_step_events_linear_v1,
)
from paperworks.v6.relation_profiling_protocol_v1 import (
    FIT_FILES,
    FROZEN_SOURCES,
    FROZEN_TARGETS,
    HORIZONS,
    derive_multi_file_source_parameters_v1,
    derive_multi_file_target_scale_v1,
    rank_direction_horizon_v1,
    selected_fit_gate_v1,
    train3_confirmation_gate_v1,
)


class Exp01ConfirmationAdapterError(RuntimeError):
    pass


@dataclass(frozen=True)
class ArmBlindConfirmationOutcomeV2:
    pair_decisions: tuple[tuple[str, str, bool], ...]
    private_decision_ledger_hash: str
    train3_read_receipt_hash: str
    train3_open_count: int = 1
    labels_accessed: bool = False
    test_accessed: bool = False

    def __post_init__(self) -> None:
        require_sha256(self.private_decision_ledger_hash, "private_decision_ledger_hash")
        require_sha256(self.train3_read_receipt_hash, "train3_read_receipt_hash")
        if type(self.labels_accessed) is not bool or type(self.test_accessed) is not bool:
            raise Exp01ConfirmationAdapterError("strict access counters are required")
        if self.labels_accessed or self.test_accessed:
            raise Exp01ConfirmationAdapterError("train3 confirmation cannot access labels or test data")
        if type(self.train3_open_count) is not int or self.train3_open_count != 1:
            raise Exp01ConfirmationAdapterError("train3 must be opened exactly once")


ConfirmationEvaluatorV2 = Callable[[tuple[tuple[str, str], ...]], ArmBlindConfirmationOutcomeV2]


@dataclass(frozen=True)
class ArmBlindRelationExecutionV2:
    outcome: ArmBlindConfirmationOutcomeV2
    private_ledger: Mapping[str, object]


def _response(values: Sequence[float], *, event_index: int, horizon: int) -> float | None:
    if horizon not in HORIZONS or event_index < 5 or event_index + horizon + 3 > len(values):
        return None
    baseline = float(statistics.median(values[event_index - 5:event_index]))
    response = float(statistics.median(values[event_index + horizon:event_index + horizon + 3])) - baseline
    if not math.isfinite(response):
        raise Exp01ConfirmationAdapterError("non-finite relation response")
    return response


def _direction_statistics_v2(
    *, target_by_file: Mapping[str, Sequence[float]], classified_by_file: Mapping[str, Any],
    source_direction: str, target_noise_scale: float, horizon: int, target_direction: str,
) -> dict[str, object]:
    per_file: dict[str, dict[str, object]] = {}
    pooled: list[float] = []
    for file_name in FIT_FILES:
        responses = [
            value for event, isolated in classified_by_file[file_name]
            if isolated and event.direction == source_direction
            for value in [_response(target_by_file[file_name], event_index=event.event_index, horizon=horizon)]
            if value is not None
        ]
        increase = sum(value > target_noise_scale for value in responses)
        decrease = sum(value < -target_noise_scale for value in responses)
        selected = increase if target_direction == "increase" else decrease
        opposite = decrease if target_direction == "increase" else increase
        per_file[file_name] = {
            "usable": len(responses),
            "selected_matches": selected,
            "opposite_matches": opposite,
            "selected_consistency": selected / len(responses) if responses else 0.0,
            "opposite_consistency": opposite / len(responses) if responses else 0.0,
        }
        pooled.extend(responses)
    selected_total = sum(int(per_file[name]["selected_matches"]) for name in FIT_FILES)
    median = float(statistics.median(pooled)) if pooled else None
    return {
        "target_direction": target_direction,
        "horizon_seconds": horizon,
        "pooled_directional_consistency": selected_total / len(pooled) if pooled else 0.0,
        "pooled_robust_effect_ratio": abs(median) / target_noise_scale if median is not None else 0.0,
        "total_usable_responses": len(pooled),
        "train1_usable_responses": int(per_file[FIT_FILES[0]]["usable"]),
        "train2_usable_responses": int(per_file[FIT_FILES[1]]["usable"]),
        "train1_selected_consistency": float(per_file[FIT_FILES[0]]["selected_consistency"]),
        "train1_opposite_consistency": float(per_file[FIT_FILES[0]]["opposite_consistency"]),
        "train2_selected_consistency": float(per_file[FIT_FILES[1]]["selected_consistency"]),
        "train2_opposite_consistency": float(per_file[FIT_FILES[1]]["opposite_consistency"]),
        "pooled_median_response": median,
    }


def fit_and_confirm_arbitrary_union_v2(
    *,
    candidate_pairs: tuple[tuple[str, str], ...],
    train1_matrix: Any,
    train2_matrix: Any,
    train3_matrix: Any,
    feature_order: Sequence[str],
    train1_read_receipt_hash: str,
    train2_read_receipt_hash: str,
    train3_read_receipt_hash: str,
) -> ArmBlindRelationExecutionV2:
    """Apply the frozen relation protocol to an arbitrary arm-blind P1 union.

    This is a prospective adapter around the already-frozen pure protocol
    primitives.  It does not call the historical fixed-47 TASK entrypoints.
    """

    for digest in (train1_read_receipt_hash, train2_read_receipt_hash, train3_read_receipt_hash):
        require_sha256(digest, "feature_read_receipt_hash")
    order = tuple(feature_order)
    positions = {name: index for index, name in enumerate(order)}
    if len(order) != len(set(order)) or not set(FROZEN_SOURCES + FROZEN_TARGETS).issubset(positions):
        raise Exp01ConfirmationAdapterError("P1 relation feature authority is incomplete")
    if any(pair[0] not in FROZEN_SOURCES or pair[1] not in FROZEN_TARGETS for pair in candidate_pairs):
        raise Exp01ConfirmationAdapterError("candidate union exceeds frozen relation family roles")
    if len(candidate_pairs) != len(set(candidate_pairs)):
        raise Exp01ConfirmationAdapterError("candidate union contains duplicates")
    matrices = {FIT_FILES[0]: train1_matrix, FIT_FILES[1]: train2_matrix}
    fit_values = {
        file_name: {name: matrix[:, positions[name]] for name in FROZEN_SOURCES + FROZEN_TARGETS}
        for file_name, matrix in matrices.items()
    }
    source_parameters = {
        source: derive_multi_file_source_parameters_v1(
            tuple(fit_values[file_name][source] for file_name in FIT_FILES)
        )
        for source in FROZEN_SOURCES
    }
    target_scales = {
        target: derive_multi_file_target_scale_v1(
            tuple(fit_values[file_name][target] for file_name in FIT_FILES)
        )
        for target in FROZEN_TARGETS
    }
    events_by_file: dict[str, dict[str, Any]] = {name: {} for name in FIT_FILES}
    for source in FROZEN_SOURCES:
        params = source_parameters[source]
        for file_name in FIT_FILES:
            events_by_file[file_name][source] = (
                extract_sustained_step_events_linear_v1(
                    fit_values[file_name][source],
                    source_step_threshold=float(params["source_step_threshold"]),
                    source_stability_tolerance=float(params["source_stability_tolerance"]),
                )
                if params["status"] == "supported" else ()
            )
    isolated_fit = {
        file_name: classify_all_source_isolation_indexed_v1(events_by_file[file_name]) for file_name in FIT_FILES
    }
    fit_relations: list[dict[str, object]] = []
    pair_fit_ledger: list[dict[str, object]] = []
    for source, target in candidate_pairs:
        supported_directions = 0
        for source_direction in ("step_up", "step_down"):
            if source_parameters[source]["status"] != "supported":
                continue
            records = [
                _direction_statistics_v2(
                    target_by_file={name: fit_values[name][target] for name in FIT_FILES},
                    classified_by_file={name: isolated_fit[name][source] for name in FIT_FILES},
                    source_direction=source_direction,
                    target_noise_scale=target_scales[target], horizon=horizon,
                    target_direction=target_direction,
                )
                for target_direction in ("increase", "decrease") for horizon in HORIZONS
            ]
            projection_keys = (
                "target_direction", "horizon_seconds", "pooled_directional_consistency",
                "pooled_robust_effect_ratio", "train1_selected_consistency",
                "train1_opposite_consistency", "train2_selected_consistency",
                "train2_opposite_consistency",
            )
            selected = rank_direction_horizon_v1(
                [{key: record[key] for key in projection_keys} for record in records]
            )
            if selected is None:
                continue
            detail = next(
                record for record in records
                if record["target_direction"] == selected["target_direction"]
                and record["horizon_seconds"] == selected["horizon_seconds"]
            )
            if selected_fit_gate_v1(detail):
                supported_directions += 1
                fit_relations.append({
                    "source": source, "target": target, "source_direction": source_direction,
                    "target_direction": detail["target_direction"], "horizon": detail["horizon_seconds"],
                    "target_noise_scale": target_scales[target], "fit_detail": detail,
                })
        pair_fit_ledger.append({"source": source, "target": target, "supported_direction_count": supported_directions})
    train3_values = {
        name: train3_matrix[:, positions[name]] for name in FROZEN_SOURCES + FROZEN_TARGETS
    }
    train3_events = {
        source: (
            extract_sustained_step_events_linear_v1(
                train3_values[source],
                source_step_threshold=float(source_parameters[source]["source_step_threshold"]),
                source_stability_tolerance=float(source_parameters[source]["source_stability_tolerance"]),
            )
            if source_parameters[source]["status"] == "supported" else ()
        )
        for source in FROZEN_SOURCES
    }
    isolated_train3 = classify_all_source_isolation_indexed_v1(train3_events)
    directional_confirmation: list[dict[str, object]] = []
    confirmed_pairs: set[tuple[str, str]] = set()
    for relation in fit_relations:
        responses = [
            value for event, isolated in isolated_train3[str(relation["source"])]
            if isolated and event.direction == relation["source_direction"]
            for value in [_response(
                train3_values[str(relation["target"])], event_index=event.event_index,
                horizon=int(relation["horizon"]),
            )]
            if value is not None
        ]
        scale = float(relation["target_noise_scale"])
        increase = sum(value > scale for value in responses)
        decrease = sum(value < -scale for value in responses)
        selected_matches = increase if relation["target_direction"] == "increase" else decrease
        opposite_matches = decrease if relation["target_direction"] == "increase" else increase
        selected_consistency = selected_matches / len(responses) if responses else 0.0
        opposite_consistency = opposite_matches / len(responses) if responses else 0.0
        median = float(statistics.median(responses)) if responses else None
        effect = abs(median) / scale if median is not None else 0.0
        confirmed = train3_confirmation_gate_v1(
            usable_responses=len(responses), source_direction_unchanged=True,
            selected_consistency=selected_consistency, opposite_consistency=opposite_consistency,
            robust_effect_ratio=effect, fit_parameters_reused_without_retuning=True,
        )
        if confirmed:
            confirmed_pairs.add((str(relation["source"]), str(relation["target"])))
        directional_confirmation.append({
            "source": relation["source"], "target": relation["target"],
            "source_direction": relation["source_direction"],
            "target_direction": relation["target_direction"], "horizon": relation["horizon"],
            "usable": len(responses), "selected_consistency": selected_consistency,
            "opposite_consistency": opposite_consistency, "robust_effect_ratio": effect,
            "confirmed": confirmed,
        })
    decisions = tuple((source, target, (source, target) in confirmed_pairs) for source, target in candidate_pairs)
    private_ledger: dict[str, object] = {
        "schema": "paperworks.validation_v2.exp01_arm_blind_relation_ledger_v2",
        "schema_version": "2.0.0", "candidate_pairs": [list(pair) for pair in candidate_pairs],
        "fit_receipts": [train1_read_receipt_hash, train2_read_receipt_hash],
        "confirmation_receipt": train3_read_receipt_hash,
        "source_parameters": source_parameters, "target_scales": target_scales,
        "pair_fit_ledger": pair_fit_ledger, "fit_relations": fit_relations,
        "directional_confirmation": directional_confirmation,
        "arm_identity_exposed": False, "labels_accessed": False, "test_accessed": False,
    }
    ledger_hash = stable_hash_v1(private_ledger)
    return ArmBlindRelationExecutionV2(
        outcome=ArmBlindConfirmationOutcomeV2(
            pair_decisions=decisions, private_decision_ledger_hash=ledger_hash,
            train3_read_receipt_hash=train3_read_receipt_hash, train3_open_count=1,
        ),
        private_ledger={**private_ledger, "ledger_hash": ledger_hash},
    )


def confirm_candidate_union_arm_blind_v2(
    *,
    candidate_union: CandidateUnionAuthorityV1,
    evaluator: ConfirmationEvaluatorV2,
) -> tuple[ProfilingSubmissionV1, ConfirmationReceiptV1, ArmBlindConfirmationOutcomeV2]:
    submission = build_profiling_submission_v1(candidate_union=candidate_union)
    outcome = evaluator(submission.candidate_pairs)
    if type(outcome) is not ArmBlindConfirmationOutcomeV2:
        raise Exp01ConfirmationAdapterError("confirmation evaluator returned an untyped outcome")
    observed = tuple((source, target) for source, target, _ in outcome.pair_decisions)
    if observed != submission.candidate_pairs or len(observed) != len(set(observed)):
        raise Exp01ConfirmationAdapterError("confirmation must return the exact canonical candidate order")
    confirmed = tuple((source, target) for source, target, accepted in outcome.pair_decisions if accepted)
    rejected = tuple((source, target) for source, target, accepted in outcome.pair_decisions if not accepted)
    decision_hash = stable_hash_v1(
        {
            "submission_hash": submission.submission_hash,
            "private_decision_ledger_hash": outcome.private_decision_ledger_hash,
            "train3_read_receipt_hash": outcome.train3_read_receipt_hash,
            "decision_partition": [
                [source, target, "CONFIRMED" if accepted else "REJECTED"]
                for source, target, accepted in outcome.pair_decisions
            ],
            "arm_identity_exposed": False,
            "labels_accessed": False,
            "test_accessed": False,
        }
    )
    receipt = build_confirmation_receipt_v1(
        candidate_union=candidate_union,
        submission=submission,
        decision_ledger_hash=decision_hash,
        confirmed_pairs=confirmed,
        rejected_pairs=rejected,
    )
    return submission, receipt, outcome


def late_join_confirmation_by_aggregate_v2(
    *, confirmation: ConfirmationReceiptV1,
) -> Mapping[str, tuple[tuple[str, str], ...]]:
    """Join frozen outcomes to aggregate hashes after confirmation only."""

    confirmed = set(confirmation.confirmed_pairs)
    return {
        aggregate.receipt_hash: tuple(pair for pair in aggregate.top20 if pair in confirmed)
        for aggregate in confirmation.candidate_union.candidate_aggregates
    }


__all__ = [
    "ArmBlindConfirmationOutcomeV2", "ArmBlindRelationExecutionV2", "ConfirmationEvaluatorV2",
    "Exp01ConfirmationAdapterError", "confirm_candidate_union_arm_blind_v2",
    "fit_and_confirm_arbitrary_union_v2", "late_join_confirmation_by_aggregate_v2",
]
