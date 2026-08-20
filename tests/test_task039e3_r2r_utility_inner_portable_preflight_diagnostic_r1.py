"""Synthetic tests for the path-silent portable preflight diagnostic harness."""

from __future__ import annotations

import importlib.util
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
SCRIPT = (
    ROOT / "scripts" / "audit_task039e3_r2r_inner_portable_preflight_failure_v1.py"
)
SPEC = importlib.util.spec_from_file_location("portable_preflight_diagnostic", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("diagnostic harness import unavailable")
diagnostic = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = diagnostic
SPEC.loader.exec_module(diagnostic)


class PortablePreflightDiagnosticR1Tests(unittest.TestCase):
    def _actions(self, failure_index: int | None = None):
        actions = []
        for index, name in enumerate(diagnostic.STAGE_NAMES):
            if index == failure_index:
                def fail() -> None:
                    print("forbidden-output")
                    raise RuntimeError("forbidden-private-path-and-value")

                actions.append((name, fail))
            else:
                actions.append((name, lambda: None))
        return tuple(actions)

    def test_all_fixed_stages_pass_without_dynamic_output(self) -> None:
        outcome = diagnostic.execute_stage_actions(self._actions())
        rendered = diagnostic.render_fixed_output(outcome)
        self.assertEqual(outcome.terminal_stage, "ALL_DIAGNOSTIC_STAGES_PASS")
        self.assertEqual(len(outcome.completed_stages), 21)
        self.assertNotIn("forbidden", rendered)
        self.assertTrue(rendered.endswith("ALL_DIAGNOSTIC_STAGES_PASS"))

    def test_every_stage_failure_is_localized_and_redacted(self) -> None:
        for index, name in enumerate(diagnostic.STAGE_NAMES):
            with self.subTest(stage=name):
                outcome = diagnostic.execute_stage_actions(self._actions(index))
                rendered = diagnostic.render_fixed_output(outcome)
                self.assertEqual(outcome.terminal_stage, name)
                self.assertEqual(
                    outcome.root_cause_class,
                    diagnostic.ROOT_CAUSE_BY_STAGE[name],
                )
                self.assertNotIn("forbidden", rendered)
                self.assertNotIn("RuntimeError", rendered)
                self.assertEqual(outcome.completed_stages[-1], (name, "BLOCK"))

    def test_invalid_stage_topology_fails_closed(self) -> None:
        outcome = diagnostic.execute_stage_actions(self._actions()[:-1])
        self.assertEqual(outcome.terminal_stage, "UNEXPECTED_FAIL_CLOSED")
        self.assertEqual(outcome.completed_stages, ())

    def test_binding_parser_accepts_only_approved_nonempty_keys(self) -> None:
        valid = "\n".join(
            f"{key}='synthetic-{index}'"
            for index, key in enumerate(diagnostic.APPROVED_BINDING_KEYS)
        )
        parsed = diagnostic._parse_binding_text(valid)
        self.assertEqual(set(parsed), set(diagnostic.APPROVED_BINDING_KEYS))
        with self.assertRaises(Exception):
            diagnostic._parse_binding_text(valid + "\nAPI_TOKEN='secret'\n")
        with self.assertRaises(Exception):
            diagnostic._parse_binding_text("HAI_DATA_ROOT=''\n")

    def test_main_entrypoint_suppresses_unexpected_exception(self) -> None:
        output = io.StringIO()
        with patch.object(diagnostic, "run_diagnostic", side_effect=RuntimeError("path")):
            with patch.object(sys, "argv", [str(SCRIPT)]):
                with patch("sys.stdout", output):
                    code = diagnostic.main()
        self.assertEqual(code, 2)
        self.assertEqual(
            output.getvalue().strip(),
            "DIAGNOSTIC_TERMINAL_STAGE=UNEXPECTED_FAIL_CLOSED",
        )
        self.assertNotIn("path", output.getvalue())


if __name__ == "__main__":
    unittest.main()
