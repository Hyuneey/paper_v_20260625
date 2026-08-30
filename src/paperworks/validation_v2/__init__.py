"""Prospective VALIDATION V2 contracts.

This package is additive.  It must not be used to reinterpret or mutate the
frozen PILOT V1 authority and artifacts.
"""

from paperworks.validation_v2.formal_v4_authority_v1 import (
    FormalV4ArtifactBindingV1,
    FormalV4AuthorizedRuntimeV1,
    FormalV4EvaluatorContractV1,
    FormalV4ExecutionContextV1,
    FormalV4PortfolioAuthorityV1,
    FormalV4RuleDescriptorV1,
    FormalV4RuntimeAuthorizationReceiptV1,
    NumericReferenceBindingV1,
    authorize_formal_v4_runtime_v1,
    build_formal_v4_portfolio_authority_v1,
    validate_formal_v4_portfolio_authority_v1,
    validate_formal_v4_runtime_authorization_v1,
)
from paperworks.validation_v2.schema_registry_v1 import (
    ValidationV2SchemaRecordV1,
    load_validation_v2_schema_registry_v1,
    validate_validation_v2_document_v1,
)
from paperworks.validation_v2.runtime_v1 import (
    FormalV4ObservationWindowV1,
    FormalV4RuntimeTraceV1,
    execute_formal_v4_rule_v1,
)

__all__ = [
    "FormalV4ArtifactBindingV1",
    "FormalV4AuthorizedRuntimeV1",
    "FormalV4EvaluatorContractV1",
    "FormalV4ExecutionContextV1",
    "FormalV4PortfolioAuthorityV1",
    "FormalV4RuleDescriptorV1",
    "FormalV4RuntimeAuthorizationReceiptV1",
    "NumericReferenceBindingV1",
    "authorize_formal_v4_runtime_v1",
    "build_formal_v4_portfolio_authority_v1",
    "validate_formal_v4_portfolio_authority_v1",
    "validate_formal_v4_runtime_authorization_v1",
    "ValidationV2SchemaRecordV1",
    "load_validation_v2_schema_registry_v1",
    "validate_validation_v2_document_v1",
    "FormalV4ObservationWindowV1",
    "FormalV4RuntimeTraceV1",
    "execute_formal_v4_rule_v1",
]
