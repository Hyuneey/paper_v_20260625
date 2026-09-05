import unittest
from paperworks.validation_v2.etapr_exchange_v1 import OfficialEtaprV1,EtaprFileExchangeV1
from paperworks.validation_v2.multipanel_etapr_v2 import score_namespaced_union_v2

class MultiPanelEtaprV2Tests(unittest.TestCase):
    def wrapper(self):return object.__new__(OfficialEtaprV1)
    def test_empty_contract(self):
        wrapper=self.wrapper()
        self.assertEqual(score_namespaced_union_v2(wrapper,[EtaprFileExchangeV1('A',3,(),((1,1),))])['status'],'NOT_APPLICABLE')
        value=score_namespaced_union_v2(wrapper,[EtaprFileExchangeV1('A',3,((1,1),),())])
        self.assertEqual((value['eTaP'],value['eTaR'],value['F1']),(0,0,0))
        self.assertEqual(value['per_file'][0]['status'],'PASS_EMPTY_PREDICTION')
        self.assertEqual(score_namespaced_union_v2(wrapper,[EtaprFileExchangeV1('A',3,(),((1,1),))])['per_file'][0]['status'],'NOT_APPLICABLE')
    def test_separator_rejects_no_gap(self):
        with self.assertRaises(ValueError):score_namespaced_union_v2(self.wrapper(),[EtaprFileExchangeV1('A',2,((0,0),),())],separator=0)

if __name__=='__main__':unittest.main()
