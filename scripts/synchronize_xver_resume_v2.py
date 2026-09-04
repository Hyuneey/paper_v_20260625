"""Sole RCC writer for the user-approved Stage B custody amendment."""
from pathlib import Path
import csv,json
from synchronize_dg04_stage_a_v1 import ROOT,RCC,PUB,write,table
from paperworks.validation_v2.exp03b_custody_v1 import replay

SOURCE='7d3178b9664e3cfa8c0a930dd00bb874723016b7'
NEXT='HAI-XVER-NORMAL-PREP-001'
SUMMARY='''DG-04 / DEC-025와 Stage A는 불변입니다. DG-03B_REVISED 승인 후 동결된 EXP-03B에서 T2는 matched-budget T1-B 대비 이점이 있지만 T0보다 우수하지 않았습니다. T0 22 Rules, T2 Repeat 1 21 Rules, V2A39는 별도 authority입니다.

사용자 schema-only allowlist projection 승인으로 정상 custody 차단을 해결했습니다. HAI22 train1~6/HAI21 train1~3 모두 NORMAL_ONLY_CUSTODY_READY. Label 이름은 header metadata로만 관찰하고 값 decode·검증·사용0. META/STAT union은 각29pairs, GDN admission0입니다.

현재 BLOCKED_PENDING_HAI_XVER_NORMAL_PREP: external GDN context/evidence, T0, provider packs 미완료. DG-XVER-PROVIDER exact token/cost 미정, calls0. eTaPR per-file109 PASS; 세 metric binding은 공격 전 결정 필요. 공격·credential0, 제출/merge/push 없음.'''
DETAIL=SUMMARY+'''

HAI22: 24 exact role features(12×12); HAI21: 22 exact(11×11), P1_PP04/P1_TIT03 ABSENT. Alias 추정0.
META20/19와 STAT20/20의 deduplicated union은 모두29이며 no padding/재생성 없음.
HAI21 train3는 frozen p60/half-open A/purge/B 산술만 materialize; block scientific execution0.
GDN은 이번 task scientific runs0. P1_PP04D 등 full context 매핑 완료 후 기존 architecture family와
split-pure event-conditioned evidence를 별도 후속 task로 실행합니다. Provider budget 준비 완료가 아닙니다.
과거 BLOCKED_NORMAL_DATA_CUSTODY 기록은 보존하며 이번 DEC-026이 schema-only 접근을 승인합니다.
Label-bearing normal container byte traversal은 있지만 excluded values deserialization0입니다.
교수 package는 NOT_SUBMITTED, vault SINGLE_COPY_LOCAL_ONLY, DG05/DG06 별도입니다.
'''


def prefix(path):
    marker='# DG04-XVER Stage B 재개 — 정상 custody 완료'
    old=path.read_text(encoding='utf-8') if path.exists() else ''
    if old.startswith(marker):old=old.split('\n\n## 이전 상태 — 역사적 기록\n\n',1)[1]
    path.write_text(marker+'\n\n'+DETAIL+'\n\n## 이전 상태 — 역사적 기록\n\n'+old,encoding='utf-8',newline='\n')


def main():
    status=json.loads((PUB/'STAGE_B_RESUME_STATUS_V2.json').read_text());replay(status)
    state=json.loads((RCC/'registry/current_state.yaml').read_text(encoding='utf-8'))
    xver={**status,'DG03C':'NOT_READY','report':'research_control_center/validation_v2/dg04_xver_prep/STAGE_B_RESUME_STATUS_V2.json'}
    state.update(xver_preparation=xver,current_phase_statement=SUMMARY,exact_next_task=NEXT,
        highest_priority_work=['정상 custody/role mapping/STAT 완료; Stage A 보존','외부 GDN context와 split-pure evidence 후속 준비','Provider 예산·공격 전 metric binding 각각 동결'],
        top_user_todo=['추가 정상-only GDN/evidence 준비는 HAI-XVER-NORMAL-PREP-001','DG-XVER-PROVIDER: exact evidence·예산 후 별도 승인','DG05 metric 선택/공격 접근과 DG06 제출 별도 승인'])
    state['top_priorities']=state['highest_priority_work'];state['recommended_next_management_task']=NEXT
    state['evaluation_expansion']['external_p1_compatibility']='ROLE_MAPPING_COMPLETE_GDN_CONTEXT_PENDING'
    for todo in state.get('user_todo_items',[]):
        if todo['id']=='USER-V2-004':todo.update(task='정상 schema-only projection 승인·custody 복원 완료',why='DEC-026;9개 projection 비간섭 PASS',linked=xver['report'],status='RESOLVED')
    write(RCC/'registry/current_state.yaml',state)
    program=json.loads((RCC/'validation_v2/PROGRAM_STATE.json').read_text(encoding='utf-8'))
    program.update(program_status=status['status'],current_stage='DG04_XVER_NORMAL_CUSTODY_AND_CANDIDATES_COMPLETE',exact_next_task=NEXT,xver_preparation=xver)
    program['decision_gates']['DG-03C']='NOT_READY_PENDING_HAI_XVER_NORMAL_PREP'
    program['decision_gates']['DG-XVER-PROVIDER']='NOT_READY_PENDING_HAI_XVER_NORMAL_PREP'
    program['decision_gates']['DG-05']='USER_DECISION_REQUIRED'
    write(RCC/'validation_v2/PROGRAM_STATE.json',program)
    table('decisions','decision_id','DEC-026',dict(date='2026-09-04',date_precision='DAY',title='NORMAL_DATA_CUSTODY_SCHEMA_ONLY_ALLOWLIST_PROJECTION',
        status='ACTIVE',context='StageA불변;normal containers contain excluded label schema',alternatives_considered='사용자 지정 positive allowlist projection',
        decision='APPROVED',reason='Normal identity와 label value 해석을 분리',consequence='정상9파일 custody PASS;provider/attack 금지;GDN 후속 준비',
        current_relevance='NORMAL_CUSTODY_RESTORED;HAI_XVER_NORMAL_PREP_PENDING',source='USER_APPROVED_VALIDATION_V2_POLICY',
        source_ref='research_control_center/validation_v2/dg04_xver_prep/NORMAL_CUSTODY_AMENDMENT_V2.md',source_commit='NONE',
        affected_components='RESULT_INTEGRITY;PROJECT_WIDE',supersedes='NONE',superseded_by='NONE',user_approved='true',confidence='HIGH'))
    table('timeline','event_id','EVENT-XVER-NORMAL-RESUME-002',dict(date='2026-09-04',date_precision='DAY',event_type='GOVERNANCE_MILESTONE',
        title='Schema-only 승인 후 정상9파일 projection·외부 후보 완료',summary='StageA불변;HAI22/21 후보각29;GDN evidence 후속;provider/attack0',
        source='USER_APPROVED_VALIDATION_V2_POLICY',source_ref=xver['report'],source_commit='NONE',affected_components='PROJECT_WIDE',
        decision_refs='DEC-026',status='ACTIVE_CONTEXT',superseded_by='NONE',notes='No label-value parsing;no merge of blocked preparation'))
    table('artifacts','artifact_id','ART-XVER-RESUME',dict(name='STAGE_B_RESUME_STATUS_V2.json',role='Normal projection mapping and candidate authority bundle',
        source_ref='validation-v2-dg04-xver-prep-001',source_commit=SOURCE,producer='RESULT_INTEGRITY',consumer='RCC',
        public_private='PUBLIC_SAFE',frozen='true',audited='true',current='true',superseded='false',safe_path=xver['report']))
    table('risks','risk_id','RISK-XVER-NORMAL-CUSTODY',dict(description='이전 schema 접근 차단은 해결;후속 GDN context/evidence와 metric 계약 미완료',
        evidence='artifact:ART-XVER-RESUME',mitigation='Label-blind projection 동결;후속 정상 준비 후 provider 예산;공격 전 metric choice',
        status='MITIGATING',scientific_source_ref='validation-v2-dg04-xver-prep-001',scientific_source_commit=SOURCE))
    for path in [RCC/'SESSION_HANDOFF.md',RCC/'history/TERMINOLOGY_GUIDE.md',
         ROOT/'docs/professor_experiment_update_v2/03_VALIDATION_V2_METHOD.md',ROOT/'docs/professor_experiment_update_v2/10_HELDOUT_NEXT_PLAN.md',
         ROOT/'docs/professor_experiment_update_v2/11_PROFESSOR_DECISION_AGENDA.md',ROOT/'docs/professor_experiment_update_v2/13_SLIDE_OUTLINE.md']:
        prefix(path)
    (PUB/'CURRENT_PREPARATION_STATUS_V2.md').write_text('# Stage B 현재 상태\n\n'+DETAIL,encoding='utf-8',newline='\n')
    path=RCC/'validation_v2/evaluation_expansion/IMPLEMENTATION_TASK_INDEX_V2.csv'
    with path.open(encoding='utf-8') as stream:rows=list(csv.DictReader(stream))
    for row in rows:
        if row['task_id']=='HAI-XVER-COMPAT-001':
            row.update(status='ROLE_MAPPING_NORMAL_CUSTODY_STAT_COMPLETE_GDN_CONTEXT_PENDING',prerequisite='DEC026 approved projection',
                       user_gate='NONE_FOR_COMPLETED_NORMAL_CUSTODY')
        if row['task_id']=='HAI-XVER-NORMAL-EVIDENCE-001':
            row.update(task_id=NEXT,status='PREPARED_FOLLOWUP_NOT_EXECUTED',prerequisite='GDN context mapping plus existing normal projection/candidates',
                       user_gate='NONE_UNLESS_NEW_SCIENTIFIC_CHOICE')
    with path.open('w',encoding='utf-8',newline='') as out:
        writer=csv.DictWriter(out,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    print('XVER_RESUME_RECORDS_SYNCHRONIZED_PENDING_NORMAL_PREP')


if __name__=='__main__':main()
