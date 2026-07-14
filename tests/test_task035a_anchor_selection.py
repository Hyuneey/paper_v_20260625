from __future__ import annotations

import unittest
import numpy as np

from experiments.argos_reproduction.anomaly_anchor_selection import select_anchor_chunks


class Task035aAnchorSelectionTests(unittest.TestCase):
    def test_five_distinct_chunks_stay_in_generation(self):
        values = np.arange(6000, dtype=float); labels = np.zeros(6000, dtype=np.int8)
        for start in (500, 1500, 2500, 3500, 4500): labels[start:start+5] = 1
        anchors = select_anchor_chunks(values, labels, 6000, chunk_size=1000, anchor_count=5)
        self.assertEqual(len(anchors), 5)
        self.assertEqual(len({item["chunk_sha256"] for item in anchors}), 5)
        self.assertTrue(all(0 <= item["chunk_start"] < item["chunk_end_exclusive"] <= 6000 for item in anchors))


if __name__ == "__main__": unittest.main()
