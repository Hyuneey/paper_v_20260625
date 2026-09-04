# DG04-XVER-PREP-001 — 현재 승인된 방법 고정

DEC-025 / DG-04: APPROVED_WITH_SCOPED_AGENTIC_CLAIM. 제목: Verifier-Guided Agentic Relational Rule Induction with GDN-Based Learned-Graph Evidence for Explainable Multivariate Time-Series Anomaly Detection

동결 정상-only EXP-03B에서 T2는 matched-maximum-budget T1-B 대비 의미적 유도를 개선했지만 주요 지표에서 T0보다 우수하지 않았습니다. GDN은 핵심 learned-graph evidence 모듈이며 후보·탐지·수치 권한이 아닙니다. Fusion은 기여가 아닌 사전등록 비교입니다.

T0 단일 출력 및 T2 Repeat 1의 기존 guard-retained Rule만 별도 HELDOUT_CANDIDATE로 고정했습니다. V2A39 reference·EXP03B·EXP02·EXP04/05·PILOT 결과는 보존합니다. Stage B는 HAI22/21 정상-only 준비 중이며 provider는 DG-03C, 공격은 DG-05, 교수 제출은 DG-06 별도 승인입니다. 추가 Agentic rescue 없음.

## 이전 기록 — 역사적 상태

# VALIDATION V2 방법

후보 prior는 META+STAT입니다. META는 공식 process graph와 reviewed semantic metadata의 hybrid이며 완전 자동 graph extraction이라고 설명하지 않습니다. 정상 관계 분석/확인은 29 candidate pairs에서 21 confirmed pairs, 39 directional relations를 만들었습니다.

수치는 정상 train1/train2로 도출하고 train4에서 동결된 EXP-02 기준으로 선택한 RELATION_SPECIFIC_NORMAL_ONLY_V1:n7-q0.90-s2-f0.05입니다. 이후 test1을 보고 수치를 선택하거나 수정하지 않았습니다.

VALIDATION V2 formally adopts the versioned V4 relational-rule descriptor and its deterministic validity, numeric binding, replay, portfolio-freeze, and runtime-authorization controls as the scientific execution authority. Canonical RuleV1/VerifierV1은 adjacent components이고 lossless canonical→V4 bridge를 주장하지 않습니다.

PCA와 fixed Isolation Forest는 train1/train2 fit, train3 calibration입니다. Rule-only와 same-second distinct-source confirm2 fusion을 포함한 5개 예측을 durable freeze/replay한 후 label을 해석했습니다. fixed runtime은 deterministic·LLM-free입니다.

GDN은 별도 normal-only EXP-01C의 predictive supporting evidence를 제공하며 설명 sidecar 외에는 runtime에 입력되지 않습니다. 자동 EXP-05는 실제 native trace와 deterministic explanation의 structural fidelity만 평가합니다. test1=DEVELOPMENT_ONLY, held-out과 human usefulness는 미검증입니다.
