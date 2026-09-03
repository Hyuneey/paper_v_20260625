# VALIDATION V2 다중 HAI 평가 Master Plan V1

## 고정된 현재 상태

- V2A: 29 META+STAT pairs → 39 directional relations → 39-rule Formal V4 portfolio.
- EXP-02: `RELATION_SPECIFIC_NORMAL_ONLY_V1:n7-q0.90-s2-f0.05`.
- EXP-04/05는 HAI 23.05 test1 `DEVELOPMENT_ONLY`; 재실행·retuning 금지.
- GDN은 `LEARNED_GRAPH_SUPPORTING`; 실행 authority가 아닌 설명 sidecar다.
- META는 `HYBRID_REVIEWED_METADATA`이며 분실된 private reviewed input을 재구성하지 않는다.

## Panel 순서

1. `PANEL-D`: 기존 HAI 23.05 test1 결과 보존.
2. `PANEL-H`: HAI 23.05 test2, DG-05 이후 one-shot primary held-out.
3. `PANEL-X1`: HAI 22.04, HAI23 integrity PASS 뒤 external replication 1.
4. `PANEL-X2`: HAI 21.03, HAI22 integrity PASS 뒤 external replication 2.
5. 버전별 결과를 동결한 뒤 `CROSS-VERSION-SYNTHESIS-001` 수행.

## 공통 선행 Gate

- exact official dataset/version/file/scenario identity
- outcome-blind P1 eligibility custodian
- 버전별 normal-only fit/calibration/selection authority
- fixed method/config/fusion contract
- official eTaPR pin과 conformance
- durable label-blind prediction freeze
- one-shot label lease
- prediction byte identity after labels
- independent arithmetic/result-integrity QA

HAI 23.05 test2는 기존 V2A 방법 bytes를 사용한다. HAI 22.04/21.03은 공격 label 없이 동일한
algorithm/policy를 재인스턴스화한다. 한 버전의 결과를 보고 다음 버전의 정책을 바꾸지 않는다.

## 해석 경계

각 버전은 별도 numerator/denominator와 Wilson 95% interval을 가진다. exact McNemar는 동일
eligible scenario set에서 미리 고정한 paired comparison에만 사용한다. 146개 nominal scenario는
IID가 아니며 version-macro mean도 설명적 summary일 뿐이다. `FINAL_VALIDATED`와
`generalized`는 모든 gate와 evidence가 충족되기 전까지 금지한다.
