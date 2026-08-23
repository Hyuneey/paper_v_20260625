from __future__ import annotations
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("audit_v2_ind",ROOT/"scripts/audit_task039e3_r2r_d2_v2_result_integrity_v1.py")
assert SPEC and SPEC.loader
audit=importlib.util.module_from_spec(SPEC); sys.modules[SPEC.name]=audit; SPEC.loader.exec_module(audit)

class IndependentD2V2AuditTests(unittest.TestCase):
    def test_50_attacks_all_rejected(self):
        total,accepted=audit.adversarial()
        self.assertEqual(total,50); self.assertEqual(accepted,0)
    def test_canonical_hash_rejects_mutation(self):
        x=audit.self_hash({"a":1})
        audit.validate_hash(x,x["artifact_hash"])
        x["a"]=2
        with self.assertRaises(audit.AuditError): audit.validate_hash(x,x["artifact_hash"])
    def test_trigger_truth_table_names(self):
        self.assertEqual(set(audit.TRIGGERS),{"NONE","D0_ONLY","RULE_RECOVERY_NATIVE_HORIZON","D0_AND_RULE_CORROBORATION_NATIVE_HORIZON"})
    def test_result_freeze_paths_exact(self):
        self.assertEqual(len(audit.RESULT_FILES),8)
    def test_no_outer_authority(self):
        self.assertEqual(audit.SCIENTIFIC_STATUS,"D2_V2_RESULT_INTEGRITY_AUDITED")
        self.assertNotIn("OUTER",audit.NEXT_TASK)
    def test_no_scientific_interpretation(self):
        task=(ROOT/"TASKS/TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-V1.md").read_text(encoding="utf-8")
        self.assertIn("integrity verification only",task.lower())
        self.assertIn("Do NOT interpret",task)

if __name__=="__main__": unittest.main()
