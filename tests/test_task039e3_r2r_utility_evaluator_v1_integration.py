from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import unittest

import paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 as auth
import paperworks.v6.task039e3_r2r_utility_evaluator_input_v1 as input_v1
import paperworks.v6.task039e3_r2r_utility_evaluator_metrics_v1 as metrics
import paperworks.v6.task039e3_r2r_utility_evaluator_v1 as evaluator
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import (
    SYNTHETIC_CONTRACT_ONLY,
    UtilityEvaluatorV1Error,
)
import paperworks.v6.task039e3_r2r_utility_protocol_v4 as v4
import paperworks.v6.task039e3_r2r_utility_source_census_supplement_v1 as supplement


ROOT = Path(__file__).resolve().parents[1]
NEGATIVE_CASE_COUNT = 8


def load(relative_path: str) -> dict[str, object]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def value_for(role: str) -> int | float:
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


class UtilityEvaluatorV1IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        v4_authority = v4.build_utility_protocol_v4_canonical_authority(
            executable_equivalence=load(
                "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"
            ),
            evidence_manifest=load("docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json"),
            dataset_manifest=load("docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json"),
            csv_structure_report=load("docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json"),
            c0_config=load("configs/v6/task039c0_candidate_discovery_protocol.json"),
            br2_config=load("configs/v6/task039br2_hai_continuous_step_feasibility.json"),
            materialized_audit_receipt=load(
                "docs/task_reports/TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZED_RECEIPT.json"
            ),
        )
        cls.bundle = auth.build_evaluator_authority_bundle_v1(v4_authority)
        cls.implementation = evaluator.build_evaluator_implementation_authority_v1(cls.bundle)
        main_records = tuple(
            auth.SyntheticNumericRecordV1(
                "SYNTHETIC_MAIN_420",
                rule.source,
                rule.relation_binding_hash,
                role,
                reference,
                value_for(role),
            )
            for rule in v4_authority.rule_descriptors
            for role, reference in rule.numeric_reference_bindings
        )
        supplement_records = tuple(
            auth.SyntheticNumericRecordV1(
                auth.SUPPLEMENT_PURPOSE,
                source,
                None,
                role,
                supplement.supplement_reference_identity_v1(source, role),
                value_for(role),
            )
            for source in auth.SUPPLEMENT_SOURCES
            for role in auth.SOURCE_CENSUS_ROLES
        )
        cls.resolver = auth.build_synthetic_numeric_resolver_v1(
            cls.bundle, main_records, supplement_records
        )

        ordered = v4_authority.feature_schema.union_features
        first_rule = v4_authority.rule_descriptors[0]
        rows: list[tuple[float, ...]] = []
        for index in range(80):
            values = {feature: 0.0 for feature in ordered}
            if index >= 20:
                values[first_rule.source] = (
                    100.0 if first_rule.source_direction == "step_up" else -100.0
                )
            rows.append(tuple(values[feature] for feature in ordered))
        cls.frame = input_v1.build_synthetic_feature_frame_v1(
            cls.bundle,
            source_file_identity="hai-test1.csv",
            start_physical_row_index=0,
            rows=tuple(rows),
        )

    def test_positive_synthetic_pipeline_is_deterministic(self) -> None:
        first = evaluator.run_synthetic_utility_evaluator_v1(
            authority=self.implementation,
            bundle=self.bundle,
            resolver=self.resolver,
            frame=self.frame,
        )
        second = evaluator.run_synthetic_utility_evaluator_v1(
            authority=self.implementation,
            bundle=self.bundle,
            resolver=self.resolver,
            frame=self.frame,
        )
        self.assertEqual(first, second)
        self.assertEqual(first.execution_mode, SYNTHETIC_CONTRACT_ONLY)
        self.assertFalse(first.scientific_eligible)
        self.assertGreater(first.source_event_count, 0)
        self.assertGreater(first.isolated_source_event_count, 0)
        self.assertGreater(first.relation_opportunity_count, 0)
        self.assertEqual(
            evaluator.validate_synthetic_evaluator_run_v1(
                first,
                authority=self.implementation,
                bundle=self.bundle,
                resolver=self.resolver,
                frame=self.frame,
            ),
            first.run_hash,
        )

    def test_no_source_event_produces_valid_zero_denominator_census(self) -> None:
        rows = tuple(tuple(0.0 for _ in self.frame.ordered_features) for _ in range(20))
        frame = input_v1.build_synthetic_feature_frame_v1(
            self.bundle,
            source_file_identity="hai-test1.csv",
            start_physical_row_index=0,
            rows=rows,
        )
        run = evaluator.run_synthetic_utility_evaluator_v1(
            authority=self.implementation,
            bundle=self.bundle,
            resolver=self.resolver,
            frame=frame,
        )
        self.assertEqual(run.relation_opportunity_count, 0)
        self.assertEqual(run.rule_prediction_artifact.evaluated_count, 0)

    def test_authority_and_run_mutations_reject_6_cases(self) -> None:
        run = evaluator.run_synthetic_utility_evaluator_v1(
            authority=self.implementation,
            bundle=self.bundle,
            resolver=self.resolver,
            frame=self.frame,
        )
        authority_mutations = (
            {"v4_authority_hash": "f" * 64},
            {"execution_mode": "REAL_AUTHORIZED_UTILITY_EXECUTION"},
            {"real_utility_execution_authorized": True},
        )
        for changes in authority_mutations:
            with self.subTest(authority=tuple(changes)), self.assertRaises(UtilityEvaluatorV1Error):
                evaluator.validate_evaluator_implementation_authority_v1(
                    replace(self.implementation, **changes), self.bundle
                )
        run_mutations = (
            {"scientific_eligible": True},
            {"relation_opportunity_count": run.relation_opportunity_count + 1},
            {"run_hash": "f" * 64},
        )
        for changes in run_mutations:
            with self.subTest(run=tuple(changes)), self.assertRaises(UtilityEvaluatorV1Error):
                evaluator.validate_synthetic_evaluator_run_v1(
                    replace(run, **changes),
                    authority=self.implementation,
                    bundle=self.bundle,
                    resolver=self.resolver,
                    frame=self.frame,
                )

    def test_synthetic_result_cannot_become_scientific(self) -> None:
        run = evaluator.run_synthetic_utility_evaluator_v1(
            authority=self.implementation,
            bundle=self.bundle,
            resolver=self.resolver,
            frame=self.frame,
        )
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics.validate_scientific_rule_prediction_artifact_v1(
                run.rule_prediction_artifact
            )

    def test_real_entrypoint_fails_before_object_inspection(self) -> None:
        class Explosive:
            def __getattribute__(self, name: str) -> object:
                raise AssertionError("real object was inspected")

        value = Explosive()
        with self.assertRaisesRegex(
            UtilityEvaluatorV1Error, "REAL_UTILITY_EXECUTION_NOT_AUTHORIZED"
        ):
            evaluator.run_real_utility_evaluator_v1(
                execution_authorization=value,
                main_locator=value,
                supplement_locator=value,
                hai_input=value,
                labels=value,
            )

    def test_claim_boundary_remains_non_scientific(self) -> None:
        claim = evaluator.evaluator_claim_boundary_v1()
        self.assertEqual(claim["real_utility_status"], "NOT_EXECUTED")
        self.assertFalse(claim["real_utility_execution_authorized"])
        self.assertFalse(claim["scientific_claims_authorized"])


if __name__ == "__main__":
    unittest.main()
