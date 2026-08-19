from __future__ import annotations

import json
from pathlib import Path
import unittest

import paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 as authority_v1
import paperworks.v6.task039e3_r2r_utility_evaluator_input_v1 as input_v1
import paperworks.v6.task039e3_r2r_utility_evaluator_metrics_v1 as metrics_v1
import paperworks.v6.task039e3_r2r_utility_evaluator_v1 as evaluator_v1
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import UtilityEvaluatorV1Error
import paperworks.v6.task039e3_r2r_utility_protocol_v4 as protocol_v4
import paperworks.v6.task039e3_r2r_utility_source_census_supplement_v1 as supplement_v1


ROOT = Path(__file__).resolve().parents[1]
CURRENT_R1_IMPLEMENTATION_IDENTITY = (
    "64a6e7f0d210dc074bc85b0f389e61b45aaa512091532cf8f4d275ccaa35746a"
)
HISTORICAL_IMPLEMENTATION_IDENTITY = (
    "332e367cdc0da21b281c5de43f6a735d7dc68bc87efafe90976d89d7f9dc3330"
)


def _load(relative_path: str) -> dict[str, object]:
    value = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise AssertionError(f"lower public authority is not an object: {relative_path}")
    return value


def _value_for(role: str) -> int | float:
    if role == "source_step_threshold":
        return 1.0
    if role == "source_stability_tolerance":
        return 0.0
    if role == "target_noise_scale":
        return 0.1
    return {
        "source_pre_window_seconds": 5,
        "source_post_window_seconds": 5,
        "minimum_source_stability_fraction": 0.8,
        "source_refractory_seconds": 10,
        "cross_source_isolation_radius_seconds": 2,
        "target_baseline_window_seconds": 5,
        "target_response_window_seconds": 3,
    }[role]


class UtilityEvaluatorV1R1IndependentMetricArtifactAudit(unittest.TestCase):
    """Independent R1 prediction-custody attack from lower public authorities."""

    @classmethod
    def setUpClass(cls) -> None:
        v4_authority = protocol_v4.build_utility_protocol_v4_canonical_authority(
            executable_equivalence=_load(
                "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"
            ),
            evidence_manifest=_load(
                "docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json"
            ),
            dataset_manifest=_load(
                "docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json"
            ),
            csv_structure_report=_load(
                "docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json"
            ),
            c0_config=_load("configs/v6/task039c0_candidate_discovery_protocol.json"),
            br2_config=_load(
                "configs/v6/task039br2_hai_continuous_step_feasibility.json"
            ),
            materialized_audit_receipt=_load(
                "docs/task_reports/TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZED_RECEIPT.json"
            ),
        )
        cls.bundle = authority_v1.build_evaluator_authority_bundle_v1(v4_authority)
        cls.implementation = evaluator_v1.build_evaluator_implementation_authority_v1(
            cls.bundle
        )
        main_records = tuple(
            authority_v1.SyntheticNumericRecordV1(
                "SYNTHETIC_MAIN_420",
                rule.source,
                rule.relation_binding_hash,
                role,
                reference,
                _value_for(role),
            )
            for rule in v4_authority.rule_descriptors
            for role, reference in rule.numeric_reference_bindings
        )
        supplement_records = tuple(
            authority_v1.SyntheticNumericRecordV1(
                authority_v1.SUPPLEMENT_PURPOSE,
                source,
                None,
                role,
                supplement_v1.supplement_reference_identity_v1(source, role),
                _value_for(role),
            )
            for source in authority_v1.SUPPLEMENT_SOURCES
            for role in authority_v1.SOURCE_CENSUS_ROLES
        )
        cls.resolver = authority_v1.build_synthetic_numeric_resolver_v1(
            cls.bundle, main_records, supplement_records
        )
        rows = tuple(
            tuple(0.0 for _ in v4_authority.feature_schema.union_features)
            for _ in range(20)
        )
        cls.frame = input_v1.build_synthetic_feature_frame_v1(
            cls.bundle,
            source_file_identity="hai-test1.csv",
            start_physical_row_index=0,
            rows=rows,
        )
        cls.synthetic_run = evaluator_v1.run_synthetic_utility_evaluator_v1(
            authority=cls.implementation,
            bundle=cls.bundle,
            resolver=cls.resolver,
            frame=cls.frame,
        )

    def test_lower_oracle_binds_current_r1_identity(self) -> None:
        self.assertEqual(
            self.implementation.implementation_identity,
            CURRENT_R1_IMPLEMENTATION_IDENTITY,
        )
        self.assertNotEqual(
            CURRENT_R1_IMPLEMENTATION_IDENTITY,
            HISTORICAL_IMPLEMENTATION_IDENTITY,
        )

    def test_prediction_factory_rejects_historical_implementation_identity(self) -> None:
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics_v1.build_rule_prediction_artifact_v1(
                evaluator_implementation_identity=HISTORICAL_IMPLEMENTATION_IDENTITY,
                bundle=self.bundle,
                frame=self.frame,
                census=self.synthetic_run.census,
                resolver=self.resolver,
                predictions=self.synthetic_run.rule_prediction_artifact.predictions,
            )


if __name__ == "__main__":
    unittest.main()
