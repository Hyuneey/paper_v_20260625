from __future__ import annotations

import csv
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from paperworks.e2e import (
    StagingPipelineConfig,
    StagingPipelineDryRunError,
    load_staging_pipeline_config,
    run_task017_staging_pipeline_dry_run,
)
from paperworks.data import SplitRole
from paperworks.metadata import MetadataRegistry, suggest_metadata_from_name
from paperworks.profiling import RelationProfilingConfig


FEATURES = ("FIT101", "LIT101", "MV101", "P101")


def write_merged_csv(path: Path, *, rows: int = 40, header_spaces: bool = False) -> None:
    start = datetime(2026, 1, 1, 0, 0, 0)
    header = ["Timestamp", *FEATURES, "Normal/Attack"]
    if header_spaces:
        header = [f" {name} " for name in header]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for index in range(rows):
            phase = index % 4
            actuator_state = 2 if phase in {1, 2} else 1
            pump_state = 2 if phase in {1, 2, 3} else 1
            fit = 10.0 + index
            lit = 20.0 + (index // 2)
            writer.writerow(
                [
                    (start + timedelta(seconds=index)).strftime("%Y-%m-%d %H:%M:%S"),
                    fit,
                    lit,
                    actuator_state,
                    pump_state,
                    "Normal",
                ]
            )


def metadata() -> MetadataRegistry:
    return MetadataRegistry(suggest_metadata_from_name(name) for name in FEATURES)


def config() -> StagingPipelineConfig:
    return StagingPipelineConfig(
        pipeline_feature_subset=FEATURES,
        split_lengths={
            SplitRole.TRAIN_NORMAL: 10,
            SplitRole.CALIBRATION_NORMAL: 10,
            SplitRole.VALIDATION: 10,
        },
        purge_gap_samples=1,
        profile_pairs=(("MV101", "FIT101"), ("P101", "LIT101")),
        profiling_config=RelationProfilingConfig(
            max_response_delay_samples=4,
            min_matched_response_count=1,
        ),
    )


class Task017StagingDryRunTests(unittest.TestCase):
    def test_dry_run_uses_only_merged_csv_and_builds_split_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_merged_csv(root / "merged.csv", header_spaces=True)

            report, split_manifest = run_task017_staging_pipeline_dry_run(
                root=root,
                config=config(),
                metadata=metadata(),
                created_at="2026-06-28T00:00:00Z",
            )

            self.assertEqual(report.used_source_files, ("merged.csv",))
            self.assertTrue(report.only_one_pipeline_timeline_source_used)
            self.assertEqual(report.pipeline_timeline_source, "merged.csv")
            self.assertFalse(split_manifest["final_test_accessed"])
            self.assertEqual(set(split_manifest["splits"]), {"train_normal", "calibration_normal", "validation"})
            self.assertTrue(report.checks["normal_attack_merged_not_combined"])
            self.assertTrue(report.checks["no_raw_rows_windows_or_plots_tracked"])
            self.assertEqual(report.metadata_summary["missing_feature_count"], 0)
            self.assertGreater(report.candidate_summary["candidate_pair_count"], 0)
            self.assertGreaterEqual(report.profiling_summary["attempt_count"], 1)
            self.assertFalse(report.raw_data_audit["raw_rows_tracked"])
            self.assertIn("not an official SWaT benchmark", report.report_statement)

    def test_rejects_multiple_timeline_sources(self) -> None:
        with self.assertRaises(StagingPipelineDryRunError):
            StagingPipelineConfig(timeline_sources=("normal.csv", "merged.csv"))

    def test_rejects_non_default_timeline_source(self) -> None:
        with self.assertRaises(StagingPipelineDryRunError):
            StagingPipelineConfig(timeline_sources=("normal.csv",))

    def test_config_loader_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps(config().to_dict()), encoding="utf-8")

            loaded = load_staging_pipeline_config(path)

            self.assertEqual(loaded.timeline_sources, ("merged.csv",))
            self.assertEqual(loaded.pipeline_feature_subset, FEATURES)
            self.assertEqual(loaded.config_hash, config().config_hash)

    def test_report_is_aggregate_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_merged_csv(root / "merged.csv")
            report, split_manifest = run_task017_staging_pipeline_dry_run(
                root=root,
                config=config(),
                metadata=metadata(),
            )

            rendered = json.dumps({"report": report.to_dict(), "split": split_manifest}, sort_keys=True)

            self.assertNotIn("OfficialSwatProvenanceManifest", rendered)
            self.assertNotIn("normal.csv", rendered)
            self.assertNotIn("attack.csv", rendered)
            self.assertNotIn("firing_records", rendered)
            self.assertNotIn("timestamps_seconds", rendered)
            self.assertNotIn("[10.0, 11.0, 12.0", rendered)


if __name__ == "__main__":
    unittest.main()
