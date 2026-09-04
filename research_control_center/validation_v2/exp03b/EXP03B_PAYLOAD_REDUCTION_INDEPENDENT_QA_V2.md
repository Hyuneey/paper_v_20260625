# EXP03B-PAYLOAD-REDUCE-001 — 최종 준비 QA

판정: **PASS / PREPARED_DG03B_REVISED_PENDING**. Provider 실행 결과가 아니라 승인 전 구현·계약·합성 검증 결과입니다. DG-03B_REVISED 승인은 아직 없으며, 기존 승인을 상속하지 않습니다.

## 검토 대상

- 시작 integration: `6f1ae35eb0a8ca0143c1e3e5cb0b752a500e09d1`
- 구현 freeze commit: `6b8463f5e420485fca0848d315db8cb7af112117`
- 실행 freeze: `bacfd22859bb7014f3604abf4ad81b63586e1a98f21ddb0206b4a8e892f8ab8c`
- 승인 budget: `e6731a2fcfc1969287f74217b6cccb05f970673b5684a20493dec535b0ad28b6`
- 기존 SCI-02와 공개 V1 계약은 삭제·수정하지 않고 SCI-02B 및 V2 문서로 전향적으로 대체했습니다.

## 독립 검토와 역할

| 역할 | 범위 | 판정 |
|---|---|---|
| Agent A | semantic schema·T0·hidden verifier·arm terminal replay·SCI-04 | PASS |
| Agent B | post-train3 binder·고정 수식·max pooling·Formal V4·guard ordering | PASS |
| Agent C/D | payload·token/cost arithmetic·receipt-first·ledger·privacy firewall | PASS |
| Agent E | 최종 source/public artifacts 독립 재검토 | PASS, blocking finding 없음 |
| Coordinator | 유일 구현/Registry writer, 승인된 private aggregate hash replay | PASS |

공유 파일 writer 충돌: 0. Provider writer 실행: 0. Agent E는 private payload/vault를 다시 열지 않았으므로 private byte 보존은 coordinator의 read-only audit 증거이며 독립 재개봉 증거로 주장하지 않습니다.

## 검증 결과

- Focused: 95/95 PASS; 독립 Agent E도 95/95 PASS.
- Validation V2: 458 tests PASS, 기존 optional-dependency skip 14개 유지.
- RCC/UI: 최종 197/197 PASS (기존 193개 + 새 semantic reporting regression 4개). 독립 Agent E 검토 시 기존 193/193 PASS.
- Agent E: implementation hash 46/46, public self-hash 25/25 replay PASS.
- Registry + generated content + link/privacy validation: PASS.
- Compile 및 diff whitespace check: PASS.
- Synthetic future-runner fixture: receipt-first, resume, 3-call 제한, 모든 output/admission/train3 freeze, 실제 합성 Formal V4 변환, guard 호출 순서 PASS. 실제 provider 또는 실제 train4 실행을 의미하지 않습니다.

## 핵심 과학·방화벽 검증

1. 29-pair cohort 및 기존 structural/STAT/GDN evidence 값이 동일합니다.
2. Pair당 structural 20행 유지, numeric option 740행 → 0행입니다. GDN 5개 horizon 행과 STAT aggregate는 유지합니다.
3. Provider schema/parser는 numeric field·NUM alias·final EXP-02 identity를 거부합니다. T0 및 모든 provider arm은 semantic Rule만 만듭니다.
4. Train2 admission·feedback·retrieval은 semantic evidence만 사용합니다. SCI-01 gate, Rule-set completeness 및 horizon preference는 유지됩니다.
5. 모든 output, admission, train3 evaluation의 durable freeze를 replay하기 전 binder가 열리지 않습니다. Provider phase는 영구 종료되어 이후 numeric/guard 결과로 재호출할 수 없습니다.
6. Binder는 `RELATION_SPECIFIC_NORMAL_ONLY_V1:n7-q0.90-s2-f0.05`의 기존 수식 및 conservative max pooling만 사용합니다. Numeric authority 불완전·비유한 값은 fail-closed입니다.
7. Hidden reference substitution, train4 receipt mutation, understated request bound, ledger gap/orphan 및 freeze mutation을 거부합니다.
8. SCI-04의 semantic majority, failure ≠ NO_RULE, strict full-cohort denominator 및 Repeat 1 portfolio lock은 유지됩니다.
9. Agentic disposition thresholds는 완화하지 않았습니다. Numeric selection은 Agentic 평가에서 제외하고 Formal V4 conversion 및 train4 guard는 post-induction engineering 결과로 분리합니다.

## 보존·접근·custody

- PILOT V1: 3,021/3,021 blobs unchanged.
- 보호된 V2 public artifacts: 149 unchanged; V2A 39-rule, EXP-02, EXP-03 V1, EXP-04/05 포함.
- 기존 EXP-03B public files: 44 unchanged; 기존 private hash bindings: 215 unchanged.
- 새 private bindings: 149 replay PASS; private index는 hash/count/status만 공개합니다.
- Private vault restore/read smoke: PASS, `SINGLE_COPY_LOCAL_ONLY`. 두 번째 backup을 주장하지 않습니다.
- 이번 작업의 raw HAI value read, test1, test2, held-out, external attack, label, provider call, capability probe, credential read, private exposure: 모두 0.
- 승인된 기존 split-pure aggregate와 custody metadata의 로컬 읽기만 수행했습니다. 재훈련·재평가·post-result tuning은 없습니다.

## 재승인 값과 한계

Snapshot `gpt-5.4-mini-2026-03-17`, N=29, R=3, concurrency=1, T1=87 / T1-B=261 / T2≤261, 총≤609 calls. T2 ACCEPTED 즉시 종료, 네 번째 호출 금지.

로컬 tokenizer: 초기 min/median/max 1,562 / 1,863 / 1,942; T1 159,096, T1-B 477,288, maximal-shape T2 878,958, schedule 1,515,342 input tokens. Repair 값은 미래 응답을 예측한 값이 아니라 synthetic maximal-shape profile입니다.

별도 API hard cap: input 7,216,128; output 1,247,232; total 8,463,360 tokens; 표준 API 비용 USD 11.03. 이전 80,373,993 input / USD 65.90은 superseded입니다. 서버 framing reserve는 공식 보장이 아니므로 첫 승인 과학 호출의 실제 usage/snapshot/schema/receipt 검증 후에만 전체 schedule을 열며 초과·불명 계량은 정지합니다.

Capability·account 상태는 호출 금지에 따라 검증하지 않았습니다. 과학적 Agentic advantage는 **미실행/미검증**이며, 다음 단계는 [수정 DG-03B 결정](DG03B_PROVIDER_DECISION_BRIEF_V2.md)입니다. 교수님 package는 초안만 갱신했고 제출하지 않았습니다.
