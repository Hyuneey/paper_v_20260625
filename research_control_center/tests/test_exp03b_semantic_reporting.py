"""Current semantic DG03B values must not regress to superseded V1 budget."""
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];PUB=ROOT/'research_control_center/validation_v2/exp03b';RCC=ROOT/'research_control_center'


class SemanticReportingTests(unittest.TestCase):
    def test_current_budget_and_provider_boundary(self):
        budget=json.loads((PUB/'EXP03B_PROVIDER_BUDGET_V2.json').read_text())
        state=json.loads((RCC/'registry/current_state.yaml').read_text(encoding='utf-8'))['exp03b_preparation']
        self.assertEqual('DG-03B_REVISED',state['next_gate']);self.assertIs(state['numeric_provider_visible'],False)
        for key in ('maximum_calls','maximum_input_tokens','maximum_output_tokens','maximum_total_tokens'):self.assertEqual(budget[key],state[key])
        self.assertEqual(budget['standard_api_cost_ceiling_usd'],state['cost_ceiling_usd'])
    def test_current_documents_not_old_approval_values(self):
        for name in ('CURRENT_CONTEXT.md','MY_TODO.md','DECISION_INBOX.md','generated/GPT_BRIEF.md'):
            text=(RCC/name).read_text(encoding='utf-8');self.assertIn('DG-03B_REVISED',text);self.assertNotIn('USD65.90',text);self.assertNotIn('81,621,225',text)
        html=(RCC/'dashboard/index.html').read_text(encoding='utf-8')
        self.assertIn('numeric option rows 0',html);self.assertIn('DG03B_PROVIDER_DECISION_BRIEF_V2.md',html);self.assertIn('8,463,360',html)
    def test_supersession_preserves_old_contracts(self):
        self.assertTrue((PUB/'SCI02_NUMERIC_OPTION_POLICY_V1.md').exists());self.assertTrue((PUB/'EXP03B_PREREGISTRATION_V1.json').exists())
        new=json.loads((PUB/'EXP03B_PREREGISTRATION_V2.json').read_text());self.assertFalse(new['provider_execution_authorized']);self.assertFalse(new['numeric_provider_selection']);self.assertEqual(new['portfolio_repeat'],1)
        old=json.loads((PUB/'EXP03B_PROVIDER_BUDGET_V1.json').read_text());self.assertEqual(old['maximum_input_tokens'],80373993)
    def test_professor_submission_not_performed(self):
        text=(ROOT/'docs/professor_experiment_update_v2/PROFESSOR_EXPERIMENT_UPDATE_V2.html').read_text(encoding='utf-8')
        self.assertIn('EXP03B-PAYLOAD-REDUCE-001',text);self.assertIn('DG-03B_REVISED',text);self.assertIn('제출하지 않았습니다',text)


if __name__=='__main__':unittest.main()
