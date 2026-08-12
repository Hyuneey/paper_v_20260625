"""Offline mutation oracle for the TASK-039E3 R1D2 integrity guard."""

from __future__ import annotations

from dataclasses import replace
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_recovery_integrity_v3 import (
    EXACT_MODEL,
    EXECUTION_SCHEDULE_HASH,
    FROZEN_RETRY_POLICY_HASH_V3,
    FROZEN_RETRY_POLICY_V3,
    FROZEN_SAMPLING_CONFIGURATION_HASH_V3,
    FROZEN_SAMPLING_CONFIGURATION_V3,
    FROZEN_SCIENTIFIC_CALL_BUDGET_HASH_V3,
    FROZEN_SCIENTIFIC_CALL_BUDGET_V3,
    FrozenSourceBlobV3,
    ObservedExecutionIntegrityStateV3,
    PostContactIntegrityGuardV3,
    RECOVERY_CAPABILITY_PROMPT_SHA256,
    RECOVERY_CAPABILITY_SCHEMA_SHA256,
    TASK039E3RecoveryIntegrityV3Error,
    build_frozen_execution_integrity_state_v3,
    capture_execution_integrity_snapshot_v3,
    git_blob_sha1_v3,
)


_COMMIT = "a" * 40
_MANIFEST = "b" * 64
_AUTHORIZATION = "c" * 64
_ACCOUNTING_BEHAVIOR = "d" * 64


def _state(**changes: object) -> ObservedExecutionIntegrityStateV3:
    values: dict[str, object] = {
        "head_commit": _COMMIT,
        "source_manifest_hash": _MANIFEST,
        "source_blobs": (
            FrozenSourceBlobV3.from_bytes("src/example_a.py", b"a = 1\n"),
            FrozenSourceBlobV3.from_bytes("src/example_b.py", b"b = 2\n"),
        ),
        "exact_model": EXACT_MODEL,
        "capability_prompt_hash": RECOVERY_CAPABILITY_PROMPT_SHA256,
        "capability_schema_hash": RECOVERY_CAPABILITY_SCHEMA_SHA256,
        "sampling_configuration": FROZEN_SAMPLING_CONFIGURATION_V3,
        "sampling_configuration_hash": FROZEN_SAMPLING_CONFIGURATION_HASH_V3,
        "urlopen_timeout_seconds": 30.0,
        "retry_wait_seconds": (2, 4),
        "retry_policy": FROZEN_RETRY_POLICY_V3,
        "retry_policy_hash": FROZEN_RETRY_POLICY_HASH_V3,
        "relation_schedule_hash": EXECUTION_SCHEDULE_HASH,
        "scientific_concurrency": 1,
        "scientific_call_budget": FROZEN_SCIENTIFIC_CALL_BUDGET_V3,
        "scientific_call_budget_hash": FROZEN_SCIENTIFIC_CALL_BUDGET_HASH_V3,
        "scientific_accounting_behavior_hash": _ACCOUNTING_BEHAVIOR,
        "r2_authorization_hash": _AUTHORIZATION,
    }
    values.update(changes)
    return ObservedExecutionIntegrityStateV3(**values)  # type: ignore[arg-type]


class R1D2PostContactIntegrityV3Tests(unittest.TestCase):
    def test_snapshot_is_deterministic_and_binds_every_required_family(self) -> None:
        observed = _state()
        snapshot_a = capture_execution_integrity_snapshot_v3(observed)
        snapshot_b = capture_execution_integrity_snapshot_v3(_state())
        self.assertEqual(
            snapshot_a.execution_configuration_fingerprint,
            snapshot_b.execution_configuration_fingerprint,
        )
        document = snapshot_a.to_dict()
        self.assertEqual(document["head_commit"], _COMMIT)
        self.assertEqual(document["source_manifest_hash"], _MANIFEST)
        self.assertEqual(len(document["source_blobs"]), 2)
        self.assertEqual(document["exact_model"], EXACT_MODEL)
        self.assertEqual(document["capability_prompt_hash"], RECOVERY_CAPABILITY_PROMPT_SHA256)
        self.assertEqual(document["capability_schema_hash"], RECOVERY_CAPABILITY_SCHEMA_SHA256)
        self.assertEqual(document["sampling_configuration_hash"], FROZEN_SAMPLING_CONFIGURATION_HASH_V3)
        self.assertEqual(document["urlopen_timeout_seconds"], 30.0)
        self.assertEqual(document["retry_wait_seconds"], [2, 4])
        self.assertEqual(document["retry_policy_hash"], FROZEN_RETRY_POLICY_HASH_V3)
        self.assertEqual(
            FROZEN_RETRY_POLICY_HASH_V3,
            "3a7192d07ef4980c9ecaeb3f28fe00f31df8c299a177d86250f5ebd09f1c477b",
        )
        self.assertEqual(document["relation_schedule_hash"], EXECUTION_SCHEDULE_HASH)
        self.assertEqual(document["scientific_concurrency"], 1)
        self.assertEqual(document["scientific_call_budget_hash"], FROZEN_SCIENTIFIC_CALL_BUDGET_HASH_V3)
        self.assertEqual(document["scientific_accounting_behavior_hash"], _ACCOUNTING_BEHAVIOR)
        self.assertEqual(document["r2_authorization_hash"], _AUTHORIZATION)

    def test_frozen_state_factory_exposes_only_runtime_bindings(self) -> None:
        state = build_frozen_execution_integrity_state_v3(
            head_commit=_COMMIT,
            source_manifest_hash=_MANIFEST,
            source_blobs=_state().source_blobs,
            scientific_accounting_behavior_hash=_ACCOUNTING_BEHAVIOR,
            r2_authorization_hash=_AUTHORIZATION,
        )
        self.assertEqual(
            state.execution_configuration_fingerprint,
            _state().execution_configuration_fingerprint,
        )

    def test_git_blob_id_and_source_order_are_exact_and_canonical(self) -> None:
        content = b"print('synthetic')\n"
        record = FrozenSourceBlobV3.from_bytes("src/test.py", content)
        self.assertEqual(record.git_blob_sha, git_blob_sha1_v3(content))
        reversed_state = _state(
            source_blobs=tuple(reversed(_state().source_blobs))
        )
        self.assertEqual(
            [item.repository_path for item in reversed_state.source_blobs],
            ["src/example_a.py", "src/example_b.py"],
        )
        with self.assertRaises(TASK039E3RecoveryIntegrityV3Error):
            FrozenSourceBlobV3.from_bytes("../escape.py", content)

    def test_non_frozen_initial_configuration_is_rejected_precontact(self) -> None:
        cases = (
            {"exact_model": "gpt-different"},
            {"urlopen_timeout_seconds": 30},
            {"urlopen_timeout_seconds": 31.0},
            {"retry_wait_seconds": (1, 4)},
            {"relation_schedule_hash": "1" * 64},
            {"scientific_concurrency": 2},
        )
        for mutation in cases:
            with self.subTest(mutation=mutation):
                with self.assertRaises(TASK039E3RecoveryIntegrityV3Error):
                    capture_execution_integrity_snapshot_v3(_state(**mutation))

    def test_every_postcontact_source_and_configuration_mutation_blocks(self) -> None:
        changed_sampling = dict(FROZEN_SAMPLING_CONFIGURATION_V3)
        changed_sampling["temperature"] = 0.8
        changed_budget = dict(FROZEN_SCIENTIFIC_CALL_BUDGET_V3)
        changed_budget["maximum_scientific_logical_calls"] = 337
        mutations = {
            "source_bytes": lambda current: replace(
                current,
                source_blobs=(
                    FrozenSourceBlobV3.from_bytes("src/example_a.py", b"a = 9\n"),
                    current.source_blobs[1],
                ),
            ),
            "source_manifest": lambda current: replace(
                current, source_manifest_hash="1" * 64
            ),
            "timeout": lambda current: replace(current, urlopen_timeout_seconds=31.0),
            "model": lambda current: replace(current, exact_model="gpt-different"),
            "prompt": lambda current: replace(
                current, capability_prompt_hash="2" * 64
            ),
            "schema": lambda current: replace(
                current, capability_schema_hash="3" * 64
            ),
            "sampling": lambda current: replace(
                current,
                sampling_configuration=changed_sampling,
                sampling_configuration_hash=stable_hash_v1(changed_sampling),
            ),
            "schedule": lambda current: replace(
                current, relation_schedule_hash="4" * 64
            ),
            "accounting_behavior": lambda current: replace(
                current, scientific_accounting_behavior_hash="5" * 64
            ),
            "call_budget": lambda current: replace(
                current,
                scientific_call_budget=changed_budget,
                scientific_call_budget_hash=stable_hash_v1(changed_budget),
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(mutation=name):
                holder = {"state": _state()}
                guard = PostContactIntegrityGuardV3(
                    snapshot=capture_execution_integrity_snapshot_v3(holder["state"]),
                    observed_state_loader=lambda: holder["state"],
                )
                self.assertEqual(guard.execute_provider_attempt(lambda: "synthetic-response"), "synthetic-response")
                holder["state"] = mutate(holder["state"])
                with self.assertRaises(TASK039E3RecoveryIntegrityV3Error):
                    guard.assert_before_scientific_phase()
                called = False

                def forbidden_recontact() -> None:
                    nonlocal called
                    called = True

                with self.assertRaises(TASK039E3RecoveryIntegrityV3Error):
                    guard.execute_provider_attempt(forbidden_recontact)
                self.assertFalse(called)
                self.assertTrue(guard.blocked)
                self.assertFalse(guard.automatic_resume_authorized)
                self.assertFalse(guard.provider_recontact_authorized)
                self.assertEqual(guard.provider_attempts_started, 1)
                self.assertEqual(guard.postcontact_integrity_status, "failed_changed")

    def test_mutation_inside_synthetic_attempt_is_detected_immediately_after(self) -> None:
        holder = {"state": _state()}
        guard = PostContactIntegrityGuardV3(
            snapshot=capture_execution_integrity_snapshot_v3(holder["state"]),
            observed_state_loader=lambda: holder["state"],
        )

        def synthetic_attempt() -> str:
            holder["state"] = replace(
                holder["state"], urlopen_timeout_seconds=31.0
            )
            return "synthetic-provider-response"

        with self.assertRaisesRegex(
            TASK039E3RecoveryIntegrityV3Error, "after_provider_attempt"
        ):
            guard.execute_provider_attempt(synthetic_attempt)
        self.assertTrue(guard.blocked)
        self.assertEqual(guard.failure_stage, "after_provider_attempt")

    def test_all_later_phase_boundaries_revalidate_the_snapshot(self) -> None:
        holder = {"state": _state()}
        guard = PostContactIntegrityGuardV3(
            snapshot=capture_execution_integrity_snapshot_v3(holder["state"]),
            observed_state_loader=lambda: holder["state"],
        )
        guard.execute_provider_attempt(lambda: "synthetic-response")
        self.assertEqual(guard.assert_before_e1_access(), "verified_unchanged")
        self.assertEqual(guard.assert_before_scientific_phase(), "verified_unchanged")
        self.assertEqual(guard.assert_at_relation_boundary(), "verified_unchanged")
        self.assertEqual(guard.assert_before_metrics_finalization(), "verified_unchanged")
        self.assertEqual(guard.assert_before_public_finalization(), "verified_unchanged")
        self.assertEqual(guard.assert_before_terminal_pass(), "verified_unchanged")
        self.assertEqual(guard.provider_attempts_started, 1)
        self.assertEqual(guard.postcontact_integrity_status, "verified_unchanged")
        self.assertEqual(
            guard.execution_configuration_fingerprint,
            capture_execution_integrity_snapshot_v3(
                holder["state"]
            ).execution_configuration_fingerprint,
        )

    def test_terminal_pass_requires_contact_and_loader_failure_is_permanent(self) -> None:
        state = _state()
        guard = PostContactIntegrityGuardV3(
            snapshot=capture_execution_integrity_snapshot_v3(state),
            observed_state_loader=lambda: state,
        )
        with self.assertRaisesRegex(
            TASK039E3RecoveryIntegrityV3Error, "provider-contact boundary"
        ):
            guard.assert_before_terminal_pass()

        broken = PostContactIntegrityGuardV3(
            snapshot=capture_execution_integrity_snapshot_v3(state),
            observed_state_loader=lambda: (_ for _ in ()).throw(OSError("synthetic")),
        )
        with self.assertRaisesRegex(
            TASK039E3RecoveryIntegrityV3Error, "state reconstruction failed"
        ):
            broken.assert_integrity("synthetic_loader_failure")
        with self.assertRaisesRegex(
            TASK039E3RecoveryIntegrityV3Error, "permanently blocked"
        ):
            broken.assert_integrity("second_check")

    def test_provider_exception_is_preserved_when_integrity_is_unchanged(self) -> None:
        state = _state()
        guard = PostContactIntegrityGuardV3(
            snapshot=capture_execution_integrity_snapshot_v3(state),
            observed_state_loader=lambda: state,
        )

        def synthetic_failure() -> None:
            raise TimeoutError("synthetic provider timeout")

        with self.assertRaisesRegex(TimeoutError, "synthetic provider timeout"):
            guard.execute_provider_attempt(synthetic_failure)
        self.assertFalse(guard.blocked)
        self.assertEqual(guard.provider_attempts_started, 1)


if __name__ == "__main__":
    unittest.main()
