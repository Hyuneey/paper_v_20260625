from __future__ import annotations

from copy import deepcopy
from dataclasses import fields, replace
import json
from pathlib import Path
import unittest

import paperworks.v6.task039e3_r2r_utility_protocol_v4 as v4


ROOT = Path(__file__).resolve().parents[1]
H = "a" * 64
J = "b" * 64
K = "c" * 64
L = "d" * 64


def load(relative_path: str) -> dict[str, object]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def bypass_mutation(value: object, **changes: object) -> object:
    result = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(result, field.name, changes.get(field.name, getattr(value, field.name)))
    return result


class UtilityProtocolV4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.executable = load(
            "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"
        )
        cls.evidence = load("docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json")
        cls.dataset = load("docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json")
        cls.csv = load("docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json")
        cls.c0 = load("configs/v6/task039c0_candidate_discovery_protocol.json")
        cls.br2 = load("configs/v6/task039br2_hai_continuous_step_feasibility.json")
        cls.audit_receipt = load(
            "docs/task_reports/TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZED_RECEIPT.json"
        )
        cls.common = v4.build_common42_public_authority_v4(cls.executable, cls.evidence)
        cls.authority = v4.build_utility_protocol_v4_canonical_authority(
            executable_equivalence=cls.executable,
            evidence_manifest=cls.evidence,
            dataset_manifest=cls.dataset,
            csv_structure_report=cls.csv,
            c0_config=cls.c0,
            br2_config=cls.br2,
            materialized_audit_receipt=cls.audit_receipt,
        )
        cls.rule = cls.authority.rule_descriptors[0]
        cls.row = v4.build_canonical_row_time_identity_v4(
            source_file_identity="hai-test1.csv",
            physical_row_index=100,
            timestamp_identity=H,
        )
        cls.opportunity = v4.build_canonical_opportunity_v4(
            cls.authority,
            relation_binding_hash=cls.rule.relation_binding_hash,
            row_time=cls.row,
        )
        cls.source_state = v4.build_source_qualification_state_v4(
            cls.opportunity,
            cls.authority,
            source_window_identity=J,
            retained_source_event_identity=K,
            retained_source_event_census_hash=L,
        )

    def test_canonical_authority_hash_and_replay(self) -> None:
        self.assertEqual(self.authority.authority_hash, v4.CANONICAL_V4_AUTHORITY_HASH)
        self.assertEqual(v4.validate_utility_protocol_v4_authority(self.authority), v4.CANONICAL_V4_AUTHORITY_HASH)

    def test_common_and_numeric_closure(self) -> None:
        self.assertEqual(len(self.common.relations), 42)
        self.assertEqual(len(self.common.reference_identities), 420)
        self.assertEqual(len(set(self.common.reference_identities)), 420)
        self.assertEqual(self.common.authority_definition_hash, v4.CANONICAL_AUTHORITY_DEFINITION_HASH)
        self.assertEqual(self.authority.numeric_authority.new_reference_set_hash, v4.NEW_REFERENCE_SET_HASH)

    def test_numeric_descriptor_has_no_values(self) -> None:
        document = self.authority.numeric_authority.to_dict()
        serialized = json.dumps(document, sort_keys=True)
        for forbidden in ("numeric_value", "source_step_threshold", "target_noise_scale", "private_path"):
            self.assertNotIn(forbidden, serialized)

    def test_materialized_audit_receipt_exact_pass(self) -> None:
        self.assertEqual(
            v4.validate_materialized_authority_audit_receipt_v4(self.audit_receipt),
            v4.MATERIALIZED_AUTHORITY_AUDIT_RECEIPT_HASH,
        )

    def test_materialized_receipt_self_rehashed_substitution_rejects(self) -> None:
        for key, value in (
            ("private_registry_hash", "f" * 64),
            ("bundle_hash", "f" * 64),
            ("normal_only_authority_materialization_audited", False),
        ):
            changed = deepcopy(self.audit_receipt)
            changed[key] = value
            changed["artifact_hash"] = v4.stable_hash_v1(
                {name: item for name, item in changed.items() if name != "artifact_hash"}
            )
            with self.subTest(key=key), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_materialized_authority_audit_receipt_v4(changed)

    def test_numeric_authority_mutations_reject(self) -> None:
        mutations = (
            {"private_registry_content_hash": "f" * 64},
            {"private_registry_content_hash": v4.HISTORICAL_NUMERIC_REGISTRY_HASH},
            {"materialized_authority_audit_receipt_hash": "f" * 64},
            {"authority_definition_hash": "f" * 64},
            {"calibration_policy_hash": "f" * 64},
            {"common42_authority_hash": "f" * 64},
            {"normal_input_identity_set_hash": "f" * 64},
            {"record_count": 419},
            {"reference_count": 419},
            {"t2_utility_scope_authorized": True},
        )
        for changes in mutations:
            changed = replace(self.authority.numeric_authority, **changes)
            with self.subTest(changes=tuple(changes)), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_numeric_authority_descriptor_v4(changed, self.common, self.audit_receipt)

    def test_rule_descriptor_count_and_reference_closure(self) -> None:
        self.assertEqual(len(self.authority.rule_descriptors), 42)
        references = [reference for rule in self.authority.rule_descriptors for _, reference in rule.numeric_reference_bindings]
        self.assertEqual(len(references), 420)
        self.assertEqual(len(set(references)), 420)
        self.assertEqual(set(references), set(self.common.reference_identities))

    def test_rule_semantic_mutations_reject(self) -> None:
        mutations = (
            {"relation_identity": "directional_relation:foreign"},
            {"relation_binding_hash": "f" * 64},
            {"semantic_execution_hash": "f" * 64},
            {"source": "P1_FCV02Z"},
            {"target": "P1_TIT03"},
            {"source_direction": "step_down" if self.rule.source_direction == "step_up" else "step_up"},
            {"target_direction": "decrease" if self.rule.target_direction == "increase" else "increase"},
            {"selected_horizon_seconds": 60 if self.rule.selected_horizon_seconds != 60 else 30},
            {"numeric_authority_descriptor_hash": "f" * 64},
        )
        for changes in mutations:
            changed = replace(self.rule, **changes)
            with self.subTest(changes=tuple(changes)), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_canonical_rule_descriptor_v4(changed, self.authority)

    def test_rule_reference_missing_extra_reorder_rejects(self) -> None:
        bindings = self.rule.numeric_reference_bindings
        for changed in (bindings[:-1], (*bindings, bindings[-1]), tuple(reversed(bindings))):
            with self.subTest(length=len(changed)), self.assertRaises(v4.UtilityProtocolV4Error):
                replace(self.rule, numeric_reference_bindings=changed)

    def test_historical_reference_namespace_is_not_execution_authority(self) -> None:
        historical = self.common.relations[0].historical_reference_pairs[0][1]
        bindings = list(self.rule.numeric_reference_bindings)
        bindings[0] = (bindings[0][0], historical)
        with self.assertRaises(v4.UtilityProtocolV4Error):
            replace(self.rule, numeric_reference_bindings=tuple(bindings))

    def test_t2_and_fake_subset_reject(self) -> None:
        for portfolio in ("T2", "T2-39", "historical_T2_subset"):
            with self.subTest(portfolio=portfolio), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.authorize_canonical_full_census_plan_v4(
                    self.authority, portfolio_identity=portfolio
                )

    def test_census_caller_authorities_reject(self) -> None:
        for key, value in (
            ("sample_n", 10),
            ("max_opportunities", 10),
            ("expected_opportunity_count", 10),
            ("caller_denominator", 10),
            ("opportunity_list", ()),
            ("relation_subset", self.authority.rule_descriptors[:39]),
            ("numeric_registry", "caller"),
        ):
            with self.subTest(key=key), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.authorize_canonical_full_census_plan_v4(self.authority, **{key: value})

    def test_canonical_census_plan_passes_replay(self) -> None:
        plan = v4.authorize_canonical_full_census_plan_v4(self.authority)
        self.assertEqual(
            v4.validate_canonical_full_census_plan_v4(plan, self.authority), plan.plan_hash
        )
        self.assertEqual(len(plan.rule_descriptor_hashes), 42)

    def test_fabricated_census_plan_rejects(self) -> None:
        for changes in (
            {"rule_descriptor_hashes": self.authority.full_census_plan.rule_descriptor_hashes[:39]},
            {"numeric_authority_descriptor_hash": "f" * 64},
            {"event_policy_hash": "f" * 64},
        ):
            try:
                changed = replace(self.authority.full_census_plan, **changes)
            except v4.UtilityProtocolV4Error:
                continue
            with self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_canonical_full_census_plan_v4(changed, self.authority)

    def test_feature_schema_exact_12_10_22_and_common_9_10_19(self) -> None:
        schema = self.authority.feature_schema
        self.assertEqual((len(schema.source_features), len(schema.target_features), len(schema.union_features)), (12, 10, 22))
        self.assertEqual((len(schema.common_source_footprint), len(schema.common_target_footprint), len(schema.common_feature_footprint)), (9, 10, 19))
        self.assertEqual(schema.canonical_v3_schema_report_hash, v4.CANONICAL_FEATURE_SCHEMA_HASH)
        self.assertEqual(schema.canonical_runtime_schema_hash, v4.CANONICAL_RUNTIME_FEATURE_SCHEMA_HASH)

    def test_feature_schema_serialized_substitutions_reject(self) -> None:
        schema = self.authority.feature_schema
        for changes in (
            {"target_features": (*schema.target_features[:-1], "P1_TIT03")},
            {"source_features": schema.source_features[:-1]},
            {"union_features": (*schema.union_features, "P1_UNKNOWN")},
            {"metadata_authorities": (*schema.metadata_authorities[:-1], (schema.metadata_authorities[-1][0], "f" * 64))},
            {"canonical_runtime_schema_hash": "f" * 64},
        ):
            try:
                changed = replace(schema, **changes)
            except v4.UtilityProtocolV4Error:
                continue
            with self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_canonical_feature_schema_v4(
                    changed,
                    dataset_manifest=self.dataset,
                    csv_structure_report=self.csv,
                    c0_config=self.c0,
                    br2_config=self.br2,
                    executable_equivalence=self.executable,
                    common_authority=self.common,
                )

    def test_lower_metadata_mutation_rejects_feature_replay(self) -> None:
        changed = deepcopy(self.c0)
        changed["common_universe"]["source_identities"] = changed["common_universe"]["source_identities"][:-1]
        with self.assertRaises(Exception):
            v4.build_canonical_feature_schema_v4(
                dataset_manifest=self.dataset,
                csv_structure_report=self.csv,
                c0_config=changed,
                br2_config=self.br2,
                executable_equivalence=self.executable,
                common_authority=self.common,
            )

    def test_selected_header_exact(self) -> None:
        expected = ("timestamp", *self.authority.feature_schema.union_features)
        self.assertEqual(v4.validate_selected_feature_header_v4(expected, self.authority), expected)
        for changed in (expected[:-1], (*expected, "P1_UNKNOWN"), (expected[0], expected[1], *expected[1:]), list(expected)):
            with self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_selected_feature_header_v4(changed, self.authority)

    def test_ascii_raw_parser_accepts_only_exact_tuple_strings(self) -> None:
        feature = self.authority.feature_schema.union_features[0]
        self.assertEqual(v4.parse_raw_feature_tokens_v4(feature, ("1", "-2.5", "3e-2"), self.authority), (1.0, -2.5, 0.03))
        for bad in ((" 1",), ("1 ",), ("NaN",), ("Inf",), ("1_0",), ("١",), ("１",), ("1e9999",), (1,), (True,), ["1"], {"1"}):
            with self.subTest(kind=type(bad).__name__), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.parse_raw_feature_tokens_v4(feature, bad, self.authority)

    def test_raw_label_policy_is_exact(self) -> None:
        self.assertEqual(v4.parse_raw_label_tokens_v4(("0", "1"), self.authority), (0, 1))
        for bad in ((0,), (1,), (True,), ("2",), ["0"], (" 0",)):
            with self.assertRaises(v4.UtilityProtocolV4Error):
                v4.parse_raw_label_tokens_v4(bad, self.authority)

    def test_strict_scalar_positive_case(self) -> None:
        self.assertEqual(
            v4.validate_strict_scalar_policy_v4(
                integer_value=1,
                boolean_value=True,
                float_value=1.0,
                string_value="1",
                tuple_value=(1,),
            ),
            v4.STRICT_SCALAR_POLICY_HASH,
        )

    def test_strict_scalar_cross_type_mutations_reject(self) -> None:
        cases = (
            {"integer_value": True},
            {"integer_value": 1.0},
            {"integer_value": "1"},
            {"boolean_value": 1},
            {"boolean_value": 1.0},
            {"boolean_value": "true"},
            {"float_value": 1},
            {"float_value": True},
            {"float_value": "1"},
            {"float_value": float("nan")},
            {"float_value": float("inf")},
            {"tuple_value": [1]},
        )
        base = dict(integer_value=1, boolean_value=True, float_value=1.0, string_value="1", tuple_value=(1,))
        for change in cases:
            with self.subTest(change=tuple(change)), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_strict_scalar_policy_v4(**{**base, **change})

    def test_canonical_opportunity_binds_all_semantics(self) -> None:
        opportunity = self.opportunity
        self.assertEqual(v4.validate_canonical_opportunity_v4(opportunity, self.authority), opportunity.opportunity_id)
        self.assertEqual(opportunity.source, self.rule.source)
        self.assertEqual(opportunity.target, self.rule.target)
        self.assertEqual(opportunity.rule_descriptor_hash, self.rule.descriptor_hash)

    def test_opportunity_semantic_mutations_reject_even_when_rehashed(self) -> None:
        mutations = (
            {"relation_identity": "directional_relation:foreign"},
            {"semantic_execution_hash": "f" * 64},
            {"source": "P1_FCV02Z"},
            {"target": "P1_TIT03"},
            {"source_direction": "step_down" if self.opportunity.source_direction == "step_up" else "step_up"},
            {"target_direction": "decrease" if self.opportunity.target_direction == "increase" else "increase"},
            {"selected_horizon_seconds": 60 if self.opportunity.selected_horizon_seconds != 60 else 30},
            {"rule_descriptor_hash": "f" * 64},
            {"numeric_authority_descriptor_hash": "f" * 64},
            {"event_policy_hash": "f" * 64},
            {"opportunity_enumeration_policy_hash": "f" * 64},
        )
        for changes in mutations:
            changed = bypass_mutation(self.opportunity, **changes)
            object.__setattr__(changed, "opportunity_id", v4.stable_hash_v1(v4._opportunity_payload(changed)))
            with self.subTest(changes=tuple(changes)), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_canonical_opportunity_v4(changed, self.authority)

    def test_opportunity_row_time_mutations_reject(self) -> None:
        for changes in (
            {"dataset_manifest_identity": "f" * 64},
            {"split_identity": v4.OUTER_SPLIT_ID},
            {"source_file_identity": "hai-test2.csv"},
            {"physical_row_index": 100.0},
            {"timestamp_identity": "f" * 64},
            {"canonical_row_time_identity": "f" * 64},
        ):
            changed = bypass_mutation(self.opportunity, **changes)
            object.__setattr__(changed, "opportunity_id", v4.stable_hash_v1(v4._opportunity_payload(changed)))
            with self.subTest(changes=tuple(changes)), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_canonical_opportunity_v4(changed, self.authority)

    def test_row_change_changes_opportunity_identity(self) -> None:
        row = v4.build_canonical_row_time_identity_v4(
            source_file_identity="hai-test1.csv", physical_row_index=101, timestamp_identity=J
        )
        changed = v4.build_canonical_opportunity_v4(
            self.authority, relation_binding_hash=self.rule.relation_binding_hash, row_time=row
        )
        self.assertNotEqual(changed.opportunity_id, self.opportunity.opportunity_id)

    def test_duplicate_opportunity_identity_rejects(self) -> None:
        with self.assertRaises(v4.UtilityProtocolV4Error):
            v4.validate_canonical_opportunity_set_v4((self.opportunity, self.opportunity), self.authority)

    def test_direct_parent_and_terminal_construction_rejects(self) -> None:
        for cls in (v4.CanonicalOpportunityV4, v4.SourceQualificationStateV4, v4.TargetEvaluationStateV4):
            with self.subTest(cls=cls.__name__), self.assertRaises(TypeError):
                cls()  # type: ignore[call-arg]

    def test_source_qualification_parent_chain_passes(self) -> None:
        self.assertEqual(
            v4.validate_source_qualification_state_v4(self.source_state, self.opportunity, self.authority),
            self.source_state.source_qualification_identity,
        )

    def test_source_qualification_parent_mutations_reject(self) -> None:
        for changes in (
            {"opportunity_id": "f" * 64},
            {"rule_descriptor_hash": "f" * 64},
            {"source_step_reference_identity": self.rule.reference_for("target_noise_scale")},
            {"source_stability_reference_identity": self.rule.reference_for("target_noise_scale")},
            {"event_policy_hash": "f" * 64},
            {"state": "caller_qualified"},
        ):
            changed = bypass_mutation(self.source_state, **changes)
            with self.subTest(changes=tuple(changes)), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_source_qualification_state_v4(changed, self.opportunity, self.authority)

    def test_terminal_expected_and_anomaly_transitions(self) -> None:
        expected = v4.transition_target_evaluation_v4(
            self.opportunity, self.source_state, self.authority,
            target_window_input_identity=H, within_split=True,
            target_context_available=True, response_matched=True,
        )
        anomaly = v4.transition_target_evaluation_v4(
            self.opportunity, self.source_state, self.authority,
            target_window_input_identity=H, within_split=True,
            target_context_available=True, response_matched=False,
        )
        self.assertEqual(expected.target_evaluation_state, "evaluated_expected_response")
        self.assertEqual(anomaly.target_evaluation_state, "evaluated_anomaly")
        self.assertFalse(expected.alarm_emitted)
        self.assertTrue(anomaly.alarm_emitted)
        v4.validate_target_evaluation_state_v4(expected, self.opportunity, self.source_state, self.authority)
        v4.validate_target_evaluation_state_v4(anomaly, self.opportunity, self.source_state, self.authority)

    def test_terminal_boundary_precedence(self) -> None:
        near_end_row = v4.build_canonical_row_time_identity_v4(
            source_file_identity="hai-test1.csv", physical_row_index=53_999, timestamp_identity=J
        )
        near_end = v4.build_canonical_opportunity_v4(
            self.authority, relation_binding_hash=self.rule.relation_binding_hash, row_time=near_end_row
        )
        near_source = v4.build_source_qualification_state_v4(
            near_end, self.authority, source_window_identity=J,
            retained_source_event_identity=K, retained_source_event_census_hash=L,
        )
        file_state = v4.transition_target_evaluation_v4(
            near_end, near_source, self.authority, target_window_input_identity=H,
            within_split=False, target_context_available=False, response_matched=False,
        )
        split_state = v4.transition_target_evaluation_v4(
            self.opportunity, self.source_state, self.authority, target_window_input_identity=H,
            within_split=False, target_context_available=False, response_matched=False,
        )
        incomplete = v4.transition_target_evaluation_v4(
            self.opportunity, self.source_state, self.authority, target_window_input_identity=H,
            within_split=True, target_context_available=False, response_matched=False,
        )
        self.assertEqual(file_state.abstention_reason, "file_boundary")
        self.assertEqual(split_state.abstention_reason, "split_boundary")
        self.assertEqual(incomplete.abstention_reason, "incomplete_target_response_window")

    def test_terminal_parent_and_state_mutations_reject(self) -> None:
        state = v4.transition_target_evaluation_v4(
            self.opportunity, self.source_state, self.authority,
            target_window_input_identity=H, within_split=True,
            target_context_available=True, response_matched=True,
        )
        mutations = (
            {"opportunity_id": "f" * 64},
            {"rule_descriptor_hash": "f" * 64},
            {"source_qualification_identity": "f" * 64},
            {"target_window_input_identity": "f" * 64},
            {"target_noise_reference_identity": self.rule.reference_for("source_step_threshold")},
            {"transition_policy_hash": "f" * 64},
            {"within_split": 1},
            {"target_evaluation_state": "abstain"},
            {"decision_row_time_identity": None},
            {"alarm_emitted": 0},
            {"abstention_reason": "file_boundary"},
        )
        for changes in mutations:
            changed = bypass_mutation(state, **changes)
            with self.subTest(changes=tuple(changes)), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_target_evaluation_state_v4(
                    changed, self.opportunity, self.source_state, self.authority
                )

    def test_terminal_forged_interior_boundaries_reject(self) -> None:
        state = v4.transition_target_evaluation_v4(
            self.opportunity, self.source_state, self.authority,
            target_window_input_identity=H, within_split=True,
            target_context_available=True, response_matched=True,
        )
        for reason in ("file_boundary", "split_boundary", "incomplete_target_response_window"):
            changed = bypass_mutation(
                state,
                target_evaluation_state="abstain",
                decision_row_time_identity=None,
                alarm_emitted=False,
                abstention_reason=reason,
            )
            values = {
                name: getattr(changed, name)
                for name in (
                    "opportunity_id", "rule_descriptor_hash", "source_qualification_identity",
                    "target_window_input_identity", "target_noise_reference_identity",
                    "numeric_authority_descriptor_hash", "transition_policy_hash",
                    "physical_row_count", "within_split", "target_context_available",
                    "response_matched", "target_evaluation_state", "decision_row_time_identity",
                    "alarm_emitted", "abstention_reason",
                )
            }
            object.__setattr__(changed, "terminal_state_provenance_hash", v4.stable_hash_v1(values))
            with self.subTest(reason=reason), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_target_evaluation_state_v4(changed, self.opportunity, self.source_state, self.authority)

    def test_transition_boolean_type_substitutions_reject(self) -> None:
        for key, value in (
            ("within_split", 1),
            ("target_context_available", 1.0),
            ("response_matched", "true"),
        ):
            args = dict(
                target_window_input_identity=H,
                within_split=True,
                target_context_available=True,
                response_matched=True,
            )
            args[key] = value
            with self.subTest(key=key), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.transition_target_evaluation_v4(
                    self.opportunity, self.source_state, self.authority, **args
                )

    def test_corrected_regression_authorities_only(self) -> None:
        self.assertEqual(
            v4.validate_regression_authorities_v4(
                v4.CORRECTED_REGRESSION_NUMERIC_REFERENCE_AUTHORITY_HASH,
                v4.CORRECTED_EVENT_POLICY_HASH,
                v4.CORRECTED_METRIC_POLICY_HASH,
            ),
            self.authority.regression_authority_hashes,
        )
        for index, wrong in enumerate(v4.HISTORICAL_WRONG_REGRESSION_HASHES):
            values = list(self.authority.regression_authority_hashes)
            values[index] = wrong
            with self.subTest(index=index), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_regression_authorities_v4(*values)

    def test_private_resolver_is_metadata_only_and_new_authority_only(self) -> None:
        contract = self.authority.private_resolver_contract
        self.assertEqual(contract.expected_records, 420)
        self.assertFalse(contract.historical_private_authority_required)
        self.assertFalse(contract.returns_partial_lookup_on_failure)
        self.assertFalse(contract.exposes_private_serialization)
        self.assertEqual(contract.private_registry_content_hash, v4.PRIVATE_REGISTRY_CONTENT_HASH)

    def test_claim_boundary_and_t2_are_closed(self) -> None:
        document = self.authority.to_dict()
        self.assertFalse(document["claim_boundary"]["evaluator_implemented"])
        self.assertFalse(document["claim_boundary"]["private_numeric_values_accessed"])
        self.assertFalse(document["claim_boundary"]["real_utility_executed"])
        self.assertFalse(document["t2_utility_scope_authorized"])
        self.assertEqual(document["main_portfolio"], "COMMON-42")

    def test_all_eight_closures_are_bound(self) -> None:
        self.assertEqual(len(self.authority.blocker_closures), 8)
        self.assertEqual(self.authority.blocker_closures, v4.BLOCKER_CLOSURES)


# Count each specified scalar coercion as an independently named focused case.
def _make_scalar_case(field_name: str, invalid: object):
    def test(self: UtilityProtocolV4Tests) -> None:
        values = dict(
            integer_value=1,
            boolean_value=True,
            float_value=1.0,
            string_value="identity",
            tuple_value=(1,),
        )
        values[field_name] = invalid
        with self.assertRaises(v4.UtilityProtocolV4Error):
            v4.validate_strict_scalar_policy_v4(**values)
    return test


_GENERATED_SCALAR_CASES = (
    ("integer_value", True),
    ("integer_value", 1.0),
    ("integer_value", "1"),
    ("boolean_value", 1),
    ("boolean_value", 1.0),
    ("boolean_value", "true"),
    ("float_value", 1),
    ("float_value", True),
    ("float_value", "1"),
    ("float_value", float("nan")),
    ("float_value", float("inf")),
    ("tuple_value", [1]),
)
for _index, (_field, _invalid) in enumerate(_GENERATED_SCALAR_CASES, start=1):
    setattr(
        UtilityProtocolV4Tests,
        f"test_generated_scalar_coercion_{_index:02d}",
        _make_scalar_case(_field, _invalid),
    )


if __name__ == "__main__":
    unittest.main()
