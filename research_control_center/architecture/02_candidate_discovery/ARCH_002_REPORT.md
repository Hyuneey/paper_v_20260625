# 관계 후보는 실제로 어떻게 만들어지는가

Scientific authority: `origin/research-v6-thesis-checkpoint` @ `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

Audit scope: pinned source, frozen public-safe candidate artifacts, tests, and execution receipts. 이 감사에서는 META/STAT/GDN을 재실행하거나 GDN을 학습하지 않았고 test2를 접근하지 않았다.

## 1. 이 단계의 목적

Candidate discovery의 역할은 가능한 source→target 쌍을 후속 normal delayed-response profiling이 검사할 제한된 cohort로 줄이는 것이다. 후보는 causal relation도, 확정 temporal relation도 아니다. 현재 구현은 서로 다른 근거를 가진 META, STAT, GDN 세 arm을 독립적으로 Top-20까지 고른 뒤 score를 합치지 않고 set union한다.

## 2. 144개 후보 공간

`CandidateUniversePolicyV1`과 frozen C0 bundle은 P1의 ordered source 12개와 target 12개를 고정한다. 두 역할 집합의 이름 overlap은 0이며, `eligible_pair_records_v1`이 ordered cross product를 만든다. 따라서 exact directed pair는 144개다. `source_i → target_j`는 ordered identity이고 반대 방향은 별도 역할 쌍이 존재할 때 독립 후보다.

## 3. META 방식

META는 HAI feature 값을 읽지 않는다. reviewed P1 metadata ledger와 official physical graph reference를 exact identity로 읽고 모든 144개 pair를 다음 우선순위로 분류한다.

1. `M1_EXPLICIT`: 공식 reference가 source→target 연결을 명시한다.
2. `M2_GRAPH_ADJACENT`: frozen directed physical graph에서 인접하다.
3. `M3_SUBSYSTEM_SUPPORTED`: reviewed subsystem metadata가 지지한다.
4. `UNSUPPORTED`: 위 근거가 없다.

순위는 evidence tier, independent official-reference count 내림차순, source/target 사전순이다. 수치 weight나 학습 score는 없다. 144개 중 30개가 supported였고, Top-20 prefix가 union에 들어갔다. META는 learned relation이 아니라 deterministic domain prior candidate evidence다.

핵심 의사코드:

```text
for pair in frozen_144_pairs:
    tier = first_matching(M1, M2, M3, UNSUPPORTED)
keep supported pairs
sort by tier, -official_reference_count, source, target
take prefix 20
```

## 4. STAT 방식

STAT은 정상 `train1`과 `train2`만 사용한다. 각 파일 안에서 source와 target의 first difference를 만들고, 1/5/10/30/60초 horizon마다 `corr(dx(t), dy(t+h))`를 계산한다. 파일 경계를 넘는 difference나 lag는 만들지 않는다.

같은 horizon에서 두 파일 correlation이 finite이고 같은 nonzero sign일 때만 stable이다. strength는 두 절댓값의 최소값이다. pair별 가장 큰 strength를 선택하고 동률이면 짧은 horizon을 쓴다. 전체 순위는 stable 우선, strength 내림차순, horizon 오름차순, source/target 순이다. 144개 중 141개가 supported, 3개가 sign-unstable였고 Top-20 prefix가 union에 들어갔다.

이 score는 **directional lagged association stability**다. downstream `RELATION_PROFILING`의 step event, response direction, horizon confirmation과 다르며 인과 근거가 아니다.

## 5. GDN 방식

Frozen passing GDN path는 `UpstreamAlignedGDN`이다. 정상 train1/train2의 full 37-node P1 context를 separate segment로 읽고, 5-step history에서 다음 1-step의 모든 node 값을 예측하도록 MSE로 학습한다. 세 seed(11, 23, 37)를 사용하고 각 seed에서 validation loss가 가장 낮은 in-memory state를 복원한다.

각 node에는 trainable 64-dimensional embedding이 있다. forward에서 embedding cosine similarity를 계산하고 target별 Top-5 neighbor를 골라 `learned_graph`를 만든다. GraphLayer는 이 edge 위에서 attention-weighted message passing을 하여 forecast한다. 학습 후 best-state embedding/graph를 꺼내 144개 허용 pair 공간으로 투영한다.

중요한 구현 제한이 있다. Frozen backend는 37×37 cosine matrix에서 diagonal/self를 먼저 mask하거나 제거하지 않고 Top-5를 계산한다. 따라서 target 자신의 identity가 내부 Top-5 슬롯 하나를 차지할 수 있다. 현재 12-source와 12-target 역할 집합은 서로 겹치지 않으므로 후속 144-pair projection이 exported self-pair는 제거하지만, 내부 neighbor budget에 미치는 기능적 영향은 시험되지 않았다. 이는 새 결과가 아니라 향후 pre-Top-5 masking sensitivity 항목이다.

세 seed aggregation은 edge selection frequency 내림차순, median cosine similarity 내림차순, source/target 순이다. 39개가 supported됐고 arm Top-20 prefix를 사용했다. Internal graph Top-5와 arm candidate Top-20은 서로 다른 budget이다.

## 6. GDN의 learned graph와 attention의 차이

- **A. learned graph adjacency:** 사용한다. embedding cosine과 target별 neighbor selection이 candidate authority의 원천이다.
- **B. graph attention:** 모델 내부 message passing에 사용하지만 coefficient를 candidate ranking이나 final evidence에 쓰지 않는다.
- **C. post-hoc XAI:** 사용하지 않는다. SHAP, attribution, 별도 explanation model이 없다.

따라서 “정상 데이터로 예측 모델을 학습하고 node-embedding learned graph edge를 후보 순위로 사용한다. attention coefficient는 최종 관계 근거가 아니며 별도 XAI도 없다”는 네 clause는 모두 **VERIFIED**다.

GDN `i → j`는 `j` 예측을 위한 selected neighbor/input dependency 후보를 뜻한다. temporal cause나 confirmed delayed response를 뜻하지 않는다.

## 7. 세 방식은 무엇이 다른가

| Arm | 보는 것 | 산출 근거 | 현재 해석 |
|---|---|---|---|
| META | reviewed metadata/physical graph | tier와 reference count | domain-prior candidate |
| STAT | normal first-difference lagged correlation | cross-file sign/strength stability | association candidate |
| GDN | normal multivariate next-value prediction | embedding graph의 seed frequency/cosine | learned-graph candidate |

세 arm의 score 단위는 다르며 비교·정규화하지 않는다. 어느 arm이 과학적으로 우수한지는 이 구현 감사로 판정할 수 없다.

## 8. Top-20은 어떻게 정해지는가

C0 protocol은 test1 outcome 전에 primary `k=20`, sensitivity `k=10/40`을 공통 정책으로 사전등록했다. 각 arm은 하나의 frozen ranking에서 prefix만 취하며 재정렬하거나 padding하지 않는다. 다만 왜 20이 과학적으로 최적인지에 대한 추가 rationale는 source에 없어 `RATIONALE_UNDOCUMENTED`다.

META는 supported 30이라 Top-40이 10개 부족하고, GDN은 supported 39라 1개 부족하다. STAT은 Top-40이 완성된다. Frozen union은 각 arm의 Top-20만 소비한다.

## 9. 47개 후보는 어떻게 만들어지는가

`integrate_candidate_union_v1`은 META→STAT→GDN 순으로 각 Top-20 pair를 읽고 exact `(source,target)` key로 중복을 접는다. arm rank와 method-specific evidence/provenance는 보존한다. global score와 global scientific rank는 만들지 않는다.

- META-only 8
- STAT-only 8
- GDN-only 18
- exactly two arms 13 (META+STAT 11, META+GDN 1, STAT+GDN 1)
- all three 0
- unique union 47

Serialization order는 stable encounter order이지 과학 순위가 아니다. Pair-level public-safe provenance는 `ARCH_002_CANDIDATE_PROVENANCE.csv`에 기록했다.

## 10. 이 단계에서 아직 모르는 것

GDN이 META/STAT보다 안정적이고 고유하며 유용한 confirmed relation을 제공하는지 모른다. META와 STAT의 상대적 contribution도 검증되지 않았다. Top-k 민감도, seed/split stability, unique confirmed yield, diagonal removal을 포함한 pre-Top-5 edge/source masking functional impact는 향후 EXP-01 대상이다. `GDN-Functional`은 네 번째 discovery arm이 아니라 validation procedure다.

## 11. 코드와 문서의 차이

현재 RCC core 설명은 `learned graph candidate`, `unscored union`, `non-causal` 경계를 지켜 source와 일치한다. 남은 주요 오독 위험은 learned graph와 attention의 혼동, GDN edge의 temporal/causal 과장, 37-node Top-5 후 144-pair projection이라는 실제 mask 순서, generic smoke backend와 passing GDNP path의 혼동이다. 상세 항목은 `ARCH_002_MISMATCHES.md`에 보존했다.

## 12. 다음 Relation Profiling 단계와의 연결

47개 cohort artifact 자체는 `relation_confirmation=not_evaluated`와 `relation_profiling_executed=false`를 기록한다. 후속 profiling이 normal step events와 response evidence를 사용해 방향·horizon을 확인한다. 이 경계를 건너기 전에는 47개를 “최종 관계”라고 부를 수 없다. 상세 검토는 **ARCH-003 — Relation Profiling & Numeric Authority Deep Audit**이다.
