from dataclasses import asdict, replace
from pathlib import Path
import unittest

from scripts import freeze_task039e3_r2r_inner_d2_v1_v2_scientific_disposition_v1 as s


class DispositionTests(unittest.TestCase):
    def setUp(self):
        self.e = s.EXPECTED
        self.d = s.derive_disposition(self.e)

    def test_d0_metrics(self):
        self.assertEqual(self.e.d0.recall, 0.7857142857142857)
        self.assertEqual(self.e.d0.normal_far_per_hour, 0.4939336325682589)

    def test_d1_metrics(self):
        self.assertEqual(self.e.d1.recall, 0.9285714285714286)
        self.assertEqual(self.e.d1.normal_far_per_hour, 40.50255787059723)

    def test_v1_metrics(self):
        self.assertEqual(self.e.d2_v1.recall, 0.7857142857142857)
        self.assertEqual(self.e.d2_v1.normal_far_per_hour, 0.7056194750975128)
        self.assertEqual(self.e.d2_v1.d0_misses_recovered, 0)

    def test_v2_metrics(self):
        self.assertEqual(self.e.d2_v2.recall, 0.7857142857142857)
        self.assertEqual(self.e.d2_v2.normal_far_per_hour, 6.915070855955625)
        self.assertEqual(self.e.d2_v2.d0_misses_recovered, 0)

    def test_d1_detects_all_d0_misses(self): self.assertEqual(self.e.d0_misses_detected_by_d1, 3)
    def test_union(self): self.assertEqual(self.e.d0_d1_union_coverage, 14)
    def test_recovery_zero(self):
        self.assertEqual(self.e.d2_v1.d0_misses_recovered, self.e.d2_v2.d0_misses_recovered)
    def test_recall_equal(self): self.assertEqual(self.e.d2_v1.recall, self.e.d2_v2.recall)
    def test_v1_far_lower(self): self.assertLess(self.e.d2_v1.normal_far_per_hour, self.e.d2_v2.normal_far_per_hour)
    def test_far_ratio(self): self.assertAlmostEqual(self.d.v2_v1_far_ratio, 9.8)
    def test_pareto(self): self.assertTrue(self.d.v1_pareto_dominates_v2)
    def test_v2_not_outer(self): self.assertNotIn("D2_V2", self.d.proposed_outer_arms)
    def test_v1_candidate_only(self): self.assertEqual(self.d.final_combined_candidate, s.V1_ID)
    def test_no_redesign(self): self.assertFalse(self.d.further_inner_fusion_redesign_recommended)
    def test_no_combined_improvement(self): self.assertFalse(self.d.combined_improvement_claim_supported)
    def test_three_outer_arms(self): self.assertEqual(self.d.proposed_outer_arm_count, 3)
    def test_outer_unauthorized(self): self.assertFalse(self.d.outer_authorized)
    def test_rule_complementary(self): self.assertTrue(self.d.rule_complementary_signal_supported)
    def test_rule_operational_false(self): self.assertFalse(self.d.rule_only_operational_utility_supported)
    def test_inner_closed(self): self.assertTrue(self.d.inner_fusion_development_closed)

    def test_mutation_rejected(self):
        with self.assertRaises(s.DispositionError):
            s.derive_disposition(replace(self.e, d2_v2=replace(self.e.d2_v2, recall=1.0)))

    def test_reports_build(self):
        reports, md = s.build_reports(self.e, self.d, "2026-08-23T00:00:00Z", 18, 0)
        self.assertEqual(len(reports), 10)
        self.assertIn(b"OUTER remains unauthorized", md)

    def test_duplicate_json_rejected(self):
        with self.assertRaises(s.DispositionError): s.strict_json(b'{"a":1,"a":2}')

    def test_hash_collision_rejected(self):
        with self.assertRaises(s.DispositionError): s.seal({"artifact_hash": "x"})

    def test_adversarial(self):
        attacks, accepted = s.adversarial_contract()
        self.assertEqual(accepted, 0); self.assertGreaterEqual(attacks, 18)

    def test_no_test_data_paths(self):
        source = Path(s.__file__).read_text("utf-8")
        for token in ("label-test1.csv", "test2.csv", "hai-23.05/test2"):
            self.assertNotIn(token, source)


if __name__ == "__main__": unittest.main()
