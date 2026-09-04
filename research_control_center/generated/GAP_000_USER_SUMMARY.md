<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=ff5895a48395a92c97930f1c6b72d5583c95b0df7eb675bbe21b768d168a8b6a authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# 본격 실험 전에 무엇을 고쳐야 하는가

## 지금까지 감사 결과 한 문장

ARCH-000~010의 120개 mismatch는 19개 root issue로 줄어들며, frozen pilot을
무효화하는 결함은 발견되지 않았지만 미래 final validation 전에 닫아야 할 authority, custody,
evaluation-design gate가 있다.

## 현재 연구를 무효로 만드는 문제가 발견됐는가

아니다. 무효화된 frozen artifact는 0개다. 현재 pilot은 V4 authority, D1의 더 약한 in-memory
pre-label gate, test1 development scope, 14 contiguous event units, held-out 부재라는 조건을 붙여
해석할 수 있다. 새 remediation은 PILOT V1을 고치지 않고 VALIDATION V2로 version을 나눈다.

## 반드시 고쳐야 하는 것

1. `P0_FIX_BEFORE_EXPANDED_VALIDATION`이었던 최종 scientific execution authority는 Formal V4로 결정·version 고정됐고,
   version과 test를 고정한다.
2. 새 D1 evaluation은 prediction을 label 전에 atomic persist, close, reopen/replay하고 label access를
   authorize해야 한다.

## 특정 실험 전에만 고치면 되는 것

아래는 primary disposition `P1_FIX_BEFORE_SPECIFIC_EXPERIMENT`이다. Urgency priority P1과 같은 축이 아니다.

- EXP-01 전: GDN Top-5 self-neighbor convention을 고치거나 명시적으로 ablation한다.
- EXP-03 전: `no_rule`과 provider/parse/verifier/budget failure를 분리한다.
- EXP-05 전: 실제 evaluated trace와 deterministic explanation renderer를 연결한다.

## 코드 문제가 아니라 실험 설계 문제인 것

- validation과 final test 역할, fusion policy selection 시점을 미리 고정한다.
- 14개를 독립 사건이라고 가정하지 말고 event-unit 정책과 분석 방법을 사전등록한다.
- EXP-04 final claim에는 PCA-SPE 외 stronger multivariate detector가 필요하다.
- GDN contribution은 seed/split stability, unique confirmed yield, masking, Top-20 sensitivity로 검증한다.
- Agentic contribution은 budget-matched 반복 실험에서 feedback이 실제 작동하고 이득을 보이는지 본다.

## 그냥 limitation으로 남겨도 되는 것

- train3가 normal-only relation confirmation과 D0 calibration에 함께 쓰였다는 점.
- 현재 D1 high FAR의 일반 원인이 아직 분석되지 않았다는 점.
- explanation의 인간 유용성이 아직 평가되지 않았다는 점.

## 지금 하지 않아도 되는 것

Runtime LLM, causal discovery, 복잡한 hierarchy/tree relation, multi-agent runtime, production fusion,
대규모 human study는 현재 석사 논문의 최소 경로에 필요하지 않다.

## 가장 안전한 다음 진행 순서

1. 완료된 GAP-000과 read-only ARCH-011의 사실을 검토한다.
2. final authority를 결정한다.
3. 승인된 authority remediation만 좁게 구현한다.
4. 필요한 실험별 P1만 닫고 protocol을 결과 전에 freeze한다.
5. development/validation 실험 뒤 fresh-machine rehearsal을 완료한다.
6. 마지막에 새 preregistered held-out study를 한 번 실행한다.

## 내가 결정해야 하는 것

1. Final authority는 Formal V4로 결정됐다. 다음 결정 전 작업은 durable custody와 protocol freeze다.
2. Graph-Guided와 Agentic의 conditional 유지 정책은 이미 승인되었다. 최종 포함 여부는 EXP-01/EXP-03
   결과가 결정한다.

기억할 한 문장: **pilot은 보존하고, final validation에 꼭 필요한 authority와 custody만 먼저 고친다.**

다음 task는 **DG-04 후속 정상 준비 — BLOCKED_NORMAL_DATA_CUSTODY (schema-only projection 범위 확인)**이다. ARCH-011은 이 remediation이나 test2 access를
자동으로 허가하지 않는다.

## 현재 DG-04 / 외부 준비 Gate

DG-04 / DEC-025 승인 완료. DG-03B_REVISED 승인 후 동결한 EXP-03B에서 T2는 T1-B 대비 이점이 있으나 T0보다 우수하지 않았습니다. T0 22 Rules, T2 Repeat 1 21 Rules는 별도 HELDOUT_CANDIDATE이며 V2A39·기존 결과는 불변입니다.

Stage B는 BLOCKED_NORMAL_DATA_CUSTODY. 공식 정상 train1 두 컨테이너의 byte identity 검증 후 embedded label schema에서 중단했습니다. label 값 해석·과학 사용 0이며 정상 컨테이너 byte traversal은 있었습니다. 추가 header 접근 자동심사를 우회하지 않았습니다. Schema-only label 식별 및 feature-only projection 범위를 확인해야 합니다.

외부 STAT/GDN/T0 미실행, DG-03C N/token/cost 미정. eTaPR109 synthetic per-file 일치; 버전 내 집계는 미정. Provider·credential·공격 payload 0. 상세: validation_v2/dg04_xver_prep/CURRENT_PREPARATION_STATUS_V1.md. 전체 task PASS가 아니며 integration merge/push·교수 제출은 하지 않습니다.
