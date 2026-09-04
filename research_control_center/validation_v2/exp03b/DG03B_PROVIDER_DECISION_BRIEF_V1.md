# DG-03B — 아직 provider 승인을 요청할 단계가 아님

상태: `NOT_READY_FOR_PROVIDER_AUTHORIZATION`.
`BLOCKED_UNDEFINED_SCIENTIFIC_BINDINGS`를 해소하고 실제29-pair payload를 profiling한 뒤
`USER_DECISION_REQUIRED`로 전환한다. 옛 DG-03 승인과 USD10.07은 EXP03B에 적용되지 않는다.

| 항목 | 현재 확인 상태 |
|---|---|
| 비교용 선호 snapshot | gpt-5.4-mini-2026-03-17; 새 capability probe 안 함 |
| 후보 endpoint | https://api.openai.com/v1/responses; 접속 안 함 |
| N / R | 29 / 3 |
| T1 / T1-B / T2 최대 | 87 / 261 / 261 |
| 총 최대 generation calls | 609; one-call probe는 승인 후 이 예산 안에 포함 |
| concurrency | 1 |
| input/output/total token caps | NOT_FROZEN |
| standard API cost ceiling | NOT_FROZEN |
| 실제29-pair prompt profile | NOT_AVAILABLE |
| reasoning / sampling / schema / prompt / timeout | 아직 새 EXP03B 계약으로 동결되지 않음 |
| 이번 provider calls / credential reads / capability probes | 0 / 0 / 0 |

공식 모델 문서의 표준 단가는 input USD0.75/M, output USD4.50/M이다.
[공식 모델 문서](https://developers.openai.com/api/docs/models/gpt-5.4-mini).
이 단가 확인은 account capability나 새 예산 승인을 뜻하지 않는다.
과거 실제 소비 토큰이나 synthetic pack 크기를 새 natural cohort의 exact profile로 대신하지 않는다.

향후 승인 대상 payload는 candidate pair identity와 bounded train1-only aggregate evidence이며
T2에 한해 규정된 train2 issue/retrieval만 추가한다. final tuple, selected-policy identity,
V2A Rule/descriptor/hash, hidden train3/train4 결과, raw rows, attack/test 정보, private path,
credentials, META tier/rank/manual text, detector outcomes는 금지한다.

실제 payload 준비 후 system/schema/alternatives/37numeric options와 worst-case
feedback/retrieval/history를 모두 포함해 cap을 계산한다. no retry/receipt-first/concurrency1,
최대3회와 ACCEPTED early stop, append-only private custody, 독립 QA를 적용할 예정이다.
실행 지시문은 지금 READY_TO_RUN으로 발행하지 않는다.
