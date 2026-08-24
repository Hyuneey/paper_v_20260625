# 구현 상태 매트릭스

상태 정의: **완료**, **완료·연구용**, **부분**, **미구현**, **역사/대체됨**.

| 영역 | 구성요소 | 상태 | 근거/비고 |
|---|---|---|---|
| 데이터 | HAI 23.05 source provenance·10개 승인 파일 custody | 완료 | byte equivalence·manifest 확인 |
| 데이터 | P1 Boiler process selection | 완료 | continuous-step feasibility에서 P1 고정 |
| 데이터 | SWaT/WADI 외부 검증 | 미구현 | 향후 연구 |
| 후보 | 144-pair universe, META/STAT/GDN | 완료·연구용 | top-10/20/40, 주 view top-20 |
| 후보 | upstream-aligned GDN | 완료·연구용 | candidate evidence이지 causal graph 아님 |
| 프로파일링 | normal-only delayed response fit/confirmation | 완료 | 23 pairs, 42 directional relations |
| 규칙 | T0/T1/T1-B/T2 construction | 완료·연구용 | provider 의존 arm은 재현용 receipt 필요 |
| 규칙 | normal-only numeric authority | 완료 | 420 bindings, 값은 private custody |
| 규칙 | deterministic validity/verifier | 완료 | 구조·evidence·parameter·split·runtime 검사 |
| 규칙 | Rule v1 decrease-family 일반 확장 | 부분 | 현재 v6 bridge 범위 제한 |
| runtime | COMMON-42 D1 LLM-free runtime | 완료·연구용 | INNER 실행·무결성 확인 |
| detector | D0 PCA-SPE | 완료·reference baseline | 0.95 variance, k=10, q=0.999 |
| fusion | D2 V1 same-second multi-source | 완료·negative result | 0/3 recovery |
| fusion | D2 V2 native-horizon multi-source | 완료·negative result | 0/3 recovery, FAR 증가 |
| fusion | D2 V3 | 미구현 | 현재 자동 설계 정당화 없음 |
| metric | event recall/FAR/recovery metrics | 완료 | 14 events, 51,019 normal sec |
| explanation | relation/horizon/satisfaction trace | 완료·연구용 | human usefulness 미평가 |
| explanation | ARTIST-style segment selection | 미구현 | 교수 결정 필요 |
| model | TSFM | 미구현 | 효과 주장 없음 |
| baseline | 강한 detector 추가 비교 | 미구현 | 교수 결정 필요 |
| OUTER | preregistration/authorization | 완료 | D0/D1/D2 V1 1회 범위 |
| OUTER | scientific result | 미구현/불가 | byte-read 전 custody 거부, 결과 없음 |
| custody | private path redaction·outside-Git | 완료 | 로컬 환경 binding 필요 |
| reporting | self-hashed public reports | 완료 | 역사적 harness remediation 존재 |
| continuity | state/ledger/handoff | 완료 | 교수 보고에는 최소화 |
| legacy | old DSL/verification/runtime/e2e | 역사/대체됨 | import compatibility only |
| ARGOS | reproduction/method validity | 역사/참조 | partial methodological support |

## 현재 남은 가장 큰 공백

1. held-out OUTER generalization 결과가 없다.
2. 강한 detector baseline과 비교하지 않았다.
3. ARTIST/TSFM 효과를 시험하지 않았다.
4. 설명의 사람 유용성을 평가하지 않았다.
5. 현재 fusion은 보완 신호를 실용 utility로 바꾸지 못했다.

