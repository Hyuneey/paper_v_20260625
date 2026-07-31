from __future__ import annotations

import unittest

from paperworks.contracts.outcome_binding_v1 import (
    bind_construction_candidate_v1,
    bind_governance_authority_v1,
    bind_v6_deployment_authority_v1,
)
from paperworks.contracts.rule_v1 import canonical_rule_document_sha256
from paperworks.contracts.runtime_authority import (
    authorize_v6_delayed_response_runtime,
)
from paperworks.v6.common import V6FoundationError
from paperworks.v6.outcomes_v1 import (
    ConstructionActionTypeV1,
    ConstructionArmV1,
    ConstructionTerminalStatusV1,
    GovernanceDecisionV1,
)
from paperworks.v6.normal_evidence_v1 import EvidenceStatusV1

from task039p1b_support import (
    action,
    construction_outcome,
    creation_metadata,
    governance_outcome,
)
from task039p1c_support import verify_canonical_fixture


class Task039P1COutcomeBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture, self.verification = verify_canonical_fixture()
        self.accepted = self.verification.accepted_rule
        self.result = self.verification.verifier_result
        assert self.accepted is not None

    def test_rule_candidate_binds_without_authority(self) -> None:
        transport_hash = canonical_rule_document_sha256(
            self.fixture.candidate_rule
        )
        outcome = construction_outcome(
            normal_relation_evidence_ref=(
                self.fixture.normal_evidence.artifact_hash
            ),
            candidate_rule_ref=transport_hash,
        )
        receipt = bind_construction_candidate_v1(
            outcome=outcome,
            normal_evidence=self.fixture.normal_evidence,
            collection=self.fixture.collection,
            candidate_rule=self.fixture.candidate_rule,
            creation_metadata=creation_metadata(),
        )
        self.assertEqual(receipt.candidate_rule_transport_hash, transport_hash)
        self.assertFalse(receipt.validity_authority_granted)
        self.assertFalse(receipt.runtime_authority_granted)

    def test_noncandidate_and_transport_mismatch_cannot_bind(self) -> None:
        cases = (
            {
                "construction_arm": ConstructionArmV1.T2,
                "normal_evidence_status": EvidenceStatusV1.INSUFFICIENT_SUPPORT,
                "candidate_rule_ref": None,
                "action_history": (
                    action(ConstructionActionTypeV1.NO_RULE),
                ),
                "terminal_status": ConstructionTerminalStatusV1.NO_RULE,
                "reason_codes": ("insufficient_trigger_support",),
            },
            {
                "construction_arm": ConstructionArmV1.T1,
                "candidate_rule_ref": None,
                "provider_call_budget": 1,
                "provider_calls_used": 1,
                "token_budget": 100,
                "terminal_status": ConstructionTerminalStatusV1.PROVIDER_ERROR,
                "reason_codes": ("provider_transport_error",),
                "provider_failure": True,
            },
            {
                "construction_arm": ConstructionArmV1.T1,
                "candidate_rule_ref": None,
                "provider_call_budget": 1,
                "provider_calls_used": 1,
                "token_budget": 100,
                "tokens_used": 10,
                "terminal_status": ConstructionTerminalStatusV1.INVALID_OUTPUT,
                "reason_codes": ("invalid_json",),
                "invalid_output_detected": True,
            },
            {
                "construction_arm": ConstructionArmV1.T2,
                "candidate_rule_ref": None,
                "verifier_result_refs": ("4" * 64,),
                "terminal_status": (
                    ConstructionTerminalStatusV1.NON_REPAIRABLE_REJECTION
                ),
                "reason_codes": ("policy_violation",),
            },
            {
                "construction_arm": ConstructionArmV1.T1_B,
                "candidate_rule_ref": None,
                "provider_call_budget": 2,
                "provider_calls_used": 2,
                "token_budget": 200,
                "tokens_used": 150,
                "independent_generation": True,
                "terminal_status": (
                    ConstructionTerminalStatusV1.BUDGET_EXHAUSTED
                ),
                "reason_codes": ("provider_call_budget_exhausted",),
            },
        )
        for values in cases:
            with self.subTest(status=values["terminal_status"].value):
                outcome = construction_outcome(**values)
                with self.assertRaises(V6FoundationError):
                    bind_construction_candidate_v1(
                        outcome=outcome,
                        normal_evidence=self.fixture.normal_evidence,
                        collection=self.fixture.collection,
                        candidate_rule=self.fixture.candidate_rule,
                        creation_metadata=creation_metadata(),
                    )
        with self.assertRaises(V6FoundationError):
            bind_construction_candidate_v1(
                outcome=construction_outcome(
                    normal_relation_evidence_ref=(
                        self.fixture.normal_evidence.artifact_hash
                    ),
                    candidate_rule_ref="0" * 64,
                ),
                normal_evidence=self.fixture.normal_evidence,
                collection=self.fixture.collection,
                candidate_rule=self.fixture.candidate_rule,
                creation_metadata=creation_metadata(),
            )

    def _governance(self, decision: GovernanceDecisionV1):
        transport_hash = canonical_rule_document_sha256(self.accepted)
        outcome = governance_outcome(
            accepted_rule_ref=transport_hash,
            verifier_result_ref=self.result.artifact_hash,
            normal_guard_assessment_ref="1" * 64,
            inner_utility_assessment_ref="2" * 64,
            governance_policy_ref="3" * 64,
            decision=decision,
            decision_reason_codes=(
                ("selected_by_frozen_inner_policy",)
                if decision is GovernanceDecisionV1.SELECTED_RULE
                else ("identity_not_worse",)
            ),
            applied_rule_ref=(
                transport_hash
                if decision is GovernanceDecisionV1.SELECTED_RULE
                else None
            ),
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

    def test_selected_and_noop_governance_remain_distinct(self) -> None:
        selected = self._governance(GovernanceDecisionV1.SELECTED_RULE)
        no_op = self._governance(GovernanceDecisionV1.NO_OP)
        self.assertTrue(selected.deployable)
        self.assertFalse(no_op.deployable)
        self.assertFalse(selected.runtime_authority_granted)
        self.assertFalse(no_op.runtime_authority_granted)

        bundle = authorize_v6_delayed_response_runtime(
            self.accepted,
            self.result,
            self.fixture.collection,
            selected,
            verifier_policy=self.fixture.policy,
            created_at="2026-07-31T00:00:00Z",
            creation_metadata=creation_metadata(),
        )
        deployment = bind_v6_deployment_authority_v1(
            governance_binding=selected,
            runtime_authorization_receipt=bundle.runtime_bundle.receipt,
            collection=self.fixture.collection,
            creation_metadata=creation_metadata(),
        )
        self.assertTrue(deployment.deployable)
        with self.assertRaises(V6FoundationError):
            bind_v6_deployment_authority_v1(
                governance_binding=no_op,
                runtime_authorization_receipt=bundle.runtime_bundle.receipt,
                collection=self.fixture.collection,
                creation_metadata=creation_metadata(),
            )

    def test_outer_or_sealed_governance_fails(self) -> None:
        transport_hash = canonical_rule_document_sha256(self.accepted)
        for field in ("outer_data_used", "sealed_data_used"):
            with self.subTest(field=field):
                with self.assertRaises(V6FoundationError):
                    governance_outcome(
                        accepted_rule_ref=transport_hash,
                        applied_rule_ref=transport_hash,
                        verifier_result_ref=self.result.artifact_hash,
                        normal_guard_assessment_ref="1" * 64,
                        inner_utility_assessment_ref="2" * 64,
                        governance_policy_ref="3" * 64,
                        **{field: True},
                    )


if __name__ == "__main__":
    unittest.main()
