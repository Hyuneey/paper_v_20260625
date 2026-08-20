"""Independent R2 rule/state/provenance audit.

The oracle in this file is the frozen V4 authority and its public lower
authority inputs.  Existing evaluator tests are not imported.  All execution
is in-memory ``SYNTHETIC_CONTRACT_ONLY`` and no private registry is opened.
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
    SyntheticNumericResolverV1,
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
    UtilityEvaluatorV1Error,
    stable_hash_v1,
)


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_V4_AUTHORITY = "1a6200adce791ddd9be8d87b566d47b65e78c1735829d0f91f4ea22127ad1343"
EXPECTED_MAIN_DESCRIPTOR = "665af1d58d672dfe8109c01e5dcb4e8f19aa2303a8f6100bfd20b3272c3bd928"
EXPECTED_RELATION_COUNT = 42

# Each entry represents a distinct authority/provenance semantic, rather than
# repeated values of one mutation.  Raw cases include all concrete mutations.
UNIQUE_RULE_STATE_ATTACK_CLASSES = 52
RAW_RULE_STATE_ADVERSARIAL_CASES = 73
MALFORMED_TO_ABSTAIN_ACCEPTED = 0


def _load(relative_path: str) -> dict[str, object]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def _build_lower_v4_authority() -> v4.UtilityProtocolV4CanonicalAuthority:
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


def _numeric_value(role: str, *, source_threshold: float = 1.0) -> int | float:
    return {
        "source_step_threshold": source_threshold,
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


def _bypass_mutation(value: object, **changes: object) -> object:
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


class UtilityEvaluatorV1R2IndependentRuleStateAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.v4_authority = _build_lower_v4_authority()
        if cls.v4_authority.authority_hash != EXPECTED_V4_AUTHORITY:
            raise AssertionError("lower V4 authority replay differs")
        if cls.v4_authority.numeric_authority.descriptor_hash != EXPECTED_MAIN_DESCRIPTOR:
            raise AssertionError("lower MAIN descriptor replay differs")
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
            cls.bundle, cls.main_records, cls.supplement_records
        )

    @classmethod
    def _frame(
        cls,
        *,
        expected_response: bool,
        start: int = 80,
        length: int = 100,
        event_index: int = 100,
    ):
        response_start = event_index + cls.rule.selected_horizon_seconds
        rows = []
        for physical in range(start, start + length):
            values = []
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
    def _case(cls, *, expected_response: bool = True, **frame_options: object):
        frame = cls._frame(expected_response=expected_response, **frame_options)
        census = enumerate_full_census_v1(frame, cls.bundle, cls.resolver)
        envelope = next(
            item
            for item in census.relation_opportunities
            if item.canonical_opportunity.relation_binding_hash
            == cls.rule.relation_binding_hash
        )
        return frame, census, envelope

    def test_lower_rule_oracle_binds_all_42_relations_and_ten_main_roles(self) -> None:
        self.assertEqual(len(self.v4_authority.rule_descriptors), EXPECTED_RELATION_COUNT)
        self.assertEqual(self.v4_authority.full_census_plan.portfolio_identity, "COMMON-42")
        self.assertFalse(v4.T2_UTILITY_SCOPE_AUTHORIZED)
        self.assertEqual(len(self.main_records), 420)
        self.assertEqual(len(self.supplement_records), 6)
        for rule in self.v4_authority.rule_descriptors:
            with self.subTest(relation=rule.relation_binding_hash):
                self.assertEqual(
                    tuple(role for role, _ in rule.numeric_reference_bindings),
                    v4.UTILITY_NUMERIC_ROLES,
                )
                self.assertEqual(len({ref for _, ref in rule.numeric_reference_bindings}), 10)
                self.assertEqual(
                    rule.numeric_authority_descriptor_hash,
                    EXPECTED_MAIN_DESCRIPTOR,
                )

    def test_canonical_execution_replays_rule_parents_and_computation_identity(self) -> None:
        frame, census, envelope = self._case()
        opportunity = envelope.canonical_opportunity
        rule = self.v4_authority.rule_by_binding(opportunity.relation_binding_hash)
        result = execute_rule_v1(envelope, census, frame, self.bundle, self.resolver)
        self.assertEqual(opportunity.relation_identity, rule.relation_identity)
        self.assertEqual(opportunity.semantic_execution_hash, rule.semantic_execution_hash)
        self.assertEqual(opportunity.source, rule.source)
        self.assertEqual(opportunity.target, rule.target)
        self.assertEqual(opportunity.source_direction, rule.source_direction)
        self.assertEqual(opportunity.target_direction, rule.target_direction)
        self.assertEqual(opportunity.selected_horizon_seconds, rule.selected_horizon_seconds)
        self.assertEqual(opportunity.rule_descriptor_hash, rule.descriptor_hash)
        self.assertEqual(opportunity.numeric_authority_descriptor_hash, EXPECTED_MAIN_DESCRIPTOR)
        references = tuple(reference for _, reference in rule.numeric_reference_bindings)
        expected_computation = stable_hash_v1(
            {
                "artifact_type": "task039e3_r2r_utility_evaluator_v1_computation",
                "authority_bundle_hash": validate_evaluator_authority_bundle_v1(self.bundle),
                "evaluator_version": EVALUATOR_VERSION,
                "execution_mode": SYNTHETIC_CONTRACT_ONLY,
                "frame_hash": frame.frame_hash,
                "isolated_source_event_identity": envelope.isolated_source_event_identity,
                "numeric_reference_identities": list(references),
                "opportunity_id": opportunity.opportunity_id,
                "rule_descriptor_hash": rule.descriptor_hash,
            }
        )
        self.assertEqual(result.evaluator_computation_identity, expected_computation)
        self.assertEqual(result.numeric_reference_identities, references)
        self.assertEqual(result.final_state, EXPECTED_RESPONSE_STATE)
        self.assertFalse(result.alarm_emitted)

    def test_every_opportunity_semantic_and_coordinate_substitution_rejects(self) -> None:
        frame, census, envelope = self._case()
        opportunity = envelope.canonical_opportunity
        changed = (
            {"relation_identity": "relation-substitute"},
            {"relation_binding_hash": "a" * 64},
            {"semantic_execution_hash": "b" * 64},
            {"source": opportunity.target},
            {"target": opportunity.source},
            {"source_direction": "step_down" if opportunity.source_direction == "step_up" else "step_up"},
            {"target_direction": "decrease" if opportunity.target_direction == "increase" else "increase"},
            {"selected_horizon_seconds": opportunity.selected_horizon_seconds + 1},
            {"rule_descriptor_hash": "c" * 64},
            {"numeric_authority_descriptor_hash": "d" * 64},
            {"event_policy_hash": "e" * 64},
            {"opportunity_enumeration_policy_hash": "f" * 64},
            {"canonical_row_time_identity": "1" * 64},
            {"physical_row_index": opportunity.physical_row_index + 1},
            {"timestamp_identity": "2" * 64},
            {"opportunity_id": "3" * 64},
        )
        for index, mutation in enumerate(changed):
            forged = _bypass_mutation(opportunity, **mutation)
            forged_envelope = replace(envelope, canonical_opportunity=forged)
            with self.subTest(case=index), self.assertRaises(UtilityEvaluatorV1Error):
                execute_rule_v1(
                    forged_envelope, census, frame, self.bundle, self.resolver
                )

    def test_main_numeric_binding_and_role_substitutions_reject(self) -> None:
        target_index = next(
            index
            for index, record in enumerate(self.main_records)
            if record.numeric_role == "target_noise_scale"
        )
        source_index = next(
            index
            for index, record in enumerate(self.main_records)
            if record.numeric_role == "source_step_threshold"
        )
        target_record = self.main_records[target_index]
        source_record = self.main_records[source_index]
        supplement_reference = supplement.supplement_reference_identity_v1(
            supplement.SUPPLEMENT_SOURCES[0], "source_step_threshold"
        )
        mutations = (
            (target_index, replace(target_record, reference_identity=supplement_reference)),
            (source_index, replace(source_record, reference_identity=supplement_reference)),
            (target_index, replace(target_record, numeric_role="source_step_threshold")),
            (target_index, replace(target_record, relation_binding_hash="a" * 64)),
            (target_index, replace(target_record, source=supplement.SUPPLEMENT_SOURCES[0])),
            (target_index, replace(target_record, authority_plane=SUPPLEMENT_PURPOSE)),
            (target_index, replace(target_record, value=1)),
        )
        for case, (index, record) in enumerate(mutations):
            changed = (*self.main_records[:index], record, *self.main_records[index + 1 :])
            with self.subTest(case=case), self.assertRaises(UtilityEvaluatorV1Error):
                build_synthetic_numeric_resolver_v1(
                    self.bundle, changed, self.supplement_records
                )

    def test_supplement_census_authority_cannot_enter_relation_semantics(self) -> None:
        record = self.supplement_records[0]
        cases = (
            replace(record, numeric_role="target_noise_scale", reference_identity="a" * 64),
            replace(
                record,
                numeric_role="target_response_window_seconds",
                reference_identity="b" * 64,
            ),
            replace(
                record,
                relation_binding_hash=self.rule.relation_binding_hash,
            ),
        )
        for index, changed_record in enumerate(cases):
            changed = (changed_record, *self.supplement_records[1:])
            with self.subTest(case=index), self.assertRaises(UtilityEvaluatorV1Error):
                build_synthetic_numeric_resolver_v1(
                    self.bundle, self.main_records, changed
                )

    def test_source_qualification_fixed_parents_and_self_rehash_reject(self) -> None:
        _, census, envelope = self._case()
        opportunity = envelope.canonical_opportunity
        source_state = v4.build_source_qualification_state_v4(
            opportunity,
            self.v4_authority,
            source_window_identity="1" * 64,
            retained_source_event_identity=envelope.isolated_source_event_identity,
            retained_source_event_census_hash=census.source_census_identity,
        )
        self.assertEqual(
            v4.validate_source_qualification_state_v4(
                source_state, opportunity, self.v4_authority
            ),
            source_state.source_qualification_identity,
        )
        mutations = (
            {"opportunity_id": "2" * 64},
            {"rule_descriptor_hash": "3" * 64},
            {"source_window_identity": "4" * 64},
            {"retained_source_event_identity": "5" * 64},
            {"retained_source_event_census_hash": "6" * 64},
            {"source_step_reference_identity": "7" * 64},
            {"source_stability_reference_identity": "8" * 64},
            {"event_policy_hash": "9" * 64},
            {"state": "abstain"},
            {"source_qualification_identity": "a" * 64},
        )
        for index, mutation in enumerate(mutations):
            forged = _bypass_mutation(source_state, **mutation)
            with self.subTest(case=index), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_source_qualification_state_v4(
                    forged, opportunity, self.v4_authority
                )

        self_rehashed = _bypass_mutation(
            source_state,
            opportunity_id="b" * 64,
        )
        object.__setattr__(
            self_rehashed,
            "source_qualification_identity",
            stable_hash_v1(_source_state_payload(self_rehashed)),
        )
        with self.assertRaises(v4.UtilityProtocolV4Error):
            v4.validate_source_qualification_state_v4(
                self_rehashed, opportunity, self.v4_authority
            )

    def test_target_state_parent_window_transition_and_self_rehash_reject(self) -> None:
        _, census, envelope = self._case()
        opportunity = envelope.canonical_opportunity
        source_state = v4.build_source_qualification_state_v4(
            opportunity,
            self.v4_authority,
            source_window_identity="1" * 64,
            retained_source_event_identity=envelope.isolated_source_event_identity,
            retained_source_event_census_hash=census.source_census_identity,
        )
        target_state = v4.transition_target_evaluation_v4(
            opportunity,
            source_state,
            self.v4_authority,
            target_window_input_identity="2" * 64,
            within_split=True,
            target_context_available=True,
            response_matched=True,
        )
        self.assertEqual(
            v4.validate_target_evaluation_state_v4(
                target_state, opportunity, source_state, self.v4_authority
            ),
            target_state.terminal_state_provenance_hash,
        )
        mutations = (
            {"opportunity_id": "3" * 64},
            {"rule_descriptor_hash": "4" * 64},
            {"source_qualification_identity": "5" * 64},
            {"target_window_input_identity": "6" * 64},
            {"target_noise_reference_identity": "7" * 64},
            {"numeric_authority_descriptor_hash": "8" * 64},
            {"transition_policy_hash": "9" * 64},
            {"physical_row_count": target_state.physical_row_count - 1},
            {"within_split": 1},
            {"target_context_available": 1},
            {"response_matched": 1},
            {"target_evaluation_state": ANOMALY_STATE},
            {"decision_row_time_identity": "a" * 64},
            {"alarm_emitted": True},
            {"abstention_reason": "split_boundary"},
            {"terminal_state_provenance_hash": "b" * 64},
        )
        for index, mutation in enumerate(mutations):
            forged = _bypass_mutation(target_state, **mutation)
            with self.subTest(case=index), self.assertRaises(v4.UtilityProtocolV4Error):
                v4.validate_target_evaluation_state_v4(
                    forged, opportunity, source_state, self.v4_authority
                )

        self_rehashed = _bypass_mutation(
            target_state,
            source_qualification_identity="c" * 64,
        )
        object.__setattr__(
            self_rehashed,
            "terminal_state_provenance_hash",
            stable_hash_v1(_target_state_payload(self_rehashed)),
        )
        with self.assertRaises(v4.UtilityProtocolV4Error):
            v4.validate_target_evaluation_state_v4(
                self_rehashed, opportunity, source_state, self.v4_authority
            )

    def test_direct_v4_state_construction_is_factory_only_and_non_authoritative(self) -> None:
        with self.assertRaises(v4.UtilityProtocolV4Error):
            v4.SourceQualificationStateV4(object())
        with self.assertRaises(v4.UtilityProtocolV4Error):
            v4.TargetEvaluationStateV4(object())

        _, census, envelope = self._case()
        opportunity = envelope.canonical_opportunity
        source_state = v4.build_source_qualification_state_v4(
            opportunity,
            self.v4_authority,
            source_window_identity="1" * 64,
            retained_source_event_identity=envelope.isolated_source_event_identity,
            retained_source_event_census_hash=census.source_census_identity,
        )
        target_state = v4.transition_target_evaluation_v4(
            opportunity,
            source_state,
            self.v4_authority,
            target_window_input_identity="2" * 64,
            within_split=True,
            target_context_available=True,
            response_matched=True,
        )
        with self.assertRaises(v4.UtilityProtocolV4Error):
            v4.validate_authoritative_terminal_metric_custody_v4_r1(
                target_state,
                source_state,
                opportunity,
                v4.build_canonical_window_coordinate_authority_v4_r1(
                    opportunity, self.v4_authority
                ),
                self.v4_authority,
            )

    def test_rule_result_parent_transition_and_computation_mutations_reject(self) -> None:
        frame, census, envelope = self._case(expected_response=False)
        result = execute_rule_v1(envelope, census, frame, self.bundle, self.resolver)
        self.assertEqual(result.final_state, ANOMALY_STATE)
        mutations = (
            {"execution_mode": "REAL_AUTHORIZED_UTILITY_EXECUTION"},
            {"opportunity_id": "1" * 64},
            {"source_event_identity": "2" * 64},
            {"relation_binding_hash": "3" * 64},
            {"source_qualification_identity": "4" * 64},
            {"target_evaluation_identity": "5" * 64},
            {"final_state": ABSTAIN_STATE},
            {"alarm_emitted": False},
            {"decision_physical_row_index": result.decision_physical_row_index + 1},
            {"numeric_reference_identities": result.numeric_reference_identities[:-1]},
            {"evaluator_computation_identity": "6" * 64},
            {"trace_hash": "7" * 64},
        )
        for index, mutation in enumerate(mutations):
            forged = replace(result, **mutation)
            with self.subTest(case=index), self.assertRaises(UtilityEvaluatorV1Error):
                validate_rule_execution_result_v1(
                    forged,
                    envelope,
                    census,
                    frame,
                    self.bundle,
                    self.resolver,
                )

        reconstructed = RuleExecutionResultV1(
            **{
                field.name: getattr(result, field.name)
                for field in fields(RuleExecutionResultV1)
            }
        )
        forged = replace(
            reconstructed,
            source_event_identity="8" * 64,
            trace_hash=stable_hash_v1(
                {
                    "forged": True,
                    "source_event_identity": "8" * 64,
                }
            ),
        )
        with self.assertRaises(UtilityEvaluatorV1Error):
            validate_rule_execution_result_v1(
                forged, envelope, census, frame, self.bundle, self.resolver
            )

    def test_only_canonical_unavailable_context_abstains(self) -> None:
        frame, census, envelope = self._case(
            expected_response=False,
            length=25,
        )
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

    def test_malformed_authority_schema_numeric_parent_and_coordinates_never_abstain(self) -> None:
        frame, census, envelope = self._case(expected_response=False)
        result = execute_rule_v1(envelope, census, frame, self.bundle, self.resolver)
        opportunity = envelope.canonical_opportunity

        reconstructed_bundle = EvaluatorAuthorityBundleV1(
            **{
                field.name: getattr(self.bundle, field.name)
                for field in fields(EvaluatorAuthorityBundleV1)
            }
        )
        changed_opportunity = _bypass_mutation(
            opportunity, physical_row_index=opportunity.physical_row_index + 1
        )
        calls = (
            lambda: execute_rule_v1(
                envelope, census, replace(frame, frame_hash="1" * 64), self.bundle, self.resolver
            ),
            lambda: execute_rule_v1(
                envelope,
                census,
                replace(frame, source_file_identity="hai-test2.csv"),
                self.bundle,
                self.resolver,
            ),
            lambda: execute_rule_v1(
                replace(envelope, isolated_source_event_identity="2" * 64),
                census,
                frame,
                self.bundle,
                self.resolver,
            ),
            lambda: execute_rule_v1(
                replace(envelope, canonical_opportunity=changed_opportunity),
                census,
                frame,
                self.bundle,
                self.resolver,
            ),
            lambda: execute_rule_v1(
                envelope,
                replace(census, census_hash="3" * 64),
                frame,
                self.bundle,
                self.resolver,
            ),
            lambda: execute_rule_v1(
                envelope, census, frame, reconstructed_bundle, self.resolver
            ),
            lambda: execute_rule_v1(envelope, census, frame, self.bundle, object()),
            lambda: validate_rule_execution_result_v1(
                replace(result, final_state=ABSTAIN_STATE),
                envelope,
                census,
                frame,
                self.bundle,
                self.resolver,
            ),
        )
        accepted_abstentions = 0
        for index, call in enumerate(calls):
            with self.subTest(case=index):
                try:
                    observed = call()
                except UtilityEvaluatorV1Error:
                    continue
                if isinstance(observed, RuleExecutionResultV1) and observed.final_state == ABSTAIN_STATE:
                    accepted_abstentions += 1
                self.fail("malformed rule/state input did not fail closed")
        self.assertEqual(accepted_abstentions, MALFORMED_TO_ABSTAIN_ACCEPTED)


if __name__ == "__main__":
    unittest.main()
