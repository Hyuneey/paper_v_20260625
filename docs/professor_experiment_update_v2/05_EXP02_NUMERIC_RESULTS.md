# EXP-02 Numeric criteria 결과

## 상태

**COMPLETE_NORMAL_ONLY / SELECTED POLICY FROZEN**

V2A의 39개 방향 관계에 대해 common fixed 1개와 relation-specific normal-only grid 36개, 총 37개 후보를 train1/train2에서 수치화하고 normal train4에서 선택했습니다. 선택에는 공격 label, test1, detector 결과를 사용하지 않았습니다.

동결된 선택 규칙이 고른 policy는 `RELATION_SPECIFIC_NORMAL_ONLY_V1:n7-q0.90-s2-f0.05`입니다. 28개 후보가 coverage guard를 통과했으며, 선택 policy의 train4 관찰값은 false-alarm second 1,470, false-alarm episode 1,461, opportunity 39, PASS 16,361, FAIL 1,790, ABSTAIN 3,764입니다. normal exposure는 198,000초였습니다.

이 결과는 normal-only 선택 결과이며 test1 공격 탐지 우수성을 뜻하지 않습니다. 선택 authority와 39-rule Formal V4 V2A portfolio는 별도 V2 identity로 동결했습니다. provider 호출은 0회입니다.
