from __future__ import annotations

import ast
import inspect
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from paperworks.profiling import task039d2_final_audit_v1 as audit
from paperworks.profiling.task039d2_audit_reference_v1 import (
    replay_synthetic_directions_reference_v1,
)
from paperworks.v6.common import stable_hash_v1
from paperworks.v6.schema_registry_v1 import load_v6_schema_registry_v1
from tests.task039d2_audit_support import make_input_set, synthetic_value_map


ROOT = Path(__file__).resolve().parents[1]


class TASK039D2FinalAuditContractTests(unittest.TestCase):
    def test_closed_self_hashed_contracts_and_authority_boundary(self) -> None:
        final_audit, authorization = audit.audit_schema_examples_v1()
        for cls, document in (
            (audit.TASK039D2FinalAuditV1, final_audit),
            (audit.TASK039E0AuthorizationV1, authorization),
        ):
            audit.verify_audit_self_hash_v1(document)
            self.assertEqual(cls.from_dict(document).to_dict(), document)
            with self.assertRaises(Exception):
                cls.from_dict({**document, "unknown": True})
        self.assertTrue(authorization["construction_evidence_protocol_design_authorized"])
        self.assertFalse(authorization["real_rule_generation_authorized"])
        self.assertFalse(authorization["llm_calls_authorized"])
        self.assertFalse(authorization["rule_v2_runtime_authorized"])
        self.assertFalse(authorization["agent_execution_authorized"])

    def test_schemas_closed_registered_and_examples_validate(self) -> None:
        registry = load_v6_schema_registry_v1(repository_root=ROOT)
        self.assertEqual(len(registry.artifact_types), 160)
        for document in audit.audit_schema_examples_v1():
            schema = registry.schema_for(document["artifact_type"])
            self.assertFalse(schema["additionalProperties"])
            self.assertEqual(list(Draft202012Validator(schema).iter_errors(document)), [])
            self.assertNotEqual(
                list(Draft202012Validator(schema).iter_errors({**document, "unknown": True})),
                [],
            )

    def test_audit_module_does_not_import_or_call_production_confirmation(self) -> None:
        tree = ast.parse(inspect.getsource(audit))
        imports = []
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
            elif isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.append(node.func.attr)
        self.assertFalse(any("task039d2_confirmation_v1" in item for item in imports))
        self.assertNotIn("confirm_relations_one_way_v1", calls)
        self.assertNotIn("load_authorized_train3_values_v1", calls)

    def test_bounded_response_matches_prepared_reference(self) -> None:
        values = [0.0] * 40
        values[11:14] = [3.0, 3.0, 3.0]
        expected = audit._bounded_target_response(values, event_index=10, horizon=1)
        from paperworks.profiling.task039d2_audit_reference_v1 import (
            reconstruct_target_response_reference_v1,
        )
        self.assertEqual(
            expected,
            reconstruct_target_response_reference_v1(
                values, event_index=10, selected_horizon_seconds=1
            ),
        )

    def test_full_45_direction_synthetic_replay_matches_prepared_oracle(self) -> None:
        input_set = make_input_set()
        values = synthetic_value_map().values
        expected = replay_synthetic_directions_reference_v1(
            directional_inputs=input_set.directional_inputs,
            source_parameters=input_set.source_parameters,
            target_parameters=input_set.target_parameters,
            value_map=synthetic_value_map(),
        )
        records = []
        for item in expected:
            relation = next(
                relation for relation in input_set.directional_inputs
                if relation.d1_directional_record_hash == item.d1_directional_record_hash
            )
            content = {
                "d1_directional_record_hash": item.d1_directional_record_hash,
                "source": item.source,
                "source_step_direction": item.source_step_direction,
                "target": item.target,
                "target_response_direction": item.target_response_direction,
                "selected_horizon_seconds": item.selected_horizon_seconds,
                "source_parameter_record_hash": relation.d1_source_parameter_record_hash,
                "target_parameter_record_hash": relation.d1_target_parameter_record_hash,
                "train3_usable_response_count": item.usable_response_count,
                "right_censored_count": item.right_censored_count,
                "selected_directional_consistency": item.selected_consistency,
                "opposite_directional_consistency": item.opposite_consistency,
                "median_target_response": item.median_target_response,
                "robust_effect_ratio": item.robust_effect_ratio,
                "source_direction_unchanged": True,
                "fit_parameters_reused_without_retuning": True,
                "parameter_retuning_used": False,
                "alternative_horizon_search_used": False,
                "opposite_direction_search_used": False,
                "lower_ranked_fallback_used": False,
                "candidate_provenance_visible": False,
                "confirmation_status": item.status,
            }
            records.append({**content, "artifact_hash": stable_hash_v1(content)})
        original_ledger = {"records": records}
        with tempfile.TemporaryDirectory() as directory:
            private_root = Path(directory) / "audit"
            result = audit.replay_train3_independently_v1(
                input_set=input_set,
                values=values,
                original_ledger=original_ledger,
                audit_private_root=private_root,
            )
            frozen = audit.load_frozen_audit_replay_v1(
                input_set=input_set,
                original_ledger=original_ledger,
                audit_private_root=private_root,
            )
        self.assertEqual(result["confirmed_count"], sum(item.status == "calibration_confirmed" for item in expected))
        self.assertEqual(frozen["audit_private_ledger_hash"], result["audit_private_ledger_hash"])
        self.assertTrue(result["record_level_parity"])


if __name__ == "__main__":
    unittest.main()
