from __future__ import annotations

"""Independent fail-closed audit of TASK-039E3-R1B pre-contact authority.

The suite uses only synthetic authorizations, injected sentinels, committed
public artifacts, and temporary directories. It never reads a credential,
contacts a provider, or opens a real private root.
"""

from argparse import Namespace
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from paperworks.v6.common import stable_hash_v1
from paperworks.v6 import task039e3_recovery_authorization_v1 as authorization_module
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
    GitExecutionStateV1,
    PriorAuthorityStateV1,
    TASK039E3RecoveryAuthorizationError,
    run_ordered_precontact_guards_v1,
    validate_r2_authorization_v1,
    validate_recovery_private_roots_v1,
)
from paperworks.v6.task039e3_recovery_execution_v1 import (
    collect_git_execution_state_v1,
    load_prior_authority_state_v1,
)


R1B_COMMIT_A = "93c2e8a6333829446c5353f1ca9b61c967f8a7a7"
R1B_COMMIT_B = "2b6e4964085b2405513680303e0586f7cca50c6d"
R1B_SOURCE_MANIFEST_HASH = (
    "d976af3fc66a3b5aa69ef9aa3a97146cd93a6941fc9e1c28b6783ed6f1a7dc7d"
)


def _authorization(**changes: object) -> dict[str, object]:
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
    content.update(changes)
    return {**content, "self_hash": stable_hash_v1(content)}


def _prior_state(**changes: object) -> PriorAuthorityStateV1:
    values: dict[str, object] = {
        "r0_commit": R0_COMMIT,
        "r0_bundle_hash": R0_BUNDLE_HASH,
        "r1a_commit": R1A_COMMIT,
        "r1a_timeout_authority_hash": R1A_TIMEOUT_AUTHORITY_HASH,
        "r1a_receipt_hash": R1A_RECEIPT_HASH,
    }
    values.update(changes)
    return PriorAuthorityStateV1(**values)  # type: ignore[arg-type]


def _git_state(**changes: object) -> GitExecutionStateV1:
    values: dict[str, object] = {
        "head_commit": R1B_COMMIT_A,
        "worktree_clean": True,
        "index_clean": True,
        "source_manifest_hash": R1B_SOURCE_MANIFEST_HASH,
        "source_blobs_match_manifest": True,
    }
    values.update(changes)
    return GitExecutionStateV1(**values)  # type: ignore[arg-type]


class R1BAuthorizationAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = Path(__file__).resolve().parents[1]

    def _root_fixture(self, base: Path) -> tuple[Path, Path, Path, Path]:
        repository = base / "synthetic-repository"
        e1 = base / "synthetic-e1"
        historical = base / "synthetic-historical-e3"
        recovery = base / "synthetic-recovery-e3"
        for path in (repository, e1, historical, recovery):
            path.mkdir()
        return repository, e1, historical, recovery

    def _guard_arguments(
        self,
        base: Path,
        *,
        calls: list[str],
    ) -> dict[str, object]:
        repository, e1, historical, recovery = self._root_fixture(base)
        return {
            "authorization_document": _authorization(),
            "prior_authority_state_loader": lambda: calls.append("load:authority")
            or _prior_state(),
            "git_state_loader": lambda: calls.append("load:git") or _git_state(),
            "repository_root": repository,
            "e1_private_value": str(e1),
            "historical_e3_private_value": str(historical),
            "recovery_e3_private_value": str(recovery),
            "historical_capability_receipt_hash": HISTORICAL_CAPABILITY_RECEIPT_HASH,
            "historical_provider_ledger_head_hash": HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
            "scientific_preflight_loader": lambda: calls.append("load:preflight")
            or {"synthetic_public_preflight": True},
            "credential_loader": lambda: calls.append("load:credential")
            or "SYNTHETIC_CREDENTIAL_SENTINEL",
            "event_sink": calls.append,
        }

    def test_exact_r2_contract_is_closed_and_self_hashed(self) -> None:
        validated = validate_r2_authorization_v1(_authorization())
        self.assertEqual(validated.r1b_commit_a, R1B_COMMIT_A)
        self.assertEqual(validated.r1b_source_manifest_hash, R1B_SOURCE_MANIFEST_HASH)

        unknown = _authorization()
        unknown["unregistered_authority"] = True
        with self.assertRaisesRegex(TASK039E3RecoveryAuthorizationError, "fields"):
            validate_r2_authorization_v1(unknown)

        tampered = _authorization()
        tampered["provider_contact_authorized"] = False
        with self.assertRaisesRegex(TASK039E3RecoveryAuthorizationError, "self-hash"):
            validate_r2_authorization_v1(tampered)

    def test_every_precontact_loader_runs_in_exact_fail_closed_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            calls: list[str] = []
            arguments = self._guard_arguments(Path(temporary), calls=calls)
            result = run_ordered_precontact_guards_v1(**arguments)  # type: ignore[arg-type]

        self.assertEqual(
            calls,
            [
                "r2_authorization_validated",
                "load:authority",
                "r0_bindings_validated",
                "r1a_bindings_validated",
                "load:git",
                "r1b_commit_validated",
                "git_worktree_and_index_validated",
                "source_manifest_validated",
                "historical_bindings_validated",
                "private_roots_validated",
                "load:preflight",
                "scientific_public_preflight_validated",
                "load:credential",
                "credential_loaded",
            ],
        )
        self.assertEqual(result.credential, "SYNTHETIC_CREDENTIAL_SENTINEL")

    def test_credential_is_unreachable_on_authority_and_historical_failures(self) -> None:
        cases = (
            ("r2", {"authorization_document": {}}),
            (
                "r0",
                {
                    "prior_authority_state_loader": lambda: _prior_state(
                        r0_bundle_hash="0" * 64
                    )
                },
            ),
            (
                "r1a",
                {
                    "prior_authority_state_loader": lambda: _prior_state(
                        r1a_receipt_hash="0" * 64
                    )
                },
            ),
            ("historical_receipt", {"historical_capability_receipt_hash": "0" * 64}),
            ("historical_ledger", {"historical_provider_ledger_head_hash": "0" * 64}),
        )
        for label, changes in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                calls: list[str] = []
                arguments = self._guard_arguments(Path(temporary), calls=calls)
                arguments.update(changes)
                with self.assertRaises(TASK039E3RecoveryAuthorizationError):
                    run_ordered_precontact_guards_v1(**arguments)  # type: ignore[arg-type]
                self.assertNotIn("load:credential", calls)
                self.assertNotIn("credential_loaded", calls)

    def test_credential_is_unreachable_on_each_git_and_manifest_failure(self) -> None:
        states = (
            _git_state(head_commit="0" * 40),
            _git_state(worktree_clean=False),
            _git_state(index_clean=False),
            _git_state(source_manifest_hash="0" * 64),
            _git_state(source_blobs_match_manifest=False),
        )
        for state in states:
            with self.subTest(state=state), tempfile.TemporaryDirectory() as temporary:
                calls: list[str] = []
                arguments = self._guard_arguments(Path(temporary), calls=calls)
                arguments["git_state_loader"] = lambda state=state: calls.append(
                    "load:git"
                ) or state
                with self.assertRaises(TASK039E3RecoveryAuthorizationError):
                    run_ordered_precontact_guards_v1(**arguments)  # type: ignore[arg-type]
                self.assertNotIn("load:preflight", calls)
                self.assertNotIn("load:credential", calls)

    def test_preflight_must_succeed_before_credential_loader(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            calls: list[str] = []
            arguments = self._guard_arguments(Path(temporary), calls=calls)

            def fail_preflight() -> object:
                calls.append("load:preflight")
                raise ValueError("synthetic public preflight rejection")

            arguments["scientific_preflight_loader"] = fail_preflight
            with self.assertRaisesRegex(ValueError, "preflight rejection"):
                run_ordered_precontact_guards_v1(**arguments)  # type: ignore[arg-type]
            self.assertNotIn("load:credential", calls)

    def test_three_root_contract_is_distinct_external_and_recovery_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository, e1, historical, recovery = self._root_fixture(root)
            # Only recovery must start empty. Existing synthetic files in E1
            # and historical custody do not get opened by root validation.
            (e1 / "SYNTHETIC_LEDGER_BINDING").write_text("x", encoding="utf-8")
            (historical / "SYNTHETIC_HISTORY_BINDING").write_text(
                "x", encoding="utf-8"
            )
            validated = validate_recovery_private_roots_v1(
                repository_root=repository,
                e1_private_value=str(e1),
                historical_e3_private_value=str(historical),
                recovery_e3_private_value=str(recovery),
            )
            self.assertEqual(validated.historical_e3_access_mode, "read_only")

            invalid_cases = (
                (repository / "contained", historical, recovery),
                (e1 / ".." / "e1", historical, recovery),
                (e1, e1, recovery),
            )
            (repository / "contained").mkdir()
            for invalid_e1, invalid_historical, invalid_recovery in invalid_cases:
                with self.subTest(invalid_e1=invalid_e1), self.assertRaises(
                    TASK039E3RecoveryAuthorizationError
                ):
                    validate_recovery_private_roots_v1(
                        repository_root=repository,
                        e1_private_value=str(invalid_e1),
                        historical_e3_private_value=str(invalid_historical),
                        recovery_e3_private_value=str(invalid_recovery),
                    )

            (recovery / "SYNTHETIC_PRIOR_STATE").write_text("x", encoding="utf-8")
            with self.assertRaisesRegex(TASK039E3RecoveryAuthorizationError, "empty"):
                validate_recovery_private_roots_v1(
                    repository_root=repository,
                    e1_private_value=str(e1),
                    historical_e3_private_value=str(historical),
                    recovery_e3_private_value=str(recovery),
                )

    def test_symlink_or_junction_component_is_rejected_before_credential(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            calls: list[str] = []
            arguments = self._guard_arguments(Path(temporary), calls=calls)
            recovery = Path(str(arguments["recovery_e3_private_value"])).resolve()
            original = authorization_module._contains_symlink_component

            with patch.object(
                authorization_module,
                "_contains_symlink_component",
                side_effect=lambda path: path == recovery or original(path),
            ):
                with self.assertRaisesRegex(TASK039E3RecoveryAuthorizationError, "symlink"):
                    run_ordered_precontact_guards_v1(**arguments)  # type: ignore[arg-type]
            self.assertNotIn("load:preflight", calls)
            self.assertNotIn("load:credential", calls)

    def test_committed_prior_authorities_and_source_manifest_reproduce(self) -> None:
        prior = load_prior_authority_state_v1(self.repository)
        self.assertEqual(prior, _prior_state())

        manifest_path = (
            self.repository
            / "docs"
            / "task_reports"
            / "TASK-039E3_R1B_SOURCE_FREEZE.json"
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        supplied = manifest.pop("artifact_hash")
        self.assertEqual(supplied, R1B_SOURCE_MANIFEST_HASH)
        self.assertEqual(stable_hash_v1(manifest), supplied)
        self.assertEqual(manifest["described_commit"], R1B_COMMIT_A)

        for record in manifest["source_records"]:
            relative = record["repository_path"]
            blob = subprocess.run(
                ["git", "rev-parse", f"{R1B_COMMIT_A}:{relative}"],
                cwd=self.repository,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            ).stdout.strip()
            content = subprocess.run(
                ["git", "show", f"{R1B_COMMIT_A}:{relative}"],
                cwd=self.repository,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).stdout
            self.assertEqual(blob, record["git_blob_sha"])
            self.assertEqual(sha256(content).hexdigest(), record["sha256"])

    def test_commit_b_is_reports_only_and_source_blobs_still_match_manifest(self) -> None:
        changed = subprocess.run(
            ["git", "diff", "--name-only", f"{R1B_COMMIT_A}..{R1B_COMMIT_B}"],
            cwd=self.repository,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.splitlines()
        self.assertTrue(changed)
        self.assertTrue(all(path.startswith("docs/task_reports/") for path in changed))

        manifest = json.loads(
            (
                self.repository
                / "docs"
                / "task_reports"
                / "TASK-039E3_R1B_SOURCE_FREEZE.json"
            ).read_text(encoding="utf-8")
        )
        # The audit suite itself runs from a later audit-only commit, so inspect
        # Commit B through raw Git objects instead of conflating current HEAD
        # with the implementation commit under audit.
        for record in manifest["source_records"]:
            relative = record["repository_path"]
            commit_b_blob = subprocess.run(
                ["git", "rev-parse", f"{R1B_COMMIT_B}:{relative}"],
                cwd=self.repository,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            ).stdout.strip()
            commit_b_bytes = subprocess.run(
                ["git", "show", f"{R1B_COMMIT_B}:{relative}"],
                cwd=self.repository,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).stdout
            self.assertEqual(commit_b_blob, record["git_blob_sha"])
            self.assertEqual(sha256(commit_b_bytes).hexdigest(), record["sha256"])

    def test_runner_cannot_reach_credential_or_provider_when_guards_reject(self) -> None:
        runner_path = self.repository / "scripts" / "run_task039e3_recovery_execution.py"
        specification = importlib.util.spec_from_file_location(
            "task039e3_r1b_audit_runner", runner_path
        )
        assert specification is not None and specification.loader is not None
        runner = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(runner)

        reached: list[str] = []
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            authorization_path = root / "SYNTHETIC_AUTHORIZATION.json"
            manifest_path = root / "SYNTHETIC_MANIFEST.json"
            authorization_path.write_text("{}", encoding="utf-8")
            manifest_path.write_text("{}", encoding="utf-8")
            args = Namespace(
                repository_root=str(self.repository),
                r2_authorization=str(authorization_path),
                r1b_source_manifest=str(manifest_path),
                e1_private_root="SYNTHETIC_E1",
                historical_e3_private_root="SYNTHETIC_HISTORY",
                recovery_e3_private_root="SYNTHETIC_RECOVERY",
            )

            def reject_guards(**kwargs: object) -> object:
                reached.append("guards")
                # The credential is passed as a callback, not evaluated early.
                self.assertTrue(callable(kwargs["credential_loader"]))
                raise TASK039E3RecoveryAuthorizationError("synthetic guard rejection")

            with (
                patch.object(runner.argparse.ArgumentParser, "parse_args", return_value=args),
                patch.object(runner, "_load_object", return_value={}),
                patch.object(runner, "run_ordered_precontact_guards_v1", side_effect=reject_guards),
                patch.object(
                    runner,
                    "_credential_loader",
                    side_effect=lambda: reached.append("credential"),
                ),
                patch.object(
                    runner,
                    "LiveOpenAIChatCompletionsTransportV1",
                    side_effect=lambda **_kwargs: reached.append("provider"),
                ),
            ):
                with self.assertRaises(TASK039E3RecoveryAuthorizationError):
                    runner.main()
        self.assertEqual(reached, ["guards"])


if __name__ == "__main__":
    unittest.main()
