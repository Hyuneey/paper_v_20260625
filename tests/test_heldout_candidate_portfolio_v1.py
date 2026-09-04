import unittest
from paperworks.validation_v2.heldout_candidate_portfolio_v1 import retained_descriptors, compare, census, candidate_manifest


def row(source='S', target='T', horizon=5):
    return dict(source=source, target=target, source_direction='step_up', target_direction='increase',
                selected_horizon_seconds=horizon, relation_id='R'+source+target,
                descriptor_hash='a'*64)


def state(cid='C', horizon=5, status='RETAINED'):
    return [cid, dict(source_direction='step_up', target_direction='increase', horizon_seconds=horizon), status]


class PortfolioTests(unittest.TestCase):
    def test_selection_by_semantics_not_position(self):
        a,b=row(),row('U')
        self.assertEqual(retained_descriptors([b,a], [state()], {'C':('S','T')}), [a])

    def test_duplicate_guard_rejected(self):
        with self.assertRaises(ValueError): retained_descriptors([row()], [state(),state()], {'C':('S','T')})

    def test_missing_descriptor_rejected(self):
        with self.assertRaises(ValueError): retained_descriptors([row()], [state(horizon=10)], {'C':('S','T')})

    def test_fail_not_retained(self):
        self.assertEqual(retained_descriptors([row()], [state(status='TRAIN4_COVERAGE_REGRESSION')], {'C':('S','T')}), [])

    def test_unknown_pair(self):
        with self.assertRaises(ValueError): retained_descriptors([row()], [state(cid='UNKNOWN')], {'C':('S','T')})

    def test_missing_lineage(self):
        with self.assertRaises(ValueError): candidate_manifest(arm='T2',repeat=1,descriptors=[row()],lineage={},method_lock_hash='a'*64,source_commit='b'*40,guard_census={},stage_counts={})

    def test_horizon_disagreement(self):
        c=compare([row()], [row(horizon=10)])
        self.assertEqual(c['directional_overlap'],1)
        self.assertEqual(c['horizon_disagreement'],1)
        self.assertEqual(c['exact_semantic_overlap'],0)

    def test_repeat_lock(self):
        for repeat in (2,3):
            with self.assertRaises(ValueError): candidate_manifest(arm='T2',repeat=repeat,descriptors=[row()],lineage={},method_lock_hash='a'*64,source_commit='b'*40,guard_census={},stage_counts={})

    def test_no_runtime_permission(self):
        d=row();m=candidate_manifest(arm='T0',repeat=1,descriptors=[d],lineage={d['relation_id']:{}},method_lock_hash='a'*64,source_commit='b'*40,guard_census={},stage_counts={})
        self.assertFalse(m['production_authorized']);self.assertFalse(m['attack_access_authorized'])

    def test_direction_disagreement(self):
        a=row();b=row();b['target_direction']='decrease'
        self.assertEqual(compare([a],[b])['direction_disagreement_pairs'],1)


if __name__=='__main__':unittest.main()
