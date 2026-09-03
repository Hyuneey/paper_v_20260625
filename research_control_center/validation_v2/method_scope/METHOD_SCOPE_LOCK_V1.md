# 연구 범위 고정 — V2-GDN-FRONT-EXP04-001

후보 제안은 META+STAT, 관계 채택은 정상 데이터의 시간적 관계 분석,
수치 권한은 EXP-02의 동결된 정상 전용 정책, 실행 권한은 Formal V4이다.
V2A의 29개 후보 pair, 21개 확인 pair, 39개 방향 규칙은 변경하지 않는다.

HAI-adapted 다중 지평 GDN은 주요 **학습 그래프 보조 근거 모듈**이다.
GDN은 핵심 후보 권한, 인과 그래프, 규칙 채택 권한 또는 추가 detector가 아니다.
EXP-01/01B의 부정적 결과와 EXP-01C의 LEARNED_GRAPH_SUPPORTING은 그대로 보존한다.
설명용 sidecar는 규칙·수치·방향·지평·PASS/FAIL/ABSTAIN을 변경할 수 없다.

잠정 제목: GDN-Assisted Evidence-Bound Relational Rule Construction for Explainable Multivariate Time-Series Anomaly Detection.
대안: Evidence-Bound Relational Rule Construction with Domain Priors and GDN-Based Learned-Graph Evidence.
최종 제목은 DG-04에서 결정한다. 새 GDN 실험이나 EXP-01D는 만들지 않는다.

실행 전 연결 코드와 근거를 Commit A에, 정확한 실행 계약을 Commit B에 고정한다.
test1 feature 접근 후 구현 변경이 필요하면 BLOCKED_POST_FEATURE_EXECUTION_REVISION_REQUIRED로 중단한다.
test1은 DEVELOPMENT_ONLY이며 test2/held-out, provider, 추가 GDN 학습은 금지한다.
