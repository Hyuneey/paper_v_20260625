from __future__ import annotations

import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from paperworks.profiling.task039d1_fit_v1 import (
    ARTIFACT_CLASS_BY_TYPE,
    ARTIFACT_CLASSES,
    TASK039D1Error,
    d1_schema_examples_v1,
    ledger_binding_v1,
    schema_for_d1_artifact_v1,
    verify_d1_self_hash_v1,
    TASK039D1SourceParameterLedgerBindingV1,
)
from paperworks.v6.schema_registry_v1 import load_v6_schema_registry_v1


ROOT = Path(__file__).resolve().parents[1]


class Task039D1FitContractTests(unittest.TestCase):
    def test_all_eight_artifacts_are_closed_self_hashed_and_round_trip(self) -> None:
        examples = d1_schema_examples_v1()
        self.assertEqual(set(examples), set(ARTIFACT_CLASS_BY_TYPE))
        self.assertEqual(len(ARTIFACT_CLASSES), 8)
        for artifact_type, document in examples.items():
            verify_d1_self_hash_v1(document)
            restored = ARTIFACT_CLASS_BY_TYPE[artifact_type].from_dict(document)
            self.assertEqual(restored.artifact_hash, document["artifact_hash"])
            with self.assertRaises(Exception):
                ARTIFACT_CLASS_BY_TYPE[artifact_type].from_dict({**document, "unknown": True})

    def test_all_schemas_are_draft_2020_12_closed_and_registered(self) -> None:
        registry = load_v6_schema_registry_v1(repository_root=ROOT)
        self.assertEqual(len(registry.artifact_types), 146)
        examples = d1_schema_examples_v1()
        for artifact_type, document in examples.items():
            schema = registry.schema_for(artifact_type)
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(schema["additionalProperties"])
            self.assertEqual(list(Draft202012Validator(schema).iter_errors(document)), [])
            self.assertNotEqual(
                list(Draft202012Validator(schema).iter_errors({**document, "extra": 1})),
                [],
            )

    def test_schema_generation_is_deterministic(self) -> None:
        example = next(iter(d1_schema_examples_v1().values()))
        self.assertEqual(schema_for_d1_artifact_v1(example), schema_for_d1_artifact_v1(example))

    def test_private_ledger_binding_exposes_hash_and_count_only(self) -> None:
        ledger = {
            "schema_version": "1.0.0",
            "artifact_type": "private_test_v1",
            "record_count": 12,
            "records": [{"private": 1}],
        }
        from paperworks.v6.common import stable_hash_v1
        ledger["artifact_hash"] = stable_hash_v1(ledger)
        binding = ledger_binding_v1(TASK039D1SourceParameterLedgerBindingV1, ledger=ledger).to_dict()
        self.assertEqual(binding["record_count"], 12)
        self.assertNotIn("records", binding)
        self.assertFalse(binding["private_contents_public"])

    def test_mutated_hash_rejected(self) -> None:
        document = next(iter(d1_schema_examples_v1().values()))
        with self.assertRaises(TASK039D1Error):
            verify_d1_self_hash_v1({**document, "artifact_hash": "f" * 64})


if __name__ == "__main__":
    unittest.main()
