from __future__ import annotations

"""Exact-Commit-A operational dry-run audit for TASK-039E3-R1B.

The test creates a detached temporary worktree at the executable source commit.
All authority artifacts and synthetic private roots remain outside it.  The
detached Python process is isolated, bytecode-disabled, and receives every
input through argv; it never imports the runner or reads environment secrets.
"""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_recovery_authorization_v1 import (
    ARTIFACT_TYPE,
    AUTHORIZATION_STATUS,
    EXACT_MODEL,
    HISTORICAL_CAPABILITY_RECEIPT_HASH,
    HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
    R0_BUNDLE_HASH,
    R0_COMMIT,
    R1A_COMMIT,
    R1A_RECEIPT_HASH,
    R1A_TIMEOUT_AUTHORITY_HASH,
    SCHEMA_VERSION,
    TASK_ID,
    URLOPEN_TIMEOUT_SECONDS,
)


R1B_COMMIT_A = "93c2e8a6333829446c5353f1ca9b61c967f8a7a7"
R1B_SOURCE_MANIFEST_HASH = (
    "d976af3fc66a3b5aa69ef9aa3a97146cd93a6941fc9e1c28b6783ed6f1a7dc7d"
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
        "r1a_receipt_hash": R1A_RECEIPT_HASH,
        "historical_capability_receipt_hash": HISTORICAL_CAPABILITY_RECEIPT_HASH,
        "historical_provider_ledger_head_hash": HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
        "r1b_commit_a": R1B_COMMIT_A,
        "r1b_source_manifest_hash": R1B_SOURCE_MANIFEST_HASH,
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

    from paperworks.v6.task039e3_recovery_authorization_v1 import (
        HISTORICAL_CAPABILITY_RECEIPT_HASH,
        HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
        PriorAuthorityStateV1,
        R0_BUNDLE_HASH,
        R0_COMMIT,
        R1A_COMMIT,
        R1A_RECEIPT_HASH,
        R1A_TIMEOUT_AUTHORITY_HASH,
        run_ordered_precontact_guards_v1,
        validate_r2_authorization_v1,
    )
    from paperworks.v6.task039e3_recovery_execution_v1 import (
        collect_git_execution_state_v1,
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
    validated = validate_r2_authorization_v1(authorization)
    observed_state = collect_git_execution_state_v1(exact_root, manifest)
    calls = []

    result = run_ordered_precontact_guards_v1(
        authorization_document=authorization,
        prior_authority_state_loader=lambda: PriorAuthorityStateV1(
            R0_COMMIT,
            R0_BUNDLE_HASH,
            R1A_COMMIT,
            R1A_TIMEOUT_AUTHORITY_HASH,
            R1A_RECEIPT_HASH,
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
        "authorization_self_hash": validated.self_hash,
        "authorization_commit": validated.r1b_commit_a,
        "authorization_manifest_hash": validated.r1b_source_manifest_hash,
        "head_commit": observed_state.head_commit,
        "worktree_clean": observed_state.worktree_clean,
        "index_clean": observed_state.index_clean,
        "source_manifest_hash": observed_state.source_manifest_hash,
        "source_blobs_match_manifest": observed_state.source_blobs_match_manifest,
        "source_record_count": len(manifest["source_records"]),
        "credential_sentinel_reached": result.credential == "SYNTHETIC_CREDENTIAL_SENTINEL",
        "public_preflight_before_credential": calls.index("public_preflight") < calls.index("credential_sentinel"),
        "last_guard": result.completed_guard_order[-1],
        "historical_root_access_mode": result.private_roots.historical_e3_access_mode,
    }, sort_keys=True))
    """
)


class ExactCommitAOperationalAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = Path(__file__).resolve().parents[1]

    def _git(self, *arguments: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=cwd or self.repository,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def test_external_authority_topology_enables_clean_exact_commit_a_dry_run(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task039e3-r1b-exact-a-") as temporary:
            root = Path(temporary)
            worktree = root / "detached-commit-a"
            external = root / "external-authority"
            e1_root = root / "synthetic-e1"
            historical_root = root / "synthetic-historical-e3"
            recovery_root = root / "synthetic-recovery-e3"
            for path in (external, e1_root, historical_root, recovery_root):
                path.mkdir()

            self._git("worktree", "add", "--detach", str(worktree), R1B_COMMIT_A)
            try:
                self.assertEqual(
                    self._git("rev-parse", "HEAD", cwd=worktree).stdout.strip(),
                    R1B_COMMIT_A,
                )

                source_manifest = external / "TASK-039E3_R1B_SOURCE_FREEZE.json"
                shutil.copy2(
                    self.repository
                    / "docs"
                    / "task_reports"
                    / "TASK-039E3_R1B_SOURCE_FREEZE.json",
                    source_manifest,
                )
                authorization = external / "SYNTHETIC_R2_AUTHORIZATION.json"
                authorization.write_text(
                    json.dumps(
                        _synthetic_r2_authorization(),
                        sort_keys=True,
                        indent=2,
                        ensure_ascii=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )

                # Demonstrate why these future-supplied artifacts cannot be
                # placed inside the exact executable worktree.
                internal_authorization = worktree / authorization.name
                internal_manifest = worktree / source_manifest.name
                shutil.copy2(authorization, internal_authorization)
                shutil.copy2(source_manifest, internal_manifest)
                dirty = self._git("status", "--porcelain=v1", cwd=worktree).stdout
                self.assertIn(authorization.name, dirty)
                self.assertIn(source_manifest.name, dirty)
                internal_authorization.unlink()
                internal_manifest.unlink()

                # The external topology leaves both worktree and index clean.
                self.assertEqual(
                    self._git("status", "--porcelain=v1", cwd=worktree).stdout,
                    "",
                )
                self.assertEqual(
                    subprocess.run(
                        ["git", "diff", "--cached", "--quiet"],
                        cwd=worktree,
                        check=False,
                    ).returncode,
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
                        str(source_manifest),
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
                self.assertEqual(observed["authorization_commit"], R1B_COMMIT_A)
                self.assertEqual(
                    observed["authorization_manifest_hash"],
                    R1B_SOURCE_MANIFEST_HASH,
                )
                self.assertEqual(observed["head_commit"], R1B_COMMIT_A)
                self.assertTrue(observed["worktree_clean"])
                self.assertTrue(observed["index_clean"])
                self.assertTrue(observed["source_blobs_match_manifest"])
                self.assertEqual(
                    observed["source_manifest_hash"], R1B_SOURCE_MANIFEST_HASH
                )
                self.assertEqual(observed["source_record_count"], 14)
                self.assertTrue(observed["credential_sentinel_reached"])
                self.assertTrue(observed["public_preflight_before_credential"])
                self.assertEqual(observed["last_guard"], "credential_loaded")
                self.assertEqual(observed["historical_root_access_mode"], "read_only")

                # The isolated run writes neither bytecode nor custody into the
                # exact source worktree.
                self.assertEqual(
                    self._git("status", "--porcelain=v1", cwd=worktree).stdout,
                    "",
                )
            finally:
                self._git("worktree", "remove", "--force", str(worktree))


if __name__ == "__main__":
    unittest.main()
