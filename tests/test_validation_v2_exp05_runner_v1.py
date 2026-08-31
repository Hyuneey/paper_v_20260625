from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import inspect
import unittest
from unittest.mock import patch

from paperworks.validation_v2 import exp05_runner_v1 as runner
from paperworks.validation_v2.formal_v4_authority_v1 import canonical_document_hash_v1
from paperworks.validation_v2.runtime_v1 import FormalV4ObservationWindowV1
from paperworks.validation_v2.schema_registry_v1 import validate_validation_v2_document_v1
from tests.test_validation_v2_formal_v4_authority_v1 import V2Fixture


def h(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


class Exp05RunnerV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = V2Fixture()
        descriptor = self.fx.descriptors[0]
        self.window = FormalV4ObservationWindowV1(
            opportunity_id="OP-EXP05-SYNTHETIC-1",
            relation_id=descriptor.relation_id,
            feature_contract_hash=self.fx.feature_binding.content_sha256,
            file_contract_hash=self.fx.file_binding.content_sha256,
            sampling_contract_hash=self.fx.sampling_binding.content_sha256,
            event_index=100,
            target_response_start_index=105,
            source_pre_values=(0.0, 0.0),
            source_post_values=(2.0, 2.0),
            target_baseline_values=(10.0, 10.0),
            target_response_values=(11.0, 11.0),
            seconds_since_previous_source_trigger=None,
            seconds_to_nearest_other_source_trigger=None,
            future_window_complete=True,
        )
        self.authorization = runner.authorize_exp05_execution_v1(
            execution_scope="SYNTHETIC_CONFORMANCE",
            preregistration_hash=h("exp05-preregistration"),
            source_commit=self.fx.commit,
            bundle=self.fx.bundle,
        )

    def tearDown(self) -> None:
        self.fx.close()

    def test_single_entrypoint_executes_runtime_once_and_returns_complete_unit(self) -> None:
        original = runner.execute_formal_v4_rule_v1
        with patch.object(runner, "execute_formal_v4_rule_v1", wraps=original) as execute:
            unit = runner.execute_and_materialize_formal_v4_rule_v1(
                self.fx.bundle,
                authorization=self.authorization,
                execution_context=self.fx.context,
                repository_root=self.fx.root,
                window=self.window,
            )
        self.assertEqual(execute.call_count, 1)
        self.assertTrue(unit.fidelity_result.all_checks_passed)
        self.assertTrue(unit.materialization_receipt.same_call_path)
        self.assertFalse(unit.materialization_receipt.labels_accessed)
        self.assertEqual(unit.materialization_receipt.provider_calls, 0)
        self.assertEqual(unit.materialization_receipt.llm_calls, 0)
        self.assertEqual(
            runner.validate_evaluated_formal_v4_explanation_unit_v1(unit), unit.unit_hash,
        )
        for filename, document in (
            ("exp05_run_authorization_v1.schema.json", unit.run_authorization.to_dict()),
            ("exp05_materialization_receipt_v1.schema.json", unit.materialization_receipt.to_dict()),
            ("formal_v4_materialized_trace_v1.schema.json", unit.materialized_trace.to_dict()),
            ("formal_v4_explanation_record_v1.schema.json", unit.explanation.to_dict()),
            ("formal_v4_explanation_fidelity_result_v1.schema.json", unit.fidelity_result.to_dict()),
            ("exp05_evaluated_unit_v1.schema.json", unit.to_dict()),
        ):
            validate_validation_v2_document_v1(filename, document)

    def test_entrypoint_does_not_accept_precomputed_trace(self) -> None:
        parameters = inspect.signature(runner.execute_and_materialize_formal_v4_rule_v1).parameters
        self.assertNotIn("runtime_trace", parameters)
        self.assertNotIn("explanation", parameters)

    def test_forged_authorization_and_wrong_context_fail_before_runtime(self) -> None:
        stale = replace(self.authorization, preregistration_hash=h("stale"))
        with patch.object(runner, "execute_formal_v4_rule_v1") as execute:
            with self.assertRaises(runner.Exp05RunnerError):
                runner.execute_and_materialize_formal_v4_rule_v1(
                    self.fx.bundle,
                    authorization=stale,
                    execution_context=self.fx.context,
                    repository_root=self.fx.root,
                    window=self.window,
                )
            execute.assert_not_called()
        wrong_context = replace(self.fx.context, source_commit="0" * 40)
        with patch.object(runner, "execute_formal_v4_rule_v1") as execute:
            with self.assertRaises(runner.Exp05RunnerError):
                runner.execute_and_materialize_formal_v4_rule_v1(
                    self.fx.bundle,
                    authorization=self.authorization,
                    execution_context=wrong_context,
                    repository_root=self.fx.root,
                    window=self.window,
                )
            execute.assert_not_called()

    def test_scientific_scope_requires_both_freeze_receipts(self) -> None:
        with self.assertRaisesRegex(runner.Exp05RunnerError, "EXP05_COMMIT_A_RECEIPT_REQUIRED"):
            runner.authorize_exp05_execution_v1(
                execution_scope="SCIENTIFIC_V2",
                preregistration_hash=h("exp05-preregistration"),
                source_commit=self.fx.commit,
                bundle=self.fx.bundle,
            )
        authorization = runner.authorize_exp05_execution_v1(
            execution_scope="SCIENTIFIC_V2",
            preregistration_hash=h("exp05-preregistration"),
            source_commit=self.fx.commit,
            bundle=self.fx.bundle,
            stage2_commit_a_receipt_hash=h("commit-a"),
            normal_selection_commit_b_receipt_hash=h("commit-b"),
            test1_features_authorized=True,
        )
        self.assertTrue(authorization.test1_features_authorized)

    def test_versioned_schemas_enforce_scope_authority_coupling(self) -> None:
        synthetic = self.authorization.to_dict()
        synthetic["test1_features_authorized"] = True
        with self.assertRaisesRegex(Exception, "oneOf match count differs"):
            validate_validation_v2_document_v1(
                "exp05_run_authorization_v1.schema.json", synthetic,
            )
        unit = runner.execute_and_materialize_formal_v4_rule_v1(
            self.fx.bundle, authorization=self.authorization,
            execution_context=self.fx.context, repository_root=self.fx.root,
            window=self.window,
        )
        receipt = unit.materialization_receipt.to_dict()
        receipt["stage2_commit_a_receipt_hash"] = h("forbidden-synthetic-receipt")
        with self.assertRaisesRegex(Exception, "oneOf match count differs"):
            validate_validation_v2_document_v1(
                "exp05_materialization_receipt_v1.schema.json", receipt,
            )

    def test_scientific_and_synthetic_scope_cannot_be_substituted(self) -> None:
        synthetic = runner.execute_and_materialize_formal_v4_rule_v1(
            self.fx.bundle, authorization=self.authorization,
            execution_context=self.fx.context, repository_root=self.fx.root,
            window=self.window,
        )
        scientific_authorization = runner.authorize_exp05_execution_v1(
            execution_scope="SCIENTIFIC_V2",
            preregistration_hash=self.authorization.preregistration_hash,
            source_commit=self.fx.commit,
            bundle=self.fx.bundle,
            stage2_commit_a_receipt_hash=h("commit-a"),
            normal_selection_commit_b_receipt_hash=h("commit-b"),
            test1_features_authorized=True,
        )
        forged = replace(
            synthetic, run_authorization=scientific_authorization, unit_hash="0" * 64,
        )
        forged = replace(forged, unit_hash=canonical_document_hash_v1(forged.payload()))
        with self.assertRaisesRegex(runner.Exp05RunnerError, "RUN_AUTHORIZATION_BINDING_MISMATCH"):
            runner.validate_evaluated_formal_v4_explanation_unit_v1(forged)

        scientific = runner.execute_and_materialize_formal_v4_rule_v1(
            self.fx.bundle, authorization=scientific_authorization,
            execution_context=self.fx.context, repository_root=self.fx.root,
            window=self.window,
        )
        self.assertTrue(scientific.materialized_trace.scientific_runner_authorized)
        self.assertEqual("SCIENTIFIC_V2", scientific.materialization_receipt.execution_scope)

    def test_mutated_unit_or_cross_trace_substitution_is_rejected(self) -> None:
        first = runner.execute_and_materialize_formal_v4_rule_v1(
            self.fx.bundle,
            authorization=self.authorization,
            execution_context=self.fx.context,
            repository_root=self.fx.root,
            window=self.window,
        )
        with self.assertRaises(runner.Exp05RunnerError):
            runner.validate_evaluated_formal_v4_explanation_unit_v1(
                replace(first, runtime_trace_hash=h("foreign"))
            )

    def test_rehashed_receipt_safety_and_authority_mutations_fail_closed(self) -> None:
        unit = runner.execute_and_materialize_formal_v4_rule_v1(
            self.fx.bundle,
            authorization=self.authorization,
            execution_context=self.fx.context,
            repository_root=self.fx.root,
            window=self.window,
        )
        for field, value in (
            ("same_call_path", False),
            ("labels_accessed", True),
            ("heldout_accessed", True),
            ("provider_calls", 1),
            ("llm_calls", 1),
            ("authorization_hash", h("wrong-authorization")),
            ("descriptor_set_hash", h("wrong-descriptor-set")),
            ("renderer_contract_hash", h("wrong-renderer")),
        ):
            changed = replace(unit.materialization_receipt, **{field: value}, receipt_hash="0" * 64)
            changed = replace(changed, receipt_hash=canonical_document_hash_v1(changed.payload()))
            forged = replace(unit, materialization_receipt=changed, unit_hash="0" * 64)
            forged = replace(forged, unit_hash=canonical_document_hash_v1(forged.payload()))
            with self.subTest(field=field), self.assertRaisesRegex(
                runner.Exp05RunnerError, "BINDING_MISMATCH"
            ):
                runner.validate_evaluated_formal_v4_explanation_unit_v1(forged)

    def test_negative_structural_fidelity_is_returned_as_durable_evidence(self) -> None:
        original_renderer = runner.render_formal_v4_explanation_v1

        def altered_renderer(trace):
            original = original_renderer(trace)
            changed = replace(original, source="OTHER-SOURCE", artifact_hash="0" * 64)
            return replace(changed, artifact_hash=changed.expected_artifact_hash)

        with patch.object(runner, "render_formal_v4_explanation_v1", side_effect=altered_renderer):
            unit = runner.execute_and_materialize_formal_v4_rule_v1(
                self.fx.bundle, authorization=self.authorization,
                execution_context=self.fx.context, repository_root=self.fx.root,
                window=self.window,
            )
            replayed_hash = runner.validate_evaluated_formal_v4_explanation_unit_v1(unit)
        self.assertFalse(unit.fidelity_result.all_checks_passed)
        self.assertTrue(any(not item.passed for item in unit.fidelity_result.checks))
        self.assertEqual(unit.unit_hash, replayed_hash)


if __name__ == "__main__":
    unittest.main()
