from __future__ import annotations

from dataclasses import replace
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from paperworks.v6.task039e3_r2r_authorization_v1 import (
    DIRECT_NUMBER_PROMPT_HASH,
    DIRECT_NUMBER_SCHEMA_HASH,
    EXACT_ENDPOINT,
    EXACT_MODEL,
    MAIN_PROMPT_HASH,
    RECOVERY_SCHEMA_V2_HASH,
    RELATION_SCHEDULE_HASH,
    T2_FOLLOWUP_PROMPT_HASH,
)
from paperworks.v6.task039e3_r2r_precontact_v1 import (
    GuardedR2RRootsV1,
    R2RLivePathDependenciesV1,
    R2RObservedIntegrityStateV1,
    R2RPostContactIntegrityGuardV1,
    R2RSourceBlobIdentityV1,
    R2R_SCIENTIFIC_ACCOUNTING_BEHAVIOR_HASH_V1,
    TASK039E3R2RPrecontactError,
    capture_r2r_integrity_snapshot_v1,
    run_r2r_live_execution_path_v1,
    validate_r2r_execution_roots_v1,
)
from paperworks.v6.task039e3_r2r_execution_v1 import R2R_ARM_RUNNERS_V1
from paperworks.v6.task039e3_r2r_failure_finalizer_v1 import (
    TASK039E3R2RFailureReceiptDoubleFault,
    TASK039E3R2RGuardedExecutionFailure,
)
from paperworks.v6.task039e3_r2r_live_execution_v1 import (
    _failure_provider_observation,
    _postcontact_failure_integrity_status,
    build_r2r_live_dependencies_v1,
)
from paperworks.v6.task039e3_r2r_request_contract_v1 import (
    DIRECT_NUMBER_SCHEMA_POLICY,
    build_r2r_main_request_v1,
    build_r2r_t2_followup_request_v1,
)


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_task039e3_r2r_scientific_execution_v1.py"


def _integrity_state() -> R2RObservedIntegrityStateV1:
    return R2RObservedIntegrityStateV1(
        execution_commit="a" * 40,
        source_manifest_hash="1" * 64,
        source_blobs=(R2RSourceBlobIdentityV1("runner.py", "b" * 40, "2" * 64),),
        authorization_hash="3" * 64,
        recovery_main_provider_schema_v2_hash=RECOVERY_SCHEMA_V2_HASH,
        main_prompt_hash=MAIN_PROMPT_HASH,
        t2_followup_prompt_hash=T2_FOLLOWUP_PROMPT_HASH,
        direct_number_prompt_hash=DIRECT_NUMBER_PROMPT_HASH,
        direct_number_schema_hash=DIRECT_NUMBER_SCHEMA_HASH,
        exact_model=EXACT_MODEL,
        endpoint=EXACT_ENDPOINT,
        sampling_configuration_hash="4" * 64,
        timeout_seconds=30.0,
        retry_policy_hash="5" * 64,
        relation_schedule_hash=RELATION_SCHEDULE_HASH,
        scientific_concurrency=1,
        scientific_call_budget_hash="6" * 64,
        scientific_accounting_behavior_hash=R2R_SCIENTIFIC_ACCOUNTING_BEHAVIOR_HASH_V1,
        recovery_execution_configuration_hash="7" * 64,
    )


class R2RLiveRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        base = Path(self.temporary.name)
        self.paths = {name: base / name for name in ("repo", "e1", "cap", "recovery", "public")}
        for path in self.paths.values():
            path.mkdir()
        self.roots = validate_r2r_execution_roots_v1(
            repository_root=self.paths["repo"],
            e1_private_root=self.paths["e1"],
            capability_ledger_root=self.paths["cap"],
            recovery_private_root=self.paths["recovery"],
            public_output_root=self.paths["public"],
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _dependencies(
        self,
        events: list[str],
        credential_calls: list[int],
        *,
        fail_stage: str | None = None,
    ) -> R2RLivePathDependenciesV1:
        def step(name: str, value: object):
            def invoke(*_args):
                events.append(name)
                if fail_stage == name:
                    raise TASK039E3R2RPrecontactError(name)
                return value

            return invoke

        baseline = _integrity_state()
        snapshot = capture_r2r_integrity_snapshot_v1(baseline)
        integrity_guard = R2RPostContactIntegrityGuardV1(snapshot, lambda: baseline)

        def credential() -> str:
            credential_calls.append(1)
            events.append("credential")
            return "synthetic-secret-never-persisted"

        return R2RLivePathDependenciesV1(
            authorization_guard=step("authorization", "auth"),
            git_source_manifest_guard=step("git_source", "git"),
            forensic_protocol_guard=step("forensic_protocol", "forensic"),
            capability_reuse_guard=step("capability_reuse", "capability"),
            execution_root_guard=step("roots", self.roots),
            fresh_ledger_guard=step("fresh_ledgers", "four-empty-ledgers"),
            integrity_snapshot_guard=step("integrity", integrity_guard),
            credential_loader=credential,
            transport_factory=step("transport", "transport"),
            e1_loader=step("e1", "evidence"),
            scientific_runner=step("science", "science-result"),
            success_finalizer=step("success_finalizer", {"status": "PASS"}),
            failure_finalizer=step("failure_finalizer", None),
        )

    def test_every_precontact_failure_precedes_credential_boundary(self) -> None:
        for failed in (
            "authorization",
            "git_source",
            "forensic_protocol",
            "capability_reuse",
            "roots",
            "fresh_ledgers",
            "integrity",
        ):
            with self.subTest(failed=failed):
                events: list[str] = []
                credential_calls: list[int] = []
                with self.assertRaises(TASK039E3R2RPrecontactError):
                    run_r2r_live_execution_path_v1(
                        self._dependencies(
                            events, credential_calls, fail_stage=failed
                        )
                    )
                self.assertEqual(credential_calls, [])
                self.assertNotIn("e1", events)
                self.assertNotIn("transport", events)

    def test_success_has_one_credential_lookup_and_fresh_ledgers_before_e1(self) -> None:
        events: list[str] = []
        credential_calls: list[int] = []
        result = run_r2r_live_execution_path_v1(
            self._dependencies(events, credential_calls)
        )
        self.assertEqual(credential_calls, [1])
        self.assertEqual(result.capability_probe_calls, 0)
        self.assertEqual(result.historical_partial_records_reused, 0)
        self.assertLess(events.index("capability_reuse"), events.index("roots"))
        self.assertLess(events.index("fresh_ledgers"), events.index("credential"))
        self.assertLess(events.index("fresh_ledgers"), events.index("e1"))
        self.assertLess(events.index("integrity"), events.index("credential"))
        self.assertEqual(events[-1], "success_finalizer")

    def test_root_guard_rejects_nesting_and_nonempty_fresh_roots(self) -> None:
        nested = self.paths["recovery"] / "nested"
        nested.mkdir()
        with self.assertRaises(TASK039E3R2RPrecontactError):
            validate_r2r_execution_roots_v1(
                repository_root=self.paths["repo"],
                e1_private_root=self.paths["e1"],
                capability_ledger_root=self.paths["cap"],
                recovery_private_root=self.paths["recovery"],
                public_output_root=nested,
            )

    def test_integrity_mutation_blocks_the_next_provider_attempt(self) -> None:
        baseline = _integrity_state()
        mutations = {
            "source_manifest_hash": "8" * 64,
            "source_blobs": (R2RSourceBlobIdentityV1("runner.py", "b" * 40, "9" * 64),),
            "authorization_hash": "a" * 64,
            "recovery_main_provider_schema_v2_hash": "b" * 64,
            "main_prompt_hash": "c" * 64,
            "t2_followup_prompt_hash": "d" * 64,
            "direct_number_prompt_hash": "e" * 64,
            "direct_number_schema_hash": "f" * 64,
            "exact_model": "wrong-model",
            "endpoint": "https://invalid.example",
            "sampling_configuration_hash": "0" * 64,
            "timeout_seconds": 31.0,
            "retry_policy_hash": "1" * 64,
            "relation_schedule_hash": "2" * 64,
            "scientific_concurrency": 2,
            "scientific_call_budget_hash": "3" * 64,
            "scientific_accounting_behavior_hash": "4" * 64,
            "recovery_execution_configuration_hash": "5" * 64,
        }
        for field, changed in mutations.items():
            with self.subTest(field=field):
                mutable = {"state": baseline}
                guard = R2RPostContactIntegrityGuardV1(
                    capture_r2r_integrity_snapshot_v1(baseline),
                    lambda: mutable["state"],
                )
                attempts: list[int] = []
                guard.invoke_guarded_provider_attempt(lambda: attempts.append(1))
                mutable["state"] = replace(baseline, **{field: changed})
                with self.assertRaises(TASK039E3R2RPrecontactError):
                    guard.invoke_guarded_provider_attempt(lambda: attempts.append(1))
                mutable["state"] = baseline
                with self.assertRaises(TASK039E3R2RPrecontactError):
                    guard.invoke_guarded_provider_attempt(lambda: attempts.append(1))
                self.assertEqual(attempts, [1])

    def test_concrete_dependency_factory_is_pure_and_has_no_capability_path(self) -> None:
        arguments = type(
            "Arguments",
            (),
            {
                "repository_root": str(self.paths["repo"] / "not-opened"),
                "r2r_authorization": str(self.paths["repo"] / "authorization.json"),
                "r2r_source_manifest": str(self.paths["repo"] / "manifest.json"),
                "r2r_audit_receipt": str(self.paths["repo"] / "audit.json"),
                "capability_receipt": str(self.paths["cap"] / "receipt.json"),
                "capability_ledger_root": str(self.paths["cap"] / "ledger"),
                "e1_private_root": str(self.paths["e1"] / "private"),
                "recovery_private_root": str(self.paths["recovery"] / "fresh"),
                "public_output_root": str(self.paths["public"] / "fresh"),
            },
        )()
        dependencies = build_r2r_live_dependencies_v1(arguments)
        self.assertEqual(
            set(R2RLivePathDependenciesV1.__dataclass_fields__),
            set(dependencies.__dataclass_fields__),
        )
        self.assertFalse(
            any("capability" in name and "reuse" not in name for name in dependencies.__dict__)
        )

    def test_postcredential_failure_is_terminal_and_double_fault_is_distinct(self) -> None:
        events: list[str] = []
        credentials: list[int] = []
        dependencies = self._dependencies(events, credentials, fail_stage="science")
        with self.assertRaises(TASK039E3R2RGuardedExecutionFailure) as observed:
            run_r2r_live_execution_path_v1(dependencies)
        self.assertEqual(observed.exception.failure_receipt, None)
        self.assertEqual(credentials, [1])
        self.assertEqual(events.count("failure_finalizer"), 1)

        failing_writer = replace(
            self._dependencies([], []),
            scientific_runner=lambda *_args: (_ for _ in ()).throw(RuntimeError("science")),
            failure_finalizer=lambda *_args: (_ for _ in ()).throw(OSError("custody")),
        )
        with self.assertRaises(TASK039E3R2RFailureReceiptDoubleFault):
            run_r2r_live_execution_path_v1(failing_writer)

    def test_failure_projection_preserves_provider_identity_and_rechecks_integrity(self) -> None:
        record = SimpleNamespace(
            slot=SimpleNamespace(to_dict=lambda: {"arm": "T1", "call_number": 1}),
            provider_response_metadata={"model": "unexpected", "response_id": "response-1"},
            terminal_slot_state="completed_model_identity_mismatch",
        )
        projected = _failure_provider_observation((record,))
        self.assertEqual(projected["actual_returned_model"], "unexpected")
        self.assertEqual(projected["actual_response_id"], "response-1")
        self.assertEqual(
            projected["terminal_slot_state"], "completed_model_identity_mismatch"
        )

        baseline = _integrity_state()
        mutable = {"state": baseline}
        guard = R2RPostContactIntegrityGuardV1(
            capture_r2r_integrity_snapshot_v1(baseline), lambda: mutable["state"]
        )
        transport = SimpleNamespace(calls=1)
        self.assertEqual(
            _postcontact_failure_integrity_status(transport, guard),
            "verified_unchanged",
        )
        mutable["state"] = replace(baseline, exact_model="changed")
        self.assertEqual(
            _postcontact_failure_integrity_status(transport, guard),
            "integrity_changed_blocked",
        )
        self.assertEqual(
            _postcontact_failure_integrity_status(SimpleNamespace(calls=0), guard),
            "integrity_changed_blocked",
        )

    def test_runner_keeps_offline_self_check_and_exposes_future_arguments(self) -> None:
        spec = importlib.util.spec_from_file_location("r2r_c1_runner", RUNNER)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        output = io.StringIO()
        with patch("sys.stdout", output):
            self.assertEqual(module.main(["--offline-self-check"]), 0)
        self.assertIn('"provider_contact_authorized":false', output.getvalue())
        source = RUNNER.read_text(encoding="utf-8")
        self.assertEqual(source.count('os.environ.get("OPENAI_API_KEY")'), 1)
        for argument in (
            "--repository-root",
            "--r2r-authorization",
            "--r2r-source-manifest",
            "--capability-receipt",
            "--capability-ledger-root",
            "--e1-private-root",
            "--recovery-private-root",
            "--public-output-root",
        ):
            self.assertIn(argument, source)

        events: list[str] = []
        ignored_dependency_credential_calls: list[int] = []
        runner_credential_calls: list[int] = []
        dependencies = self._dependencies(events, ignored_dependency_credential_calls)
        arguments: list[str] = []
        for name, path in (
            ("--repository-root", self.paths["repo"]),
            ("--r2r-authorization", self.paths["repo"] / "authorization.json"),
            ("--r2r-source-manifest", self.paths["repo"] / "manifest.json"),
            ("--r2r-audit-receipt", self.paths["repo"] / "audit.json"),
            ("--capability-receipt", self.paths["cap"] / "receipt.json"),
            ("--capability-ledger-root", self.paths["cap"]),
            ("--e1-private-root", self.paths["e1"]),
            ("--recovery-private-root", self.paths["recovery"]),
            ("--public-output-root", self.paths["public"]),
        ):
            arguments.extend((name, str(path)))

        def sentinel() -> str:
            runner_credential_calls.append(1)
            return "synthetic-sentinel"

        with (
            patch.object(module, "_credential_loader_v1", sentinel),
            patch("sys.stdout", io.StringIO()),
        ):
            self.assertEqual(
                module.main(
                    arguments,
                    live_dependencies_factory=lambda _args: dependencies,
                ),
                0,
            )
        self.assertEqual(runner_credential_calls, [1])
        self.assertEqual(ignored_dependency_credential_calls, [])

    def test_no_capability_probe_or_transport_dependency_exists(self) -> None:
        fields = set(R2RLivePathDependenciesV1.__dataclass_fields__)
        self.assertFalse(
            fields
            & {
                "capability_probe",
                "capability_request_builder",
                "capability_transport",
            }
        )

    def test_live_science_seam_reuses_r2r_v2_and_direct_v1(self) -> None:
        self.assertEqual(DIRECT_NUMBER_SCHEMA_POLICY, "UNCHANGED")
        self.assertEqual(
            build_r2r_main_request_v1.__module__,
            "paperworks.v6.task039e3_r2r_request_contract_v1",
        )
        self.assertEqual(
            build_r2r_t2_followup_request_v1.__module__,
            "paperworks.v6.task039e3_r2r_request_contract_v1",
        )
        self.assertIsNot(R2R_ARM_RUNNERS_V1.t1, R2R_ARM_RUNNERS_V1.t1b)
        self.assertIsNot(R2R_ARM_RUNNERS_V1.t1b, R2R_ARM_RUNNERS_V1.t2)
        self.assertEqual(
            R2R_ARM_RUNNERS_V1.direct_number.__name__, "run_direct_number_v1"
        )


if __name__ == "__main__":
    unittest.main()
