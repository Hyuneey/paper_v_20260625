from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from paperworks.data.hai_distribution_v1 import (
    HAIDistributionByteEquivalenceResultV1,
    HAIDistributionError,
    HAIDistributionFileEquivalenceV1,
    HAIOfficialDistributionMetadataV1,
    build_official_distribution_metadata,
    canonical_self_hash,
    require_safe_inventory_name,
)
from scripts.remediate_hai_2305_distribution import (
    SelectiveDownloadUnavailable,
    _committed_json_matches_worktree,
    _extract_exact_member,
)
from paperworks.v6.schema_registry_v1 import load_v6_schema_registry_v1


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = (
    "hai-23.05/hai-test1.csv",
    "hai-23.05/hai-test2.csv",
    "hai-23.05/hai-train1.csv",
    "hai-23.05/hai-train2.csv",
    "hai-23.05/hai-train3.csv",
    "hai-23.05/hai-train4.csv",
    "hai-23.05/label-test1.csv",
    "hai-23.05/label-test2.csv",
    "hai-23.05/summary_label1.txt",
    "hai-23.05/summary_label2.txt",
)


def _expected_files() -> list[dict[str, object]]:
    return [
        {
            "relative_path": name,
            "oid_sha256": hashlib.sha256(name.encode("ascii")).hexdigest(),
            "byte_size": index + 10,
        }
        for index, name in enumerate(EXPECTED)
    ]


def _metadata() -> HAIOfficialDistributionMetadataV1:
    expected = _expected_files()
    view = {
        "ownerRef": "icsdataset",
        "ref": "icsdataset/hai-security-dataset",
        "currentVersionNumber": 10,
        "licenseName": "CC BY-SA 4.0",
        "versions": [
            {"versionNumber": 10, "creationDate": "2023-06-01T01:13:02.73Z"}
        ],
        "url": "https://www.kaggle.com/datasets/icsdataset/hai-security-dataset",
    }
    files = {
        "datasetFiles": [
            {
                "name": item["relative_path"],
                "totalBytes": item["byte_size"],
                "creationDate": "2023-06-01T01:13:15Z",
                "fileType": "csv",
                "url": "https://signed.example.invalid/secret",
                "columns": [{"name": "must-not-be-copied"}],
            }
            for item in expected
        ]
        + [
            {
                "name": "graph/boiler/reference.json",
                "totalBytes": 123,
                "creationDate": "2023-06-01T01:13:15Z",
                "fileType": "json",
            }
        ],
        "nextPageToken": "",
    }
    return build_official_distribution_metadata(
        dataset_view=view,
        file_list=files,
        owner="icsdataset",
        slug="hai-security-dataset",
        dataset_version_identifier=10,
        expected_files=expected,
        official_git_repository="https://github.com/icsdataset/hai",
        official_git_snapshot_commit="2" * 40,
        introduction_commit="e" * 40,
        task039a_expected_config_hash="a" * 64,
        metadata_endpoint=(
            "https://www.kaggle.com/api/v1/datasets/view/"
            "icsdataset/hai-security-dataset"
        ),
        file_inventory_endpoint=(
            "https://www.kaggle.com/api/v1/datasets/list/"
            "icsdataset/hai-security-dataset?datasetVersionNumber=10&pageSize=1000"
        ),
        selective_download_endpoint_template=(
            "https://www.kaggle.com/api/v1/datasets/download/"
            "{owner}/{slug}/{file_name}?datasetVersionNumber={version}"
        ),
        created_at="2026-08-02T00:00:00Z",
        execution_code_commit="1" * 40,
    )


class Task039ARMetadataTests(unittest.TestCase):
    def test_metadata_receipt_is_complete_deterministic_and_redacted(self) -> None:
        metadata = _metadata()
        payload = metadata.to_dict()
        self.assertEqual(payload["complete_file_inventory_count"], 11)
        self.assertEqual(
            HAIOfficialDistributionMetadataV1.from_dict(payload).artifact_hash,
            metadata.artifact_hash,
        )
        serialized = json.dumps(payload, sort_keys=True).lower()
        self.assertNotIn("signed.example", serialized)
        self.assertNotIn("must-not-be-copied", serialized)
        self.assertNotIn("authorization", serialized)
        self.assertFalse(payload["credentials_included"])

    def test_wrong_owner_license_or_advertised_size_fails_closed(self) -> None:
        expected = _expected_files()
        view = {
            "ownerRef": "other",
            "ref": "other/hai-security-dataset",
            "currentVersionNumber": 10,
            "licenseName": "CC BY-SA 4.0",
            "versions": [
                {"versionNumber": 10, "creationDate": "2023-06-01T01:13:02Z"}
            ],
        }
        files = {
            "datasetFiles": [
                {
                    "name": item["relative_path"],
                    "totalBytes": item["byte_size"],
                    "creationDate": "2023-06-01T01:13:15Z",
                    "fileType": "csv",
                }
                for item in expected
            ],
            "nextPageToken": "",
        }
        with self.assertRaises(HAIDistributionError):
            build_official_distribution_metadata(
                dataset_view=view,
                file_list=files,
                owner="icsdataset",
                slug="hai-security-dataset",
                dataset_version_identifier=10,
                expected_files=expected,
                official_git_repository="https://github.com/icsdataset/hai",
                official_git_snapshot_commit="2" * 40,
                introduction_commit="e" * 40,
                task039a_expected_config_hash="a" * 64,
                metadata_endpoint="https://www.kaggle.com/api/v1/a",
                file_inventory_endpoint="https://www.kaggle.com/api/v1/b",
                selective_download_endpoint_template="https://www.kaggle.com/api/v1/c",
                created_at="2026-08-02T00:00:00Z",
                execution_code_commit="1" * 40,
            )

    def test_inventory_path_traversal_fails_closed(self) -> None:
        for invalid in ("../secret", "/absolute", "C:\\secret", "a/../b"):
            with self.subTest(value=invalid), self.assertRaises(HAIDistributionError):
                require_safe_inventory_name(invalid)


class Task039AREquivalenceTests(unittest.TestCase):
    def _record(self, name: str, *, equivalent: bool = True) -> HAIDistributionFileEquivalenceV1:
        digest = hashlib.sha256(name.encode("ascii")).hexdigest()
        extracted = digest if equivalent else "f" * 64
        return HAIDistributionFileEquivalenceV1(
            relative_path=name,
            kaggle_advertised_size_bytes=100,
            official_lfs_oid_sha256=digest,
            official_lfs_pointer_size_bytes=100,
            task039a_expected_sha256=digest,
            task039a_expected_size_bytes=100,
            extracted_sha256=extracted,
            extracted_size_bytes=100,
            byte_equivalent=equivalent,
        )

    def test_passing_result_requires_all_ten_exact_records(self) -> None:
        records = tuple(self._record(name) for name in sorted(EXPECTED))
        result = HAIDistributionByteEquivalenceResultV1(
            task_id="TASK-039AR",
            status="passed_official_distribution_byte_equivalence",
            metadata_receipt_hash="a" * 64,
            execution_code_commit="1" * 40,
            records=records,
            expected_file_count=10,
            selectively_downloaded_file_count=10,
            complete_dataset_download_used=False,
            haiend_or_earlier_payload_downloaded=False,
            credentials_included=False,
            signed_urls_included=False,
            all_files_byte_equivalent=True,
            created_at="2026-08-02T00:00:00Z",
        )
        self.assertEqual(
            HAIDistributionByteEquivalenceResultV1.from_dict(result.to_dict()).artifact_hash,
            result.artifact_hash,
        )

    def test_mismatch_cannot_claim_pass(self) -> None:
        records = [self._record(name) for name in sorted(EXPECTED)]
        records[-1] = self._record(sorted(EXPECTED)[-1], equivalent=False)
        with self.assertRaises(HAIDistributionError):
            HAIDistributionByteEquivalenceResultV1(
                task_id="TASK-039AR",
                status="passed_official_distribution_byte_equivalence",
                metadata_receipt_hash="a" * 64,
                execution_code_commit="1" * 40,
                records=tuple(records),
                expected_file_count=10,
                selectively_downloaded_file_count=10,
                complete_dataset_download_used=False,
                haiend_or_earlier_payload_downloaded=False,
                credentials_included=False,
                signed_urls_included=False,
                all_files_byte_equivalent=False,
                created_at="2026-08-02T00:00:00Z",
            )

    def test_single_member_extraction_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "one.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("hai-23.05/hai-test1.csv", b"synthetic")
            output = _extract_exact_member(
                archive=archive,
                expected_relative_path="hai-23.05/hai-test1.csv",
                destination_root=root / "output",
            )
            self.assertEqual(output.read_bytes(), b"synthetic")

    def test_multi_member_or_wrong_member_archive_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "bad.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("hai-23.05/hai-test1.csv", b"one")
                bundle.writestr("haiend-23.05/unapproved.csv", b"two")
            with self.assertRaises(SelectiveDownloadUnavailable):
                _extract_exact_member(
                    archive=archive,
                    expected_relative_path="hai-23.05/hai-test1.csv",
                    destination_root=root / "output",
                )


class Task039ARConfigTests(unittest.TestCase):
    def test_committed_json_check_is_line_ending_independent(self) -> None:
        self.assertTrue(
            _committed_json_matches_worktree(b'{"a":1}\n', b'{\r\n  "a": 1\r\n}\r\n')
        )

    def test_config_is_self_hashed_and_selective_only(self) -> None:
        path = ROOT / "configs/data/hai_2305_official_distribution_remediation.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(config["config_hash"], canonical_self_hash(config, "config_hash"))
        self.assertTrue(config["selective_file_download_required"])
        self.assertTrue(config["complete_dataset_download_prohibited"])
        self.assertIn("{file_name}", config["selective_download_endpoint_template"])
        self.assertEqual(config["kaggle_owner"], "icsdataset")
        self.assertEqual(config["kaggle_slug"], "hai-security-dataset")

    def test_optional_reports_are_self_hashed_and_redacted(self) -> None:
        for name in (
            "TASK-039AR_KAGGLE_METADATA_FREEZE.json",
            "TASK-039AR_BYTE_EQUIVALENCE_REPORT.json",
        ):
            path = ROOT / "docs/task_reports" / name
            if not path.exists():
                continue
            document = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(
                document["artifact_hash"],
                canonical_self_hash(document, "artifact_hash"),
            )
            serialized = json.dumps(document, sort_keys=True).lower()
            for prohibited in (
                "authorization",
                "cookie",
                "api_token",
                "access_token",
                "signedurl",
                "attack_start",
                "attack_target",
                "c:\\users\\",
            ):
                self.assertNotIn(prohibited, serialized)

    def test_distribution_schemas_are_registered(self) -> None:
        registry = load_v6_schema_registry_v1(repository_root=ROOT)
        self.assertIn("hai_official_distribution_metadata", registry.artifact_types)
        self.assertIn(
            "hai_distribution_byte_equivalence_result", registry.artifact_types
        )


if __name__ == "__main__":
    unittest.main()
