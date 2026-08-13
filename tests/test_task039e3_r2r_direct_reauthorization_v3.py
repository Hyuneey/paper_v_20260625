"""Offline runner-consumable V3 reauthorization and precredential oracles."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_authorization_v1 import (
    TASK039E3R2RAuthorizationError,
    validate_r2r_authorization_v1,
)
from paperworks.v6.task039e3_r2r_capability_reuse_v1 import validate_capability_reuse_v1
from paperworks.v6.task039e3_r2r_live_execution_v1 import build_r2r_live_dependencies_v1
from paperworks.v6.task039e3_r2r_precontact_v1 import (
    GuardedR2RRootsV1,
    R2RPostContactIntegrityGuardV1,
    R2R_SCIENTIFIC_ACCOUNTING_BEHAVIOR_HASH_V1,
    TASK039E3R2RGuardedExecutionFailure,
    TASK039E3R2RPrecontactError,
    capture_r2r_integrity_snapshot_v1,
    run_r2r_live_execution_path_v1,
)
from tests.test_task039e3_r2r_accounting_independent_audit import _integrity_state
from tests.test_task039e3_r2r_execution_v1 import _ledger, _receipt


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_A = "5dca2d0431d60ef2f2bdfc907ebfe3fe18521f16"
IMPLEMENTATION_B = "d511372db560fd2cf27c2d56db7c637a3324584f"
SOURCE_MANIFEST_HASH = "9037fda0bc7694fd643058a9779fb919c75664824f2f11c49dde9f4be1b209b8"
BRIDGE_B = "6f83362a09db02c1665dd75b654b09be59b8851b"
BRIDGE_BUNDLE = "6504e699583b433ff5df6cd60ce67b6d892a44d441e71acab2d0ceddfff47137"
CANONICAL_RECEIPT_HASH = "9aed9c6dd2a9e9d1985f2bcd734d27cf7cd594855feb46e41823fefc8dd52e5b"
CONFIGURATION_HASH = "23d69dfe21dd7d170d1791c1c18f63adcfa3661e32c9aee76ec9aa69952ca982"
AUTHORIZATION_HASH = "4d3dda2ab78edfff5768218905aefbb6864348e7d4471270dcb6187b59499db5"
CONSUMED_V2_HASH = "ce5ef3e3d4d737721b53fdb2ec43d116d93eeb4bd1471dd6fc4f5c0f7e306b8f"
SUPERSEDED_HASH = "cf24208fbd12f4a1b54425640bb370de9f781b222224545b8cfbd1670c1aba06"
NEW_ACCOUNTING_HASH = "0e18526c8dbcaec26d67385b89c60826dc4388cac08727cd61a2c60b1b812ae2"
OLD_ACCOUNTING_HASH = "efa52c6125ffe72d4660b52c1b45951151d679df205d8b365a11019463a925f9"
CONFIGURATION_PATH = ROOT / "docs/task_reports/TASK-039E3_R2R_REEXECUTION_CONFIGURATION_V3.json"
AUTHORIZATION_PATH = ROOT / "docs/task_reports/TASK-039E3_R2R_REEXECUTION_AUTHORIZATION_V3.json"
CONSUMED_V2_PATH = ROOT / "docs/task_reports/TASK-039E3_R2R_REEXECUTION_AUTHORIZATION_V2.json"
SUPERSEDED_PATH = ROOT / "docs/task_reports/TASK-039E3_R2R_REEXECUTION_AUTHORIZATION.json"
SCHEMA_PATH = ROOT / "schemas/v6/task039e3_r2r_execution_authorization_v1_schema.json"
SOURCE_MANIFEST_PATH = "docs/task_reports/TASK-039E3_R2R_DIRECT_NUMBER_RENDERING_REMEDIATION_SOURCE_FREEZE.json"
CANONICAL_RECEIPT_PATH = "docs/task_reports/TASK-039E3_R2R_AUDIT_RECEIPT.json"


def _git_bytes(commit: str, path: str, *, cwd: Path = ROOT) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"], cwd=cwd, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout


def _verified(raw: bytes, key: str) -> dict[str, object]:
    document = json.loads(raw)
    claimed = document[key]
    payload = dict(document)
    payload.pop(key)
    if stable_hash_v1(payload) != claimed:
        raise AssertionError(f"{key} mismatch")
    return document


class _SentinelTransportStop(RuntimeError):
    pass


class R2RDirectReauthorizationV3Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.configuration = json.loads(CONFIGURATION_PATH.read_text(encoding="utf-8"))
        self.authorization = json.loads(AUTHORIZATION_PATH.read_text(encoding="utf-8"))
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_configuration_historical_accounting_and_disclosure_boundary(self) -> None:
        content = dict(self.configuration)
        claimed = content.pop("artifact_hash")
        self.assertEqual(claimed, CONFIGURATION_HASH)
        self.assertEqual(stable_hash_v1(content), CONFIGURATION_HASH)
        expected = {
            "execution_event": "R2R_FRESH_REEXECUTION_AFTER_DIRECT_NUMBER_RENDERING_REMEDIATION",
            "execution_mode": "FRESH_FULL_COHORT_RESTART",
            "implementation_commit_a": IMPLEMENTATION_A,
            "implementation_commit_b": IMPLEMENTATION_B,
            "implementation_source_manifest_hash": SOURCE_MANIFEST_HASH,
            "independent_audit_commit_b": BRIDGE_B,
            "independent_audit_bundle_hash": BRIDGE_BUNDLE,
            "independent_audit_receipt_hash": CANONICAL_RECEIPT_HASH,
            "historical_original_r2_scientific_logical_calls": 1,
            "historical_zero_contact_r2r_scientific_logical_calls": 0,
            "historical_partial_r2_scientific_logical_calls": 5,
            "historical_scientific_logical_calls_total": 6,
            "fresh_r2r_scientific_logical_calls_minimum": 252,
            "fresh_r2r_scientific_logical_calls_maximum": 336,
            "lifetime_scientific_logical_calls_minimum": 258,
            "lifetime_scientific_logical_calls_maximum": 342,
            "scientific_accounting_behavior_hash": NEW_ACCOUNTING_HASH,
            "predecessor_authorization_v2_hash": CONSUMED_V2_HASH,
            "predecessor_authorization_v2_state": "CONSUMED_NON_REUSABLE",
            "predecessor_authorization_v2_reusable": False,
            "external_disclosure_approval_required_before_runner_invocation": True,
            "prior_one_shot_external_disclosure_approval_reusable": False,
        }
        for key, exact in expected.items():
            self.assertEqual(self.configuration[key], exact, key)
        self.assertEqual(_verified(CONSUMED_V2_PATH.read_bytes(), "self_hash")["self_hash"], CONSUMED_V2_HASH)
        self.assertEqual(_verified(SUPERSEDED_PATH.read_bytes(), "self_hash")["self_hash"], SUPERSEDED_HASH)

    def test_authorization_v3_closed_schema_native_validator_and_bridge_binding(self) -> None:
        self.assertIs(self.schema["additionalProperties"], False)
        self.assertEqual(set(self.schema["properties"]), set(self.schema["required"]))
        self.assertEqual(set(self.authorization), set(self.schema["required"]))
        content = dict(self.authorization)
        claimed = content.pop("self_hash")
        self.assertEqual(claimed, AUTHORIZATION_HASH)
        self.assertEqual(stable_hash_v1(content), AUTHORIZATION_HASH)
        validated = validate_r2r_authorization_v1(self.authorization)
        self.assertEqual(validated.self_hash, AUTHORIZATION_HASH)
        self.assertEqual(validated.implementation_commit_a, IMPLEMENTATION_A)
        self.assertEqual(validated.implementation_commit_b, IMPLEMENTATION_B)
        self.assertEqual(validated.implementation_source_manifest_hash, SOURCE_MANIFEST_HASH)
        self.assertEqual(validated.independent_audit_commit_b, BRIDGE_B)
        self.assertEqual(validated.independent_audit_bundle_hash, BRIDGE_BUNDLE)
        self.assertEqual(validated.independent_audit_receipt_hash, CANONICAL_RECEIPT_HASH)
        self.assertEqual(self.authorization["recovery_execution_configuration_hash"], CONFIGURATION_HASH)
        self.assertEqual(self.authorization["historical_aborted_r2_scientific_logical_calls"], 1)

    def test_grants_and_every_closed_prohibition(self) -> None:
        for field in ("capability_reuse_authorized", "provider_contact_authorized", "scientific_execution_authorized"):
            self.assertIs(self.authorization[field], True, field)
        prohibited = (
            "capability_probe_authorized", "provider_diagnostic_call_authorized",
            "resume_authorized", "historical_partial_result_reuse_authorized",
            "rule_v2_authorized", "runtime_authority",
            "utility_evaluation_authorized", "winner_selected",
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

    def test_bridge_exact_git_bytes_and_all_fifty_source_records(self) -> None:
        bridge = _verified(_git_bytes(BRIDGE_B, CANONICAL_RECEIPT_PATH), "artifact_hash")
        self.assertEqual(bridge["artifact_hash"], CANONICAL_RECEIPT_HASH)
        self.assertEqual(bridge["audit_bundle_hash"], BRIDGE_BUNDLE)
        self.assertEqual(bridge["implementation_commit_a"], IMPLEMENTATION_A)
        manifest = _verified(_git_bytes(IMPLEMENTATION_B, SOURCE_MANIFEST_PATH), "artifact_hash")
        self.assertEqual(manifest["artifact_hash"], SOURCE_MANIFEST_HASH)
        self.assertEqual(manifest["described_commit"], IMPLEMENTATION_A)
        self.assertEqual(manifest["source_record_count"], 50)
        for record in manifest["source_records"]:
            exact = _git_bytes(IMPLEMENTATION_A, record["repository_path"])
            blob = subprocess.run(
                ["git", "rev-parse", f"{IMPLEMENTATION_A}:{record['repository_path']}"],
                cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).stdout.strip()
            self.assertEqual(blob, record["git_blob_sha"])
            self.assertEqual(hashlib.sha256(exact).hexdigest(), record["sha256"])

    def test_new_accounting_hash_is_integrity_bound_and_old_hash_rejected(self) -> None:
        self.assertEqual(R2R_SCIENTIFIC_ACCOUNTING_BEHAVIOR_HASH_V1, NEW_ACCOUNTING_HASH)
        state = _integrity_state(NEW_ACCOUNTING_HASH)
        snapshot = capture_r2r_integrity_snapshot_v1(state)
        guard = R2RPostContactIntegrityGuardV1(snapshot, lambda: state)
        guard.assert_unchanged_before_provider_attempt()
        old_state = replace(state, scientific_accounting_behavior_hash=OLD_ACCOUNTING_HASH)
        old_guard = R2RPostContactIntegrityGuardV1(snapshot, lambda: old_state)
        with self.assertRaises(TASK039E3R2RPrecontactError):
            old_guard.assert_unchanged_before_provider_attempt()
        self.assertTrue(old_guard.blocked)

    def test_actual_precredential_path_reaches_sentinel_after_all_public_guards(self) -> None:
        execution_text = os.environ.get("TASK039E3_EXACT_5DCA_REPO")
        commit_c = os.environ.get("TASK039E3_DIRECT_REAUTHORIZATION_COMMIT_C")
        if not execution_text or not commit_c:
            self.skipTest("exact Commit-C/execution topology required")
        execution = Path(execution_text)
        self.assertEqual(
            subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=execution, check=True,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            ).stdout.strip(), IMPLEMENTATION_A,
        )
        with tempfile.TemporaryDirectory() as temporary:
            external = Path(temporary)
            authorization_path = external / "authorization.json"
            manifest_path = external / "manifest.json"
            audit_path = external / "audit.json"
            authorization_path.write_bytes(_git_bytes(commit_c, "docs/task_reports/TASK-039E3_R2R_REEXECUTION_AUTHORIZATION_V3.json"))
            manifest_path.write_bytes(_git_bytes(IMPLEMENTATION_B, SOURCE_MANIFEST_PATH))
            audit_path.write_bytes(_git_bytes(BRIDGE_B, CANONICAL_RECEIPT_PATH))
            role_paths = [external / f"role_{index}" for index in range(5)]
            for path in role_paths:
                path.mkdir()
            args = SimpleNamespace(
                repository_root=str(execution), r2r_authorization=str(authorization_path),
                r2r_source_manifest=str(manifest_path), r2r_audit_receipt=str(audit_path),
                capability_receipt=str(role_paths[0] / "unused.json"),
                capability_ledger_root=str(role_paths[1]), e1_private_root=str(role_paths[2]),
                recovery_private_root=str(role_paths[3]), public_output_root=str(role_paths[4]),
            )
            dependencies = build_r2r_live_dependencies_v1(args)
            capability_calls: list[int] = []
            credential_calls: list[int] = []
            transport_calls: list[int] = []
            stages: list[str] = []
            roots = GuardedR2RRootsV1(
                repository_root=execution, e1_private_root=role_paths[2],
                capability_ledger_root=role_paths[1], recovery_private_root=role_paths[3],
                public_output_root=role_paths[4],
            )

            def synthetic_capability(_authorization: object) -> object:
                capability_calls.append(1)
                return validate_capability_reuse_v1(private_capability_receipt=_receipt(), ledger_observation=_ledger())

            def sentinel_credential() -> str:
                credential_calls.append(1)
                return "synthetic-sentinel-not-a-real-key"

            def stop_transport(*_arguments: object) -> object:
                transport_calls.append(1)
                raise _SentinelTransportStop("stop after precredential guards")

            guarded = replace(
                dependencies, capability_reuse_guard=synthetic_capability,
                execution_root_guard=lambda: roots, credential_loader=sentinel_credential,
                transport_factory=stop_transport,
                failure_finalizer=lambda failure, _roots: {"status": type(failure).__name__},
            )
            with self.assertRaises(TASK039E3R2RGuardedExecutionFailure):
                run_r2r_live_execution_path_v1(guarded, stage_sink=stages.append)
            self.assertEqual(capability_calls, [1])
            self.assertEqual(credential_calls, [1])
            self.assertEqual(transport_calls, [1])
            self.assertEqual(stages, [
                "authorization_validated", "git_and_source_manifest_validated",
                "forensic_and_protocol_authority_validated", "durable_capability_pass_reused",
                "execution_roots_validated", "fresh_empty_ledgers_validated_before_e1",
                "postcontact_integrity_snapshot_prepared", "sole_credential_lookup_completed",
            ])


if __name__ == "__main__":
    unittest.main()
