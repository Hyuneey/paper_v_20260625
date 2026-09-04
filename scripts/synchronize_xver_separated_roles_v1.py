"""Record approved evidence roles without claiming unexecuted scientific results."""
import csv
import json
from synchronize_dg04_stage_a_v1 import ROOT, RCC, write, table
from paperworks.validation_v2.exp03b_custody_v1 import seal, replay, publish

PUB=RCC/'validation_v2/xver_normal'
SOURCE='a207dceecd1903705af904624e8e7289c9f4b036'
SUMMARY='''HAI-XVER-NORMAL-PREP-001: APPROVED_WITH_SEPARATED_GDN_EVIDENCE_ROLES.
이전 BLOCKED_GDN_METHOD_CHANGE_REQUIRED의 estimator 역할 선택은 사용자 승인으로 해소됐습니다.
Provider train1 / bounded retrieval train2에는 EXP03B-compatible split-pure GLOBAL 5-row GDN만 사용합니다.
SCI01 split-local event와 seed별 purged validation 교집합의 EVENT 10-row는 AUXILIARY_CORROBORATION_ONLY입니다.
Global/event 융합, event의 provider·retrieval·verifier·candidate 사용, train3/4 또는 numeric policy 기반 event 선택을 금지합니다.
3개 seed 전부 유지; best-seed 선택 없음. 별도 타입과 실제 frozen projector adapter 합성검사 15 PASS 및 독립 scoped QA PASS.
과학적 역할 binding은 완료됐지만 버전별 execution adapter·custody·environment·performance preflight 통합은 남아 있습니다.
현재 GDN scientific runs 0/12, 외부 T0·T2 pack·정확 token/cost 미완료; provider/credential/공격0.
DG-03B_REVISED 승인으로 완료된 EXP03B와 기존 DEC-025 / Stage A / V2A39 / T0 22 / T2 Repeat1 21 Rules / EXP02 / EXP04/05 / PILOT 결과는 불변입니다.
T2 > T1-B는 정상-only 의미 유도 비교에 한정되고 T0보다 우수하지 않습니다.
DG-03C의 현재 gate명 DG-XVER-PROVIDER는 NOT_READY_EVIDENCE_PENDING; DG05 NOT_APPROVED; 교수 package NOT_SUBMITTED; vault SINGLE_COPY_LOCAL_ONLY.'''


def main():
    binding=json.loads((PUB/'GDN_SEPARATED_EVIDENCE_BINDING_V1.json').read_text());replay(binding)
    old=json.loads((PUB/'XVER_NORMAL_PREPARATION_STATUS_V1.json').read_text());replay(old)
    body={k:v for k,v in old.items() if k not in ('self_hash','training_stop_reason')}
    body.update(schema='xver_normal_preparation_status_v2',status='BINDING_APPROVED_EXECUTION_INTEGRATION_PENDING',
        historical_status_hash=old['self_hash'],binding_hash=binding['self_hash'],
        scientific_decision_required=False,scientific_GDN_runs=0,
        decision_brief='GDN_SEPARATED_EVIDENCE_BINDING_V1.md',
        preparation_remaining=['VERSIONED_EXECUTION_ADAPTER','GLOBAL_KERNEL_EQUIVALENCE',
            'SCI01_EVENT_AND_SEED_PARTITION_CUSTODY','ENVIRONMENT_AND_PERFORMANCE_PREFLIGHT',
            '12_NORMAL_GDN_RUNS','T0_CONFIRM_BIND_GUARD','EXACT_PROVIDER_PACK_AND_BUDGET'],
        DG_XVER_PROVIDER='NOT_READY_EVIDENCE_PENDING',
        global_provider_role=binding['provider_facing_GDN'],event_role=binding['event_role'],
        execution_active=False)
    status=seal(body);publish(PUB/'XVER_NORMAL_PREPARATION_STATUS_V2.json',status)
    report='research_control_center/validation_v2/xver_normal/GDN_SEPARATED_EVIDENCE_BINDING_V1.json'
    state=json.loads((RCC/'registry/current_state.yaml').read_text(encoding='utf-8'))
    state.update(xver_normal_preparation={**status,'report':report},current_phase_statement=SUMMARY,
        scientific_decision_required='NONE_FOR_GDN_EVIDENCE_ROLE_BINDING',
        exact_next_task='HAI-XVER-NORMAL-PREP-001',
        highest_priority_work=['승인된 GLOBAL5 / AUX EVENT10 분리 binding 유지',
            'Execution adapter·custody·환경·preflight 완성 후 정상-only 12-run',
            'T0·provider pack·budget 완료 후 DG-XVER-PROVIDER 별도 승인'],
        top_user_todo=['현재 GDN evidence 역할 추가 결정 불필요','정확 evidence/budget 후 DG-XVER-PROVIDER 승인',
                       'DG05 공격 접근 및 DG06 교수 제출은 별도'])
    state['top_priorities']=state['highest_priority_work']
    state['evaluation_expansion']['external_p1_compatibility']='ROLE_AND_CONTEXT_MAPPING_COMPLETE_GDN_ROLE_BINDING_APPROVED'
    write(RCC/'registry/current_state.yaml',state)
    program=json.loads((RCC/'validation_v2/PROGRAM_STATE.json').read_text(encoding='utf-8'))
    program.update(program_status=status['status'],current_stage='XVER_GDN_SEPARATED_ROLE_BINDING_APPROVED',
        xver_normal_preparation=status,exact_next_task='HAI-XVER-NORMAL-PREP-001')
    for gate in ('DG-XVER-PROVIDER','DG-03C'):program['decision_gates'][gate]='NOT_READY_EVIDENCE_PENDING'
    program['decision_gates']['DG-05']='NOT_APPROVED'
    write(RCC/'validation_v2/PROGRAM_STATE.json',program)
    table('artifacts','artifact_id','ART-XVER-GDN-SEPARATED-ROLES',dict(
        name='GDN_SEPARATED_EVIDENCE_BINDING_V1.json',role='User-approved global-only provider GDN and isolated auxiliary event evidence',
        source_ref='validation-v2-hai-xver-normal-prep-001',source_commit=SOURCE,producer='RESULT_INTEGRITY',consumer='RCC',
        public_private='PUBLIC_SAFE',frozen='true',audited='true',current='true',superseded='false',safe_path=report))
    table('risks','risk_id','RISK-XVER-NORMAL-CUSTODY',dict(description='Context custody 및 GDN 역할 binding 해결;execution adapter·preflight·scientific execution 미완료',
        evidence='artifact:ART-XVER-GDN-SEPARATED-ROLES',mitigation='GLOBAL5와 AUX EVENT10 분리 및 split/custody 검증 후 실행;provider 별도 승인',
        status='MITIGATING',scientific_source_ref='validation-v2-hai-xver-normal-prep-001',scientific_source_commit=SOURCE))
    table('timeline','event_id','EVENT-XVER-GDN-SEPARATED-001',dict(date='2026-09-05',date_precision='DAY',event_type='GOVERNANCE_MILESTONE',
        title='사용자 승인: provider GLOBAL5 / AUX EVENT10 분리',summary='Scientific role choice resolved;15 synthetic tests PASS;GDN0/12;no provider/attack',
        source='USER_APPROVED_VALIDATION_V2_POLICY',source_ref=report,source_commit='NONE',affected_components='PROJECT_WIDE',
        decision_refs='DEC-025;DEC-026',status='ACTIVE_CONTEXT',superseded_by='NONE',notes='Explicit user amendment;not scientific execution result'))
    marker='# HAI-XVER — 승인된 GDN GLOBAL / AUX EVENT 역할 분리'
    for path in [RCC/'SESSION_HANDOFF.md',RCC/'history/TERMINOLOGY_GUIDE.md',
        ROOT/'docs/professor_experiment_update_v2/03_VALIDATION_V2_METHOD.md',
        ROOT/'docs/professor_experiment_update_v2/10_HELDOUT_NEXT_PLAN.md',
        ROOT/'docs/professor_experiment_update_v2/11_PROFESSOR_DECISION_AGENDA.md',
        ROOT/'docs/professor_experiment_update_v2/13_SLIDE_OUTLINE.md']:
        text=path.read_text(encoding='utf-8')
        if not text.startswith(marker):path.write_text(marker+'\n\n'+SUMMARY+'\n\n## 이전 기록 — 역사적 상태\n\n'+text,encoding='utf-8',newline='\n')
    for name in ('IMPLEMENTATION_TASK_INDEX_V2.csv','PANEL_REGISTRY_V2.csv'):
        path=RCC/'validation_v2/evaluation_expansion'/name
        with path.open(encoding='utf-8') as stream:rows=list(csv.DictReader(stream))
        for row in rows:
            if row.get('task_id')=='HAI-XVER-NORMAL-PREP-001':
                row.update(status=status['status'],prerequisite='Approved separated GDN roles;execution adapter and preflight',user_gate='DG_XVER_PROVIDER_AFTER_EXACT_EVIDENCE')
            if row.get('dataset_version') in ('22.04','21.03'):
                row['normal_authority_policy']='NORMAL_SPLIT_ROLE_POLICY_V3_GLOBAL_PROVIDER_AUX_EVENT_SEPARATED'
        with path.open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    print('SEPARATED_GDN_BINDING_RECORDED_EXECUTION_PENDING')


if __name__=='__main__':main()
