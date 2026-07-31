from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/v6/task039p1c_canonical_binding_freeze.json"
CONTRACT_REPORT = ROOT / "docs/task_reports/TASK-039P1C_CONTRACT_REPORT.json"
REPORT = ROOT / "docs/task_reports/TASK-039P1C_REPORT.md"
REQUIRED_DOCS = (
    "TASKS/TASK-039P1C_CANONICAL_CONTEXT_BINDING.md",
    "docs/v6/V6_CANONICAL_CONTEXT_COLLECTION.md",
    "docs/v6/V6_NORMAL_EVIDENCE_RULE_BINDING.md",
    "docs/v6/V6_VERIFIER_COLLECTION_PROTOCOL.md",
    "docs/v6/V6_GOVERNANCE_AUTHORITY_BINDING.md",
    "docs/v6/V6_DEPLOYMENT_AUTHORITY_BOUNDARY.md",
    "docs/v6/V6_LEGACY_COLLECTION_COMPATIBILITY.md",
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _self_hash(document: dict, field: str) -> str:
    payload = dict(document)
    payload.pop(field)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class Task039P1CReportTests(unittest.TestCase):
    def test_config_and_report_self_hashes(self) -> None:
        config = _read_json(CONFIG)
        report = _read_json(CONTRACT_REPORT)
        self.assertEqual(
            config["config_hash"], _self_hash(config, "config_hash")
        )
        self.assertEqual(
            report["report_hash"], _self_hash(report, "report_hash")
        )
        self.assertEqual(
            config["status"],
            "passed_canonical_context_binding_and_decoupling",
        )
        self.assertEqual(report["status"], config["status"])

    def test_required_documents_and_claim_boundary(self) -> None:
        for relative in REQUIRED_DOCS:
            with self.subTest(path=relative):
                self.assertTrue((ROOT / relative).is_file())
        text = REPORT.read_text(encoding="utf-8")
        self.assertIn(
            "TASK-039P1C connects normal-only v6 evidence and explicit outcomes",
            text,
        )
        self.assertIn("It does not implement a real Agent", text)
        self.assertIn("provider and Agent calls: 0", text)
        self.assertIn("rule execution: none", text)

    def test_parent_task_state_is_consistent(self) -> None:
        report = _read_json(CONTRACT_REPORT)
        self.assertEqual(report["parent_task"]["TASK-039P1C"], "completed")
        self.assertEqual(report["parent_task"]["TASK-039P1D"], "pending")
        self.assertEqual(report["parent_task"]["TASK-039P1"], "incomplete")
        plan = (ROOT / "IMPLEMENTATION_PLAN.md").read_text(encoding="utf-8")
        sequence = (
            ROOT / "docs/v6/V6_NEXT_TASK_SEQUENCE.md"
        ).read_text(encoding="utf-8")
        self.assertIn("**TASK-039P1C: canonical collection", plan)
        self.assertIn("Status: completed.", plan)
        self.assertIn("P1D remains pending", sequence)


if __name__ == "__main__":
    unittest.main()
