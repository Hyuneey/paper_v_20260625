# ARCH-011 Independent QA Report

## Verdict

`PASS`

ARCH-011 accurately maps the unavailable old OUTER result, the consumed one-shot
attempt, current reproduction levels, public/private portability boundaries, and
the prospective PILOT V1 / VALIDATION V2 separation. It does not claim scientific
execution, test2 content access, remediation, or fresh-machine rehearsal.

## Required QA Questions

| # | Question | Verdict | Evidence-based answer |
|---:|---|---|---|
| 1 | Is old OUTER role correct? | PASS | It was the one-shot confirmatory HAI 23.05 P1 test2 evaluation of frozen D0, COMMON-42 D1, and D2 V1. |
| 2 | Is exact stop point evidenced? | PASS | The attempt reached `OUTER_SCIENTIFIC_ATTEMPT_STARTED`, then stopped at `OUTER_TEST2_FEATURE_CUSTODY_REJECTED` before file open/read. |
| 3 | Are feature-byte accesses correctly represented? | PASS | Historical custody/file check: 1; feature byte reads, hashes, and semantic parses: 0. |
| 4 | Are label accesses correctly represented? | PASS | Label file accesses, hashes, and semantic parses: 0. |
| 5 | Is result-unavailable wording correct? | PASS | No predictions, metrics, or outcomes exist. The report uses `UNAVAILABLE` and `UNCONFIRMED`, not negative performance. |
| 6 | Is retryability correctly classified? | PASS | The sole authorized attempt was consumed, retries were 0, and attempts remaining were 0: `NOT_RETRYABLE_BY_PROTOCOL`. |
| 7 | Are reproduction levels separated? | PASS | Traceability, same-machine replay, fresh-machine synthetic, fresh-machine scientific, and independent external reproduction are separately classified. |
| 8 | Is same-machine status accurate? | PASS | Narrow frozen-artifact integrity replay is supported; full PILOT scientific recomputation is neither authorized nor demonstrated. |
| 9 | Is fresh-machine status accurate? | PASS | Synthetic reproduction is partially prepared but unexecuted; scientific reproduction is unproven and blocked by private assets and incomplete environment closure. |
| 10 | Are private assets identified safely? | PASS | Raw HAI/test2, private numeric/model authorities, local registries, and locators are named by class only; no private value or locator is exposed. Public-safe frozen predictions are correctly distinguished from private scientific inputs. |
| 11 | Are environment dependencies mapped? | PASS | Python/jsonschema, undeclared NumPy/test tooling, optional GDN dependencies, Git, schema-layout, numerical backend, and private custody dependencies are mapped. |
| 12 | Are hidden paths identified? | PASS | Source-tree schema lookup, environment bindings, Git checkout assumptions, exact Windows GDN contract, legacy host-path provenance, and Windows launcher assumptions are recorded without locator disclosure. |
| 13 | Is PILOT V1 preservation explicit? | PASS | V1 remains immutable, historically qualified, and is not rewritten or rerun. |
| 14 | Is VALIDATION V2 separation explicit? | PASS | V2 requires new method, config, authority, environment, prediction, and study identities. |
| 15 | Are authority options compared fairly? | PASS | RuleV1 end-to-end, formal V4, and a verified canonical-to-V4 bridge are compared across scope, clarity, preservation, runtime compatibility, testing, portability, and bug risk. The bridge is recommended prospectively, not pre-approved. |
| 16 | Is fresh-machine protocol non-scientific by default? | PASS | Stages 1-7 use public/synthetic inputs and stop before optional separately authorized scientific Stage 8. |
| 17 | Is release scope privacy-safe? | PASS | Public source/contracts/tests/synthetic artifacts and sanitized reports are included; raw data, test2, credentials, private authorities, locators, and restricted provider payloads are excluded. |
| 18 | Are GAP priorities updated only with evidence? | PASS | No priority, blocker, or pilot-validity change was made. Findings refine existing GAP-011/012/013 portability work. |
| 19 | Did audit access zero test2 scientific content? | PASS | ARCH-011 performed zero test2 file, byte, hash, semantic, or label access. Historical custody counters are reported separately. |
| 20 | Did audit perform zero scientific execution? | PASS | No science, fresh environment, dependency installation, remediation, prediction, metric, or provider execution occurred. |

## GAP-000 Label Normalization

PASS. Current-facing GAP output now separates:

- primary disposition, including `P0_FIX_BEFORE_EXPANDED_VALIDATION` and
  `P1_FIX_BEFORE_SPECIFIC_EXPERIMENT`; and
- urgency priority `P0` through `P3`.

No underlying triage classification was changed.

## Corrections Resolved During QA

1. The artifact portability matrix now identifies tracked D0/D1/D2 prediction
   artifacts as `PUBLIC_FROZEN` / public-safe and keeps raw data and private
   restoration authorities separate.
2. Current-facing ARCH-010 and GAP-000 user summaries no longer present ARCH-011
   as a future step; the conditional Graph-Guided/Agentic policy is recorded as
   already approved.
3. The RCC registry test now expects the eight ARCH-011 review entries required
   by the current state contract.

## Validation

- Authority gate: exact RCC branch/HEAD and scientific authority verified.
- JSON/CSV parse checks: PASS.
- RCC registry validator: PASS.
- RCC unit tests: 106/106 PASS.
- Privacy scan: PASS, zero new exposures.
- Scientific source and frozen scientific artifact diff: zero.

## Safety

- scientific executions: 0
- test2 content accesses: 0
- dependency installations: 0
- fresh-machine runs: 0
- remediation implementations: 0
- scientific source changes: 0
- frozen scientific artifact changes: 0
- remote pushes: 0

