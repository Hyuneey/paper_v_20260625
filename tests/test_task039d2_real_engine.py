from __future__ import annotations

import unittest

from paperworks.profiling.task039d2_confirmation_v1 import (
    ConfirmableDirectionalRelationV1,
    D1ParameterLedgerBindingsV1,
    D1SourceParameterRecordV1,
    D1TargetParameterRecordV1,
)
from paperworks.profiling.task039d2_real_execution_v1 import (
    D1PrivateInputsV1,
    confirm_relations_one_way_v1,
    verify_d2_self_hash_v1,
)
from paperworks.v6.common import V6_FOUNDATION_SCHEMA_VERSION, stable_hash_v1
from paperworks.v6.relation_profiling_protocol_v1 import (
    FROZEN_SOURCE_ROLES,
    FROZEN_SOURCES,
    FROZEN_TARGETS,
)


FIT_BINDINGS = ("1" * 64, "2" * 64)


def _source_record(source: str) -> D1SourceParameterRecordV1:
    content = {
        "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
        "artifact_type": "task039d1_source_parameter_record_v1",
        "source": source,
        "semantic_role": FROZEN_SOURCE_ROLES[source],
        "source_noise_scale": 0.1,
        "nontrivial_amplitude_count": 20,
        "source_step_threshold": 5.0,
        "source_stability_tolerance": 0.5,
        "parameter_status": "supported",
        "parameter_class": "normal_relation_profile_fit_derived",
        "fit_file_bindings": list(FIT_BINDINGS),
    }
    return D1SourceParameterRecordV1(
        source=source, semantic_role=FROZEN_SOURCE_ROLES[source], source_noise_scale=0.1,
        nontrivial_amplitude_count=20, source_step_threshold=5.0,
        source_stability_tolerance=0.5, parameter_status="supported",
        fit_file_bindings=FIT_BINDINGS, d1_parameter_record_hash=stable_hash_v1(content),
        source_parameter_ledger_hash="3" * 64,
    )


def _target_record(target: str) -> D1TargetParameterRecordV1:
    content = {
        "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
        "artifact_type": "task039d1_target_parameter_record_v1",
        "target": target, "target_noise_scale": 1.0,
        "parameter_class": "normal_relation_profile_fit_derived",
        "fit_file_bindings": list(FIT_BINDINGS),
    }
    return D1TargetParameterRecordV1(
        target=target, target_noise_scale=1.0, fit_file_bindings=FIT_BINDINGS,
        d1_parameter_record_hash=stable_hash_v1(content), target_parameter_ledger_hash="4" * 64,
    )


class TASK039D2RealEngineTests(unittest.TestCase):
    def test_exact_45_arm_blind_relations_produce_only_two_statuses(self) -> None:
        sources = tuple(_source_record(source) for source in FROZEN_SOURCES)
        targets = tuple(_target_record(target) for target in FROZEN_TARGETS)
        source_by_name = {item.source: item for item in sources}
        target_by_name = {item.target: item for item in targets}
        identities = [
            (source, target, direction)
            for source in FROZEN_SOURCES
            for target in FROZEN_TARGETS
            for direction in ("step_up", "step_down")
        ][:45]
        relations = tuple(
            ConfirmableDirectionalRelationV1(
                source=source, source_step_direction=direction, target=target,
                target_response_direction="increase", d1_selected_horizon_seconds=5,
                source_noise_scale_reference=source_by_name[source].d1_parameter_record_hash,
                source_threshold_reference=source_by_name[source].d1_parameter_record_hash,
                source_stability_tolerance_reference=source_by_name[source].d1_parameter_record_hash,
                target_scale_reference=target_by_name[target].d1_parameter_record_hash,
                d1_directional_record_hash=stable_hash_v1({"identity": [source, target, direction]}),
            )
            for source, target, direction in identities
        )
        private = D1PrivateInputsV1(
            source_document={}, target_document={}, directional_document={},
            source_records=sources, target_records=targets, relations=relations,
            parameter_bindings=D1ParameterLedgerBindingsV1("3" * 64, "4" * 64),
        )
        values = {name: [0.0] * 80 for name in (*FROZEN_SOURCES, *FROZEN_TARGETS)}
        outcome = confirm_relations_one_way_v1(values=values, private_inputs=private)
        ledger = outcome["ledger"]
        verify_d2_self_hash_v1(ledger)
        self.assertEqual(ledger["record_count"], 45)
        self.assertEqual({item["confirmation_status"] for item in ledger["records"]}, {"calibration_conflict"})
        self.assertTrue(all(item["parameter_retuning_used"] is False for item in ledger["records"]))
        self.assertTrue(all(item["candidate_provenance_visible"] is False for item in ledger["records"]))


if __name__ == "__main__":
    unittest.main()
