from __future__ import annotations

from functools import partial
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import PropertyMock, patch

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e2_execution_configuration_v1 import (
    CALIBRATED_NUMERIC_ROLES,
)
from paperworks.v6.task039e3_orchestration_v1 import (
    ConstructionOutcomeRecordV1,
    DirectNumberOutcomeV1,
)
from paperworks.v6.task039e3_r2r_capability_reuse_v1 import (
    ValidatedCapabilityReuseR2RV1,
)
from paperworks.v6.task039e3_r2r_authorization_v1 import (
    CAPABILITY_REUSE_BINDING_HASH,
)
from paperworks.v6.task039e3_r2r_failure_finalizer_v1 import (
    DOUBLE_FAULT_CLASSIFICATION,
    FAILURE_STATUS,
    TASK039E3R2RFailureReceiptDoubleFault,
    TASK039E3R2RGuardedExecutionFailure,
    run_guarded_r2r_execution_v1,
    write_terminal_failure_receipt_r2r_v1,
)
from paperworks.v6.task039e3_r2r_result_finalizer_v1 import (
    PRIVATE_ARTIFACT_NAMES_R2R_V1,
    PUBLIC_ARTIFACT_NAMES_R2R_V1,
    SUCCESS_STATUS,
    TASK039E3R2RResultFinalizationError,
    build_capability_reuse_binding_r2r_v1,
    finalize_successful_r2r_scientific_result_v1,
)
from paperworks.v6.task039e3_orchestration_v1 import ConstructionProposalRecordV1
from paperworks.v6.task039e3_recovery_serialization_v1 import (
    finalize_public_artifact_v1,
    verify_public_artifact_v1,
    write_public_artifact_atomic_v1,
)


ROOT = Path(__file__).resolve().parents[1]
HASH = "a" * 64
COMMIT = "b" * 40
AUTHORIZATION_HASH = "c" * 64
PRIVATE_PROPOSAL = "SYNTHETIC_PRIVATE_PROPOSAL_MUST_NOT_BE_PUBLIC"


def _outcomes() -> tuple[ConstructionOutcomeRecordV1, ...]:
    records: list[ConstructionOutcomeRecordV1] = []
    for index in range(42):
        identity = f"relation-{index:02d}"
        records.extend(
            (
                ConstructionOutcomeRecordV1(
                    relation_identity=identity,
                    arm="T0",
                    outcome="accepted_proposal",
                    accepted_call_index=0,
                    generation_calls_consumed=0,
                    verifier_invocations=1,
                    verifier_rejected_proposal_count=0,
                    first_call_admissible=True,
                ),
                ConstructionOutcomeRecordV1(
                    relation_identity=identity,
                    arm="T1",
                    outcome="accepted_proposal" if index % 2 == 0 else "no_rule",
                    accepted_call_index=1 if index % 2 == 0 else None,
                    generation_calls_consumed=1,
                    verifier_invocations=1,
                    verifier_rejected_proposal_count=index % 2,
                    first_call_admissible=index % 2 == 0,
                ),
                ConstructionOutcomeRecordV1(
                    relation_identity=identity,
                    arm="T1-B",
                    outcome="accepted_proposal",
                    accepted_call_index=2,
                    generation_calls_consumed=3,
                    verifier_invocations=3,
                    verifier_rejected_proposal_count=1,
                    first_call_admissible=False,
                ),
                ConstructionOutcomeRecordV1(
                    relation_identity=identity,
                    arm="T2",
                    outcome="accepted_proposal",
                    accepted_call_index=1,
                    generation_calls_consumed=1,
                    verifier_invocations=1,
                    verifier_rejected_proposal_count=0,
                    first_call_admissible=True,
                ),
            )
        )
    return tuple(records)


def _direct() -> tuple[DirectNumberOutcomeV1, ...]:
    return tuple(
        DirectNumberOutcomeV1(
            relation_identity=f"relation-{index:02d}",
            parse_status="valid",
            normalized_absolute_errors={
                role: (index + 1) / 100 for role in CALIBRATED_NUMERIC_ROLES
            },
            missing_number=False,
            nonfinite_or_parse_failure=False,
            sign_domain_violation_roles=(),
        )
        for index in range(42)
    )


def _accounting() -> dict[str, int]:
    return {
        "historical_aborted_r2_scientific_logical_calls": 1,
        "historical_aborted_r2_provider_authored_scientific_responses": 0,
        "r2r_t1_logical_calls": 42,
        "r2r_t1b_logical_calls": 126,
        "r2r_t2_logical_calls": 42,
        "r2r_direct_number_logical_calls": 42,
        "r2r_scientific_logical_calls": 252,
        "lifetime_scientific_logical_call_attempts": 253,
        "r2r_scientific_transport_attempts": 252,
        "r2r_scientific_transport_retries": 0,
        "scientific_concurrency": 1,
        "scientific_generation_retries": 0,
        "historical_partial_records_reused": 0,
        "additional_capability_probes": 0,
        "cumulative_real_provider_capability_probes": 2,
        "local_compatibility_slots": 0,
    }


def _capability() -> dict[str, object]:
    return build_capability_reuse_binding_r2r_v1(
        ValidatedCapabilityReuseR2RV1(
            receipt_hash="1" * 64,
            provider_ledger_hash="2" * 64,
            provider_ledger_head_hash="3" * 64,
            provider_record_hash="3" * 64,
        )
    )


def _authority() -> dict[str, str]:
    return {
        "protocol_bundle_hash": "4" * 64,
        "protocol_receipt_hash": "5" * 64,
        "forensic_commit_b": "6" * 40,
        "forensic_bundle_hash": "7" * 64,
        "forensic_receipt_hash": "8" * 64,
        "failed_r2_terminal_artifact_hash": "9" * 64,
        "failed_r2_scientific_provider_ledger_head_hash": "a" * 64,
        "capability_reuse_binding_hash": CAPABILITY_REUSE_BINDING_HASH,
        "capability_receipt_hash": "1" * 64,
        "capability_provider_ledger_hash": "2" * 64,
        "capability_provider_ledger_head_hash": "3" * 64,
        "implementation_commit_a": COMMIT,
        "implementation_commit_b": "d" * 40,
        "implementation_source_manifest_hash": HASH,
        "independent_audit_commit_b": "e" * 40,
        "independent_audit_bundle_hash": "f" * 64,
        "independent_audit_receipt_hash": "0" * 64,
        "r2r_authorization_hash": AUTHORIZATION_HASH,
    }


def _scientific_binding(record_count: int = 252) -> dict[str, object]:
    return finalize_public_artifact_v1(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039e3_r2r_transactional_provider_binding_v1",
            "task_id": "TASK-039E3-R2R-SCIENTIFIC-EXECUTION",
            "ledger_kind": "scientific_provider",
            "record_count": record_count,
            "hash_chain_verified": True,
            "authoritative_head_verified": True,
            "orphan_records": [],
            "pending_files": [],
        }
    )


def _arguments(private: Path, public: Path) -> dict[str, object]:
    capability = _capability()
    return {
        "repository_root": ROOT,
        "recovery_private_root": private,
        "public_output_root": public,
        "execution_commit": COMMIT,
        "source_manifest_hash": HASH,
        "authorization_hash": AUTHORIZATION_HASH,
        "configuration_fingerprint": "1" * 64,
        "postcontact_integrity_status": "verified_unchanged",
        "authority_bindings": _authority(),
        "capability_reuse_binding": capability,
        "scientific_provider_binding": _scientific_binding(),
        "scientific_provider_records": tuple(
            {
                "logical_call_kind": "scientific",
                "slot_index": index,
                "record_hash": stable_hash_v1({"r2r_slot": index}),
                "private_provider_payload": f"private-{index}",
            }
            for index in range(252)
        ),
        "proposal_records": tuple(
            {
                "relation_identity": f"relation-{index:02d}",
                "raw_proposal": PRIVATE_PROPOSAL,
                "record_hash": stable_hash_v1({"r2r_proposal": index}),
            }
            for index in range(42)
        ),
        "outcome_records": _outcomes(),
        "direct_number_records": _direct(),
        "typed_accounting": _accounting(),
        "scientific_source_hashes": {
            "src/paperworks/v6/task039e3_r2r_execution_v1.py": "2" * 64
        },
    }


def _failure_context() -> dict[str, object]:
    return {
        "execution_commit": COMMIT,
        "source_manifest_hash": HASH,
        "authorization_hash": AUTHORIZATION_HASH,
        "configuration_fingerprint": "1" * 64,
        "capability_reuse_status": "PASS_REUSED",
        "capability_provider_ledger_head_hash": "3" * 64,
        "scientific_provider_ledger_head_hash": "4" * 64,
        "last_attempted_scientific_slot": "T1:relation-00:1",
        "completed_r2r_scientific_logical_calls": 0,
        "r2r_scientific_transport_attempts": 1,
        "proposal_committed_count": 42,
        "outcome_committed_count": 42,
        "direct_number_committed_count": 0,
        "postcontact_integrity_status": "verified_unchanged",
        "actual_returned_model": None,
        "actual_response_id": None,
        "terminal_slot_state": "completed_nonretryable_transport_failure",
    }


class R2RFinalizationV1Tests(unittest.TestCase):
    def test_live_proposal_record_is_materializable_without_public_leakage(self) -> None:
        from paperworks.v6.task039e3_r2r_result_finalizer_v1 import _mapping_record

        class _Validity:
            proposal_hash = "a" * 64
            artifact_hash = "b" * 64

            def to_dict(self):
                return {"proposal_hash": self.proposal_hash, "artifact_hash": self.artifact_hash}

        record = object.__new__(ConstructionProposalRecordV1)
        object.__setattr__(record, "relation_identity", "relation-00")
        object.__setattr__(record, "arm", "T1")
        object.__setattr__(record, "call_number", 1)
        object.__setattr__(record, "project_proposal", {"proposal_hash": "a" * 64})
        object.__setattr__(record, "validity_result", _Validity())
        object.__setattr__(record, "proposal_envelope", None)
        with patch.object(
            ConstructionProposalRecordV1,
            "record_hash",
            new_callable=PropertyMock,
            return_value="c" * 64,
        ):
            projected = _mapping_record(record, "proposal-validity")
        self.assertEqual(projected["relation_identity"], "relation-00")
        self.assertEqual(projected["proposal_hash"], "a" * 64)

    def test_complete_synthetic_42_relation_cohort_finalizes_r2r_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            private = base / "private"
            public = base / "public"
            private.mkdir()
            result = finalize_successful_r2r_scientific_result_v1(
                **_arguments(private, public)
            )

            self.assertEqual(result.status, SUCCESS_STATUS)
            self.assertEqual(
                set(result.public_artifact_hashes),
                set(PUBLIC_ARTIFACT_NAMES_R2R_V1),
            )
            self.assertEqual(
                set(result.private_artifact_hashes),
                set(PRIVATE_ARTIFACT_NAMES_R2R_V1),
            )
            self.assertEqual(result.public_artifact_order[-1], "execution_receipt")
            for filename in PUBLIC_ARTIFACT_NAMES_R2R_V1.values():
                document = json.loads((public / filename).read_text(encoding="utf-8"))
                verify_public_artifact_v1(document)
            receipt = json.loads(
                (
                    public
                    / PUBLIC_ARTIFACT_NAMES_R2R_V1["execution_receipt"]
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(receipt["status"], SUCCESS_STATUS)
            self.assertEqual(
                receipt["typed_accounting"]["r2r_scientific_logical_calls"], 252
            )
            self.assertEqual(
                receipt["typed_accounting"][
                    "lifetime_scientific_logical_call_attempts"
                ],
                253,
            )
            self.assertFalse(receipt["historical_partial_results_reused"])
            public_text = "".join(
                path.read_text(encoding="utf-8") for path in public.iterdir()
            )
            self.assertNotIn(PRIVATE_PROPOSAL, public_text)
            private_text = (
                private
                / "final_authoritative_r2r_v1"
                / PRIVATE_ARTIFACT_NAMES_R2R_V1["proposal_validity"]
            ).read_text(encoding="utf-8")
            self.assertIn(PRIVATE_PROPOSAL, private_text)

    def test_success_receipt_is_last_and_missing_receipt_prevents_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            private = base / "private"
            public = base / "public"
            private.mkdir()
            observed: list[str] = []

            def writer(path: str | Path, document: dict[str, object]) -> dict[str, object]:
                destination = Path(path)
                observed.append(destination.name)
                if destination.name == PUBLIC_ARTIFACT_NAMES_R2R_V1["execution_receipt"]:
                    raise OSError("synthetic receipt persistence failure")
                return write_public_artifact_atomic_v1(destination, document)

            arguments = _arguments(private, public)
            arguments["artifact_writer"] = writer
            with self.assertRaisesRegex(OSError, "receipt persistence"):
                finalize_successful_r2r_scientific_result_v1(**arguments)
            self.assertEqual(
                observed[-1], PUBLIC_ARTIFACT_NAMES_R2R_V1["execution_receipt"]
            )
            self.assertFalse(
                (public / PUBLIC_ARTIFACT_NAMES_R2R_V1["execution_receipt"]).exists()
            )

    def test_corrupt_durable_receipt_prevents_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            private = base / "private"
            public = base / "public"
            private.mkdir()

            def corrupting_writer(
                path: str | Path, document: dict[str, object]
            ) -> dict[str, object]:
                destination = Path(path)
                written = write_public_artifact_atomic_v1(destination, document)
                if destination.name == PUBLIC_ARTIFACT_NAMES_R2R_V1["execution_receipt"]:
                    corrupted = dict(written)
                    corrupted["artifact_hash"] = "0" * 64
                    destination.write_text(
                        json.dumps(corrupted, sort_keys=True, separators=(",", ":")) + "\n",
                        encoding="utf-8",
                    )
                return written

            arguments = _arguments(private, public)
            arguments["artifact_writer"] = corrupting_writer
            with self.assertRaisesRegex(
                TASK039E3R2RResultFinalizationError,
                "re-read and self-hash",
            ):
                finalize_successful_r2r_scientific_result_v1(**arguments)

    def test_historical_call_or_partial_result_cannot_enter_r2r_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            private = base / "private"
            public = base / "public"
            private.mkdir()
            arguments = _arguments(private, public)
            accounting = dict(arguments["typed_accounting"])
            accounting["historical_partial_records_reused"] = 1
            arguments["typed_accounting"] = accounting
            with self.assertRaisesRegex(
                TASK039E3R2RResultFinalizationError, "mixes historical"
            ):
                finalize_successful_r2r_scientific_result_v1(**arguments)
            self.assertFalse(public.exists())
            self.assertFalse((private / "final_authoritative_r2r_v1").exists())

    def test_postcontact_failure_is_sanitized_once_without_resume_or_recontact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "TASK-039E3_R2R_EXECUTION_FAILURE.json"
            calls = {"execute": 0, "finalize": 0, "write": 0}

            def execute() -> object:
                calls["execute"] += 1
                raise RuntimeError("PRIVATE_SYNTHETIC_FAILURE_DETAIL")

            def finalize(_result: object) -> object:
                calls["finalize"] += 1
                return {"status": "impossible-pass"}

            def writer(**kwargs: object) -> dict[str, object]:
                calls["write"] += 1
                return write_terminal_failure_receipt_r2r_v1(
                    destination=destination, **kwargs
                )

            with self.assertRaises(TASK039E3R2RGuardedExecutionFailure) as raised:
                run_guarded_r2r_execution_v1(
                    provider_contact_started=True,
                    execution_stage="scientific_execution",
                    execute_science=execute,
                    finalize_success=finalize,
                    failure_receipt_writer=writer,
                    failure_context=_failure_context(),
                )
            self.assertEqual(calls, {"execute": 1, "finalize": 0, "write": 1})
            receipt = verify_public_artifact_v1(
                json.loads(destination.read_text(encoding="utf-8"))
            )
            self.assertEqual(receipt, raised.exception.failure_receipt)
            self.assertEqual(receipt["status"], FAILURE_STATUS)
            self.assertFalse(receipt["provider_recontact_authorized"])
            self.assertFalse(receipt["automatic_resume_authorized"])
            self.assertFalse(receipt["rule_v2_authorized"])
            self.assertFalse(receipt["runtime_authority"])
            self.assertFalse(receipt["utility_evaluation_authorized"])
            self.assertFalse(receipt["winner_selected"])
            self.assertNotIn("PRIVATE_SYNTHETIC_FAILURE_DETAIL", destination.read_text())

    def test_failure_receipt_persistence_failure_is_distinct_double_fault(self) -> None:
        def execute() -> object:
            raise RuntimeError("original")

        def fail_persistence(**_kwargs: object) -> dict[str, object]:
            raise OSError("persistence")

        with self.assertRaises(TASK039E3R2RFailureReceiptDoubleFault) as raised:
            run_guarded_r2r_execution_v1(
                provider_contact_started=True,
                execution_stage="public_finalization",
                execute_science=execute,
                finalize_success=lambda result: result,
                failure_receipt_writer=fail_persistence,
                failure_context=_failure_context(),
            )
        self.assertEqual(raised.exception.classification, DOUBLE_FAULT_CLASSIFICATION)

    def test_precontact_failure_does_not_materialize_postcontact_receipt(self) -> None:
        calls = {"writer": 0}

        def fail() -> object:
            raise RuntimeError("offline guard")

        def writer(**_kwargs: object) -> dict[str, object]:
            calls["writer"] += 1
            return {}

        with self.assertRaisesRegex(RuntimeError, "offline guard"):
            run_guarded_r2r_execution_v1(
                provider_contact_started=False,
                execution_stage="precontact",
                execute_science=fail,
                finalize_success=lambda result: result,
                failure_receipt_writer=writer,
                failure_context=_failure_context(),
            )
        self.assertEqual(calls["writer"], 0)


if __name__ == "__main__":
    unittest.main()
