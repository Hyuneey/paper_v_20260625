from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from paperworks.profiling.task039d2_real_execution_v1 import (
    D2_AUTHORIZATION_HASH,
    TASK039D2ExecutionError,
    expected_train3_identity_v1,
    validate_authorization_v1,
)


ROOT = Path(__file__).resolve().parents[1]


class TASK039D2RealAuthorizationTests(unittest.TestCase):
    def test_exact_independent_audit_authorization_passes(self) -> None:
        document = json.loads((ROOT / "docs/task_reports/TASK-039D2_AUTHORIZATION.json").read_text())
        parsed = validate_authorization_v1(document)
        self.assertEqual(document["artifact_hash"], D2_AUTHORIZATION_HASH)
        self.assertEqual(parsed.payload["input_directional_relation_count"], 45)

    def test_mutated_authorization_fails_closed(self) -> None:
        document = json.loads((ROOT / "docs/task_reports/TASK-039D2_AUTHORIZATION.json").read_text())
        mutated = copy.deepcopy(document)
        mutated["parameter_retuning_authorized"] = True
        with self.assertRaisesRegex(TASK039D2ExecutionError, "authorization_mismatch"):
            validate_authorization_v1(mutated)

    def test_public_manifest_binding_is_exact_train3(self) -> None:
        identity = expected_train3_identity_v1(ROOT)
        self.assertEqual(identity["relative_path"], "hai-23.05/hai-train3.csv")
        self.assertEqual(identity["row_count"], 126000)


if __name__ == "__main__":
    unittest.main()
