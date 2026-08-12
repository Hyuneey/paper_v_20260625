from __future__ import annotations

from functools import partial
import json
from pathlib import Path
import tempfile
import unittest

from paperworks.v6.task039e3_recovery_execution_v3 import (
    run_guarded_execution_v3,
    write_terminal_failure_receipt_v3,
)
from paperworks.v6.task039e3_recovery_serialization_v1 import (
    verify_public_artifact_v1,
)


HASH = "a" * 64
COMMIT = "b" * 40
SECRET_ERROR_TEXT = "SYNTHETIC_PRIVATE_PROPOSAL_MUST_NOT_PERSIST"
FAILURE_STAGES = (
    "before_e1_load",
    "during_t0",
    "during_t1",
    "during_t1b",
    "during_t2",
    "during_direct_number",
    "during_private_finalization",
    "during_metric_finalization",
    "during_public_artifact_finalization",
)


class SyntheticScientificFailure(RuntimeError):
    pass


def _failure_context() -> dict[str, object]:
    return {
        "execution_commit": COMMIT,
        "source_manifest_hash": HASH,
        "authorization_hash": "c" * 64,
        "configuration_fingerprint": "d" * 64,
        "capability_gate_status": "PASS",
        "capability_provider_ledger_head_hash": "e" * 64,
        "scientific_provider_ledger_head_hash": "f" * 64,
        "last_completed_scientific_slot": {
            "relation_index": 6,
            "arm": "T1",
            "local_call_index": 1,
        },
        "completed_scientific_logical_calls": 7,
        "scientific_transport_attempts": 8,
        "proposal_committed_count": 6,
        "outcome_committed_count": 5,
        "direct_number_committed_count": 4,
        "postcontact_integrity_status": "verified_unchanged",
    }


class R1D2FailureFinalizationTests(unittest.TestCase):
    def test_direct_failure_receipt_is_sanitized_atomic_and_self_hashed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "TASK-039E3_R2_EXECUTION_FAILURE.json"
            receipt = write_terminal_failure_receipt_v3(
                destination=destination,
                failure_stage="during_t2",
                failure=SyntheticScientificFailure(SECRET_ERROR_TEXT),
                context=_failure_context(),
            )
            observed = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(observed, receipt)
            verify_public_artifact_v1(observed)
            self.assertEqual(observed["status"], "failed_task039e3_r2_recovery_execution")
            self.assertEqual(observed["failure_stage"], "during_t2")
            self.assertEqual(
                observed["failure_classification"], "SyntheticScientificFailure"
            )
            self.assertFalse(observed["automatic_resume_authorized"])
            self.assertFalse(observed["provider_recontact_authorized"])
            self.assertFalse(observed["rule_v2_authorized"])
            self.assertFalse(observed["runtime_authority"])
            self.assertFalse(observed["utility_evaluation_authorized"])
            self.assertNotIn(SECRET_ERROR_TEXT, destination.read_text(encoding="utf-8"))

    def test_every_scientific_and_finalization_exception_freezes_durable_failure(self) -> None:
        for stage in FAILURE_STAGES:
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as temporary:
                destination = Path(temporary) / "failure.json"
                calls = {"science": 0, "success": 0}

                def execute_science() -> dict[str, str]:
                    calls["science"] += 1
                    if stage.startswith("during_") and stage.endswith("finalization"):
                        return {"science": "complete"}
                    raise SyntheticScientificFailure(SECRET_ERROR_TEXT)

                def finalize_success(_result: object) -> object:
                    calls["success"] += 1
                    raise SyntheticScientificFailure(SECRET_ERROR_TEXT)

                writer = partial(write_terminal_failure_receipt_v3, destination=destination)
                with self.assertRaises(Exception) as raised:
                    run_guarded_execution_v3(
                        provider_contact_started=True,
                        execution_stage=stage,
                        execute_science=execute_science,
                        finalize_success=finalize_success,
                        failure_receipt_writer=writer,
                        failure_context=_failure_context(),
                    )
                self.assertTrue(hasattr(raised.exception, "failure_receipt"))
                receipt = raised.exception.failure_receipt
                self.assertEqual(receipt["failure_stage"], stage)
                self.assertFalse(receipt["automatic_resume_authorized"])
                self.assertFalse(receipt["provider_recontact_authorized"])
                self.assertTrue(destination.is_file())
                self.assertEqual(
                    verify_public_artifact_v1(json.loads(destination.read_text(encoding="utf-8"))),
                    receipt,
                )
                self.assertEqual(calls["science"], 1)
                expected_success_calls = 1 if stage.endswith("finalization") else 0
                self.assertEqual(calls["success"], expected_success_calls)

    def test_failure_finalization_never_retries_science_or_returns_pass(self) -> None:
        attempts = 0
        receipts: list[dict[str, object]] = []

        def fail_once() -> None:
            nonlocal attempts
            attempts += 1
            raise SyntheticScientificFailure(SECRET_ERROR_TEXT)

        def writer(**kwargs: object) -> dict[str, object]:
            receipt = {
                "failure_stage": kwargs["failure_stage"],
                "automatic_resume_authorized": False,
                "provider_recontact_authorized": False,
            }
            receipts.append(receipt)
            return receipt

        with self.assertRaises(Exception) as raised:
            run_guarded_execution_v3(
                provider_contact_started=True,
                execution_stage="during_t1b",
                execute_science=fail_once,
                finalize_success=lambda _result: self.fail("PASS finalizer was reachable"),
                failure_receipt_writer=writer,
                failure_context=_failure_context(),
            )
        self.assertEqual(attempts, 1)
        self.assertEqual(len(receipts), 1)
        self.assertIs(raised.exception.failure_receipt, receipts[0])
        self.assertFalse(receipts[0]["automatic_resume_authorized"])
        self.assertFalse(receipts[0]["provider_recontact_authorized"])

    def test_precontact_exception_does_not_claim_a_postcontact_failure_receipt(self) -> None:
        writer_called = False

        def writer(**_kwargs: object) -> dict[str, object]:
            nonlocal writer_called
            writer_called = True
            return {}

        with self.assertRaises(SyntheticScientificFailure):
            run_guarded_execution_v3(
                provider_contact_started=False,
                execution_stage="precontact",
                execute_science=lambda: (_ for _ in ()).throw(
                    SyntheticScientificFailure(SECRET_ERROR_TEXT)
                ),
                finalize_success=lambda _result: self.fail("finalizer was reachable"),
                failure_receipt_writer=writer,
                failure_context=_failure_context(),
            )
        self.assertFalse(writer_called)

    def test_failure_receipt_persistence_error_is_a_distinct_double_fault(self) -> None:
        def failed_writer(**_kwargs: object) -> dict[str, object]:
            raise OSError("synthetic receipt storage unavailable")

        with self.assertRaises(Exception) as raised:
            run_guarded_execution_v3(
                provider_contact_started=True,
                execution_stage="during_direct_number",
                execute_science=lambda: (_ for _ in ()).throw(
                    SyntheticScientificFailure(SECRET_ERROR_TEXT)
                ),
                finalize_success=lambda _result: self.fail("finalizer was reachable"),
                failure_receipt_writer=failed_writer,
                failure_context=_failure_context(),
            )
        self.assertEqual(
            type(raised.exception).__name__,
            "TASK039E3RecoveryFailureReceiptDoubleFaultV3Error",
        )
        self.assertEqual(
            getattr(raised.exception, "failure_classification", None),
            "double_fault_failure_receipt_persistence_failed",
        )
        self.assertIsInstance(getattr(raised.exception, "original_failure", None), SyntheticScientificFailure)
        self.assertIsInstance(getattr(raised.exception, "persistence_failure", None), OSError)


if __name__ == "__main__":
    unittest.main()
