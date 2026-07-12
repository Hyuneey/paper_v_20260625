import shutil
import tempfile
import unittest
import zipfile
from collections import Counter
from pathlib import Path

from experiments.argos_reproduction import kpi_prepare, sandbox_runner


class Task024KpiSandboxTests(unittest.TestCase):
    def test_selects_lexicographically_smallest_eligible_kpi(self):
        stats = {
            "bbb": kpi_prepare.KpiStats(
                kpi_id="bbb",
                row_count=120,
                label_counts=Counter({"0": 100, "1": 20}),
            ),
            "aaa": kpi_prepare.KpiStats(
                kpi_id="aaa",
                row_count=120,
                label_counts=Counter({"0": 110, "1": 10}),
            ),
            "000-ineligible": kpi_prepare.KpiStats(
                kpi_id="000-ineligible",
                row_count=120,
                label_counts=Counter({"0": 120}),
            ),
        }

        self.assertEqual(kpi_prepare.select_kpi_id(stats, min_row_count=100), "aaa")

    def test_safe_extract_zip_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            zip_path = root / "bad.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("../evil.txt", "bad")

            with self.assertRaises(ValueError):
                kpi_prepare.safe_extract_zip(zip_path, root / "out")

    def test_restricted_subprocess_executes_fixed_rule_without_label_sequence(self):
        config = sandbox_runner.read_json(
            sandbox_runner.REPO_ROOT / "configs/argos_reproduction/task024_kpi_sandbox_smoke.json"
        )
        run_root = (
            sandbox_runner.REPO_ROOT
            / "artifacts"
            / "private_argos_reproduction"
            / "test_task024_sandbox"
        )
        if run_root.exists():
            shutil.rmtree(run_root)
        rule_code = (
            "import numpy as np\n\n"
            "def inference(sample: np.ndarray) -> np.ndarray:\n"
            "    return np.asarray(sample[:, 0] > 0.5, dtype=int)\n"
        )
        input_payload = {
            "sample": [[0.1, 0.0], [0.9, 1.0], [0.4, 2.0]],
            "row_count": 3,
            "columns": ["value", "index"],
            "source_label_counts": {"0": 2, "1": 1},
        }

        try:
            report = sandbox_runner.run_restricted_subprocess(
                rule_code,
                input_payload,
                config["sandbox"],
                run_root,
            )
        finally:
            if run_root.exists():
                shutil.rmtree(run_root)

        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(report["output_payload"]["shape"], [3])
        self.assertTrue(report["output_payload"]["binary_domain"])
        self.assertEqual(report["output_payload"]["positive_count"], 1)
        self.assertNotIn("labels", report["output_payload"])
        self.assertIsNotNone(report["output_hash"])
        self.assertFalse(report["network_isolation_enforced"])
        self.assertFalse(report["network_observed_used"])
        self.assertFalse(report["provider_credentials_present"])
        self.assertFalse(report["repository_write_isolation_enforced"])
        self.assertEqual(report["write_scope_observed"], "ignored_private_run_directory_only")
        self.assertFalse(report["cpu_limit_enforced"])
        self.assertFalse(report["memory_limit_enforced"])
        self.assertTrue(report["timeout_enforced"])
        self.assertTrue(report["static_rule_policy_enforced"])
        self.assertNotEqual(report.get("read_only_rule_and_input_mount"), True)


if __name__ == "__main__":
    unittest.main()
