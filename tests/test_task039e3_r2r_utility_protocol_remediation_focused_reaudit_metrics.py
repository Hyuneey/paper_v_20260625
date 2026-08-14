from __future__ import annotations

import inspect
import json
from pathlib import Path
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_utility_protocol_v2 import (
    CONSTRUCTION_PROVIDER_CALLS,
    EventF1CustodyV2,
    INNER_SPLIT_ID,
    IntervalV2,
    TEST1_COORDINATE_AUTHORITY,
    U6_STATUS,
    UtilityProtocolV2Error,
    alarm_episode_precision_v2,
    attack_event_recall_v2,
    authority_snapshot_v2,
    build_label_event_custody_v2,
    classify_t2_tradeoff_v2,
    event_f1_custody_v2,
    form_alarm_episodes_v2,
    normal_false_alarm_rate_per_hour_v2,
    t2_construction_cost_delta_v2,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs/task_reports"


def _json(name: str) -> dict[str, object]:
    value = json.loads((REPORTS / name).read_text(encoding="utf-8"))
    observed = value["artifact_hash"]
    payload = {key: item for key, item in value.items() if key != "artifact_hash"}
    if stable_hash_v1(payload) != observed:
        raise AssertionError(f"{name} self-hash differs")
    return value


class IndependentMetricAndGovernanceReauditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        labels = [0] * 54_000
        labels[10:12] = [1, 1]
        labels[20] = 1
        cls.custody, cls.events = build_label_event_custody_v2(
            labels=labels,
            feature_file=TEST1_COORDINATE_AUTHORITY.feature_file,
            feature_file_sha256=TEST1_COORDINATE_AUTHORITY.feature_sha256,
            label_file=TEST1_COORDINATE_AUTHORITY.label_file,
            label_file_sha256=TEST1_COORDINATE_AUTHORITY.label_sha256,
            split_id=INNER_SPLIT_ID,
            timestamps_aligned=True,
        )

    def test_label_event_custody_same_vector_invariants_and_roundtrip(self) -> None:
        self.assertEqual(self.events, (IntervalV2(10, 12), IntervalV2(20, 21)))
        self.assertEqual(self.custody.attack_labeled_seconds + self.custody.normal_labeled_seconds, 54_000)
        self.assertFalse(self.custody.to_dict()["virtual_purge_rows_included"])
        restored = type(self.custody).from_mapping(self.custody.to_dict())
        self.assertEqual(restored.artifact_hash, self.custody.artifact_hash)
        changed = self.custody.to_dict()
        changed["normal_labeled_seconds"] -= 1
        with self.assertRaises(UtilityProtocolV2Error):
            type(self.custody).from_mapping(changed)

    def test_normal_far_is_cross_bound_to_same_label_custody(self) -> None:
        alarms = form_alarm_episodes_v2((10, 20, 30))
        recall = attack_event_recall_v2(self.custody, self.events, alarms)
        precision = alarm_episode_precision_v2(self.custody, self.events, alarms)
        far = normal_false_alarm_rate_per_hour_v2(self.custody, self.events, alarms)
        self.assertEqual({recall.label_custody_hash, precision.label_custody_hash, far.label_custody_hash}, {self.custody.artifact_hash})
        self.assertEqual(far.denominator, self.custody.normal_labeled_seconds / 3600.0)
        self.assertNotIn("normal_labeled_seconds", inspect.signature(normal_false_alarm_rate_per_hour_v2).parameters)
        with self.assertRaises(UtilityProtocolV2Error):
            normal_false_alarm_rate_per_hour_v2(self.custody, (IntervalV2(1, 2),), alarms)

    def test_event_f1_preserves_component_preimages_and_roundtrips(self) -> None:
        alarms = form_alarm_episodes_v2((10, 20, 30))
        precision = alarm_episode_precision_v2(self.custody, self.events, alarms)
        recall = attack_event_recall_v2(self.custody, self.events, alarms)
        value = event_f1_custody_v2(precision, recall)
        document = value.to_dict()
        self.assertNotIn("numerator", document)
        self.assertNotIn("denominator", document)
        self.assertEqual(document["precision_component"]["numerator"], 2)
        self.assertEqual(document["precision_component"]["denominator"], 3)
        self.assertEqual(document["recall_component"]["numerator"], 2)
        self.assertEqual(document["recall_component"]["denominator"], 2)
        self.assertAlmostEqual(value.value, 0.8)
        self.assertEqual(EventF1CustodyV2.from_mapping(document).artifact_hash, value.artifact_hash)

    def test_event_f1_undefined_and_zero_cases_preserve_components(self) -> None:
        no_alarms = form_alarm_episodes_v2(())
        undefined = event_f1_custody_v2(
            alarm_episode_precision_v2(self.custody, self.events, no_alarms),
            attack_event_recall_v2(self.custody, self.events, no_alarms),
        )
        self.assertFalse(undefined.defined)
        self.assertEqual(undefined.undefined_reason, "precision_or_recall_undefined")
        self.assertFalse(undefined.precision.defined)
        zero_alarm = form_alarm_episodes_v2((30,))
        zero = event_f1_custody_v2(
            alarm_episode_precision_v2(self.custody, self.events, zero_alarm),
            attack_event_recall_v2(self.custody, self.events, zero_alarm),
        )
        self.assertTrue(zero.defined)
        self.assertEqual(zero.value, 0.0)

    def test_t2_exact_sign_grid_has_no_margin_or_winner(self) -> None:
        observed = set()
        for recall in (-1.0, 0.0, 1.0):
            for far in (-1.0, 0.0, 1.0):
                result = classify_t2_tradeoff_v2(recall, far)
                observed.add((result["delta_attack_event_recall_sign"], result["delta_normal_far_per_hour_sign"]))
                self.assertEqual(result["classification_basis"], "EXACT_TWO_DIMENSIONAL_SIGN_NO_MARGIN_NO_WEIGHTED_SCORE")
        self.assertEqual(len(observed), 9)
        snapshot = authority_snapshot_v2()
        self.assertIsNone(snapshot["materiality_margin"])
        self.assertFalse(snapshot["winner"])

    def test_comparator_specific_cost_and_u6_boundary(self) -> None:
        efficiency = _json("TASK-039E3_R2R_RESULT_ANALYSIS_EFFICIENCY.json")
        calls = {"T0": efficiency["deterministic_baseline"]["provider_calls"]}
        calls.update({arm: row["provider_calls"] for arm, row in efficiency["provider_arms"].items()})
        self.assertEqual(calls, CONSTRUCTION_PROVIDER_CALLS)
        self.assertEqual([t2_construction_cost_delta_v2(item) for item in ("T0", "T1", "T1-B")], [42, 0, -84])
        with self.assertRaises(UtilityProtocolV2Error):
            t2_construction_cost_delta_v2("COMMON-42")
        with self.assertRaises(UtilityProtocolV2Error):
            t2_construction_cost_delta_v2("generic")
        self.assertEqual(U6_STATUS, "COMPARATOR_SPECIFIC_COST_UTILITY_CONTEXT_ONLY")

    def test_minimal_previously_passed_regressions(self) -> None:
        authority = _json("TASK-039E3_R2R_UTILITY_PROTOCOL_AUTHORITY_POLICY.json")
        data = _json("TASK-039E3_R2R_UTILITY_PROTOCOL_DATA_POLICY.json")
        split = _json("TASK-039E3_R2R_UTILITY_PROTOCOL_SPLIT_POLICY.json")
        metric = _json("TASK-039E3_R2R_UTILITY_PROTOCOL_METRIC_POLICY.json")
        event = _json("TASK-039E3_R2R_UTILITY_PROTOCOL_EVENT_POLICY.json")
        equivalence = _json("TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json")
        self.assertEqual(authority["protocol_classification"], "POST_RESULT_PROTOCOL_FREEZE")
        self.assertEqual((data["dataset"], data["process_scope"]), ("HAI 23.05", "P1"))
        self.assertEqual(split["inner_assignment"], ["hai-test1.csv", "label-test1.csv"])
        self.assertEqual(split["outer_assignment"], ["hai-test2.csv", "label-test2.csv"])
        self.assertEqual(split["sealed_evaluation"], "NOT_MATERIALIZED_NOT_AUTHORIZED")
        self.assertEqual((equivalence["T0_T1_T1B_equivalent_relation_count"], equivalence["T2_accepted_equivalent_count"], equivalence["T2_no_rule_count"]), (42, 39, 3))
        self.assertEqual(metric["point_adjustment"], "PROHIBITED")
        self.assertIn("NOT_APPLICABLE", metric["auroc"])
        self.assertIn("NOT_APPLICABLE", metric["auprc"])
        self.assertEqual(event["primary_scope_wording"], "P1-bounded rule-set utility against HAI labeled attack events")


if __name__ == "__main__":
    unittest.main()
