# EXP-01 결과 및 후보 정책 처분

상태: `COMPLETE_QA_PASS`

## 결과

- 동결된 12-run schedule: 완료
- 기존 checkpoint 재사용: 12/12
- training 재실행: 0
- arm-blind train3 confirmation: 1회
- train4 fixed-checkpoint intervention: 1회
- primary mask pair: 0
- result hash: `53ee74a8036357dacf18486d4ef562dcdc948ff9e7f71fc23c53be17feb22a7e`

## 후보 정책

사전등록 규칙에 따라 GDN을 VALIDATION V2 primary discovery path에서
제외하고 ablation evidence로 보존한다. primary candidate discovery는
`META_PLUS_STAT`로 동결한다. 결과 관찰 뒤 pair를 재정렬하거나 inclusion
조건을 완화하지 않았다.

## GPU와 실행 효율

호스트의 NVIDIA GeForce RTX 5060 Laptop GPU는 확인됐지만, 동결된
checkpoint와 PyTorch 환경은 CPU authority다. 이번 장기 병목은 GPU tensor
연산이 아니라 반복 전체 시퀀스 검증이었다. `TASK-039D1R` 의미 동일성 검사를
통과한 선형 event extractor와 indexed isolation으로 후처리를 완료했다.

## 주장 경계

이 결과는 normal-only candidate guidance다. GDN의 일반적 무용성, 인과성,
이상탐지 성능, held-out 일반화를 뜻하지 않는다.
