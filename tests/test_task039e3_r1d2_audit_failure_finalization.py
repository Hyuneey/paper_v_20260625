from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from paperworks.v6.task039e3_recovery_execution_v3 import (
    FAILURE_STATUS,
    TASK039E3RecoveryFailureReceiptDoubleFaultV3Error,
    TASK039E3RecoveryGuardedExecutionFailureV3Error,
    run_guarded_execution_v3,
    write_terminal_failure_receipt_v3,
)


_FAILURE_STAGES = (
    "before_e1_load",
    "during_t0",
    "during_t1",
    "during_t1b",
    "during_t2",
    "during_direct_number",
    "provider_custody_finalization",
    "proposal_outcome_direct_snapshot_finalization",
    "metrics_finalization",
    "public_artifact_finalization",
    "execution_receipt_finalization",
)

_FORBIDDEN_MARKERS = (
    "synthetic-api-key-never-persist",
    "Authorization",
    "Bearer ",
    "chain-of-thought",
    "raw-e1-evidence",
    "raw-proposal-text",
)


class InjectedPostContactFailure(RuntimeError):
    pass


def _independent_hash(document: dict[str, object]) -> str:
    content = {key: value for key, value in document.items() if key != "artifact_hash"}
    canonical = json.dumps(
        content,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(canonical).hexdigest()


def _failure_context() -> dict[str, object]:
    return {
        "execution_commit": "a" * 40,
        "source_manifest_hash": "b" * 64,
        "authorization_hash": "c" * 64,
        "configuration_fingerprint": "d" * 64,
        "capability_gate_status": "PASS",
        "capability_provider_ledger_head_hash": "e" * 64,
        "scientific_provider_ledger_head_hash": "f" * 64,
        "last_completed_scientific_slot": {
            "relation_identity": "synthetic-relation-17",
            "arm": "T1-B",
            "local_call_index": 2,
        },
        "completed_scientific_logical_calls": 103,
        "scientific_transport_attempts": 104,
        "proposal_committed_count": 103,
        "outcome_committed_count": 84,
        "direct_number_committed_count": 16,
        "postcontact_integrity_status": "verified_unchanged",
    }


class R1D2AuditFailureFinalizationTests(unittest.TestCase):
    def test_every_required_postcontact_stage_leaves_a_durable_sanitized_receipt(self) -> None:
        for stage in _FAILURE_STAGES:
            with self.subTest(stage=stage), TemporaryDirectory() as temporary:
                destination = Path(temporary) / "terminal-failure.json"
                calls = {"execute": 0, "finalize": 0, "provider_recontact": 0}

                def execute() -> object:
                    calls["execute"] += 1
                    if stage not in {
                        "metrics_finalization",
                        "public_artifact_finalization",
                        "execution_receipt_finalization",
                    }:
                        raise InjectedPostContactFailure(
                            "synthetic-api-key-never-persist raw-e1-evidence raw-proposal-text"
                        )
                    return {"synthetic_science": "complete"}

                def finalize(_result: object) -> object:
                    calls["finalize"] += 1
                    raise InjectedPostContactFailure(
                        "Bearer synthetic-api-key-never-persist chain-of-thought"
                    )

                def writer(**kwargs: object) -> dict[str, object]:
                    return write_terminal_failure_receipt_v3(
                        destination=destination, **kwargs  # type: ignore[arg-type]
                    )

                with self.assertRaises(
                    TASK039E3RecoveryGuardedExecutionFailureV3Error
                ) as raised:
                    run_guarded_execution_v3(
                        provider_contact_started=True,
                        execution_stage=stage,
                        execute_science=execute,
                        finalize_success=finalize,
                        failure_receipt_writer=writer,
                        failure_context=_failure_context,
                    )

                self.assertEqual(calls["execute"], 1)
                self.assertLessEqual(calls["finalize"], 1)
                self.assertEqual(calls["provider_recontact"], 0)
                self.assertTrue(destination.is_file())
                disk = json.loads(destination.read_text(encoding="utf-8"))
                self.assertEqual(disk, raised.exception.failure_receipt)
                self.assertEqual(disk["status"], FAILURE_STATUS)
                self.assertEqual(disk["failure_stage"], stage)
                self.assertEqual(
                    disk["failure_classification"], "InjectedPostContactFailure"
                )
                self.assertEqual(disk["artifact_hash"], _independent_hash(disk))
                self.assertIs(disk["automatic_resume_authorized"], False)
                self.assertIs(disk["provider_recontact_authorized"], False)
                self.assertIs(disk["rule_v2_authorized"], False)
                self.assertIs(disk["runtime_authority"], False)
                self.assertIs(disk["utility_evaluation_authorized"], False)
                self.assertEqual(disk["completed_scientific_logical_calls"], 103)
                self.assertEqual(disk["scientific_transport_attempts"], 104)
                self.assertEqual(disk["proposal_committed_count"], 103)
                self.assertEqual(disk["outcome_committed_count"], 84)
                self.assertEqual(disk["direct_number_committed_count"], 16)
                rendered = destination.read_text(encoding="utf-8")
                for marker in _FORBIDDEN_MARKERS:
                    self.assertNotIn(marker, rendered)

    def test_failure_receipt_contains_the_required_reconstruction_bindings(self) -> None:
        required = {
            "failure_stage",
            "failure_classification",
            "execution_commit",
            "source_manifest_hash",
            "authorization_hash",
            "configuration_fingerprint",
            "capability_gate_status",
            "capability_provider_ledger_head_hash",
            "scientific_provider_ledger_head_hash",
            "last_completed_scientific_slot",
            "completed_scientific_logical_calls",
            "scientific_transport_attempts",
            "proposal_committed_count",
            "outcome_committed_count",
            "direct_number_committed_count",
            "postcontact_integrity_status",
            "automatic_resume_authorized",
            "provider_recontact_authorized",
        }
        with TemporaryDirectory() as temporary:
            receipt = write_terminal_failure_receipt_v3(
                destination=Path(temporary) / "failure.json",
                failure_stage="during_t2",
                failure=InjectedPostContactFailure("secret message is not authoritative"),
                context=_failure_context(),
            )
        self.assertTrue(required.issubset(receipt))
        self.assertIs(receipt["error_message_persisted"], False)
        self.assertIs(receipt["credential_persisted"], False)
        self.assertIs(receipt["authorization_header_persisted"], False)
        self.assertIs(receipt["raw_private_evidence_persisted"], False)
        self.assertIs(receipt["chain_of_thought_persisted"], False)

    def test_double_fault_is_distinct_and_can_never_return_pass(self) -> None:
        provider_calls = 0
        persistence_calls = 0

        def fail_science() -> object:
            nonlocal provider_calls
            provider_calls += 1
            raise InjectedPostContactFailure("ordinary-science-failure")

        def fail_persistence(**_kwargs: object) -> dict[str, object]:
            nonlocal persistence_calls
            persistence_calls += 1
            raise OSError("synthetic-storage-unavailable")

        with self.assertRaises(
            TASK039E3RecoveryFailureReceiptDoubleFaultV3Error
        ) as raised:
            run_guarded_execution_v3(
                provider_contact_started=True,
                execution_stage="during_t1",
                execute_science=fail_science,
                finalize_success=lambda _result: {"status": "PASS"},
                failure_receipt_writer=fail_persistence,
                failure_context=_failure_context(),
            )
        self.assertEqual(provider_calls, 1)
        self.assertEqual(persistence_calls, 1)
        self.assertEqual(
            raised.exception.failure_classification,
            "double_fault_failure_receipt_persistence_failed",
        )
        self.assertIsInstance(raised.exception.original_failure, InjectedPostContactFailure)
        self.assertIsInstance(raised.exception.persistence_failure, OSError)
        self.assertNotIn("PASS", str(raised.exception))

    def test_precontact_failure_does_not_create_false_postcontact_custody(self) -> None:
        writer_calls = 0

        def writer(**_kwargs: object) -> dict[str, object]:
            nonlocal writer_calls
            writer_calls += 1
            return {"status": FAILURE_STATUS}

        with self.assertRaises(InjectedPostContactFailure):
            run_guarded_execution_v3(
                provider_contact_started=False,
                execution_stage="before_provider_contact",
                execute_science=lambda: (_ for _ in ()).throw(
                    InjectedPostContactFailure("precontact")
                ),
                finalize_success=lambda result: result,
                failure_receipt_writer=writer,
                failure_context=_failure_context(),
            )
        self.assertEqual(writer_calls, 0)


if __name__ == "__main__":
    unittest.main()
