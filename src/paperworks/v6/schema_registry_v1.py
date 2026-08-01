"""Independent standard-library registry for lightweight v6 schemas."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping


V6_SCHEMA_REGISTRY_VERSION = "1.0.0"
V6_META_SCHEMA = "https://json-schema.org/draft/2020-12/schema"
V6_SCHEMA_FILES: Mapping[str, str] = {
    "canonical_context_build_result": (
        "schemas/v6/canonical_context_build_result_v1_schema.json"
    ),
    "construction_candidate_binding_receipt": (
        "schemas/v6/construction_candidate_binding_receipt_v1_schema.json"
    ),
    "normal_relation_evidence": (
        "schemas/v6/normal_relation_evidence_v1_schema.json"
    ),
    "detector_error_context": (
        "schemas/v6/detector_error_context_v1_schema.json"
    ),
    "rule_construction_outcome": (
        "schemas/v6/rule_construction_outcome_v1_schema.json"
    ),
    "rule_governance_outcome": (
        "schemas/v6/rule_governance_outcome_v1_schema.json"
    ),
    "governance_authority_binding_receipt": (
        "schemas/v6/governance_authority_binding_receipt_v1_schema.json"
    ),
    "gdn_backend_fidelity_record": (
        "schemas/v6/gdn_backend_fidelity_record_v1_schema.json"
    ),
    "gdn_dependency_status": (
        "schemas/v6/gdn_dependency_status_v1_schema.json"
    ),
    "gdn_fidelity_freeze": (
        "schemas/v6/gdn_fidelity_freeze_v1_schema.json"
    ),
    "hai_csv_structure_audit": (
        "schemas/v6/hai_csv_structure_audit_v1_schema.json"
    ),
    "hai_label_custody_public": (
        "schemas/v6/hai_label_custody_public_v1_schema.json"
    ),
    "hai_lfs_pointer_record": (
        "schemas/v6/hai_lfs_pointer_record_v1_schema.json"
    ),
    "hai_provenance_audit_result": (
        "schemas/v6/hai_provenance_audit_result_v1_schema.json"
    ),
    "hai_reference_inventory": (
        "schemas/v6/hai_reference_inventory_v1_schema.json"
    ),
    "normal_reference_set_binding": (
        "schemas/v6/normal_reference_set_binding_v1_schema.json"
    ),
    "rule_evidence_binding": (
        "schemas/v6/rule_evidence_binding_v1_schema.json"
    ),
    "v6_deployment_authorization_receipt": (
        "schemas/v6/v6_deployment_authorization_receipt_v1_schema.json"
    ),
    "v6_evidence_adapter_result": (
        "schemas/v6/v6_evidence_adapter_result_v1_schema.json"
    ),
}


class V6SchemaRegistryError(ValueError):
    """Raised when the independent v6 schema registry fails closed."""


@dataclass(frozen=True)
class V6SchemaRegistrationV1:
    artifact_type: str
    schema_path: str
    schema_id: str
    schema_version: str
    schema_sha256: str


class V6SchemaRegistryV1:
    """Read-only schema identity registry without jsonschema dependency."""

    def __init__(
        self,
        registrations: tuple[V6SchemaRegistrationV1, ...],
        schemas: Mapping[str, Mapping[str, Any]],
    ) -> None:
        self._registrations = {
            item.artifact_type: item for item in registrations
        }
        self._schemas = {
            key: json.loads(json.dumps(value)) for key, value in schemas.items()
        }

    @property
    def artifact_types(self) -> tuple[str, ...]:
        return tuple(sorted(self._registrations))

    def registration_for(self, artifact_type: str) -> V6SchemaRegistrationV1:
        try:
            return self._registrations[artifact_type]
        except KeyError as exc:
            raise V6SchemaRegistryError(
                f"unknown v6 artifact type: {artifact_type}"
            ) from exc

    def schema_for(self, artifact_type: str) -> dict[str, Any]:
        self.registration_for(artifact_type)
        return json.loads(json.dumps(self._schemas[artifact_type]))


def load_v6_schema_registry_v1(
    *, repository_root: str | Path | None = None
) -> V6SchemaRegistryV1:
    """Load the independent v6 schemas and verify declared identities."""

    root = (
        Path(repository_root).resolve()
        if repository_root is not None
        else Path(__file__).resolve().parents[3]
    )
    schemas_root = (root / "schemas" / "v6").resolve()
    registrations: list[V6SchemaRegistrationV1] = []
    schemas: dict[str, Mapping[str, Any]] = {}
    for artifact_type, relative in sorted(V6_SCHEMA_FILES.items()):
        path = (root / relative).resolve()
        if path.parent != schemas_root or not path.is_file():
            raise V6SchemaRegistryError(
                "v6 schema is missing or outside schemas/v6"
            )
        try:
            raw = path.read_bytes()
            schema = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise V6SchemaRegistryError(
                "v6 schema is not readable UTF-8 JSON"
            ) from exc
        if schema.get("$schema") != V6_META_SCHEMA:
            raise V6SchemaRegistryError(
                "v6 schema does not declare Draft 2020-12"
            )
        properties = schema.get("properties", {})
        if (
            properties.get("schema_version", {}).get("const")
            != V6_SCHEMA_REGISTRY_VERSION
        ):
            raise V6SchemaRegistryError(
                "v6 schema version does not match registry"
            )
        if properties.get("artifact_type", {}).get("const") != artifact_type:
            raise V6SchemaRegistryError(
                "v6 schema artifact type does not match registry"
            )
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            raise V6SchemaRegistryError("v6 schema id is missing")
        registrations.append(
            V6SchemaRegistrationV1(
                artifact_type=artifact_type,
                schema_path=relative,
                schema_id=schema_id,
                schema_version=V6_SCHEMA_REGISTRY_VERSION,
                schema_sha256=sha256(raw).hexdigest(),
            )
        )
        schemas[artifact_type] = schema
    return V6SchemaRegistryV1(tuple(registrations), schemas)
