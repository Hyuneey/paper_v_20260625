"""Synchronize current-facing records after normal result and custody closure."""
import csv
import json
from synchronize_dg04_stage_a_v1 import RCC, write, table
from xver_execution_common import ROOT, PUB, document, head, require, seal


def main():
    result=document(PUB/'NORMAL_EXECUTION_RESULT_V1.json')
    custody=document(PUB/'PUBLIC_PRIVATE_EXECUTION_INDEX_V2.json')
    require(result['scientific_GDN_runs']==12 and custody['scientific_runs']==12,'EXECUTION_CLOSURE_REQUIRED')
    qa_path=PUB/'INDEPENDENT_EXECUTION_QA_V1.json'
    qa=document(qa_path) if qa_path.is_file() else None
    if qa:require(qa['status']=='PASS' and qa['result_authority_hash']==result['self_hash'] and qa['private_index_hash']==custody['self_hash'],'INDEPENDENT_QA_RESULT_BINDING')
    source=head();status=seal({**{k:v for k,v in result.items() if k!='self_hash'},'status':'COMPLETE_QA_PASS_DG_XVER_PROVIDER_PENDING' if qa else result['status'],'result_authority_hash':result['self_hash'],'independent_qa_hash':qa['self_hash'] if qa else None,'report':'research_control_center/validation_v2/xver_normal/EXECUTION_REPORT_V1.md','private_index_hash':custody['self_hash']})
    versions=result['versions'];n22=versions['22.04'];n21=versions['21.03'];budget=result['combined_provider_ceiling']
    summary=f'''HAI-XVER-NORMAL-PREP-001: 정상-only 실행 완료, 독립 최종 QA {'PASS' if qa else 'PENDING'}. DG-XVER-PROVIDER에서 정지합니다.
HAI22/HAI21 GDN은 각각6회, 총12회입니다. GLOBAL5는 train1 provider / train2 retrieval, EVENT10은 보조 분석 전용이며 융합·후보·verifier·T0·숫자·guard 사용을 금지합니다.
HAI22 T0: {n22['T0_retained_rules']} Rules/{n22['T0_pair_count']} pairs. HAI21 T0: {n21['T0_retained_rules']} Rules/{n21['T0_pair_count']} pairs. 모두 HELDOUT_CANDIDATE, 공격 검증·production 결과가 아닙니다.
T2 provider/retrieval packs와 정확 예산은 버전별 고정됐습니다. 합계 최대 {budget['maximum_calls']} calls, {budget['maximum_total_tokens']} tokens, 표준 공개가격 상한 USD {budget['cost_ceiling_usd']}이며 실제 지출이 아닙니다.
DG-XVER-PROVIDER는 USER_DECISION_REQUIRED; provider/credential/공격 접근0. DG05 NOT_APPROVED; 교수 package NOT_SUBMITTED; DG06 필수.
DEC025 제목·claim·HAI23 V2A/T0/T2·EXP03B·EXP02·EXP04/05·PILOT 결과 불변. T2>T1-B는 정상 의미 유도에 한정하며 T0보다 우수하지 않습니다.
후보 권한 META+STAT, GDN은 비인과적 learned-graph evidence, SCI02B 고정 숫자 결합, FormalV4 실행권한, guard 단방향. 37정책 재선택·META 재구성·best seed 없음.
eTaPR109 합성/가상 동등성 PASS. 다중파일/empty/secondary P1 해석은 DG05 전 결정 항목으로 유지하며 실제 eligibility는 생성하지 않았습니다. 백업 SINGLE_COPY_LOCAL_ONLY.'''
    state=json.loads((RCC/'registry/current_state.yaml').read_text(encoding='utf-8'))
    state.update(xver_normal_execution=status,current_phase_statement=summary,exact_next_task='DG-XVER-PROVIDER',recommended_next_management_task='DG-XVER-PROVIDER',last_completed_task='HAI-XVER-NORMAL-PREP-001 — '+('COMPLETE_QA_PASS' if qa else 'NORMAL_EXECUTION_COMPLETE_FINAL_QA_PENDING'),highest_priority_work=['DG-XVER-PROVIDER 버전별 정확 예산 승인 검토','별도 승인 전 provider 호출 금지','DG05 공격 접근 및 DG06 교수 제출 별도'],top_user_todo=['DG-XVER-PROVIDER: 버전별 정확 예산 검토','DG05: 최종 prediction/label custody와 미결 metric 결정','DG06: 교수 package 실제 제출 승인'])
    state['top_priorities']=state['highest_priority_work'];write(RCC/'registry/current_state.yaml',state)
    program=json.loads((RCC/'validation_v2/PROGRAM_STATE.json').read_text(encoding='utf-8'))
    program.update(program_status='XVER_NORMAL_EXECUTION_COMPLETE_DG_XVER_PROVIDER_PENDING',current_stage='CROSS_VERSION_NORMAL_ONLY_EXECUTION_COMPLETE',xver_normal_execution=status,exact_next_task='DG-XVER-PROVIDER')
    for gate in ('DG-XVER-PROVIDER','DG-03C'):program['decision_gates'][gate]='USER_DECISION_REQUIRED'
    program['decision_gates']['DG-05']='NOT_APPROVED';write(RCC/'validation_v2/PROGRAM_STATE.json',program)
    report='research_control_center/validation_v2/xver_normal/NORMAL_EXECUTION_RESULT_V1.json'
    table('artifacts','artifact_id','ART-XVER-NORMAL-EXECUTION',dict(name='NORMAL_EXECUTION_RESULT_V1.json',role='External normal-only GDN evidence, deterministic T0 and T2 provider preparation',source_ref='validation-v2-hai-xver-normal-prep-001',source_commit=source,producer='RESULT_INTEGRITY',consumer='RCC',public_private='PUBLIC_SAFE',frozen='true',audited=str(bool(qa)).lower(),current='true',superseded='false',safe_path=report))
    for version,row in versions.items():
        table('experiments','experiment_id','EXP-H'+version[:2]+'-XVER',dict(status='IMPLEMENTED_NOT_EXECUTED',current_evidence=f"Normal-only GDN6/T0{row['T0_retained_rules']}Rules;T2 packs/budget frozen;attack evaluation not executed",result_scope='NORMAL_PREPARATION_COMPLETE_ATTACK_EVALUATION_NOT_EXECUTED',next_action='DG-XVER-PROVIDER approval;T2 normal closure;DG05',limitations='Schema-bound partial GDN context;no attack utility or cross-version generalization result',scientific_source_ref='validation-v2-hai-xver-normal-prep-001',scientific_source_commit=source,artifact_refs='ART-EVAL-EXPANSION;ART-XVER-NORMAL-EXECUTION'))
    table('claims','claim_id','CLAIM-N',dict(status='UNVALIDATED',supporting_evidence='artifact:ART-EVAL-EXPANSION;artifact:ART-XVER-NORMAL-EXECUTION',allowed_wording='External normal-only T0 instantiation and T2 evidence preparation are complete;new attack panels are not executed.',validation_needed='DG-XVER-PROVIDER;external T2 normal closure;DG05 one-shot panels;version-separated evaluation',scientific_source_ref='validation-v2-hai-xver-normal-prep-001',scientific_source_commit=source))
    table('timeline','event_id','EVENT-XVER-NORMAL-EXECUTION-001',dict(date='2026-09-05',date_precision='DAY',event_type='GOVERNANCE_MILESTONE',title='외부 버전 정상-only 실행 및 provider Gate 준비',summary='12 split-pure GDN runs;separate global/auxiliary;T0 portfolios;T2 packs;no provider or attack',source='USER_APPROVED_VALIDATION_V2_POLICY',source_ref=report,source_commit='NONE',affected_components='PROJECT_WIDE',decision_refs='DEC-025;DEC-026',status='ACTIVE_CONTEXT',superseded_by='NONE',notes='Normal evidence only;not attack utility or generalization'))
    table('risks','risk_id','RISK-XVER-NORMAL-CUSTODY',dict(description='Normal execution custody restored;single copy and unapproved provider/attack stages remain',evidence='artifact:ART-XVER-NORMAL-EXECUTION',mitigation='Exact restore/hash;DG-XVER-PROVIDER and DG05 remain explicit gates',status='MITIGATING',scientific_source_ref='validation-v2-hai-xver-normal-prep-001',scientific_source_commit=source))
    marker='# HAI-XVER — 정상-only 실행 완료 / Provider 승인 대기'
    for path in [
        RCC/'CURRENT_CONTEXT.md',
        RCC/'SESSION_HANDOFF.md',
        RCC/'MY_TODO.md',
        RCC/'DECISION_INBOX.md',
        RCC/'history/PROJECT_TIMELINE.md',
        RCC/'history/TERMINOLOGY_GUIDE.md',
        ROOT/'docs/professor_experiment_update_v2/03_VALIDATION_V2_METHOD.md',
        ROOT/'docs/professor_experiment_update_v2/10_HELDOUT_NEXT_PLAN.md',
        ROOT/'docs/professor_experiment_update_v2/11_PROFESSOR_DECISION_AGENDA.md',
        ROOT/'docs/professor_experiment_update_v2/13_SLIDE_OUTLINE.md',
    ]:
        old=path.read_text(encoding='utf-8')
        if old.startswith(marker):old=old.split('## 이전 기록 — 역사적 상태\n\n',1)[1]
        path.write_text(marker+'\n\n'+summary+'\n\n## 이전 기록 — 역사적 상태\n\n'+old,encoding='utf-8',newline='\n')
    for name in ('IMPLEMENTATION_TASK_INDEX_V2.csv','PANEL_REGISTRY_V2.csv'):
        path=RCC/'validation_v2/evaluation_expansion'/name
        with path.open(encoding='utf-8') as stream:rows=list(csv.DictReader(stream))
        for row in rows:
            if row.get('task_id')=='HAI-XVER-NORMAL-PREP-001':row.update(status='COMPLETE_QA_PASS' if qa else 'NORMAL_EXECUTION_COMPLETE_FINAL_QA_PENDING',prerequisite='12 GDN runs;T0 normal closure;T2 exact packs/budgets',user_gate='DG_XVER_PROVIDER')
            if row.get('dataset_version') in ('22.04','21.03'):row['normal_authority_policy']='XVER_T0_FROZEN_T2_PACKS_READY_PROVIDER_APPROVAL_PENDING'
        with path.open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    print('RCC_NORMAL_EXECUTION_RECORDED_'+('QA_PASS' if qa else 'FINAL_QA_PENDING'))


if __name__=='__main__':main()
