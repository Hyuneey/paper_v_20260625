# 47개 후보는 어떻게 실제 관계가 되는가

Scientific authority: `origin/research-v6-thesis-checkpoint@2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## 1. 후보와 관계의 차이

47개 candidate pair는 META·STAT·GDN이 “더 검사할 가치가 있다”고 제안한 source-target 조합이다. 아직 source 변화 부호, target 반응 부호, 지연 horizon이 정해지지 않았다. 실제 profiling은 pair마다 `step_up`과 `step_down`을 따로 보므로 94개 directional opportunity를 검사한다.

그 결과는 한 번에 42개가 되지 않는다. train1·train2에서 25개 pair context, 45개 direction이 fit gate를 통과하고, 고정된 이 기록만 train3로 넘어간다. train3에서 42개 direction이 확인되어 23개 pair context가 남고, 3개 direction은 conflict가 된다.

## 2. Source event란 무엇인가

각 시점 `t`에서 source의 직전 5행 median과 이후 5행 median을 비교한다. 차이의 절댓값이 normal train1·train2에서 정한 step threshold 이상이고, 양쪽 window 모두 최소 4/5가 각 median 주변 tolerance 안에 있어야 sustained step 후보가 된다. 차이 부호가 `step_up` 또는 `step_down`을 정한다.

같은 source에서 가까운 후보는 file-local single-link 방식으로 10행 간격까지 묶고, 가장 큰 변화 하나만 남긴다. 그 뒤 다른 11개 source의 event가 `t±2` 안에 있으면 isolated event로 쓰지 않는다. 이 절차는 causal intervention을 찾는 것이 아니라 정상 구간에서 비교적 분리된 반복 변화 context를 만든다.

## 3. Target response는 어떻게 측정하는가

source event 시점의 target baseline은 `median(target[t-5:t])`이다. horizon `h` 뒤 3행 median에서 baseline을 뺀 값이 response다. horizon은 1, 5, 10, 30, 60행이다. 파일 끝에서 완전한 window가 없으면 right-censor하고 보간하지 않는다.

response가 target normal noise scale보다 클 때만 `increase`, 음의 scale보다 작을 때만 `decrease`로 일치한다. 그 사이 값은 neutral이고 어느 방향에도 일치하지 않는다.

## 4. Horizon은 어떻게 정하는가

각 source direction마다 target response sign 2개와 horizon 5개, 총 10개 조합을 평가한다. train1과 train2 각각에서 선택 방향 consistency가 반대 방향보다 엄격히 커야 ranking 후보가 된다. 이후 pooled consistency, robust effect, 짧은 horizon, 방향 이름 순서로 하나를 고른다.

중요하게도 하나를 먼저 고른 뒤 gate를 적용한다. 그 winner가 실패해도 2등 horizon으로 돌아가지 않는다. train3에서도 horizon을 바꾸지 않는다. 따라서 “주어진 유한 후보와 metric에서 선택된 horizon”이지 물리적으로 최적임을 증명한 horizon은 아니다.

## 5. Support / Consistency / Effect

- **Support**: isolated source event 중 선택 horizon의 target window가 완전한 수. fit은 합계 20 이상, train1과 train2 각각 5 이상이어야 한다.
- **Consistency**: 선택 target 방향으로 normal noise scale을 넘은 response 수를 usable response로 나눈 값. pooled 0.70 이상, 각 fit file 0.60 이상이다.
- **Effect**: pooled target response median 절댓값을 target noise scale로 나눈 비율. fit 기준은 2.0 이상이다.

세 조건과 file별 방향 우세를 모두 만족해야 한다.

## 6. train1·train2의 역할

train1·train2는 source threshold/tolerance, target scale, event evidence, target sign, horizon을 정하는 normal fit 구간이다. 두 파일은 window 계산 때 합치지 않는다. file별 support와 방향 consistency를 보존한 뒤, response만 pooled statistic에 사용한다. candidate arm 정보는 결과가 freeze될 때까지 숨겨 동일 pair에 같은 profiling 결과를 적용한다.

## 7. train3의 역할

train3는 새 search가 아니라 confirmation이다. source/target, source sign, target sign, horizon, fit parameter reference, window/refractory/isolation 정책이 모두 고정된다. support 5 이상, 선택 consistency가 반대보다 큼, consistency 0.60 이상, effect 1.0 이상을 모두 만족해야 한다. retuning, alternate horizon, opposite-direction search, fallback, 새 relation 추가는 없다.

## 8. 47개가 어떻게 최종 관계 집합이 되는가

정확한 lineage는 다음과 같다.

`47 pairs → 94 source directions → 25 fit-supported contexts / 45 directions → 23 train3-confirmed contexts / 42 directions`

최종 relation identity에는 pair뿐 아니라 source step sign, target response sign, selected horizon, fit/confirmation hash가 포함된다. 그래서 한 pair에서 두 source sign이 모두 확인될 수 있다.

## 9. Numeric authority란 무엇인가

Numeric authority는 숫자 자체뿐 아니라 그 숫자가 어느 normal split, relation, 계산 함수, artifact, hash에서 왔는지를 함께 고정하는 권한이다. 숫자를 설명 문장에 적었다고 authority가 되지 않으며, LLM이 제안한 숫자도 authority가 아니다.

## 10. Rule 생성에 쓰는 숫자

E1 construction evidence는 42개 relation마다 11개 reference, 총 462개 binding을 만들었다. source threshold, stability tolerance, target scale, selected horizon, 7개 window/event constant가 포함된다. T0/T1/T1-B/T2는 모두 이 reference-bound evidence를 사용했고 raw value나 arbitrary literal을 사용할 수 없었다. 이 authority는 construction-only였다.

## 11. 실제 Runtime에 쓰는 숫자

Frozen D1은 historical E1 private registry를 직접 실행하지 않았다. 별도로 materialize하고 독립 감사한 `TASK039E3_UTILITY_NORMAL_ONLY_AUTHORITY_V1`을 사용했다. 42개 relation × 10개 private role = 420개 record이며, selected horizon은 COMMON-42 canonical descriptor에 남아 있다. 추가 6개 source-census record는 다른 세 source의 isolation census 전용이다.

## 12. 두 숫자는 어떻게 연결되는가

두 계층은 같은 frozen normal split과 calibration 함수를 따르며, 후속 focused private audit에서 공유하는 420개 role value가 E1과 정확히 일치하고 mismatch가 0임을 확인했다. 그러나 artifact authority와 reference identity는 의도적으로 새 version이며 historical identity를 복원하지 않았다. 즉 **값의 정확한 동등성**과 **권한 identity의 동일성**은 다른 주장이다. V4는 relation binding, role, normal input, method, record와 registry hash를 모두 검사한다.

## 13. 현재 보장할 수 있는 것

- normal train1·train2에서 fit하고 train3에서 고정 relation을 확인했다.
- candidate, fit-supported, confirmed, executable authority 단계가 분리돼 있다.
- runtime 관련 값과 horizon은 relation·method·split·artifact·hash로 추적 가능하다.
- frozen D1은 caller literal이나 LLM number가 아니라 새 normal-only authority를 사용했다.

## 14. 아직 보장할 수 없는 것

- relation이 물리적으로 참이거나 causal하다는 것
- 선택 horizon이나 numeric criteria가 과학적으로 최적이라는 것
- 420개 공유 value의 equality를 근거로 historical construction authority와 runtime authority 자체가 동일하다고 말하는 것
- 현재 relation set이 held-out 데이터에 일반화한다는 것

또한 profiler의 “seconds”는 frozen 1초 sampling contract 아래 row offset으로 구현된다. 함수 자체가 timestamp continuity를 다시 확인하지 않는다는 점은 향후 reproducibility audit에서 다뤄야 한다.
