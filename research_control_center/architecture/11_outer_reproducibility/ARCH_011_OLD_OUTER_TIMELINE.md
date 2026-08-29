# ARCH-011 OUTER Custody Audit

## Intended role

The old study was a one-shot confirmatory HAI 23.05 P1 test2 evaluation of frozen D0, COMMON-42 D1, and D2 V1. It prohibited fitting, recalibration, rule selection, policy change, D2 V2, retry, and post-result redesign.

## Exact stop point

The state reached `OUTER_SCIENTIFIC_ATTEMPT_STARTED`. The first test2 feature custody predicate then emitted `OUTER_TEST2_FEATURE_CUSTODY_REJECTED` before file open/read and before `TEST2_FEATURE_HASH_VALIDATED`.

| Counter | Frozen historical value |
|---|---:|
| scientific attempts | 1 |
| retries | 0 |
| feature custody checks | 1 |
| feature byte reads | 0 |
| feature hashes | 0 |
| feature semantic parses | 0 |
| label accesses / parses | 0 |
| D0/D1/D2 executions | 0 |
| frozen predictions | 0 |
| metrics / outcomes | 0 |

The public blocker does not distinguish symlink from another non-regular-file condition. No more specific local cause is inferred.

## Interpretation

- Result: `UNAVAILABLE`.
- Generalization: `UNCONFIRMED`.
- Negative held-out performance: not observed.
- Old protocol: `NOT_RETRYABLE_BY_PROTOCOL`.
- Same physical test2 reuse: `STUDY_DESIGN_REQUIRED`; content sealing alone neither authorizes nor forbids a genuinely new study.
