# VALIDATION V2 진행 현황 — 교수님 검토용 1쪽 요약

## 결론

VALIDATION V2의 공통 기반과 정상 HAI custody가 복구되었고, EXP-01·EXP-01B 및 EXP-02 정상 데이터 실행을 완료했습니다. 주 후보 경로는 META+STAT으로 고정되었으며, EXP-01B의 GDN Prediction-XAI 추가 검증도 동결 기준상 `GDN_ABLATION_ONLY`였습니다. EXP-04의 test1 개발 비교는 아직 시작하지 않았습니다.

## 완료한 것

- PILOT V1과 분리된 VALIDATION V2 버전·artifact·authority 정책
- Formal V4 실행 권한과 fail-closed runtime contract
- D1 prediction의 durable pre-label gate
- development/test/final 역할, event-unit, episode, Recall, FAR/hour contract
- EXP-01 음성 결과와 META+STAT primary discovery 정책 동결
- EXP-01B CUDA 9-run GDN Prediction-XAI 정상 데이터 비교 및 ablation 판정
- EXP-02 37개 normal-only numeric policy 비교와 선택 authority 동결
- stronger detector 후보로 normal-only Isolation Forest 선택 및 고정
- clean checkout·fresh environment에서 비과학적 synthetic rehearsal PASS
- PILOT V1 3,021개 보존 항목 byte identity PASS

## 아직 실행하지 않은 것

EXP-03 provider arm, stronger detector의 EXP-04 prediction, test1 개발 비교, EXP-05 실제 trace 평가는 아직 실행하지 않았습니다. 현재까지 test1·공격 label·test2·held-out 접근과 provider 호출은 모두 0회입니다.

## 현재 필요한 조치

동결된 V2A META+STAT portfolio를 입력으로 EXP-04의 label-blind prediction과 durable freeze를 수행해야 합니다. 모든 방법의 prediction freeze가 끝난 뒤에만 test1을 DEVELOPMENT_ONLY로 열 수 있습니다. EXP-03은 DG-03 provider 승인을 별도로 유지합니다.

## 주장 경계

PILOT V1 수치는 test1의 14개 연속 공격 구간 단위를 이용한 개발·예비 결과입니다. EXP-01B는 normal-only contribution 실험이며 탐지 성능 검증이 아닙니다. Graph-Guided primary/supporting 요건은 현재 실험에서 지지되지 않았고, Agentic 이득·인간 설명 유용성·held-out 일반화는 확인되지 않았습니다.
