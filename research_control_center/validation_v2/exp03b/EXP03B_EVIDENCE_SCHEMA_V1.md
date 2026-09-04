# EXP-03B evidence schema

ProviderTrain1EvidencePackV1은 train1 전용 immutable structural/predictive 타입에서만 생성합니다. Hidden train2/3/4 객체와 혼합한 뒤 필드를 삭제하는 경로는 금지합니다.
구조 행: source direction, target direction, horizon, support, consistency, effect, opposite consistency, slice ID.
수치 행: NUM alias와 train1 aggregate opportunity/PASS/FAIL/ABSTAIN·coverage·false-firing metrics 및 slice ID. 원시 role 값은 private numeric_roles authority에만 있습니다.
STAT은 train1 단독 correlation, GDN은 TRAIN1_ONLY 고정 checkpoint/purged validation 전용입니다. 방향/horizon의 모든 대안을 보이며 최종 정답·best marker는 없습니다.
정확한 closed serialized schema와 타입/범위 검사는 exp03b_prompt.py 및 exp03b_firewall_v1.py가 실행합니다. JSON output schema는 별도 EXP03B_OUTPUT_SCHEMA_V1.json입니다.
