# 데이터와 Split은 실제로 어떻게 사용되는가

Scientific authority: `origin/research-v6-thesis-checkpoint` @ `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

Audit scope: static source, frozen public metadata, custody and integrity reports. 이 감사에서는 HAI 원본을 읽거나 과학 실행을 하지 않았다.

## 1. 한눈에 보는 데이터 구조

현재 권위는 공식 `icsdataset/hai` Git/LFS snapshot에 고정된 **HAI 23.05**이다. 공개 provenance는 승인된 10개 파일의 identity, 크기·행 수, 공통 헤더, 1초 nominal sampling, timestamp/label schema를 검증한다. 원본 payload는 Git 밖의 local/private 경계에 남는다.

전체 시계열 schema는 timestamp와 86개 point를 기술한다. 현재 연구 process는 **P1 Boiler**이고, P1 scientific frame은 37개 feature를 사용한다. 이것과 candidate role universe의 12 source × 12 target, relation profiling의 필요한 subset, D1 runtime의 필요한 subset은 서로 다른 계약이다.

검증된 흐름은 다음과 같다.

`official HAI 23.05` → `DatasetManifestV2` → P1 selection → P1 data views / split manifests → task-specific readers → normal-only construction or INNER prediction → prediction authority → labels → metrics.

## 2. HAI와 P1을 어디서 어떻게 읽는가

`hai_provenance_v1.py`는 Git/LFS pointer와 materialized identity를 대조하고, CSV header·행 수·timestamp 간격·process ID를 공개-safe audit record로 만든다. `DatasetManifestV2`는 local-only storage를 강제하고 path/hash/schema를 검증한다.

P1은 `hai_continuous_step_v1.py`의 reviewed continuous-step feasibility execution에서 선택되었다. P1만 frozen gate를 통과했고 P3는 선택되지 않았다. `read_authorized_columns_v1`은 reviewed P1 columns만 읽고 file-local event/window semantics를 유지한다. 이후 `candidate_discovery_protocol_v1.py`가 process `P1`, 12개 ordered source role, 12개 ordered target role, 144개 directional pair를 고정한다.

## 3. train1~4의 역할

| Split | 검증된 역할 | 실제 소비자 | Label |
|---|---|---|---|
| train1 | NORMAL_CANDIDATE_FIT | STAT/GDN, relation fit, normal numeric authority, D0 fit | 공격 label 없음 |
| train2 | NORMAL_CANDIDATE_FIT | train1과 같은 독립 file-local evidence | 공격 label 없음 |
| train3 | NORMAL_RELATION_CALIBRATION | one-way relation confirmation; 별도 D0 SPE threshold calibration | 공격 label 없음 |
| train4 | NORMAL_GUARD | D0 frozen model/threshold의 normal sanity evaluation | 공격 label 없음 |

BR2 split manifests는 split-before-windowing, ordered raw ranges, 120-sample purge gap을 기록한다. Generic `splits_v2.py`는 operation-role mapping과 purge/window 검증을 fail-closed로 제공한다. 다만 실제 frozen task들은 이 API 하나를 공통 호출하기보다 각 task grant와 file identity check로 권한을 다시 구현한다. 따라서 계약은 존재하지만 enforcement가 분산되어 있다.

train3의 relation confirmation과 D0 calibration은 서로 다른 code path와 artifact를 사용하며 label을 사용하지 않는다. 이것은 확인된 leakage가 아니다. 그러나 같은 normal period를 두 연구 arm이 공유하므로 **ACCEPTABLE_WITH_SCOPE_LIMITATION**으로 분류한다. 확장 비교에서는 calibration independence를 따로 검토할 가치가 있다.

## 4. test1의 역할

`hai-test1.csv`는 54,000초의 **INNER development / pilot evaluation** feature authority다. label은 별도 `label-test1.csv`이고 timestamp로 정렬한다. 공개 frozen evidence는 14개 contiguous attack-event units를 기록한다. 통계적 독립성은 확립되지 않았고 final validation 표본도 아니다.

D0와 D1의 fit, COMMON-42 construction, normal numeric authority에는 test1 label 또는 result가 입력되지 않았다. individual rule을 test1 성능으로 삭제하거나 COMMON-42를 다시 고른 backward path도 찾지 못했다.

그러나 test1을 완전히 한 번만 본 독립 test라고 설명하면 안 된다. D2 V2는 D2 V1과 prior INNER diagnostic을 알고 설계되었고, 그 보고서가 이를 “explicitly label-informed INNER-development policy”로 명시한다. D2 V2 execution 자체는 label-blind prediction을 먼저 만들지만, 정책의 연구 설계는 pilot outcome-informed이다.

## 5. test2의 역할과 현재 상태

test2 feature authority와 별도 test2 label authority는 one-way held-out OUTER 대상으로 preregistered 되었다. 실제 recovery attempt는 첫 feature custody 단계에서 file identity/custody를 거부했고 **payload byte를 읽기 전에** 멈췄다.

- feature custody file access attempt: 1
- feature bytes / hashes / semantic parses: 0 / 0 / 0
- label opens / bytes / parses: 0 / 0 / 0
- D0/D1/D2 predictions: 0
- metrics: 0

따라서 과학적 결론은 “OUTER 성능이 나빴다”가 아니라 **held-out result unavailable; generalization unconfirmed**이다.

## 6. 정상 데이터만 사용하는 구간

| Subclaim | 판정 | 근거 요약 |
|---|---|---|
| A. candidate discovery normal-only | VERIFIED | META는 값 0개, STAT/GDN은 train1/train2만 허용 |
| B. GDN training normal-only | VERIFIED | P1 train1/train2와 frozen candidate mask만 사용; test/label 금지 |
| C. relation profiling normal-only | VERIFIED | D1 fit loader는 exact train1/train2만 읽음 |
| D. train3 confirmation normal-only | VERIFIED | one-way train3 grant; train1/2 reread·train4·test·label 금지 |
| E. numeric criteria normal-only | VERIFIED | frozen utility authority는 train1/train2만 읽고 label/train3/train4 접근 false |
| F. T0/T1/T1-B/T2 evidence normal-only | VERIFIED | frozen evidence pack/ledger를 소비하고 raw/test label을 포함하지 않음 |
| G. verifier attack-label use | NOT_APPLICABLE | deterministic validity는 evidence/contract를 검증하며 metric labels를 받지 않음 |
| H. COMMON-42 evaluation-outcome use | VERIFIED | construction/acceptance가 INNER evaluation보다 먼저 frozen; backward selection path 없음 |

## 7. Label을 볼 수 있는 시점

D0는 public DetectorPrediction을 atomic write/reopen하고 state를 `PREDICTION_FROZEN`으로 바꾼 뒤 label을 연다. D2 V1/V2도 같은 persistent combined-prediction gate를 가진다.

D1은 label-blind prediction object를 먼저 계산하고 self-hash/factory custody를 검증한다. 그러나 public RulePrediction file은 label-derived metrics 이후 `_public_reports_v1`에서 기록된다. 즉 decision construction-before-label은 확인되지만, D0/D2와 같은 **durable file freeze-before-label**은 확인되지 않는다. 이것은 HIGH architecture finding이다. label이 decision을 바꿨다는 증거는 아니며 frozen result를 이 감사에서 수정하지 않는다.

## 8. D0 데이터 흐름

`train1 + train2` → 37-feature standardization/PCA fit → private preprocessing/model freeze → `train3` SPE score distribution → strict frozen threshold calibration → private threshold freeze → `train4` normal sanity → `test1 features` → 54,000 label-blind scores/alarms → DetectorPrediction durable freeze → `label-test1` → event/episode metrics.

Training grant는 test1/test2/label을 모두 false로 고정한다. frozen accounting도 model fit 1회, calibration 1회, label/test access 0을 기록한다. 상세 PCA 수학은 ARCH-007 대상이다.

## 9. Rule 데이터 흐름

P1 reviewed metadata → 12×12 universe → META (no values) / STAT / GDN (train1/train2) → unscored union → train1/train2 relation fit → train3 one-way confirmation → frozen ledgers → evidence materialization (raw reread 없음) → T0/T1/T1-B/T2 → deterministic verifier → COMMON-42 → separate train1/train2 normal numeric runtime authority → `test1 features` → D1 label-blind decisions → label evaluation.

관계 construction evidence와 utility labels는 분리되어 있다. D1 durable-file ordering gap은 이 scientific separation을 반증하지 않지만 control proof를 약화한다.

## 10. D2 데이터 흐름

D2 V1/V2 execution은 test1 raw feature를 다시 읽지 않는다. exact frozen D0/D1 prediction과 source/horizon metadata를 소비해 fusion decision을 만든다. CombinedPrediction을 persistent freeze한 뒤에만 label을 읽고 metrics를 계산한다.

V1 design은 test1/label을 설계에 쓰지 않았다고 고정했다. V2는 prior INNER outcome을 문제 정의에 사용했음을 명시하므로 결과는 development pilot로만 해석한다.

## 11. Leakage 점검 결과

**NO VERIFIED LEAKAGE FOUND.** 공격/test label이 candidate fit, relation construction, numeric authority, D0 fit/calibration, COMMON-42 acceptance를 바꾼 경로는 확인되지 않았다. 동시에 “leakage impossible”이라고 주장하지 않는다.

가장 중요한 control finding은 D1의 durable persistence ordering gap이다. 다음은 task별로 분산된 split enforcement, train3 dual use, D2 V2의 명시적 pilot-informed design이다. 이들은 각각 ordering proof, 유지보수/감사 가능성, 비교 independence의 제한이다.

## 12. 코드와 문서의 차이

상세 8건은 [ARCH_001_MISMATCHES.md](ARCH_001_MISMATCHES.md)에 기록했다. 특히:

1. D1의 “prediction frozen”은 object-level에서는 사실이나 durable-file-level에서는 과장될 수 있다.
2. “test2 accesses 0”은 byte/semantic access에는 맞지만, historical custody file access attempt 1을 숨기면 안 된다.
3. “test1 evaluation”만으로 표현하면 D2 V2의 pilot-informed redesign을 놓친다.
4. 86 dataset points, 37 P1 features, 12×12 role universe, profiling/runtime subsets를 하나의 feature count로 합치면 안 된다.

## 13. 내가 이해해야 할 핵심

- train split은 하나의 동일한 역할이 아니라 fit, confirmation/calibration, sanity를 분리한다.
- 정상 데이터 공유는 자동으로 leakage가 아니지만 independence 범위를 제한할 수 있다.
- prediction 내용이 label-blind인 것과 prediction file이 label 전에 durable freeze되는 것은 서로 다른 보장이다.
- test1은 방법 개발과 pilot 비교에 사용되었으므로 final test가 아니다.
- test2는 결과가 실패한 것이 아니라 payload를 읽기 전에 custody에서 중단되어 결과가 없다.

다음 deep audit은 **ARCH-002 — META / STAT / GDN Candidate Discovery Deep Audit**이다.
