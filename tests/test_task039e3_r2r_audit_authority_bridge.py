"""Exact frozen-consumer oracles for the R2R canonical audit bridge."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_authorization_v1 import (
    validate_r2r_authorization_v1,
)
from paperworks.v6.task039e3_r2r_live_execution_v1 import (
    R2RAuthorityContextV1,
    R2RForensicProtocolContextV1,
    R2RGitSourceContextV1,
    TASK039E3R2RLiveExecutionError,
    _validate_forensic_protocol,
)


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_A = "f10365adbdde5bb2070df429770174d215829dc6"
IMPLEMENTATION_B = "067dcffc441170064180c677b0bd7845a93ce5ef"
SOURCE_MANIFEST_HASH = (
    "a58b5e3480fb7d1b88029cf2c2ff018cfdaae84be3a5861299eed003c13ad235"
)
LIVE_AUDIT_A = "8b38e466da708cb4c9cd3fa56f9958ef65de6c15"
LIVE_AUDIT_B = "8a430a0586f772cbd36e27fdbf5dbe9f04471cfc"
LIVE_AUDIT_BUNDLE = (
    "ab6bd06f5c09bc7af483437d38bc127d0d4c17134367668394bf770b3c932481"
)
LIVE_AUDIT_RECEIPT = (
    "2b3135fc8e01440f8c93fc70ee40621e861e030539b210acf6c61e03f1e67de0"
)
HISTORICAL_AUDIT_B = "7264d4c570d0c5109aec09b3b02f27f687040dc8"
HISTORICAL_CANONICAL_RECEIPT = (
    "ca827f1f10ca825941c3eb7a49aea774bf26453baba51480b4e03d2a3c9d7b74"
)
BRIDGE_BUNDLE = (
    "a9198642c04883dad793075ebf57e971f0f2ee58f468f35485186f204d064754"
)
CANONICAL_PATH = "docs/task_reports/TASK-039E3_R2R_AUDIT_RECEIPT.json"
LIVE_RECEIPT_PATH = (
    "docs/task_reports/TASK-039E3_R2R_LIVE_EXECUTOR_AUDIT_RECEIPT.json"
)
AUTHORIZATION_PATH = (
    ROOT / "docs/task_reports/TASK-039E3_R2R_REEXECUTION_AUTHORIZATION.json"
)
LIVE_EXECUTION_SOURCE = (
    "src/paperworks/v6/task039e3_r2r_live_execution_v1.py"
)


def _git_bytes(commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


def _verified_document(raw: bytes) -> dict[str, object]:
    document = json.loads(raw)
    claimed = document["artifact_hash"]
    content = dict(document)
    content.pop("artifact_hash")
    if stable_hash_v1(content) != claimed:
        raise AssertionError("audit receipt self-hash mismatch")
    return document


def _bridge_bundle_payload() -> dict[str, object]:
    return {
        "task_id": "TASK-039E3-R2R-AUDIT-AUTHORITY-BRIDGE",
        "bridge_contract_version": (
            "task039e3_r2r_canonical_audit_authority_bridge_v1"
        ),
        "implementation_commit_a": IMPLEMENTATION_A,
        "implementation_commit_b": IMPLEMENTATION_B,
        "implementation_source_manifest_hash": SOURCE_MANIFEST_HASH,
        "live_executor_audit_commit_a": LIVE_AUDIT_A,
        "live_executor_audit_commit_b": LIVE_AUDIT_B,
        "live_executor_audit_bundle_hash": LIVE_AUDIT_BUNDLE,
        "live_executor_audit_receipt_hash": LIVE_AUDIT_RECEIPT,
        "remediation_commit_a": IMPLEMENTATION_A,
        "remediation_commit_b": IMPLEMENTATION_B,
        "remediation_bundle_hash": (
            "76f010b03ec3edd285e729fd31c556e3b7b4067d6ba5d3debcebe3e5451e8e15"
        ),
        "remediation_receipt_hash": (
            "73b67d8f2cb144379ecc745b15f64d25ce18cfd79eadf03a16d30c626935eebc"
        ),
        "forensic_audit_commit_a": "851061cba61a1c974731ac475113c75c49ec42ea",
        "forensic_audit_commit_b": "342fff23283cda424a5793b19a9714c24d247b89",
        "forensic_bundle_hash": (
            "6857cf6b7b4015e595fe7efd38589f82ab41b2fccc43b79ea47277dcf824b30d"
        ),
        "forensic_receipt_hash": (
            "82c242edd17b536b3fffc6d3741c04df0794ca29e8e31b269903ee0c25ae2f6b"
        ),
        "failed_execution_receipt_hash": (
            "7d60b8c5690f4f441377c5bdeae01c78452f0ad0b4eda96d9dbd8b1eb0a3c9c7"
        ),
        "historical_canonical_audit_receipt_hash": (
            HISTORICAL_CANONICAL_RECEIPT
        ),
    }


def _authorization_context(
    *, audit_commit: str, audit_bundle: str, audit_receipt: str
) -> R2RAuthorityContextV1:
    document = json.loads(AUTHORIZATION_PATH.read_text(encoding="utf-8"))
    document.update(
        {
            "implementation_commit_a": IMPLEMENTATION_A,
            "implementation_commit_b": IMPLEMENTATION_B,
            "implementation_source_manifest_hash": SOURCE_MANIFEST_HASH,
            "independent_audit_commit_b": audit_commit,
            "independent_audit_bundle_hash": audit_bundle,
            "independent_audit_receipt_hash": audit_receipt,
        }
    )
    document.pop("self_hash")
    document["self_hash"] = stable_hash_v1(document)
    return R2RAuthorityContextV1(
        document=document,
        validated=validate_r2r_authorization_v1(document),
    )


def _git_source_context() -> R2RGitSourceContextV1:
    return R2RGitSourceContextV1(
        repository_root=ROOT,
        source_manifest={"artifact_hash": SOURCE_MANIFEST_HASH},
        source_blobs=(),
        scientific_source_hashes={},
        public_preflight={},
    )


def _invoke_with_bytes(
    raw: bytes,
    *,
    audit_commit: str,
    audit_bundle: str,
    audit_receipt: str,
) -> R2RForensicProtocolContextV1:
    with tempfile.TemporaryDirectory() as temporary:
        receipt_path = Path(temporary) / "audit.json"
        receipt_path.write_bytes(raw)
        return _validate_forensic_protocol(
            ROOT,
            receipt_path,
            _authorization_context(
                audit_commit=audit_commit,
                audit_bundle=audit_bundle,
                audit_receipt=audit_receipt,
            ),
            _git_source_context(),
        )


class R2RAuditAuthorityBridgeTests(unittest.TestCase):
    def test_bridge_bundle_and_canonical_receipt_contract(self) -> None:
        self.assertEqual(stable_hash_v1(_bridge_bundle_payload()), BRIDGE_BUNDLE)
        receipt = _verified_document((ROOT / CANONICAL_PATH).read_bytes())
        expected = {
            "status": "passed_task039e3_r2r_independent_audit",
            "blocking_finding_count": 0,
            "implementation_commit_a": IMPLEMENTATION_A,
            "implementation_commit_b": IMPLEMENTATION_B,
            "implementation_source_manifest_hash": SOURCE_MANIFEST_HASH,
            "audit_bundle_hash": BRIDGE_BUNDLE,
            "live_executor_audit_commit_a": LIVE_AUDIT_A,
            "live_executor_audit_commit_b": LIVE_AUDIT_B,
            "live_executor_audit_bundle_hash": LIVE_AUDIT_BUNDLE,
            "live_executor_audit_receipt_hash": LIVE_AUDIT_RECEIPT,
            "root_cause_closed": True,
            "scientific_semantics_changed": False,
        }
        for key, value in expected.items():
            self.assertEqual(receipt[key], value, key)
        for field in (
            "provider_contact_authorized",
            "provider_diagnostic_call_authorized",
            "scientific_execution_authorized",
            "capability_probe_authorized",
            "capability_reuse_authorized",
            "resume_authorized",
            "historical_partial_result_reuse_authorized",
            "rule_v2_authorized",
            "runtime_authority",
            "utility_evaluation_authorized",
            "winner_selected",
        ):
            self.assertIs(receipt[field], False, field)

    def test_exact_frozen_consumer_accepts_committed_canonical_bridge(self) -> None:
        self.assertEqual(
            _git_bytes(IMPLEMENTATION_A, LIVE_EXECUTION_SOURCE),
            _git_bytes(_head(), LIVE_EXECUTION_SOURCE),
        )
        current = (ROOT / CANONICAL_PATH).read_bytes()
        try:
            committed = _git_bytes(_head(), CANONICAL_PATH)
        except subprocess.CalledProcessError:
            self.skipTest("canonical bridge requires Bridge Commit A")
        if current != committed:
            self.skipTest("canonical bridge requires exact committed bytes")
        receipt = _verified_document(current)
        context = _invoke_with_bytes(
            current,
            audit_commit=_head(),
            audit_bundle=BRIDGE_BUNDLE,
            audit_receipt=str(receipt["artifact_hash"]),
        )
        self.assertEqual(context.audit_receipt_hash, receipt["artifact_hash"])

    def test_historical_canonical_receipt_fails_for_remediated_authority(self) -> None:
        old = _git_bytes(HISTORICAL_AUDIT_B, CANONICAL_PATH)
        receipt = _verified_document(old)
        self.assertEqual(receipt["artifact_hash"], HISTORICAL_CANONICAL_RECEIPT)
        with self.assertRaisesRegex(
            TASK039E3R2RLiveExecutionError,
            "R2R independent audit authority differs",
        ):
            _invoke_with_bytes(
                old,
                audit_commit=HISTORICAL_AUDIT_B,
                audit_bundle=str(receipt["audit_bundle_hash"]),
                audit_receipt=HISTORICAL_CANONICAL_RECEIPT,
            )

    def test_native_live_executor_receipt_is_not_directly_substitutable(self) -> None:
        raw = _git_bytes(LIVE_AUDIT_B, LIVE_RECEIPT_PATH)
        receipt = _verified_document(raw)
        self.assertEqual(receipt["artifact_hash"], LIVE_AUDIT_RECEIPT)
        with self.assertRaisesRegex(
            TASK039E3R2RLiveExecutionError,
            "R2R independent audit authority differs",
        ):
            _invoke_with_bytes(
                raw,
                audit_commit=LIVE_AUDIT_B,
                audit_bundle=LIVE_AUDIT_BUNDLE,
                audit_receipt=LIVE_AUDIT_RECEIPT,
            )


if __name__ == "__main__":
    unittest.main()
