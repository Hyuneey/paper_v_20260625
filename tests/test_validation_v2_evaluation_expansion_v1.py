from __future__ import annotations

import csv
import unittest
from pathlib import Path

from paperworks.validation_v2.evaluation_expansion_v1 import (
    ETAPR_COMMIT,
    ETAPR_UPSTREAM,
    EvaluationExpansionError,
    binary_stream_to_closed_ranges_v1,
    mcnemar_exact_two_sided_v1,
    partition_hai21_train3_v1,
    validate_aligned_scenario_sets_v1,
    validate_etapr_freeze_v1,
    validate_panel_registry_v1,
    validate_version_separated_summary_v1,
    wilson_interval_95_v1,
)


ROOT = Path(__file__).resolve().parents[1]


class EvaluationExpansionContractTests(unittest.TestCase):
    def test_panel_registry_is_closed_and_future_panels_unopened(self) -> None:
        path = ROOT / "research_control_center/validation_v2/evaluation_expansion/PANEL_REGISTRY_V1.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            validate_panel_registry_v1(csv.DictReader(handle))

    def test_hai21_partition_is_chronological_and_purged(self) -> None:
        result = partition_hai21_train3_v1(101, 60)
        self.assertEqual(0, result.block_a_start)
        self.assertEqual(20, result.block_a_stop)
        self.assertEqual(80, result.block_b_start)
        self.assertEqual(101, result.block_b_stop)
        self.assertEqual(60, result.block_b_start - result.block_a_stop)

    def test_hai21_partition_rejects_impossible_purge(self) -> None:
        with self.assertRaises(EvaluationExpansionError):
            partition_hai21_train3_v1(20, 60)

    def test_wilson_interval_and_undefined_denominator(self) -> None:
        low, high = wilson_interval_95_v1(11, 14) or (None, None)
        self.assertAlmostEqual(0.524108, low, places=6)
        self.assertAlmostEqual(0.924286, high, places=6)
        self.assertIsNone(wilson_interval_95_v1(0, 0))

    def test_mcnemar_exact(self) -> None:
        self.assertEqual(0.625, mcnemar_exact_two_sided_v1(1, 3))
        self.assertIsNone(mcnemar_exact_two_sided_v1(0, 0))

    def test_pairing_requires_exact_scenario_identity(self) -> None:
        self.assertEqual(("A", "B"), validate_aligned_scenario_sets_v1(("A", "B"), ("A", "B")))
        with self.assertRaises(EvaluationExpansionError):
            validate_aligned_scenario_sets_v1(("A", "B"), ("B", "A"))

    def test_primary_pooled_recall_is_rejected(self) -> None:
        rows = ({"dataset_version": "23.05"}, {"dataset_version": "22.04"})
        validate_version_separated_summary_v1(rows, primary_pooled_recall=False)
        with self.assertRaises(EvaluationExpansionError):
            validate_version_separated_summary_v1(rows, primary_pooled_recall=True)

    def test_etapr_pin_and_no_point_adjustment(self) -> None:
        validate_etapr_freeze_v1({
            "upstream": ETAPR_UPSTREAM,
            "commit": ETAPR_COMMIT,
            "implementation_mode": "OFFICIAL_OR_CONFORMANCE_VERIFIED_WRAPPER",
            "attack_data_accessed": False,
            "point_adjustment": False,
            "theta_p": 0.5,
            "theta_r": 0.1,
            "delta": 0.0,
        })

    def test_etapr_range_conversion_is_inclusive_and_file_local(self) -> None:
        self.assertEqual(
            ((1, 2, "F:1"), (4, 4, "F:2")),
            binary_stream_to_closed_ranges_v1((False, True, True, False, True), file_id="F"),
        )
        self.assertEqual((), binary_stream_to_closed_ranges_v1((False, False), file_id="G"))


if __name__ == "__main__":
    unittest.main()
