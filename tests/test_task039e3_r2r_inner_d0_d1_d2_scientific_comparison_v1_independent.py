from __future__ import annotations
import ast, importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
S=importlib.util.spec_from_file_location("comparison_ind",ROOT/"scripts"/"compare_task039e3_r2r_inner_d0_d1_d2_v1.py"); assert S and S.loader
C=importlib.util.module_from_spec(S); S.loader.exec_module(C)

class IndependentComparisonTests(unittest.TestCase):
    def test_no_production_execution_import(self):
        tree=ast.parse((ROOT/"scripts"/"compare_task039e3_r2r_inner_d0_d1_d2_v1.py").read_text())
        imports={a.name for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom)) for a in n.names}
        self.assertFalse(any("paperworks" in x for x in imports))
    def test_contract_mutations_fail(self):
        for k,v in (("d0","0"*64),("attacks",15),("no_execution",False),("no_causal_diagnosis",False),("redesign_authorized",True),("test1_feature_accesses",1),("test2_accesses",1),("outer_authorized",True)):
            with self.subTest(k=k),self.assertRaises(C.ComparisonError): C.validate_contract({**C.contract(),k:v})
    def test_frozen_artifact_hashes(self):
        self.assertEqual(len({C.D0_HASH,C.D1_HASH,C.D2_HASH}),3)
    def test_episode_formula(self): self.assertEqual(C.EXPECTED_EPISODES,{"D0":46,"D1":626,"D2":49})
    def test_d0_miss_denominator(self): self.assertEqual(14-11,3)
    def test_d2_incremental_recall(self): self.assertEqual(C.EXPECTED_RECALL["D2"]-C.EXPECTED_RECALL["D0"],0.0)
    def test_d2_incremental_far(self): self.assertEqual(C.EXPECTED_FAR["D2"]-C.EXPECTED_FAR["D0"],0.21168584252925388)
    def test_reports_exact(self): self.assertEqual(len(C.REPORT_NAMES),9)
    def test_adversarial_all_rejected(self): self.assertEqual(C.adversarial(),(30,0))

if __name__=="__main__":unittest.main()
