# ARCH-001 Independent QA Report

Status: `PASS_WITH_DOCUMENTED_GOVERNANCE_FINDINGS`

Scientific authority: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## Independent verdict

The data, split, label-access, and custody map is consistent with the inspected
pinned source and public-safe frozen evidence. The correct leakage conclusion is
`NO VERIFIED LEAKAGE FOUND`; the audit does not claim that leakage is impossible.

## Required QA questions

| # | Question | Answer |
|---|---|---|
| 1 | Is dataset identity supported? | YES |
| 2 | Is P1 scope supported? | YES |
| 3 | Are all split roles evidence-based? | YES, with distributed-enforcement qualification |
| 4 | Are train1/train2 relation-fit roles verified? | YES |
| 5 | Is train3 dual use accurately represented? | YES; `ACCEPTABLE_WITH_SCOPE_LIMITATION` |
| 6 | Is train4 role verified or honestly uncertain? | YES; normal guard / D0 sanity only |
| 7 | Is test1 correctly described as pilot evaluation? | YES |
| 8 | Is test1 backward influence ruled out? | YES for frozen upstream methods; D2 V2 remains prior-INNER-informed |
| 9 | Are attack labels excluded from rule construction? | YES |
| 10 | Is D0 calibration independent from test1 labels? | YES |
| 11 | Does D2 consume predictions rather than labels? | YES |
| 12 | Is prediction-before-label ordering evidenced? | PARTIAL BY ARM: durable for D0/D2; object-level only for D1 |
| 13 | Is test2 untouched? | YES for content; one rejected custody-level filesystem contact is disclosed |
| 14 | Is old OUTER described as result unavailable? | YES |
| 15 | Are leakage findings hidden? | NO |
| 16 | Are unknowns marked rather than guessed? | YES |

## Material findings preserved

- Critical: 0
- High: 2
- Medium: 4
- Low: 2
- Verified leakage: 0
- D1 durable public prediction-file-before-label gate: absent
- D2 V2 independent-confirmation status: absent; it is test1-informed development
- train3 dual use: normal-only and code-path isolated, with scope limitation
- OUTER: one custody access attempt; zero content bytes, labels, predictions, metrics,
  and scientific outcome

## QA feedback resolved

- Updated dashboard tests for the added ARCH-001 generated summary.
- Compared registry-derived task text after correct HTML escaping.
- Reduced `GPT_BRIEF.md` to 1,495 words.
- Corrected the official mismatch count from seven to eight.

## Validation

- RCC unit tests: 47 / 47 PASS
- Registry and generated-output validator: PASS
- Private exposures: 0
- Scientific executions: 0
- Test2 payload reads: 0
- Scientific code changes: 0
- Frozen-result changes: 0
- Remote pushes: 0

Detailed independent evidence is retained in
`bootstrap/ARCH_001/agents/agent_e_qa.json`.
