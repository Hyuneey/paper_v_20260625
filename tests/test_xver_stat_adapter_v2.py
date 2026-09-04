import unittest
from paperworks.candidates.statistical_candidate_discovery_v1 import (
    select_pair_horizon_v1, rank_pair_evidence_v1, PairStatisticalEvidenceV1, verify_vectorized_parity_v1)


class XverStatTests(unittest.TestCase):
    def pair(self, source, target, values):
        records, selection, sign=select_pair_horizon_v1(values)
        return PairStatisticalEvidenceV1(source,target,records,selection,sign)

    def test_optimized_scalar_equivalence(self): verify_vectorized_parity_v1()

    def test_equal_score_lexical_pair_and_smaller_horizon(self):
        values={h:(.5,.7) for h in (1,5,10,30,60)}
        a=self.pair('A','T',values);b=self.pair('B','T',values)
        self.assertEqual(a.selection.selected_horizon,1)
        self.assertEqual(rank_pair_evidence_v1([b,a]),(a,b))

    def test_unstable_sign_never_padded(self):
        values={h:(.9,-.9) for h in (1,5,10,30,60)}
        pair=self.pair('A','T',values)
        self.assertFalse(pair.supported)
        self.assertEqual([p for p in rank_pair_evidence_v1([pair]) if p.supported][:20],[])

    def test_weaker_split_score(self):
        values={h:(.99,.2) for h in (1,5,10,30,60)};values[5]=(.3,.4)
        pair=self.pair('A','T',values)
        self.assertEqual(pair.selection.selected_horizon,5)
        self.assertEqual(pair.selection.score,.3)


if __name__=='__main__':unittest.main()
