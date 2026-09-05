"""Receipt-only final external normal closure checks; never opens private data."""
import json
import unittest
from decimal import Decimal
from pathlib import Path
from paperworks.validation_v2.exp03b_custody_v1 import replay

RCC=Path(__file__).resolve().parents[1]
PUB=RCC/'validation_v2/xver_normal'
PARENT=RCC/'validation_v2/dg04_xver_prep'


def read(path):
    value=json.loads(path.read_text(encoding='utf-8'));replay(value);return value


class ExternalExecutionReportingTests(unittest.TestCase):
    def test_twelve_unique_exact_runs_and_separated_evidence(self):
        ids=set();authority=read(PUB/'GDN_EXECUTION_AUTHORITY_V2.json')
        for version in ('22.04','21.03'):
            context=read(PUB/f'HAI{version[:2]}_GDN_CONTEXT_MAPPING_V1.json')
            candidate=read(PARENT/f'HAI{version[:2]}_META_STAT_CANDIDATE_AUTHORITY_V2.json')
            for split in ('train1','train2'):
                for seed in (11,23,37):
                    r=read(PUB/'runs'/f'HAI{version[:2]}_{split.upper()}_SEED{seed}_RECEIPT_V1.json')
                    self.assertEqual((version,split,seed),(r['version'],r['split'],r['seed']))
                    self.assertEqual(r['authority_hash'],authority['self_hash'])
                    self.assertEqual(r['node_count'],context['context_count'])
                    self.assertEqual((r['scope'],r['status']),('SCIENTIFIC','PASS'))
                    self.assertNotIn(r['run_identity_hash'],ids);ids.add(r['run_identity_hash'])
                    self.assertEqual(r['global_row_count'],5*candidate['candidate_count'])
                    self.assertEqual(r['auxiliary_row_count'],10*candidate['candidate_count'])
                    self.assertFalse(r['global_auxiliary_fused']);self.assertFalse(r['excluded_label_values_parsed'])
                    self.assertTrue(all(r[k]==0 for k in ('raw_timestamp_overlap','provider_calls','credential_reads','attack_accesses')))
        self.assertEqual(len(ids),12)

    def test_version_evidence_portfolio_budget_closure(self):
        result=read(PUB/'NORMAL_EXECUTION_RESULT_V1.json');budgets=[]
        for version,v in result['versions'].items():
            prefix='HAI'+version[:2]
            candidate=read(PARENT/f'{prefix}_META_STAT_CANDIDATE_AUTHORITY_V2.json')
            evidence=read(PUB/f'{prefix}_EVIDENCE_FREEZE_V1.json')
            portfolio=read(PUB/f'{prefix}_T0_PORTFOLIO_AUTHORITY_V1.json')
            budget=read(PUB/f'{prefix}_T2_PROVIDER_BUDGET_V1.json');budgets.append(budget)
            profile=read(PUB/f'{prefix}_T2_TOKEN_PROFILE_V1.json')
            gdn=read(PUB/f'{prefix}_GDN_EVIDENCE_AUTHORITY_V1.json')
            subqa=read(PUB/f'{prefix}_INDEPENDENT_SUBQA_V1.json')
            self.assertEqual(candidate['candidate_count'],evidence['N'])
            self.assertEqual(candidate['self_hash'],portfolio['candidate_hash'])
            self.assertEqual(evidence['self_hash'],portfolio['evidence_hash'])
            self.assertEqual(portfolio['self_hash'],v['T0_portfolio_hash'])
            self.assertEqual(gdn['self_hash'],v['GDN_evidence_hash'])
            self.assertEqual(len(gdn['runs']),6)
            self.assertEqual(len({(r['split'],r['seed'],r['receipt_hash']) for r in gdn['runs']}),6)
            self.assertFalse(gdn['best_seed_selection']);self.assertFalse(gdn['global_event_fusion'])
            self.assertEqual(subqa['status'],'PASS')
            self.assertEqual(subqa['authority_hashes']['T0_portfolio'],portfolio['self_hash'])
            self.assertEqual(subqa['authority_hashes']['provider_budget'],budget['self_hash'])
            self.assertTrue(all(subqa[k]==0 for k in ('public_private_values_exposed','provider_calls','credential_reads','attack_or_label_accesses','independent_writes')))
            self.assertEqual(portfolio['T0_field_contract'],'STRUCTURAL_ROWS_ONLY')
            self.assertEqual(portfolio['status'],'HELDOUT_CANDIDATE_NOT_ATTACK_VALIDATED_NOT_PRODUCTION')
            self.assertEqual(portfolio['policy_searches'],0)
            self.assertEqual(evidence['event_rows_exposed'],0)
            self.assertEqual(budget['profile_hash'],profile['self_hash'])
            self.assertEqual(budget['self_hash'],v['budget_hash'])
            self.assertEqual(budget['maximum_calls'],3*evidence['N'])
            self.assertEqual(budget['maximum_total_tokens'],budget['maximum_input_tokens']+budget['maximum_output_tokens'])
            self.assertEqual((budget['arms'],budget['repetitions']),(['T2'],1))
            self.assertFalse(budget['prior_approval_inherited'])
            self.assertEqual(budget['status'],'USER_DECISION_REQUIRED')
        combined=result['combined_provider_ceiling']
        for field in ('maximum_calls','maximum_input_tokens','maximum_output_tokens','maximum_total_tokens'):
            self.assertEqual(combined[field],sum(b[field] for b in budgets))
        self.assertEqual(Decimal(combined['cost_ceiling_usd']),sum(Decimal(b['prospective_standard_price_ceiling_usd']) for b in budgets))

    def test_private_restore_and_historical_metrics_are_distinct(self):
        private=read(PUB/'PUBLIC_PRIVATE_EXECUTION_INDEX_V2.json')
        self.assertEqual(private['restore_read_hash_smoke'],'PASS')
        self.assertEqual(private['storage_policy'],'SINGLE_COPY_LOCAL_ONLY')
        self.assertFalse(private['second_copy_verified'])
        metric=read(PUB/'ETAPR_CONFORMANCE_RECEIPT_V2.json')
        self.assertEqual(len(metric['cases']),109)
        self.assertTrue(all(r['exact_equality'] for r in metric['cases']))
        self.assertEqual(metric['real_attack_or_label_files_accessed'],0)
        self.assertEqual(metric['multi_file_aggregation'],'UNRESOLVED_NOT_EXECUTED')

    def test_current_gate_does_not_rewrite_historical_preparation(self):
        state=json.loads((RCC/'registry/current_state.yaml').read_text(encoding='utf-8'))
        current=state['xver_normal_execution'];replay(current)
        self.assertEqual(current['result_authority_hash'],read(PUB/'NORMAL_EXECUTION_RESULT_V1.json')['self_hash'])
        self.assertEqual(current['scientific_GDN_runs'],12)
        self.assertEqual(state['xver_normal_preparation']['scientific_GDN_runs'],0)
        self.assertEqual(state['exact_next_task'],'DG-05 — Multi-Panel Attack Feature + Conditional Label/Scenario Access' if state.get('multipanel_pre_dg05') else ('MULTIPANEL-PRE-DG05-FREEZE-001' if state.get('xver_t2_execution') else 'DG-XVER-PROVIDER'))
        self.assertEqual(current['DG05'],'NOT_APPROVED')
        self.assertEqual(current['professor_package'],'NOT_SUBMITTED')
        self.assertTrue(all(current[k]==0 for k in ('provider_calls','credential_reads','attack_accesses')))
        self.assertFalse(current['stage_a_changed'])
