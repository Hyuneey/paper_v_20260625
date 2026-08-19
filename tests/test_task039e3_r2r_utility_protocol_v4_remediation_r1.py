from __future__ import annotations

from dataclasses import fields
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


class StringSubclass(str):
    pass


class UtilityProtocolV4RemediationR1Tests(unittest.TestCase):
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

    def top_with(self, **changes: object) -> v4.UtilityProtocolV4CanonicalAuthority:
        return bypass_mutation(self.authority, **changes)  # type: ignore[return-value]

    def test_r1_authority_and_scientific_invariants(self) -> None:
        self.assertEqual(v4.UTILITY_PROTOCOL_V4_CONTROL_REVISION, "R1")
        self.assertEqual(v4.HISTORICAL_CANONICAL_V4_AUTHORITY_HASH, "2864c99017dcea576437efe9f9c5d531cc0d7810504cb2bd8e8585643d2fa0a1")
        self.assertEqual(self.authority.authority_hash, v4.CANONICAL_V4_AUTHORITY_HASH)
        self.assertEqual(self.authority.numeric_authority.descriptor_hash, "665af1d58d672dfe8109c01e5dcb4e8f19aa2303a8f6100bfd20b3272c3bd928")
        self.assertEqual(len(self.authority.rule_descriptors), 42)
        self.assertEqual(sum(len(rule.numeric_reference_bindings) for rule in self.authority.rule_descriptors), 420)
        self.assertFalse(v4.T2_UTILITY_SCOPE_AUTHORIZED)

    def test_coordinate_replay_first_and_last_rows(self) -> None:
        cases = (
            ("hai-test1.csv", 0),
            ("hai-test1.csv", 53_999),
            ("hai-test2.csv", 0),
            ("hai-test2.csv", 230_399),
        )
        for file_identity, row_index in cases:
            with self.subTest(file=file_identity, row=row_index):
                row = v4.build_canonical_row_time_identity_v4(
                    source_file_identity=file_identity,
                    physical_row_index=row_index,
                    timestamp_identity=H,
                )
                self.assertEqual(v4.validate_canonical_row_time_identity_v4(row), row.row_time_identity)

    def test_caller_timestamp_is_ignored_and_non_authoritative(self) -> None:
        first = v4.build_canonical_row_time_identity_v4(
            source_file_identity="hai-test1.csv", physical_row_index=100, timestamp_identity=H
        )
        second = v4.build_canonical_row_time_identity_v4(
            source_file_identity="hai-test1.csv", physical_row_index=100, timestamp_identity=J
        )
        omitted = v4.build_canonical_row_time_identity_v4(
            source_file_identity="hai-test1.csv", physical_row_index=100
        )
        self.assertEqual(first, second)
        self.assertEqual(first, omitted)
        self.assertNotIn(first.timestamp_identity, {H, J})

    def test_historical_self_consistent_timestamp_substitution_rejects(self) -> None:
        changed_row = bypass_mutation(self.row, timestamp_identity=J, row_time_identity="")
        object.__setattr__(changed_row, "row_time_identity", v4.stable_hash_v1(v4._row_time_payload(changed_row)))
        changed_opportunity = bypass_mutation(
            self.opportunity,
            timestamp_identity=J,
            canonical_row_time_identity=changed_row.row_time_identity,
            opportunity_id="",
        )
        object.__setattr__(
            changed_opportunity,
            "opportunity_id",
            v4.stable_hash_v1(v4._opportunity_payload(changed_opportunity)),
        )
        with self.assertRaises(v4.UtilityProtocolV4Error):
            v4.validate_canonical_row_time_identity_v4(changed_row)
        with self.assertRaises(v4.UtilityProtocolV4Error):
            v4.validate_canonical_opportunity_v4(changed_opportunity, self.authority)

    def test_row_index_mutation_and_invalid_index_types_reject(self) -> None:
        changed = bypass_mutation(self.row, physical_row_index=101)
        with self.assertRaises(v4.UtilityProtocolV4Error):
            v4.validate_canonical_row_time_identity_v4(changed)
        for value in (-1, 54_000, True, 1.0):
            with self.subTest(value_type=type(value).__name__), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.build_canonical_row_time_identity_v4(
                    source_file_identity="hai-test1.csv", physical_row_index=value
                )

    def test_direct_caller_opportunity_sets_never_gain_census_authority(self) -> None:
        opportunities = tuple(
            sorted(
                (
                    v4.build_canonical_opportunity_v4(
                        self.authority,
                        relation_binding_hash=rule.relation_binding_hash,
                        row_time=self.row,
                    )
                    for rule in self.authority.rule_descriptors
                ),
                key=lambda item: (item.relation_binding_hash, item.canonical_row_time_identity),
            )
        )
        for candidate in ((), opportunities[:1], opportunities[:39], opportunities):
            with self.subTest(count=len(candidate)), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_canonical_opportunity_set_v4(candidate, self.authority)

    def test_caller_census_denominator_and_count_reject(self) -> None:
        for override in (
            {"denominator": 1},
            {"expected_opportunity_count": 42},
            {"sample_n": 1},
            {"relation_subset": self.authority.rule_descriptors[:39]},
        ):
            with self.subTest(key=next(iter(override))), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.authorize_canonical_full_census_plan_v4(self.authority, **override)

    def test_enumeration_contract_is_fail_closed(self) -> None:
        contract = self.authority.enumeration_authority_contract
        self.assertEqual(
            v4.validate_canonical_enumeration_authority_contract_v4_r1(contract, self.authority),
            contract.contract_hash,
        )
        self.assertFalse(contract.caller_opportunity_set_authorized)
        self.assertFalse(contract.caller_denominator_authorized)
        self.assertFalse(contract.caller_opportunity_count_authorized)
        self.assertFalse(contract.caller_relation_subset_authorized)
        self.assertFalse(contract.real_enumeration_authority_available)

    def test_historical_eight_feature_tuple_to_list_attacks_reject(self) -> None:
        names = (
            "source_features",
            "target_features",
            "union_features",
            "common_source_footprint",
            "common_target_footprint",
            "common_feature_footprint",
            "metadata_authorities",
        )
        for name in names:
            changed_schema = bypass_mutation(
                self.authority.feature_schema,
                **{name: list(getattr(self.authority.feature_schema, name))},
            )
            changed = self.top_with(feature_schema=changed_schema)
            self.assertEqual(changed.authority_hash, self.authority.authority_hash)
            with self.subTest(field=name), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_utility_protocol_v4_authority(changed)
        metadata = tuple(list(item) for item in self.authority.feature_schema.metadata_authorities)
        changed_schema = bypass_mutation(self.authority.feature_schema, metadata_authorities=metadata)
        changed = self.top_with(feature_schema=changed_schema)
        self.assertEqual(changed.authority_hash, self.authority.authority_hash)
        with self.assertRaises(v4.UtilityProtocolV4Error):
            v4.validate_utility_protocol_v4_authority(changed)

    def test_other_recursive_container_widening_attacks_reject(self) -> None:
        changed_rule = bypass_mutation(
            self.rule,
            numeric_reference_bindings=tuple(list(item) for item in self.rule.numeric_reference_bindings),
        )
        rules_with_inner_lists = (changed_rule, *self.authority.rule_descriptors[1:])
        cases = (
            self.top_with(rule_descriptors=list(self.authority.rule_descriptors)),
            self.top_with(rule_descriptors=(item for item in self.authority.rule_descriptors)),
            self.top_with(rule_descriptors=set(self.authority.rule_descriptors)),
            self.top_with(rule_descriptors=rules_with_inner_lists),
            self.top_with(
                full_census_plan=bypass_mutation(
                    self.authority.full_census_plan,
                    rule_descriptor_hashes=list(self.authority.full_census_plan.rule_descriptor_hashes),
                )
            ),
            self.top_with(
                private_resolver_contract=bypass_mutation(
                    self.authority.private_resolver_contract,
                    lookup_key_fields=list(self.authority.private_resolver_contract.lookup_key_fields),
                )
            ),
            self.top_with(blocker_closures=list(self.authority.blocker_closures)),
            self.top_with(regression_authority_hashes=list(self.authority.regression_authority_hashes)),
            self.top_with(
                file_coordinate_authority=bypass_mutation(
                    self.authority.file_coordinate_authority,
                    file_specs=list(self.authority.file_coordinate_authority.file_specs),
                )
            ),
        )
        for index, changed in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_utility_protocol_v4_authority(changed)

    def test_recursive_scalar_subtype_attacks_reject(self) -> None:
        union = self.authority.feature_schema.union_features
        changed_schema = bypass_mutation(
            self.authority.feature_schema,
            union_features=(StringSubclass(union[0]), *union[1:]),
        )
        scalar_cases = (
            self.top_with(feature_schema=changed_schema),
            self.top_with(
                numeric_authority=bypass_mutation(self.authority.numeric_authority, record_count=True)
            ),
            self.top_with(
                numeric_authority=bypass_mutation(
                    self.authority.numeric_authority, historical_e1_identity_restored=0
                )
            ),
            self.top_with(
                enumeration_authority_contract=bypass_mutation(
                    self.authority.enumeration_authority_contract,
                    caller_denominator_authorized=0,
                )
            ),
        )
        for index, changed in enumerate(scalar_cases):
            with self.subTest(index=index), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_utility_protocol_v4_authority(changed)
        for values in (
            dict(integer_value=True, boolean_value=True, float_value=1.0, string_value="x", tuple_value=()),
            dict(integer_value=1, boolean_value=1, float_value=1.0, string_value="x", tuple_value=()),
            dict(integer_value=1, boolean_value=True, float_value=1, string_value="x", tuple_value=()),
        ):
            with self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_strict_scalar_policy_v4(**values)

    def test_window_coordinates_are_derived_and_replayed(self) -> None:
        coordinate = v4.build_canonical_window_coordinate_authority_v4_r1(
            self.opportunity, self.authority
        )
        self.assertTrue(coordinate.within_split_derived)
        self.assertIsNone(coordinate.target_boundary_reason)
        self.assertEqual(
            v4.validate_canonical_window_coordinate_authority_v4_r1(
                coordinate, self.opportunity, self.authority
            ),
            coordinate.coordinate_hash,
        )
        final_row = v4.build_canonical_row_time_identity_v4(
            source_file_identity="hai-test1.csv", physical_row_index=53_999
        )
        final_opportunity = v4.build_canonical_opportunity_v4(
            self.authority,
            relation_binding_hash=self.rule.relation_binding_hash,
            row_time=final_row,
        )
        boundary = v4.build_canonical_window_coordinate_authority_v4_r1(
            final_opportunity, self.authority
        )
        self.assertFalse(boundary.within_split_derived)
        self.assertEqual(boundary.target_boundary_reason, "file_boundary")

    def test_window_substitution_and_interior_split_claims_reject(self) -> None:
        coordinate = v4.build_canonical_window_coordinate_authority_v4_r1(
            self.opportunity, self.authority
        )
        cases = (
            {"source_window_coordinate_identity": H},
            {"target_window_coordinate_identity": H},
            {"within_split_derived": False, "target_boundary_reason": "split_boundary"},
            {"source_pre_range": list(coordinate.source_pre_range)},
            {"target_response_range": (coordinate.target_response_range[0], coordinate.target_response_range[1] + 1)},
        )
        for changes in cases:
            changed = bypass_mutation(coordinate, **changes)
            with self.subTest(fields=tuple(changes)), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_canonical_window_coordinate_authority_v4_r1(
                    changed, self.opportunity, self.authority
                )

    def test_runtime_evidence_contract_is_explicitly_pending(self) -> None:
        contract = self.authority.runtime_evidence_authority_contract
        self.assertEqual(
            v4.validate_runtime_evidence_authority_contract_v4_r1(contract, self.authority),
            contract.contract_hash,
        )
        self.assertEqual(contract.synthetic_helper_authority_scope, "SYNTHETIC_CONTRACT_ONLY")
        self.assertFalse(contract.caller_source_window_authorized)
        self.assertFalse(contract.caller_target_window_authorized)
        self.assertFalse(contract.caller_within_split_authorized)
        self.assertFalse(contract.caller_response_matched_authorized)
        self.assertTrue(contract.deterministic_coordinate_boundary_abstention_authorized)
        self.assertFalse(contract.synthetic_helper_metric_custody_authorized)
        self.assertFalse(contract.real_source_evidence_authority_available)
        self.assertFalse(contract.real_response_evidence_authority_available)

    def test_synthetic_transitions_never_enter_authoritative_metric_custody(self) -> None:
        coordinate = v4.build_canonical_window_coordinate_authority_v4_r1(
            self.opportunity, self.authority
        )
        states = (
            v4.transition_target_evaluation_v4(
                self.opportunity,
                self.source_state,
                self.authority,
                target_window_input_identity=H,
                within_split=True,
                target_context_available=True,
                response_matched=True,
            ),
            v4.transition_target_evaluation_v4(
                self.opportunity,
                self.source_state,
                self.authority,
                target_window_input_identity=J,
                within_split=True,
                target_context_available=True,
                response_matched=False,
            ),
            v4.transition_target_evaluation_v4(
                self.opportunity,
                self.source_state,
                self.authority,
                target_window_input_identity=K,
                within_split=False,
                target_context_available=True,
                response_matched=True,
            ),
            v4.transition_target_evaluation_v4(
                self.opportunity,
                self.source_state,
                self.authority,
                target_window_input_identity=L,
                within_split=True,
                target_context_available=False,
                response_matched=True,
            ),
        )
        for state in states:
            with self.subTest(state=state.target_evaluation_state), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_authoritative_terminal_metric_custody_v4_r1(
                    state,
                    self.source_state,
                    self.opportunity,
                    coordinate,
                    self.authority,
                )

    def test_caller_objects_cannot_fill_missing_evaluator_evidence(self) -> None:
        coordinate = v4.build_canonical_window_coordinate_authority_v4_r1(
            self.opportunity, self.authority
        )
        for source_evidence, response_evidence in ((object(), object()), (H, J), ({}, {})):
            with self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_authoritative_terminal_metric_custody_v4_r1(
                    response_evidence,
                    source_evidence,
                    self.opportunity,
                    coordinate,
                    self.authority,
                )


def _make_generated_feature_widening_test(field_name: str):
    def test(self: UtilityProtocolV4RemediationR1Tests) -> None:
        schema = self.authority.feature_schema
        if field_name == "metadata_authorities_inner":
            changed_schema = bypass_mutation(
                schema,
                metadata_authorities=tuple(list(item) for item in schema.metadata_authorities),
            )
        else:
            changed_schema = bypass_mutation(
                schema, **{field_name: list(getattr(schema, field_name))}
            )
        with self.assertRaises(v4.UtilityProtocolV4Error):
            v4.validate_utility_protocol_v4_authority(self.top_with(feature_schema=changed_schema))

    return test


for _index, _field_name in enumerate(
    (
        "source_features",
        "target_features",
        "union_features",
        "common_source_footprint",
        "common_target_footprint",
        "common_feature_footprint",
        "metadata_authorities",
        "metadata_authorities_inner",
    ),
    start=1,
):
    setattr(
        UtilityProtocolV4RemediationR1Tests,
        f"test_generated_historical_list_widening_{_index:02d}",
        _make_generated_feature_widening_test(_field_name),
    )


def _make_generated_index_attack(value: object):
    def test(self: UtilityProtocolV4RemediationR1Tests) -> None:
        with self.assertRaises(v4.UtilityProtocolV4Error):
            v4.build_canonical_row_time_identity_v4(
                source_file_identity="hai-test1.csv", physical_row_index=value
            )

    return test


for _index, _value in enumerate((-1, 54_000, True, 1.0), start=1):
    setattr(
        UtilityProtocolV4RemediationR1Tests,
        f"test_generated_coordinate_index_attack_{_index:02d}",
        _make_generated_index_attack(_value),
    )


def _make_generated_scalar_attack(values: dict[str, object]):
    def test(self: UtilityProtocolV4RemediationR1Tests) -> None:
        with self.assertRaises(v4.UtilityProtocolV4Error):
            v4.validate_strict_scalar_policy_v4(**values)

    return test


for _index, _values in enumerate(
    (
        dict(integer_value=True, boolean_value=True, float_value=1.0, string_value="x", tuple_value=()),
        dict(integer_value=1.0, boolean_value=True, float_value=1.0, string_value="x", tuple_value=()),
        dict(integer_value=1, boolean_value=1, float_value=1.0, string_value="x", tuple_value=()),
        dict(integer_value=1, boolean_value="true", float_value=1.0, string_value="x", tuple_value=()),
        dict(integer_value=1, boolean_value=True, float_value=1, string_value="x", tuple_value=()),
        dict(integer_value=1, boolean_value=True, float_value=float("nan"), string_value="x", tuple_value=()),
        dict(integer_value=1, boolean_value=True, float_value=float("inf"), string_value="x", tuple_value=()),
        dict(integer_value=1, boolean_value=True, float_value=1.0, string_value="x", tuple_value=[]),
    ),
    start=1,
):
    setattr(
        UtilityProtocolV4RemediationR1Tests,
        f"test_generated_scalar_attack_{_index:02d}",
        _make_generated_scalar_attack(_values),
    )


if __name__ == "__main__":
    unittest.main()
