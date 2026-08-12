"""Exact-Commit-A external-input operational topology oracle for R1C."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_recovery_authorization_v2 import (
    ARTIFACT_TYPE,
    AUTHORIZATION_STATUS,
    EXACT_MODEL,
    HISTORICAL_CAPABILITY_RECEIPT_HASH,
    HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
    R0_BUNDLE_HASH,
    R0_COMMIT,
    R1A_COMMIT,
    R1A_TIMEOUT_AUTHORITY_HASH,
    R1B_AUDIT_COMMIT_B,
    R1B_AUDIT_RECEIPT_HASH,
    R1B_COMMIT_A,
    R1B_COMMIT_B,
    R1B_INDEPENDENT_AUDIT_BUNDLE_HASH,
    SCHEMA_VERSION,
    TASK_ID,
    URLOPEN_TIMEOUT_SECONDS,
)


R1C_COMMIT_A = "42f51cba0168f8050803139ec3333156ed2fa403"
R1C_SOURCE_MANIFEST_HASH = (
    "e494c727d03b75cbec7123c7bb92da61ead345673f678078d32a217dfe6350d0"
)


def _synthetic_r2_authorization() -> dict[str, object]:
    content: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": ARTIFACT_TYPE,
        "task_id": TASK_ID,
        "authorization_status": AUTHORIZATION_STATUS,
        "r0_commit": R0_COMMIT,
        "r0_bundle_hash": R0_BUNDLE_HASH,
        "r1a_commit": R1A_COMMIT,
        "r1a_timeout_authority_hash": R1A_TIMEOUT_AUTHORITY_HASH,
        "r1b_commit_a": R1B_COMMIT_A,
        "r1b_commit_b": R1B_COMMIT_B,
        "r1b_audit_commit_b": R1B_AUDIT_COMMIT_B,
        "r1b_independent_audit_bundle_hash": R1B_INDEPENDENT_AUDIT_BUNDLE_HASH,
        "r1b_audit_receipt_hash": R1B_AUDIT_RECEIPT_HASH,
        "r1c_commit_a": R1C_COMMIT_A,
        "r1c_source_manifest_hash": R1C_SOURCE_MANIFEST_HASH,
        "historical_capability_receipt_hash": HISTORICAL_CAPABILITY_RECEIPT_HASH,
        "historical_provider_ledger_head_hash": HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
        "exact_model": EXACT_MODEL,
        "urlopen_timeout_seconds": URLOPEN_TIMEOUT_SECONDS,
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


_DETACHED_AUDIT = textwrap.dedent(
    """
    import json
    from pathlib import Path
    import sys

    exact_root = Path(sys.argv[1]).resolve(strict=True)
    manifest_path = Path(sys.argv[2]).resolve(strict=True)
    authorization_path = Path(sys.argv[3]).resolve(strict=True)
    e1_root = Path(sys.argv[4]).resolve(strict=True)
    historical_root = Path(sys.argv[5]).resolve(strict=True)
    recovery_root = Path(sys.argv[6]).resolve(strict=True)
    sys.path.insert(0, str(exact_root / "src"))

    from paperworks.v6.task039e3_recovery_authorization_v2 import (
        HISTORICAL_CAPABILITY_RECEIPT_HASH,
        HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
        PriorAuthorityStateV2,
        R0_BUNDLE_HASH,
        R0_COMMIT,
        R1A_COMMIT,
        R1A_TIMEOUT_AUTHORITY_HASH,
        R1B_AUDIT_COMMIT_B,
        R1B_AUDIT_RECEIPT_HASH,
        R1B_COMMIT_A,
        R1B_COMMIT_B,
        R1B_INDEPENDENT_AUDIT_BUNDLE_HASH,
        run_ordered_precontact_guards_v2,
        validate_r2_authorization_v2,
    )
    from paperworks.v6.task039e3_recovery_execution_v2 import (
        collect_git_execution_state_v2,
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
    validated = validate_r2_authorization_v2(authorization)
    observed_state = collect_git_execution_state_v2(exact_root, manifest)
    calls = []
    result = run_ordered_precontact_guards_v2(
        authorization_document=authorization,
        prior_authority_state_loader=lambda: PriorAuthorityStateV2(
            R0_COMMIT,
            R0_BUNDLE_HASH,
            R1A_COMMIT,
            R1A_TIMEOUT_AUTHORITY_HASH,
            R1B_COMMIT_A,
            R1B_COMMIT_B,
            R1B_AUDIT_COMMIT_B,
            R1B_INDEPENDENT_AUDIT_BUNDLE_HASH,
            R1B_AUDIT_RECEIPT_HASH,
        ),
        git_state_loader=lambda: observed_state,
        repository_root=exact_root,
        e1_private_value=str(e1_root),
        historical_e3_private_value=str(historical_root),
        recovery_e3_private_value=str(recovery_root),
        historical_capability_receipt_hash=HISTORICAL_CAPABILITY_RECEIPT_HASH,
        historical_provider_ledger_head_hash=HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
        scientific_preflight_loader=lambda: calls.append("public_preflight")
        or {"synthetic_public_preflight": True},
        credential_loader=lambda: calls.append("credential_sentinel")
        or "SYNTHETIC_CREDENTIAL_SENTINEL",
        event_sink=calls.append,
    )
    print(json.dumps({
        "authorization_commit": validated.r1c_commit_a,
        "authorization_manifest_hash": validated.r1c_source_manifest_hash,
        "head_commit": observed_state.head_commit,
        "worktree_clean": observed_state.worktree_clean,
        "index_clean": observed_state.index_clean,
        "source_blobs_match_manifest": observed_state.source_blobs_match_manifest,
        "source_manifest_hash": observed_state.source_manifest_hash,
        "source_record_count": len(manifest["source_records"]),
        "credential_sentinel_reached": result.credential == "SYNTHETIC_CREDENTIAL_SENTINEL",
        "public_preflight_before_credential": calls.index("public_preflight") < calls.index("credential_sentinel"),
        "last_guard": result.completed_guard_order[-1],
        "historical_root_access_mode": result.private_roots.historical_e3_access_mode,
    }, sort_keys=True))
    """
)


class ExactCommitAOperationalTopologyAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = Path(__file__).resolve().parents[1]

    def _git(
        self, *arguments: str, cwd: Path | None = None, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=cwd or self.repository,
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def test_external_authority_and_manifest_preserve_exact_commit_a_cleanliness(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task039e3-r1c-exact-a-") as temporary:
            root = Path(temporary)
            worktree = root / "detached-commit-a"
            external = root / "external-authority"
            e1_root = root / "synthetic-e1"
            historical_root = root / "synthetic-historical-e3"
            recovery_root = root / "synthetic-recovery-e3"
            for path in (external, e1_root, historical_root, recovery_root):
                path.mkdir()

            # Use a local, no-hardlink clone as an isolated Git worktree.  It
            # is byte-backed by the same frozen objects without mutating the
            # coordinator repository's shared .git/worktrees registry (which
            # is intentionally read-only in some audit sandboxes).
            subprocess.run(
                [
                    "git",
                    "-c",
                    "safe.directory="
                    + self._git("rev-parse", "--absolute-git-dir").stdout.strip(),
                    "clone",
                    "--local",
                    "--no-hardlinks",
                    "--quiet",
                    str(self.repository),
                    str(worktree),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self._git("checkout", "--detach", R1C_COMMIT_A, cwd=worktree)
            try:
                manifest = external / "TASK-039E3_R1C_SOURCE_FREEZE.json"
                shutil.copy2(
                    self.repository
                    / "docs"
                    / "task_reports"
                    / "TASK-039E3_R1C_SOURCE_FREEZE.json",
                    manifest,
                )
                authorization = external / "SYNTHETIC_R2_AUTHORIZATION_V2.json"
                authorization.write_text(
                    json.dumps(_synthetic_r2_authorization(), sort_keys=True, indent=2)
                    + "\n",
                    encoding="utf-8",
                )

                self.assertEqual(
                    self._git("rev-parse", "HEAD", cwd=worktree).stdout.strip(),
                    R1C_COMMIT_A,
                )
                self.assertEqual(
                    self._git("status", "--porcelain=v1", cwd=worktree).stdout, ""
                )
                self.assertEqual(
                    self._git("diff", "--cached", "--quiet", cwd=worktree, check=False).returncode,
                    0,
                )

                completed = subprocess.run(
                    [
                        sys.executable,
                        "-I",
                        "-B",
                        "-c",
                        _DETACHED_AUDIT,
                        str(worktree),
                        str(manifest),
                        str(authorization),
                        str(e1_root),
                        str(historical_root),
                        str(recovery_root),
                    ],
                    cwd=external,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                observed = json.loads(completed.stdout)
                self.assertEqual(observed["authorization_commit"], R1C_COMMIT_A)
                self.assertEqual(
                    observed["authorization_manifest_hash"], R1C_SOURCE_MANIFEST_HASH
                )
                self.assertEqual(observed["head_commit"], R1C_COMMIT_A)
                self.assertTrue(observed["worktree_clean"])
                self.assertTrue(observed["index_clean"])
                self.assertTrue(observed["source_blobs_match_manifest"])
                self.assertEqual(
                    observed["source_manifest_hash"], R1C_SOURCE_MANIFEST_HASH
                )
                self.assertEqual(observed["source_record_count"], 14)
                self.assertTrue(observed["credential_sentinel_reached"])
                self.assertTrue(observed["public_preflight_before_credential"])
                self.assertEqual(observed["last_guard"], "credential_loaded")
                self.assertEqual(observed["historical_root_access_mode"], "read_only")
                self.assertEqual(
                    self._git("status", "--porcelain=v1", cwd=worktree).stdout, ""
                )
            finally:
                # TemporaryDirectory owns the isolated clone; it has no entry
                # in the coordinator repository's worktree registry.
                pass


if __name__ == "__main__":
    unittest.main()
