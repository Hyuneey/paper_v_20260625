from __future__ import annotations

import inspect
import math
import unittest

from paperworks.v6.task039e3_r2r_utility_protocol_v2 import (
    ApplicableRuleEvaluationOpportunityV2,
    UTILITY_SOURCE_UNIVERSE_V2,
    UtilityProtocolV2Error,
    abstention_rate_v2,
    cluster_source_candidates_v2,
    decision_index_v2,
    evaluate_target_opportunity_v2,
    form_source_opportunity_v2,
    no_rule_diagnostic_v2,
    source_candidate_indices_v2,
    strict_binary_labels_v2,
)


def _sources(event_index: int = 10) -> dict[str, tuple[int, ...]]:
    value = {source: () for source in UTILITY_SOURCE_UNIVERSE_V2}
    value[UTILITY_SOURCE_UNIVERSE_V2[0]] = (event_index,)
    return value


def _source(**changes: object):
    event_index = changes.get("event_index", 10)
    value: dict[str, object] = {
        "relation_binding_hash": "a" * 64,
        "source": UTILITY_SOURCE_UNIVERSE_V2[0],
        "event_index": event_index,
        "horizon_seconds": 5,
        "file_identity": "hai-test1.csv",
        "physical_row_count": 54_000,
        "source_pre": (0.0,) * 5,
        "source_post": (2.0,) * 5,
        "expected_direction": "step_up",
        "source_step_threshold": 2.0,
        "source_stability_tolerance": 0.1,
        "retained_events_by_source": _sources(event_index),
    }
    value.update(changes)
    return form_source_opportunity_v2(**value)


def _target_opportunity(event_index: int = 10) -> ApplicableRuleEvaluationOpportunityV2:
    return ApplicableRuleEvaluationOpportunityV2(
        "a" * 64, UTILITY_SOURCE_UNIVERSE_V2[0], event_index, 5, "hai-test1.csv"
    )


class IndependentOpportunityAndFailClosedReauditTests(unittest.TestCase):
    def test_historical_core_semantics_regression(self) -> None:
        self.assertEqual(source_candidate_indices_v2(10), (5,))
        self.assertEqual(source_candidate_indices_v2(9), ())
        self.assertEqual(cluster_source_candidates_v2(((5, 2.0), (14, -3.0), (23, 3.0))), ((14, -3.0),))
        self.assertIsInstance(_source(), ApplicableRuleEvaluationOpportunityV2)
        self.assertEqual(_source(expected_direction="step_down").status, "no_trigger")
        self.assertEqual([decision_index_v2(10, h) for h in (1, 5, 10, 30, 60)], [13, 17, 22, 42, 72])

    def test_target_equality_anomaly_and_well_formed_abstention_precedence(self) -> None:
        opportunity = _target_opportunity()
        equality = evaluate_target_opportunity_v2(
            opportunity,
            physical_row_count=100,
            target_baseline=(10.0,) * 5,
            target_response=(11.0,) * 3,
            expected_direction="increase",
            target_noise_scale=1.0,
        )
        self.assertEqual((equality.status, equality.anomaly, equality.decision_index), ("anomaly", True, 17))
        boundary = evaluate_target_opportunity_v2(
            _target_opportunity(95),
            physical_row_count=100,
            target_baseline=(),
            target_response=(),
            expected_direction="increase",
            target_noise_scale=1.0,
            within_split=False,
        )
        self.assertEqual((boundary.status, boundary.reason), ("abstain", "file_boundary"))

    def test_strict_binary_label_closure_passes(self) -> None:
        self.assertEqual(strict_binary_labels_v2((0, 1)), (0, 1))
        for invalid in (True, False, 0.0, 1.0, "0", "1", 2, -1, None, math.nan):
            with self.assertRaises(UtilityProtocolV2Error):
                strict_binary_labels_v2((invalid,))

    def test_blocker_abstention_denominator_remains_free_caller_input(self) -> None:
        self.assertEqual(
            tuple(inspect.signature(abstention_rate_v2).parameters),
            ("abstained_applicable_opportunities", "all_applicable_rule_evaluation_opportunities"),
        )
        result = abstention_rate_v2(1, 999)
        self.assertTrue(result["defined"])
        self.assertEqual((result["numerator"], result["denominator"]), (1, 999))
        self.assertAlmostEqual(result["value"], 1 / 999)
        self.assertFalse(no_rule_diagnostic_v2()["applicable_opportunities"])

    def test_blocker_wrong_types_are_reclassified_instead_of_rejected(self) -> None:
        for bad_window in (("0",) * 5, (True,) * 5):
            result = _source(source_pre=bad_window)
            self.assertEqual((result.status, result.reason), ("source_opportunity_not_formed", "nonfinite_source_window"))
        opportunity = _target_opportunity()
        for bad_window in (("12",) * 3, (True,) * 3):
            result = evaluate_target_opportunity_v2(
                opportunity,
                physical_row_count=100,
                target_baseline=(10.0,) * 5,
                target_response=bad_window,
                expected_direction="increase",
                target_noise_scale=1.0,
            )
            self.assertEqual((result.status, result.reason), ("abstain", "nonfinite_target_window"))

    def test_blocker_boundary_states_mask_malformed_inputs(self) -> None:
        source_mutations = {
            "source_pre": (0.0,) * 6,
            "source_step_threshold": math.nan,
            "expected_direction": "unknown",
            "horizon_seconds": 999,
            "file_identity": "unknown.csv",
        }
        for key, bad in source_mutations.items():
            result = _source(event_index=4, **{key: bad})
            self.assertEqual((result.status, result.reason), ("source_opportunity_not_formed", "insufficient_source_pre_window"))
        opportunity = _target_opportunity(95)
        target_mutations = {
            "target_baseline": (0.0,) * 6,
            "target_noise_scale": math.nan,
            "expected_direction": "unknown",
            "within_split": "false",
        }
        for key, bad in target_mutations.items():
            kwargs: dict[str, object] = {
                "physical_row_count": 100,
                "target_baseline": (0.0,) * 5,
                "target_response": (2.0,) * 3,
                "expected_direction": "increase",
                "target_noise_scale": 1.0,
                "within_split": True,
            }
            kwargs[key] = bad
            result = evaluate_target_opportunity_v2(opportunity, **kwargs)
            self.assertEqual((result.status, result.reason), ("abstain", "file_boundary"))

    def test_blocker_out_of_file_event_is_not_rejected_as_bad_coordinate(self) -> None:
        result = _source(event_index=54_000)
        self.assertEqual((result.status, result.reason), ("source_opportunity_not_formed", "incomplete_source_post_window"))


if __name__ == "__main__":
    unittest.main()
