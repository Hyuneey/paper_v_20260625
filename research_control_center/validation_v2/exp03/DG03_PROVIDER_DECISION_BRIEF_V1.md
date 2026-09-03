# DG-03 — EXP-03 Provider 실행 결정안 V1

상태: `USER_DECISION_REQUIRED`; provider/API 호출 `0`.

## 제안

- 권고 provider/model: OpenAI API / `gpt-5.4-mini`
- fallback: OpenAI API / `gpt-5.4`
- 이유: 동일 provider 안에서 structured constrained construction을 비교하고, mini를 주 선택으로
  두어 최대 비용을 제한한다. 실제 model availability는 승인 직전 capability receipt로 확인한다.

## 고정 cohort와 budget

- natural cohort: V2A frozen 39 directional relations (`N=39`)
- stress cohort: public synthetic terminal-taxonomy fixtures 10N records, provider calls 0
- repeats: `R=3`
- T1: 117 calls
- T1-B: 351 calls
- T2: 최대 351 calls
- 전체 maximum: `21N = 819` generation calls
- call당 input hard cap: 4,096 tokens
- call당 output hard cap: 2,048 tokens
- 총 input cap: 3,354,624 tokens
- 총 output cap: 1,677,312 tokens
- 총 token cap: 5,031,936 tokens
- scientific concurrency: 1

2026-09-04 공개 standard API 단가를 적용한 ceiling은 `gpt-5.4-mini` 약 USD 10.07
($0.75/M input, $4.50/M output), fallback `gpt-5.4` 약 USD 33.55
($2.50/M input, $15/M output)다. cached discount와 Batch discount는 budget에 반영하지 않는다.

## Provider로 보내는 정보

허용: relation ID, source/target identity와 direction, selected horizon, approved numeric reference ID,
bounded aggregate normal-only evidence. 금지: raw rows, private numeric payload, label/attack interval,
test1/test2/held-out, detector result, 다른 arm 결과, local path, credential.

`T0/T1/T1-B/T2`는 같은 cohort/evidence/schema를 사용한다. T1은 1 call, T1-B는 3 independent
calls, T2는 verifier feedback을 포함한 최대 3 calls다. natural과 stress는 합치지 않는다.

## 실행 전 추가 receipt

사용자가 DG-03을 승인해도 transport는 즉시 열리지 않는다. exact model availability, prompt,
schema, evidence projection, privacy, cost ceiling, receipt-first one-call authorization, output/private
custody hash가 모두 일치해야 한다. mismatch, cap exceed, credential leakage, fourth call, incomplete
schedule은 fail closed다.

Expected outputs: append-only call ledgers, sanitized terminal-class artifacts, proposal/verifier/controller
hashes, per-arm repeat metrics, cost/latency receipt, independent QA. EXP-03은 V2A portfolio, test1 결과,
held-out method set을 바꾸지 않는다.

## 필요한 사용자 결정

`OpenAI gpt-5.4-mini`, 최대 819 calls, 5,031,936 tokens, USD 10.07 ceiling과 위 redacted projection을
승인할지 결정한다. 승인 전 capability probe, credential read, provider call은 모두 금지된다.
