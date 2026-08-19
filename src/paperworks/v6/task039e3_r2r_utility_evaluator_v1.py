"""Production facade for the frozen Utility Evaluator V1 implementation.

Only the explicitly segregated ``SYNTHETIC_CONTRACT_ONLY`` plane executes in
this task.  The real entry point fails before examining any locator, private
authority, HAI input, label, or detector object.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 import (
    EvaluatorAuthorityBundleV1,
    SyntheticNumericResolverV1,
    validate_evaluator_authority_bundle_v1,
    validate_synthetic_numeric_resolver_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_census_v1 import (
    enumerate_full_census_v1,
    validate_full_census_result_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_input_v1 import (
    validate_synthetic_feature_frame_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_metrics_v1 import (
    RulePredictionArtifactV1,
    build_rule_prediction_artifact_v1,
    validate_rule_prediction_artifact_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_rule_engine_v1 import (
    execute_rule_v1,
    validate_rule_execution_result_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import (
    EVALUATOR_VERSION,
    REAL_UTILITY_EXECUTION_AUTHORIZED,
    SYNTHETIC_AUTHORITY_IDENTITY,
    SYNTHETIC_CONTRACT_ONLY,
    FullCensusResultV1,
    SyntheticFeatureFrameV1,
    UtilityEvaluatorV1Error,
    dataclass_payload_v1,
    stable_hash_v1,
    strict_bool_v1,
    strict_int_v1,
    strict_sha256_v1,
    strict_str_v1,
)
from paperworks.v6.task039e3_r2r_utility_protocol_v4 import (
    CANONICAL_V4_AUTHORITY_HASH,
    UTILITY_MAIN_PORTFOLIO,
)


EVALUATOR_PRODUCTION_MODULES = (
    "task039e3_r2r_utility_evaluator_types_v1.py",
    "task039e3_r2r_utility_evaluator_authority_v1.py",
    "task039e3_r2r_utility_evaluator_input_v1.py",
    "task039e3_r2r_utility_evaluator_census_v1.py",
    "task039e3_r2r_utility_evaluator_rule_engine_v1.py",
    "task039e3_r2r_utility_evaluator_metrics_v1.py",
    "task039e3_r2r_utility_evaluator_v1.py",
)


@dataclass(frozen=True)
class EvaluatorImplementationAuthorityV1:
    evaluator_version: str
    evaluator_authority_bundle_hash: str
    v4_authority_hash: str
    utility_portfolio: str
    execution_mode: str
    synthetic_authority_identity: str
    production_modules: tuple[str, ...]
    real_utility_execution_authorized: bool
    implementation_identity: str


def _implementation_payload(value: EvaluatorImplementationAuthorityV1) -> dict[str, object]:
    return dataclass_payload_v1(value, exclude=("implementation_identity",))


def build_evaluator_implementation_authority_v1(
    bundle: EvaluatorAuthorityBundleV1,
) -> EvaluatorImplementationAuthorityV1:
    bundle_hash = validate_evaluator_authority_bundle_v1(bundle)
    provisional = EvaluatorImplementationAuthorityV1(
        EVALUATOR_VERSION,
        bundle_hash,
        CANONICAL_V4_AUTHORITY_HASH,
        UTILITY_MAIN_PORTFOLIO,
        SYNTHETIC_CONTRACT_ONLY,
        SYNTHETIC_AUTHORITY_IDENTITY,
        EVALUATOR_PRODUCTION_MODULES,
        False,
        "",
    )
    return replace(
        provisional,
        implementation_identity=stable_hash_v1(_implementation_payload(provisional)),
    )


def validate_evaluator_implementation_authority_v1(
    authority: EvaluatorImplementationAuthorityV1,
    bundle: EvaluatorAuthorityBundleV1,
) -> str:
    if type(authority) is not EvaluatorImplementationAuthorityV1:
        raise UtilityEvaluatorV1Error("EVALUATOR_IMPLEMENTATION_AUTHORITY_TYPE_REJECTED")
    expected = build_evaluator_implementation_authority_v1(bundle)
    if authority != expected:
        raise UtilityEvaluatorV1Error("EVALUATOR_IMPLEMENTATION_AUTHORITY_REPLAY_REJECTED")
    strict_sha256_v1(authority.implementation_identity, "implementation identity")
    strict_bool_v1(
        authority.real_utility_execution_authorized,
        "real utility execution authorized",
    )
    return authority.implementation_identity


@dataclass(frozen=True)
class SyntheticEvaluatorRunV1:
    execution_mode: str
    scientific_eligible: bool
    evaluator_implementation_identity: str
    evaluator_authority_bundle_hash: str
    frame_hash: str
    census: FullCensusResultV1
    rule_prediction_artifact: RulePredictionArtifactV1
    source_event_count: int
    isolated_source_event_count: int
    relation_opportunity_count: int
    rule_evaluated_count: int
    authorized_abstain_count: int
    error_count: int
    run_hash: str


def _run_payload(value: SyntheticEvaluatorRunV1) -> dict[str, object]:
    return dataclass_payload_v1(value, exclude=("run_hash",))


def run_synthetic_utility_evaluator_v1(
    *,
    authority: EvaluatorImplementationAuthorityV1,
    bundle: EvaluatorAuthorityBundleV1,
    resolver: SyntheticNumericResolverV1,
    frame: SyntheticFeatureFrameV1,
) -> SyntheticEvaluatorRunV1:
    implementation_identity = validate_evaluator_implementation_authority_v1(
        authority, bundle
    )
    bundle_hash = validate_evaluator_authority_bundle_v1(bundle)
    validate_synthetic_numeric_resolver_v1(resolver, bundle)
    frame_hash = validate_synthetic_feature_frame_v1(frame, bundle)
    census = enumerate_full_census_v1(frame, bundle, resolver)
    validate_full_census_result_v1(census, frame, bundle, resolver)
    results = tuple(
        execute_rule_v1(envelope, census, frame, bundle, resolver)
        for envelope in census.relation_opportunities
    )
    for result, envelope in zip(results, census.relation_opportunities, strict=True):
        validate_rule_execution_result_v1(
            result, envelope, census, frame, bundle, resolver
        )
    prediction = build_rule_prediction_artifact_v1(
        evaluator_implementation_identity=implementation_identity,
        bundle=bundle,
        frame=frame,
        census=census,
        resolver=resolver,
        predictions=results,
    )
    validate_rule_prediction_artifact_v1(prediction)
    provisional = SyntheticEvaluatorRunV1(
        SYNTHETIC_CONTRACT_ONLY,
        False,
        implementation_identity,
        bundle_hash,
        frame_hash,
        census,
        prediction,
        census.retained_source_event_count,
        census.isolated_source_event_count,
        len(census.relation_opportunities),
        prediction.evaluated_count,
        prediction.abstain_count,
        prediction.error_count,
        "",
    )
    return replace(provisional, run_hash=stable_hash_v1(_run_payload(provisional)))


def validate_synthetic_evaluator_run_v1(
    run: SyntheticEvaluatorRunV1,
    *,
    authority: EvaluatorImplementationAuthorityV1,
    bundle: EvaluatorAuthorityBundleV1,
    resolver: SyntheticNumericResolverV1,
    frame: SyntheticFeatureFrameV1,
) -> str:
    if type(run) is not SyntheticEvaluatorRunV1:
        raise UtilityEvaluatorV1Error("EVALUATOR_RUN_TYPE_REJECTED")
    expected = run_synthetic_utility_evaluator_v1(
        authority=authority,
        bundle=bundle,
        resolver=resolver,
        frame=frame,
    )
    if run != expected:
        raise UtilityEvaluatorV1Error("EVALUATOR_RUN_REPLAY_REJECTED")
    for name in (
        "source_event_count",
        "isolated_source_event_count",
        "relation_opportunity_count",
        "rule_evaluated_count",
        "authorized_abstain_count",
        "error_count",
    ):
        strict_int_v1(getattr(run, name), name, minimum=0)
    strict_sha256_v1(run.run_hash, "run hash")
    return run.run_hash


def run_real_utility_evaluator_v1(
    *,
    execution_authorization: object,
    main_locator: object,
    supplement_locator: object,
    hai_input: object,
    labels: object,
) -> None:
    """Fail before inspecting any real/private object in this implementation task."""

    del execution_authorization, main_locator, supplement_locator, hai_input, labels
    if REAL_UTILITY_EXECUTION_AUTHORIZED:
        raise UtilityEvaluatorV1Error("REAL_UTILITY_EXECUTION_IMPLEMENTATION_UNAVAILABLE")
    raise UtilityEvaluatorV1Error("REAL_UTILITY_EXECUTION_NOT_AUTHORIZED")


def evaluator_claim_boundary_v1() -> dict[str, object]:
    return {
        "evaluator_version": EVALUATOR_VERSION,
        "implementation_ready_for_independent_audit": True,
        "real_utility_status": "NOT_EXECUTED",
        "real_utility_execution_authorized": False,
        "inner_execution_authorization_ready": False,
        "outer_execution_authorization_ready": False,
        "scientific_claims_authorized": False,
    }


__all__ = [
    "EVALUATOR_PRODUCTION_MODULES",
    "EvaluatorImplementationAuthorityV1",
    "SyntheticEvaluatorRunV1",
    "build_evaluator_implementation_authority_v1",
    "validate_evaluator_implementation_authority_v1",
    "run_synthetic_utility_evaluator_v1",
    "validate_synthetic_evaluator_run_v1",
    "run_real_utility_evaluator_v1",
    "evaluator_claim_boundary_v1",
]
