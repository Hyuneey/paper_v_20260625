# Scenario, Time, and Runtime Binding Decision Brief V1

Status: `USER_DECISION_REQUIRED_BEFORE_DG05_REAPPROVAL`
Scope: prospective production execution only
Access counters: attack/test `0`; label/scenario `0`; provider/credential `0`

The frozen authorities determine primary scenario identity and overlap, but they do not uniquely determine all delay, duplicate/gap, and runtime-participation behavior. This brief consolidates the remaining choices so that one later decision can close them without changing any method, portfolio, detector, Fusion policy, or metric after result access.

## Binding 1 — multi-interval detection delay

Primary hit semantics are already fixed: one official scenario is hit if any alarm overlaps any of its same-file closed intervals, and the scenario counts at most once.

For a hit scenario with disjoint intervals, choose one delay convention:

1. `HIT_INTERVAL_LOCAL_DELAY` (recommended): canonicalize intervals by parsed start, then parsed end, then original ordinal; select the first interval in that order containing an alarm; and subtract that interval's start from the first contained alarm. Delay is elapsed wall-clock seconds, including fractional seconds when present. This does not charge an alarm-free inter-interval gap as detection latency. Version-level median/IQR use only detected scenarios with a defined delay; the result must separately report detected-but-delay-unevaluable and missed counts.
2. `SCENARIO_EARLIEST_START_DELAY`: subtract the earliest interval start from the first in-interval alarm anywhere in the scenario. This measures elapsed time since the scenario first became active, including inactive gaps.
3. `DELAY_NOT_EVALUABLE_FOR_MULTI_INTERVAL`: retain primary hit/recall but report typed `NOT_EVALUABLE` delay for plural-interval scenarios. Such scenarios remain in the primary Recall denominator but not a numeric delay denominator; exact defined/undefined delay denominators must be reported.

The production preflight must not infer this choice from observed intervals or alarms.

## Binding 2 — duplicate timestamps

Choose one prospective policy:

1. `FAIL_FILE_ON_DUPLICATE_TIMESTAMP` (recommended): a duplicate or backward/non-monotone timestamp makes every base method cell for that physical file a typed `METHOD_FAILURE` before label release. Every dependent Fusion cell for the same file also becomes `METHOD_FAILURE`; no row is dropped or merged. The file remains in the complete prediction manifest. Under the already frozen incomplete-coverage policy, a persistent primary-method failure makes that panel/method result `NOT_EVALUABLE_INCOMPLETE_PREDICTION_COVERAGE`; no partial-file Recall denominator is computed.
2. `DUPLICATE_ROWS_SHARE_PHYSICAL_SECOND`: retain every prediction row, define scenario overlap as any row at that timestamp, and deduplicate alarms by physical second for episode/eTaPR coordinates. This requires additional explicit model-window and trace-coordinate rules.

Dropping a row, choosing first/last, or averaging is not authorized.

## Binding 3 — timestamp gaps and row/elapsed-time semantics

Choose one prospective policy:

1. `FAIL_FILE_ON_NON_UNIT_GAP` (recommended): require exact positive one-second increments for methods whose frozen windows/horizons are expressed as seconds but implemented as row offsets. A gap or backward timestamp creates base-method and dependent-Fusion `METHOD_FAILURE` for that file; no interpolation occurs. The terminal receipts and panel-level incomplete-coverage behavior are the same as Binding 2.
2. `SEGMENT_AT_GAPS`: retain the file but reset every detector/rule history and episode at each gap. This requires a versioned segmentation contract and proof that every frozen method's semantics are preserved.

Interpolating or treating non-unit row adjacency as elapsed one second is not authorized.

## Binding 4 — runtime participation vocabulary

Choose one reporting definition:

1. `FOUR_WAY_RUNTIME_IDENTITY_CENSUS` (recommended): report configured Rules, Rules with at least one formed opportunity, Rules with at least one evaluated outcome (`PASS` or `FAIL`), and alarming Rules (`FAIL >= 1`) separately. `ABSTAIN` and `SYSTEM_ERROR` count as formed opportunities but not evaluated outcomes. Deduplicate Rule and physical-source identities within each version/method census; a Rule must retain one immutable source identity. Rule-only and Fusion methods own separate runtime censuses even when they share a Rule portfolio. “Participating” is not used without a qualifier.
2. `PARTICIPATING_EQUALS_FORMED`: retain configured/evaluated/alarming as secondary fields and define the historical unqualified participating count as Rules with at least one formed opportunity.
3. `PARTICIPATING_EQUALS_EVALUATED`: retain configured/formed/alarming as secondary fields and define the historical unqualified count as Rules with at least one PASS/FAIL outcome.

Current aggregate production traces cannot prove per-Rule formed/evaluated membership. Whichever option is approved requires prospective trace enrichment under the same approved input/time policy. The enriched trace must bind file-local Rule alarm rows and derive episodes as maximal row-adjacent runs; it may not silently default a missing episode source to zero.

## Required evidence scope (not a semantic choice)

The current normal-burden authority freezes classes and aggregation policy but does not bind complete method-specific source bundles for all detector-only, Rule-only, and Fusion methods. A separate exact normal-source authority is required if those source predictions/traces were never persisted. Its scope is source-materialization only: no held-out/scientific outcome production, fitting, refitting, recalibration, threshold change, portfolio selection, provider call, or new method policy. It must enumerate the permitted normal files, method-specific alarm bytes, exposure/timestamp authorities, Rule traces where applicable, detector/portfolio/Fusion identities, guard/audit role classification, and permitted outputs. Fusion burden may not be inferred by adding component burdens.

## Recommendation

Approve the four recommended options together and authorize only the narrowly scoped normal-burden source materialization if replay confirms the source artifacts are absent. Approval is not itself proof of executable closure. The required sequence is: decision freeze → authorized source replay/materialization → independent synthetic and source-chain QA → one new exact executable release package → separate DG-05 reapproval. This is the smallest binding set that removes silent row/time transformations, preserves one-scenario-one-hit semantics, and makes missing evidence fail closed.

No approval in this brief authorizes attack/test/label/scenario access. A separate exact DG-05 executable release approval remains mandatory afterward.
