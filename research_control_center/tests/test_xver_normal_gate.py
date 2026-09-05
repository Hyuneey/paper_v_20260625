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
        self.assertEqual(p['decision_gates']['DG-05'],'V1_HISTORICAL_EXECUTION_SUSPENDED_V2_USER_REAPPROVAL_REQUIRED' if p.get('dg05_executable_closure') else ('USER_DECISION_REQUIRED' if p.get('multipanel_pre_dg05') else 'NOT_APPROVED'))
        self.assertEqual(
            p['decision_gates']['DG-XVER-PROVIDER'],
            'APPROVED_EXECUTED_QA_PASS' if p.get('xver_t2_execution') else ('USER_DECISION_REQUIRED' if p.get('xver_normal_execution') else 'NOT_READY_EVIDENCE_PENDING'),
        )
        self.assertFalse(p['held_out_authorized'])

    def test_current_reporting_has_precise_blocker(self):
        state=json.loads((RCC/'registry/current_state.yaml').read_text(encoding='utf-8'))
        for f in ('CURRENT_CONTEXT.md','MY_TODO.md','DECISION_INBOX.md','history/PROJECT_TIMELINE.md','history/TERMINOLOGY_GUIDE.md'):
            text=(RCC/f).read_text(encoding='utf-8')
            if state.get('dg05_executable_closure'):
                self.assertIn('DG-05 REAPPROVAL', text)
            elif state.get('xver_t2_execution'):
                self.assertIn('MULTIPANEL-PRE-DG05-FREEZE-001', text)
            elif state.get('xver_normal_execution'):
                self.assertIn('DG-XVER-PROVIDER',text)
                self.assertIn('GLOBAL5',text)
                self.assertIn('EVENT10',text)
            else:
                self.assertIn('BLOCKED_GDN_METHOD_CHANGE_REQUIRED',text)
                self.assertIn('APPROVED_WITH_SEPARATED_GDN_EVIDENCE_ROLES',text)
        dashboard=(RCC/'dashboard/index.html').read_text(encoding='utf-8')
        self.assertIn('DG-05 REAPPROVAL' if state.get('dg05_executable_closure') else ('DG-05' if state.get('multipanel_pre_dg05') else ('MULTIPANEL-PRE-DG05-FREEZE-001' if state.get('xver_t2_execution') else ('DG-XVER-PROVIDER' if state.get('xver_normal_execution') else 'GDN_EVENT_EVIDENCE_BINDING_DECISION_V1.md'))),dashboard)

    def test_approved_role_choice_is_not_execution(self):
        s=json.loads((PUB/'XVER_NORMAL_PREPARATION_STATUS_V2.json').read_text());replay(s)
        b=json.loads((PUB/'GDN_SEPARATED_EVIDENCE_BINDING_V1.json').read_text());replay(b)
        self.assertEqual(s['binding_hash'],b['self_hash'])
        self.assertFalse(s['scientific_decision_required']);self.assertFalse(s['execution_active'])
        self.assertEqual(s['scientific_GDN_runs'],0)
        self.assertEqual(s['global_provider_role'],'EXP03B_COMPATIBLE_SPLIT_PURE_GLOBAL')
        self.assertEqual(s['event_role'],'AUXILIARY_CORROBORATION_ONLY')
        for key in ('global_event_fusion_allowed','event_provider_exposure_allowed','event_retrieval_exposure_allowed',
                    'event_verifier_use_allowed','event_candidate_admission_allowed','event_numeric_policy_selection_allowed',
                    'train3_GDN_allowed','train4_GDN_allowed','best_seed_selection_allowed','provider_calls_authorized'):
            self.assertIs(b[key],False)


if __name__=='__main__':unittest.main()
