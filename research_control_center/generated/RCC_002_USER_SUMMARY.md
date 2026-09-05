<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=c8dd7e0e05f6efd13270749854b210426e7b220d0b4f521688fa4be92f000899 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
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

- DG-05: review conditional multi-panel feature access and post-global-freeze label/scenario lease
- DG05 remains NOT_APPROVED; no attack/test/label access
- DG06 remains required for professor submission

관리 작업의 다음 단계는 **DG-05 V2 METRIC VERIFIER CLOSURE — DG05-V2-METRIC-VERIFIER-CLOSURE-001** 이고, 이후 전체
구조 검토는 **고정 아키텍처의 외부 버전 adapter; 새 모델·rescue 금지** 이다. 둘 다 사용자 승인 전에
자동으로 시작하지 않는다.

## 내가 직접 확인할 것

- DG-05 V2 METRIC VERIFIER CLOSURE — DG05-V2-METRIC-VERIFIER-CLOSURE-001
- Preserve all frozen method, metric, custody, and single-copy private authorities
- DG06: professor package submission decision

Scientific authority: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## 현재 DG-04 / 외부 준비 Gate

DEC-030 records exact DG05 Executable V2 conditional reapproval, but functional pre-access replay found that the approved result builder and independent verifier omit the complete frozen eTaPR, delay, paired/McNemar, Rule/Fusion recovery, Rule runtime census, and normal-burden result surface. Phase A remains unstarted; attack/test access 0; labels/scenarios 0; lease 0; predictions 0; results 0. Current phase DG05_V2_BLOCKED_PRE_ACCESS; exact next DG05-V2-METRIC-VERIFIER-CLOSURE-001, followed by DG-05 REAPPROVAL under the new hashes. Professor package NOT_SUBMITTED; backup SINGLE_COPY_LOCAL_ONLY.
