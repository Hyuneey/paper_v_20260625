# EXP-04 grouped fusion 성능 개선

상태: `IMPLEMENTED_SYNTHETIC_CONFORMANCE_PASS_NOT_YET_SCIENTIFICALLY_EXECUTED`

## 문제

`fuse_detector_with_rules_v1`은 durable D0/D1 prediction과 Formal V4 authority를
재생한 뒤에도 같은 in-memory collection을 반복 순회했다.

- D0 dense coordinate collection: 3회
- D1 dense coordinate collection: 2회
- `rule_outcomes`: 2회
- 전체 D0 coordinate 정렬: `tuple(sorted(set(coordinates)))`
- 최종 좌표마다 동일 distinct-source set 조회: 3회

이는 fusion 정책 자체와 무관한 Python collection 처리 비용이다.

## 변경

과학적 정책을 그대로 둔 채 다음 grouped path로 교체했다.

1. D0/D1 record를 한 번 paired scan해 길이, 정렬·고유 좌표, 동일 coordinate
   census와 feature-file identity map을 검증한다.
2. `rule_outcomes`를 정확히 한 번 순회한다.
3. 각 `(file_id, row_index)`에 대해 distinct source set, rule ID list, trace hash
   list를 동시에 집계한다.
4. paired dense row를 한 번 순회해 frozen D1 FAIL census를 검증하고 D2 decision을
   즉시 만든다.
5. coordinate별 source/rule/trace 정렬은 각 group에서 한 번만 수행한다.

결과적으로 in-memory 핵심 순회는 다음처럼 줄었다.

| 대상 | 이전 | 현재 |
|---|---:|---:|
| D0/D1 dense collection pass | 5 | 2 |
| `rule_outcomes` pass | 2 | 1 |
| 전체 coordinate set+sort | 1 | 0 |
| 최종 coordinate source lookup | 3 | 1 |

Durable file replay, Formal V4 authority replay, custody, prediction hashes는 이 변경
앞단에서 기존대로 수행된다.

## 동치 경계

다음 frozen policy는 변경하지 않았다.

- eligible outcome: `FAIL` only
- coordinate: same `file_id` + `row_index`
- source rule: distinct `source_id`
- admission: distinct sources >= 2
- base preservation: pointwise `D0 OR rule_addition`
- PASS / ABSTAIN: rule addition에 포함하지 않음
- D1 durable FAIL census: rule ID와 trace hash까지 exact match
- foreign coordinate/source/descriptor/runtime authority: fail-closed

`EXP04_FUSION_POLICY_ID`와 `EXP04_FUSION_POLICY_HASH` 정의는 바꾸지 않았다.

## 합성 검증

- 기존 EXP-04 policy/custody negative tests: PASS
- PASS/FAIL/ABSTAIN, D0 base alarm, single-source, two-source 조합을 포함한 독립
  정책 reference 비교: exact tuple equality PASS
- `rule_outcomes` 단일 순회 구조 regression guard: PASS
- repeated coordinate sort/lookup 제거 guard: PASS
- focused EXP-04 tests: 9 PASS
- VALIDATION V2 suite: 312 tests OK, 6 expected skips 포함
- RCC suite: 165 tests PASS

이는 synthetic implementation evidence이며 scientific fusion 성능 결과가 아니다.

## 과학적 안전

- fusion policy/config/hash semantics: 변경 0
- architecture/hyperparameter/seed/dtype: 변경 0
- data/split/protocol/preregistration: 변경 0
- metric/threshold: 변경 0
- scientific execution: 0
- test1/test2/held-out/label access: 0
- PILOT V1 변경: 0
- frozen artifact/result 변경: 0

## 남은 병목

이 함수의 durable upstream artifact replay는 scientific custody이므로 제거하지 않았다.
실제 EXP-04 runner가 동결되면 앞선 HAI shared feature session과 이번 grouped fusion을
연결할 수 있다. 그 전에는 실제 처리시간 개선을 주장하지 않는다.
