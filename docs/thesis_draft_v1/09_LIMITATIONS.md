# 8. 한계

## 8.1 과학적 한계

| 한계 | 현재 영향 | 주장 경계 |
|---|---|---|
| 하나의 HAI process | P1 Boiler 관계에 한정 | 다른 process/CPS로 일반화하지 않음 |
| INNER attack event 14개 | 통계 검정과 안정적 효과 추정 제한 | superiority 주장 없음 |
| 하나의 reference detector | detector choice 의존 가능 | PCA-SPE를 baseline으로만 해석 |
| sensitivity 미실시 parameter | 후보·관계·threshold 경계 의존 | preregistration을 optimality로 표현하지 않음 |
| D1 높은 FAR | standalone deployability 없음 | complementarity와 운영성을 분리 |
| D2 V1/V2 recovery 0/3 | incremental recall 없음 | combined improvement 주장 없음 |
| held-out 결과 없음 | generalization 미확인 | OUTER negative result로 표현하지 않음 |
| TSFM 미구현 | foundation-model 비교 없음 | 효과 주장 없음 |
| ARTIST segment selection 미구현 | learned segment proposal 없음 | trace localization과 동일시하지 않음 |
| human usefulness 미평가 | 설명의 사용자 효용 불명 | 실행 가능·추적 가능 범위만 주장 |
| causal validation 없음 | 관계가 원인임을 입증하지 못함 | root-cause claim 금지 |

## 8.2 방법 범위 한계

현재 relation family는 bounded continuous-step delayed response에 집중한다.
복잡한 feedback loop, multi-stage dynamics, decrease-family의 일반적 확장,
비정상 sampling은 충분히 다루지 않는다. variable role metadata와 P1 scope
selection에는 사람의 공정 지식이 남는다. GDN relation은 후보 근거일 뿐
물리 graph가 아니다.

## 8.3 평가 한계

event recall과 FAR/hour는 경보 utility를 분명하게 보여주지만 latency,
operator burden, explanation correctness, intervention quality를 평가하지
않는다. 14개 event에서 D0/D1 union 14/14는 흥미로운 기술 통계이나 독립
held-out replication이 없다. D2 정책도 hyperparameter search를 하지 않은
구조 시험이므로 최적 fusion의 부재를 증명하지 않는다.

## 8.4 소프트웨어·재현성 한계

public remote checkpoint는 source, config, frozen aggregate result를 강하게
추적할 수 있다. 그러나 raw HAI acquisition, private numeric/model artifacts,
locator configuration, process-local factory custody가 Git 밖에 있어 fresh-
machine portability는 weak다. 같은 machine과 private authority가 있는 경우도
setup 절차 때문에 reproducibility는 moderate다.

task-specific governance와 schema가 과학 kernel 주변에 많이 축적돼 있어
코드 탐색 비용이 높다. 이는 결과 타당성의 결함은 아니지만 공개 reproduction
package에는 장벽이다. 논문 제출 전 전체 refactor가 필수는 아니며, 향후
kernel extraction과 clean-machine rehearsal이 필요하다.

## 8.5 미결정 범위

추가 OUTER, stronger detector, ARTIST, TSFM은 모두 교수 결정 이후의 별도
연구다. 현재 초안은 이 대안을 완료된 결과처럼 선반영하지 않는다.
