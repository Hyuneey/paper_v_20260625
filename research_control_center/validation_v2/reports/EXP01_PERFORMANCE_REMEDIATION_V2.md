# EXP-01 장기 병목 복구 기록

상태: `COMPLETE_QA_PASS`

## 결론

완료된 12개 GDN 학습 체크포인트는 재실행하지 않는다. 중단 시점의 병목은
GDN 학습이 아니라 관계 확인 후처리의 반복 전체 시퀀스 검증이었다. 기존
`TASK-039D1R`에서 의미 동일성·경계값·복잡도 검사를 통과한 다음 두 어댑터를
VALIDATION V2 EXP-01 경로에 연결했다.

- `extract_sustained_step_events_linear_v1`: 전체 시퀀스 유한값 검증 1회,
  이후 인덱스별 10개 고정 창만 평가한다.
- `classify_all_source_isolation_indexed_v1`: 다른 source event 인덱스를 정렬한
  뒤 이진 탐색한다.

관계식, threshold, horizon, refractory window, isolation radius, 후보 집합,
seed, 모델, 데이터, split, preregistration은 변경하지 않았다.

## 실행 결과

- 12/12 checkpoint를 byte/state/authority로 복구했다.
- training을 다시 실행하지 않았다.
- 최적화된 post-processing은 `COMPLETE_PENDING_INDEPENDENT_QA`로 종료했고,
  후속 독립 QA가 PASS했다.
- primary mask pair는 0개였다.
- 사전등록 규칙에 따라 GDN은 ablation으로 보존하고 primary discovery path는
  `META_PLUS_STAT`로 동결한다.
- result hash는
  `53ee74a8036357dacf18486d4ef562dcdc948ff9e7f71fc23c53be17feb22a7e`다.

## 중단된 실행의 처리

- 12/12 checkpoint 학습 완료
- partial checkpoint 0
- public EXP-01 result 0
- train1/train2/train3만 열린 뒤 후처리에서 사용자 승인에 따라 중단
- test1/test2/held-out/label 접근 0

중단 후 checkpoint 복구 영수증은 `POST_INTERRUPTION_RECOVERY_SNAPSHOT`으로
명시한다. 이는 checkpoint 생성 시점의 외부 anchor가 아니다. 각 파일의 byte
hash, canonical tensor-state hash, 원래 training code authority, training config,
12-run schedule을 모두 다시 검사한 뒤 post-processing 전용 입력으로만 사용한다.

## 재개 경로

`resume_exp01_postprocessing_v2`는 다음만 수행한다.

1. 기존 12개 checkpoint byte/state/authority replay
2. checkpoint weight에서 graph identity replay
3. 기존 META/STAT authority replay
4. arm-blind train3 relation confirmation
5. preregistered primary-mask freeze
6. 필요한 경우 train4 fixed-checkpoint intervention

이 함수에는 `train_exp01_seed_v2` 호출이 없으며 학습을 수행할 수 없다.

## 의미 보존 근거

- 기존 TASK-039D1R event parity fixtures: PASS
- 기존 TASK-039D1R isolation parity fixtures: PASS
- 구조 복잡도 검사: event extraction `O(N)`, isolation `O(E log E)`
- canonical `continuous_step_protocol_v1.py`: 변경 없음
- PILOT V1: 변경 없음

## 보수적 경계

프리레지스터된 `EXP01_FROZEN_CONTRACT_CONFLICT_PRIMARY_MASK_2_OF_3_VS_SHARED_ALL_SEEDS`
조건이 발생하면 mask를 임의로 줄이지 않는다. terminal receipt를 남기고 GDN
기여를 `UNRESOLVED_FAIL_CLOSED`로 유지한다.
