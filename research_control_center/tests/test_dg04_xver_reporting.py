"""Exact new decision/current-blocker checks; historical results remain distinct."""
import json,unittest
from pathlib import Path
from paperworks.validation_v2.exp03b_custody_v1 import replay

RCC=Path(__file__).resolve().parents[1]
PUB=RCC/'validation_v2/dg04_xver_prep'


def read(path):return json.loads(path.read_text(encoding='utf-8'))


class Dg04XverReportingTests(unittest.TestCase):
    def test_exact_lock_and_portfolio_repeats(self):
        lock=read(PUB/'FINAL_METHOD_LOCK_V1.json');replay(lock)
        self.assertEqual(lock['self_hash'],'82b483ca92926d0bbf0020de496a61d0377429fe56807c8f96c44c89557d7c13')
        self.assertEqual(lock['claim_status']['agentic_vs_T0'],'NOT_SUPPORTED')
        for arm,expected in (('T0','d95c0bb8234304f2b769e088f4399b6c071b2156982c9e1fadd175dbab5dba02'),
                             ('T2','bc2b5996989228f198dbcbf38cbedaf38516366f55d5011978ecda94ccf699b6')):
            p=read(PUB/f'{arm}_HELDOUT_CANDIDATE_PORTFOLIO_V1.json');replay(p)
            self.assertEqual(p['self_hash'],expected);self.assertEqual(p['repeat'],1)
            self.assertFalse(p['attack_access_authorized']);self.assertFalse(p['production_authorized'])

    def test_metadata_not_execution_mapping(self):
        mapping=read(PUB/'P1_FEATURE_MAPPING_AUTHORITY_V1.json');replay(mapping)
        self.assertFalse(mapping['normal_execution_authorized']);self.assertEqual(mapping['aliases_inferred'],0)
        self.assertTrue(all(not r['execution_eligible'] for r in mapping['rows']))
        self.assertEqual(mapping['portable_meta_counts'],{'21.03':19,'22.04':20})

    def test_no_fabricated_budget_or_label_zero_claim(self):
        state=read(RCC/'registry/current_state.yaml');program=read(RCC/'validation_v2/PROGRAM_STATE.json')
        self.assertEqual(state['xver_preparation']['status'],'BLOCKED_NORMAL_DATA_CUSTODY')
        self.assertIsNone(state['xver_preparation']['exact_provider_budget'])
        self.assertEqual(program['decision_gates']['DG-04'],'APPROVED_WITH_SCOPED_AGENTIC_CLAIM')
        self.assertEqual(program['decision_gates']['DG-03C'],'NOT_READY_BLOCKED_NORMAL_DATA_CUSTODY')
        blocker=read(PUB/'XVER_NORMAL_CUSTODY_BLOCKER_V1.json');replay(blocker)
        self.assertTrue(blocker['normal_container_bytes_downloaded_hashed_and_decompressed'])
        self.assertEqual(blocker['embedded_label_value_semantic_validation_or_use'],0)
        self.assertFalse(blocker['normal_custody_ready']);self.assertFalse(blocker['integration_merge_allowed'])

    def test_dashboard_scope_and_no_pooling(self):
        html=(RCC/'dashboard/index.html').read_text(encoding='utf-8')
        for token in ('dg04-xver-heading','Repeat 1','BLOCKED_NORMAL_DATA_CUSTODY','DG-03C exact budget 미정',
                      '동일 분포의 독립 표본으로 간주하지'):
            self.assertIn(token,html)
