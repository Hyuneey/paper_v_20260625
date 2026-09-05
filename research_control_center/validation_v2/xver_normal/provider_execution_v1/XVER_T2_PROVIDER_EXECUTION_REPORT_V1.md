# XVER T2 provider execution — normal-only result

Status: COMPLETE_NORMAL_ONLY / QA PASS. No attack, test, label, scenario or real eligibility authority was accessed.

## Provider

- Exact model snapshot: `gpt-5.4-mini-2026-03-17`; Responses API; reasoning none; temperature 0.7; top_p 1; store false.
- Calls: HAI22 61; HAI21 61; combined 122 (approved maximum 174).
- Metered tokens: input 333954; output 13563; total 347517 (approved maximum 3,622,912).
- Prospective standard-price arithmetic: USD 0.311499; not an invoice or actual billing record.
- Retry, fallback, provider tools, fourth calls: zero. Scientific concurrency: one.
- First scheduled HAI22 call passed receipt-first snapshot, schema, usage, privacy and durable-custody checks.

## HAI22

- Candidate N 29; first/second/third-call accepts 8/10/2.
- Explicit accepted NO_RULE 3; repair-budget failures 9.
- Feedback 32 actions across 21 pairs.
- Train2 admitted 20 pairs / 34 Rules; hidden-confirmed 31 Rules.
- Numeric bound / Formal V4 / train4 retained: 31 / 31 / 19 Rules; retained pairs 16.
- Portfolio hash: `b58313cd142256d000f89fd4a40512763b35e6b50752229109646bafc243fb5c`.

## HAI21

- Candidate N 29; first/second/third-call accepts 10/6/2.
- Explicit accepted NO_RULE 9; repair-budget failures 11.
- Feedback 32 actions across 19 pairs.
- Train2 admitted 18 pairs / 17 Rules; Block A-confirmed 9 Rules.
- Numeric bound / Formal V4 / Block B retained: 9 / 9 / 2 Rules; retained pairs 1.
- Portfolio hash: `9815c9a66debed593e21364377113d18422a840389d306a4a7648d5f035599dc`.

## Boundaries

GLOBAL5 was transmitted; EVENT10, META rank/tier, candidate arm, T0, train3, numeric values/policy, guard and attack/test information were not. HAI22 and HAI21 are normal-only method re-instantiations, not attack-performance or generalization results. No choice was made between T0 and T2.
