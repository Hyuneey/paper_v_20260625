"""Current Korean RCC record generation; historical scientific artifacts untouched."""
from pathlib import Path
import csv,json
ROOT=Path(__file__).resolve().parents[1];RCC=ROOT/'research_control_center';REG=RCC/'registry';PUB=RCC/'validation_v2/exp03b'


def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def prepend(path,text):
    old=path.read_text(encoding='utf-8');marker='# EXP03B-PAYLOAD-REDUCE-001 — 현재 준비 상태'
    if old.startswith(marker):return
    path.write_text(marker+'\n\n'+text.strip()+'\n\n## 이전 기록 — 역사적 보존·현재 승인값 아님\n\n'+old,encoding='utf-8',newline='\n')
def table(name,callback):
    path=REG/(name+'.csv')
    with path.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);columns=reader.fieldnames;rows=list(reader)
    callback(rows)
    with path.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=columns,lineterminator='\n');w.writeheader();w.writerows(rows)


def main():
    budget=json.loads((PUB/'EXP03B_PROVIDER_BUDGET_V2.json').read_text());freeze=json.loads((PUB/'EXP03B_SEMANTIC_PREPARATION_FREEZE_V2.json').read_text());commit=freeze['implementation_commit']
    state=json.loads((REG/'current_state.yaml').read_text(encoding='utf-8'))
    def current_replace(value):
        if isinstance(value,dict):return {k:current_replace(v) for k,v in value.items()}
        if isinstance(value,list):return [current_replace(v) for v in value]
        if isinstance(value,str):return value.replace('DG-03B —','DG-03B_REVISED —').replace('DG-03B:','DG-03B_REVISED:').replace('DG03B_PROVIDER_DECISION_BRIEF_V1','DG03B_PROVIDER_DECISION_BRIEF_V2').replace('81,621,225',f"{budget['maximum_total_tokens']:,}").replace('USD 65.90','USD '+budget['standard_api_cost_ceiling_usd']).replace('USD65.90','USD'+budget['standard_api_cost_ceiling_usd'])
        return value
    state=current_replace(state)
    status={'status':'PREPARED_DG03B_REVISED_PENDING','classification':'SEMANTIC_RELATIONAL_RULE_INDUCTION','cohort_count':budget['N'],'structural_rows_per_pair':20,'provider_numeric_rows':0,'numeric_provider_visible':False,'provider_calls':0,'model_snapshot':budget['model'],'maximum_calls':budget['maximum_calls'],'maximum_input_tokens':budget['maximum_input_tokens'],'maximum_output_tokens':budget['maximum_output_tokens'],'maximum_total_tokens':budget['maximum_total_tokens'],'cost_ceiling_usd':budget['standard_api_cost_ceiling_usd'],'next_gate':'DG-03B_REVISED','DG04':'DEFERRED_UNTIL_EXP03B','source_commit':commit,'budget_hash':budget['self_hash'],'freeze_hash':freeze['self_hash'],'brief':'research_control_center/validation_v2/exp03b/DG03B_PROVIDER_DECISION_BRIEF_V2.md'}
    state['exp03b_preparation']=status
    state['current_phase_statement']='EXP-03B 의미적 Rule induction V2 준비 완료. Provider의 수치 옵션 선택을 제거하고 SCI02B로 후결속합니다. 기존 결과는 그대로 보존. DG-03B_REVISED 신규 승인 전 provider0, DG-04는 EXP03B 이후입니다.'
    state['exact_next_task']='DG-03B_REVISED — EXP-03B Provider Execution Decision (DG-04 DEFERRED_UNTIL_EXP03B)';state['recommended_next_management_task']=state['exact_next_task']
    state['top_user_todo']=[f"DG-03B_REVISED: 고정 snapshot·{budget['maximum_calls']}회·최대 {budget['maximum_total_tokens']:,} tokens·USD {budget['standard_api_cost_ceiling_usd']} 승인 검토",'DG-04는 EXP-03B 의미적 추론 결과 이후 결정','DG-05 공격 접근 및 DG-06 실제 제출 별도 승인']
    write(REG/'current_state.yaml',state)
    program=json.loads((RCC/'validation_v2/PROGRAM_STATE.json').read_text(encoding='utf-8'))
    program['current_stage']='EXP03B_SEMANTIC_PREPARED_DG03B_REVISED_PENDING';program['program_status']='PREPARED_DG03B_REVISED_PENDING';program['exp03b_preparation']=status;program['experiment_status']['EXP-03B']='PREPARED_DG03B_REVISED_PENDING'
    program['decision_gates']['DG-03B']='SUPERSEDED_BY_DG03B_REVISED';program['decision_gates']['DG-03B_REVISED']='USER_DECISION_REQUIRED';program['decision_gates']['DG-04']='DEFERRED_UNTIL_EXP03B';program['exact_next_task']='DG-03B_REVISED — EXP-03B Provider Execution Decision'
    write(RCC/'validation_v2/PROGRAM_STATE.json',program)
    history=json.loads((REG/'history.yaml').read_text(encoding='utf-8'))
    if not any(x['direction']=='EXP-03B provider numeric option selection' for x in history['superseded_directions']):
        history['superseded_directions'].append({'direction':'EXP-03B provider numeric option selection','period':'2026-09-04','why_explored':'의미적 구조와 NUM option을 함께 추론','why_reduced':'740행/pair 및80M input ceiling은 주 Agentic construct에 불필요','survived':'SCI01/04·cohort29·split-pure evidence·기존 V1 계약과 기록','replacement':'의미적 구조 추론 후 SCI02B fixed numeric binding','status':'SUPERSEDED','current_claim':False})
        history['terminology'].append({'term':'EXP-03B semantic induction / SCI02B','historical':'provider NUM selection 포함','current':'provider는 의미적 Rule Set만 추론; 수치는 hidden confirmation 뒤 deterministic binding','deprecated':'provider가 executable numeric policy를 선택한다'})
    write(REG/'history.yaml',history)
    source={'scientific_source_ref':'codex/exp03b-payload-reduce-001','scientific_source_commit':commit}
    def experiment(rows):
        r=next(r for r in rows if r['experiment_id']=='EXP-03B');r.update(status='PREPARED_DG03B_REVISED_PENDING',current_evidence='의미적 구조20행;numeric provider0;29 pair;SCI02B 후결속;provider0',next_action='DG-03B_REVISED',**source)
    def claim(rows):
        r=next(r for r in rows if r['claim_id']=='CLAIM-EXP03B-PREP');r.update(claim_text='EXP-03B 의미적 induction V2 준비 완료; 수치 결속은 hidden confirmation 이후',allowed_wording='의미적 evidence-to-rule 준비; DG-03B_REVISED 대기',**source)
    def risk(rows):
        r=next(r for r in rows if r['risk_id']=='RISK-EXP03B-FIREWALL');r.update(mitigation='semantic closed schema;numeric provider 금지;후결속 gate;strict denominator;DG-03B_REVISED',**source)
    def artifact(rows):
        r=next(r for r in rows if r['artifact_id']=='ART-EXP03B-PREP');r.update(name='EXP-03B 의미적 추론 V2 및 SCI02B 준비 freeze',source_ref=source['scientific_source_ref'],source_commit=commit,safe_path='research_control_center/validation_v2/exp03b/EXP03B_SEMANTIC_PREPARATION_FREEZE_V2.json')
    def decision(rows):
        r=next(r for r in rows if r['decision_id']=='DEC-024');r.update(current_relevance='AMENDMENT_2_SEMANTIC_INDUCTION_SCI02B;PREPARED_DG03B_REVISED_PENDING',source_ref='research_control_center/validation_v2/exp03b/DEC024_PAYLOAD_REDUCTION_AMENDMENT_V2.md')
    for name,fn in [('experiments',experiment),('claims',claim),('risks',risk),('artifacts',artifact),('decisions',decision)]:table(name,fn)
    # Timeline event remains historical; add amendment through its current notes.
    def timeline(rows):
        r=next(r for r in rows if r['event_id']=='EVENT-034');r['notes']='원 준비 기록 보존. 후속 EXP03B-PAYLOAD-REDUCE-001: SCI02→SCI02B;semantic20행;DG03B_REVISED;기존80M 예산 superseded. EXP03/04/05·V2A·PILOT 불변.'
    table('timeline',timeline)
    text=f'''상태 PREPARED_DG03B_REVISED_PENDING. EXP-03B는 RULE_SET/NO_RULE·source/target direction·horizon만 추론합니다. numeric option은 provider에서 제거했고 모든 출력·train2 admission·train3 평가가 frozen된 뒤 고정 EXP02 policy를 SCI02B로 결속합니다. 기존 SCI01/04와 disposition 기준은 유지합니다.
29 pair, 20 structural rows(+5 GDN horizon rows/STAT), numeric rows740→0. 고정 {budget['model']}; 최대 {budget['maximum_calls']} calls, input {budget['maximum_input_tokens']:,}, output {budget['maximum_output_tokens']:,}, total {budget['maximum_total_tokens']:,}, USD {budget['standard_api_cost_ceiling_usd']}. 기존80,373,993 input/USD65.90은 historical superseded이며 새 승인으로 사용하지 않습니다.
DG-03B_REVISED 별도 승인 전 provider/credential/probe0. DG-04는 EXP03B 이후입니다. EXP03V1·V2A39·EXP04/05·PILOT 불변; test1/2/heldout/외부공격 접근 없음. Private vault는 SINGLE_COPY_LOCAL_ONLY. 최신 지침: validation_v2/exp03b/EXP03B_PROVIDER_EXECUTION_INSTRUCTION_V2.md.'''
    prepend(RCC/'SESSION_HANDOFF.md',text)
    for name in ('06_EXP03_AGENTIC_RESULTS.md','11_PROFESSOR_DECISION_AGENDA.md','13_SLIDE_OUTLINE.md'):prepend(ROOT/'docs/professor_experiment_update_v2'/name,text+'\n\n이 내용은 준비 계약 수정이며 새로운 과학 성능 결과가 아닙니다. 교수님에게 제출하지 않았습니다.')
    print(json.dumps({'status':'CURRENT_RECORDS_SYNCHRONIZED','implementation_commit':commit}))


if __name__=='__main__':main()
