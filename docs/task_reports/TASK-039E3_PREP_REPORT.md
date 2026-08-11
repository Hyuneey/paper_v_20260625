# TASK-039E3-PREP Report

## Result

Status: `passed_task039e3_scientific_execution_preparation`

This result means only that a deterministic, mock-only construction execution
harness exists and passes synthetic tests. It is not an E3 scientific result,
provider capability result, proposal result, Rule v2 authorization, or runtime
authorization.

## Frozen E2 binding

The harness binds:

- E2 protocol bundle:
  `2295f6e57aff47081419d70e942af02101de33fa545a758ea4a7e6476a46e6e8`;
- provider/endpoint: `openai` /
  `https://api.openai.com/v1/chat/completions`;
- model: `gpt-5.4-2026-03-05`, no fallback;
- reasoning `none`, temperature `0.7`, top-p `1.0`, 1024 completion tokens,
  null seed, stream false, and store false;
- main, T2-follow-up, and direct-number prompt hashes;
- main and direct-number structured schema hashes;
- schedule hash
  `6db63485387924b28e9ce498aae46412a127ba69055a28e72880e1afffa4c4ca`.

## Mock execution machinery

The task-owned provider interface has an in-memory mock implementation with
valid proposal, invalid schema, refusal, 429, 500, timeout, connection, 400,
401, and 403 scenarios. Capability fixtures add exact-snapshot PASS,
unavailable-snapshot BLOCK, and malformed-response BLOCK. No transport code
that can contact a provider and no credential-reading implementation exists.

Requests are deterministically hashed and bind the exact E2 user-visible
prompt, sampling, model, endpoint family, and strict response schema. Arm and
call identity live only in local slot custody. API keys and authorization
headers are excluded from canonical request artifacts and hashes.

Synthetic E1-shaped fixtures contain only fake values, fake hash references,
and `SYNTHETIC_*` identities. The main renderer supplies approved calibrated
values and references. Direct-number rendering withholds exactly source
threshold, source stability tolerance, and target scale values/references,
while preserving the selected horizon and seven D0 window constants.

## Orchestration

- T0: zero provider calls, one deterministic proposal, E0 validity V2, and no
  repair or fallback.
- T1: one call and one deterministic validity decision; no second generation.
- T1-B: exactly three stateless calls with byte-identical initial requests;
  all calls run and the lowest admissible index is selected.
- T2: at most three calls, early acceptance, deterministic revise/retrieve
  control, one same-corpus retrieval maximum, no call four, and fail-closed
  new-evidence rejection.
- Direct-number: one isolated call, three-role strict parsing, frozen
  normalized absolute error, missing/parse/nonfinite and sign/domain metrics,
  and no validity or runtime authority.

Every parsed proposal is wrapped by project code with local arm, call,
configuration, evidence, prompt, and schedule provenance. Model-provided
authority is never accepted. Validity calls the frozen project-owned
`task039e0_validity_v2` implementation with no labels or utility input.

## Custody and metrics

Scientific slot identities depend only on relation schedule index, relation
binding hash, arm, arm-local call number, scientific classification, and the
frozen schedule hash. The 42-relation maximum contains exactly 336 unique
scientific slots; capability probing has a separate non-scientific slot.

Provider call custody is append-only and hash chained. It records slot,
request hash, response presence and metadata, transport attempts, parse
status, proposal-core hash when present, terminal state, and the frozen 2/4
second retry plan without sleeping in mock execution. It stores no API
key, authorization header, raw chain-of-thought, or automatic resume grant.
Failure receipts preserve completed slot hashes and fail the full run without
relation skipping.

Private proposal/validity and per-relation outcome ledgers are prepared.
Aggregate main-arm metrics match E0, with T1-B and T2 additions. Direct-number
metrics remain separate. Public summaries contain hashes, counts, rates,
schedule accounting, and provider/model/config identity; individual proposals
and private rendered evidence remain non-public.

## Synthetic verification coverage

Tests cover deterministic request hashes, credential exclusion, initial
prompt equality, E2 renderer parity, all capability states, strict parsing,
arm-specific refusal/invalid/incomplete `no_rule` handling, eligible retries,
non-retryable 400/401/403, full-run transport exhaustion, append-only ledgers,
T0/T1/T1-B/T2 orchestration, revise/retrieve/nonrepairable/budget outcomes,
same-corpus and
single-retrieval enforcement, direct-number isolation and metrics, 336-slot
accounting, failure custody, public/private sanitization, closed schemas, and
live/credential hard locks.

## Verification

- 41 focused TASK-039E3 synthetic tests pass.
- 114 selected E0/E2/E3 protocol, boundary, schema, and orchestration tests
  pass together.
- Task modules compile, all four task schemas parse, and `pip check` passes.
- Repository-wide discovery ran 1,001 tests with 14 failures, 67 errors, and
  5 skips in frozen or optional areas. The observed blockers include absent
  Torch/PyG, unavailable external ARGOS files, and historical byte-hash or
  frozen-inventory assertions. Those paths were not modified by this task.

## Boundary receipt

| Boundary | Value |
| --- | --- |
| Real E1 private evidence accessed | `false` |
| Provider contacted | `false` |
| API key/credential accessed | `false` |
| Live capability probe executed | `false` |
| LLM called | `false` |
| Real proposal generated | `false` |
| Rule v2 authorized | `false` |
| Runtime authority | `false` |
