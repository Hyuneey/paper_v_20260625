import unittest
from paperworks.validation_v2.etapr_exchange_v1 import EtaprFileExchangeV1, validate_file_batch_v1
from paperworks.validation_v2.evaluation_expansion_v1 import binary_stream_to_closed_ranges_v1


class EtaprExchangeTests(unittest.TestCase):
    def test_closed_endpoints(self):
        self.assertEqual(binary_stream_to_closed_ranges_v1([True,False,True,True],file_id='SYNTHETIC'),
                         ((0,0,'SYNTHETIC:1'),(2,3,'SYNTHETIC:2')))

    def test_file_isolation(self):
        files=[EtaprFileExchangeV1(f,2,((0,1),),((0,1),)) for f in ('A','B')]
        validate_file_batch_v1(files)
        with self.assertRaises(ValueError):validate_file_batch_v1(files+files[:1])

    def test_bad_ranges(self):
        for ranges in (((-1,0),),((0,3),),((1,0),),((0,1),(1,2)),((True,1),)):
            with self.subTest(ranges=ranges),self.assertRaises(ValueError):
                EtaprFileExchangeV1('SYNTHETIC',3,ranges,()).validate()

    def test_empty_input_remains_explicit(self):
        EtaprFileExchangeV1('SYNTHETIC',3,(),()).validate()
        with self.assertRaises(ValueError):validate_file_batch_v1([])

    def test_prediction_fragmentation_rejected_reference_preserved(self):
        EtaprFileExchangeV1('SYNTHETIC',4,((0,1),(2,3)),((0,3),)).validate()
        with self.assertRaisesRegex(ValueError,'MAXIMAL'):
            EtaprFileExchangeV1('SYNTHETIC',4,((0,1),),((0,1),(2,3))).validate()

    def test_namespaced_empty_contract_without_engine(self):
        from paperworks.validation_v2.etapr_exchange_v1 import OfficialEtaprV1
        wrapper=object.__new__(OfficialEtaprV1)
        no_gt=wrapper.score_namespaced_union([EtaprFileExchangeV1('A',3,(),((1,1),))])
        no_prediction=wrapper.score_namespaced_union([EtaprFileExchangeV1('A',3,((1,1),),())])
        self.assertEqual(no_gt['status'],'NOT_APPLICABLE')
        self.assertEqual((no_prediction['eTaP'],no_prediction['eTaR'],no_prediction['F1']),(0,0,0))
