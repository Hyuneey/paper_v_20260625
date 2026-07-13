import ast
import json
import shutil
import unittest
from pathlib import Path
from unittest import mock

from experiments.argos_reproduction import (
    container_preflight,
    prompt_capture,
    provider_capture,
    rule_semantic_audit,
    rule_static_analysis,
)


class Task027ArgosRuleSemanticAuditTests(unittest.TestCase):
    def setUp(self):
        self.private_root = (
            prompt_capture.REPO_ROOT
            / "artifacts"
            / "private_argos_reproduction"
            / "task027_tests"
            / self.id().split(".")[-1]
        )
        if self.private_root.exists():
            shutil.rmtree(self.private_root)
        self.private_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if self.private_root.exists():
            shutil.rmtree(self.private_root)

    def _write_config(
        self,
        source: str,
        *,
        allowed_imports: list[str] | None = None,
        allowed_calls: list[str] | None = None,
        allowed_attributes: list[str] | None = None,
        expected_hash: str | None = None,
    ) -> Path:
        rule_path = self.private_root / "captured_rule.py"
        approval_path = self.private_root / "approval.json"
        config_path = self.private_root / "config.json"
        prompt_capture.write_text(rule_path, source)
        tree = ast.parse(source)
        semantics = rule_static_analysis.analyze_code_semantics(tree)
        actual_hash = prompt_capture.sha256_file(rule_path)
        config = {
            "report_statement": "synthetic TASK-027 unit-test audit only",
            "private_rule_path": rule_path.relative_to(prompt_capture.REPO_ROOT).as_posix(),
            "frozen_artifacts": {
                "rule_hash": expected_hash or actual_hash,
                "request_hash": "synthetic",
                "response_hash": "synthetic",
            },
            "frozen_static_policy": {
                "allowed_imports": allowed_imports if allowed_imports is not None else ["numpy"],
                "allowed_calls": allowed_calls if allowed_calls is not None else semantics["normalized_call_set"],
                "allowed_attributes": (
                    allowed_attributes
                    if allowed_attributes is not None
                    else semantics["normalized_attribute_set"]
                ),
                "dangerous_capabilities_rejected": [
                    "new_imports",
                    "dynamic_attribute_access",
                    "unsafe_module_level_execution",
                ],
            },
            "container_policy": {
                "image_reference": "task027-test:local",
                "pid_limit": 8,
                "cpu_limit": 1,
                "memory_limit": "256m",
                "tmpfs_spec": "/tmp:size=1m",
                "execution_timeout_seconds": 2,
            },
            "execution_approval_template_path": approval_path.relative_to(prompt_capture.REPO_ROOT).as_posix(),
            "output_semantic_report_path": (self.private_root / "semantic.json").relative_to(
                prompt_capture.REPO_ROOT
            ).as_posix(),
            "output_container_preflight_path": (self.private_root / "preflight.json").relative_to(
                prompt_capture.REPO_ROOT
            ).as_posix(),
            "boundaries": {
                "real_provider_calls": False,
                "captured_rule_execution": False,
            },
        }
        prompt_capture.write_json(
            approval_path,
            {
                "approved": False,
                "rule_hash": expected_hash or actual_hash,
                "allowed_execution_count": 1,
                "allowed_input_kind": "synthetic_non_kpi_only",
            },
        )
        prompt_capture.write_json(config_path, config)
        return config_path

    def test_derived_thresholds_include_scale_context_and_boundary_expression(self):
        response = """```python
import numpy as np

def inference(sample: np.ndarray) -> np.ndarray:
    values = np.asarray(sample)[:, 0]
    median = np.median(values)
    deviation = np.median(np.abs(values - median))
    scale = 3.0
    boundary = median + scale * deviation
    labels = np.zeros(values.shape[0], dtype=int)
    labels[values > boundary] = 1
    return labels
```"""
        analysis = rule_static_analysis.analyze_response(response)

        targets = {
            target
            for record in analysis["derived_threshold_expressions"]
            for target in record.get("targets", [])
        }
        numeric_values = [record["value"] for record in analysis["numeric_constants_with_context"]]
        self.assertIn("boundary", targets)
        self.assertIn("scale", targets)
        self.assertIn(3.0, numeric_values)
        self.assertIn(3.0, analysis["threshold_like_numeric_constants"])
        self.assertTrue(analysis["comparisons_with_redacted_expression"])
        self.assertTrue(analysis["assignments_with_redacted_expression"])

    def test_audit_rejects_new_import_call_and_attribute(self):
        source = """import numpy as np
import os

def inference(sample: np.ndarray) -> np.ndarray:
    open(os.environ.get('TASK027_PATH', 'x'))
    return np.zeros(sample.shape[0], dtype=int)
"""
        config_path = self._write_config(
            source,
            allowed_imports=["numpy"],
            allowed_calls=["numpy.zeros"],
            allowed_attributes=["numpy.ndarray", "numpy.zeros", "sample.shape"],
        )

        report = rule_semantic_audit.audit_rule(config_path, persist=False)

        policy = report["frozen_static_policy_review"]
        self.assertEqual(policy["policy_status"], "rejected")
        self.assertIn("unexpected_imports", policy["violations"])
        self.assertIn("calls_outside_frozen_allowlist", policy["violations"])
        self.assertIn("attributes_outside_frozen_allowlist", policy["violations"])

    def test_audit_rejects_dynamic_attribute_and_top_level_execution(self):
        source = """import numpy as np
print('module side effect')

def inference(sample: np.ndarray) -> np.ndarray:
    getattr(sample, 'shape')
    return np.zeros(sample.shape[0], dtype=int)
"""
        config_path = self._write_config(source)

        report = rule_semantic_audit.audit_rule(config_path, persist=False)

        policy = report["frozen_static_policy_review"]
        self.assertEqual(policy["policy_status"], "rejected")
        self.assertIn("dynamic_attribute_access", policy["violations"])
        self.assertIn("top_level_executable_statements", policy["violations"])

    def test_hash_mismatch_stops_before_semantic_audit(self):
        source = """import numpy as np

def inference(sample: np.ndarray) -> np.ndarray:
    return np.zeros(sample.shape[0], dtype=int)
"""
        config_path = self._write_config(source, expected_hash="0" * 64)

        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            rule_semantic_audit.audit_rule(config_path, persist=False)

    def test_tracked_semantic_report_does_not_include_private_source(self):
        source = """import numpy as np
PRIVATE_SENTINEL_TASK027 = 'private-source-marker-027'

def inference(sample: np.ndarray) -> np.ndarray:
    return np.zeros(sample.shape[0], dtype=int)
"""
        config_path = self._write_config(source)

        report = rule_semantic_audit.audit_rule(config_path, persist=False)
        serialized = json.dumps(report, sort_keys=True)

        self.assertNotIn("private-source-marker-027", serialized)
        self.assertNotIn(source, serialized)
        self.assertFalse(report["raw_rule_text_included"])
        self.assertFalse(report["captured_rule_executed"])
        self.assertFalse(report["provider_call_performed"])

    def test_container_preflight_reports_unavailable_without_fallback(self):
        source = """import numpy as np

def inference(sample: np.ndarray) -> np.ndarray:
    return np.zeros(sample.shape[0], dtype=int)
"""
        config_path = self._write_config(source)

        with mock.patch.object(container_preflight.shutil, "which", return_value=None):
            report = container_preflight.container_preflight(config_path, persist=False)

        self.assertEqual(report["container_preflight_status"], "unavailable")
        self.assertFalse(report["captured_rule_execution_allowed"])
        self.assertFalse(report["captured_rule_executed"])
        self.assertFalse(report["container_launched"])
        self.assertFalse(report["restricted_subprocess_fallback_allowed"])

    def test_reproducibility_metadata_does_not_fabricate_cost(self):
        fields = provider_capture.provider_reproducibility_fields(
            {
                "model": "gpt-5.6-luna",
                "max_calls": 1,
                "max_input_tokens": 20000,
                "max_output_tokens": 2000,
                "max_cost_usd": 1.0,
            },
            {
                "model_reported": "gpt-5.6-luna",
                "request_count": 1,
                "usage": {"input_tokens": 9007, "output_tokens": 1553},
                "cost_total_usd": None,
            },
        )

        self.assertTrue(fields["model_match"])
        self.assertEqual(fields["cost_status"], "unavailable_not_reported")
        self.assertIsNone(fields["cost_total_usd"])
        self.assertFalse(fields["budget_violation_observed"])
        self.assertFalse(fields["budget_compliance_fully_verified"])

    def test_repository_execution_approval_template_remains_false(self):
        approval = rule_semantic_audit.read_json(
            prompt_capture.REPO_ROOT
            / "configs"
            / "argos_reproduction"
            / "task027_captured_rule_execution_approval.template.json"
        )
        self.assertFalse(approval["approved"])
        self.assertTrue(approval["container_runtime_required"])
        self.assertFalse(approval["performance_evaluation_allowed"])


if __name__ == "__main__":
    unittest.main()
