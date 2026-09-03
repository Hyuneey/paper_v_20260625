# EXP-04 독립 결과 무결성 점검

판정: PASS. 이 판정은 결과 결속·산술·보존 검증이며 최종 과학적 검증이 아니다.

독립 reviewer가 production metric 함수를 사용하지 않는 표준 라이브러리 oracle로 67,797개 assertion을 점검했다.
5개 방법 × 54,000개 동일 coordinate, 14개 연속 공격 구간, 정상 노출 51,019초를 확인했다.
고유 alarm second → 최대 연속 episode → 공격 overlap 제외 → normal false episode 산술을 독립 재구성했다.

- 예측·bundle pre/post label hash 동일, mutation 0.
- all-method freeze 다음 one-shot capability 발급·소비·파기; pre-freeze label 0.
- source/config/39-rule portfolio/GDN sidecar 시작·종료 hash 동일.
- PCA+Rule와 IF+Rule은 base pointwise preservation PASS; 추가 Recall 0, normal false episode 각각 +2.
- 보고서 5개 행은 EXP04_RESULTS_V1.json self-hash 0f3f5966a35e35ae663e60ddbb8afb7ce62e35081a7f9383e9aaf61b75064db1 에 결속.
- 독립 reviewer의 raw HAI·raw label·test2·heldout 접근 0.

한계: 독립 reviewer는 raw label을 다시 열지 않았다. Frozen event authority와 label identity/parser gate를 검증했다.
EXP-05는 별도 reviewer가 26개 full-unit batch, 6,418개 trace 모두와 130개 선택적 GDN 문구를 확인했다.
80개 관련 파일의 before/after hash 동일; 모든 11개 fidelity 검사 PASS.
자세한 QA assertion/counter는 INDEPENDENT_QA_V1.json에 기록했다.
