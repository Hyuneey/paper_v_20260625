from __future__ import annotations

import inspect
from pathlib import Path
import unittest

from paperworks.validation_v2 import exp05_runner_v1 as runner
from paperworks.validation_v2.schema_registry_v1 import (
    load_validation_v2_schema_registry_v1,
)


class Exp05PreparedBatchPerformanceTests(unittest.TestCase):
    def test_batch_entrypoint_and_validator_are_exported(self) -> None:
        self.assertTrue(callable(runner.execute_and_materialize_formal_v4_batch_v1))
        self.assertTrue(callable(runner.validate_evaluated_formal_v4_explanation_batch_v1))

    def test_batch_uses_safe_prepared_runtime_not_direct_runtime_loop(self) -> None:
        source = inspect.getsource(runner.execute_and_materialize_formal_v4_batch_v1)
        self.assertIn("execute_formal_v4_batch_v1", source)
        self.assertNotIn("execute_formal_v4_rule_v1(", source)
        final_runtime = source.index("execute_formal_v4_batch_v1")
        materialize = source.index("_materialize_formal_v4_runtime_trace_v1")
        self.assertLess(final_runtime, materialize)

    def test_batch_contract_does_not_replace_durable_unit_custody(self) -> None:
        source = inspect.getsource(runner._materialize_formal_v4_runtime_trace_v1)
        self.assertIn("EXP05_ONE_PATH_RUNNER_CONTRACT_HASH", source)
        self.assertIn("validate_evaluated_formal_v4_explanation_unit_v1", source)
        batch_source = inspect.getsource(runner.EvaluatedFormalV4ExplanationBatchV1)
        self.assertIn("ordered_unit_hashes", batch_source)
        self.assertIn("prepared_runtime_finalization_receipt_hash", batch_source)

    def test_batch_schema_is_wheel_portable(self) -> None:
        filenames = {
            record.filename for record in load_validation_v2_schema_registry_v1()
        }
        self.assertIn("exp05_evaluated_batch_v1.schema.json", filenames)

    def test_report_preserves_scientific_boundary(self) -> None:
        report = Path(
            "research_control_center/validation_v2/reports/"
            "EXP05_PREPARED_BATCH_PERFORMANCE_V2.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "IMPLEMENTED_SYNTHETIC_CONFORMANCE_PASS_NOT_YET_SCIENTIFICALLY_EXECUTED",
            report,
        )
        self.assertIn("test1/test2/held-out/label access: 0", report)
        self.assertIn("PILOT V1 변경: 0", report)
        self.assertIn("GPU 사용은 부적절", report)


if __name__ == "__main__":
    unittest.main()
