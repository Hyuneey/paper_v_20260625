from __future__ import annotations

from copy import deepcopy
from dataclasses import fields
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import unittest

import paperworks.v6.task039e3_r2r_utility_protocol_v4 as subject


ROOT = Path(__file__).resolve().parents[1]
H = "a" * 64
J = "b" * 64
K = "c" * 64
L = "d" * 64

EXPECTED_R1_AUTHORITY = "1a6200adce791ddd9be8d87b566d47b65e78c1735829d0f91f4ea22127ad1343"
EXPECTED_COORDINATE_AUTHORITY = "6bfa5f41564cc09871463b24026b297ac12a347802b4fcecc8a094c94e3f15a0"
EXPECTED_ENUMERATION_CONTRACT = "7f854ef13afb5c2e7f5864faac249ccdd3e39060f2d2b09811e8792481b9db5b"
EXPECTED_TYPE_POLICY = "d0f549f2ce9b9ac058aa362d9579068fec2fb03a2d2cde4a4495ecc3d70db7f0"
EXPECTED_EVIDENCE_CONTRACT = "20c7247c31045dc38e99dcac147abce284e7f375799dd45e9232af318e10a15e"
EXPECTED_CSV_REPORT = "d4f43034e9402806a4f34da943a1e39191503f8f54465d6d1f98b9cdc31bb7c9"
EXPECTED_NUMERIC_DESCRIPTOR = "665af1d58d672dfe8109c01e5dcb4e8f19aa2303a8f6100bfd20b3272c3bd928"
EXPECTED_REFERENCE_SET = "d14cf57a33a4e7018cbd2342f1a5fb9fc78dfd9d86f912512a903740316c73ae"

FILE_ORACLE = {
    "hai-test1.csv": {
        "relative_path": "hai-23.05/hai-test1.csv",
        "sha256": "78c7f1d4de1f2ab9ccc2f8c719f80f831033543adb0c81d0d78f84f40838d4be",
        "split": "30a7c88d6e0af5c37493237cc83b9520cbcd6f43c2dee7bb50ec3cac2668e7d0",
        "rows": 54_000,
        "first": "2022-08-12 16:00:01",
        "last": "2022-08-13 07:00:00",
    },
    "hai-test2.csv": {
        "relative_path": "hai-23.05/hai-test2.csv",
        "sha256": "b2b8dd295aefd87e39260fe43cb4c73ee86d6264b0ac4b0761e7efb0c2b545c3",
        "split": "9d76358ff109e4a6d2a712a1ff679c199d08e9cc92239160c8016e9efa063203",
        "rows": 230_400,
        "first": "2022-08-17 00:00:01",
        "last": "2022-08-19 16:00:00",
    },
}


def load(relative_path: str) -> dict[str, object]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def independent_hash(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def bypass_mutation(value: object, **changes: object) -> object:
    result = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(result, field.name, changes.get(field.name, getattr(value, field.name)))
    return result


def independent_timestamp(file_identity: str, row_index: int) -> str:
    file_spec = FILE_ORACLE[file_identity]
    first = datetime.strptime(str(file_spec["first"]), "%Y-%m-%d %H:%M:%S")
    return (first + timedelta(seconds=row_index)).strftime("%Y-%m-%d %H:%M:%S")


def independent_timestamp_identity(file_identity: str, row_index: int) -> str:
    file_spec = FILE_ORACLE[file_identity]
    return independent_hash(
        {
            "artifact_type": "task039e3_r2r_utility_protocol_v4_r1_canonical_timestamp_identity",
            "canonical_timestamp": independent_timestamp(file_identity, row_index),
            "control_revision": "R1",
            "csv_structure_report_hash": EXPECTED_CSV_REPORT,
            "nominal_delta_seconds": 1,
            "physical_row_index": row_index,
            "source_file_identity": file_identity,
            "source_file_sha256": file_spec["sha256"],
            "split_identity": file_spec["split"],
        }
    )


def independent_row_identity(file_identity: str, row_index: int) -> str:
    file_spec = FILE_ORACLE[file_identity]
    return independent_hash(
        {
            "artifact_type": "task039e3_r2r_utility_protocol_v4_r1_canonical_row_time_identity",
            "control_revision": "R1",
            "dataset_manifest_identity": subject.DATASET_MANIFEST_ID,
            "file_coordinate_authority_hash": EXPECTED_COORDINATE_AUTHORITY,
            "physical_row_index": row_index,
            "source_file_identity": file_identity,
            "split_identity": file_spec["split"],
            "timestamp_identity": independent_timestamp_identity(file_identity, row_index),
        }
    )


class ExactStringSubclass(str):
    pass


class FocusedIndependentReaudit(unittest.TestCase):
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
        cls.materialized_receipt = load(
            "docs/task_reports/TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZED_RECEIPT.json"
        )
        cls.authority = subject.build_utility_protocol_v4_canonical_authority(
            executable_equivalence=cls.executable,
            evidence_manifest=cls.evidence,
            dataset_manifest=cls.dataset,
            csv_structure_report=cls.csv,
            c0_config=cls.c0,
            br2_config=cls.br2,
            materialized_audit_receipt=cls.materialized_receipt,
        )
        cls.rule = cls.authority.rule_descriptors[0]
        cls.row = subject.build_canonical_row_time_identity_v4(
            source_file_identity="hai-test1.csv", physical_row_index=100, timestamp_identity=H
        )
        cls.opportunity = subject.build_canonical_opportunity_v4(
            cls.authority,
            relation_binding_hash=cls.rule.relation_binding_hash,
            row_time=cls.row,
        )
        cls.source_state = subject.build_source_qualification_state_v4(
            cls.opportunity,
            cls.authority,
            source_window_identity=H,
            retained_source_event_identity=J,
            retained_source_event_census_hash=K,
        )
        cls.window = subject.build_canonical_window_coordinate_authority_v4_r1(
            cls.opportunity, cls.authority
        )
        cls.all_opportunities = tuple(
            sorted(
                (
                    subject.build_canonical_opportunity_v4(
                        cls.authority,
                        relation_binding_hash=rule.relation_binding_hash,
                        row_time=cls.row,
                    )
                    for rule in cls.authority.rule_descriptors
                ),
                key=lambda item: (item.relation_binding_hash, item.canonical_row_time_identity),
            )
        )

    def top_with(self, **changes: object) -> subject.UtilityProtocolV4CanonicalAuthority:
        return bypass_mutation(self.authority, **changes)  # type: ignore[return-value]

    def assert_authority_rejects(self, authority: object) -> None:
        with self.assertRaises(subject.UtilityProtocolV4Error):
            subject.validate_utility_protocol_v4_authority(authority)  # type: ignore[arg-type]

    def assert_census_rejects(self, opportunities: tuple[object, ...]) -> None:
        with self.assertRaises(subject.UtilityProtocolV4Error):
            subject.validate_canonical_opportunity_set_v4(opportunities, self.authority)

    def assert_metric_rejects(self, terminal: object, source_evidence: object) -> None:
        with self.assertRaises(subject.UtilityProtocolV4Error):
            subject.validate_authoritative_terminal_metric_custody_v4_r1(
                terminal,
                source_evidence,
                self.opportunity,
                self.window,
                self.authority,
            )

    def test_independent_csv_report_and_file_oracle(self) -> None:
        report_payload = {key: value for key, value in self.csv.items() if key != "report_hash"}
        self.assertEqual(independent_hash(report_payload), EXPECTED_CSV_REPORT)
        records = {record["relative_path"]: record for record in self.csv["records"]}
        for file_spec in FILE_ORACLE.values():
            record = records[file_spec["relative_path"]]
            self.assertEqual(record["file_sha256"], file_spec["sha256"])
            self.assertEqual(record["row_count"], file_spec["rows"])
            self.assertEqual(record["first_timestamp"], file_spec["first"])
            self.assertEqual(record["last_timestamp"], file_spec["last"])
            self.assertEqual(record["nominal_timestamp_delta_seconds"], 1.0)

    def test_minimal_scientific_invariants(self) -> None:
        sources = {rule.source for rule in self.authority.rule_descriptors}
        targets = {rule.target for rule in self.authority.rule_descriptors}
        references = {
            reference
            for rule in self.authority.rule_descriptors
            for _, reference in rule.numeric_reference_bindings
        }
        self.assertEqual(self.authority.authority_hash, EXPECTED_R1_AUTHORITY)
        self.assertEqual((len(self.authority.rule_descriptors), len(sources), len(targets)), (42, 9, 10))
        self.assertEqual(len(references), 420)
        self.assertEqual(self.authority.numeric_authority.descriptor_hash, EXPECTED_NUMERIC_DESCRIPTOR)
        self.assertEqual(self.authority.numeric_authority.new_reference_set_hash, EXPECTED_REFERENCE_SET)
        self.assertEqual(
            (
                len(self.authority.feature_schema.source_features),
                len(self.authority.feature_schema.target_features),
                len(self.authority.feature_schema.union_features),
            ),
            (12, 10, 22),
        )
        self.assertEqual(
            (
                len(self.authority.feature_schema.common_source_footprint),
                len(self.authority.feature_schema.common_target_footprint),
                len(self.authority.feature_schema.common_feature_footprint),
            ),
            (9, 10, 19),
        )
        self.assertFalse(subject.T2_UTILITY_SCOPE_AUTHORIZED)

    def test_coordinate_authority_hash_is_exact(self) -> None:
        self.assertEqual(self.authority.file_coordinate_authority.authority_hash, EXPECTED_COORDINATE_AUTHORITY)

    def test_canonical_different_row_is_legitimate(self) -> None:
        another = subject.build_canonical_row_time_identity_v4(
            source_file_identity="hai-test1.csv", physical_row_index=101
        )
        self.assertNotEqual(another.row_time_identity, self.row.row_time_identity)
        self.assertEqual(subject.validate_canonical_row_time_identity_v4(another), another.row_time_identity)

    def test_caller_timestamp_a_vs_b_has_no_influence(self) -> None:
        first = subject.build_canonical_row_time_identity_v4(
            source_file_identity="hai-test1.csv", physical_row_index=100, timestamp_identity=H
        )
        second = subject.build_canonical_row_time_identity_v4(
            source_file_identity="hai-test1.csv", physical_row_index=100, timestamp_identity=J
        )
        self.assertEqual(first, second)

    def test_timestamp_mutation_rejects(self) -> None:
        changed = bypass_mutation(self.row, timestamp_identity=J)
        with self.assertRaises(subject.UtilityProtocolV4Error):
            subject.validate_canonical_row_time_identity_v4(changed)

    def test_self_rehashed_timestamp_mutation_rejects(self) -> None:
        changed = bypass_mutation(self.row, timestamp_identity=J, row_time_identity="")
        object.__setattr__(changed, "row_time_identity", independent_hash(subject._row_time_payload(changed)))
        with self.assertRaises(subject.UtilityProtocolV4Error):
            subject.validate_canonical_row_time_identity_v4(changed)

    def test_self_rehashed_opportunity_timestamp_chain_rejects(self) -> None:
        changed_row = bypass_mutation(self.row, timestamp_identity=J, row_time_identity="")
        object.__setattr__(changed_row, "row_time_identity", independent_hash(subject._row_time_payload(changed_row)))
        changed = bypass_mutation(
            self.opportunity,
            timestamp_identity=J,
            canonical_row_time_identity=changed_row.row_time_identity,
            opportunity_id="",
        )
        object.__setattr__(changed, "opportunity_id", independent_hash(subject._opportunity_payload(changed)))
        with self.assertRaises(subject.UtilityProtocolV4Error):
            subject.validate_canonical_opportunity_v4(changed, self.authority)

    def test_physical_row_mutation_without_factory_rejects(self) -> None:
        changed = bypass_mutation(self.row, physical_row_index=101)
        with self.assertRaises(subject.UtilityProtocolV4Error):
            subject.validate_canonical_row_time_identity_v4(changed)

    def test_file_split_substitution_rejects(self) -> None:
        changed = bypass_mutation(
            self.opportunity,
            source_file_identity="hai-test2.csv",
            split_identity=FILE_ORACLE["hai-test2.csv"]["split"],
            opportunity_id="",
        )
        object.__setattr__(changed, "opportunity_id", independent_hash(subject._opportunity_payload(changed)))
        with self.assertRaises(subject.UtilityProtocolV4Error):
            subject.validate_canonical_opportunity_v4(changed, self.authority)

    def test_negative_row_rejects(self) -> None:
        with self.assertRaises(subject.UtilityProtocolV4Error):
            subject.build_canonical_row_time_identity_v4(
                source_file_identity="hai-test1.csv", physical_row_index=-1
            )

    def test_row_equal_to_count_rejects(self) -> None:
        with self.assertRaises(subject.UtilityProtocolV4Error):
            subject.build_canonical_row_time_identity_v4(
                source_file_identity="hai-test1.csv", physical_row_index=54_000
            )

    def test_enumeration_contract_is_exact_and_unavailable(self) -> None:
        contract = self.authority.enumeration_authority_contract
        self.assertEqual(contract.contract_hash, EXPECTED_ENUMERATION_CONTRACT)
        self.assertEqual(contract.denominator_policy, "ALL_AUTOMATICALLY_ENUMERATED_APPLICABLE_CANONICAL_OPPORTUNITIES")
        self.assertFalse(contract.real_enumeration_authority_available)
        self.assertFalse(contract.caller_opportunity_set_authorized)

    def test_caller_denominator_rejects(self) -> None:
        with self.assertRaises(subject.UtilityProtocolV4Error):
            subject.authorize_canonical_full_census_plan_v4(self.authority, denominator=1)

    def test_caller_opportunity_count_rejects(self) -> None:
        with self.assertRaises(subject.UtilityProtocolV4Error):
            subject.authorize_canonical_full_census_plan_v4(self.authority, expected_opportunity_count=42)

    def test_caller_relation_subset_rejects(self) -> None:
        with self.assertRaises(subject.UtilityProtocolV4Error):
            subject.authorize_canonical_full_census_plan_v4(
                self.authority, relation_subset=self.authority.rule_descriptors[:39]
            )

    def test_caller_sample_size_rejects(self) -> None:
        with self.assertRaises(subject.UtilityProtocolV4Error):
            subject.authorize_canonical_full_census_plan_v4(self.authority, sample_n=1)

    def test_runtime_evidence_contract_is_exact_and_pending(self) -> None:
        contract = self.authority.runtime_evidence_authority_contract
        self.assertEqual(contract.contract_hash, EXPECTED_EVIDENCE_CONTRACT)
        self.assertEqual(contract.synthetic_helper_authority_scope, "SYNTHETIC_CONTRACT_ONLY")
        self.assertFalse(contract.caller_source_window_authorized)
        self.assertFalse(contract.caller_target_window_authorized)
        self.assertFalse(contract.caller_within_split_authorized)
        self.assertFalse(contract.caller_response_matched_authorized)
        self.assertFalse(contract.real_source_evidence_authority_available)
        self.assertFalse(contract.real_response_evidence_authority_available)

    def test_valid_interior_window_is_derived(self) -> None:
        self.assertEqual(self.window.source_pre_range, (95, 100))
        self.assertEqual(self.window.source_post_range, (100, 105))
        self.assertEqual(self.window.target_baseline_range, (95, 100))
        self.assertEqual(
            self.window.target_response_range,
            (100 + self.rule.selected_horizon_seconds, 103 + self.rule.selected_horizon_seconds),
        )
        self.assertTrue(self.window.within_split_derived)
        self.assertIsNone(self.window.target_boundary_reason)

    def test_near_end_window_derives_file_boundary(self) -> None:
        row = subject.build_canonical_row_time_identity_v4(
            source_file_identity="hai-test1.csv", physical_row_index=53_999
        )
        opportunity = subject.build_canonical_opportunity_v4(
            self.authority,
            relation_binding_hash=self.rule.relation_binding_hash,
            row_time=row,
        )
        window = subject.build_canonical_window_coordinate_authority_v4_r1(opportunity, self.authority)
        self.assertFalse(window.within_split_derived)
        self.assertEqual(window.target_boundary_reason, "file_boundary")

    def test_synthetic_expected_response_rejects_metric_custody(self) -> None:
        terminal = subject.transition_target_evaluation_v4(
            self.opportunity,
            self.source_state,
            self.authority,
            target_window_input_identity=L,
            within_split=True,
            target_context_available=True,
            response_matched=True,
        )
        self.assert_metric_rejects(terminal, self.source_state)

    def test_synthetic_anomaly_rejects_metric_custody(self) -> None:
        terminal = subject.transition_target_evaluation_v4(
            self.opportunity,
            self.source_state,
            self.authority,
            target_window_input_identity=L,
            within_split=True,
            target_context_available=True,
            response_matched=False,
        )
        self.assert_metric_rejects(terminal, self.source_state)

    def test_synthetic_interior_split_boundary_rejects_metric_custody(self) -> None:
        terminal = subject.transition_target_evaluation_v4(
            self.opportunity,
            self.source_state,
            self.authority,
            target_window_input_identity=L,
            within_split=False,
            target_context_available=True,
            response_matched=True,
        )
        self.assertEqual(terminal.abstention_reason, "split_boundary")
        self.assert_metric_rejects(terminal, self.source_state)

    def test_self_rehashed_source_state_rejects_metric_custody(self) -> None:
        changed = bypass_mutation(self.source_state, source_window_identity=L, source_qualification_identity="")
        payload = {
            field.name: getattr(changed, field.name)
            for field in fields(changed)
            if field.name != "source_qualification_identity"
        }
        object.__setattr__(changed, "source_qualification_identity", independent_hash(payload))
        self.assert_metric_rejects(object(), changed)

    def test_self_rehashed_terminal_state_rejects_metric_custody(self) -> None:
        terminal = subject.transition_target_evaluation_v4(
            self.opportunity,
            self.source_state,
            self.authority,
            target_window_input_identity=L,
            within_split=True,
            target_context_available=True,
            response_matched=True,
        )
        changed = bypass_mutation(
            terminal,
            response_matched=False,
            target_evaluation_state="evaluated_anomaly",
            alarm_emitted=True,
            terminal_state_provenance_hash="",
        )
        payload = {
            field.name: getattr(changed, field.name)
            for field in fields(changed)
            if field.name != "terminal_state_provenance_hash"
        }
        object.__setattr__(changed, "terminal_state_provenance_hash", independent_hash(payload))
        self.assert_metric_rejects(changed, self.source_state)

    def test_arbitrary_objects_cannot_fill_evidence_authority(self) -> None:
        self.assert_metric_rejects(object(), object())


def _make_coordinate_replay_test(file_identity: str, row_index: int):
    def test(self: FocusedIndependentReaudit) -> None:
        expected_timestamp = independent_timestamp_identity(file_identity, row_index)
        expected_row = independent_row_identity(file_identity, row_index)
        row = subject.build_canonical_row_time_identity_v4(
            source_file_identity=file_identity,
            physical_row_index=row_index,
            timestamp_identity=H,
        )
        self.assertEqual(row.timestamp_identity, expected_timestamp)
        self.assertEqual(row.row_time_identity, expected_row)
        if row_index == int(FILE_ORACLE[file_identity]["rows"]) - 1:
            self.assertEqual(independent_timestamp(file_identity, row_index), FILE_ORACLE[file_identity]["last"])

    return test


for _file_identity, _row_index, _name in (
    ("hai-test1.csv", 0, "test1_first"),
    ("hai-test1.csv", 100, "test1_interior"),
    ("hai-test1.csv", 53_999, "test1_last"),
    ("hai-test2.csv", 0, "test2_first"),
    ("hai-test2.csv", 100, "test2_interior"),
    ("hai-test2.csv", 230_399, "test2_last"),
):
    setattr(
        FocusedIndependentReaudit,
        f"test_coordinate_replay_{_name}",
        _make_coordinate_replay_test(_file_identity, _row_index),
    )


def _make_census_attack(selector):
    def test(self: FocusedIndependentReaudit) -> None:
        self.assert_census_rejects(selector(self.all_opportunities))

    return test


for _name, _selector in (
    ("empty", lambda values: ()),
    ("singleton", lambda values: values[:1]),
    ("caller_39", lambda values: values[:39]),
    ("one_row_42", lambda values: values),
    ("arbitrary_two", lambda values: values[:2]),
):
    setattr(
        FocusedIndependentReaudit,
        f"test_census_attack_{_name}",
        _make_census_attack(_selector),
    )


def _type_attack_authority(self: FocusedIndependentReaudit, name: str):
    authority = self.authority
    schema = authority.feature_schema
    rule = self.rule
    if name == "rule_descriptors_list":
        return self.top_with(rule_descriptors=list(authority.rule_descriptors))
    if name == "numeric_bindings_list":
        changed_rule = bypass_mutation(rule, numeric_reference_bindings=list(rule.numeric_reference_bindings))
        return self.top_with(rule_descriptors=(changed_rule, *authority.rule_descriptors[1:]))
    if name in {"source_features", "target_features", "union_features", "metadata_authorities"}:
        changed_schema = bypass_mutation(schema, **{name: list(getattr(schema, name))})
        return self.top_with(feature_schema=changed_schema)
    if name == "plan_hashes_list":
        changed_plan = bypass_mutation(
            authority.full_census_plan,
            rule_descriptor_hashes=list(authority.full_census_plan.rule_descriptor_hashes),
        )
        return self.top_with(full_census_plan=changed_plan)
    if name == "blocker_closures_list":
        return self.top_with(blocker_closures=list(authority.blocker_closures))
    if name == "rule_descriptors_generator":
        return self.top_with(rule_descriptors=(item for item in authority.rule_descriptors))
    if name == "rule_descriptors_set":
        return self.top_with(rule_descriptors=set(authority.rule_descriptors))
    if name == "metadata_inner_list":
        changed_schema = bypass_mutation(
            schema,
            metadata_authorities=tuple(list(item) for item in schema.metadata_authorities),
        )
        return self.top_with(feature_schema=changed_schema)
    if name == "numeric_inner_list":
        changed_rule = bypass_mutation(
            rule,
            numeric_reference_bindings=tuple(list(item) for item in rule.numeric_reference_bindings),
        )
        return self.top_with(rule_descriptors=(changed_rule, *authority.rule_descriptors[1:]))
    if name == "regression_list":
        return self.top_with(regression_authority_hashes=list(authority.regression_authority_hashes))
    if name == "resolver_lookup_list":
        changed_resolver = bypass_mutation(
            authority.private_resolver_contract,
            lookup_key_fields=list(authority.private_resolver_contract.lookup_key_fields),
        )
        return self.top_with(private_resolver_contract=changed_resolver)
    if name == "bool_in_int":
        changed_numeric = bypass_mutation(authority.numeric_authority, record_count=True)
        return self.top_with(numeric_authority=changed_numeric)
    if name == "int_in_bool":
        changed_numeric = bypass_mutation(authority.numeric_authority, t2_utility_scope_authorized=0)
        return self.top_with(numeric_authority=changed_numeric)
    if name == "string_subclass":
        changed_schema = bypass_mutation(
            schema,
            union_features=(ExactStringSubclass(schema.union_features[0]), *schema.union_features[1:]),
        )
        return self.top_with(feature_schema=changed_schema)
    raise AssertionError(name)


def _make_type_attack(name: str):
    def test(self: FocusedIndependentReaudit) -> None:
        self.assert_authority_rejects(_type_attack_authority(self, name))

    return test


for _type_name in (
    "rule_descriptors_list",
    "numeric_bindings_list",
    "source_features",
    "target_features",
    "union_features",
    "metadata_authorities",
    "plan_hashes_list",
    "blocker_closures_list",
    "rule_descriptors_generator",
    "rule_descriptors_set",
    "metadata_inner_list",
    "numeric_inner_list",
    "regression_list",
    "resolver_lookup_list",
    "bool_in_int",
    "int_in_bool",
    "string_subclass",
):
    setattr(
        FocusedIndependentReaudit,
        f"test_type_attack_{_type_name}",
        _make_type_attack(_type_name),
    )


def _make_window_attack(name: str):
    def test(self: FocusedIndependentReaudit) -> None:
        window = self.window
        changes = {
            "source_window": {"source_window_coordinate_identity": H},
            "target_window": {"target_window_coordinate_identity": H},
            "source_interval": {"source_pre_range": (window.source_pre_range[0] - 1, window.source_pre_range[1])},
            "target_baseline": {"target_baseline_range": (window.target_baseline_range[0] - 1, window.target_baseline_range[1])},
            "target_response": {"target_response_range": (window.target_response_range[0], window.target_response_range[1] + 1)},
            "horizon": {"selected_horizon_seconds": window.selected_horizon_seconds + 1},
            "interior_split": {"within_split_derived": False, "target_boundary_reason": "split_boundary"},
        }[name]
        changed = bypass_mutation(window, **changes)
        with self.assertRaises(subject.UtilityProtocolV4Error):
            subject.validate_canonical_window_coordinate_authority_v4_r1(
                changed, self.opportunity, self.authority
            )

    return test


for _window_name in (
    "source_window",
    "target_window",
    "source_interval",
    "target_baseline",
    "target_response",
    "horizon",
    "interior_split",
):
    setattr(
        FocusedIndependentReaudit,
        f"test_window_attack_{_window_name}",
        _make_window_attack(_window_name),
    )


def test_exact_float_rejects_integer(self: FocusedIndependentReaudit) -> None:
    with self.assertRaises(subject.UtilityProtocolV4Error):
        subject.validate_strict_scalar_policy_v4(
            integer_value=1,
            boolean_value=True,
            float_value=1,
            string_value="x",
            tuple_value=(),
        )


setattr(FocusedIndependentReaudit, "test_type_attack_int_in_exact_float", test_exact_float_rejects_integer)


if __name__ == "__main__":
    unittest.main()
