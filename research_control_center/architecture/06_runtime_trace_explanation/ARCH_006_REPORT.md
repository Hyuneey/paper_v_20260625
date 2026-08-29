# Rule은 실제 시계열에서 어떻게 판단하는가

Scientific authority: `origin/research-v6-thesis-checkpoint@2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## 1. COMMON-42가 Runtime으로 들어가는 과정

Frozen D1은 canonical `RuleV1` runtime이 아니라 task-specific V4 authority plane을 사용한다. 42개 `CanonicalRuleDescriptorV4`, evaluator bundle, normal-only numeric registry, committed D1 grant, exact test1 feature custody가 모두 맞아야 실행된다. 실제 entrypoint는 `execute_authorized_inner_d1_v1`, 한 relation opportunity의 evaluator는 `execute_real_rule_v1`이다.

## 2. Source Trigger

Runtime은 매 초 42개 rule을 무조건 평가하지 않는다. 12개 source의 test1 시계열에서 먼저 sustained step event를 찾고, 같은 source에서 인접 후보 간격이 10초 이하인 single-link cluster를 만든다. Cluster에서는 절대 step amplitude가 가장 큰 후보를 남기고 정확히 동률이면 가장 이른 index를 남긴다. 그 뒤 다른 source event가 ±2초에 있으면 제외한다. 남은 isolated event와 source·direction이 맞는 COMMON descriptor만 opportunity가 된다.

한 event는 직전 5행 median과 이후 5행 median 차이가 normal authority의 threshold 이상이어야 한다. 각 window의 최소 80%가 median 주변 stability tolerance 안에 있어야 하고 부호가 descriptor의 `step_up` 또는 `step_down`과 같아야 한다. Census가 만든 event와 이 replay가 다르면 ABSTAIN이 아니라 system error다.

## 3. Horizon 이후 Target 확인

Source event가 `t`, frozen horizon이 `h`일 때 target baseline은 `median(target[t-5:t])`, response는 `median(target[t+h:t+h+3])`이다. 그 차이가 increase relation에서는 target noise scale보다 엄격히 크고, decrease relation에서는 음의 scale보다 엄격히 작아야 expected response다. Runtime은 다른 horizon을 다시 찾지 않는다.

## 4. Tolerance와 Persistence

Per-rule evaluator가 실제로 numeric resolver에서 읽는 값은 source step threshold, source stability tolerance, target noise scale 세 가지다. 나머지 일곱 role은 5/5 source window, 0.8 stability, 10초 clustering, ±2초 isolation, 5초 baseline, 3초 response 같은 frozen code contract로 실행되며 registry/reference가 그 상수와 맞아야 한다.

별도의 target persistence threshold나 연속 성공 횟수 검사는 없다. Source 쪽 지속성은 5행 post-window stability이고 target 쪽은 3행 response median이다. 이를 독립적인 persistence rule로 과장하면 안 된다.

## 5. PASS / FAIL / ABSTAIN

- PASS라는 설명용 표현은 실제 `evaluated_expected_response`다. Expected target response가 관측돼 alarm이 없다.
- FAIL이라는 설명용 표현은 실제 `evaluated_anomaly`다. Expected response가 기준을 넘지 못해 response window 마지막 행에 alarm을 낸다.
- `abstain`은 이미 형성된 opportunity의 source 또는 target context가 경계 때문에 완전하지 않을 때다. Alarm과 decision index가 없다.
- Authority, numeric, provenance, factory, replay 불일치는 system error이며 ABSTAIN으로 바뀌지 않는다.

Source event가 아예 없던 초는 PASS도 ABSTAIN도 아니다. 그 초에는 opportunity와 rule outcome이 생성되지 않는다.

## 6. 42개 Rule 결과가 D1 Alarm이 되는 방식

Frozen prediction은 54,000개 bool vector가 아니라 6,031개 rule-opportunity record다. 각 anomaly record가 자기 decision second에 alarm을 낸다. 같은 초에 여러 rule이 위반되면 여러 record로 남는다. Frozen artifact의 788 alarm records는 630 unique decision seconds에 놓여 있으므로 “788 point alarms”라고 부르면 부정확하다.

Metric 단계에서만 alarm decision index를 set으로 deduplicate하고 consecutive unique seconds를 episode로 합친다. Runtime alarm과 metric episode는 다른 객체다.

## 7. Satisfaction Trace

Frozen D1은 `task039e3_r2r_real_rule_execution_trace_v1` payload의 hash와 compact terminal record를 남긴다. Opportunity, source event, relation, final state, alarm, decision index, ten references, computation identity를 묶기 때문에 terminal result tamper closure는 강하다. Integrity audit는 6,031개 unique trace hash를 independently replay했다.

하지만 full trace payload가 별도 artifact로 저장되지는 않고 canonical `RuntimeTraceV1`의 nine satisfaction steps, canonical rule/verifier/window IDs, parameter value/unit, alignment flag도 없다. 두 schema는 **NON_EQUIVALENT**이며 terminal outcome 의미만 일부 겹친다.

## 8. D1 Prediction Freeze

Prediction은 frozen dataclass, tuple records, complete self-hash, factory/weak-reference custody로 만들어지고 label loader 직전에 replay validation된다. 실제 one-shot path에는 labels가 prediction construction으로 돌아가는 callback이 없고 integrity audit도 post-freeze mutation 0을 확인했다.

그러나 내부 record는 mutable dict이고 prediction JSON은 labels와 metrics 뒤에 public report로 쓰인다. D0/D2처럼 atomic pre-label file write, reopen, explicit frozen state, post-label byte check가 없다. 따라서 분류는 `SAFE_BUT_WEAKER_THAN_D0_D2`다. Verified leakage는 없지만 future independent D1 validation에서는 강화해야 한다.

## 9. Label은 언제 보는가

모든 rule result가 만들어지고 prediction object가 self-hash/factory 검증된 뒤 `_load_real_label_custody_v1`가 시작된다. 그 함수도 prediction을 다시 검증한 후에 label path를 확인하고 hash/open/parse한다. 정확한 thesis wording은 “label-blind prediction authority가 memory에서 검증된 뒤 label-test1을 열었다”다.

## 10. Frozen D1과 canonical RuntimeTraceV1 차이

Canonical trace는 RuleV1 runtime authorization, nine ordered operator results, parameter ID/hash/value/unit, explicit trigger/response/violation/abstain fields를 가진 typed artifact다. Frozen D1 task trace는 V4 opportunity의 terminal projection이다. Canonical trace compliance나 direct explanation compatibility는 입증되지 않았다. Frozen detection result integrity와 canonical trace equivalence는 별개다.

## 11. Runtime에서 LLM을 사용하는가

Frozen fixed-rule R0/D1 runtime에는 LLM, provider, network call이 없다. Randomness, concurrency, current-time decision도 없다. Fixed bytes, authority, code, Python numeric semantics 아래 deterministic하다. 이 주장은 future R1까지 “전체 architecture는 언제나 runtime LLM-free”라고 일반화할 수 없다.

## 12. 설명은 어떻게 만들어지는가

Canonical `render_delayed_response_explanation`은 deterministic template renderer로 구현돼 있다. Canonical authorization, RuntimeTraceV1, rule, verifier, window, evidence, graph, normal-reference, parameter hashes를 다시 확인하고 fixed text를 만든다. LLM은 사용하지 않는다.

그러나 frozen V4 D1 bridge는 이 renderer를 import/call하지 않고 canonical trace도 만들지 않는다. 따라서 current renderer implementation은 frozen D1 explanation result가 아니다.

## 13. 설명이 보장하는 것 / 못하는 것

Canonical plane에서는 source/target, authorized lag/reference, terminal outcome, no-causal/root-cause flag가 deterministic하게 묶인다. Tests는 mismatch와 invented causal claim을 fail closed로 확인한다. 하지만 frozen D1 adapter, corpus-level EXP-05, input-change consistency study, human study는 없다. Structural fidelity implementation과 human usefulness는 분리해야 하며 human usefulness는 `UNVALIDATED`다.

## 14. 현재 남은 위험

가장 큰 risk는 task V4 trace와 canonical trace/explanation 사이에 versioned bridge가 없다는 점, 그리고 D1 pre-label freeze가 memory-only라는 점이다. 추가로 788 alarm records를 unique point alarms로 부르는 혼동, ten numeric roles를 모두 dynamic lookup으로 설명하는 혼동, fixed response median을 별도 persistence rule로 설명하는 혼동이 있다. 이 audit은 frozen D1을 수정하거나 재실행하지 않는다.
