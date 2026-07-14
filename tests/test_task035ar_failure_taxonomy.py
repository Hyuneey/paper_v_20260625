from __future__ import annotations

import unittest
from pathlib import Path

from experiments.argos_reproduction.task035a_failure_taxonomy import classify_failure


class Task035arFailureTaxonomyTests(unittest.TestCase):
    def test_visible_and_runtime_categories_are_sanitized(self):
        base_provider = {"capture_status": "provider_response_captured"}
        self.assertEqual(classify_failure(provider={"capture_status": "response_without_rule"}, static={}, runtime={"terminal_status": "response_without_rule"}, response_text=None), "no_visible_output")
        self.assertEqual(classify_failure(provider=base_provider, static={}, runtime={"terminal_status": "response_without_rule"}, response_text="plain text"), "visible_output_no_python_fence")
        self.assertEqual(classify_failure(provider=base_provider, static={}, runtime={"terminal_status": "runtime_failed", "timed_out": True}, response_text="private"), "runtime_timeout")
        self.assertEqual(classify_failure(provider=base_provider, static={}, runtime={"terminal_status": "runtime_failed", "timed_out": False}, response_text="private"), "runtime_exception")

    def test_taxonomy_source_does_not_emit_private_content(self):
        from experiments.argos_reproduction import task035a_failure_taxonomy as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        self.assertNotIn("exception_message", source)
        self.assertNotIn("rule_source", source)


if __name__ == "__main__": unittest.main()
