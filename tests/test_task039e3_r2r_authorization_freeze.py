"""Offline oracle for the final one-shot R2R authorization freeze."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_authorization_v1 import (
    TASK039E3R2RAuthorizationError,
    validate_r2r_authorization_v1,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIGURATION_PATH = (
    ROOT / "docs/task_reports/TASK-039E3_R2R_EXECUTION_CONFIGURATION.json"
)
AUTHORIZATION_PATH = (
    ROOT / "docs/task_reports/TASK-039E3_R2R_EXECUTION_AUTHORIZATION.json"
)
SCHEMA_PATH = (
    ROOT / "schemas/v6/task039e3_r2r_execution_authorization_v1_schema.json"
)
SOURCE_MANIFEST_PATH = (
    "docs/task_reports/"
    "TASK-039E3_R2R_FINALIZATION_REMEDIATION_SOURCE_FREEZE.json"
)
AUDIT_RECEIPT_PATH = "docs/task_reports/TASK-039E3_R2R_AUDIT_RECEIPT.json"

BASE = "7264d4c570d0c5109aec09b3b02f27f687040dc8"
IMPLEMENTATION_A = "eb62b449e06ea5f6c4a2d445223f6ca98de3690c"
IMPLEMENTATION_B = "2caec1dbdfd175e07bc2d5d5bf4d36896f56f99d"
SOURCE_MANIFEST_HASH = (
    "01c8e23f2eb15f321295bf0163dcbd81df67ed0179817acb725614a45bfede1d"
)
AUDIT_BUNDLE_HASH = (
    "1c7694ece1d9c26944f27580b6df1110c7bd9f96fdbc2503afc7835c7be25044"
)
AUDIT_RECEIPT_HASH = (
    "ca827f1f10ca825941c3eb7a49aea774bf26453baba51480b4e03d2a3c9d7b74"
)
CONFIGURATION_HASH = "edeffb7c6c1282a529df00ec3820039c3289b3c274279131e4a305fcaf990f6d"
AUTHORIZATION_HASH = "674d314c42d672dfdd847e5552a310f938fb44b7a55c4bd49fa968d3aa746c91"


def _git_bytes(commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _verified_artifact(path: str) -> dict[str, object]:
    document = json.loads((ROOT / path).read_text(encoding="utf-8"))
    claimed = document.pop("artifact_hash")
    if claimed != stable_hash_v1(document):
        raise AssertionError(f"self-hash mismatch: {path}")
    return {"artifact_hash": claimed, **document}


def _assert_schema_rule(test: unittest.TestCase, value: object, rule: dict[str, object], name: str) -> None:
    expected_type = rule.get("type")
    types = {
        "string": str,
        "boolean": bool,
        "integer": int,
        "number": (int, float),
    }
    if expected_type in types:
        test.assertIsInstance(value, types[expected_type], name)
        if expected_type == "integer":
            test.assertIsNot(type(value), bool, name)
        if expected_type == "number":
            test.assertIsNot(type(value), bool, name)
    if "const" in rule:
        test.assertEqual(value, rule["const"], name)
        test.assertIs(type(value), type(rule["const"]), name)
    if "pattern" in rule:
        test.assertRegex(str(value), re.compile(str(rule["pattern"])), name)


class R2RAuthorizationFreezeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.configuration = json.loads(CONFIGURATION_PATH.read_text(encoding="utf-8"))
        self.authorization = json.loads(AUTHORIZATION_PATH.read_text(encoding="utf-8"))
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_configuration_self_hash_and_exact_execution_semantics(self) -> None:
        content = dict(self.configuration)
        claimed = content.pop("artifact_hash")
        self.assertEqual(claimed, CONFIGURATION_HASH)
        self.assertEqual(stable_hash_v1(content), CONFIGURATION_HASH)
        expected = {
            "recovery_execution_mode": "FRESH_FULL_COHORT_RESTART",
            "implementation_commit_a": IMPLEMENTATION_A,
            "implementation_commit_b": IMPLEMENTATION_B,
            "implementation_source_manifest_hash": SOURCE_MANIFEST_HASH,
            "exact_model": "gpt-5.4-2026-03-05",
            "endpoint": "https://api.openai.com/v1/chat/completions",
            "maximum_transport_attempts": 3,
            "maximum_transport_retries": 2,
            "retry_waits_seconds": [2.0, 4.0],
            "scientific_concurrency": 1,
            "scientific_generation_retries": 0,
            "relations": 42,
            "t1_logical_calls": 42,
            "t1_b_logical_calls": 126,
            "t2_logical_calls_minimum": 42,
            "t2_logical_calls_maximum": 126,
            "direct_number_logical_calls": 42,
            "scientific_logical_calls_minimum": 252,
            "scientific_logical_calls_maximum": 336,
            "historical_aborted_r2_scientific_logical_calls": 1,
            "additional_capability_probes": 0,
            "cumulative_capability_probes": 2,
            "maximum_cumulative_capability_probes": 2,
            "http_error_retained_bytes": 65536,
            "http_error_maximum_read_bytes": 65537,
            "http400_retryable": False,
            "historical_partial_result_reuse": False,
            "one_shot_live_runner_invocation": True,
            "automatic_resume": False,
            "automatic_reexecution": False,
            "patch_and_continue": False,
            "provider_fallback": False,
            "model_fallback": False,
            "exact_worktree_bytes_must_equal_git_objects": True,
        }
        for key, value in expected.items():
            self.assertEqual(self.configuration[key], value, key)

    def test_authorization_closed_schema_self_hash_and_native_validator(self) -> None:
        self.assertIs(self.schema["additionalProperties"], False)
        self.assertEqual(set(self.schema["properties"]), set(self.schema["required"]))
        self.assertEqual(set(self.authorization), set(self.schema["required"]))
        for name, rule in self.schema["properties"].items():
            _assert_schema_rule(self, self.authorization[name], rule, name)
        content = dict(self.authorization)
        claimed = content.pop("self_hash")
        self.assertEqual(claimed, AUTHORIZATION_HASH)
        self.assertEqual(stable_hash_v1(content), AUTHORIZATION_HASH)
        validated = validate_r2r_authorization_v1(self.authorization)
        self.assertEqual(validated.self_hash, AUTHORIZATION_HASH)
        self.assertEqual(
            self.authorization["recovery_execution_configuration_hash"],
            CONFIGURATION_HASH,
        )

    def test_exact_final_lineage_and_canonical_audit_git_bytes(self) -> None:
        self.assertEqual(
            self.authorization["implementation_commit_a"], IMPLEMENTATION_A
        )
        self.assertEqual(
            self.authorization["implementation_commit_b"], IMPLEMENTATION_B
        )
        self.assertEqual(
            self.authorization["implementation_source_manifest_hash"],
            SOURCE_MANIFEST_HASH,
        )
        self.assertEqual(self.authorization["independent_audit_commit_b"], BASE)
        self.assertEqual(
            self.authorization["independent_audit_bundle_hash"], AUDIT_BUNDLE_HASH
        )
        self.assertEqual(
            self.authorization["independent_audit_receipt_hash"], AUDIT_RECEIPT_HASH
        )
        audit_git = _git_bytes(BASE, AUDIT_RECEIPT_PATH)
        self.assertEqual(audit_git, _git_bytes("HEAD", AUDIT_RECEIPT_PATH))
        audit = json.loads(audit_git)
        self.assertEqual(audit["artifact_hash"], AUDIT_RECEIPT_HASH)
        self.assertEqual(audit["audit_bundle_hash"], AUDIT_BUNDLE_HASH)
        self.assertEqual(audit["blocking_finding_count"], 0)
        self.assertEqual(audit["status"], "passed_task039e3_r2r_independent_audit")

    def test_all_upstream_governance_artifacts_self_verify(self) -> None:
        checks = {
            "docs/task_reports/TASK-039E3_R2R_FINALIZATION_REMEDIATION_RECEIPT.json":
                "034316c037166c00184eef1f55b8c3c040500f038dbda78499d67c1a693fa95f",
            "docs/task_reports/TASK-039E3_R2_SCIENTIFIC_RECOVERY_PROTOCOL_RECEIPT.json":
                "2d65919dced159c2e584b4c5347dc2f4a3f8fd0d35323322d68014d2843f1168",
            "docs/task_reports/TASK-039E3_R2_FAILURE_FORENSIC_RECEIPT.json":
                "caa4a5b7537aaa62dd83f32253fa00aa9474c6472bdd48b23f16d80c89a15b46",
            "docs/task_reports/TASK-039E3_R2_RECOVERY_CAPABILITY_REUSE_BINDING.json":
                "a26582efd20add0e639c40e7f3ed64428dc39923d284d0f0ad0d69d017b02f82",
        }
        for path, expected in checks.items():
            with self.subTest(path=path):
                self.assertEqual(_verified_artifact(path)["artifact_hash"], expected)

    def test_complete_source_manifest_reproduces_50_exact_git_records(self) -> None:
        manifest = json.loads(_git_bytes(IMPLEMENTATION_B, SOURCE_MANIFEST_PATH))
        content = dict(manifest)
        claimed = content.pop("artifact_hash")
        self.assertEqual(claimed, SOURCE_MANIFEST_HASH)
        self.assertEqual(stable_hash_v1(content), SOURCE_MANIFEST_HASH)
        self.assertEqual(manifest["described_commit"], IMPLEMENTATION_A)
        self.assertEqual(manifest["source_record_count"], 50)
        self.assertEqual(len(manifest["source_records"]), 50)
        self.assertEqual(
            manifest["unbound_material_project_local_dependency_count"], 0
        )
        for record in manifest["source_records"]:
            path = record["repository_path"]
            with self.subTest(path=path):
                exact = _git_bytes(IMPLEMENTATION_A, path)
                blob = subprocess.run(
                    ["git", "rev-parse", f"{IMPLEMENTATION_A}:{path}"],
                    cwd=ROOT,
                    check=True,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                ).stdout.strip()
                self.assertEqual(blob, record["git_blob_sha"])
                self.assertEqual(hashlib.sha256(exact).hexdigest(), record["sha256"])

    def test_one_shot_grants_and_prohibitions_are_exact_and_latched(self) -> None:
        for field in (
            "capability_reuse_authorized",
            "provider_contact_authorized",
            "scientific_execution_authorized",
        ):
            self.assertIs(self.authorization[field], True, field)
        prohibited = (
            "capability_probe_authorized",
            "provider_diagnostic_call_authorized",
            "resume_authorized",
            "historical_partial_result_reuse_authorized",
            "rule_v2_authorized",
            "runtime_authority",
            "utility_evaluation_authorized",
            "winner_selected",
        )
        for field in prohibited:
            self.assertIs(self.authorization[field], False, field)
            changed = dict(self.authorization)
            changed[field] = True
            changed.pop("self_hash")
            changed["self_hash"] = stable_hash_v1(changed)
            with self.assertRaises(TASK039E3R2RAuthorizationError):
                validate_r2r_authorization_v1(changed)

    def test_freeze_artifacts_contain_no_secret_or_private_path(self) -> None:
        combined = (
            CONFIGURATION_PATH.read_text(encoding="utf-8")
            + AUTHORIZATION_PATH.read_text(encoding="utf-8")
        )
        for prohibited in (
            "OPENAI_API_KEY",
            "Authorization:",
            "Bearer ",
            "C:\\\\Users\\\\",
            "e1-private-root",
            "recovery-private-root",
        ):
            self.assertNotIn(prohibited, combined)


if __name__ == "__main__":
    unittest.main()
