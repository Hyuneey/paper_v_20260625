# VALIDATION V2 Stronger Detector Feasibility

## 판정

`DG-02`는 **`RESOLVED_ISOLATION_FOREST`를 유지**하는 것이 타당하다.
`IsolationForest`는 현재 허용된 범위에서 구현 성숙도, P1의 37개 수치형 변수와의
호환성, 정상 전용 학습, 비선형 다변량 score, 재현 가능성, 제한된 구현 범위를 함께
만족시키는 가장 명확한 후보다. 선택 뒤 격리된 V2 환경에 exact public stack을
설치하고 V2 전용 contract와 synthetic tests를 구현했다. 후보 선택 모호성과 local
implementation closure는 해소됐고, fresh-machine wheel manifest와 과학 입력
authority freeze는 별도 gate다. Exact six-wheel filename/size/SHA-256 manifest도
public report로 고정했다.

과학 실행 전 남은 gate는 다음과 같다.

1. CPython, NumPy, `scikit-learn`, SciPy, joblib, threadpoolctl, narwhals의 exact
   versions, installed `RECORD` hashes, fresh-machine wheel hashes를 고정했다.
2. 공개 dependency로 fresh-machine synthetic install/import가 가능한지 확인한다.
3. `random_state=0`, `n_jobs=1` 및 고정 config에서 synthetic replay가 동일한 score,
   prediction, model/prediction hash를 만드는지 검증한다.
4. 위 조건을 만족하지 못하면 detector를 과학 실행하지 않는다. dependency를 한 번의
   제한된 remediation으로 닫을 수 없거나 deterministic replay가 성립하지 않을 때만
   `DG-02`를 다시 연다.

이번 검토는 source/config/audit/dependency metadata만 읽었다. scientific data,
`test1`, `test2`, held-out, label, prediction artifact는 읽거나 실행하지 않았다.

## 로컬 근거

- `pyproject.toml`은 base import와 분리된 `validation-v2-detector` optional group에
  exact public dependency closure를 선언한다.
- base bundled interpreter에는 `sklearn`이 없고 lightweight import는 유지된다.
  별도의 `.venv/validation-v2`에는 Python 3.12.13, NumPy 2.5.2,
  scikit-learn 1.9.0, SciPy 1.18.1, joblib 1.5.3, threadpoolctl 3.6.0,
  narwhals 2.25.0이 설치됐고 installed `RECORD` hash와 `pip check`가 확인됐다.
  이는 실행 환경 근거이지 detector 성능 근거가 아니다.
- `ARCH_011_ENVIRONMENT_MATRIX.csv`는 NumPy조차 project-wide dependency lock에
  포함되지 않았고 fresh-machine numerical environment가 미완료라고 기록한다.
- frozen D0 source는 P1의 ordered 37 numeric features, normal-only `train1+train2`
  fit, `train3` calibration, per-timestamp score, label-free thresholding 계약을 이미
  명확히 갖는다. V2 추가 detector는 이 input/split/metric interface를 재사용할 수 있다.
- historical `experiments/argos_reproduction`의 LSTMAD 계열은 frozen reference-only이며
  현재 HAI V2의 재사용 가능한 scientific implementation이 아니다.
- `VERSION_POLICY.md`와 `PROGRAM_STATE.json`은 추가 baseline을
  `ISOLATION_FOREST_FIXED_NORMAL_ONLY`로 이미 분리 기록한다. 이 정책은 Pilot V1을
  변경하거나 결과를 미리 주장하지 않는다.

## 객관적 후보 비교

| 후보 | 구현 성숙도 | HAI/P1 호환성 | 정상 전용 | 다변량·비선형 | dependency closure | 결정론·재현 | 구현 범위 | 판정 |
|---|---|---|---|---|---|---|---|---|
| `IsolationForest` | 높음 (`scikit-learn`) | 높음: 37차원 numeric row score | 가능 | 가능 | 현재 미완료이나 하나의 공개 ML stack으로 닫을 수 있음 | exact pins, fixed seed, `n_jobs=1`이면 높음 | 작음 | **선택** |
| `OneClassSVM` | 높음 (`scikit-learn`) | 형식상 가능 | 가능 | 가능 | IF와 같은 stack | deterministic 가능 | 중간 | 현재 normal fit 범위에서 kernel fit 비용과 parameter 민감도가 커 우선하지 않음 |
| `LocalOutlierFactor(novelty=True)` | 높음 (`scikit-learn`) | 형식상 가능 | 가능 | 가능 | IF와 같은 stack | deterministic 가능 | 중간 | 대규모 reference-set 저장·이웃 검색 비용과 novelty 계약 부담 때문에 우선하지 않음 |
| `EllipticEnvelope` | 높음 (`scikit-learn`) | 형식상 가능 | 가능 | 제한적 | IF와 같은 stack | 높음 | 중간 | covariance/분포 가정과 대규모 robust covariance 비용 때문에 PCA-SPE의 명확한 보완으로 약함 |
| Autoencoder/Deep SVDD 계열 | 일반적으로 성숙 | 별도 sequence/data adapter 필요 | 가능 | 가능 | Torch stack과 model-specific code 추가 | seed·kernel·training 환경 민감 | 큼 | 현재 thesis 최소 범위를 초과 |
| historical LSTMAD | frozen reference는 존재 | HAI V2 재사용 계약 없음 | historical contract에 의존 | temporal/nonlinear | 별도 historical container | 현재 V2에서 미확인 | 큼 | frozen reference path이므로 부적격 |
| PyOD/Random Cut Forest 계열 | local 구현 없음 | 새 adapter 필요 | 가능 | 가능 | 새 package stack | package별 상이 | 중간~큼 | IF보다 dependency와 구현 범위가 불리함 |
| PCA-SPE | 이미 구현·감사됨 | 높음 | 가능 | 선형 | NumPy만 필요 | 높음(환경 가정 포함) | 완료 | D0 reference 유지; stronger 후보가 아님 |

이 비교는 성능 순위를 뜻하지 않는다. `IsolationForest`를 선택하는 이유는 예상 성능이
아니라, 현재 연구 질문에 필요한 **추가 nonlinear multivariate baseline**을 결과를 보기
전에 가장 작은 새 권한 표면으로 구현할 수 있기 때문이다.

## 과학적 역할과 주장 경계

- 역할: `ADDITIONAL_NONLINEAR_MULTIVARIATE_NORMAL_ONLY_BASELINE`.
- 허용 표현: “PCA-SPE 외에 고정된 정상 전용 nonlinear multivariate baseline을
  추가했다.”
- 금지 표현: “temporal SOTA”, “PCA-SPE보다 강하다”, “현대 TSAD를 대표한다”,
  “성능이 우월하다”. 이런 표현은 실행 전에는 물론 개발 결과 후에도 held-out 근거 없이
  허용되지 않는다.
- `IsolationForest`는 각 timestamp의 multivariate row를 평가하지만 시간 순서를 직접
  모델링하지 않는다. 따라서 stronger baseline이라는 말은 D0보다 더 복잡한 비선형
  reference라는 제한된 의미다.
- `test1` 결과는 `DEVELOPMENT_ONLY`다. held-out generalization은 `DG-05` 전에는
  평가하거나 주장하지 않는다.

## 정확한 구현 계획

### 1. 새 V2 authority

- 새 module/config/schema/artifact ID를 사용한다. Pilot V1의 D0 source, model,
  prediction, result를 수정하거나 migrate하지 않는다.
- proposed detector ID: `V2_ISOLATION_FOREST_FIXED_NORMAL_ONLY_V1`.
- exact feature authority는 P1 ordered 37-feature V2 contract로 제한한다. timestamp,
  label, attack metadata, non-P1 feature는 fit/score input에서 거절한다.
- input split 역할은 `ValidationProtocolV1`에서 재검증한다.

### 2. Dependency boundary

- `scikit-learn`을 import할 때 importable 여부만 보지 않고 exact environment receipt를
  replay한다.
- implementation commit에서 호환되는 exact top-level/transitive versions와 wheel
  hashes를 고정한다. 현재 audit만으로 version을 추측하여 넣지 않는다.
- optional baseline dependency가 없으면 lightweight `paperworks` import는 계속
  가능해야 하고, detector entrypoint만 project-owned fail-closed error를 낸다.

### 3. Fit·score·calibration

- model fit: normal-only `train1` file-local rows 뒤에 `train2` file-local rows를
  안정적으로 이어 붙인 하나의 fit-only matrix를 사용한다. ordered file ID, file
  content hash, 각 file row count/matrix hash, combined matrix hash를 receipt에
  결속하고 shuffle하지 않는다. 이 예외는 file-local scoring이나 metric timeline의
  cross-file merge를 허용하지 않는다.
- preprocessing: V2가 소유한 normal-only finite float64 matrix와 feature-order
  contract. Standardization은 algorithm에 필수는 아니므로 별도 성능 선택 대상으로
  만들지 않는다. 구현은 raw ordered numeric features를 사용하고 해당 결정을 config에
  고정한다.
- primary config: `n_estimators=256`, `max_samples=256`, `max_features=1.0`,
  `bootstrap=false`, `contamination="auto"`, `random_state=0`, `n_jobs=1`,
  `warm_start=false`, `verbose=0`.
- combined fit cohort가 256 rows보다 작으면 fail closed한다. fit 후
  `estimator.max_samples_ == 256`을 authority receipt에 결속하여 library의 작은-cohort
  자동 축소를 허용하지 않는다.
- score: `-estimator.score_samples(X)`를 anomaly score로 사용한다. 큰 값일수록 anomaly다.
- threshold calibration: normal-only `train3` score의 `q=0.999` nearest-rank
  order statistic. alarm comparator는 strict `score > threshold`; equality는 no-alarm.
- `train4`: normal-only sanity report만 생성한다. config 또는 threshold를 바꾸는 데
  사용하지 않는다.
- `test1`: config/model/threshold/policy freeze 뒤 feature-only score와 prediction을
  생성하고, shared durable pre-label custody가 PASS한 후에만 label metric capability를
  사용한다. 결과를 보고 config나 fusion policy를 변경하지 않는다.

### 4. Artifact·custody

- config, feature authority, split identities, environment receipt, seed, estimator params,
  model bytes hash, threshold authority, source commit을 각각 결속한다.
- serialized estimator는 private local artifact로 보관하고 public report에는 hash와
  non-sensitive metadata만 기록한다. 신뢰되지 않은 pickle/joblib payload를 load하지 않는다.
- score/prediction은 file-local one-second common adapter로 변환한다.
- prediction은 atomic write → fsync → close → reopen/replay → explicit freeze → label
  authorization → post-metric byte identity 순서를 따른다.
- metric은 V2 common contract의 Attack-event Recall, normal FAR/hour, overlap,
  incremental Recall/FAR를 사용한다. raw score나 label detail을 공개하지 않는다.

### 5. EXP-04 integration

- 독립 arm으로 `PCA-SPE`, `IsolationForest`, V2 Verified Relational Rule-only를 먼저
  평가한다.
- detector+rule policy는 detector 결과나 test1 label을 보기 전에 별도 preregistration
  receipt로 고정한다. `IsolationForest` 결과를 본 뒤 새 fusion rule을 설계하지 않는다.
- common comparison table에는 동일 file universe, event units, normal exposure, episode
  builder, metric contract를 적용한다.
- negative result도 같은 artifact namespace에서 freeze하고 보고한다.

## 필수 synthetic/contract tests

1. exact dependency/environment receipt replay와 wrong-version rejection.
2. optional dependency 부재 시 lightweight imports PASS, detector entrypoint fail-closed.
3. 37-feature order/count/hash, split role, file identity, finite float64 boundary rejection.
4. label/test1/test2/held-out objects가 fit·calibration API에 들어오면 pre-I/O rejection.
5. config enum/type/range validation과 unknown estimator parameter rejection.
6. two independent synthetic fits under the exact environment produce canonical model-content
   hash/score/prediction equivalence; unordered dict/set이나 parallel scheduling에 의존하지 않음.
7. score direction test: `-score_samples`, larger-is-more-anomalous.
8. train3 nearest-rank `q=0.999`, strict `>`, equality no-alarm, zero/one-row edge cases.
9. serialize → close → reopen → score replay equivalence and corrupted/stale/wrong-authority
   model rejection.
10. atomic prediction custody: partial-write, mutation, stale config, wrong model, wrong
    threshold, label-before-freeze rejection.
11. common per-second adapter의 exact file universe/ordering/deduplication validation.
12. event/episode/Recall/FAR/overlap integration with synthetic labels only.
13. no network, provider, LLM, clock, current working directory, private path in scientific
    output.
14. Pilot V1 preservation manifest byte identity PASS.

## 남은 비결정 사항이 아닌 것

- candidate identity에는 실질적 동률이 없다. 따라서 지금 `DG-02`를 trigger하지 않는다.
- actual performance, superiority, operational usefulness는 아직 `UNKNOWN`이다.
- exact package versions는 dependency-resolution evidence로 고정됐으며 성능 결과를
  보고 선택한 hyperparameter가 아니다.
- temporal detector를 추가하지 않는 것은 현재 master's thesis의 scope control이다.

## 안전 카운터

- scientific execution: `0`
- scientific detector fit/predict/metric execution: `0`
- scientific-data-free synthetic tests: `17 / 17 PASS`
- test1 access: `0`
- test2/held-out access: `0`
- label access: `0`
- dependency installation: isolated V2 environment exact public stack `1`
- provider/LLM calls: `0`
- Pilot V1 modifications: `0`
