from __future__ import annotations

import unittest
from dataclasses import replace
import json
from pathlib import Path

from paperworks.v6.task039e1_evidence_materialization_v1 import (
    NUMERIC_ROLE_ORDER,
    PrivateConstructionEvidenceV1,
    TASK039E1Error,
    build_public_result_artifacts_v1,
    load_e0_cohort_v1,
    materialize_from_ledgers_v1,
    resolve_private_numeric_reference_v1,
)
from tests.task039e1_real_support import synthetic_real_inputs


COMMIT = "a" * 40


class RealMaterializationTests(unittest.TestCase):
    def setUp(self):
        self.inputs = synthetic_real_inputs()

    def materialize(self):
        cohort, source, target, d1, d2 = self.inputs
        return materialize_from_ledgers_v1(
            cohort=cohort, source_ledger=source, target_ledger=target,
            directional_ledger=d1, d2_ledger=d2, execution_code_commit=COMMIT,
        )

    def test_loads_exact_frozen_e0_cohort_artifact(self):
        path = Path(__file__).resolve().parents[1] / "docs/task_reports/TASK-039E0_CONFIRMED_RELATION_COHORT.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        cohort = load_e0_cohort_v1(document)
        self.assertEqual(cohort.to_dict(), document)
        self.assertEqual(len(cohort.relations), 42)

    def test_exact_42_by_11_materialization(self):
        result = self.materialize()
        self.assertEqual(result["private_ledger"]["record_count"], 42)
        self.assertEqual(result["private_ledger"]["numeric_binding_count"], 462)
        self.assertEqual(len(result["manifest"]["entries"]), 42)
        self.assertEqual(len(result["cohort"]["confirmed_relation_primitives"]), 42)
        self.assertEqual(len(result["cohort"]["approved_numeric_evidence_bundles"]), 42)
        for record in result["private_records"]:
            self.assertEqual(tuple(item.numeric_role for item in record.numeric_bindings), NUMERIC_ROLE_ORDER)

    def test_numeric_reference_binds_value_provenance_and_relation(self):
        result = self.materialize()
        record = result["private_records"][0]
        binding = record.numeric_bindings[0]
        resolved = resolve_private_numeric_reference_v1(
            proposal_numeric_reference=binding.numeric_reference,
            relation_binding_hash=record.relation_binding_hash,
            numeric_role=binding.numeric_role,
            private_evidence_record_hash=record.artifact_hash,
            private_evidence=record,
        )
        self.assertEqual(resolved["numeric_value"], binding.numeric_value)
        self.assertFalse(resolved["runtime_authority"])
        changed = replace(binding, numeric_value=binding.numeric_value + 1)
        self.assertNotEqual(changed.numeric_reference, binding.numeric_reference)
        changed_relation = replace(binding, relation_identity="directional_relation:" + "b" * 64)
        self.assertNotEqual(changed_relation.numeric_reference, binding.numeric_reference)

    def test_resolver_rejects_each_mismatching_binding(self):
        result = self.materialize()
        record = result["private_records"][0]
        binding = record.numeric_bindings[0]
        cases = (
            {"proposal_numeric_reference": "b" * 64},
            {"relation_binding_hash": "b" * 64},
            {"numeric_role": NUMERIC_ROLE_ORDER[1]},
            {"private_evidence_record_hash": "b" * 64},
        )
        base = {
            "proposal_numeric_reference": binding.numeric_reference,
            "relation_binding_hash": record.relation_binding_hash,
            "numeric_role": binding.numeric_role,
            "private_evidence_record_hash": record.artifact_hash,
            "private_evidence": record,
        }
        for change in cases:
            with self.subTest(change=change), self.assertRaises(TASK039E1Error):
                resolve_private_numeric_reference_v1(**{**base, **change})

    def test_public_outputs_do_not_contain_private_numeric_values(self):
        result = self.materialize()
        public = build_public_result_artifacts_v1(materialized=result, execution_code_commit=COMMIT)
        self.assertFalse(result["manifest"]["private_numeric_values_included"])
        self.assertFalse(result["cohort"]["runtime_authority"])
        self.assertFalse(public["result"]["rule_generated"])
        self.assertFalse(public["receipt"]["hai_accessed"])

    def test_relation_mismatch_fails_closed(self):
        cohort, source, target, d1, d2 = self.inputs
        d1["records"][0] = {**d1["records"][0], "selected_horizon_seconds": 60}
        with self.assertRaises(TASK039E1Error):
            materialize_from_ledgers_v1(
                cohort=cohort, source_ledger=source, target_ledger=target,
                directional_ledger=d1, d2_ledger=d2, execution_code_commit=COMMIT,
            )


if __name__ == "__main__":
    unittest.main()
