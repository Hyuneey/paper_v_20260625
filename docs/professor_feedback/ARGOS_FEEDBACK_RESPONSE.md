# ARGOS 재현 및 확장 연구 피드백 답변

## 피드백 1 - ARGOS를 먼저 재현할 것

현재까지 완료한 범위는 다음과 같습니다.

- ARGOS 현재·과거 소스 이력과 논문 정렬
- 공개 KPI 데이터 한 개 시계열의 결정론적 선택과 변환 이력 기록
- pinned `train-LLM-only` DetectionAgent 프롬프트 재구성
- 승인된 실제 LLM 호출 1회의 규칙 응답 캡처
- 생성 규칙의 구문, 시그니처, 정적 안전성, 의미 AST 감사
- RepairAgent, ReviewAgent, validation selection, 결합 경로의 비실행 소스 감사

아직 완료하지 않은 범위는 규칙 실행, Repair/Review 루프의 실제 효과,
KPI 규칙 단독 성능, detector 단독 성능, detector+rule 결합 성능입니다.
Docker 실행 환경 설치는 연구자 결정에 따라 전체 실험 실행 단계까지
연기했습니다. 따라서 현재 상태는 ARGOS 재현 준비 및 비실행 감사 완료이며,
성능 재현 완료가 아닙니다.

## 피드백 2 - 왜 detector와 rule을 결합하는가

코드에서 `train-combined-fn`은 detector가 놓친 이상 구간을 대상으로 규칙을
구성하고, 이진 출력은 `max(detector, rule)`로 결합합니다. 반대로
`train-combined-fp`는 detector의 오탐 구간을 대상으로 하며
`min(detector, rule)`로 결합합니다.

논문의 해석은 LLM 규칙이 기존 detector를 항상 대체한다고 전제하지 않고,
detector의 FN 또는 FP 오류 방향을 제한적으로 보정하는 신호로 사용한다는
것입니다. 다만 이 결합이 실제로 우월하다는 결론은 detector-only,
rule-only, combined 예측을 동일한 고정 프로토콜에서 실행하기 전에는 내릴
수 없습니다.

## 피드백 3 - LLM 규칙만으로 동작할 수 있는가

현재 증거 수준은 다음과 같습니다.

| 항목 | 상태 |
|---|---|
| 규칙 생성 | 확인 |
| Python 구문과 `inference` 시그니처 | 확인 |
| 정적 안전 정책 통과 여부 | 확인 |
| 컨테이너 내 런타임 동작 | 미확인 |
| KPI 이상 탐지 성능 | 미확인 |

따라서 규칙 단독 방식은 소스상 존재하고 실제 규칙도 한 번 생성했지만,
현재 단계에서 런타임 또는 탐지 성능을 주장할 수 없습니다.

## 피드백 4 - 임계값과 파라미터는 어떻게 정해지는가

두 종류를 분리해야 합니다.

1. 규칙 내부 임계값은 LLM이 Python 코드 안에 직접 작성합니다. pinned ARGOS
   코드가 정상 데이터로 이 값을 별도 최적화하거나 보정하는 절차는 확인되지
   않았습니다.
2. 평가 임계값은 규칙이 만든 연속 점수에 대해 Point-F1, Point-F1-PA,
   Event-F1-PA 유틸리티가 해당 평가 split의 label을 사용해 탐색합니다.

따라서 보고서에 threshold 필드가 있다는 사실만으로 규칙 임계값 자체가
ARGOS 최적화로 학습되었다고 해석하면 안 됩니다. chunk size는 실행 인자로
주어지며, 논문은 데이터셋별 보정을 설명하지만 audited pinned 경로에는 이를
자동 탐색하는 루틴이 없습니다. detector 임계값은 외부 detector artifact의
생성 과정에 속하며 ARGOS driver가 결정하지 않습니다.

## 피드백 5 - 규칙 생성을 통제할 수 있는가

ARGOS는 시스템 프롬프트, label이 포함된 train chunk, 이전 규칙, 실행 오류,
RepairAgent 프롬프트, ReviewAgent의 성능·diff 피드백, validation top-k,
iteration 수로 생성을 유도합니다. chunk size, top-k, 반복 수, 모델, 온도
등 일부 설정은 사용자가 조정할 수 있습니다.

그러나 변수, 연산자, 임계값 출처, 제어 흐름을 강제하는 구조화된 스키마는
없고 핵심 규칙 내용은 provider 출력과 자연어 지시 준수에 의존합니다. 이
한계가 본 연구의 명확한 기회입니다. 즉, 후보 변수와 보정된 수치 파라미터를
명시적으로 제한하고 JSON DSL 및 결정론적 verifier로 승인 권한을 분리하는
다변량 규칙 구성으로 확장할 수 있습니다. 이 확장은 ARGOS E1-E8 실행 증거가
확보된 뒤 비교 가능한 형태로 진행해야 합니다.

## 결론 경계

현재 결과는 ARGOS의 규칙 생성·수정·선택·결합 메커니즘을 코드 수준에서
설명하고 향후 재현 실험을 고정한 것입니다. ARGOS 성능 재현, 규칙 단독의
유효성, detector 결합 우월성, 논문 최종 성능은 아직 검증되지 않았습니다.
