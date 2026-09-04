"""Synchronize partial completion and explicit access blocker, never full PASS."""
from pathlib import Path
import json,csv
from synchronize_dg04_stage_a_v1 import ROOT,RCC,PUB,write,table
from paperworks.validation_v2.exp03b_custody_v1 import replay

MARKER='# DG04-XVER-PREP-001 — 현재 중단 지점'
SUMMARY='''DG-04 / DEC-025 승인 완료. DG-03B_REVISED 승인 후 동결한 EXP-03B에서 T2는 T1-B 대비 이점이 있으나 T0보다 우수하지 않았습니다. T0 22 Rules, T2 Repeat 1 21 Rules는 별도 HELDOUT_CANDIDATE이며 V2A39·기존 결과는 불변입니다.

Stage B는 BLOCKED_NORMAL_DATA_CUSTODY. 공식 정상 train1 두 컨테이너의 byte identity 검증 후 embedded label schema에서 중단했습니다. label 값 해석·과학 사용 0이며 정상 컨테이너 byte traversal은 있었습니다. 추가 header 접근 자동심사를 우회하지 않았습니다. Schema-only label 식별 및 feature-only projection 범위를 확인해야 합니다.

외부 STAT/GDN/T0 미실행, DG-03C N/token/cost 미정. eTaPR109 synthetic per-file 일치; 버전 내 집계는 미정. Provider·credential·공격 payload 0. 상세: validation_v2/dg04_xver_prep/CURRENT_PREPARATION_STATUS_V1.md. 전체 task PASS가 아니며 integration merge/push·교수 제출은 하지 않습니다.'''
TEXT='''DG-04는 DEC-025 APPROVED_WITH_SCOPED_AGENTIC_CLAIM으로 고정했습니다. EXP-03B는 DG-03B_REVISED 승인 후 실행·QA 완료된 역사적 결과입니다. T2의 Agentic 의미 유도 이점은 matched-maximum-budget T1-B 대비이며 T0 우월성을 뜻하지 않습니다.

T0 14 pair/22 guard-retained Rules, T2 Repeat 1 13 pair/21 Rules를 별도 HELDOUT_CANDIDATE로 고정했습니다. V2A 21 pair/39 Rules 및 기존 EXP03B/EXP02/EXP04/05/PILOT 결과는 불변입니다.

Stage B: BLOCKED_NORMAL_DATA_CUSTODY. 공식 HAI22/21 train1 정상 컨테이너 각각의 byte identity 검증 후 embedded label schema에서 guard가 중단했습니다. label 값의 해석·검증·과학 사용은 0입니다. 전체 normal container hashing/decompression은 수행했으므로 label-bearing byte traversal 0이라고 주장하지 않습니다.
추가 정상 header 검사가 자동 보안심사에서 label 접근으로 거절되어 우회하지 않았습니다. 정상 schema에서 label 열만 식별하고 값은 버린 뒤 timestamp/feature만 투영하는 범위의 명시적 확인이 필요합니다. 사용자에게 로컬 경로나 upload를 요구하지 않습니다.

공식 표 기준 HAI22 24개, HAI21 22개 P1 역할 feature 대응; portable META 20/19. 정상 schema·sampling은 미검증이며 full GDN model mapping도 미완료입니다. 외부 STAT/GDN/T0 실행 및 T2 evidence pack 생성은 0입니다. DG-03C N/token/cost는 UNKNOWN이므로 아직 승인 가능한 provider brief가 아닙니다.

eTaPR 파일별 공식/합성 109건 정확 일치. 여러 파일의 버전 내 집계, P1 secondary range scope, empty-input 관례는 후속 metric 계약에서 해결해야 합니다. 실제 eligibility 0건, provider/credential/공격 payload 0입니다.

초기 read-only agent 공개 매뉴얼 검색에 scenario 설명이 일부 포함되었지만 공격 CSV/label file은 열지 않았고 eligibility/결과 판단에 사용하지 않았습니다.
Stage A만 QA PASS이며 전체 task PASS가 아닙니다. 부분/차단 상태는 validation-v2에 merge/push하지 않습니다. 교수 package는 초안이며 제출하지 않았습니다.'''


def prefix(path):
    old=path.read_text(encoding='utf-8') if path.exists() else ''
    if old.startswith(MARKER):old=old.split('\n\n## 이전 상태 — 역사적 기록\n\n',1)[1]
    path.write_text(MARKER+'\n\n'+TEXT+'\n\n## 이전 상태 — 역사적 기록\n\n'+old,encoding='utf-8',newline='\n')


def main():
    blocker=json.loads((PUB/'XVER_NORMAL_CUSTODY_BLOCKER_V1.json').read_text());replay(blocker)
    mapping=json.loads((PUB/'P1_FEATURE_MAPPING_AUTHORITY_V1.json').read_text());replay(mapping)
    metric=json.loads((PUB/'ETAPR_CONFORMANCE_RECEIPT_V2.json').read_text());replay(metric)
    status={'status':blocker['status'],'blocker_hash':blocker['self_hash'],'stage_a':'COMPLETE_QA_PASS',
            'mapping_hash':mapping['self_hash'],'metadata_feature_counts':{'22.04':24,'21.03':22},
            'portable_meta_counts':mapping['portable_meta_counts'],'external_GDN_runs':0,'external_STAT_runs':0,
            'external_T0_runs':0,'DG03C':'NOT_READY','exact_provider_budget':None,'provider_calls':0,
            'etapr_per_file':'PASS','etapr_conformance_hash':metric['self_hash'],
            'multi_file_metric_aggregation':'UNRESOLVED','attack_payload_accesses':0,
            'report':'research_control_center/validation_v2/dg04_xver_prep/XVER_NORMAL_CUSTODY_BLOCKER_V1.json'}
    state=json.loads((RCC/'registry/current_state.yaml').read_text(encoding='utf-8'))
    state['dg04_method_lock']['status']='STAGE_A_COMPLETE_STAGE_B_BLOCKED'
    state.update(xver_preparation=status,current_phase_statement=SUMMARY,
                 exact_next_task='DG-04 후속 정상 준비 — BLOCKED_NORMAL_DATA_CUSTODY (schema-only projection 범위 확인)',
                 highest_priority_work=['DG04·T0/T2 고정 완료, 기존 결과 보존','정상 schema projection 자동심사 차단 범위 확인','DG03C budget 미정; provider·공격 접근 금지'],
                 top_user_todo=['정상 schema-only label 열 식별 및 feature-only projection 범위 확인','DG-03C: 외부 evidence·정확한 예산 동결 후 별도 승인','DG-05/06: 공격 접근과 교수 제출 별도 승인'])
    state['top_priorities']=state['highest_priority_work'];state['recommended_next_management_task']=state['exact_next_task']
    for todo in state.get('user_todo_items',[]):
        if todo['id']=='USER-V2-004':todo.update(task='정상 schema-only projection 접근 범위 확인',why='자동심사가 embedded label 열 이름까지 label 접근으로 해석하여 차단',linked=status['report'],status='OPEN')
    write(RCC/'registry/current_state.yaml',state)
    program=json.loads((RCC/'validation_v2/PROGRAM_STATE.json').read_text(encoding='utf-8'))
    program.update(program_status='BLOCKED_NORMAL_DATA_CUSTODY',current_stage='DG04_XVER_STAGE_B_BLOCKED',
                   exact_next_task=state['exact_next_task'],dg04_method_lock=state['dg04_method_lock'],xver_preparation=status)
    program['decision_gates']['DG-03C']='NOT_READY_BLOCKED_NORMAL_DATA_CUSTODY';write(RCC/'validation_v2/PROGRAM_STATE.json',program)
    table('decisions','decision_id','DEC-025',{'context':'EXP03B 독립 QA PASS; T2 대 T1-B scoped support; 주요 의미 지표 T0 우월',
        'current_relevance':'DG04_RESOLVED;XVER_NORMAL_CUSTODY_BLOCKED;DG03C_NOT_READY'})
    table('risks','risk_id','RISK-XVER-NORMAL-CUSTODY',dict(category='CUSTODY',description='공식 정상 컨테이너 embedded label schema와 label 접근 금지의 보안심사 경계 미해결',
        severity='HIGH',likelihood='HIGH',affected_component='RESULT_INTEGRITY',evidence='artifact:ART-XVER-CUSTODY-STOP',
        mitigation='추가 데이터 접근 중단; label 값 배제 projection 범위 확인; private path 요청·우회 금지',owner='RESEARCH_OWNER',status='OPEN',scientific_source_ref='validation-v2-dg04-xver-prep-001',scientific_source_commit='f7ce07955e56ce0140b30faea201e7f8ac11f8a3'))
    table('timeline','event_id','EVENT-DG04-XVER-PREP-001',dict(date='2026-09-04',date_precision='DAY',event_type='GOVERNANCE_MILESTONE',
        title='DG04 승인·T0/T2 후보 고정, 외부 정상 custody 차단',summary='StageA QA PASS; external train1 두 정상 컨테이너 byte identity 뒤 header guard 중단; eTaPR per-file109 PASS; 전체 완료 아님',
        source='USER_APPROVED_VALIDATION_V2_POLICY',source_ref=status['report'],source_commit='NONE',affected_components='PROJECT_WIDE',decision_refs='DEC-025',status='ACTIVE_CONTEXT',superseded_by='NONE',notes='provider0;attack0;DG03C budget unknown;partial state not integrated'))
    for identity,name in (('ART-DG04-LOCK','FINAL_METHOD_LOCK_V1.json'),('ART-DG04-T0','T0_HELDOUT_CANDIDATE_PORTFOLIO_V1.json'),
                          ('ART-DG04-T2','T2_HELDOUT_CANDIDATE_PORTFOLIO_V1.json'),('ART-XVER-MAPPING','P1_FEATURE_MAPPING_AUTHORITY_V1.json'),
                          ('ART-XVER-CUSTODY-STOP','XVER_NORMAL_CUSTODY_BLOCKER_V1.json'),('ART-ETAPR-CONFORMANCE','ETAPR_CONFORMANCE_RECEIPT_V2.json')):
        table('artifacts','artifact_id',identity,dict(name=name,role='Prospective method or explicitly scoped preparation record',
             source_ref='validation-v2-dg04-xver-prep-001',source_commit='f7ce07955e56ce0140b30faea201e7f8ac11f8a3',producer='RESULT_INTEGRITY',consumer='RCC',
             public_private='PUBLIC_SAFE',frozen='true',audited='true',current='true',superseded='false',safe_path='research_control_center/validation_v2/dg04_xver_prep/'+name))
    for path in [RCC/'SESSION_HANDOFF.md',RCC/'history/TERMINOLOGY_GUIDE.md',
                 ROOT/'docs/professor_experiment_update_v2/03_VALIDATION_V2_METHOD.md',
                 ROOT/'docs/professor_experiment_update_v2/10_HELDOUT_NEXT_PLAN.md',
                 ROOT/'docs/professor_experiment_update_v2/11_PROFESSOR_DECISION_AGENDA.md',
                 ROOT/'docs/professor_experiment_update_v2/13_SLIDE_OUTLINE.md']:
        prefix(path)
    (PUB/'CURRENT_PREPARATION_STATUS_V1.md').write_text(MARKER+'\n\n'+TEXT+'\n',encoding='utf-8',newline='\n')
    print('DG04_XVER_BLOCKED_STATE_SYNCHRONIZED_NOT_FULL_PASS')


if __name__=='__main__':main()
