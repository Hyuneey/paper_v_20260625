"""Public metadata planning + truthful custody stop; never opens normal/attack rows."""
from pathlib import Path
from hashlib import sha1,sha256
import csv,json
from paperworks.validation_v2.exp03b_custody_v1 import seal,publish,replay

ROOT=Path(__file__).resolve().parents[1]
RCC=ROOT/'research_control_center'
PUB=RCC/'validation_v2/dg04_xver_prep'
EXP=RCC/'validation_v2/evaluation_expansion'


def document(name,text):
    (PUB/name).write_text(text.strip()+'\n',encoding='utf-8',newline='\n')


def write_csv(path,rows):
    with path.open('w',encoding='utf-8',newline='') as out:
        writer=csv.DictWriter(out,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)


def main():
    acquisition=json.loads((PUB/'XVER_NORMAL_MATERIALIZATION_CONTRACT_V1.json').read_text());replay(acquisition)
    manual=ROOT/'tmp/dg04_xver_public_manual/hai_dataset_technical_details.pdf'
    raw=manual.read_bytes()
    assert sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==acquisition['manual_git_blob_sha1']
    prior=list(csv.DictReader((EXP/'DATASET_COMPATIBILITY_MATRIX_V1.csv').open(encoding='utf-8')))
    # Reviewed official Table 1, PDF pages 13-14; no fuzzy/alias matching.
    absent21={'P1_PP04','P1_TIT03'}
    rows=[]
    for item in prior:
        tag=item['hai23_feature']; role=item['role']
        unit=('%' if role=='SOURCE' else ('l/h' if tag in {'P1_FT01Z','P1_FT02Z','P1_FT03Z'} else
             'mmH2O' if tag in {'P1_FT01','P1_FT02','P1_FT03'} else 'mm' if tag=='P1_LIT01' else
             'bar' if tag in {'P1_PIT01','P1_PIT02'} else 'degC'))
        rows.append({'hai23_identity':tag,'role':role,'hai22_identity':tag,'hai21_identity':tag if tag not in absent21 else 'ABSENT',
            'hai22_mapping':'EXACT_MATCH','hai21_mapping':'ABSENT' if tag in absent21 else 'EXACT_MATCH',
            'alias':'NONE','unit':unit,'role_unit_process_basis':'OFFICIAL_TABLE_1_SAME_ROW',
            'datatype_compatibility':'UNRESOLVED_NORMAL_SCHEMA_PENDING','sample_rate_compatibility':'UNRESOLVED_NORMAL_SCHEMA_PENDING',
            'execution_eligible':False,'evidence_reference':'HAI_PINNED_MANUAL_TABLE_1_PDF_13_14'})
    write_csv(PUB/'DATASET_COMPATIBILITY_MATRIX_V2.csv',rows)
    meta=json.loads((ROOT/'docs/task_reports/TASK-039C_META_RESULT.json').read_text())
    assert meta['artifact_hash']=='0e3b055df911c74bd0e0993b7b3bb122860b265192ad0cf91d54edc1e74635bf'
    portable={v:[p for p in meta['top20_identities'] if p['source_identity'] not in missing and p['target_identity'] not in missing]
              for v,missing in (('22.04',set()),('21.03',absent21))}
    mapping=seal({'schema':'p1_feature_mapping_authority_v1','status':'METADATA_REVIEWED_NORMAL_CUSTODY_PENDING',
        'official_commit':acquisition['pinned_commit'],'manual_git_blob_sha1':acquisition['manual_git_blob_sha1'],
        'manual_sha256':sha256(raw).hexdigest(),'table_pages':[13,14],'rows':rows,
        'meta_prior_hash':meta['artifact_hash'],'portable_meta_counts':{v:len(p) for v,p in portable.items()},
        'metadata_universes':{v:{'source_count':sum(r['role']=='SOURCE' and r[f'hai{v[:2]}_identity']!='ABSENT' for r in rows),
                               'target_count':sum(r['role']=='TARGET' and r[f'hai{v[:2]}_identity']!='ABSENT' for r in rows)} for v in portable},
        'normal_execution_authorized':False,'new_meta_pairs_created':0,'aliases_inferred':0,
        'full_gdn_model_feature_mapping':'UNRESOLVED_SEPARATE_37_NODE_MAPPING_REQUIRED'})
    publish(PUB/'P1_FEATURE_MAPPING_AUTHORITY_V1.json',mapping)
    blocker=seal({'schema':'dg04_xver_preparation_stop_v1','status':'BLOCKED_NORMAL_DATA_CUSTODY',
        'stage_a':'COMPLETE_QA_PASS','affected_versions':['22.04','21.03'],
        'initial_issue':'LABEL_COLUMN_REJECTED_BEFORE_ROWS',
        'safety_review_issue':'AUTO_REVIEW_REJECTED_ADDITIONAL_COMPLETE_NORMAL_HEADER_PRINT',
        'scope':'Explicit normal file/header authorization exists, but label-access prohibition was interpreted to include label column names by execution safety review.',
        'no_bypass_performed':True,'required_next':'Explicitly authorize schema-only embedded-label identification and label-excluding timestamp/feature projection; no label-value decoding/validation/use.',
        'official_normal_containers_materialized':['HAI22_TRAIN1','HAI21_TRAIN1'],
        'normal_custody_ready':False,'normal_rows_parsed_for_science':0,
        'normal_container_bytes_downloaded_hashed_and_decompressed':True,
        'embedded_label_schema_detected':True,'embedded_label_value_semantic_validation_or_use':0,
        'normal_label_bearing_container_byte_traversal':'YES_AUTHORIZED_OFFICIAL_NORMAL_MATERIALIZATION_NOT_LABEL_INTERPRETATION',
        'attack_payload_accesses':0,'test1_reopened':0,'test2_accesses':0,'provider_calls':0,'credential_reads':0,
        'public_manual_scenario_metadata_incidental_view':'READ_ONLY_AGENT_BROAD_MANUAL_TEXT_SEARCH;NO_ELIGIBILITY_CREATED_OR_OUTCOMES_USED',
        'external_STAT_runs':0,'external_GDN_runs':0,'external_T0_runs':0,'external_T2_packs':0,
        'DG03C':'NOT_READY_NOT_AN_APPROVABLE_BUDGET','integration_merge_allowed':False})
    publish(PUB/'XVER_NORMAL_CUSTODY_BLOCKER_V1.json',blocker)
    document('P1_MAPPING_REPORT_V1.md',f'''# P1 외부 버전 매핑 — metadata-only

공식 pinned manual Table 1(PDF 13–14쪽)을 시각 검토하고 Git blob/SHA를 재확인했습니다.
HAI22: 12 source × 12 target, 24개 exact-name metadata 대응.
HAI21: P1_PP04와 P1_TIT03은 표의 21.03 column에 없습니다. 나머지 11×11, 22개 대응입니다.
이는 정상 CSV datatype·sampling 검증 완료나 실행 가능한 candidate authority를 의미하지 않습니다.
정상 헤더 projection 접근 차단으로 실제 schema/sample-rate는 UNRESOLVED입니다.

FT01/02/03(mmH2O)와 FT01Z/02Z/03Z(l/h)를 구별했습니다. suffix 유사성을 alias 근거로 쓰지 않았습니다.
고정 META Top-20 metadata portability: HAI22 {len(portable['22.04'])}, HAI21 {len(portable['21.03'])}.
새 META 선언·pair·padding·reranking 없음. STAT를 실행하지 않아 candidate union N은 미정입니다.
GDN의 전체 37-node 입력 schema는 이 24개 역할 매핑과 별개입니다. 특히 P1_PP04D의 공식 대응을
추가 검증해야 하며 24-node 모델로 조용히 대체하지 않습니다.

일부 공개 매뉴얼 scenario 설명이 초기 read-only agent 검색에 포함되었습니다. 공격 CSV/label file은
열지 않았고 eligibility나 scientific decisions에 사용하지 않았습니다. 이후 표 페이지만 제한했습니다.
''')
    document('NORMAL_SPLIT_ROLE_POLICY_V2.md','''# 정상 split 역할 V2 — 전향적 계획

V1의 external EXP-02 재선택 계획을 prospectively supersede합니다. V1은 삭제하지 않습니다.
HAI23 기존 authority는 변경하지 않습니다.

| 버전 | train1 | train2 | train3 | train4 | train5 | train6 |
|---|---|---|---|---|---|---|
| HAI22 | provider/T0 구조·STAT·GDN | hidden verifier/retrieval | hidden confirmation·detector calibration | numeric evaluation·one-way guard | normal robustness | stability/reproduction |
| HAI21 | provider/T0 구조·STAT·GDN | hidden verifier/retrieval | A confirmation/calibration; purge; B one-way guard | 해당 없음 | 해당 없음 | 해당 없음 |

Detector fit과 candidate STAT는 별도 고정 authority로 train1+train2를 사용할 수 있습니다.
Provider STAT/GDN은 train1-only, retrieval은 train2-only입니다. Train3/guard는 돌아오지 않습니다.
수치 정책은 n7-q0.90-s2-f0.05 고정. 37-option 재선택을 하지 않으며 각 버전 train1/train2 통계로
SCI-02B 값을 산출하고 보수적 max pooling합니다. HAI23 수치값을 이전하지 않습니다.

HAI21 row arithmetic: n 행, m=floor(n/2), purge p의 좌측 floor(p/2), 우측 ceil(p/2).
A=[0,m-floor(p/2)), B=[m+ceil(p/2),n). 기존 partition_hai21_train3_v1을 재사용합니다.
정확한 p는 전체 외부 모델 feature/context authority를 완성한 뒤 history/baseline/response/horizon
의 합성 최대 raw context 이상으로 사전 동결해야 합니다. 현재 n/p 값은 미적용이며 값 기반 분석 0입니다.
이 문서는 역할 고정이며 아직 실행 가능한 분할 receipt가 아닙니다.
''')
    document('EXTERNAL_PERFORMANCE_PREFLIGHT_V1.md','''# 외부 정상 실행 성능 사전 점검

상태: STATIC_REVIEW_COMPLETE / REAL_NORMAL_PREFLIGHT_BLOCKED_BY_CUSTODY.
HAI23 학습·checkpoint·환경은 변경하지 않았습니다. 외부 GDN 실행 0/12입니다.

1. 공식 normal-file identity replay 후 timestamp+feature 전용 bounded-memory projection/cache가 필요합니다.
   현재 label-free-only V1 guard는 정상 파일의 embedded label schema에서 fail closed합니다.
2. 37-node 전체 feature mapping과 version/split/cache hash를 먼저 고정해야 합니다.
3. train1-only/train2-only 각 11/23/37, 버전당 6개 run. Robust train-only scaler, purged validation,
   self-excluded shared graph, 1/5/10/30/60 heads, 고정 CUDA dtype/seed를 run1 전에 동결합니다.
4. 기존 generic training/window/streaming hash 구현을 재사용하되 HAI23 row-count·37-column 상수
   adapter를 외부 데이터에 직접 쓰지 않습니다. GDN train4 evidence와 global EdgeMask를 split-pure
   event-conditioned evidence로 잘못 표시하지 않습니다.
5. 동일 split의 event-conditioned extraction, immutable evidence cache, deterministic serialization,
   per-run atomic checkpoint resume, bounded graph-mask batching을 사용하고 reference 동등성 검증 후 실행합니다.
6. 실제 정상파일 performance 동등성·GPU smoke·환경 freeze는 custody 다음 단계이며 완료로 표시하지 않습니다.

eTaPR 성능은 별도 synthetic conformance receipt의 fixture별 측정값에만 해당합니다. 실행 시간 예측 없음.
''')
    document('ETAPR_AND_ELIGIBILITY_PREPARATION_V1.md','''# eTaPR / eligibility 준비

Pinned official source와 MIT license를 선택 취득했습니다. 전체 repository clone/real sample 취득은 하지 않았습니다.
고정 theta_p=0.5, theta_r=0.1, delta=0.0. 별도 metric dependency target이므로 기존 과학 환경 불변입니다.
ETAPR_CONFORMANCE_RECEIPT_V2: 공식 Hypothetical 4 + local synthetic 105 정확 일치, deterministic replay PASS.
V1 receipt는 초기 wrapper 점검 기록으로 보존하며 V2가 이를 supersede합니다. 독립 QA가 발견한 인접
prediction-range 분할 허점을 maximal-range 검증으로 수정했습니다. Reference scenario 경계는 합치지 않습니다.
Wrapper는 official eTaP/eTaR만 호출합니다. 공식 synthetic oracle helper의 ancillary point-adjust 결과는
수집·보고·과학 지표로 사용하지 않습니다. Range는 inclusive/file-local, 파일 간 병합 없음.

미정 사항: 한 버전 여러 파일의 eTaPR 집계, P1-only secondary range 범위 및 out-of-scope exposure,
empty-input 과학 지표 관례. Wrapper는 per-file만 제공하고 UNRESOLVED_NOT_EXECUTED/undefined로
명시합니다. 이는 공식 구현 불일치가 아니라 후속 공격 실행 전에 해결할 metric contract 항목입니다.

P1 eligibility는 schema/release gate synthetic test만 준비했습니다. Actual scenario record 0개.
공식 scenario/target/mapping authority만 허용하고 prediction fields를 거부합니다.
향후 독립 custodian+DG05+모든 method durable freeze가 필요합니다. Primary는 official P1 scenario이며
contiguous interval을 독립 scenario로 대체하지 않습니다. Version별 보고·primary pooled Recall 금지 유지.
''')
    document('DG03C_EXTERNAL_VERSION_T2_PROVIDER_DECISION_BRIEF_V1.md','''# DG-03C — 아직 승인 가능한 예산이 아님

상태: NOT_READY_BLOCKED_NORMAL_DATA_CUSTODY. 현재 USER_DECISION_REQUIRED provider package로 표시하지 않습니다.
선호 snapshot gpt-5.4-mini-2026-03-17 / Responses API; 이동 alias·자동 fallback 금지.
HAI22와 HAI21 모두 candidate N, GDN evidence, T0, 정확한 payload/token/cost가 아직 미동결입니다.
따라서 calls/tokens/cost ceiling은 UNKNOWN이며 0원/0-token ceiling으로 오표시하지 않습니다.

고정 외부 계획: T2만 pair당 한 portfolio-producing 실행, 최대3회, ACCEPTED 즉시 종료. R=3/T1/T1-B 재실행 없음.
최대 호출 공식은 버전당 3×N입니다. N과 exact prompt가 확보되기 전에 budget을 추정 승인하지 않습니다.
Provider projection은 버전별 train1 구조·STAT·GDN, bounded train2 repair만 허용합니다.
수치정책/역할값·최종답·META tier/선언·train3/4·공격·다른 arm·private path·credential은 금지합니다.
No credential read / capability probe / provider call. 이전 DG03B 승인은 외부 버전에 승계하지 않습니다.

정확한 다음: 정상 컨테이너의 label 열을 schema로만 식별하고 값은 배제하는 projection 범위 확인 →
normal custody → mapping/candidates/GDN/T0 → evidence/prompt freeze → exact DG03C budget.
''')
    panels=list(csv.DictReader((EXP/'PANEL_REGISTRY_V1.csv').open(encoding='utf-8')))
    for row in panels[1:]:
        row['method_policy']='DG04_FINAL_METHOD_LOCK_H0_H4_S0_S3'
        if row['dataset_version']!='23.05':row['normal_authority_policy']='NORMAL_SPLIT_ROLE_POLICY_V2_PENDING_CUSTODY'
    write_csv(EXP/'PANEL_REGISTRY_V2.csv',panels)
    document('PANEL_METHOD_UPDATE_V1.md','''# 미래 Panel 방법 변경

PANEL_REGISTRY_V2는 V1의 미래 method policy만 전향적으로 supersede합니다. Development 첫 행은 동일합니다.
H0 PCA, H1 T0, H2 T2, H3 PCA+T0, H4 PCA+T2. S0 IF, S1 IF+T2, S2 V2A, S3 기존 continuity reference.
Fusion은 같은 file/physical second FAIL, 서로 다른 physical source≥2, base alarm pointwise 보존입니다.
Test1에 소급 적용하지 않습니다. External T0/T2는 아직 존재하지 않습니다.
Primary Scenario Recall/normal false episodes per hour, 기존 secondary metric 목록 유지. 새 fusion/attack metric 없음.
DG03C provider, DG05 attack, DG06 제출 승인은 각각 별개입니다.
''')
    print(json.dumps({'status':blocker['status'],'metadata_features':len(rows),'portable_META':mapping['portable_meta_counts'],'eTaPR':'PER_FILE_PASS'}))


if __name__=='__main__':main()
