from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.continuous_step_protocol_v1 import (
    ContinuousStepProtocolBundleV1,
    ContinuousStepRuleMigrationPlanV1,
    ContinuousStepRuntimeMigrationPlanV1,
    ContinuousStepVerifierMigrationPlanV1,
)
from paperworks.v6.schema_registry_v1 import load_v6_schema_registry_v1


ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = ROOT / "docs/task_reports"
BR1_TYPES = {
    "continuous_step_feasibility_policy_v1",
    "continuous_step_parameter_provenance_policy_v1",
    "continuous_step_process_selection_policy_v1",
    "continuous_step_protocol_bundle_v1",
    "continuous_step_relation_family_v1",
    "continuous_step_response_policy_v1",
    "continuous_step_rule_migration_plan_v1",
    "continuous_step_runtime_migration_plan_v1",
    "continuous_step_trigger_policy_v1",
    "continuous_step_unsupported_policy_v1",
    "continuous_step_verifier_migration_plan_v1",
}


class Task039BR1ReportTests(unittest.TestCase):
    def test_config_self_hash_and_boundary(self) -> None:
        path = ROOT / "configs/v6/task039br1_continuous_step_protocol.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        observed = payload.pop("config_hash")
        self.assertEqual(observed, stable_hash_v1(payload))
        self.assertFalse(payload["real_data_policy"]["real_hai_feature_access"])
        self.assertFalse(payload["real_data_policy"]["process_selection"])
        self.assertFalse(payload["migration_boundaries"]["rule_v1_modified"])

    def test_report_self_hashes_and_round_trip(self) -> None:
        cases = (
            ("TASK-039BR1_PROTOCOL_BUNDLE.json", ContinuousStepProtocolBundleV1),
            ("TASK-039BR1_RULE_MIGRATION_PLAN.json", ContinuousStepRuleMigrationPlanV1),
            ("TASK-039BR1_VERIFIER_MIGRATION_PLAN.json", ContinuousStepVerifierMigrationPlanV1),
            ("TASK-039BR1_RUNTIME_MIGRATION_PLAN.json", ContinuousStepRuntimeMigrationPlanV1),
        )
        for name, artifact_class in cases:
            with self.subTest(name=name):
                payload = json.loads((REPORT_ROOT / name).read_text(encoding="utf-8"))
                artifact = artifact_class.from_dict(payload)
                self.assertEqual(artifact.to_dict(), payload)

    def test_all_br1_schemas_registered_and_closed(self) -> None:
        registry = load_v6_schema_registry_v1(repository_root=ROOT)
        self.assertTrue(BR1_TYPES.issubset(set(registry.artifact_types)))
        for artifact_type in BR1_TYPES:
            with self.subTest(artifact_type=artifact_type):
                schema = registry.schema_for(artifact_type)
                self.assertFalse(schema["additionalProperties"])
                self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_required_documentation_exists(self) -> None:
        paths = (
            "TASKS/TASK-039BR1_CONTINUOUS_STEP_PROTOCOL.md",
            "docs/v6/CONTINUOUS_STEP_RELATION_SEMANTICS.md",
            "docs/v6/CONTINUOUS_STEP_TRIGGER_POLICY.md",
            "docs/v6/CONTINUOUS_STEP_RESPONSE_POLICY.md",
            "docs/v6/CONTINUOUS_STEP_FEASIBILITY_PREREGISTRATION.md",
            "docs/v6/CONTINUOUS_STEP_PROCESS_SELECTION_POLICY.md",
            "docs/v6/CONTINUOUS_STEP_PARAMETER_PROVENANCE.md",
            "docs/v6/CONTINUOUS_STEP_RULE_V2_MIGRATION_PLAN.md",
            "docs/v6/CONTINUOUS_STEP_VERIFIER_MIGRATION_PLAN.md",
            "docs/v6/CONTINUOUS_STEP_RUNTIME_TRACE_PLAN.md",
            "docs/task_reports/TASK-039BR1_REPORT.md",
        )
        for relative in paths:
            with self.subTest(path=relative):
                self.assertTrue((ROOT / relative).is_file())

    def test_final_report_claim_boundary(self) -> None:
        report = (REPORT_ROOT / "TASK-039BR1_REPORT.md").read_text(encoding="utf-8")
        required = (
            "passed_continuous_step_relation_protocol_freeze",
            "TASK-039BR2",
            "TASK-039C remains unauthorized",
            "does not execute the protocol on HAI",
            "does not select a process",
            "does not modify Rule v1",
            "does not create Rule v2",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, report)

    def test_public_outputs_contain_no_local_path_or_raw_sequence(self) -> None:
        public = tuple((ROOT / "docs/task_reports").glob("TASK-039BR1*")) + tuple(
            (ROOT / "docs/v6").glob("CONTINUOUS_STEP*"))
        absolute = re.compile(r"(?i)(?:[A-Z]:\\Users\\|/home/|/Users/)")
        raw_row = re.compile(r"(?m)^(?:timestamp|time),[^\n]+(?:,[-+]?\d+(?:\.\d+)?){2,}\s*$")
        for path in public:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertIsNone(absolute.search(text))
                self.assertIsNone(raw_row.search(text))


if __name__ == "__main__":
    unittest.main()
