# PRE-DG05 Risk Register V1

| ID | Severity | Risk | Why it matters / evidence | Must close before DG-05? | Would alter current V3 executable bytes/authority? | Recommended timing |
|---|---|---|---|---|---|---|
| R01 | `P0 BLOCKER` | Exact V3 user approval absent | V3 manifest/brief say `DG05_V3_USER_REAPPROVAL_REQUIRED`; audit grants none | yes | no scientific change; approval receipt changes execution state | after all technical P0 closure |
| R02 | `P0 BLOCKER` | V3 approval not connected to prediction executor | V3 initializer returns plain preaccess dict; production executor requires typed predecessor manifest; no adapter/orchestrator | yes | yes, executable routing and new hash closure required | immediate pre-DG05 closure task |
| R03 | `P0 BLOCKER` | Scenario interval cardinality mismatch | upstream authority supports one or more intervals; metric bridge requires exactly one; synthetic rehearsal used singleton intervals | yes | yes, metric bridge/contract or explicit authoritative constraint must change | pre-access |
| R04 | `P0 BLOCKER` | Timestamp/coordinate semantics inconsistent | projector preserves duplicates and gaps; metric bridge rejects duplicates and uses row-index delay/ranges | yes | yes | pre-access, before any label lease |
| R05 | `P0 BLOCKER` | Rule runtime census not faithful | production trace omits episode count; builder/oracle default 0; “participating” enumerates loaded descriptors | yes for complete 228-surface claim | yes | pre-access |
| R06 | `P0 BLOCKER` | Result verifier does not independently replay full lineage | verifier reopens primitive/result/contract, not original predictions/scenarios/denominator/projections/traces/normal burden | yes | yes, verifier/orchestration authority | pre-access |
| R07 | `P0 BLOCKER` | Frozen normal-burden numerics are caller supplied | bridge accepts mapping/hash without reopening version/method component authority; primary false-burden result can be self-consistent but unbound | yes | yes | pre-access |
| R08 | `P0 BLOCKER` | Fresh-process custodian not wired to V3 production state | CLI exists; synthetic rehearsal invokes custody path without a committed production V3 launcher/binding | yes | likely yes | pre-access |
| R09 | `P1 MATERIAL` | T0/T2 effective evidence asymmetry obscured by “same-information” label | T0 receipt: structural only; T2: structural+STAT+GLOBAL5 | reporting clarification required; no redesign | documentation may change, science need not | before thesis/results interpretation |
| R10 | `P1 MATERIAL` | Mandatory current-state entry docs are stale | project-state/START_HERE/PROGRAM_STATE can route a session to old decisions | governance update needed before execution | documentation only if carefully scoped | with closure, then re-freeze selectors |
| R11 | `P1 MATERIAL` | Private custody is single-copy | public index states `SINGLE_COPY_LOCAL_ONLY`, second copy false; private contents/restorability not opened in this audit | operational decision needed before irreversible lease/result work | not necessarily | before Phase A/lease |
| R12 | `P1 MATERIAL` | Canonical contract vs validation_v2 ownership unclear | current Formal V4/DG05 runtime bypasses canonical `contracts/runtime_v1.py` | must document exact route; no refactor now | documentation only unless routing changes | closure design review |
| R13 | `P2 MODERATE` | V3 initializer does not rehash its own implementation files | 7/7 hashes match now, but initializer does not enforce them | desirable before approval | yes if enforcement added | closure task |
| R14 | `P2 MODERATE` | Professor package and task indexes are stale | old title, 12-scenario line, reversed custody order, V2 gate | no scientific blocker if not used operationally; submission blocker | documentation only | after P0 closure, before professor review |
| R15 | `P2 MODERATE` | Ancillary public index has one byte-hash mismatch | QA report hash mismatch; 14 of 15 total entries match and one differs | not by itself | index/document bytes would change | later authority-index correction task |
| R16 | `P2 MODERATE` | Historical/current APIs coexist in `dg05_execution_closure_v1.py` | manual resolution may select obsolete result path; prediction primitives are still current | close via explicit orchestrator, not cleanup | likely yes | pre-access routing closure |
| R17 | `P3 COSMETIC` | Append-only handoff sections use repeated “current/next” wording | human confusion | no | documentation only | routine cleanup after gates |

## Priority conclusion

R02–R08 are substantive executable-integrity blockers independent of R01. Approval alone cannot turn the current route into a GO. The safe next action is a separately authorized executable-authority closure that preserves scientific methods and remains entirely pre-access, followed by independent audit and explicit V3 reapproval.
