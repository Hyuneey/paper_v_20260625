"""Authorized TASK-039E1 construction-evidence materialization.

This module is intentionally data-loader free.  It accepts only the frozen
D1/D2 JSON ledgers and the public E0 confirmed-relation cohort.  It never
opens HAI, calls a model service, generates a rule, or grants runtime authority.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from paperworks.v6.common import (
    V6_FOUNDATION_SCHEMA_VERSION,
    V6FoundationError,
    require_identifier,
    require_sha256,
    stable_hash_v1,
)
from paperworks.v6.task039e0_rule_construction_prep_v1 import (
    ApprovedNumericEvidenceBundleV1,
    ConfirmedRelationPrimitiveV1,
)
from paperworks.v6.task039e0_rule_construction_protocol_v1 import (
    ConfirmedRelationIdentityCohortV1,
    ConfirmedRelationIdentityV1,
)
from paperworks.v6.task039e1_evidence_materialization_prep_v1 import (
    NUMERIC_ROLE_ORDER,
    ConstructionNumericRoleV1,
)


TASK_ID = "TASK-039E1"
STATUS = "passed_task039e1_evidence_materialization"
PROCESS = "P1"
RELATION_FAMILY = "continuous_step_delayed_response_v1"
EXPECTED_RELATIONS = 42
EXPECTED_PAIRS = 23
EXPECTED_NUMERIC_BINDINGS = 462

E0_AUTHORIZATION_HASH = "d209b8332705535b8addc62e186e834288ab7c12f8454e8be85265321b663ae6"
E0_PROTOCOL_BUNDLE_HASH = "a95aecffeaff82d0c67f966f19293ef947827cb0e1e7621a38ecd7c1fd96e17b"
E0_MATERIALIZATION_POLICY_HASH = "feb77765a3447c0c896cb5dc57b5157e371fda7c7a35fd86403ba2010d38a5b9"
E0_COHORT_HASH = "e71fa69999dbc18310ebb1730fd1d0ea36403763e891b99841ab8cef7ec18732"
E0_IDENTITY_LIST_HASH = "c7f198388bbe53f44bebe5378116a35cc9ed342de7c4df29e255cb5d39cf0479"
E1_AUTHORIZATION_HASH = "03ad2a9e534d553cad75aa811090c1255988156bf1d2a217fb6b883620e05580"

D0_PROTOCOL_BUNDLE_HASH = "888e3d642eba6f8ad8784d428bc4b27d7db7592d34779ba9a1f817860d76e1eb"
SOURCE_EVENT_POLICY_HASH = "1f07a72b380b9ffb2ceb42e029517ef42716145062a57b1770d118b9db252342"
TARGET_RESPONSE_POLICY_HASH = "4b007b9511152396e03722ad8ce0e9cf659ebef2760cef5110414e4ce4bcbeaf"
CONFIRMATION_POLICY_HASH = "83419f6acefaeb21ebc329d5ff9df8563e9636da72ad5367318a172df8fb0b27"

D1_SOURCE_LEDGER_HASH = "3eb6ff199dbc67b183d35a804754e557bdfa869a899c754e551cd77e8dcfb304"
D1_TARGET_LEDGER_HASH = "f36f4b424c85b228043f9685a22a25c73d6b165e28714b627cf51e8bbb77f96e"
D1_DIRECTIONAL_LEDGER_HASH = "e372d7ccf4a7dde5f7ccd91049cc73b443b3b19a3a0c563f451aea50e8faddc7"
D2_CONFIRMATION_LEDGER_HASH = "d349421ae9a866b924c329dcb2546088466866e09f45851ec5d18090509dc062"
D2_RESULT_HASH = "3b5bdce629b6ed2bcf26751fae4e870cb63cac1e9fd3e5d3022085615c3ad09d"

PRIVATE_SOURCE_LEDGER_NAME = "TASK-039D1_SOURCE_PARAMETER_LEDGER.json"
PRIVATE_TARGET_LEDGER_NAME = "TASK-039D1_TARGET_PARAMETER_LEDGER.json"
PRIVATE_DIRECTIONAL_LEDGER_NAME = "TASK-039D1_DIRECTIONAL_FIT_LEDGER.json"
PRIVATE_D2_LEDGER_NAME = "TASK039D2_DIRECTIONAL_CONFIRMATION_LEDGER.json"
PRIVATE_E1_LEDGER_NAME = "TASK039E1_PRIVATE_CONSTRUCTION_EVIDENCE_LEDGER.json"

SOURCE_PARAMETER_ORIGIN = "d1_fit_derived_source_parameter"
TARGET_PARAMETER_ORIGIN = "d1_fit_derived_target_parameter"
HORIZON_ORIGIN = "d1_fit_selected_horizon"
WINDOW_CONSTANT_ORIGIN = "d0_preregistered_window_constant"
APPROVED_EVIDENCE_AUTHORITY = "approved_construction_evidence"

SCHEMA_FILES: Mapping[str, str] = {
    "task039e1_real_window_constant_bundle_v1": "schemas/v6/task039e1_real_window_constant_bundle_v1_schema.json",
    "task039e1_real_private_numeric_binding_v1": "schemas/v6/task039e1_real_private_numeric_binding_v1_schema.json",
    "task039e1_real_private_construction_evidence_v1": "schemas/v6/task039e1_real_private_construction_evidence_v1_schema.json",
    "task039e1_private_construction_evidence_ledger_v1": "schemas/v6/task039e1_private_construction_evidence_ledger_v1_schema.json",
    "task039e1_private_ledger_binding_v1": "schemas/v6/task039e1_private_ledger_binding_v1_schema.json",
    "task039e1_construction_evidence_manifest_v1": "schemas/v6/task039e1_construction_evidence_manifest_v1_schema.json",
    "task039e1_construction_evidence_cohort_v1": "schemas/v6/task039e1_construction_evidence_cohort_v1_schema.json",
    "task039e1_materialization_result_v1": "schemas/v6/task039e1_materialization_result_v1_schema.json",
    "task039e1_data_access_audit_v1": "schemas/v6/task039e1_data_access_audit_v1_schema.json",
    "task039e1_execution_receipt_v1": "schemas/v6/task039e1_execution_receipt_v1_schema.json",
}


class TASK039E1Error(V6FoundationError):
    """Raised when E1 authorization, provenance, or boundaries fail closed."""


def _without_hash(document: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in document.items() if key != "artifact_hash"}


def _with_hash(content: Mapping[str, Any]) -> dict[str, Any]:
    payload = json.loads(json.dumps(content, sort_keys=True, allow_nan=False))
    return {**payload, "artifact_hash": stable_hash_v1(payload)}


def verify_self_hash_v1(document: Mapping[str, Any], *, expected_hash: str | None = None) -> str:
    supplied = str(document.get("artifact_hash", ""))
    require_sha256(supplied, "artifact_hash")
    observed = stable_hash_v1(_without_hash(document))
    if observed != supplied or (expected_hash is not None and supplied != expected_hash):
        raise TASK039E1Error("artifact self-hash mismatch")
    return supplied


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TASK039E1Error(f"required artifact unavailable: {path.name}") from exc
    if not isinstance(value, dict):
        raise TASK039E1Error("artifact must be a JSON object")
    return value


def _exact_fields(document: Mapping[str, Any], fields: set[str], label: str) -> None:
    if set(document) != fields:
        raise TASK039E1Error(f"{label} fields differ from the frozen contract")


def _require_git_sha(value: str, field_name: str) -> str:
    if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
        raise TASK039E1Error(f"{field_name} must be a lowercase Git SHA-1")
    return value


def validate_e1_authorization_v1(document: Mapping[str, Any]) -> None:
    """Validate authority before any private-root operation."""

    verify_self_hash_v1(document, expected_hash=E1_AUTHORIZATION_HASH)
    expected = {
        "status": "authorized_task039e1_evidence_materialization_only",
        "protocol_bundle_hash": E0_PROTOCOL_BUNDLE_HASH,
        "cohort_hash": E0_COHORT_HASH,
        "identity_list_hash": E0_IDENTITY_LIST_HASH,
        "materialization_policy_hash": E0_MATERIALIZATION_POLICY_HASH,
        "confirmed_relation_count": 42,
        "d1_source_private_ledger_read_authorized": True,
        "d1_target_private_ledger_read_authorized": True,
        "d1_directional_private_ledger_read_authorized": True,
        "d2_private_confirmation_ledger_read_authorized": True,
        "public_hash_provenance_manifest_authorized": True,
        "hai_access_authorized": False,
        "train1_train2_train3_reread_authorized": False,
        "train4_authorized": False,
        "test_labels_attacks_authorized": False,
        "llm_calls_authorized": False,
        "t0_generation_authorized": False,
        "t1_t1b_t2_generation_authorized": False,
        "direct_number_ablation_execution_authorized": False,
        "rule_v2_materialization_authorized": False,
        "agent_execution_authorized": False,
        "detector_runtime_authorized": False,
    }
    if any(document.get(key) != value for key, value in expected.items()):
        raise TASK039E1Error("blocked_task039e1_authorization_mismatch")


def load_e0_cohort_v1(document: Mapping[str, Any]) -> ConfirmedRelationIdentityCohortV1:
    verify_self_hash_v1(document, expected_hash=E0_COHORT_HASH)
    relations_raw = document.get("relations")
    if not isinstance(relations_raw, list):
        raise TASK039E1Error("failed_task039e1_relation_binding")
    relations: list[ConfirmedRelationIdentityV1] = []
    for item in relations_raw:
        if not isinstance(item, Mapping):
            raise TASK039E1Error("failed_task039e1_relation_binding")
        relation = ConfirmedRelationIdentityV1(
            source=str(item.get("source", "")),
            source_step_direction=str(item.get("source_step_direction", "")),
            target=str(item.get("target", "")),
            target_response_direction=str(item.get("target_response_direction", "")),
            selected_delay_horizon_seconds=item.get("selected_delay_horizon_seconds"),
            d1_directional_record_hash=str(item.get("d1_directional_record_hash", "")),
            d2_confirmation_record_hash=str(item.get("d2_confirmation_record_hash", "")),
            d2_result_hash=str(item.get("d2_result_hash", "")),
            relation_family=str(item.get("relation_family", "")),
        )
        if relation.to_dict() != dict(item):
            raise TASK039E1Error("failed_task039e1_relation_binding")
        relations.append(relation)
    cohort = ConfirmedRelationIdentityCohortV1(
        tuple(relations),
        source_artifact_hash=str(document.get("source_artifact_hash", "")),
        process=str(document.get("process", "")),
        relation_family=str(document.get("relation_family", "")),
        scientific_ranking_created=document.get("scientific_ranking_created"),
        candidate_method_preference_used=document.get("candidate_method_preference_used"),
        private_numeric_values_included=document.get("private_numeric_values_included"),
    )
    if cohort.to_dict() != dict(document):
        raise TASK039E1Error("failed_task039e1_relation_binding")
    if cohort.identity_list_hash != E0_IDENTITY_LIST_HASH:
        raise TASK039E1Error("failed_task039e1_relation_binding")
    return cohort


def validate_external_roots_v1(
    *, repository_root: Path, d1_private_value: str, d2_private_value: str, e1_private_value: str
) -> tuple[Path, Path, Path]:
    raw_values = (d1_private_value, d2_private_value, e1_private_value)
    if any(not value or ".." in Path(value).parts or not Path(value).is_absolute() for value in raw_values):
        raise TASK039E1Error("private roots must be explicit absolute traversal-free paths")
    repository = repository_root.resolve(strict=True)
    d1_root = Path(d1_private_value).resolve(strict=True)
    d2_root = Path(d2_private_value).resolve(strict=True)
    e1_requested = Path(e1_private_value)
    e1_requested.mkdir(parents=True, exist_ok=True)
    e1_root = e1_requested.resolve(strict=True)
    roots = (d1_root, d2_root, e1_root)
    if len({str(path).casefold() for path in roots}) != 3:
        raise TASK039E1Error("private roots must be distinct")
    for path in roots:
        try:
            path.relative_to(repository)
        except ValueError:
            pass
        else:
            raise TASK039E1Error("private root must remain outside Git")
    return roots


def load_private_ledger_v1(
    path: Path, *, expected_hash: str, expected_type: str, expected_count: int
) -> dict[str, Any]:
    ledger = _load_json(path)
    verify_self_hash_v1(ledger, expected_hash=expected_hash)
    if ledger.get("artifact_type") != expected_type or ledger.get("record_count") != expected_count:
        raise TASK039E1Error("failed_task039e1_private_ledger_binding")
    records = ledger.get("records")
    if not isinstance(records, list) or len(records) != expected_count:
        raise TASK039E1Error("failed_task039e1_private_ledger_binding")
    hashes: list[str] = []
    for record in records:
        if not isinstance(record, dict):
            raise TASK039E1Error("private record must be an object")
        hashes.append(verify_self_hash_v1(record))
    if len(set(hashes)) != expected_count:
        raise TASK039E1Error("private record hashes must be unique")
    return ledger


@dataclass(frozen=True)
class PreregisteredWindowConstantBundleV1:
    source_pre_window_seconds: int = 5
    source_post_window_seconds: int = 5
    minimum_source_stability_fraction: float = 0.8
    source_refractory_seconds: int = 10
    cross_source_isolation_radius_seconds: int = 2
    target_baseline_window_seconds: int = 5
    target_response_window_seconds: int = 3

    def __post_init__(self) -> None:
        if (
            self.source_pre_window_seconds,
            self.source_post_window_seconds,
            self.minimum_source_stability_fraction,
            self.source_refractory_seconds,
            self.cross_source_isolation_radius_seconds,
            self.target_baseline_window_seconds,
            self.target_response_window_seconds,
        ) != (5, 5, 0.8, 10, 2, 5, 3):
            raise TASK039E1Error("D0 window constants differ")

    def _content(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "task039e1_real_window_constant_bundle_v1",
            "bundle_identity": "task039e1_preregistered_window_constants_v1",
            "d0_protocol_bundle_hash": D0_PROTOCOL_BUNDLE_HASH,
            "source_event_policy_hash": SOURCE_EVENT_POLICY_HASH,
            "target_response_policy_hash": TARGET_RESPONSE_POLICY_HASH,
            "confirmation_policy_hash": CONFIRMATION_POLICY_HASH,
            "source_pre_window_seconds": self.source_pre_window_seconds,
            "source_post_window_seconds": self.source_post_window_seconds,
            "minimum_source_stability_fraction": self.minimum_source_stability_fraction,
            "source_refractory_seconds": self.source_refractory_seconds,
            "cross_source_isolation_radius_seconds": self.cross_source_isolation_radius_seconds,
            "target_baseline_window_seconds": self.target_baseline_window_seconds,
            "target_response_window_seconds": self.target_response_window_seconds,
            "value_origin": WINDOW_CONSTANT_ORIGIN,
            "llm_generated": False,
            "runtime_authority": False,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content())


def _origin_for_role(role: str) -> str:
    if role in {"source_step_threshold", "source_stability_tolerance"}:
        return SOURCE_PARAMETER_ORIGIN
    if role == "target_noise_scale":
        return TARGET_PARAMETER_ORIGIN
    if role == "selected_delay_horizon_seconds":
        return HORIZON_ORIGIN
    if role in NUMERIC_ROLE_ORDER:
        return WINDOW_CONSTANT_ORIGIN
    raise TASK039E1Error("numeric role is not approved")


@dataclass(frozen=True)
class PrivateNumericBindingV1:
    relation_identity: str
    numeric_role: str
    numeric_value: int | float
    value_origin: str
    source_parameter_record_hash: str
    target_parameter_record_hash: str
    d1_fit_evidence_hash: str
    d2_confirmation_evidence_hash: str
    window_constant_bundle_hash: str

    def __post_init__(self) -> None:
        require_identifier(self.relation_identity, "relation_identity")
        if self.numeric_role not in NUMERIC_ROLE_ORDER or self.value_origin != _origin_for_role(self.numeric_role):
            raise TASK039E1Error("numeric role origin differs")
        if isinstance(self.numeric_value, bool) or not isinstance(self.numeric_value, (int, float)) or not math.isfinite(self.numeric_value):
            raise TASK039E1Error("numeric value must be finite")
        for name in (
            "source_parameter_record_hash", "target_parameter_record_hash",
            "d1_fit_evidence_hash", "d2_confirmation_evidence_hash",
            "window_constant_bundle_hash",
        ):
            require_sha256(getattr(self, name), name)

    def _content(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "task039e1_real_private_numeric_binding_v1",
            "relation_identity": self.relation_identity,
            "numeric_role": self.numeric_role,
            "numeric_value": self.numeric_value,
            "value_origin": self.value_origin,
            "source_parameter_record_hash": self.source_parameter_record_hash,
            "target_parameter_record_hash": self.target_parameter_record_hash,
            "d1_fit_evidence_hash": self.d1_fit_evidence_hash,
            "d2_confirmation_evidence_hash": self.d2_confirmation_evidence_hash,
            "window_constant_bundle_hash": self.window_constant_bundle_hash,
            "evidence_authority": APPROVED_EVIDENCE_AUTHORITY,
            "llm_generated": False,
            "runtime_authority": False,
        }

    @property
    def numeric_reference(self) -> str:
        return stable_hash_v1(self._content())

    def to_dict(self) -> dict[str, Any]:
        return {**self._content(), "numeric_reference": self.numeric_reference}


@dataclass(frozen=True)
class PrivateConstructionEvidenceV1:
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
    numeric_bindings: tuple[PrivateNumericBindingV1, ...]

    def __post_init__(self) -> None:
        require_sha256(self.relation_binding_hash, "relation_binding_hash")
        require_identifier(self.relation_identity, "relation_identity")
        if tuple(item.numeric_role for item in self.numeric_bindings) != NUMERIC_ROLE_ORDER:
            raise TASK039E1Error("private evidence must contain the exact eleven roles")
        if len({item.numeric_reference for item in self.numeric_bindings}) != 11:
            raise TASK039E1Error("numeric references must be unique per relation")
        for item in self.numeric_bindings:
            if item.relation_identity != self.relation_identity:
                raise TASK039E1Error("numeric relation binding differs")

    def _content(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "task039e1_real_private_construction_evidence_v1",
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
            "d2_confirmation_evidence_hash": self.d2_confirmation_evidence_hash,
            "window_constant_bundle_hash": self.window_constant_bundle_hash,
            "numeric_bindings": [item.to_dict() for item in self.numeric_bindings],
            "evidence_authority": APPROVED_EVIDENCE_AUTHORITY,
            "construction_evidence_status": "approved",
            "private_record": True,
            "rule_generated": False,
            "runtime_authority": False,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content())

    def to_dict(self) -> dict[str, Any]:
        return _with_hash(self._content())


def _record_index(ledger: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {str(record["artifact_hash"]): record for record in ledger["records"]}


def _derive_numeric_bindings(
    *, relation: Any, source_record: Mapping[str, Any], target_record: Mapping[str, Any],
    d1_record: Mapping[str, Any], d2_record: Mapping[str, Any], window: PreregisteredWindowConstantBundleV1,
) -> tuple[PrivateNumericBindingV1, ...]:
    values: Mapping[str, int | float] = {
        "source_step_threshold": source_record["source_step_threshold"],
        "source_stability_tolerance": source_record["source_stability_tolerance"],
        "target_noise_scale": target_record["target_noise_scale"],
        "selected_delay_horizon_seconds": d1_record["selected_horizon_seconds"],
        "source_pre_window_seconds": window.source_pre_window_seconds,
        "source_post_window_seconds": window.source_post_window_seconds,
        "minimum_source_stability_fraction": window.minimum_source_stability_fraction,
        "source_refractory_seconds": window.source_refractory_seconds,
        "cross_source_isolation_radius_seconds": window.cross_source_isolation_radius_seconds,
        "target_baseline_window_seconds": window.target_baseline_window_seconds,
        "target_response_window_seconds": window.target_response_window_seconds,
    }
    common = {
        "relation_identity": relation.relation_identity,
        "source_parameter_record_hash": source_record["artifact_hash"],
        "target_parameter_record_hash": target_record["artifact_hash"],
        "d1_fit_evidence_hash": d1_record["artifact_hash"],
        "d2_confirmation_evidence_hash": d2_record["artifact_hash"],
        "window_constant_bundle_hash": window.artifact_hash,
    }
    return tuple(
        PrivateNumericBindingV1(
            numeric_role=role, numeric_value=values[role], value_origin=_origin_for_role(role), **common
        ) for role in NUMERIC_ROLE_ORDER
    )


def _assert_relation_bindings(
    relation: Any, source: Mapping[str, Any], target: Mapping[str, Any],
    d1: Mapping[str, Any], d2: Mapping[str, Any],
) -> None:
    expected = (
        relation.source, relation.target, relation.source_step_direction,
        relation.target_response_direction, relation.selected_delay_horizon_seconds,
    )
    d1_observed = (
        d1.get("source"), d1.get("target"), d1.get("source_step_direction"),
        d1.get("selected_target_direction"), d1.get("selected_horizon_seconds"),
    )
    d2_observed = (
        d2.get("source"), d2.get("target"), d2.get("source_step_direction"),
        d2.get("target_response_direction"), d2.get("selected_horizon_seconds"),
    )
    if expected != d1_observed or expected != d2_observed:
        raise TASK039E1Error("failed_task039e1_relation_binding")
    if d1.get("fit_result") != "fit_supported" or d2.get("confirmation_status") != "calibration_confirmed":
        raise TASK039E1Error("failed_task039e1_relation_binding")
    if d1.get("lower_ranked_fallback_used") is not False:
        raise TASK039E1Error("failed_task039e1_relation_binding")
    if d2.get("d1_directional_record_hash") != d1.get("artifact_hash"):
        raise TASK039E1Error("failed_task039e1_relation_binding")
    if source.get("source") != relation.source or source.get("parameter_status") != "supported":
        raise TASK039E1Error("failed_task039e1_relation_binding")
    if target.get("target") != relation.target:
        raise TASK039E1Error("failed_task039e1_relation_binding")
    source_hash, target_hash = source["artifact_hash"], target["artifact_hash"]
    if d1.get("source_parameter_ref") != source_hash or d1.get("target_parameter_ref") != target_hash:
        raise TASK039E1Error("failed_task039e1_relation_binding")
    if d2.get("source_parameter_record_hash") != source_hash or d2.get("target_parameter_record_hash") != target_hash:
        raise TASK039E1Error("failed_task039e1_relation_binding")


def resolve_private_numeric_reference_v1(
    *, proposal_numeric_reference: str, relation_binding_hash: str, numeric_role: str,
    private_evidence_record_hash: str, private_evidence: PrivateConstructionEvidenceV1,
) -> dict[str, Any]:
    require_sha256(proposal_numeric_reference, "proposal_numeric_reference")
    require_sha256(relation_binding_hash, "relation_binding_hash")
    require_sha256(private_evidence_record_hash, "private_evidence_record_hash")
    if relation_binding_hash != private_evidence.relation_binding_hash or private_evidence_record_hash != private_evidence.artifact_hash:
        raise TASK039E1Error("private evidence binding mismatch")
    matches = [item for item in private_evidence.numeric_bindings if item.numeric_reference == proposal_numeric_reference]
    if len(matches) != 1 or matches[0].numeric_role != numeric_role:
        raise TASK039E1Error("numeric reference or role mismatch")
    return _with_hash({
        "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
        "artifact_type": "task039e1_resolved_private_numeric_value_v1",
        "relation_binding_hash": relation_binding_hash,
        "numeric_role": numeric_role,
        "numeric_reference": proposal_numeric_reference,
        "private_evidence_record_hash": private_evidence_record_hash,
        "numeric_value": matches[0].numeric_value,
        "construction_only": True,
        "runtime_authority": False,
    })


def materialize_from_ledgers_v1(
    *, cohort: ConfirmedRelationIdentityCohortV1, source_ledger: Mapping[str, Any],
    target_ledger: Mapping[str, Any], directional_ledger: Mapping[str, Any],
    d2_ledger: Mapping[str, Any], execution_code_commit: str,
) -> dict[str, Any]:
    _require_git_sha(execution_code_commit, "execution_code_commit")
    source_by_name = {record["source"]: record for record in source_ledger["records"]}
    target_by_name = {record["target"]: record for record in target_ledger["records"]}
    d1_by_hash = _record_index(directional_ledger)
    d2_by_hash = _record_index(d2_ledger)
    window = PreregisteredWindowConstantBundleV1()
    private_records: list[PrivateConstructionEvidenceV1] = []
    primitives: list[dict[str, Any]] = []
    bundles: list[dict[str, Any]] = []
    manifest_entries: list[dict[str, Any]] = []

    for relation in cohort.relations:
        try:
            source = source_by_name[relation.source]
            target = target_by_name[relation.target]
            d1 = d1_by_hash[relation.d1_directional_record_hash]
            d2 = d2_by_hash[relation.d2_confirmation_record_hash]
        except KeyError as exc:
            raise TASK039E1Error("failed_task039e1_relation_binding") from exc
        _assert_relation_bindings(relation, source, target, d1, d2)
        numeric = _derive_numeric_bindings(
            relation=relation, source_record=source, target_record=target,
            d1_record=d1, d2_record=d2, window=window,
        )
        by_role = {item.numeric_role: item.numeric_reference for item in numeric}
        primitive = ConfirmedRelationPrimitiveV1(
            relation_identity=relation.relation_identity,
            source=relation.source,
            source_step_direction=relation.source_step_direction,
            target=relation.target,
            target_response_direction=relation.target_response_direction,
            selected_delay_horizon_seconds=relation.selected_delay_horizon_seconds,
            approved_source_threshold_reference=by_role["source_step_threshold"],
            approved_source_stability_reference=by_role["source_stability_tolerance"],
            approved_target_scale_reference=by_role["target_noise_scale"],
            fit_evidence_reference=d1["artifact_hash"],
            confirmation_evidence_reference=d2["artifact_hash"],
        )
        private = PrivateConstructionEvidenceV1(
            relation_binding_hash=primitive.binding_hash,
            relation_identity=relation.relation_identity,
            source=relation.source,
            source_step_direction=relation.source_step_direction,
            target=relation.target,
            target_response_direction=relation.target_response_direction,
            selected_horizon_seconds=relation.selected_delay_horizon_seconds,
            source_parameter_record_hash=source["artifact_hash"],
            target_parameter_record_hash=target["artifact_hash"],
            d1_fit_evidence_hash=d1["artifact_hash"],
            d2_confirmation_evidence_hash=d2["artifact_hash"],
            window_constant_bundle_hash=window.artifact_hash,
            numeric_bindings=numeric,
        )
        window_refs = tuple(by_role[role] for role in NUMERIC_ROLE_ORDER[4:])
        bundle = ApprovedNumericEvidenceBundleV1(
            relation_binding_hash=primitive.binding_hash,
            source_threshold_reference=by_role["source_step_threshold"],
            source_stability_reference=by_role["source_stability_tolerance"],
            target_scale_reference=by_role["target_noise_scale"],
            fit_evidence_reference=d1["artifact_hash"],
            confirmation_evidence_reference=d2["artifact_hash"],
            preregistered_window_constant_references=window_refs,
        )
        manifest_entry = _with_hash({
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "task039e1_public_manifest_entry_v1",
            "relation_identity": relation.relation_identity,
            "source": relation.source,
            "source_step_direction": relation.source_step_direction,
            "target": relation.target,
            "target_response_direction": relation.target_response_direction,
            "selected_horizon_seconds": relation.selected_delay_horizon_seconds,
            "relation_binding_hash": primitive.binding_hash,
            "private_evidence_record_hash": private.artifact_hash,
            "approved_numeric_roles": list(NUMERIC_ROLE_ORDER),
            "numeric_references": [
                {"numeric_role": item.numeric_role, "numeric_reference": item.numeric_reference}
                for item in numeric
            ],
            "source_parameter_record_hash": source["artifact_hash"],
            "target_parameter_record_hash": target["artifact_hash"],
            "d1_fit_evidence_hash": d1["artifact_hash"],
            "d2_confirmation_evidence_hash": d2["artifact_hash"],
            "window_constant_bundle_hash": window.artifact_hash,
            "evidence_status": "approved",
            "private_numeric_values_included": False,
            "raw_hai_included": False,
            "rule_generated": False,
            "runtime_authority": False,
        })
        private_records.append(private)
        primitives.append(primitive.to_dict())
        bundles.append(bundle.to_dict())
        manifest_entries.append(manifest_entry)

    if len(private_records) != EXPECTED_RELATIONS or len({item.relation_identity for item in private_records}) != EXPECTED_RELATIONS:
        raise TASK039E1Error("failed_task039e1_relation_binding")
    if sum(len(item.numeric_bindings) for item in private_records) != EXPECTED_NUMERIC_BINDINGS:
        raise TASK039E1Error("failed_task039e1_numeric_provenance")
    for private in private_records:
        for binding in private.numeric_bindings:
            resolved = resolve_private_numeric_reference_v1(
                proposal_numeric_reference=binding.numeric_reference,
                relation_binding_hash=private.relation_binding_hash,
                numeric_role=binding.numeric_role,
                private_evidence_record_hash=private.artifact_hash,
                private_evidence=private,
            )
            if resolved["numeric_value"] != binding.numeric_value or resolved["runtime_authority"] is not False:
                raise TASK039E1Error("failed_task039e1_numeric_provenance")

    private_ledger = _with_hash({
        "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
        "artifact_type": "task039e1_private_construction_evidence_ledger_v1",
        "task_id": TASK_ID,
        "status": "frozen_task039e1_private_construction_evidence",
        "execution_code_commit": execution_code_commit,
        "e0_cohort_hash": E0_COHORT_HASH,
        "e0_identity_list_hash": E0_IDENTITY_LIST_HASH,
        "record_count": EXPECTED_RELATIONS,
        "numeric_binding_count": EXPECTED_NUMERIC_BINDINGS,
        "records": [item.to_dict() for item in private_records],
        "raw_hai_included": False,
        "event_timestamps_included": False,
        "attack_test_label_information_included": False,
        "absolute_paths_included": False,
        "rule_generated": False,
        "runtime_authority": False,
    })
    binding = _with_hash({
        "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
        "artifact_type": "task039e1_private_ledger_binding_v1",
        "private_ledger_hash": private_ledger["artifact_hash"],
        "record_count": EXPECTED_RELATIONS,
        "numeric_binding_count": EXPECTED_NUMERIC_BINDINGS,
        "storage_boundary": "outside_git",
        "private_contents_public": False,
        "private_numeric_values_public": False,
    })
    manifest = _with_hash({
        "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
        "artifact_type": "task039e1_construction_evidence_manifest_v1",
        "task_id": TASK_ID,
        "status": "frozen_task039e1_public_construction_evidence_manifest",
        "e0_cohort_hash": E0_COHORT_HASH,
        "relation_count": EXPECTED_RELATIONS,
        "numeric_binding_count": EXPECTED_NUMERIC_BINDINGS,
        "entries": manifest_entries,
        "private_numeric_values_included": False,
        "raw_hai_included": False,
        "rule_generated": False,
        "runtime_authority": False,
    })
    cohort_document = _with_hash({
        "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
        "artifact_type": "task039e1_construction_evidence_cohort_v1",
        "task_id": TASK_ID,
        "status": "frozen_task039e1_construction_evidence_cohort",
        "process": PROCESS,
        "relation_family": RELATION_FAMILY,
        "e0_cohort_hash": E0_COHORT_HASH,
        "e0_identity_list_hash": E0_IDENTITY_LIST_HASH,
        "e0_protocol_bundle_hash": E0_PROTOCOL_BUNDLE_HASH,
        "e1_authorization_hash": E1_AUTHORIZATION_HASH,
        "window_constant_bundle_hash": window.artifact_hash,
        "relation_count": EXPECTED_RELATIONS,
        "pair_context_count": EXPECTED_PAIRS,
        "numeric_binding_count": EXPECTED_NUMERIC_BINDINGS,
        "confirmed_relation_primitives": primitives,
        "approved_numeric_evidence_bundles": bundles,
        "public_manifest_entries": manifest_entries,
        "private_ledger_hash": private_ledger["artifact_hash"],
        "scientific_ranking_created": False,
        "candidate_origin_filtering_used": False,
        "rule_generation_executed": False,
        "runtime_authority": False,
    })
    return {
        "window": window.to_dict(), "private_records": private_records,
        "private_ledger": private_ledger, "private_binding": binding,
        "manifest": manifest, "cohort": cohort_document,
        "primitives": primitives, "bundles": bundles,
    }


def build_public_result_artifacts_v1(
    *, materialized: Mapping[str, Any], execution_code_commit: str,
) -> dict[str, dict[str, Any]]:
    access = _with_hash({
        "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
        "artifact_type": "task039e1_data_access_audit_v1",
        "task_id": TASK_ID,
        "d1_source_ledger_accessed": True,
        "d1_target_ledger_accessed": True,
        "d1_directional_ledger_accessed": True,
        "d2_confirmation_ledger_accessed": True,
        "private_input_ledgers_modified": False,
        "hai_accessed": False,
        "train1_train2_train3_reread": False,
        "train4_accessed": False,
        "test_labels_attacks_accessed": False,
        "llm_called": False,
        "t0_generated": False,
        "t1_t1b_t2_generated": False,
        "rule_v2_authorized": False,
        "runtime_authority": False,
        "absolute_local_paths_public": False,
        "private_calibrated_values_public": False,
        "prohibited_access_count": 0,
    })
    result = _with_hash({
        "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
        "artifact_type": "task039e1_materialization_result_v1",
        "task_id": TASK_ID,
        "status": STATUS,
        "e0_cohort_hash": E0_COHORT_HASH,
        "e0_protocol_bundle_hash": E0_PROTOCOL_BUNDLE_HASH,
        "e1_authorization_hash": E1_AUTHORIZATION_HASH,
        "confirmed_input_relations": 42,
        "confirmed_pair_contexts": 23,
        "materialized_private_records": 42,
        "public_manifest_entries": 42,
        "relation_primitives": 42,
        "approved_numeric_bundles": 42,
        "numeric_bindings": 462,
        "failed_relations": 0,
        "skipped_relations": 0,
        "private_ledger_hash": materialized["private_ledger"]["artifact_hash"],
        "public_manifest_hash": materialized["manifest"]["artifact_hash"],
        "construction_evidence_cohort_hash": materialized["cohort"]["artifact_hash"],
        "data_access_audit_hash": access["artifact_hash"],
        "rule_generated": False,
        "runtime_authority": False,
    })
    receipt = _with_hash({
        "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
        "artifact_type": "task039e1_execution_receipt_v1",
        "task_id": TASK_ID,
        "status": STATUS,
        "execution_code_commit": execution_code_commit,
        "e0_protocol_bundle_hash": E0_PROTOCOL_BUNDLE_HASH,
        "e0_cohort_hash": E0_COHORT_HASH,
        "e1_authorization_hash": E1_AUTHORIZATION_HASH,
        "d1_source_ledger_hash": D1_SOURCE_LEDGER_HASH,
        "d1_target_ledger_hash": D1_TARGET_LEDGER_HASH,
        "d1_directional_ledger_hash": D1_DIRECTIONAL_LEDGER_HASH,
        "d2_confirmation_ledger_hash": D2_CONFIRMATION_LEDGER_HASH,
        "window_constant_bundle_hash": materialized["window"]["artifact_hash"],
        "private_e1_ledger_hash": materialized["private_ledger"]["artifact_hash"],
        "public_manifest_hash": materialized["manifest"]["artifact_hash"],
        "construction_evidence_cohort_hash": materialized["cohort"]["artifact_hash"],
        "materialization_result_hash": result["artifact_hash"],
        "data_access_audit_hash": access["artifact_hash"],
        "hai_accessed": False,
        "llm_called": False,
        "rule_generated": False,
        "runtime_authority": False,
    })
    return {"access": access, "result": result, "receipt": receipt}


def assert_public_payload_safe_v1(document: Mapping[str, Any]) -> None:
    text = json.dumps(document, sort_keys=True, allow_nan=False)
    for forbidden in ("source_step_threshold\":", "source_stability_tolerance\":", "target_noise_scale\":"):
        if forbidden in text:
            raise TASK039E1Error("failed_task039e1_public_private_boundary")
    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, str) and len(value) >= 3 and value[1:3] in {":\\", ":/"}:
            raise TASK039E1Error("absolute path in public artifact")
    walk(document)


def write_json_v1(path: Path, document: Mapping[str, Any], *, public: bool) -> None:
    if public:
        assert_public_payload_safe_v1(document)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
        encoding="utf-8", newline="\n",
    )


def schema_documents_v1() -> dict[str, dict[str, Any]]:
    """Return the strict Draft 2020-12 schemas owned by real E1."""

    meta = "https://json-schema.org/draft/2020-12/schema"
    sha = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
    identifier = {"type": "string", "minLength": 1}
    finite_number = {"type": "number"}
    git_sha = {"type": "string", "pattern": "^[a-f0-9]{40}$"}
    false = {"const": False}
    true = {"const": True}

    def obj(properties: Mapping[str, Any], *, required: Sequence[str] | None = None) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": dict(properties),
            "required": list(required or properties.keys()),
        }

    numeric_reference = obj({"numeric_role": {"enum": list(NUMERIC_ROLE_ORDER)}, "numeric_reference": sha})
    numeric_binding = obj({
        "schema_version": {"const": V6_FOUNDATION_SCHEMA_VERSION},
        "artifact_type": {"const": "task039e1_real_private_numeric_binding_v1"},
        "relation_identity": identifier,
        "numeric_role": {"enum": list(NUMERIC_ROLE_ORDER)},
        "numeric_value": finite_number,
        "value_origin": {"enum": [SOURCE_PARAMETER_ORIGIN, TARGET_PARAMETER_ORIGIN, HORIZON_ORIGIN, WINDOW_CONSTANT_ORIGIN]},
        "source_parameter_record_hash": sha, "target_parameter_record_hash": sha,
        "d1_fit_evidence_hash": sha, "d2_confirmation_evidence_hash": sha,
        "window_constant_bundle_hash": sha,
        "evidence_authority": {"const": APPROVED_EVIDENCE_AUTHORITY},
        "llm_generated": false, "runtime_authority": false, "numeric_reference": sha,
    })
    private_record = obj({
        "schema_version": {"const": V6_FOUNDATION_SCHEMA_VERSION},
        "artifact_type": {"const": "task039e1_real_private_construction_evidence_v1"},
        "relation_binding_hash": sha, "relation_identity": identifier,
        "source": identifier, "source_step_direction": {"enum": ["step_up", "step_down"]},
        "target": identifier, "target_response_direction": {"enum": ["increase", "decrease"]},
        "selected_horizon_seconds": {"enum": [1, 5, 10, 30, 60]},
        "source_parameter_record_hash": sha, "target_parameter_record_hash": sha,
        "d1_fit_evidence_hash": sha, "d2_confirmation_evidence_hash": sha,
        "window_constant_bundle_hash": sha,
        "numeric_bindings": {"type": "array", "minItems": 11, "maxItems": 11, "items": numeric_binding},
        "evidence_authority": {"const": APPROVED_EVIDENCE_AUTHORITY},
        "construction_evidence_status": {"const": "approved"},
        "private_record": true, "rule_generated": false, "runtime_authority": false,
        "artifact_hash": sha,
    })
    manifest_entry = obj({
        "schema_version": {"const": V6_FOUNDATION_SCHEMA_VERSION},
        "artifact_type": {"const": "task039e1_public_manifest_entry_v1"},
        "relation_identity": identifier, "source": identifier,
        "source_step_direction": {"enum": ["step_up", "step_down"]},
        "target": identifier, "target_response_direction": {"enum": ["increase", "decrease"]},
        "selected_horizon_seconds": {"enum": [1, 5, 10, 30, 60]},
        "relation_binding_hash": sha, "private_evidence_record_hash": sha,
        "approved_numeric_roles": {"type": "array", "minItems": 11, "maxItems": 11, "items": {"enum": list(NUMERIC_ROLE_ORDER)}},
        "numeric_references": {"type": "array", "minItems": 11, "maxItems": 11, "items": numeric_reference},
        "source_parameter_record_hash": sha, "target_parameter_record_hash": sha,
        "d1_fit_evidence_hash": sha, "d2_confirmation_evidence_hash": sha,
        "window_constant_bundle_hash": sha, "evidence_status": {"const": "approved"},
        "private_numeric_values_included": false, "raw_hai_included": false,
        "rule_generated": false, "runtime_authority": false, "artifact_hash": sha,
    })
    primitive = obj({
        "schema_version": {"const": V6_FOUNDATION_SCHEMA_VERSION}, "artifact_type": {"const": "confirmed_relation_primitive_v1"},
        "relation_identity": identifier, "relation_family": {"const": RELATION_FAMILY},
        "source": identifier, "source_step_direction": {"enum": ["step_up", "step_down"]},
        "target": identifier, "target_response_direction": {"enum": ["increase", "decrease"]},
        "selected_delay_horizon_seconds": {"enum": [1, 5, 10, 30, 60]},
        "approved_source_threshold_reference": sha, "approved_source_stability_reference": sha,
        "approved_target_scale_reference": sha, "fit_evidence_reference": sha,
        "confirmation_evidence_reference": sha, "confirmed": true,
        "rule_authority_granted": false, "runtime_authority_granted": false, "binding_hash": sha,
    })
    approved_bundle = obj({
        "schema_version": {"const": V6_FOUNDATION_SCHEMA_VERSION}, "artifact_type": {"const": "approved_numeric_evidence_bundle_v1"},
        "relation_binding_hash": sha, "source_threshold_reference": sha,
        "source_stability_reference": sha, "target_scale_reference": sha,
        "fit_evidence_reference": sha, "confirmation_evidence_reference": sha,
        "preregistered_window_constant_references": {"type": "array", "minItems": 7, "maxItems": 7, "items": sha},
        "numeric_origin": {"const": "deterministic_calibrated_evidence"},
        "approved": true, "raw_numeric_values_included": false,
        "arbitrary_numeric_literals_allowed": false, "artifact_hash": sha,
    })
    window = obj({
        "schema_version": {"const": V6_FOUNDATION_SCHEMA_VERSION},
        "artifact_type": {"const": "task039e1_real_window_constant_bundle_v1"},
        "bundle_identity": {"const": "task039e1_preregistered_window_constants_v1"},
        "d0_protocol_bundle_hash": {"const": D0_PROTOCOL_BUNDLE_HASH},
        "source_event_policy_hash": {"const": SOURCE_EVENT_POLICY_HASH},
        "target_response_policy_hash": {"const": TARGET_RESPONSE_POLICY_HASH},
        "confirmation_policy_hash": {"const": CONFIRMATION_POLICY_HASH},
        "source_pre_window_seconds": {"const": 5}, "source_post_window_seconds": {"const": 5},
        "minimum_source_stability_fraction": {"const": 0.8}, "source_refractory_seconds": {"const": 10},
        "cross_source_isolation_radius_seconds": {"const": 2}, "target_baseline_window_seconds": {"const": 5},
        "target_response_window_seconds": {"const": 3}, "value_origin": {"const": WINDOW_CONSTANT_ORIGIN},
        "llm_generated": false, "runtime_authority": false, "artifact_hash": sha,
    })
    private_ledger = obj({
        "schema_version": {"const": V6_FOUNDATION_SCHEMA_VERSION}, "artifact_type": {"const": "task039e1_private_construction_evidence_ledger_v1"},
        "task_id": {"const": TASK_ID}, "status": {"const": "frozen_task039e1_private_construction_evidence"},
        "execution_code_commit": git_sha, "e0_cohort_hash": {"const": E0_COHORT_HASH},
        "e0_identity_list_hash": {"const": E0_IDENTITY_LIST_HASH},
        "record_count": {"const": 42}, "numeric_binding_count": {"const": 462},
        "records": {"type": "array", "minItems": 42, "maxItems": 42, "items": private_record},
        "raw_hai_included": false, "event_timestamps_included": false,
        "attack_test_label_information_included": false, "absolute_paths_included": false,
        "rule_generated": false, "runtime_authority": false, "artifact_hash": sha,
    })
    binding = obj({
        "schema_version": {"const": V6_FOUNDATION_SCHEMA_VERSION}, "artifact_type": {"const": "task039e1_private_ledger_binding_v1"},
        "private_ledger_hash": sha, "record_count": {"const": 42}, "numeric_binding_count": {"const": 462},
        "storage_boundary": {"const": "outside_git"}, "private_contents_public": false,
        "private_numeric_values_public": false, "artifact_hash": sha,
    })
    manifest = obj({
        "schema_version": {"const": V6_FOUNDATION_SCHEMA_VERSION}, "artifact_type": {"const": "task039e1_construction_evidence_manifest_v1"},
        "task_id": {"const": TASK_ID}, "status": {"const": "frozen_task039e1_public_construction_evidence_manifest"},
        "e0_cohort_hash": {"const": E0_COHORT_HASH}, "relation_count": {"const": 42}, "numeric_binding_count": {"const": 462},
        "entries": {"type": "array", "minItems": 42, "maxItems": 42, "items": manifest_entry},
        "private_numeric_values_included": false, "raw_hai_included": false,
        "rule_generated": false, "runtime_authority": false, "artifact_hash": sha,
    })
    cohort = obj({
        "schema_version": {"const": V6_FOUNDATION_SCHEMA_VERSION}, "artifact_type": {"const": "task039e1_construction_evidence_cohort_v1"},
        "task_id": {"const": TASK_ID}, "status": {"const": "frozen_task039e1_construction_evidence_cohort"},
        "process": {"const": PROCESS}, "relation_family": {"const": RELATION_FAMILY},
        "e0_cohort_hash": {"const": E0_COHORT_HASH}, "e0_identity_list_hash": {"const": E0_IDENTITY_LIST_HASH},
        "e0_protocol_bundle_hash": {"const": E0_PROTOCOL_BUNDLE_HASH}, "e1_authorization_hash": {"const": E1_AUTHORIZATION_HASH},
        "window_constant_bundle_hash": sha, "relation_count": {"const": 42}, "pair_context_count": {"const": 23},
        "numeric_binding_count": {"const": 462},
        "confirmed_relation_primitives": {"type": "array", "minItems": 42, "maxItems": 42, "items": primitive},
        "approved_numeric_evidence_bundles": {"type": "array", "minItems": 42, "maxItems": 42, "items": approved_bundle},
        "public_manifest_entries": {"type": "array", "minItems": 42, "maxItems": 42, "items": manifest_entry},
        "private_ledger_hash": sha, "scientific_ranking_created": false,
        "candidate_origin_filtering_used": false, "rule_generation_executed": false,
        "runtime_authority": false, "artifact_hash": sha,
    })
    result = obj({
        "schema_version": {"const": V6_FOUNDATION_SCHEMA_VERSION}, "artifact_type": {"const": "task039e1_materialization_result_v1"},
        "task_id": {"const": TASK_ID}, "status": {"const": STATUS},
        "e0_cohort_hash": {"const": E0_COHORT_HASH}, "e0_protocol_bundle_hash": {"const": E0_PROTOCOL_BUNDLE_HASH},
        "e1_authorization_hash": {"const": E1_AUTHORIZATION_HASH}, "confirmed_input_relations": {"const": 42},
        "confirmed_pair_contexts": {"const": 23}, "materialized_private_records": {"const": 42},
        "public_manifest_entries": {"const": 42}, "relation_primitives": {"const": 42},
        "approved_numeric_bundles": {"const": 42}, "numeric_bindings": {"const": 462},
        "failed_relations": {"const": 0}, "skipped_relations": {"const": 0},
        "private_ledger_hash": sha, "public_manifest_hash": sha,
        "construction_evidence_cohort_hash": sha, "data_access_audit_hash": sha,
        "rule_generated": false, "runtime_authority": false, "artifact_hash": sha,
    })
    access = obj({
        "schema_version": {"const": V6_FOUNDATION_SCHEMA_VERSION}, "artifact_type": {"const": "task039e1_data_access_audit_v1"},
        "task_id": {"const": TASK_ID}, "d1_source_ledger_accessed": true, "d1_target_ledger_accessed": true,
        "d1_directional_ledger_accessed": true, "d2_confirmation_ledger_accessed": true,
        "private_input_ledgers_modified": false, "hai_accessed": false,
        "train1_train2_train3_reread": false, "train4_accessed": false,
        "test_labels_attacks_accessed": false, "llm_called": false,
        "t0_generated": false, "t1_t1b_t2_generated": false,
        "rule_v2_authorized": false, "runtime_authority": false,
        "absolute_local_paths_public": false, "private_calibrated_values_public": false,
        "prohibited_access_count": {"const": 0}, "artifact_hash": sha,
    })
    receipt = obj({
        "schema_version": {"const": V6_FOUNDATION_SCHEMA_VERSION}, "artifact_type": {"const": "task039e1_execution_receipt_v1"},
        "task_id": {"const": TASK_ID}, "status": {"const": STATUS}, "execution_code_commit": git_sha,
        "e0_protocol_bundle_hash": {"const": E0_PROTOCOL_BUNDLE_HASH}, "e0_cohort_hash": {"const": E0_COHORT_HASH},
        "e1_authorization_hash": {"const": E1_AUTHORIZATION_HASH},
        "d1_source_ledger_hash": {"const": D1_SOURCE_LEDGER_HASH}, "d1_target_ledger_hash": {"const": D1_TARGET_LEDGER_HASH},
        "d1_directional_ledger_hash": {"const": D1_DIRECTIONAL_LEDGER_HASH},
        "d2_confirmation_ledger_hash": {"const": D2_CONFIRMATION_LEDGER_HASH},
        "window_constant_bundle_hash": sha, "private_e1_ledger_hash": sha, "public_manifest_hash": sha,
        "construction_evidence_cohort_hash": sha, "materialization_result_hash": sha,
        "data_access_audit_hash": sha, "hai_accessed": false, "llm_called": false,
        "rule_generated": false, "runtime_authority": false, "artifact_hash": sha,
    })
    raw = {
        "task039e1_real_window_constant_bundle_v1": window,
        "task039e1_real_private_numeric_binding_v1": numeric_binding,
        "task039e1_real_private_construction_evidence_v1": private_record,
        "task039e1_private_construction_evidence_ledger_v1": private_ledger,
        "task039e1_private_ledger_binding_v1": binding,
        "task039e1_construction_evidence_manifest_v1": manifest,
        "task039e1_construction_evidence_cohort_v1": cohort,
        "task039e1_materialization_result_v1": result,
        "task039e1_data_access_audit_v1": access,
        "task039e1_execution_receipt_v1": receipt,
    }
    return {
        name: {"$schema": meta, "$id": f"https://paperworks.local/schemas/v6/{name}.json", "title": name, **schema}
        for name, schema in raw.items()
    }


__all__ = [
    "D1_DIRECTIONAL_LEDGER_HASH", "D1_SOURCE_LEDGER_HASH", "D1_TARGET_LEDGER_HASH",
    "D2_CONFIRMATION_LEDGER_HASH", "E0_COHORT_HASH", "E0_IDENTITY_LIST_HASH",
    "E0_PROTOCOL_BUNDLE_HASH", "E1_AUTHORIZATION_HASH", "EXPECTED_NUMERIC_BINDINGS",
    "EXPECTED_PAIRS", "EXPECTED_RELATIONS", "NUMERIC_ROLE_ORDER", "PRIVATE_D2_LEDGER_NAME",
    "PRIVATE_DIRECTIONAL_LEDGER_NAME", "PRIVATE_E1_LEDGER_NAME", "PRIVATE_SOURCE_LEDGER_NAME",
    "PRIVATE_TARGET_LEDGER_NAME", "PreregisteredWindowConstantBundleV1",
    "PrivateConstructionEvidenceV1", "PrivateNumericBindingV1", "SCHEMA_FILES", "STATUS",
    "TASK039E1Error", "assert_public_payload_safe_v1", "build_public_result_artifacts_v1",
    "load_e0_cohort_v1", "load_private_ledger_v1", "materialize_from_ledgers_v1",
    "resolve_private_numeric_reference_v1", "validate_e1_authorization_v1",
    "schema_documents_v1", "validate_external_roots_v1", "verify_self_hash_v1", "write_json_v1",
]
