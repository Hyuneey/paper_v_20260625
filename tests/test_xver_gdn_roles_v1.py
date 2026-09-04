import unittest
from paperworks.validation_v2.xver_gdn_roles_v1 import (
    GlobalSeedEvidenceV1, AuxiliaryEventEvidenceV1, provider_global, retrieval_global,
    event_validation_starts,
)
from paperworks.validation_v2.exp03b_contract_v1 import SOURCES, TARGETS, HORIZONS, digest, SemanticTupleV1, StructuralTupleEvidenceV1
from paperworks.validation_v2.exp03b_semantic_v2 import Train1SemanticEvidenceV2
from paperworks.validation_v2.xver_gdn_provider_v1 import project_global_only


def global_seed(seed, split='train1', effect=1.):
    return GlobalSeedEvidenceV1('22.04', split, seed, 'S', 'T', tuple((h, .2, 0., effect) for h in HORIZONS))


def auxiliary(effect=1.):
    return AuxiliaryEventEvidenceV1('22.04', 'train1', 11, 'S', 'T',
        tuple((s, h, 1, effect, 'AVAILABLE') for s in SOURCES for h in HORIZONS))


class SeparatedEvidenceTests(unittest.TestCase):
    def test_five_global_rows_exact_available_seed_median(self):
        result=provider_global((global_seed(11, effect=-2.),global_seed(23,effect=None),global_seed(37,effect=4.)),version='22.04')
        self.assertEqual(len(result),5)
        self.assertTrue(all(row[3]==1. for row in result))

    def test_negative_is_preserved(self):
        result=provider_global(tuple(global_seed(s,effect=-1.) for s in (11,23,37)),version='22.04')
        self.assertTrue(all(row[3]==-1. for row in result))

    def test_nonmember_is_none_not_zero(self):
        result=provider_global(tuple(global_seed(s,effect=None) for s in (11,23,37)),version='22.04')
        self.assertTrue(all(row[3] is None for row in result))

    def test_auxiliary_cannot_enter_global(self):
        with self.assertRaisesRegex(ValueError,'GLOBAL_ONLY_NO_EVENT_FUSION'):
            provider_global((global_seed(11),global_seed(23),auxiliary()),version='22.04')

    def test_event_changes_cannot_change_provider_hash(self):
        seeds=tuple(global_seed(s) for s in (11,23,37))
        before=digest(provider_global(seeds,version='22.04'))
        first=auxiliary(10.);second=auxiliary(-999.)
        self.assertNotEqual(first,second)
        self.assertEqual(before,digest(provider_global(seeds,version='22.04')))

    def test_no_best_seed_or_duplicate(self):
        for seeds in ((global_seed(11),),(global_seed(11),global_seed(11),global_seed(37))):
            with self.assertRaises(ValueError):provider_global(seeds,version='22.04')

    def test_no_train2_provider_or_train1_retrieval(self):
        with self.assertRaises(ValueError):provider_global(tuple(global_seed(s,'train2') for s in (11,23,37)),version='22.04')
        with self.assertRaises(ValueError):retrieval_global(tuple(global_seed(s) for s in (11,23,37)),version='22.04')

    def test_hidden_split_rejected(self):
        for split in ('train3','train4','test1','test2'):
            with self.assertRaises(ValueError):global_seed(11,split)

    def test_version_taint_rejected(self):
        with self.assertRaises(ValueError):provider_global(tuple(global_seed(s) for s in (11,23,37)),version='21.03')

    def test_event_ten_axes(self):
        self.assertEqual(len(auxiliary().rows),10)
        with self.assertRaises(ValueError):
            AuxiliaryEventEvidenceV1('22.04','train1',11,'S','T',auxiliary().rows[:5])

    def test_seed_validation_intersection_stop_anchor(self):
        self.assertEqual(event_validation_starts(source_event_rows=(5,7,20),validation_indices=((0,0),(0,1),(0,2))), (0,2))
        with self.assertRaises(ValueError):event_validation_starts(source_event_rows=(5,),validation_indices=((1,0),))

    def test_event_unavailable_is_not_fabricated_zero(self):
        rows=tuple((s,h,0,None,'NO_VALIDATION_EVENT') for s in SOURCES for h in HORIZONS)
        AuxiliaryEventEvidenceV1('21.03','train2',11,'S','T',rows)
        with self.assertRaises(ValueError):
            AuxiliaryEventEvidenceV1('21.03','train2',11,'S','T',tuple((s,h,0,0.,'NO_VALIDATION_EVENT') for s in SOURCES for h in HORIZONS))

    def test_nested_rows_are_immutable(self):
        with self.assertRaises(ValueError):
            GlobalSeedEvidenceV1('22.04','train1',11,'S','T',tuple(list(r) for r in global_seed(11).rows))
        with self.assertRaises(ValueError):
            AuxiliaryEventEvidenceV1('22.04','train1',11,'S','T',tuple(list(r) for r in auxiliary().rows))

    def test_actual_provider_projector_global_only(self):
        rows=tuple(StructuralTupleEvidenceV1(SemanticTupleV1(s,t,h),5,.7,.1,2.,
                   'EV-'+digest((s,t,h))[:24]) for s in SOURCES for t in TARGETS for h in HORIZONS)
        evidence=Train1SemanticEvidenceV2('EXP03B-CAND-'+digest({'source':'S','target':'T'})[:20],'S','T','a'*64,rows)
        args=dict(version='22.04',train1=evidence,stat_association=.5,checkpoint_receipt_hash='b'*64)
        seeds=tuple(global_seed(s) for s in (11,23,37))
        before=project_global_only(global_seeds=seeds,**args)
        self.assertEqual(len(before['gdn_rows']),5)
        self.assertEqual(len(before['structural_rows']),20)
        with self.assertRaises(ValueError):
            project_global_only(global_seeds=(global_seed(11),global_seed(23),auxiliary()),**args)
        with self.assertRaises(TypeError):
            project_global_only(global_seeds=seeds,auxiliary=auxiliary(),**args)
        self.assertEqual(digest(before),digest(project_global_only(global_seeds=seeds,**args)))

    def test_auxiliary_rejected_by_frozen_t0_and_verifier(self):
        from paperworks.validation_v2.exp03b_semantic_v2 import t0, SemanticProposalV2
        from paperworks.validation_v2.exp03b_hidden_v2 import verify
        with self.assertRaises(ValueError):t0(auxiliary())
        with self.assertRaises(ValueError):verify(SemanticProposalV2('NO_RULE',()),auxiliary())


if __name__=='__main__':unittest.main()
