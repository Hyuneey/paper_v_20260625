from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from hashlib import sha256
import unittest

from paperworks.validation_v2.numeric_policy_v1 import (
    COMMON_FORMULA_IDS,
    EXP02_FIT_SPLITS,
    EXP02_PROVIDER_CALLS_REQUIRED,
    FIT_SPLIT_VARIABILITY_STATISTIC,
    ExactRatioV1,
    ConfirmedRelationIdentityV1,
    DiagnosticNumericProposalV1,
    NumericPolicyError,
    NumericPolicyFamilyV1,
    build_confirmed_cohort_authority_v1,
    build_normal_policy_selection_authority_v1,
    build_numeric_policy_candidate_set_v1,
    build_numeric_policy_selection_summary_v1,
    build_split_normal_summary_v1,
    candidate_set_hash_v1,
    derive_role_values_for_split_v1,
    derive_pooled_role_values_v1,
    fit_split_variability_v1,
    frozen_relation_specific_grid_v1,
    select_numeric_policy_on_train4_v1,
    symmetric_relative_difference_v1,
    validate_confirmed_cohort_authority_v1,
    validate_normal_policy_selection_authority_v1,
    validate_numeric_policy_candidate_v1,
    validate_numeric_policy_selection_result_v1,
)
from paperworks.validation_v2.protocol_v1 import build_validation_protocol_v1


def h(label: str) -> str:
    return sha256(label.encode("utf-8")).hexdigest()


COMMIT = "1" * 40


class NumericPolicyV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.protocol = build_validation_protocol_v1(source_commit=COMMIT)
        relations = (
            ConfirmedRelationIdentityV1(
                "r2", "s2", "t2", "step_down", "decrease", 10, h("binding-r2")
            ),
            ConfirmedRelationIdentityV1(
                "r1", "s1", "t1", "step_up", "increase", 5, h("binding-r1")
            ),
        )
        self.cohort = build_confirmed_cohort_authority_v1(
            cohort_id="V2-TRAIN3-CONFIRMED-COHORT-001",
            source_commit=COMMIT,
            confirmation_artifact_hash=h("train3-confirmation"),
            relations=relations,
        )
        self.candidates = build_numeric_policy_candidate_set_v1(
            cohort=self.cohort,
            normal_fit_input_hash=h("train1-train2-normal-input"),
            source_commit=COMMIT,
        )
        self.authority = build_normal_policy_selection_authority_v1(
            protocol=self.protocol,
            candidate_set_hash=candidate_set_hash_v1(self.candidates),
            cohort_hash=self.cohort.cohort_hash,
            cohort_relations=len(self.cohort.relations),
            train4_input_hash=h("train4-normal-input"),
            normal_exposure_seconds=3600,
            metric_contract_hash=h("metric-contract"),
        )

    def _summary(self, split: str, *, scale: float = 1.0):
        return build_split_normal_summary_v1(
            split_id=split, relation_id="r1", source="s1", target="t1",
            source_scope_noise=1.0 * scale,
            source_scope_quantiles=(2.0 * scale, 4.0 * scale, 8.0 * scale),
            target_scope_noise=0.5 * scale,
            relation_noise=0.8 * scale,
            relation_quantiles=(1.5 * scale, 3.5 * scale, 7.5 * scale),
            relation_target_noise=0.4 * scale,
        )

    def _selection_summary(
        self, candidate, *, retained: int = 2, opportunities: int = 2,
        pass_count: int = 90, fail_count: int = 10, abstain_count: int = 0,
        errors: int = 0, unsupported: int = 0, seconds: int = 10, episodes: int = 2,
        exposure: int = 3600, variability: Fraction = Fraction(1, 10),
    ):
        return build_numeric_policy_selection_summary_v1(
            candidate=candidate, selection_authority=self.authority,
            protocol=self.protocol,
            retained_relations=retained, cohort_relations=2,
            opportunity_relations=opportunities, pass_count=pass_count,
            fail_count=fail_count, abstain_count=abstain_count,
            system_error_count=errors, unsupported_relation_count=unsupported,
            false_alarm_seconds=seconds,
            false_alarm_episodes=episodes, normal_exposure_seconds=exposure,
            split_variability=variability,
        )

    def test_closed_grid_and_provider_free_main_path(self) -> None:
        self.assertFalse(EXP02_PROVIDER_CALLS_REQUIRED)
        self.assertEqual(len(frozen_relation_specific_grid_v1()), 36)
        self.assertEqual(len(self.candidates), 37)
        self.assertEqual(self.candidates[0].family, NumericPolicyFamilyV1.COMMON_FIXED_NORMALIZED_V1)
        self.assertEqual(self.candidates[0].formula_ids, COMMON_FORMULA_IDS)
        self.assertEqual(EXP02_FIT_SPLITS, ("train1", "train2"))
        self.assertIn("both_zero=0", FIT_SPLIT_VARIABILITY_STATISTIC)

    def test_train3_cohort_is_separate_sorted_and_self_hashed(self) -> None:
        self.assertEqual(tuple(item.relation_id for item in self.cohort.relations), ("r1", "r2"))
        self.assertEqual(self.cohort.confirmation_split, "train3")
        self.assertEqual(validate_confirmed_cohort_authority_v1(self.cohort), self.cohort.cohort_hash)
        with self.assertRaisesRegex(NumericPolicyError, "COHORT_REPLAY_MISMATCH"):
            validate_confirmed_cohort_authority_v1(replace(self.cohort, cohort_id="changed"))

    def test_only_train1_train2_can_build_normal_derivation_summary(self) -> None:
        for forbidden in ("train3", "train4", "test1", "test2", "future_heldout"):
            with self.subTest(forbidden=forbidden), self.assertRaisesRegex(
                NumericPolicyError, "NUMERIC_FIT_SPLIT_PROHIBITED"
            ):
                self._summary(forbidden)

    def test_nonfinite_wrong_type_and_unordered_quantiles_fail_closed(self) -> None:
        with self.assertRaisesRegex(NumericPolicyError, "FLOAT_INVALID"):
            build_split_normal_summary_v1(
                split_id="train1", relation_id="r", source="s", target="t",
                source_scope_noise=float("nan"), source_scope_quantiles=(1.0, 2.0, 3.0),
                target_scope_noise=1.0, relation_noise=1.0,
                relation_quantiles=(1.0, 2.0, 3.0), relation_target_noise=1.0,
            )
        with self.assertRaisesRegex(NumericPolicyError, "FLOAT_INVALID"):
            build_split_normal_summary_v1(
                split_id="train1", relation_id="r", source="s", target="t",
                source_scope_noise=1, source_scope_quantiles=(1.0, 2.0, 3.0),  # type: ignore[arg-type]
                target_scope_noise=1.0, relation_noise=1.0,
                relation_quantiles=(1.0, 2.0, 3.0), relation_target_noise=1.0,
            )
        with self.assertRaisesRegex(NumericPolicyError, "QUANTILE_ORDER_INVALID"):
            build_split_normal_summary_v1(
                split_id="train1", relation_id="r", source="s", target="t",
                source_scope_noise=1.0, source_scope_quantiles=(3.0, 2.0, 1.0),
                target_scope_noise=1.0, relation_noise=1.0,
                relation_quantiles=(1.0, 2.0, 3.0), relation_target_noise=1.0,
            )

    def test_common_and_relation_specific_formulas_are_unit_normalized(self) -> None:
        split = self._summary("train1")
        common = dict(derive_role_values_for_split_v1(candidate=self.candidates[0], summary=split))
        # max(5*1, Q75=4) and max(3*1, 0.1*5)
        self.assertEqual(common["source_step_threshold"], 5.0)
        self.assertEqual(common["source_stability_tolerance"], 3.0)
        self.assertEqual(common["target_noise_scale"], 0.5)
        relation = next(
            item for item in self.candidates
            if item.candidate_id.endswith("n3-q0.50-s2-f0.05")
        )
        values = dict(derive_role_values_for_split_v1(candidate=relation, summary=split))
        self.assertAlmostEqual(values["source_step_threshold"], 2.4)
        self.assertEqual(values["source_stability_tolerance"], 1.6)
        self.assertEqual(values["target_noise_scale"], 0.4)
        self.assertEqual(tuple(values), tuple(role for role, _ in self.candidates[0].role_scopes))

    def test_role_scopes_are_exact_and_family_specific(self) -> None:
        common_scopes = dict(self.candidates[0].role_scopes)
        relation_scopes = dict(self.candidates[1].role_scopes)
        self.assertEqual(common_scopes["source_step_threshold"], "SOURCE")
        self.assertEqual(common_scopes["target_noise_scale"], "TARGET")
        self.assertEqual(relation_scopes["source_step_threshold"], "RELATION")
        self.assertEqual(relation_scopes["target_noise_scale"], "RELATION")
        self.assertEqual(common_scopes["target_response_window_seconds"], "GLOBAL")

    def test_fit_split_variability_is_exact_relation_local_max_symmetric_difference(self) -> None:
        self.assertEqual(symmetric_relative_difference_v1(0.0, 0.0), Fraction(0, 1))
        self.assertEqual(symmetric_relative_difference_v1(1.0, 2.0), Fraction(2, 3))
        observed = fit_split_variability_v1(
            candidate=self.candidates[0],
            summaries=(self._summary("train1", scale=1.0), self._summary("train2", scale=2.0)),
        )
        self.assertEqual(observed, Fraction(2, 3))
        other = build_split_normal_summary_v1(
            split_id="train2", relation_id="other", source="s1", target="t1",
            source_scope_noise=1.0, source_scope_quantiles=(2.0, 4.0, 8.0),
            target_scope_noise=0.5, relation_noise=0.8,
            relation_quantiles=(1.5, 3.5, 7.5), relation_target_noise=0.4,
        )
        with self.assertRaisesRegex(NumericPolicyError, "CROSS_RELATION_VARIABILITY_PROHIBITED"):
            fit_split_variability_v1(
                candidate=self.candidates[0], summaries=(self._summary("train1"), other)
            )
        pooled = dict(derive_pooled_role_values_v1(
            candidate=self.candidates[0],
            summaries=(self._summary("train1", scale=1.0), self._summary("train2", scale=2.0)),
        ))
        self.assertEqual(pooled["source_step_threshold"], 10.0)
        self.assertEqual(pooled["source_stability_tolerance"], 6.0)

    def test_candidate_replay_rejects_formula_scope_and_authority_mutation(self) -> None:
        candidate = self.candidates[0]
        for changed in (
            replace(candidate, formula_ids=("raw_unit_threshold=7",)),
            replace(candidate, role_scopes=candidate.role_scopes[:-1]),
            replace(candidate, runtime_authority=True),
            replace(candidate, normal_fit_input_hash=h("stale")),
        ):
            with self.subTest(changed=changed), self.assertRaisesRegex(
                NumericPolicyError, "CANDIDATE_REPLAY_MISMATCH"
            ):
                validate_numeric_policy_candidate_v1(changed)

    def test_train4_authority_is_selection_only_not_runtime_or_label_authority(self) -> None:
        self.assertTrue(self.authority.selection_only)
        self.assertFalse(self.authority.runtime_authority)
        self.assertFalse(self.authority.labels_allowed)
        self.assertEqual(
            validate_normal_policy_selection_authority_v1(self.authority, protocol=self.protocol),
            self.authority.authority_hash,
        )
        with self.assertRaisesRegex(NumericPolicyError, "SELECTION_AUTHORITY_REPLAY_MISMATCH"):
            validate_normal_policy_selection_authority_v1(
                replace(self.authority, runtime_authority=True), protocol=self.protocol
            )
        with self.assertRaisesRegex(NumericPolicyError, "SELECTION_AUTHORITY_REPLAY_MISMATCH"):
            validate_normal_policy_selection_authority_v1(
                self.authority, protocol=build_validation_protocol_v1(source_commit="2" * 40)
            )

    def test_empty_denominators_are_explicitly_undefined_not_zero(self) -> None:
        ratio = ExactRatioV1.build(0, 0, empty_reason="ZERO_NORMAL_EXPOSURE")
        self.assertFalse(ratio.defined)
        self.assertEqual(ratio.undefined_reason, "ZERO_NORMAL_EXPOSURE")
        with self.assertRaisesRegex(NumericPolicyError, "UNDEFINED_RATIO_ACCESS"):
            _ = ratio.fraction

    def test_strict_guard_rejects_relation_deletion_and_coverage_loss(self) -> None:
        summaries = [self._selection_summary(item) for item in self.candidates]
        summaries[1] = self._selection_summary(
            self.candidates[1], retained=1, opportunities=1, seconds=0, episodes=0
        )
        result = select_numeric_policy_on_train4_v1(
            candidates=self.candidates, summaries=tuple(summaries),
            selection_authority=self.authority, protocol=self.protocol,
        )
        rejected = dict(result.rejected)
        self.assertEqual(rejected[self.candidates[1].candidate_hash], "STRICT_NONINFERIORITY_GUARD_FAILED")

    def test_complete_tie_selects_common_and_is_input_order_independent(self) -> None:
        summaries = tuple(self._selection_summary(item) for item in self.candidates)
        forward = select_numeric_policy_on_train4_v1(
            candidates=self.candidates, summaries=summaries, selection_authority=self.authority,
            protocol=self.protocol,
        )
        reverse = select_numeric_policy_on_train4_v1(
            candidates=tuple(reversed(self.candidates)), summaries=tuple(reversed(summaries)),
            selection_authority=self.authority, protocol=self.protocol,
        )
        self.assertEqual(forward.selected_candidate_id, "COMMON_FIXED_NORMALIZED_V1")
        self.assertEqual(forward.to_dict(), reverse.to_dict())

    def test_lower_train4_false_firing_can_select_relation_candidate(self) -> None:
        summaries = [self._selection_summary(item) for item in self.candidates]
        summaries[1] = self._selection_summary(self.candidates[1], seconds=1, episodes=1)
        result = select_numeric_policy_on_train4_v1(
            candidates=self.candidates, summaries=summaries, selection_authority=self.authority,
            protocol=self.protocol,
        )
        self.assertEqual(result.selected_candidate_id, self.candidates[1].candidate_id)

    def test_system_error_is_never_coerced_to_abstain_or_no_alarm(self) -> None:
        summaries = [self._selection_summary(item) for item in self.candidates]
        summaries[1] = self._selection_summary(self.candidates[1], errors=1, seconds=0, episodes=0)
        result = select_numeric_policy_on_train4_v1(
            candidates=self.candidates, summaries=summaries, selection_authority=self.authority,
            protocol=self.protocol,
        )
        self.assertEqual(dict(result.rejected)[self.candidates[1].candidate_hash], "SYSTEM_ERROR_NONZERO")

        summaries = [self._selection_summary(item) for item in self.candidates]
        summaries[1] = self._selection_summary(self.candidates[1], unsupported=1, seconds=0, episodes=0)
        result = select_numeric_policy_on_train4_v1(
            candidates=self.candidates, summaries=summaries, selection_authority=self.authority,
            protocol=self.protocol,
        )
        self.assertEqual(
            dict(result.rejected)[self.candidates[1].candidate_hash],
            "UNSUPPORTED_RELATION_NONZERO",
        )

    def test_common_baseline_explicit_failure_stops_selection(self) -> None:
        summaries = [self._selection_summary(item) for item in self.candidates]
        summaries[0] = self._selection_summary(self.candidates[0], errors=1)
        with self.assertRaisesRegex(NumericPolicyError, "BASELINE_EXPLICIT_FAILURE"):
            select_numeric_policy_on_train4_v1(
                candidates=self.candidates, summaries=summaries, selection_authority=self.authority,
                protocol=self.protocol,
            )

    def test_undefined_baseline_opportunity_fails_selection_closed(self) -> None:
        summaries = [self._selection_summary(item) for item in self.candidates]
        summaries[0] = self._selection_summary(
            self.candidates[0], retained=0, opportunities=0,
            pass_count=0, fail_count=0, abstain_count=0,
        )
        with self.assertRaisesRegex(NumericPolicyError, "SELECTION_METRIC_UNDEFINED"):
            select_numeric_policy_on_train4_v1(
                candidates=self.candidates, summaries=summaries,
                selection_authority=self.authority, protocol=self.protocol,
            )

    def test_foreign_or_incomplete_summary_set_fails_closed(self) -> None:
        summaries = tuple(self._selection_summary(item) for item in self.candidates)
        with self.assertRaisesRegex(NumericPolicyError, "SUMMARY_COVERAGE_INVALID"):
            select_numeric_policy_on_train4_v1(
                candidates=self.candidates, summaries=summaries[:-1],
                selection_authority=self.authority, protocol=self.protocol,
            )
        stale_authority = build_normal_policy_selection_authority_v1(
            protocol=self.protocol,
            candidate_set_hash=self.authority.candidate_set_hash,
            cohort_hash=self.authority.cohort_hash,
            cohort_relations=self.authority.cohort_relations,
            train4_input_hash=h("other-train4-input"),
            normal_exposure_seconds=self.authority.normal_exposure_seconds,
            metric_contract_hash=self.authority.metric_contract_hash,
        )
        with self.assertRaisesRegex(NumericPolicyError, "SELECTION_AUTHORITY_REPLAY_MISMATCH|SUMMARY_REPLAY_MISMATCH"):
            select_numeric_policy_on_train4_v1(
                candidates=self.candidates, summaries=summaries,
                selection_authority=stale_authority, protocol=self.protocol,
            )

    def test_optional_llm_diagnostic_cannot_gain_authority(self) -> None:
        diagnostic = DiagnosticNumericProposalV1("diag", h("receipt"))
        self.assertFalse(diagnostic.validity_authority)
        self.assertFalse(diagnostic.runtime_authority)
        with self.assertRaisesRegex(NumericPolicyError, "DIAGNOSTIC_AUTHORITY_ESCALATION"):
            DiagnosticNumericProposalV1("diag", h("receipt"), runtime_authority=True)

    def test_authority_booleans_are_exact_and_summary_denominators_are_bound(self) -> None:
        for change in (
            {"selection_only": 1}, {"runtime_authority": 0}, {"labels_allowed": 0},
        ):
            with self.subTest(change=change), self.assertRaisesRegex(
                NumericPolicyError, "SELECTION_AUTHORITY_BOOLEAN_INVALID"
            ):
                replace(self.authority, **change)
        with self.assertRaisesRegex(NumericPolicyError, "COHORT_CARDINALITY_MISMATCH"):
            build_numeric_policy_selection_summary_v1(
                candidate=self.candidates[0], selection_authority=self.authority,
                protocol=self.protocol, retained_relations=1, cohort_relations=1,
                opportunity_relations=1, pass_count=1, fail_count=0, abstain_count=0,
                system_error_count=0, false_alarm_seconds=0, false_alarm_episodes=0,
                normal_exposure_seconds=3600, split_variability=Fraction(0, 1),
            )
        with self.assertRaisesRegex(NumericPolicyError, "SELECTION_EXPOSURE_MISMATCH"):
            self._selection_summary(self.candidates[0], exposure=3599)
        with self.assertRaisesRegex(NumericPolicyError, "EPISODES_EXCEED_SECONDS"):
            self._selection_summary(self.candidates[0], seconds=1, episodes=2)

    def test_selection_result_hash_and_partition_replay(self) -> None:
        summaries = tuple(self._selection_summary(item) for item in self.candidates)
        result = select_numeric_policy_on_train4_v1(
            candidates=self.candidates, summaries=summaries,
            selection_authority=self.authority, protocol=self.protocol,
        )
        self.assertEqual(
            result.result_hash,
            validate_numeric_policy_selection_result_v1(
                result, candidates=self.candidates,
                selection_authority=self.authority, protocol=self.protocol,
            ),
        )
        with self.assertRaisesRegex(NumericPolicyError, "RESULT_HASH_MISMATCH"):
            validate_numeric_policy_selection_result_v1(
                replace(result, selected_candidate_id="FORGED"),
                candidates=self.candidates, selection_authority=self.authority,
                protocol=self.protocol,
            )


if __name__ == "__main__":
    unittest.main()
