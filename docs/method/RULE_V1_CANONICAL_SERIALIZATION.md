# Rule v1 Canonical Serialization

## Policy

Canonical delayed-response documents use the following frozen JSON policy:

| Property | Value |
|---|---|
| Encoding | UTF-8 |
| Key ordering | sorted |
| Item separator | `,` |
| Key separator | `:` |
| ASCII escaping | enabled |
| NaN/Infinity | prohibited |

`delayed_response_rule_to_dict()` emits only TASK-030 schema fields and returns
a new mutable dictionary. `canonical_rule_document_bytes()` produces compact
canonical bytes, and `serialize_delayed_response_rule()` returns their UTF-8
text representation.

## Round Trip

For supported delayed-response documents, parse, serialize, and parse again
preserves every schema-defined field. Semantically meaningful array ordering is
preserved. Unknown fields are not preserved because structural validation
rejects them before model construction.

The parser and serializer do not mutate caller dictionaries, source files, or
typed records.

## Document Hash Boundary

`canonical_rule_document_sha256()` hashes all canonical document bytes. This is
a transport and reproducibility hash only. It is not the document's
`verified_rule_hash`, does not prove verifier acceptance, and grants no runtime
authority.

A future deterministic verifier must define and bind the accepted-rule hash and
verifier-result reference before runtime use.
