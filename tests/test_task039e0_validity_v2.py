from __future__ import annotations

import copy
import unittest

from paperworks.v6.outcomes_v1 import ConstructionArmV1
from paperworks.v6.task039e0_rule_construction_prep_v1 import (
    prepare_rule_proposal_envelope_v1,
)
from paperworks.v6.task039e0_rule_construction_protocol_v1 import (
    FairGenerationBudgetPolicyV2,
)
from paperworks.v6.task039e0_validity_v2 import verify_prepared_rule_proposal_v2
from tests.task039e0_support import (
    rehash_proposal,
    synthetic_numeric_evidence,
    synthetic_provenance,
    synthetic_relation,
)


def _fixture():
    relation = synthetic_relation()
    evidence = synthetic_numeric_evidence(relation)
    budget = FairGenerationBudgetPolicyV2()
    provenance = synthetic_provenance(
        arm=ConstructionArmV1.T1, evidence=evidence, budget=budget
    )
    proposal = prepare_rule_proposal_envelope_v1(
        relation=relation, numeric_evidence=evidence, provenance=provenance
    )
    return proposal, relation, evidence, budget, provenance


def _verify(fixture, proposal=None):
    document, relation, evidence, budget, provenance = fixture
    return verify_prepared_rule_proposal_v2(
        document if proposal is None else proposal,
        relation=relation,
        numeric_evidence=evidence,
        provenance=provenance,
        budget=budget,
        allowed_variables=frozenset({relation.source, relation.target}),
    )


class AuthoritativeValidityV2Tests(unittest.TestCase):
    def test_admissible_result_binds_v2_budget(self) -> None:
        fixture = _fixture()
        result = _verify(fixture)
        self.assertEqual(result.status, "admissible")
        self.assertEqual(result.verifier_version, "task039e0_validity_v2")
        self.assertEqual(result.budget_policy_hash, fixture[3].artifact_hash)
        self.assertFalse(result.runtime_authority_granted)

    def test_reference_issue_is_repairable_retrieve(self) -> None:
        fixture = _fixture()
        proposal = copy.deepcopy(fixture[0])
        proposal["source_threshold_reference"] = "f" * 64
        rehash_proposal(proposal)
        result = _verify(fixture, proposal)
        issue = next(item for item in result.issues if item.code == "VALIDITY_NUMERIC_REFERENCE_MISMATCH")
        self.assertEqual((issue.repairability, issue.t2_action_class), ("repairable", "retrieve"))

    def test_wrong_relation_is_nonrepairable_no_rule(self) -> None:
        fixture = _fixture()
        proposal = copy.deepcopy(fixture[0])
        proposal["relation_identity"] = "OTHER_RELATION"
        rehash_proposal(proposal)
        result = _verify(fixture, proposal)
        issue = next(item for item in result.issues if item.code == "VALIDITY_RELATION_IDENTITY_MISMATCH")
        self.assertEqual((issue.repairability, issue.t2_action_class), ("non_repairable", "no_rule"))

    def test_serialization_issue_is_repairable_revise(self) -> None:
        fixture = _fixture()
        proposal = copy.deepcopy(fixture[0])
        proposal["proposal_hash"] = "0" * 64
        result = _verify(fixture, proposal)
        issue = next(item for item in result.issues if item.code == "VALIDITY_SERIALIZATION_HASH_MISMATCH")
        self.assertEqual((issue.repairability, issue.t2_action_class), ("repairable", "revise"))

    def test_deterministic_replay(self) -> None:
        fixture = _fixture()
        self.assertEqual(_verify(fixture).to_dict(), _verify(fixture).to_dict())


if __name__ == "__main__":
    unittest.main()

