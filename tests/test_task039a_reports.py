from __future__ import annotations

import json
import unittest
from pathlib import Path

from paperworks.data.hai_provenance_v1 import canonical_self_hash


ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = ROOT / "docs/task_reports"
RESULT_JSON = (
    "TASK-039A_DATASET_MANIFEST_V2.json",
    "TASK-039A_SOURCE_RECEIPT.json",
    "TASK-039A_CSV_STRUCTURE_REPORT.json",
    "TASK-039A_LABEL_CUSTODY_PUBLIC_REPORT.json",
    "TASK-039A_REFERENCE_INVENTORY.json",
    "TASK-039A_PROVENANCE_REPORT.json",
)
BLOCKED_JSON = {
    "TASK-039A_SOURCE_RECEIPT.json",
    "TASK-039A_PROVENANCE_REPORT.json",
}


class Task039AReportTests(unittest.TestCase):
    def test_implementation_phase_or_complete_result_set(self) -> None:
        present = [name for name in RESULT_JSON if (REPORT_ROOT / name).exists()]
        observed = frozenset(present)
        self.assertIn(
            observed,
            {frozenset(), frozenset(BLOCKED_JSON), frozenset(RESULT_JSON)},
        )
        if observed == frozenset(RESULT_JSON):
            report = (REPORT_ROOT / "TASK-039A_REPORT.md").read_text(encoding="utf-8")
            self.assertIn("passed_hai_2305_official_provenance_audit", report)
            self.assertIn("It does not select a process", report)
        elif observed == frozenset(BLOCKED_JSON):
            report = (REPORT_ROOT / "TASK-039A_REPORT.md").read_text(encoding="utf-8")
            self.assertIn("blocked_", report)
            self.assertIn("TASK-039B remains blocked", report)

    def test_any_result_json_is_self_hashed_and_public(self) -> None:
        for name in RESULT_JSON:
            path = REPORT_ROOT / name
            if not path.exists():
                continue
            with self.subTest(path=name):
                document = json.loads(path.read_text(encoding="utf-8"))
                field = "artifact_hash" if "artifact_hash" in document else "report_hash"
                self.assertEqual(document[field], canonical_self_hash(document, field))
                text = json.dumps(document, sort_keys=True).lower()
                self.assertNotIn("attack_start", text)
                self.assertNotIn("attack_target", text)
                self.assertNotIn("label_events", text)
                self.assertNotIn("summary_records", text)


if __name__ == "__main__":
    unittest.main()
