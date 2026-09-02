# 주장과 한계 Matrix

| 주장 | 현재 상태 | 근거/한계 |
|---|---|---|
| V2 공통 authority·custody·metric contract가 구현되었다 | SUPPORTED_IMPLEMENTATION | 합성·negative tests와 독립 QA |
| fresh-machine synthetic 경로가 동작한다 | SUPPORTED_SYNTHETIC | clean checkout/fresh environment receipt |
| V2 GDN이 primary 또는 supporting contribution 요건을 충족한다 | DEVELOPMENT_NOT_SUPPORTED | EXP-01과 EXP-01B 모두 ablation 판정; EXP-01B combined K=29 소폭 향상은 split 안정성·기능·rule conversion 요건을 통과하지 못함 |
| relation-specific numeric policy가 정상 데이터 선택 규칙에서 선택되었다 | NORMAL_ONLY_SUPPORTED | EXP-02는 37개 후보 중 `RELATION_SPECIFIC_NORMAL_ONLY_V1:n7-q0.90-s2-f0.05`를 동결 선택; 공격 성능 우수성은 아직 미평가 |
| verifier feedback이 construction을 개선한다 | UNVALIDATED | EXP-03 natural cohort/provider 미실행 |
| Isolation Forest가 PCA-SPE보다 낫다 | UNVALIDATED | 선택만 완료, scientific fit/evaluation 미실행 |
| V2 Rule-only가 유용하다 | UNVALIDATED | EXP-04 미실행 |
| V2 fusion이 detector를 개선한다 | UNVALIDATED | EXP-04 미실행 |
| explanation이 trace에 구조적으로 충실하다 | UNVALIDATED_SCIENTIFIC | 합성 contract만 PASS, 실제 trace 미실행 |
| explanation이 사람에게 유용하다 | NOT_EVALUATED | 현재 thesis core 요구사항 아님 |
| held-out 일반화가 확인되었다 | NOT_SUPPORTED | held-out 접근 0 |
| PILOT V1 결과가 보존되었다 | SUPPORTED_INTEGRITY | 3,021/3,021 byte identity PASS |

결과 무결성은 scientific validation과 다릅니다. 또한 14개 contiguous attack-event units의 통계적 독립성은 확립되지 않았습니다.
