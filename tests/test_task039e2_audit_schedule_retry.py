from dataclasses import replace
import unittest

from paperworks.v6.task039e2_audit_prep_v1 import (
    MAXIMUM_PROVIDER_SCIENTIFIC_CALLS,
    IndependentExecutionScheduleV1,
    IndependentRetryPolicyV1,
    TASK039E2AuditPreparationError,
    build_synthetic_relation_major_schedule_v1,
)
from task039e2_audit_support import make_schedule


class Task039E2AuditScheduleRetryTests(unittest.TestCase):
    def test_exact_schedule_and_provider_maximum(self) -> None:
        schedule = make_schedule()
        self.assertEqual(len(schedule.relation_order), 42)
        self.assertEqual(
            schedule.provider_call_counts(),
            {"T1": 42, "T1-B": 126, "T2": 126, "T1-DIRECT-NUMBER": 42},
        )
        self.assertEqual(
            sum(schedule.provider_call_counts().values()),
            MAXIMUM_PROVIDER_SCIENTIFIC_CALLS,
        )
        self.assertEqual(schedule.concurrency, 1)
        self.assertEqual(schedule.ordering_policy, "relation_major")
        self.assertFalse(schedule.cross_arm_output_visibility)
        self.assertFalse(schedule.result_dependent_ordering)
        self.assertTrue(schedule.only_t2_may_early_stop)

    def test_wrong_relation_count_concurrency_and_visibility_rejected(self) -> None:
        relations = tuple(
            f"SYNTHETIC_RELATION_{index:03d}" for index in range(1, 42)
        )
        with self.assertRaises(TASK039E2AuditPreparationError):
            build_synthetic_relation_major_schedule_v1(relations)
        schedule = make_schedule()
        for field_name, bad_value in (
            ("concurrency", 2),
            ("cross_arm_output_visibility", True),
            ("result_dependent_ordering", True),
        ):
            with self.subTest(field_name=field_name):
                with self.assertRaises(TASK039E2AuditPreparationError):
                    replace(schedule, **{field_name: bad_value})

    def test_fourth_t2_and_relation_skip_pattern_rejected(self) -> None:
        schedule = make_schedule()
        relation = schedule.relation_order[0]
        entries = list(schedule.entries)
        first_relation_end = next(
            index
            for index, entry in enumerate(entries)
            if entry.relation_identity != relation
        )
        with self.assertRaises(TASK039E2AuditPreparationError):
            replace(
                entries[first_relation_end - 1],
                sequence_index=first_relation_end,
                arm="T2",
                arm_call_number=4,
                t2_early_stop_conditional=True,
            )
        with self.assertRaises(TASK039E2AuditPreparationError):
            IndependentExecutionScheduleV1(
                relation_order=schedule.relation_order,
                entries=schedule.entries[:-1],
            )

    def test_only_registered_no_response_transport_failures_retry(self) -> None:
        policy = IndependentRetryPolicyV1()
        for outcome in (
            "connection_failure",
            "timeout_no_model_response",
            "http_429_no_model_response",
            "http_5xx_no_model_response",
        ):
            with self.subTest(outcome=outcome):
                decision = policy.classify(
                    outcome=outcome,
                    model_response_obtained=False,
                    completed_transport_retries=0,
                )
                self.assertTrue(decision.transport_retry_allowed)
                self.assertFalse(decision.scientific_generation_consumed)
                self.assertFalse(decision.full_run_failure)
                self.assertFalse(decision.relation_skipped)

    def test_scientific_and_noneligible_outcomes_never_retry(self) -> None:
        policy = IndependentRetryPolicyV1()
        cases = (
            ("http_400", False),
            ("http_401", False),
            ("http_403", False),
            ("provider_refusal", True),
            ("malformed_output", True),
            ("verifier_rejection", True),
        )
        for outcome, response_obtained in cases:
            with self.subTest(outcome=outcome):
                decision = policy.classify(
                    outcome=outcome,
                    model_response_obtained=response_obtained,
                    completed_transport_retries=0,
                )
                self.assertFalse(decision.transport_retry_allowed)
                self.assertTrue(decision.full_run_failure)

    def test_retry_exhaustion_and_disguised_response(self) -> None:
        policy = IndependentRetryPolicyV1()
        decision = policy.classify(
            outcome="connection_failure",
            model_response_obtained=False,
            completed_transport_retries=2,
        )
        self.assertFalse(decision.transport_retry_allowed)
        self.assertTrue(decision.full_run_failure)
        self.assertFalse(decision.relation_skipped)
        self.assertEqual(policy.scientific_generation_retries, 0)
        with self.assertRaises(TASK039E2AuditPreparationError):
            policy.classify(
                outcome="http_5xx_no_model_response",
                model_response_obtained=True,
                completed_transport_retries=0,
            )


if __name__ == "__main__":
    unittest.main()
