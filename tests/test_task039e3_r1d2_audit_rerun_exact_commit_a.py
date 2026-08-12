"""Exact executable-Commit-A topology oracle using the SF1 complete manifest."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
import subprocess
import tempfile
import unittest

from paperworks.v6 import task039e3_recovery_authorization_v3 as authority
from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_recovery_execution_v3 import (
    collect_git_execution_state_v3,
    load_prior_authority_state_v3,
    validate_execution_roots_v3,
)
from paperworks.v6.task039e3_scientific_execution_v1 import validate_public_preflight_v1

from test_task039e3_r1d2_audit_rerun_authority_chain import (
    COMPLETE_MANIFEST_HASH,
    R1D2_A,
    R1D2_B,
    SF1_B,
    _authorization,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = (
    ROOT
    / "docs"
    / "task_reports"
    / "TASK-039E3_R1D2_SF1_COMPLETE_SOURCE_FREEZE.json"
)


def _git(repository: Path, *arguments: str, text: bool = True) -> str | bytes:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
    )
    return completed.stdout.strip() if text else bytes(completed.stdout)


class R1D2AuditRerunExactCommitATests(unittest.TestCase):
    def test_external_complete_manifest_and_audit_git_receipt_reach_only_sentinel(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            repository = base / "exact-r1d2-a"
            subprocess.run(
                [
                    "git",
                    "-c",
                    "safe.directory=*",
                    "clone",
                    "--local",
                    "--no-hardlinks",
                    str(ROOT),
                    str(repository),
                ],
                check=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            _git(repository, "checkout", "--detach", SF1_B)

            # Build a non-circular synthetic audit history.  Audit Commit A has
            # only an oracle marker; Commit B adds the canonical receipt.  The
            # receipt binds A, while the future authorization binds B.
            marker = repository / "tests" / "SYNTHETIC_AUDIT_RERUN_ORACLE.txt"
            marker.write_text("synthetic audit rerun oracle\n", encoding="utf-8")
            _git(repository, "add", marker.relative_to(repository).as_posix())
            _git(
                repository,
                "-c",
                "user.name=R1D2 Audit Rerun Oracle",
                "-c",
                "user.email=audit-rerun@example.invalid",
                "commit",
                "-m",
                "synthetic audit rerun commit A",
            )
            audit_a = str(_git(repository, "rev-parse", "HEAD"))
            bundle_hash = "d" * 64
            receipt_content: dict[str, object] = {
                "schema_version": "1.0.0",
                "artifact_type": authority.FINAL_AUDIT_ARTIFACT_TYPE,
                "task_id": authority.FINAL_AUDIT_TASK_ID,
                "status": authority.FINAL_AUDIT_PASS_STATUS,
                "audit_run_identity": "R1D2_AUDIT_RERUN_AFTER_SF1",
                "audit_commit_a": audit_a,
                "r1d2_commit_a": R1D2_A,
                "r1d2_commit_b": R1D2_B,
                "r1d2_source_manifest_hash": COMPLETE_MANIFEST_HASH,
                "audit_bundle_hash": bundle_hash,
                "blocking_finding_count": 0,
                "provider_contact_authorized": False,
                "recovery_probe_authorized": False,
                "scientific_execution_authorized": False,
                "rule_v2_authorized": False,
                "runtime_authority": False,
                "utility_evaluation_authorized": False,
                "winner_selected": False,
            }
            receipt = {
                **receipt_content,
                "artifact_hash": stable_hash_v1(receipt_content),
            }
            self.assertNotIn("audit_commit_b", receipt)
            self.assertNotIn("r1d2_audit_commit_b", receipt)
            receipt_path = repository / authority.FINAL_AUDIT_RECEIPT_PATH
            receipt_path.write_text(
                json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
            )
            _git(repository, "add", authority.FINAL_AUDIT_RECEIPT_PATH)
            _git(
                repository,
                "-c",
                "user.name=R1D2 Audit Rerun Oracle",
                "-c",
                "user.email=audit-rerun@example.invalid",
                "commit",
                "-m",
                "synthetic audit rerun commit B",
            )
            audit_b = str(_git(repository, "rev-parse", "HEAD"))

            external = base / "external-authority"
            external.mkdir()
            external_manifest = external / "complete-source-manifest.json"
            external_manifest.write_bytes(MANIFEST_PATH.read_bytes())
            external_receipt = external / "final-audit-receipt.json"
            external_receipt.write_text(
                json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
            )
            authorization = _authorization(
                audit_commit_b=audit_b,
                audit_bundle=bundle_hash,
                receipt_hash=str(receipt["artifact_hash"]),
            )
            external_authorization = external / "r2-authorization-v3.json"
            external_authorization.write_text(
                json.dumps(authorization, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )

            _git(repository, "checkout", "--detach", R1D2_A)
            self.assertEqual(_git(repository, "rev-parse", "HEAD"), R1D2_A)
            self.assertEqual(_git(repository, "status", "--porcelain=v1"), "")

            manifest = json.loads(external_manifest.read_text(encoding="utf-8"))
            self.assertEqual(manifest["artifact_hash"], COMPLETE_MANIFEST_HASH)
            self.assertEqual(manifest["source_record_count"], 41)
            git_state = collect_git_execution_state_v3(repository, manifest)
            self.assertTrue(git_state.source_blobs_match_manifest)
            self.assertEqual(git_state.source_manifest_hash, COMPLETE_MANIFEST_HASH)

            e1_root = base / "synthetic-e1-private"
            historical_root = base / "synthetic-historical-private"
            recovery_root = base / "synthetic-recovery-private"
            public_root = base / "synthetic-public-output"
            for private_root in (e1_root, historical_root, recovery_root):
                private_root.mkdir()

            credential_calls: list[str] = []
            events: list[str] = []
            result = authority.run_ordered_precontact_guards_v3(
                authorization_document=json.loads(
                    external_authorization.read_text(encoding="utf-8")
                ),
                prior_authority_state_loader=lambda: load_prior_authority_state_v3(repository),
                git_state_loader=lambda: git_state,
                external_audit_receipt=json.loads(
                    external_receipt.read_text(encoding="utf-8")
                ),
                git_receipt_blob_loader=lambda commit, path: authority.load_audit_receipt_git_blob_v3(
                    repository, commit, path
                ),
                historical_capability_receipt_hash=authority.HISTORICAL_CAPABILITY_RECEIPT_HASH,
                historical_provider_ledger_head_hash=authority.HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
                root_guard_loader=lambda: validate_execution_roots_v3(
                    repository_root=repository,
                    e1_private_value=str(e1_root),
                    historical_e3_private_value=str(historical_root),
                    recovery_e3_private_value=str(recovery_root),
                    public_output_value=str(public_root),
                ),
                scientific_preflight_loader=lambda: validate_public_preflight_v1(repository),
                credential_loader=lambda: credential_calls.append("sentinel") or "SENTINEL",
                event_sink=events.append,
            )
            self.assertEqual(result.credential, "SENTINEL")
            self.assertEqual(credential_calls, ["sentinel"])
            self.assertEqual(events[-1], "credential_loaded")
            self.assertEqual(result.git_state.head_commit, R1D2_A)
            self.assertEqual(result.final_audit.audit_commit_b, audit_b)
            self.assertFalse(public_root.exists(), "pre-contact topology must not write output")
            self.assertEqual(_git(repository, "status", "--porcelain=v1"), "")

    def test_exact_commit_a_manifest_records_all_reproduce_from_git_objects(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["described_execution_commit"], R1D2_A)
        records = manifest["source_records"]
        self.assertEqual(len(records), 41)
        self.assertEqual(len({record["repository_path"] for record in records}), 41)
        for record in records:
            with self.subTest(path=record["repository_path"]):
                blob = _git(
                    ROOT,
                    "rev-parse",
                    f"{R1D2_A}:{record['repository_path']}",
                )
                self.assertEqual(blob, record["git_blob_sha"])
                exact_bytes = _git(
                    ROOT,
                    "show",
                    f"{R1D2_A}:{record['repository_path']}",
                    text=False,
                )
                self.assertIsInstance(exact_bytes, bytes)
                self.assertEqual(sha256(exact_bytes).hexdigest(), record["sha256"])


if __name__ == "__main__":
    unittest.main()
