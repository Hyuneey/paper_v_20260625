<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=ff5895a48395a92c97930f1c6b72d5583c95b0df7eb675bbe21b768d168a8b6a authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
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

다음 task는 **DG-04 후속 정상 준비 — BLOCKED_NORMAL_DATA_CUSTODY (schema-only projection 범위 확인)**이다. ARCH-011은 이 remediation을 실행하지 않았다.

## 현재 DG-04 / 외부 준비 Gate

DG-04 / DEC-025 승인 완료. DG-03B_REVISED 승인 후 동결한 EXP-03B에서 T2는 T1-B 대비 이점이 있으나 T0보다 우수하지 않았습니다. T0 22 Rules, T2 Repeat 1 21 Rules는 별도 HELDOUT_CANDIDATE이며 V2A39·기존 결과는 불변입니다.

Stage B는 BLOCKED_NORMAL_DATA_CUSTODY. 공식 정상 train1 두 컨테이너의 byte identity 검증 후 embedded label schema에서 중단했습니다. label 값 해석·과학 사용 0이며 정상 컨테이너 byte traversal은 있었습니다. 추가 header 접근 자동심사를 우회하지 않았습니다. Schema-only label 식별 및 feature-only projection 범위를 확인해야 합니다.

외부 STAT/GDN/T0 미실행, DG-03C N/token/cost 미정. eTaPR109 synthetic per-file 일치; 버전 내 집계는 미정. Provider·credential·공격 payload 0. 상세: validation_v2/dg04_xver_prep/CURRENT_PREPARATION_STATUS_V1.md. 전체 task PASS가 아니며 integration merge/push·교수 제출은 하지 않습니다.
