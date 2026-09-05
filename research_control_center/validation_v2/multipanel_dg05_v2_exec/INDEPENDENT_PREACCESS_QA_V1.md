# DG-05 Executable V2 Independent Pre-Access QA

Date: 2026-09-05 (Asia/Seoul)

Verdict: `BLOCKED_DG05_V2_EXECUTABLE_AUTHORITY_REPLAY`

Three independent read-only audits replayed the approved authorities and the
HAI23, HAI22, and HAI21 public lineage. No audit opened attack/test payloads or
label/scenario values and no audit wrote scientific artifacts.

## Replay results

- exact integration base: PASS
- approved authority hashes: PASS
- frozen portfolio and detector lineage: PASS
- expected prediction-cell derivation: PASS (`9 + 28 + 35 = 72`)
- focused synthetic closure tests: PASS (`45 / 45`)
- attack/test payload access: `0`
- label/scenario access: `0`

## Functional authority failure

The exact approved result builder and independent verifier are narrower than
the frozen metric authority and the reapproved task. They cannot produce and
independently replay all required eTaPR values, delay summaries, full paired
contrasts and McNemar results, Rule/Fusion recovery, Rule runtime census, and
normal-burden payloads. The verifier cannot reopen Rule trace artifacts.

This is a pre-access executable-authority defect, not an attack result. Phase A
must remain unstarted. Extending the builder or verifier requires new hashes,
a new executable closure, and new exact approval before attack/test custody.

## Independent QA conclusion

The correct safe disposition is to preserve all frozen authorities, record the
unexercised V2 approval, and stop before Phase A. No partial execution, lease,
prediction, result, or private-data exposure occurred.
