"""Clearly synthetic factories for TASK-039E1-PREP tests."""

from __future__ import annotations

from typing import Any

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e0_rule_construction_prep_v1 import (
    ConfirmedRelationPrimitiveV1,
)
from paperworks.v6.task039e1_evidence_materialization_prep_v1 import (
    ConstructionEvidenceMaterializationInputV1,
    ConstructionNumericRoleV1,
    PreregisteredWindowConstantBundleV1,
    PublicEvidenceDisclosurePolicyV1,
    SyntheticD1DirectionalFitSupportedRecordV1,
    SyntheticD1SourceParameterRecordV1,
    SyntheticD1TargetParameterRecordV1,
    SyntheticD2ConfirmationRecordV1,
    derive_synthetic_numeric_bindings_v1,
)


def synthetic_e1_digest(label: str) -> str:
    return stable_hash_v1({"synthetic_task039e1_fixture": label})


def synthetic_source_parameter(
    **overrides: Any,
) -> SyntheticD1SourceParameterRecordV1:
    values: dict[str, Any] = {
        "source": "SYNTHETIC_ACTUATOR_A",
        "source_noise_scale": 0.123,
        "source_step_threshold": 7.321,
        "source_stability_tolerance": 0.456,
        "parameter_status": "supported",
        "fit_ledger_binding_hash": synthetic_e1_digest(
            "fake-d1-source-ledger-binding"
        ),
    }
    values.update(overrides)
    return SyntheticD1SourceParameterRecordV1(**values)


def synthetic_target_parameter(
    **overrides: Any,
) -> SyntheticD1TargetParameterRecordV1:
    values: dict[str, Any] = {
        "target": "SYNTHETIC_SENSOR_B",
        "target_noise_scale": 0.789,
        "parameter_status": "supported",
        "fit_ledger_binding_hash": synthetic_e1_digest(
            "fake-d1-target-ledger-binding"
        ),
    }
    values.update(overrides)
    return SyntheticD1TargetParameterRecordV1(**values)


def synthetic_d1_fit_record(
    *,
    source_parameter: SyntheticD1SourceParameterRecordV1 | None = None,
    target_parameter: SyntheticD1TargetParameterRecordV1 | None = None,
    **overrides: Any,
) -> SyntheticD1DirectionalFitSupportedRecordV1:
    source = source_parameter or synthetic_source_parameter()
    target = target_parameter or synthetic_target_parameter()
    values: dict[str, Any] = {
        "source": source.source,
        "target": target.target,
        "source_step_direction": "step_up",
        "selected_target_direction": "increase",
        "selected_horizon_seconds": 13,
        "source_parameter_record_hash": source.artifact_hash,
        "target_parameter_record_hash": target.artifact_hash,
    }
    values.update(overrides)
    return SyntheticD1DirectionalFitSupportedRecordV1(**values)


def synthetic_d2_confirmation_record(
    *,
    d1_fit_record: SyntheticD1DirectionalFitSupportedRecordV1 | None = None,
    **overrides: Any,
) -> SyntheticD2ConfirmationRecordV1:
    d1 = d1_fit_record or synthetic_d1_fit_record()
    values: dict[str, Any] = {
        "source": d1.source,
        "target": d1.target,
        "source_step_direction": d1.source_step_direction,
        "target_response_direction": d1.selected_target_direction,
        "selected_horizon_seconds": d1.selected_horizon_seconds,
        "source_parameter_record_hash": d1.source_parameter_record_hash,
        "target_parameter_record_hash": d1.target_parameter_record_hash,
        "d1_directional_record_hash": d1.artifact_hash,
        "confirmation_status": "calibration_confirmed",
    }
    values.update(overrides)
    return SyntheticD2ConfirmationRecordV1(**values)


def synthetic_window_constants(
    **overrides: Any,
) -> PreregisteredWindowConstantBundleV1:
    values: dict[str, Any] = {
        "bundle_identity": "SYNTHETIC_D0_WINDOW_CONSTANTS_V1",
        "d0_protocol_bundle_hash": synthetic_e1_digest(
            "fake-d0-protocol-bundle"
        ),
        "source_event_policy_hash": synthetic_e1_digest(
            "fake-d0-source-event-policy"
        ),
        "target_response_policy_hash": synthetic_e1_digest(
            "fake-d0-target-response-policy"
        ),
        "confirmation_policy_hash": synthetic_e1_digest(
            "fake-d0-confirmation-policy"
        ),
        "source_pre_window_seconds": 4,
        "source_post_window_seconds": 6,
        "minimum_source_stability_fraction": 0.73,
        "source_refractory_seconds": 9,
        "cross_source_isolation_radius_seconds": 3,
        "target_baseline_window_seconds": 4,
        "target_response_window_seconds": 2,
    }
    values.update(overrides)
    return PreregisteredWindowConstantBundleV1(**values)


def synthetic_disclosure_policy(
    **overrides: Any,
) -> PublicEvidenceDisclosurePolicyV1:
    values: dict[str, Any] = {
        "policy_identity": "SYNTHETIC_PUBLIC_DISCLOSURE_POLICY_V1",
        "selected_horizon_public": True,
    }
    values.update(overrides)
    return PublicEvidenceDisclosurePolicyV1(**values)


def synthetic_materialization_input() -> ConstructionEvidenceMaterializationInputV1:
    source = synthetic_source_parameter()
    target = synthetic_target_parameter()
    d1 = synthetic_d1_fit_record(
        source_parameter=source, target_parameter=target
    )
    d2 = synthetic_d2_confirmation_record(d1_fit_record=d1)
    windows = synthetic_window_constants()
    bindings = derive_synthetic_numeric_bindings_v1(
        source_parameter=source,
        target_parameter=target,
        d1_fit_record=d1,
        d2_confirmation_record=d2,
        window_constants=windows,
    )
    by_role = {item.numeric_role: item for item in bindings}
    relation = ConfirmedRelationPrimitiveV1(
        relation_identity="SYNTHETIC_RELATION_001",
        source=source.source,
        source_step_direction=d1.source_step_direction,
        target=target.target,
        target_response_direction=d1.selected_target_direction,
        selected_delay_horizon_seconds=d1.selected_horizon_seconds,
        approved_source_threshold_reference=by_role[
            ConstructionNumericRoleV1.SOURCE_STEP_THRESHOLD.value
        ].numeric_reference,
        approved_source_stability_reference=by_role[
            ConstructionNumericRoleV1.SOURCE_STABILITY_TOLERANCE.value
        ].numeric_reference,
        approved_target_scale_reference=by_role[
            ConstructionNumericRoleV1.TARGET_NOISE_SCALE.value
        ].numeric_reference,
        fit_evidence_reference=d1.artifact_hash,
        confirmation_evidence_reference=d2.artifact_hash,
    )
    return ConstructionEvidenceMaterializationInputV1(
        relation=relation,
        source_parameter=source,
        target_parameter=target,
        d1_fit_record=d1,
        d2_confirmation_record=d2,
        window_constants=windows,
        disclosure_policy=synthetic_disclosure_policy(),
    )


def materialize_input(item: ConstructionEvidenceMaterializationInputV1):
    from paperworks.v6.task039e1_evidence_materialization_prep_v1 import (
        materialize_construction_evidence_v1,
    )

    return materialize_construction_evidence_v1(
        item.relation,
        item.source_parameter,
        item.target_parameter,
        item.d1_fit_record,
        item.d2_confirmation_record,
        item.window_constants,
        item.disclosure_policy,
    )


__all__ = [
    "materialize_input",
    "synthetic_d1_fit_record",
    "synthetic_d2_confirmation_record",
    "synthetic_disclosure_policy",
    "synthetic_e1_digest",
    "synthetic_materialization_input",
    "synthetic_source_parameter",
    "synthetic_target_parameter",
    "synthetic_window_constants",
]
