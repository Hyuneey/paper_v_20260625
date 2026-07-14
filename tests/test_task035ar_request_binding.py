from __future__ import annotations

from collections import Counter
import unittest

from experiments.argos_reproduction.remediation_slot_manifest import build_remediation_slots, remediation_request_hash


class Task035arRequestBindingTests(unittest.TestCase):
    def test_balanced_replicates_and_request_envelopes(self):
        anchors = [{"anchor_id": f"ANCHOR-{i:03d}", "kpi_id": f"KPI-{(i - 1) // 5:02d}"} for i in range(1, 51)]
        original = []
        for anchor in anchors:
            for replicate in (1, 2):
                original.append({
                    "anchor_id": anchor["anchor_id"], "replicate_id": replicate,
                    "complete_request_hash": "a" * 64, "system_prompt_hash": "b" * 64,
                    "user_prompt_hash": "c" * 64, "chunk_hash": "d" * 64,
                })
        slots = build_remediation_slots(anchors, original)
        self.assertEqual([slot["slot_id"] for slot in slots], [f"SLOT-R{i:03d}" for i in range(1, 101)])
        self.assertEqual({slot["replicate_id"] for slot in slots}, {3, 4})
        self.assertTrue(all(count == 2 for count in Counter(slot["anchor_id"] for slot in slots).values()))
        self.assertTrue(all(slot["new_request_hash"] == remediation_request_hash("a" * 64) for slot in slots))
        self.assertTrue(all(slot["prompt_bytes_unchanged"] for slot in slots))


if __name__ == "__main__": unittest.main()
