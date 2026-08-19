"""Exact synthetic source-event and COMMON-42 opportunity census.

This module reuses the frozen V3 threshold, stability, refractory, and tie
semantics.  It adds the audited 12-source numeric coverage contract and keeps
the three supplement-only sources in isolation while never extending the
COMMON-42 relation portfolio.
"""

from __future__ import annotations

import statistics
from paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 import (
    EvaluatorAuthorityBundleV1,
    SyntheticNumericResolverV1,
    validate_evaluator_authority_bundle_v1,
    validate_synthetic_numeric_resolver_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_input_v1 import (
    feature_series_v1,
    validate_synthetic_feature_frame_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import (
    CanonicalOpportunityEnvelopeV1,
    FullCensusResultV1,
    IsolatedSourceEventV1,
    RetainedSourceEventV1,
    SYNTHETIC_CONTRACT_ONLY,
    SyntheticFeatureFrameV1,
    UtilityEvaluatorV1Error,
    dataclass_payload_v1,
    stable_hash_v1,
    strict_float_v1,
    strict_sha256_v1,
)
from paperworks.v6.task039e3_r2r_utility_protocol_v3 import (
    CROSS_SOURCE_ISOLATION_RADIUS_SECONDS,
    MINIMUM_STABILITY_FRACTION,
    SOURCE_POST_WINDOW,
    SOURCE_PRE_WINDOW,
    UTILITY_SOURCE_UNIVERSE_V3,
    derive_retained_source_events_v3,
)
from paperworks.v6.task039e3_r2r_utility_protocol_v4 import (
    CANONICAL_V4_AUTHORITY_HASH,
    build_canonical_opportunity_v4,
    build_canonical_row_time_identity_v4,
    validate_canonical_opportunity_v4,
    validate_utility_protocol_v4_authority,
)


COMBINED_SOURCE_CENSUS_CONTRACT_HASH = (
    "cb53d0e4533ebadb61edbdc72b549fe47b46c8dcc4621841aac93a007660ced9"
)
SOURCE_CENSUS_EVENT_POLICY_HASH = (
    "3fb20068feff44632be3e4e6917183d52fea5616feec68ede5e9b62f95ecb390"
)
CROSS_SOURCE_ISOLATION_POLICY_HASH = (
    "f62075523632a7573d28e95ca7f0402d87e62977f4a2f14f4eaf2b9a58f0e280"
)
FULL_CENSUS_DENOMINATOR_POLICY = (
    "ALL_AUTOMATICALLY_ENUMERATED_APPLICABLE_CANONICAL_OPPORTUNITIES"
)
SOURCE_CENSUS_ROLES = (
    "source_step_threshold",
    "source_stability_tolerance",
)


def _validate_census_authority_bundle(
    authority_bundle: EvaluatorAuthorityBundleV1,
) -> None:
    try:
        validate_evaluator_authority_bundle_v1(authority_bundle)
        observed = validate_utility_protocol_v4_authority(authority_bundle.v4_authority)
    except Exception as error:
        raise UtilityEvaluatorV1Error("CENSUS_V4_AUTHORITY_INVALID") from error
    if observed != CANONICAL_V4_AUTHORITY_HASH:
        raise UtilityEvaluatorV1Error("CENSUS_V4_AUTHORITY_NOT_CURRENT")
    expected = (
        ("combined_source_census_contract_hash", COMBINED_SOURCE_CENSUS_CONTRACT_HASH),
        ("source_census_event_policy_hash", SOURCE_CENSUS_EVENT_POLICY_HASH),
        ("cross_source_isolation_policy_hash", CROSS_SOURCE_ISOLATION_POLICY_HASH),
    )
    for name, value in expected:
        if getattr(authority_bundle, name, None) != value:
            raise UtilityEvaluatorV1Error(f"CENSUS_AUTHORITY_BINDING_INVALID_{name.upper()}")


def _resolver_values(
    resolver: SyntheticNumericResolverV1,
    authority_bundle: EvaluatorAuthorityBundleV1,
) -> tuple[dict[str, float], dict[str, float]]:
    try:
        validate_synthetic_numeric_resolver_v1(resolver, authority_bundle)
    except Exception as error:
        raise UtilityEvaluatorV1Error("SOURCE_CENSUS_RESOLVER_NOT_VALIDATED") from error
    if type(resolver.validated) is not bool or resolver.validated is not True:
        raise UtilityEvaluatorV1Error("SOURCE_CENSUS_RESOLVER_NOT_VALIDATED")
    thresholds: dict[str, float] = {}
    tolerances: dict[str, float] = {}
    for source in UTILITY_SOURCE_UNIVERSE_V3:
        try:
            thresholds[source] = strict_float_v1(
                resolver.source_census_value(source, SOURCE_CENSUS_ROLES[0]),
                f"source_step_threshold[{source}]",
                positive=True,
            )
            tolerances[source] = strict_float_v1(
                resolver.source_census_value(source, SOURCE_CENSUS_ROLES[1]),
                f"source_stability_tolerance[{source}]",
                nonnegative=True,
            )
        except UtilityEvaluatorV1Error:
            raise
        except Exception as error:
            raise UtilityEvaluatorV1Error("SOURCE_CENSUS_NUMERIC_RESOLUTION_FAILED") from error
    return thresholds, tolerances


def _raw_candidate_count(
    source_series: dict[str, tuple[float, ...]],
    thresholds: dict[str, float],
    tolerances: dict[str, float],
) -> int:
    """Replay the frozen pre-clustering candidate predicate for audit counts."""

    count = 0
    for source in UTILITY_SOURCE_UNIVERSE_V3:
        series = source_series[source]
        threshold = thresholds[source]
        tolerance = tolerances[source]
        for index in range(SOURCE_PRE_WINDOW, len(series) - SOURCE_POST_WINDOW + 1):
            pre = series[index - SOURCE_PRE_WINDOW:index]
            post = series[index:index + SOURCE_POST_WINDOW]
            pre_level = float(statistics.median(pre))
            post_level = float(statistics.median(post))
            amplitude = post_level - pre_level
            pre_fraction = sum(abs(value - pre_level) <= tolerance for value in pre) / SOURCE_PRE_WINDOW
            post_fraction = sum(abs(value - post_level) <= tolerance for value in post) / SOURCE_POST_WINDOW
            if (
                amplitude != 0.0
                and abs(amplitude) >= threshold
                and pre_fraction >= MINIMUM_STABILITY_FRACTION
                and post_fraction >= MINIMUM_STABILITY_FRACTION
            ):
                count += 1
    return count


def _source_event_payload(
    *,
    frame_hash: str,
    row_identity: str,
    source: str,
    physical_row_index: int,
    direction: str,
    amplitude: float,
) -> dict[str, object]:
    return {
        "amplitude": amplitude,
        "artifact_type": "task039e3_r2r_utility_evaluator_v1_synthetic_retained_source_event",
        "execution_mode": SYNTHETIC_CONTRACT_ONLY,
        "frame_hash": frame_hash,
        "physical_row_index": physical_row_index,
        "row_identity": row_identity,
        "source": source,
        "source_census_event_policy_hash": SOURCE_CENSUS_EVENT_POLICY_HASH,
        "source_direction": direction,
    }


def _isolation_payload(
    event: RetainedSourceEventV1,
    source_census_identity: str,
) -> dict[str, object]:
    return {
        "artifact_type": "task039e3_r2r_utility_evaluator_v1_synthetic_isolated_source_event",
        "cross_source_isolation_policy_hash": CROSS_SOURCE_ISOLATION_POLICY_HASH,
        "execution_mode": SYNTHETIC_CONTRACT_ONLY,
        "retained_source_event_identity": event.source_event_identity,
        "source_census_identity": source_census_identity,
    }


def _envelope_payload(envelope: CanonicalOpportunityEnvelopeV1) -> dict[str, object]:
    opportunity = envelope.canonical_opportunity
    return {
        "artifact_type": "task039e3_r2r_utility_evaluator_v1_canonical_opportunity_envelope",
        "execution_mode": SYNTHETIC_CONTRACT_ONLY,
        "isolated_source_event_identity": envelope.isolated_source_event_identity,
        "opportunity_id": getattr(opportunity, "opportunity_id", None),
    }


def _census_payload(result: FullCensusResultV1) -> dict[str, object]:
    return {
        "artifact_type": "task039e3_r2r_utility_evaluator_v1_synthetic_full_census",
        "denominator_policy": result.denominator_policy,
        "execution_mode": result.execution_mode,
        "isolated_source_event_count": result.isolated_source_event_count,
        "opportunity_envelope_hashes": [
            item.envelope_hash for item in result.relation_opportunities
        ],
        "raw_source_event_count": result.raw_source_event_count,
        "relation_opportunity_count": len(result.relation_opportunities),
        "retained_source_event_count": result.retained_source_event_count,
        "source_census_identity": result.source_census_identity,
    }


def _build_full_census(
    frame: SyntheticFeatureFrameV1,
    authority_bundle: EvaluatorAuthorityBundleV1,
    resolver: SyntheticNumericResolverV1,
) -> FullCensusResultV1:
    _validate_census_authority_bundle(authority_bundle)
    validate_synthetic_feature_frame_v1(frame, authority_bundle)
    thresholds, tolerances = _resolver_values(resolver, authority_bundle)
    source_series = {
        source: feature_series_v1(frame, authority_bundle, source)
        for source in UTILITY_SOURCE_UNIVERSE_V3
    }
    try:
        retained_v3 = derive_retained_source_events_v3(
            source_series,
            thresholds,
            tolerances,
        )
    except Exception as error:
        raise UtilityEvaluatorV1Error("SOURCE_CENSUS_DERIVATION_FAILED") from error
    first_physical = frame.rows[0].physical_row_index
    row_by_physical = {row.physical_row_index: row for row in frame.rows}
    retained: dict[str, tuple[RetainedSourceEventV1, ...]] = {}
    for source in UTILITY_SOURCE_UNIVERSE_V3:
        records = []
        for event in retained_v3[source]:
            physical = first_physical + event.physical_index
            row = row_by_physical[physical]
            payload = _source_event_payload(
                frame_hash=frame.frame_hash,
                row_identity=row.row_identity,
                source=source,
                physical_row_index=physical,
                direction=event.direction,
                amplitude=event.amplitude,
            )
            records.append(
                RetainedSourceEventV1(
                    source,
                    physical,
                    event.direction,
                    event.amplitude,
                    stable_hash_v1(payload),
                )
            )
        retained[source] = tuple(records)
    source_census_identity = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_utility_evaluator_v1_retained_source_census",
            "combined_source_census_contract_hash": COMBINED_SOURCE_CENSUS_CONTRACT_HASH,
            "frame_hash": frame.frame_hash,
            "retained_event_identities": {
                source: [item.source_event_identity for item in retained[source]]
                for source in UTILITY_SOURCE_UNIVERSE_V3
            },
            "source_census_event_policy_hash": SOURCE_CENSUS_EVENT_POLICY_HASH,
            "source_universe": list(UTILITY_SOURCE_UNIVERSE_V3),
        }
    )
    isolated = []
    for source in UTILITY_SOURCE_UNIVERSE_V3:
        for event in retained[source]:
            conflicts = any(
                abs(event.physical_row_index - other.physical_row_index)
                <= CROSS_SOURCE_ISOLATION_RADIUS_SECONDS
                for other_source in UTILITY_SOURCE_UNIVERSE_V3
                if other_source != source
                for other in retained[other_source]
            )
            if conflicts:
                continue
            isolated.append(
                IsolatedSourceEventV1(
                    event,
                    source_census_identity,
                    CROSS_SOURCE_ISOLATION_POLICY_HASH,
                    stable_hash_v1(_isolation_payload(event, source_census_identity)),
                )
            )
    isolated.sort(key=lambda item: (item.retained_event.physical_row_index, item.retained_event.source))
    envelopes = []
    rules_by_source_direction: dict[tuple[str, str], list[object]] = {}
    for rule in authority_bundle.v4_authority.rule_descriptors:
        rules_by_source_direction.setdefault((rule.source, rule.source_direction), []).append(rule)
    for event in isolated:
        retained_event = event.retained_event
        for rule in sorted(
            rules_by_source_direction.get((retained_event.source, retained_event.direction), ()),
            key=lambda item: item.relation_binding_hash,
        ):
            row_time = build_canonical_row_time_identity_v4(
                source_file_identity=frame.source_file_identity,
                physical_row_index=retained_event.physical_row_index,
            )
            opportunity = build_canonical_opportunity_v4(
                authority_bundle.v4_authority,
                relation_binding_hash=rule.relation_binding_hash,
                row_time=row_time,
            )
            provisional = CanonicalOpportunityEnvelopeV1(
                event.isolated_event_identity,
                opportunity,
                "",
            )
            envelopes.append(
                CanonicalOpportunityEnvelopeV1(
                    provisional.isolated_source_event_identity,
                    provisional.canonical_opportunity,
                    stable_hash_v1(_envelope_payload(provisional)),
                )
            )
    envelopes.sort(
        key=lambda item: (
            item.canonical_opportunity.physical_row_index,
            item.canonical_opportunity.relation_binding_hash,
            item.canonical_opportunity.opportunity_id,
        )
    )
    provisional_result = FullCensusResultV1(
        SYNTHETIC_CONTRACT_ONLY,
        source_census_identity,
        _raw_candidate_count(source_series, thresholds, tolerances),
        sum(len(items) for items in retained.values()),
        len(isolated),
        tuple(envelopes),
        FULL_CENSUS_DENOMINATOR_POLICY,
        "",
    )
    return FullCensusResultV1(
        provisional_result.execution_mode,
        provisional_result.source_census_identity,
        provisional_result.raw_source_event_count,
        provisional_result.retained_source_event_count,
        provisional_result.isolated_source_event_count,
        provisional_result.relation_opportunities,
        provisional_result.denominator_policy,
        stable_hash_v1(_census_payload(provisional_result)),
    )


def enumerate_full_census_v1(
    frame: SyntheticFeatureFrameV1,
    authority_bundle: EvaluatorAuthorityBundleV1,
    resolver: SyntheticNumericResolverV1,
) -> FullCensusResultV1:
    """Enumerate the complete canonical census with no caller control knobs."""

    return _build_full_census(frame, authority_bundle, resolver)


def validate_full_census_result_v1(
    result: FullCensusResultV1,
    frame: SyntheticFeatureFrameV1,
    authority_bundle: EvaluatorAuthorityBundleV1,
    resolver: SyntheticNumericResolverV1,
) -> str:
    if type(result) is not FullCensusResultV1:
        raise UtilityEvaluatorV1Error("FULL_CENSUS_RESULT_TYPE_INVALID")
    expected = _build_full_census(frame, authority_bundle, resolver)
    if result != expected:
        raise UtilityEvaluatorV1Error("FULL_CENSUS_REPLAY_MISMATCH")
    return result.census_hash


def validate_opportunity_envelope_v1(
    envelope: CanonicalOpportunityEnvelopeV1,
    census: FullCensusResultV1,
    frame: SyntheticFeatureFrameV1,
    authority_bundle: EvaluatorAuthorityBundleV1,
    resolver: SyntheticNumericResolverV1,
) -> str:
    """Validate an envelope only as a member of a fully replayed census."""

    validate_full_census_result_v1(census, frame, authority_bundle, resolver)
    if type(envelope) is not CanonicalOpportunityEnvelopeV1:
        raise UtilityEvaluatorV1Error("OPPORTUNITY_ENVELOPE_TYPE_INVALID")
    if not any(envelope == item for item in census.relation_opportunities):
        raise UtilityEvaluatorV1Error("OPPORTUNITY_NOT_IN_CANONICAL_FULL_CENSUS")
    strict_sha256_v1(
        envelope.isolated_source_event_identity,
        "isolated_source_event_identity",
    )
    try:
        validate_canonical_opportunity_v4(
            envelope.canonical_opportunity,
            authority_bundle.v4_authority,
        )
    except Exception as error:
        raise UtilityEvaluatorV1Error("CANONICAL_OPPORTUNITY_INVALID") from error
    if envelope.envelope_hash != stable_hash_v1(_envelope_payload(envelope)):
        raise UtilityEvaluatorV1Error("OPPORTUNITY_ENVELOPE_HASH_INVALID")
    return envelope.envelope_hash


__all__ = [
    "COMBINED_SOURCE_CENSUS_CONTRACT_HASH",
    "SOURCE_CENSUS_EVENT_POLICY_HASH",
    "CROSS_SOURCE_ISOLATION_POLICY_HASH",
    "FULL_CENSUS_DENOMINATOR_POLICY",
    "SOURCE_CENSUS_ROLES",
    "SyntheticNumericResolverV1",
    "enumerate_full_census_v1",
    "validate_full_census_result_v1",
    "validate_opportunity_envelope_v1",
]
