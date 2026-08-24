# 부록 E — 재현성과 연구 상태

## 재현 가능한 범위

- HAI 23.05 P1 데이터 범위와 split 역할이 고정돼 있습니다.
- 144개 후보쌍, 관계 발견 경로, 관계 acceptance policy가 기록돼
  있습니다.
- 42개 verified temporal rules와 정상 데이터 수치 참조가 고정돼
  있습니다.
- D0/D1/D2 V1/D2 V2의 INNER predictions와 metrics가 동결돼 있습니다.
- 규칙 실행은 LLM-free이며 동일 입력에 동일 trace를 생성합니다.
- 이번 제출본은 기존 동결 결과만 인용했고 과학 실행이나 파라미터
  변경을 하지 않았습니다.

## 공개·비공개 경계

공개 문서에는 aggregate metrics, 구현 상태, 관계 역할과 sanitized
trace만 포함합니다. 원시 공정 데이터, 민감한 규칙 수치, 모델 내부값,
local data location은 포함하지 않습니다.

## OUTER 상태

사전등록된 held-out 평가는 test2 feature bytes와 labels를 읽기 전에
중단됐습니다. prediction과 metric이 없으므로 OUTER 과학 결과가 아니며,
일반화는 확인되지 않았습니다. 새로운 held-out 연구는 자동 재시도가
아니라 교수님 승인과 별도 사전등록이 필요한 선택지입니다.

## 현재 논문 작성에 사용할 수 있는 근거

1. 방법과 시스템 설계
2. 42개 verified relation/rule portfolio
3. INNER 이벤트 수준 detector–rule complementarity
4. rule-only false-alarm limitation
5. 두 deterministic fusion policy의 negative evidence
6. 명시적 미구현·미확인 범위

상세 개발용 reproducibility index는
[기존 전체 문서](../../professor_first_results_v1/08_REPRODUCIBILITY_AND_CODE_STATUS.md)에
분리해 두었습니다.
