# DG-03B — 별도 provider 실행 승인 필요

상태: USER_DECISION_REQUIRED. 이전 DG-03 승인은 상속하지 않습니다.
모델: `gpt-5.4-mini-2026-03-17`. Responses endpoint, reasoning none, temperature 0.7, top_p 1, store false, retry 0, timeout 60초, concurrency 1. moving alias 금지.

| 항목 | 고정 상한 |
|---|---:|
| N / R | 29 / 3 |
| T1 / T1-B / T2 calls | 87 / 261 / 261 |
| 총 generation calls | 609 |
| input tokens | 80373993 |
| output tokens | 1247232 |
| total tokens | 81621225 |
| 표준 API 비용 USD | 65.90 |

전체 스케줄 완료 시 조기 종료 범위는 435~609회이며 실제 예상치가 아닙니다. one-call probe는 첫 과학 호출을 재사용하고 추가 호출하지 않습니다. 첫 응답·usage·snapshot·schema·privacy receipt 재생 PASS 전 다음 호출을 금지합니다.
29개 실제 train1 payload를 로컬 tokenizer로 프로파일링했습니다. 로컬 token count는 API usage와 동일하다고 가정하지 않으며, UTF-8 byte bound와 고정 framing 여유로 보수적인 call별 input 상한을 고정했습니다. 각 호출 후 실제 usage를 결속하고 초과/불명 응답은 fail-closed, 자동 retry 금지입니다.
외부 전송: candidate source/target, train1 tuple aggregate, NUM aliases와 aggregate option metrics, split-pure STAT/GDN, schema. T2만 bounded train2 retrieval aggregate를 허용합니다. 원시 rows·private numeric roles·최종 Rule/EXP02 선택·train3/4·test/labels·META 선언·경로·credential·타 arm 결과는 금지합니다.
정상 aggregate도 비공개 연구 파생정보이므로 별도 승인이 필요합니다. 이번 작업은 credential/capability/provider 접근 0입니다.
요금 근거: https://developers.openai.com/api/docs/models/gpt-5.4-mini — input $0.75/M, output $4.50/M. 가격 또는 snapshot 정책 변경 시 승인 계약을 재검토하고 임의 대체하지 않습니다.
예상 산출: append-only calls/responses/usage/latency, raw/admitted outputs, hidden train3 metrics, one-way train4 guard, disposition, 독립 QA. 완료 후 DG-04 정지; production portfolio 및 공격 접근은 승인되지 않습니다.
