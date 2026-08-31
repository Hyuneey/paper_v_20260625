from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import unittest

from paperworks.validation_v2.exp03_construction_v1 import (
    ConstructionArmV1,
    ConstructionOutcomeV1,
    ConstructionTerminalClassV1,
    Exp03ContractError,
    NATURAL_NAMESPACE,
    STRESS_NAMESPACE,
    TERMINAL_CLASSES,
    aggregate_natural_metrics_v1,
    aggregate_stress_metrics_v1,
    build_natural_schedule_v1,
    build_provider_attempt_receipt_v1,
    build_provider_call_receipt_v1,
    build_provider_execution_authorization_v1,
    build_provider_input_projection_v1,
    build_stress_fixture_receipt_v1,
    build_t1b_draw_v1,
    build_terminal_record_v1,
    execute_provider_transport_v1,
    provider_call_maximum_v1,
    select_t1b_lowest_admissible_v1,
    validate_complete_natural_schedule_v1,
    validate_provider_call_budget_v1,
    verify_provider_call_receipt_v1,
    verify_t1b_selection_v1,
    verify_terminal_record_v1,
    _expected_hash,
)


def h(label: str) -> str:
    return sha256(label.encode("utf-8")).hexdigest()


class Exp03ConstructionV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.auth = build_provider_execution_authorization_v1(
            dg03_approved=True,
            approval_reference="DG03-SYNTHETIC-CONTRACT-TEST",
            provider_id="synthetic-provider",
            model_snapshot="synthetic-model-v1",
            natural_relation_count=1,
            maximum_input_tokens_per_call=100,
            maximum_output_tokens_per_call=100,
            maximum_total_tokens=4_200,
            config_hash=h("config"),
            evidence_projection_hash=h("evidence"),
            model_policy_hash=h("model-policy"),
            template_hash=h("template"),
            privacy_assessment_hash=h("privacy"),
            expected_artifact_hash=h("artifact"),
        )

    def _call(
        self,
        arm: ConstructionArmV1,
        repeat: int,
        index: int,
        *,
        relation: str = "relation-1",
        completion: str = "NONEMPTY_RESPONSE",
    ):
        successful = completion != "PROVIDER_ERROR"
        attempt = build_provider_attempt_receipt_v1(
            authorization=self.auth,
            relation_id=relation,
            arm=arm,
            repeat_index=repeat,
            call_index=index,
            attempt_index=1,
            request_hash=h(f"request-{relation}-{arm.value}-{repeat}-{index}"),
            response_hash=h(f"response-{relation}-{arm.value}-{repeat}-{index}") if successful else None,
            result_class="SUCCESS" if successful else "TERMINAL_PROVIDER_ERROR",
            input_tokens=5,
            output_tokens=4 if successful else 0,
            latency_ms=1.5,
        )
        return build_provider_call_receipt_v1(
            authorization=self.auth,
            attempts=(attempt,),
            completion_class=completion,
        )

    def _terminal(
        self,
        arm: ConstructionArmV1,
        repeat: int,
        outcome: ConstructionOutcomeV1 = ConstructionOutcomeV1.ACCEPTED_PROPOSAL,
        *,
        relation: str = "relation-1",
        calls=(),
        reason: str | None = None,
        actions=(),
        semantic: bool | None = None,
        selection=None,
    ):
        reasons = {
            ConstructionOutcomeV1.ACCEPTED_PROPOSAL: "VERIFIER_ACCEPTED",
            ConstructionOutcomeV1.ALL_DRAWS_FAILED: "T1B_ALL_DRAWS_FAILED",
            ConstructionOutcomeV1.INTENTIONAL_NO_RULE: "MODEL_INTENTIONAL_NO_RULE",
            ConstructionOutcomeV1.UNSUPPORTED_EVIDENCE: "PRECONSTRUCTION_EVIDENCE_INELIGIBLE",
            ConstructionOutcomeV1.PROVIDER_ERROR: "PROVIDER_TRANSPORT_OR_REFUSAL",
            ConstructionOutcomeV1.EMPTY_RESPONSE: "EMPTY_OR_INCOMPLETE_STRUCTURED_RESPONSE",
            ConstructionOutcomeV1.PARSE_FAILURE: "STRICT_PARSE_OR_SCHEMA_FAILURE",
            ConstructionOutcomeV1.VERIFIER_REJECTION: "DETERMINISTIC_VERIFIER_REJECTION",
            ConstructionOutcomeV1.BUDGET_EXHAUSTION: "REPAIR_BUDGET_EXHAUSTED",
            ConstructionOutcomeV1.RETRIEVAL_FAILURE: "RETRIEVAL_IDENTITY_OR_INTEGRITY_FAILURE",
            ConstructionOutcomeV1.SYSTEM_ERROR: "LOCAL_SYSTEM_OR_CUSTODY_FAILURE",
        }
        proposal = h(f"proposal-{relation}-{arm.value}-{repeat}") if outcome in {
            ConstructionOutcomeV1.ACCEPTED_PROPOSAL,
            ConstructionOutcomeV1.VERIFIER_REJECTION,
        } else None
        verifier = h(f"verifier-{relation}-{arm.value}-{repeat}") if proposal else None
        if outcome.value in {"INTENTIONAL_NO_RULE", "UNSUPPORTED_EVIDENCE"} and semantic is None:
            semantic = True
        if arm is ConstructionArmV1.T1_B and selection is None and len(calls) == 3:
            draws = tuple(
                build_t1b_draw_v1(
                    authorization=self.auth,
                    draw_index=index,
                    call_receipt=call,
                    outcome=ConstructionOutcomeV1.ACCEPTED_PROPOSAL,
                    reason_code="VERIFIER_ACCEPTED",
                    proposal_hash=proposal if index == 1 else h(f"proposal-draw-{repeat}-{index}"),
                    verifier_result_hash=verifier if index == 1 else h(f"verifier-draw-{repeat}-{index}"),
                )
                for index, call in enumerate(calls, 1)
            )
            selection = select_t1b_lowest_admissible_v1(draws, self.auth)
        if arm is ConstructionArmV1.T1_B and selection is not None:
            if selection.selected_draw_index is None:
                proposal = None
                verifier = None
            else:
                selected = selection.draw_outcomes[selection.selected_draw_index - 1]
                proposal = selected.proposal_hash
                verifier = selected.verifier_result_hash
        return build_terminal_record_v1(
            authorization=self.auth if calls else None,
            relation_id=relation,
            arm=arm,
            repeat_index=repeat,
            outcome=outcome,
            reason_code=reason or reasons[outcome],
            config_hash=h("config"),
            evidence_projection_hash=h("evidence"),
            model_policy_hash=h("model-policy"),
            template_hash=h("template"),
            proposal_hash=proposal,
            verifier_result_hash=verifier,
            call_receipts=calls,
            t1b_selection_receipt=selection,
            controller_actions=actions,
            semantic_no_rule_confirmed=semantic,
        )

    def test_exact_nine_terminal_taxonomy_and_no_generic_no_rule(self) -> None:
        self.assertEqual(len(TERMINAL_CLASSES), 9)
        self.assertEqual(set(TERMINAL_CLASSES), {item.value for item in ConstructionTerminalClassV1})
        self.assertNotIn("NO_RULE", TERMINAL_CLASSES)
        for name in (
            "PROVIDER_ERROR", "EMPTY_RESPONSE", "PARSE_FAILURE", "VERIFIER_REJECTION",
            "BUDGET_EXHAUSTION", "RETRIEVAL_FAILURE", "SYSTEM_ERROR",
        ):
            self.assertNotIn(name, {"INTENTIONAL_NO_RULE", "UNSUPPORTED_EVIDENCE"})

    def test_provider_disabled_default_and_transport_absent(self) -> None:
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_PROVIDER_NOT_AUTHORIZED"):
            build_provider_execution_authorization_v1(
                dg03_approved=False, approval_reference="pending", provider_id="p",
                model_snapshot="m", natural_relation_count=1,
                maximum_input_tokens_per_call=1, maximum_output_tokens_per_call=1,
                maximum_total_tokens=1, config_hash=h("c"),
                evidence_projection_hash=h("e"), model_policy_hash=h("m"),
                template_hash=h("t"), privacy_assessment_hash=h("p"),
                expected_artifact_hash=h("a"),
            )
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_PROVIDER_NOT_AUTHORIZED"):
            build_provider_attempt_receipt_v1(
                authorization=None, relation_id="r", arm=ConstructionArmV1.T1,
                repeat_index=1, call_index=1, attempt_index=1,
                request_hash=h("r"), response_hash=h("s"), result_class="SUCCESS",
                input_tokens=0, output_tokens=0, latency_ms=0,
            )
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_PROVIDER_TRANSPORT_NOT_IMPLEMENTED"):
            execute_provider_transport_v1(self.auth)

    def test_call_and_attempt_receipts_bind_all_authority_and_replay(self) -> None:
        call = self._call(ConstructionArmV1.T1, 1, 1)
        self.assertEqual(call.namespace, NATURAL_NAMESPACE)
        self.assertEqual(verify_provider_call_receipt_v1(call, self.auth), call.self_hash)
        self.assertEqual(call.config_hash, self.auth.config_hash)
        self.assertEqual(call.evidence_projection_hash, self.auth.evidence_projection_hash)
        self.assertEqual(call.model_policy_hash, self.auth.model_policy_hash)
        self.assertEqual(call.template_hash, self.auth.template_hash)
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_CALL_REPLAY_MISMATCH"):
            verify_provider_call_receipt_v1(replace(call, output_tokens=99), self.auth)

    def test_partial_attempt_and_stale_authority_fail_closed(self) -> None:
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_PARTIAL_CALL_RECEIPT"):
            build_provider_call_receipt_v1(
                authorization=self.auth, attempts=(), completion_class="PROVIDER_ERROR"
            )
        attempt = build_provider_attempt_receipt_v1(
            authorization=self.auth, relation_id="r", arm=ConstructionArmV1.T1,
            repeat_index=1, call_index=1, attempt_index=2,
            request_hash=h("request"), response_hash=h("response"), result_class="SUCCESS",
            input_tokens=1, output_tokens=1, latency_ms=1,
        )
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_ATTEMPT_SEQUENCE_INVALID"):
            build_provider_call_receipt_v1(
                authorization=self.auth, attempts=(attempt,), completion_class="NONEMPTY_RESPONSE"
            )
        changed = build_provider_execution_authorization_v1(
            dg03_approved=True, approval_reference="DG03-OTHER", provider_id="synthetic-provider",
            model_snapshot="other-model", natural_relation_count=1,
            maximum_input_tokens_per_call=100, maximum_output_tokens_per_call=100,
            maximum_total_tokens=4_200, config_hash=h("config"),
            evidence_projection_hash=h("evidence"), model_policy_hash=h("model-policy"),
            template_hash=h("template"), privacy_assessment_hash=h("privacy"),
            expected_artifact_hash=h("artifact"),
        )
        with self.assertRaisesRegex(Exp03ContractError, "ATTEMPT_AUTHORITY_MISMATCH"):
            verify_provider_call_receipt_v1(self._call(ConstructionArmV1.T1, 1, 1), changed)

    def test_budget_is_exactly_21n_and_duplicate_calls_rejected(self) -> None:
        self.assertEqual(provider_call_maximum_v1(2), 42)
        call = self._call(ConstructionArmV1.T1, 1, 1)
        self.assertEqual(validate_provider_call_budget_v1((call,), self.auth), 1)
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_DUPLICATE_CALL"):
            validate_provider_call_budget_v1((call, call), self.auth)

    def test_provider_visible_projection_is_closed_and_aggregate_only(self) -> None:
        payload = {
            "relation_id": "relation-1", "source_id": "source-1", "target_id": "target-1",
            "source_direction": "step_up", "target_direction": "increase",
            "selected_horizon_seconds": 10,
            "numeric_reference_ids": ["numeric-a", "numeric-b"],
            "normal_evidence_summary_hash": h("normal-summary"),
        }
        projection = build_provider_input_projection_v1(payload, self.auth)
        self.assertEqual(projection.evidence_projection_hash, self.auth.evidence_projection_hash)
        for prohibited in ("raw_rows", "labels", "test1", "test2", "local_path", "credentials", "other_arm_result"):
            with self.subTest(prohibited=prohibited), self.assertRaisesRegex(
                Exp03ContractError, "PROVIDER_PROJECTION_CLOSED_FIELD_VIOLATION"
            ):
                build_provider_input_projection_v1({**payload, prohibited: "forbidden"}, self.auth)

    def test_fourth_t2_call_rejected_and_exact_arm_counts_enforced(self) -> None:
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_CALL_INDEX_INVALID"):
            self._call(ConstructionArmV1.T2, 1, 4)
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_ARM_CALL_COUNT_INVALID"):
            self._terminal(ConstructionArmV1.T1, 1, calls=())
        two = (self._call(ConstructionArmV1.T1_B, 1, 1), self._call(ConstructionArmV1.T1_B, 1, 2))
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_ARM_CALL_COUNT_INVALID"):
            self._terminal(ConstructionArmV1.T1_B, 1, calls=two)
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_T2_CALL_REQUIRED"):
            self._terminal(ConstructionArmV1.T2, 1, calls=())

    def test_refusal_empty_and_parse_failure_remain_distinct(self) -> None:
        provider_call = self._call(ConstructionArmV1.T2, 1, 1, completion="PROVIDER_ERROR")
        empty_call = self._call(ConstructionArmV1.T2, 2, 1, completion="EMPTY_RESPONSE")
        parse_call = self._call(ConstructionArmV1.T2, 3, 1)
        records = (
            self._terminal(ConstructionArmV1.T2, 1, ConstructionOutcomeV1.PROVIDER_ERROR, calls=(provider_call,)),
            self._terminal(ConstructionArmV1.T2, 2, ConstructionOutcomeV1.EMPTY_RESPONSE, calls=(empty_call,)),
            self._terminal(ConstructionArmV1.T2, 3, ConstructionOutcomeV1.PARSE_FAILURE, calls=(parse_call,)),
        )
        self.assertEqual({item.outcome for item in records}, {"PROVIDER_ERROR", "EMPTY_RESPONSE", "PARSE_FAILURE"})

    def test_reason_class_mismatch_and_failure_to_no_rule_rejected(self) -> None:
        calls = (self._call(ConstructionArmV1.T2, 1, 1),)
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_REASON_CLASS_MISMATCH"):
            self._terminal(
                ConstructionArmV1.T2, 1, ConstructionOutcomeV1.PARSE_FAILURE,
                calls=calls, reason="MODEL_INTENTIONAL_NO_RULE",
            )
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_FAILURE_TO_NO_RULE_FORBIDDEN"):
            self._terminal(
                ConstructionArmV1.T2, 1, ConstructionOutcomeV1.PARSE_FAILURE,
                calls=calls, semantic=True,
            )

    def test_unsupported_proposal_is_verifier_rejection_not_unsupported_evidence(self) -> None:
        call = self._call(ConstructionArmV1.T1, 1, 1)
        record = self._terminal(
            ConstructionArmV1.T1, 1, ConstructionOutcomeV1.VERIFIER_REJECTION, calls=(call,)
        )
        self.assertEqual(record.outcome, "VERIFIER_REJECTION")
        self.assertIsNotNone(record.proposal_hash)
        self.assertIsNotNone(record.verifier_result_hash)
        unsupported = self._terminal(
            ConstructionArmV1.T0, 0, ConstructionOutcomeV1.UNSUPPORTED_EVIDENCE, calls=()
        )
        self.assertEqual(unsupported.reason_code, "PRECONSTRUCTION_EVIDENCE_INELIGIBLE")

    def test_budget_exhaustion_requires_three_t2_calls_in_example(self) -> None:
        calls = tuple(self._call(ConstructionArmV1.T2, 1, index) for index in (1, 2, 3))
        record = self._terminal(
            ConstructionArmV1.T2, 1, ConstructionOutcomeV1.BUDGET_EXHAUSTION,
            calls=calls, actions=("revise", "retrieve"),
        )
        self.assertEqual(record.generation_calls, 3)
        self.assertEqual(record.outcome, "BUDGET_EXHAUSTION")

    def test_t1b_exact_three_lowest_admissible_and_causes_preserved(self) -> None:
        calls = tuple(self._call(ConstructionArmV1.T1_B, 1, index) for index in (1, 2, 3))
        draws = (
            build_t1b_draw_v1(
                authorization=self.auth, draw_index=1, call_receipt=calls[0],
                outcome=ConstructionOutcomeV1.PARSE_FAILURE,
                reason_code="STRICT_PARSE_OR_SCHEMA_FAILURE",
            ),
            build_t1b_draw_v1(
                authorization=self.auth, draw_index=2, call_receipt=calls[1],
                outcome=ConstructionOutcomeV1.ACCEPTED_PROPOSAL,
                reason_code="VERIFIER_ACCEPTED", proposal_hash=h("p2"), verifier_result_hash=h("v2"),
            ),
            build_t1b_draw_v1(
                authorization=self.auth, draw_index=3, call_receipt=calls[2],
                outcome=ConstructionOutcomeV1.ACCEPTED_PROPOSAL,
                reason_code="VERIFIER_ACCEPTED", proposal_hash=h("p3"), verifier_result_hash=h("v3"),
            ),
        )
        selection = select_t1b_lowest_admissible_v1(draws, self.auth)
        self.assertEqual(selection.selected_draw_index, 2)
        self.assertEqual(selection.preserved_failure_causes, ("PARSE_FAILURE",))
        self.assertEqual(verify_t1b_selection_v1(selection, self.auth), selection.self_hash)
        with self.assertRaisesRegex(Exp03ContractError, "T1B_SELECTION_REPLAY_MISMATCH"):
            verify_t1b_selection_v1(replace(selection, selected_draw_index=3), self.auth)
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_T1B_EXACT_THREE_REQUIRED"):
            select_t1b_lowest_admissible_v1(draws[:2], self.auth)

        terminal = self._terminal(
            ConstructionArmV1.T1_B,
            1,
            calls=calls,
            selection=selection,
        )
        self.assertEqual(terminal.proposal_hash, draws[1].proposal_hash)
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_T1B_SELECTION_BINDING_MISMATCH"):
            build_terminal_record_v1(
                authorization=self.auth,
                relation_id="relation-1",
                arm=ConstructionArmV1.T1_B,
                repeat_index=1,
                outcome=ConstructionOutcomeV1.ACCEPTED_PROPOSAL,
                reason_code="VERIFIER_ACCEPTED",
                config_hash=h("config"),
                evidence_projection_hash=h("evidence"),
                model_policy_hash=h("model-policy"),
                template_hash=h("template"),
                proposal_hash=h("wrong-proposal"),
                verifier_result_hash=draws[1].verifier_result_hash,
                call_receipts=calls,
                t1b_selection_receipt=selection,
            )

    def test_t1b_all_failed_retains_draw_level_causes(self) -> None:
        calls = (
            self._call(ConstructionArmV1.T1_B, 2, 1, completion="PROVIDER_ERROR"),
            self._call(ConstructionArmV1.T1_B, 2, 2, completion="EMPTY_RESPONSE"),
            self._call(ConstructionArmV1.T1_B, 2, 3),
        )
        outcomes = (
            (ConstructionOutcomeV1.PROVIDER_ERROR, "PROVIDER_TRANSPORT_OR_REFUSAL"),
            (ConstructionOutcomeV1.EMPTY_RESPONSE, "EMPTY_OR_INCOMPLETE_STRUCTURED_RESPONSE"),
            (ConstructionOutcomeV1.PARSE_FAILURE, "STRICT_PARSE_OR_SCHEMA_FAILURE"),
        )
        draws = tuple(
            build_t1b_draw_v1(
                authorization=self.auth, draw_index=index, call_receipt=call,
                outcome=outcome, reason_code=reason,
            )
            for index, call, (outcome, reason) in zip((1, 2, 3), calls, outcomes)
        )
        selection = select_t1b_lowest_admissible_v1(draws, self.auth)
        self.assertEqual(selection.selection_outcome, "ALL_DRAWS_FAILED")
        self.assertEqual(selection.preserved_failure_causes, tuple(item[0].value for item in outcomes))
        terminal = self._terminal(
            ConstructionArmV1.T1_B,
            2,
            ConstructionOutcomeV1.ALL_DRAWS_FAILED,
            calls=calls,
            selection=selection,
        )
        self.assertEqual(terminal.outcome, "ALL_DRAWS_FAILED")

    def test_complete_schedule_has_t0_once_and_stochastic_arms_three_times(self) -> None:
        schedule = build_natural_schedule_v1(
            relation_ids=("r2", "r1"), cohort_hash=h("cohort"),
            config_hash=h("config"), evidence_projection_hash=h("evidence"),
        )
        self.assertEqual(len(schedule.entries), 20)
        self.assertEqual(sum(item.arm == "T0" for item in schedule.entries), 2)
        self.assertEqual(sum(item.arm == "T1-B" for item in schedule.entries), 6)
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_RELATION_SCHEDULE_INVALID"):
            build_natural_schedule_v1(
                relation_ids=("r", "r"), cohort_hash=h("cohort"),
                config_hash=h("config"), evidence_projection_hash=h("evidence"),
            )

    def test_complete_schedule_accepts_exact_records_and_rejects_missing_duplicate(self) -> None:
        schedule = build_natural_schedule_v1(
            relation_ids=("relation-1",), cohort_hash=h("cohort"),
            config_hash=h("config"), evidence_projection_hash=h("evidence"),
        )
        records = [self._terminal(ConstructionArmV1.T0, 0)]
        for repeat in (1, 2, 3):
            records.append(self._terminal(
                ConstructionArmV1.T1, repeat,
                calls=(self._call(ConstructionArmV1.T1, repeat, 1),),
            ))
            t1b_calls = tuple(self._call(ConstructionArmV1.T1_B, repeat, index) for index in (1, 2, 3))
            records.append(self._terminal(ConstructionArmV1.T1_B, repeat, calls=t1b_calls))
            records.append(self._terminal(
                ConstructionArmV1.T2, repeat,
                calls=(self._call(ConstructionArmV1.T2, repeat, 1),),
            ))
        self.assertEqual(validate_complete_natural_schedule_v1(schedule, records, self.auth), schedule.self_hash)
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_INCOMPLETE_SCHEDULE"):
            validate_complete_natural_schedule_v1(schedule, records[:-1], self.auth)
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_DUPLICATE_TERMINAL"):
            validate_complete_natural_schedule_v1(schedule, (*records, records[0]), self.auth)

    def test_schedule_and_terminal_mutation_or_stale_authority_fail_closed(self) -> None:
        schedule = build_natural_schedule_v1(
            relation_ids=("r",), cohort_hash=h("cohort"),
            config_hash=h("config"), evidence_projection_hash=h("evidence"),
        )
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_SCHEDULE_REPLAY_MISMATCH"):
            validate_complete_natural_schedule_v1(replace(schedule, cohort_hash=h("other")), (), None)
        partial = replace(schedule, entries=schedule.entries[:1], self_hash="")
        partial = replace(partial, self_hash=_expected_hash(partial.to_dict()))
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_SCHEDULE_REPLAY_MISMATCH"):
            validate_complete_natural_schedule_v1(partial, (), None)
        terminal = self._terminal(ConstructionArmV1.T0, 0)
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_TERMINAL_REPLAY_MISMATCH"):
            verify_terminal_record_v1(replace(terminal, reason_code="changed"), None)

    def test_natural_metrics_keep_zero_denominator_as_not_observed(self) -> None:
        accepted = self._terminal(ConstructionArmV1.T0, 0)
        metrics = aggregate_natural_metrics_v1((accepted,), None)
        self.assertEqual(metrics.semantic_no_rule_appropriateness, "NOT_OBSERVED")
        semantic = self._terminal(
            ConstructionArmV1.T0, 0, ConstructionOutcomeV1.UNSUPPORTED_EVIDENCE, semantic=True
        )
        metrics = aggregate_natural_metrics_v1((semantic,), None)
        self.assertEqual(metrics.semantic_no_rule_appropriateness, 1.0)

    def test_stress_cohort_covers_nine_classes_with_zero_provider_calls(self) -> None:
        fixtures = tuple(
            build_stress_fixture_receipt_v1(
                fixture_id=f"fixture-{index}", expected_terminal=terminal,
                observed_terminal=terminal, synthetic_input_hash=h(f"fixture-{index}"),
                controller_actions=(
                    ("revise",) if terminal is ConstructionTerminalClassV1.BUDGET_EXHAUSTION
                    else ("retrieve",) if terminal is ConstructionTerminalClassV1.RETRIEVAL_FAILURE
                    else ()
                ),
            )
            for index, terminal in enumerate(ConstructionTerminalClassV1, 1)
        )
        metrics = aggregate_stress_metrics_v1(fixtures)
        self.assertEqual(metrics.namespace, STRESS_NAMESPACE)
        self.assertEqual(metrics.result_label, "SYNTHETIC_STRESS_ONLY")
        self.assertEqual(metrics.fixture_count, 9)
        self.assertEqual(metrics.exact_match_count, 9)
        self.assertEqual(metrics.no_rule_conflation_count, 0)
        self.assertEqual(metrics.provider_calls, 0)
        self.assertEqual(metrics.controller_route_coverage, ("retrieve", "revise"))

    def test_stress_incomplete_duplicate_mutation_and_mixing_fail_closed(self) -> None:
        one = build_stress_fixture_receipt_v1(
            fixture_id="fixture", expected_terminal=ConstructionTerminalClassV1.SYSTEM_ERROR,
            observed_terminal=ConstructionTerminalClassV1.SYSTEM_ERROR,
            synthetic_input_hash=h("fixture"),
        )
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_STRESS_COVERAGE_INCOMPLETE"):
            aggregate_stress_metrics_v1((one,))
        all_rows = tuple(
            build_stress_fixture_receipt_v1(
                fixture_id=f"f-{index}", expected_terminal=terminal,
                observed_terminal=terminal, synthetic_input_hash=h(f"f-{index}"),
                controller_actions=(
                    ("revise",) if terminal is ConstructionTerminalClassV1.BUDGET_EXHAUSTION
                    else ("retrieve",) if terminal is ConstructionTerminalClassV1.RETRIEVAL_FAILURE
                    else ()
                ),
            ) for index, terminal in enumerate(ConstructionTerminalClassV1)
        )
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_DUPLICATE_STRESS_FIXTURE"):
            aggregate_stress_metrics_v1((*all_rows, all_rows[0]))
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_STRESS_REPLAY_MISMATCH"):
            aggregate_stress_metrics_v1((replace(all_rows[0], observed_terminal="PARSE_FAILURE"), *all_rows[1:]))
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_NATURAL_STRESS_MIX_FORBIDDEN"):
            aggregate_stress_metrics_v1((self._terminal(ConstructionArmV1.T0, 0),))  # type: ignore[arg-type]

        invalid = replace(all_rows[0], observed_terminal="UNKNOWN_TERMINAL", self_hash="")
        invalid = replace(invalid, self_hash=_expected_hash(invalid.to_dict()))
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_STRESS_TERMINAL_INVALID"):
            aggregate_stress_metrics_v1((invalid, *all_rows[1:]))

    def test_rehashed_invalid_t1b_draw_and_repeated_retrieval_fail_closed(self) -> None:
        call = self._call(ConstructionArmV1.T1_B, 1, 1)
        valid = build_t1b_draw_v1(
            authorization=self.auth,
            draw_index=1,
            call_receipt=call,
            outcome=ConstructionOutcomeV1.PARSE_FAILURE,
            reason_code="STRICT_PARSE_OR_SCHEMA_FAILURE",
        )
        forged = replace(valid, outcome="ACCEPTED_PROPOSAL", self_hash="")
        forged = replace(forged, self_hash=_expected_hash(forged.to_dict()))
        calls = (
            call,
            self._call(ConstructionArmV1.T1_B, 1, 2),
            self._call(ConstructionArmV1.T1_B, 1, 3),
        )
        remaining = tuple(
            build_t1b_draw_v1(
                authorization=self.auth,
                draw_index=index,
                call_receipt=calls[index - 1],
                outcome=ConstructionOutcomeV1.PARSE_FAILURE,
                reason_code="STRICT_PARSE_OR_SCHEMA_FAILURE",
            )
            for index in (2, 3)
        )
        with self.assertRaises(Exp03ContractError):
            select_t1b_lowest_admissible_v1((forged, *remaining), self.auth)
        t2_calls = tuple(self._call(ConstructionArmV1.T2, 1, index) for index in (1, 2, 3))
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_REPEATED_RETRIEVAL_FORBIDDEN"):
            self._terminal(
                ConstructionArmV1.T2,
                1,
                ConstructionOutcomeV1.BUDGET_EXHAUSTION,
                calls=t2_calls,
                actions=("retrieve", "retrieve"),
            )

    def test_t2_action_history_accounts_for_calls_without_dangling_actions(self) -> None:
        two_parse_calls = tuple(self._call(ConstructionArmV1.T2, 1, index) for index in (1, 2))
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_T2_ACTION_SEQUENCE_INVALID"):
            self._terminal(
                ConstructionArmV1.T2,
                1,
                ConstructionOutcomeV1.PARSE_FAILURE,
                calls=two_parse_calls,
            )
        provider_calls = (
            self._call(ConstructionArmV1.T2, 2, 1),
            self._call(ConstructionArmV1.T2, 2, 2, completion="PROVIDER_ERROR"),
        )
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_T2_ACTION_SEQUENCE_INVALID"):
            self._terminal(
                ConstructionArmV1.T2,
                2,
                ConstructionOutcomeV1.PROVIDER_ERROR,
                calls=provider_calls,
            )
        with self.assertRaisesRegex(Exp03ContractError, "EXP03_T2_ACTION_SEQUENCE_INVALID"):
            self._terminal(
                ConstructionArmV1.T2,
                3,
                ConstructionOutcomeV1.PARSE_FAILURE,
                calls=(self._call(ConstructionArmV1.T2, 3, 1),),
                actions=("revise",),
            )

    def test_rehashed_unknown_terminal_enums_use_project_error(self) -> None:
        record = self._terminal(ConstructionArmV1.T0, 0)
        for field in ("arm", "outcome"):
            forged = replace(record, **{field: "UNKNOWN"}, self_hash="")
            forged = replace(forged, self_hash=_expected_hash(forged.to_dict()))
            with self.subTest(field=field), self.assertRaisesRegex(
                Exp03ContractError, "EXP03_TERMINAL_ENUM_INVALID"
            ):
                verify_terminal_record_v1(forged, None)

    def test_frozen_dataclasses_are_immutable(self) -> None:
        terminal = self._terminal(ConstructionArmV1.T0, 0)
        with self.assertRaises(Exception):
            terminal.outcome = "SYSTEM_ERROR"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
