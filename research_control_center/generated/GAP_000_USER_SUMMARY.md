<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=0679baf23b38ac292c9ec0334debce0277b7bbb1b7d17558ff90374c40286fe3 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
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

다음 task는 **DG-XVER-PROVIDER**이다. ARCH-011은 이 remediation이나 test2 access를
자동으로 허가하지 않는다.

## 현재 DG-04 / 외부 준비 Gate

HAI-XVER-NORMAL-PREP-001: 정상-only 실행 완료, 독립 최종 QA PASS. DG-XVER-PROVIDER에서 정지합니다.
HAI22/HAI21 GDN은 각각6회, 총12회입니다. GLOBAL5는 train1 provider / train2 retrieval, EVENT10은 보조 분석 전용이며 융합·후보·verifier·T0·숫자·guard 사용을 금지합니다.
HAI22 T0: 13 Rules/12 pairs. HAI21 T0: 7 Rules/5 pairs. 모두 HELDOUT_CANDIDATE, 공격 검증·production 결과가 아닙니다.
T2 provider/retrieval packs와 정확 예산은 버전별 고정됐습니다. 합계 최대 174 calls, 3622912 tokens, 표준 공개가격 상한 USD 4.06이며 실제 지출이 아닙니다.
DG-XVER-PROVIDER는 USER_DECISION_REQUIRED; provider/credential/공격 접근0. DG05 NOT_APPROVED; 교수 package NOT_SUBMITTED; DG06 필수.
DEC025 제목·claim·HAI23 V2A/T0/T2·EXP03B·EXP02·EXP04/05·PILOT 결과 불변. T2>T1-B는 정상 의미 유도에 한정하며 T0보다 우수하지 않습니다.
후보 권한 META+STAT, GDN은 비인과적 learned-graph evidence, SCI02B 고정 숫자 결합, FormalV4 실행권한, guard 단방향. 37정책 재선택·META 재구성·best seed 없음.
eTaPR109 합성/가상 동등성 PASS. 다중파일/empty/secondary P1 해석은 DG05 전 결정 항목으로 유지하며 실제 eligibility는 생성하지 않았습니다. 백업 SINGLE_COPY_LOCAL_ONLY.
