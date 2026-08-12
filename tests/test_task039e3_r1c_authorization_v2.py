from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6 import task039e3_recovery_authorization_v2 as authority


_R1C_COMMIT = "c" * 40
_R1C_MANIFEST = "d" * 64


def _authorization(**changes: object) -> dict[str, object]:
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
        "r1b_independent_audit_bundle_hash": (
            authority.R1B_INDEPENDENT_AUDIT_BUNDLE_HASH
        ),
        "r1b_audit_receipt_hash": authority.R1B_AUDIT_RECEIPT_HASH,
        "r1c_commit_a": _R1C_COMMIT,
        "r1c_source_manifest_hash": _R1C_MANIFEST,
        "historical_capability_receipt_hash": (
            authority.HISTORICAL_CAPABILITY_RECEIPT_HASH
        ),
        "historical_provider_ledger_head_hash": (
            authority.HISTORICAL_PROVIDER_LEDGER_HEAD_HASH
        ),
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
    content.update(changes)
    return {**content, "self_hash": stable_hash_v1(content)}


def _prior(**changes: str) -> authority.PriorAuthorityStateV2:
    values = {
        "r0_commit": authority.R0_COMMIT,
        "r0_bundle_hash": authority.R0_BUNDLE_HASH,
        "r1a_commit": authority.R1A_COMMIT,
        "r1a_timeout_authority_hash": authority.R1A_TIMEOUT_AUTHORITY_HASH,
        "r1b_commit_a": authority.R1B_COMMIT_A,
        "r1b_commit_b": authority.R1B_COMMIT_B,
        "r1b_audit_commit_b": authority.R1B_AUDIT_COMMIT_B,
        "r1b_independent_audit_bundle_hash": (
            authority.R1B_INDEPENDENT_AUDIT_BUNDLE_HASH
        ),
        "r1b_audit_receipt_hash": authority.R1B_AUDIT_RECEIPT_HASH,
    }
    values.update(changes)
    return authority.PriorAuthorityStateV2(**values)


class RecoveryAuthorizationV2Tests(unittest.TestCase):
    def test_closed_self_hashed_authorization_binds_audit_and_future_r1c(self) -> None:
        validated = authority.validate_r2_authorization_v2(_authorization())
        self.assertEqual(validated.r1c_commit_a, _R1C_COMMIT)
        self.assertEqual(validated.r1c_source_manifest_hash, _R1C_MANIFEST)
        extra = _authorization()
        extra["unexpected"] = True
        with self.assertRaisesRegex(
            authority.TASK039E3RecoveryAuthorizationV2Error, "closed contract"
        ):
            authority.validate_r2_authorization_v2(extra)

    def test_every_frozen_authority_binding_fails_closed(self) -> None:
        cases = (
            ("r0_commit", "0" * 40),
            ("r0_bundle_hash", "0" * 64),
            ("r1a_commit", "0" * 40),
            ("r1a_timeout_authority_hash", "0" * 64),
            ("r1b_commit_a", "0" * 40),
            ("r1b_commit_b", "0" * 40),
            ("r1b_audit_commit_b", "0" * 40),
            ("r1b_independent_audit_bundle_hash", "0" * 64),
            ("r1b_audit_receipt_hash", "0" * 64),
            ("historical_capability_receipt_hash", "0" * 64),
            ("historical_provider_ledger_head_hash", "0" * 64),
            ("exact_model", "model-alias"),
            ("urlopen_timeout_seconds", 60.0),
            ("provider_contact_authorized", False),
            ("recovery_probe_authorized", False),
            ("scientific_execution_after_capability_pass_authorized", False),
            ("rule_v2_authorized", True),
            ("runtime_authority", True),
            ("utility_evaluation_authorized", True),
        )
        for field, value in cases:
            with self.subTest(field=field):
                with self.assertRaises(authority.TASK039E3RecoveryAuthorizationV2Error):
                    authority.validate_r2_authorization_v2(
                        _authorization(**{field: value})
                    )

    def test_self_hash_and_dynamic_r1c_bindings_fail_closed(self) -> None:
        bad = _authorization()
        bad["self_hash"] = "0" * 64
        with self.assertRaisesRegex(
            authority.TASK039E3RecoveryAuthorizationV2Error, "self-hash"
        ):
            authority.validate_r2_authorization_v2(bad)
        for field, value in (
            ("r1c_commit_a", "not-a-commit"),
            ("r1c_source_manifest_hash", "not-a-hash"),
        ):
            with self.subTest(field=field):
                with self.assertRaises(authority.TASK039E3RecoveryAuthorizationV2Error):
                    authority.validate_r2_authorization_v2(
                        _authorization(**{field: value})
                    )

    def test_probe_accounting_preserves_one_additional_probe_limit(self) -> None:
        before = authority.RecoveryProbeAccountingV2()
        self.assertEqual(before.cumulative_probe_count, 1)
        recovery = before.allocate_recovery_probe()
        self.assertEqual(recovery.cumulative_probe_count, 2)
        for attempts in (1, 2, 3):
            self.assertIs(recovery.with_transport_attempts(attempts), recovery)
        with self.assertRaisesRegex(
            authority.TASK039E3RecoveryAuthorizationV2Error, "third"
        ):
            recovery.allocate_recovery_probe()

    def test_schema_is_closed_and_matches_validator_field_set(self) -> None:
        schema_path = (
            Path(__file__).parents[1]
            / "schemas/v6/task039e3_recovery_execution_authorization_v2_schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(set(schema["properties"]), set(schema["required"]))
        self.assertEqual(set(schema["required"]), set(_authorization()))
        self.assertEqual(
            schema["properties"]["r1b_audit_commit_b"]["const"],
            authority.R1B_AUDIT_COMMIT_B,
        )

    def test_root_guards_remain_external_distinct_and_recovery_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            repository = base / "repo"
            e1 = base / "e1"
            historical = base / "historical"
            recovery = base / "recovery"
            for path in (repository, e1, historical, recovery):
                path.mkdir()
            roots = authority.validate_recovery_private_roots_v2(
                repository_root=repository,
                e1_private_value=str(e1),
                historical_e3_private_value=str(historical),
                recovery_e3_private_value=str(recovery),
            )
            self.assertEqual(roots.historical_e3_access_mode, "read_only")
            with self.assertRaises(authority.TASK039E3RecoveryAuthorizationV2Error):
                authority.validate_recovery_private_roots_v2(
                    repository_root=repository,
                    e1_private_value=str(repository),
                    historical_e3_private_value=str(historical),
                    recovery_e3_private_value=str(recovery),
                )

    def test_credential_is_unreachable_until_every_precontact_guard_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            repository = base / "repo"
            e1 = base / "e1"
            historical = base / "historical"
            recovery = base / "recovery"
            for path in (repository, e1, historical, recovery):
                path.mkdir()
            credential_calls: list[str] = []

            def credential_loader() -> str:
                credential_calls.append("credential")
                return "synthetic-only"

            common = {
                "authorization_document": _authorization(),
                "prior_authority_state_loader": _prior,
                "git_state_loader": lambda: authority.GitExecutionStateV2(
                    _R1C_COMMIT, True, True, _R1C_MANIFEST, True
                ),
                "repository_root": repository,
                "e1_private_value": str(e1),
                "historical_e3_private_value": str(historical),
                "recovery_e3_private_value": str(recovery),
                "historical_capability_receipt_hash": (
                    authority.HISTORICAL_CAPABILITY_RECEIPT_HASH
                ),
                "historical_provider_ledger_head_hash": (
                    authority.HISTORICAL_PROVIDER_LEDGER_HEAD_HASH
                ),
                "scientific_preflight_loader": lambda: {"synthetic": True},
                "credential_loader": credential_loader,
            }
            failure_cases = (
                {"authorization_document": {}},
                {
                    "prior_authority_state_loader": lambda: _prior(
                        r1b_audit_commit_b="0" * 40
                    )
                },
                {
                    "git_state_loader": lambda: authority.GitExecutionStateV2(
                        "0" * 40, True, True, _R1C_MANIFEST, True
                    )
                },
                {
                    "git_state_loader": lambda: authority.GitExecutionStateV2(
                        _R1C_COMMIT, False, True, _R1C_MANIFEST, True
                    )
                },
                {
                    "git_state_loader": lambda: authority.GitExecutionStateV2(
                        _R1C_COMMIT, True, False, _R1C_MANIFEST, True
                    )
                },
                {
                    "git_state_loader": lambda: authority.GitExecutionStateV2(
                        _R1C_COMMIT, True, True, "0" * 64, True
                    )
                },
                {
                    "git_state_loader": lambda: authority.GitExecutionStateV2(
                        _R1C_COMMIT, True, True, _R1C_MANIFEST, False
                    )
                },
                {"historical_capability_receipt_hash": "0" * 64},
                {"historical_provider_ledger_head_hash": "0" * 64},
                {"recovery_e3_private_value": str(repository)},
                {
                    "scientific_preflight_loader": lambda: (_ for _ in ()).throw(
                        authority.TASK039E3RecoveryAuthorizationV2Error("preflight")
                    )
                },
            )
            for changes in failure_cases:
                with self.subTest(fields=tuple(changes)):
                    credential_calls.clear()
                    arguments = dict(common)
                    arguments.update(changes)
                    with self.assertRaises(
                        authority.TASK039E3RecoveryAuthorizationV2Error
                    ):
                        authority.run_ordered_precontact_guards_v2(**arguments)
                    self.assertEqual(credential_calls, [])

            events: list[str] = []
            result = authority.run_ordered_precontact_guards_v2(
                **common, event_sink=events.append
            )
            self.assertEqual(credential_calls, ["credential"])
            self.assertEqual(events[-1], "credential_loaded")
            self.assertEqual(result.completed_guard_order, tuple(events))

    def test_module_contains_no_environment_or_compatibility_bridge_access(self) -> None:
        source = Path(authority.__file__).read_text(encoding="utf-8")
        credential_name = "OPENAI" + "_API_KEY"
        bridge_name = "Recovery" + "ScientificCompatibilityTransportV1"
        self.assertNotIn(credential_name, source)
        self.assertNotIn("os.environ", source)
        self.assertNotIn(bridge_name, source)
        self.assertNotIn("task039e3_recovery_execution_v1", source)


if __name__ == "__main__":
    unittest.main()
