<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=e292a040dcb35b3efff4ed02d623232f7b57003aed48ecac5716df16332272a7 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# GPT Brief — Research Control Center

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
다음: DG-03 provider 예산·승인 검토. DG-04 제목, DG-05 attack panel, DG-06 실제 제출은 별도 Gate입니다.


Scientific authority: `origin/research-v6-thesis-checkpoint` @ `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`.

> Chat memory must not override the scientific authority or RCC registry.

## Research objective

Graph-guided, training-time agentic verified rule construction for explainable multivariate time-series anomaly detection.

## Current phase

**EVALUATION_SCOPE_EXPANSION** — V2A 개발 결과는 immutable이다. 향후 평가는 HAI23 test2 primary held-out와 HAI22/21 external replications로 version 분리하며 146 nominal scenarios를 IID로 합치지 않는다. 공격 접근은 DG-05 전 0이다.

## How to read RCC status

`audited=true`는 Evidence-reviewed이며 scientific validation이 아니다.
A Result-integrity audit checks custody and arithmetic, not generalization.
이 상태들은 not a single completion percentage다. claim은 claims.csv가 관리한다.

    ## Architecture in one line

HAI provenance and P1 scope -> frozen role universe -> META / STAT / GDN -> unscored candidate union -> normal relation profiling -> construction evidence -> T0 / T1 / T1-B / T2 -> task deterministic verifier; T0 / T1 / T1-B equivalence -> COMMON-42 metadata plus private runtime numeric authority -> real D1; HAI plus frozen detector authority -> D0; frozen D0 + D1 -> D2 policies -> event / episode metrics -> result-integrity governance

## Data and split boundary

HAI 23.05 P1 is selected. train1/train2 fit normal evidence; train3 confirms relations and
calibrates D0; train4 is a guard. test1 is development evidence. OUTER produced no result.
PILOT V1 D1 lacks durable pre-label persistence; PILOT V1 D2 V2 is test1-informed.
VALIDATION V2 completed durable five-method prediction replay before its one-shot label access.

## Evaluation expansion boundary

The frozen 14-scenario test1 result remains DEVELOPMENT_ONLY and will not be reopened.
The prospective panels are HAI 23.05 test2 as PRIMARY_HELDOUT and HAI 22.04 plus
HAI 21.03 as version-separated external replications. Their 146 nominal scenarios are
not IID and one pooled Recall is prohibited as the primary result. DG-05 is mandatory
before any new attack payload or label access; DG-03 is the exact current decision gate.

## Candidate-discovery boundary

    PILOT V1은 47-pair union을 보존한다. V2 EXP-01은 META_PLUS_STAT을 선택했고,
    EXP-01B는 GDN-XAI arm을 동일 예산으로 비교한 뒤 `GDN_ABLATION_ONLY`로 끝났다.
    META provenance는 `HYBRID_REVIEWED_METADATA`이고,
    researcher intervention은 `HUMAN_INTERVENTION_LEVEL_1`이다.
    exact replay에는 private reviewed semantic declaration이 필요하므로 공개 재현 상태는
    `PARTIALLY_REPRODUCIBLE_PRIVATE_REVIEWED_INPUT_REQUIRED`이다.

## Relation and numeric-authority boundary

The lineage is 47 pairs → 94 directions → 25/45 fit-supported → 23/42 confirmed. Confirmation
cannot search or retune. Construction and runtime numeric identities remain separate. Repeated
normal response is not causal proof.

## Rule-construction boundary

E3 exposes a fixed relation, horizon, and normal-only references to a closed proposal schema.
`accepted_proposal` grants neither runtime authority nor detection performance. T2 feedback was zero.

## Frozen pilot runtime boundary

D1 is COMMON-42 Verified Relational Rule-only, not T2 Agentic Rule-only. D0 is the frozen
37-feature PCA-SPE baseline. D2 V1/V2 preserved D0 pointwise and recovered 0/3 misses;
their development-only FAR increased. PILOT V1 lacks the later V2 durable custody gate.

## How we got here

    History cannot override current state. ARGOS remains partial support.

## Established boundary

Frozen discovery, construction, runtime, and integrity artifacts establish execution and custody,
not causality, physical truth, general GDN utility, agentic-feedback advantage, or generalization.
T2 feedback actions were zero.

## Frozen INNER pilot observations

The INNER evaluation contains 14 contiguous attack-event units; statistical independence is
not established. D0 PCA-SPE responded to
11/14 with Normal FAR 0.4939336325682589 episodes/hour. D1 verified Rule-only responded
to 13/14 with Normal FAR 40.50255787059723 episodes/hour. Their event overlap was both
10, D0-only 1, D1-only 3, neither 0. D2 V1 and D2 V2 each responded to 11/14 and each
recovered 0/3 D0-missed events; their Normal FAR values were 0.7056194750975128 and
6.915070855955625 episodes/hour respectively. These are exact public frozen pilot
observations, not new calculations.

> These 14 units are pilot evidence only, not validated performance.

## Unresolved scientific questions

- GDN general utility beyond the current normal-only EXP-01 and EXP-01B scope
- Agentic verifier-feedback advantage
- Practical Rule-only operational utility
- Detector-plus-Rule improvement
- Held-out generalization
- Human explanation usefulness

    Graph-Guided and Agentic remain provisional contribution labels. EXP-01 and EXP-01B do not
    support GDN under their original protocols. Later EXP-01C provides LEARNED_GRAPH_SUPPORTING
    evidence only; it does not replace the META+STAT discovery policy. DG-04 controls final wording. T2
    feedback advantage also remains unsupported.

## Claim boundaries

- **CLAIM-A · SUPPORTED_IMPLEMENTATION** — The pinned HAI P1 INNER architecture and its frozen execution paths were implemented.
- **CLAIM-B · SUPPORTED_IMPLEMENTATION** — The implemented pipeline transformed confirmed normal-data relation evidence into frozen executable rules under deterministic authority controls.
- **CLAIM-C · SUPPORTED_IMPLEMENTATION** — VerifierV1 deterministically checks its canonical contract; VALIDATION V2 executable eligibility is separately governed by Formal V4 validity replay numeric binding portfolio-freeze runtime-authorization and custody controls.
- **CLAIM-D · SUPPORTED_IMPLEMENTATION** — Given frozen Formal V4 descriptor validity numeric-reference portfolio runtime-authorization and input authorities the fixed-rule VALIDATION V2 runtime evaluates without an LLM and produces deterministic traces.
- **CLAIM-E · DEVELOPMENT_NOT_SUPPORTED** — EXP-01/01B 음성 결과 유지. 별도 EXP-01C는 LEARNED_GRAPH_SUPPORTING이며2pair의 일부 horizon이 V2A와 겹친다. GDN은 primary discovery나 detector가 아니다.
- **CLAIM-F · NOT_SUPPORTED** — The current pilot did not establish a feedback advantage and the feedback mechanism was not empirically exercised.
- **CLAIM-G · DEVELOPMENT_SUPPORTED** — Rule-only 반응은 PCA미탐2/3 및 IF미탐6/9이다. 고정 fusion의 실제 회수는 둘다0이다.
- **CLAIM-H · UNVALIDATED** — V2A Rule-only는11/14이나 정상 FAR37.6095/hour로 운영 효용은 미검증이다.
- **CLAIM-I · DEVELOPMENT_NOT_SUPPORTED** — 두 V2 frozen confirm2 fusion은 기준 detector Recall을 개선하지 못하고 정상false episodes를2개씩 늘렸다. V1 음성 결과도 보존한다.
- **CLAIM-J · NOT_SUPPORTED** — Held-out generalization remains unconfirmed because no OUTER scientific result is available.
- **CLAIM-K · DEVELOPMENT_SUPPORTED** — 실제6418trace 전체에서11개 automated structural checks가 PASS했다. GDN clauses130개는 원래 outcome을 바꾸지 않았다.
- **CLAIM-L · UNVALIDATED** — A trace-grounded explanation interface is implemented; human usefulness has not been evaluated.
- **CLAIM-M · NOT_SUPPORTED** — The system records bounded temporal relation evidence and trace-grounded violations without causal attribution.
- **CLAIM-N · UNVALIDATED** — A version-separated preregistered evaluation plan exists; no new attack panel result exists.

## Current execution gates

EXP-03 awaits DG-03. Final contribution wording awaits DG-04; all new attack panels await DG-05;
professor submission awaits DG-06. Cross-version P1 compatibility remains unresolved.

## Top user TODO

- DG-03에서 EXP-03 provider/model과 819-call·5,031,936-token 상한을 검토한다. 승인 전 호출은 0이다.
- 다중 HAI plan은 승인됐지만 실제 P1 denominator와 공격 결과는 아직 없음을 확인한다.
- DG-04 제목·기여, DG-05 attack panel, DG-06 교수님 제출을 각각 별도로 검토한다.

## Exact next task

Management: **DG-03 — EXP-03 Provider Execution Decision**

Following architecture review: **NONE — ARCH-000 through ARCH-011 complete**
