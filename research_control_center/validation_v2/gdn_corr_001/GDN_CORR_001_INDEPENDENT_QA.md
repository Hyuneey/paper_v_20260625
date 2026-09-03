# GDN-CORR-001 독립 QA

## 판정

`PASS`

## 독립 검증 범위

- 네 결함의 코드 경로와 정정 semantics
- EXP-01B-R1 산술, self-hash, disposition
- EXP-01C checkpoint·evidence·ranking·functional 결과와 disposition
- HAI normal-only split custody와 금지 접근 카운터
- 원본 EXP-01B-V1, V2A, PILOT V1 불변성
- public artifact privacy

## 결과

- EXP-01B-R1 disposition `GDN_ABLATION_ONLY` 독립 재생: PASS
- EXP-01C disposition `LEARNED_GRAPH_SUPPORTING` 독립 재생: PASS
- checkpoint byte/state/graph/view/seed 검증: `9/9` PASS
- private evidence byte/self-hash 검증: `9/9` PASS
- pair assessment state: 각 run `144/144`
- direct EdgeMask: 모든 graph member에 5개 horizon
- SourceOcclusion: 모든 144 pair에 5개 horizon
- Attention capture prediction invariance: `9/9` PASS
- checkpoint post-evaluation immutability: `9/9` PASS
- implementation reference: `11/11` source-commit hash와 일치
- 관련 테스트: `77` distinct PASS
- bundled CPU suite optional-Torch skip: `5`; frozen CUDA smoke 및 9개 CUDA receipt로 실행 근거 보완

## 보고 결함 폐쇄

1. `TRAIN2_ONLY` validation block이 `TRAIN1`으로 보인 표기 오류는 R2에서 정확히 3개 label만 정정했다. 과학 수치와 결론은 변경하지 않았다.
2. shared attention의 horizon key 부재는 self-hashed binding receipt로 폐쇄했다. 같은 non-head-specific encoder evidence를 `1/5/10/30/60`초에 명시적으로 결속했으며 numerical recomputation은 없었다.

## 결과 파일 SHA-256 결속

| 실험 | 파일 | SHA-256 |
|---|---|---|
| EXP-01B-R1 | `EXP01B_R1_CORRECTED_RESULTS.csv` | `883306778523fef0948922c1f30dd81884263c8b35bcd5e566fe28071a36e929` |
| EXP-01B-R1 | `EXP01B_R1_RANDOM_CONTROL_RESULTS.csv` | `1a15d988210b57408a8b104b2ba265f9c93c4dcb4f3198e62ad9be9b8c8a6ec8` |
| EXP-01B-R1 | `EXP01B_R1_STABILITY_RESULTS.csv` | `11225db02b6db1e29572c15df7ee8e039aa903b4c24b4c70203e470d4dd2030d` |
| EXP-01C | `EXP01C_RANDOM_CONTROL_RESULTS.csv` | `e6c01d5e83848079f3430ca42447add9bd63671cdbf1cc07f3e11325e18b8bf8` |
| EXP-01C | `EXP01C_RANKING_RESULTS.csv` | `5f63df56faad1eef3eb3497b99cc92ad63390bbb762835e9af30e178e900b766` |
| EXP-01C | `EXP01C_STABILITY_RESULTS.csv` | `faf66efb4bd55fdc2a27c291d55a32e99e3c73f27936e513a4d2368662e92b25` |

위 6개 hash는 `GDN_CORR_001_RESULT_BINDING_RECEIPT.json`에도 self-hashed 형태로 결속했다.

## 불변성·안전

- base `063b80a2` 대비 EXP-01B-V1 및 V2A 변경: 없음
- 기존 tracked file 삭제: 없음
- test1 / labels / test2 / held-out 접근: `0`
- public private-path/secret marker: `0`
- private checkpoint/evidence: Git ignore 유지

## QA 결론

정정 재분석과 하나의 HAI-adapted prospective experiment는 사전등록·불변성·privacy 경계를 충족했다. `LEARNED_GRAPH_SUPPORTING`은 정상 데이터에서의 supporting evidence이며 primary improvement, causality, test 성능 또는 held-out validation을 의미하지 않는다.
