from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from paperworks.v6.common import stable_hash_v1
from paperworks.v6 import task039e3_recovery_authorization_v3 as authority


_R1D2_COMMIT_A = "4" * 40
_R1D2_COMMIT_B = "5" * 40
_R1D2_MANIFEST = "6" * 64
_AUDIT_COMMIT_B = "7" * 40
_AUDIT_BUNDLE = "8" * 64


def _audit_receipt(**changes: object) -> dict[str, object]:
    content: dict[str, object] = {
        "schema_version": "1.0.0",
        "artifact_type": authority.FINAL_AUDIT_ARTIFACT_TYPE,
        "task_id": authority.FINAL_AUDIT_TASK_ID,
        "status": authority.FINAL_AUDIT_PASS_STATUS,
        "r1d2_commit_a": _R1D2_COMMIT_A,
        "r1d2_commit_b": _R1D2_COMMIT_B,
        "r1d2_source_manifest_hash": _R1D2_MANIFEST,
        "audit_bundle_hash": _AUDIT_BUNDLE,
        "provider_contacted": False,
    }
    content.update(changes)
    return {**content, "artifact_hash": stable_hash_v1(content)}


_AUDIT_RECEIPT = _audit_receipt()
_AUDIT_RECEIPT_HASH = str(_AUDIT_RECEIPT["artifact_hash"])


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
        "r1c_commit_a": authority.R1C_COMMIT_A,
        "r1c_commit_b": authority.R1C_COMMIT_B,
        "r1c_source_manifest_hash": authority.R1C_SOURCE_MANIFEST_HASH,
        "r1c_implementation_receipt_hash": (
            authority.R1C_IMPLEMENTATION_RECEIPT_HASH
        ),
        "r1c_remediation_bundle_hash": authority.R1C_REMEDIATION_BUNDLE_HASH,
        "r1c_audit_commit_b": authority.R1C_AUDIT_COMMIT_B,
        "r1c_independent_audit_bundle_hash": (
            authority.R1C_INDEPENDENT_AUDIT_BUNDLE_HASH
        ),
        "r1c_audit_receipt_hash": authority.R1C_AUDIT_RECEIPT_HASH,
        "corrected_custody_accounting_hash": (
            authority.CORRECTED_CUSTODY_ACCOUNTING_HASH
        ),
        "historical_blocked_r1d_commit": authority.HISTORICAL_BLOCKED_R1D_COMMIT,
        "historical_blocked_r1d_preflight_hash": (
            authority.HISTORICAL_BLOCKED_R1D_PREFLIGHT_HASH
        ),
        "historical_blocked_r1d_implementation_receipt_hash": (
            authority.HISTORICAL_BLOCKED_R1D_IMPLEMENTATION_RECEIPT_HASH
        ),
        "historical_blocked_r1d_data_access_audit_hash": (
            authority.HISTORICAL_BLOCKED_R1D_DATA_ACCESS_AUDIT_HASH
        ),
        "r1d2_commit_a": _R1D2_COMMIT_A,
        "r1d2_commit_b": _R1D2_COMMIT_B,
        "r1d2_source_manifest_hash": _R1D2_MANIFEST,
        "r1d2_audit_commit_b": _AUDIT_COMMIT_B,
        "r1d2_independent_audit_bundle_hash": _AUDIT_BUNDLE,
        "r1d2_audit_receipt_hash": _AUDIT_RECEIPT_HASH,
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


def _prior() -> authority.PriorAuthorityStateV3:
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
        r1c_independent_audit_bundle_hash=(
            authority.R1C_INDEPENDENT_AUDIT_BUNDLE_HASH
        ),
        r1c_audit_receipt_hash=authority.R1C_AUDIT_RECEIPT_HASH,
        corrected_custody_accounting_hash=(
            authority.CORRECTED_CUSTODY_ACCOUNTING_HASH
        ),
        historical_blocked_r1d_commit=authority.HISTORICAL_BLOCKED_R1D_COMMIT,
        historical_blocked_r1d_preflight_hash=(
            authority.HISTORICAL_BLOCKED_R1D_PREFLIGHT_HASH
        ),
        historical_blocked_r1d_implementation_receipt_hash=(
            authority.HISTORICAL_BLOCKED_R1D_IMPLEMENTATION_RECEIPT_HASH
        ),
        historical_blocked_r1d_data_access_audit_hash=(
            authority.HISTORICAL_BLOCKED_R1D_DATA_ACCESS_AUDIT_HASH
        ),
    )


def _git_blob(receipt: dict[str, object] | None = None) -> bytes:
    return json.dumps(receipt or _AUDIT_RECEIPT, sort_keys=True).encode("utf-8")


class RecoveryAuthorizationV3Tests(unittest.TestCase):
    def test_closed_authorization_requires_final_audit_bindings(self) -> None:
        validated = authority.validate_r2_authorization_v3(_authorization())
        self.assertEqual(validated.r1d2_commit_a, _R1D2_COMMIT_A)
        self.assertEqual(validated.r1d2_commit_b, _R1D2_COMMIT_B)
        self.assertEqual(validated.r1d2_audit_commit_b, _AUDIT_COMMIT_B)
        self.assertEqual(validated.r1d2_audit_receipt_hash, _AUDIT_RECEIPT_HASH)

        for missing in (
            "r1d2_commit_a",
            "r1d2_commit_b",
            "r1d2_source_manifest_hash",
            "r1d2_audit_commit_b",
            "r1d2_independent_audit_bundle_hash",
            "r1d2_audit_receipt_hash",
        ):
            with self.subTest(missing=missing):
                document = _authorization()
                del document[missing]
                with self.assertRaisesRegex(
                    authority.TASK039E3RecoveryAuthorizationV3Error,
                    "closed contract",
                ):
                    authority.validate_r2_authorization_v3(document)

        extra = _authorization()
        extra["legacy_r1d_alias"] = True
        with self.assertRaisesRegex(
            authority.TASK039E3RecoveryAuthorizationV3Error, "closed contract"
        ):
            authority.validate_r2_authorization_v3(extra)

    def test_corrected_custody_hash_is_authoritative_and_revoked_hash_fails(self) -> None:
        self.assertTrue(authority.CORRECTED_CUSTODY_ACCOUNTING_HASH.endswith("5fbeb616"))
        authority.validate_r2_authorization_v3(_authorization())
        revoked = "ac5dd3d8b060ef353b18a124ea9344ab679cbd6ac82bbcfb5d9f94ce3d6ae967"
        with self.assertRaisesRegex(
            authority.TASK039E3RecoveryAuthorizationV3Error,
            "corrected_custody_accounting_hash differs",
        ):
            authority.validate_r2_authorization_v3(
                _authorization(corrected_custody_accounting_hash=revoked)
            )

    def test_authority_bindings_and_execution_authority_fail_closed(self) -> None:
        cases = (
            ("r0_bundle_hash", "0" * 64),
            ("r1a_timeout_authority_hash", "0" * 64),
            ("r1c_audit_commit_b", "0" * 40),
            ("r1c_independent_audit_bundle_hash", "0" * 64),
            ("historical_blocked_r1d_commit", "0" * 40),
            ("historical_capability_receipt_hash", "0" * 64),
            ("exact_model", "model-alias"),
            ("urlopen_timeout_seconds", 31.0),
            ("provider_contact_authorized", False),
            ("recovery_probe_authorized", False),
            ("scientific_execution_after_capability_pass_authorized", False),
            ("rule_v2_authorized", True),
            ("runtime_authority", True),
            ("utility_evaluation_authorized", True),
            ("winner_selected", True),
        )
        for field, value in cases:
            with self.subTest(field=field):
                with self.assertRaises(authority.TASK039E3RecoveryAuthorizationV3Error):
                    authority.validate_r2_authorization_v3(
                        _authorization(**{field: value})
                    )

    def test_external_pass_receipt_must_equal_authorized_git_object(self) -> None:
        validated = authority.validate_r2_authorization_v3(_authorization())
        calls: list[tuple[str, str]] = []

        def loader(commit: str, path: str) -> bytes:
            calls.append((commit, path))
            return _git_blob()

        result = authority.validate_final_audit_provenance_v3(
            authorization=validated,
            external_audit_receipt=_AUDIT_RECEIPT,
            git_receipt_blob_loader=loader,
        )
        self.assertEqual(result.receipt_hash, _AUDIT_RECEIPT_HASH)
        self.assertEqual(
            calls, [(_AUDIT_COMMIT_B, authority.FINAL_AUDIT_RECEIPT_PATH)]
        )

        failure = _audit_receipt(status="blocked_task039e3_r1d2_independent_audit")
        wrong_self_hash = dict(_AUDIT_RECEIPT)
        wrong_self_hash["artifact_hash"] = "0" * 64
        wrong_commit = _audit_receipt(r1d2_commit_a="9" * 40)
        wrong_commit_b = _audit_receipt(r1d2_commit_b="9" * 40)
        wrong_manifest = _audit_receipt(r1d2_source_manifest_hash="9" * 64)
        wrong_bundle = _audit_receipt(audit_bundle_hash="9" * 64)
        for receipt in (
            failure,
            wrong_self_hash,
            wrong_commit,
            wrong_commit_b,
            wrong_manifest,
            wrong_bundle,
        ):
            with self.subTest(receipt=receipt.get("status")):
                with self.assertRaises(authority.TASK039E3RecoveryAuthorizationV3Error):
                    authority.validate_final_audit_provenance_v3(
                        authorization=validated,
                        external_audit_receipt=receipt,
                        git_receipt_blob_loader=loader,
                    )

        different_git = _audit_receipt(provider_contacted=True)
        with self.assertRaisesRegex(
            authority.TASK039E3RecoveryAuthorizationV3Error,
            "receipt hash differs from R2 authorization",
        ):
            authority.validate_final_audit_provenance_v3(
                authorization=validated,
                external_audit_receipt=_AUDIT_RECEIPT,
                git_receipt_blob_loader=lambda _commit, _path: _git_blob(different_git),
            )

    def test_concrete_git_loader_reads_fixed_commit_path_without_shell(self) -> None:
        completed = __import__("subprocess").CompletedProcess(
            args=[], returncode=0, stdout=_git_blob(), stderr=b""
        )
        repository = Path(__file__).resolve().parents[1]
        with patch.object(authority.subprocess, "run", return_value=completed) as run:
            observed = authority.load_audit_receipt_git_blob_v3(
                repository, _AUDIT_COMMIT_B
            )
        self.assertEqual(observed, _git_blob())
        arguments = run.call_args.args[0]
        self.assertEqual(arguments[-2:], ["blob", f"{_AUDIT_COMMIT_B}:{authority.FINAL_AUDIT_RECEIPT_PATH}"])
        self.assertIs(run.call_args.kwargs["shell"], False)
        self.assertEqual(run.call_args.kwargs["stderr"], authority.subprocess.DEVNULL)
        with self.assertRaisesRegex(
            authority.TASK039E3RecoveryAuthorizationV3Error, "path differs"
        ):
            authority.load_audit_receipt_git_blob_v3(
                repository, _AUDIT_COMMIT_B, "untrusted.json"
            )

    def test_credential_unreachable_until_final_audit_and_all_guards_pass(self) -> None:
        credential_calls: list[str] = []
        root_calls: list[str] = []

        def credential_loader() -> str:
            credential_calls.append("credential")
            return "synthetic-only"

        def root_loader() -> dict[str, bool]:
            root_calls.append("roots")
            return {"synthetic_roots": True}

        common = {
            "authorization_document": _authorization(),
            "prior_authority_state_loader": _prior,
            "git_state_loader": lambda: authority.GitExecutionStateV3(
                _R1D2_COMMIT_A, True, True, _R1D2_MANIFEST, True
            ),
            "external_audit_receipt": _AUDIT_RECEIPT,
            "git_receipt_blob_loader": lambda _commit, _path: _git_blob(),
            "historical_capability_receipt_hash": (
                authority.HISTORICAL_CAPABILITY_RECEIPT_HASH
            ),
            "historical_provider_ledger_head_hash": (
                authority.HISTORICAL_PROVIDER_LEDGER_HEAD_HASH
            ),
            "root_guard_loader": root_loader,
            "scientific_preflight_loader": lambda: {"ready": True},
            "credential_loader": credential_loader,
        }
        failure_cases = (
            {"authorization_document": {}},
            {
                "prior_authority_state_loader": lambda: replace(
                    _prior(), r1c_audit_receipt_hash="0" * 64
                )
            },
            {
                "git_state_loader": lambda: authority.GitExecutionStateV3(
                    "0" * 40, True, True, _R1D2_MANIFEST, True
                )
            },
            {
                "git_state_loader": lambda: authority.GitExecutionStateV3(
                    _R1D2_COMMIT_A, False, True, _R1D2_MANIFEST, True
                )
            },
            {
                "git_state_loader": lambda: authority.GitExecutionStateV3(
                    _R1D2_COMMIT_A, True, False, _R1D2_MANIFEST, True
                )
            },
            {
                "git_state_loader": lambda: authority.GitExecutionStateV3(
                    _R1D2_COMMIT_A, True, True, "0" * 64, True
                )
            },
            {
                "external_audit_receipt": _audit_receipt(
                    status="blocked_task039e3_r1d2_independent_audit"
                )
            },
            {"git_receipt_blob_loader": lambda _commit, _path: b"not-json"},
            {"historical_capability_receipt_hash": "0" * 64},
            {
                "root_guard_loader": lambda: (_ for _ in ()).throw(
                    authority.TASK039E3RecoveryAuthorizationV3Error("roots")
                )
            },
            {
                "scientific_preflight_loader": lambda: (_ for _ in ()).throw(
                    authority.TASK039E3RecoveryAuthorizationV3Error("preflight")
                )
            },
        )
        for changes in failure_cases:
            with self.subTest(fields=tuple(changes)):
                credential_calls.clear()
                arguments = dict(common)
                arguments.update(changes)
                with self.assertRaises(authority.TASK039E3RecoveryAuthorizationV3Error):
                    authority.run_ordered_precontact_guards_v3(**arguments)
                self.assertEqual(credential_calls, [])

        events: list[str] = []
        result = authority.run_ordered_precontact_guards_v3(
            **common, event_sink=events.append
        )
        self.assertEqual(credential_calls, ["credential"])
        self.assertEqual(events[-2:], ["scientific_public_preflight_validated", "credential_loaded"])
        self.assertLess(
            events.index("r1d2_audit_pass_and_git_provenance_validated"),
            events.index("credential_loaded"),
        )
        self.assertEqual(result.completed_guard_order, tuple(events))

    def test_schema_is_closed_and_matches_validator_contract(self) -> None:
        schema_path = (
            Path(__file__).parents[1]
            / "schemas/v6/task039e3_recovery_execution_authorization_v3_schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(set(schema["properties"]), set(schema["required"]))
        self.assertEqual(set(schema["required"]), set(_authorization()))
        self.assertEqual(
            schema["properties"]["corrected_custody_accounting_hash"]["const"],
            authority.CORRECTED_CUSTODY_ACCOUNTING_HASH,
        )
        for field in (
            "r1d2_commit_a",
            "r1d2_commit_b",
            "r1d2_source_manifest_hash",
            "r1d2_audit_commit_b",
            "r1d2_independent_audit_bundle_hash",
            "r1d2_audit_receipt_hash",
        ):
            self.assertIn(field, schema["required"])

    def test_module_has_no_environment_network_or_legacy_bridge_access(self) -> None:
        source = Path(authority.__file__).read_text(encoding="utf-8")
        credential_name = "OPENAI" + "_API_KEY"
        bridge_name = "Recovery" + "ScientificCompatibilityTransportV1"
        self.assertNotIn(credential_name, source)
        self.assertNotIn("os.environ", source)
        self.assertNotIn("urllib", source)
        self.assertNotIn(bridge_name, source)
        self.assertNotIn("task039e3_recovery_execution_v1", source)


if __name__ == "__main__":
    unittest.main()
