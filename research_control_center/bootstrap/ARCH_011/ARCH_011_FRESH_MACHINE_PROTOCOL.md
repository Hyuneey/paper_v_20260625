# ARCH-011 Fresh-Machine Rehearsal Protocol

This protocol is a design only; ARCH-011 did not execute it.

| Stage | Inputs | Expected output | Failure criterion | Private assets? | Scientific execution? |
|---|---|---|---|---|---|
| 1 Clone | exact reviewed release commit | clean checkout and recorded Git/OS/CPU | wrong SHA, dirty tree | No | No |
| 2 Install | public locked core/test profile | resolved package receipt | undeclared/unresolved dependency | No | No |
| 3 Import/static | package, schemas, configs | imports and packaged resource closure | source-tree-only resource failure | No | No |
| 4 RCC tests | RCC public files | validator and RCC unit PASS | stale registry/privacy violation | No | No |
| 5 Synthetic contract | synthetic fixture only | schema/split/authority negative tests PASS | private locator/network required | No | No |
| 6 Synthetic E2E | synthetic candidate/evidence/rule data | candidate -> relation -> rule -> verifier -> runtime -> metric smoke | uncontrolled code/provider/label leakage | No | No |
| 7 Artifact restore | public/sanitized manifest | checksum/identity replay | missing or stale public artifact | No | No |
| 8 Optional science | separately authorized private assets | new VALIDATION V2 receipt | any missing gate or pre-label custody failure | Yes | Yes |

The first rehearsal stops after Stage 7. Run it after final-authority, dependency, schema-resource, and entrypoint remediation, and before any held-out access.

One-command commands such as `python -m paperworks status`, `smoke`, and `verify-artifacts` are `USEFUL`, not required for the thesis if the same staged commands are documented and tested.
