from __future__ import annotations

import inspect
from pathlib import Path
import unittest

from paperworks.validation_v2 import runtime_v1


class FormalV4PreparedRuntimePerformanceTests(unittest.TestCase):
    def test_prepared_runtime_has_start_execute_finalize_boundary(self) -> None:
        self.assertTrue(callable(runtime_v1.execute_formal_v4_batch_v1))
        self.assertTrue(callable(runtime_v1.prepare_formal_v4_runtime_session_v1))
        self.assertTrue(callable(runtime_v1.execute_prepared_formal_v4_rule_v1))
        self.assertTrue(callable(runtime_v1.finalize_formal_v4_runtime_session_v1))

    def test_window_execution_has_no_file_or_authority_replay_call(self) -> None:
        source = inspect.getsource(runtime_v1.execute_prepared_formal_v4_rule_v1)
        self.assertNotIn("read_bytes", source)
        self.assertNotIn("load_formal_v4_numeric", source)
        self.assertNotIn("validate_formal_v4_runtime_authorization", source)
        self.assertIn("_execute_with_prepared_parameters_v1", source)

    def test_finalization_replays_authority_after_disabling_session(self) -> None:
        source = inspect.getsource(runtime_v1.finalize_formal_v4_runtime_session_v1)
        disabled = source.index("session._state.active = False")
        replay = source.index("validate_formal_v4_runtime_authorization_v1")
        self.assertLess(disabled, replay)
        self.assertIn("bound_bytes_unchanged=True", source)

    def test_report_preserves_scientific_boundary(self) -> None:
        report = Path(
            "research_control_center/validation_v2/reports/"
            "FORMAL_V4_PREPARED_RUNTIME_PERFORMANCE_V2.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "IMPLEMENTED_SYNTHETIC_CONFORMANCE_PASS_NOT_YET_SCIENTIFICALLY_EXECUTED",
            report,
        )
        self.assertIn("PILOT V1 변경: 0", report)
        self.assertIn("test1/test2/held-out/label access: 0", report)
        self.assertIn("GPU 사용은 부적절", report)


if __name__ == "__main__":
    unittest.main()
