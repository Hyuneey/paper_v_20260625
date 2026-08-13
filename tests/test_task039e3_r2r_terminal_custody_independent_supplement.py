from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import unittest

from paperworks.v6.common import stable_hash_v1


ROOT = Path(__file__).resolve().parents[1]
SUPPLEMENT_HASH = "54d71edb6357e8c4d4a5479a9f0b130ca0f89f10ed4ff04ad9ba90122f3ff7c2"
BINDING_HASH = "4faccc88de1754993f3fda4bbb98fedfb44c6386d72b8cc20122b93440c13345"
REQUIRED_RECORD_FIELDS = {
    "relation_identity",
    "arm",
    "call_number",
    "proposal_envelope",
    "proposal_hash",
    "validity_hash",
    "original_record_hash",
    "recomputed_record_hash",
    "supplement_record_hash",
}


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError("JSON object required")
    return value


def _verify_self_hash(document: dict[str, object], expected: str) -> None:
    observed = document.get("artifact_hash")
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    if observed != expected or stable_hash_v1(payload) != expected:
        raise AssertionError("artifact self-hash differs")


def _walk(value: object):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key, item
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


@unittest.skipUnless(
    os.environ.get("TASK039E3_CUSTODY_SUPPLEMENT"),
    "task-local supplemental custody path is intentionally external",
)
class IndependentSupplementCustodyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.supplement = _read(Path(os.environ["TASK039E3_CUSTODY_SUPPLEMENT"]))

    def test_artifact_records_and_record_hashes_are_exact(self) -> None:
        _verify_self_hash(self.supplement, SUPPLEMENT_HASH)
        records = self.supplement["records"]
        self.assertIsInstance(records, list)
        self.assertEqual(self.supplement["proposal_record_count"], len(records))
        self.assertEqual(len(records), 251)
        keys: set[tuple[str, str, int]] = set()
        for record in records:
            self.assertEqual(set(record), REQUIRED_RECORD_FIELDS)
            key = (
                record["relation_identity"], record["arm"], record["call_number"]
            )
            self.assertNotIn(key, keys)
            keys.add(key)
            supplement_hash = stable_hash_v1(
                {
                    field: value
                    for field, value in record.items()
                    if field != "supplement_record_hash"
                }
            )
            self.assertEqual(supplement_hash, record["supplement_record_hash"])
            preimage = {
                field: record[field]
                for field in (
                    "relation_identity",
                    "arm",
                    "call_number",
                    "proposal_envelope",
                    "proposal_hash",
                    "validity_hash",
                )
            }
            recomputed = stable_hash_v1(preimage)
            self.assertEqual(recomputed, record["original_record_hash"])
            self.assertEqual(recomputed, record["recomputed_record_hash"])
        self.assertEqual(len(keys), 251)

    def test_private_supplement_excludes_unrequired_private_content(self) -> None:
        forbidden_exact_keys = {
            "numeric_value",
            "raw_time_series",
            "provider_raw_response",
            "provider_response_content",
            "OPENAI_API_KEY",
            "authorization_header",
            "chain_of_thought",
            "private_path",
        }
        observed_keys = {key for key, _ in _walk(self.supplement)}
        self.assertTrue(forbidden_exact_keys.isdisjoint(observed_keys))
        text = json.dumps(self.supplement, sort_keys=True)
        for literal in (
            "Authorization: Bearer",
            "OPENAI_API_KEY",
            '"raw_time_series":',
        ):
            self.assertNotIn(literal, text)
        self.assertFalse(self.supplement["raw_time_series_included"])

    def test_public_binding_is_exact_and_contains_hash_only(self) -> None:
        binding = _read(
            ROOT
            / "docs/task_reports/TASK-039E3_R2R_TERMINAL_CUSTODY_REMEDIATION_BINDING.json"
        )
        _verify_self_hash(binding, BINDING_HASH)
        self.assertEqual(
            binding["original_execution_receipt_hash"],
            "d164f00da3121e345907fe9076e62f4697493f26dde7448cc8527b895cbffa6e",
        )
        self.assertEqual(
            binding["original_private_proposal_ledger_hash"],
            "1d573ae83a147edf4aacb2a806016d7cfaf23b90d17e11e4e7b3c885c30e0e93",
        )
        self.assertEqual(
            binding["blocked_terminal_audit_receipt_hash"],
            "6a2f3bd18e2df370eaee5bb5da95bc12c7f3da72eff11b82fd06b3775191614b",
        )
        self.assertEqual(binding["supplemental_private_artifact_hash"], SUPPLEMENT_HASH)
        self.assertEqual(
            (
                binding["proposal_records"],
                binding["record_hash_exact_matches"],
                binding["record_hash_mismatches"],
            ),
            (251, 251, 0),
        )
        self.assertFalse(binding["original_execution_roots_modified"])
        self.assertFalse(binding["scientific_results_changed"])
        self.assertFalse(binding["provider_responses_changed"])
        forbidden_public_keys = {
            "relation_identity",
            "proposal_core",
            "evidence_hash",
            "private_path",
        }
        self.assertTrue(
            forbidden_public_keys.isdisjoint({key for key, _ in _walk(binding)})
        )

    def test_all_public_remediation_json_is_self_hashed_and_sanitized(self) -> None:
        paths = sorted(
            (ROOT / "docs/task_reports").glob(
                "TASK-039E3_R2R_TERMINAL_CUSTODY_REMEDIATION_*.json"
            )
        )
        self.assertEqual(len(paths), 5)
        for path in paths:
            document = _read(path)
            observed = document["artifact_hash"]
            self.assertEqual(
                stable_hash_v1(
                    {key: value for key, value in document.items() if key != "artifact_hash"}
                ),
                observed,
            )
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("AppData", text)
            self.assertNotIn("Authorization: Bearer", text)
            self.assertNotIn("OPENAI_API_KEY", text)


if __name__ == "__main__":
    unittest.main()
