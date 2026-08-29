# D0 PCA-SPE Detector는 실제로 어떻게 동작하는가

Scientific authority: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## 1. D0의 연구상 역할

D0는 HAI 23.05 P1의 37개 변수를 함께 보는 단순한 normal-only 다변량 기준 탐지기다. 정확한 명칭은 `D0_PCA_SPE_V1`, 역할은 **simple deterministic reference detector**다. 논문의 핵심 기여도, 강한 최신 탐지기의 대표도, PCA 최적성의 증명도 아니다.

## 2. 어떤 변수를 입력으로 쓰는가

고정된 순서의 P1-prefixed numeric column 37개를 사용한다. timestamp, label, attack metadata, 비-P1 column은 제외한다. Relation 후보용 12 source·12 target universe와는 다른 계약이다. 누락, NaN/Inf, shape·dtype·순서 불일치는 보간하지 않고 거절한다.

## 3. 정상 데이터를 어떻게 표준화하는가

Normal train1과 train2를 그 순서로 합친 뒤 각 변수의 population mean과 `ddof=0` population standard deviation을 구한다. scale은 최소 `1e-12`로 고정한다. sklearn `StandardScaler`가 아니라 NumPy로 구현한 명시적 계산이다.

```text
mu = mean(concat(train1, train2), axis=0)
scale = max(std(..., ddof=0), 1e-12)
Z = (X - mu) / scale
```

## 4. PCA는 무엇을 학습하는가

표준화한 train1+train2에서 `C=(Z.T @ Z)/n`을 만들고 대칭화한 뒤 `np.linalg.eigh`를 사용한다. 누적 설명분산이 0.95 이상이 되는 최소 `k`를 선택한다. 허가된 frozen fit에서는 `k=10`, residual dimension은 27이었다. 10은 미리 고정한 hyperparameter가 아니라 0.95 정책의 frozen 결과다.

Randomized solver는 없다. stable ordering, loading sign anchor, cutoff exact-tie fail-closed 규칙이 있다. 다만 BLAS/LAPACK 전체 build까지 공개 권한에 결속된 것은 아니므로 분류는 `DETERMINISTIC_WITH_ENV_ASSUMPTIONS`다.

## 5. SPE란 무엇인가

각 시점의 표준화 벡터를 retained PCA subspace에 투영해 복원하고, 원래 표준화 벡터와의 residual 제곱합을 계산한다.

```text
z = (x - mean) / scale
projection = (z @ Wk) @ Wk.T
residual = z - projection
SPE = sum(residual ** 2)
```

SPE는 시점별 residual magnitude이며 probability나 confidence가 아니다. smoothing, dilation, point adjustment도 없다.

## 6. Threshold는 어디서 결정되는가

이미 고정된 scaler/PCA로 normal train3의 각 행 SPE를 계산하고, stable ascending sort 뒤 `ceil(0.999*n)-1` 위치를 택한다. `n=126000`일 때 zero-based index는 125873이다. interpolation이나 분포 가정은 사용하지 않는다. Threshold artifact에는 train3 identity, q, index, comparator, `labels_used=false`, `test_used=false`와 hash가 들어가며 실제 값은 private custody에 남는다.

Train3는 relation confirmation에도 사용되지만 경로와 artifact가 분리돼 있다. 이는 `ACCEPTABLE_WITH_SCOPE_LIMITATION`이며 검증된 leakage는 아니다.

## 7. test1에서는 무엇을 하는가

Test1 feature 54,000행을 같은 frozen mean/scale/loadings으로 변환해 54,000개 SPE를 만든다. 점수는 private evidence로 고정하고, 공개 prediction에는 점수 값 대신 row별 Boolean alarm과 decision identity, score-vector content hash를 남긴다.

## 8. Alarm은 어떻게 만들어지는가

정확한 비교는 `score > threshold`다. 같은 값은 alarm이 아니다. 유효하지 않은 숫자나 authority는 normal로 처리하지 않고 hard error로 닫힌다.

## 9. Prediction은 언제 고정되는가

54,000개 prediction record를 atomic JSON 파일로 기록하고, fsync·replace 후 다시 읽어 schema·closure·self-hash를 검증한다. 그 뒤에만 state가 `PREDICTION_FROZEN`으로 이동한다. Frozen prediction은 metric 전후에도 원래 bytes와 동일해야 한다.

## 10. Label은 언제 보는가

Label loader는 state가 `PREDICTION_FROZEN`이 아니면 즉시 거절한다. 즉 test1 label은 scaler/PCA fit, train3 calibration, test1 score, point alarm, durable prediction artifact에 영향을 주지 않는다. D0의 경계는 label 전 in-memory object만 사용한 frozen D1보다 강하다.

## 11. 11/14는 무엇을 뜻하는가

14개의 contiguous attack-event unit 가운데 D0 alarm episode와 한 번 이상 겹친 unit이 11개였다는 **attack-event recall**이다. 통계적 독립성은 확립되지 않았고 point recall도 아니다. 이 결과는 현재 INNER pilot 관찰이며 final validation이 아니다.

## 12. FAR/hour는 무엇을 뜻하는가

876개 alarm point를 연속 구간으로 묶으면 전체 alarm episode 46개가 된다. 그중 attack timestamp와 겹치지 않는 normal false episode가 7개다. 이를 normal labeled exposure hour로 나눈 값이 `0.4939336325682589 episodes/hour`다. Point-level FPR과 다르다.

## 13. D0의 장점과 한계

장점은 normal-only fit, 닫힌 계산, 명시적 threshold, durable prediction-before-label, hash-bound artifact, LLM/network 비의존성이다. 한계는 단순 선형 PCA residual 모델, 한 frozen feature scope와 0.95 정책, 14-event pilot, 동일 데이터 환경 의존성, 미완료 fresh-machine reproduction이다.

## 14. 왜 stronger detector가 추가로 필요한가

D0는 Rule-only가 전통적 deterministic multivariate reference와 어떻게 다른 반응을 보이는지 확인하는 기준선이다. 현재 비교만으로 contemporary multivariate TSAD 대비 성능을 말할 수 없다. 새 독립 사전등록에서는 적어도 하나의 더 강한 다변량 detector를 추가해야 한다. ARCH-007은 후보를 선택하거나 구현하지 않았다.

결론: D0 구현·권한·예측 순서·frozen result lineage는 추적 가능하고 result integrity가 감사됐다. 성능 수치는 14-event pilot이며 우수성·일반화·SOTA 주장은 허용되지 않는다.
