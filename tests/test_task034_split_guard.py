from __future__ import annotations

import csv
from pathlib import Path
import tempfile
import unittest

import numpy as np

from experiments.argos_reproduction.kpi_split_guard import (
    KpiSplitGuardError,
    assert_sealed_read_range,
    compute_pinned_argos_split,
    read_validation_prefix,
    split_manifest_payload,
)


class Task034SplitGuardTests(unittest.TestCase):
    def test_frozen_row_count_uses_nested_pinned_integer_logic(self) -> None:
        split = compute_pinned_argos_split(146255)
        self.assertEqual(split.train_end_exclusive, 81902)
        self.assertEqual(split.validation_start, 81902)
        self.assertEqual(split.validation_end_exclusive, 102378)
        self.assertEqual(split.test_start, 102378)
        self.assertEqual(split.test_end_exclusive, 146255)
        self.assertEqual(split.train_row_count + split.validation_row_count + split.test_row_count, 146255)

    def test_read_request_at_test_start_is_rejected(self) -> None:
        split = compute_pinned_argos_split(100)
        with self.assertRaisesRegex(KpiSplitGuardError, "TASK034_TEST_RANGE_READ_PROHIBITED"):
            assert_sealed_read_range(start=split.test_start, end_exclusive=split.test_start + 1, boundaries=split)

    def test_prefix_reader_stops_before_test_and_retains_validation_only(self) -> None:
        split = compute_pinned_argos_split(20)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "series.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["value", "label", "index"])
                for index in range(20):
                    writer.writerow([float(index), index % 2, index])
            data = read_validation_prefix(path, split)
        self.assertEqual(data.values.shape, (split.validation_row_count, 1))
        self.assertEqual(data.labels.shape, (split.validation_row_count,))
        self.assertEqual(data.maximum_parsed_row_exclusive, split.test_start)
        self.assertFalse(data.test_rows_parsed)
        np.testing.assert_array_equal(
            data.values[:, 0], np.arange(split.validation_start, split.validation_end_exclusive, dtype=float)
        )

    def test_manifest_is_hash_stable(self) -> None:
        split = compute_pinned_argos_split(100)
        first = split_manifest_payload(split, source_commit="a" * 40, source_blob_hash="b" * 40)
        second = split_manifest_payload(split, source_commit="a" * 40, source_blob_hash="b" * 40)
        self.assertEqual(first, second)
        self.assertEqual(first["test_status"], "sealed_not_accessed")


if __name__ == "__main__":
    unittest.main()
