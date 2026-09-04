"""Public-safe Stage B preparation receipts; no dataset or provider I/O."""
from pathlib import Path
from hashlib import sha256
import csv,json,subprocess
from paperworks.validation_v2.exp03b_custody_v1 import seal,publish,replay
from paperworks.validation_v2.exp03b_contract_v1 import require
from paperworks.validation_v2.gdn_corr_contract_v1 import Exp01CConfigV1

ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/'research_control_center/validation_v2/dg04_xver_prep'
EXP=ROOT/'research_control_center/validation_v2/evaluation_expansion'


def doc(name, content):
    (PUB/name).write_text(content.strip()+'\n',encoding='utf-8',newline='\n')


def main():
    old=json.loads((PUB/'P1_FEATURE_MAPPING_AUTHORITY_V1.json').read_text());replay(old)
    projection=json.loads((PUB/'NORMAL_SCHEMA_ONLY_PROJECTION_CONTRACT_V2.json').read_text());replay(projection)
    custody={v:json.loads((PUB/f'HAI{v[:2]}_NORMAL_PROJECTION_RECEIPT_V2.json').read_text()) for v in ('22.04','21.03')}
    candidates={v:json.loads((PUB/f'HAI{v[:2]}_META_STAT_CANDIDATE_AUTHORITY_V2.json').read_text()) for v in custody}
    for value in [*custody.values(),*candidates.values()]:replay(value)
    rows=[]
    for v,bundle in custody.items():
        require(bundle['status']=='NORMAL_ONLY_CUSTODY_READY','NORMAL_CUSTODY')
        for r in old['rows']:
            identity=r[f'hai{v[:2]}_identity'];present=identity!='ABSENT'
            if present:
                require(all(identity in file['projected_feature_identities'] and file['sample_interval_seconds']==1 and
                            file['datatype']=='FINITE_FLOAT64' for file in bundle['records']),'MAPPING_SCHEMA')
            rows.append({'version':v,'canonical_hai23_identity':r['hai23_identity'],'mapped_identity':identity,
                'status':'EXACT_MATCH' if present else 'ABSENT','verified_alias':False,'role':r['role'],
                'unit':r['unit'],'role_unit_process_basis':r['role_unit_process_basis'],
                'datatype_compatibility':'FINITE_FLOAT64' if present else 'NOT_APPLICABLE',
                'sample_rate_compatibility':'ONE_SECOND' if present else 'NOT_APPLICABLE',
                'execution_eligible':present,'evidence_reference':r['evidence_reference'],
                'normal_custody_hash':bundle['self_hash']})
    mapping=seal({'schema':'p1_feature_mapping_authority_v2','supersedes_hash':old['self_hash'],
         'scope':'CANDIDATE_ROLE_FEATURES_NOT_FULL_GDN_CONTEXT','projection_contract_hash':projection['self_hash'],
         'rows':rows,'normal_execution_authorized':True,'aliases_inferred':0,
         'versions':{v:{'source_count':c['source_count'],'target_count':c['target_count'],
                       'universe_count':c['universe_count'],'portable_META':c['META_count'],
                       'status':'FULL_COMMON_P1_UNIVERSE' if c['universe_count']==144 else 'PARTIAL_COMMON_P1_UNIVERSE'} for v,c in candidates.items()}})
    publish(PUB/'P1_FEATURE_MAPPING_AUTHORITY_V2.json',mapping)
    with (PUB/'DATASET_COMPATIBILITY_MATRIX_V3.csv').open('w',encoding='utf-8',newline='') as out:
        writer=csv.DictWriter(out,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    n=custody['21.03']['records'][2]['row_count'];m=n//2;p=projection['hai21_partition']['purge_seconds']
    partition=seal({'schema':'hai21_train3_partition_receipt_v2','projection_contract_hash':projection['self_hash'],
        'projection_hash':custody['21.03']['records'][2]['projection_hash'],'row_count':n,'purge_rows':p,
        'block_A':[0,m-p//2],'purge':[m-p//2,m+(p+1)//2],'block_B':[m+(p+1)//2,n],
        'index_semantics':'ZERO_BASED_HALF_OPEN','context_cross_boundary_allowed':False,
        'arithmetic_frozen_before_projection':True,'scientific_block_values_consumed':False})
    publish(PUB/'HAI21_TRAIN3_PARTITION_RECEIPT_V2.json',partition)
    config=Exp01CConfigV1()
    plan=seal({'schema':'external_gdn_preparation_plan_v2','status':'BLOCKED_PENDING_HAI_XVER_NORMAL_PREP',
        'architecture_family_config':config.to_dict(),'architecture_family_hash':config.config_hash,
        'scientific_training_this_task':False,'runs_per_version':6,
        'run_matrix':[{'split':s,'seed':seed} for s in ('train1','train2') for seed in (11,23,37)],
        'context_mapping_status':'ROLE_MAPPING_READY_FULL_GDN_CONTEXT_INCOMPLETE',
        'unresolved_identity':'P1_PP04D','unresolved_reason':'Not defined by inspected official datapoint table; header equality alone does not prove role/unit.',
        'context_policy':'Freeze exact independently supported version-specific context subset; no guessed alias/zero filling/candidate-only substitution.',
        'environment_status':'PLANNED_NOT_LIVE_VERIFIED','device':'cuda','dtype':'float32',
        'fallback':'WHOLE_VERSION_PROSPECTIVE_CONTRACT_ONLY_BEFORE_RUN_1',
        'checkpoint_namespace':'external_version/version/split/seed/private_checkpoint',
        'provider_evidence':'SPLIT_PURE_EVENT_CONDITIONED_EDGEMASK; global evidence separately labelled',
        'reusable_backend':'train_exp01c_seed_v1; purged_contiguous_validation_plan_v1; evaluate_exp01c_checkpoint_v1',
        'prohibited_adapter':'exp03b_gdn_v1.infer hardcoded HAI23 row/37-node identity',
        'code_hashes':{f:sha256((ROOT/f).read_bytes()).hexdigest() for f in
            ['src/paperworks/validation_v2/gdn_corr_contract_v1.py','src/paperworks/validation_v2/exp01c_backend_v1.py']}})
    publish(PUB/'EXTERNAL_GDN_PREPARATION_PLAN_V2.json',plan)
    doc('HAI-XVER-NORMAL-PREP-001.md','''# HAI-XVER-NORMAL-PREP-001 — 다음 정상-only 실행

Stage A와 external normal projection/META+STAT authority를 재사용합니다. 공격/provider/credential 금지.
현재는 외부 GDN 학습·semantic evidence·T0·T2 pack 미실행입니다. 이 파일을 생성했다고 실행하지 않습니다.

1. P1 role mapping과 별도로 37개 historical context node의 공식 role/unit/version 대응을 동결합니다.
   P1_PP04D는 공식 표에서 미해결. 헤더 같음·suffix 제거·PP04/SP 추정 대응 금지.
   Exact-compatible version-specific subset만 prospective freeze하며 24-node 후보-only 대체/zero-fill 금지.
   방어 가능한 포함 정책이 없으면 BLOCKED_GDN_COMPATIBILITY. 새 empirical 선택을 하지 않습니다.
2. 현재 architecture family/config hash를 그대로 적용합니다. 각 버전 train1/train2 × seed11/23/37,
   총6회. Train-only robust median/IQR, purged validation, self-exclusion, shared multi-horizon1/5/10/30/60.
   CUDA environment/driver/torch/dtype/config/node order/actual row count를 run1 전에 별도 receipt로 동결하고
   synthetic smoke/reference equivalence PASS 후 실행합니다. 부분 실행 뒤 backend 변경 금지.
3. 정상 projection을 승인 context allowlist로 별도 버전 확장하고 checkpoint atomic/reopen/hash/private custody.
   HAI23 checkpoint 재학습 및 historical hardcoded 37-node/rowcount inference 직접 사용 금지.
4. Train1 provider-equivalent structural/STAT/GDN와 train2 hidden/retrieval을 물리적으로 분리합니다.
   Global EdgeMask를 event-conditioned라고 표시하지 않습니다. Train3/4 정보를 provider에 전송하지 않습니다.
5. T0 once/pair → hidden train2 → hidden train3 → frozen SCI02B → Formal V4 → one-way normal guard.
   HAI21 train3는 동결 A/purge/B 산술에 따라 file-local로 취급하고 boundary context 공유 금지.
6. T2 single portfolio-producing schedule만 준비: 최대3call/pair, ACCEPTED early-stop; repeats/T1/T1-B 없음.
   Exact evidence/prompt/schema/privacy/token/cost freeze 후 DG-XVER-PROVIDER에 중단합니다.

수치정책 n7-q0.90-s2-f0.05 고정, train1/train2 deterministic max pooling. 37-grid 재선택 금지.
GPU/normal computation은 과학·privacy choice가 없으면 별도 사용자 결정 없이 이 후속 범위로 가능하나
provider와 모든 공격 접근은 별도 승인입니다. 기존 V2A/T0/T2 결과는 수정하지 않습니다.
''')
    doc('METRIC_BINDING_DECISION_BRIEF_V2.md','''# 공격 실행 전 미정 metric binding

기존 eTaPR per-file conformance는 PASS입니다. 다음 세 선택은 frozen 계약으로 도출되지 않아 임의 결정하지 않습니다.

1. 한 버전 여러 파일: per-file only인지, version aggregate인지. Aggregate라면 P/R weighting과 F1 산식 필요.
2. Secondary P1 range scope: OUT_OF_SCOPE/CROSS_PROCESS/UNRESOLVED 시간의 prediction/reference/exposure 처리.
   Primary P1 denominator에서 빠진 공격 시간을 normal로 자동 재분류하지 않습니다.
3. Empty eTaPR: reference-only/prediction-only/both-empty 각각의 값, undefined 처리와 aggregate denominator.

현재 wrapper는 per-file/UNDEFINED_EMPTY_RANGE_INPUT만 제공합니다. 이것은 정상 준비를 막지 않지만
DG05 metric freeze 전에 SCIENTIFIC_DECISION_REQUIRED입니다. Primary scenario denominator0은
NOT_OBSERVED. 공식 scenario가 primary unit이며 interval subdivision·point adjustment·primary pooled Recall 금지.
''')
    doc('DG_XVER_PROVIDER_DECISION_BRIEF_V1.md',f'''# DG-XVER-PROVIDER — 준비 대기

상태: BLOCKED_PENDING_HAI_XVER_NORMAL_PREP. 이전 DG03C 미준비 기록은 역사적으로 보존합니다.
HAI22 N={candidates['22.04']['candidate_count']}; HAI21 N={candidates['21.03']['candidate_count']}.
구조적 최대 호출은 각 3N={3*candidates['22.04']['candidate_count']}/{3*candidates['21.03']['candidate_count']}이지만
이는 승인 가능한 exact provider budget이 아닙니다. Expected calls/input/output/total token/cost는 UNKNOWN.
실제 GDN/structural evidence와 prompt가 없으므로 정확한 payload 또는 READY를 만들지 않습니다.

선호 snapshot gpt-5.4-mini-2026-03-17 / Responses API. 최종 freeze에서 재검증하되 지금 capability probe 없음.
각 pair 한 portfolio-producing execution, 3회 이내, ACCEPTED 즉시 중지. 동시 호출1, automatic retry/fallback 없음.
Provider: 해당 version train1 pair/structural/STAT/GDN, T2 bounded train2 aggregate만.
금지: numeric policy/role values, 최종답, META tier/manual, train3/4, 공격, labels, 경로, credential, 다른 arm outcomes.
No credential read / provider calls. 다음: HAI-XVER-NORMAL-PREP-001.
''')
    doc('DG05_MULTI_PANEL_ATTACK_ACCESS_BRIEF_V1.md','''# DG05 다중 panel 공격 접근 — USER_DECISION_REQUIRED

HAI23_TEST2_PRIMARY_HELDOUT_V1 / HAI22_EXTERNAL_REPLICATION_V1 / HAI21_EXTERNAL_REPLICATION_V1.
HAI23_TEST1_DEVELOPMENT_V1은 immutable이고 재개하지 않습니다.
Primary H0 PCA, H1 T0, H2 T2, H3 PCA+T0, H4 PCA+T2.
Secondary IF, IF+T2, V2A39 reference 및 역사적 continuity. 기존 same-file/second FAIL≥2 physical sources,
base detector alarm pointwise 보존 fusion만 사용. 새 fusion 없음.

전제: HAI23 기존 T0/T2 portfolios; 외부 버전 normal custody/candidates/context/GDN/semantic/T0/T2 portfolios;
동결 SCI02B/normal role/metric authority. 외부 T2는 별도 DG-XVER-PROVIDER 승인 필요.
공식 scenario ID/attacked point와 frozen P1 mapping을 독립 custodian이 사용하며 prediction/outcome 입력 금지.
Eligibility는 모든 method prediction atomic/fsync/close/reopen/schema/hash/row-count freeze와 writer권한 회수 후 공개.
Primary P1_ELIGIBLE scenario Recall/normal false episodes per hour. Secondary ranges/coverage/delay/overlap은
기존 계약만 사용하며 METRIC_BINDING_DECISION_BRIEF_V2의 미정 사항을 먼저 해결합니다.
One-shot label capability, no post-result tuning, version-separated reporting/no primary pooling/no IID.
어떤 method authority/custody/metric gate라도 실패하면 affected panel fail closed; 독립 QA 필수.
Actual scenario/eligibility는 이 준비에서 만들지 않았으며 모든 attack access0. 제출 DG06 별도.
''')
    doc('EXTERNAL_PERFORMANCE_PREFLIGHT_V2.md',f'''# 외부 정상 성능 사전 점검

실측: 9개 streaming projection 완료, 기존 scalar/vectorized STAT synthetic parity PASS.
Projection은 byte framing만 전체 traverse, selected-only decode; 파일당 최대CSV record1MiB.
Projected CSV를 immutable shared cache로 재사용하고 float64 round_trip으로 frozen STAT 정밀도를 보존합니다.
Projection file별 wall_seconds는 custody receipts, STAT wall_seconds는 candidate receipts에 기록했습니다.

| 경로 | 병목 분류 | 고정 대응 |
|---|---|---|
| acquisition/hash/projection | IO_BOUND + PYTHON_OVERHEAD | streaming; selected spans; streaming hash; immutable reuse |
| timestamp/mapping | CPU_BOUND | once-per-projection validation; receipt lookup |
| STAT | CPU_BOUND + MEMORY_BOUND | unchanged vectorized matrix; one split at a time; scalar parity |
| temporal evidence/SCI02B/Formal V4/guard | CPU_BOUND/PYTHON_OVERHEAD | frozen kernels; cached tuples; source-specific event universe |
| GDN windows/training/extraction | GPU_BENEFICIAL + MEMORY_BOUND | future fixed CUDA; batch windows/masks; atomic per-run checkpoint |
| T0/hidden verifier/serialization | CPU_BOUND/PYTHON_OVERHEAD | immutable evidence cache; deterministic serialization |

GDN real run/smoke/environment verification와 외부 temporal/T0 guard는 아직 실행하지 않았습니다.
별도 후속 contract에서 reference equivalence 후 실행합니다. HAI23 backend/seed/hyperparameter 변경0.
실제 정상 결과로 성능 설정을 선택하지 않았습니다. 시간 예측 없음.
''')
    doc('NORMAL_SPLIT_ROLE_POLICY_V3.md',f'''# 정상 split 역할 V3 — schema-only amendment 적용

V1/V2는 역사적으로 보존. 외부 numeric option search는 superseded.
HAI22: train1 provider/T0, train2 hidden verifier/retrieval, train3 hidden confirmation/calibration,
train4 numeric evaluation/one-way guard, train5 robustness, train6 reproducibility.
Candidate STAT와 별도 detector fit은 train1+train2; provider/retrieval STAT는 각각 split-pure.
HAI21: train1/provider/T0, train2/hidden/retrieval, train3 n={n}.
Frozen arithmetic p=60, A=[0,{m-30}), purge=[{m-30},{m+30}), B=[{m+30},{n}).
이 산술은 projection 전에 contract로 고정했으며 현재 schema/count로 materialize했을 뿐 block scientific values는 미사용입니다.
No shared timestamp/context; windows/events를 각 block 내부에서만 생성합니다.
SCI02B n7-q0.90-s2-f0.05 deterministic normal train1/train2 max pooling; 37옵션 재선택0.
''')
    status=seal({'schema':'dg04_xver_resumed_preparation_v2','status':'BLOCKED_PENDING_HAI_XVER_NORMAL_PREP',
        'stage_a':'COMPLETE_QA_PASS','stage_a_changed':False,'historical_blocker':'RESOLVED_BY_SCHEMA_ONLY_USER_APPROVAL',
        'projection_contract_hash':projection['self_hash'],'normal_custody_hashes':{v:c['self_hash'] for v,c in custody.items()},
        'mapping_hash':mapping['self_hash'],'candidate_hashes':{v:c['self_hash'] for v,c in candidates.items()},
        'candidate_counts':{v:c['candidate_count'] for v,c in candidates.items()},'GDN_scientific_runs':0,'external_T0_runs':0,
        'external_provider_evidence_ready':False,'exact_provider_budget':None,'provider_calls':0,
        'label_values_parsed':False,'attack_payload_accesses':0,'test1_accesses':0,'test2_accesses':0,
        'projection_files':9,'private_exposures':0,'exact_next':'HAI-XVER-NORMAL-PREP-001',
        'additional_dependencies':['GDN_CONTEXT_MAPPING_P1_PP04D','PRE_ATTACK_METRIC_BINDING_DECISION'],
        'integration_merge_allowed':False})
    publish(PUB/'STAGE_B_RESUME_STATUS_V2.json',status)
    print(json.dumps({'status':status['status'],'normal_files':9,'candidate_counts':status['candidate_counts'],'partition':partition['self_hash']}))


if __name__=='__main__':main()
