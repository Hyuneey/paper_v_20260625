from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e2_execution_configuration_v1 import CALIBRATED_NUMERIC_ROLES
from paperworks.v6.task039e3_orchestration_v1 import (
    ConstructionOutcomeRecordV1,
    DirectNumberOutcomeV1,
)
from paperworks.v6.task039e3_recovery_result_finalizer_v3 import (
    PRIVATE_ARTIFACT_NAMES_V3,
    PUBLIC_ARTIFACT_NAMES_V3,
    SUCCESS_STATUS,
    TASK039E3RecoveryResultFinalizationV3Error,
    finalize_successful_scientific_result_v3,
    prepare_result_roots_v3,
    provider_custody_binding_from_reconstruction_v3,
)
from paperworks.v6.task039e3_recovery_serialization_v1 import (
    finalize_public_artifact_v1,
    verify_public_artifact_v1,
    write_public_artifact_atomic_v1,
)
from paperworks.v6.task039e3_recovery_transactional_custody_v3 import (
    TransactionalHashChainCustodyV3,
)


ROOT = Path(__file__).resolve().parents[1]
HASH = "a" * 64
COMMIT = "b" * 40
PRIVATE_PROPOSAL = "SYNTHETIC_PRIVATE_PROPOSAL_NOT_PUBLIC"


def _authority() -> dict[str, str]:
    return {
        "r0_bundle_hash": "1" * 64,
        "r1a_timeout_authority_hash": "2" * 64,
        "r1b_commit_b": "3" * 40,
        "r1c_commit_b": "4" * 40,
        "r1c_audit_bundle_hash": "5" * 64,
        "r1d2_commit_a": COMMIT,
        "r1d2_commit_b": "6" * 40,
        "r1d2_source_manifest_hash": HASH,
        "r1d2_audit_commit_b": "7" * 40,
        "r1d2_independent_audit_bundle_hash": "8" * 64,
        "r1d2_audit_receipt_hash": "9" * 64,
        "r2_authorization_hash": "c" * 64,
    }


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
                    verifier_rejected_proposal_count=2,
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
            normalized_absolute_errors={role: (index + 1) / 100 for role in CALIBRATED_NUMERIC_ROLES},
            missing_number=False,
            nonfinite_or_parse_failure=False,
            sign_domain_violation_roles=(),
        )
        for index in range(42)
    )


def _accounting() -> dict[str, int]:
    return {
        "historical_capability_probes": 1,
        "current_recovery_capability_logical_calls": 1,
        "current_recovery_capability_transport_attempts": 1,
        "current_recovery_capability_transport_retries": 0,
        "cumulative_real_provider_capability_probes": 2,
        "t1_logical_calls": 42,
        "t1b_logical_calls": 126,
        "t2_logical_calls": 42,
        "direct_number_logical_calls": 42,
        "scientific_logical_calls": 252,
        "scientific_transport_attempts": 252,
        "scientific_transport_retries": 0,
        "scientific_concurrency": 1,
        "scientific_generation_retries": 0,
        "local_compatibility_slots": 0,
    }


def _artifact(artifact_type: str, **values: object) -> dict[str, object]:
    return finalize_public_artifact_v1(
        {"schema_version": "3.0.0", "artifact_type": artifact_type, **values}
    )


def _arguments(private: Path, public: Path) -> dict[str, object]:
    provider_records = tuple(
        {
            "logical_call_kind": "scientific",
            "slot_index": index,
            "response_origin": "provider",
            "scientific": True,
            "record_hash": stable_hash_v1({"slot": index}),
        }
        for index in range(252)
    )
    proposal_records = tuple(
        {
            "relation_identity": f"relation-{index:02d}",
            "proposal_private": PRIVATE_PROPOSAL,
            "record_hash": stable_hash_v1({"proposal": index}),
        }
        for index in range(42)
    )
    return {
        "repository_root": ROOT,
        "recovery_private_root": private,
        "public_output_root": public,
        "execution_commit": COMMIT,
        "source_manifest_hash": HASH,
        "authorization_hash": "c" * 64,
        "configuration_fingerprint": "d" * 64,
        "postcontact_integrity_status": "verified_unchanged",
        "authority_bindings": _authority(),
        "capability_receipt": _artifact(
            "task039e3_recovery_capability_receipt_v3",
            gate_status="PASS",
            provider_contacted=True,
        ),
        "capability_provider_binding": _artifact(
            "task039e3_r2_transactional_provider_binding_v3",
            ledger_kind="recovery_capability",
            record_count=1,
            hash_chain_verified=True,
            authoritative_head_verified=True,
            orphan_records=[],
            pending_files=[],
        ),
        "scientific_provider_binding": _artifact(
            "task039e3_r2_transactional_provider_binding_v3",
            ledger_kind="scientific_provider",
            record_count=252,
            hash_chain_verified=True,
            authoritative_head_verified=True,
            orphan_records=[],
            pending_files=[],
        ),
        "scientific_provider_records": provider_records,
        "proposal_records": proposal_records,
        "outcome_records": _outcomes(),
        "direct_number_records": _direct(),
        "typed_accounting": _accounting(),
        "scientific_source_hashes": {
            "src/paperworks/v6/task039e3_orchestration_v1.py": "e" * 64
        },
    }


class R1D2ResultFinalizerV3Tests(unittest.TestCase):
    def test_transactional_reconstruction_converts_to_verified_final_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            custody = TransactionalHashChainCustodyV3(
                Path(temporary) / "ledger",
                ledger_kind="scientific_provider",
                allowed_logical_call_kind="scientific",
            )
            custody.append(
                logical_call_kind="scientific",
                slot_identity="T1:relation-00:1",
                payload={"response_origin": "provider", "scientific": True},
            )
            binding = provider_custody_binding_from_reconstruction_v3(custody.reconstruct())
            verify_public_artifact_v1(binding)
            self.assertEqual(binding["record_count"], 1)
            self.assertTrue(binding["hash_chain_verified"])
            self.assertTrue(binding["authoritative_head_verified"])
            self.assertEqual(binding["orphan_records"], [])

    def test_synthetic_42_relation_result_materializes_complete_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            private = base / "private"
            public = base / "public"
            private.mkdir()
            result = finalize_successful_scientific_result_v3(**_arguments(private, public))

            self.assertEqual(result.status, SUCCESS_STATUS)
            self.assertEqual(set(result.public_artifact_hashes), set(PUBLIC_ARTIFACT_NAMES_V3))
            self.assertEqual(set(result.private_artifact_hashes), set(PRIVATE_ARTIFACT_NAMES_V3))
            self.assertEqual(result.public_artifact_order[-1], "execution_receipt")
            for filename in PUBLIC_ARTIFACT_NAMES_V3.values():
                verify_public_artifact_v1(json.loads((public / filename).read_text(encoding="utf-8")))
            for filename in PRIVATE_ARTIFACT_NAMES_V3.values():
                verify_public_artifact_v1(
                    json.loads((private / "final_authoritative_v3" / filename).read_text(encoding="utf-8"))
                )

            construction = json.loads(
                (public / PUBLIC_ARTIFACT_NAMES_V3["construction_metrics"]).read_text(encoding="utf-8")
            )
            self.assertEqual(construction["main_metrics"]["T1"]["accepted_proposal_count"], 21)
            self.assertEqual(construction["main_metrics"]["T1-B"]["generation_calls_consumed"], 126)
            direct = json.loads(
                (public / PUBLIC_ARTIFACT_NAMES_V3["direct_number_metrics"]).read_text(encoding="utf-8")
            )
            for role in CALIBRATED_NUMERIC_ROLES:
                self.assertEqual(direct["normalized_absolute_error_summary_by_role"][role]["count"], 42)
            summary = json.loads(
                (public / PUBLIC_ARTIFACT_NAMES_V3["execution_summary"]).read_text(encoding="utf-8")
            )
            self.assertEqual(summary["scientific_calls"], 252)
            self.assertEqual(summary["scientific_call_counts"]["T1-B"], 126)
            receipt = json.loads(
                (public / PUBLIC_ARTIFACT_NAMES_V3["execution_receipt"]).read_text(encoding="utf-8")
            )
            self.assertEqual(receipt["artifact_hash"], result.execution_receipt_hash)
            self.assertEqual(receipt["status"], SUCCESS_STATUS)
            self.assertEqual(
                receipt["construction_metrics_hash"],
                result.public_artifact_hashes["construction_metrics"],
            )

            public_text = "".join(path.read_text(encoding="utf-8") for path in public.iterdir())
            self.assertNotIn(PRIVATE_PROPOSAL, public_text)
            private_proposal = private / "final_authoritative_v3" / PRIVATE_ARTIFACT_NAMES_V3["proposal_validity"]
            self.assertIn(PRIVATE_PROPOSAL, private_proposal.read_text(encoding="utf-8"))

    def test_receipt_is_written_last_and_pass_requires_durable_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            private = base / "private"
            public = base / "public"
            private.mkdir()
            observed: list[str] = []

            def writer(path: str | Path, document: dict[str, object]) -> dict[str, object]:
                destination = Path(path)
                observed.append(destination.name)
                if destination.name == PUBLIC_ARTIFACT_NAMES_V3["execution_receipt"]:
                    raise OSError("synthetic receipt persistence failure")
                return write_public_artifact_atomic_v1(destination, document)

            arguments = _arguments(private, public)
            arguments["artifact_writer"] = writer
            with self.assertRaisesRegex(OSError, "receipt persistence"):
                finalize_successful_scientific_result_v3(**arguments)
            self.assertEqual(observed[-1], PUBLIC_ARTIFACT_NAMES_V3["execution_receipt"])
            self.assertFalse((public / PUBLIC_ARTIFACT_NAMES_V3["execution_receipt"]).exists())

    def test_incomplete_or_inconsistent_science_blocks_before_root_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            private = base / "private"
            public = base / "public"
            private.mkdir()
            arguments = _arguments(private, public)
            accounting = dict(arguments["typed_accounting"])
            accounting["scientific_logical_calls"] = 251
            arguments["typed_accounting"] = accounting
            with self.assertRaisesRegex(
                TASK039E3RecoveryResultFinalizationV3Error, "typed accounting"
            ):
                finalize_successful_scientific_result_v3(**arguments)
            self.assertFalse(public.exists())
            self.assertFalse((private / "final_authoritative_v3").exists())

    def test_public_root_must_be_external_distinct_and_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            private = base / "private"
            private.mkdir()
            public = base / "public"
            public.mkdir()
            (public / "occupied").write_text("x", encoding="utf-8")
            with self.assertRaisesRegex(
                TASK039E3RecoveryResultFinalizationV3Error, "new or empty"
            ):
                prepare_result_roots_v3(
                    repository_root=ROOT,
                    recovery_private_root=private,
                    public_output_root=public,
                )
            self.assertFalse((private / "final_authoritative_v3").exists())

            protected = base / "historical-private"
            protected.mkdir()
            nested_public = protected / "public"
            with self.assertRaisesRegex(
                TASK039E3RecoveryResultFinalizationV3Error, "distinct and unnested"
            ):
                prepare_result_roots_v3(
                    repository_root=ROOT,
                    recovery_private_root=private,
                    public_output_root=nested_public,
                    protected_private_roots=(protected,),
                )

        with tempfile.TemporaryDirectory(dir=ROOT) as repository_temporary:
            base = Path(repository_temporary)
            private = base / "private"
            public = base / "public"
            private.mkdir()
            with self.assertRaisesRegex(
                TASK039E3RecoveryResultFinalizationV3Error, "distinct and unnested"
            ):
                prepare_result_roots_v3(
                    repository_root=ROOT,
                    recovery_private_root=private,
                    public_output_root=public,
                )


if __name__ == "__main__":
    unittest.main()
