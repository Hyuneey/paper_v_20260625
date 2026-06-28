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
    SupportSliceSelectionPolicy,
    render_task020_report_markdown,
    run_task018_support_aware_staging,
    run_task019_rule_evidence_audit,
    run_task020_rule_robustness,
)
from paperworks.metadata import MetadataRegistry, suggest_metadata_from_name
from paperworks.profiling import RelationProfilingConfig
from paperworks.verification import VerificationConfig


FEATURES = ("FIT101", "LIT101", "MV101", "P101")
CREATED_AT = "2026-06-29T00:00:00+09:00"


def write_support_fixture(path: Path, *, rows: int = 80) -> None:
    start = datetime(2026, 1, 1, 0, 0, 0)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Timestamp", *FEATURES, "Normal/Attack"])
        for index in range(rows):
            mv_state = 1
            if 20 <= index <= 23 or 40 <= index <= 43:
                mv_state = 2
            fit = 10.0
            if index >= 20:
                fit = 11.0
            if index >= 40:
                fit = 12.0
            writer.writerow(
                [
                    (start + timedelta(seconds=index)).strftime("%Y-%m-%d %H:%M:%S"),
                    fit,
                    20.0 + (index % 3),
                    mv_state,
                    1,
                    "Attack" if index % 11 == 0 else "Normal",
                ]
            )


def metadata() -> MetadataRegistry:
    return MetadataRegistry(suggest_metadata_from_name(name) for name in FEATURES)


def task018_config() -> SupportAwareStagingConfig:
    dry_run = StagingPipelineConfig(
        pipeline_feature_subset=FEATURES,
        split_lengths={
            SplitRole.TRAIN_NORMAL: 8,
            SplitRole.CALIBRATION_NORMAL: 8,
            SplitRole.VALIDATION: 8,
        },
        purge_gap_samples=1,
        seed=20,
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
    return SupportAwareStagingConfig(
        dry_run_config=dry_run,
        selection_policy=SupportSliceSelectionPolicy(
            minimum_trigger_count=1,
            minimum_matched_response_count=1,
            maximum_right_censored_ratio=0.5,
            allowed_source_variables=("MV101",),
            allowed_target_variables=("FIT101",),
            maximum_slice_length=dry_run.required_loaded_rows,
            search_step=10,
        ),
    )


def task018_and_019_payloads(root: Path, config: SupportAwareStagingConfig):
    scan_report, dry_report, split_manifest = run_task018_support_aware_staging(
        root=root,
        config=config,
        metadata=metadata(),
        created_at=CREATED_AT,
    )
    support_payload = {"report_id": scan_report.report_id, "report": scan_report.to_dict()}
    dry_payload = {
        "report_id": dry_report.report_id,
        "report": dry_report.to_dict(),
        "split_manifest": split_manifest,
    }
    audit = run_task019_rule_evidence_audit(
        root=root,
        config=config,
        metadata=metadata(),
        support_scan_report=support_payload,
        dry_run_report=dry_payload,
        reconstructed_task018_created_at=CREATED_AT,
        created_at=CREATED_AT,
    )
    audit_payload = {"report_id": audit.report_id, "report": audit.to_dict()}
    return support_payload, dry_payload, audit_payload


class Task020RuleRobustnessTests(unittest.TestCase):
    def test_robustness_scan_and_synthetic_replay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_support_fixture(root / "merged.csv")
            config = task018_config()
            support_payload, dry_payload, audit_payload = task018_and_019_payloads(root, config)

            robustness, replay = run_task020_rule_robustness(
                root=root,
                config=config,
                metadata=metadata(),
                support_scan_report=support_payload,
                dry_run_report=dry_payload,
                rule_evidence_audit=audit_payload,
                reconstructed_task018_created_at=CREATED_AT,
                created_at="2026-06-29T02:00:00+09:00",
                max_scan_slices=5,
                max_stability_rebuild_slices=2,
            )

            self.assertEqual(robustness.used_source_files, ("merged.csv",))
            self.assertFalse(robustness.labels_used_for_selection)
            self.assertGreaterEqual(robustness.passing_slice_count, 1)
            self.assertGreaterEqual(robustness.pair_summaries[0].supported_slice_count, 1)
            self.assertTrue(robustness.checks["no_anomaly_performance_slice_selection"])
            self.assertGreaterEqual(len(robustness.stability_observations), 1)
            self.assertEqual(replay.used_source_files, ())
            self.assertTrue(replay.checks["missing_response_cases_fire"])
            self.assertTrue(replay.checks["expected_response_cases_do_not_fire"])
            self.assertIn("not an official SWaT benchmark", robustness.report_statement)

    def test_reports_are_aggregate_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_support_fixture(root / "merged.csv")
            config = task018_config()
            support_payload, dry_payload, audit_payload = task018_and_019_payloads(root, config)

            robustness, replay = run_task020_rule_robustness(
                root=root,
                config=config,
                metadata=metadata(),
                support_scan_report=support_payload,
                dry_run_report=dry_payload,
                rule_evidence_audit=audit_payload,
                reconstructed_task018_created_at=CREATED_AT,
                created_at="2026-06-29T02:00:00+09:00",
                max_scan_slices=5,
                max_stability_rebuild_slices=2,
            )
            rendered = (
                json.dumps(robustness.to_dict(), sort_keys=True)
                + json.dumps(replay.to_dict(), sort_keys=True)
                + render_task020_report_markdown(robustness, replay)
            )

            self.assertNotIn("OfficialSwatProvenanceManifest", rendered)
            self.assertNotIn("normal.csv", rendered)
            self.assertNotIn("attack.csv", rendered)
            self.assertNotIn("firing_records", rendered)
            self.assertNotIn("timestamps_seconds", rendered)
            self.assertNotIn("[10.0, 10.0, 10.0", rendered)


if __name__ == "__main__":
    unittest.main()
