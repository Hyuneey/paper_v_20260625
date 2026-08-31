from __future__ import annotations

from dataclasses import replace
from hashlib import sha1, sha256
import json
from pathlib import Path
import tempfile
import unittest

from paperworks.validation_v2.formal_v4_authority_v1 import (
    V4_NUMERIC_ROLES,
    FormalV4ArtifactBindingV1,
    FormalV4AuthorityError,
    FormalV4AuthorizedRuntimeV1,
    FormalV4EvaluatorContractV1,
    FormalV4ExecutionContextV1,
    FormalV4RuleDescriptorV1,
    NumericReferenceBindingV1,
    authorize_formal_v4_runtime_v1,
    build_formal_v4_portfolio_authority_v1,
    canonical_document_hash_v1,
    validate_formal_v4_portfolio_authority_v1,
    validate_formal_v4_runtime_authorization_v1,
)
from paperworks.validation_v2.runtime_v1 import (
    FORMAL_V4_RESPONSE_POLICY_HASH,
    FORMAL_V4_TRACE_CONTRACT_HASH,
    FORMAL_V4_TRIGGER_POLICY_HASH,
    FormalV4ObservationWindowV1,
    execute_formal_v4_rule_v1,
)
from paperworks.validation_v2.schema_registry_v1 import (
    load_validation_v2_schema_registry_v1,
    validate_validation_v2_document_v1,
)


def h(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def git_commit(value: str) -> str:
    return sha1(value.encode("utf-8")).hexdigest()


class V2Fixture:
    def __init__(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.commit = git_commit("source-commit")
        self.runtime_path = "src/paperworks/validation_v2/runtime_v1.py"
        source_runtime = Path(__file__).parents[1] / self.runtime_path
        self._write_bytes(self.runtime_path, source_runtime.read_bytes())
        self.runtime_binding = self._binding("V2-RUNTIME-V1", self.runtime_path)
        self.evaluator = FormalV4EvaluatorContractV1(
            evaluator_id="V2-V4-EVALUATOR-1",
            implementation_path=self.runtime_path,
            implementation_hash=self.runtime_binding.content_sha256,
            trigger_policy_hash=FORMAL_V4_TRIGGER_POLICY_HASH,
            response_policy_hash=FORMAL_V4_RESPONSE_POLICY_HASH,
            trace_contract_hash=FORMAL_V4_TRACE_CONTRACT_HASH,
        )
        for name in ("feature", "file", "sampling", "runtime-config"):
            self._write_json(f"authority/{name}.json", {"artifact": name, "version": 1})
        self.feature_binding = self._binding("V2-FEATURE", "authority/feature.json")
        self.file_binding = self._binding("V2-FILE", "authority/file.json")
        self.sampling_binding = self._binding("V2-SAMPLING", "authority/sampling.json")
        self.config_binding = self._binding("V2-RUNTIME-CONFIG", "authority/runtime-config.json")
        self.relation_specs = (("REL-1", "step_up", "increase", 5), ("REL-2", "step_down", "decrease", 60))
        self.numeric_values = {
            "source_step_threshold": 1.0, "source_stability_tolerance": 0.1, "target_noise_scale": 0.2,
            "source_pre_window_seconds": 2.0, "source_post_window_seconds": 2.0,
            "minimum_source_stability_fraction": 1.0, "source_refractory_seconds": 0.0,
            "cross_source_isolation_radius_seconds": 0.0, "target_baseline_window_seconds": 2.0,
            "target_response_window_seconds": 2.0,
        }
        numeric_document = {
            "artifact_type": "validation_v2_formal_v4_numeric_authority_v1",
            "bindings": [
                {
                    "numeric_role": role,
                    "reference_hash": self._reference_hash(relation, role, index),
                    "reference_id": f"REF-{relation}-{index}",
                    "relation_id": relation,
                    "value": float(self.numeric_values[role]),
                }
                for relation, _, _, _ in self.relation_specs
                for index, role in enumerate(V4_NUMERIC_ROLES)
            ],
            "schema_version": "1.0.0",
        }
        self._write_json("authority/numeric.json", numeric_document)
        self.numeric_binding = self._binding("V2-NUMERIC", "authority/numeric.json")
        self.descriptors = tuple(self._descriptor(*spec) for spec in self.relation_specs)
        relation_document = {
            "artifact_type": "validation_v2_formal_v4_relation_authority_v1",
            "relations": [
                {
                    "relation_binding_hash": item.relation_binding_hash,
                    "relation_id": item.relation_id,
                    "selected_horizon_seconds": item.selected_horizon_seconds,
                    "semantic_execution_hash": item.semantic_execution_hash,
                    "source": item.source,
                    "source_direction": item.source_direction,
                    "target": item.target,
                    "target_direction": item.target_direction,
                }
                for item in self.descriptors
            ],
            "schema_version": "1.0.0",
        }
        self._write_json("authority/relations.json", relation_document)
        self.relation_binding = self._binding("V2-RELATIONS", "authority/relations.json")
        self.authority = build_formal_v4_portfolio_authority_v1(
            method_id="VALIDATION-V2-RULE-ONLY", config_id="CONFIG-V2-1", experiment_id="EXP-04-V2",
            portfolio_id="V2-PORTFOLIO-2", source_commit=self.commit, descriptors=self.descriptors,
            relation_authority_binding=self.relation_binding, numeric_authority_binding=self.numeric_binding,
            feature_contract_binding=self.feature_binding, file_contract_binding=self.file_binding,
            sampling_contract_binding=self.sampling_binding, evaluator=self.evaluator, repository_root=self.root,
        )
        self.context = FormalV4ExecutionContextV1(
            source_commit=self.commit, runtime_config_binding=self.config_binding,
            relation_authority_binding=self.relation_binding, numeric_authority_binding=self.numeric_binding,
            feature_contract_binding=self.feature_binding, file_contract_binding=self.file_binding,
            sampling_contract_binding=self.sampling_binding, evaluator_implementation_binding=self.runtime_binding,
        )
        self.bundle = authorize_formal_v4_runtime_v1(
            self.authority, self.evaluator, expected_source_commit=self.commit,
            execution_context=self.context, repository_root=self.root, split_role="DEVELOPMENT_TEST1",
        )

    def close(self) -> None:
        self.temporary.cleanup()

    def _write_bytes(self, relative: str, raw: bytes) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def _write_json(self, relative: str, document: object) -> None:
        self._write_bytes(relative, json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8"))

    def _binding(self, artifact_id: str, relative: str) -> FormalV4ArtifactBindingV1:
        return FormalV4ArtifactBindingV1(artifact_id, relative, sha256((self.root / relative).read_bytes()).hexdigest())

    def _descriptor(self, relation: str, source_direction: str, target_direction: str, horizon: int) -> FormalV4RuleDescriptorV1:
        bindings = tuple(NumericReferenceBindingV1(role, f"REF-{relation}-{index}", self._reference_hash(relation, role, index)) for index, role in enumerate(V4_NUMERIC_ROLES))
        return FormalV4RuleDescriptorV1(
            relation_id=relation, relation_binding_hash=h(f"binding-{relation}"), semantic_execution_hash=h(f"semantic-{relation}"),
            source=f"SRC-{relation}", target=f"TGT-{relation}", source_direction=source_direction,
            target_direction=target_direction, selected_horizon_seconds=horizon, numeric_reference_bindings=bindings,
            numeric_authority_hash=self.numeric_binding.content_sha256,
        )

    def _reference_hash(self, relation: str, role: str, index: int) -> str:
        return canonical_document_hash_v1({
            "numeric_role": role,
            "reference_id": f"REF-{relation}-{index}",
            "relation_id": relation,
            "value": float(self.numeric_values[role]),
        })


class FormalV4AuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = V2Fixture()

    def tearDown(self) -> None:
        self.fx.close()

    def test_schema_registry_validates_produced_documents(self) -> None:
        self.assertEqual(len(load_validation_v2_schema_registry_v1()), 19)
        validate_validation_v2_document_v1("formal_v4_portfolio_authority_v1.schema.json", self.fx.authority.to_dict())
        validate_validation_v2_document_v1("formal_v4_runtime_authorization_v1.schema.json", self.fx.bundle.receipt.to_dict())

    def test_authority_denies_canonical_and_heldout_claims(self) -> None:
        validate_formal_v4_portfolio_authority_v1(
            self.fx.authority, evaluator=self.fx.evaluator, expected_source_commit=self.fx.commit, repository_root=self.fx.root
        )
        document = self.fx.authority.to_dict()
        self.assertEqual(document["authority_family"], "FORMAL_V4")
        self.assertFalse(document["canonical_rule_v1_authoritative"])
        self.assertFalse(document["verifier_v1_authoritative"])
        self.assertFalse(document["heldout_authorized"])

    def test_runtime_authorization_replays_actual_context(self) -> None:
        self.assertEqual(
            validate_formal_v4_runtime_authorization_v1(self.fx.bundle, execution_context=self.fx.context, repository_root=self.fx.root),
            self.fx.bundle.receipt.authorization_hash,
        )
        stale = replace(self.fx.context, source_commit=git_commit("stale"))
        with self.assertRaises(FormalV4AuthorityError):
            validate_formal_v4_runtime_authorization_v1(self.fx.bundle, execution_context=stale, repository_root=self.fx.root)

    def test_runtime_rejects_mutated_implementation(self) -> None:
        (self.fx.root / self.fx.runtime_path).write_text("mutated", encoding="utf-8")
        with self.assertRaises(FormalV4AuthorityError):
            validate_formal_v4_runtime_authorization_v1(self.fx.bundle, execution_context=self.fx.context, repository_root=self.fx.root)

    def test_descriptor_must_replay_relation_authority(self) -> None:
        altered = replace(self.fx.descriptors[0], semantic_execution_hash=h("substitute"))
        with self.assertRaises(FormalV4AuthorityError):
            build_formal_v4_portfolio_authority_v1(
                method_id="V2", config_id="C", experiment_id="E", portfolio_id="P", source_commit=self.fx.commit,
                descriptors=(altered, self.fx.descriptors[1]), relation_authority_binding=self.fx.relation_binding,
                numeric_authority_binding=self.fx.numeric_binding, feature_contract_binding=self.fx.feature_binding,
                file_contract_binding=self.fx.file_binding, sampling_contract_binding=self.fx.sampling_binding,
                evaluator=self.fx.evaluator, repository_root=self.fx.root,
            )

    def test_formal_v4_authority_is_consumed_by_runtime_entrypoint(self) -> None:
        window = FormalV4ObservationWindowV1(
            opportunity_id="OP-1", relation_id="REL-1",
            feature_contract_hash=self.fx.feature_binding.content_sha256,
            file_contract_hash=self.fx.file_binding.content_sha256,
            sampling_contract_hash=self.fx.sampling_binding.content_sha256,
            event_index=100, target_response_start_index=105,
            source_pre_values=(0.0, 0.0), source_post_values=(2.0, 2.0),
            target_baseline_values=(10.0, 10.0), target_response_values=(11.0, 11.0),
            seconds_since_previous_source_trigger=None, seconds_to_nearest_other_source_trigger=None, future_window_complete=True,
        )
        trace = execute_formal_v4_rule_v1(
            self.fx.bundle, execution_context=self.fx.context, repository_root=self.fx.root, window=window
        )
        self.assertEqual(trace.final_outcome, "PASS")
        self.assertFalse(trace.alarm_emitted)

    def test_numeric_value_mutation_and_horizon_substitution_are_rejected(self) -> None:
        window = FormalV4ObservationWindowV1(
            opportunity_id="OP-1", relation_id="REL-1",
            feature_contract_hash=self.fx.feature_binding.content_sha256,
            file_contract_hash=self.fx.file_binding.content_sha256,
            sampling_contract_hash=self.fx.sampling_binding.content_sha256,
            event_index=100, target_response_start_index=106,
            source_pre_values=(0.0, 0.0), source_post_values=(2.0, 2.0),
            target_baseline_values=(10.0, 10.0), target_response_values=(11.0, 11.0),
            seconds_since_previous_source_trigger=None, seconds_to_nearest_other_source_trigger=None,
            future_window_complete=True,
        )
        with self.assertRaises(FormalV4AuthorityError):
            execute_formal_v4_rule_v1(
                self.fx.bundle, execution_context=self.fx.context, repository_root=self.fx.root, window=window
            )
        numeric_path = self.fx.root / self.fx.numeric_binding.relative_path
        document = json.loads(numeric_path.read_text(encoding="utf-8"))
        document["bindings"][0]["value"] = 100.0
        numeric_path.write_text(json.dumps(document, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        valid_window = replace(window, target_response_start_index=105)
        with self.assertRaises(FormalV4AuthorityError):
            execute_formal_v4_rule_v1(
                self.fx.bundle, execution_context=self.fx.context, repository_root=self.fx.root, window=valid_window
            )

    def test_windows_backslash_traversal_is_rejected(self) -> None:
        with self.assertRaises(FormalV4AuthorityError):
            FormalV4EvaluatorContractV1(
                evaluator_id="bad", implementation_path="src\\..\\outside.py", implementation_hash=h("x"),
                trigger_policy_hash=h("x"), response_policy_hash=h("x"), trace_contract_hash=h("x"),
            )

    def test_wrong_split_and_forged_capability_are_rejected(self) -> None:
        with self.assertRaises(FormalV4AuthorityError):
            authorize_formal_v4_runtime_v1(
                self.fx.authority, self.fx.evaluator, expected_source_commit=self.fx.commit,
                execution_context=self.fx.context, repository_root=self.fx.root, split_role="HELD_OUT",
            )
        forged = FormalV4AuthorizedRuntimeV1(self.fx.authority, self.fx.evaluator, self.fx.bundle.receipt, self.fx.context, None)
        with self.assertRaises(FormalV4AuthorityError):
            validate_formal_v4_runtime_authorization_v1(forged, execution_context=self.fx.context, repository_root=self.fx.root)


if __name__ == "__main__":
    unittest.main()
