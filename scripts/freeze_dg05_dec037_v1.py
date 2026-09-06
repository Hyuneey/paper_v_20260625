"""Persist the explicitly approved, prospective DEC-037 amendment."""
from __future__ import annotations
import argparse
from pathlib import Path
from paperworks.validation_v2.dg05_hai_official_scenario_v1 import canonical_bytes, self_hashed
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args(); body={'schema':'dg05_scientific_decision_v1','decision_id':'DEC-037','title':'HAI21 Prospective Direct-Target Process Scope Amendment','status':'APPROVED_AND_FROZEN','approved_at':'2026-09-07 Asia/Seoul','dataset_version':'21.03','semantic':'AT_LEAST_ONE_DIRECT_OFFICIAL_TARGET_WITH_OFFICIAL_HAI21_PROCESS_MEMBERSHIP_P1','multi_target_aggregation':'ANY_VERIFIED_P1_DIRECT_TARGET','unknown_handling':'UNRESOLVED_UNLESS_ANY_VERIFIED_P1_DIRECT_TARGET','historical_predecessor':{'authority_id':'FULL_PROCESS_SCOPE_AUTHORITY_V1','authority_sha256':'0e4fb08ca07cf713df2e5021d9e2fe1721ec99a308cf7656ac63894b40ffe619','historical_audit_sha256':'0f97b2ffeba86f88d5a60e1000b4e95cf3e6d55dc2a49092d7a6d6227ccdfaa6','decision_brief_sha256':'19ff5bff630f0e4371579add7f73452a3b6c4ad60ace02d5d9ddd1d32440b862'},'forbidden':['ALL_SEMANTICS','MAJORITY_SEMANTICS','PRIMARY_TARGET_ONLY','PROCESS_LABEL_BASED_ELIGIBILITY','CROSS_VERSION_MAPPING_REUSE','HEURISTIC_ALIAS'],'does_not_change':['scenario_authority','DEC-031','DEC-034','DEC-035','DEC-036','detectors','Rules','thresholds','metric_formulas'],'performance_contact':{'heldout_feature_values_used_for_method_design':0,'heldout_predictions_observed':0,'heldout_metrics_observed':0,'method_comparisons_observed':0,'result_driven_changes':0}}
 a.output.write_bytes(canonical_bytes(self_hashed(body))+b'\n')
if __name__=='__main__':main()
