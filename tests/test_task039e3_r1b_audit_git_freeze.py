"""Independent raw-Git audit oracle for TASK-039E3-R1B source freeze."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import unittest


_MAIN = "11a5f04a0422049a099020f06c59ec23bc72d130"
_E3_PREP = "aee1fc6e22bcb45572fe3bab5c9bb605de09d721"
_HISTORICAL_E3_A = "48b79643088ce1a0179191d7ddae4c97dc8dece9"
_HISTORICAL_BLOCK = "52a8cec2d170f9b8e3c5c0ac048115ffad93e018"
_R0 = "d5164aa93cc4c3efb6a343e0890b554f436a7e39"
_BLOCKED_R1 = "2f4aac3209ad0756649b3be7d993fc217357025e"
_R1A = "260b91be463815bc5bb453ca2cc05cec741aacc3"
_R1B_A = "93c2e8a6333829446c5353f1ca9b61c967f8a7a7"
_R1B_B = "2b6e4964085b2405513680303e0586f7cca50c6d"

_SOURCE_MANIFEST_HASH = "d976af3fc66a3b5aa69ef9aa3a97146cd93a6941fc9e1c28b6783ed6f1a7dc7d"
_IMPLEMENTATION_BUNDLE_HASH = "0822326ef4b5b6a86ff8c3f17cc2db460a1efb5b0b0683a027e3e8e49c6c302e"
_IMPLEMENTATION_RECEIPT_HASH = "22236bce28da183bebf7778675453ecbef134f67653275f2bda8604933261722"
_R0_BUNDLE_HASH = "8c402cdea45f53a7bb49cfb8ba796d4b557a6fb70532c7ad22281f3b62c60ccc"
_R0_PROTOCOL_HASH = "8b1b55c4ed96b0642737e616dd60b271684d59738c8186211abb9c6c46cd1362"
_R1A_TIMEOUT_HASH = "d70f40d644405387681dfd2984b9fed2c4c8c0d6da13fbdd79a428b226b46865"
_R1A_RECEIPT_HASH = "2ad5eac5d18ad6ecac742279dc5c7c70d5fca3546f1aa2ea8607889119fa1441"

_REPORTS = {
    "docs/task_reports/TASK-039E3_R1B_DATA_ACCESS_AUDIT.json",
    "docs/task_reports/TASK-039E3_R1B_IMPLEMENTATION_AUTHORITY.json",
    "docs/task_reports/TASK-039E3_R1B_IMPLEMENTATION_RECEIPT.json",
    "docs/task_reports/TASK-039E3_R1B_RECOVERY_CONFIGURATION.json",
    "docs/task_reports/TASK-039E3_R1B_REPORT.md",
    "docs/task_reports/TASK-039E3_R1B_SOURCE_FREEZE.json",
    "docs/task_reports/TASK-039E3_R1B_TEST_REPORT.json",
}


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def _git_bytes(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args],
        cwd=_repo(),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _git_text(*args: str) -> str:
    return _git_bytes(*args).decode("utf-8").strip()


def _commit_parent(commit: str) -> str:
    parts = _git_text("rev-list", "--parents", "-n", "1", commit).split()
    if len(parts) != 2:
        raise AssertionError(f"expected one parent for {commit}, got {parts[1:]}")
    return parts[1]


def _blob(commit: str, path: str) -> bytes:
    return _git_bytes("show", f"{commit}:{path}")


def _json_at(commit: str, path: str) -> dict[str, object]:
    value = json.loads(_blob(commit, path).decode("utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"expected JSON object at {commit}:{path}")
    return value


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _assert_artifact_self_hash(test: unittest.TestCase, document: dict[str, object]) -> None:
    supplied = document.get("artifact_hash")
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    test.assertEqual(supplied, _canonical_sha256(payload))


def _assert_named_self_hash(
    test: unittest.TestCase,
    document: dict[str, object],
    field: str,
) -> None:
    supplied = document.get(field)
    payload = {key: value for key, value in document.items() if key != field}
    test.assertEqual(supplied, _canonical_sha256(payload))


class TestTask039E3R1BGitFreezeAudit(unittest.TestCase):
    def test_exact_authoritative_lineage_and_main(self) -> None:
        self.assertEqual(_git_text("rev-parse", "origin/main"), _MAIN)
        expected_parents = {
            _HISTORICAL_E3_A: _E3_PREP,
            _HISTORICAL_BLOCK: _HISTORICAL_E3_A,
            _R0: _HISTORICAL_BLOCK,
            _BLOCKED_R1: _R0,
            _R1A: _BLOCKED_R1,
            _R1B_A: _R1A,
            _R1B_B: _R1B_A,
        }
        for commit, parent in expected_parents.items():
            with self.subTest(commit=commit):
                self.assertEqual(_commit_parent(commit), parent)

    def test_commit_b_is_exactly_reports_only(self) -> None:
        changed = {
            line.split("\t", 1)[1]
            for line in _git_text("diff", "--name-status", _R1B_A, _R1B_B).splitlines()
        }
        self.assertEqual(changed, _REPORTS)
        for line in _git_text("diff", "--name-status", _R1B_A, _R1B_B).splitlines():
            self.assertTrue(line.startswith("A\t"), line)

    def test_all_fourteen_manifest_records_match_raw_git_blobs(self) -> None:
        path = "docs/task_reports/TASK-039E3_R1B_SOURCE_FREEZE.json"
        manifest = _json_at(_R1B_B, path)
        _assert_artifact_self_hash(self, manifest)
        self.assertEqual(manifest["artifact_hash"], _SOURCE_MANIFEST_HASH)
        self.assertEqual(manifest["described_commit"], _R1B_A)
        self.assertEqual(manifest["source_record_count"], 14)
        records = manifest["source_records"]
        self.assertIsInstance(records, list)
        self.assertEqual(len(records), 14)
        seen: set[str] = set()
        for record in records:
            self.assertIsInstance(record, dict)
            repository_path = record["repository_path"]
            self.assertIsInstance(repository_path, str)
            self.assertNotIn(repository_path, seen)
            seen.add(repository_path)
            blob_a = _blob(_R1B_A, repository_path)
            blob_sha_a = _git_text("rev-parse", f"{_R1B_A}:{repository_path}")
            blob_sha_b = _git_text("rev-parse", f"{_R1B_B}:{repository_path}")
            self.assertEqual(blob_sha_a, record["git_blob_sha"])
            self.assertEqual(hashlib.sha256(blob_a).hexdigest(), record["sha256"])
            self.assertEqual(blob_sha_b, blob_sha_a)
            self.assertEqual(_blob(_R1B_B, repository_path), blob_a)

    def test_receipt_components_and_authority_bindings_recompute(self) -> None:
        receipt_path = "docs/task_reports/TASK-039E3_R1B_IMPLEMENTATION_RECEIPT.json"
        receipt = _json_at(_R1B_B, receipt_path)
        _assert_artifact_self_hash(self, receipt)
        self.assertEqual(receipt["artifact_hash"], _IMPLEMENTATION_RECEIPT_HASH)
        self.assertEqual(receipt["implementation_bundle_hash"], _IMPLEMENTATION_BUNDLE_HASH)
        self.assertEqual(receipt["source_manifest_hash"], _SOURCE_MANIFEST_HASH)
        self.assertEqual(receipt["r1b_commit_a"], _R1B_A)

        component_paths = {
            "data_access_audit": "docs/task_reports/TASK-039E3_R1B_DATA_ACCESS_AUDIT.json",
            "implementation_authority": "docs/task_reports/TASK-039E3_R1B_IMPLEMENTATION_AUTHORITY.json",
            "recovery_configuration": "docs/task_reports/TASK-039E3_R1B_RECOVERY_CONFIGURATION.json",
            "source_freeze": "docs/task_reports/TASK-039E3_R1B_SOURCE_FREEZE.json",
            "test_report": "docs/task_reports/TASK-039E3_R1B_TEST_REPORT.json",
        }
        components = receipt["component_artifact_hashes"]
        self.assertIsInstance(components, dict)
        self.assertEqual(set(components), set(component_paths))
        for name, component_path in component_paths.items():
            document = _json_at(_R1B_B, component_path)
            _assert_artifact_self_hash(self, document)
            self.assertEqual(components[name], document["artifact_hash"])

        report_bytes = _blob(_R1B_B, "docs/task_reports/TASK-039E3_R1B_REPORT.md")
        self.assertEqual(receipt["report_sha256"], hashlib.sha256(report_bytes).hexdigest())

        authority = _json_at(
            _R1B_B,
            "docs/task_reports/TASK-039E3_R1B_IMPLEMENTATION_AUTHORITY.json",
        )
        self.assertEqual(authority["r0_commit"], _R0)
        self.assertEqual(authority["r0_bundle_hash"], _R0_BUNDLE_HASH)
        self.assertEqual(authority["r0_recovery_protocol_hash"], _R0_PROTOCOL_HASH)
        self.assertEqual(authority["r1a_commit"], _R1A)
        self.assertEqual(authority["r1a_timeout_authority_hash"], _R1A_TIMEOUT_HASH)
        self.assertEqual(authority["r1a_receipt_hash"], _R1A_RECEIPT_HASH)
        self.assertFalse(authority["provider_contact_authorized"])
        self.assertFalse(authority["recovery_probe_authorized"])
        self.assertFalse(authority["scientific_execution_authorized"])

        r0_receipt = _json_at(_R0, "docs/task_reports/TASK-039E3_R0_RECEIPT.json")
        r0_protocol = _json_at(_R0, "docs/task_reports/TASK-039E3_R0_RECOVERY_PROTOCOL.json")
        _assert_artifact_self_hash(self, r0_receipt)
        _assert_artifact_self_hash(self, r0_protocol)
        self.assertEqual(r0_receipt["artifact_hash"], _R0_BUNDLE_HASH)
        self.assertEqual(r0_protocol["artifact_hash"], _R0_PROTOCOL_HASH)
        self.assertEqual(
            r0_receipt["component_artifact_hashes"]["recovery"],
            r0_protocol["artifact_hash"],
        )

        r1a_authority = _json_at(
            _R1A,
            "docs/task_reports/TASK-039E3_R1A_TIMEOUT_AUTHORITY.json",
        )
        r1a_receipt = _json_at(_R1A, "docs/task_reports/TASK-039E3_R1A_RECEIPT.json")
        _assert_named_self_hash(self, r1a_authority, "self_hash")
        _assert_named_self_hash(self, r1a_receipt, "self_hash")
        self.assertEqual(r1a_authority["self_hash"], _R1A_TIMEOUT_HASH)
        self.assertEqual(r1a_receipt["self_hash"], _R1A_RECEIPT_HASH)
        self.assertEqual(r1a_receipt["timeout_authority_hash"], _R1A_TIMEOUT_HASH)


if __name__ == "__main__":
    unittest.main()
