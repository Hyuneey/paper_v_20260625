# 부록 B — 구현 상태

상태는 **완료**, **완료·연구용**, **부분**, **미구현**으로 구분합니다.

| 영역 | 구현 항목 | 상태 | 비고 |
|---|---|---|---|
| 데이터 | HAI 23.05 provenance와 P1 Boiler 범위 | 완료 | 첫 연구 범위 고정 |
| 후보 | 144쌍과 metadata/statistics/graph ranking | 완료·연구용 | graph relation은 인과 관계가 아님 |
| 프로파일링 | normal-only delayed response fit/confirmation | 완료 | 23쌍, 42개 방향 관계 |
| 규칙 | template 및 bounded LLM construction | 완료·연구용 | LLM 수치 생성 금지 |
| 규칙 | normal-only numeric references | 완료 | 공개 보고서에는 민감한 수치 미포함 |
| 검증 | deterministic verifier | 완료 | 유효성·근거·실행 조건 확인 |
| runtime | 42-rule D1 LLM-free runtime | 완료·연구용 | INNER 결과 확인 |
| detector | PCA-SPE D0 | 완료 | reference baseline |
| fusion | D2 V1 same-second | 완료 | 미탐 회복 0/3 |
| fusion | D2 V2 native-horizon | 완료 | 미탐 회복 0/3, FAR 증가 |
| metrics | event recall, FAR/hour, recovery | 완료 | INNER 14 events |
| explanation | temporal relation + satisfaction trace | 완료·연구용 | human study 미실시 |
| rule family | 더 복잡한 decrease/multi-stage dynamics 일반화 | 부분 | 현재 relation family 제한 |
| TSFM | foundation model comparison | 미구현 | 효과 주장 없음 |
| ARTIST | segment proposal/selection | 미구현 | 교수 결정 필요 |
| detector | stronger multivariate baseline | 미구현 | 교수 결정 필요 |
| validation | held-out scientific result | 미구현 | 데이터 읽기 전 중단, 결과 없음 |
| explanation | human usefulness evaluation | 미구현 | 후속 연구 후보 |

현재 구현은 연구 prototype으로 재현·검증됐지만 production deployment를
주장하지 않습니다. 전체 코드 영역별 목록은
[기존 구현 상태표](../../professor_first_results_v1/05_IMPLEMENTATION_STATUS_MATRIX.md)에
있습니다.
