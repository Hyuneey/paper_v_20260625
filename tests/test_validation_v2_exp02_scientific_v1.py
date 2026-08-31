from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from hashlib import sha256
import json
import unittest

from paperworks.validation_v2.exp02_scientific_v1 import (
    EXP02_CANDIDATE_COUNT,
    EXP02_PUBLIC_AUTHORITY_STATE,
    EXP02_SELECTION_NAMESPACE,
    CandidateEvaluationStateV1,
    Exp02OperationV1,
    Exp02ScientificError,
    Exp02ScientificStageV1,
    advance_exp02_scientific_state_v1,
    assert_exp02_split_allowed_v1,
    build_atomic_freeze_evidence_v1,
    build_candidate_evaluation_receipt_v1,
    build_candidate_set_freeze_receipt_v1,
    build_formal_v4_numeric_authority_public_receipt_v1,
    build_private_summary_hash_receipt_v1,
    build_selection_decision_receipt_v1,
    build_train4_evaluation_bundle_v1,
    build_v2_confirmed_cohort_binding_v1,
    freeze_selected_policy_v1,
    start_exp02_scientific_state_v1,
    validate_candidate_set_freeze_receipt_v1,
    validate_formal_v4_numeric_authority_public_receipt_v1,
    validate_private_summary_hash_receipts_v1,
    validate_selected_policy_freeze_receipt_v1,
    validate_selection_decision_receipt_v1,
    validate_train4_evaluation_bundle_v1,
    validate_v2_confirmed_cohort_binding_v1,
)
from paperworks.validation_v2.numeric_policy_v1 import (
    ConfirmedRelationIdentityV1,
    build_confirmed_cohort_authority_v1,
    build_normal_policy_selection_authority_v1,
    build_numeric_policy_candidate_set_v1,
    build_numeric_policy_selection_summary_v1,
    candidate_set_hash_v1,
    select_numeric_policy_on_train4_v1,
)
from paperworks.validation_v2.protocol_v1 import build_validation_protocol_v1


def h(label: str) -> str:
    return sha256(label.encode("utf-8")).hexdigest()


def body_hash(document) -> str:
    return sha256(
        json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


COMMIT = "1" * 40


class Exp02ScientificV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.protocol = build_validation_protocol_v1(source_commit=COMMIT)
        relations = (
            ConfirmedRelationIdentityV1("r1", "s1", "t1", "step_up", "increase", 5, h("r1")),
            ConfirmedRelationIdentityV1("r2", "s2", "t2", "step_down", "decrease", 10, h("r2")),
        )
        self.cohort = build_confirmed_cohort_authority_v1(
            cohort_id="V2-EXP02-COHORT", source_commit=COMMIT,
            confirmation_artifact_hash=h("confirmation"), relations=relations,
        )
        self.cohort_binding = build_v2_confirmed_cohort_binding_v1(self.cohort)
        self.train_receipts = tuple(
            build_private_summary_hash_receipt_v1(
                split_id=split, cohort=self.cohort_binding,
                private_summary_bundle_hash=h(f"private-{split}"),
            )
            for split in ("train1", "train2")
        )
        self.train_receipts_hash = validate_private_summary_hash_receipts_v1(
            self.train_receipts, cohort=self.cohort_binding,
            expected_receipt_hashes={item.split_id: item.self_hash for item in self.train_receipts},
        )
        self.candidates = build_numeric_policy_candidate_set_v1(
            cohort=self.cohort, normal_fit_input_hash=self.train_receipts_hash,
            source_commit=COMMIT,
        )
        self.candidate_receipt = build_candidate_set_freeze_receipt_v1(
            candidates=self.candidates, cohort=self.cohort_binding,
            fit_summary_receipts_hash=self.train_receipts_hash,
        )
        self.selection_authority = build_normal_policy_selection_authority_v1(
            protocol=self.protocol, candidate_set_hash=candidate_set_hash_v1(self.candidates),
            cohort_hash=self.cohort.cohort_hash, cohort_relations=2,
            train4_input_hash=h("train4-input"), normal_exposure_seconds=3600,
            metric_contract_hash=h("metric"),
        )
        self.summaries = tuple(self._summary(candidate) for candidate in self.candidates)
        self.evaluations = tuple(
            build_candidate_evaluation_receipt_v1(
                candidate=candidate, summary=summary,
                selection_authority=self.selection_authority, protocol=self.protocol,
            )
            for candidate, summary in zip(self.candidates, self.summaries)
        )
        self.evaluation_bundle = build_train4_evaluation_bundle_v1(
            candidates=self.candidates, candidate_set_receipt=self.candidate_receipt,
            evaluations=self.evaluations, selection_authority=self.selection_authority,
            summaries=self.summaries, protocol=self.protocol,
        )
        self.result = select_numeric_policy_on_train4_v1(
            candidates=self.candidates, summaries=self.summaries,
            selection_authority=self.selection_authority, protocol=self.protocol,
        )
        self.decision = build_selection_decision_receipt_v1(
            result=self.result, candidates=self.candidates,
            selection_authority=self.selection_authority, protocol=self.protocol,
            evaluation_bundle=self.evaluation_bundle,
            candidate_set_receipt=self.candidate_receipt,
            cohort=self.cohort_binding, summaries=self.summaries,
        )
        self.public_authority = build_formal_v4_numeric_authority_public_receipt_v1(
            authority_artifact_id="V2-EXP02-FORMAL-V4-NUMERIC",
            authority_artifact_hash=h("private-numeric-authority"),
            decision=self.decision, cohort=self.cohort_binding,
        )

    def _summary(
        self, candidate, *, errors: int = 0, unsupported: int = 0,
        false_alarm_seconds: int = 10,
    ):
        return build_numeric_policy_selection_summary_v1(
            candidate=candidate, selection_authority=self.selection_authority,
            protocol=self.protocol, retained_relations=2, cohort_relations=2,
            opportunity_relations=2, pass_count=90, fail_count=10,
            abstain_count=0, system_error_count=errors,
            unsupported_relation_count=unsupported, false_alarm_seconds=false_alarm_seconds,
            false_alarm_episodes=2, normal_exposure_seconds=3600,
            split_variability=Fraction(1, 10),
        )

    def test_test1_and_heldout_are_prohibited_for_every_operation(self) -> None:
        for operation in Exp02OperationV1:
            for split in ("test1", "test2", "future_heldout"):
                with self.subTest(operation=operation, split=split), self.assertRaisesRegex(
                    Exp02ScientificError, "SPLIT_PROHIBITED"
                ):
                    assert_exp02_split_allowed_v1(split_id=split, operation=operation)

    def test_cohort_binding_is_hash_only_and_external_identity_rejects_rehash(self) -> None:
        self.assertEqual(self.cohort_binding.confirmation_split, "train3")
        self.assertEqual(self.cohort_binding.relation_count, 2)
        self.assertEqual(
            validate_v2_confirmed_cohort_binding_v1(
                self.cohort_binding, cohort=self.cohort,
                expected_receipt_hash=self.cohort_binding.self_hash,
            ), self.cohort_binding.self_hash,
        )
        other_cohort = build_confirmed_cohort_authority_v1(
            cohort_id="V2-EXP02-OTHER", source_commit=COMMIT,
            confirmation_artifact_hash=h("other"), relations=self.cohort.relations,
        )
        coordinated = build_v2_confirmed_cohort_binding_v1(other_cohort)
        with self.assertRaisesRegex(Exp02ScientificError, "COHORT_STALE"):
            validate_v2_confirmed_cohort_binding_v1(
                coordinated, cohort=other_cohort,
                expected_receipt_hash=self.cohort_binding.self_hash,
            )

    def test_private_summary_receipts_are_exact_train1_train2_and_public_safe(self) -> None:
        document = json.dumps([item.to_dict() for item in self.train_receipts])
        self.assertNotIn("source_scope_noise", document)
        self.assertNotIn("target_scope_noise", document)
        self.assertNotIn("\\\\", document)
        self.assertFalse(any(item.contains_numeric_values for item in self.train_receipts))
        self.assertFalse(any(item.contains_private_paths for item in self.train_receipts))

    def test_private_summary_partial_stale_and_mutated_receipts_fail(self) -> None:
        expected = {item.split_id: item.self_hash for item in self.train_receipts}
        with self.assertRaisesRegex(Exp02ScientificError, "SUMMARY_SPLIT_COVERAGE"):
            validate_private_summary_hash_receipts_v1(
                self.train_receipts[:1], cohort=self.cohort_binding,
                expected_receipt_hashes=expected,
            )
        with self.assertRaisesRegex(Exp02ScientificError, "SUMMARY_STALE"):
            validate_private_summary_hash_receipts_v1(
                self.train_receipts, cohort=self.cohort_binding,
                expected_receipt_hashes={**expected, "train1": h("stale")},
            )
        changed = replace(self.train_receipts[0], contains_numeric_values=True)
        with self.assertRaisesRegex(Exp02ScientificError, "SUMMARY_REPLAY_MISMATCH"):
            validate_private_summary_hash_receipts_v1(
                (changed, self.train_receipts[1]), cohort=self.cohort_binding,
                expected_receipt_hashes=expected,
            )

    def test_exact_37_candidate_set_and_selection_only_namespace(self) -> None:
        self.assertEqual(len(self.candidates), EXP02_CANDIDATE_COUNT)
        self.assertEqual(self.candidate_receipt.candidate_count, 37)
        self.assertEqual(self.candidate_receipt.authority_namespace, EXP02_SELECTION_NAMESPACE)
        self.assertTrue(self.candidate_receipt.selection_only)
        self.assertFalse(self.candidate_receipt.runtime_authority)
        self.assertFalse(self.candidate_receipt.labels_allowed)
        validate_candidate_set_freeze_receipt_v1(
            self.candidate_receipt, candidates=self.candidates,
            cohort=self.cohort_binding, fit_summary_receipts_hash=self.train_receipts_hash,
            expected_receipt_hash=self.candidate_receipt.self_hash,
        )

    def test_partial_candidate_set_and_wrong_external_identity_fail(self) -> None:
        with self.assertRaisesRegex(Exception, "CANDIDATE_GRID_INCOMPLETE|CANDIDATE_COUNT"):
            build_candidate_set_freeze_receipt_v1(
                candidates=self.candidates[:-1], cohort=self.cohort_binding,
                fit_summary_receipts_hash=self.train_receipts_hash,
            )
        with self.assertRaisesRegex(Exp02ScientificError, "CANDIDATE_STALE"):
            validate_candidate_set_freeze_receipt_v1(
                self.candidate_receipt, candidates=self.candidates,
                cohort=self.cohort_binding, fit_summary_receipts_hash=self.train_receipts_hash,
                expected_receipt_hash=h("stale"),
            )

    def test_train4_bundle_covers_every_candidate_without_numeric_payload(self) -> None:
        self.assertEqual(self.evaluation_bundle.candidate_count, 37)
        self.assertEqual(self.evaluation_bundle.evaluated_count, 37)
        self.assertEqual(self.evaluation_bundle.failed_count, 0)
        self.assertFalse(self.evaluation_bundle.contains_numeric_values)
        validate_train4_evaluation_bundle_v1(
            self.evaluation_bundle, candidates=self.candidates,
            candidate_set_receipt=self.candidate_receipt,
            selection_authority=self.selection_authority,
            summaries=self.summaries, protocol=self.protocol,
            expected_bundle_hash=self.evaluation_bundle.self_hash,
        )

    def test_train4_explicit_failures_cannot_be_hidden(self) -> None:
        failed_summary = self._summary(self.candidates[0], errors=1)
        with self.assertRaisesRegex(Exp02ScientificError, "FAILURE_HIDDEN"):
            build_candidate_evaluation_receipt_v1(
                candidate=self.candidates[0], summary=failed_summary,
                selection_authority=self.selection_authority,
                protocol=self.protocol,
            )
        explicit = build_candidate_evaluation_receipt_v1(
            candidate=self.candidates[0], summary=failed_summary,
            selection_authority=self.selection_authority, protocol=self.protocol,
            issue_codes=("SYSTEM_ERROR_NONZERO",),
        )
        self.assertIs(explicit.state, CandidateEvaluationStateV1.FAILED)

    def test_partial_duplicate_and_mutated_evaluation_bundle_fail(self) -> None:
        with self.assertRaisesRegex(Exp02ScientificError, "EVALUATION_COVERAGE"):
            build_train4_evaluation_bundle_v1(
                candidates=self.candidates, candidate_set_receipt=self.candidate_receipt,
                evaluations=self.evaluations[:-1], selection_authority=self.selection_authority,
                summaries=self.summaries, protocol=self.protocol,
            )
        duplicated = self.evaluations[:-1] + (self.evaluations[0],)
        with self.assertRaisesRegex(Exp02ScientificError, "EVALUATION_COVERAGE"):
            build_train4_evaluation_bundle_v1(
                candidates=self.candidates, candidate_set_receipt=self.candidate_receipt,
                evaluations=duplicated, selection_authority=self.selection_authority,
                summaries=self.summaries, protocol=self.protocol,
            )
        changed = replace(self.evaluations[0], issue_codes=("SYSTEM_ERROR_NONZERO",))
        with self.assertRaisesRegex(Exp02ScientificError, "EVALUATION_ROW_MUTATED"):
            build_train4_evaluation_bundle_v1(
                candidates=self.candidates, candidate_set_receipt=self.candidate_receipt,
                evaluations=(changed,) + self.evaluations[1:],
                selection_authority=self.selection_authority,
                summaries=self.summaries, protocol=self.protocol,
            )
        coordinated_summary = self._summary(self.candidates[0], false_alarm_seconds=11)
        coordinated_row = build_candidate_evaluation_receipt_v1(
            candidate=self.candidates[0], summary=coordinated_summary,
            selection_authority=self.selection_authority, protocol=self.protocol,
        )
        with self.assertRaisesRegex(Exp02ScientificError, "ROW_REPLAY_MISMATCH"):
            build_train4_evaluation_bundle_v1(
                candidates=self.candidates, candidate_set_receipt=self.candidate_receipt,
                evaluations=(coordinated_row,) + self.evaluations[1:],
                selection_authority=self.selection_authority,
                summaries=self.summaries, protocol=self.protocol,
            )

    def test_selection_decision_binds_result_evaluation_and_external_identity(self) -> None:
        validate_selection_decision_receipt_v1(
            self.decision, result=self.result, candidates=self.candidates,
            selection_authority=self.selection_authority, protocol=self.protocol,
            evaluation_bundle=self.evaluation_bundle,
            candidate_set_receipt=self.candidate_receipt,
            cohort=self.cohort_binding, summaries=self.summaries,
            expected_receipt_hash=self.decision.self_hash,
        )
        with self.assertRaisesRegex(Exp02ScientificError, "DECISION_STALE"):
            validate_selection_decision_receipt_v1(
                self.decision, result=self.result, candidates=self.candidates,
                selection_authority=self.selection_authority, protocol=self.protocol,
                evaluation_bundle=self.evaluation_bundle,
                candidate_set_receipt=self.candidate_receipt,
                cohort=self.cohort_binding, summaries=self.summaries,
                expected_receipt_hash=h("other-decision"),
            )

    def test_public_v4_authority_is_count_hash_only_and_not_runtime_authority(self) -> None:
        self.assertEqual(self.public_authority.relation_count, 2)
        self.assertEqual(self.public_authority.numeric_role_count, 10)
        self.assertEqual(self.public_authority.binding_count, 20)
        self.assertEqual(self.public_authority.state, EXP02_PUBLIC_AUTHORITY_STATE)
        self.assertFalse(self.public_authority.runtime_authorized)
        document = json.dumps(self.public_authority.to_dict())
        self.assertNotIn('"values":', document)
        self.assertNotIn("relative_path", document)
        validate_formal_v4_numeric_authority_public_receipt_v1(
            self.public_authority, decision=self.decision,
            cohort=self.cohort_binding,
            expected_receipt_hash=self.public_authority.self_hash,
        )

    def test_public_authority_rejects_private_path_mutation_and_stale_identity(self) -> None:
        with self.assertRaisesRegex(Exp02ScientificError, "PUBLIC_ID_INVALID"):
            build_formal_v4_numeric_authority_public_receipt_v1(
                authority_artifact_id="C:\\private\\authority.json",
                authority_artifact_hash=h("authority"), decision=self.decision,
                cohort=self.cohort_binding,
            )
        with self.assertRaisesRegex(Exp02ScientificError, "PUBLIC_AUTHORITY_STALE"):
            validate_formal_v4_numeric_authority_public_receipt_v1(
                self.public_authority, decision=self.decision,
                cohort=self.cohort_binding, expected_receipt_hash=h("stale"),
            )

    def test_public_authority_rejects_valid_decision_from_unrelated_cohort(self) -> None:
        other = build_confirmed_cohort_authority_v1(
            cohort_id="V2-EXP02-UNRELATED", source_commit=COMMIT,
            confirmation_artifact_hash=h("unrelated-confirmation"), relations=self.cohort.relations,
        )
        with self.assertRaisesRegex(Exp02ScientificError, "AUTHORITY_COHORT_MISMATCH"):
            build_formal_v4_numeric_authority_public_receipt_v1(
                authority_artifact_id="V2-EXP02-FOREIGN",
                authority_artifact_hash=h("foreign-authority"),
                decision=self.decision,
                cohort=build_v2_confirmed_cohort_binding_v1(other),
            )

    def test_atomic_freeze_callback_proves_write_fsync_close_and_reopen(self) -> None:
        def persist(payload: bytes):
            return build_atomic_freeze_evidence_v1(
                artifact_id="V2-EXP02-SELECTED-POLICY", payload=payload,
                reopened_bytes_sha256=sha256(payload).hexdigest(),
                atomic_replace_completed=True, fsync_completed=True,
                close_completed=True, reopen_completed=True,
            )

        frozen = freeze_selected_policy_v1(
            artifact_id="V2-EXP02-SELECTED-POLICY", decision=self.decision,
            numeric_authority=self.public_authority, persist_and_reopen=persist,
        )
        self.assertTrue(frozen.frozen)
        self.assertFalse(frozen.runtime_authorized)
        self.assertFalse(frozen.label_access_authorized)
        validate_selected_policy_freeze_receipt_v1(
            frozen, decision=self.decision, numeric_authority=self.public_authority,
            expected_receipt_hash=frozen.self_hash,
        )

    def test_partial_write_reopen_mismatch_and_foreign_evidence_fail(self) -> None:
        payload = b"payload"
        with self.assertRaisesRegex(Exp02ScientificError, "FREEZE_SEQUENCE_INCOMPLETE"):
            build_atomic_freeze_evidence_v1(
                artifact_id="a", payload=payload,
                reopened_bytes_sha256=sha256(payload).hexdigest(),
                atomic_replace_completed=True, fsync_completed=False,
                close_completed=True, reopen_completed=True,
            )
        with self.assertRaisesRegex(Exp02ScientificError, "FREEZE_REOPEN_MISMATCH"):
            build_atomic_freeze_evidence_v1(
                artifact_id="a", payload=payload, reopened_bytes_sha256=h("different"),
                atomic_replace_completed=True, fsync_completed=True,
                close_completed=True, reopen_completed=True,
            )

        def foreign(payload_bytes: bytes):
            return build_atomic_freeze_evidence_v1(
                artifact_id="FOREIGN", payload=payload_bytes,
                reopened_bytes_sha256=sha256(payload_bytes).hexdigest(),
                atomic_replace_completed=True, fsync_completed=True,
                close_completed=True, reopen_completed=True,
            )

        with self.assertRaisesRegex(Exp02ScientificError, "FREEZE_EVIDENCE_FOREIGN"):
            freeze_selected_policy_v1(
                artifact_id="V2-EXP02-SELECTED-POLICY", decision=self.decision,
                numeric_authority=self.public_authority, persist_and_reopen=foreign,
            )

        def coordinated_forgery(payload_bytes: bytes):
            valid = build_atomic_freeze_evidence_v1(
                artifact_id="V2-EXP02-SELECTED-POLICY", payload=payload_bytes,
                reopened_bytes_sha256=sha256(payload_bytes).hexdigest(),
                atomic_replace_completed=True, fsync_completed=True,
                close_completed=True, reopen_completed=True,
            )
            forged = replace(
                valid, byte_count=1, reopened_bytes_sha256=h("wrong-reopen"),
                fsync_completed=False, close_completed=False, reopen_completed=False,
                evidence_hash="",
            )
            return replace(forged, evidence_hash=body_hash(forged.body_dict()))

        with self.assertRaisesRegex(Exp02ScientificError, "FREEZE_EVIDENCE_FOREIGN"):
            freeze_selected_policy_v1(
                artifact_id="V2-EXP02-SELECTED-POLICY", decision=self.decision,
                numeric_authority=self.public_authority, persist_and_reopen=coordinated_forgery,
            )

    def test_freeze_receipt_mutation_and_external_staleness_fail(self) -> None:
        def persist(payload: bytes):
            return build_atomic_freeze_evidence_v1(
                artifact_id="selected", payload=payload,
                reopened_bytes_sha256=sha256(payload).hexdigest(),
                atomic_replace_completed=True, fsync_completed=True,
                close_completed=True, reopen_completed=True,
            )

        frozen = freeze_selected_policy_v1(
            artifact_id="selected", decision=self.decision,
            numeric_authority=self.public_authority, persist_and_reopen=persist,
        )
        with self.assertRaisesRegex(Exp02ScientificError, "FREEZE_RECEIPT_MUTATED"):
            validate_selected_policy_freeze_receipt_v1(
                replace(frozen, runtime_authorized=True), decision=self.decision,
                numeric_authority=self.public_authority,
                expected_receipt_hash=frozen.self_hash,
            )
        with self.assertRaisesRegex(Exp02ScientificError, "FREEZE_RECEIPT_STALE"):
            validate_selected_policy_freeze_receipt_v1(
                frozen, decision=self.decision, numeric_authority=self.public_authority,
                expected_receipt_hash=h("stale-freeze"),
            )

    def test_state_machine_rejects_skips_repeats_and_mutation(self) -> None:
        state = start_exp02_scientific_state_v1(self.protocol)
        with self.assertRaisesRegex(Exp02ScientificError, "STATE_ORDER"):
            advance_exp02_scientific_state_v1(
                state, next_stage=Exp02ScientificStageV1.CANDIDATES_FROZEN,
                artifact_hash=h("skip"), protocol=self.protocol,
            )
        for stage in tuple(Exp02ScientificStageV1)[1:]:
            state = advance_exp02_scientific_state_v1(
                state, next_stage=stage, artifact_hash=h(stage.value), protocol=self.protocol,
            )
        self.assertIs(state.stage, Exp02ScientificStageV1.POLICY_DURABLY_FROZEN)
        self.assertEqual(len(state.bound_artifact_hashes), 7)
        with self.assertRaisesRegex(Exp02ScientificError, "STATE_MUTATED"):
            advance_exp02_scientific_state_v1(
                replace(state, protocol_hash=h("mutated")),
                next_stage=Exp02ScientificStageV1.POLICY_DURABLY_FROZEN,
                artifact_hash=h("again"), protocol=self.protocol,
            )

        early = start_exp02_scientific_state_v1(self.protocol)
        coordinated = replace(early, protocol_hash=h("foreign-protocol"), self_hash="")
        coordinated = replace(coordinated, self_hash=body_hash(coordinated.body_dict()))
        with self.assertRaisesRegex(Exp02ScientificError, "STATE_AUTHORITY_MISMATCH"):
            advance_exp02_scientific_state_v1(
                coordinated, next_stage=Exp02ScientificStageV1.COHORT_BOUND,
                artifact_hash=h("cohort"), protocol=self.protocol,
            )

    def test_selection_rejects_failed_candidate_listed_as_eligible(self) -> None:
        failed_summary = self._summary(self.candidates[0], errors=1)
        failed_row = build_candidate_evaluation_receipt_v1(
            candidate=self.candidates[0], summary=failed_summary,
            selection_authority=self.selection_authority, protocol=self.protocol,
            issue_codes=("SYSTEM_ERROR_NONZERO",),
        )
        summaries = (failed_summary, *self.summaries[1:])
        bundle = build_train4_evaluation_bundle_v1(
            candidates=self.candidates, candidate_set_receipt=self.candidate_receipt,
            evaluations=(failed_row, *self.evaluations[1:]),
            selection_authority=self.selection_authority, summaries=summaries,
            protocol=self.protocol,
        )
        with self.assertRaisesRegex(Exp02ScientificError, "SELECTION_REPLAY_FAILED|SELECTION_EVALUATION_PARTITION_MISMATCH"):
            build_selection_decision_receipt_v1(
                result=self.result, candidates=self.candidates,
                selection_authority=self.selection_authority, protocol=self.protocol,
                evaluation_bundle=bundle, candidate_set_receipt=self.candidate_receipt,
                cohort=self.cohort_binding, summaries=summaries,
            )


if __name__ == "__main__":
    unittest.main()
