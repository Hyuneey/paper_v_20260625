<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=9e16b8482351007c7c7a47539230833ee5dd6560378b6076c1b19590c09d011a authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
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

다음 task는 **MULTIPANEL-PRE-DG05-FREEZE-001**이다. ARCH-011은 이 remediation을 실행하지 않았다.

## 현재 DG-04 / 외부 준비 Gate

XVER-T2-PROVIDER-EXEC-001: COMPLETE_NORMAL_ONLY / QA PASS.
정확한 snapshot gpt-5.4-mini-2026-03-17로 HAI22 61회, HAI21 61회, 합계 122회 호출했습니다. retry/fallback/tools/4차 호출은 0이며 EVENT10은 전송하지 않았습니다.
실제 계량 사용량은 입력 333954 / 출력 13563 / 합계 347517 tokens이고 표준 공개가격 단순 산식은 USD 0.311499입니다. 이는 청구서가 아닙니다.
HAI22 T2는 train2 입장 20 pairs, 정상 확인 31 Rules, Formal V4 31, train4 유지 19 Rules/16 pairs입니다.
HAI21 T2는 train2 입장 18 pairs, 정상 확인 9 Rules, Formal V4 9, Block B 유지 2 Rules/1 pairs입니다.
두 결과는 HELDOUT_CANDIDATE이며 공격 검증·production·T2>T0 일반화 결론이 아닙니다. T0/T2/V2A는 별도 사전등록 방법으로 유지하며 선택하지 않았습니다.
모든 provider 출력과 admission을 양 버전에서 먼저 닫은 뒤 train3/Block A, SCI02B, Formal V4, 단방향 guard를 수행했습니다. 공격/test/label/real eligibility 접근은 0입니다.
DG-XVER-PROVIDER는 승인·실행 완료. DG05는 NOT_APPROVED, 교수 package는 NOT_SUBMITTED, DG06 필수입니다.
정확한 다음 작업은 MULTIPANEL-PRE-DG05-FREEZE-001이며 multi-file aggregation, empty-input, secondary P1 해석과 최종 prediction-before-label custody를 공격 접근 전에 고정합니다. 백업은 SINGLE_COPY_LOCAL_ONLY입니다.
