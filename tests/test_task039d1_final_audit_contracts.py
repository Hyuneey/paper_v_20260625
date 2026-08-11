from __future__ import annotations

import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from paperworks.profiling.task039d1_final_audit_v1 import (
    TASK039D1FinalAuditV1,
    TASK039D2AuthorizationV1,
    audit_schema_examples_v1,
    schema_for_audit_artifact_v1,
    verify_audit_self_hash_v1,
)
from paperworks.v6.schema_registry_v1 import load_v6_schema_registry_v1


ROOT = Path(__file__).resolve().parents[1]


class TASK039D1FinalAuditContractTests(unittest.TestCase):
    def test_closed_self_hashed_round_trip(self) -> None:
        audit, authorization = audit_schema_examples_v1()
        for artifact_class, document in (
            (TASK039D1FinalAuditV1, audit),
            (TASK039D2AuthorizationV1, authorization),
        ):
            verify_audit_self_hash_v1(document)
            self.assertEqual(artifact_class.from_dict(document).to_dict(), document)
            with self.assertRaises(Exception):
                artifact_class.from_dict({**document, "unknown": True})

    def test_schemas_are_closed_registered_and_validate_examples(self) -> None:
        registry = load_v6_schema_registry_v1(repository_root=ROOT)
        self.assertEqual(len(registry.artifact_types), 146)
        for document in audit_schema_examples_v1():
            schema = registry.schema_for(document["artifact_type"])
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(schema["additionalProperties"])
            self.assertEqual(list(Draft202012Validator(schema).iter_errors(document)), [])
            self.assertNotEqual(
                list(Draft202012Validator(schema).iter_errors({**document, "unknown": True})),
                [],
            )

    def test_schema_generation_is_deterministic(self) -> None:
        audit, authorization = audit_schema_examples_v1()
        self.assertEqual(schema_for_audit_artifact_v1(audit), schema_for_audit_artifact_v1(audit))
        self.assertEqual(
            schema_for_audit_artifact_v1(authorization),
            schema_for_audit_artifact_v1(authorization),
        )


if __name__ == "__main__":
    unittest.main()
