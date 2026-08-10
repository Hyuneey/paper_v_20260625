from __future__ import annotations

import ast
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from paperworks.contracts.outcome_binding_v1 import (
    bind_construction_candidate_v1,
    bind_governance_authority_v1,
)
from paperworks.contracts.rule_v1 import canonical_rule_document_sha256
from paperworks.contracts.runtime_authority import (
    authorize_v6_delayed_response_runtime,
)
from paperworks.v6.schema_registry_v1 import load_v6_schema_registry_v1
from paperworks.v6.outcomes_v1 import GovernanceDecisionV1

from task039p1b_support import (
    construction_outcome,
    creation_metadata,
    governance_outcome,
)
from task039p1c_support import verify_canonical_fixture


ROOT = Path(__file__).resolve().parents[1]
P1C_TYPES = {
    "normal_reference_set_binding",
    "rule_evidence_binding",
    "canonical_context_build_result",
    "construction_candidate_binding_receipt",
    "governance_authority_binding_receipt",
    "v6_deployment_authorization_receipt",
}
P1D_TYPES = {
    "gdn_backend_fidelity_record",
    "gdn_dependency_status",
    "gdn_fidelity_freeze",
}
TASK039A_TYPES = {
    "hai_csv_structure_audit",
    "hai_label_custody_public",
    "hai_lfs_pointer_record",
    "hai_provenance_audit_result",
    "hai_reference_inventory",
}
TASK039AR_TYPES = {
    "hai_distribution_byte_equivalence_result",
    "hai_official_distribution_metadata",
}
TASK039BR0_TYPES = {
    "hai_continuous_route_readiness_v1",
    "hai_continuous_source_morphology_v1",
    "hai_source_exclusion_record_v1",
    "hai_source_exclusion_summary_v1",
    "haiend_route_readiness_v1",
    "relation_family_route_decision_v1",
    "rule_v1_compatibility_record_v1",
    "task039br0_data_access_audit_v1",
}
TASK039BR1_TYPES = {
    "continuous_step_feasibility_policy_v1",
    "continuous_step_parameter_provenance_policy_v1",
    "continuous_step_process_selection_policy_v1",
    "continuous_step_protocol_bundle_v1",
    "continuous_step_relation_family_v1",
    "continuous_step_response_policy_v1",
    "continuous_step_rule_migration_plan_v1",
    "continuous_step_runtime_migration_plan_v1",
    "continuous_step_trigger_policy_v1",
    "continuous_step_unsupported_policy_v1",
    "continuous_step_verifier_migration_plan_v1",
}
TASK039BR2_TYPES = {
    "continuous_calibration_confirmation_record_v1",
    "continuous_directional_fit_record_v1",
    "continuous_source_event_summary_v1",
    "continuous_source_screening_record_v1",
    "continuous_target_scale_record_v1",
    "hai_continuous_process_feasibility_v1",
    "hai_continuous_process_freeze_v1",
    "hai_continuous_process_selection_result_v1",
    "task039br2_data_access_audit_v1",
    "task039br2_execution_interpretation_v1",
    "task039br2_execution_receipt_v1",
}
TASK039C0_TYPES = {
    "candidate_arm_result_contract_v1",
    "candidate_budget_policy_v1",
    "candidate_discovery_protocol_bundle_v1",
    "candidate_integration_policy_v1",
    "candidate_universe_policy_v1",
    "gdn_candidate_policy_v1",
    "metadata_candidate_policy_v1",
    "statistical_candidate_policy_v1",
    "task039c0_data_access_policy_v1",
    "task039c0_parallel_branch_plan_v1",
}


class Task039P1CSchemaBoundaryTests(unittest.TestCase):
    def test_p1c_and_p1d_schemas_are_registered_and_meta_valid(self) -> None:
        registry = load_v6_schema_registry_v1(repository_root=ROOT)
        self.assertTrue(P1C_TYPES.issubset(registry.artifact_types))
        self.assertTrue(P1D_TYPES.issubset(registry.artifact_types))
        self.assertTrue(TASK039A_TYPES.issubset(registry.artifact_types))
        self.assertTrue(TASK039AR_TYPES.issubset(registry.artifact_types))
        self.assertTrue(TASK039BR0_TYPES.issubset(registry.artifact_types))
        self.assertTrue(TASK039BR1_TYPES.issubset(registry.artifact_types))
        self.assertTrue(TASK039BR2_TYPES.issubset(registry.artifact_types))
        self.assertTrue(TASK039C0_TYPES.issubset(registry.artifact_types))
        self.assertEqual(len(registry.artifact_types), 80)
        for artifact_type in (
            P1C_TYPES
            | P1D_TYPES
            | TASK039A_TYPES
            | TASK039AR_TYPES
            | TASK039BR0_TYPES
            | TASK039BR1_TYPES
            | TASK039BR2_TYPES
            | TASK039C0_TYPES
        ):
            Draft202012Validator.check_schema(
                registry.schema_for(artifact_type)
            )

    def test_p1c_artifact_instances_validate_against_registered_schemas(
        self,
    ) -> None:
        registry = load_v6_schema_registry_v1(repository_root=ROOT)
        fixture, verification = verify_canonical_fixture()
        accepted = verification.accepted_rule
        assert accepted is not None
        candidate_hash = canonical_rule_document_sha256(
            fixture.candidate_rule
        )
        construction = bind_construction_candidate_v1(
            outcome=construction_outcome(
                normal_relation_evidence_ref=(
                    fixture.normal_evidence.artifact_hash
                ),
                candidate_rule_ref=candidate_hash,
            ),
            normal_evidence=fixture.normal_evidence,
            collection=fixture.collection,
            candidate_rule=fixture.candidate_rule,
            creation_metadata=creation_metadata(),
        )
        accepted_transport = canonical_rule_document_sha256(accepted)
        governance = bind_governance_authority_v1(
            outcome=governance_outcome(
                accepted_rule_ref=accepted_transport,
                verifier_result_ref=(
                    verification.verifier_result.artifact_hash
                ),
                normal_guard_assessment_ref="1" * 64,
                inner_utility_assessment_ref="2" * 64,
                governance_policy_ref="3" * 64,
                decision=GovernanceDecisionV1.SELECTED_RULE,
                applied_rule_ref=accepted_transport,
            ),
            accepted_rule=accepted,
            verifier_result=verification.verifier_result,
            collection=fixture.collection,
            verifier_policy=fixture.policy,
            normal_guard_assessment_ref="1" * 64,
            inner_utility_assessment_ref="2" * 64,
            governance_policy_ref="3" * 64,
            creation_metadata=creation_metadata(),
        )
        runtime = authorize_v6_delayed_response_runtime(
            accepted,
            verification.verifier_result,
            fixture.collection,
            governance,
            verifier_policy=fixture.policy,
            created_at="2026-07-31T00:00:00Z",
            creation_metadata=creation_metadata(),
        )
        instances = {
            "normal_reference_set_binding": (
                fixture.collection.normal_reference_binding.to_dict()
            ),
            "rule_evidence_binding": fixture.collection.evidence.to_dict(),
            "canonical_context_build_result": (
                fixture.build_result.to_dict()
            ),
            "construction_candidate_binding_receipt": (
                construction.to_dict()
            ),
            "governance_authority_binding_receipt": governance.to_dict(),
            "v6_deployment_authorization_receipt": (
                runtime.deployment_receipt.to_dict()
            ),
        }
        for artifact_type, instance in instances.items():
            with self.subTest(artifact_type=artifact_type):
                validator = Draft202012Validator(
                    registry.schema_for(artifact_type)
                )
                self.assertEqual(list(validator.iter_errors(instance)), [])

    def test_p1b_modules_remain_free_of_canonical_imports(self) -> None:
        for relative in (
            "src/paperworks/v6/common.py",
            "src/paperworks/v6/normal_evidence_v1.py",
            "src/paperworks/v6/detector_context_v1.py",
            "src/paperworks/v6/outcomes_v1.py",
            "src/paperworks/v6/adapters_v1.py",
            "src/paperworks/v6/schema_registry_v1.py",
        ):
            with self.subTest(path=relative):
                tree = ast.parse(
                    (ROOT / relative).read_text(encoding="utf-8"),
                    filename=relative,
                )
                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        imports.append(node.module)
                    elif isinstance(node, ast.Import):
                        imports.extend(alias.name for alias in node.names)
                self.assertFalse(
                    any(
                        item == "paperworks.contracts"
                        or item.startswith("paperworks.contracts.")
                        for item in imports
                    ),
                    imports,
                )

    def test_p1c_does_not_expose_rule_execution_or_scientific_consumers(
        self,
    ) -> None:
        production_files = (
            "src/paperworks/contracts/context_protocol_v1.py",
            "src/paperworks/contracts/normal_evidence_binding_v1.py",
            "src/paperworks/contracts/canonical_collection_v1.py",
            "src/paperworks/contracts/collection_adapters_v1.py",
            "src/paperworks/contracts/outcome_binding_v1.py",
        )
        prohibited = {
            "paperworks.candidates",
            "paperworks.gdn",
            "paperworks.profiling",
            "paperworks.planning",
            "paperworks.evaluation",
            "paperworks.e2e",
            "experiments.argos_reproduction",
        }
        for relative in production_files:
            with self.subTest(path=relative):
                tree = ast.parse(
                    (ROOT / relative).read_text(encoding="utf-8"),
                    filename=relative,
                )
                modules = {
                    node.module
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom) and node.module
                }
                self.assertTrue(modules.isdisjoint(prohibited))


if __name__ == "__main__":
    unittest.main()
