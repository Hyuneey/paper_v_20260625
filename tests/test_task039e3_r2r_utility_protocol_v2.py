from __future__ import annotations

import copy
import inspect
import json
import math
import os
from pathlib import Path
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_utility_protocol_v2 import (
    AUTHORIZED_REFERENCE_SET_HASH,
    CandidateDecisionV2,
    CONSTRUCTION_PROVIDER_CALLS,
    E1_PRIVATE_LEDGER_HASH,
    EventF1CustodyV2,
    INNER_SPLIT_ID,
    IntervalV2,
    TEST1_COORDINATE_AUTHORITY,
    UTILITY_SOURCE_UNIVERSE_V2,
    UtilityProtocolV2Error,
    abstention_rate_v2,
    alarm_episode_precision_v2,
    attack_event_recall_v2,
    authority_snapshot_v2,
    authorized_reference_specs_v2,
    build_label_event_custody_v2,
    classify_t2_tradeoff_v2,
    cluster_source_candidates_v2,
    decision_index_v2,
    derive_attack_events_v2,
    evaluate_target_opportunity_v2,
    event_f1_custody_v2,
    form_alarm_episodes_v2,
    form_source_opportunity_v2,
    is_event_isolated_v2,
    logical_to_physical_v2,
    no_rule_diagnostic_v2,
    normal_false_alarm_rate_per_hour_v2,
    physical_to_logical_v2,
    resolve_numeric_reference_v2,
    source_candidate_indices_v2,
    source_context_state_v2,
    strict_binary_labels_v2,
    t2_construction_cost_delta_v2,
    verify_private_numeric_registry_v2,
)


ROOT = Path(__file__).resolve().parents[1]
EQUIVALENCE_PATH = ROOT / "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"


def _equivalence() -> dict[str, object]:
    return json.loads(EQUIVALENCE_PATH.read_text(encoding="utf-8"))


def _exact_sources(*, conflict_offset: int | None = None) -> dict[str, tuple[int, ...]]:
    result = {source: () for source in UTILITY_SOURCE_UNIVERSE_V2}
    result[UTILITY_SOURCE_UNIVERSE_V2[0]] = (10,)
    if conflict_offset is not None:
        result[UTILITY_SOURCE_UNIVERSE_V2[1]] = (10 + conflict_offset,)
    return result


def _opportunity(**changes: object):
    event_index = changes.get("event_index", 10)
    retained = _exact_sources()
    retained[UTILITY_SOURCE_UNIVERSE_V2[0]] = (event_index,)
    kwargs: dict[str, object] = {
        "relation_binding_hash": "a" * 64,
        "source": UTILITY_SOURCE_UNIVERSE_V2[0],
        "event_index": 10,
        "horizon_seconds": 5,
        "file_identity": "hai-test1.csv",
        "physical_row_count": 54_000,
        "source_pre": (0.0,) * 5,
        "source_post": (2.0,) * 5,
        "expected_direction": "step_up",
        "source_step_threshold": 2.0,
        "source_stability_tolerance": 0.1,
        "retained_events_by_source": retained,
    }
    kwargs.update(changes)
    return form_source_opportunity_v2(**kwargs)


def _private_registry_from_env() -> dict[str, object]:
    path = os.environ.get("TASK039E3_UTILITY_NUMERIC_REGISTRY_V2")
    if not path:
        raise unittest.SkipTest("private registry is materialized only after Commit A")
    return json.loads(Path(path).read_text(encoding="utf-8"))


class CoordinateAndSourceAuthorityV2Tests(unittest.TestCase):
    def test_test1_and_test2_bidirectional_mapping(self) -> None:
        self.assertEqual(logical_to_physical_v2("hai-test1.csv", 0), 0)
        self.assertEqual(logical_to_physical_v2("label-test1.csv", 53_999), 53_999)
        self.assertEqual(logical_to_physical_v2("hai-test2.csv", 54_120), 0)
        self.assertEqual(logical_to_physical_v2("label-test2.csv", 284_519), 230_399)
        self.assertEqual(physical_to_logical_v2("hai-test2.csv", 0), 54_120)
        self.assertEqual(physical_to_logical_v2("label-test2.csv", 230_399), 284_519)

    def test_purge_endpoints_types_and_wrong_files_reject(self) -> None:
        for value in (54_000, 54_119):
            with self.assertRaises(UtilityProtocolV2Error):
                logical_to_physical_v2("hai-test2.csv", value)
        for value in (-1, 284_520, True, 54_120.0, "54120"):
            with self.assertRaises(UtilityProtocolV2Error):
                logical_to_physical_v2("hai-test2.csv", value)  # type: ignore[arg-type]
        with self.assertRaises(UtilityProtocolV2Error):
            physical_to_logical_v2("unknown.csv", 0)

    def test_exact_12_source_authority_and_isolation_boundary(self) -> None:
        self.assertEqual(len(UTILITY_SOURCE_UNIVERSE_V2), 12)
        self.assertFalse(is_event_isolated_v2(UTILITY_SOURCE_UNIVERSE_V2[0], 10, _exact_sources(conflict_offset=-2)))
        self.assertFalse(is_event_isolated_v2(UTILITY_SOURCE_UNIVERSE_V2[0], 10, _exact_sources(conflict_offset=2)))
        self.assertTrue(is_event_isolated_v2(UTILITY_SOURCE_UNIVERSE_V2[0], 10, _exact_sources(conflict_offset=-3)))
        self.assertTrue(is_event_isolated_v2(UTILITY_SOURCE_UNIVERSE_V2[0], 10, _exact_sources(conflict_offset=3)))

    def test_missing_extra_and_unknown_sources_reject(self) -> None:
        missing = _exact_sources()
        missing.pop(UTILITY_SOURCE_UNIVERSE_V2[-1])
        extra = _exact_sources()
        extra["unbound"] = ()
        for mapping in (missing, extra):
            with self.assertRaises(UtilityProtocolV2Error):
                is_event_isolated_v2(UTILITY_SOURCE_UNIVERSE_V2[0], 10, mapping)
        with self.assertRaises(UtilityProtocolV2Error):
            is_event_isolated_v2("unknown", 10, _exact_sources())
        not_retained = _exact_sources()
        not_retained[UTILITY_SOURCE_UNIVERSE_V2[0]] = (11,)
        with self.assertRaises(UtilityProtocolV2Error):
            is_event_isolated_v2(UTILITY_SOURCE_UNIVERSE_V2[0], 10, not_retained)


class NumericRegistryV2Tests(unittest.TestCase):
    def test_authorized_reference_set(self) -> None:
        specs = authorized_reference_specs_v2(_equivalence())
        self.assertEqual((len(specs), len({spec["reference"] for spec in specs})), (420, 420))

    def test_materialized_registry_self_hash_and_all_420_resolutions(self) -> None:
        registry = _private_registry_from_env()
        self.assertEqual(verify_private_numeric_registry_v2(registry), registry["artifact_hash"])
        for record in registry["records"]:
            self.assertTrue(math.isfinite(resolve_numeric_reference_v2(record["reference"], record["numeric_role"], registry)))

    def test_role_wrong_e1_nonfinite_and_direct_number_reject(self) -> None:
        registry = _private_registry_from_env()
        first = registry["records"][0]
        with self.assertRaises(UtilityProtocolV2Error):
            resolve_numeric_reference_v2(first["reference"], "target_noise_scale" if first["numeric_role"] != "target_noise_scale" else "source_step_threshold", registry)
        for mutator in ("wrong_e1", "nonfinite", "direct"):
            changed = copy.deepcopy(registry)
            if mutator == "wrong_e1":
                changed["e1_private_ledger_hash"] = "0" * 64
            elif mutator == "nonfinite":
                changed["records"][0]["numeric_value"] = "nan"
                changed["records"][0]["record_hash"] = stable_hash_v1({k: v for k, v in changed["records"][0].items() if k != "record_hash"})
            else:
                changed["direct_number_provenance"] = 1
            changed["artifact_hash"] = stable_hash_v1({k: v for k, v in changed.items() if k != "artifact_hash"})
            with self.assertRaises(UtilityProtocolV2Error):
                verify_private_numeric_registry_v2(changed)


class OpportunityStateMachineV2Tests(unittest.TestCase):
    def test_scan_and_source_boundary_not_opportunity(self) -> None:
        self.assertEqual(source_candidate_indices_v2(10), (5,))
        self.assertEqual(source_candidate_indices_v2(9), ())
        self.assertEqual(source_context_state_v2(4, 100).status, "source_opportunity_not_formed")
        self.assertEqual(source_context_state_v2(96, 100).status, "source_opportunity_not_formed")
        self.assertIsNone(source_context_state_v2(95, 100))

    def test_opportunity_no_trigger_and_nonfinite_source_states(self) -> None:
        formed = _opportunity()
        self.assertEqual(formed.event_index, 10)
        wrong = _opportunity(expected_direction="step_down")
        self.assertEqual(wrong.status, "no_trigger")
        nonfinite = _opportunity(source_post=(2.0, 2.0, float("nan"), 2.0, 2.0))
        self.assertEqual(nonfinite.status, "source_opportunity_not_formed")

    def test_cluster_policy_and_strict_inputs(self) -> None:
        self.assertEqual(cluster_source_candidates_v2(((5, 2.0), (14, -3.0), (23, 3.0))), ((14, -3.0),))
        for candidates in (((True, 1.0),), ((1, float("inf")),), ((1.0, 2.0),)):
            with self.assertRaises(UtilityProtocolV2Error):
                cluster_source_candidates_v2(candidates)  # type: ignore[arg-type]

    def test_target_expected_anomaly_abstain_and_reason_precedence(self) -> None:
        opportunity = _opportunity()
        expected = evaluate_target_opportunity_v2(
            opportunity, physical_row_count=100, target_baseline=(10.0,) * 5,
            target_response=(12.0,) * 3, expected_direction="increase", target_noise_scale=1.0,
        )
        equality = evaluate_target_opportunity_v2(
            opportunity, physical_row_count=100, target_baseline=(10.0,) * 5,
            target_response=(11.0,) * 3, expected_direction="increase", target_noise_scale=1.0,
        )
        self.assertEqual((expected.status, equality.status), ("expected_response", "anomaly"))
        boundary_opportunity = _opportunity(event_index=95)
        boundary = evaluate_target_opportunity_v2(
            boundary_opportunity, physical_row_count=100, target_baseline=(), target_response=(),
            expected_direction="increase", target_noise_scale=1.0, within_split=False,
        )
        self.assertEqual(boundary.reason, "file_boundary")
        incomplete = evaluate_target_opportunity_v2(
            opportunity, physical_row_count=100, target_baseline=(), target_response=(),
            expected_direction="increase", target_noise_scale=1.0,
            response_window_complete=False,
        )
        self.assertEqual(incomplete.reason, "incomplete_target_response_window")

    def test_target_exact_lengths_nonfinite_and_scalar_types(self) -> None:
        opportunity = _opportunity()
        for baseline, response in (((1.0,) * 6, (2.0,) * 3), ((1.0,) * 5, (2.0,) * 2)):
            with self.assertRaises(UtilityProtocolV2Error):
                evaluate_target_opportunity_v2(
                    opportunity, physical_row_count=100, target_baseline=baseline,
                    target_response=response, expected_direction="increase", target_noise_scale=1.0,
                )
        abstain = evaluate_target_opportunity_v2(
            opportunity, physical_row_count=100, target_baseline=(10.0,) * 5,
            target_response=(12.0, float("nan"), 12.0), expected_direction="increase", target_noise_scale=1.0,
        )
        self.assertEqual((abstain.status, abstain.reason), ("abstain", "nonfinite_target_window"))
        for invalid in (float("nan"), float("inf"), -float("inf"), True, "1"):
            with self.assertRaises(UtilityProtocolV2Error):
                evaluate_target_opportunity_v2(
                    opportunity, physical_row_count=100, target_baseline=(10.0,) * 5,
                    target_response=(12.0,) * 3, expected_direction="increase", target_noise_scale=invalid,
                )

    def test_decision_horizons_and_no_rule(self) -> None:
        self.assertEqual([decision_index_v2(10, h) for h in (1, 5, 10, 30, 60)], [13, 17, 22, 42, 72])
        value = no_rule_diagnostic_v2()
        self.assertTrue(value["no_rule_relation_diagnostic_only"])
        self.assertEqual((value["applicable_opportunities"], value["alarms"], value["abstentions"]), (0, 0, 0))
        self.assertEqual(abstention_rate_v2(1, 4)["value"], 0.25)
        self.assertFalse(abstention_rate_v2(0, 0)["defined"])
        with self.assertRaises(UtilityProtocolV2Error):
            abstention_rate_v2(2, 1)

    def test_fail_closed_window_and_state_inputs(self) -> None:
        for invalid_threshold in (True, "1", float("nan"), float("inf"), -float("inf")):
            with self.assertRaises(UtilityProtocolV2Error):
                _opportunity(source_step_threshold=invalid_threshold)
        with self.assertRaises(UtilityProtocolV2Error):
            _opportunity(source_pre=(0.0,) * 6)
        with self.assertRaises(UtilityProtocolV2Error):
            decision_index_v2(True, 5)
        for invalid in (
            ("unknown", None, None, None),
            ("anomaly", False, 10, None),
            ("expected_response", False, -1, None),
            ("abstain", None, None, "unknown"),
        ):
            with self.assertRaises(UtilityProtocolV2Error):
                CandidateDecisionV2(*invalid)


class LabelMetricCustodyV2Tests(unittest.TestCase):
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

    def test_strict_binary_labels(self) -> None:
        self.assertEqual(strict_binary_labels_v2((0, 1)), (0, 1))
        for invalid in (0.0, 1.0, True, False, "0", "1", 2, -1, None):
            with self.assertRaises(UtilityProtocolV2Error):
                strict_binary_labels_v2((invalid,))

    def test_label_event_custody_self_hash_counts_and_roundtrip(self) -> None:
        self.assertEqual(self.events, (IntervalV2(10, 12), IntervalV2(20, 21)))
        self.assertEqual(self.custody.attack_labeled_seconds + self.custody.normal_labeled_seconds, 54_000)
        self.assertFalse(self.custody.to_dict()["virtual_purge_rows_included"])
        restored = type(self.custody).from_mapping(self.custody.to_dict())
        self.assertEqual(restored.artifact_hash, self.custody.artifact_hash)
        tampered = self.custody.to_dict()
        tampered["normal_labeled_seconds"] -= 1
        with self.assertRaises(UtilityProtocolV2Error):
            type(self.custody).from_mapping(tampered)

    def test_row_alignment_fails_closed(self) -> None:
        with self.assertRaises(UtilityProtocolV2Error):
            build_label_event_custody_v2(
                labels=(0,) * 10,
                feature_file=TEST1_COORDINATE_AUTHORITY.feature_file,
                feature_file_sha256=TEST1_COORDINATE_AUTHORITY.feature_sha256,
                label_file=TEST1_COORDINATE_AUTHORITY.label_file,
                label_file_sha256=TEST1_COORDINATE_AUTHORITY.label_sha256,
                split_id=INNER_SPLIT_ID,
                timestamps_aligned=True,
            )

    def test_recall_precision_far_share_label_and_alarm_custody(self) -> None:
        alarms = form_alarm_episodes_v2((10, 20, 30))
        recall = attack_event_recall_v2(self.custody, self.events, alarms)
        precision = alarm_episode_precision_v2(self.custody, self.events, alarms)
        far = normal_false_alarm_rate_per_hour_v2(self.custody, self.events, alarms)
        self.assertEqual({recall.label_custody_hash, precision.label_custody_hash, far.label_custody_hash}, {self.custody.artifact_hash})
        self.assertEqual({recall.alarm_episode_set_hash, precision.alarm_episode_set_hash, far.alarm_episode_set_hash}, {recall.alarm_episode_set_hash})
        self.assertEqual(far.denominator, self.custody.normal_labeled_seconds / 3600.0)
        self.assertNotIn("normal_labeled_seconds", inspect.signature(normal_false_alarm_rate_per_hour_v2).parameters)

    def test_event_f1_full_component_roundtrip_and_undefined(self) -> None:
        alarms = form_alarm_episodes_v2((10, 20, 30))
        precision = alarm_episode_precision_v2(self.custody, self.events, alarms)
        recall = attack_event_recall_v2(self.custody, self.events, alarms)
        f1 = event_f1_custody_v2(precision, recall)
        self.assertNotIn("numerator", f1.to_dict())
        self.assertNotIn("denominator", f1.to_dict())
        self.assertEqual(EventF1CustodyV2.from_mapping(f1.to_dict()).artifact_hash, f1.artifact_hash)
        no_alarms = form_alarm_episodes_v2(())
        undefined = event_f1_custody_v2(
            alarm_episode_precision_v2(self.custody, self.events, no_alarms),
            attack_event_recall_v2(self.custody, self.events, no_alarms),
        )
        self.assertFalse(undefined.defined)
        self.assertEqual(undefined.undefined_reason, "precision_or_recall_undefined")
        self.assertEqual(EventF1CustodyV2.from_mapping(undefined.to_dict()).artifact_hash, undefined.artifact_hash)

    def test_event_mismatch_rejects(self) -> None:
        with self.assertRaises(UtilityProtocolV2Error):
            attack_event_recall_v2(self.custody, (IntervalV2(1, 2),), ())


class InterpretationCostAndRegressionV2Tests(unittest.TestCase):
    def test_exact_delta_signs_have_no_materiality_margin(self) -> None:
        self.assertEqual(
            classify_t2_tradeoff_v2(0.0, -0.1),
            {
                "delta_attack_event_recall_sign": "ZERO",
                "delta_normal_far_per_hour_sign": "NEGATIVE",
                "classification_basis": "EXACT_TWO_DIMENSIONAL_SIGN_NO_MARGIN_NO_WEIGHTED_SCORE",
            },
        )
        for recall in (-1.0, 0.0, 1.0):
            for far in (-1.0, 0.0, 1.0):
                result = classify_t2_tradeoff_v2(recall, far)
                self.assertIn(result["delta_attack_event_recall_sign"], {"NEGATIVE", "ZERO", "POSITIVE"})

    def test_comparator_specific_costs_and_common_has_none(self) -> None:
        self.assertEqual(CONSTRUCTION_PROVIDER_CALLS, {"T0": 0, "T1": 42, "T1-B": 126, "T2": 42})
        self.assertEqual(t2_construction_cost_delta_v2("T0"), 42)
        self.assertEqual(t2_construction_cost_delta_v2("T1"), 0)
        self.assertEqual(t2_construction_cost_delta_v2("T1-B"), -84)
        with self.assertRaises(UtilityProtocolV2Error):
            t2_construction_cost_delta_v2("COMMON-42")

    def test_authority_and_scientific_regressions(self) -> None:
        snapshot = authority_snapshot_v2()
        self.assertFalse(snapshot["utility_protocol_audited"])
        self.assertFalse(snapshot["rule_v2"])
        self.assertFalse(snapshot["production_runtime"])
        self.assertFalse(snapshot["winner"])
        value = _equivalence()
        self.assertEqual(value["T0_T1_T1B_equivalent_relation_count"], 42)
        self.assertEqual(value["T2_accepted_equivalent_count"], 39)
        self.assertEqual(value["T2_no_rule_count"], 3)
        self.assertFalse(value["identical_projections_treated_as_independent_predictions"])


if __name__ == "__main__":
    unittest.main()
