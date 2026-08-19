from __future__ import annotations

import copy
import inspect
import json
import math
from pathlib import Path
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_utility_protocol_v3 import (
    AcceptedRelationBindingV3,
    ApplicableRuleEvaluationOpportunityV3,
    AvailableSourceWindowV3,
    AvailableTargetWindowV3,
    FullCensusEnumerationV3,
    NumericParameterV3,
    P1UtilityFeatureSchemaV3,
    TargetEvaluationOutcomeV3,
    UTILITY_SOURCE_UNIVERSE_V3,
    UnavailableSourceContextV3,
    UnavailableTargetContextV3,
    UtilityProtocolV3Error,
    accepted_relation_binding_v3,
    build_p1_utility_feature_schema_v3,
    evaluate_target_response_v3,
    executable_authority_v3,
    form_source_opportunity_v3,
    opportunity_record_v3,
    parse_raw_feature_tokens_v3,
    parse_raw_label_tokens_v3,
)


ROOT = Path(__file__).resolve().parents[1]
ROW_COUNT = 54_000


def load(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class IndependentTypeAndStateAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.equivalence = load(
            "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"
        )
        cls.authority = executable_authority_v3(cls.equivalence)
        cls.relation_hash = sorted(cls.authority.signatures_by_relation)[0]
        cls.relation = accepted_relation_binding_v3(
            cls.authority, cls.relation_hash, "COMMON-42"
        )
        cls.schema = build_p1_utility_feature_schema_v3(
            dataset_manifest=load("docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json"),
            csv_structure_report=load("docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json"),
            c0_config=load("configs/v6/task039c0_candidate_discovery_protocol.json"),
            br2_config=load("configs/v6/task039br2_hai_continuous_step_feasibility.json"),
            executable_equivalence=cls.equivalence,
        )

    def _retained_map(self, index: int | None = None) -> dict[str, tuple[int, ...]]:
        return {
            source: (index,) if source == self.relation.source and index is not None else ()
            for source in UTILITY_SOURCE_UNIVERSE_V3
        }

    def _opportunity(self, index: int = 100) -> ApplicableRuleEvaluationOpportunityV3:
        return ApplicableRuleEvaluationOpportunityV3(
            self.relation.relation_binding_hash,
            self.relation.executable_signature_hash,
            self.relation.portfolio_identity,
            "hai-test1.csv",
            self.relation.source,
            self.relation.target,
            index,
            self.relation.selected_horizon_seconds,
        )

    def test_raw_feature_parser_accepts_exact_decimal_grammar(self) -> None:
        tokens = ("0", "1", "-1", "+1.5", "0.25", ".5", "1.", "1e3", "-2.5E-4")
        observed = parse_raw_feature_tokens_v3(
            self.schema.feature_entries[0].feature_name, tokens, self.schema
        )
        self.assertEqual(
            observed,
            (0.0, 1.0, -1.0, 1.5, 0.25, 0.5, 1.0, 1000.0, -0.00025),
        )
        self.assertTrue(all(type(value) is float and math.isfinite(value) for value in observed))

    def test_raw_feature_parser_rejects_malformed_or_non_string_values(self) -> None:
        invalid = (
            "abc", "", " ", "NaN", "nan", "Inf", "-Inf", "True", "False",
            None, True, False, 1, 1.0, 1 + 2j,
        )
        feature = self.schema.feature_entries[0].feature_name
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(UtilityProtocolV3Error):
                parse_raw_feature_tokens_v3(feature, (value,), self.schema)

    def test_raw_label_parser_is_exact_and_has_no_coercion(self) -> None:
        self.assertEqual(parse_raw_label_tokens_v3(("0", "1")), (0, 1))
        for value in (0, 1, True, False, "0.0", "1.0", "-1", "2", "", None, "NaN"):
            with self.subTest(value=value), self.assertRaises(UtilityProtocolV3Error):
                parse_raw_label_tokens_v3((value,))

    def test_internal_windows_require_exact_tuple_float_finite_contract(self) -> None:
        source = self.relation.source
        target = self.relation.target
        AvailableSourceWindowV3(source, (0.0,) * 5, (1.0,) * 5)
        AvailableTargetWindowV3(target, (0.0,) * 5, (1.0,) * 3)
        invalid_values = (True, 1, "1.5", None, float("nan"), float("inf"), 1 + 2j)
        for value in invalid_values:
            with self.subTest(value=value), self.assertRaises(UtilityProtocolV3Error):
                AvailableSourceWindowV3(source, (value,) * 5, (1.0,) * 5)
            with self.subTest(value=value), self.assertRaises(UtilityProtocolV3Error):
                AvailableTargetWindowV3(target, (0.0,) * 5, (value,) * 3)
        for values in ((0.0,) * 4, (0.0,) * 6, [0.0] * 5):
            with self.subTest(values=values), self.assertRaises(UtilityProtocolV3Error):
                AvailableSourceWindowV3(source, values, (1.0,) * 5)  # type: ignore[arg-type]

    def test_discriminated_unavailable_contexts_have_no_value_payload(self) -> None:
        source_signature = inspect.signature(UnavailableSourceContextV3)
        target_signature = inspect.signature(UnavailableTargetContextV3)
        self.assertNotIn("pre_values", source_signature.parameters)
        self.assertNotIn("post_values", source_signature.parameters)
        self.assertNotIn("baseline_values", target_signature.parameters)
        self.assertNotIn("response_values", target_signature.parameters)
        with self.assertRaises((TypeError, UtilityProtocolV3Error)):
            UnavailableSourceContextV3(
                self.relation.source, "insufficient_source_pre_window", (0.0,) * 5
            )
        with self.assertRaises((TypeError, UtilityProtocolV3Error)):
            UnavailableTargetContextV3(
                self.relation.target, "file_boundary", (0.0,) * 3
            )
        with self.assertRaises(TypeError):
            AvailableSourceWindowV3(self.relation.source)  # type: ignore[call-arg]
        with self.assertRaises(TypeError):
            AvailableTargetWindowV3(self.relation.target)  # type: ignore[call-arg]

    def test_invalid_source_payload_cannot_be_masked_by_boundary(self) -> None:
        with self.assertRaises(UtilityProtocolV3Error):
            invalid = AvailableSourceWindowV3(
                self.relation.source, ("1.5",) * 5, (1.0,) * 5  # type: ignore[arg-type]
            )
            form_source_opportunity_v3(
                relation=self.relation,
                authority=self.authority,
                file_identity="hai-test1.csv",
                physical_row_count=ROW_COUNT,
                event_index=4,
                source_context=invalid,
                source_step_threshold=NumericParameterV3("source_step_threshold", 0.5),
                source_stability_tolerance=NumericParameterV3("source_stability_tolerance", 0.0),
                retained_events_by_source=self._retained_map(),
            )
        valid = form_source_opportunity_v3(
            relation=self.relation,
            authority=self.authority,
            file_identity="hai-test1.csv",
            physical_row_count=ROW_COUNT,
            event_index=4,
            source_context=UnavailableSourceContextV3(
                self.relation.source, "insufficient_source_pre_window"
            ),
            source_step_threshold=NumericParameterV3("source_step_threshold", 0.5),
            source_stability_tolerance=NumericParameterV3("source_stability_tolerance", 0.0),
            retained_events_by_source=self._retained_map(),
        )
        self.assertEqual(valid.state, "source_opportunity_not_formed")

    def test_invalid_target_payload_cannot_be_masked_by_file_or_split_boundary(self) -> None:
        file_boundary = self._opportunity(ROW_COUNT - 1)
        interior = self._opportunity(100)
        for opportunity, within_split in ((file_boundary, True), (interior, False)):
            with self.subTest(within_split=within_split), self.assertRaises(UtilityProtocolV3Error):
                invalid = AvailableTargetWindowV3(
                    self.relation.target, (0.0,) * 5, ("abc",) * 3  # type: ignore[arg-type]
                )
                evaluate_target_response_v3(
                    opportunity,
                    relation=self.relation,
                    authority=self.authority,
                    target_context=invalid,
                    physical_row_count=ROW_COUNT,
                    within_split=within_split,
                    target_noise_scale=NumericParameterV3("target_noise_scale", 0.5),
                )
        observed_file = evaluate_target_response_v3(
            file_boundary,
            relation=self.relation,
            authority=self.authority,
            target_context=UnavailableTargetContextV3(self.relation.target, "file_boundary"),
            physical_row_count=ROW_COUNT,
            within_split=True,
            target_noise_scale=NumericParameterV3("target_noise_scale", 0.5),
        )
        observed_split = evaluate_target_response_v3(
            interior,
            relation=self.relation,
            authority=self.authority,
            target_context=UnavailableTargetContextV3(self.relation.target, "split_boundary"),
            physical_row_count=ROW_COUNT,
            within_split=False,
            target_noise_scale=NumericParameterV3("target_noise_scale", 0.5),
        )
        self.assertEqual((observed_file.target_evaluation_state, observed_file.abstention_reason), ("abstain", "file_boundary"))
        self.assertEqual((observed_split.target_evaluation_state, observed_split.abstention_reason), ("abstain", "split_boundary"))

    def test_complete_target_context_reaches_scientific_evaluation(self) -> None:
        baseline = (0.0,) * 5
        if self.relation.expected_target_direction == "increase":
            response = (2.0,) * 3
        else:
            response = (-2.0,) * 3
        observed = evaluate_target_response_v3(
            self._opportunity(100),
            relation=self.relation,
            authority=self.authority,
            target_context=AvailableTargetWindowV3(self.relation.target, baseline, response),
            physical_row_count=ROW_COUNT,
            within_split=True,
            target_noise_scale=NumericParameterV3("target_noise_scale", 0.5),
        )
        self.assertEqual(observed.target_evaluation_state, "evaluated_expected_response")
        self.assertEqual(observed.decision_index, 100 + self.relation.selected_horizon_seconds + 2)

    def test_parameter_and_scalar_mutations_fail_closed(self) -> None:
        for value in (True, 1.0, "10"):
            with self.subTest(index=value), self.assertRaises(UtilityProtocolV3Error):
                ApplicableRuleEvaluationOpportunityV3(
                    self.relation.relation_binding_hash,
                    self.relation.executable_signature_hash,
                    self.relation.portfolio_identity,
                    "hai-test1.csv",
                    self.relation.source,
                    self.relation.target,
                    value,  # type: ignore[arg-type]
                    self.relation.selected_horizon_seconds,
                )
        for role, value in (
            ("source_step_threshold", 0.0),
            ("source_step_threshold", -1.0),
            ("source_stability_tolerance", -1.0),
            ("target_noise_scale", 0.0),
            ("target_noise_scale", -1.0),
            ("unknown_role", 1.0),
        ):
            with self.subTest(role=role, value=value), self.assertRaises(UtilityProtocolV3Error):
                NumericParameterV3(role, value)
        with self.assertRaises(UtilityProtocolV3Error):
            AcceptedRelationBindingV3(
                self.relation.relation_binding_hash,
                self.relation.executable_signature_hash,
                self.relation.portfolio_identity,
                "UNKNOWN_SOURCE",
                self.relation.target,
                self.relation.expected_source_direction,
                self.relation.expected_target_direction,
                self.relation.selected_horizon_seconds,
            )
        with self.assertRaises(UtilityProtocolV3Error):
            AcceptedRelationBindingV3(
                self.relation.relation_binding_hash,
                self.relation.executable_signature_hash,
                self.relation.portfolio_identity,
                self.relation.source,
                "UNKNOWN_TARGET",
                self.relation.expected_source_direction,
                self.relation.expected_target_direction,
                self.relation.selected_horizon_seconds,
            )
        for direction, horizon in (("wrong", self.relation.selected_horizon_seconds), (self.relation.expected_source_direction, 2)):
            with self.subTest(direction=direction, horizon=horizon), self.assertRaises(UtilityProtocolV3Error):
                AcceptedRelationBindingV3(
                    self.relation.relation_binding_hash,
                    self.relation.executable_signature_hash,
                    self.relation.portfolio_identity,
                    self.relation.source,
                    self.relation.target,
                    direction,
                    self.relation.expected_target_direction,
                    horizon,
                )

    def test_missing_or_extra_source_universe_rejects(self) -> None:
        context = AvailableSourceWindowV3(self.relation.source, (0.0,) * 5, (2.0,) * 5)
        base = self._retained_map(100)
        missing = dict(base)
        missing.pop(next(iter(missing)))
        extra = {**base, "P1_EXTRA": ()}
        for retained in (missing, extra):
            with self.assertRaises(UtilityProtocolV3Error):
                form_source_opportunity_v3(
                    relation=self.relation,
                    authority=self.authority,
                    file_identity="hai-test1.csv",
                    physical_row_count=ROW_COUNT,
                    event_index=100,
                    source_context=context,
                    source_step_threshold=NumericParameterV3("source_step_threshold", 0.5),
                    source_stability_tolerance=NumericParameterV3("source_stability_tolerance", 0.0),
                    retained_events_by_source=retained,
                )

    def test_serialized_schema_cannot_substitute_unknown_target_or_metadata(self) -> None:
        document = self.schema.to_dict()
        target_index = next(
            index for index, entry in enumerate(document["feature_entries"])
            if entry["role"] == "target"
        )
        for mutation in ("metadata", "unknown_target"):
            changed = copy.deepcopy(document)
            if mutation == "metadata":
                changed["feature_entries"][target_index]["metadata_authority_hash"] = "f" * 64
            else:
                changed["feature_entries"][target_index]["feature_name"] = "P1_ZZZ"
                changed["feature_entries"][target_index]["metadata_authority_hash"] = "f" * 64
                changed["feature_entries"] = sorted(
                    changed["feature_entries"], key=lambda entry: entry["feature_name"]
                )
            changed["artifact_hash"] = stable_hash_v1(
                {key: value for key, value in changed.items() if key != "artifact_hash"}
            )
            with self.subTest(mutation=mutation), self.assertRaises(UtilityProtocolV3Error):
                P1UtilityFeatureSchemaV3.from_mapping(changed)

    def test_canonical_scalar_policy_rejects_int_parameter_and_float_row_count(self) -> None:
        with self.assertRaises(UtilityProtocolV3Error):
            NumericParameterV3("source_step_threshold", 1)  # type: ignore[arg-type]
        relation_hashes = tuple(sorted(self.authority.signatures_by_relation))
        with self.assertRaises(UtilityProtocolV3Error):
            FullCensusEnumerationV3(
                (), relation_hashes, (), "COMMON-42", "hai-test1.csv", 54_000.0, "a" * 64  # type: ignore[arg-type]
            )

    def test_interior_abstain_record_requires_coordinate_derived_provenance(self) -> None:
        opportunity = self._opportunity(100)
        forced = TargetEvaluationOutcomeV3("abstain", None, False, "file_boundary")
        with self.assertRaises(UtilityProtocolV3Error):
            opportunity_record_v3(opportunity, forced)


if __name__ == "__main__":
    unittest.main()
