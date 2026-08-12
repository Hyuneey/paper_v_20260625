"""Independent post-contact integrity oracle for R1D2-AUDIT.

The positive tests prove declared/configuration mutations block.  The omitted
dependency test deliberately passes while proving the audit's blocking source-
freeze defect: mutations outside the 16-record manifest are invisible.
"""

from __future__ import annotations

from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from paperworks.v6 import task039e3_recovery_integrity_v3 as integrity


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "docs/task_reports/TASK-039E3_R1D2_SOURCE_FREEZE.json"
HEAD = "2653f2b7349a049f9ca4828d736dfea9462c4748"
HASH_A = "a" * 64


def _runner_module():
    path = ROOT / "scripts/run_task039e3_recovery_execution_v3.py"
    specification = importlib.util.spec_from_file_location("r1d2_audit_runner", path)
    if specification is None or specification.loader is None:
        raise AssertionError("V3 runner import specification unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _copy_manifest_sources(destination: Path, manifest: dict[str, object]) -> None:
    for record in manifest["source_records"]:  # type: ignore[index]
        repository_path = str(record["repository_path"])
        target = destination / repository_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / repository_path).read_bytes())


def _state_from_directory(directory: Path, manifest: dict[str, object]):
    runner = _runner_module()
    return integrity.build_frozen_execution_integrity_state_v3(
        head_commit=HEAD,
        source_manifest_hash=str(manifest["artifact_hash"]),
        source_blobs=runner._source_blobs(directory, manifest),
        scientific_accounting_behavior_hash="b" * 64,
        r2_authorization_hash="c" * 64,
    )


class R1D2AuditPostContactIntegrityTests(unittest.TestCase):
    def test_declared_source_mutation_blocks_and_prevents_next_attempt(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            _copy_manifest_sources(repository, manifest)
            loader = lambda: _state_from_directory(repository, manifest)
            guard = integrity.PostContactIntegrityGuardV3(
                snapshot=integrity.capture_execution_integrity_snapshot_v3(loader()),
                observed_state_loader=loader,
            )
            guard.execute_provider_attempt(lambda: "synthetic-provider-response")
            declared = repository / "src/paperworks/v6/task039e3_recovery_execution_v3.py"
            declared.write_bytes(declared.read_bytes() + b"\n# synthetic mutation\n")
            with self.assertRaisesRegex(
                integrity.TASK039E3RecoveryIntegrityV3Error,
                "integrity mismatch",
            ):
                guard.assert_at_relation_boundary()
            calls: list[str] = []
            with self.assertRaisesRegex(
                integrity.TASK039E3RecoveryIntegrityV3Error, "permanently blocked"
            ):
                guard.execute_provider_attempt(lambda: calls.append("attempt"))
            self.assertEqual(calls, [])

    def test_omitted_material_dependency_mutations_are_undetected_blocker(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        frozen = {record["repository_path"] for record in manifest["source_records"]}
        omitted_material = (
            "src/paperworks/v6/common.py",
            "src/paperworks/v6/task039e2_execution_configuration_v1.py",
            "src/paperworks/v6/task039e3_live_transport_v1.py",
            "src/paperworks/v6/task039e3_recovery_authorization_v1.py",
        )
        self.assertTrue(all(path not in frozen for path in omitted_material))

        for omitted in omitted_material:
            with self.subTest(omitted=omitted), tempfile.TemporaryDirectory() as temporary:
                repository = Path(temporary)
                _copy_manifest_sources(repository, manifest)
                omitted_copy = repository / omitted
                omitted_copy.parent.mkdir(parents=True, exist_ok=True)
                omitted_copy.write_bytes((ROOT / omitted).read_bytes())
                loader = lambda: _state_from_directory(repository, manifest)
                guard = integrity.PostContactIntegrityGuardV3(
                    snapshot=integrity.capture_execution_integrity_snapshot_v3(loader()),
                    observed_state_loader=loader,
                )
                guard.execute_provider_attempt(lambda: "synthetic-provider-response")
                omitted_copy.write_bytes(
                    omitted_copy.read_bytes() + b"\n# post-contact mutation\n"
                )
                # Characterizes BLOCKING incomplete_active_source_freeze: the
                # exact guard reports unchanged because this dependency was
                # omitted from its observed source_blobs.
                self.assertEqual(
                    guard.assert_at_relation_boundary(), "verified_unchanged"
                )
                self.assertFalse(guard.blocked)

    def test_configuration_and_binding_mutations_all_fail_closed(self) -> None:
        initial = integrity.build_frozen_execution_integrity_state_v3(
            head_commit=HEAD,
            source_manifest_hash=HASH_A,
            source_blobs=(
                integrity.FrozenSourceBlobV3.from_bytes(
                    "src/synthetic_active.py", b"VALUE = 1\n"
                ),
            ),
            scientific_accounting_behavior_hash="b" * 64,
            r2_authorization_hash="c" * 64,
        )
        mutations = {
            "source_manifest": {"source_manifest_hash": "d" * 64},
            "timeout": {"urlopen_timeout_seconds": 31.0},
            "model": {"exact_model": "gpt-mutated"},
            "prompt": {"capability_prompt_hash": "d" * 64},
            "schema": {"capability_schema_hash": "d" * 64},
            "sampling": {
                "sampling_configuration": {
                    **dict(initial.sampling_configuration),
                    "temperature": 0.8,
                }
            },
            "retry_policy": {
                "retry_policy": {
                    **dict(initial.retry_policy),
                    "maximum_transport_retries_per_request": 3,
                }
            },
            "schedule": {"relation_schedule_hash": "d" * 64},
            "accounting": {"scientific_accounting_behavior_hash": "d" * 64},
        }
        for name, changes in mutations.items():
            with self.subTest(name=name):
                holder = {"state": initial}
                guard = integrity.PostContactIntegrityGuardV3(
                    snapshot=integrity.capture_execution_integrity_snapshot_v3(initial),
                    observed_state_loader=lambda: holder["state"],
                )
                guard.execute_provider_attempt(lambda: "synthetic-provider-response")
                holder["state"] = replace(initial, **changes)
                with self.assertRaises(integrity.TASK039E3RecoveryIntegrityV3Error):
                    guard.assert_before_terminal_pass()
                self.assertTrue(guard.blocked)


if __name__ == "__main__":
    unittest.main()
