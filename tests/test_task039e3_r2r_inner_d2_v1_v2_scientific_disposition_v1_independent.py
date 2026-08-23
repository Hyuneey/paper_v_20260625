from dataclasses import replace
from pathlib import Path
import unittest

from scripts import freeze_task039e3_r2r_inner_d2_v1_v2_scientific_disposition_v1 as s


class IndependentDispositionTests(unittest.TestCase):
    def reject(self, evidence):
        with self.assertRaises(s.DispositionError): s.derive_disposition(evidence)

    def test_d0_recall_attack(self): self.reject(replace(s.EXPECTED, d0=replace(s.EXPECTED.d0, recall=1.0)))
    def test_d1_far_attack(self): self.reject(replace(s.EXPECTED, d1=replace(s.EXPECTED.d1, normal_far_per_hour=0.0)))
    def test_v1_recovery_attack(self): self.reject(replace(s.EXPECTED, d2_v1=replace(s.EXPECTED.d2_v1, d0_misses_recovered=1)))
    def test_v2_recovery_attack(self): self.reject(replace(s.EXPECTED, d2_v2=replace(s.EXPECTED.d2_v2, d0_misses_recovered=1)))
    def test_union_attack(self): self.reject(replace(s.EXPECTED, d0_d1_union_coverage=13))
    def test_complementarity_attack(self): self.reject(replace(s.EXPECTED, d0_misses_detected_by_d1=2))
    def test_v2_selected_attack(self): self.assertNotEqual(s.derive_disposition(s.EXPECTED).final_combined_candidate, s.V2_ID)
    def test_v1_not_called_success(self): self.assertFalse(s.derive_disposition(s.EXPECTED).combined_incremental_utility_supported)
    def test_no_v3(self): self.assertFalse(s.derive_disposition(s.EXPECTED).further_inner_fusion_redesign_recommended)
    def test_outer_set_exact(self): self.assertEqual(s.derive_disposition(s.EXPECTED).proposed_outer_arms, s.OUTER_ARMS)
    def test_outer_disposition(self): self.assertEqual(s.derive_disposition(s.EXPECTED).outer_disposition, s.OUTER_DISPOSITION)
    def test_thesis_not_fatal(self): self.assertFalse(s.derive_disposition(s.EXPECTED).thesis_fatal_blocker)
    def test_claim_adjustment(self): self.assertTrue(s.derive_disposition(s.EXPECTED).thesis_claim_adjustment_required)
    def test_v2_ablation(self): self.assertEqual(s.derive_disposition(s.EXPECTED).d2_v2_disposition, s.V2_DISPOSITION)
    def test_supported_claims(self): self.assertIn("RULE_LAYER_HAS_DETECTOR_COMPLEMENTARY_EVENT_INFORMATION", s.SUPPORTED_CLAIMS)
    def test_unsupported_claims(self): self.assertIn("GENERALIZATION_TO_OUTER", s.UNSUPPORTED_CLAIMS)

    def test_no_execution_calls(self):
        source = Path(s.__file__).read_text("utf-8")
        for token in ("fusion_oracle(", "rule_reevaluation", "DetectorPrediction", "RulePrediction"):
            self.assertNotIn(token, source)

    def test_no_parameter_search(self):
        source = Path(s.__file__).read_text("utf-8")
        self.assertNotIn("parameter_sweep(", source)

    def test_no_push(self):
        source = Path(s.__file__).read_text("utf-8")
        self.assertNotIn('git("push"', source)

    def test_all_invalid_rejected(self):
        attacks, accepted = s.adversarial_contract()
        self.assertEqual((attacks, accepted), (18, 0))


if __name__ == "__main__": unittest.main()
