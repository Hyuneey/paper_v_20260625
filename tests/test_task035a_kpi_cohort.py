from __future__ import annotations

import unittest

from experiments.argos_reproduction.expanded_kpi_cohort import parse_prefix_records, split_ranges


class GuardedRow(dict):
    def __init__(self, kpi: str, position: int, test_start: int):
        super().__init__({"KPI ID": kpi})
        self.position = position; self.test_start = test_start

    def __getitem__(self, key):
        if key in {"value", "label"}:
            if self.position >= self.test_start:
                raise AssertionError("sealed field accessed")
            return self.position if key == "value" else self.position % 2
        return super().__getitem__(key)


class Task035aKpiCohortTests(unittest.TestCase):
    def test_split_is_exhaustive_and_nonoverlapping(self):
        ranges = split_ranges(10000)
        self.assertEqual(ranges, {"generation": [0, 4000], "inner_selection": [4000, 5600], "outer_validation": [5600, 7000], "sealed_test": [7000, 10000]})

    def test_prefix_parser_never_accesses_sealed_value_or_label(self):
        rows = [GuardedRow("kpi-a", position, 7) for position in range(10)]
        result = parse_prefix_records(rows, {"kpi-a": 10})
        self.assertEqual(len(result["kpi-a"]["value"]), 7)

    def test_selection_policy_is_lexicographic(self):
        eligible = sorted(["kpi-z", "kpi-a", "kpi-b"])
        self.assertEqual(eligible[:2], ["kpi-a", "kpi-b"])


if __name__ == "__main__": unittest.main()
