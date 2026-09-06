from __future__ import annotations

import unittest
import json
from pathlib import Path

from paperworks.validation_v2.dg05_dec031_v1 import (
    DG05Dec031Error,
    build_physical_timeline_authority_v1,
    build_timeline_failure_receipts_v1,
    derive_four_way_runtime_census_v1,
    interval_local_detection_v1,
    require_valid_physical_timeline_v1,
)
from paperworks.validation_v2.dg05_production_chain_v1 import digest_v1


H = "a" * 64
G = "b" * 40
ROOT = Path(__file__).resolve().parents[1]


def _times(count: int = 6) -> list[str]:
    return [f"2026-09-05T00:00:0{index}" for index in range(count)]


class Dec031TimelineTests(unittest.TestCase):
    def test_binding_authority_replays_and_withholds_real_access(self) -> None:
        path = ROOT / "research_control_center/validation_v2/dg05_dec031_binding/DEC031_BINDING_AUTHORITY_V1.json"
        value = json.loads(path.read_text(encoding="ascii"))
        self.assertEqual(value["self_hash"], digest_v1({k: v for k, v in value.items() if k != "self_hash"}))
        self.assertFalse(value["dg05_real_access_authorized"])
        self.assertEqual(value["attack_test_accesses"], 0)
        self.assertEqual(value["label_scenario_accesses"], 0)

    def _authority(self, timestamps: list[str]) -> dict:
        return build_physical_timeline_authority_v1(
            panel_id="PANEL",
            file_id="FILE",
            timestamps=timestamps,
            physical_file_authority_hash=H,
            projection_authority_hash=H,
            source_commit=G,
        )

    def test_valid_physical_time_authority(self) -> None:
        authority = self._authority(_times())
        self.assertEqual(authority["status"], "VALID_PHYSICAL_ONE_SECOND_TIMESTAMP_AUTHORITY")
        require_valid_physical_timeline_v1(authority)

    def test_duplicate_fails_closed_without_repair(self) -> None:
        authority = self._authority([_times()[0], "2026-09-05T00:00:00.000000"])
        self.assertEqual(authority["status"], "INVALID_TIMESTAMP_AUTHORITY_DUPLICATE")
        with self.assertRaisesRegex(DG05Dec031Error, "DUPLICATE"):
            require_valid_physical_timeline_v1(authority)
        self.assertEqual(authority["duplicate_repair"], "PROHIBITED")

    def test_gap_and_backward_time_fail_closed(self) -> None:
        for timestamps in (
            ["2026-09-05T00:00:00", "2026-09-05T00:00:02"],
            ["2026-09-05T00:00:01", "2026-09-05T00:00:00"],
        ):
            authority = self._authority(timestamps)
            self.assertEqual(authority["status"], "INVALID_TIMESTAMP_AUTHORITY_NON_UNIT_GAP")
            with self.assertRaisesRegex(DG05Dec031Error, "NON_UNIT_GAP"):
                require_valid_physical_timeline_v1(authority)

    def test_invalid_timeline_emits_complete_failure_cells(self) -> None:
        authority = self._authority(["2026-09-05T00:00:00", "2026-09-05T00:00:02"])
        receipts = build_timeline_failure_receipts_v1(
            panel_id="PANEL",
            file_id="FILE",
            method_authority_hashes={"M0": H, "M3": "c" * 64},
            timeline_authority=authority,
            release_manifest_hash="d" * 64,
        )
        self.assertEqual([row["method_id"] for row in receipts], ["M0", "M3"])
        self.assertTrue(all(row["status"] == "METHOD_FAILURE" for row in receipts))
        self.assertTrue(all(not row["scientific_prediction_invoked"] for row in receipts))


class Dec031IntervalDelayTests(unittest.TestCase):
    def test_hit_in_second_disjoint_interval_is_interval_local(self) -> None:
        result = interval_local_detection_v1(
            alarm_timestamps=["2026-09-05T00:00:21"],
            closed_intervals=[
                ["2026-09-05T00:00:00.5", "2026-09-05T00:00:05.5"],
                ["2026-09-05T00:00:20.25", "2026-09-05T00:00:22.25"],
            ],
        )
        self.assertEqual(result["scenario_outcome"], "HIT")
        self.assertEqual(result["containing_interval_index"], 1)
        self.assertEqual(result["interval_local_delay_seconds"], "0.750000")

    def test_inactive_gap_and_outside_alarms_are_miss(self) -> None:
        result = interval_local_detection_v1(
            alarm_timestamps=[
                "2026-09-04T23:59:59",
                "2026-09-05T00:00:10",
                "2026-09-05T00:00:30",
            ],
            closed_intervals=[
                ["2026-09-05T00:00:00", "2026-09-05T00:00:05"],
                ["2026-09-05T00:00:20", "2026-09-05T00:00:25"],
            ],
        )
        self.assertEqual(result["scenario_outcome"], "MISS")
        self.assertEqual(result["detection_delay_status"], "NOT_DETECTED")

    def test_earliest_alarm_and_overlap_tie_policy(self) -> None:
        result = interval_local_detection_v1(
            alarm_timestamps=["2026-09-05T00:00:07", "2026-09-05T00:00:06"],
            closed_intervals=[
                ["2026-09-05T00:00:05", "2026-09-05T00:00:08"],
                ["2026-09-05T00:00:04", "2026-09-05T00:00:08"],
                ["2026-09-05T00:00:04", "2026-09-05T00:00:09"],
            ],
        )
        self.assertEqual(result["earliest_hit_timestamp"], "2026-09-05T00:00:06")
        self.assertEqual(result["containing_interval_index"], 1)
        self.assertEqual(result["interval_local_delay_seconds"], "2.000000")

    def test_closed_boundary_and_unsampled_endpoint(self) -> None:
        result = interval_local_detection_v1(
            alarm_timestamps=["2026-09-05T00:00:03"],
            closed_intervals=[["2026-09-05T00:00:00.25", "2026-09-05T00:00:03"]],
        )
        self.assertEqual(result["scenario_outcome"], "HIT")
        self.assertEqual(result["interval_local_delay_seconds"], "2.750000")


class Dec031RuntimeTests(unittest.TestCase):
    def _trace(self) -> dict:
        return {
            "file_id": "F",
            "opportunities": 5,
            "pass": 1,
            "fail": 2,
            "abstain": 1,
            "system_errors": 1,
            "evaluation_invocations": 5,
            "evaluated_system_errors": 1,
            "rule_alarm_rows": [1, 2],
            "per_rule_runtime": [
                {
                    "rule_id": "R0", "source_id": "S0", "opportunities": 0,
                    "pass": 0, "fail": 0, "abstain": 0, "system_errors": 0,
                    "evaluation_invocations": 0, "evaluated_system_errors": 0,
                    "fail_rows": [],
                },
                {
                    "rule_id": "R1", "source_id": "S1", "opportunities": 3,
                    "pass": 1, "fail": 1, "abstain": 1, "system_errors": 0,
                    "evaluation_invocations": 3, "evaluated_system_errors": 0,
                    "fail_rows": [1],
                },
                {
                    "rule_id": "R2", "source_id": "S2", "opportunities": 2,
                    "pass": 0, "fail": 1, "abstain": 0, "system_errors": 1,
                    "evaluation_invocations": 2, "evaluated_system_errors": 1,
                    "fail_rows": [2],
                },
            ],
        }

    def test_four_way_identities_and_union_episodes(self) -> None:
        result = derive_four_way_runtime_census_v1(
            configured_rule_sources={"R0": "S0", "R1": "S1", "R2": "S2"},
            file_timestamps={"F": _times()},
            traces=[self._trace()],
        )
        self.assertEqual(result["configured_rule_ids"], ["R0", "R1", "R2"])
        self.assertEqual(result["formed_rule_ids"], ["R1", "R2"])
        self.assertEqual(result["evaluated_rule_ids"], ["R1", "R2"])
        self.assertEqual(result["alarming_rule_ids"], ["R1", "R2"])
        self.assertEqual(result["system_error_rule_ids"], ["R2"])
        self.assertEqual(result["physical_union_alarm_seconds"], 2)
        self.assertEqual(result["physical_union_alarm_episodes"], 1)

    def test_pre_evaluation_error_is_not_evaluated(self) -> None:
        trace = self._trace()
        row = trace["per_rule_runtime"][2]
        row.update(fail=0, system_errors=2, evaluation_invocations=0, evaluated_system_errors=0, fail_rows=[])
        trace.update(fail=1, system_errors=2, evaluation_invocations=3, evaluated_system_errors=0, rule_alarm_rows=[1])
        result = derive_four_way_runtime_census_v1(
            configured_rule_sources={"R0": "S0", "R1": "S1", "R2": "S2"},
            file_timestamps={"F": _times()},
            traces=[trace],
        )
        self.assertNotIn("R2", result["evaluated_rule_ids"])
        self.assertIn("R2", result["system_error_rule_ids"])

    def test_missing_rule_and_missing_alarm_evidence_rejected(self) -> None:
        for mutation in ("missing_rule", "missing_alarm"):
            trace = self._trace()
            if mutation == "missing_rule":
                trace["per_rule_runtime"].pop()
            else:
                trace.pop("rule_alarm_rows")
            with self.assertRaises(DG05Dec031Error):
                derive_four_way_runtime_census_v1(
                    configured_rule_sources={"R0": "S0", "R1": "S1", "R2": "S2"},
                    file_timestamps={"F": _times()},
                    traces=[trace],
                )

    def test_out_of_bounds_and_authority_swap_rejected(self) -> None:
        trace = self._trace()
        trace["per_rule_runtime"][2]["fail_rows"] = [99]
        trace["rule_alarm_rows"] = [1, 99]
        with self.assertRaisesRegex(DG05Dec031Error, "PROVENANCE"):
            derive_four_way_runtime_census_v1(
                configured_rule_sources={"R0": "S0", "R1": "S1", "R2": "S2"},
                file_timestamps={"F": _times()},
                traces=[trace],
            )
        trace = self._trace()
        trace["per_rule_runtime"][1]["source_id"] = "SWAPPED"
        with self.assertRaisesRegex(DG05Dec031Error, "AUTHORITY_MISMATCH"):
            derive_four_way_runtime_census_v1(
                configured_rule_sources={"R0": "S0", "R1": "S1", "R2": "S2"},
                file_timestamps={"F": _times()},
                traces=[trace],
            )


if __name__ == "__main__":
    unittest.main()
