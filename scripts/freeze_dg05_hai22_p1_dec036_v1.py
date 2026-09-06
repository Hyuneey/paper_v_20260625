"""Freeze DEC-036 source-rooted HAI22 P1 decisions from the private scenario root."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from paperworks.validation_v2.dg05_hai_official_scenario_v1 import canonical_bytes, self_hashed
from paperworks.validation_v2.dg05_hai22_direct_target_scope_v1 import build_target_process_authority, classify_scenarios

def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument('--scenario', type=Path, required=True); parser.add_argument('--decision', type=Path, required=True); parser.add_argument('--private-output', type=Path, required=True); parser.add_argument('--public-output', type=Path, required=True); args=parser.parse_args()
    scenario=json.loads(args.scenario.read_text(encoding='utf-8')); decision=json.loads(args.decision.read_text(encoding='utf-8'))
    target=build_target_process_authority(scenario_authority=scenario, decision_hash=decision['self_hash']); eligibility=classify_scenarios(scenario_authority=scenario,target_authority=target,decision_hash=decision['self_hash'])
    private=self_hashed({'schema':'hai22_p1_dec036_private_bundle_v1','target_process_authority':target,'eligibility_authority':eligibility})
    args.private_output.parent.mkdir(parents=True,exist_ok=True); args.private_output.write_bytes(canonical_bytes(private)+b'\n')
    counts={status:sum(item['primary_status']==status for item in eligibility['decisions']) for status in ('P1_ELIGIBLE','P1_NOT_ELIGIBLE','UNRESOLVED')}
    public=self_hashed({'schema':'hai22_p1_dec036_public_receipt_v1','status':'PASS' if counts['UNRESOLVED']==0 else 'INCOMPLETE','decision_id':'DEC-036','private_bundle_sha256':private['self_hash'],'target_process_authority_sha256':target['self_hash'],'eligibility_authority_sha256':eligibility['self_hash'],'target_representation_count':len(target['records']),'heuristic_aliases':0,'classification_counts':counts,'heldout_predictions_observed':0,'heldout_metrics_observed':0})
    args.public_output.parent.mkdir(parents=True,exist_ok=True); args.public_output.write_bytes(canonical_bytes(public)+b'\n'); print(json.dumps({'private':private['self_hash'],'public':public['self_hash'],'counts':counts},sort_keys=True))
if __name__=='__main__': main()
