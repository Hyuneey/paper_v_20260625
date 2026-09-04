"""Public-safe result/decision package from closed receipts only, not raw data."""
from collections import Counter
from decimal import Decimal
from xver_execution_common import ROOT, PUB, PARENT, document, publish, seal, require
from xver_result_integrity_v1 import scientific_receipts


def write_report(path,text):
    path.write_text(text,encoding='utf-8',newline='\n')


def main():
    versions={};budgets={};sections=[]
    for version in ('22.04','21.03'):
        v=version[:2];context=document(PUB/f'HAI{v}_GDN_CONTEXT_MAPPING_V1.json')
        candidate=document(PARENT/f'HAI{v}_META_STAT_CANDIDATE_AUTHORITY_V2.json')
        records=scientific_receipts(version)
        require(all(r['status']=='PASS' and r['scope']=='SCIENTIFIC' and r['node_count']==context['context_count'] for r in records),'TWELVE_SCIENTIFIC_RUNS_REQUIRED')
        states=Counter()
        for r in records:states.update(r['auxiliary_states'])
        gdn=seal({'schema':'xver_GDN_evidence_authority_v1','version':version,'execution_hash':document(PUB/'GDN_EXECUTION_AUTHORITY_V2.json')['self_hash'],'context_hash':context['self_hash'],'context_count':context['context_count'],'context_status':context['context_status'],'candidate_hash':candidate['self_hash'],'N':candidate['candidate_count'],'runs':[{'split':r['split'],'seed':r['seed'],'receipt_hash':r['self_hash'],'global_hash':r['global_hash'],'auxiliary_hash':r['auxiliary_hash']} for r in records],'global_role':'RULE_INDUCTION_SUPPORT','global_rows_per_pair':5,'auxiliary_role':'AUXILIARY_CORROBORATION_ONLY','auxiliary_rows_per_pair_seed':10,'auxiliary_seed_states':dict(states),'total_seed_count_per_split':3,'best_seed_selection':False,'global_event_fusion':False,'scientific_GPU_owners':1,'provider_calls':0,'attack_accesses':0})
        publish(PUB/f'HAI{v}_GDN_EVIDENCE_AUTHORITY_V1.json',gdn)
        portfolio=document(PUB/f'HAI{v}_T0_PORTFOLIO_AUTHORITY_V1.json');budget=document(PUB/f'HAI{v}_T2_PROVIDER_BUDGET_V1.json');profile=document(PUB/f'HAI{v}_T2_TOKEN_PROFILE_V1.json')
        require(budget['N']==portfolio['candidate_N']==candidate['candidate_count'] and budget['status']=='USER_DECISION_REQUIRED','VERSION_CLOSURE')
        budgets[version]=budget
        versions[version]={'N':candidate['candidate_count'],'context_count':context['context_count'],'context_status':context['context_status'],'GDN_scientific_runs':len(records),'GDN_evidence_hash':gdn['self_hash'],'auxiliary_states':dict(states),'T0_pair_count':portfolio['final_pair_count'],'T0_retained_rules':portfolio['guard_retained_rules'],'T0_portfolio_hash':portfolio['self_hash'],'T2_evidence_ready':True,'provider_pack_count':budget['N'],'retrieval_pack_count':budget['N'],'budget_hash':budget['self_hash'],'hard_token_ceiling':budget['maximum_total_tokens'],'max_calls':budget['maximum_calls'],'cost_ceiling_usd':budget['prospective_standard_price_ceiling_usd']}
        sections.append(f'''## HAI {version}

- Frozen candidate N: {budget['N']}; canonical GDN context: {context['context_count']} / 37 ({context['context_status']}).
- Six split-pure scientific runs PASS; train1/train2 seeds 11/23/37, no best seed.
- GLOBAL: five horizon rows per pair, provider train1 / retrieval train2 only.
- Auxiliary Event states: {dict(states)}. Analysis-only, not fused or exposed.
- T0: {portfolio['guard_retained_rules']} retained Rules / {portfolio['final_pair_count']} pairs; hash `{portfolio['self_hash']}`.
- T2 provider / retrieval packs: {budget['N']} each, exact byte hashes bound in token profile.
- Calls: {budget['calls_if_all_accept_first']} if all first proposals accepted; maximum {budget['maximum_calls']}. No probabilistic expected-call claim.
- Initial local tokens min/median/max: {profile['minimum_initial_input_tokens']} / {profile['median_initial_input_tokens']} / {profile['maximum_initial_input_tokens']}.
- Initial total: {profile['initial_total_input_tokens']}; maximal-shape repair: {profile['maximum_repair_profile_input_tokens']}; profiled maximal-shape schedule: {profile['maximum_shape_schedule_profile_input_tokens']}.
- Hard input/output/total caps: {budget['maximum_input_tokens']} / {budget['maximum_output_tokens']} / {budget['maximum_total_tokens']}.
- Prospective standard-price ceiling: USD {budget['prospective_standard_price_ceiling_usd']}; NOT actual billing.
- Budget authority hash: `{budget['self_hash']}`.
''')
    combined={'maximum_calls':sum(b['maximum_calls'] for b in budgets.values()),'maximum_input_tokens':sum(b['maximum_input_tokens'] for b in budgets.values()),'maximum_output_tokens':sum(b['maximum_output_tokens'] for b in budgets.values()),'maximum_total_tokens':sum(b['maximum_total_tokens'] for b in budgets.values()),'cost_ceiling_usd':str(sum(Decimal(b['prospective_standard_price_ceiling_usd']) for b in budgets.values()))}
    result=seal({'schema':'xver_normal_execution_result_v1','status':'NORMAL_EXECUTION_COMPLETE_PENDING_INDEPENDENT_FINAL_QA','versions':versions,'combined_provider_ceiling':combined,'scientific_GDN_runs':12,'stage_a_changed':False,'provider_calls':0,'credential_reads':0,'attack_accesses':0,'excluded_values_parsed':False,'global_provider_role':'EXP03B_COMPATIBLE_SPLIT_PURE_GLOBAL','event_role':'AUXILIARY_CORROBORATION_ONLY','DG_XVER_PROVIDER':'USER_DECISION_REQUIRED','DG05':'NOT_APPROVED','professor_package':'NOT_SUBMITTED','storage_policy':'SINGLE_COPY_LOCAL_ONLY'})
    publish(PUB/'NORMAL_EXECUTION_RESULT_V1.json',result)
    write_report(PUB/'DG_XVER_PROVIDER_DECISION_BRIEF_V1.md','''# DG-XVER-PROVIDER — external T2 execution decision

Status: USER_DECISION_REQUIRED. This preparation authorizes no provider call.
Combined approval is possible only for both exact version budgets below.

Model `gpt-5.4-mini-2026-03-17`; Responses API; reasoning none; temperature 0.7;
top_p 1; store false; standard/default tier; timeout 60s; retry0; concurrency1;
no tools, fallback or moving alias. One portfolio-producing T2 execution/version,
max three calls/pair, immediate stop on ACCEPTED or nonrepairable failure.
No external T1/T1-B or three-repeat experiment.

Provider: fixed candidate identity plus train1 structural20/STAT/GLOBAL5 only.
Repair: one bounded train2 structural/STAT/GLOBAL5 slice in canonical order,
issue codes only, no correct-option marker. Auxiliary Event evidence is prohibited.
Never send META rank/tier/manual status, arm identity, T0 output, train3, numeric
policy/values, guard, test/attack/labels, detector/Fusion, private paths or secrets.

Every future call MUST bind version + candidate + approved initial/retrieval pack
byte hash, not candidate ID alone: shared pair IDs occur across versions.
Replay execution/source/prompt/schema/privacy/custody/budget before credential
access. First scheduled scientific call doubles as receipt-first probe; no extra
call. Validate returned snapshot/schema/usage and durable custody before continuing.
No retry or fallback on mismatch/failure; append-only requests/responses/usage/
latency/cost and preserve failures, never convert them to NO_RULE.

Local tiktoken0.12.0/o200k counts are profiles, not server metering. Hard caps use
closed ASCII byte/escaping bounds plus explicit512-token framing reserve; this
reserve is not a proof of service overhead. Fail closed if receipt usage or
pretransport reservation does not fit phase and cumulative approved ceilings.

Price source: [official model documentation](https://developers.openai.com/api/docs/models/gpt-5.4-mini),
checked2026-09-05: inputUSD0.75/outputUSD4.50 per million, no cache discount.
Backup is SINGLE_COPY_LOCAL_ONLY; restore/hash receipts are required.
After future T2 outputs/admissions freeze: hidden confirmation, SCI02B fixed
calibration, Formal V4 and one-way guard; never provider revision after guard.
DG-05 remains NOT_APPROVED. No attack performance or generalization claim.

'''+''.join(sections)+f'\n## Combined ceiling\n\n{combined}\n\nProvider calls in preparation:0. Credential reads:0. Attack access:0.\n')
    write_report(PUB/'EXECUTION_REPORT_V1.md','# Cross-version normal-only execution\n\n'+''.join(sections)+'''
## Interpretation

These are normal-evidence and held-out-candidate portfolios, not attack-validated
or production results. GDN remains noncausal supporting evidence, not candidate,
verifier, numeric or detector authority. Candidate admission remains META+STAT.
No META reviewed input was reconstructed. T0 remains the frozen structural-only
deterministic method; no STAT/GDN enhancement was added to T0.
HAI23 Stage A/EXP results and portfolios remain separate and immutable.
The scoped EXP03B claim is T2 versus T1-B, not T2 superiority over T0.

eTaPR109 official hypothetical/synthetic cases pass; multi-file aggregation,
empty-input interpretation and secondary P1 treatment remain pre-DG05 decisions.
P1 eligibility remains design-only. No pooled primary Recall or IID claim.
''')
    print('NORMAL_RESULT_AND_DG_XVER_BRIEF_WRITTEN_FINAL_QA_PENDING')


if __name__=='__main__':main()
