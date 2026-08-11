from __future__ import annotations

import ast
import copy
import json
from pathlib import Path
import unittest

from paperworks.v6.schema_registry_v1 import load_v6_schema_registry_v1
from paperworks.v6.task039e2_execution_configuration_v1 import (
    ARTIFACT_CLASSES,
    PUBLIC_REPORT_FILES,
    STATUS,
    build_task039e2_artifacts_v1,
    schema_documents_v1,
    verify_self_hash_v1,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"


class AuthoritativeReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts = build_task039e2_artifacts_v1(ROOT)

    def test_committed_reports_equal_deterministic_build(self) -> None:
        for name, filename in PUBLIC_REPORT_FILES.items():
            with self.subTest(name=name):
                committed = json.loads((REPORTS / filename).read_text(encoding="utf-8"))
                self.assertEqual(self.artifacts[name].to_dict(), committed)
                self.assertEqual(committed["artifact_hash"], verify_self_hash_v1(committed))
        self.assertEqual(STATUS, self.artifacts["protocol_bundle"].to_dict()["status"])

    def test_committed_artifact_schemas_equal_generator(self) -> None:
        schemas = schema_documents_v1(self.artifacts)
        for artifact_type, schema in schemas.items():
            with self.subTest(artifact_type=artifact_type):
                committed = json.loads(
                    (ROOT / "schemas" / "v6" / f"{artifact_type}_schema.json").read_text(encoding="utf-8")
                )
                self.assertEqual(schema, committed)
                self.assertFalse(committed["additionalProperties"])

    def test_instances_validate_and_unknown_fields_fail(self) -> None:
        try:
            import jsonschema
        except ModuleNotFoundError:
            self.skipTest("jsonschema unavailable")
        schemas = schema_documents_v1(self.artifacts)
        for artifact in self.artifacts.values():
            document = artifact.to_dict()
            validator = jsonschema.Draft202012Validator(schemas[artifact.ARTIFACT_TYPE])
            self.assertEqual([], list(validator.iter_errors(document)))
            altered = copy.deepcopy(document)
            altered["unknown"] = True
            self.assertTrue(list(validator.iter_errors(altered)))

    def test_all_authoritative_schemas_are_registered(self) -> None:
        registry = load_v6_schema_registry_v1(repository_root=ROOT)
        for cls in ARTIFACT_CLASSES:
            self.assertIn(cls.ARTIFACT_TYPE, registry.artifact_types)

    def test_no_provider_private_or_credential_access_path_in_e2(self) -> None:
        paths = (
            ROOT / "src/paperworks/v6/task039e2_execution_configuration_v1.py",
            ROOT / "scripts/run_task039e2_execution_freeze.py",
        )
        for path in paths:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".")[0])
            self.assertTrue(imports.isdisjoint({"openai", "requests", "httpx", "urllib", "socket"}))
            self.assertNotIn("os.getenv", source)
            self.assertNotIn("os.environ", source)
            self.assertNotIn("TASK039E1_PRIVATE_ROOT", source)
            self.assertNotIn("materialize_construction_evidence", source)
            self.assertNotIn("provider_client", source)

    def test_no_e3_authorization_artifact_exists(self) -> None:
        self.assertFalse((REPORTS / "TASK-039E3_AUTHORIZATION.json").exists())


if __name__ == "__main__":
    unittest.main()
