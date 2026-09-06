from __future__ import annotations
import unittest
from paperworks.validation_v2.dg05_hai_scenario_adapter_v1 import digest
from paperworks.validation_v2.dg05_production_route_v11 import DG05ProductionRouteV11Error,initialize_prediction_schedule_v11
class V11RouteTests(unittest.TestCase):
 def authorities(self,unresolved=False):
  rows=[]
  for panel,version,count in [('HAI23_TEST2_PRIMARY_HELDOUT_V1','23.05',38),('HAI22_EXTERNAL_REPLICATION_V1','22.04',58),('HAI21_EXTERNAL_REPLICATION_V1','21.03',50)]:rows += [{'panel_id':panel,'dataset_version':version,'physical_file_id':'F','scenario_id':f'{version}:{i}','closed_intervals':[{'start':'x','end':'y'}],'attacked_identities':['x'],'explicit_affected_processes':[]} for i in range(count)]
  s={'schema':'hai_official_source_triangulated_scenario_authority_private_v1','canonical_records':rows};p={'schema':'hai_p1_direct_target_denominator_authority_v2','decisions':[{'eligibility_status':'P1_ELIGIBLE'} for _ in rows]};
  if unresolved:p['decisions'][0]['eligibility_status']='UNRESOLVED'
  return {**s,'self_hash':digest(s)},{**p,'self_hash':digest(p)}
 def test_incomplete_p1_cannot_reach_schedule(self):
  s,p=self.authorities(True)
  with self.assertRaises(DG05ProductionRouteV11Error):initialize_prediction_schedule_v11(unified_scenario=s,unified_p1=p,state={'state':'GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED'})
 def test_route_names_only_frozen_kernel(self):
  s,p=self.authorities();o=initialize_prediction_schedule_v11(unified_scenario=s,unified_p1=p,state={'state':'GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED'});self.assertFalse(o['alternate_scientific_route']);self.assertEqual(o['heldout_prediction_cells'],0)
