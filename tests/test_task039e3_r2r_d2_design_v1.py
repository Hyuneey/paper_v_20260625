from __future__ import annotations

import copy
from dataclasses import asdict, replace
import inspect
import json
from pathlib import Path
import unittest

from paperworks.v6.task039e3_r2r_d2_design_v1 import (
    ADDED_NORMAL_RECOVERY_FAR_FORMULA,
    COMMON42_SOURCE_MAPPING_HASH,
    CORROBORATION_COUNT_RATIONALE,
    D0_MISSED_ATTACK_RECOVERY_FORMULA,
    D2DesignAuthorityV1,
    D2DesignError,
    D2SyntheticRuleAlarmV1,
    D2_DESIGN_HASH,
    D2_FUSION_FAMILY,
    D2_ID,
    FROZEN_D0_DETECTOR_PREDICTION_HASH,
    FROZEN_D1_RULE_PREDICTION_HASH,
    REQUIRED_DISTINCT_SOURCE_COUNT,
    SAME_SECOND_POLICY,
    SOURCE_RESOLUTION_POLICY,
    TRIGGER_CLASSES,
    build_d2_design_authority_v1,
    canonical_config_document_v1,
    common42_source_mapping_hash_v1,
    fuse_d2_point_v1,
    fuse_synthetic_timeline_v1,
    resolve_d1_alarm_source_v1,
    validate_d2_config_v1,
    validate_d2_design_authority_v1,
    validate_d2_design_document_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_metrics_v1 import (
    ALARM_EPISODE_POLICY,
    ATTACK_EVENT_RECALL_FORMULA,
    NORMAL_FAR_FORMULA,
)
from paperworks.v6.task039e3_r2r_utility_normal_only_authority_v1 import (
    build_common42_authority_v1,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "v6" / "task039e3_r2r_d2_detector_rule_corroboration_v1.json"
EQUIVALENCE = ROOT / "docs" / "task_reports" / "TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"
EVIDENCE = ROOT / "docs" / "task_reports" / "TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json"


def _relation_hash(seed: int) -> str:
    return f"{seed:064x}"


class D2DesignV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authority = build_common42_authority_v1(
            json.loads(EQUIVALENCE.read_text(encoding="utf-8")),
            json.loads(EVIDENCE.read_text(encoding="utf-8")),
        )

    def test_01_canonical_design_and_exact_input_hashes(self) -> None:
        design = build_d2_design_authority_v1()
        self.assertEqual(validate_d2_design_authority_v1(design), D2_DESIGN_HASH)
        self.assertEqual(design.d2_id, D2_ID)
        self.assertEqual(design.d2_fusion_family, D2_FUSION_FAMILY)
        self.assertEqual(
            design.frozen_inputs.d0_detector_prediction_hash,
            FROZEN_D0_DETECTOR_PREDICTION_HASH,
        )
        self.assertEqual(
            design.frozen_inputs.d1_rule_prediction_hash,
            FROZEN_D1_RULE_PREDICTION_HASH,
        )

    def test_02_factory_custody_rejects_reconstruction_and_copies(self) -> None:
        issued = build_d2_design_authority_v1()
        for forged in (
            D2DesignAuthorityV1(**asdict(issued)),
            copy.copy(issued),
            copy.deepcopy(issued),
            replace(issued),
        ):
            with self.assertRaises(D2DesignError):
                validate_d2_design_authority_v1(forged)

    def test_03_document_self_hash_and_semantic_replay(self) -> None:
        document = build_d2_design_authority_v1().to_public_dict()
        self.assertEqual(validate_d2_design_document_v1(document), D2_DESIGN_HASH)
        mutated = copy.deepcopy(document)
        mutated["fusion_policy"]["d0_alarms_preserved"] = False
        from paperworks.v6.common import stable_hash_v1

        payload = dict(mutated)
        payload.pop("design_hash")
        mutated["design_hash"] = stable_hash_v1(payload)
        with self.assertRaises(D2DesignError):
            validate_d2_design_document_v1(mutated)

    def test_04_config_is_exact_and_self_hashed(self) -> None:
        committed = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(committed, canonical_config_document_v1())
        self.assertEqual(validate_d2_config_v1(committed), committed["config_hash"])

    def test_05_d0_alarm_is_always_preserved(self) -> None:
        for sources in ((), ("A",), ("A", "B"), ("A", "B", "C")):
            alarm, _trigger = fuse_d2_point_v1(True, sources)
            self.assertTrue(alarm)

    def test_06_single_source_cannot_recover(self) -> None:
        self.assertEqual(fuse_d2_point_v1(False, ("A",)), (False, "NONE"))

    def test_07_same_source_duplicate_rules_count_once(self) -> None:
        self.assertEqual(fuse_d2_point_v1(False, ("A", "A")), (False, "NONE"))

    def test_08_two_or_more_distinct_sources_recover(self) -> None:
        self.assertEqual(fuse_d2_point_v1(False, ("A", "B")), (True, "RULE_RECOVERY"))
        self.assertEqual(
            fuse_d2_point_v1(False, ("A", "B", "C")),
            (True, "RULE_RECOVERY"),
        )

    def test_09_trigger_classes_are_exact(self) -> None:
        observed = (
            fuse_d2_point_v1(False, ())[1],
            fuse_d2_point_v1(True, ())[1],
            fuse_d2_point_v1(False, ("A", "B"))[1],
            fuse_d2_point_v1(True, ("A", "B"))[1],
        )
        self.assertEqual(observed, TRIGGER_CLASSES)

    def test_10_same_second_only_and_adjacent_seconds_do_not_corroborate(self) -> None:
        records = (
            D2SyntheticRuleAlarmV1(0, _relation_hash(1), "A", True),
            D2SyntheticRuleAlarmV1(1, _relation_hash(2), "B", True),
        )
        decisions = fuse_synthetic_timeline_v1((False, False), records)
        self.assertEqual(tuple(item.trigger_class for item in decisions), ("NONE", "NONE"))
        same_second = (
            D2SyntheticRuleAlarmV1(0, _relation_hash(1), "A", True),
            D2SyntheticRuleAlarmV1(0, _relation_hash(2), "B", True),
        )
        self.assertEqual(
            fuse_synthetic_timeline_v1((False,), same_second)[0].trigger_class,
            "RULE_RECOVERY",
        )

    def test_11_source_mapping_is_complete_and_exact(self) -> None:
        self.assertEqual(common42_source_mapping_hash_v1(self.authority), COMMON42_SOURCE_MAPPING_HASH)
        self.assertEqual(len(self.authority.relations), 42)
        self.assertEqual(len({item.relation_binding_hash for item in self.authority.relations}), 42)
        resolved = resolve_d1_alarm_source_v1(
            self.authority.relations[0].relation_binding_hash,
            self.authority,
        )
        self.assertEqual(resolved.relation_identity, self.authority.relations[0].relation_identity)
        self.assertEqual(resolved.source_variable_identity, self.authority.relations[0].source)
        with self.assertRaises(D2DesignError):
            resolve_d1_alarm_source_v1("0" * 64, self.authority)

    def test_12_source_and_same_second_policies_are_frozen(self) -> None:
        design = build_d2_design_authority_v1()
        self.assertEqual(design.source_resolution.source_resolution_policy, SOURCE_RESOLUTION_POLICY)
        self.assertFalse(design.source_resolution.string_convention_inference_allowed)
        self.assertFalse(design.source_resolution.opportunity_id_inversion_allowed)
        self.assertEqual(design.corroboration_policy.required_distinct_source_count, 2)
        self.assertEqual(REQUIRED_DISTINCT_SOURCE_COUNT, 2)
        self.assertEqual(design.corroboration_policy.same_second_policy, SAME_SECOND_POLICY)
        self.assertEqual(design.corroboration_policy.temporal_tolerance_seconds, 0)

    def test_13_no_score_label_rule_rerun_or_fusion_alternatives(self) -> None:
        policy = build_d2_design_authority_v1().fusion_policy
        self.assertTrue(policy.d0_alarm_boolean_only)
        self.assertFalse(policy.d0_score_access_allowed)
        self.assertFalse(policy.label_aware_fusion)
        self.assertFalse(policy.d1_numeric_reevaluation_allowed)
        self.assertFalse(policy.raw_any_rule_or_allowed)
        self.assertFalse(policy.and_gating_allowed)
        self.assertFalse(policy.weighted_fusion_allowed)

    def test_14_input_reruns_test2_and_execution_are_prohibited(self) -> None:
        design = build_d2_design_authority_v1()
        self.assertFalse(design.frozen_inputs.d0_rerun_allowed)
        self.assertFalse(design.frozen_inputs.d1_rerun_allowed)
        self.assertEqual(design.test2_accesses, 0)
        self.assertFalse(design.d2_authorized)
        self.assertFalse(design.d2_executed)
        self.assertEqual(design.d2_executions, 0)

    def test_15_metric_formulas_are_exact(self) -> None:
        metric = build_d2_design_authority_v1().metric_policy
        self.assertEqual(metric.attack_event_recall_formula, ATTACK_EVENT_RECALL_FORMULA)
        self.assertEqual(metric.normal_far_formula, NORMAL_FAR_FORMULA)
        self.assertEqual(metric.alarm_episode_policy, ALARM_EPISODE_POLICY)
        self.assertEqual(metric.d0_missed_attack_recovery_formula, D0_MISSED_ATTACK_RECOVERY_FORMULA)
        self.assertEqual(metric.added_normal_recovery_far_formula, ADDED_NORMAL_RECOVERY_FAR_FORMULA)
        self.assertFalse(metric.metrics_compute_during_design)

    def test_16_independence_is_machine_readable(self) -> None:
        independence = build_d2_design_authority_v1().independence
        self.assertFalse(independence.d0_prediction_content_read_for_design)
        self.assertFalse(independence.d1_prediction_content_read_for_design)
        self.assertFalse(independence.d0_metrics_used_for_design)
        self.assertFalse(independence.d1_metrics_used_for_design)
        self.assertFalse(independence.test1_used_for_design)
        self.assertFalse(independence.labels_used_for_design)
        self.assertEqual(independence.fusion_candidates_compared, 0)
        self.assertFalse(independence.hyperparameter_search_performed)
        self.assertEqual(independence.corroboration_count_rationale, CORROBORATION_COUNT_RATIONALE)

    def test_17_no_caller_scientific_override_signatures(self) -> None:
        self.assertEqual(tuple(inspect.signature(build_d2_design_authority_v1).parameters), ())
        self.assertEqual(
            tuple(inspect.signature(fuse_d2_point_v1).parameters),
            ("d0_alarm", "alarming_source_variables"),
        )
        for forbidden in (
            "source_count",
            "tolerance",
            "window",
            "threshold",
            "score",
            "label",
            "d0_suppression",
            "rule_rerun",
            "fusion_selection",
        ):
            self.assertNotIn(forbidden, inspect.signature(fuse_d2_point_v1).parameters)

    def test_18_synthetic_input_boundary_is_strict(self) -> None:
        with self.assertRaises(D2DesignError):
            fuse_d2_point_v1(1, ())  # type: ignore[arg-type]
        with self.assertRaises(D2DesignError):
            fuse_d2_point_v1(False, ["A", "B"])  # type: ignore[arg-type]
        with self.assertRaises(D2DesignError):
            D2SyntheticRuleAlarmV1(-1, _relation_hash(1), "A", True)
        with self.assertRaises(D2DesignError):
            D2SyntheticRuleAlarmV1(0, _relation_hash(1), "", True)


if __name__ == "__main__":
    unittest.main()
