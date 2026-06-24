"""Variable metadata schemas and validation utilities."""

from paperworks.metadata.schema import (
    MetadataCoverageReport,
    MetadataRegistry,
    MetadataSourceMethod,
    MetadataValidationError,
    PhysicalType,
    ReviewStatus,
    ValueType,
    VariableMetadata,
    VariableRole,
    load_metadata_json,
    suggest_metadata_from_name,
    validate_feature_coverage,
)

__all__ = [
    "MetadataCoverageReport",
    "MetadataRegistry",
    "MetadataSourceMethod",
    "MetadataValidationError",
    "PhysicalType",
    "ReviewStatus",
    "ValueType",
    "VariableMetadata",
    "VariableRole",
    "load_metadata_json",
    "suggest_metadata_from_name",
    "validate_feature_coverage",
]

