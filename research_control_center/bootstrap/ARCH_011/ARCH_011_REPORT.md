# 이 연구를 다른 환경에서도 다시 돌릴 수 있는가

## 1. 현재 OUTER에는 왜 결과가 없는가

기존 OUTER는 HAI 23.05 test2에서 D0, D1, D2 V1을 한 번만 확인하려던 confirmatory study였다.
한 번의 과학 시도가 시작된 뒤 첫 test2 feature custody 조건이 거절되었고, feature file을 열거나
읽기 전에 정지했다. 따라서 scientific result는 `UNAVAILABLE`, generalization은 `UNCONFIRMED`다.

## 2. test2를 실제로 읽었는가

Custody-level feature-file check는 1회 있었다. 그러나 feature byte read, hash, semantic parse,
label access, prediction, metric, outcome exposure는 모두 0이었다. 그러므로 “완전히 접촉하지 않았다”와
“과학적으로 읽었다”는 표현이 모두 부정확하다.

## 3. 기존 OUTER를 다시 실행하면 되는가

아니다. 단 한 번의 authorized attempt가 소비되었고 retry budget은 0이다. 구 protocol은
`NOT_RETRYABLE_BY_PROTOCOL`이다. 새 실행에는 새 study identity, authority, preregistration이 필요하다.

## 4. 새로운 held-out 검증은 무엇이 달라야 하는가

Data identity, feature/event-unit contract, development/validation/final 역할, final Rule/runtime authority,
stronger detector, fusion policy, metrics, durable prediction-before-label custody, reporting plan을 결과 전에
고정해야 한다. 같은 물리적 test2를 쓸 수 있는지는 content seal이 보존되었다는 사실만으로 결정되지
않으며 `STUDY_DESIGN_REQUIRED`다.

## 5. 현재 무엇까지 재현 가능한가

Traceability는 강하다. 같은 환경의 frozen artifact integrity replay도 부분적으로 가능하다. 반면 fresh
machine synthetic end-to-end와 scientific recomputation은 실행으로 입증되지 않았다. External full
reproduction은 private assets와 redistribution boundary 때문에 현재 불가능하다.

## 6. 같은 PC에서의 재현과 새 PC 재현은 무엇이 다른가

같은 PC에는 local custody와 과거 environment가 남아 있을 수 있다. 새 PC는 Python/package lock,
schema resources, Git authority, private asset restoration, numeric backend identity를 모두 다시 구성해야
한다. 동일 SHA만으로 동일 scientific environment가 만들어지는 것은 아니다.

## 7. 어떤 private asset이 필요한가

Raw HAI payload, private label/test2 custody, D0 preprocessing/model/threshold authority, relation/runtime
numeric authority, task-specific registries와 locators가 필요하다. 공개 release에는 payload나 path가 아니라
logical ID, hash, schema, restoration contract만 포함해야 한다.

## 8. 현재 환경 의존성

Core metadata는 Python >=3.11과 jsonschema 4.26.0을 선언한다. 하지만 scientific NumPy 2.3.5와 test
tooling은 project metadata에 완전히 선언되지 않았고 root lock이 없다. GDN의 exact environment는
CPython 3.12.13, windows-amd64, CPU, exact wheels와 external roots에 결속된다.

## 9. 절대경로·운영체제 의존성

Current core는 대체로 relative path와 explicit encoding을 사용한다. 그러나 schema loader는 source-tree
layout을 가정하고, scientific custody는 local environment bindings를 요구하며, exact GDN은 Windows
platform contract다. Historical absolute host paths는 frozen provenance이며 current recipe가 아니다.

## 10. PILOT V1은 어떻게 보존할 것인가

PILOT V1 artifacts와 현재 qualification을 그대로 보존한다. 새 lock, bridge, durable gate 또는 protocol을
과거 artifact에 소급 적용하지 않는다.

## 11. VALIDATION V2는 어떻게 분리할 것인가

새 method/config/authority/environment/experiment IDs와 prediction schema version을 사용한다. V1 hashes와
결과는 immutable predecessor로 참조하고, V2 결과만 remediated method의 evidence가 된다.

## 12. Final execution authority 선택지

RuleV1-only는 conceptual clarity가 높지만 V4 cohort/semantics를 바꿀 위험과 큰 이관 부담이 있다. Formal
V4는 가장 작은 구현 범위지만 canonical verifier claim을 좁혀야 한다. Verified canonical-to-V4 bridge는
V4 runtime 보존과 canonical admissibility를 함께 노릴 수 있으나 lossless mapping과 conformance test가
필수다. 현재 권고는 bridge를 우선 검증하고, lossless equivalence가 증명되지 않으면 formal V4로 범위를
좁히는 것이다. 이 선택은 아직 DEC-020으로 최종 승인되어야 한다.

## 13. Fresh-machine rehearsal 계획

Clone, public dependency install, import/static verification, RCC tests, synthetic contract, synthetic
candidate-to-metric smoke, public artifact restoration 순서로 진행하고 과학 데이터 전에 멈춘다. Authority와
dependency remediation 후, held-out access 전에 실행하는 것이 가장 안전하다.

## 14. 논문 제출 시 공개 가능한 범위

Source, schemas, tests, synthetic fixture, public configs, RCC docs, sanitized example artifacts, dependency
lock과 reproduction guide는 공개 가능하다. Raw/private data, credentials, private locators, restricted numeric
payload, sealed labels/test2, private provider payload는 제외한다.

## 15. 다음 remediation에서 꼭 고쳐야 할 것

첫 순서는 final authority decision과 versioned bridge contract/conformance freeze다. 이어서 D1 durable
pre-label persistence를 구현하고, environment lock/schema packaging/entrypoint를 scientific held-out 전에
fresh-machine rehearsal로 검증한다. ARCH-011은 어떤 remediation도 구현하지 않았다.
