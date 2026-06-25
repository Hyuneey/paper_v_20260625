from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from paperworks.data import (
    OfficialSwatFileRecord,
    OfficialSwatManifestError,
    OfficialSwatProvenanceManifest,
    build_official_swat_file_record,
    hash_approved_swat_file,
)


def write_fixture(path: Path) -> None:
    path.write_text("header\nrow1\n", encoding="utf-8")


class OfficialSwatManifestTests(unittest.TestCase):
    def test_pending_manifest_records_blockers(self) -> None:
        manifest = OfficialSwatProvenanceManifest()

        self.assertFalse(manifest.dec007_resolution_ready)
        self.assertIn("request_record_missing", manifest.resolution_blockers())
        self.assertIn("terms_not_acknowledged", manifest.resolution_blockers())
        self.assertIn("terms_source_url_missing", manifest.resolution_blockers())
        self.assertIn("required_credit_statement_missing", manifest.resolution_blockers())
        self.assertIn("no_sharing_not_acknowledged", manifest.resolution_blockers())
        self.assertIn("publication_notification_not_acknowledged", manifest.resolution_blockers())
        self.assertEqual(len(manifest.manifest_id), 64)

    def test_resolution_ready_manifest(self) -> None:
        file_record = OfficialSwatFileRecord(
            logical_role="official_train_normal",
            relative_path="official/train.csv",
            sha256="a" * 64,
            bytes=10,
            rows_excluding_header=1,
            file_version_note="SWaT A1 and A2 Dec 2015",
        )
        manifest = OfficialSwatProvenanceManifest(
            request_record_reference="local_private_record:itrust_request_2026-06-25",
            approval_record_reference="local_private_record:itrust_approval_2026-06-25",
            terms_acknowledged=True,
            terms_acknowledged_by="researcher",
            terms_acknowledged_date="2026-06-25",
            terms_source_url="https://www.sutd.edu.sg/itrust/itrust-labs/datasets/terms-of-usage/",
            required_credit_statement="Credit iTrust/SUTD when publishing work using the dataset.",
            no_sharing_acknowledged=True,
            publication_notification_acknowledged=True,
            dataset_edition="SWaT A1 and A2 Dec 2015",
            dataset_version="official_iTrust_download",
            files=(file_record,),
            split_protocol_frozen=True,
            metric_protocol_frozen=True,
            sealed_test_access_policy_approved=True,
            git_artifact_policy_approved=True,
        )

        self.assertTrue(manifest.dec007_resolution_ready)
        self.assertEqual(manifest.resolution_blockers(), ())
        self.assertEqual(OfficialSwatProvenanceManifest.from_json(manifest.to_json()).to_dict(), manifest.to_dict())

    def test_rejects_non_official_source_route_for_primary_resolution(self) -> None:
        with self.assertRaisesRegex(OfficialSwatManifestError, "official_iTrust_request"):
            OfficialSwatProvenanceManifest(source_route="explicitly_approved_alternative")

    def test_final_test_opened_is_not_allowed_in_task015_manifest(self) -> None:
        with self.assertRaisesRegex(OfficialSwatManifestError, "final test"):
            OfficialSwatProvenanceManifest(final_test_opened=True)

    def test_safe_hash_record_for_local_approved_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "official_train.csv"
            write_fixture(path)

            record = build_official_swat_file_record(
                root=root,
                relative_path="official_train.csv",
                logical_role="official_train_normal",
                rows_excluding_header=1,
                file_version_note="synthetic unit-test fixture",
            )

            self.assertEqual(record.sha256, hash_approved_swat_file(path))
            self.assertEqual(record.bytes, path.stat().st_size)
            self.assertEqual(record.relative_path, "official_train.csv")

    def test_rejects_unsafe_paths(self) -> None:
        with self.assertRaises(OfficialSwatManifestError):
            OfficialSwatFileRecord(
                logical_role="bad",
                relative_path="../outside.csv",
                sha256="a" * 64,
                bytes=1,
            )

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(OfficialSwatManifestError):
                build_official_swat_file_record(
                    root=Path(tmp),
                    relative_path="../outside.csv",
                    logical_role="bad",
                )


if __name__ == "__main__":
    unittest.main()
