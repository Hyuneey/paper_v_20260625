# TASK-039D1 Final Audit

Status: `passed_task039d1_final_audit`
Readiness: `READY_FOR_TASK039D2`

The independent train1/train2 replay reproduced the D1 fit-supported normal
delayed-response relation candidates. It does not establish confirmation,
causality, method superiority, rule validity, or anomaly performance.

## Independent replay

- Source records: `12` (`12` supported, `0` unsupported).
- Target records: `12`.
- Directional results: `45` fit-supported, `17` direction-unstable, `32` fit-unsupported.
- Pair results: `25` fit-supported, `22` unsupported.
- Pair-summary hash reproduced: `a466057faa20eacd0692b6a9c19fbbb5b8968135ba4c018310a076aa0393d4f2`.
- Original private ledger hashes and all normalized records reproduced exactly.
- Provenance was loaded only after private replay ledgers and pair outcomes were frozen.

## Fit-only arm summaries

- META: `16/20`, yield `0.80`, `29` directions.
- STAT: `17/20`, yield `0.85`, `33` directions.
- GDN: `5/20`, yield `0.25`, `7` directions.
- Shared-pair invariance: `true`; winner selected: `false`.

## Boundaries and authorization

- Train1/train2 accessed by audit: `true` / `true`.
- Train3/train4/test/labels/attacks accessed: `false`.
- BR2 pair outcomes accessed: `false`.
- Rule v2 authorized: `false`.
- D2 executed: `false`.
- D2 authorization hash: `791f985afdc5f16b5c6b5aec4eb7bcefe1e39bc3b0f262cc0ff56c7ff5071f25`.
- A separate clean D2 execution-code commit is required before train3 access.

## Regression audit

- Audit/D1R/D1: `52` passing tests.
- D0, C0, META, STAT, and three-arm integration: `145` passing tests
  (`1` expected skip).
- BR1/BR2, HAI provenance, TASK-032, candidate, and relation suites: `255`
  passing tests.
- Exact GDN environment: `87` passing tests and `1` expected skip; the four
  diagnostics require the intentionally absent external GDN checkout or the
  historical GDNC execution branch.
- Minimal guarded discovery: `645` runnable tests, `53` classified optional
  imports, `9` expected missing-external/dependency diagnostics, and `1`
  historical inventory mismatch caused by additive audit files.
- Exact-environment guarded discovery: `967` runnable tests, `16` classified
  optional pytest imports, and only the corresponding external-checkout,
  historical-branch, optional-import-order, and additive-inventory diagnostics.
- Python compilation, `242` public JSON documents, `118` v6 schemas, `110`
  registered schemas, public/private self-hashes, both `pip check` runs,
  diff checks, and public boundary scans passed.

No unexplained scientific regression was found.
