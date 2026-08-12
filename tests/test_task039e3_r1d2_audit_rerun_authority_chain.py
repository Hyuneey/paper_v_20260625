"""Independent SF1-rerun oracle for the final-audit to R2 authority chain."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import subprocess
import unittest

from paperworks.v6 import task039e3_recovery_authorization_v3 as authority
from paperworks.v6.common import stable_hash_v1


ROOT = Path(__file__).resolve().parents[1]
R1D2_A = "2653f2b7349a049f9ca4828d736dfea9462c4748"
R1D2_B = "3da8b7007b7dd78d934554b299e6cb264a0e6470"
COMPLETE_MANIFEST_HASH = (
    "e8f236a8238bad744eced3009e2000bab9597094cab04446d920df0a0ddf9283"
)
SF1_A = "86e7b38c36286a140f2549cff388b6700ab5d363"
SF1_B = "5296cf7a054d4fc3bbfdf742b70585bc0dc90515"
SF1_RECEIPT_HASH = (
    "02cb86d536ba48c7bb7931ad37489dc68cfd89a5af84278920b58dc58a9048f1"
)
HISTORICAL_BLOCKED_AUDIT_B = "460cc11a038ba2fd5604a4b2b0b57616b70c97cc"
HISTORICAL_BLOCKED_RECEIPT_HASH = (
    "523368de774b289823206ddf976a8a9e164c3c397427f68c19fb7b952a3db8db"
)
SYNTHETIC_AUDIT_A = "a" * 40
SYNTHETIC_AUDIT_B = "b" * 40
SYNTHETIC_AUDIT_BUNDLE = "c" * 64


def _receipt(**changes: object) -> dict[str, object]:
    content: dict[str, object] = {
        "schema_version": "1.0.0",
        "artifact_type": "task039e3_r1d2_audit_receipt_v1",
        "task_id": "TASK-039E3-R1D2-AUDIT",
        "status": "passed_task039e3_r1d2_independent_audit",
        "audit_run_identity": "R1D2_AUDIT_RERUN_AFTER_SF1",
        "audit_commit_a": SYNTHETIC_AUDIT_A,
        "r1d2_commit_a": R1D2_A,
        "r1d2_commit_b": R1D2_B,
        "r1d2_source_manifest_hash": COMPLETE_MANIFEST_HASH,
        "audit_bundle_hash": SYNTHETIC_AUDIT_BUNDLE,
        "blocking_finding_count": 0,
        "sf1_commit_a": SF1_A,
        "sf1_commit_b": SF1_B,
        "sf1_complete_source_manifest_hash": COMPLETE_MANIFEST_HASH,
        "sf1_receipt_hash": SF1_RECEIPT_HASH,
        "historical_blocked_audit_commit_b": HISTORICAL_BLOCKED_AUDIT_B,
        "historical_blocked_audit_receipt_hash": HISTORICAL_BLOCKED_RECEIPT_HASH,
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


def _authorization(
    *,
    audit_commit_b: str = SYNTHETIC_AUDIT_B,
    audit_bundle: str = SYNTHETIC_AUDIT_BUNDLE,
    receipt_hash: str | None = None,
    **changes: object,
) -> dict[str, object]:
    receipt_hash = receipt_hash or str(_receipt()["artifact_hash"])
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
        "r1d2_source_manifest_hash": COMPLETE_MANIFEST_HASH,
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
        historical_blocked_r1d_implementation_receipt_hash=authority.HISTORICAL_BLOCKED_R1D_IMPLEMENTATION_RECEIPT_HASH,
        historical_blocked_r1d_data_access_audit_hash=authority.HISTORICAL_BLOCKED_R1D_DATA_ACCESS_AUDIT_HASH,
    )


class R1D2AuditRerunAuthorityChainTests(unittest.TestCase):
    def test_receipt_shape_is_canonical_self_hashed_and_non_circular(self) -> None:
        receipt = _receipt()
        self.assertEqual(receipt["artifact_type"], authority.FINAL_AUDIT_ARTIFACT_TYPE)
        self.assertEqual(receipt["task_id"], authority.FINAL_AUDIT_TASK_ID)
        self.assertEqual(receipt["status"], authority.FINAL_AUDIT_PASS_STATUS)
        self.assertEqual(receipt["r1d2_source_manifest_hash"], COMPLETE_MANIFEST_HASH)
        self.assertNotIn("audit_commit_b", receipt)
        self.assertNotIn("r1d2_audit_commit_b", receipt)
        self.assertEqual(
            receipt["artifact_hash"],
            stable_hash_v1({key: value for key, value in receipt.items() if key != "artifact_hash"}),
        )

    def test_historical_blocked_receipt_remains_exact_git_object(self) -> None:
        completed = subprocess.run(
            [
                "git",
                "show",
                f"{HISTORICAL_BLOCKED_AUDIT_B}:{authority.FINAL_AUDIT_RECEIPT_PATH}",
            ],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        historical = json.loads(completed.stdout.decode("utf-8"))
        self.assertEqual(
            historical["status"], "blocked_task039e3_r1d2_independent_audit"
        )
        self.assertEqual(historical["artifact_hash"], HISTORICAL_BLOCKED_RECEIPT_HASH)
        self.assertEqual(
            stable_hash_v1(
                {key: value for key, value in historical.items() if key != "artifact_hash"}
            ),
            HISTORICAL_BLOCKED_RECEIPT_HASH,
        )

    def test_future_authority_binds_complete_manifest_and_exact_git_receipt(self) -> None:
        receipt = _receipt()
        validated = authority.validate_r2_authorization_v3(_authorization())
        calls: list[tuple[str, str]] = []

        def git_loader(commit: str, path: str) -> bytes:
            calls.append((commit, path))
            return json.dumps(receipt, sort_keys=True).encode("utf-8")

        provenance = authority.validate_final_audit_provenance_v3(
            authorization=validated,
            external_audit_receipt=receipt,
            git_receipt_blob_loader=git_loader,
        )
        self.assertEqual(validated.r1d2_source_manifest_hash, COMPLETE_MANIFEST_HASH)
        self.assertEqual(provenance.audit_commit_b, SYNTHETIC_AUDIT_B)
        self.assertEqual(provenance.receipt_hash, receipt["artifact_hash"])
        self.assertEqual(
            calls,
            [(SYNTHETIC_AUDIT_B, authority.FINAL_AUDIT_RECEIPT_PATH)],
        )

        for bad_receipt in (
            _receipt(status="blocked_task039e3_r1d2_independent_audit"),
            _receipt(r1d2_source_manifest_hash="0" * 64),
            _receipt(audit_bundle_hash="0" * 64),
        ):
            with self.subTest(field=bad_receipt):
                bad_auth = authority.validate_r2_authorization_v3(
                    _authorization(receipt_hash=str(bad_receipt["artifact_hash"]))
                )
                with self.assertRaises(authority.TASK039E3RecoveryAuthorizationV3Error):
                    authority.validate_final_audit_provenance_v3(
                        authorization=bad_auth,
                        external_audit_receipt=bad_receipt,
                        git_receipt_blob_loader=lambda _commit, _path, value=bad_receipt: json.dumps(
                            value, sort_keys=True
                        ).encode("utf-8"),
                    )

    def test_all_guard_failures_precede_sentinel_credential_boundary(self) -> None:
        receipt = _receipt()
        credential_calls: list[str] = []
        events: list[str] = []

        def credential_loader() -> str:
            credential_calls.append("credential")
            return "SYNTHETIC_SENTINEL"

        valid: dict[str, object] = {
            "authorization_document": _authorization(),
            "prior_authority_state_loader": _prior,
            "git_state_loader": lambda: authority.GitExecutionStateV3(
                R1D2_A, True, True, COMPLETE_MANIFEST_HASH, True
            ),
            "external_audit_receipt": receipt,
            "git_receipt_blob_loader": lambda _commit, _path: json.dumps(
                receipt, sort_keys=True
            ).encode("utf-8"),
            "historical_capability_receipt_hash": authority.HISTORICAL_CAPABILITY_RECEIPT_HASH,
            "historical_provider_ledger_head_hash": authority.HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
            "root_guard_loader": lambda: {"synthetic_roots": "valid"},
            "scientific_preflight_loader": lambda: {"synthetic_preflight": "valid"},
            "credential_loader": credential_loader,
        }
        failing_cases: list[tuple[str, dict[str, object]]] = [
            ("authorization", {"authorization_document": {}}),
            (
                "prior_authority",
                {
                    "prior_authority_state_loader": lambda: replace(
                        _prior(), r0_commit="0" * 40
                    )
                },
            ),
            (
                "execution_commit",
                {
                    "git_state_loader": lambda: authority.GitExecutionStateV3(
                        "0" * 40, True, True, COMPLETE_MANIFEST_HASH, True
                    )
                },
            ),
            (
                "complete_manifest",
                {
                    "git_state_loader": lambda: authority.GitExecutionStateV3(
                        R1D2_A, True, True, "0" * 64, True
                    )
                },
            ),
            (
                "source_blobs",
                {
                    "git_state_loader": lambda: authority.GitExecutionStateV3(
                        R1D2_A, True, True, COMPLETE_MANIFEST_HASH, False
                    )
                },
            ),
            (
                "audit_pass",
                {
                    "external_audit_receipt": _receipt(
                        status="blocked_task039e3_r1d2_independent_audit"
                    )
                },
            ),
            (
                "audit_git_receipt",
                {"git_receipt_blob_loader": lambda _commit, _path: b"not-json"},
            ),
            (
                "historical_custody",
                {"historical_capability_receipt_hash": "0" * 64},
            ),
            (
                "roots",
                {"root_guard_loader": lambda: (_ for _ in ()).throw(ValueError("roots"))},
            ),
            (
                "scientific_preflight",
                {
                    "scientific_preflight_loader": lambda: (_ for _ in ()).throw(
                        ValueError("preflight")
                    )
                },
            ),
        ]
        for name, changes in failing_cases:
            with self.subTest(guard=name):
                credential_calls.clear()
                arguments = dict(valid)
                arguments.update(changes)
                with self.assertRaises(Exception):
                    authority.run_ordered_precontact_guards_v3(**arguments)
                self.assertEqual(credential_calls, [])

        credential_calls.clear()
        result = authority.run_ordered_precontact_guards_v3(
            **valid, event_sink=events.append
        )
        self.assertEqual(result.credential, "SYNTHETIC_SENTINEL")
        self.assertEqual(credential_calls, ["credential"])
        self.assertEqual(
            events,
            [
                "r2_authorization_v3_validated",
                "prior_authority_bindings_validated",
                "r1d2_commit_a_and_source_manifest_validated",
                "r1d2_audit_pass_and_git_provenance_validated",
                "historical_custody_bindings_validated",
                "private_and_public_roots_validated",
                "scientific_public_preflight_validated",
                "credential_loaded",
            ],
        )


if __name__ == "__main__":
    unittest.main()
