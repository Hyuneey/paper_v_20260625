from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
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
)
from paperworks.v6.task039e3_recovery_serialization_v1 import (
    RecoverySerializationError,
    finalize_public_artifact_v1,
    verify_public_artifact_v1,
    write_public_artifact_atomic_v1,
)


ROOT = Path(__file__).resolve().parents[1]
COMMIT = "b" * 40
HASH = "a" * 64
PRIVATE_SENTINEL = "AUDIT_PRIVATE_PROPOSAL_MUST_NOT_BE_PUBLIC"


def _artifact(artifact_type: str, **values: object) -> dict[str, object]:
    return finalize_public_artifact_v1(
        {"schema_version": "3.0.0", "artifact_type": artifact_type, **values}
    )


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


def _outcomes(t2_calls: int = 42) -> tuple[ConstructionOutcomeRecordV1, ...]:
    result: list[ConstructionOutcomeRecordV1] = []
    per_relation_t2 = t2_calls // 42
    if t2_calls not in {42, 84, 126}:
        raise ValueError("audit fixture requires uniform T2 calls")
    for index in range(42):
        relation = f"relation-{index:02d}"
        result.extend(
            (
                ConstructionOutcomeRecordV1(
                    relation_identity=relation,
                    arm="T0",
                    outcome="accepted_proposal",
                    accepted_call_index=0,
                    generation_calls_consumed=0,
                    verifier_invocations=1,
                    verifier_rejected_proposal_count=0,
                    first_call_admissible=True,
                ),
                ConstructionOutcomeRecordV1(
                    relation_identity=relation,
                    arm="T1",
                    outcome="accepted_proposal" if index % 2 == 0 else "no_rule",
                    accepted_call_index=1 if index % 2 == 0 else None,
                    generation_calls_consumed=1,
                    verifier_invocations=1,
                    verifier_rejected_proposal_count=index % 2,
                    first_call_admissible=index % 2 == 0,
                ),
                ConstructionOutcomeRecordV1(
                    relation_identity=relation,
                    arm="T1-B",
                    outcome="accepted_proposal",
                    accepted_call_index=(index % 3) + 1,
                    generation_calls_consumed=3,
                    verifier_invocations=3,
                    verifier_rejected_proposal_count=index % 3,
                    first_call_admissible=index % 3 == 0,
                ),
                ConstructionOutcomeRecordV1(
                    relation_identity=relation,
                    arm="T2",
                    outcome="accepted_proposal",
                    accepted_call_index=per_relation_t2,
                    generation_calls_consumed=per_relation_t2,
                    verifier_invocations=per_relation_t2,
                    verifier_rejected_proposal_count=per_relation_t2 - 1,
                    first_call_admissible=per_relation_t2 == 1,
                    revise_count=per_relation_t2 - 1,
                    feedback_path="revise" if per_relation_t2 > 1 else None,
                ),
            )
        )
    return tuple(result)


def _direct() -> tuple[DirectNumberOutcomeV1, ...]:
    return tuple(
        DirectNumberOutcomeV1(
            relation_identity=f"relation-{index:02d}",
            parse_status="valid",
            normalized_absolute_errors={
                role: (index + role_index + 1) / 100
                for role_index, role in enumerate(CALIBRATED_NUMERIC_ROLES)
            },
            missing_number=False,
            nonfinite_or_parse_failure=False,
            sign_domain_violation_roles=(),
        )
        for index in range(42)
    )


def _accounting(t2_calls: int) -> dict[str, int]:
    scientific = 210 + t2_calls
    return {
        "historical_capability_probes": 1,
        "current_recovery_capability_logical_calls": 1,
        "current_recovery_capability_transport_attempts": 2,
        "current_recovery_capability_transport_retries": 1,
        "cumulative_real_provider_capability_probes": 2,
        "t1_logical_calls": 42,
        "t1b_logical_calls": 126,
        "t2_logical_calls": t2_calls,
        "direct_number_logical_calls": 42,
        "scientific_logical_calls": scientific,
        "scientific_transport_attempts": scientific + 3,
        "scientific_transport_retries": 3,
        "scientific_concurrency": 1,
        "scientific_generation_retries": 0,
        "local_compatibility_slots": 0,
    }


def _arguments(private: Path, public: Path, *, t2_calls: int = 42) -> dict[str, object]:
    scientific = 210 + t2_calls
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
            record_count=scientific,
            hash_chain_verified=True,
            authoritative_head_verified=True,
            orphan_records=[],
            pending_files=[],
        ),
        "scientific_provider_records": tuple(
            {
                "logical_call_kind": "scientific",
                "scientific": True,
                "slot_index": index,
                "response_origin": "provider",
                "record_hash": stable_hash_v1({"slot": index}),
            }
            for index in range(scientific)
        ),
        "proposal_records": tuple(
            {
                "relation_identity": f"relation-{index:02d}",
                "proposal_private": PRIVATE_SENTINEL,
                "record_hash": stable_hash_v1({"proposal": index}),
            }
            for index in range(42)
        ),
        "outcome_records": _outcomes(t2_calls),
        "direct_number_records": _direct(),
        "typed_accounting": _accounting(t2_calls),
        "scientific_source_hashes": {"frozen-arm-source.py": "e" * 64},
    }


def _manual_construction_metrics(
    records: tuple[ConstructionOutcomeRecordV1, ...],
) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for arm in ("T0", "T1", "T1-B", "T2"):
        items = [record for record in records if record.arm == arm]
        count = len(items)
        accepted = sum(record.outcome == "accepted_proposal" for record in items)
        values: dict[str, object] = {
            "eligible_relation_count": count,
            "accepted_proposal_count": accepted,
            "accepted_proposal_rate": accepted / count,
            "no_rule_count": sum(record.outcome == "no_rule" for record in items),
            "no_rule_rate": sum(record.outcome == "no_rule" for record in items) / count,
            "verifier_rejected_proposal_count": sum(record.verifier_rejected_proposal_count for record in items),
            "first_call_admissible_rate": sum(record.first_call_admissible for record in items) / count,
            "eventual_admissible_rate": accepted / count,
            "generation_calls_consumed": sum(record.generation_calls_consumed for record in items),
            "verifier_invocations": sum(record.verifier_invocations for record in items),
            "retrieval_count": sum(record.retrieval_count for record in items),
            "revise_count": sum(record.revise_count for record in items),
            "budget_exhaustion_count": sum(record.budget_exhaustion_count for record in items),
        }
        if arm == "T1-B":
            values["any_admissible_among_3_rate"] = sum(record.accepted_call_index is not None for record in items) / count
            values["selected_call_index_distribution"] = {
                str(call): sum(record.accepted_call_index == call for record in items)
                for call in (1, 2, 3)
            }
        if arm == "T2":
            recovered = sum(
                record.outcome == "accepted_proposal"
                and record.accepted_call_index is not None
                and record.accepted_call_index > 1
                for record in items
            )
            values.update(
                {
                    "feedback_recovery_count": recovered,
                    "feedback_recovery_rate": recovered / count,
                    "accepted_after_revise": sum(record.outcome == "accepted_proposal" and record.feedback_path == "revise" for record in items),
                    "accepted_after_retrieve": sum(record.outcome == "accepted_proposal" and record.feedback_path == "retrieve" for record in items),
                    "no_rule_due_non_repairable_issue": sum(record.no_rule_reason == "non_repairable_issue" for record in items),
                    "no_rule_due_budget_exhaustion": sum(record.no_rule_reason == "budget_exhaustion" for record in items),
                }
            )
        result[arm] = values
    return result


def _manual_direct_summary(records: tuple[DirectNumberOutcomeV1, ...]) -> dict[str, object]:
    by_role: dict[str, object] = {}
    for role in CALIBRATED_NUMERIC_ROLES:
        values = [float(record.normalized_absolute_errors[role]) for record in records]
        by_role[role] = {
            "count": len(values),
            "minimum": min(values),
            "maximum": max(values),
            "mean": statistics.fmean(values),
            "median": statistics.median(values),
            "missing_number_count": 0,
            "missing_number_rate": 0.0,
            "nonfinite_or_parse_failure_count": 0,
            "nonfinite_or_parse_failure_rate": 0.0,
            "sign_domain_violation_count": 0,
            "sign_domain_violation_rate": 0.0,
        }
    return {
        "normalized_absolute_error_summary_by_role": by_role,
        "missing_number_rate": 0.0,
        "nonfinite_or_parse_failure_rate": 0.0,
        "sign_domain_violation_rate": 0.0,
        "validity_authority": False,
        "runtime_authority": False,
    }


class IndependentResultCompletenessAudit(unittest.TestCase):
    def test_full_42_relation_result_and_metrics_reconstruct_independently(self) -> None:
        for t2_calls in (42, 84):
            with self.subTest(t2_calls=t2_calls), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary)
                private = base / "recovery-private"
                public = base / "sanitized-public"
                private.mkdir()
                arguments = _arguments(private, public, t2_calls=t2_calls)
                result = finalize_successful_scientific_result_v3(**arguments)
                self.assertEqual(result.status, SUCCESS_STATUS)
                self.assertEqual(result.public_artifact_order[-1], "execution_receipt")
                self.assertEqual(set(result.public_artifact_hashes), set(PUBLIC_ARTIFACT_NAMES_V3))
                self.assertEqual(set(result.private_artifact_hashes), set(PRIVATE_ARTIFACT_NAMES_V3))

                for name in PUBLIC_ARTIFACT_NAMES_V3.values():
                    verify_public_artifact_v1(json.loads((public / name).read_text(encoding="utf-8")))
                private_root = private / "final_authoritative_v3"
                for name in PRIVATE_ARTIFACT_NAMES_V3.values():
                    verify_public_artifact_v1(json.loads((private_root / name).read_text(encoding="utf-8")))

                construction = json.loads((public / PUBLIC_ARTIFACT_NAMES_V3["construction_metrics"]).read_text(encoding="utf-8"))
                self.assertEqual(construction["main_metrics"], _manual_construction_metrics(arguments["outcome_records"]))
                direct = json.loads((public / PUBLIC_ARTIFACT_NAMES_V3["direct_number_metrics"]).read_text(encoding="utf-8"))
                expected_direct = _manual_direct_summary(arguments["direct_number_records"])
                for key, expected in expected_direct.items():
                    if isinstance(expected, dict):
                        self.assertEqual(set(direct[key]), set(expected))
                        for role, role_expected in expected.items():
                            for metric, value in role_expected.items():
                                if isinstance(value, float):
                                    self.assertTrue(math.isclose(direct[key][role][metric], value, rel_tol=1e-15, abs_tol=0.0))
                                else:
                                    self.assertEqual(direct[key][role][metric], value)
                    else:
                        self.assertEqual(direct[key], expected)
                summary = json.loads((public / PUBLIC_ARTIFACT_NAMES_V3["execution_summary"]).read_text(encoding="utf-8"))
                self.assertEqual(summary["scientific_calls"], 210 + t2_calls)
                self.assertEqual(summary["scientific_call_counts"]["T1-B"], 126)
                receipt = json.loads((public / PUBLIC_ARTIFACT_NAMES_V3["execution_receipt"]).read_text(encoding="utf-8"))
                self.assertEqual(receipt["artifact_hash"], result.execution_receipt_hash)
                self.assertEqual(receipt["construction_metrics_hash"], result.public_artifact_hashes["construction_metrics"])
                self.assertEqual(receipt["direct_number_metrics_hash"], result.public_artifact_hashes["direct_number_metrics"])
                self.assertEqual(receipt["private_ledger_bindings_hash"], result.public_artifact_hashes["private_bindings"])
                public_bytes = b"".join(path.read_bytes() for path in public.iterdir())
                self.assertNotIn(PRIVATE_SENTINEL.encode(), public_bytes)
                self.assertIn(PRIVATE_SENTINEL, (private_root / PRIVATE_ARTIFACT_NAMES_V3["proposal_validity"]).read_text(encoding="utf-8"))

    def test_receipt_is_last_and_receipt_absence_or_corruption_prevents_pass(self) -> None:
        for mode in ("missing", "corrupt"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary)
                private = base / "private"
                public = base / "public"
                private.mkdir()
                order: list[str] = []

                def writer(path: str | Path, document: dict[str, object]) -> dict[str, object]:
                    destination = Path(path)
                    order.append(destination.name)
                    written = write_public_artifact_atomic_v1(destination, document)
                    if destination.name == PUBLIC_ARTIFACT_NAMES_V3["execution_receipt"]:
                        if mode == "missing":
                            destination.unlink()
                        else:
                            destination.write_text("{}\n", encoding="utf-8")
                    return written

                arguments = _arguments(private, public)
                arguments["artifact_writer"] = writer
                with self.assertRaises(
                    (FileNotFoundError, RecoverySerializationError, TASK039E3RecoveryResultFinalizationV3Error)
                ):
                    finalize_successful_scientific_result_v3(**arguments)
                self.assertEqual(order[-1], PUBLIC_ARTIFACT_NAMES_V3["execution_receipt"])

    def test_public_private_root_overlap_matrix_and_git_cleanliness(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            repo = base / "repo"
            repo.mkdir()
            recovery = base / "recovery"
            recovery.mkdir()
            e1 = base / "e1"
            e1.mkdir()
            historical = base / "historical"
            historical.mkdir()
            cases = (
                (repo / "public", repo, recovery, (e1, historical)),
                (base, repo, recovery, (e1, historical)),
                (e1 / "public", repo, recovery, (e1, historical)),
                (base, repo, recovery, (base / "inside-public-e1", historical)),
                (historical / "public", repo, recovery, (e1, historical)),
                (base, repo, recovery, (e1, base / "inside-public-historical")),
                (recovery / "public", repo, recovery, (e1, historical)),
                (base, repo, base / "inside-public-recovery", (e1, historical)),
            )
            for public, repository, private, protected in cases:
                with self.subTest(public=str(public)), self.assertRaises(TASK039E3RecoveryResultFinalizationV3Error):
                    prepare_result_roots_v3(
                        repository_root=repository,
                        recovery_private_root=private,
                        public_output_root=public,
                        protected_private_roots=protected,
                    )

    def test_scientific_arm_entrypoints_are_frozen_imports(self) -> None:
        from paperworks.v6 import task039e3_orchestration_v1 as frozen
        from paperworks.v6 import task039e3_recovery_science_v2 as recovery
        from paperworks.v6 import task039e3_scientific_execution_v1 as scientific

        self.assertIs(recovery.run_t1_v1, frozen.run_t1_v1)
        self.assertIs(recovery.run_t1b_v1, frozen.run_t1b_v1)
        self.assertIs(recovery.run_t2_v1, frozen.run_t2_v1)
        self.assertIs(recovery.run_direct_number_v1, frozen.run_direct_number_v1)
        self.assertIs(recovery.run_real_t0_v1, scientific.run_real_t0_v1)
        source = subprocess.check_output(
            [
                "git",
                "-c",
                f"safe.directory={ROOT}",
                "show",
                "2653f2b7349a049f9ca4828d736dfea9462c4748:src/paperworks/v6/task039e3_recovery_science_v2.py",
            ],
            cwd=ROOT,
        )
        manifest = json.loads(
            (ROOT / "docs/task_reports/TASK-039E3_R1D2_SOURCE_FREEZE.json").read_text(encoding="utf-8")
        )
        expected = next(
            record["sha256"]
            for record in manifest["source_records"]
            if record["repository_path"] == "src/paperworks/v6/task039e3_recovery_science_v2.py"
        )
        self.assertEqual(hashlib.sha256(source).hexdigest(), expected)


if __name__ == "__main__":
    unittest.main()
