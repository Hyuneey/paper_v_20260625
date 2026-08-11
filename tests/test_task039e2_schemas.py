from __future__ import annotations

import json
import unittest
from pathlib import Path

from paperworks.v6.task039e2_execution_freeze_prep_v1 import (
    ProviderResponseCustodyReceiptV1,
    T2RetrievalCorpusPolicyV1,
    structured_output_schema_hash_v1,
)
from tests.task039e2_support import (
    synthetic_capability_receipt,
    synthetic_configuration_and_schedule,
    synthetic_hash,
    synthetic_t0_proposal,
    synthetic_view,
)


ROOT = Path(__file__).resolve().parents[1]


class E2SchemaDraftTests(unittest.TestCase):
    def test_closed_schema_drafts_parse_and_match_contract_documents(self) -> None:
        configuration, schedule = synthetic_configuration_and_schedule()
        view = synthetic_view()
        documents = {
            "task039e2_model_capability_receipt_v1_schema.json": synthetic_capability_receipt().to_dict(),
            "task039e2_construction_execution_configuration_v1_schema.json": configuration.to_dict(),
            "task039e2_construction_input_view_v1_schema.json": view.to_dict(),
            "task039e2_structured_rule_proposal_v1_schema.json": synthetic_t0_proposal(),
            "task039e2_construction_execution_schedule_v1_schema.json": schedule.to_dict(),
            "task039e2_t2_retrieval_corpus_policy_v1_schema.json": T2RetrievalCorpusPolicyV1(
                view.initial_evidence_corpus_hash
            ).to_dict(),
            "task039e2_provider_response_custody_receipt_v1_schema.json": ProviderResponseCustodyReceiptV1(
                provider_identifier="SYNTHETIC_PROVIDER",
                model_identifier="SYNTHETIC_MODEL_VERSION_001",
                call_number=1,
                provider_request_identifier="SYNTHETIC_REQUEST_001",
                response_received=True,
                structured_parse_result="parsed",
                transport_retry_count=0,
                proposal_hash=synthetic_hash("proposal"),
            ).to_dict(),
        }
        for name, document in documents.items():
            with self.subTest(schema=name):
                schema = json.loads(
                    (ROOT / "schemas" / "v6" / name).read_text(encoding="utf-8")
                )
                self.assertFalse(schema["additionalProperties"])
                self.assertEqual(set(document), set(schema["required"]))
                for field_name, definition in schema["properties"].items():
                    if "const" in definition:
                        self.assertEqual(document[field_name], definition["const"])

    def test_structured_output_schema_hash_is_deterministic(self) -> None:
        path = ROOT / "schemas" / "v6" / "task039e2_structured_rule_proposal_v1_schema.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        first = structured_output_schema_hash_v1(schema)
        second = structured_output_schema_hash_v1(
            json.loads(path.read_text(encoding="utf-8"))
        )
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)


if __name__ == "__main__":
    unittest.main()
