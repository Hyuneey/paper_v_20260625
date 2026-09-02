from __future__ import annotations

import unittest

from paperworks.validation_v2.exp01b_functional_v1 import (
    EdgeMaskEvidenceV1,
    Exp01BFunctionalError,
    file_local_block_permutation_v1,
    matched_random_controls_v1,
    occlusion_seed_v1,
    relative_delta_mse_v1,
    remove_exact_edge_without_refill_v1,
    target_specific_mse_v1,
    verify_attention_capture_invariance_v1,
)


class Exp01BFunctionalTests(unittest.TestCase):
    def test_target_specific_edge_mask_arithmetic_and_no_refill(self) -> None:
        self.assertEqual(target_specific_mse_v1((1.0, 3.0), (1.0, 1.0)), 2.0)
        delta = relative_delta_mse_v1(baseline_target_mse=2.0, masked_target_mse=3.0)
        evidence = EdgeMaskEvidenceV1(
            edge=("S1", "T1"), view="TRAIN1_TRAIN2_COMBINED", seed=11,
            baseline_target_mse=2.0, masked_target_mse=3.0, relative_delta_mse=delta,
        )
        self.assertGreater(evidence.relative_delta_mse, 0)
        self.assertEqual(
            remove_exact_edge_without_refill_v1((("S1", "T1"), ("S2", "T1")), edge=("S1", "T1")),
            (("S2", "T1"),),
        )

    def test_random_control_is_target_matched_and_deterministic(self) -> None:
        graph = (("S1", "T1"), ("S2", "T1"), ("S3", "T1"), ("S1", "T2"))
        first = matched_random_controls_v1(
            focal_edges=(("S1", "T1"),), eligible_graph_edges=graph, seed=11,
        )
        second = matched_random_controls_v1(
            focal_edges=(("S1", "T1"),), eligible_graph_edges=graph, seed=11,
        )
        self.assertEqual(first, second)
        self.assertEqual(first[("S1", "T1")][0][1], "T1")

    def test_source_occlusion_is_file_local_marginal_preserving_and_nonidentity(self) -> None:
        original = tuple(float(value) for value in range(15))
        permuted = file_local_block_permutation_v1(original, seed=23)
        self.assertCountEqual(permuted, original)
        self.assertNotEqual(permuted, original)
        self.assertEqual(permuted, file_local_block_permutation_v1(original, seed=23))
        self.assertEqual(
            occlusion_seed_v1(view="TRAIN1_ONLY", run_seed=23, file_id="train4", source="P1_FCV01D"),
            occlusion_seed_v1(view="TRAIN1_ONLY", run_seed=23, file_id="train4", source="P1_FCV01D"),
        )

    def test_attention_capture_must_preserve_predictions(self) -> None:
        verify_attention_capture_invariance_v1((1.0, 2.0), (1.0, 2.0000001), atol=1e-6, rtol=1e-6)
        with self.assertRaisesRegex(Exp01BFunctionalError, "changed prediction"):
            verify_attention_capture_invariance_v1((1.0,), (2.0,), atol=1e-7, rtol=1e-6)


if __name__ == "__main__":
    unittest.main()
