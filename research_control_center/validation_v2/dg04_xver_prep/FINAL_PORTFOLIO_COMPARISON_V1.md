# 정상-only 포트폴리오 비교

포트폴리오 선택은 하지 않았습니다. V2A는 기존 reference, T0/T2는 별도 HELDOUT_CANDIDATE입니다. 공격·production 권한은 없습니다. T2는 Repeat 1만 사용했습니다.

| portfolio | pairs | retained Rules | sources | targets |
|---|---:|---:|---:|---:|
| T0 | 14 | 22 | 8 | 7 |
| T2 | 13 | 21 | 8 | 7 |
| V2A | 21 | 39 | 9 | 9 |

T0/T2 비교: {"pair_overlap": 12, "directional_overlap": 20, "exact_semantic_overlap": 20, "left_only_rules": 2, "right_only_rules": 1, "horizon_agreement": 20, "horizon_disagreement": 0, "direction_disagreement_pairs": 0}

Train4 census는 기존 arm-group cross-source isolation context에 결속되며 retained-only universe를 재평가한 결과가 아닙니다. V2A의 동일-context train4 비교와 per-rule opportunity coverage는 보존 artifact에 없으므로 미제공입니다. 수치값·private 경로는 공개하지 않습니다.
