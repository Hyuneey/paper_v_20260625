# Official HAI scenario-authority recovery audit V2

Status: `BLOCKED`

Verdict: `OFFICIAL_SCENARIO_AUTHORITY_INCOMPLETE`

This audit exhaustively searched the bounded, value-blind official evidence available for HAI 23.05, HAI 22.04, and HAI 21.03. It preserves the historical V1 blocker and does not implement an adapter. Official sources establish nominal attack counts, source identities, and portions of the attack-design semantics. They do not establish a complete deterministic occurrence-to-file/interval/identity construction contract for any of the three versions.

## Audit boundary

- Official HAI Git history: all 87 reachable commits in the non-shallow pinned repository, all observed branch/tag refs, deleted and renamed paths, commit messages, scripts, notebooks, and README history.
- Official/institutional materials: HAI GitHub documentation, DataON, official Kaggle metadata, HAICon/DACON pages, author papers and slides, and author-maintained eTaPR/TaPR code.
- No real held-out row, label value, scenario record, or attack interval was opened.
- Public examples and third-party code were not promoted to authority.
- Inaccessible dynamic baseline notebook bodies remain an explicit search limitation, not evidence of absence.

## Sufficiency rule

A version is `AUTHORITY_COMPLETE` only when official value-blind evidence deterministically binds scenario identity, physical file, interval extraction, plural-interval ownership, attacked identities, affected-process semantics or official unavailability, nominal census, canonical ordering, and duplicate/error behavior. Counts alone and generic contiguous-label segmentation are insufficient.

## HAI 23.05

Source class: `OFFICIAL_SEPARATE_SCENARIO_METADATA` (candidate source exists; executable grammar unresolved).

| Needed claim | Exact official evidence | What it establishes | What remains unresolved |
|---|---|---|---|
| Nominal census | Pinned README at commit `2a814ceb`; README blob `de19cf9`; introduction commit `ebcd09bb` | `hai-test2` has published Attack Count 38 | Whether 38 indexes summary records, occurrence IDs, scenario types, or label runs |
| Source identity | `label-test2.csv` pointer blob `5bbca74a`; `summary_label2.txt` pointer blob `ef02d541`; both introduced by `ebcd09bb` | Two version-bound official source identities exist | Summary schema, join key, precedence, and null behavior |
| Scenario generation | Complete reachable-history filename and content search | No generator/parser was found in the 87 reachable commits | Official occurrence-ID and grouping algorithm |
| Interval construction | README timestamp/label description; author-maintained eTaPR `load_stream_2_range` | Dataset timestamp/label concepts and generic metric range conversion | HAI23 endpoint convention, timezone, overlap, interrupted/repeated ownership, and summary/label reconciliation |
| Targets/processes | README states controller/point targets replace process labels from HAI22 | Target roles exist conceptually | Target serialization, direct-versus-affected semantics, and official process mapping |

Authority status: `PARTIAL`.

The author-maintained eTaPR function assigns ordinal names to contiguous binary-label ranges. It does not consume `summary_label2.txt`, bind HAI23 physical files, recover official identities, group plural intervals, or map targets/processes. It is therefore not a substitute scenario authority.

## HAI 22.04

Source class: `OFFICIAL_SEPARATE_SCENARIO_METADATA` (four exact summaries plus an official attack-description table; executable grammar unresolved).

| Needed claim | Exact official evidence | What it establishes | What remains unresolved |
|---|---|---|---|
| Nominal census | Pinned README; DataON DOI `10.22711/idr/977`; HAI22 release manual | test1/test2/test3/test4 counts are 7/17/10/24 = 58; 58 includes single and combined situations | Executable summary-record reconciliation |
| Source/file identity | Exact official summary blobs `5f5045e2`, `bc860102`, `5a4c8f1f`, `a72af258`, introduced at `4700346e` | Each summary pathname corresponds to test1–test4 and remains byte-identical in pinned history | Formal grammar connecting a summary record to a manual ID |
| Scenario unit | HAI22 technical manual structural table: No, ID, Start Time, Attack Scenario, Target Controller, Target Point(s), Duration | One numbered table row is one listed scenario; a simultaneous two-primitive combination is one row | Summary delimiter/encoding, stable record join, duplicate/conflict policy |
| Interval construction | Manual structural fields | Start and duration are official concepts | Closed-end arithmetic, timezone/cross-midnight behavior, and plural-interval ownership |
| Targets/processes | Manual target-controller/target-point columns; README label-policy change | Typed target roles are official | Canonical target parsing, escaping/multiplicity, affected-process semantics, and conflict precedence |

Authority status: `PARTIAL`.

The exact summary objects were identified but not opened. HAICon/eTaPR code establishes scoring interfaces and generic ranges, not the official HAI22 summary transformation. DataON contains a conflicting prose split statement, so the explicit file inventory and pinned README—not that sentence—remain the trustworthy count/file authority.

## HAI 21.03

Source class: `OFFICIAL_TEST_CONTAINER_LABEL_DERIVATION_AUTHORITY` (documented labels exist; official label-to-occurrence rule unresolved).

| Needed claim | Exact official evidence | What it establishes | What remains unresolved |
|---|---|---|---|
| Nominal census | Pinned README; author presentation | test1–test5 contain 5/20/8/5/12 = 50; design contains 25 single and 25 combined attacks | Stable 50-occurrence IDs and joins |
| Attack provenance | Author paper §3.3 | Automation stored attack target/time metadata for labeling; targets may be sequential or parallel | Public occurrence export and canonical grouping |
| Attack templates | Author paper Appendix A, AP01–AP27 | Template-level controller, variable, point, and edition applicability | Which templates/targets compose each of the 50 file/time-bound occurrences |
| Labels/processes | README data fields and P1–P4 definitions | Global and process-specific labels exist | Direct attacked point/process attribution and propagated-effect semantics |
| Event conversion | Author-maintained eTaPR `load_stream_2_range` | Generic contiguous range conversion for metric input | Proof that a contiguous range equals one official HAI21 scenario; repeated interventions make that unsafe |
| Competition crosswalk | Author paper §4.1.1 | HAICon2020 used five validation attacks and 45 test attacks with deidentified/shuffled columns | Released-dataset occurrence/file/identity crosswalk |

Authority status: `PARTIAL`.

The HAI21 paper is the strongest design provenance: it explains the 25+25 design, stored metadata, combined attacks, and repeated interventions. It does not expose the 50-occurrence metadata needed to reproduce file assignment, intervals, membership, targets, and process attribution.

## Cross-version conclusion

No transformation rule was borrowed across versions. No scenario was inferred from record values. The only shared official claims are broad dataset field conventions and nominal counts. Each version lacks a complete occurrence-level grammar, and the missing pieces differ.

The frozen P1 denominator cannot be executed from these value-blind authorities because none supplies a complete occurrence-to-attacked-identity/process binding. Empty attacked identities cannot be declared an official “not provided” semantic without a source stating that semantic; doing so would undermine P1 eligibility.

No `HAI_OFFICIAL_SCENARIO_SOURCE_AUTHORITY_V2` was created. The JSON companion to this report is the new recovery-audit authority, not a production construction authority.

## Recovered-source locators

- Official pinned repository README: https://github.com/icsdataset/hai/blob/2a814cebc9a66b06c9e5cd545e2d72e65d383737/README.md
- HAI22 official DataON record: https://doi.org/10.22711/idr/977
- HAI dataset/challenge author paper: https://cset21.isi.edu/papers/cset21-1.pdf
- Author presentation: https://cset21.isi.edu/cset21-1-pres.pdf
- Author-maintained eTaPR source: https://github.com/wshw4ng/eTaPR/blob/main/eTaPR_pkg/DataManage/File_IO.py
- HAICon2020 official page: https://dacon.io/competitions/official/235624/overview/description
- HAICon2021 official page: https://dacon.io/en/competitions/official/235757/overview/description

## Safety counters

`real_heldout_rows_parsed=0`, `real_label_values_parsed=0`, `real_scenario_records_accessed=0`, `real_attack_intervals_observed=0`, `predictions_executed=0`, `metrics_computed=0`, `provider_calls=0`, `credential_reads=0`, `private_exposures=0`.

No scientific authority changed. No adapter, V11 release, held-out execution, prediction, denominator, or metric was produced.
