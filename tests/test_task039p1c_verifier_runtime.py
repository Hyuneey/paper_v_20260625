from __future__ import annotations

import dataclasses
import unittest
from types import SimpleNamespace
from unittest import mock

from paperworks.contracts.outcome_binding_v1 import (
    bind_governance_authority_v1,
)
from paperworks.contracts.rule_v1 import canonical_rule_document_sha256
from paperworks.contracts.runtime_authority import (
    RuntimeAuthorizationError,
    authorize_delayed_response_runtime,
    authorize_v6_delayed_response_runtime,
)
from paperworks.contracts.verifier_v1 import verify_delayed_response_rule
from paperworks.v6.outcomes_v1 import GovernanceDecisionV1

from task039p1b_support import creation_metadata, governance_outcome
from task039p1c_support import verify_canonical_fixture


class Task039P1CVerifierRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture, self.verification = verify_canonical_fixture()
        self.accepted = self.verification.accepted_rule
        self.result = self.verification.verifier_result
        assert self.accepted is not None

    def selected_governance(self):
        transport_hash = canonical_rule_document_sha256(self.accepted)
        outcome = governance_outcome(
            accepted_rule_ref=transport_hash,
            verifier_result_ref=self.result.artifact_hash,
            normal_guard_assessment_ref="1" * 64,
            inner_utility_assessment_ref="2" * 64,
            governance_policy_ref="3" * 64,
            decision=GovernanceDecisionV1.SELECTED_RULE,
            applied_rule_ref=transport_hash,
        )
        return bind_governance_authority_v1(
            outcome=outcome,
            accepted_rule=self.accepted,
            verifier_result=self.result,
            collection=self.fixture.collection,
            verifier_policy=self.fixture.policy,
            normal_guard_assessment_ref="1" * 64,
            inner_utility_assessment_ref="2" * 64,
            governance_policy_ref="3" * 64,
            creation_metadata=creation_metadata(),
        )

    def test_v6_rule_passes_all_twenty_validity_stages(self) -> None:
        self.assertEqual(self.result.status, "accepted")
        self.assertEqual(len(self.verification.stage_records), 20)
        self.assertEqual(
            {item.status for item in self.verification.stage_records},
            {"passed"},
        )
        self.assertEqual(
            self.result.verified_evidence,
            (self.fixture.collection.evidence.evidence_id,),
        )
        self.assertEqual(
            self.result.verified_normal_references,
            (
                self.fixture.collection.normal_reference_binding.normal_reference_id,
            ),
        )
        self.assertFalse(self.verification.runtime_authorized)
        self.assertFalse(self.fixture.collection.rule_binding_verified)

    def test_legacy_runtime_entry_rejects_v6_without_governance(self) -> None:
        with self.assertRaises(RuntimeAuthorizationError) as raised:
            authorize_delayed_response_runtime(
                self.accepted,
                self.result,
                self.fixture.collection,
                verifier_policy=self.fixture.policy,
                created_at="2026-07-31T00:00:00Z",
            )
        self.assertEqual(
            raised.exception.issue_code,
            "V6_GOVERNANCE_AUTHORITY_REQUIRED",
        )

    def test_normal_reference_source_binding_mismatch_fails_stage_14(
        self,
    ) -> None:
        source = self.fixture.collection
        changed_normal = dataclasses.replace(
            source.normal_reference_binding,
            normal_relation_evidence_hash="0" * 64,
        )
        protocol_view = SimpleNamespace(
            graph=source.graph,
            evidence=source.evidence,
            parameters=source.parameters,
            graph_by_id=source.graph_by_id,
            edge_by_id=source.edge_by_id,
            evidence_by_id=source.evidence_by_id,
            normal_reference_by_id={
                source.normal_reference_binding.normal_reference_id: (
                    changed_normal
                )
            },
            parameter_by_id=source.parameter_by_id,
            rule_binding_verified=False,
            runtime_authorized=False,
        )
        outcome = verify_delayed_response_rule(
            self.fixture.candidate_rule,
            protocol_view,
            policy=self.fixture.policy,
        )
        self.assertIn(
            "NORMAL_REFERENCE_BINDING_MISMATCH",
            {item.code for item in outcome.verifier_result.violations},
        )

    def test_selected_v6_governance_creates_synthetic_authorization_only(
        self,
    ) -> None:
        governance = self.selected_governance()
        with mock.patch(
            "paperworks.contracts.runtime_v1.execute_delayed_response_rule"
        ) as execute:
            bundle = authorize_v6_delayed_response_runtime(
                self.accepted,
                self.result,
                self.fixture.collection,
                governance,
                verifier_policy=self.fixture.policy,
                created_at="2026-07-31T00:00:00Z",
                creation_metadata=creation_metadata(),
            )
        execute.assert_not_called()
        self.assertTrue(bundle.runtime_authorized)
        self.assertEqual(
            bundle.deployment_receipt.runtime_scope,
            "synthetic_only",
        )

    def test_rule_graph_parameter_and_evidence_mutation_fail_closed(self) -> None:
        governance = self.selected_governance()
        bad_rule = dataclasses.replace(self.accepted, verified_rule_hash="0" * 64)
        with self.assertRaises(RuntimeAuthorizationError):
            authorize_v6_delayed_response_runtime(
                bad_rule,
                self.result,
                self.fixture.collection,
                governance,
                verifier_policy=self.fixture.policy,
                created_at="2026-07-31T00:00:00Z",
                creation_metadata=creation_metadata(),
            )

        with self.assertRaises(ValueError):
            dataclasses.replace(
                self.fixture.collection,
                evidence=dataclasses.replace(
                    self.fixture.collection.evidence,
                    normal_reference_binding_hash="0" * 64,
                ),
            )
        with self.assertRaises(ValueError):
            dataclasses.replace(
                self.fixture.collection,
                parameters=(
                    dataclasses.replace(
                        self.fixture.collection.parameters[0],
                        artifact_hash="0" * 64,
                    ),
                )
                + self.fixture.collection.parameters[1:],
            )
        with self.assertRaises(ValueError):
            dataclasses.replace(
                self.fixture.collection,
                graph=dataclasses.replace(
                    self.fixture.collection.graph,
                    artifact_hash="0" * 64,
                ),
            )


if __name__ == "__main__":
    unittest.main()
