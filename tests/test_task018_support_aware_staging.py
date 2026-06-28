from __future__ import annotations

import csv
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from paperworks.data import SplitRole
from paperworks.e2e import (
    StagingPipelineConfig,
    SupportAwareStagingConfig,
    SupportAwareStagingError,
    SupportSliceSelectionPolicy,
    load_support_aware_staging_config,
    run_task018_support_aware_staging,
    scan_support_aware_slice,
)
from paperworks.metadata import MetadataRegistry, suggest_metadata_from_name
from paperworks.profiling import RelationProfilingConfig
from paperworks.verification import VerificationConfig


FEATURES = ("FIT101", "LIT101", "MV101", "P101")


def write_support_fixture(path: Path, *, rows: int = 60) -> None:
    start = datetime(2026, 1, 1, 0, 0, 0)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Timestamp", *FEATURES, "Normal/Attack"])
        for index in range(rows):
            mv_state = 1
            if 20 <= index <= 23:
                mv_state = 2
            p_state = 1
            fit = 10.0
            if index >= 20:
                fit = 11.0
            lit = 20.0 + (index % 3)
            writer.writerow(
                [
                    (start + timedelta(seconds=index)).strftime("%Y-%m-%d %H:%M:%S"),
                    fit,
                    lit,
                    mv_state,
                    p_state,
                    "Attack" if index % 7 == 0 else "Normal",
                ]
            )


def metadata() -> MetadataRegistry:
    return MetadataRegistry(suggest_metadata_from_name(name) for name in FEATURES)


def dry_run_config() -> StagingPipelineConfig:
    return StagingPipelineConfig(
        pipeline_feature_subset=FEATURES,
        split_lengths={
            SplitRole.TRAIN_NORMAL: 8,
            SplitRole.CALIBRATION_NORMAL: 8,
            SplitRole.VALIDATION: 8,
        },
        purge_gap_samples=1,
        seed=18,
        profile_pairs=(("MV101", "FIT101"),),
        profiling_config=RelationProfilingConfig(
            max_response_delay_samples=3,
            min_matched_response_count=1,
        ),
        verification_config=VerificationConfig(
            max_normal_false_fire_rate=1.0,
            min_validation_coverage=0.0,
            firing_overlap_jaccard_threshold=1.0,
            min_calibration_support_count=1,
        ),
    )


def task018_config() -> SupportAwareStagingConfig:
    return SupportAwareStagingConfig(
        dry_run_config=dry_run_config(),
        selection_policy=SupportSliceSelectionPolicy(
            minimum_trigger_count=1,
            minimum_matched_response_count=1,
            maximum_right_censored_ratio=0.5,
            allowed_source_variables=("MV101",),
            allowed_target_variables=("FIT101",),
            maximum_slice_length=dry_run_config().required_loaded_rows,
            search_step=10,
        ),
    )


class Task018SupportAwareStagingTests(unittest.TestCase):
    def test_support_scan_selects_first_predeclared_passing_slice_without_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_support_fixture(root / "merged.csv")

            report = scan_support_aware_slice(root=root, config=task018_config())

            self.assertEqual(report.used_source_files, ("merged.csv",))
            self.assertFalse(report.labels_used_for_selection)
            self.assertIsNotNone(report.selected_slice)
            assert report.selected_slice is not None
            self.assertEqual(report.selected_slice.timeline_start_index, 10)
            self.assertEqual(report.selected_slice.supported_pair_count, 1)
            self.assertGreaterEqual(report.selected_slice.total_trigger_count, 1)
            self.assertTrue(report.checks["selected_slice_has_supported_pair"])
            self.assertIn("not an official SWaT benchmark", report.report_statement)

    def test_support_aware_runner_reuses_selected_slice_for_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_support_fixture(root / "merged.csv")

            scan_report, dry_report, split_manifest = run_task018_support_aware_staging(
                root=root,
                config=task018_config(),
                metadata=metadata(),
                created_at="2026-06-28T00:00:00Z",
            )

            self.assertIsNotNone(scan_report.selected_slice)
            assert scan_report.selected_slice is not None
            self.assertEqual(dry_report.split_summary["timeline_start_index"], 10)
            self.assertEqual(split_manifest["timeline_start_index"], 10)
            self.assertGreaterEqual(dry_report.profiling_summary["verified_rule_count"], 1)
            self.assertTrue(dry_report.checks["no_final_test_access"])
            self.assertFalse(dry_report.raw_data_audit["raw_rows_tracked"])

    def test_rejects_label_based_selection_policy(self) -> None:
        with self.assertRaises(SupportAwareStagingError):
            SupportSliceSelectionPolicy(
                minimum_trigger_count=1,
                minimum_matched_response_count=1,
                maximum_right_censored_ratio=0.5,
                allowed_source_variables=("MV101",),
                allowed_target_variables=("FIT101",),
                maximum_slice_length=26,
                search_step=10,
                labels_policy="use_labels_for_selection",
            )

    def test_config_loader_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task018.json"
            path.write_text(json.dumps(task018_config().to_dict()), encoding="utf-8")

            loaded = load_support_aware_staging_config(path)

            self.assertEqual(loaded.timeline_source, "merged.csv")
            self.assertEqual(loaded.config_hash, task018_config().config_hash)
            self.assertEqual(loaded.selection_policy.search_step, 10)

    def test_report_is_aggregate_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_support_fixture(root / "merged.csv")

            report = scan_support_aware_slice(root=root, config=task018_config())
            rendered = json.dumps(report.to_dict(), sort_keys=True)

            self.assertNotIn("OfficialSwatProvenanceManifest", rendered)
            self.assertNotIn("normal.csv", rendered)
            self.assertNotIn("attack.csv", rendered)
            self.assertNotIn("firing_records", rendered)
            self.assertNotIn("timestamps_seconds", rendered)
            self.assertNotIn("[10.0, 10.0, 10.0", rendered)


if __name__ == "__main__":
    unittest.main()
