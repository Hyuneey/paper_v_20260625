from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from paperworks.v6.common import stable_hash_v1
from paperworks.v6 import task039e3_recovery_authorization_v1 as authorization_module
from paperworks.v6.task039e3_recovery_authorization_v1 import (
    ARTIFACT_TYPE,
    AUTHORIZATION_STATUS,
    EXACT_MODEL,
    GitExecutionStateV1,
    HISTORICAL_CAPABILITY_RECEIPT_HASH,
    HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
    PriorAuthorityStateV1,
    R0_BUNDLE_HASH,
    R0_COMMIT,
    R1A_COMMIT,
    R1A_RECEIPT_HASH,
    R1A_TIMEOUT_AUTHORITY_HASH,
    RecoveryProbeAccountingV1,
    TASK039E3RecoveryAuthorizationError,
    TASK_ID,
    URLOPEN_TIMEOUT_SECONDS,
    run_ordered_precontact_guards_v1,
    validate_r2_authorization_v1,
    validate_recovery_private_roots_v1,
)


_COMMIT = "1" * 40
_MANIFEST = "2" * 64


def _authorization(**changes: object) -> dict[str, object]:
    content: dict[str, object] = {
        "schema_version": "1.0.0",
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
        "r1b_commit_a": _COMMIT,
        "r1b_source_manifest_hash": _MANIFEST,
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


class RecoveryAuthorizationTests(unittest.TestCase):
    def test_exact_future_authorization_and_closed_fields(self) -> None:
        validated = validate_r2_authorization_v1(_authorization())
        self.assertEqual(validated.r1b_commit_a, _COMMIT)
        document = _authorization()
        document["unknown"] = True
        with self.assertRaisesRegex(TASK039E3RecoveryAuthorizationError, "fields differ"):
            validate_r2_authorization_v1(document)

    def test_self_hash_and_every_authority_binding_fail_closed(self) -> None:
        bad_hash = _authorization()
        bad_hash["self_hash"] = "0" * 64
        with self.assertRaisesRegex(TASK039E3RecoveryAuthorizationError, "self-hash"):
            validate_r2_authorization_v1(bad_hash)
        for field, bad in (
            ("r0_commit", "0" * 40),
            ("r0_bundle_hash", "0" * 64),
            ("r1a_commit", "0" * 40),
            ("r1a_timeout_authority_hash", "0" * 64),
            ("r1a_receipt_hash", "0" * 64),
            ("historical_capability_receipt_hash", "0" * 64),
            ("historical_provider_ledger_head_hash", "0" * 64),
            ("exact_model", "alias"),
            ("urlopen_timeout_seconds", 31.0),
            ("provider_contact_authorized", False),
            ("recovery_probe_authorized", False),
            ("scientific_execution_after_capability_pass_authorized", False),
            ("rule_v2_authorized", True),
            ("winner_selected", True),
        ):
            with self.subTest(field=field):
                with self.assertRaises(TASK039E3RecoveryAuthorizationError):
                    validate_r2_authorization_v1(_authorization(**{field: bad}))

    def test_probe_accounting_prevents_third_probe_and_ignores_attempt_count(self) -> None:
        historical = RecoveryProbeAccountingV1()
        self.assertEqual(historical.cumulative_probe_count, 1)
        recovery = historical.allocate_recovery_probe()
        self.assertEqual(recovery.cumulative_probe_count, 2)
        self.assertIs(recovery.with_transport_attempts(3), recovery)
        self.assertEqual(recovery.cumulative_probe_count, 2)
        with self.assertRaisesRegex(TASK039E3RecoveryAuthorizationError, "third"):
            recovery.allocate_recovery_probe()

    def test_distinct_external_empty_roots_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            repository = base / "repo"
            e1 = base / "e1"
            historical = base / "historical"
            recovery = base / "recovery"
            for path in (repository, e1, historical, recovery):
                path.mkdir()
            roots = validate_recovery_private_roots_v1(
                repository_root=repository,
                e1_private_value=str(e1),
                historical_e3_private_value=str(historical),
                recovery_e3_private_value=str(recovery),
            )
            self.assertEqual(roots.historical_e3_access_mode, "read_only")
            self.assertEqual(roots.recovery_e3_private_root, recovery.resolve())

    def test_root_guards_reject_containment_traversal_duplicates_and_nonempty(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            repository = base / "repo"
            e1 = base / "e1"
            historical = base / "historical"
            recovery = base / "recovery"
            for path in (repository, e1, historical, recovery):
                path.mkdir()
            repository_private = repository / "private"
            repository_private.mkdir()
            with self.assertRaisesRegex(TASK039E3RecoveryAuthorizationError, "disjoint"):
                validate_recovery_private_roots_v1(
                    repository_root=repository,
                    e1_private_value=str(repository_private),
                    historical_e3_private_value=str(historical),
                    recovery_e3_private_value=str(recovery),
                )
            with self.assertRaisesRegex(TASK039E3RecoveryAuthorizationError, "traversal"):
                validate_recovery_private_roots_v1(
                    repository_root=repository,
                    e1_private_value=str(e1 / ".." / "e1"),
                    historical_e3_private_value=str(historical),
                    recovery_e3_private_value=str(recovery),
                )
            with self.assertRaisesRegex(TASK039E3RecoveryAuthorizationError, "distinct"):
                validate_recovery_private_roots_v1(
                    repository_root=repository,
                    e1_private_value=str(e1),
                    historical_e3_private_value=str(e1),
                    recovery_e3_private_value=str(recovery),
                )
            (recovery / "prior").write_text("occupied", encoding="utf-8")
            with self.assertRaisesRegex(TASK039E3RecoveryAuthorizationError, "empty"):
                validate_recovery_private_roots_v1(
                    repository_root=repository,
                    e1_private_value=str(e1),
                    historical_e3_private_value=str(historical),
                    recovery_e3_private_value=str(recovery),
                )

    def test_symlink_escape_rejected_when_platform_supports_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            repository = base / "repo"
            e1 = base / "e1"
            historical = base / "historical"
            recovery = base / "recovery"
            for path in (repository, e1, historical, recovery):
                path.mkdir()
            link = base / "linked-recovery"
            try:
                link.symlink_to(recovery, target_is_directory=True)
            except OSError:
                with patch.object(
                    authorization_module,
                    "_contains_symlink_component",
                    side_effect=lambda path: path == recovery,
                ):
                    with self.assertRaisesRegex(
                        TASK039E3RecoveryAuthorizationError, "symlink"
                    ):
                        validate_recovery_private_roots_v1(
                            repository_root=repository,
                            e1_private_value=str(e1),
                            historical_e3_private_value=str(historical),
                            recovery_e3_private_value=str(recovery),
                        )
                return
            with self.assertRaisesRegex(TASK039E3RecoveryAuthorizationError, "symlink"):
                validate_recovery_private_roots_v1(
                    repository_root=repository,
                    e1_private_value=str(e1),
                    historical_e3_private_value=str(historical),
                    recovery_e3_private_value=str(link),
                )

    def test_credential_loader_is_last_and_unreachable_on_each_guard_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            repository = base / "repo"
            e1 = base / "e1"
            historical = base / "historical"
            recovery = base / "recovery"
            for path in (repository, e1, historical, recovery):
                path.mkdir()
            calls: list[str] = []

            def credential_loader() -> str:
                calls.append("credential")
                return "synthetic-credential"

            common = dict(
                authorization_document=_authorization(),
                prior_authority_state_loader=lambda: PriorAuthorityStateV1(
                    R0_COMMIT,
                    R0_BUNDLE_HASH,
                    R1A_COMMIT,
                    R1A_TIMEOUT_AUTHORITY_HASH,
                    R1A_RECEIPT_HASH,
                ),
                git_state_loader=lambda: GitExecutionStateV1(_COMMIT, True, True, _MANIFEST, True),
                repository_root=repository,
                e1_private_value=str(e1),
                historical_e3_private_value=str(historical),
                recovery_e3_private_value=str(recovery),
                historical_capability_receipt_hash=HISTORICAL_CAPABILITY_RECEIPT_HASH,
                historical_provider_ledger_head_hash=HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
                scientific_preflight_loader=lambda: {"synthetic": True},
                credential_loader=credential_loader,
            )
            failure_cases = (
                {"authorization_document": {}},
                {"prior_authority_state_loader": lambda: PriorAuthorityStateV1(
                    "0" * 40, R0_BUNDLE_HASH, R1A_COMMIT,
                    R1A_TIMEOUT_AUTHORITY_HASH, R1A_RECEIPT_HASH,
                )},
                {"prior_authority_state_loader": lambda: PriorAuthorityStateV1(
                    R0_COMMIT, R0_BUNDLE_HASH, "0" * 40,
                    R1A_TIMEOUT_AUTHORITY_HASH, R1A_RECEIPT_HASH,
                )},
                {"git_state_loader": lambda: GitExecutionStateV1("0" * 40, True, True, _MANIFEST, True)},
                {"git_state_loader": lambda: GitExecutionStateV1(_COMMIT, False, True, _MANIFEST, True)},
                {"git_state_loader": lambda: GitExecutionStateV1(_COMMIT, True, False, _MANIFEST, True)},
                {"git_state_loader": lambda: GitExecutionStateV1(_COMMIT, True, True, "0" * 64, True)},
                {"git_state_loader": lambda: GitExecutionStateV1(_COMMIT, True, True, _MANIFEST, False)},
                {"historical_capability_receipt_hash": "0" * 64},
                {"historical_provider_ledger_head_hash": "0" * 64},
                {"recovery_e3_private_value": str(repository / "private")},
            )
            for changes in failure_cases:
                with self.subTest(changes=tuple(changes)):
                    calls.clear()
                    arguments = dict(common)
                    arguments.update(changes)
                    with self.assertRaises(TASK039E3RecoveryAuthorizationError):
                        run_ordered_precontact_guards_v1(**arguments)
                    self.assertEqual(calls, [])

            events: list[str] = []
            result = run_ordered_precontact_guards_v1(**common, event_sink=events.append)
            self.assertEqual(calls, ["credential"])
            self.assertEqual(events[-1], "credential_loaded")
            self.assertEqual(result.completed_guard_order, tuple(events))


if __name__ == "__main__":
    unittest.main()
