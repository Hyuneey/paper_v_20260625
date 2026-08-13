"""Exact frozen-consumer oracles for the direct-remediation audit bridge."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_authorization_v1 import validate_r2r_authorization_v1
from paperworks.v6.task039e3_r2r_live_execution_v1 import (
    R2RAuthorityContextV1,
    R2RForensicProtocolContextV1,
    R2RGitSourceContextV1,
    TASK039E3R2RLiveExecutionError,
    _validate_forensic_protocol,
)


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_A = "5dca2d0431d60ef2f2bdfc907ebfe3fe18521f16"
IMPLEMENTATION_B = "d511372db560fd2cf27c2d56db7c637a3324584f"
SOURCE_MANIFEST_HASH = "9037fda0bc7694fd643058a9779fb919c75664824f2f11c49dde9f4be1b209b8"
DIRECT_AUDIT_A = "10195ce26439521870c012f733079831d6bb3d2e"
DIRECT_AUDIT_B = "2e1e10926ffe7c718e3e4f63dbe40d85f7e7bbdd"
DIRECT_AUDIT_BUNDLE = "12d11e3da47208538c1ae4b0baf406822de6b8f97d125a1212ead088f3685353"
DIRECT_AUDIT_RECEIPT = "0af6b8e9095cc6426e74953f853ebaf0643df3245c90b1ab034ef1cb00a05ebe"
HISTORICAL_BRIDGE_B = "498f0dc96483649a9fb0d4affb1ad351d067a9d0"
HISTORICAL_CANONICAL_RECEIPT = "f8ce7dc61f1ebcb17c4ddda95e915e21140049ac5958c34843228970db318009"
BRIDGE_BUNDLE = "6504e699583b433ff5df6cd60ce67b6d892a44d441e71acab2d0ceddfff47137"
CANONICAL_PATH = "docs/task_reports/TASK-039E3_R2R_AUDIT_RECEIPT.json"
DIRECT_RECEIPT_PATH = "docs/task_reports/TASK-039E3_R2R_DIRECT_RENDERING_AUDIT_RECEIPT.json"
AUTHORIZATION_PATH = ROOT / "docs/task_reports/TASK-039E3_R2R_REEXECUTION_AUTHORIZATION_V2.json"
LIVE_EXECUTION_SOURCE = "src/paperworks/v6/task039e3_r2r_live_execution_v1.py"


def _git_bytes(commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"], cwd=ROOT, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout


def _head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
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
        "task_id": "TASK-039E3-R2R-DIRECT-REMEDIATION-AUTHORITY-BRIDGE",
        "bridge_contract_version": "task039e3_r2r_direct_remediation_canonical_audit_authority_bridge_v1",
        "implementation_commit_a": IMPLEMENTATION_A,
        "implementation_commit_b": IMPLEMENTATION_B,
        "implementation_source_manifest_hash": SOURCE_MANIFEST_HASH,
        "direct_remediation_commit_a": IMPLEMENTATION_A,
        "direct_remediation_commit_b": IMPLEMENTATION_B,
        "direct_remediation_bundle_hash": "ed53460360705d17630b39749f5b39cfe4229f0a535f9814730681aa5d0fbf78",
        "direct_remediation_receipt_hash": "721cbc3f51709293bf489a0622843e0f968957fcd24672756a0409e55ea7f43d",
        "direct_rendering_audit_commit_a": DIRECT_AUDIT_A,
        "direct_rendering_audit_commit_b": DIRECT_AUDIT_B,
        "direct_rendering_audit_bundle_hash": DIRECT_AUDIT_BUNDLE,
        "direct_rendering_audit_receipt_hash": DIRECT_AUDIT_RECEIPT,
        "direct_failure_forensic_commit_a": "86da3bfd609a92540a781dfa7cd05f92c74692ec",
        "direct_failure_forensic_commit_b": "4712eeea87f0f60b51f4db9414fb589391c899d1",
        "direct_failure_forensic_bundle_hash": "1ba71368cbdfa29aa12c2b6bac3ba4cee029766222455334e5fb84ff5c70bd11",
        "direct_failure_forensic_receipt_hash": "910a3ef3e536e209c267c7a3d437cc25d42f5c388534bce051e27e10f6e1b333",
        "failed_execution_receipt_hash": "b68443208e7dca30aaad862610421d7c78cf40cc8c951b33ef4a55a9929c5393",
        "historical_canonical_audit_receipt_hash": HISTORICAL_CANONICAL_RECEIPT,
        "historical_canonical_bridge_commit_b": HISTORICAL_BRIDGE_B,
        "historical_canonical_bridge_bundle_hash": "a9198642c04883dad793075ebf57e971f0f2ee58f468f35485186f204d064754",
        "scientific_accounting_behavior_hash": "0e18526c8dbcaec26d67385b89c60826dc4388cac08727cd61a2c60b1b812ae2",
    }


def _authorization_context(*, audit_commit: str, audit_bundle: str, audit_receipt: str) -> R2RAuthorityContextV1:
    document = json.loads(AUTHORIZATION_PATH.read_text(encoding="utf-8"))
    document.update({
        "implementation_commit_a": IMPLEMENTATION_A,
        "implementation_commit_b": IMPLEMENTATION_B,
        "implementation_source_manifest_hash": SOURCE_MANIFEST_HASH,
        "independent_audit_commit_b": audit_commit,
        "independent_audit_bundle_hash": audit_bundle,
        "independent_audit_receipt_hash": audit_receipt,
    })
    document.pop("self_hash")
    document["self_hash"] = stable_hash_v1(document)
    return R2RAuthorityContextV1(document=document, validated=validate_r2r_authorization_v1(document))


def _git_source_context() -> R2RGitSourceContextV1:
    return R2RGitSourceContextV1(
        repository_root=ROOT,
        source_manifest={"artifact_hash": SOURCE_MANIFEST_HASH},
        source_blobs=(), scientific_source_hashes={}, public_preflight={},
    )


def _invoke_with_bytes(raw: bytes, *, audit_commit: str, audit_bundle: str, audit_receipt: str) -> R2RForensicProtocolContextV1:
    with tempfile.TemporaryDirectory() as temporary:
        receipt_path = Path(temporary) / "audit.json"
        receipt_path.write_bytes(raw)
        return _validate_forensic_protocol(
            ROOT, receipt_path,
            _authorization_context(
                audit_commit=audit_commit, audit_bundle=audit_bundle,
                audit_receipt=audit_receipt,
            ),
            _git_source_context(),
        )


class R2RDirectAuthorityBridgeTests(unittest.TestCase):
    def test_bridge_bundle_and_consumer_contract(self) -> None:
        self.assertEqual(stable_hash_v1(_bridge_bundle_payload()), BRIDGE_BUNDLE)
        receipt = _verified_document((ROOT / CANONICAL_PATH).read_bytes())
        expected = {
            "artifact_type": "task039e3_r2r_independent_audit_receipt_v1",
            "status": "passed_task039e3_r2r_independent_audit",
            "blocking_finding_count": 0,
            "implementation_commit_a": IMPLEMENTATION_A,
            "implementation_commit_b": IMPLEMENTATION_B,
            "implementation_source_manifest_hash": SOURCE_MANIFEST_HASH,
            "audit_bundle_hash": BRIDGE_BUNDLE,
            "direct_rendering_audit_commit_a": DIRECT_AUDIT_A,
            "direct_rendering_audit_commit_b": DIRECT_AUDIT_B,
            "direct_rendering_audit_bundle_hash": DIRECT_AUDIT_BUNDLE,
            "direct_rendering_audit_receipt_hash": DIRECT_AUDIT_RECEIPT,
            "historical_scientific_logical_calls_total": 6,
            "root_cause_closed": True,
            "scientific_protocol_changed": False,
            "direct_number_withholding_policy_changed": False,
        }
        for key, exact in expected.items():
            self.assertEqual(receipt[key], exact, key)
        for field in (
            "provider_contact_authorized", "provider_diagnostic_call_authorized",
            "scientific_execution_authorized", "capability_probe_authorized",
            "capability_reuse_authorized", "resume_authorized",
            "historical_partial_result_reuse_authorized", "rule_v2_authorized",
            "runtime_authority", "utility_evaluation_authorized", "winner_selected",
        ):
            self.assertIs(receipt[field], False, field)

    def test_exact_frozen_consumer_accepts_committed_bridge(self) -> None:
        self.assertEqual(_git_bytes(IMPLEMENTATION_A, LIVE_EXECUTION_SOURCE), _git_bytes(_head(), LIVE_EXECUTION_SOURCE))
        current = (ROOT / CANONICAL_PATH).read_bytes()
        try:
            committed = _git_bytes(_head(), CANONICAL_PATH)
        except subprocess.CalledProcessError:
            self.skipTest("canonical bridge requires Bridge Commit A")
        if current != committed:
            self.skipTest("canonical bridge requires exact committed bytes")
        receipt = _verified_document(current)
        context = _invoke_with_bytes(
            current, audit_commit=_head(), audit_bundle=BRIDGE_BUNDLE,
            audit_receipt=str(receipt["artifact_hash"]),
        )
        self.assertEqual(context.audit_receipt_hash, receipt["artifact_hash"])

    def test_historical_canonical_receipt_rejected_for_new_authority(self) -> None:
        raw = _git_bytes(HISTORICAL_BRIDGE_B, CANONICAL_PATH)
        receipt = _verified_document(raw)
        self.assertEqual(receipt["artifact_hash"], HISTORICAL_CANONICAL_RECEIPT)
        with self.assertRaisesRegex(TASK039E3R2RLiveExecutionError, "R2R independent audit authority differs"):
            _invoke_with_bytes(
                raw, audit_commit=HISTORICAL_BRIDGE_B,
                audit_bundle=str(receipt["audit_bundle_hash"]),
                audit_receipt=HISTORICAL_CANONICAL_RECEIPT,
            )

    def test_native_direct_audit_receipt_not_directly_substitutable(self) -> None:
        raw = _git_bytes(DIRECT_AUDIT_B, DIRECT_RECEIPT_PATH)
        receipt = _verified_document(raw)
        self.assertEqual(receipt["artifact_hash"], DIRECT_AUDIT_RECEIPT)
        with self.assertRaisesRegex(TASK039E3R2RLiveExecutionError, "R2R independent audit authority differs"):
            _invoke_with_bytes(
                raw, audit_commit=DIRECT_AUDIT_B,
                audit_bundle=DIRECT_AUDIT_BUNDLE,
                audit_receipt=DIRECT_AUDIT_RECEIPT,
            )


if __name__ == "__main__":
    unittest.main()
