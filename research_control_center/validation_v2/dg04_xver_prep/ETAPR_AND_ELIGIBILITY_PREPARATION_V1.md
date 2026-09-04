# eTaPR / eligibility 준비

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
