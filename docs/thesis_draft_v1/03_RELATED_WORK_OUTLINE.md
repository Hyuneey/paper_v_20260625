# 2. 관련연구 구조 초안

이 장은 구조와 비교축을 먼저 고정한 초안이다. 저장소에서 확인되지 않은
논문명·저자·연도·DOI는 기입하지 않으며 `[BIB-VERIFY-*]`로 표시한다.

## 2.1 다변량 시계열 이상탐지

- reconstruction, forecasting, density/representation 기반 TSAD의 기본
  분류를 정리한다. `[BIB-VERIFY-TSAD-SURVEY]`
- 높은 탐지 성능과 해석 가능한 변수·시간 관계 제공이 별개임을 논의한다.
- 본 연구의 PCA-SPE는 제안 모델이 아니라 투명한 reference detector임을
  명확히 한다. `[BIB-VERIFY-PCA-SPE]`

비교축: 탐지 목적, 정상 전용 학습, score 설명 가능성, event metric,
held-out 검증 범위.

## 2.2 그래프 기반 TSAD와 GDN

- 변수 간 learned graph를 이용한 다변량 모델의 동기를 정리한다.
- GDN은 후보 graph evidence로 사용되며, edge를 인과 또는 root cause로
  해석하지 않는다. 저장소에는 pinned upstream mapping과 fidelity audit가
  존재한다. `[BIB-VERIFY-GDN-CANONICAL]`
- 본 연구의 차이: GDN score 자체를 최종 탐지 설명으로 쓰지 않고,
  candidate universe 안에서 관계 profiling 대상으로 제한한다.

## 2.3 설명 가능한 TSAD

- feature attribution, reconstruction-error decomposition, counterfactual,
  prototype, rule/trace 설명을 비교한다. `[BIB-VERIFY-XTSAD-SURVEY]`
- 본 연구는 attribution score가 아니라 source–target–lag–expected response
  구조와 satisfaction trace를 제공한다.
- human usefulness는 평가하지 않았으므로 “설명 가능”은 실행 가능한
  관계 근거의 가시성 범위로 한정한다.

## 2.4 CPS invariant 및 rule 기반 이상탐지

- 정상 운전 invariant, 물리·논리 관계, 시간 규칙 기반 탐지를 정리한다.
  `[BIB-VERIFY-CPS-INVARIANT]`
- 사람이 작성한 invariant와 데이터 기반 calibration의 장단점을 비교한다.
- 본 연구는 normal-only evidence, bounded rule schema, deterministic verifier를
  결합하지만 물리 법칙이나 인과 invariant를 주장하지 않는다.

## 2.5 ARGOS와 detector–rule 보완

저장소의 ARGOS 검토는 `partial_methodological_support`다. bounded revision을
통한 runtime recovery와 일부 Review 개선은 확인됐지만, 전체 aggregator의
일관된 우월성이나 sealed confirmation은 없다. 본 연구는 이 검토에서
드러난 자유 Python, LLM 수치, selection/leakage, FP correction 위험을
동기로 삼되 ARGOS 코드를 production dependency로 사용하지 않는다.

비교축: 규칙 생성 자유도, numeric authority, deterministic validation,
runtime containment, detector correction 방향, no-op, evaluation leakage.
정확한 ARGOS 서지는 `[BIB-VERIFY-ARGOS-CANONICAL]`에서 확인한다.

## 2.6 LLM 보조 규칙 생성

- 자연어/코드 기반 규칙 생성, constrained decoding, schema-guided output을
  정리한다. `[BIB-VERIFY-LLM-RULE-GENERATION]`
- 본 연구의 차이는 LLM이 parameter value와 final validity를 소유하지
  않으며, runtime에도 참여하지 않는다는 점이다.
- T0/T1/T1-B/T2는 동일 계약과 총 call budget을 공유하도록 설계된다.

## 2.7 Agentic verifier 및 repair 시스템

- generator–critic/verifier–repair 반복 구조를 정리한다.
  `[BIB-VERIFY-AGENTIC-VERIFICATION]`
- repair 성공을 performance 향상과 동일시하지 않는 연구 공백을 제시한다.
- 본 결과에서 T2는 39/42 accepted, 3 no_rule였고 feedback action은 0이므로
  agentic repair의 성능 최적화 주장은 하지 않는다.

## 2.8 시간/구간 localization과 ARTIST

- anomaly segment proposal, temporal localization, subsequence explanation을
  구분한다. `[BIB-VERIFY-ARTIST-CANONICAL]`
- 본 연구의 transition+horizon localization은 ARTIST식 learned segment
  selection과 동일하지 않다.
- 교수 결정에 따라 ARTIST 비교는 related-work limitation으로 남기거나
  새 method/evaluation 항목으로 확장한다.

## 2.9 TSFM

- time-series foundation model의 representation과 anomaly detection 활용을
  개괄한다. `[BIB-VERIFY-TSFM-SURVEY]`
- 현재 연구에는 TSFM 구현·실험이 없으며 효과 주장을 하지 않는다.
- 교수 결정 전에는 관련연구의 향후 비교 가능성으로만 다룬다.

## 2.10 위치 정리

본 연구의 위치는 “새 graph detector”나 “자유 자연어 설명기”가 아니다.
graph-guided candidate curation, normal-only relation evidence, bounded rule
construction, deterministic verification, LLM-free execution을 하나의
검증 가능한 경로로 연결하고, 그 규칙의 detector complementarity와 fusion
실패를 분리해 평가하는 데 있다.
