"""Record the exact official-source recovery boundary for DEC-036's six cases."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
def cb(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def d(v):return hashlib.sha256(cb(v)).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);p.add_argument('--public-output',type=Path,required=True);a=p.parse_args();b=json.loads(a.bundle.read_text());t,e=b['target_process_authority'],b['eligibility_authority']; unresolved=[r for r in t['records'] if r['official_process_membership']=='UNRESOLVED']; count=sum(x['primary_status']=='UNRESOLVED' for x in e['decisions'])
 if len(unresolved)!=1 or count!=6:raise ValueError('HAI22_SIX_CASE_PREDECESSOR_MISMATCH')
 out={'schema':'hai22_dec036_six_case_official_source_recovery_receipt_v1','status':'INCOMPLETE','verdict':'HAI22_P1_OFFICIAL_PROCESS_MEMBERSHIP_INCOMPLETE','predecessor_target_process_authority_sha256':t['self_hash'],'predecessor_eligibility_authority_sha256':e['self_hash'],'unresolved_target_representation_count':1,'affected_scenario_count':count,'unresolved_target_private_set_hash':d(sorted(x['raw_official_target_identity_hash'] for x in unresolved)),'official_sources_examined':['hai_dataset_technical_details.pdf:HAI22 Target Controller/Target Point row binding','icsdataset/hai official repository 22.04 summary roots','icsdataset/hai official repository graph assets limited to 23.05 boiler topology','HAI22 official header identity authority'], 'recovery_outcome':'NO_VERSION_BOUND_OFFICIAL_SOURCE_WITH_A_UNIQUE_PROCESS_MEMBERSHIP_FOR_THE_MULTICONTROLLER_RAW_TARGET_REPRESENTATION','forbidden_inference':['target_prefix','controller_visual_similarity','cross_version_graph_reuse','manual_target_splitting_without_official_grammar','majority_vote'],'heldout_predictions_observed':0,'heldout_metrics_observed':0};out['self_hash']=d(out);a.public_output.write_bytes(cb(out)+b'\n');print(json.dumps({'hash':out['self_hash'],'affected_scenarios':count},sort_keys=True))
if __name__=='__main__':main()
