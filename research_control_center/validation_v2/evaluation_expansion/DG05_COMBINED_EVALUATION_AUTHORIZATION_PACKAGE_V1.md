# DG-05 Combined Evaluation Authorization Package V1

상태: `PREPARATION_ONLY_NOT_AUTHORIZED`

## Panel IDs

1. `HAI23_TEST2_PRIMARY_HELDOUT_V1`
2. `HAI22_EXTERNAL_REPLICATION_V1`
3. `HAI21_EXTERNAL_REPLICATION_V1`

## 승인 전 반드시 결속할 항목

- official HAI repository/version/file/LFS identities
- HAI22/21 P1 exact tags, units, roles, sampling and compatibility
- deterministic version-specific normal split authorities
- official scenario IDs and opaque outcome-blind P1 eligibility authority
- exact five methods; version-specific re-instantiation policy
- frozen PCA/IF/STAT/EXP-02/Formal V4/fusion semantics
- official eTaPR implementation/commit/parameters/conformance
- Scenario Recall/FAR/coverage/delay/Wilson/paired-comparison policies
- per-panel atomic prediction write/fsync/close/reopen/hash/record replay
- no prediction writer after freeze
- one-shot label capability and post-label prediction byte equality
- failure, abstain, no-op and unavailable-panel reporting
- version-separated report and no primary pooled Recall

## Failure policy

Compatibility, scenario identity, P1 eligibility, method, metric, prediction custody, or environment mismatch
stops only the affected panel before label access. A failed panel is not silently removed or replaced. No policy
changes after any attack result. Old OUTER authorization is not reusable.

현재 이 문서는 attack byte의 stat/hash/open/download/parse를 허가하지 않는다.
