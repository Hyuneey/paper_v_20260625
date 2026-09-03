# V2-GDN-FRONT-EXP04-001 최종 보고서

## 판정

PASS · DEVELOPMENT_ONLY. 동결 Commit B에서 한 번의 coordinator-owned runner로 실행했고, 독립 결과 QA와 전체 trace QA를 통과했다. 최종 validation이나 held-out 일반화가 아니다.

## Scope와 GDN

주 후보 authority는 META+STAT, relation admission은 normal-only temporal profiling, 숫자는 EXP-02 policy, runtime은 Formal V4다.
EXP-01C GDN은 LEARNED_GRAPH_SUPPORTING이다. 안정 양성 2pair 모두 V2A pair+horizon에 일치하여 문서상 GDN_ASSISTED_TITLE_STRONG이지만 최종 제목은 DG-04다.
39-rule portfolio와 모든 detection prediction은 sidecar 유무와 무관하게 byte-identical하다. 실제 설명 6,418개 중 130개에만 보조 문구가 존재한다.

## Custody와 performance

- Task public/private final index: 122개, missing required 0, restore PASS.
- Vault status: SINGLE_COPY_LOCAL_ONLY.
- Scientific source/config 변경: feature access 뒤 0.
- Synthetic 39rule profile은 390 trace 약 11.2초, 1,560 trace 약 42.4–44.6초. OS RSS/I/O는 NOT_MEASURED.
- CPU_APPROPRIATE; 추가 GDN 학습이나 GPU 변경 없음.

## EXP-04

| 방법 | Recall | FAR/hour | false episode |
|---|---:|---:|---:|
| D0 PCA-SPE | 11/14 | 0.4939336325682588839451968874340932 | 7 |
| Isolation Forest | 5/14 | 1.764048687743781728375703169407476 | 25 |
| Rule-only V2A | 11/14 | 37.60951802269742644896999157176738 | 533 |
| PCA+Rule | 11/14 | 0.6350575275877614222152531409866912 | 9 |
| IF+Rule | 5/14 | 1.905172582763284266645759422960074 | 27 |

PCA/Rule event overlap = 9/2/2/1. Rule은 PCA miss 2/3에 반응했으나 fusion 실제 recovery=0/3.
IF/Rule overlap = 5/0/6/3. Rule은 IF miss 6/9에 반응했으나 fusion actual recovery=0/9.
양 fusion은 incremental Recall=0, incremental FAR=0.1411238950195025382700562535525981.
따라서 frozen fusion improvement는 DEVELOPMENT_NOT_SUPPORTED.

## EXP-05

Native opportunity 6,418: PASS4,561 / FAIL681 / ABSTAIN1,176.
26개 full batch의 6,418개 단위 모두 11개 structural fidelity 검사 PASS.
Human usefulness는 UNVALIDATED이며 predictive dependency를 causality로 설명하지 않는다.

## 독립 QA와 안전

Arithmetic reviewer: 67,797 independent assertions PASS. Full-trace reviewer: 6,418/6,418, files80 before/after unchanged PASS.
5×54,000 coordinate, maximal episode, 14 event-unit hit, exposure51,019, exact fraction, native contributor, report binding, pre/post label prediction byte identity를 확인했다.
test2=0, heldout=0, provider=0, additional GDN training=0, result-driven redesign=0.
Raw OS byte opens는 global 계측하지 않았으므로 adapter semantic passes를 전체 byte-I/O 횟수로 오해하지 않는다.

## 다음

DG-03 provider 실행 결정을 준비한다. DG-04 제목, DG-05 heldout, DG-06 제출은 별도 승인 전 진행하지 않는다.
