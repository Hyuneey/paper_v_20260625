from __future__ import annotations

import copy
import inspect
import unittest

from paperworks.v6.common import stable_hash_v1
import paperworks.v6.task039e3_r2r_d2_design_v1 as subject


def _rehashed_mutation(path: tuple[str, ...], value: object) -> dict[str, object]:
    document = copy.deepcopy(subject.build_d2_design_authority_v1().to_public_dict())
    cursor: dict[str, object] = document
    for name in path[:-1]:
        child = cursor[name]
        if not isinstance(child, dict):
            raise AssertionError("independent mutation path does not reach an object")
        cursor = child
    cursor[path[-1]] = value
    payload = dict(document)
    payload.pop("design_hash")
    document["design_hash"] = stable_hash_v1(payload)
    return document


ATTACKS: tuple[tuple[str, tuple[str, ...], object], ...] = (
    ("d0_artifact_substitution", ("frozen_inputs", "d0_detector_prediction_hash"), "0" * 64),
    ("d1_artifact_substitution", ("frozen_inputs", "d1_rule_prediction_hash"), "1" * 64),
    ("source_count_one", ("corroboration_policy", "required_distinct_source_count"), 1),
    ("source_count_three", ("corroboration_policy", "required_distinct_source_count"), 3),
    (
        "same_source_duplicate_counting",
        ("corroboration_policy", "duplicate_rules_from_same_source_count_once"),
        False,
    ),
    ("temporal_tolerance", ("corroboration_policy", "temporal_tolerance_seconds"), 1),
    ("rolling_window", ("corroboration_policy", "rolling_window_allowed"), True),
    ("temporal_dilation", ("corroboration_policy", "temporal_dilation_allowed"), True),
    ("event_expansion", ("corroboration_policy", "event_expansion_allowed"), True),
    ("d0_score_dependency", ("fusion_policy", "d0_score_access_allowed"), True),
    ("label_dependency", ("fusion_policy", "label_aware_fusion"), True),
    ("d0_alarm_suppression", ("fusion_policy", "d0_alarms_preserved"), False),
    ("suppression_permission", ("fusion_policy", "d0_suppression_allowed"), True),
    ("raw_any_rule_or", ("fusion_policy", "raw_any_rule_or_allowed"), True),
    ("and_substitution", ("fusion_policy", "and_gating_allowed"), True),
    ("weighted_fusion", ("fusion_policy", "weighted_fusion_allowed"), True),
    ("d1_rerun", ("frozen_inputs", "d1_rerun_allowed"), True),
    ("d0_rerun", ("frozen_inputs", "d0_rerun_allowed"), True),
    ("test2", ("test2_accesses",), 1),
    ("outer", ("outer_authorized",), True),
    ("primary_metric_mutation", ("metric_policy", "attack_event_recall_formula"), "MUTATED"),
    (
        "d0_missed_recovery_formula",
        ("metric_policy", "d0_missed_attack_recovery_formula"),
        "MUTATED",
    ),
    ("added_far_formula", ("metric_policy", "added_normal_recovery_far_formula"), "MUTATED"),
    ("point_adjustment", ("metric_policy", "point_adjustment_allowed"), True),
    ("metric_computation", ("metric_policy", "metrics_compute_during_design"), True),
    ("fusion_selection", ("fusion_policy", "fusion_candidates_compared"), 1),
    ("hyperparameter_search", ("fusion_policy", "hyperparameter_search_performed"), True),
    ("replacement_artifact", ("frozen_inputs", "replacement_artifacts_allowed"), True),
    ("reconstructed_artifact", ("frozen_inputs", "reconstructed_artifacts_allowed"), True),
    ("mapping_substitution", ("source_resolution", "common42_source_mapping_hash"), "2" * 64),
    ("string_inference", ("source_resolution", "string_convention_inference_allowed"), True),
    ("opportunity_inversion", ("source_resolution", "opportunity_id_inversion_allowed"), True),
    ("same_second_mutation", ("corroboration_policy", "same_second_policy"), "PLUS_OR_MINUS_ONE"),
    ("prediction_labels", ("future_prediction_contract", "labels_allowed"), True),
    ("prediction_metrics", ("future_prediction_contract", "metrics_allowed"), True),
    ("prediction_raw_numeric", ("future_prediction_contract", "raw_numeric_values_allowed"), True),
    (
        "label_before_prediction",
        ("future_prediction_contract", "prediction_frozen_before_label_access"),
        False,
    ),
    ("d2_authorized", ("d2_authorized",), True),
    ("d2_executed", ("d2_executed",), True),
    ("scientific_execution", ("scientific_executions",), 1),
    ("push_attempt", ("push_attempted",), True),
)


class IndependentD2DesignV1Tests(unittest.TestCase):
    def test_01_all_rehashed_semantic_attacks_are_rejected(self) -> None:
        accepted: list[str] = []
        for name, path, value in ATTACKS:
            document = _rehashed_mutation(path, value)
            try:
                subject.validate_d2_design_document_v1(document)
            except subject.D2DesignError:
                continue
            accepted.append(name)
        self.assertEqual(accepted, [])
        self.assertGreaterEqual(len(ATTACKS), 20)

    def test_02_independent_truth_table(self) -> None:
        cases = (
            (False, (), False, "NONE"),
            (True, (), True, "D0_ONLY"),
            (False, ("A",), False, "NONE"),
            (False, ("A", "A"), False, "NONE"),
            (False, ("A", "B"), True, "RULE_RECOVERY"),
            (True, ("A", "B"), True, "D0_AND_RULE_CORROBORATION"),
        )
        for d0, sources, expected_alarm, expected_class in cases:
            alarm, trigger = subject.fuse_d2_point_v1(d0, sources)
            self.assertEqual((alarm, trigger), (expected_alarm, expected_class))

    def test_03_adjacent_seconds_cannot_be_combined(self) -> None:
        records = (
            subject.D2SyntheticRuleAlarmV1(0, "1" * 64, "A", True),
            subject.D2SyntheticRuleAlarmV1(1, "2" * 64, "B", True),
        )
        decisions = subject.fuse_synthetic_timeline_v1((False, False), records)
        self.assertFalse(any(item.d2_alarm_emitted for item in decisions))

    def test_04_api_has_no_fusion_choice_or_scientific_knobs(self) -> None:
        self.assertEqual(tuple(inspect.signature(subject.build_d2_design_authority_v1).parameters), ())
        parameters = tuple(inspect.signature(subject.fuse_d2_point_v1).parameters)
        self.assertEqual(parameters, ("d0_alarm", "alarming_source_variables"))
        self.assertFalse(
            {
                "source_count",
                "temporal_tolerance",
                "window",
                "score",
                "label",
                "fusion",
                "d0_artifact",
                "d1_artifact",
            }
            & set(parameters)
        )

    def test_05_design_source_has_no_prediction_or_metric_io(self) -> None:
        source = inspect.getsource(subject)
        self.assertNotIn("Path(", source)
        self.assertNotIn("read_text(", source)
        self.assertNotIn("open(", source)
        self.assertNotIn("execute_authorized_d0", source)
        self.assertNotIn("execute_rule", source)
        self.assertNotIn("label-test", source)
        self.assertNotIn("hai-test", source)

    def test_06_design_remains_local_and_unauthorized(self) -> None:
        design = subject.build_d2_design_authority_v1()
        self.assertEqual(design.remote_egress_status, "LOCAL_ONLY_NOT_PUSHED")
        self.assertFalse(design.push_attempted)
        self.assertFalse(design.d2_authorized)
        self.assertFalse(design.d2_executed)
        self.assertEqual(design.scientific_executions, 0)
        self.assertEqual(design.d0_executions, 0)
        self.assertEqual(design.d1_executions, 0)
        self.assertEqual(design.d2_executions, 0)


if __name__ == "__main__":
    unittest.main()
