# Cross-version Replication Policy V1

`same method`는 `same numeric bytes`가 아니다. HAI 22.04/21.03에서는 다음을 고정한다.

- candidate-budget policy와 frozen HAI23 META prior portability
- STAT algorithm, profiling horizon/parameter policy
- EXP-02의 37-candidate grid와 selection rule
- Formal V4 semantics
- PCA-SPE/Isolation Forest algorithm과 config policy
- frozen fusion semantics, metric, custody, report schema

버전별 normal data로 STAT, confirmation, numeric summary/policy, Formal V4 portfolio, detector model,
threshold를 다시 만든다. Attack metadata·label은 이 과정에 관여하지 않는다. GDN은 frozen
EXP-01C architecture의 별도 evidence sidecar이며 core replication을 block하거나 Rule inclusion을
바꾸지 않는다.

## META portability

`FROZEN_HAI23_META_PRIOR_PORTABILITY_V1`만 허용한다. HAI23 public META Top-20 중 exact match
또는 독립적으로 verified alias만 옮긴다. 새 pair를 선언하거나 private reviewed input을
복원·재작성하지 않는다. 의미 있는 fixed prior가 남지 않으면 `BLOCKED_META_PORTABILITY`다.

## 현재 호환성 상태

HAI22/21의 file count와 point count는 pinned official README에서 확인됐다. 그러나 현재 tracked
authority에는 P1 tag/unit/role crosswalk가 없다. 따라서 alias와 common universe는 전부
`UNRESOLVED`이며, 공격 payload 전 별도 normal-only/public-metadata task가 필요하다.
