from __future__ import annotations

import copy
import unittest
from pathlib import Path

from paperworks.profiling.task039d2_real_execution_v1 import (
    ARTIFACT_CLASS_BY_TYPE,
    d2_schema_examples_v1,
)
from paperworks.v6.schema_registry_v1 import load_v6_schema_registry_v1


ROOT = Path(__file__).resolve().parents[1]


class TASK039D2RealContractTests(unittest.TestCase):
    def test_all_six_artifacts_round_trip_and_reject_unknown_fields(self) -> None:
        examples = d2_schema_examples_v1()
        self.assertEqual(len(examples), 6)
        for artifact_type, document in examples.items():
            cls = ARTIFACT_CLASS_BY_TYPE[artifact_type]
            self.assertEqual(cls.from_dict(document).to_dict(), document)
            mutated = copy.deepcopy(document)
            mutated["unknown"] = True
            with self.assertRaises(Exception):
                cls.from_dict(mutated)

    def test_registry_contains_all_real_d2_schemas(self) -> None:
        registry = load_v6_schema_registry_v1(repository_root=ROOT)
        self.assertEqual(len(registry.artifact_types), 146)
        for artifact_type in d2_schema_examples_v1():
            schema = registry.schema_for(artifact_type)
            self.assertFalse(schema["additionalProperties"])
            self.assertEqual(schema["properties"]["artifact_type"]["const"], artifact_type)


if __name__ == "__main__":
    unittest.main()
