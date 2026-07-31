from __future__ import annotations

import json
import unittest

from tests.test_task039p0_alignment_audit import (
    ROOT,
    read_public_text,
    sha256_json,
)


CONFIG_PATH = "configs/v6/task039p1b_evidence_outcome_freeze.json"
CONTRACT_REPORT_PATH = "docs/task_reports/TASK-039P1B_CONTRACT_REPORT.json"
REQUIRED_DOCS = (
    "TASKS/TASK-039P1B_NORMAL_EVIDENCE_AND_OUTCOMES.md",
    "docs/v6/V6_NORMAL_RELATION_EVIDENCE.md",
    "docs/v6/V6_DETECTOR_ERROR_CONTEXT.md",
    "docs/v6/V6_CONSTRUCTION_OUTCOME_SEMANTICS.md",
    "docs/v6/V6_GOVERNANCE_OUTCOME_SEMANTICS.md",
    "docs/v6/V6_VALIDITY_UTILITY_BOUNDARY.md",
    "docs/v6/V6_LEGACY_EVIDENCE_ADAPTER_POLICY.md",
    "docs/task_reports/TASK-039P1B_REPORT.md",
)


class Task039P1BReportTests(unittest.TestCase):
    def test_config_and_report_self_hashes(self) -> None:
        config = json.loads(read_public_text(ROOT / CONFIG_PATH))
        report = json.loads(read_public_text(ROOT / CONTRACT_REPORT_PATH))
        observed_config_hash = config.pop("config_hash")
        observed_report_hash = report.pop("report_hash")
        self.assertEqual(observed_config_hash, sha256_json(config))
        self.assertEqual(observed_report_hash, sha256_json(report))

    def test_required_documents_and_status(self) -> None:
        for relative in REQUIRED_DOCS:
            with self.subTest(relative=relative):
                self.assertTrue(read_public_text(ROOT / relative).strip())
        report = read_public_text(ROOT / "docs/task_reports/TASK-039P1B_REPORT.md")
        self.assertIn("passed_normal_evidence_and_outcome_foundation", report)

    def test_parent_task_states_are_explicit(self) -> None:
        report = json.loads(read_public_text(ROOT / CONTRACT_REPORT_PATH))
        self.assertEqual(report["parent_task"]["TASK-039P1A"], "completed")
        self.assertEqual(report["parent_task"]["TASK-039P1B"], "completed")
        self.assertEqual(report["parent_task"]["TASK-039P1C"], "pending")
        self.assertEqual(report["parent_task"]["TASK-039P1D"], "pending")
        self.assertEqual(report["parent_task"]["TASK-039P1"], "incomplete")

    def test_no_execution_or_data_scope(self) -> None:
        report = json.loads(read_public_text(ROOT / CONTRACT_REPORT_PATH))
        scope = report["scope"]
        self.assertEqual(scope["provider_calls"], 0)
        self.assertEqual(scope["agent_calls"], 0)
        self.assertFalse(scope["detector_execution"])
        self.assertFalse(scope["rule_execution"])
        self.assertFalse(scope["dataset_access"])
        self.assertFalse(scope["private_artifact_access"])
        self.assertFalse(scope["outer_access"])
        self.assertFalse(scope["sealed_access"])

    def test_final_claim_boundary_is_present(self) -> None:
        report = read_public_text(ROOT / "docs/task_reports/TASK-039P1B_REPORT.md")
        required = (
            "TASK-039P1B defines normal relation evidence, optional detector-error context,\n"
            "and explicit construction/governance/runtime outcome semantics only."
        )
        self.assertIn(required, report)
        self.assertIn("It does not implement a real Agent", report)


if __name__ == "__main__":
    unittest.main()
