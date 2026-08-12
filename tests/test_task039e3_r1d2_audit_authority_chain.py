from __future__ import annotations

from dataclasses import replace
import json
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6 import task039e3_recovery_authorization_v3 as authority


_R1D2_COMMIT_A = "2653f2b7349a049f9ca4828d736dfea9462c4748"
_R1D2_COMMIT_B = "3da8b7007b7dd78d934554b299e6cb264a0e6470"
_R1D2_SOURCE_MANIFEST = (
    "d9ea32af4ffb60af8bb6d0b7a496a74e4126d8e411e337da64ce64e15a152e48"
)
_AUDIT_COMMIT_A = "1" * 40
_AUDIT_COMMIT_B = "2" * 40
_AUDIT_BUNDLE = "3" * 64


def _audit_receipt(**changes: object) -> dict[str, object]:
    content: dict[str, object] = {
        "schema_version": "1.0.0",
        "artifact_type": "task039e3_r1d2_audit_receipt_v1",
        "task_id": "TASK-039E3-R1D2-AUDIT",
        "status": "passed_task039e3_r1d2_independent_audit",
        "audit_commit_a": _AUDIT_COMMIT_A,
        "r1d2_commit_a": _R1D2_COMMIT_A,
        "r1d2_commit_b": _R1D2_COMMIT_B,
        "r1d2_source_manifest_hash": _R1D2_SOURCE_MANIFEST,
        "audit_bundle_hash": _AUDIT_BUNDLE,
        "blocking_finding_count": 0,
        "provider_contact_authorized": False,
        "recovery_probe_authorized": False,
        "scientific_execution_authorized": False,
        "rule_v2_authorized": False,
        "runtime_authority": False,
        "utility_evaluation_authorized": False,
        "winner_selected": False,
    }
    content.update(changes)
    return {**content, "artifact_hash": stable_hash_v1(content)}


_RECEIPT = _audit_receipt()
_RECEIPT_HASH = str(_RECEIPT["artifact_hash"])


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
        "r1c_implementation_receipt_hash": authority.R1C_IMPLEMENTATION_RECEIPT_HASH,
        "r1c_remediation_bundle_hash": authority.R1C_REMEDIATION_BUNDLE_HASH,
        "r1c_audit_commit_b": authority.R1C_AUDIT_COMMIT_B,
        "r1c_independent_audit_bundle_hash": authority.R1C_INDEPENDENT_AUDIT_BUNDLE_HASH,
        "r1c_audit_receipt_hash": authority.R1C_AUDIT_RECEIPT_HASH,
        "corrected_custody_accounting_hash": authority.CORRECTED_CUSTODY_ACCOUNTING_HASH,
        "historical_blocked_r1d_commit": authority.HISTORICAL_BLOCKED_R1D_COMMIT,
        "historical_blocked_r1d_preflight_hash": authority.HISTORICAL_BLOCKED_R1D_PREFLIGHT_HASH,
        "historical_blocked_r1d_implementation_receipt_hash": (
            authority.HISTORICAL_BLOCKED_R1D_IMPLEMENTATION_RECEIPT_HASH
        ),
        "historical_blocked_r1d_data_access_audit_hash": (
            authority.HISTORICAL_BLOCKED_R1D_DATA_ACCESS_AUDIT_HASH
        ),
        "r1d2_commit_a": _R1D2_COMMIT_A,
        "r1d2_commit_b": _R1D2_COMMIT_B,
        "r1d2_source_manifest_hash": _R1D2_SOURCE_MANIFEST,
        "r1d2_audit_commit_b": _AUDIT_COMMIT_B,
        "r1d2_independent_audit_bundle_hash": _AUDIT_BUNDLE,
        "r1d2_audit_receipt_hash": _RECEIPT_HASH,
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


def _git_receipt(receipt: dict[str, object] | None = None) -> bytes:
    return json.dumps(receipt or _RECEIPT, sort_keys=True).encode("utf-8")


class R1D2AuditAuthorityChainTests(unittest.TestCase):
    def test_receipt_contract_is_complete_and_non_circular(self) -> None:
        required = {
            "artifact_type",
            "task_id",
            "status",
            "audit_commit_a",
            "r1d2_commit_a",
            "r1d2_commit_b",
            "r1d2_source_manifest_hash",
            "audit_bundle_hash",
            "blocking_finding_count",
            "provider_contact_authorized",
            "recovery_probe_authorized",
            "scientific_execution_authorized",
            "rule_v2_authorized",
            "runtime_authority",
            "utility_evaluation_authorized",
            "artifact_hash",
        }
        self.assertTrue(required.issubset(_RECEIPT))
        self.assertNotIn("audit_commit_b", _RECEIPT)
        self.assertNotIn("r1d2_audit_commit_b", _RECEIPT)
        self.assertEqual(_RECEIPT["blocking_finding_count"], 0)
        self.assertEqual(
            _RECEIPT["artifact_hash"],
            stable_hash_v1(
                {key: value for key, value in _RECEIPT.items() if key != "artifact_hash"}
            ),
        )

    def test_future_authorization_supplies_non_circular_commit_b_binding(self) -> None:
        validated = authority.validate_r2_authorization_v3(_authorization())
        calls: list[tuple[str, str]] = []

        def loader(commit: str, path: str) -> bytes:
            calls.append((commit, path))
            return _git_receipt()

        provenance = authority.validate_final_audit_provenance_v3(
            authorization=validated,
            external_audit_receipt=_RECEIPT,
            git_receipt_blob_loader=loader,
        )
        self.assertEqual(provenance.audit_commit_b, _AUDIT_COMMIT_B)
        self.assertEqual(provenance.receipt_hash, _RECEIPT_HASH)
        self.assertEqual(
            calls,
            [(_AUDIT_COMMIT_B, "docs/task_reports/TASK-039E3_R1D2_AUDIT_RECEIPT.json")],
        )

    def test_external_receipt_must_be_byte_content_equivalent_to_git_object(self) -> None:
        validated = authority.validate_r2_authorization_v3(_authorization())
        altered = _audit_receipt(documentation_note="not in external copy")
        with self.assertRaises(authority.TASK039E3RecoveryAuthorizationV3Error):
            authority.validate_final_audit_provenance_v3(
                authorization=validated,
                external_audit_receipt=_RECEIPT,
                git_receipt_blob_loader=lambda _commit, _path: _git_receipt(altered),
            )

        blocked = _audit_receipt(
            status="blocked_task039e3_r1d2_independent_audit",
            blocking_finding_count=1,
        )
        blocked_authorization = _authorization(
            r1d2_audit_receipt_hash=blocked["artifact_hash"]
        )
        with self.assertRaises(authority.TASK039E3RecoveryAuthorizationV3Error):
            authority.validate_final_audit_provenance_v3(
                authorization=authority.validate_r2_authorization_v3(
                    blocked_authorization
                ),
                external_audit_receipt=blocked,
                git_receipt_blob_loader=lambda _commit, _path: _git_receipt(blocked),
            )

    def test_every_precredential_guard_failure_keeps_sentinel_unreachable(self) -> None:
        credential_calls: list[str] = []

        def credential_loader() -> str:
            credential_calls.append("credential")
            return "synthetic-credential-sentinel"

        valid = {
            "authorization_document": _authorization(),
            "prior_authority_state_loader": _prior,
            "git_state_loader": lambda: authority.GitExecutionStateV3(
                _R1D2_COMMIT_A, True, True, _R1D2_SOURCE_MANIFEST, True
            ),
            "external_audit_receipt": _RECEIPT,
            "git_receipt_blob_loader": lambda _commit, _path: _git_receipt(),
            "historical_capability_receipt_hash": authority.HISTORICAL_CAPABILITY_RECEIPT_HASH,
            "historical_provider_ledger_head_hash": authority.HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
            "root_guard_loader": lambda: {"all_synthetic_roots_valid": True},
            "scientific_preflight_loader": lambda: {"public_preflight": "PASS"},
            "credential_loader": credential_loader,
        }
        bad_git_states = {
            "commit_a": authority.GitExecutionStateV3(
                "0" * 40, True, True, _R1D2_SOURCE_MANIFEST, True
            ),
            "worktree": authority.GitExecutionStateV3(
                _R1D2_COMMIT_A, False, True, _R1D2_SOURCE_MANIFEST, True
            ),
            "index": authority.GitExecutionStateV3(
                _R1D2_COMMIT_A, True, False, _R1D2_SOURCE_MANIFEST, True
            ),
            "manifest": authority.GitExecutionStateV3(
                _R1D2_COMMIT_A, True, True, "0" * 64, True
            ),
            "source_blobs": authority.GitExecutionStateV3(
                _R1D2_COMMIT_A, True, True, _R1D2_SOURCE_MANIFEST, False
            ),
        }
        cases: list[tuple[str, dict[str, object]]] = [
            ("r2_authorization", {"authorization_document": {}}),
            (
                "prior_authority",
                {
                    "prior_authority_state_loader": lambda: replace(
                        _prior(), corrected_custody_accounting_hash="0" * 64
                    )
                },
            ),
            *[
                (name, {"git_state_loader": (lambda state=state: state)})
                for name, state in bad_git_states.items()
            ],
            (
                "final_audit_receipt",
                {
                    "external_audit_receipt": _audit_receipt(
                        status="blocked_task039e3_r1d2_independent_audit"
                    )
                },
            ),
            (
                "audit_git_object",
                {"git_receipt_blob_loader": lambda _commit, _path: b"not-json"},
            ),
            (
                "audit_git_equivalence",
                {
                    "git_receipt_blob_loader": lambda _commit, _path: _git_receipt(
                        _audit_receipt(extra="different")
                    )
                },
            ),
            (
                "historical_capability_custody",
                {"historical_capability_receipt_hash": "0" * 64},
            ),
            (
                "historical_provider_custody",
                {"historical_provider_ledger_head_hash": "0" * 64},
            ),
            (
                "private_public_roots",
                {
                    "root_guard_loader": lambda: (_ for _ in ()).throw(
                        authority.TASK039E3RecoveryAuthorizationV3Error("roots")
                    )
                },
            ),
            (
                "scientific_public_preflight",
                {
                    "scientific_preflight_loader": lambda: (_ for _ in ()).throw(
                        authority.TASK039E3RecoveryAuthorizationV3Error("preflight")
                    )
                },
            ),
        ]

        for name, changes in cases:
            with self.subTest(guard=name):
                credential_calls.clear()
                arguments = dict(valid)
                arguments.update(changes)
                with self.assertRaises(Exception):
                    authority.run_ordered_precontact_guards_v3(**arguments)
                self.assertEqual(credential_calls, [])

        events: list[str] = []
        authority.run_ordered_precontact_guards_v3(**valid, event_sink=events.append)
        self.assertEqual(credential_calls, ["credential"])
        self.assertEqual(events[-1], "credential_loaded")
        self.assertLess(
            events.index("r1d2_audit_pass_and_git_provenance_validated"),
            events.index("credential_loaded"),
        )

    def test_revoked_custody_hash_has_zero_authority(self) -> None:
        revoked = "ac5dd3d8b060ef353b18a124ea9344ab679cbd6ac82bbcfb5d9f94ce3d6ae967"
        self.assertEqual(
            authority.CORRECTED_CUSTODY_ACCOUNTING_HASH,
            "ac5dd3d8b060ef353b18a124ea9344ab679cbd6ac82bbcfb5d9f94ce5fbeb616",
        )
        with self.assertRaises(authority.TASK039E3RecoveryAuthorizationV3Error):
            authority.validate_r2_authorization_v3(
                _authorization(corrected_custody_accounting_hash=revoked)
            )


if __name__ == "__main__":
    unittest.main()
