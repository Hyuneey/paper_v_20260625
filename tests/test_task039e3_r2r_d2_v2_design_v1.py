from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import unittest

from paperworks.v6 import task039e3_r2r_d2_v2_design_v1 as subject


ROOT = Path(__file__).resolve().parents[1]


class D2V2DesignV1Tests(unittest.TestCase):
    def test_exact_factory_design_and_config(self) -> None:
        design = subject.build_d2_v2_design_authority_v1()
        self.assertEqual(subject.validate_d2_v2_design_authority_v1(design), subject.D2_V2_DESIGN_HASH)
        self.assertEqual(design.d2_v2_id, subject.D2_V2_ID)
        self.assertEqual(design.input_authority.d0_detector_prediction_hash, subject.FROZEN_D0_PREDICTION_HASH)
        self.assertEqual(design.input_authority.d1_rule_prediction_hash, subject.FROZEN_D1_PREDICTION_HASH)
        self.assertEqual(design.input_authority.source_map_hash, subject.FROZEN_SOURCE_MAP_HASH)
        config = json.loads((ROOT / "configs/v6/task039e3_r2r_d2_v2_native_horizon_corroboration_v1.json").read_text(encoding="utf-8"))
        self.assertEqual(subject.validate_d2_v2_config_v1(config), config["config_hash"])

    def test_exact_public_native_horizon_authority_replays(self) -> None:
        load = lambda name: json.loads((ROOT / name).read_text(encoding="utf-8"))
        horizon_map = subject.resolve_native_horizon_map_from_frozen_authorities_v1(
            load("docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"),
            load("docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json"),
            load("docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_SOURCE_MAP.json"),
        )
        self.assertEqual(horizon_map.entry_count, 42)
        self.assertEqual(len(horizon_map.entries), 42)
        self.assertEqual(len({entry.relation_binding_hash for entry in horizon_map.entries}), 42)
        self.assertEqual(horizon_map.map_hash, subject.D2_V2_NATIVE_HORIZON_MAP_HASH)
        self.assertTrue(horizon_map.values_public)
        self.assertEqual((horizon_map.missing_count, horizon_map.ambiguous_count), (0, 0))
        self.assertEqual((horizon_map.label_derived_count, horizon_map.test1_derived_count), (0, 0))

    def test_missing_ambiguous_and_substituted_horizon_map_rejected(self) -> None:
        document = subject.native_horizon_map_document_v1()
        for mutate in (
            lambda d: d["entries"].pop(),
            lambda d: d["entries"].append(dict(d["entries"][0])),
            lambda d: d["entries"][0].__setitem__("native_horizon_seconds", 2),
            lambda d: d.__setitem__("label_derived_count", 1),
            lambda d: d.__setitem__("test1_derived_count", 1),
        ):
            candidate = json.loads(json.dumps(document))
            mutate(candidate)
            with self.assertRaises(subject.D2V2DesignError):
                subject.validate_native_horizon_map_document_v1(candidate)

    def test_design_rejects_fixed_windows_gap_hardcoding_and_scope_changes(self) -> None:
        original = subject.build_d2_v2_design_authority_v1().to_public_dict()
        mutations = (
            ("evidence_token_policy", "global_fixed_temporal_window_seconds", 2),
            ("evidence_token_policy", "global_fixed_temporal_window_seconds", 169),
            ("evidence_token_policy", "diagnostic_gap_values_used_as_parameters", True),
            ("corroboration_policy", "required_distinct_source_count", 1),
            ("corroboration_policy", "required_distinct_source_count", 3),
            ("corroboration_policy", "single_source_fallback", True),
            ("corroboration_policy", "exact_same_second_included", False),
            ("fusion_policy", "d0_alarms_preserved", False),
            ("fusion_policy", "d0_score_dependency", True),
            ("fusion_policy", "rule_reevaluation_dependency", True),
        )
        for section, key, value in mutations:
            candidate = json.loads(json.dumps(original))
            candidate[section][key] = value
            with self.assertRaises(subject.D2V2DesignError):
                subject.validate_d2_v2_design_document_v1(candidate)

    def test_factory_custody_rejects_caller_constructed_design(self) -> None:
        issued = subject.build_d2_v2_design_authority_v1()
        forged = replace(issued, d2_v2_authorized=True)
        with self.assertRaises(subject.D2V2DesignError):
            subject.validate_d2_v2_design_authority_v1(forged)

    def test_causal_token_start_expiry_and_split_clip(self) -> None:
        binding = subject.FROZEN_NATIVE_HORIZON_BINDINGS[0][0]
        record = subject.D2V2SyntheticRuleAlarmV1(3, binding, "SOURCE_A", True)
        token = subject.build_synthetic_causal_tokens_v1((record,), ((binding, 4),), 6)[0]
        self.assertEqual(token.start_physical_row_index, 3)
        self.assertEqual(token.expiry_physical_row_index, 5)
        self.assertGreaterEqual(token.start_physical_row_index, record.decision_physical_row_index)

    def test_same_source_collapse_and_two_distinct_sources(self) -> None:
        a, b, c = (row[0] for row in subject.FROZEN_NATIVE_HORIZON_BINDINGS[:3])
        records = (
            subject.D2V2SyntheticRuleAlarmV1(1, a, "SOURCE_A", True),
            subject.D2V2SyntheticRuleAlarmV1(1, b, "SOURCE_A", True),
            subject.D2V2SyntheticRuleAlarmV1(1, c, "SOURCE_B", True),
        )
        tokens = subject.build_synthetic_causal_tokens_v1(records, ((a, 1), (b, 1), (c, 1)), 4)
        decisions = subject.fuse_synthetic_native_horizon_timeline_v1((False,) * 4, tokens)
        self.assertEqual(decisions[1].active_distinct_sources, ("SOURCE_A", "SOURCE_B"))
        self.assertEqual(decisions[1].trigger_class, "RULE_RECOVERY_NATIVE_HORIZON")

    def test_asynchronous_overlap_and_expired_evidence(self) -> None:
        a, b = (row[0] for row in subject.FROZEN_NATIVE_HORIZON_BINDINGS[:2])
        records = (
            subject.D2V2SyntheticRuleAlarmV1(1, a, "SOURCE_A", True),
            subject.D2V2SyntheticRuleAlarmV1(2, b, "SOURCE_B", True),
        )
        tokens = subject.build_synthetic_causal_tokens_v1(records, ((a, 2), (b, 1)), 5)
        decisions = subject.fuse_synthetic_native_horizon_timeline_v1((False,) * 5, tokens)
        self.assertTrue(decisions[2].d2_v2_alarm_emitted)
        self.assertFalse(decisions[4].d2_v2_alarm_emitted)

    def test_d0_preservation_and_no_execution_authority(self) -> None:
        decisions = subject.fuse_synthetic_native_horizon_timeline_v1((True, False), ())
        self.assertTrue(decisions[0].d2_v2_alarm_emitted)
        design = subject.build_d2_v2_design_authority_v1()
        self.assertFalse(design.d2_v2_authorized)
        self.assertFalse(design.d2_v2_executed)
        self.assertFalse(design.outer_authorized)


if __name__ == "__main__":
    unittest.main()
