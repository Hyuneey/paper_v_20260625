"""Synthetic-only TASK-039E1 construction-evidence materialization.

This module models future private D1/D2 record shapes and deterministically
materializes reference-bound construction evidence. Every accepted identity
must be visibly synthetic. No file, provider, Agent, rule, or runtime path is
available here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Sequence

from paperworks.v6.common import (
    V6_FOUNDATION_SCHEMA_VERSION,
    V6FoundationError,
    require_finite,
    require_identifier,
    require_sha256,
    stable_hash_v1,
)
from paperworks.v6.task039e0_rule_construction_prep_v1 import (
    ApprovedNumericEvidenceBundleV1,
    ConfirmedRelationPrimitiveV1,
)


TASK_ID = "TASK-039E1-PREP"
BASE_COMMIT = "239c6bf8cd52566f201e29cec50569a06b6fc74e"
BRANCH = "task-039e1-evidence-materialization-prep"
PREPARATION_STATUS = "passed_task039e1_evidence_materialization_preparation"

REAL_D2_RESULT_CONSUMED = False
REAL_CONFIRMED_RELATION_IDENTITY_CONSUMED = False
D1_PRIVATE_LEDGER_ACCESSED = False
D2_PRIVATE_LEDGER_ACCESSED = False
HAI_ACCESSED = False
LLM_CALLED = False
RULE_GENERATED = False
RUNTIME_AUTHORITY_GRANTED = False
E1_AUTHORIZATION_CREATED = False

SOURCE_PARAMETER_ORIGIN = "d1_fit_derived_source_parameter"
TARGET_PARAMETER_ORIGIN = "d1_fit_derived_target_parameter"
HORIZON_ORIGIN = "d1_fit_selected_horizon"
WINDOW_CONSTANT_ORIGIN = "d0_preregistered_window_constant"
APPROVED_EVIDENCE_AUTHORITY = "approved_construction_evidence"
CONSTRUCTION_EVIDENCE_STATUS = "approved"


class TASK039E1PreparationError(V6FoundationError):
    """Raised when synthetic materialization fails closed."""


def _require_synthetic_identifier(value: str, field_name: str) -> str:
    require_identifier(value, field_name)
    if not value.startswith("SYNTHETIC_"):
        raise TASK039E1PreparationError(
            f"{field_name} must use the SYNTHETIC_ prefix"
        )
    return value


def _exact_false(value: bool, field_name: str) -> None:
    if value is not False:
        raise TASK039E1PreparationError(f"{field_name} must remain false")


def _positive_number(value: int | float, field_name: str) -> float:
    result = require_finite(value, field_name)
    if result <= 0.0:
        raise TASK039E1PreparationError(f"{field_name} must be positive")
    return result


def _nonnegative_number(value: int | float, field_name: str) -> float:
    result = require_finite(value, field_name)
    if result < 0.0:
        raise TASK039E1PreparationError(
            f"{field_name} must be non-negative"
        )
    return result


def _positive_integer(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise TASK039E1PreparationError(f"{field_name} must be positive")
    return value


def _fraction(value: int | float, field_name: str) -> float:
    result = require_finite(value, field_name)
    if not 0.0 < result <= 1.0:
        raise TASK039E1PreparationError(f"{field_name} must be in (0, 1]")
    return result


class ConstructionNumericRoleV1(str, Enum):
    SOURCE_STEP_THRESHOLD = "source_step_threshold"
    SOURCE_STABILITY_TOLERANCE = "source_stability_tolerance"
    TARGET_NOISE_SCALE = "target_noise_scale"
    SELECTED_DELAY_HORIZON_SECONDS = "selected_delay_horizon_seconds"
    SOURCE_PRE_WINDOW_SECONDS = "source_pre_window_seconds"
    SOURCE_POST_WINDOW_SECONDS = "source_post_window_seconds"
    MINIMUM_SOURCE_STABILITY_FRACTION = (
        "minimum_source_stability_fraction"
    )
    SOURCE_REFRACTORY_SECONDS = "source_refractory_seconds"
    CROSS_SOURCE_ISOLATION_RADIUS_SECONDS = (
        "cross_source_isolation_radius_seconds"
    )
    TARGET_BASELINE_WINDOW_SECONDS = "target_baseline_window_seconds"
    TARGET_RESPONSE_WINDOW_SECONDS = "target_response_window_seconds"


NUMERIC_ROLE_ORDER = tuple(item.value for item in ConstructionNumericRoleV1)
WINDOW_NUMERIC_ROLES = (
    ConstructionNumericRoleV1.SOURCE_PRE_WINDOW_SECONDS.value,
    ConstructionNumericRoleV1.SOURCE_POST_WINDOW_SECONDS.value,
    ConstructionNumericRoleV1.MINIMUM_SOURCE_STABILITY_FRACTION.value,
    ConstructionNumericRoleV1.SOURCE_REFRACTORY_SECONDS.value,
    ConstructionNumericRoleV1.CROSS_SOURCE_ISOLATION_RADIUS_SECONDS.value,
    ConstructionNumericRoleV1.TARGET_BASELINE_WINDOW_SECONDS.value,
    ConstructionNumericRoleV1.TARGET_RESPONSE_WINDOW_SECONDS.value,
)


@dataclass(frozen=True)
class SyntheticD1SourceParameterRecordV1:
    """Synthetic structural counterpart of one private D1 source record."""

    source: str
    source_noise_scale: float | None
    source_step_threshold: float | None
    source_stability_tolerance: float | None
    parameter_status: str
    fit_ledger_binding_hash: str
    source_threshold_origin: str = SOURCE_PARAMETER_ORIGIN
    stability_tolerance_origin: str = SOURCE_PARAMETER_ORIGIN
    parameter_class: str = "normal_relation_profile_fit_derived"
    synthetic_fixture: bool = True
    real_record: bool = False

    def __post_init__(self) -> None:
        _require_synthetic_identifier(self.source, "source")
        require_sha256(self.fit_ledger_binding_hash, "fit_ledger_binding_hash")
        if self.parameter_status not in {"supported", "unsupported"}:
            raise TASK039E1PreparationError("source parameter status is invalid")
        if self.source_threshold_origin != SOURCE_PARAMETER_ORIGIN:
            raise TASK039E1PreparationError("source threshold origin is invalid")
        if self.stability_tolerance_origin != SOURCE_PARAMETER_ORIGIN:
            raise TASK039E1PreparationError("stability tolerance origin is invalid")
        if self.parameter_class != "normal_relation_profile_fit_derived":
            raise TASK039E1PreparationError("source parameter class is invalid")
        if self.synthetic_fixture is not True:
            raise TASK039E1PreparationError("source record must remain synthetic")
        _exact_false(self.real_record, "real_record")
        if self.parameter_status == "supported":
            if (
                self.source_noise_scale is None
                or self.source_step_threshold is None
                or self.source_stability_tolerance is None
            ):
                raise TASK039E1PreparationError(
                    "supported source parameters must be complete"
                )
            _positive_number(self.source_noise_scale, "source_noise_scale")
            _positive_number(
                self.source_step_threshold, "source_step_threshold"
            )
            _nonnegative_number(
                self.source_stability_tolerance,
                "source_stability_tolerance",
            )
        else:
            for field_name in (
                "source_noise_scale",
                "source_step_threshold",
                "source_stability_tolerance",
            ):
                value = getattr(self, field_name)
                if value is not None:
                    _nonnegative_number(value, field_name)

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "task039e1_synthetic_d1_source_parameter_record_v1",
            "source": self.source,
            "source_noise_scale": self.source_noise_scale,
            "source_step_threshold": self.source_step_threshold,
            "source_stability_tolerance": self.source_stability_tolerance,
            "parameter_status": self.parameter_status,
            "fit_ledger_binding_hash": self.fit_ledger_binding_hash,
            "source_threshold_origin": self.source_threshold_origin,
            "stability_tolerance_origin": self.stability_tolerance_origin,
            "parameter_class": self.parameter_class,
            "synthetic_fixture": self.synthetic_fixture,
            "real_record": self.real_record,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["artifact_hash"] = self.artifact_hash
        return payload


@dataclass(frozen=True)
class SyntheticD1TargetParameterRecordV1:
    """Synthetic structural counterpart of one private D1 target record."""

    target: str
    target_noise_scale: float | None
    parameter_status: str
    fit_ledger_binding_hash: str
    target_scale_origin: str = TARGET_PARAMETER_ORIGIN
    parameter_class: str = "normal_relation_profile_fit_derived"
    synthetic_fixture: bool = True
    real_record: bool = False

    def __post_init__(self) -> None:
        _require_synthetic_identifier(self.target, "target")
        require_sha256(self.fit_ledger_binding_hash, "fit_ledger_binding_hash")
        if self.parameter_status not in {"supported", "unsupported"}:
            raise TASK039E1PreparationError("target parameter status is invalid")
        if self.target_scale_origin != TARGET_PARAMETER_ORIGIN:
            raise TASK039E1PreparationError("target scale origin is invalid")
        if self.parameter_class != "normal_relation_profile_fit_derived":
            raise TASK039E1PreparationError("target parameter class is invalid")
        if self.synthetic_fixture is not True:
            raise TASK039E1PreparationError("target record must remain synthetic")
        _exact_false(self.real_record, "real_record")
        if self.parameter_status == "supported":
            if self.target_noise_scale is None:
                raise TASK039E1PreparationError(
                    "supported target scale must be present"
                )
            _positive_number(self.target_noise_scale, "target_noise_scale")
        elif self.target_noise_scale is not None:
            _nonnegative_number(self.target_noise_scale, "target_noise_scale")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "task039e1_synthetic_d1_target_parameter_record_v1",
            "target": self.target,
            "target_noise_scale": self.target_noise_scale,
            "parameter_status": self.parameter_status,
            "fit_ledger_binding_hash": self.fit_ledger_binding_hash,
            "target_scale_origin": self.target_scale_origin,
            "parameter_class": self.parameter_class,
            "synthetic_fixture": self.synthetic_fixture,
            "real_record": self.real_record,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["artifact_hash"] = self.artifact_hash
        return payload


@dataclass(frozen=True)
class SyntheticD1DirectionalFitSupportedRecordV1:
    """Synthetic structural counterpart of a fit-supported D1 direction."""

    source: str
    target: str
    source_step_direction: str
    selected_target_direction: str
    selected_horizon_seconds: int
    source_parameter_record_hash: str
    target_parameter_record_hash: str
    fit_result: str = "fit_supported"
    lower_ranked_fallback_used: bool = False
    candidate_arm_evidence_visible: bool = False
    synthetic_fixture: bool = True
    real_record: bool = False

    def __post_init__(self) -> None:
        _require_synthetic_identifier(self.source, "source")
        _require_synthetic_identifier(self.target, "target")
        if self.source == self.target:
            raise TASK039E1PreparationError("source and target must differ")
        if self.source_step_direction not in {"step_up", "step_down"}:
            raise TASK039E1PreparationError("source direction is invalid")
        if self.selected_target_direction not in {"increase", "decrease"}:
            raise TASK039E1PreparationError("target direction is invalid")
        _positive_integer(
            self.selected_horizon_seconds, "selected_horizon_seconds"
        )
        require_sha256(
            self.source_parameter_record_hash,
            "source_parameter_record_hash",
        )
        require_sha256(
            self.target_parameter_record_hash,
            "target_parameter_record_hash",
        )
        if self.fit_result != "fit_supported":
            raise TASK039E1PreparationError("D1 record must be fit-supported")
        _exact_false(self.lower_ranked_fallback_used, "lower_ranked_fallback_used")
        _exact_false(
            self.candidate_arm_evidence_visible,
            "candidate_arm_evidence_visible",
        )
        if self.synthetic_fixture is not True:
            raise TASK039E1PreparationError("D1 fit record must remain synthetic")
        _exact_false(self.real_record, "real_record")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "task039e1_synthetic_d1_directional_fit_supported_record_v1",
            "source": self.source,
            "target": self.target,
            "source_step_direction": self.source_step_direction,
            "selected_target_direction": self.selected_target_direction,
            "selected_horizon_seconds": self.selected_horizon_seconds,
            "source_parameter_record_hash": self.source_parameter_record_hash,
            "target_parameter_record_hash": self.target_parameter_record_hash,
            "fit_result": self.fit_result,
            "lower_ranked_fallback_used": self.lower_ranked_fallback_used,
            "candidate_arm_evidence_visible": self.candidate_arm_evidence_visible,
            "synthetic_fixture": self.synthetic_fixture,
            "real_record": self.real_record,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["artifact_hash"] = self.artifact_hash
        return payload


@dataclass(frozen=True)
class SyntheticD2ConfirmationRecordV1:
    """Synthetic structural counterpart of one private D2 outcome record."""

    source: str
    target: str
    source_step_direction: str
    target_response_direction: str
    selected_horizon_seconds: int
    source_parameter_record_hash: str
    target_parameter_record_hash: str
    d1_directional_record_hash: str
    confirmation_status: str
    fit_parameters_reused_without_retuning: bool = True
    synthetic_fixture: bool = True
    real_record: bool = False
    runtime_authority_granted: bool = False

    def __post_init__(self) -> None:
        _require_synthetic_identifier(self.source, "source")
        _require_synthetic_identifier(self.target, "target")
        if self.source == self.target:
            raise TASK039E1PreparationError("source and target must differ")
        if self.source_step_direction not in {"step_up", "step_down"}:
            raise TASK039E1PreparationError("source direction is invalid")
        if self.target_response_direction not in {"increase", "decrease"}:
            raise TASK039E1PreparationError("target direction is invalid")
        _positive_integer(
            self.selected_horizon_seconds, "selected_horizon_seconds"
        )
        for field_name in (
            "source_parameter_record_hash",
            "target_parameter_record_hash",
            "d1_directional_record_hash",
        ):
            require_sha256(getattr(self, field_name), field_name)
        if self.confirmation_status not in {
            "calibration_confirmed",
            "calibration_conflict",
        }:
            raise TASK039E1PreparationError("D2 confirmation status is invalid")
        if not isinstance(self.fit_parameters_reused_without_retuning, bool):
            raise TASK039E1PreparationError("D2 retuning flag must be boolean")
        if self.synthetic_fixture is not True:
            raise TASK039E1PreparationError("D2 record must remain synthetic")
        _exact_false(self.real_record, "real_record")
        _exact_false(
            self.runtime_authority_granted, "runtime_authority_granted"
        )

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "task039e1_synthetic_d2_confirmation_record_v1",
            "source": self.source,
            "target": self.target,
            "source_step_direction": self.source_step_direction,
            "target_response_direction": self.target_response_direction,
            "selected_horizon_seconds": self.selected_horizon_seconds,
            "source_parameter_record_hash": self.source_parameter_record_hash,
            "target_parameter_record_hash": self.target_parameter_record_hash,
            "d1_directional_record_hash": self.d1_directional_record_hash,
            "confirmation_status": self.confirmation_status,
            "fit_parameters_reused_without_retuning": (
                self.fit_parameters_reused_without_retuning
            ),
            "synthetic_fixture": self.synthetic_fixture,
            "real_record": self.real_record,
            "runtime_authority_granted": self.runtime_authority_granted,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["artifact_hash"] = self.artifact_hash
        return payload


@dataclass(frozen=True)
class PreregisteredWindowConstantBundleV1:
    """Non-learned constants bound to synthetic D0 policy-hash fixtures."""

    bundle_identity: str
    d0_protocol_bundle_hash: str
    source_event_policy_hash: str
    target_response_policy_hash: str
    confirmation_policy_hash: str
    source_pre_window_seconds: int
    source_post_window_seconds: int
    minimum_source_stability_fraction: float
    source_refractory_seconds: int
    cross_source_isolation_radius_seconds: int
    target_baseline_window_seconds: int
    target_response_window_seconds: int
    value_origin: str = WINDOW_CONSTANT_ORIGIN
    llm_generated: bool = False
    runtime_authority_granted: bool = False
    synthetic_fixture: bool = True

    def __post_init__(self) -> None:
        _require_synthetic_identifier(self.bundle_identity, "bundle_identity")
        for field_name in (
            "d0_protocol_bundle_hash",
            "source_event_policy_hash",
            "target_response_policy_hash",
            "confirmation_policy_hash",
        ):
            require_sha256(getattr(self, field_name), field_name)
        for field_name in (
            "source_pre_window_seconds",
            "source_post_window_seconds",
            "source_refractory_seconds",
            "cross_source_isolation_radius_seconds",
            "target_baseline_window_seconds",
            "target_response_window_seconds",
        ):
            _positive_integer(getattr(self, field_name), field_name)
        _fraction(
            self.minimum_source_stability_fraction,
            "minimum_source_stability_fraction",
        )
        if self.value_origin != WINDOW_CONSTANT_ORIGIN:
            raise TASK039E1PreparationError("window origin must bind D0 policy")
        _exact_false(self.llm_generated, "llm_generated")
        _exact_false(
            self.runtime_authority_granted, "runtime_authority_granted"
        )
        if self.synthetic_fixture is not True:
            raise TASK039E1PreparationError("window bundle must remain synthetic")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "task039e1_preregistered_window_constant_bundle_v1",
            "bundle_identity": self.bundle_identity,
            "d0_protocol_bundle_hash": self.d0_protocol_bundle_hash,
            "source_event_policy_hash": self.source_event_policy_hash,
            "target_response_policy_hash": self.target_response_policy_hash,
            "confirmation_policy_hash": self.confirmation_policy_hash,
            "source_pre_window_seconds": self.source_pre_window_seconds,
            "source_post_window_seconds": self.source_post_window_seconds,
            "minimum_source_stability_fraction": (
                self.minimum_source_stability_fraction
            ),
            "source_refractory_seconds": self.source_refractory_seconds,
            "cross_source_isolation_radius_seconds": (
                self.cross_source_isolation_radius_seconds
            ),
            "target_baseline_window_seconds": (
                self.target_baseline_window_seconds
            ),
            "target_response_window_seconds": self.target_response_window_seconds,
            "value_origin": self.value_origin,
            "llm_generated": self.llm_generated,
            "runtime_authority_granted": self.runtime_authority_granted,
            "synthetic_fixture": self.synthetic_fixture,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["artifact_hash"] = self.artifact_hash
        return payload


@dataclass(frozen=True)
class PrivateNumericEvidenceValueV1:
    """One private numeric value bound to every required evidence layer."""

    numeric_role: str
    numeric_value: int | float
    value_origin: str
    source_parameter_record_hash: str
    target_parameter_record_hash: str
    d1_fit_evidence_hash: str
    d2_confirmation_evidence_hash: str
    window_constant_bundle_hash: str
    evidence_authority: str = APPROVED_EVIDENCE_AUTHORITY
    llm_generated: bool = False
    runtime_authority_granted: bool = False

    def __post_init__(self) -> None:
        if self.numeric_role not in NUMERIC_ROLE_ORDER:
            raise TASK039E1PreparationError("numeric role is not approved")
        require_finite(self.numeric_value, "numeric_value")
        expected_origin = _numeric_role_origin(self.numeric_role)
        if self.value_origin != expected_origin:
            raise TASK039E1PreparationError("numeric role origin is invalid")
        for field_name in (
            "source_parameter_record_hash",
            "target_parameter_record_hash",
            "d1_fit_evidence_hash",
            "d2_confirmation_evidence_hash",
            "window_constant_bundle_hash",
        ):
            require_sha256(getattr(self, field_name), field_name)
        if self.evidence_authority != APPROVED_EVIDENCE_AUTHORITY:
            raise TASK039E1PreparationError("evidence authority is not approved")
        _exact_false(self.llm_generated, "llm_generated")
        _exact_false(
            self.runtime_authority_granted, "runtime_authority_granted"
        )

    def _content_dict(self) -> dict[str, Any]:
        return {
            "numeric_role": self.numeric_role,
            "numeric_value": self.numeric_value,
            "value_origin": self.value_origin,
            "source_parameter_record_hash": self.source_parameter_record_hash,
            "target_parameter_record_hash": self.target_parameter_record_hash,
            "d1_fit_evidence_hash": self.d1_fit_evidence_hash,
            "d2_confirmation_evidence_hash": (
                self.d2_confirmation_evidence_hash
            ),
            "window_constant_bundle_hash": self.window_constant_bundle_hash,
            "evidence_authority": self.evidence_authority,
            "llm_generated": self.llm_generated,
            "runtime_authority_granted": self.runtime_authority_granted,
        }

    @property
    def numeric_reference(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["numeric_reference"] = self.numeric_reference
        return payload


def _numeric_role_origin(role: str) -> str:
    if role in {
        ConstructionNumericRoleV1.SOURCE_STEP_THRESHOLD.value,
        ConstructionNumericRoleV1.SOURCE_STABILITY_TOLERANCE.value,
    }:
        return SOURCE_PARAMETER_ORIGIN
    if role == ConstructionNumericRoleV1.TARGET_NOISE_SCALE.value:
        return TARGET_PARAMETER_ORIGIN
    if role == ConstructionNumericRoleV1.SELECTED_DELAY_HORIZON_SECONDS.value:
        return HORIZON_ORIGIN
    if role in WINDOW_NUMERIC_ROLES:
        return WINDOW_CONSTANT_ORIGIN
    raise TASK039E1PreparationError("numeric role is not approved")


def derive_synthetic_numeric_bindings_v1(
    *,
    source_parameter: SyntheticD1SourceParameterRecordV1,
    target_parameter: SyntheticD1TargetParameterRecordV1,
    d1_fit_record: SyntheticD1DirectionalFitSupportedRecordV1,
    d2_confirmation_record: SyntheticD2ConfirmationRecordV1,
    window_constants: PreregisteredWindowConstantBundleV1,
) -> tuple[PrivateNumericEvidenceValueV1, ...]:
    """Derive the only permitted synthetic numeric bindings."""

    if source_parameter.parameter_status != "supported":
        raise TASK039E1PreparationError("source parameters are not supported")
    if source_parameter.source_step_threshold is None:
        raise TASK039E1PreparationError("source step threshold is unavailable")
    if source_parameter.source_stability_tolerance is None:
        raise TASK039E1PreparationError(
            "source stability tolerance is unavailable"
        )
    if target_parameter.parameter_status != "supported":
        raise TASK039E1PreparationError("target parameters are not supported")
    if target_parameter.target_noise_scale is None:
        raise TASK039E1PreparationError("target scale is unavailable")
    if d2_confirmation_record.confirmation_status != "calibration_confirmed":
        raise TASK039E1PreparationError("D2 record is not confirmed")
    if not d2_confirmation_record.fit_parameters_reused_without_retuning:
        raise TASK039E1PreparationError("D2 record retuned fit parameters")

    common = {
        "source_parameter_record_hash": source_parameter.artifact_hash,
        "target_parameter_record_hash": target_parameter.artifact_hash,
        "d1_fit_evidence_hash": d1_fit_record.artifact_hash,
        "d2_confirmation_evidence_hash": d2_confirmation_record.artifact_hash,
        "window_constant_bundle_hash": window_constants.artifact_hash,
    }
    values: dict[str, int | float] = {
        ConstructionNumericRoleV1.SOURCE_STEP_THRESHOLD.value: (
            source_parameter.source_step_threshold
        ),
        ConstructionNumericRoleV1.SOURCE_STABILITY_TOLERANCE.value: (
            source_parameter.source_stability_tolerance
        ),
        ConstructionNumericRoleV1.TARGET_NOISE_SCALE.value: (
            target_parameter.target_noise_scale
        ),
        ConstructionNumericRoleV1.SELECTED_DELAY_HORIZON_SECONDS.value: (
            d1_fit_record.selected_horizon_seconds
        ),
        ConstructionNumericRoleV1.SOURCE_PRE_WINDOW_SECONDS.value: (
            window_constants.source_pre_window_seconds
        ),
        ConstructionNumericRoleV1.SOURCE_POST_WINDOW_SECONDS.value: (
            window_constants.source_post_window_seconds
        ),
        ConstructionNumericRoleV1.MINIMUM_SOURCE_STABILITY_FRACTION.value: (
            window_constants.minimum_source_stability_fraction
        ),
        ConstructionNumericRoleV1.SOURCE_REFRACTORY_SECONDS.value: (
            window_constants.source_refractory_seconds
        ),
        ConstructionNumericRoleV1.CROSS_SOURCE_ISOLATION_RADIUS_SECONDS.value: (
            window_constants.cross_source_isolation_radius_seconds
        ),
        ConstructionNumericRoleV1.TARGET_BASELINE_WINDOW_SECONDS.value: (
            window_constants.target_baseline_window_seconds
        ),
        ConstructionNumericRoleV1.TARGET_RESPONSE_WINDOW_SECONDS.value: (
            window_constants.target_response_window_seconds
        ),
    }
    return tuple(
        PrivateNumericEvidenceValueV1(
            numeric_role=role,
            numeric_value=values[role],
            value_origin=_numeric_role_origin(role),
            **common,
        )
        for role in NUMERIC_ROLE_ORDER
    )


@dataclass(frozen=True)
class PrivateConstructionEvidenceV1:
    """Private construction-only evidence with fully bound numeric values."""

    relation_binding_hash: str
    relation_identity: str
    source: str
    source_step_direction: str
    target: str
    target_response_direction: str
    selected_horizon_seconds: int
    source_parameter_record_hash: str
    target_parameter_record_hash: str
    d1_fit_evidence_hash: str
    d2_confirmation_evidence_hash: str
    window_constant_bundle_hash: str
    numeric_bindings: tuple[PrivateNumericEvidenceValueV1, ...]
    evidence_authority: str = APPROVED_EVIDENCE_AUTHORITY
    construction_evidence_status: str = CONSTRUCTION_EVIDENCE_STATUS
    private_record: bool = True
    rule_generated: bool = False
    runtime_authority_granted: bool = False

    def __post_init__(self) -> None:
        require_sha256(self.relation_binding_hash, "relation_binding_hash")
        _require_synthetic_identifier(self.relation_identity, "relation_identity")
        _require_synthetic_identifier(self.source, "source")
        _require_synthetic_identifier(self.target, "target")
        if self.source_step_direction not in {"step_up", "step_down"}:
            raise TASK039E1PreparationError("source direction is invalid")
        if self.target_response_direction not in {"increase", "decrease"}:
            raise TASK039E1PreparationError("target direction is invalid")
        _positive_integer(self.selected_horizon_seconds, "selected_horizon_seconds")
        for field_name in (
            "source_parameter_record_hash",
            "target_parameter_record_hash",
            "d1_fit_evidence_hash",
            "d2_confirmation_evidence_hash",
            "window_constant_bundle_hash",
        ):
            require_sha256(getattr(self, field_name), field_name)
        observed_roles = tuple(item.numeric_role for item in self.numeric_bindings)
        if observed_roles != NUMERIC_ROLE_ORDER:
            raise TASK039E1PreparationError(
                "private numeric bindings must cover each approved role once"
            )
        for item in self.numeric_bindings:
            expected = (
                self.source_parameter_record_hash,
                self.target_parameter_record_hash,
                self.d1_fit_evidence_hash,
                self.d2_confirmation_evidence_hash,
                self.window_constant_bundle_hash,
            )
            observed = (
                item.source_parameter_record_hash,
                item.target_parameter_record_hash,
                item.d1_fit_evidence_hash,
                item.d2_confirmation_evidence_hash,
                item.window_constant_bundle_hash,
            )
            if observed != expected:
                raise TASK039E1PreparationError(
                    "numeric binding provenance does not match private evidence"
                )
        if self.evidence_authority != APPROVED_EVIDENCE_AUTHORITY:
            raise TASK039E1PreparationError("evidence authority is not approved")
        if self.construction_evidence_status != CONSTRUCTION_EVIDENCE_STATUS:
            raise TASK039E1PreparationError("construction evidence is not approved")
        if self.private_record is not True:
            raise TASK039E1PreparationError("private evidence must remain private")
        _exact_false(self.rule_generated, "rule_generated")
        _exact_false(
            self.runtime_authority_granted, "runtime_authority_granted"
        )

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "private_construction_evidence_v1",
            "relation_binding_hash": self.relation_binding_hash,
            "relation_identity": self.relation_identity,
            "source": self.source,
            "source_step_direction": self.source_step_direction,
            "target": self.target,
            "target_response_direction": self.target_response_direction,
            "selected_horizon_seconds": self.selected_horizon_seconds,
            "source_parameter_record_hash": self.source_parameter_record_hash,
            "target_parameter_record_hash": self.target_parameter_record_hash,
            "d1_fit_evidence_hash": self.d1_fit_evidence_hash,
            "d2_confirmation_evidence_hash": (
                self.d2_confirmation_evidence_hash
            ),
            "window_constant_bundle_hash": self.window_constant_bundle_hash,
            "numeric_bindings": [item.to_dict() for item in self.numeric_bindings],
            "evidence_authority": self.evidence_authority,
            "construction_evidence_status": self.construction_evidence_status,
            "private_record": self.private_record,
            "rule_generated": self.rule_generated,
            "runtime_authority_granted": self.runtime_authority_granted,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["artifact_hash"] = self.artifact_hash
        return payload


@dataclass(frozen=True)
class PublicEvidenceDisclosurePolicyV1:
    policy_identity: str
    selected_horizon_public: bool
    raw_values_public: bool = False
    private_numeric_values_public: bool = False
    runtime_authority_granted: bool = False

    def __post_init__(self) -> None:
        _require_synthetic_identifier(self.policy_identity, "policy_identity")
        if not isinstance(self.selected_horizon_public, bool):
            raise TASK039E1PreparationError(
                "selected-horizon disclosure policy must be boolean"
            )
        _exact_false(self.raw_values_public, "raw_values_public")
        _exact_false(
            self.private_numeric_values_public,
            "private_numeric_values_public",
        )
        _exact_false(
            self.runtime_authority_granted, "runtime_authority_granted"
        )

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(
            {
                "policy_identity": self.policy_identity,
                "selected_horizon_public": self.selected_horizon_public,
                "raw_values_public": self.raw_values_public,
                "private_numeric_values_public": self.private_numeric_values_public,
                "runtime_authority_granted": self.runtime_authority_granted,
            }
        )


@dataclass(frozen=True)
class PublicConstructionEvidenceManifestEntryV1:
    """Public entry containing references and roles, never private values."""

    relation_binding_hash: str
    relation_identity: str
    source: str
    target: str
    source_step_direction: str
    target_response_direction: str
    selected_horizon_seconds: int | None
    private_evidence_record_hash: str
    approved_numeric_roles: tuple[str, ...]
    source_parameter_record_hash: str
    target_parameter_record_hash: str
    d1_fit_evidence_hash: str
    d2_confirmation_evidence_hash: str
    window_constant_bundle_hash: str
    disclosure_policy_hash: str
    construction_evidence_status: str = CONSTRUCTION_EVIDENCE_STATUS
    private_numeric_values_included: bool = False
    raw_hai_included: bool = False
    rule_generated: bool = False
    runtime_authority_granted: bool = False

    def __post_init__(self) -> None:
        for field_name in (
            "relation_binding_hash",
            "private_evidence_record_hash",
            "source_parameter_record_hash",
            "target_parameter_record_hash",
            "d1_fit_evidence_hash",
            "d2_confirmation_evidence_hash",
            "window_constant_bundle_hash",
            "disclosure_policy_hash",
        ):
            require_sha256(getattr(self, field_name), field_name)
        _require_synthetic_identifier(self.relation_identity, "relation_identity")
        _require_synthetic_identifier(self.source, "source")
        _require_synthetic_identifier(self.target, "target")
        if self.source_step_direction not in {"step_up", "step_down"}:
            raise TASK039E1PreparationError("source direction is invalid")
        if self.target_response_direction not in {"increase", "decrease"}:
            raise TASK039E1PreparationError("target direction is invalid")
        if self.selected_horizon_seconds is not None:
            _positive_integer(
                self.selected_horizon_seconds, "selected_horizon_seconds"
            )
        if self.approved_numeric_roles != NUMERIC_ROLE_ORDER:
            raise TASK039E1PreparationError("approved numeric roles are incomplete")
        if self.construction_evidence_status != CONSTRUCTION_EVIDENCE_STATUS:
            raise TASK039E1PreparationError("construction evidence is not approved")
        for field_name in (
            "private_numeric_values_included",
            "raw_hai_included",
            "rule_generated",
            "runtime_authority_granted",
        ):
            _exact_false(getattr(self, field_name), field_name)

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "public_construction_evidence_manifest_entry_v1",
            "relation_binding_hash": self.relation_binding_hash,
            "relation_identity": self.relation_identity,
            "source": self.source,
            "target": self.target,
            "source_step_direction": self.source_step_direction,
            "target_response_direction": self.target_response_direction,
            "selected_horizon_seconds": self.selected_horizon_seconds,
            "private_evidence_record_hash": self.private_evidence_record_hash,
            "approved_numeric_roles": list(self.approved_numeric_roles),
            "source_parameter_record_hash": self.source_parameter_record_hash,
            "target_parameter_record_hash": self.target_parameter_record_hash,
            "d1_fit_evidence_hash": self.d1_fit_evidence_hash,
            "d2_confirmation_evidence_hash": (
                self.d2_confirmation_evidence_hash
            ),
            "window_constant_bundle_hash": self.window_constant_bundle_hash,
            "disclosure_policy_hash": self.disclosure_policy_hash,
            "construction_evidence_status": self.construction_evidence_status,
            "private_numeric_values_included": (
                self.private_numeric_values_included
            ),
            "raw_hai_included": self.raw_hai_included,
            "rule_generated": self.rule_generated,
            "runtime_authority_granted": self.runtime_authority_granted,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["artifact_hash"] = self.artifact_hash
        return payload


@dataclass(frozen=True)
class ConstructionEvidenceMaterializationInputV1:
    relation: ConfirmedRelationPrimitiveV1
    source_parameter: SyntheticD1SourceParameterRecordV1
    target_parameter: SyntheticD1TargetParameterRecordV1
    d1_fit_record: SyntheticD1DirectionalFitSupportedRecordV1
    d2_confirmation_record: SyntheticD2ConfirmationRecordV1
    window_constants: PreregisteredWindowConstantBundleV1
    disclosure_policy: PublicEvidenceDisclosurePolicyV1


@dataclass(frozen=True)
class MaterializedConstructionEvidenceV1:
    private_evidence: PrivateConstructionEvidenceV1
    public_manifest: PublicConstructionEvidenceManifestEntryV1
    approved_numeric_bundle: ApprovedNumericEvidenceBundleV1
    materialization_status: str = CONSTRUCTION_EVIDENCE_STATUS
    rule_generated: bool = False
    runtime_authority_granted: bool = False

    def __post_init__(self) -> None:
        if self.materialization_status != CONSTRUCTION_EVIDENCE_STATUS:
            raise TASK039E1PreparationError("materialization is not approved")
        if (
            self.public_manifest.private_evidence_record_hash
            != self.private_evidence.artifact_hash
            or self.public_manifest.relation_binding_hash
            != self.private_evidence.relation_binding_hash
            or self.approved_numeric_bundle.relation_binding_hash
            != self.private_evidence.relation_binding_hash
        ):
            raise TASK039E1PreparationError(
                "materialized evidence artifacts are not mutually bound"
            )
        _exact_false(self.rule_generated, "rule_generated")
        _exact_false(
            self.runtime_authority_granted, "runtime_authority_granted"
        )

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(
            {
                "private_evidence_hash": self.private_evidence.artifact_hash,
                "public_manifest_hash": self.public_manifest.artifact_hash,
                "approved_numeric_bundle_hash": (
                    self.approved_numeric_bundle.artifact_hash
                ),
                "materialization_status": self.materialization_status,
                "rule_generated": self.rule_generated,
                "runtime_authority_granted": self.runtime_authority_granted,
            }
        )


def _assert_exact_bindings(
    item: ConstructionEvidenceMaterializationInputV1,
) -> None:
    relation = item.relation
    source = item.source_parameter
    target = item.target_parameter
    d1 = item.d1_fit_record
    d2 = item.d2_confirmation_record
    for value, field_name in (
        (relation.relation_identity, "relation_identity"),
        (relation.source, "relation_source"),
        (relation.target, "relation_target"),
    ):
        _require_synthetic_identifier(value, field_name)
    if source.source != relation.source or d1.source != relation.source or d2.source != relation.source:
        raise TASK039E1PreparationError("source identity mismatch")
    if target.target != relation.target or d1.target != relation.target or d2.target != relation.target:
        raise TASK039E1PreparationError("target identity mismatch")
    if d1.source_step_direction != relation.source_step_direction or d2.source_step_direction != relation.source_step_direction:
        raise TASK039E1PreparationError("source direction mismatch")
    if d1.selected_target_direction != relation.target_response_direction or d2.target_response_direction != relation.target_response_direction:
        raise TASK039E1PreparationError("target direction mismatch")
    if d1.selected_horizon_seconds != relation.selected_delay_horizon_seconds or d2.selected_horizon_seconds != relation.selected_delay_horizon_seconds:
        raise TASK039E1PreparationError("selected horizon mismatch")
    if source.parameter_status != "supported" or source.source_step_threshold is None:
        raise TASK039E1PreparationError("source step threshold is unavailable")
    if source.source_stability_tolerance is None:
        raise TASK039E1PreparationError("source stability tolerance is unavailable")
    if target.parameter_status != "supported" or target.target_noise_scale is None:
        raise TASK039E1PreparationError("target scale is unavailable")
    if source.source_threshold_origin != SOURCE_PARAMETER_ORIGIN:
        raise TASK039E1PreparationError("source threshold origin mismatch")
    if source.stability_tolerance_origin != SOURCE_PARAMETER_ORIGIN:
        raise TASK039E1PreparationError("stability tolerance origin mismatch")
    if target.target_scale_origin != TARGET_PARAMETER_ORIGIN:
        raise TASK039E1PreparationError("target scale origin mismatch")
    if d1.source_parameter_record_hash != source.artifact_hash:
        raise TASK039E1PreparationError("D1 source parameter hash mismatch")
    if d1.target_parameter_record_hash != target.artifact_hash:
        raise TASK039E1PreparationError("D1 target parameter hash mismatch")
    if relation.fit_evidence_reference != d1.artifact_hash:
        raise TASK039E1PreparationError("D1 directional record hash mismatch")
    if d2.d1_directional_record_hash != d1.artifact_hash:
        raise TASK039E1PreparationError("D2-to-D1 binding mismatch")
    if d2.source_parameter_record_hash != source.artifact_hash or d2.target_parameter_record_hash != target.artifact_hash:
        raise TASK039E1PreparationError("D2 parameter binding mismatch")
    if d2.confirmation_status != "calibration_confirmed":
        raise TASK039E1PreparationError("D2 record is not confirmed")
    if not d2.fit_parameters_reused_without_retuning:
        raise TASK039E1PreparationError("D2 parameters were retuned")
    if relation.confirmation_evidence_reference != d2.artifact_hash:
        raise TASK039E1PreparationError("D2 confirmation record hash mismatch")


def materialize_construction_evidence_v1(
    relation: ConfirmedRelationPrimitiveV1,
    source_parameter: SyntheticD1SourceParameterRecordV1,
    target_parameter: SyntheticD1TargetParameterRecordV1,
    d1_fit_record: SyntheticD1DirectionalFitSupportedRecordV1,
    d2_confirmation_record: SyntheticD2ConfirmationRecordV1,
    window_constants: PreregisteredWindowConstantBundleV1,
    disclosure_policy: PublicEvidenceDisclosurePolicyV1,
) -> MaterializedConstructionEvidenceV1:
    """Materialize exact synthetic evidence without I/O or rule generation."""

    expected_types = (
        (relation, ConfirmedRelationPrimitiveV1, "relation"),
        (
            source_parameter,
            SyntheticD1SourceParameterRecordV1,
            "source_parameter",
        ),
        (
            target_parameter,
            SyntheticD1TargetParameterRecordV1,
            "target_parameter",
        ),
        (
            d1_fit_record,
            SyntheticD1DirectionalFitSupportedRecordV1,
            "d1_fit_record",
        ),
        (
            d2_confirmation_record,
            SyntheticD2ConfirmationRecordV1,
            "d2_confirmation_record",
        ),
        (
            window_constants,
            PreregisteredWindowConstantBundleV1,
            "window_constants",
        ),
        (
            disclosure_policy,
            PublicEvidenceDisclosurePolicyV1,
            "disclosure_policy",
        ),
    )
    for value, expected_type, field_name in expected_types:
        if not isinstance(value, expected_type):
            raise TASK039E1PreparationError(
                f"{field_name} has the wrong contract type"
            )
    item = ConstructionEvidenceMaterializationInputV1(
        relation,
        source_parameter,
        target_parameter,
        d1_fit_record,
        d2_confirmation_record,
        window_constants,
        disclosure_policy,
    )
    _assert_exact_bindings(item)
    numeric_bindings = derive_synthetic_numeric_bindings_v1(
        source_parameter=source_parameter,
        target_parameter=target_parameter,
        d1_fit_record=d1_fit_record,
        d2_confirmation_record=d2_confirmation_record,
        window_constants=window_constants,
    )
    by_role = {entry.numeric_role: entry for entry in numeric_bindings}
    expected_refs = {
        "approved_source_threshold_reference": by_role[
            ConstructionNumericRoleV1.SOURCE_STEP_THRESHOLD.value
        ].numeric_reference,
        "approved_source_stability_reference": by_role[
            ConstructionNumericRoleV1.SOURCE_STABILITY_TOLERANCE.value
        ].numeric_reference,
        "approved_target_scale_reference": by_role[
            ConstructionNumericRoleV1.TARGET_NOISE_SCALE.value
        ].numeric_reference,
    }
    for field_name, expected in expected_refs.items():
        if getattr(relation, field_name) != expected:
            raise TASK039E1PreparationError(
                f"{field_name} does not bind the exact numeric value"
            )
    private = PrivateConstructionEvidenceV1(
        relation_binding_hash=relation.binding_hash,
        relation_identity=relation.relation_identity,
        source=relation.source,
        source_step_direction=relation.source_step_direction,
        target=relation.target,
        target_response_direction=relation.target_response_direction,
        selected_horizon_seconds=relation.selected_delay_horizon_seconds,
        source_parameter_record_hash=source_parameter.artifact_hash,
        target_parameter_record_hash=target_parameter.artifact_hash,
        d1_fit_evidence_hash=d1_fit_record.artifact_hash,
        d2_confirmation_evidence_hash=d2_confirmation_record.artifact_hash,
        window_constant_bundle_hash=window_constants.artifact_hash,
        numeric_bindings=numeric_bindings,
    )
    manifest = PublicConstructionEvidenceManifestEntryV1(
        relation_binding_hash=relation.binding_hash,
        relation_identity=relation.relation_identity,
        source=relation.source,
        target=relation.target,
        source_step_direction=relation.source_step_direction,
        target_response_direction=relation.target_response_direction,
        selected_horizon_seconds=(
            relation.selected_delay_horizon_seconds
            if disclosure_policy.selected_horizon_public
            else None
        ),
        private_evidence_record_hash=private.artifact_hash,
        approved_numeric_roles=NUMERIC_ROLE_ORDER,
        source_parameter_record_hash=source_parameter.artifact_hash,
        target_parameter_record_hash=target_parameter.artifact_hash,
        d1_fit_evidence_hash=d1_fit_record.artifact_hash,
        d2_confirmation_evidence_hash=d2_confirmation_record.artifact_hash,
        window_constant_bundle_hash=window_constants.artifact_hash,
        disclosure_policy_hash=disclosure_policy.artifact_hash,
    )
    approved_bundle = ApprovedNumericEvidenceBundleV1(
        relation_binding_hash=relation.binding_hash,
        source_threshold_reference=expected_refs[
            "approved_source_threshold_reference"
        ],
        source_stability_reference=expected_refs[
            "approved_source_stability_reference"
        ],
        target_scale_reference=expected_refs[
            "approved_target_scale_reference"
        ],
        fit_evidence_reference=d1_fit_record.artifact_hash,
        confirmation_evidence_reference=d2_confirmation_record.artifact_hash,
        preregistered_window_constant_references=tuple(
            by_role[role].numeric_reference for role in WINDOW_NUMERIC_ROLES
        ),
    )
    return MaterializedConstructionEvidenceV1(
        private_evidence=private,
        public_manifest=manifest,
        approved_numeric_bundle=approved_bundle,
    )


def materialize_construction_evidence_collection_v1(
    inputs: Sequence[ConstructionEvidenceMaterializationInputV1],
) -> tuple[MaterializedConstructionEvidenceV1, ...]:
    """Materialize a collection while rejecting duplicate relations."""

    relation_hashes = tuple(item.relation.binding_hash for item in inputs)
    if len(relation_hashes) != len(set(relation_hashes)):
        raise TASK039E1PreparationError("duplicate relation binding")
    return tuple(
        materialize_construction_evidence_v1(
            item.relation,
            item.source_parameter,
            item.target_parameter,
            item.d1_fit_record,
            item.d2_confirmation_record,
            item.window_constants,
            item.disclosure_policy,
        )
        for item in inputs
    )


@dataclass(frozen=True)
class ResolvedPrivateNumericValueV1:
    relation_binding_hash: str
    numeric_role: str
    numeric_reference: str
    private_evidence_record_hash: str
    numeric_value: int | float
    evidence_authority: str = APPROVED_EVIDENCE_AUTHORITY
    construction_only: bool = True
    runtime_authority_granted: bool = False

    def __post_init__(self) -> None:
        for field_name in (
            "relation_binding_hash",
            "numeric_reference",
            "private_evidence_record_hash",
        ):
            require_sha256(getattr(self, field_name), field_name)
        if self.numeric_role not in NUMERIC_ROLE_ORDER:
            raise TASK039E1PreparationError("numeric role is not approved")
        require_finite(self.numeric_value, "numeric_value")
        if self.evidence_authority != APPROVED_EVIDENCE_AUTHORITY:
            raise TASK039E1PreparationError("evidence authority is not approved")
        if self.construction_only is not True:
            raise TASK039E1PreparationError("resolved value is construction-only")
        _exact_false(
            self.runtime_authority_granted, "runtime_authority_granted"
        )

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "resolved_private_numeric_value_v1",
            "relation_binding_hash": self.relation_binding_hash,
            "numeric_role": self.numeric_role,
            "numeric_reference": self.numeric_reference,
            "private_evidence_record_hash": self.private_evidence_record_hash,
            "numeric_value": self.numeric_value,
            "evidence_authority": self.evidence_authority,
            "construction_only": self.construction_only,
            "runtime_authority_granted": self.runtime_authority_granted,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["artifact_hash"] = self.artifact_hash
        return payload


def resolve_private_numeric_reference_v1(
    *,
    proposal_numeric_reference: str,
    relation_binding_hash: str,
    numeric_role: str,
    private_evidence_record_hash: str,
    private_evidence: PrivateConstructionEvidenceV1,
) -> ResolvedPrivateNumericValueV1:
    """Resolve one approved construction reference without runtime authority."""

    require_sha256(proposal_numeric_reference, "proposal_numeric_reference")
    require_sha256(relation_binding_hash, "relation_binding_hash")
    require_sha256(
        private_evidence_record_hash, "private_evidence_record_hash"
    )
    if relation_binding_hash != private_evidence.relation_binding_hash:
        raise TASK039E1PreparationError("relation binding mismatch")
    if private_evidence_record_hash != private_evidence.artifact_hash:
        raise TASK039E1PreparationError("private evidence hash mismatch")
    if (
        private_evidence.evidence_authority != APPROVED_EVIDENCE_AUTHORITY
        or private_evidence.construction_evidence_status
        != CONSTRUCTION_EVIDENCE_STATUS
    ):
        raise TASK039E1PreparationError("evidence authority is not approved")
    if private_evidence.runtime_authority_granted:
        raise TASK039E1PreparationError(
            "runtime-authorized evidence cannot be resolved by this preparation"
        )
    matches = tuple(
        item
        for item in private_evidence.numeric_bindings
        if item.numeric_reference == proposal_numeric_reference
    )
    if len(matches) != 1:
        raise TASK039E1PreparationError("numeric reference is not approved")
    match = matches[0]
    if match.numeric_role != numeric_role:
        raise TASK039E1PreparationError("numeric role mismatch")
    return ResolvedPrivateNumericValueV1(
        relation_binding_hash=relation_binding_hash,
        numeric_role=numeric_role,
        numeric_reference=proposal_numeric_reference,
        private_evidence_record_hash=private_evidence_record_hash,
        numeric_value=match.numeric_value,
    )


def assert_preparation_boundary_v1(
    *,
    real_d2_result: object | None = None,
    real_confirmed_identity: object | None = None,
    d1_private_ledger: object | None = None,
    d2_private_ledger: object | None = None,
    hai_input: object | None = None,
    provider: object | None = None,
) -> None:
    """Reject all real/private/executable inputs before any operation."""

    if any(
        item is not None
        for item in (
            real_d2_result,
            real_confirmed_identity,
            d1_private_ledger,
            d2_private_ledger,
            hai_input,
            provider,
        )
    ):
        raise TASK039E1PreparationError(
            "TASK-039E1-PREP accepts synthetic fixtures only"
        )


__all__ = [
    "APPROVED_EVIDENCE_AUTHORITY",
    "BASE_COMMIT",
    "BRANCH",
    "CONSTRUCTION_EVIDENCE_STATUS",
    "ConstructionEvidenceMaterializationInputV1",
    "ConstructionNumericRoleV1",
    "D1_PRIVATE_LEDGER_ACCESSED",
    "D2_PRIVATE_LEDGER_ACCESSED",
    "E1_AUTHORIZATION_CREATED",
    "HAI_ACCESSED",
    "LLM_CALLED",
    "MaterializedConstructionEvidenceV1",
    "NUMERIC_ROLE_ORDER",
    "PREPARATION_STATUS",
    "PreregisteredWindowConstantBundleV1",
    "PrivateConstructionEvidenceV1",
    "PrivateNumericEvidenceValueV1",
    "PublicConstructionEvidenceManifestEntryV1",
    "PublicEvidenceDisclosurePolicyV1",
    "REAL_CONFIRMED_RELATION_IDENTITY_CONSUMED",
    "REAL_D2_RESULT_CONSUMED",
    "RULE_GENERATED",
    "RUNTIME_AUTHORITY_GRANTED",
    "ResolvedPrivateNumericValueV1",
    "SyntheticD1DirectionalFitSupportedRecordV1",
    "SyntheticD1SourceParameterRecordV1",
    "SyntheticD1TargetParameterRecordV1",
    "SyntheticD2ConfirmationRecordV1",
    "TASK039E1PreparationError",
    "WINDOW_NUMERIC_ROLES",
    "assert_preparation_boundary_v1",
    "derive_synthetic_numeric_bindings_v1",
    "materialize_construction_evidence_collection_v1",
    "materialize_construction_evidence_v1",
    "resolve_private_numeric_reference_v1",
]
