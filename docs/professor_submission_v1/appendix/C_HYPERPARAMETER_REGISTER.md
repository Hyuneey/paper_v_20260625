# 부록 C — 하이퍼파라미터 요약

이번 제출본에서는 어떤 값도 변경하거나 새 sensitivity sweep을 하지
않았습니다. 전체 16개 provenance register는
[기존 전체 레지스터](../../professor_first_results_v1/06_HYPERPARAMETER_PROVENANCE_REGISTER.md)에
있습니다.

## A. 사전등록 또는 정상 데이터에서 동결된 항목

| 항목 | 값 | 역할·근거 | 현재 평가 |
|---|---|---|---|
| profiling horizon grid | 1, 5, 10, 30, 60초 | delayed response 탐색 범위 | 합리적이나 다른 시간척도 sensitivity 미실시 |
| fit support | pooled ≥20, each train ≥5 | 관계 근거 최소량 | 정상 데이터 기반, 감사 완료 |
| calibration support | isolated events ≥5 | 별도 정상 구간 확인 | 정상 데이터 기반, 감사 완료 |
| PCA selected components | k=10 | 0.95 explained variance target로 정상 데이터에서 선택 | 선택 과정 확인 완료 |

## B. 합리적이나 sensitivity가 충분하지 않은 항목

| 항목 | 값 | 역할·근거 | 남은 위험 |
|---|---|---|---|
| relation consistency gates | fit pooled ≥0.70, per-file ≥0.60; calibration ≥0.60 | 방향 안정성 | 경계값 민감성 미평가 |
| effect-ratio gates | fit ≥2.0; calibration ≥1.0 | noise 대비 response | 변수 scale별 영향 가능 |
| PCA explained variance | 0.95 | reference detector subspace | detector 선택 의존 |
| D0 threshold quantile | 0.999 | 정상 SPE 상위 quantile | recall/FAR trade-off sensitivity 미실시 |
| D2 distinct-source count | 2 | single-source recovery 금지 | 보완 신호 억제와 FP 사이 trade-off |

## C. 구조적 한계가 관측된 항목

| 항목 | 정책 | 관측된 결과 | 평가 |
|---|---|---|---|
| D2 V1 temporal gate | 두 source의 exact same-second corroboration | D0 미탐 회복 0/3 | asynchronous signal과 구조 불일치 |
| D2 V2 temporal gate | per-rule native-horizon persistence | D0 미탐 회복 0/3, FAR 6.915070855955625 | 시간 기억만으로 utility 개선 실패 |

이 값들이 최적이라는 주장은 하지 않습니다. 다만 결과를 본 뒤 값을
변경하지 않았기 때문에 현재 negative fusion evidence의 해석은
보존됩니다.
