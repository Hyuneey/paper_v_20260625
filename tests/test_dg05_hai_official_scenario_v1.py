from __future__ import annotations

import unittest

from paperworks.validation_v2.dg05_hai_official_scenario_v1 import _hai21_compatible_pairs, _residual_pair, _unique_join


class OfficialScenarioJoinTests(unittest.TestCase):
    def test_join_accepts_unique_timestamp_duration_pair(self) -> None:
        manual = [{"manual_start_minute": "5:41", "manual_duration_seconds": 190}]
        intervals = [{"start": "2021-07-10 05:41:22", "end": "2021-07-10 05:44:32", "duration_seconds": 190}]
        self.assertEqual(len(_unique_join(manual, intervals, inclusive_duration=False)), 1)

    def test_join_rejects_duration_mismatch(self) -> None:
        manual = [{"manual_start_minute": "5:41", "manual_duration_seconds": 190}]
        intervals = [{"start": "2021-07-10 05:41:22", "end": "2021-07-10 05:44:31", "duration_seconds": 189}]
        with self.assertRaisesRegex(ValueError, "JOIN_NOT_UNIQUE"):
            _unique_join(manual, intervals, inclusive_duration=False)

    def test_join_uses_inclusive_manual_duration_only_when_explicit(self) -> None:
        manual = [{"manual_start_minute": "5:41", "manual_duration_seconds": 190}]
        intervals = [{"start": "2021-07-10 05:41:22", "end": "2021-07-10 05:44:31", "duration_seconds": 189}]
        self.assertEqual(len(_unique_join(manual, intervals, inclusive_duration=True)), 1)

    def test_dec035_residual_pair_requires_a_single_same_file_residual(self) -> None:
        manual = [
            {"official_occurrence_id": "A201", "manual_start_minute": "1:00", "manual_duration_seconds": 2},
            {"official_occurrence_id": "A209", "manual_start_minute": "1:02", "manual_duration_seconds": 2},
        ]
        intervals = [
            {"start": "2021-01-01 01:00:00", "end": "2021-01-01 01:00:01", "duration_seconds": 1},
            {"start": "2021-01-01 01:03:00", "end": "2021-01-01 01:03:09", "duration_seconds": 9},
        ]
        compatible = _hai21_compatible_pairs(manual, intervals)
        index, label, proof = _residual_pair(manual=manual, intervals=intervals, compatible=compatible, expected_id="A209")
        self.assertEqual((index, label), (1, 1))
        self.assertEqual(proof["join_kind"], "UNIQUE_RESIDUAL_OFFICIAL_SOURCE_BIJECTION")
