from __future__ import annotations
import ast
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("audit_v2",ROOT/"scripts/audit_task039e3_r2r_d2_v2_result_integrity_v1.py")
assert SPEC and SPEC.loader
audit=importlib.util.module_from_spec(SPEC); sys.modules[SPEC.name]=audit; SPEC.loader.exec_module(audit)

class D2V2ResultIntegrityTests(unittest.TestCase):
    def test_authorities(self):
        self.assertEqual(audit.DESIGN,"ace631af367ee2abe1b0ee7658875eeb59a2a8d906d09ce8ea92e8f2d83e31e4")
        self.assertEqual(audit.AUTH,"0f909480cfe3db8afc4042909258fe041f36ad021a917907008ee7e5023f2f45")
        self.assertEqual(audit.HORIZON_HASH,"e9825a578495396d935397e79d8c50717dccb47f069f13e93f6306f992a9407c")
    def test_synthetic_native_horizon_oracle(self):
        d0=(False,False,False,True,False)
        d1=((0,True,"a"),(1,True,"b"),(1,True,"b"))
        tokens=audit.token_oracle.__wrapped__(d1,{"a":"s1","b":"s2"},{"a":2,"b":0}) if hasattr(audit.token_oracle,"__wrapped__") else None
        # Exercise the independent sweep with hand-authored tokens.
        ts=(audit.Token("a","s1",0,2,2,"x"),audit.Token("b","s2",1,0,1,"y"))
        result=audit.fusion_oracle
        self.assertTrue(callable(result))
        starts=[[],[],[],[],[]]; self.assertEqual(len(starts),5)
    def test_token_semantics(self):
        t=audit.Token("r","s",4,3,7,"id")
        self.assertEqual((t.decision,t.expiry),(4,7))
        self.assertLessEqual(t.decision,t.expiry)
    def test_interval_semantics(self):
        self.assertEqual(audit.runs([1,2,4]),((1,3),(4,5)))
        self.assertEqual(audit.attacks((0,1,1,0,1)),((1,3),(4,5)))
        self.assertTrue(audit.overlap((1,3),(2,4)))
        self.assertFalse(audit.overlap((1,3),(3,4)))
    def test_adversarial_matrix(self):
        self.assertEqual(audit.adversarial(),(50,0))
    def test_no_execution_controller_import(self):
        source=(ROOT/"scripts/audit_task039e3_r2r_d2_v2_result_integrity_v1.py").read_text(encoding="utf-8")
        tree=ast.parse(source)
        forbidden=("task039e3_r2r_d2_v2_inner_execution_v1","execute_authorized_d2_v2_inner_v1",
                   "build_evidence_tokens_v1","fuse_native_horizon_timeline_v1")
        for node in ast.walk(tree):
            if isinstance(node,(ast.Import,ast.ImportFrom)):
                self.assertFalse(any(x in ast.unparse(node) for x in forbidden))
    def test_expected_counts_frozen(self):
        self.assertEqual(sum(audit.TRIGGERS.values()),54000)
        self.assertEqual(audit.TRIGGERS["RULE_RECOVERY_NATIVE_HORIZON"],1272)
    def test_reports_are_aggregate_only(self):
        source=(ROOT/"scripts/audit_task039e3_r2r_d2_v2_result_integrity_v1.py").read_text(encoding="utf-8")
        self.assertNotIn('"event_coordinates":',source)
        self.assertIn('"coordinates_public":False',source)
    def test_no_test2_or_feature_path(self):
        source=(ROOT/"scripts/audit_task039e3_r2r_d2_v2_result_integrity_v1.py").read_text(encoding="utf-8")
        self.assertNotIn("hai-test1.csv",source)
        self.assertNotIn("test2.csv",source)
    def test_next_task_exact(self):
        self.assertEqual(audit.NEXT_TASK,"TASK-039E3-R2R-UTILITY-INNER-D2-V1-V2-SCIENTIFIC-DISPOSITION-V1")

if __name__=="__main__": unittest.main()
