"""Independent complete-manifest post-contact mutation oracle."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6 import task039e3_recovery_integrity_v3 as integrity


ROOT = Path(__file__).resolve().parents[1]
R1D2_A = "2653f2b7349a049f9ca4828d736dfea9462c4748"
SF1_B = "5296cf7a054d4fc3bbfdf742b70585bc0dc90515"
MANIFEST_PATH = (
    "docs/task_reports/TASK-039E3_R1D2_SF1_COMPLETE_SOURCE_FREEZE.json"
)
PREVIOUSLY_OMITTED = {
    "src/paperworks/__init__.py",
    "src/paperworks/data/__init__.py",
    "src/paperworks/data/contracts.py",
    "src/paperworks/data/contracts_v2.py",
    "src/paperworks/data/files.py",
    "src/paperworks/data/official_swat.py",
    "src/paperworks/data/splits.py",
    "src/paperworks/data/splits_v2.py",
    "src/paperworks/data/staging_swat.py",
    "src/paperworks/metadata/__init__.py",
    "src/paperworks/metadata/schema.py",
    "src/paperworks/v6/__init__.py",
    "src/paperworks/v6/adapters_v1.py",
    "src/paperworks/v6/candidate_discovery_protocol_v1.py",
    "src/paperworks/v6/common.py",
    "src/paperworks/v6/continuous_step_protocol_v1.py",
    "src/paperworks/v6/detector_context_v1.py",
    "src/paperworks/v6/normal_evidence_v1.py",
    "src/paperworks/v6/outcomes_v1.py",
    "src/paperworks/v6/schema_registry_v1.py",
    "src/paperworks/v6/task039e0_rule_construction_prep_v1.py",
    "src/paperworks/v6/task039e0_validity_v1.py",
    "src/paperworks/v6/task039e2_execution_configuration_v1.py",
    "src/paperworks/v6/task039e3_live_transport_v1.py",
    "src/paperworks/v6/task039e3_recovery_authorization_v1.py",
}
REPRESENTATIVE_OMISSIONS = {
    "common": "src/paperworks/v6/common.py",
    "e2_configuration": (
        "src/paperworks/v6/task039e2_execution_configuration_v1.py"
    ),
    "retry_after_helper": "src/paperworks/v6/task039e3_live_transport_v1.py",
    "v1_root_validator": (
        "src/paperworks/v6/task039e3_recovery_authorization_v1.py"
    ),
}


def _git_bytes(*arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _manifest() -> dict[str, object]:
    return json.loads(_git_bytes("show", f"{SF1_B}:{MANIFEST_PATH}"))


def _initial_state() -> integrity.ObservedExecutionIntegrityStateV3:
    manifest = _manifest()
    records = manifest["source_records"]
    assert isinstance(records, list)
    blobs = tuple(
        integrity.FrozenSourceBlobV3(
            repository_path=str(record["repository_path"]),
            git_blob_sha=str(record["git_blob_sha"]),
            sha256=str(record["sha256"]),
        )
        for record in records
    )
    return integrity.build_frozen_execution_integrity_state_v3(
        head_commit=R1D2_A,
        source_manifest_hash=str(manifest["artifact_hash"]),
        source_blobs=blobs,
        scientific_accounting_behavior_hash=hashlib.sha256(
            b"independent-rerun-accounting-behavior"
        ).hexdigest(),
        r2_authorization_hash=hashlib.sha256(
            b"independent-rerun-synthetic-authorization"
        ).hexdigest(),
    )


def _assert_postcontact_rejection(
    test: unittest.TestCase,
    initial: integrity.ObservedExecutionIntegrityStateV3,
    mutated: integrity.ObservedExecutionIntegrityStateV3,
) -> None:
    holder = {"state": initial}
    guard = integrity.PostContactIntegrityGuardV3(
        snapshot=integrity.capture_execution_integrity_snapshot_v3(initial),
        observed_state_loader=lambda: holder["state"],
    )
    test.assertEqual(
        guard.execute_provider_attempt(lambda: "synthetic-provider-response"),
        "synthetic-provider-response",
    )
    holder["state"] = mutated
    with test.assertRaises(integrity.TASK039E3RecoveryIntegrityV3Error):
        guard.assert_before_terminal_pass()
    next_attempts: list[str] = []
    with test.assertRaisesRegex(
        integrity.TASK039E3RecoveryIntegrityV3Error,
        "permanently blocked",
    ):
        guard.execute_provider_attempt(lambda: next_attempts.append("forbidden"))
    test.assertEqual(next_attempts, [])
    test.assertTrue(guard.blocked)
    test.assertEqual(guard.postcontact_integrity_status, "failed_changed")
    test.assertFalse(guard.automatic_resume_authorized)
    test.assertFalse(guard.provider_recontact_authorized)


class R1D2AuditRerunPostContactIntegrityTests(unittest.TestCase):
    def test_all_41_complete_manifest_records_are_integrity_bound(self) -> None:
        initial = _initial_state()
        self.assertEqual(len(initial.source_blobs), 41)
        for index, blob in enumerate(initial.source_blobs):
            for field, value in (
                ("git_blob_sha", "f" * 40),
                ("sha256", "f" * 64),
            ):
                with self.subTest(path=blob.repository_path, field=field):
                    changed = list(initial.source_blobs)
                    changed[index] = replace(blob, **{field: value})
                    _assert_postcontact_rejection(
                        self,
                        initial,
                        replace(initial, source_blobs=tuple(changed)),
                    )

    def test_all_25_previously_omitted_dependencies_are_now_detected(self) -> None:
        initial = _initial_state()
        by_path = {blob.repository_path: blob for blob in initial.source_blobs}
        self.assertEqual(len(PREVIOUSLY_OMITTED), 25)
        self.assertTrue(PREVIOUSLY_OMITTED.issubset(by_path))
        detected: set[str] = set()
        for path in sorted(PREVIOUSLY_OMITTED):
            with self.subTest(path=path):
                changed = tuple(
                    replace(blob, sha256="e" * 64)
                    if blob.repository_path == path
                    else blob
                    for blob in initial.source_blobs
                )
                _assert_postcontact_rejection(
                    self, initial, replace(initial, source_blobs=changed)
                )
                detected.add(path)
        self.assertEqual(detected, PREVIOUSLY_OMITTED)
        self.assertEqual(
            {name: path in detected for name, path in REPRESENTATIVE_OMISSIONS.items()},
            {name: True for name in REPRESENTATIVE_OMISSIONS},
        )

    def test_every_configuration_family_is_bound_and_blocks_recontact(self) -> None:
        initial = _initial_state()
        sampling = dict(initial.sampling_configuration)
        sampling["temperature"] = 0.8
        retry_policy = dict(initial.retry_policy)
        retry_policy["maximum_transport_retries_per_request"] = 3
        call_budget = dict(initial.scientific_call_budget)
        call_budget["maximum_scientific_logical_calls"] = 337
        mutations = {
            "head": replace(initial, head_commit="f" * 40),
            "source_manifest": replace(initial, source_manifest_hash="f" * 64),
            "model": replace(initial, exact_model="gpt-mutated"),
            "prompt": replace(initial, capability_prompt_hash="f" * 64),
            "schema": replace(initial, capability_schema_hash="f" * 64),
            "sampling": replace(
                initial,
                sampling_configuration=sampling,
                sampling_configuration_hash=stable_hash_v1(sampling),
            ),
            "timeout": replace(initial, urlopen_timeout_seconds=31.0),
            "retry_waits": replace(initial, retry_wait_seconds=(3, 4)),
            "retry_policy": replace(
                initial,
                retry_policy=retry_policy,
                retry_policy_hash=stable_hash_v1(retry_policy),
            ),
            "schedule": replace(initial, relation_schedule_hash="f" * 64),
            "concurrency": replace(initial, scientific_concurrency=2),
            "call_budget": replace(
                initial,
                scientific_call_budget=call_budget,
                scientific_call_budget_hash=stable_hash_v1(call_budget),
            ),
            "accounting": replace(
                initial, scientific_accounting_behavior_hash="f" * 64
            ),
            "authorization": replace(initial, r2_authorization_hash="f" * 64),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name):
                _assert_postcontact_rejection(self, initial, mutation)

    def test_mutation_during_attempt_is_detected_before_any_next_attempt(self) -> None:
        initial = _initial_state()
        holder = {"state": initial}
        guard = integrity.PostContactIntegrityGuardV3(
            snapshot=integrity.capture_execution_integrity_snapshot_v3(initial),
            observed_state_loader=lambda: holder["state"],
        )

        def synthetic_attempt() -> str:
            holder["state"] = replace(initial, urlopen_timeout_seconds=31.0)
            return "synthetic-provider-response"

        with self.assertRaisesRegex(
            integrity.TASK039E3RecoveryIntegrityV3Error,
            "after_provider_attempt",
        ):
            guard.execute_provider_attempt(synthetic_attempt)
        self.assertEqual(guard.provider_attempts_started, 1)
        self.assertTrue(guard.blocked)
        subsequent: list[str] = []
        with self.assertRaisesRegex(
            integrity.TASK039E3RecoveryIntegrityV3Error,
            "permanently blocked",
        ):
            guard.execute_provider_attempt(lambda: subsequent.append("forbidden"))
        self.assertEqual(subsequent, [])


if __name__ == "__main__":
    unittest.main()
