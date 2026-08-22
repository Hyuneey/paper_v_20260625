from __future__ import annotations
import ast,importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1];S=importlib.util.spec_from_file_location("diag_ind",ROOT/"scripts"/"diagnose_task039e3_r2r_d2_recovery_signal_failure_v1.py");assert S and S.loader;D=importlib.util.module_from_spec(S);S.loader.exec_module(D)
class IndependentDiagnosticTests(unittest.TestCase):
    def test_no_production_import(self):
        tree=ast.parse((ROOT/"scripts"/"diagnose_task039e3_r2r_d2_recovery_signal_failure_v1.py").read_text());imports={a.name for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom)) for a in n.names};self.assertFalse(any("paperworks" in x for x in imports))
    def test_no_policy_search_terms_as_calls(self):
        src=(ROOT/"scripts"/"diagnose_task039e3_r2r_d2_recovery_signal_failure_v1.py").read_text();self.assertNotIn("execute_authorized",src);self.assertNotIn("alternative_prediction",src)
    def test_relation_source_collapse(self):
        x=D.structure((0,2),((0,"r1"),(0,"r2")),{"r1":"same","r2":"same"},"X");self.assertEqual(x["event_wide_distinct_source_count"],1);self.assertEqual(x["d1_relation_alarm_records_within_interval"],2)
    def test_relative_offsets_only(self):
        x=D.structure((100,110),((103,"r"),(108,"r")),{"r":"s"},"X");self.assertEqual((x["first_d1_alarm_offset_from_interval_start_seconds"],x["last_d1_alarm_offset_from_interval_start_seconds"]),(3,8));self.assertNotIn("start",{k for k in x if k in ("start","end","timestamp")})
    def test_contract_mutations(self):
        for k,v in (("d0","0"*64),("alternative_fusion_policies_executed",1),("hypothetical_performance_calculations",1),("parameter_sweeps",1),("new_thresholds_selected",1),("new_temporal_windows_selected",1),("test2_accesses",1),("redesign_authorized",True)):
            with self.subTest(k=k),self.assertRaises(D.DiagnosticError):D.vc({**D.contract(),k:v})
    def test_report_inventory(self): self.assertEqual(len(D.NAMES),10)
    def test_all_attacks_rejected(self): self.assertEqual(D.adversarial(),(40,0))
if __name__=="__main__":unittest.main()
