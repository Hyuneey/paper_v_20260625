# 하이퍼파라미터 출처 레지스터

평가 등급:

- `JUSTIFIED_AND_AUDITED`: 사전 고정 근거와 독립 검증이 있음
- `REASONABLE_BUT_SENSITIVITY_UNTESTED`: 합리적 근거는 있으나 sensitivity 미실시
- `STRUCTURAL_MISMATCH_OBSERVED`: 결과에서 정책–신호 구조 불일치 확인
- `REFERENCE_BASELINE_ONLY`: 비교 기준선 목적
- `FUTURE_WORK`: 현재 결론 범위 밖

| parameter | value | scientific role | source/rationale | label used? | freeze point | sensitivity? | assessment | risk | possible future action |
|---|---|---|---|---|---|---|---|---|---|
| candidate Top-K | primary 20; views 10/20/40 | arm별 후보 예산 | candidate protocol의 bounded budget | 아니오 | C0 protocol | 예산 view는 보존, 성능 sweep 아님 | REASONABLE_BUT_SENSITIVITY_UNTESTED | 후보 누락/중복 | thesis appendix에 제한 명시 |
| profiling horizons | 1, 5, 10, 30, 60초 | delayed response 탐색 | continuous-step preregistration | 아니오 | BR1/D0 protocol | 아니오 | REASONABLE_BUT_SENSITIVITY_UNTESTED | 다른 시간척도 누락 | 후속 독립 연구 |
| source refractory | 10초 | 중복 step event clustering | frozen continuous-step policy | 아니오 | BR1 | 아니오 | REASONABLE_BUT_SENSITIVITY_UNTESTED | event count 민감성 | 범위 제한 명시 |
| cross-source isolation radius | ±2초 inclusive | 동시 다른 source 오염 방지 | frozen isolation rule | 아니오 | BR1 | 아니오 | REASONABLE_BUT_SENSITIVITY_UNTESTED | 진짜 동시 제어 제거 가능 | 후속 robustness |
| fit support | pooled≥20, each train≥5 | fit evidence 최소량 | train1/2 사전 gate | 아니오 | D0 profiling protocol | 아니오 | JUSTIFIED_AND_AUDITED | rare relation 제외 | 데이터 확대 시 재검토 |
| fit consistency | pooled≥0.70, per-file≥0.60 | 방향 안정성 | preregistered normal-only gate | 아니오 | D0 profiling protocol | 아니오 | REASONABLE_BUT_SENSITIVITY_UNTESTED | 경계값 의존 | sensitivity appendix 후보 |
| fit effect ratio | ≥2.0 | noise 대비 반응 크기 | robust normal effect gate | 아니오 | D0 profiling protocol | 아니오 | REASONABLE_BUT_SENSITIVITY_UNTESTED | scale별 편향 | future sensitivity |
| calibration support | ≥5 isolated events | train3 confirmation 최소량 | confirmation protocol | 아니오 | D0/D2 confirmation | 아니오 | JUSTIFIED_AND_AUDITED | 낮은 support | 외부 data 확인 |
| calibration consistency | ≥0.60 | 방향 confirmation | frozen confirmation gate | 아니오 | D0/D2 confirmation | 아니오 | REASONABLE_BUT_SENSITIVITY_UNTESTED | 경계값 의존 | future sensitivity |
| calibration effect ratio | ≥1.0 | train3 effect 유지 | frozen confirmation gate | 아니오 | D0/D2 confirmation | 아니오 | REASONABLE_BUT_SENSITIVITY_UNTESTED | 약한 관계 허용 | future sensitivity |
| PCA variance target | 0.95 | D0 retained subspace | conventional reference baseline | 아니오 | D0 design | 아니오 | REFERENCE_BASELINE_ONLY | detector choice 의존 | 강한 baseline 결정 |
| PCA selected k | 10 | D0 retained components | train4 normal PCA가 0.95 target로 선택 | 아니오 | D0 training | 재계산 검증만 | JUSTIFIED_AND_AUDITED | split 특이성 | 다른 split은 새 preregistration |
| D0 threshold quantile | 0.999 | SPE alarm threshold | normal train4 upper quantile | 아니오 | D0 design/training | 아니오 | REFERENCE_BASELINE_ONLY | FAR/recall 민감 | stronger baseline 또는 prereg sweep |
| D2 distinct-source count | 2 | rule corroboration | single-source fallback 금지 | V1 설계에는 이전 INNER 문제 인식, 값 tuning은 없음 | D2 V1 design | 아니오 | STRUCTURAL_MISMATCH_OBSERVED | signal 억제 또는 FP 허용 | 자동 V3 금지, 교수 결정 |
| D2 V1 temporal policy | exact same-second | conservative corroboration | fixed structural gate | V1 결과 전에 고정 | D2 V1 design | 아니오 | STRUCTURAL_MISMATCH_OBSERVED | asynchronous attack signal 누락 | V2가 구조 문제만 시험 |
| D2 V2 temporal policy | per-rule native horizon, causal/inclusive | asynchronous evidence memory | 이미 고정된 COMMON-42 horizon | prior diagnostic은 문제 정의에 사용; 새 test1 window 없음 | D2 V2 preregistration | 아니오 | STRUCTURAL_MISMATCH_OBSERVED | FAR 6.915, 회복 0 | further fusion 중지 권고 |

## 해석

하이퍼파라미터가 “아무 근거 없이 선택”된 것은 아니지만, 전체 sensitivity가 끝난 것도 아니다. 정상 데이터 기반 authority와 사전 고정은 leakage를 줄였고 재현성을 높였지만, 외부 일반화나 최적값을 보장하지 않는다. 특히 D2 V1/V2는 결과가 보여 준 구조적 mismatch 자체가 중요한 negative evidence다.
