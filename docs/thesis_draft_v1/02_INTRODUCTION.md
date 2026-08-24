# 1. 서론

## 1.1 연구 배경

산업 제어시스템과 CPS는 센서, 제어 명령, actuator feedback이 시간에
따라 상호작용하는 다변량 동적 시스템이다. 이상탐지 모델은 이들 변수의
공동 분포나 예측 오차를 이용해 경보를 발생시킬 수 있다. 그러나 높은
탐지 성능이 곧 사람이 이해할 수 있는 설명을 의미하지는 않는다. 운영자
입장에서는 “이상 점수가 높다”는 사실뿐 아니라 어떤 source 변화 뒤 어떤
target 반응이 기대됐고, 실제 반응이 언제 어떻게 어긋났는지를 알아야
한다.

규칙 기반 설명은 변수, 조건, 시간 관계를 명시적으로 표현할 수 있다는
장점이 있다. 반면 사람이 모든 관계와 임계값을 수작업으로 작성하기는
어렵고, 공정별 도메인 지식 의존도가 높다. LLM은 규칙 구조와 설명을
작성하는 데 유연하지만, 데이터에 근거하지 않은 수치, 실행 불가능한
코드, 불명확한 검증 책임을 만들 수 있다. 특히 LLM이 규칙의 제안자,
수치 결정자, 승인자, runtime 실행자를 동시에 맡으면 재현성과 과학적
통제가 약해진다.

## 1.2 문제의 재정의

본 연구는 LLM이 좋은 규칙을 자유롭게 생성하는지 묻지 않는다. 대신
정상 데이터와 후보 그래프로 탐색 공간을 제한하고, LLM의 역할을 typed
구조 제안으로 한정하며, 수치·유효성·실행을 결정론적 구성요소가 소유할
수 있는지를 묻는다. 이때 규칙은 자연어 설명이 아니라 반복 실행 가능한
과학적 artifact다. 규칙은 source variable, target variable, source
transition, expected response, lag/horizon, parameter reference와 trace
semantics를 가져야 한다.

핵심 설계 원리는 **proposal authority와 validity authority의 분리**다.
graph/metadata/statistics는 후보를 제시하지만 원인을 증명하지 않는다.
LLM은 규칙 형식을 제안하지만 수치와 최종 유효성을 결정하지 않는다.
정상 데이터의 numeric authority가 파라미터 근거를 제공하고,
deterministic verifier가 증거와 계약을 검사한다. runtime은 LLM-free로
동작하며 관측된 만족 trace에만 설명을 결합한다.

## 1.3 연구 목적과 범위

첫째, 정상 CPS 데이터에서 규칙으로 전환 가능한 다변량 시간 관계를
발견·확인한다. 둘째, 제한된 agentic construction과 결정론적 검증을
통해 실행 가능한 규칙을 만든다. 셋째, 규칙 계층이 기준 탐지기와 다른
이벤트 증거를 제공하는지 평가한다. 넷째, 두 단순 fusion 정책이 그
보완성을 추가 detector utility로 전환하는지 검증한다.

본 연구의 주 기여는 새 detector가 아니다. PCA-SPE는 규칙 효용을
평가하기 위한 reference detector다. 또한 graph edge나 rule trace를
인과 관계 또는 root cause로 해석하지 않는다. TSFM과 ARTIST식 segment
selection도 현재 구현 범위 밖이며, held-out 일반화는 확인되지 않았다.

## 1.4 잠정 연구 질문

- **RQ1:** 그래프 유도 후보 발견과 정상 전용 시간 관계 프로파일링은
  CPS 규칙 구성에 유용한 다변량 관계를 식별할 수 있는가?
- **RQ2:** 제한된 LLM 보조 구성과 결정론적 수치·검증 권한을 결합해
  실행 가능하고 사람이 읽을 수 있는 시간 규칙을 만들 수 있는가?
- **RQ3:** 검증된 시간 규칙은 기준 다변량 탐지기와 보완적인 이상 이벤트
  증거를 제공하는가?
- **RQ4:** 단순 결정론적 fusion은 그 보완 증거를 추가 detector
  utility로 전환할 수 있는가?

이 문구는 `PROVISIONAL_PENDING_PROFESSOR_APPROVAL`이며, held-out
일반화 RQ는 답변된 항목으로 추가하지 않는다.

## 1.5 잠정 기여

- **C1:** graph-guided discovery와 normal-only temporal evidence를
  연결한 CPS 규칙 후보 파이프라인.
- **C2:** LLM의 구조 제안과 숫자·유효성·runtime 권한을 분리한 bounded
  agentic construction architecture.
- **C3:** 규칙을 결정론적 수치 증거에 결합하고 satisfaction trace를
  생성하는 verifier/runtime interface.
- **C4:** INNER detector–rule complementarity와 D2 V1/V2의 negative
  fusion evidence를 함께 제시한 실증 분석.

네 기여는 모두 `PROVISIONAL_PENDING_PROFESSOR_APPROVAL`이다.

## 1.6 논문 구성

2장은 관련연구와 본 연구의 차이를 정리한다. 3장은 rule validity와
utility를 분리한 문제를 정의한다. 4장은 후보 발견부터 실행 trace까지의
방법을 설명한다. 5장은 HAI 23.05 P1 실험설계와 파라미터 출처를 제시한다.
6장은 D0/D1/D2 결과와 fusion 실패를 보고한다. 7장은 의미와 설계 교훈을,
8장은 과학적·소프트웨어 한계를, 9장은 결론과 후속 결정사항을 다룬다.
