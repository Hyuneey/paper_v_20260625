from __future__ import annotations

import inspect
import unittest
from dataclasses import FrozenInstanceError, replace

from paperworks.profiling.task039d2_confirmation_v1 import (
    ConfirmableDirectionalRelationV1,
    D1SourceParameterRecordV1,
    D1TargetParameterRecordV1,
    FrozenConfirmationControlsV1,
    TASK039D2PreparationError,
    confirm_synthetic_relations_v1,
)
from paperworks.v6.common import stable_hash_v1
from paperworks.v6.relation_profiling_protocol_v1 import (
    FROZEN_SOURCE_ROLES,
    FROZEN_SOURCES,
    FROZEN_TARGETS,
)


FIT_BINDINGS = (
    stable_hash_v1({"synthetic": "fit1"}),
    stable_hash_v1({"synthetic": "fit2"}),
)
SOURCE_LEDGER = stable_hash_v1({"synthetic": "source_ledger"})
TARGET_LEDGER = stable_hash_v1({"synthetic": "target_ledger"})


def source_record() -> D1SourceParameterRecordV1:
    source = FROZEN_SOURCES[0]
    content = {
        "schema_version": "1.0.0",
        "artifact_type": "task039d1_source_parameter_record_v1",
        "source": source,
        "semantic_role": FROZEN_SOURCE_ROLES[source],
        "source_noise_scale": 0.1,
        "nontrivial_amplitude_count": 20,
        "source_step_threshold": 1.0,
        "source_stability_tolerance": 0.1,
        "parameter_status": "supported",
        "parameter_class": "normal_relation_profile_fit_derived",
        "fit_file_bindings": list(FIT_BINDINGS),
    }
    return D1SourceParameterRecordV1(
        source=source,
        semantic_role=FROZEN_SOURCE_ROLES[source],
        source_noise_scale=0.1,
        nontrivial_amplitude_count=20,
        source_step_threshold=1.0,
        source_stability_tolerance=0.1,
        parameter_status="supported",
        fit_file_bindings=FIT_BINDINGS,
        d1_parameter_record_hash=stable_hash_v1(content),
        source_parameter_ledger_hash=SOURCE_LEDGER,
    )


def target_record() -> D1TargetParameterRecordV1:
    target = FROZEN_TARGETS[0]
    content = {
        "schema_version": "1.0.0",
        "artifact_type": "task039d1_target_parameter_record_v1",
        "target": target,
        "target_noise_scale": 1.0,
        "parameter_class": "normal_relation_profile_fit_derived",
        "fit_file_bindings": list(FIT_BINDINGS),
    }
    return D1TargetParameterRecordV1(
        target=target,
        target_noise_scale=1.0,
        fit_file_bindings=FIT_BINDINGS,
        d1_parameter_record_hash=stable_hash_v1(content),
        target_parameter_ledger_hash=TARGET_LEDGER,
    )


def relation() -> ConfirmableDirectionalRelationV1:
    source = source_record()
    target = target_record()
    return ConfirmableDirectionalRelationV1(
        source=source.source,
        source_step_direction="step_up",
        target=target.target,
        target_response_direction="increase",
        d1_selected_horizon_seconds=5,
        source_noise_scale_reference=source.d1_parameter_record_hash,
        source_threshold_reference=source.d1_parameter_record_hash,
        source_stability_tolerance_reference=source.d1_parameter_record_hash,
        target_scale_reference=target.d1_parameter_record_hash,
        d1_directional_record_hash=stable_hash_v1({"synthetic": "directional"}),
    )


class TASK039D2NoRetuningTests(unittest.TestCase):
    def test_numeric_d1_records_are_frozen_and_self_hash_bound(self) -> None:
        source = source_record()
        target = target_record()
        for field_name, changed_value in (
            ("source_noise_scale", 0.2),
            ("source_step_threshold", 1.1),
            ("source_stability_tolerance", 0.2),
        ):
            with self.subTest(field=field_name):
                with self.assertRaisesRegex(
                    TASK039D2PreparationError, "record hash mismatch"
                ):
                    replace(source, **{field_name: changed_value})
        with self.assertRaisesRegex(TASK039D2PreparationError, "record hash mismatch"):
            replace(target, target_noise_scale=1.1)
        with self.assertRaises(FrozenInstanceError):
            source.source_step_threshold = 2.0  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            target.target_noise_scale = 2.0  # type: ignore[misc]

    def test_direction_and_horizon_contract_fields_are_immutable(self) -> None:
        frozen_relation = relation()
        for field_name, changed_value in (
            ("source_step_direction", "step_down"),
            ("target_response_direction", "decrease"),
            ("d1_selected_horizon_seconds", 10),
        ):
            with self.subTest(field=field_name):
                with self.assertRaises(FrozenInstanceError):
                    setattr(frozen_relation, field_name, changed_value)

    def test_fixed_windows_isolation_and_search_controls_reject_changes(self) -> None:
        attempted_changes = (
            ("pre_window_seconds", 4),
            ("post_window_seconds", 6),
            ("response_window_seconds", 4),
            ("refractory_period_seconds", 9),
            ("isolation_radius_seconds", 3),
            ("alternative_horizon_search", True),
            ("opposite_direction_search", True),
            ("lower_ranked_fallback", True),
            ("retuning_allowed", True),
        )
        controls = FrozenConfirmationControlsV1()
        for field_name, changed_value in attempted_changes:
            with self.subTest(field=field_name):
                with self.assertRaisesRegex(TASK039D2PreparationError, "retuning"):
                    replace(controls, **{field_name: changed_value})

    def test_engine_exposes_no_retuning_or_search_arguments(self) -> None:
        parameters = set(inspect.signature(confirm_synthetic_relations_v1).parameters)
        forbidden = {
            "source_threshold",
            "stability_tolerance",
            "target_scale",
            "source_direction",
            "target_direction",
            "horizon",
            "pre_window",
            "post_window",
            "response_window",
            "isolation_radius",
            "alternative_horizon",
            "fallback",
            "flip_target_direction",
        }
        self.assertTrue(parameters.isdisjoint(forbidden))
        source = inspect.getsource(confirm_synthetic_relations_v1)
        self.assertNotIn("for horizon in", source)
        self.assertNotIn("for target_direction in", source)
        self.assertNotIn("rank_direction_horizon", source)
        with self.assertRaises(TypeError):
            confirm_synthetic_relations_v1(  # type: ignore[call-arg]
                relations=(),
                source_parameter_records=(),
                target_parameter_records=(),
                parameter_ledger_bindings=None,
                value_map=None,
                alternative_horizon=10,
            )


if __name__ == "__main__":
    unittest.main()
