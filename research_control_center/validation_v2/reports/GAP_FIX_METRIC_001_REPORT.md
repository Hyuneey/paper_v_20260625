# GAP-FIX-METRIC-001 — Metric Portability & Common Evaluation Contract

## 판정

`PASS` — VALIDATION V2의 공통 초 단위 alarm, attack-event unit, episode,
Recall, FAR/hour, overlap, D0-miss recovery와 incremental metric 의미를
순수 함수와 self-hashed schema로 고정했다.

- implementation commit: `c9e2da71e197e24df499101f99c2f6ffa38e1576`
- protocol hash: `2c3000a912caf2167bfe49929c55229e5159d52cc9ad09b7e48d79d9aecc562f`
- metric contract hash: `aec2dd11b8178071eb91160f1dff45f9cd0cc1be6c314aa3641ed0698df3dde4`
- schema registry: `12` entries

## 고정된 공통 의미

- file-local strict one-second coordinate와 전체 행 coverage를 별도 authority로 검증한다.
- D0/D2의 Boolean point prediction은 공통 dense alarm timeline으로 변환한다.
- D1은 durable prediction receipt와 Formal V4 trace를 함께 재검증하며 `FAIL`만 alarm이다.
- `PASS`, `ABSTAIN`, `NO_OPPORTUNITY`는 no-alarm이지만 system error는 no-alarm으로 축소하지 않는다.
- attack-event unit은 strict label `1`의 최대 연속 half-open 구간이며 point adjustment는 없다.
- episode는 같은 file의 unique alarm second를 gap `0`으로 묶은 최대 연속 구간이다.
- attack과 일부라도 겹친 mixed episode는 normal false episode에서 전체 제외하고 분할하지 않는다.
- Recall과 FAR/hour는 exact numerator/denominator와 `UNDEFINED` 상태를 함께 보존한다.
- 비교 결과는 BOTH/base-only/candidate-only/neither, miss recovery, incremental Recall/FAR를
  signed exact metric으로 기록한다.

## Fail-closed 경계

다음은 모두 거절된다.

- protocol과 다른 metric contract를 다시 hash한 문서
- file authority보다 짧거나 긴 prediction/label timeline
- 변조된 alarm state/count 또는 result/bundle self-hash
- D1 prediction과 durable receipt의 artifact/authority 불일치
- Formal V4 trace outcome/hash/runtime context 불일치
- `FAIL` Boolean과 contributing rule/trace provenance 불일치

## Stage 1 범위 제한

이 PASS는 `SYNTHETIC_CONTRACT_ONLY`이고 `scientific_eligible=false`인 portable metric
primitives에만 적용된다. scientific evaluation은 아직 허가되지 않았다. Stage 3 wrapper는
full Formal V4 descriptor/numeric timing authority, 실제 label-access capability, metric 후
prediction byte identity 재검증을 반드시 결속해야 한다.

## 검증

- focused metric tests: `24/24 PASS`
- all VALIDATION V2 tests: `76 PASS`, Windows symlink privilege `1 SKIP`
- RCC tests: `126/126 PASS`
- compileall / diff check: `PASS`
- independent QA: `PASS`
- PILOT V1 preservation: `3,021 blobs verified`

## 안전

scientific execution, test1/test2/held-out access, provider call, private exposure는 모두 `0`이다.
PILOT V1 source/artifact/result는 변경하지 않았다.
