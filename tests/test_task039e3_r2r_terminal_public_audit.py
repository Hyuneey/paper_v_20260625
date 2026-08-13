from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest

from paperworks.v6.task039e3_recovery_serialization_v1 import verify_public_artifact_v1
from task039e3_terminal_audit_support import public_root, read_json, verified_artifact


EXPECTED_RECEIPT = "d164f00da3121e345907fe9076e62f4697493f26dde7448cc8527b895cbffa6e"
IMPLEMENTATION_A = "5dca2d0431d60ef2f2bdfc907ebfe3fe18521f16"
IMPLEMENTATION_B = "d511372db560fd2cf27c2d56db7c637a3324584f"
SOURCE_MANIFEST = "9037fda0bc7694fd643058a9779fb919c75664824f2f11c49dde9f4be1b209b8"
AUTHORIZATION = "4d3dda2ab78edfff5768218905aefbb6864348e7d4471270dcb6187b59499db5"
AUDIT_COMMIT_B = "6f83362a09db02c1665dd75b654b09be59b8851b"
AUDIT_BUNDLE = "6504e699583b433ff5df6cd60ce67b6d892a44d441e71acab2d0ceddfff47137"
AUDIT_RECEIPT = "9aed9c6dd2a9e9d1985f2bcd734d27cf7cd594855feb46e41823fefc8dd52e5b"

PUBLIC_NAMES = {
    "capability_reuse": "TASK-039E3_R2R_CAPABILITY_REUSE_BINDING.json",
    "provider_custody": "TASK-039E3_R2R_PROVIDER_CUSTODY_BINDING.json",
    "private_bindings": "TASK-039E3_R2R_PRIVATE_LEDGER_BINDINGS.json",
    "construction_metrics": "TASK-039E3_R2R_CONSTRUCTION_METRICS.json",
    "direct_number_metrics": "TASK-039E3_R2R_DIRECT_NUMBER_METRICS.json",
    "execution_summary": "TASK-039E3_R2R_EXECUTION_SUMMARY.json",
    "data_access_audit": "TASK-039E3_R2R_DATA_ACCESS_AUDIT.json",
    "execution_receipt": "TASK-039E3_R2R_EXECUTION_RECEIPT.json",
}
RECEIPT_FIELDS = {
    "capability_reuse": "capability_reuse_artifact_hash",
    "provider_custody": "provider_custody_binding_hash",
    "private_bindings": "private_ledger_bindings_hash",
    "construction_metrics": "construction_metrics_hash",
    "direct_number_metrics": "direct_number_metrics_hash",
    "execution_summary": "execution_summary_hash",
    "data_access_audit": "data_access_audit_hash",
}


class TerminalPublicAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = public_root()
        self.docs = {
            key: verified_artifact(self.root / filename)
            for key, filename in PUBLIC_NAMES.items()
        }

    def test_exact_regular_public_set_self_hashes_and_receipt_bindings(self) -> None:
        self.assertEqual({path.name for path in self.root.iterdir()}, set(PUBLIC_NAMES.values()))
        for filename in PUBLIC_NAMES.values():
            path = self.root / filename
            self.assertTrue(path.is_file())
            self.assertFalse(path.is_symlink())
            document = read_json(path)
            self.assertEqual(verify_public_artifact_v1(document), self.docs[next(k for k, v in PUBLIC_NAMES.items() if v == filename)])
        receipt = self.docs["execution_receipt"]
        self.assertEqual(receipt["artifact_hash"], EXPECTED_RECEIPT)
        for key, field in RECEIPT_FIELDS.items():
            self.assertEqual(receipt[field], self.docs[key]["artifact_hash"])

    def test_authority_count_and_accounting_cross_bindings(self) -> None:
        receipt = self.docs["execution_receipt"]
        self.assertEqual(receipt["execution_code_commit"], IMPLEMENTATION_A)
        self.assertEqual(receipt["implementation_commit_a"], IMPLEMENTATION_A)
        self.assertEqual(receipt["implementation_commit_b"], IMPLEMENTATION_B)
        self.assertEqual(receipt["implementation_source_manifest_hash"], SOURCE_MANIFEST)
        self.assertEqual(receipt["source_manifest_hash"], SOURCE_MANIFEST)
        self.assertEqual(receipt["r2r_authorization_hash"], AUTHORIZATION)
        self.assertEqual(receipt["independent_audit_commit_b"], AUDIT_COMMIT_B)
        self.assertEqual(receipt["independent_audit_bundle_hash"], AUDIT_BUNDLE)
        self.assertEqual(receipt["independent_audit_receipt_hash"], AUDIT_RECEIPT)
        self.assertEqual(receipt["postcontact_integrity_status"], "verified_unchanged")
        self.assertEqual(receipt["typed_accounting"], self.docs["execution_summary"]["typed_accounting"])
        bindings = self.docs["private_bindings"]
        self.assertEqual(
            (bindings["provider_records"], bindings["proposal_records"], bindings["outcome_records"], bindings["direct_number_records"]),
            (252, 251, 168, 42),
        )
        self.assertEqual(bindings["historical_r2_records_included"], 0)
        self.assertFalse(receipt["historical_partial_results_reused"])

    def test_frozen_write_last_and_final_read_contract_is_content_complete(self) -> None:
        source = (Path(__file__).parents[1] / "src/paperworks/v6/task039e3_r2r_result_finalizer_v1.py").read_text(encoding="utf-8")
        write_receipt = source.index('write_order.append("execution_receipt")')
        reread_public = source.index("observed_public: dict[str, dict[str, Any]]")
        reread_receipt = source.index('"R2R execution receipt"')
        self.assertLess(write_receipt, reread_public)
        self.assertLess(reread_public, reread_receipt)
        for key, field in RECEIPT_FIELDS.items():
            self.assertEqual(self.docs["execution_receipt"][field], self.docs[key]["artifact_hash"])

    def test_public_leak_scan(self) -> None:
        combined = "\n".join((self.root / name).read_text(encoding="utf-8") for name in PUBLIC_NAMES.values())
        for pattern in (
            r"OPENAI_API_KEY",
            r"Bearer\s+[A-Za-z0-9._-]+",
            r"(?<![A-Za-z])sk-[A-Za-z0-9_-]{8,}",
            r"[A-Za-z]:\\Users\\",
            r'"relation_identity"\s*:',
            r'"numeric_reference"\s*:',
            r'"evidence_identity"\s*:',
            r'"chain_of_thought"\s*:',
            r'"raw_provider_(?:response|content)"\s*:',
        ):
            self.assertIsNone(re.search(pattern, combined, flags=re.IGNORECASE), pattern)
        access = self.docs["data_access_audit"]
        self.assertEqual(access["prohibited_access_count"], 0)
        self.assertFalse(access["credential_persisted"])
        self.assertFalse(access["raw_private_evidence_public"])
        self.assertFalse(access["individual_proposals_public"])

    def test_source_manifest_git_objects_and_execution_worktree_bytes(self) -> None:
        repo = Path(__file__).parents[1]
        manifest = verified_artifact(repo / "docs/task_reports/TASK-039E3_R2R_DIRECT_NUMBER_RENDERING_REMEDIATION_SOURCE_FREEZE.json")
        execution = self.root.parent / "execution"
        self.assertEqual(manifest["artifact_hash"], SOURCE_MANIFEST)
        self.assertEqual(manifest["source_record_count"], 50)
        self.assertEqual(manifest["unbound_material_project_local_dependency_count"], 0)
        self.assertEqual(manifest["dynamic_imports_found"], 0)
        self.assertEqual(manifest["unresolved_project_local_imports"], [])
        git = lambda *args: subprocess.run(["git", *args], cwd=repo, check=True, stdout=subprocess.PIPE).stdout
        for record in manifest["source_records"]:
            spec = f"{IMPLEMENTATION_A}:{record['repository_path']}"
            blob = git("rev-parse", spec).decode().strip()
            data = git("cat-file", "blob", spec)
            self.assertEqual(blob, record["git_blob_sha"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), record["sha256"])
            self.assertEqual((execution / record["repository_path"]).read_bytes(), data)


if __name__ == "__main__":
    unittest.main()
