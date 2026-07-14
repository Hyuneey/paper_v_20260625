# Schema Validation Strategy

## Current Validator Audit

`tests/test_task030_method_schemas.py` is a fixture-focused local validator. It
supports local `#/...` references (including `$defs` reached through such
references), `anyOf`, type unions, `required`, `additionalProperties`, `enum`,
`const`, `pattern`, limited `date`/`date-time` formats, numeric bounds including
`exclusiveMinimum`, and `uniqueItems` through canonical JSON comparison.

It is not a complete Draft 2020-12 implementation. It does not provide general
URI or anchor resolution, `$dynamicRef`, complete `format` behavior,
`oneOf`/`allOf`/`not`, conditional or dependent schemas,
`unevaluatedProperties`, `contains` semantics, meta-schema validation, or the
full standard's numeric and Unicode edge behavior. It must remain a synthetic
contract-test helper.

## DEC-035 Recommendation

Use `jsonschema.validators.Draft202012Validator` from `python-jsonschema` for
production structural validation. Keep project-owned deterministic checks for:

- cross-artifact references and hash/status consistency;
- unit and graph endpoint compatibility;
- split and calibration provenance;
- relation-family compatibility;
- claim-boundary and verifier policy.

`jsonschema` is not declared in `pyproject.toml`, whose runtime dependencies are
currently only pinned PyTorch and PyG packages. No dependency is installed or
changed by TASK-031. Dependency approval and version pinning are deferred to
TASK-032A.
