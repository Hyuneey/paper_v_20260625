TASK-039E3-R2R-UTILITY-INNER-D2-DESIGN-AND-FREEZE-V1

CODEX EXECUTION MODE:
LOCAL STATIC DESIGN / PREREGISTRATION ONLY

OPTIONAL READ-ONLY AUDIT AGENTS ALLOWED.

NO D0 EXECUTION.
NO D1 EXECUTION.
NO D0 PREDICTION CONTENT READ.
NO D1 PREDICTION CONTENT READ.
NO TEST1 ACCESS.
NO LABEL ACCESS.
NO TEST2 ACCESS.
NO D2 EXECUTION.
NO METRIC COMPUTATION.
NO PUSH.

====================================================================
0. PURPOSE
====================================================================

Design, preregister, independently audit, and freeze the primary D2
Detector+Rule combined alarm policy.

D0 and D1 real INNER results now both exist and are integrity-audited.

However D2 MUST NOT be tuned to their observed metric values or alarm
locations.

This task is DESIGN-AND-FREEZE ONLY.

Do NOT execute D2.

Do NOT open D0 prediction records.

Do NOT open D1 prediction records.

Do NOT inspect test1 values or labels.

The design may bind only the immutable artifact identities and their frozen
schemas/authorities.

Primary D2 scientific question:

Can verified rule corroboration recover detector-missed anomaly events while
adding substantially less false-alarm burden than unrestricted Rule-only
alarming?

====================================================================
1. REPOSITORY / LOCAL BASE
====================================================================

Repository:

Hyuneey/paper_v_20260625

Remote state:

LOCAL_ONLY_NOT_PUSHED

DO NOT PUSH.

Create branch locally:

task-039e3-r2r-utility-inner-d2-design-and-freeze-v1

from exactly:

1c2f9a6272ee711b70b44ed79b9210af1026d3af

Require:

- exact local HEAD
- clean worktree
- clean index
- no rebase
- no merge
- all D0 local commits resolvable
- NO PUSH
- NO remote branch creation

====================================================================
2. CONTINUITY FIRST
====================================================================

Read exactly:

1. AGENTS.md
2. docs/project_state/START_HERE.md
3. docs/project_state/CURRENT_STATE.json
4. docs/project_state/HANDOFF.md
5. docs/project_state/RESEARCH_SCOPE.md
6. docs/project_state/AUTHORITY_INDEX.md
7. docs/project_state/DECISION_LOG.md
8. docs/project_state/SAFETY_BOUNDARIES.md
9. D1 result-integrity authorities
10. D0 result-integrity authorities
11. D0 report-hash remediation authorities
12. this task

Validate CURRENT_STATE self-hash.

====================================================================
3. FROZEN INPUT ARTIFACTS
====================================================================

D0 DetectorPrediction:

a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6

D1 RulePrediction:

58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682

Future D2 MUST consume these exact immutable artifacts.

D0 MUST NOT be rerun.

D1 MUST NOT be rerun.

D2 design must reject any replacement/reconstructed prediction artifact.

====================================================================
4. INPUT CONTENT MUST NOT BE READ DURING DESIGN
====================================================================

This task may inspect:

- artifact schemas;
- artifact hashes;
- public authority definitions;
- COMMON-42 relation schema;
- D0/D1 prediction type definitions.

This task MUST NOT inspect:

- D0 alarm timestamps;
- D1 alarm timestamps;
- D0 alarm count;
- D1 alarm count;
- D0 metric values;
- D1 metric values;
- D0 missed events;
- D1 missed events;
- test1 labels.

Machine-readable design declaration:

d0_prediction_content_read_for_design = false

d1_prediction_content_read_for_design = false

d0_metric_artifact_read_for_design = false

d1_metric_artifact_read_for_design = false

test1_read_for_design = false

label_read_for_design = false

====================================================================
5. PRIMARY D2 IDENTITY
====================================================================

Freeze:

D2_ID:

D2_D0_PLUS_VERIFIED_RULE_CORROBORATION_V1

D2_ROLE:

PRIMARY_COMBINED_DETECTOR_RULE_ARM

D2_FUSION_FAMILY:

DETECTOR_PRESERVING_MULTI_SOURCE_RULE_CORROBORATION

Scientific LLM at runtime:

false

Trainable fusion:

false

Label-aware fusion:

false

Score weighting:

false

====================================================================
6. SCIENTIFIC PRINCIPLE
====================================================================

D0 remains the primary anomaly detector.

D1 verified rules are NOT allowed to replace or suppress D0.

Rules may contribute a recovery alarm only when they provide non-singleton
cross-variable corroboration.

Freeze principle:

1. preserve every D0 alarm;
2. a single Rule-only alarm cannot create a D2 recovery alarm;
3. Rule recovery requires concurrent violations from at least two distinct
   source variables;
4. no labels participate in fusion;
5. no detector score tuning participates in fusion;
6. no temporal tolerance/window is introduced.

====================================================================
7. EXACT POINTWISE D2 FUSION
====================================================================

For each physical test1 second t:

D0_alarm(t) =
the exact alarm boolean from frozen D0 DetectorPrediction.

Let:

A_t =
all frozen D1 RulePrediction records satisfying:

decision_physical_row_index == t
AND
alarm_emitted == true

Resolve each alarming D1 record to its exact frozen COMMON-42 source variable.

Let:

S_t =
set of DISTINCT source variables among A_t.

Define:

rule_corroboration(t) =
|S_t| >= 2

Define:

rule_recovery(t) =
NOT D0_alarm(t)
AND rule_corroboration(t)

Define final:

D2_alarm(t) =
D0_alarm(t)
OR rule_recovery(t)

Equivalent:

D2_alarm(t) =
D0_alarm(t)
OR (|S_t| >= 2)

because recovery classification is descriptive and D0 alarms are always
preserved.

====================================================================
8. WHY CORROBORATION COUNT = 2
====================================================================

Freeze rationale:

2 is NOT a performance-tuned threshold.

It is the minimum cardinality that distinguishes:

single-rule evidence

from:

multi-source corroborated physical evidence.

Do NOT evaluate or search:

1
2
3
4
...

No consensus sweep.

No D0/D1 metric-driven selection.

No later INNER tuning.

====================================================================
9. DISTINCT-SOURCE RULE
====================================================================

Multiple alarming rules sharing the same source variable count as:

ONE source.

Example conceptual rule:

source A → target B alarm
source A → target C alarm

counts as:

1 distinct source

not 2.

Require at least:

2 distinct source-variable identities.

This reduces duplicate evidence from one initiating signal without introducing
a learned or numeric parameter.

====================================================================
10. SOURCE RESOLUTION
====================================================================

Resolve D1 prediction opportunity/rule identity to the exact frozen COMMON-42
directed relation authority.

Do NOT infer source variable from string conventions if an authoritative
mapping exists.

Require deterministic mapping:

D1 prediction identity
→ frozen relation identity
→ source variable identity

If exact source identity cannot be unambiguously resolved from existing frozen
authorities:

BLOCK:

D2_DESIGN_BLOCKED_D1_SOURCE_RESOLUTION_UNAVAILABLE

Do not redesign fusion automatically.

====================================================================
11. SAME-SECOND CORROBORATION
====================================================================

Corroboration is allowed only at the exact same:

decision_physical_row_index

No ±1 second.

No lag tolerance.

No rolling window.

No dilation.

No event expansion.

This deliberately avoids a new temporal hyperparameter.

====================================================================
12. D0 PRESERVATION
====================================================================

D2 may NEVER suppress a D0 alarm.

Require:

if D0_alarm(t) == true:

D2_alarm(t) == true

No false-positive correction in primary D2.

No AND gating.

No rule veto.

No detector suppression.

====================================================================
13. RULE RECOVERY ONLY
====================================================================

Rules contribute only in the positive recovery direction.

Primary scientific correction direction:

DETECTOR_FALSE_NEGATIVE_RECOVERY

Do NOT implement primary D0 false-positive removal.

Existing project policy already treats FP correction as supplementary.

D2 V1 focuses on detector-miss recovery.

====================================================================
14. NO D0 SCORE ACCESS
====================================================================

D2 fusion must use only the frozen D0 alarm boolean.

Do NOT use:

- raw SPE;
- score evidence;
- distance from threshold;
- confidence band;
- secondary detector threshold.

This prevents post-result detector-score tuning.

====================================================================
15. NO RULE NUMERIC RE-EVALUATION
====================================================================

D2 consumes frozen D1 RulePrediction only.

Do NOT:

- rerun rules;
- reopen numeric rule registries for evaluation;
- alter rule thresholds;
- recalculate rule outcomes.

The exact D1 prediction is the scientific authority.

====================================================================
16. D2 PREDICTION ARTIFACT DESIGN
====================================================================

Define future:

ScientificCombinedPredictionArtifactV1

Exactly one record per physical second:

0 ... 53999

Each record may contain:

physical_row_index

d2_alarm_emitted

trigger_class

optional provenance identity refs

Allowed trigger_class:

NONE
D0_ONLY
RULE_RECOVERY
D0_AND_RULE_CORROBORATION

Optional sanitized rule provenance may contain:

- frozen relation IDs;
- source variable IDs;

but no raw numeric values.

====================================================================
17. TRIGGER CLASS SEMANTICS
====================================================================

For each t:

if not D0 and not corroborated:
NONE

if D0 and not corroborated:
D0_ONLY

if not D0 and corroborated:
RULE_RECOVERY

if D0 and corroborated:
D0_AND_RULE_CORROBORATION

Trigger class must NOT affect final alarm semantics beyond the fixed policy.

====================================================================
18. LABEL-BLIND FUSION
====================================================================

The complete D2 CombinedPrediction artifact must be frozen before label access.

Future execution order:

1. load exact D0 prediction
2. load exact D1 prediction
3. resolve frozen rule-source mapping
4. compute D2 pointwise fusion
5. freeze CombinedPrediction artifact
6. ONLY THEN load labels
7. compute metrics

Labels cannot influence fusion.

====================================================================
19. PRIMARY COMPARISON METRICS
====================================================================

Use exactly the same primary metrics as D0/D1.

Metric 1:

Attack-event Recall

Formula:

ATTACK_EVENTS_OVERLAPPED_BY_AT_LEAST_ONE_ALARM_EPISODE_DIVIDED_BY_ALL_ATTACK_EVENTS

Metric 2:

Normal FAR episodes/hour

Formula:

ALARM_EPISODES_WITH_NO_ATTACK_TIMESTAMP_DIVIDED_BY_NORMAL_LABELED_SECONDS_OVER_3600

Alarm episodes:

MAXIMAL_CONTIGUOUS_UNIQUE_ONE_SECOND_DECISION_INDICES_FILE_LOCAL

No point adjustment.

====================================================================
20. D2-SPECIFIC INCREMENTAL METRICS
====================================================================

Freeze additional D2 utility metrics now.

These do NOT alter the D2 prediction.

A. D0-Missed Attack Recovery Rate

Denominator:

attack events NOT overlapped by any frozen D0 alarm episode

Numerator:

those denominator events overlapped by at least one RULE_RECOVERY D2 episode

Formula identity:

D0_MISSED_ATTACK_EVENTS_RECOVERED_BY_RULE_RECOVERY
DIVIDED_BY
ALL_D0_MISSED_ATTACK_EVENTS

If denominator = 0:

undefined reason:

NO_D0_MISSED_ATTACK_EVENTS

B. Incremental Attack-event Recall

D2 Attack-event Recall
-
D0 Attack-event Recall

C. Added Normal Recovery Episodes / Hour

Numerator:

RULE_RECOVERY alarm episodes with zero attack-event overlap

Denominator:

normal labeled seconds / 3600

D. Incremental Normal FAR

D2 Normal FAR
-
D0 Normal FAR

These metrics quantify:

benefit = detector misses recovered

cost = additional false-alarm episodes.

====================================================================
21. D1 IS NOT THE D2 BASELINE
====================================================================

Primary D2 incremental comparison is:

D2 versus D0

because D2 is a detector augmentation.

D1 remains a separate Rule-only arm.

Final table later:

D0 Detector-only

D1 Rule-only

D2 Detector + corroborated Rule recovery

Do NOT optimize D2 to beat D1.

====================================================================
22. D2 CLAIM BOUNDARY
====================================================================

Allowed future claims:

- rule corroboration recovered detector-missed attack events;
- D2 increased/decreased event recall;
- rule recovery added a measurable false-alarm cost;
- verified physical relation violations provided interpretable supporting
  evidence.

Do NOT claim:

- causality;
- root cause;
- optimal fusion;
- universally superior detector;
- SOTA performance.

====================================================================
23. NO RAW OR FUSED UNION ALTERNATIVE IN PRIMARY TASK
====================================================================

Do NOT silently introduce:

D0 OR any D1 rule alarm

as the primary D2.

Do NOT add multiple fusion candidates and choose the best.

Do NOT test:

OR
AND
weighted
score gating
one-source
two-source
three-source

within INNER data.

Primary D2 policy is frozen exactly once.

====================================================================
24. OPTIONAL NAIVE UNION STATUS
====================================================================

A naive raw union may only be added later as a separately preregistered
diagnostic baseline if scientifically necessary.

It is NOT part of D2 V1.

Do not implement it here.

====================================================================
25. DESIGN MODULE
====================================================================

Create:

src/paperworks/v6/
task039e3_r2r_d2_design_v1.py

No real prediction reads.

No test1 reads.

No labels.

Define immutable contracts such as:

D2DesignAuthorityV1

D2FrozenInputAuthorityV1

D2SourceResolutionPolicyV1

D2RuleCorroborationPolicyV1

D2FusionPolicyV1

D2TriggerClassPolicyV1

D2MetricPolicyV1

D2FuturePredictionContractV1

No caller scientific knobs.

====================================================================
26. CONFIG
====================================================================

Create:

configs/v6/
task039e3_r2r_d2_detector_rule_corroboration_v1.json

Self-hashed.

Must encode:

- D2 ID
- exact frozen D0 prediction hash
- exact frozen D1 prediction hash
- distinct source criterion
- required source count = 2
- exact same-second policy
- D0 preserve = true
- no D0 score
- no label fusion
- exact metric policies

Do NOT include observed D0/D1 performance values.

====================================================================
27. D2 DESIGN HASH
====================================================================

Create canonical:

D2_DESIGN_HASH

from complete frozen policy.

Future D2 implementation/execution must require this exact design hash.

====================================================================
28. DESIGN-INDEPENDENCE DECLARATION
====================================================================

Machine-readable:

d0_prediction_content_read_for_design = false

d1_prediction_content_read_for_design = false

d0_metrics_used_for_design = false

d1_metrics_used_for_design = false

test1_used_for_design = false

labels_used_for_design = false

fusion_candidates_compared = 0

hyperparameter_search_performed = false

rule_corroboration_count = 2

corroboration_count_rationale =
MINIMUM_NON_SINGLETON_DISTINCT_SOURCE_CORROBORATION

====================================================================
29. STATIC TESTS
====================================================================

Create:

tests/test_task039e3_r2r_d2_design_v1.py

Synthetic/static only.

Test at least:

- exact D0 hash
- exact D1 hash
- D2 ID
- D0 preservation
- single D1 alarm cannot recover
- two rules from SAME source cannot recover
- two distinct sources recover
- 3+ distinct sources recover
- same-second requirement
- adjacent-second alarms do not corroborate
- no D0 score dependency
- no label dependency
- D0 alarm always preserved
- trigger classes exact
- caller source-count override rejected
- caller temporal-window override rejected
- caller D0 suppression rejected
- caller rule rerun rejected
- test2 rejected
- D1 rerun rejected
- D0 rerun rejected
- D2 execution not authorized
- metric formulas exact
- D0-missed recovery metric exact
- added FAR metric exact

====================================================================
30. DESIGN COMMIT A
====================================================================

Create local Commit A containing ONLY:

- task specification
- D2 design module
- D2 config
- static tests

No prediction artifacts.

No metric results.

NO PUSH.

Suggested:

TASK-039E3-R2R design preregister D2 corroborated rule recovery

====================================================================
31. INDEPENDENT DESIGN AUDIT
====================================================================

After Commit A add:

tests/
test_task039e3_r2r_d2_design_v1_independent.py

Do not modify production after Commit A.

Attack at least:

- D0 artifact substitution
- D1 artifact substitution
- source count 1
- source count 3
- same-source duplicate counting
- temporal tolerance insertion
- rolling window insertion
- D0 score dependency
- label dependency
- D0 alarm suppression
- any-rule raw OR substitution
- AND substitution
- weighted fusion
- D1 rerun
- D0 rerun
- test2
- OUTER
- metric mutation
- D0-missed recovery formula mutation
- caller fusion selection

Require:

accepted invalid = 0

====================================================================
32. INDEPENDENT AUDIT COMMIT B
====================================================================

Commit B contains ONLY:

independent audit test.

NO PUSH.

Suggested:

TASK-039E3-R2R independently audit D2 fusion preregistration

====================================================================
33. DESIGN REPORTS
====================================================================

Create self-hashed:

TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_V1_DESIGN.json

TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_V1_INPUT_AUTHORITY.json

TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_V1_CORROBORATION_POLICY.json

TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_V1_METRIC_POLICY.json

TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_V1_INDEPENDENCE.json

TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_V1_INDEPENDENT_AUDIT.json

TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_V1_READINESS.json

TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_V1_BUNDLE.json

TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_V1_RECEIPT.json

TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_V1_REPORT.md

No D0/D1 observed metric values.

No prediction content.

No test labels.

====================================================================
34. DESIGN FREEZE COMMIT C
====================================================================

Commit C contains ONLY:

sanitized D2 design reports.

No source.

No tests.

NO PUSH.

Suggested:

TASK-039E3-R2R freeze D2 corroborated rule recovery design

====================================================================
35. CONTINUITY
====================================================================

Update locally:

docs/project_state/CURRENT_STATE.md
docs/project_state/CURRENT_STATE.json
docs/project_state/AUTHORITY_INDEX.md
docs/project_state/DECISION_LOG.md
docs/project_state/TASK_LEDGER.md
docs/project_state/HANDOFF.md

Append durable decision:

DEC-D2-001

Primary D2 is detector-preserving same-second multi-source verified-rule
corroboration.

Rules require at least two distinct source variables to create a detector
recovery alarm.

This was frozen before D2 execution and without prediction-content/label
inspection.

Set:

UTILITY_INNER_D0_RESULT_INTEGRITY_AUDITED = true

UTILITY_INNER_D1_RESULT_INTEGRITY_AUDITED = true

UTILITY_INNER_D2_DESIGN_FROZEN = true

UTILITY_INNER_D2_AUTHORIZED = false

UTILITY_INNER_D2_EXECUTED = false

UTILITY_OUTER_EXECUTION_AUTHORIZED = false

REMOTE_EGRESS_STATUS = LOCAL_ONLY_NOT_PUSHED

====================================================================
36. CONTINUITY COMMIT D
====================================================================

Commit D contains ONLY:

docs/project_state updates.

NO PUSH.

Suggested:

TASK-039E3-R2R update handoff after D2 design freeze

====================================================================
37. PASS CRITERIA
====================================================================

PASS requires:

- corrected D0 integrity remediation PASS;
- D0 exact prediction hash bound;
- D1 exact prediction hash bound;
- no D0 content read;
- no D1 content read;
- no D0/D1 metric read for design;
- no test1;
- no labels;
- D2 policy exact;
- D0 alarms always preserved;
- two distinct source requirement exact;
- same-second exact;
- no temporal parameter;
- no D0 score;
- no rule rerun;
- no hyperparameter search;
- metric formulas frozen;
- accepted invalid 0;
- no scientific execution;
- no remote push.

====================================================================
38. PASS STATUS
====================================================================

Status:

passed_task039e3_r2r_utility_inner_d2_design_and_freeze_v1

Scientific state:

D2_DESIGN_FROZEN_NOT_AUTHORIZED

Remote state:

LOCAL_ONLY_NOT_PUSHED

====================================================================
39. BLOCK CONDITIONS
====================================================================

BLOCK if:

- D0/D1 artifact identities unresolved;
- D1 source mapping cannot be resolved exactly;
- prediction content is read during design;
- observed metrics influence fusion;
- labels accessed;
- test2 touched;
- multiple fusion candidates evaluated;
- D0 suppression permitted;
- fusion remains caller-configurable;
- D2 execution occurs;
- remote push occurs.

On BLOCK:

freeze sanitized blocker
update continuity
STOP.

Do not invent another fusion automatically.

====================================================================
40. EXACT NEXT TASK AFTER PASS
====================================================================

Do NOT start automatically.

Exact next task:

TASK-039E3-R2R-UTILITY-INNER-D2-EXECUTION-AUTHORIZATION-V1

That task will authorize only:

- exact frozen D2 design;
- exact D0 DetectorPrediction artifact;
- exact D1 RulePrediction artifact;
- exact COMMON-42 relation/source mapping;
- test1 labels only AFTER CombinedPrediction freeze;
- same frozen metric/event policies.

It must NOT:

- rerun D0;
- rerun D1;
- modify fusion;
- access test2.

Then:

TASK-039E3-R2R-UTILITY-INNER-D2-EXECUTION-V1

Then:

TASK-039E3-R2R-UTILITY-INNER-D2-RESULT-INTEGRITY-AUDIT-V1

Then:

D0 vs D1 vs D2 final INNER scientific comparison.

====================================================================
41. FINAL RESPONSE
====================================================================

Return only sanitized fields:

Status

Branch
Base

D2 Design Commit A
Independent Audit Commit B
Design Freeze Commit C
Continuity Commit D

Remote egress status
Push attempted?

Worktree/index

D2 ID
D2 fusion family
D2 design hash

D0 DetectorPrediction hash
D1 RulePrediction hash

D0 prediction content read?
D1 prediction content read?
D0 metric used?
D1 metric used?
Test1 used?
Labels used?

COMMON-42 source mapping available?
Source resolution policy

Required distinct source count
Same-second policy
D0 preservation policy
D0 score dependency
Rule rerun dependency

Trigger classes

Primary metric 1
Primary metric 2

D0-missed attack recovery metric
Incremental recall metric
Added normal recovery FAR metric
Incremental FAR metric

Fusion candidates compared
Hyperparameter search performed

Static tests
Independent attacks
Accepted invalid

Scientific executions
D0 executions
D1 executions
D2 executions
Test2 accesses

Private paths exposed
Private numeric values exposed

Design report hash
Input authority hash
Corroboration policy hash
Metric policy hash
Independence hash
Independent audit hash
Readiness hash
Bundle hash
Receipt hash

CURRENT_STATE self-hash
HANDOFF updated

UTILITY_INNER_D2_DESIGN_FROZEN
UTILITY_INNER_D2_AUTHORIZED
UTILITY_INNER_D2_EXECUTED

OUTER authorized

Blockers
Exact next task

STOP.

