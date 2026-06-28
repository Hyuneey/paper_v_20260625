from __future__ import annotations

import csv
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from paperworks.data import (
    StagingSwatMirrorError,
    StagingSwatMirrorManifest,
    build_task016_staging_development_report,
    inspect_staging_swat_mirror,
    inspect_staging_swat_mirror_from_env,
)
from paperworks.data.staging_swat import TASK016_REQUIRED_REPORT_STATEMENT
from paperworks.metadata import MetadataRegistry, suggest_metadata_from_name


def write_staging_csv(path: Path, *, rows: int, attack: bool = False, irregular: bool = False) -> None:
    start = datetime(2026, 1, 1, 0, 0, 0)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Timestamp", "FIT101", "LIT101", "MV101", "Normal/Attack"])
        for index in range(rows):
            timestamp = start + timedelta(seconds=index)
            if irregular and index == rows - 1:
                timestamp += timedelta(seconds=3)
            writer.writerow(
                [
                    timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    1.0 + index,
                    2.0 + index,
                    index % 2,
                    "Attack" if attack else "Normal",
                ]
            )


def write_staging_csv_with_header_spaces(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([" Timestamp ", " FIT101 ", " LIT101 ", " MV101 ", " Normal/Attack "])
        writer.writerow(["2026-01-01 00:00:00", 1.0, 2.0, 0, "Normal"])


class StagingSwatTests(unittest.TestCase):
    def test_staging_manifest_records_schema_and_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_staging_csv(root / "normal.csv", rows=3)
            write_staging_csv(root / "attack.csv", rows=2, attack=True)
            write_staging_csv(root / "merged.csv", rows=5)

            manifest = inspect_staging_swat_mirror(root=root)

            self.assertEqual(manifest.staging_source_label, "kaggle_mirror_staging")
            self.assertEqual(manifest.source_kind, "kaggle_mirror")
            self.assertEqual(manifest.dataset_status, "staging_only")
            self.assertFalse(manifest.final_claims_allowed)
            self.assertEqual(manifest.feature_columns, ("FIT101", "LIT101", "MV101"))
            self.assertEqual(manifest.feature_count, 3)
            self.assertTrue(manifest.columns_consistent)
            self.assertEqual(manifest.aggregate_label_counts["Normal"], 8)
            self.assertEqual(manifest.aggregate_label_counts["Attack"], 2)
            self.assertEqual(len(manifest.manifest_id), 64)
            self.assertIn(TASK016_REQUIRED_REPORT_STATEMENT, manifest.to_json())

    def test_manifest_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_staging_csv(root / "normal.csv", rows=1)
            write_staging_csv(root / "attack.csv", rows=1, attack=True)
            write_staging_csv(root / "merged.csv", rows=2)
            manifest = inspect_staging_swat_mirror(root=root)

            restored = StagingSwatMirrorManifest.from_json(manifest.to_json())

            self.assertEqual(restored.to_dict(), manifest.to_dict())

    def test_staging_loader_normalizes_header_whitespace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_staging_csv_with_header_spaces(root / "normal.csv")
            write_staging_csv_with_header_spaces(root / "attack.csv")
            write_staging_csv_with_header_spaces(root / "merged.csv")

            manifest = inspect_staging_swat_mirror(root=root)

            self.assertEqual(manifest.feature_columns, ("FIT101", "LIT101", "MV101"))
            self.assertEqual(manifest.aggregate_label_counts, {"Normal": 3})

    def test_development_report_is_not_final_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_staging_csv(root / "normal.csv", rows=2)
            write_staging_csv(root / "attack.csv", rows=1, attack=True)
            write_staging_csv(root / "merged.csv", rows=3)
            manifest = inspect_staging_swat_mirror(root=root)
            metadata = MetadataRegistry(suggest_metadata_from_name(name) for name in manifest.feature_columns)

            report = build_task016_staging_development_report(manifest=manifest, metadata=metadata)

            self.assertEqual(report.report_statement, TASK016_REQUIRED_REPORT_STATEMENT)
            self.assertEqual(report.staging_source_label, "kaggle_mirror_staging")
            self.assertFalse(report.final_claims_allowed)
            self.assertFalse(report.dec007_resolved)
            self.assertFalse(report.official_manifest_used)
            self.assertEqual(report.metadata_missing_features, ())
            self.assertEqual(report.metadata_extra_features, ())
            self.assertEqual(len(report.report_id), 64)

    def test_env_loader_uses_swat_data_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_staging_csv(root / "normal.csv", rows=1)
            write_staging_csv(root / "attack.csv", rows=1, attack=True)
            write_staging_csv(root / "merged.csv", rows=2)
            old = os.environ.get("SWAT_DATA_ROOT")
            os.environ["SWAT_DATA_ROOT"] = str(root)
            try:
                manifest = inspect_staging_swat_mirror_from_env()
            finally:
                if old is None:
                    os.environ.pop("SWAT_DATA_ROOT", None)
                else:
                    os.environ["SWAT_DATA_ROOT"] = old

            self.assertEqual(manifest.local_root_env, "SWAT_DATA_ROOT")
            self.assertEqual(len(manifest.files), 3)

    def test_irregular_sampling_is_recorded_as_limitation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_staging_csv(root / "normal.csv", rows=3, irregular=True)
            write_staging_csv(root / "attack.csv", rows=1, attack=True)
            write_staging_csv(root / "merged.csv", rows=4)
            manifest = inspect_staging_swat_mirror(root=root)

            self.assertIsNone(manifest.files[0].inferred_sampling_period_seconds)
            self.assertTrue(manifest.files[0].limitations)

    def test_rejects_unsafe_paths_and_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(StagingSwatMirrorError):
                inspect_staging_swat_mirror(root=Path(tmp), relative_paths=("../normal.csv",))
            with self.assertRaises(StagingSwatMirrorError):
                inspect_staging_swat_mirror(root=Path(tmp), relative_paths=("missing.csv",))


if __name__ == "__main__":
    unittest.main()
