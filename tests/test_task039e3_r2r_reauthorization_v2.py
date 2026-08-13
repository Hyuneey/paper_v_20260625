"""Offline runner-consumable V2 reauthorization and precredential oracles."""

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
from paperworks.v6.task039e3_r2r_capability_reuse_v1 import (
    validate_capability_reuse_v1,
)
from paperworks.v6.task039e3_r2r_live_execution_v1 import (
    build_r2r_live_dependencies_v1,
)
from paperworks.v6.task039e3_r2r_precontact_v1 import (
    GuardedR2RRootsV1,
    TASK039E3R2RGuardedExecutionFailure,
    run_r2r_live_execution_path_v1,
)
from tests.test_task039e3_r2r_execution_v1 import _ledger, _receipt


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_A = "f10365adbdde5bb2070df429770174d215829dc6"
IMPLEMENTATION_B = "067dcffc441170064180c677b0bd7845a93ce5ef"
SOURCE_MANIFEST_HASH = (
    "a58b5e3480fb7d1b88029cf2c2ff018cfdaae84be3a5861299eed003c13ad235"
)
BRIDGE_B = "498f0dc96483649a9fb0d4affb1ad351d067a9d0"
BRIDGE_BUNDLE = "a9198642c04883dad793075ebf57e971f0f2ee58f468f35485186f204d064754"
CANONICAL_RECEIPT_HASH = (
    "f8ce7dc61f1ebcb17c4ddda95e915e21140049ac5958c34843228970db318009"
)
CONFIGURATION_HASH = (
    "df5afd183de0c4f453f2a8e93c50fe43847fbd85154aa44a380a62dbdab6e593"
)
AUTHORIZATION_HASH = (
    "ce5ef3e3d4d737721b53fdb2ec43d116d93eeb4bd1471dd6fc4f5c0f7e306b8f"
)
SUPERSEDED_HASH = (
    "cf24208fbd12f4a1b54425640bb370de9f781b222224545b8cfbd1670c1aba06"
)
CONFIGURATION_PATH = (
    ROOT / "docs/task_reports/TASK-039E3_R2R_REEXECUTION_CONFIGURATION_V2.json"
)
AUTHORIZATION_PATH = (
    ROOT / "docs/task_reports/TASK-039E3_R2R_REEXECUTION_AUTHORIZATION_V2.json"
)
SUPERSEDED_PATH = (
    ROOT / "docs/task_reports/TASK-039E3_R2R_REEXECUTION_AUTHORIZATION.json"
)
SCHEMA_PATH = (
    ROOT / "schemas/v6/task039e3_r2r_execution_authorization_v1_schema.json"
)
SOURCE_MANIFEST_PATH = (
    "docs/task_reports/"
    "TASK-039E3_R2R_LIVE_EXECUTOR_REMEDIATION_SOURCE_FREEZE.json"
)
CANONICAL_RECEIPT_PATH = (
    "docs/task_reports/TASK-039E3_R2R_AUDIT_RECEIPT.json"
)


def _git_bytes(commit: str, path: str, *, cwd: Path = ROOT) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
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


class R2RReauthorizationV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.configuration = json.loads(CONFIGURATION_PATH.read_text(encoding="utf-8"))
        self.authorization = json.loads(AUTHORIZATION_PATH.read_text(encoding="utf-8"))
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_configuration_and_superseded_unexecuted_authority(self) -> None:
        content = dict(self.configuration)
        claimed = content.pop("artifact_hash")
        self.assertEqual(claimed, CONFIGURATION_HASH)
        self.assertEqual(stable_hash_v1(content), CONFIGURATION_HASH)
        expected = {
            "audit_authority_bridge_commit_b": BRIDGE_B,
            "audit_authority_bridge_bundle_hash": BRIDGE_BUNDLE,
            "canonical_audit_receipt_hash": CANONICAL_RECEIPT_HASH,
            "implementation_commit_a": IMPLEMENTATION_A,
            "implementation_commit_b": IMPLEMENTATION_B,
            "implementation_source_manifest_hash": SOURCE_MANIFEST_HASH,
            "predecessor_reauthorization_hash": SUPERSEDED_HASH,
            "predecessor_reauthorization_state": (
                "SUPERSEDED_UNEXECUTED_AUTHORITY_CONTRACT_MISMATCH"
            ),
            "predecessor_reauthorization_invoked": False,
            "predecessor_reauthorization_usable": False,
            "failed_r2r_partial_t0_reusable": False,
            "additional_capability_probes": 0,
            "capability_probes_current": 2,
            "capability_probes_maximum": 2,
        }
        for key, exact in expected.items():
            self.assertEqual(self.configuration[key], exact, key)
        superseded = _verified(SUPERSEDED_PATH.read_bytes(), "self_hash")
        self.assertEqual(superseded["self_hash"], SUPERSEDED_HASH)
        self.assertEqual(
            SUPERSEDED_PATH.read_bytes(),
            _git_bytes(BRIDGE_B, "docs/task_reports/TASK-039E3_R2R_REEXECUTION_AUTHORIZATION.json"),
        )

    def test_authorization_v2_closed_schema_native_validator_and_bridge_binding(self) -> None:
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
        self.assertEqual(
            self.authorization["recovery_execution_configuration_hash"],
            CONFIGURATION_HASH,
        )

    def test_grants_prohibitions_and_failed_partial_boundary(self) -> None:
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
        self.assertIs(self.configuration["failed_r2r_partial_t0_reusable"], False)

    def test_bridge_receipt_exact_git_bytes_and_source_manifest(self) -> None:
        bridge = _verified(_git_bytes(BRIDGE_B, CANONICAL_RECEIPT_PATH), "artifact_hash")
        self.assertEqual(bridge["artifact_hash"], CANONICAL_RECEIPT_HASH)
        self.assertEqual(bridge["audit_bundle_hash"], BRIDGE_BUNDLE)
        self.assertEqual(bridge["implementation_commit_a"], IMPLEMENTATION_A)
        self.assertEqual(bridge["implementation_source_manifest_hash"], SOURCE_MANIFEST_HASH)
        manifest = _verified(_git_bytes(IMPLEMENTATION_B, SOURCE_MANIFEST_PATH), "artifact_hash")
        self.assertEqual(manifest["artifact_hash"], SOURCE_MANIFEST_HASH)
        self.assertEqual(manifest["described_commit"], IMPLEMENTATION_A)
        self.assertEqual(manifest["source_record_count"], 50)
        for record in manifest["source_records"]:
            exact = _git_bytes(IMPLEMENTATION_A, record["repository_path"])
            blob = subprocess.run(
                ["git", "rev-parse", f"{IMPLEMENTATION_A}:{record['repository_path']}"],
                cwd=ROOT,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).stdout.strip()
            self.assertEqual(blob, record["git_blob_sha"])
            self.assertEqual(hashlib.sha256(exact).hexdigest(), record["sha256"])

    def test_actual_precredential_path_reaches_sentinel_after_audit_guard(self) -> None:
        execution_text = os.environ.get("TASK039E3_EXACT_F103_REPO")
        commit_c = os.environ.get("TASK039E3_REAUTHORIZATION_COMMIT_C")
        if not execution_text or not commit_c:
            self.skipTest("exact Commit-C/execution topology required")
        execution = Path(execution_text)
        self.assertEqual(
            subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=execution,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).stdout.strip(),
            IMPLEMENTATION_A,
        )
        with tempfile.TemporaryDirectory() as temporary:
            external = Path(temporary)
            authorization_path = external / "authorization.json"
            manifest_path = external / "manifest.json"
            audit_path = external / "audit.json"
            authorization_path.write_bytes(
                _git_bytes(
                    commit_c,
                    "docs/task_reports/TASK-039E3_R2R_REEXECUTION_AUTHORIZATION_V2.json",
                )
            )
            manifest_path.write_bytes(_git_bytes(IMPLEMENTATION_B, SOURCE_MANIFEST_PATH))
            audit_path.write_bytes(_git_bytes(BRIDGE_B, CANONICAL_RECEIPT_PATH))
            role_paths = [external / f"role_{index}" for index in range(5)]
            for path in role_paths:
                path.mkdir()
            args = SimpleNamespace(
                repository_root=str(execution),
                r2r_authorization=str(authorization_path),
                r2r_source_manifest=str(manifest_path),
                r2r_audit_receipt=str(audit_path),
                capability_receipt=str(role_paths[0] / "unused.json"),
                capability_ledger_root=str(role_paths[1]),
                e1_private_root=str(role_paths[2]),
                recovery_private_root=str(role_paths[3]),
                public_output_root=str(role_paths[4]),
            )
            dependencies = build_r2r_live_dependencies_v1(args)
            capability_calls: list[int] = []
            credential_calls: list[int] = []
            transport_calls: list[int] = []
            stages: list[str] = []
            roots = GuardedR2RRootsV1(
                repository_root=execution,
                e1_private_root=role_paths[2],
                capability_ledger_root=role_paths[1],
                recovery_private_root=role_paths[3],
                public_output_root=role_paths[4],
            )

            def synthetic_capability(_authorization: object) -> object:
                capability_calls.append(1)
                return validate_capability_reuse_v1(
                    private_capability_receipt=_receipt(),
                    ledger_observation=_ledger(),
                )

            def sentinel_credential() -> str:
                credential_calls.append(1)
                return "synthetic-sentinel-not-a-real-key"

            def stop_transport(*_arguments: object) -> object:
                transport_calls.append(1)
                raise _SentinelTransportStop("stop after precredential guards")

            guarded = replace(
                dependencies,
                capability_reuse_guard=synthetic_capability,
                execution_root_guard=lambda: roots,
                credential_loader=sentinel_credential,
                transport_factory=stop_transport,
                failure_finalizer=lambda failure, _roots: {
                    "status": type(failure).__name__
                },
            )
            with self.assertRaises(TASK039E3R2RGuardedExecutionFailure):
                run_r2r_live_execution_path_v1(guarded, stage_sink=stages.append)
            self.assertEqual(capability_calls, [1])
            self.assertEqual(credential_calls, [1])
            self.assertEqual(transport_calls, [1])
            self.assertEqual(
                stages,
                [
                    "authorization_validated",
                    "git_and_source_manifest_validated",
                    "forensic_and_protocol_authority_validated",
                    "durable_capability_pass_reused",
                    "execution_roots_validated",
                    "fresh_empty_ledgers_validated_before_e1",
                    "postcontact_integrity_snapshot_prepared",
                    "sole_credential_lookup_completed",
                ],
            )


if __name__ == "__main__":
    unittest.main()
