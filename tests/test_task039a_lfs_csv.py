from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from paperworks.data.hai_provenance_v1 import (
    HAICsvStructureAuditV1,
    HAIProvenanceError,
    audit_csv_structure,
    parse_lfs_pointer_text,
    validate_lfs_materialization,
)


def _pointer(content: bytes) -> str:
    digest = hashlib.sha256(content).hexdigest()
    return (
        "version https://git-lfs.github.com/spec/v1\n"
        f"oid sha256:{digest}\n"
        f"size {len(content)}\n"
    )


class Task039ALfsCsvTests(unittest.TestCase):
    def test_valid_lfs_pointer_and_materialized_file(self) -> None:
        content = b"synthetic-public-fixture\n"
        digest = hashlib.sha256(content).hexdigest()
        oid, size = parse_lfs_pointer_text(_pointer(content))
        self.assertEqual((oid, size), (digest, len(content)))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.csv"
            path.write_bytes(content)
            record = validate_lfs_materialization(
                relative_path="hai-23.05/hai-train1.csv",
                pointer_text=_pointer(content),
                materialized_path=path,
                expected_oid_sha256=digest,
                expected_size_bytes=len(content),
            )
        self.assertTrue(record.pointer_matches_expected)
        self.assertTrue(record.materialized_matches_pointer)
        self.assertTrue(record.materialized)
        self.assertEqual(record, type(record).from_dict(record.to_dict()))

    def test_malformed_pointer_oid_and_size_mismatch_fail_closed(self) -> None:
        with self.assertRaises(HAIProvenanceError):
            parse_lfs_pointer_text("not a pointer")
        content = b"synthetic"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.csv"
            path.write_bytes(content)
            record = validate_lfs_materialization(
                relative_path="hai-23.05/hai-test1.csv",
                pointer_text=_pointer(content),
                materialized_path=path,
                expected_oid_sha256="0" * 64,
                expected_size_bytes=len(content) + 1,
            )
        self.assertFalse(record.pointer_matches_expected)

    def test_unmaterialized_pointer_is_not_dataset_content(self) -> None:
        intended = b"bounded synthetic content"
        pointer = _pointer(intended).encode("ascii")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.csv"
            path.write_bytes(pointer)
            record = validate_lfs_materialization(
                relative_path="hai-23.05/hai-test2.csv",
                pointer_text=pointer.decode("ascii"),
                materialized_path=path,
                expected_oid_sha256=hashlib.sha256(intended).hexdigest(),
                expected_size_bytes=len(intended),
            )
        self.assertFalse(record.materialized)
        self.assertFalse(record.materialized_matches_pointer)

    def test_haiend_path_is_rejected(self) -> None:
        with self.assertRaises(HAIProvenanceError):
            validate_lfs_materialization(
                relative_path="haiend-23.05/haiend-test1.csv",
                pointer_text=_pointer(b"x"),
                materialized_path=Path("missing"),
                expected_oid_sha256=hashlib.sha256(b"x").hexdigest(),
                expected_size_bytes=1,
            )

    def test_streaming_csv_structure_and_round_trip(self) -> None:
        text = (
            "timestamp,P1_SYN_SOURCE,P3_SYN_TARGET\n"
            "2026-01-01 00:00:00,0,1.0\n"
            "2026-01-01 00:00:01,1,1.1\n"
            "2026-01-01 00:00:02,0,1.2\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.csv"
            path.write_text(text, encoding="utf-8")
            record = audit_csv_structure(
                path,
                relative_path="hai-23.05/hai-train1.csv",
                expected_point_count=2,
                canonical_header=("timestamp", "P1_SYN_SOURCE", "P3_SYN_TARGET"),
                official_train_normal_description_verified=True,
            )
        self.assertEqual(record.row_count, 3)
        self.assertTrue(record.timestamps_strictly_increasing)
        self.assertEqual(record.nominal_timestamp_delta_seconds, 1.0)
        self.assertEqual(record.normal_file_status, "normal_only_verified")
        self.assertEqual(record.process_ids_observed, ("P1", "P3"))
        self.assertEqual(record, HAICsvStructureAuditV1.from_dict(record.to_dict()))

    def test_duplicate_nonmonotonic_malformed_and_header_mismatch(self) -> None:
        text = (
            "timestamp,P1_SYN_SOURCE,P3_SYN_TARGET\n"
            "2026-01-01 00:00:01,0,1.0\n"
            "2026-01-01 00:00:01,1,1.1\n"
            "not-a-time,0,1.2\n"
            "2026-01-01 00:00:00,0\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.csv"
            path.write_text(text, encoding="utf-8")
            record = audit_csv_structure(
                path,
                relative_path="hai-23.05/hai-test1.csv",
                expected_point_count=2,
                canonical_header=("timestamp", "OTHER", "HEADER"),
                test_file_structural_only=True,
            )
        self.assertFalse(record.timestamps_strictly_increasing)
        self.assertEqual(record.duplicate_timestamp_count, 1)
        self.assertEqual(record.malformed_row_count, 1)
        self.assertEqual(record.inconsistent_field_count_rows, 1)
        self.assertFalse(record.ordered_header_matches_canonical)
        self.assertTrue(record.test_file_structural_only)
        self.assertIsNone(record.normal_file_status)

    def test_irregular_positive_intervals_remain_visible(self) -> None:
        text = (
            "timestamp,P1_SYN_SOURCE,P3_SYN_TARGET\n"
            "2026-01-01 00:00:00,0,1.0\n"
            "2026-01-01 00:00:01,1,1.1\n"
            "2026-01-01 00:00:03,0,1.2\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.csv"
            path.write_text(text, encoding="utf-8")
            record = audit_csv_structure(
                path,
                relative_path="hai-23.05/hai-test2.csv",
                expected_point_count=2,
                test_file_structural_only=True,
            )
        self.assertTrue(record.timestamps_strictly_increasing)
        self.assertEqual(record.distinct_timestamp_delta_seconds, (1.0, 2.0))

    def test_test_record_exposes_no_feature_statistics(self) -> None:
        prohibited = {
            "feature_minimum",
            "feature_maximum",
            "feature_mean",
            "feature_variance",
            "correlations",
            "constant_features",
        }
        self.assertTrue(prohibited.isdisjoint(HAICsvStructureAuditV1.__dataclass_fields__))


if __name__ == "__main__":
    unittest.main()
