from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from paperworks.contracts import assess_legacy_artifact, assess_legacy_artifact_file


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "fixtures/task032a"
EXPECTED_CONTEXT = {
    "approved_verifier_policy",
    "dataset_version",
    "evidence_package_id",
    "graph_edge_id",
    "matched_normal_reference_id",
    "operating_regime_id",
    "parameter_record_ids",
}


def read_json(name: str) -> dict:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def canonical_hash(value: dict) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class Task032ALegacyAdapterTests(unittest.TestCase):
    def test_supported_delayed_response_is_assessment_only(self) -> None:
        source = read_json("legacy_supported_delayed_response.json")
        assessment = assess_legacy_artifact(source)
        self.assertEqual(assessment.status, "convertible_delayed_response_pending_context")
        self.assertEqual(assessment.detected_relation_family, "delayed_response")
        self.assertFalse(assessment.target_artifact_created)
        self.assertEqual(set(assessment.required_external_context), EXPECTED_CONTEXT)
        self.assertIn("synthetic_smoke_calibration_must_not_be_promoted", assessment.warnings)
        self.assertNotIn("target_artifact", assessment.to_dict())

    def test_source_object_and_file_are_not_modified(self) -> None:
        source = read_json("legacy_supported_delayed_response.json")
        before = copy.deepcopy(source)
        before_hash = canonical_hash(source)
        assessment = assess_legacy_artifact(source)
        self.assertEqual(source, before)
        self.assertEqual(canonical_hash(source), before_hash)
        self.assertEqual(assessment.source_sha256, before_hash)

        path = FIXTURE_ROOT / "legacy_supported_delayed_response.json"
        file_before = path.read_bytes()
        assess_legacy_artifact_file(path)
        self.assertEqual(path.read_bytes(), file_before)

    def test_unsupported_relation_and_multivariate_inputs_are_explicit(self) -> None:
        relation = assess_legacy_artifact(read_json("legacy_unsupported_relation.json"))
        multivariate = assess_legacy_artifact(read_json("legacy_unsupported_multivariate.json"))
        self.assertEqual(relation.status, "unsupported_legacy_artifact")
        self.assertEqual(multivariate.status, "unsupported_legacy_artifact")
        self.assertIn("multiple_sources_or_targets_are_outside_the_mvp", multivariate.unsupported_reasons)
        self.assertFalse(relation.target_artifact_created)
        self.assertFalse(multivariate.target_artifact_created)

    def test_malformed_structure_is_invalid(self) -> None:
        assessment = assess_legacy_artifact(read_json("legacy_invalid_structure.json"))
        self.assertEqual(assessment.status, "invalid_legacy_artifact")
        self.assertIn("trigger_variable_contradicts_source", assessment.unsupported_reasons)

    def test_executable_dynamic_fields_and_missing_identifier_are_rejected(self) -> None:
        executable = read_json("legacy_supported_delayed_response.json")
        executable["payload"]["dynamic_expression"] = "prohibited fixture marker"
        assessment = assess_legacy_artifact(executable)
        self.assertEqual(assessment.status, "unsupported_legacy_artifact")
        self.assertTrue(assessment.unsupported_reasons[0].startswith("executable_or_dynamic_field:"))

        missing_identifier = read_json("legacy_supported_delayed_response.json")
        del missing_identifier["source_schema_identifier"]
        missing = assess_legacy_artifact(missing_identifier)
        self.assertEqual(missing.status, "unsupported_legacy_artifact")
        self.assertIn("missing_or_unrecognized_legacy_schema_identifier", missing.unsupported_reasons)

        expression = read_json("legacy_supported_delayed_response.json")
        expression["payload"]["formula"] = "synthetic marker"
        rejected_expression = assess_legacy_artifact(expression)
        self.assertEqual(rejected_expression.status, "unsupported_legacy_artifact")

    def test_new_contract_modules_have_no_prohibited_execution_surface(self) -> None:
        package_root = REPO_ROOT / "src/paperworks/contracts"
        prohibited = ("exec(", "eval(", "compile(", "subprocess", "importlib", "requests", "httpx")
        for path in package_root.glob("*.py"):
            text = path.read_text(encoding="utf-8")
            for marker in prohibited:
                self.assertNotIn(marker, text, (path.name, marker))
            self.assertNotIn("SWAT_DATA_ROOT", text)
            self.assertNotIn("external/argos", text)

    def test_tracked_assessment_report_contains_no_target_artifacts(self) -> None:
        report = json.loads(
            (REPO_ROOT / "docs/task_reports/TASK-032A_LEGACY_ASSESSMENT_REPORT.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(report["counts"]["target_artifacts_created"], 0)
        self.assertFalse(report["conversion_performed"])
        self.assertFalse(report["partial_conversion_allowed"])
        for assessment in report["assessments"]:
            self.assertFalse(assessment["target_artifact_created"])


if __name__ == "__main__":
    unittest.main()
