import unittest
from paperworks.validation_v2.p1_eligibility_design_v1 import validate_future_eligibility_record_v1, validate_future_release_gate_v1
from paperworks.validation_v2.exp03b_custody_v1 import seal


class EligibilityDesignTests(unittest.TestCase):
    def test_synthetic_shape(self):
        value=dict(scenario_id='SYNTHETIC',official_target_id='SYNTHETIC_POINT',mapping_hash='a'*64,
                   status='UNRESOLVED',official_source_hash='b'*64)
        validate_future_eligibility_record_v1(value)
        for field in ('prediction','rule_fired','detector_score','hit','raw_value'):
            with self.assertRaises(ValueError):validate_future_eligibility_record_v1({**value,field:True})

    def test_release_requires_all_methods(self):
        methods={'H0':'c'*64,'H1':'d'*64}
        record=dict(panel_id='SYNTHETIC_PANEL',method_prediction_hashes=methods,
                    all_predictions_durably_frozen=True,prediction_generators_revoked=True,
                    label_access_started=False,dg05_authorization_hash='e'*64)
        validate_future_release_gate_v1(seal(record),methods,panel_id='SYNTHETIC_PANEL')
        for key,value in (('method_prediction_hashes',{'H0':'c'*64}),('all_predictions_durably_frozen',False),
                          ('prediction_generators_revoked',False),('label_access_started',True),('dg05_authorization_hash',None)):
            with self.assertRaises(ValueError):
                validate_future_release_gate_v1(seal({**record,key:value}),methods,panel_id='SYNTHETIC_PANEL')
