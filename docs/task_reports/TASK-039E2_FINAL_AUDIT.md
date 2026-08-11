# TASK-039E2 Final Audit

## Status

`passed_task039e2_final_audit`

Readiness: `READY_FOR_TASK039E3`

The frozen TASK-039E2 rule-construction execution configuration was
independently reproduced without contacting a provider, inspecting a
credential value, executing the capability probe, opening E1 private
evidence, or generating a real proposal. There are no blocking findings.

Audit artifact hash:
`eef76ee5d30a8fcb47ad706ac3ba39e2247e69568edcb5909572c8fd41587c8d`.

## Lineage and independent oracle

- E2 commit: `3c263277d5b30217058601bd0e12876d2cf58ba4`
- E2 protocol bundle:
  `2295f6e57aff47081419d70e942af02101de33fa545a758ea4a7e6476a46e6e8`
- Audit PREP commit:
  `e5a6f3cd1bc3355142ff3794049f4a4039926d6c`
- Audit PREP merge:
  `136d207a9e12322ea56d20781d8ec4a7654f8764`
- Independent configuration reproduction:
  `c47689c5c0a7c92e87e81c3836321125dc95cb12d388e3eef246ed0d5852c201`

The audit oracle uses the Python standard library only and does not import or
call the production E2 configuration builder. Its 32 preregistered
adversarial tests passed.

## Provider and generation configuration

The audit reproduced exactly:

- provider `openai`;
- API base `https://api.openai.com`;
- endpoint `/v1/chat/completions`;
- endpoint family `chat_completions`;
- model snapshot `gpt-5.4-2026-03-05`;
- snapshot lock with no alias, upgrade, alternative-model, or provider
  fallback;
- reasoning effort `none`;
- temperature `0.7`;
- top-p `1.0`;
- maximum completion tokens `1024`;
- `n = 1`, null seed, no seed-determinism claim;
- zero presence and frequency penalties;
- non-streaming, no storage, no tools, and stateless requests.

The account-specific snapshot remains `not_probed`. Snapshot unavailability
must block TASK-039E3 before a scientific call.

## Prompt, schema, and fairness audit

All three committed prompt hashes were reproduced from canonical Git content:

- main initial:
  `a251e4b9da31c33e72d14dd81da6b2b1d0d1437fdf37ca311330eccce226f1ba`;
- T2 follow-up:
  `a633067a7c9927be158f68ce714236f4c18c09433d49c903dac941a9774eeca5`;
- direct-number:
  `fb01d8990ee3a7affe540dfdf3556b46d7bd744cd1e3a04d6fd9d79772dd2769`.

The independent synthetic reconstruction produced one model-visible
scientific-content hash across T1, T1-B calls 1-3, and T2 call 1:
`cc013b4a93766bfa13b50283da8fde7930bcc54f8940f88bd8091535318b73cc`.
Arm labels, call indices, other-arm outcomes, candidate-method provenance, and
utility results are absent from model-visible input.

The main provider schema is closed and generic. It contains no singleton
source/target answer, selected-horizon answer, expected evidence hash, or
expected numeric-reference constant. Its hash is
`92c628faf78e5ebdcfc3ec2dbeb9daa42b6beff0875cbf226c87c2f2c43cc216`.
It governs syntax only; `task039e0_validity_v2` remains the separate
deterministic semantic verifier. The provider emits only
`ProviderProposalCoreV1`; project code adds arm, call, evidence, budget,
provider, and schedule provenance afterward.

## Arm controls

T1-B requires exactly three independent stateless calls, exposes no prior
proposal or validity result, and selects the lowest admissible call index or
`no_rule`. A fourth call is impossible.

T2 call 1 has the same scientific input as T1/T1-B. Follow-up content is
bounded to the original input, deterministic issue codes and affected fields,
an approved targeted re-presentation, and the previous proposal hash. The
project-owned controller is bound by
`6cc22fea19a636d590cb5e744d896e8f8588946049d2e0743674883c9eae15b4`.
Retrieval is at most one action and is a strict subset of the initially
authorized E1 evidence identities; it introduces no new measurement.

The direct-number comparator withholds both values and references for exactly
the source threshold, source stability tolerance, and target noise scale. It
retains only the approved relation semantics, selected horizon, and seven
preregistered window constants. T0 remains deterministic, provider-free,
search-free, fallback-free, and synthetic-only during E2.

## Schedule, retry, and custody

The schedule contains 42 relations in exact E1 cohort serialization order,
bound by identity-order hash
`debb7eededbe9b0cfd6d178d1f34f1cdfff225b6a59c9f1d8ecb309d4f69568e`.
It freezes 42 T1 calls, 126 fixed T1-B calls, at most 126 T2 calls, and 42
direct-number calls: at most 336 scientific provider calls, with concurrency
one. T0 uses zero provider calls.

One future non-scientific `SYNTHETIC_CAPABILITY_CHECK` is scheduled before
real relation calls. It was not executed by E2 or this audit and may not
change the frozen configuration.

Transport retry is limited to two retries when no model response was obtained
for a preregistered transport failure. Scientific-generation retry is zero.
Malformed output, structured parse failure, provider refusal, verifier
rejection, and low-quality output cannot be relabeled as transport failures.
Retry exhaustion aborts the full run; relation skipping is prohibited.

Provider-response custody permits bounded operational and scientific receipt
metadata. It prohibits API keys, authorization headers, chain-of-thought, and
raw HAI.

## Findings and regressions

Blocking findings: `0`.

Important nonblocking finding: three raw-byte prompt assertions observe CRLF
in the ordinary Windows checkout. Canonical Git blobs reproduce the frozen
hashes, and the full E2 suite passes 85/85 with canonical LF content. This is
an environment-sensitive line-ending diagnostic, not a prompt change.

Regression evidence:

- E2 audit PREP: 32 passed;
- complete E2/E2-PREP/audit suite: 85 passed on canonical Git/LF content;
- E1 and E1 audit: 79 passed;
- E0: 65 passed on canonical LF content;
- D-family: 164 passed, 2 skipped;
- BR-family: 101 passed;
- C-family: 188 passed, 2 skipped, 4 expected missing-external-checkout
  diagnostics;
- HAI provenance: 37 passed;
- TASK-032: 106 passed;
- P1 construction/outcome: 131 passed with 3 expected
  optional-dependency-presence diagnostics;
- exact and existing-environment `pip check`: passed;
- compilation, JSON/schema/self-hash, diff, and public-boundary scans: passed.

There is no unexplained scientific regression.

## Authority boundary

`TASK039E3AuthorizationV1` was created with hash
`85470f2c433bb64c052e635dbb5276fbbd26caa54394a1950317eb3deb7baae3`.
It authorizes future provider execution only after a separate clean E3
execution-code commit and one passing capability probe. It grants no HAI,
train, test, label, attack, detector-utility, Rule v2, Agent-runtime, or
outer/sealed authority. No provider or credential was accessed by this audit.
