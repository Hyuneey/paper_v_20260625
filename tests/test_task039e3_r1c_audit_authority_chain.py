from __future__ import annotations

import ast
import json
from pathlib import Path
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6 import task039e3_recovery_authorization_v2 as authority


ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION_SOURCE = ROOT / "src/paperworks/v6/task039e3_recovery_authorization_v2.py"
EXECUTION_SOURCE = ROOT / "src/paperworks/v6/task039e3_recovery_execution_v2.py"
RUNNER_SOURCE = ROOT / "scripts/run_task039e3_recovery_execution_v2.py"
SCHEMA = ROOT / "schemas/v6/task039e3_recovery_execution_authorization_v2_schema.json"

AUDIT_BINDING_FIELDS = {
    "r1c_audit_commit_b",
    "r1c_independent_audit_bundle_hash",
    "r1c_audit_receipt_hash",
}


def _synthetic_authorization() -> dict[str, object]:
    content: dict[str, object] = {
        "schema_version": authority.SCHEMA_VERSION,
        "artifact_type": authority.ARTIFACT_TYPE,
        "task_id": authority.TASK_ID,
        "authorization_status": authority.AUTHORIZATION_STATUS,
        "r0_commit": authority.R0_COMMIT,
        "r0_bundle_hash": authority.R0_BUNDLE_HASH,
        "r1a_commit": authority.R1A_COMMIT,
        "r1a_timeout_authority_hash": authority.R1A_TIMEOUT_AUTHORITY_HASH,
        "r1b_commit_a": authority.R1B_COMMIT_A,
        "r1b_commit_b": authority.R1B_COMMIT_B,
        "r1b_audit_commit_b": authority.R1B_AUDIT_COMMIT_B,
        "r1b_independent_audit_bundle_hash": authority.R1B_INDEPENDENT_AUDIT_BUNDLE_HASH,
        "r1b_audit_receipt_hash": authority.R1B_AUDIT_RECEIPT_HASH,
        "r1c_commit_a": "4" * 40,
        "r1c_source_manifest_hash": "5" * 64,
        "historical_capability_receipt_hash": authority.HISTORICAL_CAPABILITY_RECEIPT_HASH,
        "historical_provider_ledger_head_hash": authority.HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
        "exact_model": authority.EXACT_MODEL,
        "urlopen_timeout_seconds": authority.URLOPEN_TIMEOUT_SECONDS,
        "historical_capability_probe_count": 1,
        "maximum_additional_recovery_probes": 1,
        "maximum_cumulative_capability_probes": 2,
        "provider_contact_authorized": True,
        "recovery_probe_authorized": True,
        "scientific_execution_after_capability_pass_authorized": True,
        "rule_v2_authorized": False,
        "runtime_authority": False,
        "utility_evaluation_authorized": False,
        "winner_selected": False,
    }
    return {**content, "self_hash": stable_hash_v1(content)}


class R1CAuditToR2AuthorityChainTests(unittest.TestCase):
    """Independent oracle showing whether R1C-AUDIT provenance is enforceable."""

    def test_closed_authorization_and_schema_have_no_r1c_audit_binding(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertTrue(AUDIT_BINDING_FIELDS.isdisjoint(authority._AUTHORIZATION_KEYS))
        self.assertTrue(AUDIT_BINDING_FIELDS.isdisjoint(schema["properties"]))
        self.assertTrue(AUDIT_BINDING_FIELDS.isdisjoint(schema["required"]))

    def test_valid_authorization_can_be_accepted_without_r1c_audit_result(self) -> None:
        document = _synthetic_authorization()
        validated = authority.validate_r2_authorization_v2(document)
        self.assertEqual(validated.r1c_commit_a, "4" * 40)
        for field in AUDIT_BINDING_FIELDS:
            self.assertNotIn(field, document)

    def test_adding_r1c_audit_provenance_is_rejected_by_closed_contract(self) -> None:
        for field in sorted(AUDIT_BINDING_FIELDS):
            with self.subTest(field=field):
                document = _synthetic_authorization()
                document[field] = "6" * (40 if field.endswith("commit_b") else 64)
                content = {key: value for key, value in document.items() if key != "self_hash"}
                document["self_hash"] = stable_hash_v1(content)
                with self.assertRaisesRegex(
                    authority.TASK039E3RecoveryAuthorizationV2Error,
                    "closed contract",
                ):
                    authority.validate_r2_authorization_v2(document)

    def test_no_enforced_wrapper_closes_chain_before_credential(self) -> None:
        sources = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (AUTHORIZATION_SOURCE, EXECUTION_SOURCE, RUNNER_SOURCE)
        )
        for field in AUDIT_BINDING_FIELDS:
            self.assertNotIn(field, sources)
        runner_tree = ast.parse(RUNNER_SOURCE.read_text(encoding="utf-8"))
        imports = {
            alias.name
            for node in ast.walk(runner_tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        self.assertIn("run_ordered_precontact_guards_v2", imports)
        self.assertFalse(any("audit" in name.lower() and "r1c" in name.lower() for name in imports))


if __name__ == "__main__":
    unittest.main()
