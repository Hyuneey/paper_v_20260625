# TASK-039E3-R2R-UTILITY-INNER-D2-V2-R5-EXECUTION-ACCOUNTING-SCHEMA-PARSER-REMEDIATION-R2

## Scope

Repair only the public execution-accounting producer-schema parser used after
the completed R5 scientific oracle. Recover the exact frozen producer schema
with Python AST structure, validate every required accounting semantic in one
pass, and fail closed unless the committed R5 blocker evidence supports the
entire completion snapshot.

## Hard boundaries

- No D0, D1, D2 V1, or D2 V2 execution.
- No scientific-oracle recomputation or scientific artifact reparse.
- No label, test1 feature, test2, or OUTER access.
- No frozen accounting, result, private evidence, authorization, policy, or
  native-horizon modification.
- No regular-expression, line-based, quoted-key, fuzzy-name, or hash-guided
  producer-schema extraction.
- No push.

## Authorized reads

The one real invocation may read only the frozen producer/type source, the
public accounting JSON once, committed R5 and R1 blocker evidence, public
custody compatibility metadata, and tracked public files needed for
non-scientific completion checks.

## Completion rule

Final completion requires exact accounting semantics, a complete committed R5
scientific-oracle snapshot, custody compatibility, result-freeze immutability,
public leakage and report-schema checks, zero prohibited access, and zero
accepted invalid cases. Missing committed evidence is a blocker; values in the
task specification are not substituted for committed authority.
