<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=c752d7a6fd77b3de559afb880cb003a45b9cd44fa9ba8113133949ddc6f347f2 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# 지금 연구는 어디까지 왔나

## 한 문장 상태

HAI 23.05 P1을 대상으로 한 전체 INNER 연구 경로는 구현되고 예비 실행 및 무결성
감사까지 끝났지만, 과학적 가설 검증·홀드아웃 일반화·새 컴퓨터 재현은 아직 끝나지 않았다.

## 상태 라벨 읽는 법

- **구현됨 / 실행됨**은 엔지니어링 상태다. 성능 검증을 뜻하지 않는다.
- **Evidence-reviewed**는 소스나 공개 증거 상태를 고정 권한과 대조했다는 뜻이다.
  과학적 성능을 감사하거나 검증했다는 뜻이 아니다.
- **Result-integrity audited**는 명시된 고정 결과의 보관·불변성·순서·산술을 확인했다는
  뜻이다. 우수성이나 일반화를 입증하지 않는다.
- **Independently reproduced**는 필요한 환경과 custody에서 독립 재현했다는 별도 상태다.
- 과학적 주장의 허용 범위는 오직 `claims.csv`가 결정한다. 구성요소의 호환용
  `claim_ready` 필드는 좁은 구현·계약 문구만 지원하며 과학적 성능 검증을 뜻하지 않는다.

이 숫자들은 하나의 연구 완료율이 아니다.

## 이미 만들어진 것

데이터 출처와 분할 통제에서 시작해 META·STAT·GDN 후보 탐색, 관계 프로파일링,
normal-only 수치 권한, 규칙 생성, 결정론적 검증기, COMMON-42 고정 규칙, LLM 없는
고정 규칙 런타임, D0/D1/D2 평가와 결과 무결성 감사까지 이어지는 구조가 있다.

## 실제 실행된 것

- 144개 가능한 관계에서 META·STAT·GDN이 각각 top-20을 만들었고 합집합은 47개였다.
- 23개 pair context에서 42개 방향성 시간 관계가 확인되어 COMMON-42로 고정되었다.
- T0/T1/T1-B/T2 규칙 생성 경로가 모두 실행되었고 승인 수는 42/42/42/39였다.
- D0, D1, D2 V1, D2 V2의 INNER 결과가 고정되고 독립 무결성 감사를 받았다.
- OUTER는 실행 결과가 아니라 차단 기록만 있다.

## 현재 관찰된 결과

- D0: 11/14 attack-event response; Normal FAR 0.4939336325682589 episodes/hour.
- D1: 13/14 attack-event response; Normal FAR 40.50255787059723 episodes/hour.
- 두 신호의 사건 겹침: both 10; D0-only 1; D1-only 3; neither 0.
- D2 V1: 11/14; Normal FAR 0.7056194750975128 episodes/hour; D0-miss recovery 0/3.
- D2 V2: 11/14; Normal FAR 6.915070855955625 episodes/hour; D0-miss recovery 0/3.

이 수치는 통계적 독립성이 입증되지 않은 14개 연속 attack-event unit의 INNER 예비 관찰이다.
검증된 일반 성능으로 표현하면 안 된다.

## 아직 증명되지 않은 것

- Agentic의 T0 대비 우월성·고정 cohort 밖 전이·held-out utility
- Practical Rule-only operational utility
- Detector-plus-Rule improvement beyond the tested negative pilot policies
- Held-out generalization
- Human explanation usefulness

특히 GDN의 고유 기여와 Agentic 피드백의 이점은 아직 가설이다. 현재 T2에서는 피드백
행동이 0회였으므로 Agentic 장점이 실험된 것으로 볼 수 없다. D1은 D0와 다른 사건에
반응했지만 정상 FAR가 높아 실용성을 주장할 수 없다. 현재 D2 정책도 개선 주장을 지지하지 않는다.

## 가장 큰 위험 5개

- The INNER pilot contains only 14 contiguous attack-event units; statistical independence is not established, so stable performance and superiority cannot be inferred.
- V2A Rule-only도 정상 FAR37.6095/hour로 높아 운영 효용 미확인.
- EXP-01/01B primary GDN 미지원;EXP-01C는 bounded supporting evidence만 제공한다.
- Held-out generalization is unavailable because no OUTER scientific result exists.
- 필수 private122artifact 보존/재생 PASS이나 SINGLE_COPY_LOCAL_ONLY이고 fresh-machine scientific reproduction은 미실시.

## 다음에 해야 할 것

- 승인된 GLOBAL5 / AUX EVENT10 분리 binding 유지
- Execution adapter·custody·환경·preflight 완성 후 정상-only 12-run
- T0·provider pack·budget 완료 후 DG-XVER-PROVIDER 별도 승인

관리 작업의 다음 단계는 **HAI-XVER-NORMAL-PREP-001** 이고, 이후 전체
구조 검토는 **고정 아키텍처의 외부 버전 adapter; 새 모델·rescue 금지** 이다. 둘 다 사용자 승인 전에
자동으로 시작하지 않는다.

## 내가 직접 확인할 것

- 현재 GDN evidence 역할 추가 결정 불필요
- 정확 evidence/budget 후 DG-XVER-PROVIDER 승인
- DG05 공격 접근 및 DG06 교수 제출은 별도

Scientific authority: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## 현재 DG-04 / 외부 준비 Gate

HAI-XVER-NORMAL-PREP-001: APPROVED_WITH_SEPARATED_GDN_EVIDENCE_ROLES.
이전 BLOCKED_GDN_METHOD_CHANGE_REQUIRED의 estimator 역할 선택은 사용자 승인으로 해소됐습니다.
Provider train1 / bounded retrieval train2에는 EXP03B-compatible split-pure GLOBAL 5-row GDN만 사용합니다.
SCI01 split-local event와 seed별 purged validation 교집합의 EVENT 10-row는 AUXILIARY_CORROBORATION_ONLY입니다.
Global/event 융합, event의 provider·retrieval·verifier·candidate 사용, train3/4 또는 numeric policy 기반 event 선택을 금지합니다.
3개 seed 전부 유지; best-seed 선택 없음. 별도 타입과 실제 frozen projector adapter 합성검사 15 PASS 및 독립 scoped QA PASS.
과학적 역할 binding은 완료됐지만 버전별 execution adapter·custody·environment·performance preflight 통합은 남아 있습니다.
현재 GDN scientific runs 0/12, 외부 T0·T2 pack·정확 token/cost 미완료; provider/credential/공격0.
DG-03B_REVISED 승인으로 완료된 EXP03B와 기존 DEC-025 / Stage A / V2A39 / T0 22 / T2 Repeat1 21 Rules / EXP02 / EXP04/05 / PILOT 결과는 불변입니다.
T2 > T1-B는 정상-only 의미 유도 비교에 한정되고 T0보다 우수하지 않습니다.
DG-03C의 현재 gate명 DG-XVER-PROVIDER는 NOT_READY_EVIDENCE_PENDING; DG05 NOT_APPROVED; 교수 package NOT_SUBMITTED; vault SINGLE_COPY_LOCAL_ONLY.
