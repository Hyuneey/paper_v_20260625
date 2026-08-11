from __future__ import annotations

import copy
import json
import os
import subprocess
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError

from paperworks.profiling.task039d2_result_recovery_v1 import (
    COMMIT_A_SCIENTIFIC_SOURCE_HASHES,
    ORIGINAL_COMMIT_A,
    SCIENTIFIC_SOURCE_PATHS,
    bind_exact_four_source_hash_schema_v1,
    validate_exact_four_source_hash_map_v1,
    verify_scientific_sources_unchanged_v1,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/v6/task039d2_real_execution_receipt_v1_schema.json"


class TASK039D2RResultContractTests(unittest.TestCase):
    def setUp(self) -> None:
        raw = subprocess.check_output([
            "git", "-C", str(ROOT), "show",
            f"{ORIGINAL_COMMIT_A}:schemas/v6/task039d2_real_execution_receipt_v1_schema.json",
        ])
        self.original_schema = json.loads(raw.decode("utf-8"))
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.validator = Draft202012Validator(self.schema)

    def _receipt(self, source_hashes: dict[str, str]) -> dict[str, object]:
        document = json.loads(
            subprocess.check_output([
                "git", "-C", str(ROOT), "show",
                f"{ORIGINAL_COMMIT_A}:schemas/v6/task039d2_real_execution_receipt_v1_schema.json",
            ]).decode("utf-8")
        )
        del document
        from paperworks.profiling.task039d2_result_recovery_v1 import build_execution_receipt_from_frozen_ledger_v1
        digest = "0" * 64
        directional = {"artifact_hash": digest}
        pair = {"artifact_hash": digest}
        arm = {"artifact_hash": digest}
        result = {"artifact_hash": digest}
        access = {"artifact_hash": digest}
        return build_execution_receipt_from_frozen_ledger_v1(
            scientific_source_hashes=source_hashes, directional=directional, pair=pair,
            arm=arm, result=result, access=access,
        )

    def test_root_cause_one_key_schema_and_four_key_runtime(self) -> None:
        original_map = self.original_schema["properties"]["scientific_source_hashes"]
        self.assertFalse(original_map["additionalProperties"])
        self.assertEqual(len(original_map["required"]), 1)
        runner = (ROOT / "scripts/run_task039d2_confirmation.py").read_text(encoding="utf-8")
        self.assertTrue(all(path in runner for path in SCIENTIFIC_SOURCE_PATHS))
        self.assertIn("bind_exact_four_source_hash_schema_v1", runner)

    def test_generated_and_committed_schema_are_identical(self) -> None:
        generated = bind_exact_four_source_hash_schema_v1(self.original_schema)
        self.assertEqual(generated, self.schema)
        source_contract = self.schema["properties"]["scientific_source_hashes"]
        self.assertFalse(source_contract["additionalProperties"])
        self.assertEqual(source_contract["required"], list(SCIENTIFIC_SOURCE_PATHS))
        self.assertEqual(set(source_contract["properties"]), set(SCIENTIFIC_SOURCE_PATHS))

    def test_exact_four_key_runtime_map_validates(self) -> None:
        receipt = self._receipt(dict(COMMIT_A_SCIENTIFIC_SOURCE_HASHES))
        self.validator.validate(receipt)
        self.assertEqual(validate_exact_four_source_hash_map_v1(receipt["scientific_source_hashes"]), COMMIT_A_SCIENTIFIC_SOURCE_HASHES)

    def test_missing_unknown_and_malformed_source_hashes_fail(self) -> None:
        exact = self._receipt(dict(COMMIT_A_SCIENTIFIC_SOURCE_HASHES))
        for remove_count in (1, 3):
            mutated = copy.deepcopy(exact)
            for key in list(SCIENTIFIC_SOURCE_PATHS)[:remove_count]:
                del mutated["scientific_source_hashes"][key]
            with self.assertRaises(ValidationError):
                self.validator.validate(mutated)
        unknown = copy.deepcopy(exact)
        unknown["scientific_source_hashes"]["src/unknown.py"] = "0" * 64
        with self.assertRaises(ValidationError):
            self.validator.validate(unknown)
        malformed = copy.deepcopy(exact)
        malformed["scientific_source_hashes"][SCIENTIFIC_SOURCE_PATHS[0]] = "not-a-sha"
        with self.assertRaises(ValidationError):
            self.validator.validate(malformed)

    def test_scientific_commit_a_blobs_are_unchanged(self) -> None:
        self.assertEqual(verify_scientific_sources_unchanged_v1(ROOT, ORIGINAL_COMMIT_A), COMMIT_A_SCIENTIFIC_SOURCE_HASHES)
        changed = subprocess.check_output([
            "git", "-C", str(ROOT), "diff", "--name-only", ORIGINAL_COMMIT_A, "--", *SCIENTIFIC_SOURCE_PATHS,
        ], text=True).strip()
        self.assertEqual(changed, "")


if __name__ == "__main__":
    unittest.main()
