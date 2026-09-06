from __future__ import annotations

import unittest

from paperworks.validation_v2.dg05_hai_official_scenario_v1 import _unique_join


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
