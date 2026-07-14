"""Fail-closed Draft 2020-12 structural schema registry."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import FormatError, SchemaError

from paperworks.contracts.models import (
    SchemaRegistration,
    StructuralValidationIssue,
    StructuralValidationReport,
)


EXPECTED_META_SCHEMA = "https://json-schema.org/draft/2020-12/schema"
EXPECTED_CONTRACT_COMMIT = "317a43a0bfe0be59caad611edf895c0f3ddc6e37"
EXPECTED_REGISTRY_VERSION = "1.0.0"
EXPECTED_SCHEMA_FILES = {
    "evidence_package": "schemas/evidence_package_schema.json",
    "explanation_record": "schemas/explanation_record_schema.json",
    "graph": "schemas/graph_schema.json",
    "parameter_registry": "schemas/parameter_registry_schema.json",
    "rule_dsl": "schemas/rule_dsl_schema.json",
    "runtime_trace": "schemas/runtime_trace_schema.json",
    "verifier_result": "schemas/verifier_result_schema.json",
}
DEFAULT_MANIFEST = Path("configs/contracts/task032a_schema_registry.json")
_SAFE_KEYWORD_PATTERN = r"[^A-Za-z0-9]+"


class SchemaRegistryError(ValueError):
    """Raised when the trusted schema registry cannot be initialized."""


class SchemaRegistry:
    """Validated registrations and Draft 2020-12 validator instances."""

    def __init__(
        self,
        registrations: Sequence[SchemaRegistration],
        schemas: Mapping[str, Mapping[str, Any]],
        *,
        format_checker: FormatChecker,
    ) -> None:
        self._registrations = {item.artifact_type: item for item in registrations}
        self._schemas = {key: copy.deepcopy(value) for key, value in schemas.items()}
        self._format_checker = format_checker
        self._validators = {
            artifact_type: Draft202012Validator(schema, format_checker=format_checker)
            for artifact_type, schema in self._schemas.items()
        }

    @property
    def artifact_types(self) -> tuple[str, ...]:
        return tuple(sorted(self._registrations))

    def registration_for(self, artifact_type: str) -> SchemaRegistration:
        try:
            return self._registrations[artifact_type]
        except KeyError as exc:
            raise SchemaRegistryError(f"unknown registered artifact type: {artifact_type}") from exc

    def validate_artifact(self, artifact_type: str, instance: Mapping[str, Any]) -> StructuralValidationReport:
        instance_hash = _canonical_sha256(instance)
        if artifact_type not in self._registrations:
            issue = StructuralValidationIssue(
                issue_code="REGISTRY_UNKNOWN_ARTIFACT_TYPE",
                instance_path="/",
                schema_path="/",
                validator_keyword="registry",
                message="artifact type is not registered",
            )
            return StructuralValidationReport(
                registry_version=_registry_version(self._registrations.values()),
                artifact_type=artifact_type,
                schema_id="",
                schema_version="",
                schema_sha256="",
                instance_sha256=instance_hash,
                status="registry_error",
                issues=(issue,),
            )

        registration = self._registrations[artifact_type]
        errors = self._validators[artifact_type].iter_errors(copy.deepcopy(dict(instance)))
        issues = tuple(sorted((_normalize_error(error) for error in errors), key=_issue_sort_key))
        return StructuralValidationReport(
            registry_version=registration.registry_version,
            artifact_type=artifact_type,
            schema_id=registration.schema_id,
            schema_version=registration.schema_version,
            schema_sha256=registration.schema_sha256,
            instance_sha256=instance_hash,
            status="invalid" if issues else "valid",
            issues=issues,
        )


def load_schema_registry(
    manifest_path: str | Path | None = None,
    *,
    repository_root: str | Path | None = None,
) -> SchemaRegistry:
    root = Path(repository_root).resolve() if repository_root is not None else _repository_root()
    manifest = Path(manifest_path) if manifest_path is not None else DEFAULT_MANIFEST
    if not manifest.is_absolute():
        manifest = root / manifest
    if not manifest.is_file():
        raise SchemaRegistryError("schema registry manifest is missing")

    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SchemaRegistryError("schema registry manifest is unreadable") from exc

    registry_version = str(payload.get("registry_version", ""))
    contract_commit = str(payload.get("contract_commit", ""))
    rows = payload.get("registrations")
    if set(payload) != {"registry_version", "contract_commit", "registrations"}:
        raise SchemaRegistryError("schema registry manifest fields do not match the required contract")
    if registry_version != EXPECTED_REGISTRY_VERSION or contract_commit != EXPECTED_CONTRACT_COMMIT:
        raise SchemaRegistryError("schema registry version or contract commit mismatch")
    if not isinstance(rows, list) or not rows:
        raise SchemaRegistryError("schema registry manifest is incomplete")

    registrations: list[SchemaRegistration] = []
    schemas: dict[str, Mapping[str, Any]] = {}
    seen_files: set[str] = set()
    seen_ids: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise SchemaRegistryError("schema registration must be an object")
        registration = _registration_from_dict(row, registry_version, contract_commit)
        expected_file = EXPECTED_SCHEMA_FILES.get(registration.artifact_type)
        if expected_file is None or registration.schema_file != expected_file:
            raise SchemaRegistryError("artifact type is mapped to an unexpected canonical schema file")
        if registration.artifact_type in schemas:
            raise SchemaRegistryError("duplicate artifact type registration")
        if registration.schema_file in seen_files or registration.schema_id in seen_ids:
            raise SchemaRegistryError("duplicate schema file or schema id registration")
        if not registration.format_validation:
            raise SchemaRegistryError("format validation must be enabled")

        schema_path = (root / registration.schema_file).resolve()
        schemas_root = (root / "schemas").resolve()
        if schema_path.parent != schemas_root or not schema_path.is_file():
            raise SchemaRegistryError("registered canonical schema file is missing or outside schemas")
        schema_bytes = schema_path.read_bytes()
        if hashlib.sha256(schema_bytes).hexdigest() != registration.schema_sha256:
            raise SchemaRegistryError("registered schema hash mismatch")
        try:
            schema = json.loads(schema_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SchemaRegistryError("registered schema is not valid UTF-8 JSON") from exc
        _validate_schema_identity(schema, registration)
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            raise SchemaRegistryError("registered schema failed Draft 2020-12 meta-validation") from exc

        registrations.append(registration)
        schemas[registration.artifact_type] = schema
        seen_files.add(registration.schema_file)
        seen_ids.add(registration.schema_id)

    if set(schemas) != set(EXPECTED_SCHEMA_FILES):
        raise SchemaRegistryError("schema registry must contain exactly the seven canonical artifact types")
    format_checker = _required_format_checker()
    return SchemaRegistry(registrations, schemas, format_checker=format_checker)


def validate_artifact(
    artifact_type: str,
    instance: Mapping[str, Any],
    *,
    registry: SchemaRegistry | None = None,
) -> StructuralValidationReport:
    active_registry = registry or load_schema_registry()
    return active_registry.validate_artifact(artifact_type, instance)


def validate_artifact_file(
    artifact_type: str,
    instance_path: str | Path,
    *,
    registry: SchemaRegistry | None = None,
) -> StructuralValidationReport:
    path = Path(instance_path)
    try:
        instance = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SchemaRegistryError("artifact file is not readable UTF-8 JSON") from exc
    if not isinstance(instance, dict):
        raise SchemaRegistryError("artifact file must contain a JSON object")
    return validate_artifact(artifact_type, instance, registry=registry)


def _registration_from_dict(
    row: Mapping[str, Any], registry_version: str, contract_commit: str
) -> SchemaRegistration:
    required = {
        "artifact_type",
        "schema_file",
        "schema_id",
        "schema_version",
        "schema_sha256",
        "format_validation",
    }
    if set(row) != required:
        raise SchemaRegistryError("schema registration fields do not match the required manifest contract")
    digest = str(row["schema_sha256"])
    if not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise SchemaRegistryError("schema registration hash is invalid")
    return SchemaRegistration(
        registry_version=registry_version,
        contract_commit=contract_commit,
        artifact_type=str(row["artifact_type"]),
        schema_file=str(row["schema_file"]),
        schema_id=str(row["schema_id"]),
        schema_version=str(row["schema_version"]),
        schema_sha256=digest,
        format_validation=row["format_validation"] is True,
    )


def _validate_schema_identity(schema: Mapping[str, Any], registration: SchemaRegistration) -> None:
    if schema.get("$schema") != EXPECTED_META_SCHEMA:
        raise SchemaRegistryError("registered schema does not declare Draft 2020-12")
    if schema.get("$id") != registration.schema_id:
        raise SchemaRegistryError("registered schema id mismatch")
    version = schema.get("properties", {}).get("schema_version", {}).get("const")
    if version != registration.schema_version:
        raise SchemaRegistryError("registered schema version mismatch")


def _required_format_checker() -> FormatChecker:
    checker = FormatChecker()
    probes = (
        ("date", "2026-07-14", "2026-02-30"),
        ("date-time", "2026-07-14T00:00:00Z", "2026-02-30T00:00:00Z"),
    )
    for format_name, valid_value, invalid_value in probes:
        try:
            checker.check(valid_value, format_name)
        except FormatError as exc:
            raise SchemaRegistryError(f"required {format_name} format checker rejected a valid probe") from exc
        try:
            checker.check(invalid_value, format_name)
        except FormatError:
            continue
        raise SchemaRegistryError(f"required {format_name} format checker is unavailable")
    return checker


def _normalize_error(error: Any) -> StructuralValidationIssue:
    keyword = str(error.validator or "unknown")
    code_keyword = re.sub(_SAFE_KEYWORD_PATTERN, "_", keyword).strip("_").upper() or "UNKNOWN"
    return StructuralValidationIssue(
        issue_code=f"SCHEMA_{code_keyword}",
        instance_path=_json_pointer(error.absolute_path),
        schema_path=_json_pointer(error.absolute_schema_path),
        validator_keyword=keyword,
        message=_sanitized_message(keyword),
    )


def _sanitized_message(keyword: str) -> str:
    messages = {
        "required": "required property is missing",
        "additionalProperties": "unregistered property is present",
        "format": "value does not match the required format",
        "type": "value has an invalid JSON type",
        "enum": "value is not in the allowed enumeration",
        "const": "value does not match the required constant",
        "pattern": "string does not match the required pattern",
        "uniqueItems": "array items are not unique",
        "minimum": "number is below the allowed minimum",
        "maximum": "number exceeds the allowed maximum",
        "exclusiveMinimum": "number is not above the exclusive minimum",
        "minItems": "array has too few items",
        "maxItems": "array has too many items",
        "anyOf": "value does not match any allowed structural alternative",
    }
    return messages.get(keyword, "value failed structural schema validation")


def _json_pointer(parts: Sequence[Any]) -> str:
    encoded = [str(item).replace("~", "~0").replace("/", "~1") for item in parts]
    return "/" + "/".join(encoded) if encoded else "/"


def _issue_sort_key(issue: StructuralValidationIssue) -> tuple[str, str, str, str]:
    return (issue.instance_path, issue.schema_path, issue.validator_keyword, issue.message)


def _canonical_sha256(instance: Mapping[str, Any]) -> str:
    payload = json.dumps(instance, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _registry_version(registrations: Sequence[SchemaRegistration]) -> str:
    versions = {item.registry_version for item in registrations}
    return next(iter(versions)) if len(versions) == 1 else "unknown"


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]
