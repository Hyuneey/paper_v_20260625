from __future__ import annotations

import ast
import json
import unittest

import paperworks.v6
from paperworks.v6.schema_registry_v1 import (
    V6_SCHEMA_FILES,
    V6SchemaRegistryError,
    load_v6_schema_registry_v1,
)
from tests.test_task039p0_alignment_audit import ROOT, read_public_text


P1B_MODULES = (
    "src/paperworks/v6/__init__.py",
    "src/paperworks/v6/common.py",
    "src/paperworks/v6/normal_evidence_v1.py",
    "src/paperworks/v6/detector_context_v1.py",
    "src/paperworks/v6/outcomes_v1.py",
    "src/paperworks/v6/adapters_v1.py",
    "src/paperworks/v6/schema_registry_v1.py",
)
PROHIBITED_IMPORT_PREFIXES = (
    "paperworks.contracts",
    "paperworks.dsl",
    "paperworks.verification",
    "paperworks.runtime",
    "paperworks.planning",
    "paperworks.e2e",
    "experiments.argos_reproduction",
    "torch",
    "torch_geometric",
    "jsonschema",
)


class SchemaAndBoundaryTests(unittest.TestCase):
    def test_independent_schema_registry(self) -> None:
        registry = load_v6_schema_registry_v1(repository_root=ROOT)
        self.assertEqual(registry.artifact_types, tuple(sorted(V6_SCHEMA_FILES)))
        for artifact_type in registry.artifact_types:
            registration = registry.registration_for(artifact_type)
            self.assertEqual(registration.schema_version, "1.0.0")
            self.assertEqual(
                registry.schema_for(artifact_type)["properties"]["artifact_type"]["const"],
                artifact_type,
            )
        with self.assertRaises(V6SchemaRegistryError):
            registry.registration_for("unknown")

    def test_all_five_schemas_are_draft_2020_12_json(self) -> None:
        for relative in V6_SCHEMA_FILES.values():
            schema = json.loads(read_public_text(ROOT / relative))
            self.assertEqual(
                schema["$schema"], "https://json-schema.org/draft/2020-12/schema"
            )

    def test_import_boundary(self) -> None:
        observed: set[str] = set()
        for relative in P1B_MODULES:
            tree = ast.parse(read_public_text(ROOT / relative), filename=relative)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    observed.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    observed.add(node.module)
        violations = sorted(
            name
            for name in observed
            if any(
                name == prefix or name.startswith(prefix + ".")
                for prefix in PROHIBITED_IMPORT_PREFIXES
            )
        )
        self.assertEqual(violations, [])

    def test_canonical_contract_collection_unchanged_by_p1b(self) -> None:
        text = read_public_text(ROOT / "src/paperworks/contracts/__init__.py")
        self.assertNotIn("paperworks.v6", text)
        self.assertFalse(
            hasattr(paperworks.v6, "adapt_evidence_package_v1"),
            "anomaly-anchored EvidencePackageV1 must not have an automatic adapter",
        )


if __name__ == "__main__":
    unittest.main()
