"""Current-facing DG04 decision update; historical result authorities unchanged."""
from pathlib import Path
import json
import csv
from paperworks.validation_v2.exp03b_custody_v1 import replay
ROOT=Path(__file__).resolve().parents[1]
RCC=ROOT/'research_control_center'
PUB=RCC/'validation_v2/dg04_xver_prep'


def write(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def table(name, key, identity, fields):
    path=RCC/'registry'/(name+'.csv')
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f);cols=reader.fieldnames;rows=list(reader)
    row=next((r for r in rows if r[key]==identity),None)
    if row is None:row=dict.fromkeys(cols,'NONE');row[key]=identity;rows.append(row)
    row.update(fields)
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=cols,lineterminator='\n');writer.writeheader();writer.writerows(rows)


def prepend(path,text):
    marker='# DG04-XVER-PREP-001 — 현재 승인된 방법 고정'
    old=path.read_text(encoding='utf-8') if path.exists() else ''
    if old.startswith(marker):return
    path.write_text(marker+'\n\n'+text+'\n\n## 이전 기록 — 역사적 상태\n\n'+old,encoding='utf-8',newline='\n')


def main():
    lock=json.loads((PUB/'FINAL_METHOD_LOCK_V1.json').read_text());replay(lock)
    portfolios={a:json.loads((PUB/f'{a}_HELDOUT_CANDIDATE_PORTFOLIO_V1.json').read_text()) for a in ('T0','T2')}
    for value in portfolios.values():replay(value)
    summary={'status':'STAGE_A_COMPLETE_STAGE_B_IN_PROGRESS','decision_id':'DEC-025','decision':lock['status'],
        'title':lock['title'],'method_lock_hash':lock['self_hash'],
        'supported_boundary':'T2_VS_MATCHED_MAXIMUM_BUDGET_T1B', 'T0_limitation':lock['required_limitation'],
        'portfolios':{a:{'hash':p['self_hash'],**p['census']} for a,p in portfolios.items()},
        'next_gate':'DG-03C','provider_calls_this_task':0,'attack_access_authorized':False,
        'report':'research_control_center/validation_v2/dg04_xver_prep/FINAL_TITLE_CLAIMS_AND_RQ_V1.md'}
    text='DEC-025 / DG-04: APPROVED_WITH_SCOPED_AGENTIC_CLAIM. 제목: '+lock['title']+'\n\n동결 정상-only EXP-03B에서 T2는 matched-maximum-budget T1-B 대비 의미적 유도를 개선했지만 주요 지표에서 T0보다 우수하지 않았습니다. GDN은 핵심 learned-graph evidence 모듈이며 후보·탐지·수치 권한이 아닙니다. Fusion은 기여가 아닌 사전등록 비교입니다.\n\nT0 단일 출력 및 T2 Repeat 1의 기존 guard-retained Rule만 별도 HELDOUT_CANDIDATE로 고정했습니다. V2A39 reference·EXP03B·EXP02·EXP04/05·PILOT 결과는 보존합니다. Stage B는 HAI22/21 정상-only 준비 중이며 provider는 DG-03C, 공격은 DG-05, 교수 제출은 DG-06 별도 승인입니다. 추가 Agentic rescue 없음.'
    state=json.loads((RCC/'registry/current_state.yaml').read_text(encoding='utf-8'))
    state.update(dg04_method_lock=summary,current_phase_statement=text,exact_next_task='DG04-XVER-PREP-001 Stage B — cross-version 정상-only 준비',
        recommended_next_management_task='DG04-XVER-PREP-001 Stage B — cross-version 정상-only 준비',
        recommended_next_architecture_task='고정 아키텍처의 외부 버전 adapter; 새 모델·rescue 금지',
        top_user_todo=['DG-03C: 외부 버전 T2 provider 예산 고정 후 승인','DG-05: 공격 접근 전 별도 승인','DG-06: 교수 package 실제 제출 전 검토'])
    state['highest_priority_work']=['DG-04 승인 반영 완료; T0/T2/V2A 별도 유지','HAI22/21 정상-only 준비; provider·공격·label 금지','DG-03C exact freeze 전 credential·probe·호출 금지']
    state['top_priorities']=state['highest_priority_work']
    for todo in state.get('user_todo_items',[]):
        if todo['id']=='USER-V2-004':todo.update(task='DG-03C — 외부 T2 provider 결정 준비',why='DG-04는 DEC-025로 승인됨; Stage B 정확한 준비·예산 필요',linked=summary['report'],status='OPEN')
    write(RCC/'registry/current_state.yaml',state)
    program=json.loads((RCC/'validation_v2/PROGRAM_STATE.json').read_text(encoding='utf-8'))
    program.update(current_stage='DG04_XVER_STAGE_B_PREPARATION',program_status='IN_PROGRESS_NORMAL_ONLY',dg04_method_lock=summary,exact_next_task=state['exact_next_task'])
    program['decision_gates']['DG-04']='APPROVED_WITH_SCOPED_AGENTIC_CLAIM'
    program['decision_gates']['DG-03C']='NOT_READY_NO_PROVIDER_AUTHORIZATION'
    write(RCC/'validation_v2/PROGRAM_STATE.json',program)
    table('decisions','decision_id','DEC-025',dict(date='2026-09-04',date_precision='DAY',title='FINAL_METHOD_AND_SCOPED_AGENTIC_CONTRIBUTION_LOCK',status='ACTIVE',context='EXP03B独立QA PASS;T2対T1-B supported;T0 superior on principal semantic metrics',alternatives_considered='사용자 명시적 최종 결정',decision=lock['status'],reason='의미적 유도와 공격 utility를 분리하고 비교 경계를 고정',consequence='T0/T2 별도 held-out 후보;GDN evidence only;fusion comparison only;추가 rescue 없음',current_relevance='DG04_RESOLVED;XVER_NORMAL_PREPARATION;DG03C_REQUIRED',source='USER_APPROVED_VALIDATION_V2_POLICY',source_ref=summary['report'],source_commit='NONE',affected_components='T2_AGENTIC_FEEDBACK;RESULT_INTEGRITY;PROJECT_WIDE',supersedes='NONE',superseded_by='NONE',user_approved='true',confidence='HIGH'))
    table('decisions','decision_id','DEC-024',dict(current_relevance='EXP03B_COMPLETE_QA_PASS;DG04_RESOLVED_BY_DEC025'))
    table('claims','claim_id','CLAIM-EXP03B-PREP',dict(claim_text='EXP03B: verifier feedback improves semantic induction over matched-maximum-budget T1-B',allowed_wording='정상-only 동결 EXP03B에서 T2 대 T1-B 이점;주요 의미 지표 T0 우월성 아님',validation_needed='DG-05 이후 별도 공격 utility·cross-version 평가;LLM 필수성 미입증'))
    for name in ('CURRENT_CONTEXT.md','SESSION_HANDOFF.md','MY_TODO.md','DECISION_INBOX.md'):
        prepend(RCC/name,text)
    prepend(RCC/'history/TERMINOLOGY_GUIDE.md',text)
    for name in ('03_VALIDATION_V2_METHOD.md','10_HELDOUT_NEXT_PLAN.md','11_PROFESSOR_DECISION_AGENDA.md','13_SLIDE_OUTLINE.md'):
        prepend(ROOT/'docs/professor_experiment_update_v2'/name,text)
    print('DG04_STAGE_A_RECORDS_SYNCHRONIZED')


if __name__=='__main__':main()
