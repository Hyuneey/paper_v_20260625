from __future__ import annotations

import unittest
from experiments.argos_reproduction.multi_rule_static_audit import audit_response


class Task035aStaticAuditTests(unittest.TestCase):
    def test_safe_numpy_rule_passes(self):
        report, _ = audit_response("```python\nimport numpy as np\ndef inference(sample):\n    return np.zeros(len(sample), dtype=int)\n```")
        self.assertEqual(report["static_status"], "static_valid")

    def test_file_and_process_calls_fail(self):
        for call in ("open('x')", "__import__('os').system('x')", "np.load('x')"):
            report, _ = audit_response(f"```python\nimport numpy as np\ndef inference(sample):\n    {call}\n    return np.zeros(len(sample), dtype=int)\n```")
            self.assertEqual(report["static_status"], "static_invalid")

    def test_hardcoded_label_array_fails(self):
        report, _ = audit_response("```python\nimport numpy as np\ndef inference(sample):\n    return [0,1,0,1]\n```")
        self.assertTrue(report["hardcoded_index_or_label_suspicion"])


if __name__ == "__main__": unittest.main()
