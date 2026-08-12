import unittest

from paperworks.v6.common import stable_hash_v1, thaw_json
from paperworks.v6.task039e2_execution_configuration_v1 import (
    DIRECT_NUMBER_PROVIDER_SCHEMA_V1,
    MAIN_PROVIDER_SCHEMA_V1,
)
from paperworks.v6.task039e3_execution_prep_v1 import (
    MockProviderEventV1,
    MockProviderTransportV1,
    ProviderCallLedgerV1,
    build_direct_number_request_v1,
    build_main_request_v1,
)
from paperworks.v6.task039e3_orchestration_v1 import (
    ConstructionOutcomeLedgerV1,
    ConstructionProposalLedgerV1,
    run_t1_v1,
    run_t1b_v1,
    run_t2_v1,
)
from paperworks.v6.task039e3_r2r_request_contract_v1 import (
    DIRECT_NUMBER_PROVIDER_SCHEMA_V1_HASH,
    DIRECT_NUMBER_SCHEMA_POLICY,
    ORIGINAL_MAIN_PROVIDER_SCHEMA_V1_HASH,
    RECOVERY_MAIN_PROVIDER_SCHEMA_NAME_V2,
    RECOVERY_MAIN_PROVIDER_SCHEMA_V2,
    RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH,
    assert_r2r_request_contract_v1,
    build_r2r_direct_number_request_v1,
    build_r2r_main_request_v1,
    build_r2r_t2_followup_request_v1,
)
from task039e3_support import make_evidence, valid_core_document


def _events(evidence, count: int):
    return tuple(
        MockProviderEventV1("valid_proposal", valid_core_document(evidence))
        for _ in range(count)
    )


class Task039E3R2RRequestContractTests(unittest.TestCase):
    def test_exact_schema_projection_and_hashes(self) -> None:
        assert_r2r_request_contract_v1()
        self.assertEqual(
            stable_hash_v1(MAIN_PROVIDER_SCHEMA_V1),
            ORIGINAL_MAIN_PROVIDER_SCHEMA_V1_HASH,
        )
        self.assertEqual(
            stable_hash_v1(RECOVERY_MAIN_PROVIDER_SCHEMA_V2),
            RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH,
        )
        self.assertEqual(
            stable_hash_v1(DIRECT_NUMBER_PROVIDER_SCHEMA_V1),
            DIRECT_NUMBER_PROVIDER_SCHEMA_V1_HASH,
        )
        schema = thaw_json(RECOVERY_MAIN_PROVIDER_SCHEMA_V2)
        self.assertNotIn("$schema", schema)
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["required"], MAIN_PROVIDER_SCHEMA_V1["required"])
        self.assertEqual(
            set(schema["properties"]), set(MAIN_PROVIDER_SCHEMA_V1["properties"])
        )
        serialized = str(schema)
        for removed_keyword in (
            "minLength",
            "pattern",
            "minItems",
            "maxItems",
            "uniqueItems",
        ):
            self.assertNotIn(removed_keyword, serialized)

    def test_r2r_main_builder_changes_only_structured_schema_contract(self) -> None:
        view = make_evidence().render_view()
        original = build_main_request_v1(view)
        recovery = build_r2r_main_request_v1(view)
        original_body = thaw_json(original.request_body)
        recovery_body = thaw_json(recovery.request_body)
        original_contract = original_body["response_format"]["json_schema"]
        recovery_contract = recovery_body["response_format"]["json_schema"]
        self.assertEqual(original_body["messages"], recovery_body["messages"])
        for key in set(original_body) - {"response_format"}:
            self.assertEqual(original_body[key], recovery_body[key])
        self.assertEqual(recovery.provider_schema_hash, RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH)
        self.assertEqual(recovery.schema_name, RECOVERY_MAIN_PROVIDER_SCHEMA_NAME_V2)
        self.assertTrue(recovery_contract["strict"])
        self.assertEqual(
            recovery_contract["schema"], thaw_json(RECOVERY_MAIN_PROVIDER_SCHEMA_V2)
        )
        self.assertNotEqual(original_contract["schema"], recovery_contract["schema"])

    def test_direct_number_request_is_byte_semantically_unchanged(self) -> None:
        view = make_evidence().render_view()
        self.assertEqual(DIRECT_NUMBER_SCHEMA_POLICY, "UNCHANGED")
        self.assertEqual(
            build_r2r_direct_number_request_v1(view).to_dict(),
            build_direct_number_request_v1(view).to_dict(),
        )

    def test_v1_default_request_behavior_is_unchanged(self) -> None:
        evidence = make_evidence()
        expected = build_main_request_v1(evidence.render_view())
        transport = MockProviderTransportV1(_events(evidence, 1))
        outcome = run_t1_v1(
            relation_schedule_index=0,
            evidence=evidence,
            transport=transport,
            call_ledger=ProviderCallLedgerV1(),
            proposal_ledger=ConstructionProposalLedgerV1(),
            outcome_ledger=ConstructionOutcomeLedgerV1(),
        )
        self.assertEqual(outcome.outcome, "accepted_proposal")
        self.assertEqual(transport.request_hashes, (expected.request_hash,))
        self.assertEqual(expected.provider_schema_hash, ORIGINAL_MAIN_PROVIDER_SCHEMA_V1_HASH)

    def test_t1_uses_injected_recovery_schema(self) -> None:
        evidence = make_evidence()
        expected = build_r2r_main_request_v1(evidence.render_view())
        transport = MockProviderTransportV1(_events(evidence, 1))
        outcome = run_t1_v1(
            relation_schedule_index=0,
            evidence=evidence,
            transport=transport,
            call_ledger=ProviderCallLedgerV1(),
            proposal_ledger=ConstructionProposalLedgerV1(),
            outcome_ledger=ConstructionOutcomeLedgerV1(),
            main_request_builder=build_r2r_main_request_v1,
        )
        self.assertEqual(outcome.outcome, "accepted_proposal")
        self.assertEqual(transport.request_hashes, (expected.request_hash,))

    def test_t1b_uses_three_identical_injected_recovery_requests(self) -> None:
        evidence = make_evidence()
        expected = build_r2r_main_request_v1(evidence.render_view())
        transport = MockProviderTransportV1(_events(evidence, 3))
        outcome = run_t1b_v1(
            relation_schedule_index=0,
            evidence=evidence,
            transport=transport,
            call_ledger=ProviderCallLedgerV1(),
            proposal_ledger=ConstructionProposalLedgerV1(),
            outcome_ledger=ConstructionOutcomeLedgerV1(),
            main_request_builder=build_r2r_main_request_v1,
        )
        self.assertEqual(outcome.generation_calls_consumed, 3)
        self.assertEqual(outcome.accepted_call_index, 1)
        self.assertEqual(transport.request_hashes, (expected.request_hash,) * 3)

    def test_t2_controller_is_unchanged_with_injected_recovery_builders(self) -> None:
        evidence = make_evidence()
        observed = []

        def main_builder(view):
            request = build_r2r_main_request_v1(view)
            observed.append(request)
            return request

        def followup_builder(**kwargs):
            request = build_r2r_t2_followup_request_v1(**kwargs)
            observed.append(request)
            return request

        transport = MockProviderTransportV1(_events(evidence, 2))
        outcome = run_t2_v1(
            relation_schedule_index=0,
            evidence=evidence,
            transport=transport,
            call_ledger=ProviderCallLedgerV1(),
            proposal_ledger=ConstructionProposalLedgerV1(),
            outcome_ledger=ConstructionOutcomeLedgerV1(),
            synthetic_validity_faults=(
                "SYNTHETIC_REPAIRABLE_REVISE",
                None,
                None,
            ),
            main_request_builder=main_builder,
            t2_followup_request_builder=followup_builder,
        )
        self.assertEqual(outcome.accepted_call_index, 2)
        self.assertEqual(outcome.revise_count, 1)
        self.assertEqual(outcome.retrieval_count, 0)
        self.assertEqual(outcome.feedback_path, "revise")
        self.assertEqual([item.purpose for item in observed], ["main_initial", "t2_followup"])
        self.assertTrue(
            all(
                item.provider_schema_hash == RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH
                for item in observed
            )
        )

    def test_provider_schema_relaxation_does_not_admit_duplicate_variables(self) -> None:
        evidence = make_evidence()
        invalid = valid_core_document(evidence)
        invalid["variables"] = [invalid["source"], invalid["source"]]
        transport = MockProviderTransportV1(
            (MockProviderEventV1("valid_proposal", invalid),)
        )
        outcome = run_t1_v1(
            relation_schedule_index=0,
            evidence=evidence,
            transport=transport,
            call_ledger=ProviderCallLedgerV1(),
            proposal_ledger=ConstructionProposalLedgerV1(),
            outcome_ledger=ConstructionOutcomeLedgerV1(),
            main_request_builder=build_r2r_main_request_v1,
        )
        self.assertEqual(outcome.outcome, "no_rule")
        self.assertEqual(outcome.no_rule_reason, "verifier_rejection")
        self.assertEqual(outcome.verifier_rejected_proposal_count, 1)


if __name__ == "__main__":
    unittest.main()
