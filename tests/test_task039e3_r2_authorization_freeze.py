"""Offline oracle for the final TASK-039E3 R2 Authorization V3 freeze."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest

from paperworks.v6 import task039e3_recovery_authorization_v3 as authority
from paperworks.v6.common import stable_hash_v1


ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION_PATH = ROOT / "docs/task_reports/TASK-039E3_R2_AUTHORIZATION_V3.json"
SCHEMA_PATH = (
    ROOT / "schemas/v6/task039e3_recovery_execution_authorization_v3_schema.json"
)
MANIFEST_PATH = (
    ROOT / "docs/task_reports/TASK-039E3_R1D2_SF1_COMPLETE_SOURCE_FREEZE.json"
)
AUDIT_RECEIPT_PATH = ROOT / authority.FINAL_AUDIT_RECEIPT_PATH
R1D2_A = "2653f2b7349a049f9ca4828d736dfea9462c4748"
R1D2_B = "3da8b7007b7dd78d934554b299e6cb264a0e6470"
AUDIT_B = "116e56246c44bb356bad5818160527c66c6bb580"
MANIFEST_HASH = "e8f236a8238bad744eced3009e2000bab9597094cab04446d920df0a0ddf9283"
AUDIT_BUNDLE_HASH = (
    "5d7da8d040647c4d4aab916c110b112f18d1a85a11500507c375480f117cbad9"
)
AUDIT_RECEIPT_HASH = (
    "e23aac907717c3159b4c16c2bee9337a26b7ae201b811a11feec02176c138225"
)
AUTHORIZATION_HASH = (
    "2133f54651447258c00546d6293600f95bbea86500a7ced7ca9bbe820ef373cc"
)


def _git_bytes(commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _prior_authority() -> authority.PriorAuthorityStateV3:
    return authority.PriorAuthorityStateV3(
        r0_commit=authority.R0_COMMIT,
        r0_bundle_hash=authority.R0_BUNDLE_HASH,
        r1a_commit=authority.R1A_COMMIT,
        r1a_timeout_authority_hash=authority.R1A_TIMEOUT_AUTHORITY_HASH,
        r1b_commit_a=authority.R1B_COMMIT_A,
        r1b_commit_b=authority.R1B_COMMIT_B,
        r1c_commit_a=authority.R1C_COMMIT_A,
        r1c_commit_b=authority.R1C_COMMIT_B,
        r1c_source_manifest_hash=authority.R1C_SOURCE_MANIFEST_HASH,
        r1c_implementation_receipt_hash=authority.R1C_IMPLEMENTATION_RECEIPT_HASH,
        r1c_remediation_bundle_hash=authority.R1C_REMEDIATION_BUNDLE_HASH,
        r1c_audit_commit_b=authority.R1C_AUDIT_COMMIT_B,
        r1c_independent_audit_bundle_hash=authority.R1C_INDEPENDENT_AUDIT_BUNDLE_HASH,
        r1c_audit_receipt_hash=authority.R1C_AUDIT_RECEIPT_HASH,
        corrected_custody_accounting_hash=authority.CORRECTED_CUSTODY_ACCOUNTING_HASH,
        historical_blocked_r1d_commit=authority.HISTORICAL_BLOCKED_R1D_COMMIT,
        historical_blocked_r1d_preflight_hash=authority.HISTORICAL_BLOCKED_R1D_PREFLIGHT_HASH,
        historical_blocked_r1d_implementation_receipt_hash=(
            authority.HISTORICAL_BLOCKED_R1D_IMPLEMENTATION_RECEIPT_HASH
        ),
        historical_blocked_r1d_data_access_audit_hash=(
            authority.HISTORICAL_BLOCKED_R1D_DATA_ACCESS_AUDIT_HASH
        ),
    )


class R2AuthorizationFreezeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = json.loads(AUTHORIZATION_PATH.read_text(encoding="utf-8"))
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_closed_schema_self_hash_and_native_validator(self) -> None:
        self.assertFalse(self.schema["additionalProperties"])
        self.assertEqual(set(self.schema["properties"]), set(self.schema["required"]))
        self.assertEqual(set(self.document), set(self.schema["required"]))
        self.assertEqual(len(self.document), 44)
        for name, rule in self.schema["properties"].items():
            value = self.document[name]
            if "const" in rule:
                self.assertEqual(value, rule["const"], name)
                self.assertIs(type(value), type(rule["const"]), name)
            if "pattern" in rule:
                self.assertRegex(value, re.compile(rule["pattern"]), name)
        content = {
            key: value for key, value in self.document.items() if key != "self_hash"
        }
        self.assertEqual(stable_hash_v1(content), AUTHORIZATION_HASH)
        self.assertEqual(self.document["self_hash"], AUTHORIZATION_HASH)
        validated = authority.validate_r2_authorization_v3(self.document)
        self.assertEqual(validated.self_hash, AUTHORIZATION_HASH)

    def test_final_audit_git_provenance_and_historical_block_are_exact(self) -> None:
        external = json.loads(AUDIT_RECEIPT_PATH.read_text(encoding="utf-8"))
        audit_git_bytes = _git_bytes(AUDIT_B, authority.FINAL_AUDIT_RECEIPT_PATH)
        self.assertEqual(json.loads(audit_git_bytes), external)
        self.assertEqual(external["artifact_hash"], AUDIT_RECEIPT_HASH)
        self.assertEqual(external["audit_bundle_hash"], AUDIT_BUNDLE_HASH)
        self.assertEqual(external["r1d2_source_manifest_hash"], MANIFEST_HASH)
        historical = json.loads(
            _git_bytes(
                "460cc11a038ba2fd5604a4b2b0b57616b70c97cc",
                authority.FINAL_AUDIT_RECEIPT_PATH,
            )
        )
        self.assertEqual(
            historical["status"], "blocked_task039e3_r1d2_independent_audit"
        )
        self.assertEqual(
            historical["artifact_hash"],
            "523368de774b289823206ddf976a8a9e164c3c397427f68c19fb7b952a3db8db",
        )

    def test_complete_manifest_reproduces_all_exact_git_blobs(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["artifact_hash"], MANIFEST_HASH)
        self.assertEqual(manifest["described_execution_commit"], R1D2_A)
        self.assertEqual(len(manifest["source_records"]), 41)
        self.assertEqual(manifest["unbound_material_dependency_count"], 0)
        for record in manifest["source_records"]:
            with self.subTest(path=record["repository_path"]):
                exact = _git_bytes(R1D2_A, record["repository_path"])
                blob = subprocess.run(
                    ["git", "hash-object", "--stdin"],
                    cwd=ROOT,
                    input=exact,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                ).stdout.decode("ascii").strip()
                self.assertEqual(blob, record["git_blob_sha"])
                self.assertEqual(hashlib.sha256(exact).hexdigest(), record["sha256"])

    def test_actual_authorization_reaches_only_sentinel_after_all_guards(self) -> None:
        receipt = json.loads(AUDIT_RECEIPT_PATH.read_text(encoding="utf-8"))
        events: list[str] = []
        credential_calls: list[str] = []

        def sentinel() -> str:
            credential_calls.append("sentinel")
            return "SYNTHETIC_SENTINEL"

        bootstrap = authority.run_ordered_precontact_guards_v3(
            authorization_document=self.document,
            prior_authority_state_loader=_prior_authority,
            git_state_loader=lambda: authority.GitExecutionStateV3(
                R1D2_A, True, True, MANIFEST_HASH, True
            ),
            external_audit_receipt=receipt,
            git_receipt_blob_loader=lambda commit, path: _git_bytes(commit, path),
            historical_capability_receipt_hash=(
                authority.HISTORICAL_CAPABILITY_RECEIPT_HASH
            ),
            historical_provider_ledger_head_hash=(
                authority.HISTORICAL_PROVIDER_LEDGER_HEAD_HASH
            ),
            root_guard_loader=lambda: {"synthetic_roots": "validated"},
            scientific_preflight_loader=lambda: {"synthetic_preflight": "validated"},
            credential_loader=sentinel,
            event_sink=events.append,
        )
        self.assertEqual(credential_calls, ["sentinel"])
        self.assertEqual(bootstrap.credential, "SYNTHETIC_SENTINEL")
        self.assertEqual(events[-1], "credential_loaded")
        self.assertEqual(
            events,
            [
                "r2_authorization_v3_validated",
                "prior_authority_bindings_validated",
                "r1d2_commit_a_and_source_manifest_validated",
                "r1d2_audit_pass_and_git_provenance_validated",
                "historical_custody_bindings_validated",
                "private_and_public_roots_validated",
                "scientific_public_preflight_validated",
                "credential_loaded",
            ],
        )

    def test_authority_boundary_is_exact(self) -> None:
        self.assertTrue(self.document["provider_contact_authorized"])
        self.assertTrue(self.document["recovery_probe_authorized"])
        self.assertTrue(
            self.document["scientific_execution_after_capability_pass_authorized"]
        )
        self.assertEqual(self.document["historical_capability_probe_count"], 1)
        self.assertEqual(self.document["maximum_additional_recovery_probes"], 1)
        self.assertEqual(self.document["maximum_cumulative_capability_probes"], 2)
        self.assertEqual(self.document["exact_model"], "gpt-5.4-2026-03-05")
        self.assertEqual(self.document["urlopen_timeout_seconds"], 30.0)
        for field in (
            "rule_v2_authorized",
            "runtime_authority",
            "utility_evaluation_authorized",
            "winner_selected",
        ):
            self.assertIs(self.document[field], False, field)


if __name__ == "__main__":
    unittest.main()
