<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=a2dc415791dab575e45a9027f5d53efe20b96316a9f026068ecb7c66136d9ba3 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# 지금 연구는 어디까지 왔나

## 한 문장 상태

HAI 23.05 P1을 대상으로 한 전체 INNER 연구 경로는 구현되고 예비 실행 및 무결성
감사까지 끝났지만, 과학적 가설 검증·홀드아웃 일반화·새 컴퓨터 재현은 아직 끝나지 않았다.

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

이 수치는 독립 공격 사건 14개의 INNER 예비 관찰이다. 검증된 일반 성능으로 표현하면 안 된다.

## 아직 증명되지 않은 것

- GDN unique and stable scientific contribution beyond META and STAT
- Agentic verifier-feedback advantage
- Practical Rule-only operational utility
- Detector-plus-Rule improvement beyond the tested negative pilot policies
- Held-out generalization
- Human explanation usefulness

특히 GDN의 고유 기여와 Agentic 피드백의 이점은 아직 가설이다. 현재 T2에서는 피드백
행동이 0회였으므로 Agentic 장점이 실험된 것으로 볼 수 없다. D1은 D0와 다른 사건에
반응했지만 정상 FAR가 높아 실용성을 주장할 수 없다. 현재 D2 정책도 개선 주장을 지지하지 않는다.

## 가장 큰 위험 5개

- The INNER pilot contains only 14 independent attack events so stable performance and superiority cannot be inferred.
- Rule-only normal FAR is high in the frozen INNER pilot so operational utility is not established.
- GDN candidate evidence exists but unique stable contribution beyond META and STAT is unvalidated.
- Held-out generalization is unavailable because no OUTER scientific result exists.
- Fresh-machine reproducibility is incomplete despite strong public traceability.

## 다음에 해야 할 것

- Preregister expanded Rule-only and detector comparison evidence with more independent events and a stronger multivariate detector baseline.
- Design isolated stability and contribution tests for GDN and an actually exercised budget-matched feedback comparison for T2.
- Complete fresh-machine reproducibility and authority rehearsal before any newly authorized held-out study.

관리 작업의 다음 단계는 **RCC-003 — Research Timeline & Decision Backfill** 이고, 이후 전체
구조 검토는 **ARCH-000 — Full Architecture Overview Audit** 이다. 둘 다 사용자 승인 전에
자동으로 시작하지 않는다.

## 내가 직접 확인할 것

- Review the full current-state summary and challenge any unsupported component status.
- Approve or adjust the conservative claim boundaries before thesis wording uses them.
- Inspect the architecture overview and identify components that need explanation before ARCH-000.

Scientific authority: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`
