"""Independent registry extension for dataset-neutral v2 JSON schemas."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping


V2_REGISTRY_VERSION = "2.0.0"
V2_META_SCHEMA = "https://json-schema.org/draft/2020-12/schema"
V2_SCHEMA_FILES: Mapping[str, str] = {
    "dataset_manifest_v2": "schemas/v6/dataset_manifest_v2_schema.json",
    "data_view_manifest_v2": "schemas/v6/data_view_manifest_v2_schema.json",
    "split_manifest_v2": "schemas/v6/split_manifest_v2_schema.json",
    "data_adapter_result_v2": "schemas/v6/data_adapter_result_v2_schema.json",
}


class SchemaRegistryV2Error(ValueError):
    """Raised when the independent v2 schema registry fails closed."""


@dataclass(frozen=True)
class SchemaRegistrationV2:
    artifact_type: str
    schema_path: str
    schema_id: str
    schema_version: str
    schema_sha256: str


class SchemaRegistryV2:
    """Read-only registrations and schema documents without v1 registry mutation."""

    def __init__(
        self,
        registrations: tuple[SchemaRegistrationV2, ...],
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

    def registration_for(self, artifact_type: str) -> SchemaRegistrationV2:
        try:
            return self._registrations[artifact_type]
        except KeyError as exc:
            raise SchemaRegistryV2Error(
                f"unknown v2 artifact type: {artifact_type}"
            ) from exc

    def schema_for(self, artifact_type: str) -> dict[str, Any]:
        self.registration_for(artifact_type)
        return json.loads(json.dumps(self._schemas[artifact_type]))


def load_schema_registry_v2(
    *, repository_root: str | Path | None = None
) -> SchemaRegistryV2:
    """Load only the four v2 schemas, leaving the TASK-032 registry untouched."""

    root = (
        Path(repository_root).resolve()
        if repository_root is not None
        else Path(__file__).resolve().parents[3]
    )
    schemas_root = (root / "schemas" / "v6").resolve()
    registrations: list[SchemaRegistrationV2] = []
    schemas: dict[str, Mapping[str, Any]] = {}
    for artifact_type, relative in sorted(V2_SCHEMA_FILES.items()):
        path = (root / relative).resolve()
        if path.parent != schemas_root or not path.is_file():
            raise SchemaRegistryV2Error("v2 schema is missing or outside schemas/v6")
        try:
            raw = path.read_bytes()
            schema = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SchemaRegistryV2Error("v2 schema is not readable UTF-8 JSON") from exc
        if schema.get("$schema") != V2_META_SCHEMA:
            raise SchemaRegistryV2Error("v2 schema does not declare Draft 2020-12")
        properties = schema.get("properties", {})
        if properties.get("schema_version", {}).get("const") != V2_REGISTRY_VERSION:
            raise SchemaRegistryV2Error("v2 schema version does not match registry")
        if properties.get("artifact_type", {}).get("const") != artifact_type:
            raise SchemaRegistryV2Error("v2 schema artifact type does not match registry")
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            raise SchemaRegistryV2Error("v2 schema id is missing")
        registrations.append(
            SchemaRegistrationV2(
                artifact_type=artifact_type,
                schema_path=relative,
                schema_id=schema_id,
                schema_version=V2_REGISTRY_VERSION,
                schema_sha256=sha256(raw).hexdigest(),
            )
        )
        schemas[artifact_type] = schema
    return SchemaRegistryV2(tuple(registrations), schemas)
