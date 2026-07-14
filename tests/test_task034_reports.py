from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPORTS = (
    "TASK-034_SPLIT_MANIFEST.json",
    "TASK-034_RUNTIME_REPORT.json",
    "TASK-034_VALIDATION_METRICS_REPORT.json",
    "TASK-034_E3_FREEZE_RECORD.json",
)


class Task034ReportTests(unittest.TestCase):
    def test_report_contract_paths_are_declared(self) -> None:
        config = json.loads(
            (ROOT / "configs/argos_reproduction/task034_e2_kpi_validation.json").read_text(encoding="utf-8")
        )
        self.assertEqual(set(config["reports"]), {"split", "runtime", "metrics", "freeze"})

    def test_present_reports_are_aggregate_and_keep_e3_sealed(self) -> None:
        for name in REPORTS:
            path = ROOT / "docs/task_reports" / name
            if not path.exists():
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            encoded = json.dumps(payload, sort_keys=True)
            self.assertNotIn("source_values", encoded)
            self.assertNotIn("target_values", encoded)
            self.assertNotIn("validation_values.npy", encoded)
            self.assertNotIn("validation_labels.npy", encoded)
            self.assertNotIn("artifacts/private_", encoded)
            self.assertFalse(payload.get("private_paths_included", False))
        freeze = ROOT / "docs/task_reports/TASK-034_E3_FREEZE_RECORD.json"
        if freeze.exists():
            payload = json.loads(freeze.read_text(encoding="utf-8"))
            self.assertEqual(payload["e3_test_status"], "sealed_not_accessed")
            self.assertEqual(payload["e3_run_status"], "not_run")
            self.assertEqual(payload["e3_authorization_status"], "not_authorized")


if __name__ == "__main__":
    unittest.main()
