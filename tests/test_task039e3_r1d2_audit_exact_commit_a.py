"""Exact-Commit-A external-input/pre-credential topology oracle."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6 import task039e3_recovery_authorization_v3 as authority
from paperworks.v6.task039e3_recovery_execution_v3 import (
    collect_git_execution_state_v3,
    load_prior_authority_state_v3,
    validate_execution_roots_v3,
)
from paperworks.v6.task039e3_scientific_execution_v1 import (
    validate_public_preflight_v1,
)


ROOT = Path(__file__).resolve().parents[1]
R1D2_A = "2653f2b7349a049f9ca4828d736dfea9462c4748"
R1D2_B = "3da8b7007b7dd78d934554b299e6cb264a0e6470"
MANIFEST_HASH = "d9ea32af4ffb60af8bb6d0b7a496a74e4126d8e411e337da64ce64e15a152e48"


def _run(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def _authorization(
    *, audit_commit_b: str, audit_bundle: str, receipt_hash: str
) -> dict[str, object]:
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
        "r1c_commit_a": authority.R1C_COMMIT_A,
        "r1c_commit_b": authority.R1C_COMMIT_B,
        "r1c_source_manifest_hash": authority.R1C_SOURCE_MANIFEST_HASH,
        "r1c_implementation_receipt_hash": authority.R1C_IMPLEMENTATION_RECEIPT_HASH,
        "r1c_remediation_bundle_hash": authority.R1C_REMEDIATION_BUNDLE_HASH,
        "r1c_audit_commit_b": authority.R1C_AUDIT_COMMIT_B,
        "r1c_independent_audit_bundle_hash": authority.R1C_INDEPENDENT_AUDIT_BUNDLE_HASH,
        "r1c_audit_receipt_hash": authority.R1C_AUDIT_RECEIPT_HASH,
        "corrected_custody_accounting_hash": authority.CORRECTED_CUSTODY_ACCOUNTING_HASH,
        "historical_blocked_r1d_commit": authority.HISTORICAL_BLOCKED_R1D_COMMIT,
        "historical_blocked_r1d_preflight_hash": authority.HISTORICAL_BLOCKED_R1D_PREFLIGHT_HASH,
        "historical_blocked_r1d_implementation_receipt_hash": authority.HISTORICAL_BLOCKED_R1D_IMPLEMENTATION_RECEIPT_HASH,
        "historical_blocked_r1d_data_access_audit_hash": authority.HISTORICAL_BLOCKED_R1D_DATA_ACCESS_AUDIT_HASH,
        "r1d2_commit_a": R1D2_A,
        "r1d2_commit_b": R1D2_B,
        "r1d2_source_manifest_hash": MANIFEST_HASH,
        "r1d2_audit_commit_b": audit_commit_b,
        "r1d2_independent_audit_bundle_hash": audit_bundle,
        "r1d2_audit_receipt_hash": receipt_hash,
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


class R1D2AuditExactCommitATopologyTests(unittest.TestCase):
    def test_exact_commit_a_external_authority_manifest_roots_reach_sentinel(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            repository = base / "exact-a"
            git_directory = _run(ROOT, "rev-parse", "--absolute-git-dir")
            subprocess.run(
                [
                    "git",
                    "-c",
                    f"safe.directory={git_directory}",
                    "clone",
                    "--local",
                    "--no-hardlinks",
                    str(ROOT),
                    str(repository),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            _run(repository, "checkout", "--detach", R1D2_B)

            # Construct a non-circular synthetic future Audit A then reports-only
            # Audit B.  The receipt binds Audit A, while future R2 authority (not
            # the receipt itself) binds Audit B and the receipt hash.
            marker = repository / "tests/SYNTHETIC_R1D2_AUDIT_ORACLE.txt"
            marker.write_text("synthetic audit-only oracle\n", encoding="utf-8")
            _run(repository, "add", marker.relative_to(repository).as_posix())
            _run(
                repository,
                "-c", "user.name=R1D2 Audit Oracle",
                "-c", "user.email=audit@example.invalid",
                "commit", "-m", "synthetic audit commit A",
            )
            audit_a = _run(repository, "rev-parse", "HEAD")
            bundle = "a" * 64
            receipt_content: dict[str, object] = {
                "schema_version": "1.0.0",
                "artifact_type": authority.FINAL_AUDIT_ARTIFACT_TYPE,
                "task_id": authority.FINAL_AUDIT_TASK_ID,
                "status": authority.FINAL_AUDIT_PASS_STATUS,
                "audit_commit_a": audit_a,
                "r1d2_commit_a": R1D2_A,
                "r1d2_commit_b": R1D2_B,
                "r1d2_source_manifest_hash": MANIFEST_HASH,
                "audit_bundle_hash": bundle,
                "provider_contacted": False,
            }
            receipt = {
                **receipt_content,
                "artifact_hash": stable_hash_v1(receipt_content),
            }
            receipt_path = repository / authority.FINAL_AUDIT_RECEIPT_PATH
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_path.write_text(
                json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
            )
            _run(repository, "add", authority.FINAL_AUDIT_RECEIPT_PATH)
            _run(
                repository,
                "-c", "user.name=R1D2 Audit Oracle",
                "-c", "user.email=audit@example.invalid",
                "commit", "-m", "synthetic audit commit B",
            )
            audit_b = _run(repository, "rev-parse", "HEAD")

            external = base / "external"
            external.mkdir()
            manifest_external = external / "R1D2_SOURCE_FREEZE.json"
            manifest_external.write_bytes(
                (ROOT / "docs/task_reports/TASK-039E3_R1D2_SOURCE_FREEZE.json").read_bytes()
            )
            receipt_external = external / "R1D2_AUDIT_RECEIPT.json"
            receipt_external.write_text(
                json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
            )
            authorization = _authorization(
                audit_commit_b=audit_b,
                audit_bundle=bundle,
                receipt_hash=str(receipt["artifact_hash"]),
            )
            authorization_external = external / "R2_AUTHORIZATION.json"
            authorization_external.write_text(
                json.dumps(authorization, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )

            _run(repository, "checkout", "--detach", R1D2_A)
            self.assertEqual(_run(repository, "rev-parse", "HEAD"), R1D2_A)
            self.assertEqual(_run(repository, "status", "--porcelain=v1"), "")

            e1 = base / "e1-private"
            historical = base / "historical-private"
            recovery = base / "recovery-private"
            public = base / "sanitized-public"
            for root in (e1, historical, recovery):
                root.mkdir()
            manifest = json.loads(manifest_external.read_text(encoding="utf-8"))
            observed_git = collect_git_execution_state_v3(repository, manifest)
            credential_calls: list[str] = []
            roots = lambda: validate_execution_roots_v3(
                repository_root=repository,
                e1_private_value=str(e1),
                historical_e3_private_value=str(historical),
                recovery_e3_private_value=str(recovery),
                public_output_value=str(public),
            )
            result = authority.run_ordered_precontact_guards_v3(
                authorization_document=json.loads(
                    authorization_external.read_text(encoding="utf-8")
                ),
                prior_authority_state_loader=lambda: load_prior_authority_state_v3(repository),
                git_state_loader=lambda: observed_git,
                external_audit_receipt=json.loads(
                    receipt_external.read_text(encoding="utf-8")
                ),
                git_receipt_blob_loader=lambda commit, path: authority.load_audit_receipt_git_blob_v3(
                    repository, commit, path
                ),
                historical_capability_receipt_hash=authority.HISTORICAL_CAPABILITY_RECEIPT_HASH,
                historical_provider_ledger_head_hash=authority.HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
                root_guard_loader=roots,
                scientific_preflight_loader=lambda: validate_public_preflight_v1(repository),
                credential_loader=lambda: credential_calls.append("sentinel") or "SENTINEL",
            )
            self.assertEqual(result.git_state.head_commit, R1D2_A)
            self.assertEqual(result.git_state.source_manifest_hash, MANIFEST_HASH)
            self.assertTrue(result.git_state.source_blobs_match_manifest)
            self.assertEqual(result.final_audit.audit_commit_b, audit_b)
            self.assertEqual(credential_calls, ["sentinel"])
            self.assertEqual(_run(repository, "status", "--porcelain=v1"), "")
            self.assertFalse(public.exists(), "pre-contact topology must not write output")
            self.assertEqual(shutil.which("git") is not None, True)


if __name__ == "__main__":
    unittest.main()
