# DG-03B_REVISED — 의미적 Rule induction 별도 승인

USER_DECISION_REQUIRED. 기존 DG-03/DG-03B 승인과 USD65.90·80,373,993 input ceiling은 상속하지 않습니다. 기존 V1은 역사적 보존입니다.

| 승인 항목 | 고정 값 |
|---|---:|
| snapshot | gpt-5.4-mini-2026-03-17 |
| N / R | 29 / 3 |
| T1 / T1-B / T2 최대 calls | 87 / 261 / 261 |
| 총 최대 calls | 609 |
| 최대 input tokens | 7,216,128 |
| 최대 output tokens | 1,247,232 |
| 최대 total tokens | 8,463,360 |
| 표준 API 비용 상한 | USD 11.03 |
| initial / repair call input cap | 7,168 / 23,552 |
| call output cap | 2,048 |

Responses endpoint `https://api.openai.com/v1/responses`; reasoning none, temperature0.7, top_p1, store=false, standard service tier, timeout60초, retry0, concurrency1. moving alias·도구·자동 fallback 금지. T2 ACCEPTED 즉시 종료, 최대3 calls. 완료 schedule 범위는435~609회이며 예상 실사용량 예측이 아닙니다.

A. **로컬 tokenizer 추정**: tiktoken0.12.0/o200k_base로 29개 초기 요청을 정확히 직렬화·계수. min/median/max=1562/1863/1942. T1 159,096, T1-B 477,288, 최대형태 T2 878,958, 전체 1,515,342 input tokens. repair는 미래 결과 대신 synthetic 최대형태 profile입니다. 모든 가능한 미래 출력의 BPE 최대값이나 API billing과 동일하지 않습니다.

B. **API hard ceiling**: 작은 closed ASCII request의 UTF8 byte/escape bound와512 service-framing reserve, 단계별 cap 및 transport 전 누적 input/output/cost reservation. framing은 문서로 보장된 서버 내부 token 수가 아닌 보수적 가정입니다. 첫 승인된 과학 호출 1회에서 실제 snapshot·usage·schema·privacy·durable receipt를 검증한 뒤 full schedule을 엽니다. 계량 상한 초과/불명·가격/모델 변경은 정지하며 자동 retry하지 않습니다.

외부 전송: fixed pair ID/source/target, train1 structural20 rows·STAT·GDN, schema/criteria. T2 repair만 bounded train2 structural alternatives를 추가합니다. numeric rows740→0, NUM aliases/수치정책 선택/최종 EXP02 identity는 전송하지 않습니다. private raw rows/role values, 최종 정답, train3/4, test/labels/heldout, detector/Fusion, META 선언, 경로·credential은 금지합니다. Aggregate는 비공개 연구 파생정보이므로 이 별도 승인이 필요합니다.

요금 근거: [공식 GPT-5.4 Mini 문서](https://developers.openai.com/api/docs/models/gpt-5.4-mini), 표준 input $0.75/M, output $4.50/M. 예상 최대 산식=7216128×0.75/M+1247232×4.50/M, 센트 올림.

Budget hash `e6731a2fcfc1969287f74217b6cccb05f970673b5684a20493dec535b0ad28b6`. Execution freeze `bacfd22859bb7014f3604abf4ad81b63586e1a98f21ddb0206b4a8e892f8ab8c`. Implementation commit `6b8463f5e420485fca0848d315db8cb7af112117`. Output/ledger/latency/cost는 append-only private custody. 모든 outputs/admissions/train3 freeze 후 고정 SCI02B·FormalV4·train4. 독립 QA 후 DG-04 정지. V2A39-rule·EXP03V1·EXP04/05·held-out 방법은 변경하지 않습니다. 현재 provider/credential/probe=0.
