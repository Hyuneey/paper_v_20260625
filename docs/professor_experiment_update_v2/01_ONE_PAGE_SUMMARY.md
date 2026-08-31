# VALIDATION V2 진행 현황 — 교수님 검토용 1쪽 요약

## 결론

VALIDATION V2의 공통 기반과 실험별 사전등록·합성 검증은 완료되었습니다. 그러나 현재 작업 환경에는 승인된 정상 HAI 입력의 custody binding이 없으므로, EXP-01·EXP-02·EXP-04·EXP-05의 과학 실행은 시작하지 않았습니다. 이는 부정적 실험 결과가 아니라 입력 권한이 없는 상태에서 fail-closed로 멈춘 것입니다.

## 완료한 것

- PILOT V1과 분리된 VALIDATION V2 버전·artifact·authority 정책
- Formal V4 실행 권한과 fail-closed runtime contract
- D1 prediction의 durable pre-label gate
- development/test/final 역할, event-unit, episode, Recall, FAR/hour contract
- EXP-01, EXP-02, EXP-03, stronger detector, EXP-04, EXP-05 사전등록과 합성 테스트
- stronger detector 후보로 normal-only Isolation Forest 선택 및 고정
- clean checkout·fresh environment에서 비과학적 synthetic rehearsal PASS
- PILOT V1 3,021개 보존 항목 byte identity PASS

## 아직 실행하지 않은 것

EXP-01, EXP-02, EXP-03 provider arm, stronger detector fit, EXP-04, EXP-05의 실제 과학 데이터 실행은 모두 0회입니다. test1·test2·held-out 접근과 provider 호출도 0회입니다.

## 현재 필요한 조치

VALIDATION V2에 사용할 승인된 정상 HAI custody binding을 복원하거나 새로 발급해야 합니다. 이후 frozen preregistration 그대로 EXP-01과 EXP-02를 시작합니다. EXP-03은 natural cohort와 정확한 call/token budget이 정해진 뒤 DG-03에서 별도 provider 승인을 받습니다.

## 주장 경계

PILOT V1 수치는 test1의 14개 연속 공격 구간 단위를 이용한 개발·예비 결과입니다. 통계적 독립성, held-out 일반화, Graph-Guided 기여, Agentic 이득, 인간 설명 유용성은 확인되지 않았습니다. 이번 패키지는 구현·준비도 보고이며 새로운 V2 성능 결과 보고가 아닙니다.
