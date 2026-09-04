"""Schema-bound external adapter. Frozen confirmation arithmetic is unchanged."""
from typing import Any, Sequence
import statistics
from paperworks.validation_v2.exp01_relation_confirmation_v2 import (
    ArmBlindRelationExecutionV2, ArmBlindConfirmationOutcomeV2,
    Exp01ConfirmationAdapterError, _response, _direction_statistics_v2,
)
from paperworks.v6.common import require_sha256, stable_hash_v1
from paperworks.profiling.task039d1_execution_optimization_v1 import extract_sustained_step_events_linear_v1
from paperworks.v6.relation_profiling_protocol_v1 import (
    FIT_FILES, HORIZONS, derive_multi_file_source_parameters_v1,
    derive_multi_file_target_scale_v1, rank_direction_horizon_v1,
    selected_fit_gate_v1, train3_confirmation_gate_v1,
)
from .exp03b_numeric_v1 import nearest
from .exp03b_contract_v1 import require


def classify_mapped_isolation(events):
    """Same >2 physical-source isolation, explicit schema-derived universe."""
    require(bool(events), 'EMPTY_SOURCE_UNIVERSE')
    result = {}
    for source, local in events.items():
        others = tuple(sorted({e.event_index for s, rows in events.items()
                               if s != source for e in rows}))
        result[source] = tuple((e, nearest(e.event_index, others) is None or
                                nearest(e.event_index, others) > 2) for e in local)
    return result


def fit_and_confirm_mapped_union_v1(
    *,
    mapped_sources: tuple[str, ...],
    mapped_targets: tuple[str, ...],
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
    if len(order) != len(set(order)) or not set(mapped_sources + mapped_targets).issubset(positions):
        raise Exp01ConfirmationAdapterError("P1 relation feature authority is incomplete")
    if any(pair[0] not in mapped_sources or pair[1] not in mapped_targets for pair in candidate_pairs):
        raise Exp01ConfirmationAdapterError("candidate union exceeds frozen relation family roles")
    if len(candidate_pairs) != len(set(candidate_pairs)):
        raise Exp01ConfirmationAdapterError("candidate union contains duplicates")
    matrices = {FIT_FILES[0]: train1_matrix, FIT_FILES[1]: train2_matrix}
    fit_values = {
        file_name: {name: matrix[:, positions[name]] for name in mapped_sources + mapped_targets}
        for file_name, matrix in matrices.items()
    }
    source_parameters = {
        source: derive_multi_file_source_parameters_v1(
            tuple(fit_values[file_name][source] for file_name in FIT_FILES)
        )
        for source in mapped_sources
    }
    target_scales = {
        target: derive_multi_file_target_scale_v1(
            tuple(fit_values[file_name][target] for file_name in FIT_FILES)
        )
        for target in mapped_targets
    }
    events_by_file: dict[str, dict[str, Any]] = {name: {} for name in FIT_FILES}
    for source in mapped_sources:
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
        file_name: classify_mapped_isolation(events_by_file[file_name]) for file_name in FIT_FILES
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
        name: train3_matrix[:, positions[name]] for name in mapped_sources + mapped_targets
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
        for source in mapped_sources
    }
    isolated_train3 = classify_mapped_isolation(train3_events)
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
