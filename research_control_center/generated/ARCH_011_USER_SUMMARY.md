<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=0679baf23b38ac292c9ec0334debce0277b7bbb1b7d17558ff90374c40286fe3 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# OUTER와 재현성을 쉽게 이해하기

## 1. OUTER가 정확히 무엇인가?

개발에 쓰지 않은 held-out test2에서 frozen D0/D1/D2 V1을 한 번 확인하려던 confirmatory study다.

## 2. 왜 결과가 없는가?

유일한 시도가 시작된 뒤 첫 feature custody 검사에서 파일을 열기 전에 중단되었다. Prediction과 metric이 없으므로 성능 결과도 없다.

## 3. test2 내용은 본 적이 있는가?

Custody check는 1회였지만 feature bytes/hash/parse와 labels는 모두 0이다. 즉 과학 내용은 보지 않았다.

## 4. 그냥 다시 실행하면 왜 안 되는가?

One-shot attempt가 소비되었고 retry 권한이 0이기 때문이다. 구 protocol은 `NOT_RETRYABLE_BY_PROTOCOL`이며 새 study와 preregistration이 필요하다.

## 5. 새 held-out은 어떻게 해야 하는가?

Data, method, authority, event unit, metrics, fusion policy, environment, prediction-before-label 순서를 결과 전에 고정해야 한다. 같은 test2 reuse 여부도 새 연구가 명시적으로 결정해야 한다.

## 6. traceability와 reproducibility는 뭐가 다른가?

Traceability는 source/artifact lineage를 찾는 능력이다. Reproducibility는 다른 환경에서 같은 절차와 출력을 다시 만드는 능력이다.

## 7. same-machine과 fresh-machine은 뭐가 다른가?

같은 PC에는 local asset과 environment가 남아 있다. Fresh machine은 dependency, schema, Git authority, private restoration을 처음부터 재구성해야 한다.

## 8. 현재 프로젝트는 어디까지 재현 가능한가?

Traceability는 `STRONG_SUPPORTED`이고 same-machine은 `PARTIAL_MODERATE`다. Fresh-machine synthetic/scientific reproduction은 아직 입증되지 않았다.

## 9. PILOT V1과 VALIDATION V2를 왜 나누는가?

과거 결과를 새 code와 protocol로 소급 변경하지 않기 위해서다. V1은 그대로 보존하고 remediation 결과는 V2로만 평가한다.

## 10. 어떤 authority option이 가장 현실적인가?

DEC-020은 lossless equivalence를 강제하지 않고 Formal V4를 별도 VALIDATION V2 authority로 선택했다. canonical RuleV1·VerifierV1 authority는 주장하지 않는다.

## 11. fresh-machine rehearsal은 언제 해야 하는가?

Authority/dependency/entrypoint remediation 뒤, held-out 접근 전이다. 첫 rehearsal은 synthetic/public 단계에서 멈춘다.

## 12. 논문 공개본에는 무엇을 포함해야 하는가?

Source, tests, schemas, synthetic fixture, public configs, RCC docs, lock과 guide를 포함한다. Raw/private data, test2, credentials, private numeric/model payload는 제외한다.

기억할 한 문장: **현재 연구는 잘 추적되지만, 새 컴퓨터에서 과학 결과를 다시 만드는 상태는 아직 아니다.**

다음 task는 **DG-XVER-PROVIDER**이다. ARCH-011은 이 remediation을 실행하지 않았다.

## 현재 DG-04 / 외부 준비 Gate

HAI-XVER-NORMAL-PREP-001: 정상-only 실행 완료, 독립 최종 QA PASS. DG-XVER-PROVIDER에서 정지합니다.
HAI22/HAI21 GDN은 각각6회, 총12회입니다. GLOBAL5는 train1 provider / train2 retrieval, EVENT10은 보조 분석 전용이며 융합·후보·verifier·T0·숫자·guard 사용을 금지합니다.
HAI22 T0: 13 Rules/12 pairs. HAI21 T0: 7 Rules/5 pairs. 모두 HELDOUT_CANDIDATE, 공격 검증·production 결과가 아닙니다.
T2 provider/retrieval packs와 정확 예산은 버전별 고정됐습니다. 합계 최대 174 calls, 3622912 tokens, 표준 공개가격 상한 USD 4.06이며 실제 지출이 아닙니다.
DG-XVER-PROVIDER는 USER_DECISION_REQUIRED; provider/credential/공격 접근0. DG05 NOT_APPROVED; 교수 package NOT_SUBMITTED; DG06 필수.
DEC025 제목·claim·HAI23 V2A/T0/T2·EXP03B·EXP02·EXP04/05·PILOT 결과 불변. T2>T1-B는 정상 의미 유도에 한정하며 T0보다 우수하지 않습니다.
후보 권한 META+STAT, GDN은 비인과적 learned-graph evidence, SCI02B 고정 숫자 결합, FormalV4 실행권한, guard 단방향. 37정책 재선택·META 재구성·best seed 없음.
eTaPR109 합성/가상 동등성 PASS. 다중파일/empty/secondary P1 해석은 DG05 전 결정 항목으로 유지하며 실제 eligibility는 생성하지 않았습니다. 백업 SINGLE_COPY_LOCAL_ONLY.
