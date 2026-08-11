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
    "candidate_arm_result_contract_v1": (
        "schemas/v6/candidate_arm_result_contract_v1_schema.json"
    ),
    "candidate_budget_policy_v1": (
        "schemas/v6/candidate_budget_policy_v1_schema.json"
    ),
    "candidate_discovery_protocol_bundle_v1": (
        "schemas/v6/candidate_discovery_protocol_bundle_v1_schema.json"
    ),
    "candidate_integration_policy_v1": (
        "schemas/v6/candidate_integration_policy_v1_schema.json"
    ),
    "candidate_method_comparison_policy_v1": (
        "schemas/v6/candidate_method_comparison_policy_v1_schema.json"
    ),
    "candidate_provenance_analysis_view_v1": (
        "schemas/v6/candidate_provenance_analysis_view_v1_schema.json"
    ),
    "candidate_profiling_cohort_v1": (
        "schemas/v6/candidate_profiling_cohort_v1_schema.json"
    ),
    "candidate_profiling_entry_v1": (
        "schemas/v6/candidate_profiling_entry_v1_schema.json"
    ),
    "candidate_universe_policy_v1": (
        "schemas/v6/candidate_universe_policy_v1_schema.json"
    ),
    "canonical_context_build_result": (
        "schemas/v6/canonical_context_build_result_v1_schema.json"
    ),
    "continuous_step_feasibility_policy_v1": (
        "schemas/v6/continuous_step_feasibility_policy_v1_schema.json"
    ),
    "continuous_step_parameter_provenance_policy_v1": (
        "schemas/v6/continuous_step_parameter_provenance_policy_v1_schema.json"
    ),
    "continuous_step_process_selection_policy_v1": (
        "schemas/v6/continuous_step_process_selection_policy_v1_schema.json"
    ),
    "continuous_step_protocol_bundle_v1": (
        "schemas/v6/continuous_step_protocol_bundle_v1_schema.json"
    ),
    "continuous_step_relation_family_v1": (
        "schemas/v6/continuous_step_relation_family_v1_schema.json"
    ),
    "continuous_step_response_policy_v1": (
        "schemas/v6/continuous_step_response_policy_v1_schema.json"
    ),
    "continuous_step_rule_migration_plan_v1": (
        "schemas/v6/continuous_step_rule_migration_plan_v1_schema.json"
    ),
    "continuous_step_runtime_migration_plan_v1": (
        "schemas/v6/continuous_step_runtime_migration_plan_v1_schema.json"
    ),
    "continuous_step_trigger_policy_v1": (
        "schemas/v6/continuous_step_trigger_policy_v1_schema.json"
    ),
    "continuous_step_unsupported_policy_v1": (
        "schemas/v6/continuous_step_unsupported_policy_v1_schema.json"
    ),
    "continuous_step_verifier_migration_plan_v1": (
        "schemas/v6/continuous_step_verifier_migration_plan_v1_schema.json"
    ),
    "continuous_source_screening_record_v1": (
        "schemas/v6/continuous_source_screening_record_v1_schema.json"
    ),
    "continuous_source_event_summary_v1": (
        "schemas/v6/continuous_source_event_summary_v1_schema.json"
    ),
    "continuous_target_scale_record_v1": (
        "schemas/v6/continuous_target_scale_record_v1_schema.json"
    ),
    "continuous_directional_fit_record_v1": (
        "schemas/v6/continuous_directional_fit_record_v1_schema.json"
    ),
    "continuous_calibration_confirmation_record_v1": (
        "schemas/v6/continuous_calibration_confirmation_record_v1_schema.json"
    ),
    "hai_continuous_process_feasibility_v1": (
        "schemas/v6/hai_continuous_process_feasibility_v1_schema.json"
    ),
    "hai_continuous_process_selection_result_v1": (
        "schemas/v6/hai_continuous_process_selection_result_v1_schema.json"
    ),
    "hai_continuous_process_freeze_v1": (
        "schemas/v6/hai_continuous_process_freeze_v1_schema.json"
    ),
    "task039br2_execution_interpretation_v1": (
        "schemas/v6/task039br2_execution_interpretation_v1_schema.json"
    ),
    "task039br2_data_access_audit_v1": (
        "schemas/v6/task039br2_data_access_audit_v1_schema.json"
    ),
    "task039br2_execution_receipt_v1": (
        "schemas/v6/task039br2_execution_receipt_v1_schema.json"
    ),
    "construction_candidate_binding_receipt": (
        "schemas/v6/construction_candidate_binding_receipt_v1_schema.json"
    ),
    "normal_relation_evidence": (
        "schemas/v6/normal_relation_evidence_v1_schema.json"
    ),
    "numeric_evidence_authority_policy_v1": (
        "schemas/v6/numeric_evidence_authority_policy_v1_schema.json"
    ),
    "detector_error_context": (
        "schemas/v6/detector_error_context_v1_schema.json"
    ),
    "directional_relation_identity_v1": (
        "schemas/v6/directional_relation_identity_v1_schema.json"
    ),
    "directional_relation_selection_policy_v1": (
        "schemas/v6/directional_relation_selection_policy_v1_schema.json"
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
    "gdn_candidate_policy_v1": (
        "schemas/v6/gdn_candidate_policy_v1_schema.json"
    ),
    "gdn_candidate_result_v1": (
        "schemas/v6/gdn_candidate_result_v1_schema.json"
    ),
    "gdn_api_drift_matrix_v1": (
        "schemas/v6/gdn_api_drift_matrix_v1_schema.json"
    ),
    "gdn_index_semantics_receipt_v1": (
        "schemas/v6/gdn_index_semantics_receipt_v1_schema.json"
    ),
    "gdn_legacy_oracle_receipt_v1": (
        "schemas/v6/gdn_legacy_oracle_receipt_v1_schema.json"
    ),
    "gdn_port_compatibility_closure_receipt_v1": (
        "schemas/v6/gdn_port_compatibility_closure_receipt_v1_schema.json"
    ),
    "hai_csv_structure_audit": (
        "schemas/v6/hai_csv_structure_audit_v1_schema.json"
    ),
    "hai_continuous_route_readiness_v1": (
        "schemas/v6/hai_continuous_route_readiness_v1_schema.json"
    ),
    "hai_continuous_source_morphology_v1": (
        "schemas/v6/hai_continuous_source_morphology_v1_schema.json"
    ),
    "hai_distribution_byte_equivalence_result": (
        "schemas/v6/hai_distribution_byte_equivalence_v1_schema.json"
    ),
    "hai_label_custody_public": (
        "schemas/v6/hai_label_custody_public_v1_schema.json"
    ),
    "hai_source_exclusion_record_v1": (
        "schemas/v6/hai_source_exclusion_record_v1_schema.json"
    ),
    "hai_source_exclusion_summary_v1": (
        "schemas/v6/hai_source_exclusion_summary_v1_schema.json"
    ),
    "haiend_route_readiness_v1": (
        "schemas/v6/haiend_route_readiness_v1_schema.json"
    ),
    "hai_lfs_pointer_record": (
        "schemas/v6/hai_lfs_pointer_record_v1_schema.json"
    ),
    "hai_official_distribution_metadata": (
        "schemas/v6/hai_official_distribution_metadata_v1_schema.json"
    ),
    "hai_provenance_audit_result": (
        "schemas/v6/hai_provenance_audit_result_v1_schema.json"
    ),
    "hai_reference_inventory": (
        "schemas/v6/hai_reference_inventory_v1_schema.json"
    ),
    "metadata_candidate_policy_v1": (
        "schemas/v6/metadata_candidate_policy_v1_schema.json"
    ),
    "metadata_candidate_result_v1": (
        "schemas/v6/metadata_candidate_result_v1_schema.json"
    ),
    "normal_reference_set_binding": (
        "schemas/v6/normal_reference_set_binding_v1_schema.json"
    ),
    "rule_evidence_binding": (
        "schemas/v6/rule_evidence_binding_v1_schema.json"
    ),
    "relation_family_route_decision_v1": (
        "schemas/v6/relation_family_route_decision_v1_schema.json"
    ),
    "rule_v1_compatibility_record_v1": (
        "schemas/v6/rule_v1_compatibility_record_v1_schema.json"
    ),
    "statistical_candidate_policy_v1": (
        "schemas/v6/statistical_candidate_policy_v1_schema.json"
    ),
    "statistical_candidate_result_v1": (
        "schemas/v6/statistical_candidate_result_v1_schema.json"
    ),
    "source_scale_policy_v1": (
        "schemas/v6/source_scale_policy_v1_schema.json"
    ),
    "source_step_profiling_policy_v1": (
        "schemas/v6/source_step_profiling_policy_v1_schema.json"
    ),
    "target_response_profiling_policy_v1": (
        "schemas/v6/target_response_profiling_policy_v1_schema.json"
    ),
    "pyg_softmax_compatibility_receipt_v1": (
        "schemas/v6/pyg_softmax_compatibility_receipt_v1_schema.json"
    ),
    "profiling_identity_view_policy_v1": (
        "schemas/v6/profiling_identity_view_policy_v1_schema.json"
    ),
    "profiling_identity_view_v1": (
        "schemas/v6/profiling_identity_view_v1_schema.json"
    ),
    "relation_confirmation_policy_v1": (
        "schemas/v6/relation_confirmation_policy_v1_schema.json"
    ),
    "relation_fit_gate_policy_v1": (
        "schemas/v6/relation_fit_gate_policy_v1_schema.json"
    ),
    "relation_profiling_outcome_policy_v1": (
        "schemas/v6/relation_profiling_outcome_policy_v1_schema.json"
    ),
    "relation_profiling_protocol_v1": (
        "schemas/v6/relation_profiling_protocol_v1_schema.json"
    ),
    "task039c0_data_access_policy_v1": (
        "schemas/v6/task039c0_data_access_policy_v1_schema.json"
    ),
    "task039c0_parallel_branch_plan_v1": (
        "schemas/v6/task039c0_parallel_branch_plan_v1_schema.json"
    ),
    "task039c_arm_binding_v1": (
        "schemas/v6/task039c_arm_binding_v1_schema.json"
    ),
    "task039c_gdn_environment_receipt_v1": (
        "schemas/v6/task039c_gdn_environment_receipt_v1_schema.json"
    ),
    "task039c_gdn_final_audit_v1": (
        "schemas/v6/task039c_gdn_final_audit_v1_schema.json"
    ),
    "task039c_gdnp_data_access_audit_v1": (
        "schemas/v6/task039c_gdnp_data_access_audit_v1_schema.json"
    ),
    "task039c_gdnp_execution_receipt_v1": (
        "schemas/v6/task039c_gdnp_execution_receipt_v1_schema.json"
    ),
    "task039c_integration_receipt_v1": (
        "schemas/v6/task039c_integration_receipt_v1_schema.json"
    ),
    "task039c_three_arm_overlap_v1": (
        "schemas/v6/task039c_three_arm_overlap_v1_schema.json"
    ),
    "task039d0_relation_profiling_protocol_config": (
        "schemas/v6/task039d0_relation_profiling_protocol_config_schema.json"
    ),
    "task039d1_authorization_v1": (
        "schemas/v6/task039d1_authorization_v1_schema.json"
    ),
    "task039d1_aborted_execution_record_v1": (
        "schemas/v6/task039d1_aborted_execution_record_v1_schema.json"
    ),
    "task039d1_arm_fit_summary_v1": (
        "schemas/v6/task039d1_arm_fit_summary_v1_schema.json"
    ),
    "task039d1_data_access_audit_v1": (
        "schemas/v6/task039d1_data_access_audit_v1_schema.json"
    ),
    "task039d1_directional_fit_ledger_binding_v1": (
        "schemas/v6/task039d1_directional_fit_ledger_binding_v1_schema.json"
    ),
    "task039d1_execution_receipt_v1": (
        "schemas/v6/task039d1_execution_receipt_v1_schema.json"
    ),
    "task039d1_execution_complexity_receipt_v1": (
        "schemas/v6/task039d1_execution_complexity_receipt_v1_schema.json"
    ),
    "task039d1_final_audit_v1": (
        "schemas/v6/task039d1_final_audit_v1_schema.json"
    ),
    "task039d1_fit_result_v1": (
        "schemas/v6/task039d1_fit_result_v1_schema.json"
    ),
    "task039d1_pair_fit_summary_v1": (
        "schemas/v6/task039d1_pair_fit_summary_v1_schema.json"
    ),
    "task039d1_source_parameter_ledger_binding_v1": (
        "schemas/v6/task039d1_source_parameter_ledger_binding_v1_schema.json"
    ),
    "task039d1_target_parameter_ledger_binding_v1": (
        "schemas/v6/task039d1_target_parameter_ledger_binding_v1_schema.json"
    ),
    "task039d2_authorization_v1": (
        "schemas/v6/task039d2_authorization_v1_schema.json"
    ),
    "task039d_data_access_policy_v1": (
        "schemas/v6/task039d_data_access_policy_v1_schema.json"
    ),
    "task039d_protocol_bundle_v1": (
        "schemas/v6/task039d_protocol_bundle_v1_schema.json"
    ),
    "task039d0_authorization_v1": (
        "schemas/v6/task039d0_authorization_v1_schema.json"
    ),
    "upstream_gdn_fidelity_receipt_v1": (
        "schemas/v6/upstream_gdn_fidelity_receipt_v1_schema.json"
    ),
    "task039br0_data_access_audit_v1": (
        "schemas/v6/task039br0_data_access_audit_v1_schema.json"
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


def _schema_declares_const_v1(
    schema: Mapping[str, Any], *, property_name: str, expected: str
) -> bool:
    """Accept a top-level const or identical consts in all local oneOf branches."""

    if schema.get("properties", {}).get(property_name, {}).get("const") == expected:
        return True
    branches = schema.get("oneOf")
    definitions = schema.get("$defs", {})
    if not isinstance(branches, list) or not branches:
        return False
    values: list[Any] = []
    for branch in branches:
        reference = branch.get("$ref") if isinstance(branch, Mapping) else None
        prefix = "#/$defs/"
        if not isinstance(reference, str) or not reference.startswith(prefix):
            return False
        definition = definitions.get(reference[len(prefix):])
        if not isinstance(definition, Mapping):
            return False
        values.append(definition.get("properties", {}).get(property_name, {}).get("const"))
    return bool(values) and all(value == expected for value in values)


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
        if not _schema_declares_const_v1(
            schema,
            property_name="schema_version",
            expected=V6_SCHEMA_REGISTRY_VERSION,
        ):
            raise V6SchemaRegistryError(
                "v6 schema version does not match registry"
            )
        if not _schema_declares_const_v1(
            schema,
            property_name="artifact_type",
            expected=artifact_type,
        ):
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
