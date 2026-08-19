"""Deterministic synthetic rule interpreter for Utility Evaluator V1.

The interpreter consumes the canonical V4 opportunity produced by the
evaluator census.  It neither constructs an alternative opportunity authority
nor accepts caller-authored scientific outcomes.  The only executable plane in
this freeze is ``SYNTHETIC_CONTRACT_ONLY``; a later, separately authorized task
must add the real data-plane custody boundary.

No private value is included in a returned result or trace hash preimage.
"""

from __future__ import annotations

import statistics

from paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 import (
    EvaluatorAuthorityBundleV1,
    SyntheticNumericResolverV1,
    validate_evaluator_authority_bundle_v1,
    validate_synthetic_numeric_resolver_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_census_v1 import (
    validate_opportunity_envelope_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_input_v1 import (
    feature_value_v1,
    validate_synthetic_feature_frame_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import (
    EVALUATOR_VERSION,
    SYNTHETIC_CONTRACT_ONLY,
    CanonicalOpportunityEnvelopeV1,
    FullCensusResultV1,
    RuleExecutionResultV1,
    SyntheticFeatureFrameV1,
    UtilityEvaluatorV1Error,
    stable_hash_v1,
    strict_bool_v1,
    strict_float_v1,
    strict_int_v1,
    strict_sha256_v1,
    strict_str_v1,
)
from paperworks.v6.task039e3_r2r_utility_protocol_v2 import (
    MINIMUM_STABILITY_FRACTION,
    SOURCE_POST_WINDOW,
    SOURCE_PRE_WINDOW,
    TARGET_BASELINE_WINDOW,
    TARGET_RESPONSE_WINDOW,
)
from paperworks.v6.task039e3_r2r_utility_protocol_v4 import (
    BOUNDARY_WINDOW_POLICY_HASH,
    CANONICAL_V4_AUTHORITY_HASH,
    FILE_ROW_COUNTS,
    FROZEN_RESPONSE_POLICY_HASH,
    FROZEN_SOURCE_TRIGGER_POLICY_HASH,
    PURGE_POLICY_HASH,
    TERMINAL_TRANSITION_POLICY_HASH,
    UTILITY_NUMERIC_ROLES,
    CanonicalOpportunityV4,
    UtilityProtocolV4Error,
    build_source_qualification_state_v4,
    transition_target_evaluation_v4,
    validate_canonical_opportunity_v4,
    validate_source_qualification_state_v4,
    validate_target_evaluation_state_v4,
)


SOURCE_THRESHOLD_ROLE = "source_step_threshold"
SOURCE_STABILITY_ROLE = "source_stability_tolerance"
TARGET_NOISE_ROLE = "target_noise_scale"

EXPECTED_RESPONSE_STATE = "evaluated_expected_response"
ANOMALY_STATE = "evaluated_anomaly"
ABSTAIN_STATE = "abstain"

_SOURCE_WINDOW_OFFSETS = tuple(range(-SOURCE_PRE_WINDOW, SOURCE_POST_WINDOW))


def _fail(message: str) -> None:
    # Error text is deliberately structural and never interpolates a value.
    raise UtilityEvaluatorV1Error(message)


def _validate_envelope_v1(
    envelope: CanonicalOpportunityEnvelopeV1,
    census: FullCensusResultV1,
    frame: SyntheticFeatureFrameV1,
    bundle: EvaluatorAuthorityBundleV1,
    resolver: SyntheticNumericResolverV1,
) -> CanonicalOpportunityV4:
    if type(envelope) is not CanonicalOpportunityEnvelopeV1:
        _fail("RULE_INVALID_OPPORTUNITY_ENVELOPE_TYPE")
    strict_sha256_v1(
        envelope.isolated_source_event_identity,
        "isolated_source_event_identity",
    )
    strict_sha256_v1(envelope.envelope_hash, "envelope_hash")
    opportunity = envelope.canonical_opportunity
    if type(opportunity) is not CanonicalOpportunityV4:
        _fail("RULE_INVALID_CANONICAL_OPPORTUNITY_TYPE")
    try:
        validate_canonical_opportunity_v4(opportunity, bundle.v4_authority)
    except UtilityProtocolV4Error as exc:
        raise UtilityEvaluatorV1Error("RULE_CANONICAL_OPPORTUNITY_REPLAY") from exc
    try:
        validate_opportunity_envelope_v1(
            envelope,
            census,
            frame,
            bundle,
            resolver,
        )
    except UtilityEvaluatorV1Error as exc:
        raise UtilityEvaluatorV1Error("RULE_OPPORTUNITY_CENSUS_CUSTODY") from exc
    return opportunity


def _validated_resolver_v1(
    resolver: SyntheticNumericResolverV1,
    bundle: EvaluatorAuthorityBundleV1,
    bundle_hash: str,
) -> SyntheticNumericResolverV1:
    if type(resolver) is not SyntheticNumericResolverV1:
        _fail("RULE_INVALID_SYNTHETIC_RESOLVER_TYPE")
    if type(resolver.validated) is not bool or resolver.validated is not True:
        _fail("RULE_SYNTHETIC_RESOLVER_NOT_VALIDATED")
    if resolver.bundle_hash != bundle_hash:
        _fail("RULE_SYNTHETIC_RESOLVER_AUTHORITY_MISMATCH")
    try:
        validate_synthetic_numeric_resolver_v1(resolver, bundle)
    except UtilityEvaluatorV1Error as exc:
        raise UtilityEvaluatorV1Error("RULE_SYNTHETIC_RESOLVER_REPLAY") from exc
    return resolver


def _window_values_v1(
    frame: SyntheticFeatureFrameV1,
    bundle: EvaluatorAuthorityBundleV1,
    *,
    feature: str,
    indices: tuple[int, ...],
) -> tuple[float, ...] | None:
    observed: list[float] = []
    for index in indices:
        if index < 0:
            return None
        try:
            value = feature_value_v1(
                frame,
                bundle,
                physical_row_index=index,
                feature=feature,
            )
        except UtilityEvaluatorV1Error as exc:
            # Only absence of an otherwise canonical physical coordinate is an
            # authorized synthetic boundary.  A malformed cell/frame remains
            # an error and is never converted to abstention.
            if str(exc) == "ROW_OUTSIDE_SYNTHETIC_FRAME":
                return None
            raise
        observed.append(strict_float_v1(value, "scientific feature value"))
    return tuple(observed)


def _abstain_result_v1(
    *,
    envelope: CanonicalOpportunityEnvelopeV1,
    opportunity: CanonicalOpportunityV4,
    rule: object,
    frame_hash: str,
    bundle_hash: str,
    numeric_references: tuple[str, ...],
    reason: str,
    source_qualification_identity: str | None = None,
    target_evaluation_identity: str | None = None,
) -> RuleExecutionResultV1:
    computation_identity = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_utility_evaluator_v1_computation",
            "authority_bundle_hash": bundle_hash,
            "evaluator_version": EVALUATOR_VERSION,
            "execution_mode": SYNTHETIC_CONTRACT_ONLY,
            "frame_hash": frame_hash,
            "isolated_source_event_identity": envelope.isolated_source_event_identity,
            "numeric_reference_identities": list(numeric_references),
            "opportunity_id": opportunity.opportunity_id,
            "rule_descriptor_hash": rule.descriptor_hash,
        }
    )
    trace_payload = {
        "artifact_type": "task039e3_r2r_utility_evaluator_v1_rule_execution_trace",
        "abstention_reason": reason,
        "alarm_emitted": False,
        "authority_bundle_hash": bundle_hash,
        "decision_physical_row_index": None,
        "evaluator_computation_identity": computation_identity,
        "execution_mode": SYNTHETIC_CONTRACT_ONLY,
        "expected_direction": opportunity.target_direction,
        "final_state": ABSTAIN_STATE,
        "numeric_reference_identities": list(numeric_references),
        "opportunity_id": opportunity.opportunity_id,
        "relation_binding_hash": opportunity.relation_binding_hash,
        "rule_descriptor_hash": rule.descriptor_hash,
        "selected_horizon_seconds": opportunity.selected_horizon_seconds,
        "source_event_identity": envelope.isolated_source_event_identity,
        "source_qualification_identity": source_qualification_identity,
        "target_evaluation_identity": target_evaluation_identity,
    }
    return RuleExecutionResultV1(
        execution_mode=SYNTHETIC_CONTRACT_ONLY,
        opportunity_id=opportunity.opportunity_id,
        source_event_identity=envelope.isolated_source_event_identity,
        relation_binding_hash=opportunity.relation_binding_hash,
        source_qualification_identity=source_qualification_identity,
        target_evaluation_identity=target_evaluation_identity,
        final_state=ABSTAIN_STATE,
        alarm_emitted=False,
        decision_physical_row_index=None,
        numeric_reference_identities=numeric_references,
        evaluator_computation_identity=computation_identity,
        trace_hash=stable_hash_v1(trace_payload),
    )


def execute_rule_v1(
    envelope: CanonicalOpportunityEnvelopeV1,
    census: FullCensusResultV1,
    frame: SyntheticFeatureFrameV1,
    bundle: EvaluatorAuthorityBundleV1,
    resolver: SyntheticNumericResolverV1,
) -> RuleExecutionResultV1:
    """Evaluate one canonical COMMON-42 opportunity deterministically.

    The authoritative API deliberately has no caller outcome, source/target
    direction, threshold, window, denominator, or abstention override.
    """

    try:
        bundle_hash = validate_evaluator_authority_bundle_v1(bundle)
    except (UtilityEvaluatorV1Error, UtilityProtocolV4Error) as exc:
        raise UtilityEvaluatorV1Error("RULE_EVALUATOR_AUTHORITY_REPLAY") from exc
    if bundle.v4_authority.authority_hash != CANONICAL_V4_AUTHORITY_HASH:
        _fail("RULE_HISTORICAL_OR_SUBSTITUTE_V4_AUTHORITY")
    try:
        frame_hash = validate_synthetic_feature_frame_v1(frame, bundle)
    except UtilityEvaluatorV1Error:
        raise
    if frame.execution_mode != SYNTHETIC_CONTRACT_ONLY:
        _fail("RULE_REAL_EXECUTION_NOT_AUTHORIZED")
    resolver = _validated_resolver_v1(resolver, bundle, bundle_hash)
    opportunity = _validate_envelope_v1(envelope, census, frame, bundle, resolver)
    if (
        frame.dataset_manifest_identity != opportunity.dataset_manifest_identity
        or frame.split_identity != opportunity.split_identity
        or frame.source_file_identity != opportunity.source_file_identity
    ):
        _fail("RULE_FRAME_OPPORTUNITY_PROVENANCE")

    rule = bundle.v4_authority.rule_by_binding(opportunity.relation_binding_hash)
    if rule.descriptor_hash != opportunity.rule_descriptor_hash:
        _fail("RULE_DESCRIPTOR_PARENT_MISMATCH")
    numeric_references = tuple(reference for _, reference in rule.numeric_reference_bindings)
    if (
        type(rule.numeric_reference_bindings) is not tuple
        or tuple(role for role, _ in rule.numeric_reference_bindings) != UTILITY_NUMERIC_ROLES
        or len(numeric_references) != 10
        or len(set(numeric_references)) != 10
    ):
        _fail("RULE_NUMERIC_REFERENCE_BINDINGS")
    for reference in numeric_references:
        strict_str_v1(reference, "numeric reference identity")

    event_index = strict_int_v1(
        opportunity.physical_row_index,
        "opportunity physical row index",
        minimum=0,
    )
    source_indices = tuple(event_index + offset for offset in _SOURCE_WINDOW_OFFSETS)
    source_values = _window_values_v1(
        frame,
        bundle,
        feature=opportunity.source,
        indices=source_indices,
    )
    if source_values is None:
        return _abstain_result_v1(
            envelope=envelope,
            opportunity=opportunity,
            rule=rule,
            frame_hash=frame_hash,
            bundle_hash=bundle_hash,
            numeric_references=numeric_references,
            reason="incomplete_source_window",
        )

    threshold_reference = rule.reference_for(SOURCE_THRESHOLD_ROLE)
    tolerance_reference = rule.reference_for(SOURCE_STABILITY_ROLE)
    noise_reference = rule.reference_for(TARGET_NOISE_ROLE)
    threshold = strict_float_v1(
        resolver.relation_value(
            opportunity.relation_binding_hash,
            SOURCE_THRESHOLD_ROLE,
            threshold_reference,
        ),
        "source step threshold",
        positive=True,
    )
    tolerance = strict_float_v1(
        resolver.relation_value(
            opportunity.relation_binding_hash,
            SOURCE_STABILITY_ROLE,
            tolerance_reference,
        ),
        "source stability tolerance",
        nonnegative=True,
    )

    pre_values = source_values[:SOURCE_PRE_WINDOW]
    post_values = source_values[SOURCE_PRE_WINDOW:]
    pre_level = float(statistics.median(pre_values))
    post_level = float(statistics.median(post_values))
    amplitude = post_level - pre_level
    pre_fraction = sum(abs(value - pre_level) <= tolerance for value in pre_values) / SOURCE_PRE_WINDOW
    post_fraction = sum(abs(value - post_level) <= tolerance for value in post_values) / SOURCE_POST_WINDOW
    observed_direction = "step_up" if amplitude > 0.0 else "step_down"
    if (
        amplitude == 0.0
        or abs(amplitude) < threshold
        or pre_fraction < MINIMUM_STABILITY_FRACTION
        or post_fraction < MINIMUM_STABILITY_FRACTION
        or observed_direction != opportunity.source_direction
    ):
        _fail("RULE_SOURCE_EVENT_EVIDENCE_MISMATCH")

    source_window_identity = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_utility_evaluator_v1_source_window",
            "feature_identity": opportunity.source,
            "frame_hash": frame_hash,
            "physical_row_indices": list(source_indices),
        }
    )
    computation_identity = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_utility_evaluator_v1_computation",
            "authority_bundle_hash": bundle_hash,
            "evaluator_version": EVALUATOR_VERSION,
            "execution_mode": SYNTHETIC_CONTRACT_ONLY,
            "frame_hash": frame_hash,
            "isolated_source_event_identity": envelope.isolated_source_event_identity,
            "numeric_reference_identities": list(numeric_references),
            "opportunity_id": opportunity.opportunity_id,
            "rule_descriptor_hash": rule.descriptor_hash,
        }
    )
    v4_source_state = build_source_qualification_state_v4(
        opportunity,
        bundle.v4_authority,
        source_window_identity=source_window_identity,
        retained_source_event_identity=envelope.isolated_source_event_identity,
        retained_source_event_census_hash=census.source_census_identity,
    )
    validate_source_qualification_state_v4(
        v4_source_state,
        opportunity,
        bundle.v4_authority,
    )
    source_qualification_identity = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_utility_evaluator_v1_source_qualification",
            "evaluator_computation_identity": computation_identity,
            "event_policy_hash": opportunity.event_policy_hash,
            "source_trigger_policy_hash": FROZEN_SOURCE_TRIGGER_POLICY_HASH,
            "opportunity_id": opportunity.opportunity_id,
            "retained_source_event_identity": envelope.isolated_source_event_identity,
            "rule_descriptor_hash": rule.descriptor_hash,
            "source_stability_reference_identity": tolerance_reference,
            "source_step_reference_identity": threshold_reference,
            "source_window_identity": source_window_identity,
            "state": "source_qualified",
            "v4_source_qualification_identity": v4_source_state.source_qualification_identity,
        }
    )

    baseline_indices = tuple(range(event_index - TARGET_BASELINE_WINDOW, event_index))
    response_start = event_index + opportunity.selected_horizon_seconds
    response_indices = tuple(range(response_start, response_start + TARGET_RESPONSE_WINDOW))
    target_window_input_identity = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_utility_evaluator_v1_target_window",
            "baseline_physical_row_indices": list(baseline_indices),
            "feature_identity": opportunity.target,
            "frame_hash": frame_hash,
            "response_physical_row_indices": list(response_indices),
            "selected_horizon_seconds": opportunity.selected_horizon_seconds,
        }
    )
    decision_index = event_index + opportunity.selected_horizon_seconds + TARGET_RESPONSE_WINDOW - 1
    if decision_index >= FILE_ROW_COUNTS[opportunity.source_file_identity]:
        v4_target_state = transition_target_evaluation_v4(
            opportunity,
            v4_source_state,
            bundle.v4_authority,
            target_window_input_identity=target_window_input_identity,
            within_split=True,
            target_context_available=False,
            response_matched=False,
        )
        validate_target_evaluation_state_v4(
            v4_target_state,
            opportunity,
            v4_source_state,
            bundle.v4_authority,
        )
        target_abstention_identity = stable_hash_v1(
            {
                "abstention_reason": "file_boundary",
                "artifact_type": "task039e3_r2r_utility_evaluator_v1_target_evaluation",
                "evaluator_computation_identity": computation_identity,
                "final_state": ABSTAIN_STATE,
                "numeric_authority_descriptor_hash": opportunity.numeric_authority_descriptor_hash,
                "opportunity_id": opportunity.opportunity_id,
                "rule_descriptor_hash": rule.descriptor_hash,
                "source_qualification_identity": source_qualification_identity,
                "target_noise_reference_identity": noise_reference,
                "target_window_input_identity": target_window_input_identity,
                "boundary_window_policy_hash": BOUNDARY_WINDOW_POLICY_HASH,
                "purge_policy_hash": PURGE_POLICY_HASH,
                "response_policy_hash": FROZEN_RESPONSE_POLICY_HASH,
                "transition_policy_hash": TERMINAL_TRANSITION_POLICY_HASH,
                "v4_terminal_state_provenance_hash": v4_target_state.terminal_state_provenance_hash,
            }
        )
        return _abstain_result_v1(
            envelope=envelope,
            opportunity=opportunity,
            rule=rule,
            frame_hash=frame_hash,
            bundle_hash=bundle_hash,
            numeric_references=numeric_references,
            reason="file_boundary",
            source_qualification_identity=source_qualification_identity,
            target_evaluation_identity=target_abstention_identity,
        )
    target_baseline = _window_values_v1(
        frame,
        bundle,
        feature=opportunity.target,
        indices=baseline_indices,
    )
    target_response = _window_values_v1(
        frame,
        bundle,
        feature=opportunity.target,
        indices=response_indices,
    )
    if target_baseline is None or target_response is None:
        v4_target_state = transition_target_evaluation_v4(
            opportunity,
            v4_source_state,
            bundle.v4_authority,
            target_window_input_identity=target_window_input_identity,
            within_split=True,
            target_context_available=False,
            response_matched=False,
        )
        validate_target_evaluation_state_v4(
            v4_target_state,
            opportunity,
            v4_source_state,
            bundle.v4_authority,
        )
        target_abstention_identity = stable_hash_v1(
            {
                "abstention_reason": "incomplete_target_response_window",
                "artifact_type": "task039e3_r2r_utility_evaluator_v1_target_evaluation",
                "evaluator_computation_identity": computation_identity,
                "final_state": ABSTAIN_STATE,
                "numeric_authority_descriptor_hash": opportunity.numeric_authority_descriptor_hash,
                "opportunity_id": opportunity.opportunity_id,
                "rule_descriptor_hash": rule.descriptor_hash,
                "source_qualification_identity": source_qualification_identity,
                "target_noise_reference_identity": noise_reference,
                "target_window_input_identity": target_window_input_identity,
                "boundary_window_policy_hash": BOUNDARY_WINDOW_POLICY_HASH,
                "purge_policy_hash": PURGE_POLICY_HASH,
                "response_policy_hash": FROZEN_RESPONSE_POLICY_HASH,
                "transition_policy_hash": TERMINAL_TRANSITION_POLICY_HASH,
                "v4_terminal_state_provenance_hash": v4_target_state.terminal_state_provenance_hash,
            }
        )
        return _abstain_result_v1(
            envelope=envelope,
            opportunity=opportunity,
            rule=rule,
            frame_hash=frame_hash,
            bundle_hash=bundle_hash,
            numeric_references=numeric_references,
            reason="incomplete_target_response_window",
            source_qualification_identity=source_qualification_identity,
            target_evaluation_identity=target_abstention_identity,
        )

    noise = strict_float_v1(
        resolver.relation_value(
            opportunity.relation_binding_hash,
            TARGET_NOISE_ROLE,
            noise_reference,
        ),
        "target noise scale",
        positive=True,
    )
    baseline_level = float(statistics.median(target_baseline))
    response_delta = float(statistics.median(target_response)) - baseline_level
    response_matched = (
        response_delta > noise
        if opportunity.target_direction == "increase"
        else response_delta < -noise
    )
    strict_bool_v1(response_matched, "response matched")
    final_state = EXPECTED_RESPONSE_STATE if response_matched else ANOMALY_STATE
    alarm_emitted = not response_matched

    v4_target_state = transition_target_evaluation_v4(
        opportunity,
        v4_source_state,
        bundle.v4_authority,
        target_window_input_identity=target_window_input_identity,
        within_split=True,
        target_context_available=True,
        response_matched=response_matched,
    )
    validate_target_evaluation_state_v4(
        v4_target_state,
        opportunity,
        v4_source_state,
        bundle.v4_authority,
    )
    if (
        v4_target_state.target_evaluation_state != final_state
        or v4_target_state.alarm_emitted is not alarm_emitted
    ):
        _fail("RULE_V4_TARGET_TRANSITION_REPLAY")

    target_evaluation_identity = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_utility_evaluator_v1_target_evaluation",
            "decision_physical_row_index": decision_index,
            "evaluator_computation_identity": computation_identity,
            "expected_target_direction": opportunity.target_direction,
            "final_state": final_state,
            "numeric_authority_descriptor_hash": opportunity.numeric_authority_descriptor_hash,
            "opportunity_id": opportunity.opportunity_id,
            "rule_descriptor_hash": rule.descriptor_hash,
            "selected_horizon_seconds": opportunity.selected_horizon_seconds,
            "source_qualification_identity": source_qualification_identity,
            "target_noise_reference_identity": noise_reference,
            "target_window_input_identity": target_window_input_identity,
            "boundary_window_policy_hash": BOUNDARY_WINDOW_POLICY_HASH,
            "purge_policy_hash": PURGE_POLICY_HASH,
            "response_policy_hash": FROZEN_RESPONSE_POLICY_HASH,
            "transition_policy_hash": TERMINAL_TRANSITION_POLICY_HASH,
            "v4_terminal_state_provenance_hash": v4_target_state.terminal_state_provenance_hash,
        }
    )
    trace_payload = {
        "artifact_type": "task039e3_r2r_utility_evaluator_v1_rule_execution_trace",
        "abstention_reason": None,
        "alarm_emitted": alarm_emitted,
        "authority_bundle_hash": bundle_hash,
        "decision_physical_row_index": decision_index,
        "evaluator_computation_identity": computation_identity,
        "execution_mode": SYNTHETIC_CONTRACT_ONLY,
        "expected_direction": opportunity.target_direction,
        "final_state": final_state,
        "numeric_reference_identities": list(numeric_references),
        "opportunity_id": opportunity.opportunity_id,
        "relation_binding_hash": opportunity.relation_binding_hash,
        "rule_descriptor_hash": rule.descriptor_hash,
        "selected_horizon_seconds": opportunity.selected_horizon_seconds,
        "source_event_identity": envelope.isolated_source_event_identity,
        "source_qualification_identity": source_qualification_identity,
        "target_evaluation_identity": target_evaluation_identity,
    }
    return RuleExecutionResultV1(
        execution_mode=SYNTHETIC_CONTRACT_ONLY,
        opportunity_id=opportunity.opportunity_id,
        source_event_identity=envelope.isolated_source_event_identity,
        relation_binding_hash=opportunity.relation_binding_hash,
        source_qualification_identity=source_qualification_identity,
        target_evaluation_identity=target_evaluation_identity,
        final_state=final_state,
        alarm_emitted=alarm_emitted,
        decision_physical_row_index=decision_index,
        numeric_reference_identities=numeric_references,
        evaluator_computation_identity=computation_identity,
        trace_hash=stable_hash_v1(trace_payload),
    )


def validate_rule_execution_result_v1(
    result: RuleExecutionResultV1,
    envelope: CanonicalOpportunityEnvelopeV1,
    census: FullCensusResultV1,
    frame: SyntheticFeatureFrameV1,
    bundle: EvaluatorAuthorityBundleV1,
    resolver: SyntheticNumericResolverV1,
) -> str:
    """Replay the complete synthetic computation and reject every mutation."""

    if type(result) is not RuleExecutionResultV1:
        _fail("RULE_EXECUTION_RESULT_TYPE")
    expected = execute_rule_v1(envelope, census, frame, bundle, resolver)
    if result != expected:
        _fail("RULE_EXECUTION_RESULT_REPLAY")
    strict_sha256_v1(result.trace_hash, "trace_hash")
    return result.trace_hash


__all__ = [
    "SOURCE_THRESHOLD_ROLE",
    "SOURCE_STABILITY_ROLE",
    "TARGET_NOISE_ROLE",
    "EXPECTED_RESPONSE_STATE",
    "ANOMALY_STATE",
    "ABSTAIN_STATE",
    "execute_rule_v1",
    "validate_rule_execution_result_v1",
]
