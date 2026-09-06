from __future__ import annotations
import unittest
from paperworks.validation_v2.dg05_hai_scenario_adapter_v1 import digest
from paperworks.validation_v2.dg05_label_custodian_v3 import CustodianV3Error,prepare_custodian_input_v3
class V11CustodianTests(unittest.TestCase):
 def scenario(self):
  rows=[]
  for panel,version,prefix,count in [('HAI23_TEST2_PRIMARY_HELDOUT_V1','23.05','H23',38),('HAI22_EXTERNAL_REPLICATION_V1','22.04','H22',58),('HAI21_EXTERNAL_REPLICATION_V1','21.03','H21',50)]:rows += [{'panel_id':panel,'dataset_version':version,'physical_file_id':prefix,'scenario_id':f'{prefix}:{i}','closed_intervals':[{'start':'2026-01-01T00:00:00','end':'2026-01-01T00:00:01'}],'attacked_identities':['X'],'explicit_affected_processes':[]} for i in range(count)]
  b={'schema':'hai_official_source_triangulated_scenario_authority_private_v1','canonical_records':rows};return {**b,'self_hash':digest(b)}
 def p1(self,unresolved=False):
  ds=[{'scenario_id':f'S{i}','eligibility_status':'P1_ELIGIBLE'} for i in range(146)];
  if unresolved:ds[0]['eligibility_status']='UNRESOLVED'
  b={'schema':'hai_p1_direct_target_denominator_authority_v2','decisions':ds};return {**b,'self_hash':digest(b)}
 def test_complete_p1_and_freeze_are_required(self):
  out=prepare_custodian_input_v3(unified_scenario=self.scenario(),unified_p1=self.p1(),predecessor_state={'state':'GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED'});self.assertEqual(len(out['records']),146);self.assertFalse(out['prediction_capability'])
  with self.assertRaisesRegex(CustodianV3Error,'INCOMPLETE'):prepare_custodian_input_v3(unified_scenario=self.scenario(),unified_p1=self.p1(True),predecessor_state={'state':'GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED'})
