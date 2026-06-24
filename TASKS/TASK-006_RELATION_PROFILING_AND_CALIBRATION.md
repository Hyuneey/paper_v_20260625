---
id: TASK-006
title: Implement high-resolution relation profiling and normal-data calibration
status: blocked
depends_on: [TASK-005]
phase_gate: Milestone 3
suggested_branch: task-006-relation-profiling
---

# TASK-006: Relation Profiling and Calibration

## 1. Goal

For approved binary-actuator → continuous-sensor candidate pairs, profile the normal trigger-response relation on the canonical high-resolution rule view and derive calibrated response-delay and response-magnitude parameters from `calibration_normal` only.

## 2. Architecture context

GDN may operate on a downsampled view, but executable temporal rules require time-accurate profiling. This task converts a candidate pair into a structured evidence pack without using final test information.

## 3. Preconditions

- Phase Gate A approved.
- Canonical rule view has verified timestamps and sampling period.
- Candidate pair artifacts are approved.
- Actuator state mappings are available in metadata.
- Calibration policy is approved or recorded as a decision.

## 4. Inputs

- approved candidate pairs,
- canonical rule view from `calibration_normal`,
- variable metadata,
- dataset/view/split manifests,
- profiling config.

Optional validation observations may be computed later for verifier input, but must be stored separately from normal calibration statistics.

## 5. Initial supported relation

```text
source: binary actuator
target: continuous sensor
trigger: configured source transition, initially closed -> open
response: positive target change above calibrated magnitude
```

Do not generalize silently to other pair types.

## 6. Required outputs

- trigger-event table,
- response-event table,
- response-delay distribution,
- response-magnitude distribution,
- support counts,
- missing-response statistics,
- calibration records,
- structured evidence-pack artifacts,
- unsupported-pair reports.

## 7. Required schemas

```python
@dataclass(frozen=True)
class RelationProfile:
    source: str
    target: str
    relation_type: str
    source_view: str
    sampling_period_seconds: float
    trigger_count: int
    matched_response_count: int
    censored_or_missing_count: int
    delay_summary_seconds: Mapping[str, float]
    magnitude_summary: Mapping[str, float]
    normal_support_status: str
    upstream_artifact_ids: tuple[str, ...]
    schema_version: str

@dataclass(frozen=True)
class CalibrationRecord:
    parameter_name: str
    value: float
    unit: str
    method: str
    quantile_or_config: Mapping[str, Any]
    normal_support_count: int
    relation_profile_id: str
    calibration_split_id: str
    schema_version: str
```

## 8. Time-resolution rules

- Use the canonical rule view, not an implicit GDN view.
- Compute delay from timestamps when available.
- If sample indices are used, convert through recorded `sampling_period_seconds`.
- Detect irregular gaps and follow an explicit approved policy.
- Do not express a delay in seconds if timing metadata is unverified.

## 9. Profiling rules

- Define trigger transitions from metadata/config.
- Define response onset deterministically.
- Handle repeated triggers and overlapping response windows explicitly.
- Record right-censored or missing responses rather than dropping them silently.
- Return `INSUFFICIENT_NORMAL_SUPPORT` when support is below the approved minimum.
- Do not fabricate values for unsupported pairs.

## 10. Evidence pack

The evidence pack may contain aggregate and reference information only:

```text
candidate pair
variable metadata
normal trigger/response summary
calibrated Delta t
calibrated minimum magnitude
support counts
recommended rule family
artifact references
```

Do not include raw SWaT rows or long raw sequences in Git-tracked evidence packs or future LLM prompts.

## 11. In scope

- event extraction,
- delay/magnitude statistics,
- calibration,
- aggregate evidence packs,
- synthetic tests.

## 12. Out of scope

- final test evaluation,
- full DyGraphAD,
- LLM calls,
- generalized pair types,
- causal interpretation.

## 13. Acceptance criteria

1. Calibration uses only `calibration_normal`.
2. Delay values are traceable to timestamps/sampling period.
3. Same input/config yields identical aggregate artifacts.
4. Unsupported pairs produce explicit status.
5. Every numeric parameter references a calibration record.
6. GDN-view downsampling cannot silently enter rule calibration.
7. Raw SWaT sequences are absent from tracked outputs.

## 14. Required tests

- exact synthetic response delay,
- exact response magnitude,
- repeated-trigger handling,
- missing response,
- irregular sampling policy,
- insufficient support,
- unit conversion,
- wrong-view rejection,
- test-split rejection,
- evidence-pack provenance round trip.

## 15. Stop conditions

Stop if trigger encoding, response definition, quantile choice, or support threshold requires an unapproved scientific decision.
