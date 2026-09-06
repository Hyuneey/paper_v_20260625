from __future__ import annotations
import unittest
from paperworks.validation_v2.dg05_hai_scenario_adapter_v1 import OfficialHAIScenarioAdapterError, adapt_frozen_hai_authority, digest

class ScenarioAdapterGateTests(unittest.TestCase):
 def authority(self):
  rows=[]
  for panel,version,prefix,count in [('HAI23_TEST2_PRIMARY_HELDOUT_V1','23.05','HAI23',38),('HAI22_EXTERNAL_REPLICATION_V1','22.04','HAI22',58),('HAI21_EXTERNAL_REPLICATION_V1','21.03','HAI21',50)]:
   rows += [{'panel_id':panel,'dataset_version':version,'physical_file_id':f'{prefix}_TEST1','scenario_id':f'{prefix}:{i}','closed_intervals':[{'start':'2026-01-01T00:00:00','end':'2026-01-01T00:00:01'}],'attacked_identities':['X'],'explicit_affected_processes':[]} for i in range(count)]
  body={'schema':'hai_official_source_triangulated_scenario_authority_private_v1','canonical_records':rows};return {**body,'self_hash':digest(body)}
 def test_prefreeze_access_fails(self):
  with self.assertRaisesRegex(OfficialHAIScenarioAdapterError,'BEFORE_GLOBAL_FREEZE'):adapt_frozen_hai_authority(unified_authority=self.authority(),predecessor_state={'state':'PREDICTIONS_COMPLETE_LABEL_LOCKED'})
 def test_adapter_has_no_prediction_capability(self):
  out=adapt_frozen_hai_authority(unified_authority=self.authority(),predecessor_state={'state':'GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED'})
  self.assertEqual(len(out['records']),146);self.assertFalse(out['prediction_capability'])
