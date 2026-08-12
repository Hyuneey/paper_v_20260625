from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e2_execution_configuration_v1 import (
    CALIBRATED_NUMERIC_ROLES,
)
from paperworks.v6.task039e3_orchestration_v1 import (
    ConstructionOutcomeRecordV1,
    DirectNumberOutcomeV1,
)
from paperworks.v6.task039e3_r2r_authorization_v1 import (
    validate_r2r_authorization_v1,
)
from paperworks.v6.task039e3_r2r_capability_reuse_v1 import (
    ValidatedCapabilityReuseR2RV1,
)
from paperworks.v6.task039e3_r2r_failure_finalizer_v1 import (
    DOUBLE_FAULT_CLASSIFICATION,
    TASK039E3R2RFailureReceiptDoubleFault,
    TASK039E3R2RGuardedExecutionFailure,
    run_guarded_r2r_execution_v1,
    write_terminal_failure_receipt_r2r_v1,
)
from paperworks.v6.task039e3_r2r_result_finalizer_v1 import (
    PUBLIC_ARTIFACT_NAMES_R2R_V1,
    SUCCESS_STATUS,
    build_capability_reuse_binding_r2r_v1,
    finalize_successful_r2r_scientific_result_v1,
)
from paperworks.v6.task039e3_recovery_serialization_v1 import (
    finalize_public_artifact_v1,
    verify_public_artifact_v1,
    write_public_artifact_atomic_v1,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/v6/task039e3_r2r_execution_authorization_v1_schema.json"
IMPLEMENTATION_A = "3aa63588b08692b0333de26d3042b717e62014f2"
IMPLEMENTATION_B = "c6e34440ee362df51e95b6181853f3f89fe4310e"
SOURCE_MANIFEST = "35e73804156c097b27ae3d216575af6867a6330d346ddc71c888b5917a60859a"
FUTURE_AUDIT_B = "d" * 40
FUTURE_AUDIT_BUNDLE = "e" * 64
FUTURE_AUDIT_RECEIPT = "f" * 64
AUTHORIZATION_HASH = "9" * 64


def _future_authorization() -> dict[str, object]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    document: dict[str, object] = {}
    for key, definition in schema["properties"].items():
        if key == "self_hash":
            continue
        if "const" in definition:
            document[key] = definition["const"]
        elif "{40}" in definition.get("pattern", ""):
            document[key] = "a" * 40
        else:
            document[key] = "b" * 64
    document.update(
        {
            "implementation_commit_a": IMPLEMENTATION_A,
            "implementation_commit_b": IMPLEMENTATION_B,
            "implementation_source_manifest_hash": SOURCE_MANIFEST,
            "independent_audit_commit_b": FUTURE_AUDIT_B,
            "independent_audit_bundle_hash": FUTURE_AUDIT_BUNDLE,
            "independent_audit_receipt_hash": FUTURE_AUDIT_RECEIPT,
            "recovery_execution_configuration_hash": "c" * 64,
        }
    )
    document["self_hash"] = stable_hash_v1(document)
    return document


def _capability_binding() -> dict[str, object]:
    return build_capability_reuse_binding_r2r_v1(
        ValidatedCapabilityReuseR2RV1(
            receipt_hash="9ee4637da31b585a34eda4bad3b3be1dfa5597396ce1e78ef0564fa53da2b428",
            provider_ledger_hash="d6531d990bd70d89d114094f003dd9387e4df2db9cf9c2fc14bb5cf790818294",
            provider_ledger_head_hash="e0b449ca96ffbf229954c059780baf8fb115aa79fc5d65802dd19e3a54120471",
            provider_record_hash="e0b449ca96ffbf229954c059780baf8fb115aa79fc5d65802dd19e3a54120471",
        )
    )


def _authority_bindings() -> dict[str, str]:
    authorization = _future_authorization()
    authorization_hash = str(authorization["self_hash"])
    return {
        "protocol_bundle_hash": "dbfab6817a8924b6c728c4a82405f5ffb030672c0057e6d25425fd5084e9e4a3",
        "protocol_receipt_hash": "2d65919dced159c2e584b4c5347dc2f4a3f8fd0d35323322d68014d2843f1168",
        "forensic_commit_b": "12a974eb06999ec35266c73c8665852c072b1a41",
        "forensic_bundle_hash": "8c01943ec1ac99ee2021a7e085eeffa45403590ca8f0857d71131ce20369a514",
        "forensic_receipt_hash": "caa4a5b7537aaa62dd83f32253fa00aa9474c6472bdd48b23f16d80c89a15b46",
        "failed_r2_terminal_artifact_hash": "871afdea4753ae04594037ebaf973f2bf2963accb258df8b890076aa64cb837c",
        "failed_r2_scientific_provider_ledger_head_hash": "55bc62f047c085e3323fc28b1207afc3e5552a4ff05abad1b1fc05d055f79260",
        "capability_reuse_binding_hash": "a26582efd20add0e639c40e7f3ed64428dc39923d284d0f0ad0d69d017b02f82",
        "capability_receipt_hash": "9ee4637da31b585a34eda4bad3b3be1dfa5597396ce1e78ef0564fa53da2b428",
        "capability_provider_ledger_hash": "d6531d990bd70d89d114094f003dd9387e4df2db9cf9c2fc14bb5cf790818294",
        "capability_provider_ledger_head_hash": "e0b449ca96ffbf229954c059780baf8fb115aa79fc5d65802dd19e3a54120471",
        "implementation_commit_a": IMPLEMENTATION_A,
        "implementation_commit_b": IMPLEMENTATION_B,
        "implementation_source_manifest_hash": SOURCE_MANIFEST,
        "independent_audit_commit_b": FUTURE_AUDIT_B,
        "independent_audit_bundle_hash": FUTURE_AUDIT_BUNDLE,
        "independent_audit_receipt_hash": FUTURE_AUDIT_RECEIPT,
        "r2r_authorization_hash": authorization_hash,
    }


def _outcomes(t2_calls: int = 42) -> tuple[ConstructionOutcomeRecordV1, ...]:
    if t2_calls not in (42, 126):
        raise ValueError("fixture supports only minimum/maximum T2 budgets")
    records: list[ConstructionOutcomeRecordV1] = []
    t2_per_relation = t2_calls // 42
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
                    outcome="accepted_proposal",
                    accepted_call_index=1,
                    generation_calls_consumed=1,
                    verifier_invocations=1,
                    verifier_rejected_proposal_count=0,
                    first_call_admissible=True,
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
                    accepted_call_index=t2_per_relation,
                    generation_calls_consumed=t2_per_relation,
                    verifier_invocations=t2_per_relation,
                    verifier_rejected_proposal_count=t2_per_relation - 1,
                    first_call_admissible=t2_per_relation == 1,
                ),
            )
        )
    return tuple(records)


def _direct() -> tuple[DirectNumberOutcomeV1, ...]:
    return tuple(
        DirectNumberOutcomeV1(
            relation_identity=f"relation-{index:02d}",
            parse_status="valid",
            normalized_absolute_errors={role: 0.01 for role in CALIBRATED_NUMERIC_ROLES},
            missing_number=False,
            nonfinite_or_parse_failure=False,
            sign_domain_violation_roles=(),
        )
        for index in range(42)
    )


def _typed_accounting(t2_calls: int = 42) -> dict[str, int]:
    r2r_calls = 42 + 126 + t2_calls + 42
    return {
        "historical_aborted_r2_scientific_logical_calls": 1,
        "historical_aborted_r2_provider_authored_scientific_responses": 0,
        "r2r_t1_logical_calls": 42,
        "r2r_t1b_logical_calls": 126,
        "r2r_t2_logical_calls": t2_calls,
        "r2r_direct_number_logical_calls": 42,
        "r2r_scientific_logical_calls": r2r_calls,
        "lifetime_scientific_logical_call_attempts": 1 + r2r_calls,
        "r2r_scientific_transport_attempts": r2r_calls,
        "r2r_scientific_transport_retries": 0,
        "scientific_concurrency": 1,
        "scientific_generation_retries": 0,
        "historical_partial_records_reused": 0,
        "additional_capability_probes": 0,
        "cumulative_real_provider_capability_probes": 2,
        "local_compatibility_slots": 0,
    }


def _finalizer_arguments(private: Path, public: Path) -> dict[str, object]:
    t2_calls = 42
    r2r_calls = 42 + 126 + t2_calls + 42
    authorization_hash = str(_future_authorization()["self_hash"])
    provider_binding = finalize_public_artifact_v1(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039e3_r2r_transactional_provider_binding_v1",
            "task_id": "TASK-039E3-R2R-SCIENTIFIC-EXECUTION",
            "ledger_kind": "scientific_provider",
            "record_count": r2r_calls,
            "hash_chain_verified": True,
            "authoritative_head_verified": True,
            "orphan_records": [],
            "pending_files": [],
        }
    )
    return {
        "repository_root": ROOT,
        "recovery_private_root": private,
        "public_output_root": public,
        "execution_commit": IMPLEMENTATION_A,
        "source_manifest_hash": SOURCE_MANIFEST,
        "authorization_hash": authorization_hash,
        "configuration_fingerprint": "7" * 64,
        "postcontact_integrity_status": "verified_unchanged",
        "authority_bindings": _authority_bindings(),
        "capability_reuse_binding": _capability_binding(),
        "scientific_provider_binding": provider_binding,
        "scientific_provider_records": tuple(
            {
                "logical_call_kind": "scientific",
                "slot_index": index,
                "record_hash": stable_hash_v1({"independent-audit-provider": index}),
            }
            for index in range(r2r_calls)
        ),
        "proposal_records": tuple(
            {
                "relation_identity": f"relation-{index:02d}",
                "record_hash": stable_hash_v1({"independent-audit-proposal": index}),
            }
            for index in range(42)
        ),
        "outcome_records": _outcomes(t2_calls),
        "direct_number_records": _direct(),
        "typed_accounting": _typed_accounting(t2_calls),
        "scientific_source_hashes": {
            "src/paperworks/v6/task039e3_r2r_live_execution_v1.py": "6" * 64,
        },
    }


def _failure_context() -> dict[str, object]:
    return {
        "execution_commit": IMPLEMENTATION_A,
        "source_manifest_hash": SOURCE_MANIFEST,
        "authorization_hash": str(_future_authorization()["self_hash"]),
        "configuration_fingerprint": "7" * 64,
        "capability_reuse_status": "PASS_REUSED",
        "capability_provider_ledger_head_hash": "e0b449ca96ffbf229954c059780baf8fb115aa79fc5d65802dd19e3a54120471",
        "scientific_provider_ledger_head_hash": "8" * 64,
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


class R2RIndependentAuditFinalizationAuthorityTests(unittest.TestCase):
    def test_future_closed_authorization_binds_final_c1_identities(self) -> None:
        document = _future_authorization()
        validated = validate_r2r_authorization_v1(document)
        self.assertEqual(validated.implementation_commit_a, IMPLEMENTATION_A)
        self.assertEqual(validated.implementation_commit_b, IMPLEMENTATION_B)
        self.assertEqual(validated.implementation_source_manifest_hash, SOURCE_MANIFEST)
        self.assertEqual(validated.independent_audit_commit_b, FUTURE_AUDIT_B)
        self.assertEqual(validated.independent_audit_bundle_hash, FUTURE_AUDIT_BUNDLE)
        self.assertEqual(validated.independent_audit_receipt_hash, FUTURE_AUDIT_RECEIPT)

    def test_complete_synthetic_result_binds_every_authority_and_receipt_is_last(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            private = base / "private"
            public = base / "public"
            private.mkdir()
            result = finalize_successful_r2r_scientific_result_v1(
                **_finalizer_arguments(private, public)
            )
            self.assertEqual(result.status, SUCCESS_STATUS)
            self.assertEqual(result.public_artifact_order[-1], "execution_receipt")
            receipt_path = public / PUBLIC_ARTIFACT_NAMES_R2R_V1["execution_receipt"]
            receipt = verify_public_artifact_v1(
                json.loads(receipt_path.read_text(encoding="utf-8"))
            )
            self.assertEqual(receipt["implementation_commit_a"], IMPLEMENTATION_A)
            self.assertEqual(receipt["implementation_commit_b"], IMPLEMENTATION_B)
            self.assertEqual(receipt["implementation_source_manifest_hash"], SOURCE_MANIFEST)
            self.assertEqual(receipt["independent_audit_commit_b"], FUTURE_AUDIT_B)
            self.assertEqual(receipt["independent_audit_bundle_hash"], FUTURE_AUDIT_BUNDLE)
            self.assertEqual(receipt["independent_audit_receipt_hash"], FUTURE_AUDIT_RECEIPT)
            for key, filename in PUBLIC_ARTIFACT_NAMES_R2R_V1.items():
                document = verify_public_artifact_v1(
                    json.loads((public / filename).read_text(encoding="utf-8"))
                )
                self.assertEqual(result.public_artifact_hashes[key], document["artifact_hash"])

    def test_pass_is_impossible_if_any_pre_receipt_public_artifact_is_deleted_or_corrupt(self) -> None:
        prerequisite_keys = tuple(
            key for key in PUBLIC_ARTIFACT_NAMES_R2R_V1 if key != "execution_receipt"
        )
        unsafe_passes: list[str] = []
        for target_key in prerequisite_keys:
            for mutation in ("delete", "corrupt"):
                with self.subTest(target=target_key, mutation=mutation):
                    with tempfile.TemporaryDirectory() as temporary:
                        base = Path(temporary)
                        private = base / "private"
                        public = base / "public"
                        private.mkdir()
                        target = public / PUBLIC_ARTIFACT_NAMES_R2R_V1[target_key]

                        def writer(
                            path: str | Path, document: dict[str, object]
                        ) -> dict[str, object]:
                            destination = Path(path)
                            written = write_public_artifact_atomic_v1(destination, document)
                            if (
                                destination.name
                                == PUBLIC_ARTIFACT_NAMES_R2R_V1["execution_receipt"]
                            ):
                                if mutation == "delete":
                                    target.unlink()
                                else:
                                    altered = json.loads(target.read_text(encoding="utf-8"))
                                    altered["artifact_hash"] = "0" * 64
                                    target.write_text(
                                        json.dumps(
                                            altered,
                                            sort_keys=True,
                                            separators=(",", ":"),
                                        )
                                        + "\n",
                                        encoding="utf-8",
                                    )
                            return written

                        arguments = _finalizer_arguments(private, public)
                        arguments["artifact_writer"] = writer
                        try:
                            result = finalize_successful_r2r_scientific_result_v1(
                                **arguments
                            )
                        except Exception:
                            continue
                        if result.status == SUCCESS_STATUS:
                            unsafe_passes.append(f"{target_key}:{mutation}")
        self.assertEqual(
            unsafe_passes,
            [],
            "terminal PASS survived missing/corrupt prerequisite artifacts: "
            + ", ".join(unsafe_passes),
        )

    def test_postcontact_failure_is_sanitized_and_double_fault_is_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "TASK-039E3_R2R_EXECUTION_FAILURE.json"

            def fail_science() -> object:
                raise RuntimeError("SYNTHETIC_PRIVATE_DETAIL")

            def writer(**kwargs: object) -> dict[str, object]:
                return write_terminal_failure_receipt_r2r_v1(
                    destination=destination, **kwargs
                )

            with self.assertRaises(TASK039E3R2RGuardedExecutionFailure) as observed:
                run_guarded_r2r_execution_v1(
                    provider_contact_started=True,
                    execution_stage="scientific_execution",
                    execute_science=fail_science,
                    finalize_success=lambda result: result,
                    failure_receipt_writer=writer,
                    failure_context=_failure_context(),
                )
            receipt = verify_public_artifact_v1(
                json.loads(destination.read_text(encoding="utf-8"))
            )
            self.assertEqual(receipt, observed.exception.failure_receipt)
            self.assertFalse(receipt["provider_recontact_authorized"])
            self.assertFalse(receipt["automatic_resume_authorized"])
            self.assertFalse(receipt["rule_v2_authorized"])
            self.assertFalse(receipt["runtime_authority"])
            self.assertFalse(receipt["utility_evaluation_authorized"])
            self.assertFalse(receipt["winner_selected"])
            self.assertNotIn("SYNTHETIC_PRIVATE_DETAIL", destination.read_text())

        with self.assertRaises(TASK039E3R2RFailureReceiptDoubleFault) as doubled:
            run_guarded_r2r_execution_v1(
                provider_contact_started=True,
                execution_stage="receipt_finalization",
                execute_science=lambda: (_ for _ in ()).throw(RuntimeError("first")),
                finalize_success=lambda result: result,
                failure_receipt_writer=lambda **_kwargs: (_ for _ in ()).throw(
                    OSError("second")
                ),
                failure_context=_failure_context(),
            )
        self.assertEqual(doubled.exception.classification, DOUBLE_FAULT_CLASSIFICATION)


if __name__ == "__main__":
    unittest.main()
