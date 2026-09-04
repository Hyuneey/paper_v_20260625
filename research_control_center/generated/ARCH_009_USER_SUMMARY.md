<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=0679baf23b38ac292c9ec0334debce0277b7bbb1b7d17558ff90374c40286fe3 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# D2에서 Detector와 Rule을 어떻게 합쳤는가

## 1. 왜 D0와 D1을 합치려고 했는가?

D0가 놓친 3개 attack-event unit에 D1은 모두 반응했다. 그래서 D0 alarm은 지키면서 신뢰할 만한
D1 evidence만 추가하면 detector miss를 줄일 수 있는지 시험했다. D2는 이 질문을 위한
deterministic fusion-policy pilot이다.

## 2. D2 V1은 무엇인가?

같은 `decision_physical_row_index`, 즉 같은 1초 decision row에서 alarm을 낸 D1 source를 센다.
같은 source의 여러 rule은 한 번만 세고, 서로 다른 source가 2개 이상이면 D1 alarm을 추가한다.
D0가 이미 alarm이면 항상 유지한다.

## 3. 왜 distinct sources >= 2를 쓰는가?

한 source의 여러 relation record가 우연히 중복되어도 여러 독립 source evidence처럼 세지 않기 위한
frozen corroboration contract다. 이 threshold가 과학적으로 최적이라는 뜻은 아니다.

## 4. “same-second”는 정확히 무엇인가?

D1 record의 `decision_physical_row_index`가 정확히 같은 경우다. Source trigger 시점이나 attack
episode 전체가 아니다. Rolling window나 tolerance도 없다.

## 5. D2 V2는 V1과 무엇이 다른가?

V2는 D1 alarm을 한 row에서만 보지 않고 relation의 frozen native horizon 끝까지 active token으로
유지한다. 그 시간에 동시에 active한 서로 다른 source가 2개 이상이면 추가한다. D0 preservation과
source threshold 2는 그대로다.

## 6. native horizon/persistence는 실제 무엇인가?

Alarm decision index가 `i`, frozen relation horizon이 `h`라면 token은 `i <= t <= i+h`에서 active다.
별도의 연속 alarm 횟수 threshold나 learned persistence model은 없다.

## 7. D1은 3개를 잡았는데 왜 D2는 못 잡았는가?

V1에서는 두 unit의 여러 source alarm이 같은 row에 맞지 않았고 한 unit은 source가 하나뿐이었다.
V2는 temporal activity를 늘렸지만 frozen result상 세 unit 어디에도 추가 alarm을 admit하지 못했다.
Single-source unit은 정책상 제외되며, 나머지 두 unit의 V2 상세 원인은 public frozen trace만으로는
확정할 수 없다. 핵심은 **D1 response와 D2 admission은 다른 조건**이라는 점이다.

## 8. D2 V1 결과는 D0보다 좋은가?

현재 pilot metric으로는 아니다. D0와 같은 11/14였고 Normal FAR은
0.7056194750975128로 D0의 0.4939336325682589보다 높았다. Recovery는
0/3였다.

## 9. D2 V2 결과는 D0보다 좋은가?

아니다. V2도 11/14, recovery 0/3였고 Normal FAR은
6.915070855955625로 더 높았다. 이는 현재 test1 descriptive result이며
새로운 통계 비교를 한 것이 아니다.

## 10. 왜 V2는 독립 검증이 아닌가?

V1 negative result와 test1 diagnostic이 V2 문제 설정을 informed했고 동일 test1에서 평가됐다.
V2 결과 자체는 freeze 전에 보지 않았지만 validation/final-test가 분리되지 않았으므로
`TEST1_INFORMED_DEVELOPMENT`이다.

## 11. 현재 Detector+Rule에 대해 무엇을 말할 수 있는가?

D0/D1 response diversity는 pilot에서 관찰됐다. 하지만 현재 V1/V2는 그 diversity를 incremental
attack-event recall로 바꾸지 못했고 normal FAR을 늘렸다. 이것은 현재 두 policy의 negative pilot
result이지 Detector+Rule 전체가 쓸모없다는 증거가 아니다.

## 12. 앞으로 무엇을 검증해야 하는가?

더 큰 evaluation scope, event-unit definition freeze, validation/final-test 분리, final test 전에 고정된
fusion policy, stronger detector, durable upstream prediction, preregistered incremental Recall/FAR와
D0-miss recovery가 필요하다.

기억할 한 문장: **D1의 다른 response가 관찰됐지만, 현재 V1/V2 gate는 이를 recall 증가로 바꾸지
못했고 V2는 독립 검증이 아니다.**

다음 task는 **DG-XVER-PROVIDER**이다.

## 현재 DG-04 / 외부 준비 Gate

HAI-XVER-NORMAL-PREP-001: 정상-only 실행 완료, 독립 최종 QA PASS. DG-XVER-PROVIDER에서 정지합니다.
HAI22/HAI21 GDN은 각각6회, 총12회입니다. GLOBAL5는 train1 provider / train2 retrieval, EVENT10은 보조 분석 전용이며 융합·후보·verifier·T0·숫자·guard 사용을 금지합니다.
HAI22 T0: 13 Rules/12 pairs. HAI21 T0: 7 Rules/5 pairs. 모두 HELDOUT_CANDIDATE, 공격 검증·production 결과가 아닙니다.
T2 provider/retrieval packs와 정확 예산은 버전별 고정됐습니다. 합계 최대 174 calls, 3622912 tokens, 표준 공개가격 상한 USD 4.06이며 실제 지출이 아닙니다.
DG-XVER-PROVIDER는 USER_DECISION_REQUIRED; provider/credential/공격 접근0. DG05 NOT_APPROVED; 교수 package NOT_SUBMITTED; DG06 필수.
DEC025 제목·claim·HAI23 V2A/T0/T2·EXP03B·EXP02·EXP04/05·PILOT 결과 불변. T2>T1-B는 정상 의미 유도에 한정하며 T0보다 우수하지 않습니다.
후보 권한 META+STAT, GDN은 비인과적 learned-graph evidence, SCI02B 고정 숫자 결합, FormalV4 실행권한, guard 단방향. 37정책 재선택·META 재구성·best seed 없음.
eTaPR109 합성/가상 동등성 PASS. 다중파일/empty/secondary P1 해석은 DG05 전 결정 항목으로 유지하며 실제 eligibility는 생성하지 않았습니다. 백업 SINGLE_COPY_LOCAL_ONLY.
