from __future__ import annotations

import ast
import hashlib
import json
import unittest

from paperworks.data.schema_registry_v2 import (
    V2_META_SCHEMA,
    V2_SCHEMA_FILES,
    load_schema_registry_v2,
)
from tests.test_task039p0_alignment_audit import (
    ROOT,
    read_public_bytes,
    read_public_text,
)
from tests.task039p1a_support import (
    data_view_manifest_v2,
    dataset_manifest_v2,
    split_manifest_v2,
)
from paperworks.data.contracts_v2 import SplitRoleV2

FORBIDDEN_IMPORTS = (
    "paperworks.dsl",
    "paperworks.verification",
    "paperworks.runtime",
    "paperworks.planning.refiner",
    "paperworks.e2e",
    "experiments.argos_reproduction",
)
V1_SCHEMA_HASHES = {
    "schemas/evidence_package_schema.json": "efe7037c44b7b7ca8525fed352f10202d6e3ce5bc4e4a07c8e70bc08d2cc40d7",
    "schemas/explanation_record_schema.json": "bf72609ca7b2d6f03b0ea16a31ff2cfdf111a5545ce62c3c3514e599acc06081",
    "schemas/graph_schema.json": "a26fe5c7ca02629f2c57a37a6edf3efa4bad8712951a15740b7787fa7d96d271",
    "schemas/parameter_registry_schema.json": "1d2cd55385bead2ef8563ca06f6e548e3c49b3f3f7bf06bb23f2fae10ff03065",
    "schemas/rule_dsl_schema.json": "67d50b9b3fd229c6fa6294f3106339c4ba2c093edb48a8be2100817379f7fa8a",
    "schemas/runtime_trace_schema.json": "cc90b512bbf36370f3ec041a6f5747c5f9c087b7deaf7160285c7a5c476a17e6",
    "schemas/verifier_result_schema.json": "9d1325a0832c6a0886f8438e1459373a2dd1db3791d88b454055056578002ae4",
}


class Task039P1ASchemaAndBoundaryTests(unittest.TestCase):
    def test_independent_registry_contains_exactly_four_v2_schemas(self) -> None:
        registry = load_schema_registry_v2(repository_root=ROOT)
        self.assertEqual(registry.artifact_types, tuple(sorted(V2_SCHEMA_FILES)))
        for artifact_type in registry.artifact_types:
            registration = registry.registration_for(artifact_type)
            schema = registry.schema_for(artifact_type)
            self.assertEqual(schema["$schema"], V2_META_SCHEMA)
            self.assertEqual(
                schema["properties"]["artifact_type"]["const"], artifact_type
            )
            self.assertRegex(registration.schema_sha256, r"^[a-f0-9]{64}$")

    def test_contract_serializations_match_schema_required_fields(self) -> None:
        registry = load_schema_registry_v2(repository_root=ROOT)
        instances = {
            "dataset_manifest_v2": dataset_manifest_v2().to_dict(),
            "data_view_manifest_v2": data_view_manifest_v2().to_dict(),
            "split_manifest_v2": split_manifest_v2(
                SplitRoleV2.NORMAL_GUARD
            ).to_dict(),
        }
        for artifact_type, instance in instances.items():
            with self.subTest(artifact_type=artifact_type):
                schema = registry.schema_for(artifact_type)
                self.assertEqual(set(instance), set(schema["required"]))
                self.assertEqual(instance["schema_version"], "2.0.0")
                self.assertEqual(instance["artifact_type"], artifact_type)

    def test_existing_seven_schema_bytes_are_unchanged(self) -> None:
        for relative, expected in V1_SCHEMA_HASHES.items():
            with self.subTest(relative=relative):
                observed = hashlib.sha256(
                    read_public_bytes(ROOT / relative)
                ).hexdigest()
                self.assertEqual(observed, expected)

    def test_v2_modules_do_not_import_legacy_or_reference_paths(self) -> None:
        paths = (
            "src/paperworks/data/contracts_v2.py",
            "src/paperworks/data/splits_v2.py",
            "src/paperworks/data/adapters_v2.py",
            "src/paperworks/data/schema_registry_v2.py",
        )
        for relative in paths:
            tree = ast.parse(read_public_text(ROOT / relative))
            imported: list[str] = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imported.append(node.module or "")
            with self.subTest(relative=relative):
                for module in imported:
                    self.assertFalse(
                        any(
                            module == forbidden
                            or module.startswith(forbidden + ".")
                            for forbidden in FORBIDDEN_IMPORTS
                        ),
                        module,
                    )

    def test_schema_files_are_plain_draft_2020_12_json(self) -> None:
        for relative in V2_SCHEMA_FILES.values():
            payload = json.loads(read_public_text(ROOT / relative))
            self.assertEqual(payload["$schema"], V2_META_SCHEMA)
            self.assertFalse(payload.get("additionalProperties", True))


if __name__ == "__main__":
    unittest.main()
