from __future__ import annotations

from dataclasses import replace
import json
import math
from pathlib import Path
from types import SimpleNamespace
import unittest

import paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 as evaluator
from paperworks.v6.task039e3_r2r_utility_evaluator_census_v1 import (
    COMBINED_SOURCE_CENSUS_CONTRACT_HASH,
    CROSS_SOURCE_ISOLATION_POLICY_HASH,
    FULL_CENSUS_DENOMINATOR_POLICY,
    SOURCE_CENSUS_EVENT_POLICY_HASH,
    enumerate_full_census_v1,
    validate_full_census_result_v1,
    validate_opportunity_envelope_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_input_v1 import (
    build_synthetic_feature_frame_v1,
    feature_series_v1,
    feature_value_v1,
    load_authorized_hai_feature_frame_v1,
    validate_synthetic_feature_frame_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import (
    SYNTHETIC_CONTRACT_ONLY,
    UtilityEvaluatorV1Error,
)
from paperworks.v6.task039e3_r2r_utility_protocol_v3 import UTILITY_SOURCE_UNIVERSE_V3
from paperworks.v6 import task039e3_r2r_utility_protocol_v4 as v4
import paperworks.v6.task039e3_r2r_utility_source_census_supplement_v1 as supplement


ROOT = Path(__file__).resolve().parents[1]


def load(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class UtilityEvaluatorInputCensusTests(unittest.TestCase):
    """37 invalid cases plus deterministic positive synthetic paths."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.authority = v4.build_utility_protocol_v4_canonical_authority(
            executable_equivalence=load(
                "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"
            ),
            evidence_manifest=load(
                "docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json"
            ),
            dataset_manifest=load("docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json"),
            csv_structure_report=load("docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json"),
            c0_config=load("configs/v6/task039c0_candidate_discovery_protocol.json"),
            br2_config=load("configs/v6/task039br2_hai_continuous_step_feasibility.json"),
            materialized_audit_receipt=load(
                "docs/task_reports/TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZED_RECEIPT.json"
            ),
        )
        cls.bundle = evaluator.build_evaluator_authority_bundle_v1(cls.authority)
        cls.features = cls.authority.feature_schema.union_features
        cls.main_rule = cls.authority.rule_descriptors[0]
        main = []
        for rule in cls.authority.rule_descriptors:
            for role, reference in rule.numeric_reference_bindings:
                value: int | float
                if role == "source_step_threshold":
                    value = 1.0
                elif role == "source_stability_tolerance":
                    value = 0.0
                elif role == "target_noise_scale":
                    value = 1.0
                else:
                    value = {
                        "source_pre_window_seconds": 5,
                        "source_post_window_seconds": 5,
                        "minimum_source_stability_fraction": 0.8,
                        "source_refractory_seconds": 10,
                        "cross_source_isolation_radius_seconds": 2,
                        "target_baseline_window_seconds": 5,
                        "target_response_window_seconds": 3,
                    }[role]
                main.append(
                    evaluator.SyntheticNumericRecordV1(
                        "SYNTHETIC_MAIN_420",
                        rule.source,
                        rule.relation_binding_hash,
                        role,
                        reference,
                        value,
                    )
                )
        cls.main_records = tuple(main)
        cls.supplement_records = tuple(
            evaluator.SyntheticNumericRecordV1(
                evaluator.SUPPLEMENT_PURPOSE,
                source,
                None,
                role,
                supplement.supplement_reference_identity_v1(source, role),
                1.0 if role == "source_step_threshold" else 0.0,
            )
            for source in evaluator.SUPPLEMENT_SOURCES
            for role in evaluator.SOURCE_CENSUS_ROLES
        )

    def resolver(self):
        return evaluator.build_synthetic_numeric_resolver_v1(
            self.bundle,
            self.main_records,
            self.supplement_records,
        )

    def matrix(
        self,
        *steps: tuple[str, int, float],
        row_count: int = 25,
    ) -> tuple[tuple[float, ...], ...]:
        values = [[0.0 for _ in self.features] for _ in range(row_count)]
        for feature, start, level in steps:
            column = self.features.index(feature)
            for index in range(start, row_count):
                values[index][column] = float(level)
        return tuple(tuple(row) for row in values)

    def frame(self, *steps: tuple[str, int, float]):
        return build_synthetic_feature_frame_v1(
            self.bundle,
            source_file_identity="hai-test1.csv",
            start_physical_row_index=100,
            rows=self.matrix(*steps),
        )

    def matching_step(self, source: str | None = None) -> tuple[str, int, float]:
        rule = self.main_rule
        if source is not None:
            candidates = [item for item in self.authority.rule_descriptors if item.source == source]
            self.assertTrue(candidates)
            rule = candidates[0]
        return (rule.source, 10, 2.0 if rule.source_direction == "step_up" else -2.0)

    def test_exact_synthetic_schema_and_value_access(self) -> None:
        frame = self.frame(self.matching_step())
        self.assertEqual(validate_synthetic_feature_frame_v1(frame, self.bundle), frame.frame_hash)
        self.assertEqual(frame.execution_mode, SYNTHETIC_CONTRACT_ONLY)
        self.assertEqual(len(frame.ordered_features), 22)
        self.assertEqual(feature_series_v1(frame, self.bundle, self.main_rule.source)[-1], self.matching_step()[2])
        self.assertEqual(
            feature_value_v1(
                frame,
                self.bundle,
                physical_row_index=124,
                feature=self.main_rule.source,
            ),
            self.matching_step()[2],
        )

    def test_input_constructor_scalar_and_container_rejections_12_cases(self) -> None:
        valid = self.matrix()
        cases = (
            {"rows": list(valid)},
            {"rows": (list(valid[0]),) + valid[1:]},
            {"rows": ((0,) + valid[0][1:],) + valid[1:]},
            {"rows": ((True,) + valid[0][1:],) + valid[1:]},
            {"rows": ((math.nan,) + valid[0][1:],) + valid[1:]},
            {"rows": ((math.inf,) + valid[0][1:],) + valid[1:]},
            {"rows": tuple(row[:-1] for row in valid)},
            {"rows": tuple(row + (0.0,) for row in valid)},
            {"source_file_identity": "hai-train1.csv"},
            {"start_physical_row_index": -1},
            {"start_physical_row_index": 53_990},
            {"start_physical_row_index": True},
        )
        for override in cases:
            kwargs = {
                "source_file_identity": "hai-test1.csv",
                "start_physical_row_index": 100,
                "rows": valid,
                **override,
            }
            with self.subTest(override=override), self.assertRaises(UtilityEvaluatorV1Error):
                build_synthetic_feature_frame_v1(self.bundle, **kwargs)

    def test_real_loader_fails_before_any_path_authority_1_case(self) -> None:
        with self.assertRaisesRegex(
            UtilityEvaluatorV1Error,
            "REAL_HAI_EXECUTION_AUTHORIZATION_UNAVAILABLE",
        ):
            load_authorized_hai_feature_frame_v1(
                self.bundle,
                execution_authorization=object(),
                dataset_manifest_identity="wrong",
                split_identity="wrong",
                source_file_identity="wrong",
                expected_file_identity="wrong",
            )

    def test_frame_mutations_rejected_11_cases(self) -> None:
        frame = self.frame()
        row = frame.rows[0]
        row_cases = (
            replace(row, physical_row_index=row.physical_row_index + 1),
            replace(row, timestamp_second=row.timestamp_second + 1),
            replace(row, feature_values=tuple(reversed(row.feature_values))),
            replace(row, feature_values=((row.feature_values[0][0], math.nan),) + row.feature_values[1:]),
            replace(row, row_identity="b" * 64),
        )
        cases = (
            replace(frame, dataset_manifest_identity="wrong"),
            replace(frame, split_identity="wrong"),
            replace(frame, source_file_identity="hai-test2.csv"),
            replace(frame, feature_schema_authority_hash="b" * 64),
            replace(frame, ordered_features=frame.ordered_features[:-1]),
            *(replace(frame, rows=(candidate,) + frame.rows[1:]) for candidate in row_cases),
            replace(frame, frame_hash="b" * 64),
        )
        for candidate in cases:
            with self.subTest(field_difference=True), self.assertRaises(UtilityEvaluatorV1Error):
                validate_synthetic_feature_frame_v1(candidate, self.bundle)

    def test_exact_12_source_census_and_common_only_expansion(self) -> None:
        frame = self.frame(self.matching_step())
        resolver = self.resolver()
        result = enumerate_full_census_v1(frame, self.bundle, resolver)
        self.assertEqual(validate_full_census_result_v1(result, frame, self.bundle, resolver), result.census_hash)
        self.assertEqual(len(UTILITY_SOURCE_UNIVERSE_V3), 12)
        self.assertEqual(result.denominator_policy, FULL_CENSUS_DENOMINATOR_POLICY)
        self.assertGreater(result.raw_source_event_count, 0)
        self.assertEqual(result.retained_source_event_count, 1)
        self.assertEqual(result.isolated_source_event_count, 1)
        self.assertGreater(len(result.relation_opportunities), 0)
        self.assertTrue(
            all(item.canonical_opportunity.source == self.main_rule.source for item in result.relation_opportunities)
        )

    def test_supplement_pp04_overlap_prevents_false_main_isolation(self) -> None:
        main = self.matching_step()
        frame = self.frame(main, ("P1_PP04", 10, 2.0))
        result = enumerate_full_census_v1(frame, self.bundle, self.resolver())
        self.assertEqual(result.retained_source_event_count, 2)
        self.assertEqual(result.isolated_source_event_count, 0)
        self.assertEqual(result.relation_opportunities, ())

    def test_supplement_fcv02z_overlap_prevents_false_main_isolation(self) -> None:
        main = self.matching_step()
        frame = self.frame(main, ("P1_FCV02Z", 10, 2.0))
        result = enumerate_full_census_v1(frame, self.bundle, self.resolver())
        self.assertEqual(result.retained_source_event_count, 2)
        self.assertEqual(result.isolated_source_event_count, 0)
        self.assertEqual(result.relation_opportunities, ())

    def test_supplement_only_event_never_creates_common_relation(self) -> None:
        frame = self.frame(("P1_PP04", 10, 2.0))
        result = enumerate_full_census_v1(frame, self.bundle, self.resolver())
        self.assertEqual(result.retained_source_event_count, 1)
        self.assertEqual(result.isolated_source_event_count, 1)
        self.assertEqual(result.relation_opportunities, ())

    def test_refractory_retention_and_event_identity_are_deterministic(self) -> None:
        frame = self.frame(self.matching_step())
        first = enumerate_full_census_v1(frame, self.bundle, self.resolver())
        second = enumerate_full_census_v1(frame, self.bundle, self.resolver())
        self.assertEqual(first, second)
        self.assertGreater(first.raw_source_event_count, first.retained_source_event_count)
        self.assertEqual(first.retained_source_event_count, 1)

    def test_resolver_and_authority_rejections_7_cases(self) -> None:
        frame = self.frame()
        bad_bundles = (
            replace(self.bundle, combined_source_census_contract_hash="b" * 64),
            replace(self.bundle, source_census_event_policy_hash="b" * 64),
            replace(self.bundle, cross_source_isolation_policy_hash="b" * 64),
        )
        for bundle in bad_bundles:
            with self.subTest(bundle=True), self.assertRaises(UtilityEvaluatorV1Error):
                enumerate_full_census_v1(frame, bundle, self.resolver())
        mutations = ("validated", "threshold_type", "tolerance_domain", "missing_source")
        for mutation in mutations:
            resolver = self.resolver()
            source = UTILITY_SOURCE_UNIVERSE_V3[0]
            if mutation == "validated":
                resolver.validated = False
            elif mutation == "threshold_type":
                resolver._source_values[(source, "source_step_threshold")] = 1  # type: ignore[assignment]
            elif mutation == "tolerance_domain":
                resolver._source_values[(source, "source_stability_tolerance")] = -1.0
            else:
                del resolver._source_values[(source, "source_step_threshold")]
            with self.subTest(resolver=mutation), self.assertRaises(UtilityEvaluatorV1Error):
                enumerate_full_census_v1(frame, self.bundle, resolver)

    def test_canonical_looking_fake_bundle_and_resolver_rejected_2_cases(self) -> None:
        frame = self.frame()
        fake_bundle = SimpleNamespace(**{
            field: getattr(self.bundle, field)
            for field in self.bundle.__dataclass_fields__
        })
        fake_bundle.bundle_hash = self.bundle.bundle_hash
        with self.assertRaises(UtilityEvaluatorV1Error):
            validate_synthetic_feature_frame_v1(frame, fake_bundle)
        fake_resolver = SimpleNamespace(
            validated=True,
            source_census_value=lambda _source, role: 1.0 if role == "source_step_threshold" else 0.0,
        )
        with self.assertRaises(UtilityEvaluatorV1Error):
            enumerate_full_census_v1(frame, self.bundle, fake_resolver)

    def test_caller_census_control_parameters_absent_6_cases(self) -> None:
        frame = self.frame()
        for key, value in (
            ("source_subset", UTILITY_SOURCE_UNIVERSE_V3[:9]),
            ("relation_subset", self.authority.rule_descriptors[:39]),
            ("opportunity_list", ()),
            ("sample_n", 1),
            ("max_opportunities", 1),
            ("denominator", 1),
        ):
            with self.subTest(key=key), self.assertRaises(TypeError):
                enumerate_full_census_v1(frame, self.bundle, self.resolver(), **{key: value})

    def test_census_and_envelope_mutations_rejected_4_cases(self) -> None:
        frame = self.frame(self.matching_step())
        resolver = self.resolver()
        result = enumerate_full_census_v1(frame, self.bundle, resolver)
        envelope = result.relation_opportunities[0]
        validate_opportunity_envelope_v1(envelope, result, frame, self.bundle, resolver)
        cases = (
            replace(result, raw_source_event_count=result.raw_source_event_count + 1),
            replace(result, relation_opportunities=result.relation_opportunities[1:]),
            replace(result, denominator_policy="CALLER_DENOMINATOR"),
            replace(result, census_hash="b" * 64),
        )
        for candidate in cases:
            with self.subTest(result_mutation=True), self.assertRaises(UtilityEvaluatorV1Error):
                validate_full_census_result_v1(candidate, frame, self.bundle, resolver)
        forged = replace(envelope, isolated_source_event_identity="b" * 64, envelope_hash="c" * 64)
        with self.assertRaises(UtilityEvaluatorV1Error):
            validate_opportunity_envelope_v1(forged, result, frame, self.bundle, resolver)


if __name__ == "__main__":
    unittest.main()
