<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=37991eb80f9a1f37099cd2b71c9d1117b8e2e94badee421f12cebd17fdb6cb62 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# RCC 현재 연구 상태

## VALIDATION V2 개발 결과 · 결과 무결성 QA PASS

모든 5개 prediction freeze와 replay 후에만 test1 label을 해석했습니다.
PILOT V1과 별도 결과이며 최종 과학적 검증은 아닙니다.

| 방법 | Attack-event Recall | Normal FAR/hour | 정상 false episode |
|---|---:|---:|---:|
| D0 PCA-SPE | 11/14 | 0.4939336325682588839451968874340932 | 7 |
| Isolation Forest | 5/14 | 1.764048687743781728375703169407476 | 25 |
| Rule-only V2A | 11/14 | 37.60951802269742644896999157176738 | 533 |
| PCA+Rule | 11/14 | 0.6350575275877614222152531409866912 | 9 |
| IF+Rule | 5/14 | 1.905172582763284266645759422960074 | 27 |

두 고정 fusion은 추가 탐지 0개, 정상 false episode 각각 2개 증가로 탐지 개선이 지지되지 않았습니다.
전체 6,418개 actual trace의 자동 구조 충실도 QA는 PASS입니다.
GDN은 LEARNED_GRAPH_SUPPORTING: 2개 pair의 보조 근거이며 130개 설명에 선택적 문구를 붙였을 뿐 예측에는 영향을 주지 않습니다.
EXP-01·EXP-01B의 기존 음성 결과는 유지합니다. 전체 split에서 GDN 안정성을 입증한 것은 아닙니다.
14 contiguous attack-event units의 통계적 독립성, human usefulness, held-out 일반화는 미확인입니다.
평가 계획은 HAI23 test2 primary held-out와 HAI22/21 external replication으로 확대됐습니다.
146개 nominal scenario는 IID가 아니며 primary pooled Recall을 만들지 않습니다. 실제 P1 denominator는 아직 pending입니다.
다음: DG-05 — Multi-Panel Attack Feature + Conditional Label/Scenario Access. DG-03 provider 승인, DG-04 제목, DG-05 attack panel, DG-06 실제 제출은 서로 별도 Gate입니다.


과학 source authority: `origin/research-v6-thesis-checkpoint` @ `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`
Registry version: `0.1.0`
Registry snapshot: `2026-09-03T17:08:57Z`

## 현재 단계

**평가 범위 확장** (`EVALUATION_SCOPE_EXPANSION`)

MULTIPANEL-PRE-DG05-FREEZE-001 COMPLETE_QA_PASS. HAI22/21 PCA-SPE and secondary Isolation Forest are frozen from label-blind normal projections. Five primary methods per panel, immutable Fusion, method-blind P1 eligibility, official-scenario metrics, file-namespaced eTaPR, empty-input behavior, paired contrasts, and the global prediction-before-any-label custody state machine are frozen. No attack/test/label/scenario data was accessed. Current phase PRE_DG05_FROZEN; exact next DG-05 USER_DECISION_REQUIRED. Professor package NOT_SUBMITTED; backup SINGLE_COPY_LOCAL_ONLY.

## 상태를 읽는 방법

- **구현 완료 / 실제 실행 완료:** 엔지니어링 상태일 뿐이다.
- **근거 점검 완료 (Evidence-reviewed):** 호환용 component field `audited`가 pinned authority와
  source 또는 evidence 상태를 대조했다는 뜻이다. 성능 검증이 아니다.
- **결과 무결성 확인 (Result Integrity):** 명시된 결과 artifact의 custody·불변성·순서·산술을
  확인한 상태다. 과학적 검증이 아니다.
- **독립 재현 완료 (Reproduced):** 필요한 환경과 custody 아래에서 별도로 재현한 상태다.
- **과학적 검증:** 가설에 대한 충분한 독립 근거가 있는 상태이며 component 상태에서 추론하지
  않고 `claims.csv`가 관리한다.

구현 완료, 실행 완료, 결과 무결성 확인, 과학적 검증, 재현성, 일반화는 서로 다른 상태다.
따라서 아래 개수는 하나의 완료율이 아니며, 근거 점검 완료 수가 실제 실행 완료 수보다 많을 수 있다.

## 구성요소 요약

- **구현 완료:** 30
- **실제 실행 완료:** 29
- **근거 점검 완료 (Evidence-reviewed):** 30
- **독립 재현 완료:** 0

## 데이터·split 점검

- **데이터셋 / 공정:** HAI 23.05 / P1 Boiler
- **Label 접근:** 정상 근거 구성은 label-blind다. PILOT V1 D1의 약한 in-memory 경계는 역사적 조건으로 유지하고, VALIDATION V2는 no-overwrite prediction freeze·replay·one-shot label lease·label 이후 byte 확인을 요구한다.
- **정보 누출:** 확인된 정보 누출은 없다. PILOT V1의 D1 custody 조건은 유지되며 GAP-FIX-002가 향후 VALIDATION V2 custody gap을 닫았다. D2 V2는 여전히 test1-informed development다.
- **Test1:** INNER 개발용 14개 연속 attack-event unit 예비 실험이다. 통계적 독립성은 확립되지 않았고 최종 검증이 아니다.
- **Test2:** custody 단계의 file 접근 시도 1회가 byte read 전에 거부됐으며 held-out 결과는 없다.

## META provenance 점검

- **META SOURCE:** `HYBRID_REVIEWED_METADATA`
- **META USER INTERVENTION:** `HUMAN_INTERVENTION_LEVEL_1`
- **META EXACT PUBLIC REPRODUCIBILITY:** `PARTIALLY_REPRODUCIBLE_PRIVATE_REVIEWED_INPUT_REQUIRED`
- **경계:** 공식 P1 graph 자동 처리와 AI-assisted reviewed semantic declaration이 함께
  ranking에 기여했다. 최종 Top-20은 deterministic code가 선택했으며 researcher pair
  selection은 확인되지 않았다.

## 고정 D1 runtime·trace 점검

- **실행 authority:** task-specific V4 authority plane — CanonicalRuleDescriptorV4 42개, 고정 V4 evaluator bundle, normal-only Utility V4 numeric resolver, committed one-attempt INNER grant.
- **Prediction:** opportunity record 6,031개, anomalous rule record 788개, 고유 alarm decision second 630개, downstream metric episode 626개.
- **고정 경계:** D0/D2보다 약한 in-memory pre-label freeze; label 전 durable persistence = 아니오.
- **Trace:** canonical RuntimeTraceV1과 동등하지 않으며 terminal outcome semantics만 부분적으로 겹친다.
- **설명:** canonical RuntimeTraceV1 renderer는 있지만 고정 V4 D1이 호출하지 않았고 고정 D1 explanation artifact도 없다.

## 고정 D2 fusion 점검

- **역할:** D0 alarm을 보존하는 결정론적 fusion-policy 예비 실험
- **V1:** 11/14; Normal FAR 0.7056194750975128 episodes/hour; D0-miss recovery 0/3.
- **V2:** 11/14; Normal FAR 6.915070855955625 episodes/hour; D0-miss recovery 0/3.
- **D0 보존:** pointwise 보존 — `D2(t)=D0(t) OR policy_admits_D1(t)`
- **고정 / label:** V1과 V2 모두 label 접근 전 durable prediction file gate를 사용한다.
- **경계:** V2는 test1-informed development이며 독립 확인이 아니다. 현재 V1/V2 결과로 Detector+Rule이 일반적으로 쓸모없다고 결론 내릴 수 없다.

## 구현 구성요소

| 구성요소 | 엔지니어링·근거 표시 | 다음 조치 |
|---|---|---|
| DATA_PROVENANCE | 구현·실행·근거 점검 완료 | 데이터 판본과 공개 가능한 식별 정보를 고정한다. |
| SPLIT_GOVERNANCE | 구현·실행·근거 점검 완료 | 각 split의 허용 역할과 경계 제거 규칙을 강제한다. |
| VARIABLE_ROLE_UNIVERSE | 구현·실행·근거 점검 완료 | source·target 역할과 가능한 pair universe를 고정한다. |
| META_DISCOVERY | 구현·실행·근거 점검 완료 | 실제 값 없이 metadata만으로 후보를 순위화한다. |
| STAT_DISCOVERY | 구현·실행·근거 점검 완료 | 정상 데이터의 시간 지연 통계 연관성으로 후보를 순위화한다. |
| GDN_DISCOVERY | 구현·실행·근거 점검 완료 | 학습 그래프의 후보 순위 근거를 만들며 인과관계로 해석하지 않는다. |
| CANDIDATE_UNION | 구현·실행·근거 점검 완료 | META·STAT·GDN 후보를 재점수화 없이 합친다. |
| RELATION_PROFILING | 구현·실행·근거 점검 완료 | 정상 반복 반응에서 방향과 시간 지연을 확인한다. |
| NUMERIC_AUTHORITY | 구현·실행·근거 점검 완료 | 시간·허용오차·지속성·크기 참조를 정상 근거에 결속한다. |
| EVIDENCE_PACK | 구현·실행·근거 점검 완료 | 고정 관계와 수치 참조, 근거 출처 추적(Provenance)을 구성 단계에 전달한다. |
| RULE_DSL | 구현·실행·근거 점검 완료 | 제안 가능한 필드를 닫힌 구조로 제한하고 canonical Rule과 분리한다. |
| T0_TEMPLATE | 구현·실행·근거 점검 완료 | LLM 없이 만드는 규칙 구성 비교 기준이다. |
| T1_ONE_SHOT | 구현·실행·근거 점검 완료 | 제한된 LLM 1회 제안 비교군이다. |
| T1B_REPEAT | 구현·실행·근거 점검 완료 | T2와 같은 호출 예산으로 독립 생성을 반복한다. |
| T2_AGENTIC_FEEDBACK | 구현·실행·근거 점검 완료 | revise·retrieve·no_rule을 허용하는 제한된 제어 경로다. |
| DETERMINISTIC_VERIFIER | 구현·실행·근거 점검 완료 | label 없이 구조·근거·수치·실행 계약을 검사한다. |
| COMMON42_FREEZE | 구현·실행·근거 점검 완료 | 검증된 42개 관계 규칙 portfolio를 불변 상태로 고정한다. |
| RULE_RUNTIME | 구현·실행·근거 점검 완료 | 고정 규칙과 승인된 수치 참조를 결정론적으로 실행한다. |
| SATISFACTION_TRACE | 구현·실행·근거 점검 완료 | 관찰된 평가 단계와 권한 결속을 기록한다. |
| EXPLANATION_RENDERER | 구현·실행·근거 점검 완료 | 규칙과 trace에 있는 사실만 제한적으로 설명한다. |
| D0_PCA_SPE | 구현·실행·근거 점검 완료 | 단순하고 결정론적인 정상 전용 다변량 기준선이다. |
| D1_RULE_ONLY | 구현·실행·근거 점검 완료 | COMMON-42만으로 만드는 독립 이상 신호다. |
| D2_V1 | 구현·실행·근거 점검 완료 | 같은 초의 D0·D1 근거를 결합하는 고정 정책이다. |
| D2_V2 | 구현·실행·근거 점검 완료 | native horizon 근거를 이용하는 test1-informed 개발 정책이다. |
| EPISODE_CONSTRUCTION | 구현·실행·근거 점검 완료 | 연속 alarm second를 최대 연속 구간으로 묶는다. |
| ATTACK_EVENT_RECALL | 구현·실행·근거 점검 완료 | alarm episode가 겹친 attack-event unit 비율을 측정한다. |
| NORMAL_FAR | 구현·실행·근거 점검 완료 | 정상 노출 시간당 비공격 alarm episode 수를 측정한다. |
| RESULT_INTEGRITY | 구현·실행·근거 점검 완료 | prediction·metric·순서·누출 경계를 확인하며 성능 타당성을 대신하지 않는다. |
| OUTER_EVALUATION | 진행 전 해결 필요 (BLOCKED) | 일반화 검증 경로지만 현재 과학 결과는 없다. |
| REPRODUCIBILITY | 부분 완료 | source pin·artifact 보존·복원 준비 수준을 구분한다. |
| PROFESSOR_REPORTING | 구현·실행·근거 점검 완료 | 고정 관찰과 주장 한계를 함께 전달한다. |
| THESIS_DRAFT | 구현 완료·미실행 | 잠정 서술 맥락이며 scientific authority를 대체하지 않는다. |

호환용 field `claim_ready`는 이 요약에서 제외했다. 이는 component가 좁은 구현 또는 계약
주장을 하나 이상 지원한다는 뜻일 뿐이다.

## 실험

| 실험 | 상태 | 결과 범위 |
|---|---|---|
| EXP-01 | 실행·근거 점검 완료·개발 결과 | META·STAT·GDN의 고유하고 유용한 후보 기여가 있는지 비교한다. |
| EXP-01B | 실행·근거 점검 완료·개발 결과 | Embedding·Attention·EdgeMask·Source Occlusion을 동일 정상 관계 기준에서 비교한다. |
| EXP-02 | 실행·근거 점검 완료·개발 결과 | 응답 시간·허용오차·지속성 기준이 validity와 utility에 미치는 영향을 비교한다. |
| EXP-03 | 실행·근거 점검 완료·개발 결과 | T2 verifier feedback의 이점이 있는지 예산이 맞는 대조군과 비교한다. |
| EXP-04 | 실행·근거 점검 완료·개발 결과 | D0·D1·D2의 attack response와 정상 false alarm 부담을 함께 비교한다. |
| EXP-05 | 실행·근거 점검 완료·개발 결과 | 설명이 rule·trace·수치 출처·outcome을 벗어나지 않는지 검사한다. |
| EXP-06 | 설계만 완료 | 고정 규칙 결과나 정답을 받지 않는 별도 runtime LLM 비교 가능성을 검토한다. |
| EXP-H23-HOLDOUT | PRE_DG05_FROZEN | PREREGISTRATION_FROZEN_NO_ATTACK_RESULT |
| EXP-H22-XVER | PRE_DG05_FROZEN | PREREGISTRATION_FROZEN_NO_ATTACK_RESULT |
| EXP-H21-XVER | PRE_DG05_FROZEN | PREREGISTRATION_FROZEN_NO_ATTACK_RESULT |
| EXP-03B | 실행·근거 점검 완료·개발 결과 | 정상 확인 reference 기반 DEVELOPMENT_ONLY;T2 대 T1-B 사전등록 비교 |

## 공식 연구 주장

주장 상태는 `registry/claims.csv`에서만 가져온다.

| 주장 | 상태 | 허용되는 설명 |
|---|---|---|
| CLAIM-A | 구현 근거로 지원됨 | 구현은 확인됐지만 전체 방법의 일반화나 최종 검증을 뜻하지 않는다. |
| CLAIM-B | 구현 근거로 지원됨 | 정상 관계 근거를 권한 통제 아래 실행 가능한 규칙으로 변환했다. |
| CLAIM-C | 구현 근거로 지원됨 | 구조·근거·수치·split·실행 계약을 검사하지만 과학적 진실을 증명하지 않는다. |
| CLAIM-D | 구현 근거로 지원됨 | 고정 authority가 같으면 현재 runtime은 LLM 없이 결정론적으로 평가한다. |
| CLAIM-E | 현재 개발 결과로 지원되지 않음 | EXP-01과 EXP-01B의 동결된 정상 전용 기준은 GDN의 핵심·보조 기여를 지원하지 않았다. |
| CLAIM-F | 현재 근거로 지원되지 않음 | 현재 feedback action이 0이므로 이점은 지원되지 않는다. |
| CLAIM-G | DEVELOPMENT_SUPPORTED | 현재 14-unit pilot에서 서로 다른 event response가 관찰됐다. |
| CLAIM-H | 미검증 (UNVALIDATED) | 높은 event response와 높은 정상 FAR가 함께 있어 운영 유용성은 미검증이다. |
| CLAIM-I | 현재 개발 결과로 지원되지 않음 | 현재 D2 V1/V2는 D0 Recall을 개선하지 못했다. |
| CLAIM-J | 현재 근거로 지원되지 않음 | OUTER 과학 결과가 없어 일반화는 확인되지 않았다. |
| CLAIM-K | DEVELOPMENT_SUPPORTED | renderer 결속은 구현됐지만 전체 corpus의 fidelity는 조건부다. |
| CLAIM-L | 미검증 (UNVALIDATED) | trace 기반 interface는 있으나 사람에게 유용한지는 평가하지 않았다. |
| CLAIM-M | 현재 근거로 지원되지 않음 | 현재 근거는 시간 관계와 위반을 기록할 뿐 인과를 지원하지 않는다. |
| CLAIM-N | 미검증 (UNVALIDATED) | External versions completed normal-only T0/T2 method re-instantiation; attack panels remain unexecuted. |
| CLAIM-EXP03B-PREP | DEVELOPMENT_SUPPORTED | 정상-only 동결 EXP03B에서 T2 대 T1-B 이점;주요 의미 지표 T0 우월성 아님 |

## 연구 상태의 서로 다른 차원

- **엔지니어링:** 아키텍처는 대부분 구현됐고 주요 frozen INNER 경로가 실행됐다.
- **결과 무결성:** Explicit integrity audits exist for frozen D0, D1, D2 V1, D2 V2, EXP-01, EXP-01B, and EXP-02 results; this checks result custody and arithmetic, not performance validity.
- **과학적 검증:** 부분적이고 미완료다. 주요 성능·기여 가설은 미검증이거나 현재 근거로 지원되지 않는다.
- **재현성:** Fresh-machine synthetic rehearsal passed; authorized scientific-data reproduction and external reproduction remain pending.
- **일반화:** OUTER 과학 결과가 없어 held-out 일반화는 미확인이다.
- **연구 주장:** 좁은 구현·계약 주장만 지원되며 `claims.csv`가 공식 주장 기준이다.

## 현재 보장되지 않는 것

아직 확립되지 않음:

- GDN general utility beyond the current normal-only EXP-01 and EXP-01B scope
- Agentic의 T0 대비 우월성·고정 cohort 밖 전이·held-out utility
- Rule-only의 실제 운영 유용성
- Detector+Rule 성능 향상
- Held-out 일반화
- 설명의 인간 유용성

## 정확한 다음 작업

**DG-05 — Multi-Panel Attack Feature + Conditional Label/Scenario Access**

## 현재 DG-04 / 외부 준비 Gate

MULTIPANEL-PRE-DG05-FREEZE-001 COMPLETE_QA_PASS. HAI22/21 PCA-SPE and secondary Isolation Forest are frozen from label-blind normal projections. Five primary methods per panel, immutable Fusion, method-blind P1 eligibility, official-scenario metrics, file-namespaced eTaPR, empty-input behavior, paired contrasts, and the global prediction-before-any-label custody state machine are frozen. No attack/test/label/scenario data was accessed. Current phase PRE_DG05_FROZEN; exact next DG-05 USER_DECISION_REQUIRED. Professor package NOT_SUBMITTED; backup SINGLE_COPY_LOCAL_ONLY.
