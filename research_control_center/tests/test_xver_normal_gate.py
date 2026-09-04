"""Current scientific gate may not be reported as an executed experiment."""
import json
from pathlib import Path
import unittest
from paperworks.validation_v2.exp03b_custody_v1 import replay

RCC=Path(__file__).resolve().parents[1]
PUB=RCC/'validation_v2/xver_normal'


class XverNormalGateTests(unittest.TestCase):
    def test_truthful_scientific_stop(self):
        s=json.loads((PUB/'XVER_NORMAL_PREPARATION_STATUS_V1.json').read_text());replay(s)
        self.assertEqual(s['status'],'BLOCKED_GDN_METHOD_CHANGE_REQUIRED')
        self.assertEqual(s['scientific_GDN_runs'],0)
        for v in s['versions'].values():
            self.assertFalse(v['T0_executed']);self.assertFalse(v['T2_evidence_ready'])
            self.assertIsNone(v['cost_ceiling']);self.assertIsNone(v['hard_token_ceiling'])
            self.assertEqual(v['maximum_calls_structural_only'],3*v['candidate_count'])

    def test_context_receipts_have_only_normal_splits(self):
        for v in ('22','21'):
            d=json.loads((PUB/f'HAI{v}_GDN_CONTEXT_PROJECTION_RECEIPT_V1.json').read_text());replay(d)
            self.assertEqual({r['source_file_identity'] for r in d['records']},{f'HAI{v}_TRAIN1',f'HAI{v}_TRAIN2'})
            for r in d['records']:
                replay(r)
                self.assertFalse(r['label_values_parsed']);self.assertFalse(r['label_values_used'])
                self.assertFalse(r['label_values_validated'])
                self.assertFalse({'Attack','attack','attack_P1','attack_P2','attack_P3'}&set(r['projected_feature_identities']))

    def test_no_gate_authorization(self):
        p=json.loads((RCC/'validation_v2/PROGRAM_STATE.json').read_text(encoding='utf-8'))
        self.assertEqual(p['decision_gates']['DG-05'],'NOT_APPROVED')
        self.assertEqual(p['decision_gates']['DG-XVER-PROVIDER'],'NOT_READY_EVENT_EVIDENCE_BINDING_REQUIRED')
        self.assertFalse(p['held_out_authorized'])

    def test_current_reporting_has_precise_blocker(self):
        for f in ('CURRENT_CONTEXT.md','MY_TODO.md','DECISION_INBOX.md','history/PROJECT_TIMELINE.md','history/TERMINOLOGY_GUIDE.md'):
            text=(RCC/f).read_text(encoding='utf-8')
            self.assertIn('BLOCKED_GDN_METHOD_CHANGE_REQUIRED',text)
        self.assertIn('GDN_EVENT_EVIDENCE_BINDING_DECISION_V1.md',(RCC/'dashboard/index.html').read_text(encoding='utf-8'))


if __name__=='__main__':unittest.main()
