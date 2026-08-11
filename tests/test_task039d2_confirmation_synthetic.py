from __future__ import annotations

import unittest
from dataclasses import fields
from pathlib import Path

from paperworks.profiling.task039d2_confirmation_v1 import (
    CONFIRMATION_POLICY_HASH,
    D1ParameterLedgerBindingsV1,
    D1SourceParameterRecordV1,
    D1TargetParameterRecordV1,
    ConfirmableDirectionalRelationV1,
    SYNTHETIC_CASES,
    SyntheticTrain3ValueMapV1,
    apply_exact_confirmation_gate_v1,
    build_synthetic_preparation_execution_receipt_v1,
    classify_train3_all_source_isolation_v1,
    confirm_synthetic_relations_v1,
    evaluate_train3_target_response_window_v1,
    extract_train3_source_events_v1,
)
from paperworks.profiling.task039d1_execution_optimization_v1 import (
    extract_sustained_step_events_linear_v1,
)
from paperworks.v6.common import stable_hash_v1
from paperworks.v6.continuous_step_protocol_v1 import (
    SustainedStepEventV1,
    evaluate_target_response_v1,
    extract_sustained_step_events_v1,
)
from paperworks.v6.relation_profiling_protocol_v1 import (
    FROZEN_SOURCE_ROLES,
    FROZEN_SOURCES,
    FROZEN_TARGETS,
    classify_all_source_isolation_v1,
    train3_confirmation_gate_v1,
)
from paperworks.v6.schema_registry_v1 import load_v6_schema_registry_v1


ROOT = Path(__file__).resolve().parents[1]
SOURCE_LEDGER_HASH = stable_hash_v1({"synthetic_fixture": "source_ledger"})
TARGET_LEDGER_HASH = stable_hash_v1({"synthetic_fixture": "target_ledger"})
FIT_FILE_BINDINGS = (
    stable_hash_v1({"synthetic_fixture": "fit_file_1"}),
    stable_hash_v1({"synthetic_fixture": "fit_file_2"}),
)


def source_record(
    source: str,
    *,
    threshold: float = 1.0,
    tolerance: float = 0.1,
) -> D1SourceParameterRecordV1:
    content = {
        "schema_version": "1.0.0",
        "artifact_type": "task039d1_source_parameter_record_v1",
        "source": source,
        "semantic_role": FROZEN_SOURCE_ROLES[source],
        "source_noise_scale": 0.1,
        "nontrivial_amplitude_count": 20,
        "source_step_threshold": threshold,
        "source_stability_tolerance": tolerance,
        "parameter_status": "supported",
        "parameter_class": "normal_relation_profile_fit_derived",
        "fit_file_bindings": list(FIT_FILE_BINDINGS),
    }
    return D1SourceParameterRecordV1(
        source=source,
        semantic_role=FROZEN_SOURCE_ROLES[source],
        source_noise_scale=0.1,
        nontrivial_amplitude_count=20,
        source_step_threshold=threshold,
        source_stability_tolerance=tolerance,
        parameter_status="supported",
        fit_file_bindings=FIT_FILE_BINDINGS,
        d1_parameter_record_hash=stable_hash_v1(content),
        source_parameter_ledger_hash=SOURCE_LEDGER_HASH,
    )


def target_record(target: str, *, scale: float = 1.0) -> D1TargetParameterRecordV1:
    content = {
        "schema_version": "1.0.0",
        "artifact_type": "task039d1_target_parameter_record_v1",
        "target": target,
        "target_noise_scale": scale,
        "parameter_class": "normal_relation_profile_fit_derived",
        "fit_file_bindings": list(FIT_FILE_BINDINGS),
    }
    return D1TargetParameterRecordV1(
        target=target,
        target_noise_scale=scale,
        fit_file_bindings=FIT_FILE_BINDINGS,
        d1_parameter_record_hash=stable_hash_v1(content),
        target_parameter_ledger_hash=TARGET_LEDGER_HASH,
    )


def source_series(
    direction: str,
    count: int,
    *,
    horizon: int = 5,
    include_right_censored: bool = False,
) -> tuple[tuple[float, ...], tuple[int, ...]]:
    spacing = 90 if include_right_censored else 40
    positions = [20 + spacing * index for index in range(count)]
    if include_right_censored:
        length = positions[-1] + spacing
        positions.append(length - 5)
    else:
        length = positions[-1] + max(horizon + 15, 30) if positions else 80
    baseline, stepped = (0.0, 2.0) if direction == "step_up" else (2.0, 0.0)
    values = [baseline] * length
    for position in positions:
        for index in range(position, min(position + 15, length)):
            values[index] = stepped
    events = extract_sustained_step_events_linear_v1(
        values,
        source_step_threshold=1.0,
        source_stability_tolerance=0.1,
    )
    selected = tuple(event.event_index for event in events if event.direction == direction)
    expected_count = count + int(include_right_censored)
    if len(selected) != expected_count:
        raise AssertionError((direction, expected_count, selected))
    return tuple(values), selected


def target_series(
    length: int,
    event_indices: tuple[int, ...],
    responses: tuple[float, ...],
    *,
    horizon: int,
) -> tuple[float, ...]:
    values = [0.0] * length
    for event_index, response in zip(event_indices, responses, strict=True):
        start = event_index + horizon
        if start + 3 <= length:
            values[start : start + 3] = [response] * 3
    return tuple(values)


def execute_case(
    *,
    source_direction: str = "step_up",
    target_direction: str = "increase",
    responses: tuple[float, ...] = (2.0, 2.0, 2.0, 2.0, 2.0),
    horizon: int = 5,
    include_right_censored: bool = False,
    response_horizon: int | None = None,
    interfering_offset: int | None = None,
):
    source = FROZEN_SOURCES[0]
    target = FROZEN_TARGETS[0]
    source_values, event_indices = source_series(
        source_direction,
        len(responses),
        horizon=horizon,
        include_right_censored=include_right_censored,
    )
    values: dict[str, tuple[float, ...]] = {
        name: tuple(0.0 for _ in source_values) for name in FROZEN_SOURCES
    }
    values[source] = source_values
    if interfering_offset is not None:
        position = event_indices[0] + interfering_offset
        other_values = [0.0] * len(source_values)
        for index in range(position, min(position + 15, len(other_values))):
            other_values[index] = 2.0
        values[FROZEN_SOURCES[1]] = tuple(other_values)
    target_values = target_series(
        len(source_values),
        event_indices,
        responses + ((0.0,) if include_right_censored else ()),
        horizon=horizon if response_horizon is None else response_horizon,
    )
    values[target] = target_values
    sources = tuple(source_record(name) for name in FROZEN_SOURCES)
    target_parameters = (target_record(target),)
    relation = ConfirmableDirectionalRelationV1(
        source=source,
        source_step_direction=source_direction,
        target=target,
        target_response_direction=target_direction,
        d1_selected_horizon_seconds=horizon,
        source_noise_scale_reference=sources[0].d1_parameter_record_hash,
        source_threshold_reference=sources[0].d1_parameter_record_hash,
        source_stability_tolerance_reference=sources[0].d1_parameter_record_hash,
        target_scale_reference=target_parameters[0].d1_parameter_record_hash,
        d1_directional_record_hash=stable_hash_v1(
            {"synthetic_fixture": "directional_record", "direction": source_direction}
        ),
    )
    result = confirm_synthetic_relations_v1(
        relations=(relation,),
        source_parameter_records=sources,
        target_parameter_records=target_parameters,
        parameter_ledger_bindings=D1ParameterLedgerBindingsV1(
            SOURCE_LEDGER_HASH, TARGET_LEDGER_HASH
        ),
        value_map=SyntheticTrain3ValueMapV1(
            fixture_id="synthetic_confirmation_case",
            values=values,
        ),
    )[0]
    return result, relation, sources, target_parameters, values, event_indices


def event(index: int) -> SustainedStepEventV1:
    return SustainedStepEventV1(index, "step_up", 0.0, 2.0, 2.0, 1.0, 1.0)


class TASK039D2SyntheticConfirmationTests(unittest.TestCase):
    def test_confirmed_insufficient_and_exact_five_response_boundary(self) -> None:
        confirmed, *_ = execute_case()
        self.assertEqual(confirmed.status, "calibration_confirmed")
        self.assertEqual(confirmed.usable_response_count, 5)
        self.assertEqual(confirmed.selected_directional_consistency, 1.0)
        insufficient, *_ = execute_case(responses=(2.0, 2.0, 2.0, 2.0))
        self.assertEqual(insufficient.status, "calibration_conflict")
        self.assertEqual(insufficient.usable_response_count, 4)

    def test_exact_gate_boundaries_and_d0_parity(self) -> None:
        cases = (
            ("consistency_exactly_0_60", 5, True, 0.60, 0.20, 1.0, True),
            ("consistency_just_below_0_60", 100, True, 0.59, 0.20, 2.0, False),
            ("effect_exactly_1_0", 5, True, 0.80, 0.20, 1.0, True),
            ("effect_just_below_1_0", 5, True, 0.80, 0.20, 0.999999, False),
            ("selected_greater", 5, True, 0.60, 0.40, 1.0, True),
            ("equality", 5, True, 0.60, 0.60, 1.0, False),
            ("opposite_greater", 5, True, 0.60, 0.80, 1.0, False),
            ("source_changed", 5, False, 0.80, 0.10, 2.0, False),
        )
        for name, usable, unchanged, selected, opposite, effect_ratio, expected in cases:
            with self.subTest(name=name):
                observed = apply_exact_confirmation_gate_v1(
                    usable_responses=usable,
                    source_direction_unchanged=unchanged,
                    selected_consistency=selected,
                    opposite_consistency=opposite,
                    robust_effect_ratio=effect_ratio,
                    fit_parameters_reused_without_retuning=True,
                )
                reference = train3_confirmation_gate_v1(
                    usable_responses=usable,
                    source_direction_unchanged=unchanged,
                    selected_consistency=selected,
                    opposite_consistency=opposite,
                    robust_effect_ratio=effect_ratio,
                    fit_parameters_reused_without_retuning=True,
                )
                self.assertEqual(observed, reference)
                self.assertEqual(observed, expected)

    def test_right_censoring_is_counted_and_never_imputed(self) -> None:
        result, *_ = execute_case(
            responses=(2.0, 2.0, 2.0, 2.0, 2.0),
            horizon=60,
            include_right_censored=True,
        )
        self.assertEqual(result.usable_response_count, 5)
        self.assertEqual(result.right_censored_count, 1)
        self.assertEqual(result.status, "calibration_confirmed")

    def test_both_source_and_target_directions(self) -> None:
        for source_direction in ("step_up", "step_down"):
            for target_direction, response in (("increase", 2.0), ("decrease", -2.0)):
                with self.subTest(
                    source_direction=source_direction, target_direction=target_direction
                ):
                    result, *_ = execute_case(
                        source_direction=source_direction,
                        target_direction=target_direction,
                        responses=(response,) * 5,
                    )
                    self.assertEqual(result.status, "calibration_confirmed")
                    self.assertEqual(result.source_step_direction, source_direction)
                    self.assertEqual(result.target_response_direction, target_direction)

    def test_all_12_source_isolation_and_inclusive_plus_minus_two_boundary(self) -> None:
        result, *_ = execute_case(
            responses=(2.0,) * 5,
            interfering_offset=2,
        )
        self.assertEqual(result.usable_response_count, 4)
        self.assertEqual(result.status, "calibration_conflict")
        for offset, isolated in ((-3, True), (-2, False), (2, False), (3, True)):
            fixture = {source: () for source in FROZEN_SOURCES}
            fixture[FROZEN_SOURCES[0]] = (event(50),)
            fixture[FROZEN_SOURCES[1]] = (event(50 + offset),)
            observed = classify_train3_all_source_isolation_v1(fixture)
            self.assertEqual(observed[FROZEN_SOURCES[0]][0][1], isolated)
            self.assertEqual(observed, classify_all_source_isolation_v1(fixture))

    def test_selected_horizon_is_immutable_and_no_alternative_is_searched(self) -> None:
        result, *_ = execute_case(
            responses=(2.0,) * 5,
            horizon=5,
            response_horizon=10,
        )
        payload = result.to_dict()
        self.assertEqual(result.selected_horizon_seconds, 5)
        self.assertEqual(result.status, "calibration_conflict")
        self.assertFalse(payload["alternative_horizon_search_performed"])
        self.assertFalse(payload["lower_ranked_fallback_used"])

    def test_target_direction_is_immutable_and_never_flipped(self) -> None:
        result, *_ = execute_case(
            target_direction="increase",
            responses=(-2.0,) * 5,
        )
        payload = result.to_dict()
        self.assertEqual(result.target_response_direction, "increase")
        self.assertEqual(result.opposite_directional_consistency, 1.0)
        self.assertFalse(result.target_direction_unchanged)
        self.assertEqual(result.status, "calibration_conflict")
        self.assertFalse(payload["opposite_direction_search_performed"])

    def test_optimized_wrappers_match_frozen_reference_helpers(self) -> None:
        source_values, indices = source_series("step_up", 5)
        sources = {source: source_record(source) for source in FROZEN_SOURCES}
        values = {source: tuple(0.0 for _ in source_values) for source in FROZEN_SOURCES}
        values[FROZEN_SOURCES[0]] = source_values
        values[FROZEN_TARGETS[0]] = target_series(
            len(source_values), indices, (2.0,) * 5, horizon=5
        )
        value_map = SyntheticTrain3ValueMapV1(
            fixture_id="synthetic_wrapper_parity",
            values=values,
        )
        extracted = extract_train3_source_events_v1(value_map, sources)
        reference_events = extract_sustained_step_events_v1(
            source_values,
            source_step_threshold=1.0,
            source_stability_tolerance=0.1,
        )
        self.assertEqual(extracted[FROZEN_SOURCES[0]], reference_events)
        self.assertEqual(
            classify_train3_all_source_isolation_v1(extracted),
            classify_all_source_isolation_v1(extracted),
        )
        for event_index in (*indices, len(source_values) - 5):
            observed = evaluate_train3_target_response_window_v1(
                values[FROZEN_TARGETS[0]],
                event_index=event_index,
                selected_horizon_seconds=5,
            )
            reference = evaluate_target_response_v1(
                values[FROZEN_TARGETS[0]],
                event_index=event_index,
                horizon_seconds=5,
                target_noise_scale=1.0,
                target_direction="increase",
            )
            self.assertEqual(observed, (reference.right_censored, reference.target_response))

    def test_result_and_receipt_schemas_are_closed_and_self_hashed(self) -> None:
        result, *_ = execute_case()
        result_document = result.to_dict()
        receipt = build_synthetic_preparation_execution_receipt_v1()
        pairs = (
            (result_document, "task039d2_confirmation_result_v1_schema.json"),
            (receipt, "task039d2_execution_receipt_v1_schema.json"),
        )
        import json

        registry = load_v6_schema_registry_v1(repository_root=ROOT)
        self.assertEqual(len(registry.artifact_types), 144)

        for document, schema_name in pairs:
            schema = json.loads((ROOT / "schemas" / "v6" / schema_name).read_text("utf-8"))
            self.assertEqual(schema, registry.schema_for(document["artifact_type"]))
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(schema["additionalProperties"])
            self.assertEqual(set(document), set(schema["required"]))
            for field_name, specification in schema["properties"].items():
                if "const" in specification:
                    self.assertEqual(document[field_name], specification["const"])
            content = {key: value for key, value in document.items() if key != "artifact_hash"}
            self.assertEqual(document["artifact_hash"], stable_hash_v1(content))
        self.assertEqual(receipt["confirmation_policy_hash"], CONFIRMATION_POLICY_HASH)
        self.assertEqual(tuple(receipt["synthetic_cases"]), SYNTHETIC_CASES)

    def test_arm_blind_contracts_and_outputs(self) -> None:
        forbidden = {
            "meta_rank",
            "meta_tier",
            "stat_score",
            "stat_horizon",
            "gdn_rank",
            "gdn_similarity",
            "gdn_frequency",
            "origin_arms",
            "overlap_category",
        }
        relation_fields = {item.name for item in fields(ConfirmableDirectionalRelationV1)}
        self.assertTrue(relation_fields.isdisjoint(forbidden))
        result, relation, *_ = execute_case()
        self.assertTrue(set(relation.to_dict()).isdisjoint(forbidden))
        self.assertTrue(set(result.to_dict()).isdisjoint(forbidden))
        self.assertFalse(result.to_dict()["candidate_arm_provenance_visible"])
        with self.assertRaises(TypeError):
            ConfirmableDirectionalRelationV1(  # type: ignore[call-arg]
                **{
                    **{key: value for key, value in relation.to_dict().items() if key not in {"schema_version", "artifact_type", "artifact_hash"}},
                    "origin_arms": ["META"],
                }
            )


if __name__ == "__main__":
    unittest.main()
