"""Wheel-portable schema registry and dependency-free validator for V2."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from importlib import resources
import json
import re
from typing import Any, Mapping

from .schemas.schema_documents_v1 import EMBEDDED_VALIDATION_V2_SCHEMAS, META


VALIDATION_V2_META_SCHEMA = META
VALIDATION_V2_SCHEMA_REGISTRY_VERSION = "1.8.0"


class ValidationV2SchemaRegistryError(ValueError):
    pass


@dataclass(frozen=True)
class ValidationV2SchemaRecordV1:
    filename: str
    sha256: str
    document: Mapping[str, Any]


def _canonical_bytes(document: Mapping[str, Any]) -> bytes:
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def load_validation_v2_schema_registry_v1() -> tuple[ValidationV2SchemaRecordV1, ...]:
    """Load schemas from Python modules that are included in every wheel.

    Human-readable JSON resources are cross-checked when present in a source
    checkout, but runtime portability does not depend on package-data rules.
    """

    package = resources.files("paperworks.validation_v2.schemas")
    records: list[ValidationV2SchemaRecordV1] = []
    for filename, embedded in sorted(EMBEDDED_VALIDATION_V2_SCHEMAS.items()):
        document = dict(embedded)
        if document.get("$schema") != VALIDATION_V2_META_SCHEMA:
            raise ValidationV2SchemaRegistryError(f"schema draft differs for {filename}")
        resource = package.joinpath(filename)
        if resource.is_file():
            try:
                source_document = json.loads(resource.read_text(encoding="utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValidationV2SchemaRegistryError(f"schema JSON is invalid: {filename}") from exc
            if source_document != document:
                raise ValidationV2SchemaRegistryError(f"embedded and source schema differ: {filename}")
        raw = _canonical_bytes(document)
        records.append(ValidationV2SchemaRecordV1(filename, sha256(raw).hexdigest(), document))
    return tuple(records)


def _resolve_ref(root: Mapping[str, Any], reference: str) -> Mapping[str, Any]:
    prefix = "#/$defs/"
    if not reference.startswith(prefix):
        raise ValidationV2SchemaRegistryError(f"external schema reference prohibited: {reference}")
    name = reference[len(prefix):]
    resolved = root.get("$defs", {}).get(name)
    if type(resolved) is not dict:
        raise ValidationV2SchemaRegistryError(f"schema reference is missing: {reference}")
    return resolved


def _validate_node(value: Any, schema: Mapping[str, Any], root: Mapping[str, Any], location: str) -> None:
    if "$ref" in schema:
        _validate_node(value, _resolve_ref(root, schema["$ref"]), root, location)
        return
    if "oneOf" in schema:
        matches = 0
        for alternative in schema["oneOf"]:
            try:
                _validate_node(value, alternative, root, location)
            except ValidationV2SchemaRegistryError:
                continue
            matches += 1
        if matches != 1:
            raise ValidationV2SchemaRegistryError(f"{location} oneOf match count differs: {matches}")
    if "const" in schema:
        expected = schema["const"]
        if type(value) is not type(expected) or value != expected:
            raise ValidationV2SchemaRegistryError(f"{location} const differs")
    if "enum" in schema and not any(type(value) is type(item) and value == item for item in schema["enum"]):
        raise ValidationV2SchemaRegistryError(f"{location} enum differs")
    expected_type = schema.get("type")
    type_ok = {
        "object": type(value) is dict,
        "array": type(value) is list,
        "string": type(value) is str,
        "integer": type(value) is int,
        "boolean": type(value) is bool,
        None: True,
    }.get(expected_type, False)
    if not type_ok:
        raise ValidationV2SchemaRegistryError(f"{location} type differs")
    if expected_type == "string":
        if len(value) < schema.get("minLength", 0):
            raise ValidationV2SchemaRegistryError(f"{location} is too short")
        if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
            raise ValidationV2SchemaRegistryError(f"{location} pattern differs")
    elif expected_type == "array":
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", len(value)):
            raise ValidationV2SchemaRegistryError(f"{location} length differs")
        if "items" in schema:
            for index, item in enumerate(value):
                _validate_node(item, schema["items"], root, f"{location}[{index}]")
    elif expected_type == "object":
        required = set(schema.get("required", ()))
        missing = required - set(value)
        if missing:
            raise ValidationV2SchemaRegistryError(f"{location} missing fields: {sorted(missing)}")
        if len(value) < schema.get("minProperties", 0):
            raise ValidationV2SchemaRegistryError(f"{location} has too few properties")
        if "propertyNames" in schema:
            for key in value:
                _validate_node(key, schema["propertyNames"], root, f"{location} property name")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = set(value) - set(properties)
            if extra:
                raise ValidationV2SchemaRegistryError(f"{location} extra fields: {sorted(extra)}")
        for key, item in value.items():
            if key in properties:
                _validate_node(item, properties[key], root, f"{location}.{key}")
            elif type(schema.get("additionalProperties")) is dict:
                _validate_node(item, schema["additionalProperties"], root, f"{location}.{key}")
    if expected_type == "integer" and "minimum" in schema and value < schema["minimum"]:
        raise ValidationV2SchemaRegistryError(f"{location} is below minimum")


def validate_validation_v2_document_v1(filename: str, document: Mapping[str, Any]) -> str:
    records = {record.filename: record for record in load_validation_v2_schema_registry_v1()}
    if filename not in records:
        raise ValidationV2SchemaRegistryError(f"unknown V2 schema: {filename}")
    if type(document) is not dict:
        raise ValidationV2SchemaRegistryError("V2 document must be an exact object")
    record = records[filename]
    _validate_node(document, record.document, record.document, "$")
    return record.sha256
