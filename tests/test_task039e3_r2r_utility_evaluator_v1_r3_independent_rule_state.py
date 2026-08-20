"""Independent R3 rule/state/provenance completion audit.

The primary oracle is reconstructed from the committed lower V4 authority
documents.  No evaluator implementation test is imported.  All runtime data
is an in-memory ``SYNTHETIC_CONTRACT_ONLY`` fixture; this module never opens a
private registry, locator, HAI file, label vector, or attack interval.

The historical R2 audit incorrectly called ``dataclasses.replace`` on the
factory-only ``CanonicalOpportunityV4``.  This corrected audit deliberately
uses ``object.__new__`` for adversarial copies of factory-only V4 objects, so
the mutation reaches the production validator without invoking a forbidden
constructor.
"""

from __future__ import annotations

from dataclasses import fields, replace
import json
from pathlib import Path
import unittest

from paperworks.v6 import task039e3_r2r_utility_protocol_v4 as v4
from paperworks.v6 import task039e3_r2r_utility_source_census_supplement_v1 as supplement
from paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 import (
    SUPPLEMENT_PURPOSE,
    EvaluatorAuthorityBundleV1,
    SyntheticNumericRecordV1,
    build_evaluator_authority_bundle_v1,
    build_synthetic_numeric_resolver_v1,
    validate_evaluator_authority_bundle_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_census_v1 import (
    enumerate_full_census_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_input_v1 import (
    build_synthetic_feature_frame_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_rule_engine_v1 import (
    ABSTAIN_STATE,
    ANOMALY_STATE,
    EXPECTED_RESPONSE_STATE,
    execute_rule_v1,
    validate_rule_execution_result_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import (
    EVALUATOR_VERSION,
    SYNTHETIC_CONTRACT_ONLY,
    RuleExecutionResultV1,
    SyntheticFeatureFrameV1,
    SyntheticFeatureRowV1,
    UtilityEvaluatorV1Error,
    stable_hash_v1,
)


ROOT = Path(__file__).resolve().parents[1]

# Frozen lower-authority constants, stated explicitly instead of inferred from
# evaluator reports or prior implementation tests.
EXPECTED_V4_AUTHORITY = "1a6200adce791ddd9be8d87b566d47b65e78c1735829d0f91f4ea22127ad1343"
EXPECTED_PORTFOLIO = "COMMON-42"
EXPECTED_RELATION_COUNT = 42
EXPECTED_MAIN_DESCRIPTOR = "665af1d58d672dfe8109c01e5dcb4e8f19aa2303a8f6100bfd20b3272c3bd928"
EXPECTED_MAIN_REFERENCE_SET = "d14cf57a33a4e7018cbd2342f1a5fb9fc78dfd9d86f912512a903740316c73ae"
EXPECTED_MAIN_REFERENCE_COUNT = 420
EXPECTED_EVENT_POLICY = "6e4a4467953c5c9bf973a0a8a18950669dc902310407b7b354128ad91febb2f4"
EXPECTED_NUMERIC_ROLES = (
    "source_step_threshold",
    "source_stability_tolerance",
    "target_noise_scale",
    "source_pre_window_seconds",
    "source_post_window_seconds",
    "minimum_source_stability_fraction",
    "source_refractory_seconds",
    "cross_source_isolation_radius_seconds",
    "target_baseline_window_seconds",
    "target_response_window_seconds",
)

# Counts represent distinct semantic attack classes and concrete invalid
# operations in this file.  They intentionally exclude canonical positive
# executions and the 42-relation lower-authority replay loop.
UNIQUE_RULE_STATE_ATTACK_CLASSES = 68
RAW_RULE_STATE_ADVERSARIAL_CASES = 119
MALFORMED_TO_ABSTAIN_ACCEPTED = 0
SUPPLEMENT_RELATION_EXECUTION_ACCEPTED = 0
AUTHORITATIVE_STATE_FORGERIES_ACCEPTED = 0


def _load(relative_path: str) -> dict[str, object]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def _build_lower_v4_authority() -> v4.UtilityProtocolV4CanonicalAuthority:
    """Replay V4 from committed public inputs, not an evaluator report."""

    return v4.build_utility_protocol_v4_canonical_authority(
        executable_equivalence=_load(
            "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"
        ),
        evidence_manifest=_load(
            "docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json"
        ),
        dataset_manifest=_load("docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json"),
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


def _numeric_value(role: str) -> int | float:
    return {
        "source_step_threshold": 1.0,
        "source_stability_tolerance": 0.0,
        "target_noise_scale": 0.5,
        "source_pre_window_seconds": 5,
        "source_post_window_seconds": 5,
        "minimum_source_stability_fraction": 0.8,
        "source_refractory_seconds": 10,
        "cross_source_isolation_radius_seconds": 2,
        "target_baseline_window_seconds": 5,
        "target_response_window_seconds": 3,
    }[role]


def _forge_factory_object(value: object, **changes: object) -> object:
    """Create an invalid lookalike without invoking a factory-only __new__."""

    result = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(
            result,
            field.name,
            changes.get(field.name, getattr(value, field.name)),
        )
    return result


def _source_state_payload(state: v4.SourceQualificationStateV4) -> dict[str, object]:
    return {
        "opportunity_id": state.opportunity_id,
        "rule_descriptor_hash": state.rule_descriptor_hash,
        "source_window_identity": state.source_window_identity,
        "retained_source_event_identity": state.retained_source_event_identity,
        "retained_source_event_census_hash": state.retained_source_event_census_hash,
        "source_step_reference_identity": state.source_step_reference_identity,
        "source_stability_reference_identity": state.source_stability_reference_identity,
        "event_policy_hash": state.event_policy_hash,
        "state": state.state,
    }


def _target_state_payload(state: v4.TargetEvaluationStateV4) -> dict[str, object]:
    return {
        "opportunity_id": state.opportunity_id,
        "rule_descriptor_hash": state.rule_descriptor_hash,
        "source_qualification_identity": state.source_qualification_identity,
        "target_window_input_identity": state.target_window_input_identity,
        "target_noise_reference_identity": state.target_noise_reference_identity,
        "numeric_authority_descriptor_hash": state.numeric_authority_descriptor_hash,
        "transition_policy_hash": state.transition_policy_hash,
        "physical_row_count": state.physical_row_count,
        "within_split": state.within_split,
        "target_context_available": state.target_context_available,
        "response_matched": state.response_matched,
        "target_evaluation_state": state.target_evaluation_state,
        "decision_row_time_identity": state.decision_row_time_identity,
        "alarm_emitted": state.alarm_emitted,
        "abstention_reason": state.abstention_reason,
    }


class UtilityEvaluatorV1R3IndependentRuleStateAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.v4_authority = _build_lower_v4_authority()
        if cls.v4_authority.authority_hash != EXPECTED_V4_AUTHORITY:
            raise AssertionError("lower V4 authority replay differs")
        if cls.v4_authority.numeric_authority.descriptor_hash != EXPECTED_MAIN_DESCRIPTOR:
            raise AssertionError("lower MAIN descriptor replay differs")
        if cls.v4_authority.numeric_authority.new_reference_set_hash != EXPECTED_MAIN_REFERENCE_SET:
            raise AssertionError("lower MAIN reference set replay differs")
        cls.bundle = build_evaluator_authority_bundle_v1(cls.v4_authority)
        cls.rule = next(
            item
            for item in cls.v4_authority.rule_descriptors
            if item.selected_horizon_seconds == 10
        )
        cls.main_records = tuple(
            SyntheticNumericRecordV1(
                "SYNTHETIC_MAIN_420",
                rule.source,
                rule.relation_binding_hash,
                role,
                reference,
                _numeric_value(role),
            )
            for rule in cls.v4_authority.rule_descriptors
            for role, reference in rule.numeric_reference_bindings
        )
        cls.supplement_records = tuple(
            SyntheticNumericRecordV1(
                SUPPLEMENT_PURPOSE,
                source,
                None,
                role,
                supplement.supplement_reference_identity_v1(source, role),
                _numeric_value(role),
            )
            for source in supplement.SUPPLEMENT_SOURCES
            for role in supplement.SUPPLEMENT_ROLES
        )
        cls.resolver = build_synthetic_numeric_resolver_v1(
            cls.bundle,
            cls.main_records,
            cls.supplement_records,
        )

    @classmethod
    def _frame(
        cls,
        *,
        expected_response: bool,
        start: int = 80,
        length: int = 100,
        event_index: int = 100,
    ) -> SyntheticFeatureFrameV1:
        response_start = event_index + cls.rule.selected_horizon_seconds
        rows: list[tuple[float, ...]] = []
        for physical in range(start, start + length):
            values: list[float] = []
            for feature in cls.v4_authority.feature_schema.union_features:
                value = 0.0
                if feature == cls.rule.source and physical >= event_index + 1:
                    value = 2.0 if cls.rule.source_direction == "step_up" else -2.0
                if (
                    expected_response
                    and feature == cls.rule.target
                    and response_start <= physical < response_start + 3
                ):
                    value = 2.0 if cls.rule.target_direction == "increase" else -2.0
                values.append(value)
            rows.append(tuple(values))
        return build_synthetic_feature_frame_v1(
            cls.bundle,
            source_file_identity="hai-test1.csv",
            start_physical_row_index=start,
            rows=tuple(rows),
        )

    @classmethod
    def _case(
        cls,
        *,
        expected_response: bool = True,
        **frame_options: object,
    ) -> tuple[SyntheticFeatureFrameV1, object, object]:
        frame = cls._frame(expected_response=expected_response, **frame_options)
        census = enumerate_full_census_v1(frame, cls.bundle, cls.resolver)
        envelope = next(
            item
            for item in census.relation_opportunities
            if item.canonical_opportunity.relation_binding_hash
            == cls.rule.relation_binding_hash
        )
        return frame, census, envelope

    def test_lower_common42_rule_oracle_and_descriptor_preimages(self) -> None:
        self.assertEqual(self.v4_authority.authority_hash, EXPECTED_V4_AUTHORITY)
        self.assertEqual(self.v4_authority.full_census_plan.portfolio_identity, EXPECTED_PORTFOLIO)
        self.assertEqual(len(self.v4_authority.rule_descriptors), EXPECTED_RELATION_COUNT)
        self.assertFalse(v4.T2_UTILITY_SCOPE_AUTHORIZED)
        self.assertEqual(tuple(v4.UTILITY_NUMERIC_ROLES), EXPECTED_NUMERIC_ROLES)
        self.assertEqual(len(self.main_records), EXPECTED_MAIN_REFERENCE_COUNT)
        self.assertEqual(len(self.supplement_records), 6)
        relation_ids: set[str] = set()
        binding_hashes: set[str] = set()
        semantic_hashes: set[str] = set()
        descriptor_hashes: set[str] = set()
        references: set[str] = set()
        for rule in self.v4_authority.rule_descriptors:
            relation_ids.add(rule.relation_identity)
            binding_hashes.add(rule.relation_binding_hash)
            semantic_hashes.add(rule.semantic_execution_hash)
            descriptor_hashes.add(rule.descriptor_hash)
            bindings = rule.numeric_reference_bindings
            self.assertEqual(tuple(role for role, _ in bindings), EXPECTED_NUMERIC_ROLES)
            self.assertEqual(len(bindings), 10)
            self.assertEqual(len({reference for _, reference in bindings}), 10)
            self.assertEqual(rule.numeric_authority_descriptor_hash, EXPECTED_MAIN_DESCRIPTOR)
            descriptor_preimage = {
                "artifact_type": "task039e3_r2r_utility_protocol_v4_rule_descriptor",
                "numeric_authority_descriptor_hash": rule.numeric_authority_descriptor_hash,
                "numeric_reference_bindings": [
                    {"numeric_role": role, "reference_identity": reference}
                    for role, reference in bindings
                ],
                "relation_binding_hash": rule.relation_binding_hash,
                "relation_identity": rule.relation_identity,
                "schema_version": "4.0.0",
                "selected_horizon_seconds": rule.selected_horizon_seconds,
                "semantic_execution_hash": rule.semantic_execution_hash,
                "source": rule.source,
                "source_direction": rule.source_direction,
                "target": rule.target,
                "target_direction": rule.target_direction,
            }
            self.assertEqual(stable_hash_v1(descriptor_preimage), rule.descriptor_hash)
            references.update(reference for _, reference in bindings)
        self.assertEqual(len(relation_ids), 42)
        self.assertEqual(len(binding_hashes), 42)
        self.assertEqual(len(semantic_hashes), 42)
        self.assertEqual(len(descriptor_hashes), 42)
        self.assertEqual(len(references), 420)

    def test_rule_descriptor_semantic_substitutions_reject(self) -> None:
        rule = self.rule
        other = next(item for item in self.v4_authority.rule_descriptors if item != rule)
        changed_bindings = list(rule.numeric_reference_bindings)
        changed_bindings[0] = (changed_bindings[0][0], other.numeric_reference_bindings[0][1])
        role_swapped = list(rule.numeric_reference_bindings)
        role_swapped[0] = ("target_noise_scale", role_swapped[0][1])
        attacks = (
            {"relation_identity": other.relation_identity},
            {"relation_binding_hash": other.relation_binding_hash},
            {"semantic_execution_hash": other.semantic_execution_hash},
            {"source": other.source},
            {"target": other.target},
            {"source_direction": "step_down" if rule.source_direction == "step_up" else "step_up"},
            {"target_direction": "decrease" if rule.target_direction == "increase" else "increase"},
            {"selected_horizon_seconds": 60 if rule.selected_horizon_seconds != 60 else 30},
            {"numeric_reference_bindings": tuple(changed_bindings)},
            {"numeric_reference_bindings": tuple(role_swapped)},
            {"numeric_reference_bindings": rule.numeric_reference_bindings[:-1]},
            {"numeric_authority_descriptor_hash": "a" * 64},
        )
        for case_id, changes in enumerate(attacks):
            forged = _forge_factory_object(rule, **changes)
            with self.subTest(case=case_id), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_canonical_rule_descriptor_v4(forged, self.v4_authority)

    def test_opportunity_semantic_coordinate_and_parent_substitutions_reject(self) -> None:
        _, _, envelope = self._case()
        opportunity = envelope.canonical_opportunity
        other = next(item for item in self.v4_authority.rule_descriptors if item != self.rule)
        attacks = (
            {"dataset_manifest_identity": "dataset-substitute"},
            {"split_identity": v4.OUTER_SPLIT_ID},
            {"source_file_identity": "hai-test2.csv"},
            {"relation_identity": other.relation_identity},
            {"relation_binding_hash": other.relation_binding_hash},
            {"semantic_execution_hash": other.semantic_execution_hash},
            {"source": other.source},
            {"target": other.target},
            {"source_direction": "step_down" if opportunity.source_direction == "step_up" else "step_up"},
            {"target_direction": "decrease" if opportunity.target_direction == "increase" else "increase"},
            {"selected_horizon_seconds": opportunity.selected_horizon_seconds + 1},
            {"canonical_row_time_identity": "1" * 64},
            {"physical_row_index": opportunity.physical_row_index + 1},
            {"physical_row_index": True},
            {"timestamp_identity": "2" * 64},
            {"rule_descriptor_hash": other.descriptor_hash},
            {"numeric_authority_descriptor_hash": "3" * 64},
            {"event_policy_hash": "4" * 64},
            {"opportunity_enumeration_policy_hash": "5" * 64},
            {"opportunity_id": "6" * 64},
        )
        for case_id, changes in enumerate(attacks):
            forged = _forge_factory_object(opportunity, **changes)
            with self.subTest(case=case_id), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_canonical_opportunity_v4(forged, self.v4_authority)
        with self.assertRaises(v4.UtilityProtocolV4Error):
            v4.CanonicalOpportunityV4(object())

    def test_main_numeric_roles_references_and_supplement_misuse_reject(self) -> None:
        target_index = next(
            index for index, record in enumerate(self.main_records)
            if record.numeric_role == "target_noise_scale"
        )
        threshold_index = next(
            index for index, record in enumerate(self.main_records)
            if record.numeric_role == "source_step_threshold"
        )
        tolerance_index = next(
            index for index, record in enumerate(self.main_records)
            if record.numeric_role == "source_stability_tolerance"
        )
        target = self.main_records[target_index]
        threshold = self.main_records[threshold_index]
        tolerance = self.main_records[tolerance_index]
        supplemental_ref = supplement.supplement_reference_identity_v1(
            supplement.SUPPLEMENT_SOURCES[0], "source_step_threshold"
        )
        main_attacks = (
            (target_index, replace(target, reference_identity=supplemental_ref)),
            (threshold_index, replace(threshold, reference_identity=supplemental_ref)),
            (target_index, replace(target, numeric_role="source_step_threshold")),
            (target_index, replace(target, relation_binding_hash="7" * 64)),
            (target_index, replace(target, source=supplement.SUPPLEMENT_SOURCES[0])),
            (target_index, replace(target, authority_plane=SUPPLEMENT_PURPOSE)),
            (threshold_index, replace(threshold, value=0.0)),
            (threshold_index, replace(threshold, value=1)),
            (tolerance_index, replace(tolerance, value=-1.0)),
            (target_index, replace(target, value=float("nan"))),
        )
        for case_id, (index, record) in enumerate(main_attacks):
            changed = (*self.main_records[:index], record, *self.main_records[index + 1 :])
            with self.subTest(main_case=case_id), self.assertRaises(UtilityEvaluatorV1Error):
                build_synthetic_numeric_resolver_v1(
                    self.bundle, changed, self.supplement_records
                )

        supplemental = self.supplement_records[0]
        supplement_attacks = (
            replace(supplemental, numeric_role="target_noise_scale", reference_identity="8" * 64),
            replace(supplemental, numeric_role="target_response_window_seconds", reference_identity="9" * 64),
            replace(supplemental, relation_binding_hash=self.rule.relation_binding_hash),
            replace(supplemental, authority_plane="SYNTHETIC_MAIN_420"),
            replace(supplemental, reference_identity=self.rule.numeric_reference_bindings[0][1]),
            replace(supplemental, source=self.rule.source),
            replace(supplemental, value=1),
        )
        accepted = 0
        for case_id, record in enumerate(supplement_attacks):
            changed = (record, *self.supplement_records[1:])
            with self.subTest(supplement_case=case_id):
                try:
                    build_synthetic_numeric_resolver_v1(
                        self.bundle, self.main_records, changed
                    )
                except UtilityEvaluatorV1Error:
                    continue
                accepted += 1
        self.assertEqual(accepted, SUPPLEMENT_RELATION_EXECUTION_ACCEPTED)

    def test_canonical_execution_binds_rule_event_and_computation_preimage(self) -> None:
        frame, census, envelope = self._case(expected_response=True)
        opportunity = envelope.canonical_opportunity
        rule = self.v4_authority.rule_by_binding(opportunity.relation_binding_hash)
        result = execute_rule_v1(envelope, census, frame, self.bundle, self.resolver)
        expected_references = tuple(reference for _, reference in rule.numeric_reference_bindings)
        expected_computation = stable_hash_v1(
            {
                "artifact_type": "task039e3_r2r_utility_evaluator_v1_computation",
                "authority_bundle_hash": validate_evaluator_authority_bundle_v1(self.bundle),
                "evaluator_version": EVALUATOR_VERSION,
                "execution_mode": SYNTHETIC_CONTRACT_ONLY,
                "frame_hash": frame.frame_hash,
                "isolated_source_event_identity": envelope.isolated_source_event_identity,
                "numeric_reference_identities": list(expected_references),
                "opportunity_id": opportunity.opportunity_id,
                "rule_descriptor_hash": rule.descriptor_hash,
            }
        )
        self.assertEqual(result.evaluator_computation_identity, expected_computation)
        self.assertEqual(result.opportunity_id, opportunity.opportunity_id)
        self.assertEqual(result.source_event_identity, envelope.isolated_source_event_identity)
        self.assertEqual(result.relation_binding_hash, rule.relation_binding_hash)
        self.assertEqual(result.numeric_reference_identities, expected_references)
        self.assertEqual(result.final_state, EXPECTED_RESPONSE_STATE)
        self.assertFalse(result.alarm_emitted)

    def test_source_state_parent_chain_mutation_and_self_rehash_reject(self) -> None:
        _, census, envelope = self._case()
        opportunity = envelope.canonical_opportunity
        state = v4.build_source_qualification_state_v4(
            opportunity,
            self.v4_authority,
            source_window_identity="a" * 64,
            retained_source_event_identity=envelope.isolated_source_event_identity,
            retained_source_event_census_hash=census.source_census_identity,
        )
        self.assertEqual(
            v4.validate_source_qualification_state_v4(
                state, opportunity, self.v4_authority
            ),
            state.source_qualification_identity,
        )
        attacks = (
            {"opportunity_id": "b" * 64},
            {"rule_descriptor_hash": "c" * 64},
            {"source_window_identity": "d" * 64},
            {"retained_source_event_identity": "e" * 64},
            {"retained_source_event_census_hash": "f" * 64},
            {"source_step_reference_identity": "1" * 64},
            {"source_stability_reference_identity": "2" * 64},
            {"event_policy_hash": "3" * 64},
            {"state": ABSTAIN_STATE},
            {"source_qualification_identity": "4" * 64},
        )
        for case_id, changes in enumerate(attacks):
            forged = _forge_factory_object(state, **changes)
            with self.subTest(case=case_id), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_source_qualification_state_v4(
                    forged, opportunity, self.v4_authority
                )
        self_rehashed = _forge_factory_object(state, opportunity_id="5" * 64)
        object.__setattr__(
            self_rehashed,
            "source_qualification_identity",
            stable_hash_v1(_source_state_payload(self_rehashed)),
        )
        with self.assertRaises(v4.UtilityProtocolV4Error):
            v4.validate_source_qualification_state_v4(
                self_rehashed, opportunity, self.v4_authority
            )
        with self.assertRaises(v4.UtilityProtocolV4Error):
            v4.SourceQualificationStateV4(object())

    def test_source_state_wrong_opportunity_parent_rejects_without_replace(self) -> None:
        _, census, envelope = self._case()
        opportunity = envelope.canonical_opportunity
        state = v4.build_source_qualification_state_v4(
            opportunity,
            self.v4_authority,
            source_window_identity="6" * 64,
            retained_source_event_identity=envelope.isolated_source_event_identity,
            retained_source_event_census_hash=census.source_census_identity,
        )
        other_rule = next(
            rule for rule in self.v4_authority.rule_descriptors
            if rule.relation_binding_hash != opportunity.relation_binding_hash
        )
        row_time = v4.build_canonical_row_time_identity_v4(
            source_file_identity=opportunity.source_file_identity,
            physical_row_index=opportunity.physical_row_index,
        )
        other_opportunity = v4.build_canonical_opportunity_v4(
            self.v4_authority,
            relation_binding_hash=other_rule.relation_binding_hash,
            row_time=row_time,
        )
        with self.assertRaises(v4.UtilityProtocolV4Error):
            v4.validate_source_qualification_state_v4(
                state, other_opportunity, self.v4_authority
            )

    def test_target_state_parent_window_coordinate_transition_mutations_reject(self) -> None:
        _, census, envelope = self._case()
        opportunity = envelope.canonical_opportunity
        source = v4.build_source_qualification_state_v4(
            opportunity,
            self.v4_authority,
            source_window_identity="7" * 64,
            retained_source_event_identity=envelope.isolated_source_event_identity,
            retained_source_event_census_hash=census.source_census_identity,
        )
        target = v4.transition_target_evaluation_v4(
            opportunity,
            source,
            self.v4_authority,
            target_window_input_identity="8" * 64,
            within_split=True,
            target_context_available=True,
            response_matched=True,
        )
        self.assertEqual(
            v4.validate_target_evaluation_state_v4(
                target, opportunity, source, self.v4_authority
            ),
            target.terminal_state_provenance_hash,
        )
        attacks = (
            {"opportunity_id": "9" * 64},
            {"rule_descriptor_hash": "a" * 64},
            {"source_qualification_identity": "b" * 64},
            {"target_window_input_identity": "c" * 64},
            {"target_noise_reference_identity": "d" * 64},
            {"numeric_authority_descriptor_hash": "e" * 64},
            {"transition_policy_hash": "f" * 64},
            {"physical_row_count": target.physical_row_count - 1},
            {"physical_row_count": True},
            {"within_split": 1},
            {"target_context_available": 1},
            {"response_matched": 1},
            {"target_evaluation_state": ANOMALY_STATE},
            {"decision_row_time_identity": "1" * 64},
            {"alarm_emitted": True},
            {"abstention_reason": "split_boundary"},
            {"terminal_state_provenance_hash": "2" * 64},
        )
        for case_id, changes in enumerate(attacks):
            forged = _forge_factory_object(target, **changes)
            with self.subTest(case=case_id), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_target_evaluation_state_v4(
                    forged, opportunity, source, self.v4_authority
                )
        self_rehashed = _forge_factory_object(
            target, source_qualification_identity="3" * 64
        )
        object.__setattr__(
            self_rehashed,
            "terminal_state_provenance_hash",
            stable_hash_v1(_target_state_payload(self_rehashed)),
        )
        with self.assertRaises(v4.UtilityProtocolV4Error):
            v4.validate_target_evaluation_state_v4(
                self_rehashed, opportunity, source, self.v4_authority
            )
        with self.assertRaises(v4.UtilityProtocolV4Error):
            v4.TargetEvaluationStateV4(object())

    def test_target_state_wrong_source_parent_and_synthetic_metric_custody_reject(self) -> None:
        _, census, envelope = self._case()
        opportunity = envelope.canonical_opportunity
        source = v4.build_source_qualification_state_v4(
            opportunity,
            self.v4_authority,
            source_window_identity="4" * 64,
            retained_source_event_identity=envelope.isolated_source_event_identity,
            retained_source_event_census_hash=census.source_census_identity,
        )
        other_source = v4.build_source_qualification_state_v4(
            opportunity,
            self.v4_authority,
            source_window_identity="5" * 64,
            retained_source_event_identity=envelope.isolated_source_event_identity,
            retained_source_event_census_hash=census.source_census_identity,
        )
        target = v4.transition_target_evaluation_v4(
            opportunity,
            source,
            self.v4_authority,
            target_window_input_identity="6" * 64,
            within_split=True,
            target_context_available=True,
            response_matched=True,
        )
        with self.assertRaises(v4.UtilityProtocolV4Error):
            v4.validate_target_evaluation_state_v4(
                target, opportunity, other_source, self.v4_authority
            )
        window = v4.build_canonical_window_coordinate_authority_v4_r1(
            opportunity, self.v4_authority
        )
        with self.assertRaises(v4.UtilityProtocolV4Error):
            v4.validate_authoritative_terminal_metric_custody_v4_r1(
                target, source, opportunity, window, self.v4_authority
            )

    def test_target_transition_oracle_distinguishes_evaluation_and_abstention(self) -> None:
        _, census, envelope = self._case()
        opportunity = envelope.canonical_opportunity
        source = v4.build_source_qualification_state_v4(
            opportunity,
            self.v4_authority,
            source_window_identity="7" * 64,
            retained_source_event_identity=envelope.isolated_source_event_identity,
            retained_source_event_census_hash=census.source_census_identity,
        )
        expected = v4.transition_target_evaluation_v4(
            opportunity, source, self.v4_authority,
            target_window_input_identity="8" * 64,
            within_split=True, target_context_available=True, response_matched=True,
        )
        anomaly = v4.transition_target_evaluation_v4(
            opportunity, source, self.v4_authority,
            target_window_input_identity="9" * 64,
            within_split=True, target_context_available=True, response_matched=False,
        )
        split = v4.transition_target_evaluation_v4(
            opportunity, source, self.v4_authority,
            target_window_input_identity="a" * 64,
            within_split=False, target_context_available=True, response_matched=True,
        )
        missing = v4.transition_target_evaluation_v4(
            opportunity, source, self.v4_authority,
            target_window_input_identity="b" * 64,
            within_split=True, target_context_available=False, response_matched=False,
        )
        self.assertEqual(expected.target_evaluation_state, EXPECTED_RESPONSE_STATE)
        self.assertFalse(expected.alarm_emitted)
        self.assertEqual(anomaly.target_evaluation_state, ANOMALY_STATE)
        self.assertTrue(anomaly.alarm_emitted)
        self.assertEqual((split.target_evaluation_state, split.abstention_reason), (ABSTAIN_STATE, "split_boundary"))
        self.assertEqual((missing.target_evaluation_state, missing.abstention_reason), (ABSTAIN_STATE, "incomplete_target_response_window"))
        for field_name in ("within_split", "target_context_available", "response_matched"):
            kwargs = {
                "target_window_input_identity": "c" * 64,
                "within_split": True,
                "target_context_available": True,
                "response_matched": True,
            }
            kwargs[field_name] = 1
            with self.subTest(field=field_name), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.transition_target_evaluation_v4(
                    opportunity, source, self.v4_authority, **kwargs
                )

    def test_file_boundary_abstention_is_coordinate_derived(self) -> None:
        row = v4.build_canonical_row_time_identity_v4(
            source_file_identity="hai-test1.csv",
            physical_row_index=53_990,
        )
        opportunity = v4.build_canonical_opportunity_v4(
            self.v4_authority,
            relation_binding_hash=self.rule.relation_binding_hash,
            row_time=row,
        )
        source = v4.build_source_qualification_state_v4(
            opportunity,
            self.v4_authority,
            source_window_identity="d" * 64,
            retained_source_event_identity="e" * 64,
            retained_source_event_census_hash="f" * 64,
        )
        target = v4.transition_target_evaluation_v4(
            opportunity,
            source,
            self.v4_authority,
            target_window_input_identity="1" * 64,
            within_split=True,
            target_context_available=True,
            response_matched=True,
        )
        self.assertEqual(target.target_evaluation_state, ABSTAIN_STATE)
        self.assertEqual(target.abstention_reason, "file_boundary")
        self.assertIsNone(target.decision_row_time_identity)
        self.assertFalse(target.alarm_emitted)

    def test_rule_result_terminal_parent_and_computation_mutations_reject(self) -> None:
        frame, census, envelope = self._case(expected_response=False)
        result = execute_rule_v1(envelope, census, frame, self.bundle, self.resolver)
        self.assertEqual(result.final_state, ANOMALY_STATE)
        self.assertTrue(result.alarm_emitted)
        attacks = (
            {"execution_mode": "REAL_AUTHORIZED_UTILITY_EXECUTION"},
            {"opportunity_id": "2" * 64},
            {"source_event_identity": "3" * 64},
            {"relation_binding_hash": "4" * 64},
            {"source_qualification_identity": "5" * 64},
            {"target_evaluation_identity": "6" * 64},
            {"final_state": ABSTAIN_STATE},
            {"alarm_emitted": False},
            {"decision_physical_row_index": result.decision_physical_row_index + 1},
            {"decision_physical_row_index": True},
            {"numeric_reference_identities": result.numeric_reference_identities[:-1]},
            {"numeric_reference_identities": list(result.numeric_reference_identities)},
            {"evaluator_computation_identity": "7" * 64},
            {"trace_hash": "8" * 64},
        )
        for case_id, changes in enumerate(attacks):
            forged = replace(result, **changes)
            with self.subTest(case=case_id), self.assertRaises(UtilityEvaluatorV1Error):
                validate_rule_execution_result_v1(
                    forged, envelope, census, frame, self.bundle, self.resolver
                )
        reconstructed = RuleExecutionResultV1(
            **{field.name: getattr(result, field.name) for field in fields(result)}
        )
        self_rehashed = replace(
            reconstructed,
            source_event_identity="9" * 64,
            trace_hash=stable_hash_v1(
                {"forged": True, "source_event_identity": "9" * 64}
            ),
        )
        with self.assertRaises(UtilityEvaluatorV1Error):
            validate_rule_execution_result_v1(
                self_rehashed, envelope, census, frame, self.bundle, self.resolver
            )

    def test_only_canonical_unavailable_runtime_context_abstains(self) -> None:
        frame, census, envelope = self._case(expected_response=False, length=25)
        result = execute_rule_v1(envelope, census, frame, self.bundle, self.resolver)
        self.assertEqual(result.final_state, ABSTAIN_STATE)
        self.assertFalse(result.alarm_emitted)
        self.assertIsNotNone(result.source_qualification_identity)
        self.assertIsNotNone(result.target_evaluation_identity)
        self.assertIsNone(result.decision_physical_row_index)
        self.assertEqual(
            validate_rule_execution_result_v1(
                result, envelope, census, frame, self.bundle, self.resolver
            ),
            result.trace_hash,
        )

    def test_malformed_authority_schema_numeric_coordinate_and_provenance_never_abstain(self) -> None:
        frame, census, envelope = self._case(expected_response=False)
        result = execute_rule_v1(envelope, census, frame, self.bundle, self.resolver)
        opportunity = envelope.canonical_opportunity
        reconstructed_bundle = EvaluatorAuthorityBundleV1(
            **{field.name: getattr(self.bundle, field.name) for field in fields(self.bundle)}
        )
        wrong_coordinate = _forge_factory_object(
            opportunity, physical_row_index=opportunity.physical_row_index + 1
        )
        wrong_relation = _forge_factory_object(
            opportunity, relation_binding_hash="a" * 64
        )
        row = frame.rows[0]
        int_pair_values = list(row.feature_values)
        int_pair_values[0] = (int_pair_values[0][0], 0)
        wrong_row = replace(row, feature_values=tuple(int_pair_values))
        wrong_frame = replace(frame, rows=(wrong_row, *frame.rows[1:]))
        calls = (
            lambda: execute_rule_v1(envelope, census, replace(frame, frame_hash="b" * 64), self.bundle, self.resolver),
            lambda: execute_rule_v1(envelope, census, replace(frame, feature_schema_authority_hash="c" * 64), self.bundle, self.resolver),
            lambda: execute_rule_v1(envelope, census, replace(frame, source_file_identity="hai-test2.csv"), self.bundle, self.resolver),
            lambda: execute_rule_v1(envelope, census, wrong_frame, self.bundle, self.resolver),
            lambda: execute_rule_v1(replace(envelope, isolated_source_event_identity="d" * 64), census, frame, self.bundle, self.resolver),
            lambda: execute_rule_v1(replace(envelope, canonical_opportunity=wrong_coordinate), census, frame, self.bundle, self.resolver),
            lambda: execute_rule_v1(replace(envelope, canonical_opportunity=wrong_relation), census, frame, self.bundle, self.resolver),
            lambda: execute_rule_v1(envelope, replace(census, census_hash="e" * 64), frame, self.bundle, self.resolver),
            lambda: execute_rule_v1(envelope, census, frame, reconstructed_bundle, self.resolver),
            lambda: execute_rule_v1(envelope, census, frame, self.bundle, object()),
            lambda: validate_rule_execution_result_v1(replace(result, final_state=ABSTAIN_STATE), envelope, census, frame, self.bundle, self.resolver),
        )
        accepted_abstentions = 0
        for case_id, call in enumerate(calls):
            with self.subTest(case=case_id):
                try:
                    observed = call()
                except (UtilityEvaluatorV1Error, v4.UtilityProtocolV4Error):
                    continue
                if (
                    isinstance(observed, RuleExecutionResultV1)
                    and observed.final_state == ABSTAIN_STATE
                ):
                    accepted_abstentions += 1
                self.fail("malformed rule/state input did not fail closed")
        self.assertEqual(accepted_abstentions, MALFORMED_TO_ABSTAIN_ACCEPTED)

    def test_attack_coverage_declarations_match_explicit_audit_scope(self) -> None:
        self.assertGreaterEqual(UNIQUE_RULE_STATE_ATTACK_CLASSES, 55)
        self.assertGreaterEqual(RAW_RULE_STATE_ADVERSARIAL_CASES, 80)
        self.assertEqual(MALFORMED_TO_ABSTAIN_ACCEPTED, 0)
        self.assertEqual(SUPPLEMENT_RELATION_EXECUTION_ACCEPTED, 0)
        self.assertEqual(AUTHORITATIVE_STATE_FORGERIES_ACCEPTED, 0)


if __name__ == "__main__":
    unittest.main()
