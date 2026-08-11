"""Independent synthetic construction-evidence audit preparation.

The oracle in this module uses only stdlib canonical JSON and SHA-256. It does
not import or call an E1 materializer, read a ledger, inspect HAI, invoke an
LLM, generate a rule, or grant runtime authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
import re
from typing import Any, Mapping, Sequence


TASK_ID = "TASK-039E1-AUDIT-PREP"
BASE_COMMIT = "20ca2e6f561ce0cdfaf822198f7b64d8e143215c"
BRANCH = "task-039e1-audit-prep"
PREPARATION_STATUS = "passed_task039e1_audit_preparation"

EXPECTED_RELATIONS = 42
EXPECTED_PAIR_CONTEXTS = 23
EXPECTED_ROLES_PER_RELATION = 11
EXPECTED_NUMERIC_BINDINGS = 462

REAL_E1_RESULT_ACCESSED = False
REAL_D2_RESULT_ACCESSED = False
D1_PRIVATE_LEDGERS_ACCESSED = False
D2_PRIVATE_LEDGERS_ACCESSED = False
E1_PRIVATE_LEDGER_ACCESSED = False
REAL_CONFIRMED_IDENTITIES_CONSUMED = False
HAI_ACCESSED = False
LLM_AVAILABLE = False
LLM_CALLED = False
RULE_GENERATION_AVAILABLE = False
RULE_GENERATED = False
RUNTIME_AUTHORITY_GRANTED = False
E1_AUTHORIZED = False
E2_AUTHORIZATION_CREATED = False

APPROVED_EVIDENCE_AUTHORITY = "approved_construction_evidence"
APPROVED_STATUS = "approved"
RELATION_FAMILY = "continuous_step_delayed_response_v1"

NUMERIC_ROLES = (
    "source_step_threshold",
    "source_stability_tolerance",
    "target_noise_scale",
    "selected_delay_horizon",
    "source_pre_window",
    "source_post_window",
    "minimum_source_stability_fraction",
    "source_refractory",
    "cross_source_isolation_radius",
    "target_baseline_window",
    "target_response_window",
)
WINDOW_ROLES = NUMERIC_ROLES[4:]
CALIBRATED_PRIVATE_ROLES = NUMERIC_ROLES[:3]
ROLE_ORIGINS = {
    "source_step_threshold": "d1_source_parameter_record",
    "source_stability_tolerance": "d1_source_parameter_record",
    "target_noise_scale": "d1_target_parameter_record",
    "selected_delay_horizon": "d1_directional_record",
    "source_pre_window": "d0_window_constant_bundle",
    "source_post_window": "d0_window_constant_bundle",
    "minimum_source_stability_fraction": "d0_window_constant_bundle",
    "source_refractory": "d0_window_constant_bundle",
    "cross_source_isolation_radius": "d0_window_constant_bundle",
    "target_baseline_window": "d0_window_constant_bundle",
    "target_response_window": "d0_window_constant_bundle",
}

_HASH = re.compile(r"^[a-f0-9]{64}$")
_SYNTHETIC = re.compile(r"^SYNTHETIC_[A-Za-z0-9._:-]+$")
_ABSOLUTE_WINDOWS = re.compile(r"^[A-Za-z]:[\\/]")


class TASK039E1AuditPreparationError(ValueError):
    """Raised when independent audit preparation fails closed."""


def _canonical_json_bytes(document: Mapping[str, Any]) -> bytes:
    try:
        encoded = json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise TASK039E1AuditPreparationError(
            "audit document is not canonical JSON"
        ) from exc
    return encoded.encode("utf-8")


def _independent_hash(document: Mapping[str, Any]) -> str:
    return sha256(_canonical_json_bytes(document)).hexdigest()


def _require_hash(value: str, field_name: str) -> None:
    if not isinstance(value, str) or _HASH.fullmatch(value) is None:
        raise TASK039E1AuditPreparationError(
            f"{field_name} must be a lowercase SHA-256 hash"
        )


def _require_synthetic(value: str, field_name: str) -> None:
    if not isinstance(value, str) or _SYNTHETIC.fullmatch(value) is None:
        raise TASK039E1AuditPreparationError(
            f"{field_name} must use a SYNTHETIC_ identity"
        )


def _require_finite(value: int | float, field_name: str) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
    ):
        raise TASK039E1AuditPreparationError(f"{field_name} must be finite")


def independent_numeric_role_origin_v1(numeric_role: str) -> str:
    """Return the independently frozen origin for one E0 numeric role."""

    try:
        return ROLE_ORIGINS[numeric_role]
    except KeyError as exc:
        raise TASK039E1AuditPreparationError(
            "numeric role is outside the eleven-role freeze"
        ) from exc


def independent_numeric_reference_v1(
    *,
    numeric_role: str,
    numeric_value: int | float,
    value_origin: str,
    source_parameter_record_hash: str,
    target_parameter_record_hash: str,
    d1_evidence_record_hash: str,
    d2_evidence_record_hash: str,
    window_constant_bundle_hash: str,
) -> str:
    """Independently calculate one numeric-reference SHA-256."""

    expected_origin = independent_numeric_role_origin_v1(numeric_role)
    if value_origin != expected_origin:
        raise TASK039E1AuditPreparationError("numeric-role origin mismatch")
    _require_finite(numeric_value, "numeric_value")
    for field_name, value in (
        ("source_parameter_record_hash", source_parameter_record_hash),
        ("target_parameter_record_hash", target_parameter_record_hash),
        ("d1_evidence_record_hash", d1_evidence_record_hash),
        ("d2_evidence_record_hash", d2_evidence_record_hash),
        ("window_constant_bundle_hash", window_constant_bundle_hash),
    ):
        _require_hash(value, field_name)
    return _independent_hash(
        {
            "schema_version": "1.0.0",
            "artifact_type": "independent_construction_numeric_reference_v1",
            "numeric_role": numeric_role,
            "numeric_value": numeric_value,
            "value_origin": value_origin,
            "source_parameter_record_hash": source_parameter_record_hash,
            "target_parameter_record_hash": target_parameter_record_hash,
            "d1_evidence_record_hash": d1_evidence_record_hash,
            "d2_evidence_record_hash": d2_evidence_record_hash,
            "window_constant_bundle_hash": window_constant_bundle_hash,
            "evidence_authority": APPROVED_EVIDENCE_AUTHORITY,
            "runtime_authority_granted": False,
        }
    )


@dataclass(frozen=True)
class IndependentPublicRelationPrimitiveV1:
    relation_identity: str
    pair_context_identity: str
    source: str
    source_step_direction: str
    target: str
    target_response_direction: str
    selected_delay_horizon: int
    relation_binding_hash: str
    d1_directional_record_hash: str
    d2_confirmation_record_hash: str
    relation_family: str = RELATION_FAMILY
    private_numeric_values_included: bool = False
    runtime_authority_granted: bool = False

    def __post_init__(self) -> None:
        for field_name in (
            "relation_identity",
            "pair_context_identity",
            "source",
            "target",
        ):
            _require_synthetic(getattr(self, field_name), field_name)
        if self.source == self.target:
            raise TASK039E1AuditPreparationError("source and target must differ")
        if self.source_step_direction not in {"step_up", "step_down"}:
            raise TASK039E1AuditPreparationError("source direction is invalid")
        if self.target_response_direction not in {"increase", "decrease"}:
            raise TASK039E1AuditPreparationError("target direction is invalid")
        if (
            isinstance(self.selected_delay_horizon, bool)
            or not isinstance(self.selected_delay_horizon, int)
            or self.selected_delay_horizon <= 0
        ):
            raise TASK039E1AuditPreparationError("selected horizon is invalid")
        for field_name in (
            "relation_binding_hash",
            "d1_directional_record_hash",
            "d2_confirmation_record_hash",
        ):
            _require_hash(getattr(self, field_name), field_name)
        if self.relation_family != RELATION_FAMILY:
            raise TASK039E1AuditPreparationError("relation family mismatch")
        if self.private_numeric_values_included:
            raise TASK039E1AuditPreparationError(
                "public relation primitive contains private values"
            )
        if self.runtime_authority_granted:
            raise TASK039E1AuditPreparationError(
                "public relation primitive preclaims runtime authority"
            )

    def identity_dict(self) -> dict[str, str]:
        return {
            "relation_identity": self.relation_identity,
            "source": self.source,
            "source_step_direction": self.source_step_direction,
            "target": self.target,
            "target_response_direction": self.target_response_direction,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.identity_dict(),
            "pair_context_identity": self.pair_context_identity,
            "selected_delay_horizon": self.selected_delay_horizon,
            "relation_binding_hash": self.relation_binding_hash,
            "d1_directional_record_hash": self.d1_directional_record_hash,
            "d2_confirmation_record_hash": self.d2_confirmation_record_hash,
            "relation_family": self.relation_family,
            "private_numeric_values_included": self.private_numeric_values_included,
            "runtime_authority_granted": self.runtime_authority_granted,
        }


def independent_cohort_identity_list_hash_v1(
    relations: Sequence[IndependentPublicRelationPrimitiveV1],
) -> str:
    return _independent_hash(
        {"relation_identities": [item.identity_dict() for item in relations]}
    )


@dataclass(frozen=True)
class IndependentNumericBindingV1:
    relation_binding_hash: str
    numeric_role: str
    numeric_value: int | float
    value_origin: str
    source_parameter_record_hash: str
    target_parameter_record_hash: str
    d1_evidence_record_hash: str
    d2_evidence_record_hash: str
    window_constant_bundle_hash: str
    numeric_reference: str
    evidence_authority: str = APPROVED_EVIDENCE_AUTHORITY
    runtime_authority_granted: bool = False

    def __post_init__(self) -> None:
        for field_name in (
            "relation_binding_hash",
            "source_parameter_record_hash",
            "target_parameter_record_hash",
            "d1_evidence_record_hash",
            "d2_evidence_record_hash",
            "window_constant_bundle_hash",
            "numeric_reference",
        ):
            _require_hash(getattr(self, field_name), field_name)
        independent_numeric_role_origin_v1(self.numeric_role)
        _require_finite(self.numeric_value, "numeric_value")
        if self.evidence_authority != APPROVED_EVIDENCE_AUTHORITY:
            raise TASK039E1AuditPreparationError("evidence authority is invalid")

    def reference_content(self) -> dict[str, Any]:
        return {
            "numeric_role": self.numeric_role,
            "numeric_value": self.numeric_value,
            "value_origin": self.value_origin,
            "source_parameter_record_hash": self.source_parameter_record_hash,
            "target_parameter_record_hash": self.target_parameter_record_hash,
            "d1_evidence_record_hash": self.d1_evidence_record_hash,
            "d2_evidence_record_hash": self.d2_evidence_record_hash,
            "window_constant_bundle_hash": self.window_constant_bundle_hash,
        }

    def recomputed_reference(self) -> str:
        return independent_numeric_reference_v1(**self.reference_content())

    def to_dict(self) -> dict[str, Any]:
        return {
            "relation_binding_hash": self.relation_binding_hash,
            **self.reference_content(),
            "numeric_reference": self.numeric_reference,
            "evidence_authority": self.evidence_authority,
            "runtime_authority_granted": self.runtime_authority_granted,
        }


@dataclass(frozen=True)
class IndependentPrivateConstructionEvidenceV1:
    relation_identity: str
    pair_context_identity: str
    relation_binding_hash: str
    source: str
    source_step_direction: str
    target: str
    target_response_direction: str
    selected_delay_horizon: int
    source_parameter_record_hash: str
    target_parameter_record_hash: str
    d1_evidence_record_hash: str
    d2_evidence_record_hash: str
    window_constant_bundle_hash: str
    confirmation_status: str
    numeric_bindings: tuple[IndependentNumericBindingV1, ...]
    evidence_authority: str = APPROVED_EVIDENCE_AUTHORITY
    construction_evidence_status: str = APPROVED_STATUS
    runtime_authority_granted: bool = False

    def __post_init__(self) -> None:
        for field_name in (
            "relation_identity",
            "pair_context_identity",
            "source",
            "target",
        ):
            _require_synthetic(getattr(self, field_name), field_name)
        for field_name in (
            "relation_binding_hash",
            "source_parameter_record_hash",
            "target_parameter_record_hash",
            "d1_evidence_record_hash",
            "d2_evidence_record_hash",
            "window_constant_bundle_hash",
        ):
            _require_hash(getattr(self, field_name), field_name)
        if self.source_step_direction not in {"step_up", "step_down"}:
            raise TASK039E1AuditPreparationError("source direction is invalid")
        if self.target_response_direction not in {"increase", "decrease"}:
            raise TASK039E1AuditPreparationError("target direction is invalid")
        if (
            isinstance(self.selected_delay_horizon, bool)
            or not isinstance(self.selected_delay_horizon, int)
            or self.selected_delay_horizon <= 0
        ):
            raise TASK039E1AuditPreparationError("selected horizon is invalid")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "artifact_type": "independent_private_construction_evidence_v1",
            "relation_identity": self.relation_identity,
            "pair_context_identity": self.pair_context_identity,
            "relation_binding_hash": self.relation_binding_hash,
            "source": self.source,
            "source_step_direction": self.source_step_direction,
            "target": self.target,
            "target_response_direction": self.target_response_direction,
            "selected_delay_horizon": self.selected_delay_horizon,
            "source_parameter_record_hash": self.source_parameter_record_hash,
            "target_parameter_record_hash": self.target_parameter_record_hash,
            "d1_evidence_record_hash": self.d1_evidence_record_hash,
            "d2_evidence_record_hash": self.d2_evidence_record_hash,
            "window_constant_bundle_hash": self.window_constant_bundle_hash,
            "confirmation_status": self.confirmation_status,
            "numeric_bindings": [item.to_dict() for item in self.numeric_bindings],
            "evidence_authority": self.evidence_authority,
            "construction_evidence_status": self.construction_evidence_status,
            "runtime_authority_granted": self.runtime_authority_granted,
        }

    @property
    def artifact_hash(self) -> str:
        return _independent_hash(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return {**self._content_dict(), "artifact_hash": self.artifact_hash}


@dataclass(frozen=True)
class IndependentApprovedNumericBundleV1:
    relation_binding_hash: str
    source_threshold_reference: str
    source_stability_reference: str
    target_scale_reference: str
    selected_horizon_reference: str
    window_constant_references: tuple[str, ...]
    d1_evidence_record_hash: str
    d2_evidence_record_hash: str
    approved: bool = True
    runtime_authority_granted: bool = False

    def __post_init__(self) -> None:
        for field_name in (
            "relation_binding_hash",
            "source_threshold_reference",
            "source_stability_reference",
            "target_scale_reference",
            "selected_horizon_reference",
            "d1_evidence_record_hash",
            "d2_evidence_record_hash",
        ):
            _require_hash(getattr(self, field_name), field_name)
        if len(self.window_constant_references) != len(WINDOW_ROLES):
            raise TASK039E1AuditPreparationError(
                "numeric bundle window reference count is invalid"
            )
        for value in self.window_constant_references:
            _require_hash(value, "window_constant_reference")

    @property
    def artifact_hash(self) -> str:
        return _independent_hash(self.to_dict(include_hash=False))

    def to_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload = {
            "schema_version": "1.0.0",
            "artifact_type": "independent_approved_numeric_bundle_v1",
            "relation_binding_hash": self.relation_binding_hash,
            "source_threshold_reference": self.source_threshold_reference,
            "source_stability_reference": self.source_stability_reference,
            "target_scale_reference": self.target_scale_reference,
            "selected_horizon_reference": self.selected_horizon_reference,
            "window_constant_references": list(self.window_constant_references),
            "d1_evidence_record_hash": self.d1_evidence_record_hash,
            "d2_evidence_record_hash": self.d2_evidence_record_hash,
            "approved": self.approved,
            "runtime_authority_granted": self.runtime_authority_granted,
        }
        if include_hash:
            payload["artifact_hash"] = self.artifact_hash
        return payload


@dataclass(frozen=True)
class PublicWindowProtocolConstantV1:
    numeric_role: str
    numeric_value: int | float

    def __post_init__(self) -> None:
        if self.numeric_role not in WINDOW_ROLES:
            raise TASK039E1AuditPreparationError(
                "only window protocol constants may be public"
            )
        _require_finite(self.numeric_value, "numeric_value")

    def to_dict(self) -> dict[str, Any]:
        return {
            "numeric_role": self.numeric_role,
            "numeric_value": self.numeric_value,
        }


@dataclass(frozen=True)
class IndependentPublicManifestEntryV1:
    relation_identity: str
    pair_context_identity: str
    relation_binding_hash: str
    source: str
    source_step_direction: str
    target: str
    target_response_direction: str
    selected_delay_horizon: int
    private_evidence_record_hash: str
    approved_numeric_roles: tuple[str, ...]
    source_parameter_record_hash: str
    target_parameter_record_hash: str
    d1_evidence_record_hash: str
    d2_evidence_record_hash: str
    window_constant_bundle_hash: str
    public_window_protocol_constants: tuple[PublicWindowProtocolConstantV1, ...]
    construction_evidence_status: str = APPROVED_STATUS
    private_calibrated_values_included: bool = False
    raw_hai_included: bool = False
    absolute_private_paths_included: bool = False
    runtime_authority_granted: bool = False

    def __post_init__(self) -> None:
        for field_name in (
            "relation_identity",
            "pair_context_identity",
            "source",
            "target",
        ):
            _require_synthetic(getattr(self, field_name), field_name)
        for field_name in (
            "relation_binding_hash",
            "private_evidence_record_hash",
            "source_parameter_record_hash",
            "target_parameter_record_hash",
            "d1_evidence_record_hash",
            "d2_evidence_record_hash",
            "window_constant_bundle_hash",
        ):
            _require_hash(getattr(self, field_name), field_name)

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "artifact_type": "independent_public_construction_evidence_manifest_v1",
            "relation_identity": self.relation_identity,
            "pair_context_identity": self.pair_context_identity,
            "relation_binding_hash": self.relation_binding_hash,
            "source": self.source,
            "source_step_direction": self.source_step_direction,
            "target": self.target,
            "target_response_direction": self.target_response_direction,
            "selected_delay_horizon": self.selected_delay_horizon,
            "private_evidence_record_hash": self.private_evidence_record_hash,
            "approved_numeric_roles": list(self.approved_numeric_roles),
            "source_parameter_record_hash": self.source_parameter_record_hash,
            "target_parameter_record_hash": self.target_parameter_record_hash,
            "d1_evidence_record_hash": self.d1_evidence_record_hash,
            "d2_evidence_record_hash": self.d2_evidence_record_hash,
            "window_constant_bundle_hash": self.window_constant_bundle_hash,
            "public_window_protocol_constants": [
                item.to_dict() for item in self.public_window_protocol_constants
            ],
            "construction_evidence_status": self.construction_evidence_status,
            "private_calibrated_values_included": (
                self.private_calibrated_values_included
            ),
            "raw_hai_included": self.raw_hai_included,
            "absolute_private_paths_included": (
                self.absolute_private_paths_included
            ),
            "runtime_authority_granted": self.runtime_authority_granted,
        }

    @property
    def artifact_hash(self) -> str:
        return _independent_hash(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return {**self._content_dict(), "artifact_hash": self.artifact_hash}


_PROHIBITED_PUBLIC_KEYS = {
    "source_step_threshold",
    "source_stability_tolerance",
    "target_noise_scale",
    "calibrated_numeric_values",
    "private_numeric_bindings",
    "raw_hai",
    "raw_hai_rows",
    "hai_values",
    "private_path",
    "absolute_path",
}


def audit_public_manifest_sanitization_v1(document: Mapping[str, Any]) -> None:
    """Reject calibrated-value, raw-data, and private-path public leakage."""

    def walk(value: Any, path: str) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                if key in _PROHIBITED_PUBLIC_KEYS:
                    raise TASK039E1AuditPreparationError(
                        f"public calibrated/private leak at {path}.{key}"
                    )
                if key in {
                    "private_calibrated_values_included",
                    "raw_hai_included",
                    "absolute_private_paths_included",
                    "runtime_authority_granted",
                } and item is not False:
                    raise TASK039E1AuditPreparationError(
                        f"public boundary flag preclaimed at {path}.{key}"
                    )
                walk(item, f"{path}.{key}")
        elif isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                walk(item, f"{path}[{index}]")
        elif isinstance(value, str):
            if value.startswith("/") or _ABSOLUTE_WINDOWS.match(value):
                raise TASK039E1AuditPreparationError(
                    f"absolute private path at {path}"
                )

    walk(document, "$manifest")


@dataclass(frozen=True)
class SyntheticConstructionEvidenceAuditDatasetV1:
    e0_cohort_identity_list_hash: str
    public_relation_primitives: tuple[IndependentPublicRelationPrimitiveV1, ...]
    private_evidence_records: tuple[IndependentPrivateConstructionEvidenceV1, ...]
    approved_numeric_bundles: tuple[IndependentApprovedNumericBundleV1, ...]
    public_manifest_entries: tuple[IndependentPublicManifestEntryV1, ...]

    def __post_init__(self) -> None:
        _require_hash(
            self.e0_cohort_identity_list_hash,
            "e0_cohort_identity_list_hash",
        )


@dataclass(frozen=True)
class IndependentEvidenceAuditResultV1:
    confirmed_relation_count: int
    pair_context_count: int
    private_evidence_record_count: int
    numeric_binding_count: int
    public_relation_primitive_count: int
    approved_numeric_bundle_count: int
    public_manifest_entry_count: int
    skipped_relation_count: int
    role_frequencies: tuple[tuple[str, int], ...]
    e0_cohort_identity_preserved: bool
    public_private_separation_passed: bool
    audit_status: str = PREPARATION_STATUS
    real_result_audited: bool = False
    runtime_authority_granted: bool = False

    def __post_init__(self) -> None:
        expected = (
            EXPECTED_RELATIONS,
            EXPECTED_PAIR_CONTEXTS,
            EXPECTED_RELATIONS,
            EXPECTED_NUMERIC_BINDINGS,
            EXPECTED_RELATIONS,
            EXPECTED_RELATIONS,
            EXPECTED_RELATIONS,
            0,
        )
        observed = (
            self.confirmed_relation_count,
            self.pair_context_count,
            self.private_evidence_record_count,
            self.numeric_binding_count,
            self.public_relation_primitive_count,
            self.approved_numeric_bundle_count,
            self.public_manifest_entry_count,
            self.skipped_relation_count,
        )
        if observed != expected:
            raise TASK039E1AuditPreparationError("42/462 accounting mismatch")
        if self.role_frequencies != tuple(
            (role, EXPECTED_RELATIONS) for role in NUMERIC_ROLES
        ):
            raise TASK039E1AuditPreparationError("role frequency mismatch")
        if not self.e0_cohort_identity_preserved:
            raise TASK039E1AuditPreparationError("E0 cohort identity mismatch")
        if not self.public_private_separation_passed:
            raise TASK039E1AuditPreparationError("public/private separation failed")
        if self.real_result_audited or self.runtime_authority_granted:
            raise TASK039E1AuditPreparationError("audit preparation preclaims authority")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "artifact_type": "task039e1_independent_evidence_audit_result_v1",
            "confirmed_relation_count": self.confirmed_relation_count,
            "pair_context_count": self.pair_context_count,
            "private_evidence_record_count": self.private_evidence_record_count,
            "numeric_binding_count": self.numeric_binding_count,
            "public_relation_primitive_count": self.public_relation_primitive_count,
            "approved_numeric_bundle_count": self.approved_numeric_bundle_count,
            "public_manifest_entry_count": self.public_manifest_entry_count,
            "skipped_relation_count": self.skipped_relation_count,
            "role_frequencies": [
                {"numeric_role": role, "count": count}
                for role, count in self.role_frequencies
            ],
            "e0_cohort_identity_preserved": self.e0_cohort_identity_preserved,
            "public_private_separation_passed": (
                self.public_private_separation_passed
            ),
            "audit_status": self.audit_status,
            "real_result_audited": self.real_result_audited,
            "runtime_authority_granted": self.runtime_authority_granted,
        }

    @property
    def artifact_hash(self) -> str:
        return _independent_hash(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return {**self._content_dict(), "artifact_hash": self.artifact_hash}


def _binding_map(
    private: IndependentPrivateConstructionEvidenceV1,
) -> dict[str, IndependentNumericBindingV1]:
    if len(private.numeric_bindings) != EXPECTED_ROLES_PER_RELATION:
        raise TASK039E1AuditPreparationError(
            "private record must contain exactly eleven roles"
        )
    roles = tuple(item.numeric_role for item in private.numeric_bindings)
    if len(set(roles)) != EXPECTED_ROLES_PER_RELATION:
        raise TASK039E1AuditPreparationError("duplicated numeric role")
    if set(roles) != set(NUMERIC_ROLES):
        raise TASK039E1AuditPreparationError("missing or extra numeric role")
    return {item.numeric_role: item for item in private.numeric_bindings}


def audit_independent_relation_evidence_v1(
    primitive: IndependentPublicRelationPrimitiveV1,
    private: IndependentPrivateConstructionEvidenceV1,
    bundle: IndependentApprovedNumericBundleV1,
    manifest: IndependentPublicManifestEntryV1,
) -> tuple[str, ...]:
    """Audit one synthetic record without any production materializer call."""

    relation_fields = (
        "relation_identity",
        "pair_context_identity",
        "relation_binding_hash",
        "source",
        "source_step_direction",
        "target",
        "target_response_direction",
        "selected_delay_horizon",
    )
    for field_name in relation_fields:
        if getattr(private, field_name) != getattr(primitive, field_name):
            raise TASK039E1AuditPreparationError(
                f"relation {field_name} mismatch"
            )
        if getattr(manifest, field_name) != getattr(primitive, field_name):
            raise TASK039E1AuditPreparationError(
                f"public {field_name} mismatch"
            )
    if private.d1_evidence_record_hash != primitive.d1_directional_record_hash:
        raise TASK039E1AuditPreparationError("wrong D1 evidence record")
    if private.d2_evidence_record_hash != primitive.d2_confirmation_record_hash:
        raise TASK039E1AuditPreparationError("wrong D2 evidence record")
    if private.confirmation_status != "calibration_confirmed":
        raise TASK039E1AuditPreparationError("D2 conflict status rejected")
    if private.evidence_authority != APPROVED_EVIDENCE_AUTHORITY:
        raise TASK039E1AuditPreparationError("private evidence is not approved")
    if private.construction_evidence_status != APPROVED_STATUS:
        raise TASK039E1AuditPreparationError("private status is not approved")
    if private.runtime_authority_granted:
        raise TASK039E1AuditPreparationError("runtime authority preclaim rejected")

    by_role = _binding_map(private)
    common_hashes = (
        "relation_binding_hash",
        "source_parameter_record_hash",
        "target_parameter_record_hash",
        "d1_evidence_record_hash",
        "d2_evidence_record_hash",
        "window_constant_bundle_hash",
    )
    for role in NUMERIC_ROLES:
        binding = by_role[role]
        for field_name in common_hashes:
            if getattr(binding, field_name) != getattr(private, field_name):
                raise TASK039E1AuditPreparationError(
                    f"numeric {field_name} mismatch"
                )
        if binding.value_origin != independent_numeric_role_origin_v1(role):
            raise TASK039E1AuditPreparationError("numeric-role origin mismatch")
        if binding.runtime_authority_granted:
            raise TASK039E1AuditPreparationError(
                "numeric binding preclaims runtime authority"
            )
        if binding.recomputed_reference() != binding.numeric_reference:
            raise TASK039E1AuditPreparationError(
                "numeric-reference hash mismatch"
            )
    if by_role["selected_delay_horizon"].numeric_value != primitive.selected_delay_horizon:
        raise TASK039E1AuditPreparationError("selected horizon value mismatch")

    expected_bundle_refs = (
        by_role["source_step_threshold"].numeric_reference,
        by_role["source_stability_tolerance"].numeric_reference,
        by_role["target_noise_scale"].numeric_reference,
        by_role["selected_delay_horizon"].numeric_reference,
    )
    observed_bundle_refs = (
        bundle.source_threshold_reference,
        bundle.source_stability_reference,
        bundle.target_scale_reference,
        bundle.selected_horizon_reference,
    )
    if observed_bundle_refs != expected_bundle_refs:
        raise TASK039E1AuditPreparationError("approved numeric bundle mismatch")
    if bundle.window_constant_references != tuple(
        by_role[role].numeric_reference for role in WINDOW_ROLES
    ):
        raise TASK039E1AuditPreparationError("window reference bundle mismatch")
    if (
        bundle.relation_binding_hash != primitive.relation_binding_hash
        or bundle.d1_evidence_record_hash != primitive.d1_directional_record_hash
        or bundle.d2_evidence_record_hash != primitive.d2_confirmation_record_hash
        or not bundle.approved
        or bundle.runtime_authority_granted
    ):
        raise TASK039E1AuditPreparationError("approved bundle provenance mismatch")

    if manifest.private_evidence_record_hash != private.artifact_hash:
        raise TASK039E1AuditPreparationError("private evidence hash mismatch")
    if manifest.approved_numeric_roles != NUMERIC_ROLES:
        raise TASK039E1AuditPreparationError("public role names mismatch")
    for field_name in (
        "source_parameter_record_hash",
        "target_parameter_record_hash",
        "d1_evidence_record_hash",
        "d2_evidence_record_hash",
        "window_constant_bundle_hash",
    ):
        if getattr(manifest, field_name) != getattr(private, field_name):
            raise TASK039E1AuditPreparationError(
                f"public provenance {field_name} mismatch"
            )
    if (
        manifest.construction_evidence_status != APPROVED_STATUS
        or manifest.private_calibrated_values_included
        or manifest.raw_hai_included
        or manifest.absolute_private_paths_included
        or manifest.runtime_authority_granted
    ):
        raise TASK039E1AuditPreparationError("public boundary preclaim rejected")
    public_window_roles = tuple(
        item.numeric_role for item in manifest.public_window_protocol_constants
    )
    if public_window_roles not in {(), WINDOW_ROLES}:
        raise TASK039E1AuditPreparationError("public window role disclosure mismatch")
    if public_window_roles:
        for public_item in manifest.public_window_protocol_constants:
            if public_item.numeric_value != by_role[public_item.numeric_role].numeric_value:
                raise TASK039E1AuditPreparationError(
                    "public window constant mismatch"
                )
    audit_public_manifest_sanitization_v1(manifest.to_dict())
    return tuple(by_role)


def audit_synthetic_construction_evidence_dataset_v1(
    dataset: SyntheticConstructionEvidenceAuditDatasetV1,
) -> IndependentEvidenceAuditResultV1:
    """Audit exact 42/462 synthetic accounting and E0 identity preservation."""

    collections = (
        dataset.public_relation_primitives,
        dataset.private_evidence_records,
        dataset.approved_numeric_bundles,
        dataset.public_manifest_entries,
    )
    if any(len(items) != EXPECTED_RELATIONS for items in collections):
        raise TASK039E1AuditPreparationError("record collection count must be 42")
    relation_ids = tuple(
        item.relation_binding_hash for item in dataset.public_relation_primitives
    )
    relation_names = tuple(
        item.relation_identity for item in dataset.public_relation_primitives
    )
    directional_identities = tuple(
        (
            item.source,
            item.source_step_direction,
            item.target,
            item.target_response_direction,
        )
        for item in dataset.public_relation_primitives
    )
    if any(
        len(set(values)) != EXPECTED_RELATIONS
        for values in (relation_ids, relation_names, directional_identities)
    ):
        raise TASK039E1AuditPreparationError("duplicate relation rejected")
    context_pairs: dict[str, tuple[str, str]] = {}
    for item in dataset.public_relation_primitives:
        pair = (item.source, item.target)
        previous = context_pairs.setdefault(item.pair_context_identity, pair)
        if previous != pair:
            raise TASK039E1AuditPreparationError("pair context identity mismatch")
    if (
        len(context_pairs) != EXPECTED_PAIR_CONTEXTS
        or len(set(context_pairs.values())) != EXPECTED_PAIR_CONTEXTS
    ):
        raise TASK039E1AuditPreparationError("pair context count must be 23")
    if independent_cohort_identity_list_hash_v1(
        dataset.public_relation_primitives
    ) != dataset.e0_cohort_identity_list_hash:
        raise TASK039E1AuditPreparationError("E0 cohort identity mismatch")

    maps: list[dict[str, Any]] = []
    for items in collections[1:]:
        mapping = {item.relation_binding_hash: item for item in items}
        if len(mapping) != EXPECTED_RELATIONS or set(mapping) != set(relation_ids):
            raise TASK039E1AuditPreparationError(
                "relation partition mismatch or duplicate relation"
            )
        maps.append(mapping)
    frequencies = {role: 0 for role in NUMERIC_ROLES}
    audited = 0
    for primitive in dataset.public_relation_primitives:
        roles = audit_independent_relation_evidence_v1(
            primitive,
            maps[0][primitive.relation_binding_hash],
            maps[1][primitive.relation_binding_hash],
            maps[2][primitive.relation_binding_hash],
        )
        audited += 1
        for role in roles:
            frequencies[role] += 1
    return IndependentEvidenceAuditResultV1(
        confirmed_relation_count=len(dataset.public_relation_primitives),
        pair_context_count=len(
            {item.pair_context_identity for item in dataset.public_relation_primitives}
        ),
        private_evidence_record_count=len(dataset.private_evidence_records),
        numeric_binding_count=sum(
            len(item.numeric_bindings) for item in dataset.private_evidence_records
        ),
        public_relation_primitive_count=len(dataset.public_relation_primitives),
        approved_numeric_bundle_count=len(dataset.approved_numeric_bundles),
        public_manifest_entry_count=len(dataset.public_manifest_entries),
        skipped_relation_count=EXPECTED_RELATIONS - audited,
        role_frequencies=tuple((role, frequencies[role]) for role in NUMERIC_ROLES),
        e0_cohort_identity_preserved=True,
        public_private_separation_passed=True,
    )


@dataclass(frozen=True)
class IndependentResolvedNumericValueV1:
    relation_binding_hash: str
    numeric_role: str
    numeric_reference: str
    private_evidence_record_hash: str
    numeric_value: int | float
    construction_only: bool = True
    runtime_authority_granted: bool = False

    def __post_init__(self) -> None:
        for field_name in (
            "relation_binding_hash",
            "numeric_reference",
            "private_evidence_record_hash",
        ):
            _require_hash(getattr(self, field_name), field_name)
        independent_numeric_role_origin_v1(self.numeric_role)
        _require_finite(self.numeric_value, "numeric_value")
        if not self.construction_only or self.runtime_authority_granted:
            raise TASK039E1AuditPreparationError(
                "resolved value must remain construction-only"
            )


def audit_resolve_numeric_reference_v1(
    *,
    proposal_numeric_reference: str,
    relation_binding_hash: str,
    numeric_role: str,
    private_evidence_record_hash: str,
    private_evidence: IndependentPrivateConstructionEvidenceV1,
) -> IndependentResolvedNumericValueV1:
    """Verify and resolve one reference with the independent hash oracle."""

    for field_name, value in (
        ("proposal_numeric_reference", proposal_numeric_reference),
        ("relation_binding_hash", relation_binding_hash),
        ("private_evidence_record_hash", private_evidence_record_hash),
    ):
        _require_hash(value, field_name)
    if relation_binding_hash != private_evidence.relation_binding_hash:
        raise TASK039E1AuditPreparationError("relation mismatch rejected")
    if private_evidence_record_hash != private_evidence.artifact_hash:
        raise TASK039E1AuditPreparationError("private evidence hash mismatch")
    if (
        private_evidence.evidence_authority != APPROVED_EVIDENCE_AUTHORITY
        or private_evidence.construction_evidence_status != APPROVED_STATUS
        or private_evidence.runtime_authority_granted
    ):
        raise TASK039E1AuditPreparationError("evidence authority mismatch")
    matches = tuple(
        item
        for item in private_evidence.numeric_bindings
        if item.numeric_reference == proposal_numeric_reference
    )
    if len(matches) != 1:
        raise TASK039E1AuditPreparationError("numeric reference is not unique")
    binding = matches[0]
    if binding.numeric_role != numeric_role:
        raise TASK039E1AuditPreparationError("numeric role mismatch")
    if binding.recomputed_reference() != binding.numeric_reference:
        raise TASK039E1AuditPreparationError("numeric-reference hash mismatch")
    return IndependentResolvedNumericValueV1(
        relation_binding_hash=relation_binding_hash,
        numeric_role=numeric_role,
        numeric_reference=proposal_numeric_reference,
        private_evidence_record_hash=private_evidence_record_hash,
        numeric_value=binding.numeric_value,
    )


@dataclass(frozen=True)
class FuturePrivateLedgerReplayDesignV1:
    logical_inputs: tuple[str, ...] = (
        "d1_source_ledger",
        "d1_target_ledger",
        "d1_directional_ledger",
        "d2_confirmation_ledger",
        "e1_private_construction_evidence_ledger",
    )
    expected_relation_count: int = EXPECTED_RELATIONS
    expected_numeric_binding_count: int = EXPECTED_NUMERIC_BINDINGS
    real_reads_enabled: bool = False
    separate_authorization_required: bool = True
    raw_hai_allowed: bool = False
    runtime_authority_granted: bool = False

    def __post_init__(self) -> None:
        if len(self.logical_inputs) != 5 or len(set(self.logical_inputs)) != 5:
            raise TASK039E1AuditPreparationError("replay ledger design is invalid")
        if (
            self.expected_relation_count != EXPECTED_RELATIONS
            or self.expected_numeric_binding_count != EXPECTED_NUMERIC_BINDINGS
            or self.real_reads_enabled
            or not self.separate_authorization_required
            or self.raw_hai_allowed
            or self.runtime_authority_granted
        ):
            raise TASK039E1AuditPreparationError("replay design preclaims access")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "artifact_type": "task039e1_future_private_ledger_replay_design_v1",
            "logical_inputs": list(self.logical_inputs),
            "expected_relation_count": self.expected_relation_count,
            "expected_numeric_binding_count": self.expected_numeric_binding_count,
            "real_reads_enabled": self.real_reads_enabled,
            "separate_authorization_required": self.separate_authorization_required,
            "raw_hai_allowed": self.raw_hai_allowed,
            "runtime_authority_granted": self.runtime_authority_granted,
        }

    @property
    def artifact_hash(self) -> str:
        return _independent_hash(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        return {**self._content_dict(), "artifact_hash": self.artifact_hash}


FUTURE_REPLAY_DESIGN = FuturePrivateLedgerReplayDesignV1()


def attempt_future_private_ledger_replay_v1(
    *,
    d1_source_ledger: str,
    d1_target_ledger: str,
    d1_directional_ledger: str,
    d2_confirmation_ledger: str,
    e1_private_evidence_ledger: str,
    authorization: object | None = None,
) -> None:
    """Fail before opening any path; PREP has no valid authorization type."""

    paths = (
        d1_source_ledger,
        d1_target_ledger,
        d1_directional_ledger,
        d2_confirmation_ledger,
        e1_private_evidence_ledger,
    )
    if any("hai" in value.lower() for value in paths):
        raise TASK039E1AuditPreparationError("HAI path rejected")
    if any(value.startswith("/") or _ABSOLUTE_WINDOWS.match(value) for value in paths):
        raise TASK039E1AuditPreparationError("absolute private path rejected")
    raise TASK039E1AuditPreparationError(
        "real private-ledger replay is disabled in audit preparation"
    )


def assert_audit_preparation_boundary_v1(
    *,
    real_e1_result: object | None = None,
    real_d2_result: object | None = None,
    d1_private_ledger: object | None = None,
    d2_private_ledger: object | None = None,
    e1_private_ledger: object | None = None,
    real_confirmed_identity: object | None = None,
    hai_input: object | None = None,
    llm: object | None = None,
) -> None:
    if any(
        value is not None
        for value in (
            real_e1_result,
            real_d2_result,
            d1_private_ledger,
            d2_private_ledger,
            e1_private_ledger,
            real_confirmed_identity,
            hai_input,
            llm,
        )
    ):
        raise TASK039E1AuditPreparationError(
            "audit preparation accepts synthetic inputs only"
        )


__all__ = [
    "APPROVED_EVIDENCE_AUTHORITY",
    "BASE_COMMIT",
    "BRANCH",
    "CALIBRATED_PRIVATE_ROLES",
    "D1_PRIVATE_LEDGERS_ACCESSED",
    "D2_PRIVATE_LEDGERS_ACCESSED",
    "E1_AUTHORIZED",
    "E1_PRIVATE_LEDGER_ACCESSED",
    "E2_AUTHORIZATION_CREATED",
    "EXPECTED_NUMERIC_BINDINGS",
    "EXPECTED_PAIR_CONTEXTS",
    "EXPECTED_RELATIONS",
    "EXPECTED_ROLES_PER_RELATION",
    "FUTURE_REPLAY_DESIGN",
    "FuturePrivateLedgerReplayDesignV1",
    "HAI_ACCESSED",
    "IndependentApprovedNumericBundleV1",
    "IndependentEvidenceAuditResultV1",
    "IndependentNumericBindingV1",
    "IndependentPrivateConstructionEvidenceV1",
    "IndependentPublicManifestEntryV1",
    "IndependentPublicRelationPrimitiveV1",
    "IndependentResolvedNumericValueV1",
    "LLM_AVAILABLE",
    "LLM_CALLED",
    "NUMERIC_ROLES",
    "PREPARATION_STATUS",
    "PublicWindowProtocolConstantV1",
    "REAL_CONFIRMED_IDENTITIES_CONSUMED",
    "REAL_D2_RESULT_ACCESSED",
    "REAL_E1_RESULT_ACCESSED",
    "ROLE_ORIGINS",
    "RULE_GENERATION_AVAILABLE",
    "RULE_GENERATED",
    "RUNTIME_AUTHORITY_GRANTED",
    "SyntheticConstructionEvidenceAuditDatasetV1",
    "TASK039E1AuditPreparationError",
    "WINDOW_ROLES",
    "assert_audit_preparation_boundary_v1",
    "attempt_future_private_ledger_replay_v1",
    "audit_independent_relation_evidence_v1",
    "audit_public_manifest_sanitization_v1",
    "audit_resolve_numeric_reference_v1",
    "audit_synthetic_construction_evidence_dataset_v1",
    "independent_cohort_identity_list_hash_v1",
    "independent_numeric_reference_v1",
    "independent_numeric_role_origin_v1",
]
