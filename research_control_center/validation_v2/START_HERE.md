# VALIDATION V2

VALIDATION V2 is a prospective scientific version. It does not rewrite,
migrate, or relabel PILOT V1.

Start with these controls:

1. `VERSION_POLICY.md` defines the V1/V2 boundary.
2. `DECISION_GATES.md` defines the only user decision gates.
3. `TASK_INDEX.csv` is the ordered implementation ledger.
4. `PROGRAM_STATE.json` is the machine-readable program status.
5. `PILOT_V1_PRESERVATION_MANIFEST.json` binds the immutable authority.

The current development split is `test1`. It remains development-only.
No test2 or other held-out access is authorized by this program.

## Current execution status

- Shared V2 authority, custody, protocol, metric, and experiment-preparation
  contracts are frozen and synthetic-tested.
- The clean-checkout fresh-machine synthetic rehearsal passed without
  scientific data.
- The four normal HAI files are materialized and bound under `DATA-POLICY-001`.
- EXP-01, the separate EXP-01B GDN-XAI experiment, and EXP-02 are complete.
- `META_PLUS_STAT` and the 39-rule Formal V4 V2A portfolio are frozen.
- EXP-04와 EXP-05 개발 결과는 완료·동결됐으며 test1을 다시 열지 않는다.
- DEC-022는 HAI 23.05 test2, HAI 22.04, HAI 21.03의 version-separated 평가 계획을 승인했다.
- HAI22/21 P1 tag·unit·role 호환성은 아직 `UNRESOLVED`; attack access 전 별도 normal-only/public-metadata authority가 필요하다.
- Missing HAI 23.05 data must trigger `CODE_BASED_MATERIALIZATION` through the
  approved official distribution workflow before any user-path request.
- Exact next task는 DG-03이다. EXP-03은 OpenAI `gpt-5.4-mini`, 최대 819 calls,
  5,031,936 tokens, USD 10.07 ceiling을 검토하기 전 provider contact가 0이어야 한다.

## Resume receipt

- `DEC-020 = APPROVED_FORMAL_V4`
- `DG-01 = RESOLVED_BY_USER`
- Canonical-to-V4 bridge: `NOT_SELECTED`
- Minimum thesis path bridge requirement: `NOT_REQUIRED`
- Historical blocker: `BLOCKED_NORMAL_DATA_NOT_FOUND`
- Corrected root cause: `HAI_CODE_MATERIALIZATION_POLICY_NOT_PROPAGATED_TO_V2_RECOVERY_LOGIC`
- Current state: `NORMAL_ONLY_TRACKS_COMPLETE_EXP04_NEXT`
- test1, labels, test2, held-out, and provider accesses during the completed
  normal-only tracks: `0`

The approved recovery path remains `scripts/materialize_hai_2305_normal_v2.py`
for future restoration. Never perform a host-wide search, manual upload, or
test1/test2 acquisition as a substitute.
