"""TASK-030 structural contracts and migration-assessment foundations."""

from paperworks.contracts.legacy_adapter import (
    ADAPTER_VERSION,
    assess_legacy_artifact,
    assess_legacy_artifact_file,
)
from paperworks.contracts.models import (
    LegacyFieldMapping,
    LegacyMigrationAssessment,
    SchemaRegistration,
    StructuralValidationIssue,
    StructuralValidationReport,
)
from paperworks.contracts.schema_registry import (
    SchemaRegistry,
    SchemaRegistryError,
    load_schema_registry,
    validate_artifact,
    validate_artifact_file,
)

__all__ = [
    "ADAPTER_VERSION",
    "LegacyFieldMapping",
    "LegacyMigrationAssessment",
    "SchemaRegistration",
    "SchemaRegistry",
    "SchemaRegistryError",
    "StructuralValidationIssue",
    "StructuralValidationReport",
    "assess_legacy_artifact",
    "assess_legacy_artifact_file",
    "load_schema_registry",
    "validate_artifact",
    "validate_artifact_file",
]
