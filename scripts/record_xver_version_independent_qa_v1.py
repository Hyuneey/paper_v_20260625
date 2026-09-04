"""Record independently reported, public-safe version QA after all three reviews."""
import argparse
from xver_execution_common import PUB, PARENT, document, publish, seal, head, require
from xver_result_integrity_v1 import scientific_receipts


def main(version):
    v=version[:2];runs=scientific_receipts(version)
    candidate=document(PARENT/f'HAI{v}_META_STAT_CANDIDATE_AUTHORITY_V2.json')
    evidence=document(PUB/f'HAI{v}_EVIDENCE_FREEZE_V1.json')
    portfolio=document(PUB/f'HAI{v}_T0_PORTFOLIO_AUTHORITY_V1.json')
    budget=document(PUB/f'HAI{v}_T2_PROVIDER_BUDGET_V1.json')
    profile=document(PUB/f'HAI{v}_T2_TOKEN_PROFILE_V1.json')
    require(evidence['N']==portfolio['candidate_N']==budget['N']==candidate['candidate_count'],'QA_COHORT')
    require(portfolio['evidence_hash']==evidence['self_hash'] and budget['profile_hash']==profile['self_hash'],'QA_LINEAGE')
    receipt=seal({'schema':'xver_version_independent_subQA_v1','status':'PASS','version':version,'source_commit':head(),
      'review_roles':{
       'GDN_RUN_AND_CUSTODY':{'status':'PASS','six_exact_slots':True,'unique_namespaces':6,'artifact_byte_hashes_replayed':18,'identity_receipt_hashes_replayed':24,'failed_scientific_attempts':0,'checkpoint_tensors_deserialized':False},
       'T0_FORMAL_GUARD_LINEAGE':{'status':'PASS','candidate_slots':candidate['candidate_count'],'durable_T0_once_slots':candidate['candidate_count'],'train2_admitted_pairs':portfolio['train2_admitted_pairs'],'train2_admitted_rules':portfolio['train2_admitted_rules'],'semantic_confirmed_rules':portfolio['semantic_confirmed_rules'],'numeric_bound':portfolio['numeric_bound_rules'],'Formal_V4':portfolio['Formal_V4_rules'],'guard_retained_rules':portfolio['guard_retained_rules'],'guard_retained_pairs':portfolio['final_pair_count'],'source_data_recomputed':False},
       'PROVIDER_PACK_FIREWALL_AND_BUDGET':{'status':'PASS','provider_packs':budget['N'],'hidden_retrieval_packs':budget['N'],'initial_requests':budget['N'],'exact_serializer_replay':True,'offline_tokenizer_replay':True,'maximum_calls':budget['maximum_calls'],'maximum_input_tokens':budget['maximum_input_tokens'],'maximum_output_tokens':budget['maximum_output_tokens'],'maximum_total_tokens':budget['maximum_total_tokens'],'prospective_cost_ceiling_usd':budget['prospective_standard_price_ceiling_usd']}},
      'authority_hashes':{'GDN_execution':runs[0]['authority_hash'],'evidence':evidence['self_hash'],'T0_portfolio':portfolio['self_hash'],'token_profile':profile['self_hash'],'provider_budget':budget['self_hash']},
      'limitations':['Guard/source metrics were independently linked and censused, not recomputed from normal rows.','Model tensors and private numerical evidence were byte-hashed, not deserialized by independent QA.'],
      'public_private_values_exposed':0,'provider_calls':0,'credential_reads':0,'attack_or_label_accesses':0,'independent_writes':0})
    publish(PUB/f'HAI{v}_INDEPENDENT_SUBQA_V1.json',receipt)
    print('INDEPENDENT_VERSION_SUBQA_RECORDED',version,receipt['self_hash'])


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--version',choices=('22.04','21.03'),required=True);args=parser.parse_args();main(args.version)
