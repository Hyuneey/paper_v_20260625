from __future__ import annotations

import inspect
from pathlib import Path
import unittest

from paperworks.validation_v2 import exp02_runner_v1 as runner


class Exp02PerformanceFoundationTests(unittest.TestCase):
    def test_single_parse_and_batch_boundaries_are_exported(self) -> None:
        self.assertTrue(callable(runner.prepare_exp02_fit_splits_once_v1))
        self.assertTrue(callable(runner.build_exp02_fit_summary_batch_once_v1))
        self.assertTrue(callable(
            runner.prepare_exp02_train4_once_after_candidate_freeze_v1
        ))
        self.assertTrue(callable(runner.evaluate_exp02_candidate_batch_once_v1))

    def test_train4_path_requires_candidate_closure_before_open(self) -> None:
        source = inspect.getsource(
            runner.prepare_exp02_train4_once_after_candidate_freeze_v1
        )
        closure_check = source.index("closed_before_train4")
        split_open = source.index("execute_authorized_split_open_v1")
        self.assertLess(closure_check, split_open)
        self.assertIn('split_id="train4"', source)

    def test_batch_contract_keeps_exact_frozen_denominator(self) -> None:
        source = inspect.getsource(runner.evaluate_exp02_candidate_batch_once_v1)
        self.assertIn("len(candidate_tuple) != 37", source)
        self.assertIn("evaluator(", source)
        self.assertIn("full_coverage=True", source)
        self.assertNotIn("test1", source.lower())
        self.assertNotIn("test2", source.lower())

    def test_report_keeps_scientific_execution_blocked(self) -> None:
        report = Path(
            "research_control_center/validation_v2/reports/"
            "EXP02_PERFORMANCE_FOUNDATION_V2.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "IMPLEMENTED_SYNTHETIC_ONLY_SCIENTIFIC_BINDINGS_STILL_REQUIRED",
            report,
        )
        self.assertIn("EXP02-BIND-QUANTILE", report)
        self.assertIn("scientific execution: 0", report)
        self.assertIn("PILOT V1 change: 0", report)


if __name__ == "__main__":
    unittest.main()
