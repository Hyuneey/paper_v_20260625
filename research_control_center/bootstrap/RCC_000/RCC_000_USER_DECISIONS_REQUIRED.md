# RCC-000 User Decisions Required

## DECISION-001 — RCC canonical source policy

**Question**

Research Control Center가 scientific source authority로 어떤 Git ref 정책을
사용해야 하는가?

**Options**

- **A. Recommended:** `origin/research-v6-thesis-checkpoint`를 exact commit
  `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`과 함께 고정하고,
  `thesis-v1-post-push-audit`를 immutable pin으로 사용한다.
- **B.** thesis branch
  `origin/task-039e3-r2r-thesis-draft-scaffold-v1@ebc5a57...`를 단일 입력으로
  사용한다.
- **C.** 현재 checkout 또는 `origin/main`을 사용한다.

**Codex Recommendation**

Option A. Branch name만 저장하지 말고 exact commit과 tag를 함께 저장한다.
Option C는 최신 implementation/result를 포함하지 않으므로 선택하지 않는다.

**Why user decision is required**

RCC가 이후 source/artifact indexing을 어느 ref에 고정할지는 control-plane
정책이다. Codex가 문서 branch를 scientific authority로 자동 승격하면 안 된다.

## DECISION-002 — Thesis draft overlay ingestion

**Question**

RCC가 scientific checkpoint와 별도로 최신 thesis draft branch를 read-only
documentation overlay로 색인할 것인가?

**Options**

- **A. Recommended:** yes. Scientific authority는 `2dc7e6c...`로 유지하고,
  thesis 문서만 `ebc5a57...`에서 별도 namespace로 읽는다.
- **B.** no. RCC-001은 checkpoint만 읽고 thesis 문서는 이후 추가한다.

**Codex Recommendation**

Option A. 두 ref의 역할을 명시적으로 분리하면 최신 thesis 문서를 제공하면서
frozen science의 기준점을 흐리지 않는다.

**Why user decision is required**

Thesis draft는 교수 결정 4개가 미해결인 잠정 문서이며 canonical scientific
checkpoint와 동일한 authority로 취급할 수 없다.
