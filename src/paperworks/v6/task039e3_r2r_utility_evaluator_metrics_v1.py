"""Synthetic-only prediction artifacts and frozen utility metric interfaces.

This module implements the already-frozen event semantics without opening a
label file or a scientific authority.  Raw alarm timestamps are deduplicated
and merged only when consecutive at the one-second sampling interval.  Attack
events are maximal file-local runs of exact integer label ``1`` values.

All constructors in this freeze produce ``SYNTHETIC_CONTRACT_ONLY`` objects.
The scientific validators intentionally fail closed; a later execution-
authorization task must provide real custody rather than promoting these
objects.  No weighted score or detector/rule fusion operation exists here.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import math
from weakref import ReferenceType, ref

from paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 import (
    COMBINED_SOURCE_CENSUS_CONTRACT_HASH,
    MAIN_DESCRIPTOR_HASH,
    SUPPLEMENT_DESCRIPTOR_HASH,
    EvaluatorAuthorityBundleV1,
    SyntheticNumericResolverV1,
    validate_evaluator_authority_bundle_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_census_v1 import (
    validate_full_census_result_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_input_v1 import (
    validate_synthetic_feature_frame_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_rule_engine_v1 import (
    validate_rule_execution_result_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import (
    EVALUATOR_VERSION,
    SYNTHETIC_AUTHORITY_IDENTITY,
    SYNTHETIC_CONTRACT_ONLY,
    FullCensusResultV1,
    RuleExecutionResultV1,
    SyntheticFeatureFrameV1,
    UtilityEvaluatorV1Error,
    dataclass_payload_v1,
    stable_hash_v1,
    strict_bool_v1,
    strict_float_v1,
    strict_int_v1,
    strict_sha256_v1,
    strict_str_v1,
    strict_tuple_v1,
)
from paperworks.v6.task039e3_r2r_utility_protocol_v4 import (
    CANONICAL_V4_AUTHORITY_HASH,
    CORRECTED_EVENT_POLICY_HASH,
    CORRECTED_METRIC_POLICY_HASH,
    UTILITY_MAIN_PORTFOLIO,
)


RULE_PREDICTION_ARTIFACT_TYPE = "task039e3_r2r_rule_prediction_artifact_v1"
DETECTOR_PREDICTION_ARTIFACT_TYPE = "task039e3_r2r_detector_prediction_artifact_v1"
COMPARISON_INPUT_ARTIFACT_TYPE = "task039e3_r2r_rule_detector_comparison_input_v1"
ALARM_EPISODE_POLICY = "MAXIMAL_CONTIGUOUS_UNIQUE_ONE_SECOND_DECISION_INDICES_FILE_LOCAL"
ATTACK_EVENT_POLICY = "MAXIMAL_CONTIGUOUS_STRICT_LABEL_ONE_RUNS_FILE_LOCAL"
ATTACK_EVENT_RECALL_FORMULA = "ATTACK_EVENTS_OVERLAPPED_BY_AT_LEAST_ONE_ALARM_EPISODE_DIVIDED_BY_ALL_ATTACK_EVENTS"
NORMAL_FAR_FORMULA = "ALARM_EPISODES_WITH_NO_ATTACK_TIMESTAMP_DIVIDED_BY_NORMAL_LABELED_SECONDS_OVER_3600"
FULL_CENSUS_DENOMINATOR_POLICY = "ALL_AUTOMATICALLY_ENUMERATED_APPLICABLE_CANONICAL_OPPORTUNITIES"
CANONICAL_EVALUATOR_AUTHORITY_BUNDLE_HASH = "0510da125dd8a799c988927ba49ecb784cad5ea12b05b41e31406effe23051c9"

_FINAL_STATES = frozenset({"evaluated_expected_response", "evaluated_anomaly", "abstain"})
_ISSUED_RULE_ARTIFACTS: dict[int, tuple[ReferenceType[RulePredictionArtifactV1], str]]
_METRIC_ISSUANCE_TOKEN = object()


def _fail(code: str) -> None:
    raise UtilityEvaluatorV1Error(code)


@dataclass(frozen=True)
class IntervalV1:
    """A nonempty, file-local, half-open one-second interval."""

    start: int
    end: int

    def __post_init__(self) -> None:
        strict_int_v1(self.start, "interval start", minimum=0)
        strict_int_v1(self.end, "interval end", minimum=0)
        if self.end <= self.start:
            _fail("METRIC_INTERVAL_EMPTY_OR_REVERSED")


def strict_synthetic_binary_labels_v1(labels: tuple[int, ...]) -> tuple[int, ...]:
    strict_tuple_v1(labels, "synthetic labels")
    for value in labels:
        if type(value) is not int or value not in {0, 1}:
            _fail("METRIC_LABEL_NOT_EXACT_BINARY_INTEGER")
    return labels


def derive_attack_events_v1(labels: tuple[int, ...]) -> tuple[IntervalV1, ...]:
    values = strict_synthetic_binary_labels_v1(labels)
    events: list[IntervalV1] = []
    start: int | None = None
    for index, value in enumerate((*values, 0)):
        if value == 1 and start is None:
            start = index
        elif value == 0 and start is not None:
            events.append(IntervalV1(start, index))
            start = None
    return tuple(events)


def form_alarm_episodes_v1(raw_alarm_timestamps: tuple[int, ...]) -> tuple[IntervalV1, ...]:
    strict_tuple_v1(raw_alarm_timestamps, "raw alarm timestamps")
    normalized: set[int] = set()
    for timestamp in raw_alarm_timestamps:
        normalized.add(strict_int_v1(timestamp, "alarm timestamp", minimum=0))
    ordered = sorted(normalized)
    if not ordered:
        return ()
    episodes: list[IntervalV1] = []
    start = previous = ordered[0]
    for timestamp in ordered[1:]:
        if timestamp == previous + 1:
            previous = timestamp
            continue
        episodes.append(IntervalV1(start, previous + 1))
        start = previous = timestamp
    episodes.append(IntervalV1(start, previous + 1))
    return tuple(episodes)


def _overlap(left: IntervalV1, right: IntervalV1) -> bool:
    return left.start < right.end and right.start < left.end


@dataclass(frozen=True)
class SyntheticLabelEventCustodyV1:
    execution_mode: str
    synthetic_authority_identity: str
    dataset_manifest_identity: str
    split_identity: str
    source_file_identity: str
    physical_row_count: int
    strict_label_vector_hash: str
    attack_events: tuple[IntervalV1, ...]
    attack_labeled_seconds: int
    normal_labeled_seconds: int
    event_policy_hash: str
    custody_hash: str


_ISSUED_LABEL_CUSTODIES: dict[
    int,
    tuple[
        ReferenceType[SyntheticLabelEventCustodyV1],
        str,
        str,
        str,
        int,
        int,
        int,
    ],
] = {}


def _label_custody_payload(custody: SyntheticLabelEventCustodyV1) -> dict[str, object]:
    return dataclass_payload_v1(custody, exclude=("custody_hash",))


def _attack_event_set_hash(events: tuple[IntervalV1, ...]) -> str:
    return stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_synthetic_attack_event_set_v1",
            "event_policy_hash": CORRECTED_EVENT_POLICY_HASH,
            "interval_semantics": "HALF_OPEN_FILE_LOCAL_ONE_SECOND",
            "events": [dataclass_payload_v1(item) for item in events],
        }
    )


def _issue_label_custody(custody: SyntheticLabelEventCustodyV1) -> SyntheticLabelEventCustodyV1:
    issued_id = id(custody)

    def _discard(_reference: object, *, key: int = issued_id) -> None:
        _ISSUED_LABEL_CUSTODIES.pop(key, None)

    _ISSUED_LABEL_CUSTODIES[issued_id] = (
        ref(custody, _discard),
        custody.custody_hash,
        custody.strict_label_vector_hash,
        _attack_event_set_hash(custody.attack_events),
        custody.physical_row_count,
        custody.attack_labeled_seconds,
        custody.normal_labeled_seconds,
    )
    return custody


def build_synthetic_label_event_custody_v1(
    *,
    labels: tuple[int, ...],
    dataset_manifest_identity: str,
    split_identity: str,
    source_file_identity: str,
) -> SyntheticLabelEventCustodyV1:
    values = strict_synthetic_binary_labels_v1(labels)
    events = derive_attack_events_v1(values)
    label_hash = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_synthetic_strict_binary_label_vector_v1",
            "execution_mode": SYNTHETIC_CONTRACT_ONLY,
            "labels": list(values),
        }
    )
    result = SyntheticLabelEventCustodyV1(
        SYNTHETIC_CONTRACT_ONLY,
        SYNTHETIC_AUTHORITY_IDENTITY,
        strict_str_v1(dataset_manifest_identity, "dataset manifest identity"),
        strict_str_v1(split_identity, "split identity"),
        strict_str_v1(source_file_identity, "source file identity"),
        len(values),
        label_hash,
        events,
        sum(values),
        len(values) - sum(values),
        CORRECTED_EVENT_POLICY_HASH,
        "",
    )
    issued = replace(result, custody_hash=stable_hash_v1(_label_custody_payload(result)))
    return _issue_label_custody(issued)


def validate_synthetic_label_event_custody_v1(custody: SyntheticLabelEventCustodyV1) -> str:
    if type(custody) is not SyntheticLabelEventCustodyV1:
        _fail("METRIC_LABEL_CUSTODY_TYPE_REJECTED")
    issuance = _ISSUED_LABEL_CUSTODIES.get(id(custody))
    if (
        issuance is None
        or issuance[0]() is not custody
        or issuance[1] != custody.custody_hash
        or issuance[2] != custody.strict_label_vector_hash
        or issuance[3] != _attack_event_set_hash(custody.attack_events)
        or issuance[4] != custody.physical_row_count
        or issuance[5] != custody.attack_labeled_seconds
        or issuance[6] != custody.normal_labeled_seconds
    ):
        _fail("METRIC_LABEL_CUSTODY_FACTORY_CUSTODY_REJECTED")
    if (
        custody.execution_mode != SYNTHETIC_CONTRACT_ONLY
        or custody.synthetic_authority_identity != SYNTHETIC_AUTHORITY_IDENTITY
        or custody.event_policy_hash != CORRECTED_EVENT_POLICY_HASH
    ):
        _fail("METRIC_LABEL_CUSTODY_AUTHORITY_REJECTED")
    strict_int_v1(custody.physical_row_count, "physical row count", minimum=0)
    strict_int_v1(custody.attack_labeled_seconds, "attack labeled seconds", minimum=0)
    strict_int_v1(custody.normal_labeled_seconds, "normal labeled seconds", minimum=0)
    strict_sha256_v1(custody.strict_label_vector_hash, "strict label vector hash")
    strict_sha256_v1(custody.custody_hash, "label custody hash")
    if custody.attack_labeled_seconds + custody.normal_labeled_seconds != custody.physical_row_count:
        _fail("METRIC_LABEL_CUSTODY_EXPOSURE_REJECTED")
    strict_tuple_v1(custody.attack_events, "attack events")
    if any(type(event) is not IntervalV1 for event in custody.attack_events):
        _fail("METRIC_ATTACK_EVENT_TYPE_REJECTED")
    if any(event.end > custody.physical_row_count for event in custody.attack_events):
        _fail("METRIC_ATTACK_EVENT_OUT_OF_RANGE")
    if sum(event.end - event.start for event in custody.attack_events) != custody.attack_labeled_seconds:
        _fail("METRIC_ATTACK_EVENT_EXPOSURE_REJECTED")
    if any(left.end >= right.start for left, right in zip(custody.attack_events, custody.attack_events[1:])):
        _fail("METRIC_ATTACK_EVENT_MAXIMALITY_REJECTED")
    expected = stable_hash_v1(_label_custody_payload(custody))
    if custody.custody_hash != expected:
        _fail("METRIC_LABEL_CUSTODY_HASH_REJECTED")
    return expected


@dataclass(frozen=True)
class BoundMetricV1:
    execution_mode: str
    metric_policy_hash: str
    metric_name: str
    formula_identity: str
    value: float | None
    numerator: int
    denominator: float
    defined: bool
    undefined_reason: str | None
    label_custody_hash: str
    alarm_episode_set_hash: str
    metric_hash: str


_ISSUED_BOUND_METRICS: dict[
    int,
    tuple[
        ReferenceType[BoundMetricV1],
        str,
        str,
        str,
        str,
        str,
    ],
] = {}

_ALLOWED_METRIC_FORMULAS = {
    "attack_event_recall": ATTACK_EVENT_RECALL_FORMULA,
    "normal_false_alarm_rate_per_hour": NORMAL_FAR_FORMULA,
}

_UNDEFINED_REASONS = {
    "attack_event_recall": "no_attack_events",
    "normal_false_alarm_rate_per_hour": "no_normal_exposure",
}


def _metric_payload(metric: BoundMetricV1) -> dict[str, object]:
    return dataclass_payload_v1(metric, exclude=("metric_hash",))


def _episode_set_hash(episodes: tuple[IntervalV1, ...]) -> str:
    return stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_alarm_episode_set_v1",
            "event_policy_hash": CORRECTED_EVENT_POLICY_HASH,
            "interval_semantics": "HALF_OPEN_FILE_LOCAL_ONE_SECOND",
            "episodes": [dataclass_payload_v1(item) for item in episodes],
        }
    )


def _validate_canonical_alarm_episodes_v1(
    episodes: tuple[IntervalV1, ...],
    *,
    physical_row_count: int,
) -> tuple[IntervalV1, ...]:
    """Validate an already-formed canonical, maximal alarm episode tuple."""

    strict_tuple_v1(episodes, "alarm episodes")
    strict_int_v1(physical_row_count, "physical row count", minimum=0)
    previous: IntervalV1 | None = None
    for episode in episodes:
        if type(episode) is not IntervalV1:
            _fail("METRIC_ALARM_EPISODE_TYPE_REJECTED")
        strict_int_v1(episode.start, "alarm episode start", minimum=0)
        strict_int_v1(episode.end, "alarm episode end", minimum=0)
        if episode.end <= episode.start:
            _fail("METRIC_ALARM_EPISODE_EMPTY_OR_REVERSED")
        if episode.end > physical_row_count:
            _fail("METRIC_ALARM_EPISODE_OUT_OF_RANGE")
        if previous is not None and previous.end >= episode.start:
            _fail("METRIC_ALARM_EPISODE_NONCANONICAL")
        previous = episode
    return episodes


def _issue_bound_metric(metric: BoundMetricV1) -> BoundMetricV1:
    issued_id = id(metric)

    def _discard(_reference: object, *, key: int = issued_id) -> None:
        _ISSUED_BOUND_METRICS.pop(key, None)

    _ISSUED_BOUND_METRICS[issued_id] = (
        ref(metric, _discard),
        metric.metric_hash,
        metric.metric_name,
        metric.formula_identity,
        metric.label_custody_hash,
        metric.alarm_episode_set_hash,
    )
    return metric


def _build_bound_metric(
    *,
    metric_name: str,
    formula_identity: str,
    numerator: int,
    denominator: float,
    undefined_reason: str,
    custody_hash: str,
    episodes: tuple[IntervalV1, ...],
    issuance_token: object,
) -> BoundMetricV1:
    if issuance_token is not _METRIC_ISSUANCE_TOKEN:
        _fail("METRIC_BOUND_METRIC_ISSUANCE_REJECTED")
    if _ALLOWED_METRIC_FORMULAS.get(metric_name) != formula_identity:
        _fail("METRIC_BOUND_METRIC_SEMANTIC_AUTHORITY_REJECTED")
    strict_int_v1(numerator, "metric numerator", minimum=0)
    strict_float_v1(denominator, "metric denominator", nonnegative=True)
    if denominator == 0.0:
        value = None
        defined = False
        reason: str | None = undefined_reason
    else:
        value = float(numerator / denominator)
        defined = True
        reason = None
    result = BoundMetricV1(
        SYNTHETIC_CONTRACT_ONLY,
        CORRECTED_METRIC_POLICY_HASH,
        metric_name,
        formula_identity,
        value,
        numerator,
        denominator,
        defined,
        reason,
        custody_hash,
        _episode_set_hash(episodes),
        "",
    )
    issued = replace(result, metric_hash=stable_hash_v1(_metric_payload(result)))
    return _issue_bound_metric(issued)


def validate_bound_metric_v1(metric: BoundMetricV1) -> str:
    if type(metric) is not BoundMetricV1:
        _fail("METRIC_BOUND_METRIC_TYPE_REJECTED")
    issuance = _ISSUED_BOUND_METRICS.get(id(metric))
    if (
        issuance is None
        or issuance[0]() is not metric
        or issuance[1] != metric.metric_hash
        or issuance[2] != metric.metric_name
        or issuance[3] != metric.formula_identity
        or issuance[4] != metric.label_custody_hash
        or issuance[5] != metric.alarm_episode_set_hash
    ):
        _fail("METRIC_BOUND_METRIC_FACTORY_CUSTODY_REJECTED")
    if metric.execution_mode != SYNTHETIC_CONTRACT_ONLY or metric.metric_policy_hash != CORRECTED_METRIC_POLICY_HASH:
        _fail("METRIC_BOUND_METRIC_AUTHORITY_REJECTED")
    if _ALLOWED_METRIC_FORMULAS.get(metric.metric_name) != metric.formula_identity:
        _fail("METRIC_BOUND_METRIC_SEMANTIC_AUTHORITY_REJECTED")
    strict_sha256_v1(metric.label_custody_hash, "metric label custody hash")
    strict_sha256_v1(metric.alarm_episode_set_hash, "metric alarm episode set hash")
    strict_sha256_v1(metric.metric_hash, "metric hash")
    strict_int_v1(metric.numerator, "metric numerator", minimum=0)
    strict_float_v1(metric.denominator, "metric denominator", nonnegative=True)
    strict_bool_v1(metric.defined, "metric defined")
    if metric.defined:
        if metric.undefined_reason is not None or metric.denominator == 0.0:
            _fail("METRIC_BOUND_METRIC_STATE_REJECTED")
        observed = strict_float_v1(metric.value, "metric value")
        if not math.isclose(observed, metric.numerator / metric.denominator, rel_tol=0.0, abs_tol=1e-15):
            _fail("METRIC_BOUND_METRIC_VALUE_REJECTED")
    else:
        if (
            metric.value is not None
            or metric.undefined_reason != _UNDEFINED_REASONS[metric.metric_name]
            or metric.denominator != 0.0
        ):
            _fail("METRIC_BOUND_METRIC_STATE_REJECTED")
    expected = stable_hash_v1(_metric_payload(metric))
    if metric.metric_hash != expected:
        _fail("METRIC_BOUND_METRIC_HASH_REJECTED")
    return expected


def attack_event_recall_v1(
    custody: SyntheticLabelEventCustodyV1,
    alarm_episodes: tuple[IntervalV1, ...],
) -> BoundMetricV1:
    validate_synthetic_label_event_custody_v1(custody)
    _validate_canonical_alarm_episodes_v1(
        alarm_episodes,
        physical_row_count=custody.physical_row_count,
    )
    covered = sum(any(_overlap(event, alarm) for alarm in alarm_episodes) for event in custody.attack_events)
    return _build_bound_metric(
        metric_name="attack_event_recall",
        formula_identity=ATTACK_EVENT_RECALL_FORMULA,
        numerator=covered,
        denominator=float(len(custody.attack_events)),
        undefined_reason="no_attack_events",
        custody_hash=custody.custody_hash,
        episodes=alarm_episodes,
        issuance_token=_METRIC_ISSUANCE_TOKEN,
    )


def normal_far_episodes_per_hour_v1(
    custody: SyntheticLabelEventCustodyV1,
    alarm_episodes: tuple[IntervalV1, ...],
) -> BoundMetricV1:
    validate_synthetic_label_event_custody_v1(custody)
    _validate_canonical_alarm_episodes_v1(
        alarm_episodes,
        physical_row_count=custody.physical_row_count,
    )
    false_alarms = sum(not any(_overlap(event, alarm) for event in custody.attack_events) for alarm in alarm_episodes)
    return _build_bound_metric(
        metric_name="normal_false_alarm_rate_per_hour",
        formula_identity=NORMAL_FAR_FORMULA,
        numerator=false_alarms,
        denominator=float(custody.normal_labeled_seconds / 3600.0),
        undefined_reason="no_normal_exposure",
        custody_hash=custody.custody_hash,
        episodes=alarm_episodes,
        issuance_token=_METRIC_ISSUANCE_TOKEN,
    )


@dataclass(frozen=True)
class RulePredictionArtifactV1:
    artifact_type: str
    execution_mode: str
    synthetic_authority_identity: str
    scientific_eligible: bool
    evaluator_version: str
    evaluator_implementation_identity: str
    evaluator_authority_bundle_hash: str
    v4_authority_hash: str
    common_portfolio: str
    common_relation_count: int
    main_descriptor_hash: str
    supplement_descriptor_hash: str
    combined_source_census_contract_hash: str
    dataset_manifest_identity: str
    split_identity: str
    source_file_identity: str
    opportunity_census_identity: str
    denominator_policy: str
    predictions: tuple[RuleExecutionResultV1, ...]
    trace_identities: tuple[str, ...]
    evaluated_count: int
    alarm_count: int
    abstain_count: int
    error_count: int
    artifact_hash: str


_ISSUED_RULE_ARTIFACTS = {}


def _rule_artifact_payload(artifact: RulePredictionArtifactV1) -> dict[str, object]:
    return dataclass_payload_v1(artifact, exclude=("artifact_hash",))


def _validate_execution_result_structure(result: RuleExecutionResultV1) -> None:
    if type(result) is not RuleExecutionResultV1 or result.execution_mode != SYNTHETIC_CONTRACT_ONLY:
        _fail("PREDICTION_RESULT_MODE_OR_TYPE_REJECTED")
    for identity in (
        result.opportunity_id,
        result.source_event_identity,
        result.relation_binding_hash,
        result.evaluator_computation_identity,
        result.trace_hash,
    ):
        strict_sha256_v1(identity, "prediction identity")
    if result.source_qualification_identity is not None:
        strict_sha256_v1(result.source_qualification_identity, "source qualification identity")
    if result.target_evaluation_identity is not None:
        strict_sha256_v1(result.target_evaluation_identity, "target evaluation identity")
    if result.final_state not in _FINAL_STATES:
        _fail("PREDICTION_FINAL_STATE_REJECTED")
    strict_bool_v1(result.alarm_emitted, "alarm emitted")
    strict_tuple_v1(result.numeric_reference_identities, "numeric reference identities")
    if len(result.numeric_reference_identities) != 10 or len(set(result.numeric_reference_identities)) != 10:
        _fail("PREDICTION_REFERENCE_CLOSURE_REJECTED")
    for identity in result.numeric_reference_identities:
        reference = strict_str_v1(identity, "numeric reference identity")
        prefix = "TASK039E3_UTILITY_NORMAL_ONLY_AUTHORITY_V1:"
        if not reference.startswith(prefix):
            _fail("PREDICTION_REFERENCE_NAMESPACE_REJECTED")
        strict_sha256_v1(reference[len(prefix):], "numeric reference digest")
    if result.final_state == "evaluated_anomaly":
        if result.alarm_emitted is not True or type(result.decision_physical_row_index) is not int:
            _fail("PREDICTION_ANOMALY_STATE_REJECTED")
    elif result.final_state == "evaluated_expected_response":
        if result.alarm_emitted is not False or type(result.decision_physical_row_index) is not int:
            _fail("PREDICTION_EXPECTED_STATE_REJECTED")
    elif result.alarm_emitted is not False or result.decision_physical_row_index is not None:
        _fail("PREDICTION_ABSTAIN_STATE_REJECTED")


def build_rule_prediction_artifact_v1(
    *,
    evaluator_implementation_identity: str,
    bundle: EvaluatorAuthorityBundleV1,
    frame: SyntheticFeatureFrameV1,
    census: FullCensusResultV1,
    resolver: SyntheticNumericResolverV1,
    predictions: tuple[RuleExecutionResultV1, ...],
) -> RulePredictionArtifactV1:
    bundle_hash = validate_evaluator_authority_bundle_v1(bundle)
    if bundle_hash != CANONICAL_EVALUATOR_AUTHORITY_BUNDLE_HASH:
        _fail("PREDICTION_EVALUATOR_AUTHORITY_BUNDLE_REJECTED")
    validate_synthetic_feature_frame_v1(frame, bundle)
    validate_full_census_result_v1(census, frame, bundle, resolver)
    strict_sha256_v1(evaluator_implementation_identity, "evaluator implementation identity")
    strict_tuple_v1(predictions, "rule predictions")
    if frame.execution_mode != SYNTHETIC_CONTRACT_ONLY or census.execution_mode != SYNTHETIC_CONTRACT_ONLY:
        _fail("PREDICTION_REAL_EXECUTION_NOT_AUTHORIZED")
    if census.denominator_policy != FULL_CENSUS_DENOMINATOR_POLICY:
        _fail("PREDICTION_DENOMINATOR_POLICY_REJECTED")
    strict_sha256_v1(census.census_hash, "opportunity census identity")
    expected_opportunities = tuple(
        envelope.canonical_opportunity.opportunity_id for envelope in census.relation_opportunities
    )
    if len(predictions) != len(expected_opportunities):
        _fail("PREDICTION_FULL_CENSUS_CLOSURE_REJECTED")
    observed_opportunities: list[str] = []
    for result, envelope in zip(predictions, census.relation_opportunities, strict=True):
        _validate_execution_result_structure(result)
        validate_rule_execution_result_v1(
            result,
            envelope,
            census,
            frame,
            bundle,
            resolver,
        )
        observed_opportunities.append(result.opportunity_id)
    if tuple(observed_opportunities) != expected_opportunities or len(set(observed_opportunities)) != len(observed_opportunities):
        _fail("PREDICTION_OPPORTUNITY_SET_REJECTED")
    traces = tuple(result.trace_hash for result in predictions)
    if len(set(traces)) != len(traces):
        _fail("PREDICTION_TRACE_IDENTITY_DUPLICATE")
    evaluated = sum(result.final_state != "abstain" for result in predictions)
    alarms = sum(result.alarm_emitted for result in predictions)
    abstains = sum(result.final_state == "abstain" for result in predictions)
    result = RulePredictionArtifactV1(
        RULE_PREDICTION_ARTIFACT_TYPE,
        SYNTHETIC_CONTRACT_ONLY,
        SYNTHETIC_AUTHORITY_IDENTITY,
        False,
        EVALUATOR_VERSION,
        evaluator_implementation_identity,
        bundle_hash,
        CANONICAL_V4_AUTHORITY_HASH,
        UTILITY_MAIN_PORTFOLIO,
        42,
        MAIN_DESCRIPTOR_HASH,
        SUPPLEMENT_DESCRIPTOR_HASH,
        COMBINED_SOURCE_CENSUS_CONTRACT_HASH,
        frame.dataset_manifest_identity,
        frame.split_identity,
        frame.source_file_identity,
        census.census_hash,
        FULL_CENSUS_DENOMINATOR_POLICY,
        predictions,
        traces,
        evaluated,
        alarms,
        abstains,
        0,
        "",
    )
    issued = replace(result, artifact_hash=stable_hash_v1(_rule_artifact_payload(result)))
    issued_id = id(issued)

    def _discard(_reference: object, *, key: int = issued_id) -> None:
        _ISSUED_RULE_ARTIFACTS.pop(key, None)

    _ISSUED_RULE_ARTIFACTS[issued_id] = (ref(issued, _discard), issued.artifact_hash)
    return issued


def validate_rule_prediction_artifact_v1(artifact: RulePredictionArtifactV1) -> str:
    if type(artifact) is not RulePredictionArtifactV1:
        _fail("PREDICTION_ARTIFACT_TYPE_REJECTED")
    issuance = _ISSUED_RULE_ARTIFACTS.get(id(artifact))
    if (
        issuance is None
        or issuance[0]() is not artifact
        or issuance[1] != artifact.artifact_hash
    ):
        _fail("PREDICTION_ARTIFACT_FACTORY_CUSTODY_REJECTED")
    if (
        artifact.artifact_type != RULE_PREDICTION_ARTIFACT_TYPE
        or artifact.execution_mode != SYNTHETIC_CONTRACT_ONLY
        or artifact.synthetic_authority_identity != SYNTHETIC_AUTHORITY_IDENTITY
        or artifact.scientific_eligible is not False
        or artifact.evaluator_version != EVALUATOR_VERSION
        or artifact.evaluator_authority_bundle_hash != CANONICAL_EVALUATOR_AUTHORITY_BUNDLE_HASH
        or artifact.v4_authority_hash != CANONICAL_V4_AUTHORITY_HASH
        or artifact.common_portfolio != UTILITY_MAIN_PORTFOLIO
        or artifact.common_relation_count != 42
        or artifact.main_descriptor_hash != MAIN_DESCRIPTOR_HASH
        or artifact.supplement_descriptor_hash != SUPPLEMENT_DESCRIPTOR_HASH
        or artifact.combined_source_census_contract_hash != COMBINED_SOURCE_CENSUS_CONTRACT_HASH
        or artifact.denominator_policy != FULL_CENSUS_DENOMINATOR_POLICY
        or artifact.error_count != 0
    ):
        _fail("PREDICTION_ARTIFACT_AUTHORITY_REJECTED")
    for name in (
        "common_relation_count",
        "evaluated_count",
        "alarm_count",
        "abstain_count",
        "error_count",
    ):
        strict_int_v1(getattr(artifact, name), name, minimum=0)
    for name in (
        "evaluator_implementation_identity",
        "evaluator_authority_bundle_hash",
        "v4_authority_hash",
        "main_descriptor_hash",
        "supplement_descriptor_hash",
        "combined_source_census_contract_hash",
        "opportunity_census_identity",
        "artifact_hash",
    ):
        strict_sha256_v1(getattr(artifact, name), name)
    strict_tuple_v1(artifact.predictions, "predictions")
    for result in artifact.predictions:
        _validate_execution_result_structure(result)
    expected_traces = tuple(result.trace_hash for result in artifact.predictions)
    if artifact.trace_identities != expected_traces or len(set(expected_traces)) != len(expected_traces):
        _fail("PREDICTION_ARTIFACT_TRACE_REJECTED")
    if artifact.evaluated_count != sum(item.final_state != "abstain" for item in artifact.predictions):
        _fail("PREDICTION_ARTIFACT_EVALUATED_COUNT_REJECTED")
    if artifact.alarm_count != sum(item.alarm_emitted for item in artifact.predictions):
        _fail("PREDICTION_ARTIFACT_ALARM_COUNT_REJECTED")
    if artifact.abstain_count != sum(item.final_state == "abstain" for item in artifact.predictions):
        _fail("PREDICTION_ARTIFACT_ABSTAIN_COUNT_REJECTED")
    expected = stable_hash_v1(_rule_artifact_payload(artifact))
    if artifact.artifact_hash != expected:
        _fail("PREDICTION_ARTIFACT_HASH_REJECTED")
    return expected


def validate_scientific_rule_prediction_artifact_v1(artifact: RulePredictionArtifactV1) -> str:
    """Fail closed until a later task implements authorized real custody."""

    validate_rule_prediction_artifact_v1(artifact)
    _fail("PREDICTION_SYNTHETIC_ARTIFACT_NOT_SCIENTIFICALLY_ELIGIBLE")


def alarm_episodes_from_rule_artifact_v1(artifact: RulePredictionArtifactV1) -> tuple[IntervalV1, ...]:
    validate_rule_prediction_artifact_v1(artifact)
    timestamps = tuple(
        result.decision_physical_row_index
        for result in artifact.predictions
        if result.alarm_emitted and result.decision_physical_row_index is not None
    )
    return form_alarm_episodes_v1(timestamps)


@dataclass(frozen=True)
class SyntheticPointDiagnosticsV1:
    execution_mode: str
    formula_scope: str
    physical_point_count: int
    detector_false_negative_points: int
    recovered_false_negative_points: int
    added_false_positive_points: int
    diagnostic_hash: str


def _diagnostic_payload(value: SyntheticPointDiagnosticsV1) -> dict[str, object]:
    return dataclass_payload_v1(value, exclude=("diagnostic_hash",))


def build_synthetic_point_diagnostics_v1(
    *,
    labels: tuple[int, ...],
    detector_alarm_points: tuple[bool, ...],
    rule_alarm_points: tuple[bool, ...],
) -> SyntheticPointDiagnosticsV1:
    values = strict_synthetic_binary_labels_v1(labels)
    strict_tuple_v1(detector_alarm_points, "detector alarm points")
    strict_tuple_v1(rule_alarm_points, "rule alarm points")
    if len(values) != len(detector_alarm_points) or len(values) != len(rule_alarm_points):
        _fail("DIAGNOSTIC_POINT_VECTOR_LENGTH_REJECTED")
    for item in detector_alarm_points + rule_alarm_points:
        strict_bool_v1(item, "alarm point")
    detector_fn = sum(label == 1 and not detector for label, detector in zip(values, detector_alarm_points))
    recovered = sum(
        label == 1 and not detector and rule
        for label, detector, rule in zip(values, detector_alarm_points, rule_alarm_points)
    )
    added_fp = sum(
        label == 0 and not detector and rule
        for label, detector, rule in zip(values, detector_alarm_points, rule_alarm_points)
    )
    result = SyntheticPointDiagnosticsV1(
        SYNTHETIC_CONTRACT_ONLY,
        "INTERFACE_ONLY_POINT_LEVEL_DIAGNOSTICS_NOT_A_SCIENTIFIC_METRIC_OR_FUSION_RULE",
        len(values),
        detector_fn,
        recovered,
        added_fp,
        "",
    )
    return replace(result, diagnostic_hash=stable_hash_v1(_diagnostic_payload(result)))


@dataclass(frozen=True)
class DetectorPredictionArtifactV1:
    artifact_type: str
    execution_mode: str
    scientific_eligible: bool
    detector_authority_identity: str
    dataset_manifest_identity: str
    split_identity: str
    source_file_identity: str
    point_predictions: tuple[bool, ...]
    artifact_hash: str


def _detector_payload(value: DetectorPredictionArtifactV1) -> dict[str, object]:
    return dataclass_payload_v1(value, exclude=("artifact_hash",))


def build_synthetic_detector_prediction_artifact_v1(
    *,
    detector_authority_identity: str,
    dataset_manifest_identity: str,
    split_identity: str,
    source_file_identity: str,
    point_predictions: tuple[bool, ...],
) -> DetectorPredictionArtifactV1:
    strict_sha256_v1(detector_authority_identity, "detector authority identity")
    strict_tuple_v1(point_predictions, "detector predictions")
    for value in point_predictions:
        strict_bool_v1(value, "detector prediction")
    result = DetectorPredictionArtifactV1(
        DETECTOR_PREDICTION_ARTIFACT_TYPE,
        SYNTHETIC_CONTRACT_ONLY,
        False,
        detector_authority_identity,
        strict_str_v1(dataset_manifest_identity, "dataset manifest identity"),
        strict_str_v1(split_identity, "split identity"),
        strict_str_v1(source_file_identity, "source file identity"),
        point_predictions,
        "",
    )
    return replace(result, artifact_hash=stable_hash_v1(_detector_payload(result)))


def validate_detector_prediction_artifact_v1(artifact: DetectorPredictionArtifactV1) -> str:
    if type(artifact) is not DetectorPredictionArtifactV1:
        _fail("DETECTOR_ARTIFACT_TYPE_REJECTED")
    if (
        artifact.artifact_type != DETECTOR_PREDICTION_ARTIFACT_TYPE
        or artifact.execution_mode != SYNTHETIC_CONTRACT_ONLY
        or artifact.scientific_eligible is not False
    ):
        _fail("DETECTOR_ARTIFACT_AUTHORITY_REJECTED")
    strict_tuple_v1(artifact.point_predictions, "detector predictions")
    for value in artifact.point_predictions:
        strict_bool_v1(value, "detector prediction")
    expected = stable_hash_v1(_detector_payload(artifact))
    if artifact.artifact_hash != expected:
        _fail("DETECTOR_ARTIFACT_HASH_REJECTED")
    return expected


@dataclass(frozen=True)
class RuleDetectorComparisonInputV1:
    artifact_type: str
    execution_mode: str
    scientific_eligible: bool
    detector_artifact_hash: str
    d1_rule_artifact_hash: str
    d2_rule_artifact_hash: str
    same_rule_artifact_required: bool
    fusion_authorized: bool
    artifact_hash: str


def _comparison_payload(value: RuleDetectorComparisonInputV1) -> dict[str, object]:
    return dataclass_payload_v1(value, exclude=("artifact_hash",))


def build_synthetic_rule_detector_comparison_input_v1(
    *,
    detector: DetectorPredictionArtifactV1,
    d1_rule_artifact: RulePredictionArtifactV1,
    d2_rule_artifact: RulePredictionArtifactV1,
) -> RuleDetectorComparisonInputV1:
    detector_hash = validate_detector_prediction_artifact_v1(detector)
    d1_hash = validate_rule_prediction_artifact_v1(d1_rule_artifact)
    d2_hash = validate_rule_prediction_artifact_v1(d2_rule_artifact)
    if d1_hash != d2_hash:
        _fail("COMPARISON_D1_D2_RULE_ARTIFACT_MUST_BE_IDENTICAL")
    if (
        detector.dataset_manifest_identity != d1_rule_artifact.dataset_manifest_identity
        or detector.split_identity != d1_rule_artifact.split_identity
        or detector.source_file_identity != d1_rule_artifact.source_file_identity
    ):
        _fail("COMPARISON_DATASET_SPLIT_FILE_CUSTODY_REJECTED")
    result = RuleDetectorComparisonInputV1(
        COMPARISON_INPUT_ARTIFACT_TYPE,
        SYNTHETIC_CONTRACT_ONLY,
        False,
        detector_hash,
        d1_hash,
        d2_hash,
        True,
        False,
        "",
    )
    return replace(result, artifact_hash=stable_hash_v1(_comparison_payload(result)))


def validate_scientific_rule_detector_comparison_input_v1(
    comparison: RuleDetectorComparisonInputV1,
) -> str:
    if type(comparison) is not RuleDetectorComparisonInputV1:
        _fail("COMPARISON_INPUT_TYPE_REJECTED")
    if stable_hash_v1(_comparison_payload(comparison)) != comparison.artifact_hash:
        _fail("COMPARISON_INPUT_HASH_REJECTED")
    _fail("COMPARISON_SYNTHETIC_INPUT_NOT_SCIENTIFICALLY_ELIGIBLE")


__all__ = [
    "RULE_PREDICTION_ARTIFACT_TYPE",
    "DETECTOR_PREDICTION_ARTIFACT_TYPE",
    "COMPARISON_INPUT_ARTIFACT_TYPE",
    "ALARM_EPISODE_POLICY",
    "ATTACK_EVENT_POLICY",
    "ATTACK_EVENT_RECALL_FORMULA",
    "NORMAL_FAR_FORMULA",
    "CANONICAL_EVALUATOR_AUTHORITY_BUNDLE_HASH",
    "IntervalV1",
    "SyntheticLabelEventCustodyV1",
    "BoundMetricV1",
    "RulePredictionArtifactV1",
    "SyntheticPointDiagnosticsV1",
    "DetectorPredictionArtifactV1",
    "RuleDetectorComparisonInputV1",
    "strict_synthetic_binary_labels_v1",
    "derive_attack_events_v1",
    "form_alarm_episodes_v1",
    "build_synthetic_label_event_custody_v1",
    "validate_synthetic_label_event_custody_v1",
    "attack_event_recall_v1",
    "normal_far_episodes_per_hour_v1",
    "validate_bound_metric_v1",
    "build_rule_prediction_artifact_v1",
    "validate_rule_prediction_artifact_v1",
    "validate_scientific_rule_prediction_artifact_v1",
    "alarm_episodes_from_rule_artifact_v1",
    "build_synthetic_point_diagnostics_v1",
    "build_synthetic_detector_prediction_artifact_v1",
    "validate_detector_prediction_artifact_v1",
    "build_synthetic_rule_detector_comparison_input_v1",
    "validate_scientific_rule_detector_comparison_input_v1",
]
