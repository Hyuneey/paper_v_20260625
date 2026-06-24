from __future__ import annotations

import csv
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from paperworks.data import (
    DataViewName,
    DatasetFile,
    DatasetManifest,
    SplitRole,
    assert_no_overlapping_ranges,
    assert_split_permitted,
    build_data_view_manifest,
    build_sequential_split_manifests,
    generate_split_windows,
    inspect_csv_metadata,
    required_purge_gap,
    resolve_data_root,
    sha256_file,
    validate_local_files,
)
from paperworks.data.files import DataFileError, IrregularSamplingError
from paperworks.data.splits import SplitPermissionError, SplitRangeError


def write_synthetic_csv(path: Path, *, rows: int = 8, irregular: bool = False) -> None:
    start = datetime(2026, 1, 1, 0, 0, 0)
    timestamps = [start + timedelta(seconds=index) for index in range(rows)]
    if irregular:
        timestamps[3] = timestamps[3] + timedelta(seconds=2)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Timestamp", "S1", "A1", "Normal/Attack"])
        for index, timestamp in enumerate(timestamps):
            writer.writerow(
                [
                    timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    index,
                    index % 2,
                    "Normal",
                ]
            )


class DataContractTests(unittest.TestCase):
    def make_manifest(self, root: Path, relative_path: str = "synthetic.csv") -> DatasetManifest:
        path = root / relative_path
        digest = sha256_file(path)
        return DatasetManifest(
            dataset_name="SWaT",
            source_kind="unknown",
            source_reference="synthetic",
            dataset_edition="unverified",
            normal_data_version="unverified",
            file_fingerprints={relative_path: digest},
            feature_count=2,
            feature_names_hash="0" * 64,
            timestamp_column="Timestamp",
            sampling_period_seconds=1.0,
            label_column="Normal/Attack",
            label_encoding={"normal": "Normal", "attack": "Attack"},
            files=(
                DatasetFile(
                    logical_role="synthetic_fixture",
                    relative_path=relative_path,
                    sha256=digest,
                ),
            ),
        )

    def test_manifest_round_trip_and_unknown_edition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_synthetic_csv(root / "synthetic.csv")
            manifest = self.make_manifest(root)
            restored = DatasetManifest.from_json(manifest.to_json())
            self.assertEqual(restored.to_dict(), manifest.to_dict())
            self.assertEqual(restored.dataset_edition, "unverified")
            self.assertEqual(len(restored.manifest_id), 64)

    def test_validate_local_files_detects_hash_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "synthetic.csv"
            write_synthetic_csv(path)
            manifest = self.make_manifest(root)
            validate_local_files(manifest, root)
            with path.open("a", encoding="utf-8") as handle:
                handle.write("\n")
            with self.assertRaises(DataFileError):
                validate_local_files(manifest, root)

    def test_resolve_data_root_uses_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("SWAT_DATA_ROOT")
            os.environ["SWAT_DATA_ROOT"] = tmp
            try:
                self.assertEqual(resolve_data_root(), Path(tmp))
            finally:
                if old is None:
                    os.environ.pop("SWAT_DATA_ROOT", None)
                else:
                    os.environ["SWAT_DATA_ROOT"] = old

    def test_irregular_timestamp_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic.csv"
            write_synthetic_csv(path, irregular=True)
            with self.assertRaises(IrregularSamplingError):
                inspect_csv_metadata(
                    path,
                    relative_path="synthetic.csv",
                    timestamp_column="Timestamp",
                    label_column="Normal/Attack",
                    timestamp_formats=("%Y-%m-%d %H:%M:%S",),
                )

    def test_view_sampling_and_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_synthetic_csv(root / "synthetic.csv")
            manifest = self.make_manifest(root)
            view = build_data_view_manifest(manifest, name=DataViewName.CANONICAL_RULE)
            self.assertEqual(view.sampling_period_seconds, 1.0)
            self.assertEqual(view.upstream_dataset_manifest_id, manifest.manifest_id)
            self.assertEqual(view.source_view, "canonical_rule_view")

    def test_split_role_negative_cases(self) -> None:
        with self.assertRaises(SplitPermissionError):
            assert_split_permitted(SplitRole.TEST, "train_candidate_learner")
        with self.assertRaises(SplitPermissionError):
            assert_split_permitted(SplitRole.TEST, "profile_relation")
        with self.assertRaises(SplitPermissionError):
            assert_split_permitted(SplitRole.TEST, "calibrate_rule_parameters")
        with self.assertRaises(SplitPermissionError):
            assert_split_permitted(SplitRole.TEST, "refine_rule")
        assert_split_permitted(SplitRole.TEST, "final_evaluate")

    def test_raw_range_overlap_rejection(self) -> None:
        with self.assertRaises(SplitRangeError):
            assert_no_overlapping_ranges(((0, 10), (9, 20)))

    def test_split_before_window_and_purge_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_synthetic_csv(root / "synthetic.csv", rows=30)
            manifest = self.make_manifest(root)
            view = build_data_view_manifest(manifest)
            purge = required_purge_gap(window_size=4, max_lag_samples=2)
            splits = build_sequential_split_manifests(
                total_length=30,
                role_lengths=((SplitRole.TRAIN_NORMAL, 10), (SplitRole.CALIBRATION_NORMAL, 10)),
                dataset_manifest_id=manifest.manifest_id,
                data_view_id=view.view_id,
                purge_gap_samples=purge,
                seed=123,
            )
            self.assertEqual(purge, 5)
            self.assertEqual(splits[0].raw_index_ranges, ((0, 10),))
            self.assertEqual(splits[1].raw_index_ranges, ((15, 25),))
            windows = generate_split_windows(splits[0], window_size=4)
            self.assertTrue(windows)
            for window in windows:
                self.assertGreaterEqual(window.input_start, 0)
                self.assertLess(window.target_index, 10)

    def test_synthetic_fixture_does_not_reference_swat_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic.csv"
            write_synthetic_csv(path)
            header = path.read_text(encoding="utf-8").splitlines()[0]
            forbidden_sensor = "FIT" + "101"
            forbidden_actuator = "MV" + "101"
            self.assertNotIn(forbidden_sensor, header)
            self.assertNotIn(forbidden_actuator, header)


if __name__ == "__main__":
    unittest.main()
