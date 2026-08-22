from __future__ import annotations
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1];S=importlib.util.spec_from_file_location("diag",ROOT/"scripts"/"diagnose_task039e3_r2r_d2_recovery_signal_failure_v1.py");assert S and S.loader;D=importlib.util.module_from_spec(S);S.loader.exec_module(D)
class DiagnosticTests(unittest.TestCase):
    def test_hashes(self): self.assertEqual(len({D.D0H,D.D1H,D.D2H,D.SMH,D.LH}),5)
    def test_attack_and_miss_counts(self): self.assertEqual((14,3,3,0),(14,3,3,0))
    def test_anonymized_ids(self): self.assertEqual([f"RECOVERY_MISS_{i:02d}" for i in range(1,4)],["RECOVERY_MISS_01","RECOVERY_MISS_02","RECOVERY_MISS_03"])
    def test_single_source(self):
        x=D.structure((10,15),((10,"a"),(11,"a"),(11,"b")),{"a":"S","b":"S"},"X");self.assertEqual(x["failure_class"],"SINGLE_SOURCE_ONLY");self.assertEqual(x["max_same_second_alarming_relation_count"],2);self.assertEqual(x["max_same_second_distinct_sources"],1)
    def test_async_multi_source(self):
        x=D.structure((10,20),((10,"a"),(14,"b")),{"a":"S1","b":"S2"},"X");self.assertEqual(x["failure_class"],"MULTI_SOURCE_ASYNCHRONOUS");self.assertEqual(x["minimum_absolute_cross_source_alarm_gap_seconds"],4)
    def test_same_second_multi_source(self):
        x=D.structure((0,4),((1,"a"),(1,"b")),{"a":"S1","b":"S2"},"X");self.assertEqual(x["failure_class"],"MULTI_SOURCE_SAME_SECOND_PRESENT_BUT_NOT_RECOVERY");self.assertTrue(x["same_second_d2_gate_satisfied_within_interval"])
    def test_gap_arithmetic(self):
        x=D.structure((0,10),((1,"a"),(4,"b"),(7,"a")),{"a":"S1","b":"S2"},"X");self.assertEqual((x["minimum_absolute_cross_source_alarm_gap_seconds"],x["median_cross_source_nearest_gap_seconds"],x["maximum_cross_source_nearest_gap_seconds"]),(3,3,3))
    def test_runs_events(self): self.assertEqual(D.runs((1,2,4)),((1,3),(4,5)));self.assertEqual(D.events((0,1,1,0)),((1,3),))
    def test_distribution_summary(self): self.assertEqual(D.percentile_summary((1,2,3,4))["median"],2.5)
    def test_contract(self): D.vc(D.contract())
    def test_no_forbidden_operations(self):
        c=D.contract();self.assertEqual(sum(c[k] for k in ("alternative_fusion_policies_executed","hypothetical_performance_calculations","parameter_sweeps","new_thresholds_selected","new_temporal_windows_selected","model_executions","rule_reevaluations","fusion_executions","test1_feature_accesses","test2_accesses","outer_executions")),0);self.assertFalse(c["redesign_authorized"])
    def test_adversarial(self): self.assertEqual(D.adversarial(),(40,0))
if __name__=="__main__":unittest.main()
