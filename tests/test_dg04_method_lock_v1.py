import copy
import json
from pathlib import Path
import unittest
from paperworks.validation_v2.final_method_lock_v1 import method_lock, TITLE, NUMERIC_POLICY
from paperworks.validation_v2.exp03b_custody_v1 import replay

ROOT = Path(__file__).resolve().parents[1]


class MethodLockTests(unittest.TestCase):
    def inputs(self):
        root = ROOT / 'research_control_center/validation_v2/exp03b/execution_v2'
        return [json.loads((root / name).read_text()) for name in
                ('EXP03B_REVISED_RESULTS_V1.json', 'EXP03B_EXECUTION_INDEPENDENT_QA_V1.json')]

    def test_exact_result_and_qa(self):
        lock = method_lock(*self.inputs()); replay(lock)
        self.assertEqual(lock['title'], TITLE)
        self.assertEqual(lock['numeric_policy'], NUMERIC_POLICY)

    def test_no_new_access_or_repeat_choice(self):
        lock = method_lock(*self.inputs())
        for field in ('provider_calls_allowed', 'attack_access_allowed', 'production_authorized',
                      'additional_agentic_rescue_allowed', 'numeric_reselection_allowed'):
            self.assertIs(lock[field], False)
        self.assertEqual(lock['T2_portfolio_repeat'], 1)
        self.assertEqual(lock['claim_status']['agentic_vs_T0'], 'NOT_SUPPORTED')

    def test_result_mutation_fails(self):
        result, qa = self.inputs(); result['disposition'] = 'OTHER'
        with self.assertRaises(ValueError): method_lock(result, qa)

    def test_qa_mutation_fails(self):
        result, qa = self.inputs(); qa['status'] = 'FAIL'
        with self.assertRaises(ValueError): method_lock(result, qa)

    def test_method_roles_and_fusion(self):
        lock = method_lock(*self.inputs())
        self.assertEqual(len(lock['primary_methods']), 5)
        self.assertEqual(lock['fusion']['minimum_distinct_physical_sources'], 2)
        self.assertEqual(lock['fusion']['outcomes'], ['FAIL'])
        self.assertTrue(lock['fusion']['preserve_base_detector_alarm_pointwise'])


if __name__ == '__main__': unittest.main()
