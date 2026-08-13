"""Offline oracle for the one-shot R2R fresh reexecution authority."""

from __future__ import annotations

import ast
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
BASE = "8a430a0586f772cbd36e27fdbf5dbe9f04471cfc"
IMPLEMENTATION_A = "f10365adbdde5bb2070df429770174d215829dc6"
IMPLEMENTATION_B = "067dcffc441170064180c677b0bd7845a93ce5ef"
SOURCE_MANIFEST_HASH = (
    "a58b5e3480fb7d1b88029cf2c2ff018cfdaae84be3a5861299eed003c13ad235"
)
AUDIT_A = "8b38e466da708cb4c9cd3fa56f9958ef65de6c15"
AUDIT_B = BASE
AUDIT_BUNDLE_HASH = (
    "ab6bd06f5c09bc7af483437d38bc127d0d4c17134367668394bf770b3c932481"
)
AUDIT_RECEIPT_HASH = (
    "2b3135fc8e01440f8c93fc70ee40621e861e030539b210acf6c61e03f1e67de0"
)
FORENSIC_RECEIPT_HASH = (
    "82c242edd17b536b3fffc6d3741c04df0794ca29e8e31b269903ee0c25ae2f6b"
)
FAILED_EXECUTION_RECEIPT_HASH = (
    "7d60b8c5690f4f441377c5bdeae01c78452f0ad0b4eda96d9dbd8b1eb0a3c9c7"
)
OLD_AUTHORIZATION_HASH = (
    "674d314c42d672dfdd847e5552a310f938fb44b7a55c4bd49fa968d3aa746c91"
)
CONFIGURATION_HASH = (
    "3c6e0659c2af0bc4cc4684f895e043581cdac67749226241bf74837f889e9fa6"
)
AUTHORIZATION_HASH = (
    "cf24208fbd12f4a1b54425640bb370de9f781b222224545b8cfbd1670c1aba06"
)

CONFIGURATION_PATH = (
    ROOT / "docs/task_reports/TASK-039E3_R2R_REEXECUTION_CONFIGURATION.json"
)
AUTHORIZATION_PATH = (
    ROOT / "docs/task_reports/TASK-039E3_R2R_REEXECUTION_AUTHORIZATION.json"
)
OLD_AUTHORIZATION_PATH = (
    ROOT / "docs/task_reports/TASK-039E3_R2R_EXECUTION_AUTHORIZATION.json"
)
SCHEMA_PATH = (
    ROOT / "schemas/v6/task039e3_r2r_execution_authorization_v1_schema.json"
)
SOURCE_MANIFEST_PATH = (
    "docs/task_reports/"
    "TASK-039E3_R2R_LIVE_EXECUTOR_REMEDIATION_SOURCE_FREEZE.json"
)
AUDIT_RECEIPT_PATH = (
    "docs/task_reports/TASK-039E3_R2R_LIVE_EXECUTOR_AUDIT_RECEIPT.json"
)


def _git_bytes(commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _verified_json_bytes(raw: bytes) -> dict[str, object]:
    document = json.loads(raw)
    key = "self_hash" if "self_hash" in document else "artifact_hash"
    claimed = document[key]
    content = dict(document)
    content.pop(key)
    if stable_hash_v1(content) != claimed:
        raise AssertionError("artifact self-hash mismatch")
    return document


def _assert_schema_rule(
    test: unittest.TestCase,
    value: object,
    rule: dict[str, object],
    name: str,
) -> None:
    expected_type = rule.get("type")
    native_types: dict[str, type[object] | tuple[type[object], ...]] = {
        "string": str,
        "boolean": bool,
        "integer": int,
        "number": (int, float),
    }
    if isinstance(expected_type, str) and expected_type in native_types:
        test.assertIsInstance(value, native_types[expected_type], name)
        if expected_type in {"integer", "number"}:
            test.assertIsNot(type(value), bool, name)
    if "const" in rule:
        test.assertEqual(value, rule["const"], name)
        test.assertIs(type(value), type(rule["const"]), name)
    if "pattern" in rule:
        test.assertRegex(str(value), re.compile(str(rule["pattern"])), name)


class R2RReauthorizationFreezeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.configuration = json.loads(
            CONFIGURATION_PATH.read_text(encoding="utf-8")
        )
        self.authorization = json.loads(
            AUTHORIZATION_PATH.read_text(encoding="utf-8")
        )
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_reexecution_configuration_self_hash_and_consumed_predecessor(self) -> None:
        content = dict(self.configuration)
        claimed = content.pop("artifact_hash")
        self.assertEqual(claimed, CONFIGURATION_HASH)
        self.assertEqual(stable_hash_v1(content), CONFIGURATION_HASH)
        expected = {
            "execution_event": (
                "R2R_FRESH_REEXECUTION_AFTER_ZERO_CONTACT_EXECUTOR_REMEDIATION"
            ),
            "execution_mode": "FRESH_FULL_COHORT_RESTART",
            "implementation_commit_a": IMPLEMENTATION_A,
            "implementation_commit_b": IMPLEMENTATION_B,
            "implementation_source_manifest_hash": SOURCE_MANIFEST_HASH,
            "live_executor_audit_commit_b": AUDIT_B,
            "live_executor_audit_bundle_hash": AUDIT_BUNDLE_HASH,
            "live_executor_audit_receipt_hash": AUDIT_RECEIPT_HASH,
            "predecessor_consumed_authorization_hash": OLD_AUTHORIZATION_HASH,
            "predecessor_authorization_reusable": False,
            "historical_failed_execution_receipt_hash": (
                FAILED_EXECUTION_RECEIPT_HASH
            ),
            "historical_failed_execution_provider_calls": 0,
            "historical_failed_execution_scientific_logical_calls": 0,
            "failed_r2r_partial_t0_reusable": False,
            "fresh_r2r_scientific_logical_calls_minimum": 252,
            "fresh_r2r_scientific_logical_calls_maximum": 336,
            "historical_original_r2_aborted_provider_logical_calls": 1,
            "lifetime_provider_scientific_accounting": (
                "1 + actual new R2R scientific logical calls"
            ),
            "capability_probes_current": 2,
            "capability_probes_maximum": 2,
            "additional_capability_probes": 0,
            "third_capability_probe_authorized": False,
            "automatic_resume": False,
            "automatic_whole_run_reexecution": False,
            "whole_run_resume": False,
            "patch_and_continue": False,
        }
        for key, exact in expected.items():
            self.assertEqual(self.configuration[key], exact, key)

    def test_new_authorization_closed_schema_self_hash_and_validator(self) -> None:
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

    def test_new_implementation_audit_and_exact_audit_git_bytes(self) -> None:
        self.assertEqual(self.authorization["implementation_commit_a"], IMPLEMENTATION_A)
        self.assertEqual(self.authorization["implementation_commit_b"], IMPLEMENTATION_B)
        self.assertEqual(
            self.authorization["implementation_source_manifest_hash"],
            SOURCE_MANIFEST_HASH,
        )
        self.assertEqual(self.authorization["independent_audit_commit_b"], AUDIT_B)
        self.assertEqual(
            self.authorization["independent_audit_bundle_hash"], AUDIT_BUNDLE_HASH
        )
        self.assertEqual(
            self.authorization["independent_audit_receipt_hash"],
            AUDIT_RECEIPT_HASH,
        )
        raw = _git_bytes(AUDIT_B, AUDIT_RECEIPT_PATH)
        self.assertEqual(raw, (ROOT / AUDIT_RECEIPT_PATH).read_bytes())
        receipt = _verified_json_bytes(raw)
        self.assertEqual(receipt["artifact_hash"], AUDIT_RECEIPT_HASH)
        self.assertEqual(receipt["live_executor_independent_audit_bundle_hash"], AUDIT_BUNDLE_HASH)
        self.assertEqual(receipt["status"], "passed_task039e3_r2r_live_executor_independent_audit")
        self.assertEqual(receipt["blocking_finding_count"], 0)
        self.assertEqual(receipt["remediation_commit_a"], IMPLEMENTATION_A)
        self.assertEqual(receipt["remediation_commit_b"], IMPLEMENTATION_B)
        self.assertEqual(receipt["remediation_source_manifest_hash"], SOURCE_MANIFEST_HASH)
        report_sha256 = hashlib.sha256(
            _git_bytes(
                AUDIT_B,
                "docs/task_reports/TASK-039E3_R2R_LIVE_EXECUTOR_AUDIT_REPORT.md",
            )
        ).hexdigest()
        self.assertEqual(report_sha256, receipt["report_sha256"])
        bundle_payload = {
            "task_id": "TASK-039E3-R2R-LIVE-EXECUTOR-INDEPENDENT-AUDIT",
            "audit_commit_a": AUDIT_A,
            "remediation_commit_a": IMPLEMENTATION_A,
            "remediation_commit_b": IMPLEMENTATION_B,
            "remediation_source_manifest_hash": SOURCE_MANIFEST_HASH,
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
            "forensic_receipt_hash": FORENSIC_RECEIPT_HASH,
            "failed_execution_receipt_hash": FAILED_EXECUTION_RECEIPT_HASH,
            "component_artifact_hashes": receipt["component_artifact_hashes"],
            "report_sha256": report_sha256,
        }
        self.assertEqual(stable_hash_v1(bundle_payload), AUDIT_BUNDLE_HASH)

    def test_schema_and_upstream_governance_receipts_are_immutable(self) -> None:
        self.assertEqual(
            SCHEMA_PATH.read_bytes(),
            _git_bytes(
                BASE,
                "schemas/v6/task039e3_r2r_execution_authorization_v1_schema.json",
            ),
        )
        checks = {
            "docs/task_reports/TASK-039E3_R2R_LIVE_EXECUTOR_REMEDIATION_RECEIPT.json": (
                "73b67d8f2cb144379ecc745b15f64d25ce18cfd79eadf03a16d30c626935eebc"
            ),
            "docs/task_reports/TASK-039E3_R2R_FAILURE_FORENSIC_RECEIPT.json": (
                FORENSIC_RECEIPT_HASH
            ),
            "docs/task_reports/TASK-039E3_R2_SCIENTIFIC_RECOVERY_PROTOCOL_RECEIPT.json": (
                "2d65919dced159c2e584b4c5347dc2f4a3f8fd0d35323322d68014d2843f1168"
            ),
        }
        for path, exact_hash in checks.items():
            with self.subTest(path=path):
                artifact = _verified_json_bytes((ROOT / path).read_bytes())
                self.assertEqual(artifact["artifact_hash"], exact_hash)

    def test_complete_source_manifest_reproduces_50_exact_git_records(self) -> None:
        manifest = _verified_json_bytes(_git_bytes(IMPLEMENTATION_B, SOURCE_MANIFEST_PATH))
        self.assertEqual(manifest["artifact_hash"], SOURCE_MANIFEST_HASH)
        self.assertEqual(manifest["described_commit"], IMPLEMENTATION_A)
        self.assertEqual(manifest["material_path_count"], 49)
        self.assertEqual(manifest["source_record_count"], 50)
        self.assertEqual(manifest["unbound_material_project_local_dependency_count"], 0)
        self.assertEqual(manifest["dynamic_imports_found"], False)
        self.assertEqual(manifest["unresolved_project_local_imports"], [])
        self.assertEqual(manifest["unresolved_dynamic_imports"], 0)
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

    def test_old_authorization_is_unchanged_consumed_and_partial_state_unusable(self) -> None:
        old_raw = OLD_AUTHORIZATION_PATH.read_bytes()
        self.assertEqual(
            old_raw,
            _git_bytes(BASE, "docs/task_reports/TASK-039E3_R2R_EXECUTION_AUTHORIZATION.json"),
        )
        old = _verified_json_bytes(old_raw)
        self.assertEqual(old["self_hash"], OLD_AUTHORIZATION_HASH)
        self.assertIs(self.configuration["predecessor_authorization_reusable"], False)
        self.assertIs(self.configuration["failed_r2r_partial_t0_reusable"], False)
        forensic = _verified_json_bytes(
            (ROOT / "docs/task_reports/TASK-039E3_R2R_FAILURE_FORENSIC_RECEIPT.json").read_bytes()
        )
        self.assertEqual(forensic["artifact_hash"], FORENSIC_RECEIPT_HASH)
        self.assertEqual(forensic["failed_execution_receipt_hash"], FAILED_EXECUTION_RECEIPT_HASH)
        self.assertIs(forensic["scientific_result_evaluable"], False)
        self.assertIs(forensic["authorization_reusable"], False)

    def test_grants_prohibitions_and_capability_accounting_are_exact(self) -> None:
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
            mutated = dict(self.authorization)
            mutated[field] = True
            mutated.pop("self_hash")
            mutated["self_hash"] = stable_hash_v1(mutated)
            with self.assertRaises(TASK039E3R2RAuthorizationError):
                validate_r2r_authorization_v1(mutated)
        self.assertEqual(self.configuration["capability_probes_current"], 2)
        self.assertEqual(self.configuration["capability_probes_maximum"], 2)
        self.assertEqual(self.configuration["additional_capability_probes"], 0)

    def test_governance_artifacts_are_sanitized_and_provider_free(self) -> None:
        combined = CONFIGURATION_PATH.read_text(encoding="utf-8") + AUTHORIZATION_PATH.read_text(encoding="utf-8")
        for prohibited in (
            "Authorization:",
            "Bearer ",
            "C:\\Users\\",
            "e1-private-root",
            "recovery-private-root",
        ):
            self.assertNotIn(prohibited, combined)
        tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
        imported_roots = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in (
                node.names
                if isinstance(node, ast.Import)
                else [ast.alias(name=node.module or "")]
            )
        }
        self.assertTrue(
            imported_roots.isdisjoint({"urllib", "requests", "httpx", "socket"})
        )


if __name__ == "__main__":
    unittest.main()
