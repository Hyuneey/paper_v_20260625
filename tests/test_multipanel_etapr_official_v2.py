import sys
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'artifacts/validation_v2/dg04_xver_prep/metric_source/af9e7aed35cfd160cbe0d04c8ec4c102502cb677'
DEPS=ROOT/'artifacts/validation_v2/dg04_xver_prep/metric_dependencies'
sys.path[:0]=[str(SOURCE),str(DEPS)]

from paperworks.validation_v2.etapr_exchange_v1 import EtaprFileExchangeV1,OfficialEtaprV1
from paperworks.validation_v2.multipanel_etapr_v2 import score_namespaced_union_v2


class OfficialMultiFileBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.wrapper=OfficialEtaprV1(SOURCE)

    def fixtures(self):
        return [EtaprFileExchangeV1('b',20,((2,5),),((3,6),)),EtaprFileExchangeV1('a',15,((8,10),),((8,9),))]

    def test_file_order_and_separator_invariance(self):
        values=[]
        for separator in (1,7,101,1024):
            for files in (self.fixtures(),list(reversed(self.fixtures()))):
                result=score_namespaced_union_v2(self.wrapper,files,separator=separator)
                values.append((result['eTaP'],result['eTaR'],result['F1']))
        self.assertTrue(all(value==values[0] for value in values))
        # Independent block-diagonal oracle: construct the disjoint ranges
        # directly rather than calling the versioned wrapper.
        refs=[];preds=[];offset=0
        for namespace,item in enumerate(sorted(self.fixtures(),key=lambda value:value.file_id)):
            refs.extend(self.wrapper._range_class(offset+a,offset+b,f'or{namespace}-{i}') for i,(a,b) in enumerate(item.reference_ranges))
            preds.extend(self.wrapper._range_class(offset+a,offset+b,f'op{namespace}-{i}') for i,(a,b) in enumerate(item.prediction_ranges))
            offset += item.row_count + 53
        engine=self.wrapper._engine_class(theta_p=.5,theta_r=.1,delta=0.0);engine.set(refs,preds)
        p,r=float(engine.eTaP()),float(engine.eTaR());oracle=(p,r,0 if p+r==0 else 2*p*r/(p+r))
        self.assertEqual(values[0],oracle)

    def test_physical_files_never_merge_ranges(self):
        files=[EtaprFileExchangeV1('a',5,((4,4),),((4,4),)),EtaprFileExchangeV1('b',5,((0,0),),((0,0),))]
        result=score_namespaced_union_v2(self.wrapper,files,separator=1)
        self.assertEqual((result['eTaP'],result['eTaR'],result['F1']),(1,1,1))

    def test_official_empty_behavior_is_guarded(self):
        no_prediction=score_namespaced_union_v2(self.wrapper,[EtaprFileExchangeV1('a',5,((1,2),),())])
        no_ground_truth=score_namespaced_union_v2(self.wrapper,[EtaprFileExchangeV1('a',5,(),((1,2),))])
        self.assertEqual((no_prediction['eTaP'],no_prediction['eTaR'],no_prediction['F1']),(0,0,0))
        self.assertEqual(no_ground_truth['status'],'NOT_APPLICABLE')


if __name__=='__main__': unittest.main()
