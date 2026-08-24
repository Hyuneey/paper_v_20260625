# 논문 초안 상태와 미결정 사항

## 현재 상태

- 기준: canonical remote checkpoint `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`
- 작업 유형: 기존 동결 근거의 논문 서술화
- 과학 실행 및 test2 접근: 없음
- 중앙 해석: `RULE_SIGNAL_PRESENT_BUT_CURRENT_FUSION_UTILITY_UNSUPPORTED`
- 권고 경로: `THESIS_FIRST_PENDING_PROFESSOR_FEEDBACK`

## 잠정 제목

**설명 가능한 다변량 시계열 이상탐지를 위한 그래프 유도 에이전틱 규칙 구성과 결정론적 검증**

영문 작업 제목은 *Graph-guided Agentic Rule Construction with
Deterministic Verification for Explainable Multivariate Time-Series Anomaly
Detection*이다. 제목과 아래 RQ·기여는 모두
`PROVISIONAL_PENDING_PROFESSOR_APPROVAL`이다.

## 잠정 연구 질문

- **RQ1.** 그래프 유도 후보 발견과 정상 전용 시간 관계 프로파일링은
  CPS 규칙 구성에 유용한 다변량 관계를 식별할 수 있는가?
- **RQ2.** 제한된 LLM 보조 구성, 결정론적 수치 권한, 결정론적 검증을
  결합해 실행 가능하고 사람이 읽을 수 있는 시간 규칙을 만들 수 있는가?
- **RQ3.** 검증된 시간 규칙은 기준 다변량 탐지기와 보완적인 이상 이벤트
  증거를 제공하는가?
- **RQ4.** 단순한 결정론적 결합 정책은 이 보완 증거를 기준 탐지기 대비
  추가 효용으로 전환할 수 있는가?

held-out 일반화는 답변된 RQ가 아니며 현재 주장 범위에 포함하지 않는다.

## 잠정 기여

1. 그래프 유도 관계 발견과 정상 전용 시간 증거 구축 파이프라인.
2. LLM이 구조만 제안하고 수치·유효성·runtime 판단은 소유하지 않는
   제한된 에이전틱 규칙 구성 아키텍처.
3. 규칙을 수치 증거에 결합하고 만족 trace를 생성하는 결정론적 검증 및
   실행 인터페이스.
4. INNER에서 detector–rule 이벤트 보완성을 보이면서 두 결정론적 fusion의
   실패도 함께 제시하는 D0/D1/D2 실증 분석.

## 교수님 확인이 필요한 네 결정

### [PROFESSOR_DECISION_1_CONTRIBUTION]

- 권고 기본안: 기여를 그래프 유도 규칙 구성과 결정론적 검증으로 확정.
- 대안: 결합 탐지 성능 향상을 필수 기여로 요구.
- 변경되는 장: 제목, 초록, 서론, RQ, 결론.
- 과학적 영향: 대안은 현재 결과로 지지되지 않아 새 연구가 필요함.

### [PROFESSOR_DECISION_2_EXPLANATION_INTERFACE]

- 권고 기본안: 실행 규칙과 satisfaction trace를 주 설명 인터페이스로 사용.
- 대안: ARTIST식 segment proposal/selection을 추가.
- 변경되는 장: 관련연구, 방법, 설명 평가, 한계.
- 과학적 영향: 대안은 새 구현과 별도 설명 유용성 평가를 요구함.

### [PROFESSOR_DECISION_3_OUTER_REQUIREMENT]

- 권고 기본안: INNER 범위로 논문을 먼저 작성.
- 대안: 새 사전등록을 거친 독립 OUTER 연구를 먼저 수행.
- 변경되는 장: 실험설계, 결과, 일반화 논의.
- 과학적 영향: 대안은 일반화 근거를 강화할 수 있으나 현재 시도를 자동
  재개할 수 없고 새 승인·설계가 필요함.

### [PROFESSOR_DECISION_4_DETECTOR_BASELINE]

- 권고 기본안: PCA-SPE를 명시적 reference detector로 유지.
- 대안: 강한 다변량 detector 하나를 추가.
- 변경되는 장: 관련연구, 실험설계, 비교결과, 논의.
- 과학적 영향: 대안은 외적 설득력을 높일 수 있으나 새 실험이며 현재
  규칙 구성 기여의 성립 조건은 아님.
