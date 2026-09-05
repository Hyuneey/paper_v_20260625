# MULTIPANEL-DG05-EXEC-001 independent pre-access QA

Verdict: `BLOCKED_DG05_AUTHORITY_REPLAY`

Three independent read-only audits reviewed authority/custody, prediction
lineage, and metric/lease readiness before any attack/test payload access.

## Replayed successfully

- integration base, branch, and origin parity;
- all required public authority self-hashes and all frozen portfolio hashes;
- 10-file physical census and exact 72-cell method census;
- positive feature allowlists: HAI23 37, HAI22 24, HAI21 22;
- synthetic custody, lease-ordering, mutation-detection, Wilson, paired-table,
  McNemar, delay, false-burden, and eTaPR arithmetic tests.

## Material execution gaps

- exact preregistration identity is caller-selected rather than constant-bound;
- result receipts do not replay result-authority bytes;
- scenario/denominator/result authority materialization is absent;
- the frozen P1-only mapping cannot distinguish a verified non-P1 identity
  from an unresolved identity;
- scenario coordinates are not bound to prediction/scenario artifacts;
- custodian process isolation is not technically enforced;
- the production feature-only projection and 72-cell prediction runner does
  not exist;
- PCA and Isolation Forest currently share a panel-level umbrella detector
  hash; a future runner must additionally bind exact method-specific fit and
  threshold subauthorities.

Because the approved artifacts must not be rewritten after DG-05 approval,
the audit stopped before raw attack/test payload acquisition. No label lease
was issued or consumed.

Safety counters: attack/test payload access `0`; label/scenario access `0`;
prediction writes `0`; provider calls `0`; GDN training `0`; private exposure
`0`; frozen result changes `0`.
