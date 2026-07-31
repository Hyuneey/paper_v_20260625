from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from paperworks.gdn.fidelity_v1 import GDNFidelityFreezeV1


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/v6/task039p1d_gdn_fidelity_freeze.json"
IMPORT_REPORT = ROOT / "docs/task_reports/TASK-039P1D_IMPORT_REPORT.json"
FIDELITY_REPORT = ROOT / "docs/task_reports/TASK-039P1D_FIDELITY_REPORT.json"
REPORT = ROOT / "docs/task_reports/TASK-039P1D_REPORT.md"
REQUIRED_DOCS = (
    "TASKS/TASK-039P1D_GDN_IMPORT_AND_FIDELITY.md",
    "docs/v6/V6_GDN_OPTIONAL_DEPENDENCY_BOUNDARY.md",
    "docs/v6/V6_GDN_FIDELITY_AUDIT.md",
    "docs/v6/V6_GDN_BACKEND_USE_POLICY.md",
    "docs/v6/V6_GDN_UPSTREAM_MAPPING.md",
)


def _canonical_hash(document: dict, field: str) -> str:
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


class Task039P1DReportTests(unittest.TestCase):
    def test_config_and_reports_are_self_hashed(self) -> None:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        import_report = json.loads(IMPORT_REPORT.read_text(encoding="utf-8"))
        fidelity_report = json.loads(FIDELITY_REPORT.read_text(encoding="utf-8"))
        self.assertEqual(config["config_hash"], _canonical_hash(config, "config_hash"))
        self.assertEqual(
            import_report["report_hash"],
            _canonical_hash(import_report, "report_hash"),
        )
        self.assertEqual(
            fidelity_report["report_hash"],
            _canonical_hash(fidelity_report, "report_hash"),
        )
        parsed = GDNFidelityFreezeV1.from_dict(config)
        self.assertEqual(parsed.artifact_hash, config["artifact_hash"])

    def test_required_documents_and_completion_state(self) -> None:
        for relative in REQUIRED_DOCS:
            with self.subTest(path=relative):
                self.assertTrue((ROOT / relative).is_file())
        report = REPORT.read_text(encoding="utf-8")
        self.assertIn("passed_gdn_optional_import_and_fidelity_freeze", report)
        self.assertIn("TASK-039P1D resolves the optional dependency", report)
        self.assertIn("It does not implement or validate the final production GDN", report)
        sequence = (
            ROOT / "docs/v6/V6_NEXT_TASK_SEQUENCE.md"
        ).read_text(encoding="utf-8")
        self.assertIn("TASK-039P1 is complete", sequence)
        self.assertIn("next task is TASK-039A", sequence)

    def test_reports_preserve_historical_hashes_and_scope(self) -> None:
        fidelity = json.loads(FIDELITY_REPORT.read_text(encoding="utf-8"))
        imports = json.loads(IMPORT_REPORT.read_text(encoding="utf-8"))
        compatibility = fidelity["historical_compatibility"]
        self.assertTrue(compatibility["torch_backend_behavior_AST_unchanged"])
        self.assertTrue(compatibility["masked_source_unchanged"])
        self.assertEqual(len(compatibility["TASK005_checkpoint_id"]), 64)
        self.assertEqual(len(compatibility["TASK005_edge_artifact_id"]), 64)
        self.assertFalse(compatibility["numerical_replay_executed"])
        self.assertEqual(imports["scope"]["provider_calls"], 0)
        self.assertFalse(imports["scope"]["dataset_access"])
        self.assertFalse(imports["scope"]["rule_execution"])


if __name__ == "__main__":
    unittest.main()
