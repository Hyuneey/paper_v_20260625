import json
from pathlib import Path
import unittest

from paperworks.v6.task039e3_execution_prep_v1 import (
    ExecutionFailureReceiptV1,
    MockProviderEventV1,
    MockProviderTransportV1,
    ProviderCallLedgerV1,
    ProviderCallSlotV1,
    TASK039E3PreparationReceiptV1,
    build_main_request_v1,
    execute_mock_provider_slot_v1,
)
from paperworks.v6.task039e3_orchestration_v1 import (
    ConstructionOutcomeLedgerV1,
    ConstructionProposalLedgerV1,
    PublicConstructionMetricsV1,
    aggregate_construction_metrics_v1,
    aggregate_direct_number_metrics_v1,
)
from task039e3_support import make_evidence, valid_core_document


class Task039E3SchemasReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).parents[1] / "schemas" / "v6"

    def _load(self, filename: str) -> dict[str, object]:
        return json.loads((self.root / filename).read_text(encoding="utf-8"))

    def test_task_schemas_are_valid_closed_json_objects(self) -> None:
        filenames = (
            "task039e3_provider_call_record_v1_schema.json",
            "task039e3_execution_failure_receipt_v1_schema.json",
            "task039e3_public_construction_metrics_v1_schema.json",
            "task039e3_preparation_receipt_v1_schema.json",
        )
        for filename in filenames:
            with self.subTest(filename=filename):
                schema = self._load(filename)
                self.assertEqual(schema["type"], "object")
                self.assertIs(schema["additionalProperties"], False)
                self.assertEqual(set(schema["required"]), set(schema["properties"]))

    def test_preparation_receipt_matches_closed_schema_and_has_no_authority(self) -> None:
        receipt = TASK039E3PreparationReceiptV1().to_dict()
        schema = self._load("task039e3_preparation_receipt_v1_schema.json")
        self.assertEqual(set(receipt), set(schema["required"]))
        self.assertEqual(receipt["status"], "passed_task039e3_scientific_execution_preparation")
        self.assertTrue(receipt["e3_authorization_bound"])
        self.assertTrue(receipt["e0_e1_lineage_bound"])
        self.assertEqual(
            receipt["e3_authorization_hash"],
            "85470f2c433bb64c052e635dbb5276fbbd26caa54394a1950317eb3deb7baae3",
        )
        self.assertFalse(receipt["provider_contacted"])
        self.assertFalse(receipt["credential_accessed"])
        self.assertFalse(receipt["real_e1_result_accessed"])
        self.assertFalse(receipt["llm_called"])
        self.assertFalse(receipt["real_t0_generated"])
        self.assertFalse(receipt["rule_v2_authorized"])
        self.assertFalse(receipt["runtime_authority"])

    def test_call_failure_and_public_contract_keys_match_schemas(self) -> None:
        evidence = make_evidence()
        ledger = ProviderCallLedgerV1()
        slot = ProviderCallSlotV1(
            0, evidence.relation.binding_hash, "T1", 1, True
        )
        call = execute_mock_provider_slot_v1(
            slot=slot,
            request=build_main_request_v1(evidence.render_view()),
            transport=MockProviderTransportV1(
                (MockProviderEventV1("valid_proposal", valid_core_document(evidence)),)
            ),
            ledger=ledger,
            parse_kind="proposal",
        ).record
        failure = ExecutionFailureReceiptV1(
            failure_reason="SYNTHETIC_FAILURE",
            failed_slot_hash=slot.slot_hash,
            completed_slot_record_hashes=(call.record_hash,),
            provider_call_ledger_hash=ledger.ledger_hash,
        )
        public = PublicConstructionMetricsV1(
            provider_call_ledger_hash=ledger.ledger_hash,
            proposal_ledger_hash=ConstructionProposalLedgerV1().ledger_hash,
            outcome_ledger_hash=ConstructionOutcomeLedgerV1().ledger_hash,
            main_metrics=aggregate_construction_metrics_v1(()),
            direct_number_metrics=aggregate_direct_number_metrics_v1(()),
            scientific_slot_count=1,
        )
        cases = (
            (
                call.to_dict(),
                "task039e3_provider_call_record_v1_schema.json",
            ),
            (
                failure.to_dict(),
                "task039e3_execution_failure_receipt_v1_schema.json",
            ),
            (
                public.to_dict(),
                "task039e3_public_construction_metrics_v1_schema.json",
            ),
        )
        for document, filename in cases:
            with self.subTest(filename=filename):
                schema = self._load(filename)
                self.assertEqual(set(document), set(schema["required"]))
                if filename == "task039e3_provider_call_record_v1_schema.json":
                    self.assertEqual(
                        set(document["slot"]),
                        set(schema["properties"]["slot"]["required"]),
                    )
                    attempt_schema = schema["properties"]["transport_attempts"][
                        "items"
                    ]
                    self.assertEqual(
                        set(document["transport_attempts"][0]),
                        set(attempt_schema["required"]),
                    )


if __name__ == "__main__":
    unittest.main()
