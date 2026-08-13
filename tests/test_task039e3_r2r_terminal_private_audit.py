from __future__ import annotations

from collections import Counter
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_recovery_transactional_custody_v3 import reconstruct_transactional_ledger_v3
from task039e3_terminal_audit_support import final_private_root, private_root, public_root, verified_artifact


PRIVATE_NAMES = {
    "scientific_provider": "TASK039E3_R2R_SCIENTIFIC_PROVIDER_LEDGER.json",
    "proposal_validity": "TASK039E3_R2R_PROPOSAL_VALIDITY_LEDGER.json",
    "construction_outcome": "TASK039E3_R2R_CONSTRUCTION_OUTCOME_LEDGER.json",
    "direct_number": "TASK039E3_R2R_DIRECT_NUMBER_LEDGER.json",
}
PRIVATE_FIELDS = {
    "scientific_provider": "scientific_provider_ledger_hash",
    "proposal_validity": "proposal_validity_ledger_hash",
    "construction_outcome": "construction_outcome_ledger_hash",
    "direct_number": "direct_number_ledger_hash",
}


class TerminalPrivateAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = private_root()
        self.final = final_private_root()
        self.docs = {key: verified_artifact(self.final / name) for key, name in PRIVATE_NAMES.items()}
        self.bindings = verified_artifact(public_root() / "TASK-039E3_R2R_PRIVATE_LEDGER_BINDINGS.json")

    def test_exact_authoritative_snapshots_and_public_bindings(self) -> None:
        self.assertEqual({path.name for path in self.final.iterdir()}, set(PRIVATE_NAMES.values()))
        expected = {"scientific_provider": 252, "proposal_validity": 251, "construction_outcome": 168, "direct_number": 42}
        for key, count in expected.items():
            self.assertEqual(self.docs[key]["record_count"], count)
            self.assertEqual(len(self.docs[key]["records"]), count)
            self.assertEqual(self.docs[key]["artifact_hash"], self.bindings[PRIVATE_FIELDS[key]])
            self.assertEqual(self.docs[key]["historical_r2_records_included"], 0)
            self.assertFalse(self.docs[key]["credential_included"])
            self.assertFalse(self.docs[key]["authorization_header_included"])

    def test_transactional_provider_and_http_error_reconstruction(self) -> None:
        live = self.root / "scientific_r2r_v1"
        provider = reconstruct_transactional_ledger_v3(live / "provider", ledger_kind="scientific_provider")
        http = reconstruct_transactional_ledger_v3(live / "http_error_attempts", ledger_kind="http_error_custody")
        self.assertEqual(provider.authoritative_record_count, 252)
        self.assertEqual(provider.ledger_hash, "d6dc0db9abe2e0631ef7ff324358875c2575b27a6b0dc951be212a5712e7f6ee")
        self.assertEqual(provider.head_record_hash, "63bec365e303e2fa8bc0b51d13267cacb63d6cc3da4e38076830c7668a163b44")
        self.assertEqual(provider.orphan_records, ())
        self.assertEqual(provider.pending_files, ())
        self.assertEqual(http.authoritative_record_count, 0)
        self.assertEqual(http.ledger_hash, "36bd9d061b5e47a7bece1e19366d06c57ed91bdf1e2cd64bdb691875e0d3065d")
        self.assertIsNone(http.head_record_hash)
        self.assertEqual(http.orphan_records, ())
        self.assertEqual(http.pending_files, ())
        payloads = [dict(record["payload"]) for record in provider.reachable_records]
        self.assertEqual(payloads, self.docs["scientific_provider"]["records"])

    def test_provider_slot_attempt_model_and_terminal_semantics(self) -> None:
        records = self.docs["scientific_provider"]["records"]
        self.assertEqual(Counter(record["slot"]["arm"] for record in records), {"T1": 42, "T1-B": 126, "T2": 42, "T1-DIRECT-NUMBER": 42})
        self.assertEqual(Counter(record["slot"]["arm_local_call_number"] for record in records if record["slot"]["arm"] == "T1-B"), {1: 42, 2: 42, 3: 42})
        self.assertEqual(Counter(record["slot"]["relation_schedule_index"] for record in records), {index: 6 for index in range(42)})
        attempts = 0
        for record in records:
            self.assertEqual(stable_hash_v1(record["slot"]), record["slot_hash"])
            self.assertTrue(record["provider_contacted"])
            self.assertTrue(record["provider_authored_response"])
            self.assertTrue(record["response_present"])
            self.assertEqual(record["response_origin"], "provider")
            self.assertEqual(record["terminal_slot_state"], "completed_provider_response")
            self.assertEqual(record["provider_response_metadata"]["model"], "gpt-5.4-2026-03-05")
            self.assertEqual(len(record["transport_attempts"]), 1)
            attempt = record["transport_attempts"][0]
            self.assertEqual(attempt["attempt_number"], 1)
            self.assertEqual(attempt["returned_model"], "gpt-5.4-2026-03-05")
            self.assertIsNone(attempt["actual_retry_delay_before_attempt_seconds"])
            attempts += 1
        self.assertEqual(attempts, 252)

    def test_complete_relation_arm_and_direct_coverage(self) -> None:
        outcomes = self.docs["construction_outcome"]["records"]
        direct = self.docs["direct_number"]["records"]
        relations = {record["relation_identity"] for record in outcomes}
        self.assertEqual(len(relations), 42)
        self.assertEqual(len({(record["relation_identity"], record["arm"]) for record in outcomes}), 168)
        for relation in relations:
            self.assertEqual({record["arm"] for record in outcomes if record["relation_identity"] == relation}, {"T0", "T1", "T1-B", "T2"})
        self.assertEqual({record["relation_identity"] for record in direct}, relations)
        self.assertEqual(len({record["relation_identity"] for record in direct}), 42)
        self.assertTrue(all(record["generation_calls_consumed"] == 1 for record in direct))
        self.assertTrue(all(record["validity_authority"] is False and record["runtime_authority"] is False for record in direct))


if __name__ == "__main__":
    unittest.main()
