"""Public-only regression checks for the executed semantic experiment."""
import json
from fractions import Fraction
from pathlib import Path
import unittest

from paperworks.validation_v2.exp03b_custody_v1 import replay

ROOT = Path(__file__).resolve().parents[2]
RCC = ROOT / 'research_control_center'
PUB = RCC / 'validation_v2/exp03b/execution_v2'


def read(name):
    value = json.loads((PUB / name).read_text()); replay(value); return value


class ExecutedSemanticReportingTests(unittest.TestCase):
    def test_results_bound_to_independent_qa(self):
        result = read('EXP03B_REVISED_RESULTS_V1.json'); qa = read('EXP03B_EXECUTION_INDEPENDENT_QA_V1.json')
        self.assertEqual(qa['result_hash'], result['self_hash']); self.assertEqual(qa['status'], 'PASS')
        self.assertEqual(result['N'], 29); self.assertEqual(result['next_gate'], 'DG-04')

    def test_call_usage_and_reserved_budget(self):
        r = read('EXP03B_REVISED_RESULTS_V1.json'); total = r['usage_total']
        self.assertEqual([r['usage_by_arm'][a]['calls'] for a in ('T1', 'T1-B', 'T2')], [87, 261, 170])
        for key in ('calls', 'input_tokens', 'output_tokens'):
            self.assertEqual(total[key], sum(v[key] for v in r['usage_by_arm'].values()))
        self.assertEqual(total['total_tokens'], total['input_tokens'] + total['output_tokens'])
        self.assertLessEqual(total['calls'], 609); self.assertLessEqual(total['total_tokens'], 8463360)

    def test_strict_reference_and_raw_denominators(self):
        r = read('EXP03B_REVISED_RESULTS_V1.json')
        for arm, report in r['reports'].items():
            self.assertEqual(report['strict']['N'], 29)
            c = report['raw_and_admitted_coverage']; self.assertEqual(c['observations'], 29 if arm == 'T0' else 87)
            self.assertLessEqual(c['admitted'], c['selected_raw_parsed'])
            self.assertEqual(sum(c['terminals'].values()), c['observations'])

    def test_fixed_disposition_and_t0_limitation(self):
        r = read('EXP03B_REVISED_RESULTS_V1.json')
        f = lambda x: Fraction(x['numerator'], x['denominator'])
        self.assertEqual(r['disposition'], 'AGENTIC_ADVANTAGE_SUPPORTED')
        self.assertGreater(f(r['reports']['T0']['strict']['F1']), f(r['reports']['T2']['strict']['F1']))
        self.assertGreater(f(r['reports']['T2']['strict']['F1']), f(r['reports']['T1-B']['strict']['F1']))
        brief = (PUB / 'DG04_EXP03B_DECISION_BRIEF_V1.md').read_text(encoding='utf-8')
        self.assertIn('T0가 T2보다 높습니다', brief); self.assertIn('lexicographic', brief)

    def test_no_attack_or_deployment_and_single_copy(self):
        r = read('EXP03B_REVISED_RESULTS_V1.json')
        for key in ('test1', 'test2', 'heldout', 'external_attack', 'attack_label', 'GDN_retraining', 'frozen_result_changes', 'post_result_tuning', 'private_exposures'):
            self.assertEqual(r[key], 0)
        self.assertFalse(r['production_portfolio_created'])
        index = read('EXP03B_EXECUTION_PRIVATE_INDEX_V1.json')
        self.assertEqual(index['storage_policy'], 'SINGLE_COPY_LOCAL_ONLY'); self.assertFalse(index['second_copy_verified'])

    def test_current_gate_and_result_registry_binding(self):
        r = read('EXP03B_REVISED_RESULTS_V1.json')
        state = json.loads((RCC / 'registry/current_state.yaml').read_text(encoding='utf-8'))
        program = json.loads((RCC / 'validation_v2/PROGRAM_STATE.json').read_text(encoding='utf-8'))
        self.assertEqual(state['exp03b_execution']['result_hash'], r['self_hash'])
        self.assertEqual(program['decision_gates']['DG-03B_REVISED'], 'APPROVED_EXECUTED')
        if state.get('dg04_method_lock'):
            self.assertEqual(state['dg04_method_lock']['decision_id'],'DEC-025')
            self.assertEqual(program['decision_gates']['DG-04'],'APPROVED_WITH_SCOPED_AGENTIC_CLAIM')
            self.assertEqual(state['dg04_method_lock']['method_lock_hash'],'82b483ca92926d0bbf0020de496a61d0377429fe56807c8f96c44c89557d7c13')
            self.assertEqual(state['xver_preparation']['DG03C'],'NOT_READY')
            self.assertEqual(state['xver_preparation']['provider_calls'],0)
        else:
            self.assertEqual(program['decision_gates']['DG-04'], 'USER_DECISION_REQUIRED')
        self.assertFalse(program['held_out_authorized'])
        html = (RCC / 'dashboard/index.html').read_text(encoding='utf-8')
        self.assertIn('EXP03B_RESULTS_REPORT_V1.md', html); self.assertIn('518 calls', html)


if __name__ == '__main__': unittest.main()
