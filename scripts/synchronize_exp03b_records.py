"""Generate Korean current records from frozen EXP-03B preparation authorities."""
from pathlib import Path
import csv,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
RCC=ROOT/'research_control_center';REG=RCC/'registry';PUB=RCC/'validation_v2/exp03b'
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def append_csv(name,row):
    if name=='artifacts' and row.get('artifact_id')=='ART-EXP03B-PREP':row['safe_path']='research_control_center/validation_v2/exp03b/EXP03B_FINAL_PREPARATION_FREEZE_V2.json'
    path=REG/(name+'.csv')
    with path.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
    key=fields[0]
    if any(r[key]==row[key] for r in rows):raise ValueError('DUPLICATE_REGISTRY_ID')
    with path.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows+[row])
def prepend(path,text):
    old=path.read_text(encoding='utf-8');path.write_text(text.strip()+'\n\n## 이전 기록 — 역사적 보존\n\n'+old,encoding='utf-8',newline='\n')
def main():
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    state=json.loads((REG/'current_state.yaml').read_text(encoding='utf-8'))
    budget=json.loads((PUB/'EXP03B_PROVIDER_BUDGET_V1.json').read_text())
    status={'status':'PREPARED_DG03B_PENDING','classification':'AGENTIC_EVIDENCE_TO_RULE_INDUCTION','cohort_count':29,'options':37,'provider_calls':0,'model_snapshot':budget['model'],'maximum_calls':budget['maximum_calls'],'maximum_total_tokens':budget['maximum_total_tokens'],'cost_ceiling_usd':budget['standard_api_cost_ceiling_usd'],'next_gate':'DG-03B','DG04':'DEFERRED_UNTIL_EXP03B','source_commit':commit}
    state['exp03b_preparation']=status
    state['exp03_v1_construct_classification']='CONSTRAINED_RULE_MATERIALIZATION_BENCHMARK'
    state['current_phase_statement']='EXP-03B SCI-01~04 binding과 정상 전용 evidence 준비 완료. Provider 호출 0회이며 DG-03B 별도 승인 대기. EXP-03 V1은 constrained Rule materialization 결과로 보존하고 DG-04는 EXP-03B 이후로 연기합니다.'
    state['exact_next_task']='DG-03B — EXP-03B Provider Execution Decision (DG-04 DEFERRED_UNTIL_EXP03B)'
    state['recommended_next_management_task']=state['exact_next_task'];state['recommended_next_architecture_task']='EXP-03B 승인 후 실행·독립 QA; 이후 DG-04'
    state['top_user_todo']=['DG-03B: 고정 snapshot·609회·최대 81,621,225 tokens·USD 65.90 예산과 aggregate 전송 검토','DG-04는 EXP-03B 결과 이후 결정','DG-05 공격 접근 및 DG-06 실제 제출은 별도 승인']
    write(REG/'current_state.yaml',state)
    history=json.loads((REG/'history.yaml').read_text(encoding='utf-8'))
    history['superseded_directions'].append({'direction':'EXP-03 V1을 evidence induction으로 해석','period':'2026-09-04','why_explored':'T0/T1/T1-B/T2 구성 비교','why_reduced':'정답 방향·horizon·numeric reference가 입력에 포함','survived':'constrained Rule materialization 결과·feedback0 보존','replacement':'EXP-03B 정상 evidence-to-rule induction','status':'SUPERSEDED','current_claim':False})
    history['terminology'].append({'term':'EXP-03 / EXP-03B','historical':'reference-bound materialization을 Agentic 구성으로 해석','current':'V1 constrained materialization;EXP-03B evidence induction 준비','deprecated':'V1으로 direction/horizon induction 또는 Agentic 우월성을 주장'})
    write(REG/'history.yaml',history)
    program=json.loads((RCC/'validation_v2/PROGRAM_STATE.json').read_text(encoding='utf-8'))
    program['current_stage']='EXP03B_PREPARED_DG03B_PENDING';program['program_status']='PREPARED_DG03B_PENDING';program['exp03b_preparation']=status
    program['decision_gates']['DG-04']='DEFERRED_UNTIL_EXP03B';program['decision_gates']['DG-03B']='USER_DECISION_REQUIRED'
    program['experiments']['EXP-03B']='PREPARED_DG03B_PENDING'
    write(RCC/'validation_v2/PROGRAM_STATE.json',program)
    source={'scientific_source_ref':'validation-v2-exp03b-prep-001','scientific_source_commit':commit}
    append_csv('experiments',{'experiment_id':'EXP-03B','name':'Agentic evidence-to-rule induction','research_question':'train1 evidence에서 규칙 구조를 추론하고 bounded feedback으로 개선하는가','comparison':'T0;T1;T1-B;T2','dataset_scope':'HAI23.05 정상 train1/2/3/4; 공격 금지','status':'PREPARED_DG03B_PENDING','current_evidence':'SCI-01~04 승인;29 pair split-pure evidence;synthetic QA PASS;provider0','result_scope':'준비 결과이며 Agentic 성능 결과 아님','primary_metrics':'strict full-cohort F1;semantic exact set;directional F1;train4 burden','limitations':'single-copy private custody;새 provider 승인 필요','next_action':'DG-03B','claim_impact':'DG-04 연기;Agentic 미검증',**source,'linked_component_ids':'T2_AGENTIC_FEEDBACK;RESULT_INTEGRITY','artifact_refs':'ART-EXP03B-PREP'})
    append_csv('claims',{'claim_id':'CLAIM-EXP03B-PREP','claim_text':'EXP-03B 분할 순수 추론 실험 준비 완료; 실험 결과는 아직 없음','claim_type':'IMPLEMENTATION','status':'SUPPORTED_IMPLEMENTATION','supporting_evidence':'artifact:ART-EXP03B-PREP','contradicting_evidence':'EXP-03 V1 feedback0은 induction 결과가 아님','allowed_wording':'정상 evidence-to-rule 실험 준비;DG-03B 대기','forbidden_wording':'Agentic 우월성 검증 완료','validation_needed':'별도 provider 승인과 실행·독립 QA',**source,'linked_experiment_ids':'EXP-03B'})
    append_csv('risks',{'risk_id':'RISK-EXP03B-FIREWALL','category':'CONSTRUCT_VALIDITY','description':'최종 답/hidden split 누출 및 실패를 NO_RULE로 오인할 위험','severity':'HIGH','likelihood':'MEDIUM','affected_component':'T2_AGENTIC_FEEDBACK','evidence':'artifact:ART-EXP03B-PREP','mitigation':'별도 타입·closed schema·taint 검사·strict denominator·DG-03B','owner':'RESEARCH_OWNER','status':'MITIGATING',**source})
    append_csv('artifacts',{'artifact_id':'ART-EXP03B-PREP','name':'EXP-03B 과학 binding·준비 freeze','role':'Provider 승인 전 정상-only preparation','source_ref':'validation-v2-exp03b-prep-001','source_commit':commit,'producer':'T2_AGENTIC_FEEDBACK','consumer':'RESULT_INTEGRITY','public_private':'PUBLIC_SAFE','frozen':'true','audited':'true','current':'true','superseded':'false','safe_path':'research_control_center/validation_v2/exp03b/EXP03B_FINAL_PREPARATION_FREEZE_V1.json'})
    append_csv('decisions',{'decision_id':'DEC-024','date':'2026-09-04','date_precision':'DAY','title':'DEFER_DG04_AND_RUN_EXP03B_CONSTRUCT_VALIDITY_CORRECTION','status':'ACTIVE','context':'V1 입력에 이미 방향·horizon·numeric reference가 있어 constrained materialization을 측정','alternatives_considered':'V1 보존;한 번의 bounded EXP03B correction','decision':'SCI-01~04 승인;EXP03B preparation;DG-04 연기;DG-03B 별도 승인','reason':'정답 제공과 evidence induction의 construct validity 구분','consequence':'추가 Agentic rescue 없음;held-out 계획·V2A39-rule 변경 없음','current_relevance':'PREPARED_DG03B_PENDING','source':'USER_APPROVED_VALIDATION_V2_POLICY','source_ref':'research_control_center/validation_v2/exp03b/SCI01_STRUCTURAL_GATE_V1.md','source_commit':'NONE','affected_components':'T2_AGENTIC_FEEDBACK;RESULT_INTEGRITY','supersedes':'NONE','superseded_by':'NONE','user_approved':'true','confidence':'HIGH'})
    append_csv('timeline',{'event_id':'EVENT-034','date':'2026-09-04','date_precision':'DAY','event_type':'GOVERNANCE_MILESTONE','title':'EXP-03B 과학 binding과 정상-only 준비 완료','summary':'SCI01~04;29 pair;37 options;split-pure GDN;provider0;DG-03B 대기','source':'USER_APPROVED_VALIDATION_V2_POLICY','source_ref':'research_control_center/validation_v2/exp03b/EXP03B_PREREGISTRATION_V1.json','source_commit':'NONE','affected_components':'T2_AGENTIC_FEEDBACK;RESULT_INTEGRITY','decision_refs':'DEC-024','status':'ACTIVE_CONTEXT','superseded_by':'NONE','notes':'EXP03 V1·EXP04/05·V2A·PILOT 보존'})
    prepend(RCC/'SESSION_HANDOFF.md',f'''# 현재 세션 인계 — EXP03B-BIND-001

SCI-01~04 승인 사항을 구현하고 train1 provider/T0 및 train2 hidden evidence 29 pair를 준비했습니다. train3는 frozen reference만 재생했으며 train4는 guard 입력 identity만 확인했습니다. 실제 provider/guard 결과는 없습니다.
상태 PREPARED_DG03B_PENDING. 다음은 DG-03B 신규 승인입니다. model {budget['model']}, 609 calls, input {budget['maximum_input_tokens']}, output {budget['maximum_output_tokens']}, 총 {budget['maximum_total_tokens']}, USD {budget['standard_api_cost_ceiling_usd']}.
기존 audit7c의 SCI 미정 blocker는 사용자 승인으로 해소됐습니다. EXP03 V1은 CONSTRAINED_RULE_MATERIALIZATION_BENCHMARK로 보존. DG-04는 EXP03B 이후로 연기. test1/2/외부공격/provider 접근 금지 유지.
private vault는 SINGLE_COPY_LOCAL_ONLY이며 독립 backup을 주장하지 않습니다. 지침: validation_v2/exp03b/EXP03B_PROVIDER_EXECUTION_INSTRUCTION_V1.md.
''')
    prepend(PUB/'DEC024_CORRECTION_RECORD_V1.md','# DEC-024 현재 disposition\n\nSCI-01~04는 EXP03B-BIND-001 사용자 지시로 승인됐습니다. 준비 완료: PREPARED_DG03B_PENDING. 중앙 Registry 승격. DG-04 DEFERRED_UNTIL_EXP03B. 아래 미정 binding 감사는 역사적 기록입니다.')
    for name in ('06_EXP03_AGENTIC_RESULTS.md','11_PROFESSOR_DECISION_AGENDA.md','13_SLIDE_OUTLINE.md'):
        prepend(ROOT/'docs/professor_experiment_update_v2'/name,'''# EXP-03B construct-validity 보정 — 준비 완료

EXP-03 V1은 고정 방향·horizon·numeric reference를 Formal V4 envelope로 만드는 CONSTRAINED_RULE_MATERIALIZATION_BENCHMARK입니다. feedback 0 결과와 모든 수치는 그대로 보존합니다. evidence-to-rule induction 또는 Agentic 우월성을 검증한 결과가 아닙니다.
EXP-03B는 train1 evidence에서 RULE_SET/NO_RULE·방향·horizon·NUM option을 추론하고 train2 hidden verifier의 제한된 feedback을 비교합니다. 29 pair, 37 options, T0/T1/T1-B/T2, R3 (T0는 단일 실행), Repeat1 portfolio 정책. train3 hidden reference 및 train4 one-way guard로 평가합니다.
SCI-01~04 binding과 정상 evidence 준비 완료, provider 호출 0. DG-03B 신규 예산 승인 필요: 고정 gpt-5.4-mini-2026-03-17, 최대609회, 최대USD65.90. DG-04는 EXP03B 결과 이후로 연기합니다. EXP04/05·V2A39-rule·held-out 방법은 변경하지 않습니다. test/공격 접근 및 제출 없음.
''')
    # Allow only the exact new committed implementation identity.
    validator=RCC/'scripts/validate_registry.py';text=validator.read_text(encoding='utf-8');text=text.replace('CURRENT_V2_SCIENTIFIC_SOURCES = {','CURRENT_V2_SCIENTIFIC_SOURCES = {\n    "validation-v2-exp03b-prep-001": {"'+commit+'"},',1);validator.write_text(text,encoding='utf-8',newline='\n')
    print(json.dumps({'status':'SYNCHRONIZED','implementation_commit':commit}))
if __name__=='__main__':main()
