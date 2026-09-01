from __future__ import annotations

import inspect
from pathlib import Path
import unittest

from paperworks.gdn import exp01_upstream_backend_v2 as gdn_backend
from paperworks.validation_v2 import evaluation_custody_v1 as evaluation_custody
from paperworks.validation_v2 import exp01_checkpoint_v2 as checkpoint
from paperworks.validation_v2 import formal_v4_authority_v1 as formal_v4
from paperworks.validation_v2 import io_hash_v1 as io_hash
from paperworks.validation_v2 import metric_contract_v1 as metric
from paperworks.validation_v2 import prediction_custody_v1 as prediction_custody
from paperworks.validation_v2 import private_feature_cache_v1 as feature_cache


class RemainingPerformanceClosureTests(unittest.TestCase):
    def test_bound_file_verification_uses_bounded_memory_hashing(self) -> None:
        self.assertIn("stream.read", inspect.getsource(io_hash.sha256_file_v1))
        self.assertNotIn("read_bytes", inspect.getsource(io_hash.sha256_file_v1))
        for function in (
            prediction_custody._verify_bound_bytes,
            evaluation_custody._verify_bound_files,
            formal_v4._file_sha256,
        ):
            with self.subTest(function=function.__name__):
                source = inspect.getsource(function)
                self.assertIn("sha256_file_v1", source)
                self.assertNotIn("read_bytes", source)

    def test_checkpoint_hashing_avoids_full_tensor_and_file_byte_copies(self) -> None:
        self.assertNotIn("tobytes", inspect.getsource(checkpoint.canonical_state_hash_v2))
        self.assertIn("memoryview", inspect.getsource(checkpoint.canonical_state_hash_v2))
        for function in (
            checkpoint.persist_private_checkpoint_v2,
            checkpoint.reopen_private_checkpoint_v2,
            checkpoint.recover_existing_private_checkpoint_v2,
        ):
            with self.subTest(function=function.__name__):
                self.assertNotIn("read_bytes", inspect.getsource(function))

    def test_gdn_sample_lookup_reuses_prepared_segment_tensors(self) -> None:
        constructor = inspect.getsource(gdn_backend._FileLocalLazyWindows.__init__)
        lookup = inspect.getsource(gdn_backend._FileLocalLazyWindows.__getitem__)
        self.assertIn("torch_module.as_tensor", constructor)
        self.assertNotIn("as_tensor", lookup)
        self.assertIn("history.transpose", lookup)

    def test_metric_overlap_is_linear_sweep_not_nested_any(self) -> None:
        helper = inspect.getsource(metric._match_event_episode_overlaps_v1)
        evaluator = inspect.getsource(metric.evaluate_common_timeline_v1)
        self.assertIn("while event_cursor", helper)
        self.assertNotIn("any(", helper)
        self.assertIn("_match_event_episode_overlaps_v1", evaluator)
        self.assertNotIn("any(_overlap", evaluator)

    def test_private_cache_is_normal_only_path_free_and_non_authoritative(self) -> None:
        source = inspect.getsource(feature_cache.persist_private_feature_cache_v1)
        receipt_source = inspect.getsource(feature_cache.PrivateFeatureCacheReceiptV1.body_document)
        self.assertIn("FEATURE_CACHE_ROOT_INSIDE_REPOSITORY_REJECTED", source)
        self.assertIn('"scientific_authority": False', receipt_source)
        self.assertIn('"test1_accesses": 0', receipt_source)
        self.assertIn('"test2_accesses": 0', receipt_source)
        self.assertNotIn("cache_path", receipt_source)

    def test_report_keeps_scientific_and_access_boundaries(self) -> None:
        report = Path(
            "research_control_center/validation_v2/reports/"
            "REMAINING_PERFORMANCE_CLOSURE_V2.md"
        ).read_text(encoding="utf-8")
        self.assertIn("scientific execution: 0", report)
        self.assertIn("test1/test2/held-out/label access: 0", report)
        self.assertIn("PILOT V1/frozen result change: 0", report)
        self.assertIn("private feature cache materialization: 0", report)


if __name__ == "__main__":
    unittest.main()
