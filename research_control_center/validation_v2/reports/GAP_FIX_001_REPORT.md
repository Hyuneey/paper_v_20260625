# GAP-FIX-001 — Formal V4 Authority Contract & Conformance Freeze

## 결론

**PASS — VALIDATION V2는 별도 Formal V4 authority를 사용한다.**

Canonical RuleV1/VerifierV1 → V4 bridge는 lossless equivalence가 입증되지 않았으므로 강제하지 않았다. 이 선택은 PILOT V1을 해석하거나 마이그레이션하지 않는다. Canonical RuleV1과 VerifierV1이 VALIDATION V2 실행을 직접 지배한다는 주장도 하지 않는다.

## 구현된 권한 경계

- `FormalV4RuleDescriptorV1`은 실제 byte-hash가 고정된 relation authority와 value-bearing numeric authority record에 정확히 재결속된다.
- runtime authorization은 source commit, runtime config, evaluator implementation bytes, relation/numeric authority, feature/file/sampling contract를 모두 재검증한다.
- numeric value는 caller가 전달하지 않는다. bound numeric authority artifact에서 읽고 `(relation, role, reference, value)` hash를 다시 계산한다.
- evaluator의 trigger/response/trace policy hash는 `runtime_policy_v1.py`의 고정 상수와 일치해야 한다.
- target response start index는 `event_index + selected_horizon_seconds`와 같아야 한다.
- held-out split, stale commit, wrong authority, mutated artifact, forged capability, path traversal을 fail-closed로 거부한다.
- JSON schema는 wheel에 항상 포함되는 Python module에 내장되며, source checkout에서는 사람이 읽는 JSON schema와 동일한지 추가 확인한다.

## 범위 한계

현재 PASS는 **authority와 이미 materialized된 observation window의 deterministic conformance**에 대한 것이다.

아직 완료되지 않은 항목:

- scientific frame에서 observation window를 만드는 V2 adapter
- durable D1 prediction-before-label custody
- development/final split protocol freeze
- scientific execution 및 결과

따라서 GAP-FIX-001 PASS는 scientific execution readiness 또는 scientific validation PASS가 아니다.

## 검증

- 독립 QA adversarial/focused tests: 13/13 PASS
- coordinator focused tests: 9/9 PASS
- RCC/UI regression: 126/126 PASS
- package compile: PASS
- wheel build/install/schema import: PASS
- PILOT V1 Git-tree preservation: 3,021/3,021 blobs PASS
- scientific execution: 0
- test2/held-out access: 0
- provider call: 0
- private exposure: 0

## 다음 gate

`GAP-FIX-002 — Durable D1 Prediction-before-label Gate`
