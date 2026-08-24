# 재현성과 코드 상태

## 동결 기준

- 보고서 시작 기준 commit: `70811efe44246796797299d58125720298e3a380`
- 시작 CURRENT_STATE self-hash: `74875a5bee93621d5c98e7898f74f1206ee7149dcfcb51a6f21a58310c8f561f`
- 시작 상태: `OUTER_TEST2_FEATURE_CUSTODY_REJECTED`
- remote egress: `LOCAL_ONLY_NOT_PUSHED`

## 공개 과학 근거 인덱스

| 근거 | 공개 artifact |
|---|---|
| COMMON-42 identity | `docs/task_reports/TASK-039E0_CONFIRMED_RELATION_COHORT.json` |
| D0/D1/D2 V1 비교 | `TASK-039E3_R2R_UTILITY_INNER_D0_D1_D2_COMPARISON_V1_*` |
| D2 V2 result integrity | `TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_COMPLETION_V1.json` |
| V1/V2 scientific disposition | `TASK-039E3_R2R_UTILITY_INNER_D2_V1_V2_DISPOSITION_V1_*` |
| OUTER failure | `TASK-039E3_R2R_UTILITY_OUTER_D0_D1_D2V1_EXECUTION_RECOVERY_V1_BLOCKER.json` |
| ARGOS validity | `docs/argos_reproduction/ARGOS_METHODOLOGICAL_VALIDITY_REPORT.md` |

## 보존 패키지

실제 보존 파일은 repository 밖의 승인된 local preservation namespace에 생성했다. 추적 문서에는 경로를 기록하지 않는다.

| logical file | SHA-256 | bytes | 포함 범위 |
|---|---|---:|---|
| `repository-all-refs.bundle` | `232b6c9c0224e1109878e571ed0f45c2703e38e6e2e20426afe55cd5cd591dd1` | 18,889,326 | 모든 local refs와 Git history |
| `source-only-head.zip` | `8427aacf47697b045224349ccd898d722a9360dfe99660ffb15a4c87ee7b0b3d` | 2,949,430 | HEAD의 tracked source/tests/config와 method/v6 documentation |

`git bundle verify`는 complete history를 확인했다. source archive는 `git archive`로 만들고 `src`, `tests`, `scripts`, `configs`, `docs/v6`, `docs/method`만 명시해 untracked raw HAI뿐 아니라 task result artifacts, private registries, private evidence, credentials도 포함하지 않는다.

## 환경 요약

| 항목 | 값 |
|---|---|
| OS/shell | Windows / PowerShell 7.6.4 |
| Git | 2.55.0.windows.4 |
| bundled Python | 3.12.13 |
| project Python floor | >=3.11 |
| required package | jsonschema[format-nongpl]==4.26.0 |
| optional GDN | torch==2.12.1, torch-geometric==2.8.0 |

정확한 private data root, credentials, OS user path는 기록하지 않았다.

## canonical local branch/commit inventory

| role | branch/commit |
|---|---|
| report base and OUTER failure continuity | `task-039e3-r2r-utility-outer-d0-d1-d2v1-execution-recovery-v1` @ `70811efe...` |
| D2 V1/V2 disposition | `task-039e3-r2r-utility-inner-d2-v1-v2-scientific-disposition-v1` @ `634231bb...` |
| D2 V2 integrity completion | `task-039e3-r2r-utility-inner-d2-v2-r5-accounting-r5-report-render-remediation-r1` @ `9287d5f6...` |
| D0/D1/D2 comparison | `task-039e3-r2r-utility-inner-d0-d1-d2-scientific-comparison-v1` @ `37a8df93...` |
| COMMON-42 normal authority | `task-039e3-r2r-utility-normal-only-authority-v1-freeze` @ `d58757b6...` |

전체 417 refs는 bundle 안에 보존했고, 본문에는 결정에 필요한 canonical subset만 표시한다.

## 실행/데이터 경계

이 보고서 작업의 과학 실행은 0, test2 access는 0, 동결 결과 변경은 0이다. 보고서 수치는 공개 동결 artifact의 복사 또는 허용된 결정론 산술만 사용했다.
