<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=c752d7a6fd77b3de559afb880cb003a45b9cd44fa9ba8113133949ddc6f347f2 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# 47개 후보는 어떻게 42개 실행 관계가 되는가

## 한 문장 답

47개 pair를 정상 train1·train2의 반복 source step과 delayed target response로 검사하고,
선택된 relation만 train3에서 검색·재조정 없이 확인한 뒤, 별도 numeric authority를 붙여
실행 가능하게 만든다.

## 단계별 숫자

| 단계 | 수 | 의미 |
|---|---:|---|
| Candidate pairs | 47 | discovery가 제안한 source-target 조합 |
| Source-direction opportunities | 94 | pair마다 step_up·step_down을 별도로 검사 |
| Fit-supported | 25 contexts / 45 directions | train1·train2 gate 통과 |
| Confirmed | 23 contexts / 42 relations | 고정 identity가 train3 gate 통과 |

## 1. 47개 후보 중 무엇을 검사하는가?

source가 정상 구간에서 충분히 크고 지속적인 step을 만들었을 때 target이 일정 시간 뒤
같은 방향으로 반복 반응하는지 검사한다. 후보는 아직 관계가 아니고, source sign,
target sign, horizon이 정해져야 relation이 된다.

## 2. Source event와 target response

Source event는 직전 5행과 이후 5행 median 차이가 normal-derived threshold 이상이고 양쪽이
안정적일 때 생긴다. 같은 source의 가까운 event는 single-link 10행 cluster로 묶고, 다른
source event가 ±2행 안에 있으면 isolation에서 제외한다.

Target response는 event 전 5행 median을 baseline으로 하고, horizon 뒤 3행 median에서
baseline을 뺀 값이다. 파일 끝의 불완전 window는 버리며 보간하지 않는다.

## 3. Lag/horizon은 무엇이며 왜 여러 개를 보는가?

반응이 즉시 오지 않을 수 있어 1, 5, 10, 30, 60행 지연을 미리 고정해 비교한다. 각
source direction에서 consistency, effect, 짧은 horizon 순으로 하나만 고른다. 선택된
horizon은 이 유한 grid의 규칙상 winner이지 물리적 최적값이 아니다.

## 4. Consistency와 effect

Consistency는 usable event 중 target response가 선택 방향의 normal noise scale을 넘은
비율이다. Effect는 target response median의 절댓값을 target noise scale로 나눈 비율이다.
Support, consistency, effect, 두 fit file의 방향 우세를 모두 통과해야 한다.

## 5. 왜 train3에서 다시 확인하는가?

train1·train2에서 골랐던 relation이 다른 normal file에서도 유지되는지 보기 위해서다.
train3는 source/target/sign/horizon/parameter를 바꾸지 않고 같은 항목만 검사한다. 실패하면
conflict로 남고 다른 horizon이나 방향을 찾지 않는다.

## 6. 23 pair contexts와 42 relations의 차이

한 source-target pair에서 `step_up`과 `step_down`이 각각 별도 relation이 될 수 있다.
그래서 23개의 pair context 안에 42개의 directional relation이 존재한다.

## 7. Numeric authority는 무엇인가?

실행 숫자가 어느 normal split, relation, 계산 함수, artifact, hash에서 왔는지를 함께
고정한 권한이다. LLM은 authoritative number를 정하지 않는다.

Construction 시점에는 relation마다 11개 reference, 총 462개가 있었다. Frozen D1 runtime은
새 version의 normal-only authority에서 relation마다 10개 private role, 총 420개를 사용하고,
horizon은 canonical descriptor에서 사용한다. Focused audit는 공유 420개 value가 E1과 정확히
일치함을 확인했지만, 두 authority identity 자체가 같다는 뜻은 아니다.

## 8. 왜 causal relation이라고 부르면 안 되는가?

정상 데이터에서 반복되는 순서와 방향을 operationalize했을 뿐, intervention이나 물리 법칙,
root-cause를 검증하지 않았다. Held-out 일반화도 아직 확인되지 않았다.

## 다음 파트 전에 이해할 것

1. candidate, fit-supported, confirmed, runtime-bound는 서로 다른 단계다.
2. train3는 재탐색이 아니라 고정 relation의 확인이다.
3. value equality와 authority identity equality는 다르다.
4. relation numeric authority와 D0 PCA-SPE threshold는 별개다.

다음 task는 **HAI-XVER-NORMAL-PREP-001**이다.

## 현재 DG-04 / 외부 준비 Gate

HAI-XVER-NORMAL-PREP-001: APPROVED_WITH_SEPARATED_GDN_EVIDENCE_ROLES.
이전 BLOCKED_GDN_METHOD_CHANGE_REQUIRED의 estimator 역할 선택은 사용자 승인으로 해소됐습니다.
Provider train1 / bounded retrieval train2에는 EXP03B-compatible split-pure GLOBAL 5-row GDN만 사용합니다.
SCI01 split-local event와 seed별 purged validation 교집합의 EVENT 10-row는 AUXILIARY_CORROBORATION_ONLY입니다.
Global/event 융합, event의 provider·retrieval·verifier·candidate 사용, train3/4 또는 numeric policy 기반 event 선택을 금지합니다.
3개 seed 전부 유지; best-seed 선택 없음. 별도 타입과 실제 frozen projector adapter 합성검사 15 PASS 및 독립 scoped QA PASS.
과학적 역할 binding은 완료됐지만 버전별 execution adapter·custody·environment·performance preflight 통합은 남아 있습니다.
현재 GDN scientific runs 0/12, 외부 T0·T2 pack·정확 token/cost 미완료; provider/credential/공격0.
DG-03B_REVISED 승인으로 완료된 EXP03B와 기존 DEC-025 / Stage A / V2A39 / T0 22 / T2 Repeat1 21 Rules / EXP02 / EXP04/05 / PILOT 결과는 불변입니다.
T2 > T1-B는 정상-only 의미 유도 비교에 한정되고 T0보다 우수하지 않습니다.
DG-03C의 현재 gate명 DG-XVER-PROVIDER는 NOT_READY_EVIDENCE_PENDING; DG05 NOT_APPROVED; 교수 package NOT_SUBMITTED; vault SINGLE_COPY_LOCAL_ONLY.
