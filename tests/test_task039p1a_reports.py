from __future__ import annotations

import json
import subprocess
import unittest

from tests.test_task039p0_alignment_audit import (
    ROOT,
    assert_public_tracked_path,
    read_public_text,
    sha256_json,
)


STARTING_COMMIT = "1c8a7f40b1ee46e0f819afe1b8b43904e3927e53"
REPORT_PATH = ROOT / "docs/task_reports/TASK-039P1A_CONTRACT_REPORT.json"


class Task039P1AReportTests(unittest.TestCase):
    def test_contract_report_is_self_hashed(self) -> None:
        report = json.loads(read_public_text(REPORT_PATH))
        observed = report.pop("report_hash")
        self.assertEqual(observed, sha256_json(report))

    def test_required_documents_are_tracked_and_claim_bounded(self) -> None:
        required = (
            "TASKS/TASK-039P1A_DATASET_NEUTRAL_FOUNDATION.md",
            "docs/v6/V6_DATASET_MANIFEST_V2.md",
            "docs/v6/V6_SPLIT_ROLE_AND_PERMISSION_POLICY.md",
            "docs/v6/V6_LEGACY_DATA_ADAPTER_POLICY.md",
            "docs/task_reports/TASK-039P1A_REPORT.md",
            "docs/task_reports/TASK-039P1A_CONTRACT_REPORT.json",
        )
        for relative in required:
            assert_public_tracked_path(ROOT / relative)
        report = read_public_text(ROOT / "docs/task_reports/TASK-039P1A_REPORT.md")
        self.assertIn("passed_dataset_neutral_data_split_foundation", report)
        self.assertIn("does not establish HAI readiness", report)

    def test_structured_report_freezes_roles_and_boundaries(self) -> None:
        report = json.loads(read_public_text(REPORT_PATH))
        self.assertEqual(len(report["split_roles"]), 7)
        self.assertEqual(report["implementation"]["typed_operation_count"], 11)
        self.assertFalse(report["scope"]["consumer_migration"])
        self.assertFalse(report["scope"]["dataset_access"])
        self.assertFalse(report["scope"]["private_artifact_access"])
        self.assertFalse(report["scope"]["outer_access"])
        self.assertFalse(report["scope"]["sealed_access"])

    def test_source_changes_are_confined_to_data_foundation(self) -> None:
        output = subprocess.check_output(
            ["git", "diff", "--name-only", STARTING_COMMIT, "--", "src"],
            cwd=ROOT,
            text=True,
        )
        changed = [line.strip() for line in output.splitlines() if line.strip()]
        self.assertTrue(changed)
        for relative in changed:
            self.assertTrue(relative.startswith("src/paperworks/data/"), relative)


if __name__ == "__main__":
    unittest.main()
