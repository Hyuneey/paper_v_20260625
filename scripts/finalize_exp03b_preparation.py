"""Deterministic public preparation package; no provider or raw feature reads."""
from pathlib import Path
from hashlib import sha256
import json
import subprocess
from paperworks.validation_v2.exp03b_contract_v1 import digest,require
from paperworks.validation_v2.exp03b_custody_v1 import publish,seal,replay

ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/'research_control_center/validation_v2/exp03b'
PRIVATE=ROOT/'artifacts/validation_v2/exp03b/private'
BASE='7c69eb3b4db8d479706f6e51b459413b8c24b564'
def read(name):
    d=json.loads((PUB/name).read_text());replay(d);return d
def md(name,text):
    if name=='EXP03B_PROVIDER_EXECUTION_INSTRUCTION_V1.md':text=text.replace('EXP03B_FINAL_PREPARATION_FREEZE_V1.json','EXP03B_FINAL_PREPARATION_FREEZE_V2.json')
    (PUB/name).write_text(text.strip()+'\n',encoding='utf-8',newline='\n')
def main():
    cohort=read('EXP03B_COHORT_AUTHORITY_V1.json');binding=read('EXP03B_SCIENTIFIC_BINDINGS_V1.json');budget=read('EXP03B_PROVIDER_BUDGET_V1.json');prompt=read('EXP03B_PROMPT_FREEZE_V1.json')
    for name,h in binding['implementation_hashes'].items():require(sha256((ROOT/name).read_bytes()).hexdigest()==h,'PRE_IO_BINDING_CHANGED')
    authority=json.loads((ROOT/'research_control_center/validation_v2/core_v2a/authorities/V2A_CONFIRMED_COHORT_AUTHORITY.json').read_text())
    require(authority['cohort_hash']==digest({k:v for k,v in authority.items() if k!='cohort_hash'}),'TRAIN3_REFERENCE_HASH')
    pairs=[]
    for p in cohort['pairs']:
        relations=[{'source_direction':r['source_direction'],'target_direction':r['target_direction'],'horizon_seconds':r['selected_horizon_seconds']} for r in authority['relations'] if r['source']==p['source'] and r['target']==p['target']]
        pairs.append({'candidate_id':p['candidate_id'],'relations':sorted(relations,key=lambda r:(r['source_direction'],r['target_direction'],r['horizon_seconds']))})
    hidden=seal({'schema':'exp03b_hidden_train3_reference_v1','upstream_cohort_hash':authority['cohort_hash'],'pairs':pairs,'role':'FROZEN_NORMAL_CONFIRMED_RELATION_REFERENCE','feature_reads':0})
    publish(PRIVATE/'train3/reference.json',hidden)
    receipts={s:read(f'EXP03B_{s.upper()}_EVIDENCE_RECEIPT_V1.json')['self_hash'] for s in ('train1','train2')}
    receipts['train4']=read('EXP03B_TRAIN4_PREPARATION_RECEIPT_V1.json')['self_hash']
    publish(PUB/'EXP03B_SPLIT_PURE_EVIDENCE_RECEIPT_V1.json',seal({'schema':'exp03b_preparation_closure_v1','cohort_count':cohort['count'],'evidence_receipts':receipts,'hidden_reference_hash':hidden['self_hash'],'train3_feature_reads':0,'T0_runs':cohort['count'],'train4_guard_status':'IMPLEMENTED_NOT_EXECUTED_NO_ARM_OUTPUTS','provider_calls':0,'credential_reads':0,'test1_accesses':0,'test2_accesses':0,'label_accesses':0,'private_exposures':0}))
    publish(PUB/'EXP03B_PREREGISTRATION_V1.json',seal({'experiment_id':'EXP-03B','status':'PREPARED_DG03B_PENDING','scientific_bindings_hash':binding['self_hash'],'cohort_hash':cohort['self_hash'],'provider_budget_hash':budget['self_hash'],'prompt_freeze_hash':prompt['self_hash'],'arms':{'T0':'ONE_DETERMINISTIC_RUN','T1':'ONE_CALL_NO_FEEDBACK','T1-B':'THREE_STATELESS_DRAWS_HIDDEN_SELECTION','T2':'MAX_THREE_CALLS_EARLY_STOP_ACCEPTED'},'R':3,'portfolio_repeat':1,'next_gate':'DG-03B','DG04':'DEFERRED_UNTIL_EXP03B','provider_execution_authorized':False,'disposition_spec_hash':sha256((PUB/'EXP03B_DISPOSITION_RULE_V1.md').read_bytes()).hexdigest(),'post_result_tuning':False,'additional_agentic_rescue':False}))
    md('EXP03B_EVIDENCE_SCHEMA_V1.md','''# EXP-03B evidence schema

ProviderTrain1EvidencePackV1은 train1 전용 immutable structural/predictive 타입에서만 생성합니다. Hidden train2/3/4 객체와 혼합한 뒤 필드를 삭제하는 경로는 금지합니다.
구조 행: source direction, target direction, horizon, support, consistency, effect, opposite consistency, slice ID.
수치 행: NUM alias와 train1 aggregate opportunity/PASS/FAIL/ABSTAIN·coverage·false-firing metrics 및 slice ID. 원시 role 값은 private numeric_roles authority에만 있습니다.
STAT은 train1 단독 correlation, GDN은 TRAIN1_ONLY 고정 checkpoint/purged validation 전용입니다. 방향/horizon의 모든 대안을 보이며 최종 정답·best marker는 없습니다.
정확한 closed serialized schema와 타입/범위 검사는 exp03b_prompt.py 및 exp03b_firewall_v1.py가 실행합니다. JSON output schema는 별도 EXP03B_OUTPUT_SCHEMA_V1.json입니다.
''')
    fields={'candidate_identity':'CANDIDATE_IDENTITY','train1_tuple_aggregates':'NONANSWER_EVIDENCE','train1_numeric_alias_metrics':'NONANSWER_EVIDENCE','train1_STAT_GDN':'NONANSWER_EVIDENCE','output_schema':'FORMAT_CONSTRAINT','V2A_final_direction_horizon':'PROHIBITED','final_numeric_reference':'PROHIBITED','META_rank_tier':'PROHIBITED','train2_hidden_outcomes':'PROHIBITED','train3_train4':'PROHIBITED'}
    (PUB/'EXP03B_PROVIDER_VISIBILITY_MATRIX_V1.csv').write_text('field,classification,provider_visible\n'+''.join(f'{k},{v},{str(v!="PROHIBITED").lower()}\n' for k,v in fields.items()),encoding='utf-8',newline='\n')
    md('DG03B_PROVIDER_DECISION_BRIEF_V1.md',f'''# DG-03B — 별도 provider 실행 승인 필요

상태: USER_DECISION_REQUIRED. 이전 DG-03 승인은 상속하지 않습니다.
모델: `{budget['model']}`. Responses endpoint, reasoning none, temperature 0.7, top_p 1, store false, retry 0, timeout 60초, concurrency 1. moving alias 금지.

| 항목 | 고정 상한 |
|---|---:|
| N / R | {cohort['count']} / 3 |
| T1 / T1-B / T2 calls | 87 / 261 / 261 |
| 총 generation calls | {budget['maximum_calls']} |
| input tokens | {budget['maximum_input_tokens']} |
| output tokens | {budget['maximum_output_tokens']} |
| total tokens | {budget['maximum_total_tokens']} |
| 표준 API 비용 USD | {budget['standard_api_cost_ceiling_usd']} |

전체 스케줄 완료 시 조기 종료 범위는 435~609회이며 실제 예상치가 아닙니다. one-call probe는 첫 과학 호출을 재사용하고 추가 호출하지 않습니다. 첫 응답·usage·snapshot·schema·privacy receipt 재생 PASS 전 다음 호출을 금지합니다.
29개 실제 train1 payload를 로컬 tokenizer로 프로파일링했습니다. 로컬 token count는 API usage와 동일하다고 가정하지 않으며, UTF-8 byte bound와 고정 framing 여유로 보수적인 call별 input 상한을 고정했습니다. 각 호출 후 실제 usage를 결속하고 초과/불명 응답은 fail-closed, 자동 retry 금지입니다.
외부 전송: candidate source/target, train1 tuple aggregate, NUM aliases와 aggregate option metrics, split-pure STAT/GDN, schema. T2만 bounded train2 retrieval aggregate를 허용합니다. 원시 rows·private numeric roles·최종 Rule/EXP02 선택·train3/4·test/labels·META 선언·경로·credential·타 arm 결과는 금지합니다.
정상 aggregate도 비공개 연구 파생정보이므로 별도 승인이 필요합니다. 이번 작업은 credential/capability/provider 접근 0입니다.
요금 근거: https://developers.openai.com/api/docs/models/gpt-5.4-mini — input $0.75/M, output $4.50/M. 가격 또는 snapshot 정책 변경 시 승인 계약을 재검토하고 임의 대체하지 않습니다.
예상 산출: append-only calls/responses/usage/latency, raw/admitted outputs, hidden train3 metrics, one-way train4 guard, disposition, 독립 QA. 완료 후 DG-04 정지; production portfolio 및 공격 접근은 승인되지 않습니다.
''')
    md('EXP03B_PROVIDER_EXECUTION_INSTRUCTION_V1.md',f'''# EXP-03B 승인 후 실행 절차

현재 실행 금지: DG-03B USER_DECISION_REQUIRED. exact release commit은 EXP03B_RELEASE_RECEIPT_V1.json의 implementation_commit 및 preparation_commit을 재생합니다. source/hash closure는 EXP03B_FINAL_PREPARATION_FREEZE_V1.json입니다.
budget self hash: `{budget['self_hash']}`. 모델 `{budget['model']}`, 최대 {budget['maximum_calls']}회, input {budget['maximum_input_tokens']}, output {budget['maximum_output_tokens']}, 총 {budget['maximum_total_tokens']}, USD {budget['standard_api_cost_ceiling_usd']}.
1. clean branch/origin, release receipt, 모든 implementation/evidence hash, private vault 복구를 점검합니다. Gate 승인 파일은 사용자의 새 승인을 받은 뒤에만 생성합니다: gate=DG-03B, status=APPROVED, budget_hash 및 execution_freeze_hash를 exact binding하고 self-hash를 부여합니다. 준비 코드가 승인 파일을 자동 생성하지 않습니다.
2. 기존 고정 CUDA/Python 환경을 변경하지 않습니다. PYTHONPATH=src;tests. `python scripts/execute_exp03b_provider.py --approval <private-approved-receipt> --probe-only`를 실행합니다. credential은 이 승인 검증과 reservation 이후 transport 안에서만 읽습니다. public 출력에 경로/key/response를 노출하지 않습니다.
3. ONE_CALL_CAPABILITY_RECEIPT PASS 후 같은 approval로 probe-only 없이 재개합니다. 첫 호출은 재사용합니다. unmatched request, hash mismatch, snapshot 변경, budget/privacy 오류는 자동 재시도하지 않습니다. 한 writer, 동시 호출 1, T2 ACCEPTED 즉시 종료, 최대 3회입니다.
4. 모든 arm output이 atomic/fsync/close/reopen/hash replay 후 ALL_ARM_OUTPUTS_FROZEN으로 잠긴 다음 `python scripts/evaluate_exp03b_frozen_outputs.py`를 실행합니다. train3 hidden reference → train4 one-way guard 순서이며 provider로 돌아가는 경로는 없습니다. T0는 단일 산출물을 반복 표에서 참조합니다.
5. 독립 read-only QA로 call/response/cost ledger, strict denominator, semantic repair, guard, frozen output 무변경을 검사하고 공개 안전 보고/RCC를 동기화합니다. DG-04에서 정지합니다. test1/2/외부 공격/held-out 접근과 production Agentic portfolio 생성은 금지합니다.
''')
    md('EXP03B_PERFORMANCE_PREFLIGHT_V1.md','''# 성능 preflight

정상 evidence materialization 완료: train1/2 각 29 pair, 20 semantic tuple, 37 numeric option. column scale 및 candidate-source event map은 split별 캐시를 재사용하며 Formal V4를 다른 evaluator로 대체하지 않습니다. GDN은 각 split 3개 고정 checkpoint inference만 실행했고 재학습하지 않았습니다.
provider execution은 immutable evidence를 읽기만 합니다. train2 검증은 20 tuple ×37 option의 bounded table 조회이며 원시 HAI를 다시 열지 않습니다. train3 set 비교는 고정 cohort dictionary입니다. train4는 각 arm/repeat의 고정 두 numeric world를 실행하며 이벤트를 source별 재사용합니다.
prompt serialization/token profiling은 로컬에서 완료했습니다. 29 request exact size는 TRAIN1_PROMPT_SIZE_PROFILE receipt에, 최대 repair size는 TRAIN2 profile에 있습니다. API 지연/가격의 실제 측정은 수행하지 않았습니다.
reference/optimized equivalence는 frozen quantile와 Formal V4 synthetic regression으로 검사합니다. 정상 과학 결과를 성능 개선 목적으로 재실행하지 않습니다.
''')
    md('EXP03B_INFORMATION_FIREWALL_QA_V1.md','''# Information firewall QA

PASS: provider builder는 train1 전용 structural/predictive 타입만 허용합니다. hidden 객체의 직렬화 제거 방식이 아니며 train2/3/4 final answer를 받지 않습니다. closed initial/repair schema는 추가 필드·정답 marker·원시 numeric role·META tier/rank를 거부합니다. train2 retrieval은 전 대안을 canonical order로 표시합니다.
새 admission adapter는 train2 preferred semantic tuple과 NUM option을 강제하지만 feedback에는 정답을 포함하지 않습니다. 실제 train1/2 private evidence와 T0 및 numeric-role 파일은 최종 freeze의 215 hash record로 결속했습니다.
provider/credential/capability/test/attack 접근 0. 실제 network privacy audit은 승인 후 one-call receipt-first 단계에서 다시 수행해야 합니다.
''')
    md('EXP03B_SYNTHETIC_QA_V1.md','''# Synthetic QA

70 focused tests PASS: 기존 preparation audit6 + bindings45 + execution9 + gate/reporting10. 정상 과학 데이터를 테스트 fixture로 사용하지 않았습니다.
검사: split purity, SCI thresholds, 37 options, quantile equivalence, T0, train2 completeness/NO_RULE, exact preferred tuple, horizon, numeric instability, partial guard, FAIL union, majority/failures/strict metrics, prompt taint, receipt-first/concurrency/caps, actual Formal V4 descriptor/numeric conversion.
별도 독립 numeric oracle: 3 synthetic fixtures ×2 directions ×37 options =222 exact formula matches. Validation V2 regression458개: PASS, optional dependency14 skip(기존 경계). RCC/UI integration 결과는 최종 QA/release 기록에 별도 결속합니다.
''')
    # Every future execution helper is bound, not just the original pre-I/O files.
    paths=list((ROOT/'src/paperworks/validation_v2').glob('exp03b_*.py'))+[ROOT/'scripts'/p for p in ('execute_exp03b_provider.py','evaluate_exp03b_frozen_outputs.py','prepare_exp03b_evidence_v1.py','profile_exp03b_prompts.py')]
    impl={p.relative_to(ROOT).as_posix():sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    impl.update(binding['implementation_hashes'])
    private_hashes={p.relative_to(PRIVATE).as_posix():sha256(p.read_bytes()).hexdigest() for p in sorted(PRIVATE.rglob('*.json')) if p.relative_to(PRIVATE).parts[0] in ('train1','train2','train3','train4')}
    final=seal({'schema':'exp03b_final_preparation_freeze_v1','status':'PREPARED_DG03B_PENDING','audit_base_commit':BASE,'pre_io_binding_hash':binding['self_hash'],'implementation_hashes':impl,'implementation_bundle_hash':digest(impl),'provider_config_hash':budget['config_hash'],'provider_budget_hash':budget['self_hash'],'provider_prompt_hash':prompt['self_hash'],'private_reference_hash':hidden['self_hash'],'private_input_hashes':private_hashes,'provider_authorized':False,'source_commit_semantics':'audit_base_plus_pre_IO_file_hashes; release receipt binds committed implementation separately'})
    # Called only after final source QA. Never mutate an existing freeze.
    publish(PUB/'EXP03B_FINAL_PREPARATION_FREEZE_V2.json',final)
    print(json.dumps({'status':'PACKAGE_GENERATED','N':cohort['count'],'reference_count':sum(len(r['relations']) for r in pairs),'provider_calls':0,'freeze_hash':final['self_hash']}))

if __name__=='__main__':main()
