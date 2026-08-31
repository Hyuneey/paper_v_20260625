# PILOT V1 이후 무엇이 달라졌는가

PILOT V1은 그대로 보존됩니다. VALIDATION V2는 이를 수정한 이름이 아니라 별도 scientific version입니다.

| 영역 | PILOT V1 | VALIDATION V2 |
|---|---|---|
| Rule/runtime authority | frozen V4 COMMON-42 경로 | 별도 Formal V4 authority와 exact binding replay |
| D1 pre-label custody | 메모리 내 freeze | atomic durable write → close → reopen/replay → label lease → post-label byte check |
| split 역할 | pilot 절차로 추적 | train/test/final 역할과 no-post-test-tuning contract 고정 |
| metrics | frozen pilot 구현 | portable common per-second adapter와 합성 contract tests |
| GDN | self-neighbor 포함 가능 pilot behavior | self-excluded corrected behavior와 ablation 계획 고정 |
| numeric policy | pilot fixed authority | normal-only policy comparison 계획 고정 |
| stronger detector | PCA-SPE reference only | normal-only Isolation Forest 비교 arm 준비 |
| explanation | frozen D1 trace와 canonical renderer 미연결 | V2 runtime trace → deterministic renderer → structural validator 경로 준비 |
| 재현성 | traceability 중심 | clean checkout fresh-environment synthetic rehearsal PASS |

바뀌지 않은 것은 더 중요합니다. test1은 development-only이고, test2/held-out은 열지 않았으며, Runtime LLM은 사용하지 않습니다. V2 결과를 보기 전 사전등록과 contract를 먼저 고정했습니다.
