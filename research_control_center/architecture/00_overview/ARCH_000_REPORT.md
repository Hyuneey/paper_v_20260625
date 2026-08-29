# 전체 아키텍처 구현 점검

## 1. 한눈에 보는 현재 구조

현재 시스템은 실제 코드와 frozen INNER 결과까지 연결된다. 다만 RCC의 개념도보다 실행 구현은 더 많은 task-specific bridge와 governance 계층을 사용한다. 파일이 존재한다는 사실과 frozen 결과에 사용됐다는 사실을 분리했다.

## 2. 실제 코드 기준 전체 흐름

P1의 frozen 후보 universe에서 META/STAT/GDN이 독립 후보 증거를 만들고, unscored union과 normal-only relation profiling을 거쳐 construction evidence가 생성된다. T0/T1/T1-B/T2는 task verifier를 통과하지만, utility의 COMMON-42에는 T0/T1/T1-B의 executable equivalence가 연결되고 T2는 포함되지 않는다. D1은 Utility V4 descriptor와 private numeric authority를 사용하는 real bridge로 실행됐다. D0은 별도의 PCA-SPE bridge이며, D2는 frozen D0/D1 prediction만 소비한다.

## 3. Input → Process → Output

각 edge는 `ARCH_000_DATAFLOW.csv`에 근거와 함께 기록했다. 직접 source edge를 찾지 못한 연결은 `UNKNOWN`으로 남겼다. 특히 provenance→split, representative split guard→frozen bridges, task verifier→COMMON-42는 직접 함수 호출보다 artifact/policy 매개 연결이다.

## 4. 핵심 Scientific Core

후보 탐색, 관계 profiling, construction evidence, bounded construction arms, executed task verifier, real D1 runtime, D0/D2, episode/event metric이 핵심이다. GDN edge는 후보 증거이며 인과 또는 고유 기여 검증이 아니다. T2 실행은 있었지만 현재 cohort에서 feedback action은 0이었다.

## 5. Governance / Reporting Layer

Custody, split policy, authorization, freeze, receipt, integrity audit는 과학 연산과 분리된 통제 계층이다. Professor/thesis/RCC 문서는 frozen public-safe metadata의 소비자이며 결과 생산자가 아니다.

## 6. 실제 실행된 경로

Candidate discovery, profiling, construction, COMMON-42 utility preparation, D0, D1, D2 V1/V2와 metric 경로는 frozen evidence로 실행을 추적할 수 있다. Explanation renderer는 구현·테스트됐지만 frozen D1 결과 경로의 사용은 찾지 못했다.

## 7. Frozen Result까지 연결된 경로

D0는 persistent prediction-before-label까지 명확하다. D1은 label-blind prediction object가 label보다 먼저 만들어지고 검증됐지만 D0와 같은 public-file persistence 문구로 강화하면 안 된다. D2 V1 frozen 결과는 authorized recovery entrypoint로 완성됐고, D2 V2 integrity PASS는 결과 재실행 없는 composite completion이다.

## 8. 구현돼 있지만 실행되지 않은 부분

Canonical RuntimeTraceV1과 explanation renderer는 현재 canonical vertical slice에는 연결되지만 frozen D1 bridge에서 직접 사용되지 않았다. OUTER는 실행 code/governance가 있으나 blocker만 존재하며 scientific result는 없다. Fresh-machine reproduction도 미완료다.

## 9. Legacy / Superseded / Dead-path 후보

Legacy DSL/verifier/runtime/e2e와 ARGOS reproduction은 current v6 core와 분리해야 한다. Generic universe와 frozen C0 authority, canonical/task verifier, canonical/synthetic/real runtime처럼 중복된 계층은 삭제 대상이 아니라 deep review 대상이다.

## 10. 문서와 실제 코드의 차이

총 15개 mismatch를 기록했다. Critical은 0이며 High 8, Medium 6, Low 1이다. 가장 큰 차이는 executed representative symbol, T2의 utility 제외, two-stage numeric authority, typed trace/explanation의 frozen-result 부재다.

## 11. 현재 가장 중요한 Architecture Risk

서로 다른 canonical/task-specific 표현과 runtime/verifier 계층이 의미상 동일하다고 가정될 위험이 가장 크다. Frozen 결과 자체가 추적 불가능한 것은 아니지만, 다음 deep review에서 계약 변환과 authority 경계를 확인해야 한다.

## 12. 앞으로 깊게 볼 Part

`DEEP_REVIEW_INDEX.md`의 ARCH-001~011 순서로 진행한다. 첫 단계는 Data / Provenance / Split Governance이며, 본 감사에서는 어떠한 scientific code도 수정하지 않았다.
