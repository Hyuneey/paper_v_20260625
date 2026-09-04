# 공격 실행 전 미정 metric binding

기존 eTaPR per-file conformance는 PASS입니다. 다음 세 선택은 frozen 계약으로 도출되지 않아 임의 결정하지 않습니다.

1. 한 버전 여러 파일: per-file only인지, version aggregate인지. Aggregate라면 P/R weighting과 F1 산식 필요.
2. Secondary P1 range scope: OUT_OF_SCOPE/CROSS_PROCESS/UNRESOLVED 시간의 prediction/reference/exposure 처리.
   Primary P1 denominator에서 빠진 공격 시간을 normal로 자동 재분류하지 않습니다.
3. Empty eTaPR: reference-only/prediction-only/both-empty 각각의 값, undefined 처리와 aggregate denominator.

현재 wrapper는 per-file/UNDEFINED_EMPTY_RANGE_INPUT만 제공합니다. 이것은 정상 준비를 막지 않지만
DG05 metric freeze 전에 SCIENTIFIC_DECISION_REQUIRED입니다. Primary scenario denominator0은
NOT_OBSERVED. 공식 scenario가 primary unit이며 interval subdivision·point adjustment·primary pooled Recall 금지.
