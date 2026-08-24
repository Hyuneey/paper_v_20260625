# 설명 가능한 다변량 시계열 이상탐지를 위한 그래프 유도 에이전틱 규칙 구성과 결정론적 검증

> Working thesis draft — `PROVISIONAL_PENDING_PROFESSOR_APPROVAL`

## 초록

다변량 사이버물리시스템 이상탐지기는 이상 여부를 알릴 수 있지만, 어떤
제어 변수의 변화와 어떤 공정 변수의 시간 지연 반응이 기대 관계를
위반했는지를 사람이 읽을 수 있는 형태로 제공하는 데 한계가 있다. LLM을
이용한 규칙 생성은 표현의 유연성을 제공하지만 수치 환각, 재현성 저하,
유효성 책임의 혼합을 만들 수 있다. 본 연구는 이 문제를 LLM의 자유 생성
문제가 아니라 제안 권한과 과학적 유효성 권한을 분리하는 규칙 구성 문제로
정의한다.

제안 방법은 정상 CPS 데이터에서 metadata, statistical relation, learned
graph 기반 후보를 찾고 source transition 이후 target response를 여러
horizon에서 프로파일링한다. LLM은 허용된 relation과 typed schema 안에서
규칙 구조를 제안할 수 있지만 최종 numeric parameter, validity, runtime
decision을 소유하지 않는다. 수치는 normal-only deterministic calibration에
결합되고 verifier가 구조, 변수 역할, graph/evidence, parameter provenance,
operational contract와 claim boundary를 검사한다. 승인된 규칙은 runtime에서
LLM 없이 실행되며 satisfaction trace를 생성한다.

HAI 23.05 P1 Boiler에서 144개 source–target 후보를 구성하고 META/STAT/GDN
top-20의 unscored union으로 47개 pair를 만들었다. normal train1/2 fit과
train3 confirmation을 거쳐 23개 pair의 42개 directed relation을 확정했다.
이 COMMON-42 rule layer는 INNER 14개 attack event 중 13개를 탐지했으며
PCA-SPE reference detector가 놓친 3개 event를 모두 포함했다. 그러나 D1의
Normal FAR는 40.50255787059723 episodes/hour이었다. exact same-second
two-source fusion인 D2 V1과 native-horizon persistence를 사용한 D2 V2는
모두 D0 miss를 0/3만 회복했다. V2의 FAR는 6.915070855955625로 증가했다.

결론적으로 verified rule signal은 reference detector와 event-level에서
보완적이지만 현재 fusion은 이 신호를 incremental detector utility로
전환하지 못했다. 본 연구는 새 detector의 우월성을 주장하지 않으며,
graph-guided verified rule construction, deterministic execution trace,
complementarity와 negative fusion evidence를 기여 후보로 제시한다. held-out
평가는 test2 bytes와 labels를 읽기 전에 중단되어 일반화는 확인되지 않았다.

## 1. 서론

### 1.1 배경과 동기

산업 공정은 여러 sensor, controller, actuator가 시간적으로 결합된 동적
시스템이다. multivariate anomaly detector는 joint variation이나 prediction/
reconstruction error를 이용해 unusual state를 찾는다. 이러한 score는 경보
발생에는 유용하지만 운영자가 문제를 이해하기 위해 필요한 관계 정보를
직접 제공하지 않을 수 있다. 운영자는 어떤 command transition 이후 어떤
sensor response가 얼마 동안 기대됐고, 관측이 그 기대와 어떻게 달랐는지
확인해야 한다.

시간 규칙은 이러한 정보를 명시적으로 표현할 수 있다. 그러나 공정의 모든
variable pair, delay, tolerance를 사람이 작성하기는 어렵다. LLM을 사용하면
규칙 구조와 설명을 빠르게 만들 수 있지만, LLM이 수치 임계값이나 실행
코드를 자유롭게 만들고 자신의 결과를 승인하면 근거와 재현성이 약해진다.
과거 ARGOS 계열 방법의 repository-level 검토에서도 bounded repair와 review의
일부 component evidence는 있었지만, unrestricted code generation, numeric
authority, detector correction safety, sealed validation 문제가 남았다.

본 연구는 이 문제를 “LLM이 좋은 규칙을 생성하는가”에서 “LLM의 구조
제안 능력을 사용하더라도 scientific authority를 deterministic하게 통제할
수 있는가”로 전환한다. graph와 statistics는 candidate를 제시하고,
normal-only profiling은 relation evidence를 만들며, LLM은 bounded schema
안의 구조만 제안한다. numeric authority와 verifier가 규칙을 승인하고,
runtime은 LLM 없이 trace를 만든다.

### 1.2 연구 목적

첫째, 정상 CPS 데이터에서 rule construction에 사용할 수 있는 directed
temporal relation을 graph-guided 방식으로 발견한다. 둘째, proposal과
numeric/validity authority를 분리한 agentic construction을 구현한다. 셋째,
verified rule이 reference detector와 보완적인 attack-event evidence를
제공하는지 평가한다. 넷째, 단순 deterministic fusion이 그 complementarity를
incremental utility로 바꾸는지 검증한다.

본 연구의 contribution은 새 anomaly detector가 아니며 D2 superiority도
아니다. graph edge와 trace는 causal root cause를 증명하지 않는다. TSFM과
ARTIST-style segment selection은 구현하지 않았고 held-out generalization은
확인되지 않았다.

### 1.3 잠정 연구 질문

**RQ1.** graph-guided candidate discovery와 normal-only temporal profiling은
CPS rule construction에 유용한 multivariate relation을 식별할 수 있는가?

**RQ2.** bounded LLM-assisted construction, deterministic numeric authority,
deterministic verification을 결합해 executable, human-readable temporal rule을
만들 수 있는가?

**RQ3.** verified temporal rule은 reference multivariate detector와 보완적인
anomaly-event evidence를 제공하는가?

**RQ4.** simple deterministic fusion은 이 보완 evidence를 incremental detector
utility로 전환할 수 있는가?

RQ 문구는 교수 검토 전 provisional이며 held-out RQ를 answered로 추가하지
않는다.

### 1.4 잠정 기여

본 논문의 첫 번째 기여 후보는 graph-guided relation discovery와 normal-only
temporal evidence pipeline이다. 두 번째는 LLM이 structured candidate만
제안하고 numeric parameters, validity, runtime을 결정하지 않는 bounded
agentic architecture다. 세 번째는 rules를 numeric evidence와 binding하고
satisfaction trace를 생성하는 deterministic verifier/runtime interface다.
네 번째는 D0/D1/D2 INNER analysis를 통해 detector–rule complementarity와
두 fusion policy의 negative evidence를 투명하게 함께 제시한 것이다. 네
항목은 모두 `PROVISIONAL_PENDING_PROFESSOR_APPROVAL`이다.

## 2. 관련연구와 연구 위치

### 2.1 Multivariate TSAD와 graph model

multivariate TSAD는 reconstruction, forecasting, representation, density
estimation 등 다양한 방식으로 joint anomaly를 찾는다
`[BIB-VERIFY-TSAD-SURVEY]`. graph-based model은 variable dependency를 학습해
prediction 또는 anomaly score를 개선한다. GDN 계열은 dynamic learned graph를
사용하는 대표 축으로 정리할 수 있다 `[BIB-VERIFY-GDN-CANONICAL]`.

본 연구는 graph detector 자체를 contribution으로 제시하지 않는다. GDN,
STAT, META는 relation profiling 대상으로 사용할 candidate evidence를
제공한다. exported edge는 predefined candidate universe에 속해야 하고,
learned edge는 인과 relation으로 승격되지 않는다.

### 2.2 Explainable TSAD와 temporal localization

기존 설명 방식에는 feature attribution, reconstruction-error decomposition,
counterfactual, subsequence/segment localization, rule explanation이 있다
`[BIB-VERIFY-XTSAD-SURVEY]`. 본 연구의 interface는 source transition,
target response, lag/horizon, expected direction과 runtime satisfaction trace를
제공한다. 이는 time-variable-relation localization이지만 learned important
segment를 먼저 선택하는 ARTIST-style method와 동일하지 않다
`[BIB-VERIFY-ARTIST-CANONICAL]`.

### 2.3 CPS invariant와 rule-based detection

CPS invariant 연구는 정상 운전의 물리·논리 관계를 위반 탐지에 사용한다
`[BIB-VERIFY-CPS-INVARIANT]`. 사람이 작성한 invariant는 해석이 쉽지만
확장성이 낮고, 데이터 기반 rule은 coverage를 늘릴 수 있지만 근거와
parameter control이 필요하다. 본 연구는 normal-only evidence와 deterministic
calibration을 사용하지만 physical law나 causal invariant를 주장하지 않는다.

### 2.4 LLM rule generation과 agentic verification

LLM-assisted rule generation은 자연어와 code generation의 유연성을 활용할
수 있다 `[BIB-VERIFY-LLM-RULE-GENERATION]`. agentic verifier/repair system은
generator output을 critique하고 수정한다 `[BIB-VERIFY-AGENTIC-VERIFICATION]`.
그러나 syntax repair와 detection utility는 별개의 결과다. 본 연구는 T0,
T1, budget-matched T1-B, bounded T2를 같은 contract에서 비교하고 numeric
authority와 final acceptance를 LLM 밖에 둔다.

### 2.5 ARGOS, TSFM과 본 연구의 경계

저장소의 ARGOS reproduction은 component-level partial methodological support를
제공하지만 complete aggregator superiority를 지지하지 않는다
`[BIB-VERIFY-ARGOS-CANONICAL]`. 이 경험은 detector-preserving correction,
no-op, leakage-safe selection, deterministic validation의 필요성을 강화했다.
TSFM은 현재 구현·평가하지 않았으며 related-work의 future comparison으로만
남긴다 `[BIB-VERIFY-TSFM-SURVEY]`.

따라서 본 연구의 위치는 새 graph detector나 자유 natural-language
explainer가 아니라 candidate curation부터 evidence-bound executable rule과
utility analysis까지의 controlled construction pipeline에 있다.

## 3. 문제 정의

1초 간격의 multivariate time series를
\(X=\{\mathbf{x}_t\}_{t=1}^{T}\), \(\mathbf{x}_t\in\mathbb{R}^{d}\)로
둔다. source set \(S\)는 control command 또는 actuator feedback이고 target
set \(Y\)는 continuous process sensor다. candidate relation은
\(r=(s,y)\), \(s\in S\), \(y\in Y\)인 directed pair다.

source event \(e=(s,t_e,d)\)는 시간 \(t_e\)의 stable step transition이며
\(d\)는 increase/decrease direction이다. candidate horizon
\(H=\{1,5,10,30,60\}\)에서 target response direction, support, consistency,
robust effect를 normal files별로 측정한다. 확인된 evidence는 정상 상태에서
반복 관측된 relation을 의미하지만 causality를 뜻하지 않는다.

verified rule은 source/target, trigger, expected direction, lag/window,
parameter reference, abstention, output, claim policy를 갖는다. parameter는
자유 numeric literal이 아니라 normal calibration artifact에 연결된다.
runtime outcome은 expected-response satisfied, anomaly, abstain으로 구분되고,
trace는 regime/trigger/lag/window/relation/tolerance/persistence/output 단계를
기록한다.

attack event는 strict label-one maximal contiguous run이고 alarm episode는
중복 제거된 one-second point alarm의 maximal contiguous run이다. event recall은
alarm episode와 한 번 이상 overlap한 attack event의 비율이며 Normal FAR/hour는
attack timestamp와 겹치지 않는 alarm episode를 normal exposure hour로 나눈다.

이 논문은 rule validity와 utility를 분리한다. validity는 structure, roles,
graph/evidence, parameter provenance, split, operational contract, claim boundary를
검사한다. utility는 valid rule이 anomaly event를 포착하고 detector miss를
보완하며 false alarm을 얼마나 만드는지 평가한다. label-aware utility가
validity를 소급 결정하지 않는다.

## 4. 방법

### 4.1 Data role과 process scope

HAI normal train1/2는 candidate와 relation fit, train3는 one-way relation
confirmation과 D0 threshold calibration, train4는 normal sanity에 사용한다.
test1 prediction은 label-blind하게 고정하고 label-test1은 이후 metric에만
사용한다. test2는 held-out이다. continuous-step feasibility에서 P1 Boiler를
primary process로 고정했다.

12 source와 12 target role의 directed product에서 144 candidate pair를
만들었다. metadata role은 search space를 제한하지만 domain knowledge를
완전히 제거하지 않는다.

### 4.2 Candidate discovery

META는 feature values 없이 metadata role과 subsystem/graph support를 사용한다.
STAT는 normal train1/2의 file-local difference를 이용해 1/5/10/30/60초 lagged
correlation을 계산한다. GDN은 mask가 적용된 universe 안의 upstream-aligned
learned graph ranking을 제공한다. 세 score를 하나로 합치지 않고 primary
top-20의 identity-based set union을 만들며 provenance를 유지한다. 그 결과
47개 unique pair가 profiling cohort가 됐다.

### 4.3 Normal temporal profiling

source event는 10초 refractory와 ±2초 inclusive cross-source isolation을
적용한다. train1/2 fit은 pooled support≥20, each-file support≥5, pooled
consistency≥0.70, per-file consistency≥0.60, robust effect ratio≥2.0을
요구한다. train3 confirmation은 support≥5, consistency≥0.60, effect ratio≥1.0을
요구하며 alternative horizon search를 하지 않는다. 23 pair에서 42 directed
relation이 확인됐다.

### 4.4 Rule construction과 numeric authority

T0는 deterministic template, T1은 one-shot constrained LLM, T1-B는 T2와 같은
총 call budget의 independent generation, T2는 bounded verifier-feedback이다.
모든 arm은 같은 evidence, parameter strategy, schema, verifier와 provider
policy를 공유한다. LLM은 candidate 밖 변수를 선택하거나 final numeric
parameter를 만들 수 없다.

numeric authority는 normal data calibration으로 threshold, tolerance,
lag/window reference를 결정한다. 공개 rule은 identity를 보존하지만 private
numeric payload를 노출하지 않는다. T0/T1/T1-B는 42/42 COMMON-equivalent
rule을 만들었고 T2는 39 accepted, 3 no_rule이었다. 이 결과는 feedback
performance optimization을 입증하지 않는다.

### 4.5 Deterministic verifier와 runtime

verifier는 closed schema, role compatibility, candidate membership,
graph/evidence binding, parameter provenance, time/unit consistency, split,
complexity, abstention, duplicate/conflict, prohibited claim을 검사한다. acceptance는
runtime authorization과 분리된다.

runtime은 LLM, dynamic code execution 없이 accepted rule을 평가한다. 각
opportunity에서 source trigger와 target response를 검사하고 satisfied,
anomaly, abstain을 기록한다. satisfaction trace는 사람이 어떤 variable
relation과 horizon에서 판단이 이뤄졌는지 확인할 수 있게 한다.

### 4.6 D0/D1/D2 utility design

D1은 COMMON-42를 모든 applicable opportunity에 실행한 rule-only arm이다.
D0는 37개 P1 feature의 normal-only PCA-SPE reference다. cumulative variance
0.95의 최소 k를 선택해 k=10이 됐고 normal train3 0.999 quantile threshold에서
strict `score > threshold`를 alarm으로 정했다.

D2 V1은 모든 D0 alarm을 보존하면서 같은 second의 distinct D1 source가
2개 이상일 때 recovery를 추가한다. D2 V2는 각 rule evidence를 frozen native
horizon까지 causal/inclusive하게 유지하고 active distinct source≥2일 때
recovery한다. 두 arm은 D0 score, labels, rule reevaluation을 fusion에 사용하지
않는다.

## 5. 실험 설정

dataset은 HAI 23.05, process는 P1 Boiler, sampling은 1초다. candidate universe는
144, integrated cohort는 47, confirmed relation은 42, utility portfolio는
COMMON-42다. INNER attack event는 14개이고 normal exposure는 51,019초다.
primary metric은 Attack-event Recall과 Normal FAR episodes/hour다.

candidate K=20(views 10/20/40), horizon 1/5/10/30/60, refractory 10초,
isolation ±2초, relation support/consistency/effect gate는 frozen protocol이다.
일부는 reasonable하지만 sensitivity-untested다. PCA 0.95와 q=0.999는 reference
baseline choice이고, D2 source count 2와 V1/V2 time policy는 structural
limitation이 관측됐다. preregistration은 optimality의 증명이 아니다.

## 6. 결과

### 6.1 Primary result

| Arm | Attack-event Recall | Normal FAR/hour | D0 miss recovery |
|---|---:|---:|---:|
| D0 PCA-SPE | 0.7857142857142857 | 0.4939336325682589 | baseline |
| D1 COMMON-42 | 0.9285714285714286 | 40.50255787059723 | 3/3 |
| D2 V1 | 0.7857142857142857 | 0.7056194750975128 | 0/3 |
| D2 V2 | 0.7857142857142857 | 6.915070855955625 | 0/3 |

D0는 11/14, D1은 13/14 events를 탐지했다. 두 arm이 모두 탐지한 event는 10,
D0 only는 1, D1 only는 3, neither는 0이었다. union은 14/14이고 D1은 D0가
놓친 3개를 모두 포함했다. 따라서 rule layer는 reference detector에 event-
level complementary evidence를 제공했다. 하지만 D1 normal false-alarm episode는
574개로 standalone operation을 지지하지 않는다.

### 6.2 Fusion failure

D0-missed/D1-detected 세 event 중 하나는 single-source였고 두 개는 multi-
source지만 asynchronous였다. V1의 exact same-second two-source condition은
세 event를 모두 놓쳤다. V2는 native horizon memory로 corroboration을 늘렸지만
recovery는 여전히 0/3이었다. normal V2 rule-recovery false alarm은 92 episodes,
Added FAR는 6.4916991708971175였다. Incremental Normal FAR는
6.421137223387365였다.

event set union은 매초 label-blind하게 실행 가능한 gate가 아니다. V1은
temporal structure를 보존하지 못했고 V2는 normal evidence도 함께 누적했다.
따라서 central interpretation은
`RULE_SIGNAL_PRESENT_BUT_CURRENT_FUSION_UTILITY_UNSUPPORTED`다.

### 6.3 Explanation 사례

공개 descriptor에서 `P1_FCV01D → P1_FT02`의 step-up 후 1초 target decrease,
`P1_PCV01D → P1_PIT01`의 step-up 후 60초 target increase,
`P1_LCV01D → P1_PIT01`의 step-up 후 10초 target decrease 관계를 예로 들 수
있다. runtime은 source stability와 trigger를 확인하고 native horizon의
target direction을 검사해 outcome과 trace를 남긴다. 이 설명은 variable–time
relation violation을 localize하지만 causal fault나 공격 주체를 증명하지
않는다.

### 6.4 Held-out status

preregistered held-out evaluation은 data-custody boundary에서 test2 feature
bytes와 labels를 읽기 전에 중단됐다. feature byte read=0, semantic parse=0,
label access=0, OUTER D0/D1/D2 execution=0이며 prediction과 metric은 없다.
따라서 이는 negative OUTER result가 아니고 generalization은 unconfirmed다.

## 7. 논의

결정론적 numeric authority는 LLM의 structural flexibility와 scientific
reproducibility를 양립시키는 핵심이다. normal evidence에 binding된 parameter는
LLM hallucination과 result-driven threshold change를 막는다. verifier는 syntax
correctness를 넘어 evidence, provenance, operational contract와 claim boundary를
독립적으로 검사한다.

결과는 validity와 utility의 차이를 보여준다. COMMON-42는 valid하고 executable
하지만 D1 FAR는 높다. 동시에 D1_ONLY 3 events는 relation violation이 PCA-SPE와
다른 signal을 가진다는 과학적 근거다. 따라서 rule signal을 폐기할 이유도,
바로 배포할 이유도 없다.

fusion 결과는 event-level complementarity와 point-level operational decision의
간극을 드러낸다. V1은 asynchronous evidence를 버렸고 V2는 memory를 늘렸지만
normal context를 구별하지 못했다. 단순히 window를 늘리는 것이 아니라 어떤
evidence가 normal transition에서 반복되는지 구별하는 문제가 남는다. 그러나
이 관찰만으로 D2 V3를 설계하거나 tuning할 권한은 없다.

본 explanation은 unconstrained natural language가 아니라 verified relation과
observed runtime facts에 기반한다. 동일 input과 authority에서 같은 trace를
만든다는 장점이 있지만 human usefulness는 측정되지 않았다. ARTIST-style
segment selection을 추가할지는 explanation contribution의 범위에 대한 교수
결정이다.

## 8. 한계

과학적으로 하나의 HAI process와 14 INNER events만 평가했고 reference detector도
PCA-SPE 하나다. 일부 hyperparameter는 sensitivity-untested이고 D1 FAR는 높다.
D2 V1/V2는 incremental recall을 만들지 못했다. OUTER 결과, TSFM, ARTIST
segment selection, human explanation study, causal validation이 없다. 따라서
statistical superiority, deployability, held-out generalization, root cause를
주장하지 않는다.

소프트웨어 측면에서 result traceability는 strong하지만 raw HAI와 private
numeric/model authority가 Git 밖에 있고 locator/factory setup이 필요해 same-
machine reproducibility는 moderate, fresh-machine portability는 weak다. task-
specific governance가 scientific kernel 주변에 축적돼 탐색 비용도 높다.
private data exclusion 자체는 결함이 아니며 논문 검토 전 대규모 refactor는
필수하지 않다.

## 9. 결론

본 연구는 graph-guided candidate discovery에서 normal temporal evidence,
bounded rule construction, deterministic numeric authority/verifier, LLM-free
runtime과 trace까지 이어지는 executable rule pipeline을 구현했다. D1은 D0
miss 3/3을 포착해 event-level complementarity를 보였지만 높은 FAR 때문에
standalone utility가 없었다. D2 V1/V2는 complementarity를 incremental detector
utility로 전환하지 못했다.

따라서 가장 강하게 지지되는 thesis framing은 새 detector나 fusion superiority가
아니라 graph-guided verified temporal rule construction과 transparent utility
analysis다. negative fusion result는 실패를 숨기지 않고 signal structure와
operational gate의 차이를 설명하는 근거다.

최종 범위는 다음 네 결정을 기다린다.

- `[PROFESSOR_DECISION_1_CONTRIBUTION]`: verified rule construction framing 승인
- `[PROFESSOR_DECISION_2_EXPLANATION_INTERFACE]`: trace 유지 또는 ARTIST 추가
- `[PROFESSOR_DECISION_3_OUTER_REQUIREMENT]`: thesis first 또는 새 OUTER first
- `[PROFESSOR_DECISION_4_DETECTOR_BASELINE]`: PCA-SPE 유지 또는 stronger baseline

현재 권고는 `THESIS_FIRST_PENDING_PROFESSOR_FEEDBACK`이다.
