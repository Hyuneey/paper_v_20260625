# EXP03B-PREP-001 독립 QA — 제한된 사전 감사

판정: `BOUNDED_PREFLIGHT_QA_PASS`.
전체 task: `BLOCKED_UNDEFINED_SCIENTIFIC_BINDINGS`.
이 PASS는 evidence builder, information firewall, verifier, runner 또는 scientific preregistration의
완료 판정이 아니다. 해당 구현·동결은 아직 진행하지 않았다.

## 역할 및 확인

- Agent A `exp03b_construct`: V1 입력·feedback reachability·재분류, 이후 budget/privacy 검토.
- Agent B `exp03b_evidence`: split-local evidence와 기존 producer 의존성.
- Agent C `exp03b_fairness`: arm fairness, guard/metric aggregation과 미정 명세.
- Agent E `exp03b_independent_qa`: 독립 공개 authority replay, source pointers, 6개 신규 테스트.
- Coordinator: 유일한 writer. provider writer 없음. shared-write conflict0.

독립 QA는149개 protected public blob, N29, confirmed21 pair/39 relations,609call 상한을
저장된 receipt와 동일하게 재생했다. V1 projection/template/verifier 코드가 재분류를 뒷받침한다.
기존 fit/confirmation gate가 서로 다른 역할과 수치임을 확인했다.
SCI-01/02는 명백히 material scientific choices이며 SCI-03/04도 실행 전 명시적 결속이 필요하다.

## 검증 범위

- 신규 공개/synthetic preflight tests6/6 PASS.
- 기존 EXP03 관련57개와 합산 focused63/63 PASS.
- RCC/UI193/193 PASS; 이번 확인 테스트 합계256개. 전체 Validation V2 scientific suite를 재실행한 것은 아니다.
- 기존 EXP03 private completed-output audit:585 request/response,390terminal,ledger identity PASS;
  이것은 이번 준비에서 유일하게 허용된 과거 private 출력 재생이며 raw HAI 데이터 읽기는0이다.
- PILOT V1 preservation3,021/3,021 PASS.
- Registry/generated validation PASS. 기존 Registry/Dashboard는 변경하지 않았다.
- Public privacy scan PASS; 실제 입력 pack에 대한 정보방화벽 테스트는 NOT_IMPLEMENTED.

## 미완료 요구사항을 PASS로 표시하지 않음

| 요구 | 상태 |
|---|---|
| V1 측정 대상 재분류 근거 | AUDITED |
| frozen authorities/call-output replay | PASS |
| EXP03B 과학 임계값·선택·guard/metric bindings | UNRESOLVED |
| 실제 train1 evidence pack / hidden authorities | NOT_MATERIALIZED |
| provider payload taint firewall / train2 verifier / arm runner | NOT_IMPLEMENTED |
| 실제29개 prompt 크기 / token / cost ceiling | NOT_FROZEN |
| synthetic full scientific arm suite / performance equivalence | NOT_RUN |
| DG-03B budget authorization | NOT_READY |
| central Registry/Dashboard/professor/private-vault update | DEFERRED_WITH_INCOMPLETE_PREPARATION |
| task branch push / integration merge | NOT_PERFORMED; full task PASS 조건 미충족 |

Agent QA 접근: provider0, credential0, private payload0, scientific dataset0, writes0.
Coordinator 접근: provider0, credential0, train/test/heldout/label0; 과거 EXP03 private 출력 read-only replay만 수행.
기존 결과·V2A·EXP02·EXP03 V1·EXP04/05·GDN 및 PILOT V1 변경0.
