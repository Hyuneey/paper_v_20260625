"""Public-safe prospective semantic freeze and revised decision package generator."""
from pathlib import Path
from hashlib import sha256
import json,subprocess
from paperworks.validation_v2.exp03b_contract_v1 import digest,require
from paperworks.validation_v2.exp03b_custody_v1 import publish,seal,replay
from paperworks.validation_v2.exp03b_binder_v2 import POLICY
from paperworks.validation_v2.exp03b_firewall_v2 import STRUCTURAL_COLUMNS,GDN_COLUMNS
ROOT=Path(__file__).resolve().parents[1];PUB=ROOT/'research_control_center/validation_v2/exp03b';PRIVATE=ROOT/'artifacts/validation_v2/exp03b/private'


def read(name):
    v=json.loads((PUB/name).read_text());replay(v);return v
def md(name,text):
    p=PUB/name;payload=text.strip()+'\n'
    if p.exists():require(p.read_text(encoding='utf-8')==payload,'FROZEN_DOCUMENT_CONFLICT')
    else:p.write_text(payload,encoding='utf-8',newline='\n')


def main():
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    prior=read('EXP03B_FINAL_PREPARATION_FREEZE_V2.json');cohort=read('EXP03B_COHORT_AUTHORITY_V1.json');budget=read('EXP03B_PROVIDER_BUDGET_V2.json');profile=read('EXP03B_PAYLOAD_TOKEN_PROFILE_V2.json');prompt=read('EXP03B_PROMPT_FREEZE_V2.json')
    for name,h in prior['implementation_hashes'].items():require(sha256((ROOT/name).read_bytes()).hexdigest()==h,'V1_IMPLEMENTATION_CHANGED')
    for name,h in prior['private_input_hashes'].items():require(sha256((PRIVATE/name).read_bytes()).hexdigest()==h,'V1_PRIVATE_CHANGED')
    policy_path=ROOT/'research_control_center/validation_v2/core_v2a/authorities/EXP02_SELECTED_POLICY_AUTHORITY_V2A.json'
    policy_raw=policy_path.read_bytes();policy_doc=json.loads(policy_raw)
    require(POLICY in policy_raw.decode(),'FROZEN_EXP02_POLICY_MISMATCH')
    source_paths=list((ROOT/'src/paperworks/validation_v2').glob('exp03b_*_v2.py'))+[ROOT/'scripts'/n for n in ('execute_exp03b_provider_v2.py','evaluate_exp03b_frozen_outputs_v2.py','prepare_exp03b_semantic_v2.py')]
    impl={**prior['implementation_hashes'],**{p.relative_to(ROOT).as_posix():sha256(p.read_bytes()).hexdigest() for p in source_paths}}
    provider_hashes={p.relative_to(PRIVATE).as_posix():sha256(p.read_bytes()).hexdigest() for p in sorted((PRIVATE/'semantic_v2').rglob('*.json'))}
    private_hashes={**provider_hashes,**{n:prior['private_input_hashes'][n] for n in ('train1/numeric_roles.json','train2/numeric_roles.json','train3/reference.json','train4/input_receipt.json')}}
    amendment=seal({'schema':'exp03b_scientific_amendment_v2','task':'EXP03B-PAYLOAD-REDUCE-001','approved_by':'RESEARCH_OWNER','decision_id':'DEC-024-AMENDMENT-2','supersedes':['SCI02_PROVIDER_NUMERIC_OPTION_SELECTION','EXP03B_PREREGISTRATION_V1','EXP03B_PROVIDER_BUDGET_V1'],'prior_artifacts_preserved':True,'SCI01':'UNCHANGED_STRUCTURAL_GATES','SCI02B':'DETERMINISTIC_POST_INDUCTION_NUMERIC_BINDING','SCI03':'UNCHANGED_GUARD_AND_AGGREGATION_AFTER_BINDER','SCI04':'UNCHANGED_SEMANTIC_MAJORITY_AND_STRICT_FAILURES','fixed_execution_policy':POLICY,'fixed_policy_file_sha256':sha256(policy_raw).hexdigest(),'provider_numeric_fields_allowed':False,'provider_execution_authorized':False,'source_commit':commit})
    publish(PUB/'EXP03B_SCIENTIFIC_AMENDMENT_V2.json',amendment)
    prereg=seal({'experiment_id':'EXP-03B','version':'2.0.0','status':'PREPARED_DG03B_REVISED_PENDING','construct':'SEMANTIC_RELATIONAL_RULE_INDUCTION','cohort_hash':cohort['self_hash'],'N':cohort['count'],'R':3,'portfolio_repeat':1,'T0':'ONE_DETERMINISTIC_SEMANTIC_RUN','T1':'ONE_SEMANTIC_PROPOSAL_NO_FEEDBACK','T1B':'THREE_STATELESS_PROPOSALS_HIDDEN_TRAIN2_SELECTION','T2':'MAX_THREE_SEMANTIC_CALLS_EARLY_STOP_ACCEPTED','scientific_amendment_hash':amendment['self_hash'],'provider_budget_hash':budget['self_hash'],'prompt_freeze_hash':prompt['self_hash'],'disposition_spec_hash':sha256((PUB/'EXP03B_DISPOSITION_RULE_V1.md').read_bytes()).hexdigest(),'numeric_provider_selection':False,'train2_admission':'SEMANTIC_ONLY','post_induction_order':['ALL_PROVIDER_OUTPUTS_FROZEN','TRAIN2_ADMISSIONS_FROZEN','TRAIN3_SEMANTIC_EVALUATION_FROZEN','SCI02B_FIXED_NUMERIC_BINDING','FORMAL_V4_CONVERSION','TRAIN4_ONE_WAY_GUARD'],'next_gate':'DG-03B_REVISED','DG04':'DEFERRED_UNTIL_EXP03B','provider_execution_authorized':False,'additional_agentic_rescue':False,'source_commit':commit})
    publish(PUB/'EXP03B_PREREGISTRATION_V2.json',prereg)
    schema={'$schema':'https://json-schema.org/draft/2020-12/schema','title':'EXP03B Provider Train1 Semantic Evidence V2','type':'object','additionalProperties':False,'properties':{'candidate_id':{'type':'string','pattern':'^EXP03B-CAND-[0-9a-f]{20}$'},'source':{'type':'string','pattern':'^P1_[A-Z0-9]+$'},'target':{'type':'string','pattern':'^P1_[A-Z0-9]+$'},'split':{'const':'train1'},'structural_columns':{'const':STRUCTURAL_COLUMNS},'structural_rows':{'type':'array','minItems':20,'maxItems':20,'items':{'type':'array','minItems':8,'maxItems':8,'prefixItems':[{'enum':['step_up','step_down']},{'enum':['increase','decrease']},{'enum':[1,5,10,30,60]},{'type':'integer','minimum':0},{'type':'number','minimum':0,'maximum':1},{'type':'number','minimum':0,'maximum':1},{'type':'number','minimum':0},{'type':'string','pattern':'^EV-[0-9a-f]{24}$'}]}},'stat_association':{'type':'number'},'gdn_columns':{'const':GDN_COLUMNS},'gdn_rows':{'type':'array','minItems':5,'maxItems':5,'items':{'type':'array','minItems':4,'maxItems':4}}}}
    schema['required']=list(schema['properties']);publish(PUB/'EXP03B_EVIDENCE_SCHEMA_V2.json',schema)
    freeze=seal({'schema':'exp03b_semantic_preparation_freeze_v2','status':'PREPARED_DG03B_REVISED_PENDING','implementation_commit':commit,'normal_custody_source_commit':prior['audit_base_commit'],'prior_freeze_hash':prior['self_hash'],'implementation_hashes':impl,'implementation_bundle_hash':digest(impl),'provider_config_hash':budget['config_hash'],'provider_budget_hash':budget['self_hash'],'provider_prompt_hash':prompt['self_hash'],'private_reference_hash':prior['private_reference_hash'],'private_input_hashes':private_hashes,'provider_input_hashes':provider_hashes,'preregistration_hash':prereg['self_hash'],'scientific_amendment_hash':amendment['self_hash'],'frozen_exp02_policy_file_hash':sha256(policy_raw).hexdigest(),'provider_authorized':False})
    publish(PUB/'EXP03B_SEMANTIC_PREPARATION_FREEZE_V2.json',freeze)
    md('SCI02B_DETERMINISTIC_NUMERIC_BINDING_V1.md',f'''# SCI-02B — 의미적 추론 후 결정론적 수치 결속

사용자 승인 EXP03B-PAYLOAD-REDUCE-001. 기존 SCI-02 provider의 37-option 선택은 SUPERSEDED이며 V1 파일·숫자·hash는 보존합니다. provider는 RULE_SET/NO_RULE·source/target direction·horizon·evidence slice만 산출합니다.

모든 arm output의 durable hash closure → train2 admission freeze → train3 semantic evaluation freeze → SCI02B → Formal V4 → train4 guard 순서를 강제합니다. provider phase는 영구 폐쇄하고 binder 이후 새 호출/resume도 거부합니다.

실행 calibrator는 `{POLICY}` 고정입니다. private NUM-033 매핑은 frozen grid의 exact configuration에서 유도되며 provider object에는 존재하지 않습니다. source noise는 file-local median absolute first difference; source direction별 Q90. threshold=max(7×source noise,Q90); tolerance=max(2×source noise,0.05×threshold); target scale은 target noise. 나머지 frozen runtime windows는 유지합니다. train1/train2 각각 도출한 role을 max pooling합니다. 기존 준비에서 생성된 hash-bound split-local numeric cache를 재사용하며 수치나 policy를 재선택하지 않습니다.

provider 출력·admission·train3 의미적 점수는 calibration에 byte/hash 독립입니다. 불완전·nonfinite·잘못된 role/window는 NUMERIC_BINDING_FAIL_CLOSED이며 NO_RULE로 변환하지 않습니다. frozen custody/hash 실패는 전체 정지합니다. 실제 Formal V4 descriptor/numeric validity를 재사용하되 production/held-out 배포 권한은 생성하지 않습니다.

train4는 동일 semantic Rule의 fixed policy와 Common comparator를 평가합니다. SCI03 coverage·최소5 opportunities·lexicographic burden(초/시간,episode/시간,abstain,complexity)·부분 retention·file-local FAIL union을 그대로 유지합니다. 숫자가 같아도 Common의 낮은 complexity가 이기므로 기준을 완화하지 않습니다. train4 이후 provider feedback/retuning은 없습니다.
''')
    md('EXP03B_METRIC_POLICY_V2.md','''# EXP-03B 의미적 metric policy V2

SCI04는 그대로 유지합니다. 실패는 NO_RULE이 아닌 no-vote이며 full N denominator에서 항상 incorrect. 세 번 중 exact semantic set이 2회 이상이면 majority; field-wise 투표 금지. T0는 단일 deterministic 결과만 참조합니다. Repeat1만 prospective portfolio source입니다.

Agentic 지표: strict RULE/NO_RULE F1, admitted directional micro precision/recall/F1, exact semantic set, source/target accuracy, horizon accuracy, feedback/repair distinct pairs, valid-output coverage, failure taxonomy, calls/tokens/latency/cost. numeric option accuracy/stability/selection은 제거합니다.

후속 engineering 지표: numeric binding 성공, 실제 Formal V4 conversion, train4 retained Rules, normal false seconds/hour 및 episodes/hour, coverage, abstain. 의미적 평가를 역으로 수정하지 않습니다.

Disposition은 EXP03B_DISPOSITION_RULE_V1.md와 동일합니다: feedback≥3 pair, exact semantic repair≥2 pair, T2 majority exact≥T1-B+2, strict pair F1 비열등, directional F1 개선, train4 burden 비열등, Formal V4 conversion 비열등을 모두 만족해야 ADVANTAGE. exact repair≥2이나 전체 미달이면 MECHANISM_SUPPORTED_BUT_ADVANTAGE_LIMITED, 그 외 NOT_SUPPORTED. undefined burden/degenerate reference로 우수성을 주장하지 않습니다.
''')
    md('EXP03B_INFORMATION_FIREWALL_V2.md','''# EXP-03B Information Firewall V2

ProviderTrain1EvidencePackV2와 Train2SemanticEvidenceV2는 물리적으로 분리된 immutable 타입입니다. builder는 hidden authority/binder/evaluator를 import하지 않습니다. 기존 split-pure train1 structural 및 predictive authority를 재사용하되 mixed-split object는 만들지 않습니다.

초기 payload: candidate/source/target, 20 structural alternatives, train1 STAT, TRAIN1_ONLY 고정 GDN·purged validation 5-horizon rows. structural evidence의 aggregate 숫자는 허용하지만 raw role values·numeric option tables·NUM alias·최종 EXP02 identity·최종 direction/horizon·META tier/rank·train3/4·test/label·detector/Fusion·경로/credential은 금지합니다.

T2만 train2 semantic issue codes와 1 bounded structural retrieval을 받습니다. 모든 20 대안은 canonical order, best/pass marker 없음. STAT/GDN 추가 retrieval은 이 V2 구현에서 생략하며 기존 structural slice를 유지합니다. T1/T1-B는 feedback을 받지 않습니다. numeric feedback/retrieval schema가 없습니다.

Closed schema·taint 검사·exact request/config replay·candidate binding으로 추가 field/값 identity를 거부합니다. 모든 output 및 train2 admission이 먼저 동결되며 train3 평가도 동결된 뒤에만 SCI02B가 private numeric cache를 읽습니다. 이후 provider phase는 복귀 불가합니다. 이번 준비는 provider/credential/test/attack 접근 0입니다.
''')
    md('DG03B_PROVIDER_DECISION_BRIEF_V2.md',f'''# DG-03B_REVISED — 의미적 Rule induction 별도 승인

USER_DECISION_REQUIRED. 기존 DG-03/DG-03B 승인과 USD65.90·80,373,993 input ceiling은 상속하지 않습니다. 기존 V1은 역사적 보존입니다.

| 승인 항목 | 고정 값 |
|---|---:|
| snapshot | {budget['model']} |
| N / R | {budget['N']} / {budget['R']} |
| T1 / T1-B / T2 최대 calls | {budget['T1_calls']} / {budget['T1B_calls']} / {budget['T2_calls']} |
| 총 최대 calls | {budget['maximum_calls']} |
| 최대 input tokens | {budget['maximum_input_tokens']:,} |
| 최대 output tokens | {budget['maximum_output_tokens']:,} |
| 최대 total tokens | {budget['maximum_total_tokens']:,} |
| 표준 API 비용 상한 | USD {budget['standard_api_cost_ceiling_usd']} |
| initial / repair call input cap | {budget['phase_input_caps']['initial']:,} / {budget['phase_input_caps']['repair']:,} |
| call output cap | {budget['output_tokens_per_call_cap']:,} |

Responses endpoint `https://api.openai.com/v1/responses`; reasoning none, temperature0.7, top_p1, store=false, standard service tier, timeout60초, retry0, concurrency1. moving alias·도구·자동 fallback 금지. T2 ACCEPTED 즉시 종료, 최대3 calls. 완료 schedule 범위는435~609회이며 예상 실사용량 예측이 아닙니다.

A. **로컬 tokenizer 추정**: tiktoken0.12.0/o200k_base로 29개 초기 요청을 정확히 직렬화·계수. min/median/max={profile['minimum_initial_tokens']}/{profile['median_initial_tokens']}/{profile['maximum_initial_tokens']}. T1 {profile['T1_input_estimate']:,}, T1-B {profile['T1B_input_estimate']:,}, 최대형태 T2 {profile['T2_maximal_shape_input_estimate']:,}, 전체 {profile['schedule_maximal_shape_input_estimate']:,} input tokens. repair는 미래 결과 대신 synthetic 최대형태 profile입니다. 모든 가능한 미래 출력의 BPE 최대값이나 API billing과 동일하지 않습니다.

B. **API hard ceiling**: 작은 closed ASCII request의 UTF8 byte/escape bound와512 service-framing reserve, 단계별 cap 및 transport 전 누적 input/output/cost reservation. framing은 문서로 보장된 서버 내부 token 수가 아닌 보수적 가정입니다. 첫 승인된 과학 호출 1회에서 실제 snapshot·usage·schema·privacy·durable receipt를 검증한 뒤 full schedule을 엽니다. 계량 상한 초과/불명·가격/모델 변경은 정지하며 자동 retry하지 않습니다.

외부 전송: fixed pair ID/source/target, train1 structural20 rows·STAT·GDN, schema/criteria. T2 repair만 bounded train2 structural alternatives를 추가합니다. numeric rows740→0, NUM aliases/수치정책 선택/최종 EXP02 identity는 전송하지 않습니다. private raw rows/role values, 최종 정답, train3/4, test/labels/heldout, detector/Fusion, META 선언, 경로·credential은 금지합니다. Aggregate는 비공개 연구 파생정보이므로 이 별도 승인이 필요합니다.

요금 근거: [공식 GPT-5.4 Mini 문서](https://developers.openai.com/api/docs/models/gpt-5.4-mini), 표준 input $0.75/M, output $4.50/M. 예상 최대 산식={budget['maximum_input_tokens']}×0.75/M+{budget['maximum_output_tokens']}×4.50/M, 센트 올림.

Budget hash `{budget['self_hash']}`. Execution freeze `{freeze['self_hash']}`. Implementation commit `{commit}`. Output/ledger/latency/cost는 append-only private custody. 모든 outputs/admissions/train3 freeze 후 고정 SCI02B·FormalV4·train4. 독립 QA 후 DG-04 정지. V2A39-rule·EXP03V1·EXP04/05·held-out 방법은 변경하지 않습니다. 현재 provider/credential/probe=0.
''')
    md('EXP03B_PROVIDER_EXECUTION_INSTRUCTION_V2.md',f'''# EXP-03B V2 승인 후 실행 지침

현재 실행 금지: DG-03B_REVISED USER_DECISION_REQUIRED. 구현 commit `{commit}`. 최종 통합 commit은 `git log -1 --format=%H -- research_control_center/validation_v2/exp03b/EXP03B_SEMANTIC_PREPARATION_FREEZE_V2.json`으로 freeze 추가 commit을 확인하고 branch/origin parity를 검증합니다.
Exact model `{budget['model']}`; calls≤{budget['maximum_calls']}, input≤{budget['maximum_input_tokens']}, output≤{budget['maximum_output_tokens']}, total≤{budget['maximum_total_tokens']}, USD≤{budget['standard_api_cost_ceiling_usd']}.

1. 새 사용자 승인 뒤에만 private approval receipt를 생성합니다. `gate=DG-03B_REVISED`, `status=APPROVED`, `budget_hash={budget['self_hash']}`, `execution_freeze_hash={freeze['self_hash']}` 및 canonical self_hash. 이전 승인파일 재사용 금지. 현재 준비 코드가 승인을 만들지 않습니다.
2. source/public/private hashes·ignored custody·PILOT 보존·clean/origin parity를 점검합니다. PYTHONPATH=src;tests. `python scripts/execute_exp03b_provider_v2.py --approval <private-approved-receipt> --probe-only`. 이 작업에서는 실행하지 않았습니다. 승인·budget·source·phase gate 통과 후 transport 안에서만 credential을 읽습니다.
3. 첫 과학 호출은 추가 probe가 아닌 schedule 첫 호출입니다. response/cost/latency receipt atomic write/fsync/close/reopen/hash replay 및 model/schema/privacy/usage PASS 뒤 같은 명령에서 --probe-only를 제거해 재개합니다. 재개 시 기존 호출을 다시 보내지 않습니다. ledger gap/orphan/unmatched request·hash mismatch는 자동 retry하지 않고 정지합니다. concurrency1, T2 ACCEPTED 즉시 종료, 최대3.
4. ALL_ARM_OUTPUTS_FROZEN 이후 provider phase는 영구 폐쇄합니다. `python scripts/evaluate_exp03b_frozen_outputs_v2.py`가 call/raw/verifier/feedback replay → train2 admission freeze → train3 semantic evaluation freeze → deterministic SCI02B → Formal V4 → train4 one-way guard를 수행합니다. numeric binding은 semantic output을 수정하지 않습니다. T0 단일 결과는 반복표에서 참조만 합니다.
5. 독립 read-only QA로 exact call/output/cost/latency custody, failure denominator, semantic repair, numeric binding, guard 및 immutable 결과를 확인합니다. 공개 안전 보고와 RCC를 동기화한 뒤 DG-04에서 정지합니다. test1/2/held-out/외부공격 접근 및 production Agentic portfolio 생성은 금지합니다.
''')
    md('DEC024_PAYLOAD_REDUCTION_AMENDMENT_V2.md',f'''# DEC-024 Amendment 2 — 사용자 승인 과학 단순화

EXP03B-PAYLOAD-REDUCE-001에서 승인. semantic induction은 유지하고 provider numeric-option 선택만 제거합니다. SCI02_PROVIDER_NUMERIC_SELECTION → SUPERSEDED; SCI02B_DETERMINISTIC_POST_INDUCTION_NUMERIC_BINDING → SELECTED.
V1 preregistration·SCI02·budget·payload는 역사적 보존. 740 option rows/pair와80,373,993 input/USD65.90은 현재 승인 요청이 아닙니다. 새 20 structural rows(+5 GDN horizon rows,단일 STAT)와 DG03B V2 budget을 사용합니다.
이 변경은 과학 결과가 아닌 provider 전 계약 변경입니다. EXP03V1·cohort29·SCI01/04·EXP02selected·V2A39·EXP04/05·GDN·PILOT는 불변. DG-04 DEFERRED_UNTIL_EXP03B. 새 예산 승인 전 provider0.
Amendment hash `{amendment['self_hash']}`.
''')
    md('EXP03B_PERFORMANCE_PREFLIGHT_V2.md',f'''# EXP-03B payload 성능 preflight V2

기존 hash-bound split-pure evidence에서 선택지표 없이 구조·STAT·GDN만 투영했습니다. 정상 raw feature 재읽기·GDN 재학습·provider 실행 없음. train1/train2 별도 cache; T0 once/pair. provider/verifier는20 tuple 조회이며740 numeric rows를 계산/전송하지 않습니다. 후속 binder는 고정 policy만 읽고 old37-grid를 재탐색하지 않습니다.
초기 local token min/median/max={profile['minimum_initial_tokens']}/{profile['median_initial_tokens']}/{profile['maximum_initial_tokens']}; schedule 최대형태 estimate={profile['schedule_maximal_shape_input_estimate']:,}. 실제 API latency/usage는 미측정. 29 payload마다 hash와 token profile 결속. hard cap은 별도 budgetV2입니다.
새 projection은 기존 train1 structural/STAT/GDN 값에 exact equality이며 scientific evidence 변형/반올림/요약 변경 없음. Binder formula·max pooling·FormalV4/guard는 기존 구현 재사용 및 synthetic equality 검사를 수행합니다.
''')
    print(json.dumps({'status':'PREPARED_DG03B_REVISED_PENDING','implementation_commit':commit,'freeze_hash':freeze['self_hash'],'private_hash_count':len(private_hashes),'implementation_hash_count':len(impl)}))


if __name__=='__main__':main()
