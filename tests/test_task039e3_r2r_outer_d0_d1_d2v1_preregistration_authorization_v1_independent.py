from __future__ import annotations

from dataclasses import replace
import unittest

from paperworks.v6 import task039e3_r2r_outer_d0_d1_d2v1_preregistration_authorization_v1 as m


class OuterAuthorizationIndependentAttacks(unittest.TestCase):
    def setUp(self) -> None:
        self.p = m.get_outer_preregistration()

    def attack(self, value: m.OuterThreeArmPreregistrationV1) -> None:
        with self.assertRaises(m.OuterAuthorizationError):
            m.validate_preregistration(value)

    def test_01_feature_substitution(self): self.attack(replace(self.p, dataset=replace(self.p.dataset, test2_feature_sha256="f" * 64)))
    def test_02_label_substitution(self): self.attack(replace(self.p, dataset=replace(self.p.dataset, test2_label_sha256="f" * 64)))
    def test_03_row_count_substitution(self): self.attack(replace(self.p, dataset=replace(self.p.dataset, row_count=230399)))
    def test_04_d0_model_substitution(self): self.attack(replace(self.p, d0=replace(self.p.d0, model_sha256="f" * 64)))
    def test_05_d0_threshold_substitution(self): self.attack(replace(self.p, d0=replace(self.p.d0, threshold_sha256="f" * 64)))
    def test_06_d0_model_refit(self): self.attack(replace(self.p, d0=replace(self.p.d0, refit_authorized=True)))
    def test_07_d1_portfolio_substitution(self): self.attack(replace(self.p, d1=replace(self.p.d1, portfolio="COMMON-41")))
    def test_08_one_rule_deletion(self): self.attack(replace(self.p, d1=replace(self.p.d1, relation_count=41)))
    def test_09_one_rule_addition(self): self.attack(replace(self.p, d1=replace(self.p.d1, relation_count=43)))
    def test_10_one_rule_numeric_change(self): self.attack(replace(self.p, d1=replace(self.p.d1, private_registry_sha256="1" * 64)))
    def test_11_evaluator_change(self): self.attack(replace(self.p, d1=replace(self.p.d1, evaluator_identity="1" * 64)))
    def test_12_d2_v2_substitution(self): self.attack(replace(self.p, d2_v1=replace(self.p.d2_v1, d2_id="D2_V2")))
    def test_13_source_count_one(self): self.attack(replace(self.p, d2_v1=replace(self.p.d2_v1, required_distinct_source_count=1)))
    def test_14_source_count_three(self): self.attack(replace(self.p, d2_v1=replace(self.p.d2_v1, required_distinct_source_count=3)))
    def test_15_window_insertion(self): self.attack(replace(self.p, d2_v1=replace(self.p.d2_v1, temporal_corroboration_policy="PLUS_MINUS_WINDOW")))
    def test_16_d0_score_gating(self): self.attack(replace(self.p, d2_v1=replace(self.p.d2_v1, d0_score_dependency=True)))
    def test_17_label_aware_fusion(self): self.attack(replace(self.p, d2_v1=replace(self.p.d2_v1, label_aware_fusion=True)))
    def test_18_label_opened_before_d2_freeze(self): self.attack(replace(self.p, ordering=replace(self.p.ordering, all_predictions_frozen_and_reopened_before_label=False)))
    def test_19_test2_tuning(self): self.attack(replace(self.p, d1=replace(self.p.d1, rule_recalibration_authorized=True)))
    def test_20_second_outer_attempt(self): self.attack(replace(self.p, one_shot=replace(self.p.one_shot, coordinated_outer_scientific_attempts=2)))
    def test_21_result_driven_retry(self): self.attack(replace(self.p, one_shot=replace(self.p.one_shot, retry_after_feature_semantic_parse_authorized=True)))
    def test_22_post_outer_redesign(self): self.attack(replace(self.p, no_post_outer_development=False))


if __name__ == "__main__":
    unittest.main()
