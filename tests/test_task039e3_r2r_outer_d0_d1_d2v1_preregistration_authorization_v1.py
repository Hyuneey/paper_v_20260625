from __future__ import annotations

from dataclasses import replace
import unittest

from paperworks.v6 import task039e3_r2r_outer_d0_d1_d2v1_preregistration_authorization_v1 as m


class OuterPreregistrationAuthorizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.p = m.get_outer_preregistration()

    def reject(self, value: m.OuterThreeArmPreregistrationV1) -> None:
        with self.assertRaises(m.OuterAuthorizationError):
            m.validate_preregistration(value)

    def test_01_exact_feature_manifest_sha(self): self.assertEqual(self.p.dataset.test2_feature_sha256, m.TEST2_FEATURE_SHA256)
    def test_02_exact_label_manifest_sha(self): self.assertEqual(self.p.dataset.test2_label_sha256, m.TEST2_LABEL_SHA256)
    def test_03_exact_rows(self): self.assertEqual(self.p.dataset.row_count, 230400)
    def test_04_exact_arm_set(self): self.assertEqual(self.p.arms, m.OUTER_ARMS)
    def test_05_d0_exact_design(self): self.assertEqual(self.p.d0.design_sha256, m.D0_DESIGN_SHA256)
    def test_06_d0_exact_model(self): self.assertEqual(self.p.d0.model_sha256, m.D0_MODEL_SHA256)
    def test_07_d0_exact_threshold(self): self.assertEqual(self.p.d0.threshold_sha256, m.D0_THRESHOLD_SHA256)
    def test_08_d0_refit_rejected(self): self.reject(replace(self.p, d0=replace(self.p.d0, refit_authorized=True)))
    def test_09_d0_recalibration_rejected(self): self.reject(replace(self.p, d0=replace(self.p.d0, recalibration_authorized=True)))
    def test_10_d1_common42_exact(self): self.assertEqual((self.p.d1.portfolio, self.p.d1.relation_count), ("COMMON-42", 42))
    def test_11_d1_rule_mutation_rejected(self): self.reject(replace(self.p, d1=replace(self.p.d1, relation_count=41)))
    def test_12_d1_numeric_mutation_rejected(self): self.reject(replace(self.p, d1=replace(self.p.d1, descriptor_sha256="0" * 64)))
    def test_13_evaluator_substitution_rejected(self): self.reject(replace(self.p, d1=replace(self.p.d1, evaluator_identity="0" * 64)))
    def test_14_d2_v1_exact(self): self.assertEqual(self.p.d2_v1.design_sha256, m.D2_V1_DESIGN_SHA256)
    def test_15_d2_v2_rejected(self): self.reject(replace(self.p, d2_v1=replace(self.p.d2_v1, d2_v2_execution_authorized=True)))
    def test_16_d2_source_map_exact(self): self.assertEqual(self.p.d2_v1.source_map_sha256, m.D2_SOURCE_MAP_SHA256)
    def test_17_source_count_one_rejected(self): self.reject(replace(self.p, d2_v1=replace(self.p.d2_v1, required_distinct_source_count=1)))
    def test_18_source_count_three_rejected(self): self.reject(replace(self.p, d2_v1=replace(self.p.d2_v1, required_distinct_source_count=3)))
    def test_19_temporal_tolerance_rejected(self): self.reject(replace(self.p, d2_v1=replace(self.p.d2_v1, temporal_tolerance_seconds=1)))
    def test_20_native_horizon_rejected(self): self.reject(replace(self.p, d2_v1=replace(self.p.d2_v1, native_horizon_memory=True)))
    def test_21_d0_suppression_rejected(self): self.reject(replace(self.p, d2_v1=replace(self.p.d2_v1, d0_preservation_policy="SUPPRESS_D0")))
    def test_22_label_before_predictions_rejected(self): self.reject(replace(self.p, ordering=replace(self.p.ordering, label_open_step=15)))
    def test_23_prediction_order_rejected(self): self.reject(replace(self.p, ordering=replace(self.p.ordering, execution_order=tuple(reversed(self.p.ordering.execution_order)))))
    def test_24_primary_metric_mutation_rejected(self): self.reject(replace(self.p, metrics=replace(self.p.metrics, primary_metrics=("OTHER",))))
    def test_25_weighted_score_rejected(self): self.reject(replace(self.p, metrics=replace(self.p.metrics, weighted_score_authorized=True)))
    def test_26_preregistration_test2_access_rejected(self): self.reject(replace(self.p, dataset=replace(self.p.dataset, preregistration_test2_feature_accesses=1)))
    def test_27_second_outer_execution_rejected(self): self.reject(replace(self.p, one_shot=replace(self.p.one_shot, coordinated_outer_scientific_attempts=2)))
    def test_28_retry_authorization_rejected(self): self.reject(replace(self.p, one_shot=replace(self.p.one_shot, coordinated_outer_scientific_retries=1)))
    def test_29_post_outer_redesign_rejected(self): self.reject(replace(self.p, one_shot=replace(self.p.one_shot, post_outer_redesign_authorized=True)))
    def test_30_preregistration_hash_stable(self): self.assertEqual(m.outer_preregistration_hash(self.p), m.stable_hash(m.asdict(self.p)))
    def test_31_caller_reconstruction_rejected_for_issuance(self):
        reconstructed = replace(self.p)
        self.assertIsNot(reconstructed, self.p)
        with self.assertRaises(m.OuterAuthorizationError):
            m.issue_outer_execution_authorization(reconstructed)


if __name__ == "__main__":
    unittest.main()
