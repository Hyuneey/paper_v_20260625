# ARCH-008 Independent QA Report

Final verdict: **PASS** after four pre-PASS corrections. All 20 required questions are satisfactory.

| # | Question | Answer |
|---:|---|---|
| 1 | D1 object correctly identified? | YES — COMMON-42 V4 fixed Rule-only prediction |
| 2 | COMMON-42 terminology correct? | YES — Verified Relational Rule-only |
| 3 | 13/14 semantics verified? | YES — operational event overlap Recall; not point Recall or statistical independence |
| 4 | FAR/hour semantics verified? | YES — normal false episodes per normal labeled hour |
| 5 | Rule records / seconds / episodes separated? | YES — 788 / 630 / 626 |
| 6 | Normal false episodes verified? | YES — 574 |
| 7 | D0/D1 overlap verified? | YES — four-cell frozen table |
| 8 | D1-only=3 verified? | YES |
| 9 | D0-only=1 verified? | YES |
| 10 | Union interpretation conservative? | YES — only direct `neither=0` wording retained |
| 11 | Pilot versus general complementarity separated? | YES |
| 12 | Rule-only utility remains unvalidated? | YES |
| 13 | D1 not called Agentic Rule-only? | YES |
| 14 | Direct LLM Rule-only language qualified? | YES — not directly tested |
| 15 | test1 remains pilot? | YES |
| 16 | Durable-freeze limitation visible? | YES |
| 17 | No new metrics/statistical tests? | YES |
| 18 | High-FAR cause not invented? | YES — CAUSE_NOT_YET_ANALYZED |
| 19 | Held-out generalization unconfirmed? | YES |
| 20 | Zero scientific computation? | YES |

The QA reviewer also confirmed that D1 integrity and later comparison integrity are not conflated: the former has an explicit result-integrity audit; the latter is frozen, self-hashed and evidence-reviewed without a separately identified result-integrity audit.

Final mechanical validation: registry PASS; dashboard and summaries refresh PASS; RCC tests 86/86 PASS; privacy PASS. All scientific, test1, test2, source-change, frozen-result-change and exposure counters remained zero.
