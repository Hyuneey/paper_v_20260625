from __future__ import annotations

import inspect
from pathlib import Path
import unittest

from paperworks.validation_v2 import isolation_forest_v1 as isolation
from paperworks.validation_v2 import pca_spe_v2 as pca


class DetectorStreamingHashPerformanceTests(unittest.TestCase):
    def test_helper_uses_buffer_view_without_full_tobytes_copy(self) -> None:
        source = inspect.getsource(isolation._sha256_contiguous_array_v1)
        self.assertIn("memoryview", source)
        self.assertIn('view.cast("B")', source)
        self.assertNotIn("tobytes", source)

    def test_all_detector_authority_hash_call_sites_use_helper(self) -> None:
        for function in (
            isolation._normalize_matrix_input,
            isolation.fit_isolation_forest_v1,
            isolation.calibrate_isolation_forest_threshold_v1,
            pca.calibrate_pca_spe_threshold_v2,
        ):
            with self.subTest(function=function.__name__):
                source = inspect.getsource(function)
                self.assertNotIn("tobytes", source)
                self.assertIn("_sha256_contiguous_array_v1", source)

    def test_report_preserves_scientific_boundary(self) -> None:
        report = Path(
            "research_control_center/validation_v2/reports/"
            "DETECTOR_STREAMING_HASH_PERFORMANCE_V2.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "IMPLEMENTED_SYNTHETIC_CONFORMANCE_PASS_NOT_YET_SCIENTIFICALLY_EXECUTED",
            report,
        )
        self.assertIn("test1/test2/held-out/label access: 0", report)
        self.assertIn("PILOT V1 변경: 0", report)
        self.assertIn("digest equality: PASS", report)


if __name__ == "__main__":
    unittest.main()
