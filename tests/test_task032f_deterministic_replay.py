from __future__ import annotations

import unittest
from pathlib import Path

from paperworks.contracts import verify_task032f_deterministic_replay


ROOT = Path(__file__).resolve().parents[1]


class Task032FDeterministicReplayTests(unittest.TestCase):
    def test_two_fresh_complete_runs_are_hash_identical(self) -> None:
        result = verify_task032f_deterministic_replay(
            ROOT / "configs/contracts/task032f_synthetic_vertical_slice.json"
        )
        self.assertEqual(result["status"], "deterministic_replay_verified")
        self.assertEqual(result["fresh_runs"], 2)
        self.assertTrue(result["fixture_hashes_unchanged"])
        self.assertTrue(result["reports_byte_equivalent"])
        self.assertEqual(result["first_report_hash"], result["second_report_hash"])
        for key in (
            "adapter_target_hashes_equal",
            "candidate_transport_hash_equal",
            "verification_subject_hash_equal",
            "accepted_rule_hash_equal",
            "verifier_result_binding_equal",
            "authorization_binding_equal",
            "scenario_bindings_equal",
        ):
            self.assertTrue(result[key])


if __name__ == "__main__":
    unittest.main()
