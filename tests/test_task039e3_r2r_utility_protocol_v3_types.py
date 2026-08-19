from __future__ import annotations

import json
from pathlib import Path
import unittest

from paperworks.v6.task039e3_r2r_utility_protocol_v3 import (
    AcceptedRelationBindingV3,
    ApplicableRuleEvaluationOpportunityV3,
    AvailableSourceWindowV3,
    AvailableTargetWindowV3,
    NumericParameterV3,
    P1UtilityFeatureSchemaV3,
    UnavailableSourceContextV3,
    UnavailableTargetContextV3,
    UTILITY_SOURCE_UNIVERSE_V3,
    UtilityProtocolV3Error,
    accepted_relation_binding_v3,
    build_p1_utility_feature_schema_v3,
    evaluate_target_response_v3,
    executable_authority_v3,
    form_source_opportunity_v3,
    parse_raw_feature_tokens_v3,
    parse_raw_label_tokens_v3,
    validate_selected_feature_header_v3,
)


ROOT = Path(__file__).resolve().parents[1]


def load(name: str) -> dict[str, object]:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class FeatureSchemaAndTypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.equivalence = load(
            "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"
        )
        cls.authority = executable_authority_v3(cls.equivalence)
        cls.schema = build_p1_utility_feature_schema_v3(
            dataset_manifest=load("docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json"),
            csv_structure_report=load("docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json"),
            c0_config=load("configs/v6/task039c0_candidate_discovery_protocol.json"),
            br2_config=load("configs/v6/task039br2_hai_continuous_step_feasibility.json"),
            executable_equivalence=cls.equivalence,
        )
        first = sorted(cls.authority.signatures_by_relation)[0]
        cls.relation = accepted_relation_binding_v3(cls.authority, first, "COMMON-42")

    def test_feature_schema_exact_scope_and_roundtrip(self) -> None:
        self.assertEqual(len(self.schema.feature_entries), 22)
        self.assertEqual(self.schema.required_source_count, 12)
        self.assertEqual(self.schema.required_target_count, 10)
        self.assertEqual(
            {entry.feature_name for entry in self.schema.feature_entries if entry.role == "source"},
            set(UTILITY_SOURCE_UNIVERSE_V3),
        )
        self.assertTrue(all(entry.unit_identity is None for entry in self.schema.feature_entries))
        self.assertTrue(all(entry.expected_logical_type == "finite_real_scalar" for entry in self.schema.feature_entries))
        self.assertTrue(all(entry.missing_value_policy == "PROHIBITED_NO_AUTHORIZED_MISSING_TOKEN" for entry in self.schema.feature_entries))
        self.assertEqual(P1UtilityFeatureSchemaV3.from_mapping(self.schema.to_dict()), self.schema)

    def test_missing_or_ambiguous_metadata_authority_rejects(self) -> None:
        c0 = load("configs/v6/task039c0_candidate_discovery_protocol.json")
        c0["common_universe"]["source_identities"] = c0["common_universe"]["source_identities"][:-1]
        with self.assertRaises(UtilityProtocolV3Error):
            build_p1_utility_feature_schema_v3(
                dataset_manifest=load("docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json"),
                csv_structure_report=load("docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json"),
                c0_config=c0,
                br2_config=load("configs/v6/task039br2_hai_continuous_step_feasibility.json"),
                executable_equivalence=self.equivalence,
            )

    def test_raw_parser_is_explicit_and_internal_values_are_canonical(self) -> None:
        feature = self.relation.source
        self.assertEqual(parse_raw_feature_tokens_v3(feature, ("1", "-2.5", "3e-2"), self.schema), (1.0, -2.5, 0.03))
        for bad in (True, False, None, 1.0, "abc", "NaN", "Inf", " 1", "1 ", ""):
            with self.subTest(bad=bad), self.assertRaises(UtilityProtocolV3Error):
                parse_raw_feature_tokens_v3(feature, (bad,), self.schema)
        with self.assertRaises(UtilityProtocolV3Error):
            parse_raw_feature_tokens_v3("P1_UNKNOWN", ("1",), self.schema)

    def test_selected_header_exact_missing_duplicate_unknown(self) -> None:
        expected = ("timestamp", *(entry.feature_name for entry in self.schema.feature_entries))
        self.assertEqual(validate_selected_feature_header_v3(expected, self.schema), expected)
        for bad in (expected[:-1], (*expected, "P1_UNKNOWN"), (expected[0], expected[1], *expected[1:])):
            with self.assertRaises(UtilityProtocolV3Error):
                validate_selected_feature_header_v3(bad, self.schema)

    def test_label_parser_accepts_only_exact_raw_tokens(self) -> None:
        self.assertEqual(parse_raw_label_tokens_v3(("0", "1", "0")), (0, 1, 0))
        for bad in (True, False, 0, 1, 0.0, 1.0, "2", "-1", None, float("nan")):
            with self.subTest(bad=bad), self.assertRaises(UtilityProtocolV3Error):
                parse_raw_label_tokens_v3((bad,))

    def test_internal_windows_reject_bool_string_none_complex_nonfinite_and_wrong_lengths(self) -> None:
        good = (0.0,) * 5
        AvailableSourceWindowV3(self.relation.source, good, good)
        cases = (
            (True,) * 5,
            ("1.5",) * 5,
            ("abc",) * 5,
            (None,) * 5,
            (1 + 2j,) * 5,
            (float("nan"),) * 5,
            (float("inf"),) * 5,
            (0.0,) * 4,
            (0.0,) * 6,
            [0.0] * 5,
        )
        for case in cases:
            with self.subTest(case=case), self.assertRaises(UtilityProtocolV3Error):
                AvailableSourceWindowV3(self.relation.source, case, good)  # type: ignore[arg-type]
        for response in ((0.0,) * 2, (0.0,) * 4, ("1.5",) * 3):
            with self.assertRaises(UtilityProtocolV3Error):
                AvailableTargetWindowV3(self.relation.target, good, response)  # type: ignore[arg-type]

    def test_scalar_and_state_mutations_fail_closed(self) -> None:
        for bad in (True, False, 1.0, "10"):
            with self.subTest(index=bad), self.assertRaises(UtilityProtocolV3Error):
                ApplicableRuleEvaluationOpportunityV3(
                    self.relation.relation_binding_hash,
                    self.relation.executable_signature_hash,
                    "COMMON-42",
                    "hai-test1.csv",
                    self.relation.source,
                    self.relation.target,
                    bad,  # type: ignore[arg-type]
                    self.relation.selected_horizon_seconds,
                )
        with self.assertRaises(UtilityProtocolV3Error):
            AcceptedRelationBindingV3(
                self.relation.relation_binding_hash,
                self.relation.executable_signature_hash,
                "COMMON-42",
                "P1_UNKNOWN",
                self.relation.target,
                self.relation.expected_source_direction,
                self.relation.expected_target_direction,
                self.relation.selected_horizon_seconds,
            )
        with self.assertRaises(UtilityProtocolV3Error):
            AvailableSourceWindowV3(self.relation.source, (0.0,) * 5, (1.0,) * 5, "unknown")
        with self.assertRaises(UtilityProtocolV3Error):
            UnavailableTargetContextV3(self.relation.target, "unknown")
        for bad in (float("nan"), float("inf"), -1.0, True, "1"):
            with self.subTest(parameter=bad), self.assertRaises(UtilityProtocolV3Error):
                NumericParameterV3("source_step_threshold", bad)  # type: ignore[arg-type]
        with self.assertRaises(UtilityProtocolV3Error):
            NumericParameterV3("unknown_role", 1.0)

    def _retained_map(self, index: int = 100) -> dict[str, tuple[int, ...]]:
        result = {source: () for source in UTILITY_SOURCE_UNIVERSE_V3}
        result[self.relation.source] = (index,)
        return result

    @staticmethod
    def _bypass_source(values: object, feature: str) -> AvailableSourceWindowV3:
        result = object.__new__(AvailableSourceWindowV3)
        object.__setattr__(result, "feature_identity", feature)
        object.__setattr__(result, "pre_values", values)
        object.__setattr__(result, "post_values", values)
        object.__setattr__(result, "state", "available_source_window")
        return result

    @staticmethod
    def _bypass_target(values: object, feature: str) -> AvailableTargetWindowV3:
        result = object.__new__(AvailableTargetWindowV3)
        object.__setattr__(result, "feature_identity", feature)
        object.__setattr__(result, "baseline_values", values)
        object.__setattr__(result, "response_values", values)
        object.__setattr__(result, "state", "available_target_window")
        return result

    def test_source_boundary_cannot_mask_malformed_values(self) -> None:
        malformed = self._bypass_source(("1.5",) * 5, self.relation.source)
        with self.assertRaises(UtilityProtocolV3Error):
            form_source_opportunity_v3(
                relation=self.relation,
                authority=self.authority,
                file_identity="hai-test1.csv",
                physical_row_count=54_000,
                event_index=4,
                source_context=malformed,
                source_step_threshold=NumericParameterV3("source_step_threshold", 0.5),
                source_stability_tolerance=NumericParameterV3("source_stability_tolerance", 0.0),
                retained_events_by_source=self._retained_map(4),
            )
        valid = AvailableSourceWindowV3(self.relation.source, (0.0,) * 5, (1.0,) * 5)
        result = form_source_opportunity_v3(
            relation=self.relation,
            authority=self.authority,
            file_identity="hai-test1.csv",
            physical_row_count=54_000,
            event_index=4,
            source_context=valid,
            source_step_threshold=NumericParameterV3("source_step_threshold", 0.5),
            source_stability_tolerance=NumericParameterV3("source_stability_tolerance", 0.0),
            retained_events_by_source=self._retained_map(4),
        )
        self.assertEqual(result.state, "source_opportunity_not_formed")

    def _opportunity(self, index: int) -> ApplicableRuleEvaluationOpportunityV3:
        return ApplicableRuleEvaluationOpportunityV3(
            self.relation.relation_binding_hash,
            self.relation.executable_signature_hash,
            "COMMON-42",
            "hai-test1.csv",
            self.relation.source,
            self.relation.target,
            index,
            self.relation.selected_horizon_seconds,
        )

    def test_target_file_and_split_boundaries_cannot_mask_malformed_values(self) -> None:
        malformed = self._bypass_target((True,) * 5, self.relation.target)
        near_end = self._opportunity(53_999)
        for within_split in (True, False):
            with self.subTest(within_split=within_split), self.assertRaises(UtilityProtocolV3Error):
                evaluate_target_response_v3(
                    near_end,
                    relation=self.relation,
                    authority=self.authority,
                    target_context=malformed,
                    physical_row_count=54_000,
                    within_split=within_split,
                    target_noise_scale=NumericParameterV3("target_noise_scale", 0.5),
                )
        middle = self._opportunity(100)
        with self.assertRaises(UtilityProtocolV3Error):
            evaluate_target_response_v3(
                middle,
                relation=self.relation,
                authority=self.authority,
                target_context=malformed,
                physical_row_count=54_000,
                within_split=False,
                target_noise_scale=NumericParameterV3("target_noise_scale", 0.5),
            )
        valid = AvailableTargetWindowV3(self.relation.target, (0.0,) * 5, (1.0,) * 3)
        file_result = evaluate_target_response_v3(
            near_end,
            relation=self.relation,
            authority=self.authority,
            target_context=valid,
            physical_row_count=54_000,
            within_split=True,
            target_noise_scale=NumericParameterV3("target_noise_scale", 0.5),
        )
        split_result = evaluate_target_response_v3(
            middle,
            relation=self.relation,
            authority=self.authority,
            target_context=valid,
            physical_row_count=54_000,
            within_split=False,
            target_noise_scale=NumericParameterV3("target_noise_scale", 0.5),
        )
        self.assertEqual((file_result.target_evaluation_state, file_result.abstention_reason), ("abstain", "file_boundary"))
        self.assertEqual((split_result.target_evaluation_state, split_result.abstention_reason), ("abstain", "split_boundary"))

    def test_tagged_unavailable_contexts_have_no_value_payload(self) -> None:
        source = UnavailableSourceContextV3(self.relation.source, "insufficient_source_pre_window")
        target = UnavailableTargetContextV3(self.relation.target, "incomplete_target_response_window")
        self.assertFalse(hasattr(source, "pre_values"))
        self.assertFalse(hasattr(source, "post_values"))
        self.assertFalse(hasattr(target, "baseline_values"))
        self.assertFalse(hasattr(target, "response_values"))
        result = evaluate_target_response_v3(
            self._opportunity(100),
            relation=self.relation,
            authority=self.authority,
            target_context=target,
            physical_row_count=54_000,
            within_split=True,
            target_noise_scale=NumericParameterV3("target_noise_scale", 0.5),
        )
        self.assertEqual(result.target_evaluation_state, "abstain")
        self.assertEqual(result.abstention_reason, "incomplete_target_response_window")
        self.assertFalse(result.alarm_emitted)

    def test_wrong_parameter_role_and_bad_universe_reject_before_state(self) -> None:
        valid = AvailableSourceWindowV3(self.relation.source, (0.0,) * 5, (1.0,) * 5)
        with self.assertRaises(UtilityProtocolV3Error):
            form_source_opportunity_v3(
                relation=self.relation,
                authority=self.authority,
                file_identity="hai-test1.csv",
                physical_row_count=54_000,
                event_index=100,
                source_context=valid,
                source_step_threshold=NumericParameterV3("target_noise_scale", 0.5),
                source_stability_tolerance=NumericParameterV3("source_stability_tolerance", 0.0),
                retained_events_by_source=self._retained_map(),
            )
        incomplete = self._retained_map()
        incomplete.pop(next(iter(incomplete)))
        with self.assertRaises(UtilityProtocolV3Error):
            form_source_opportunity_v3(
                relation=self.relation,
                authority=self.authority,
                file_identity="hai-test1.csv",
                physical_row_count=54_000,
                event_index=100,
                source_context=valid,
                source_step_threshold=NumericParameterV3("source_step_threshold", 0.5),
                source_stability_tolerance=NumericParameterV3("source_stability_tolerance", 0.0),
                retained_events_by_source=incomplete,
            )


if __name__ == "__main__":
    unittest.main()
