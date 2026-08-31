from __future__ import annotations

from dataclasses import replace
from hashlib import sha1, sha256
from pathlib import Path
import unittest

from paperworks.validation_v2.explanation_fidelity_v1 import (
    EXP05_FIDELITY_CHECK_IDS,
    EXP05_RENDERER_CONTRACT_HASH,
    EXP05_RENDERER_VERSION,
    EXP05_SCIENTIFIC_RUNNER_AUTHORIZED,
    ExplanationFidelityError,
    MaterializedFormalV4TraceV1,
    hash_formal_v4_observation_window_v1,
    materialize_formal_v4_trace_v1,
    render_formal_v4_explanation_v1,
    validate_formal_v4_explanation_fidelity_v1,
    validate_materialized_formal_v4_trace_v1,
)
from paperworks.validation_v2.formal_v4_authority_v1 import (
    V4_NUMERIC_ROLES,
    FormalV4ArtifactBindingV1,
    FormalV4ExecutionContextV1,
    FormalV4PortfolioAuthorityV1,
    FormalV4RuleDescriptorV1,
    FormalV4RuntimeAuthorizationReceiptV1,
    NumericReferenceBindingV1,
    canonical_document_hash_v1,
    canonical_json_bytes_v1,
)
from paperworks.validation_v2.runtime_policy_v1 import FORMAL_V4_TRACE_CONTRACT_HASH
from paperworks.validation_v2.runtime_v1 import (
    FORMAL_V4_RUNTIME_VERSION,
    FormalV4ObservationWindowV1,
    FormalV4RuntimeTraceV1,
)


def h(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def commit(value: str) -> str:
    return sha1(value.encode("utf-8")).hexdigest()


def binding(name: str) -> FormalV4ArtifactBindingV1:
    return FormalV4ArtifactBindingV1(
        artifact_id=f"ART-{name}",
        relative_path=f"authority/{name}.json",
        content_sha256=h(name),
    )


class ExplanationFixture:
    def __init__(self) -> None:
        self.source_commit = commit("exp05-source")
        self.numeric_binding = binding("numeric")
        self.feature_binding = binding("feature")
        self.file_binding = binding("file")
        self.sampling_binding = binding("sampling")
        self.relation_binding = binding("relation")
        self.runtime_config_binding = binding("runtime-config")
        self.runtime_impl_binding = binding("runtime-implementation")
        self.numeric_refs = tuple(
            NumericReferenceBindingV1(
                numeric_role=role,
                reference_id=f"REF-{index:02d}-{role}",
                reference_hash=h(f"REF-{index:02d}-{role}"),
            )
            for index, role in enumerate(V4_NUMERIC_ROLES)
        )
        self.descriptor = FormalV4RuleDescriptorV1(
            relation_id="REL-P1-001",
            relation_binding_hash=h("relation-binding"),
            semantic_execution_hash=h("semantic-execution"),
            source="P1_SOURCE_001",
            target="P1_TARGET_001",
            source_direction="step_up",
            target_direction="increase",
            selected_horizon_seconds=5,
            numeric_reference_bindings=self.numeric_refs,
            numeric_authority_hash=self.numeric_binding.content_sha256,
        )
        self.authority = FormalV4PortfolioAuthorityV1(
            method_id="VALIDATION-V2-FORMAL-V4",
            config_id="CONFIG-V2-EXP05",
            experiment_id="EXP-05",
            portfolio_id="PORTFOLIO-V2-EXP05",
            source_commit=self.source_commit,
            descriptors=(self.descriptor,),
            relation_authority_binding=self.relation_binding,
            numeric_authority_binding=self.numeric_binding,
            feature_contract_binding=self.feature_binding,
            file_contract_binding=self.file_binding,
            sampling_contract_binding=self.sampling_binding,
            evaluator_contract_hash=h("evaluator-contract"),
            allowed_split_roles=("DEVELOPMENT_TEST1",),
        )
        self.context = FormalV4ExecutionContextV1(
            source_commit=self.source_commit,
            runtime_config_binding=self.runtime_config_binding,
            relation_authority_binding=self.relation_binding,
            numeric_authority_binding=self.numeric_binding,
            feature_contract_binding=self.feature_binding,
            file_contract_binding=self.file_binding,
            sampling_contract_binding=self.sampling_binding,
            evaluator_implementation_binding=self.runtime_impl_binding,
        )
        receipt_base = {
            "artifact_type": "validation_v2_formal_v4_runtime_authorization_v1",
            "authority_family": "FORMAL_V4",
            "authority_hash": self.authority.authority_hash,
            "authorization_id": "V2-AUTH-EXP05",
            "descriptor_set_hash": self.authority.descriptor_set_hash,
            "evaluator_contract_hash": self.authority.evaluator_contract_hash,
            "execution_context_hash": self.context.context_hash,
            "feature_contract_hash": self.feature_binding.content_sha256,
            "file_contract_hash": self.file_binding.content_sha256,
            "heldout_authorized": False,
            "label_access_before_prediction_freeze": False,
            "numeric_authority_hash": self.numeric_binding.content_sha256,
            "portfolio_id": self.authority.portfolio_id,
            "runtime_config_hash": self.context.runtime_config_hash,
            "sampling_contract_hash": self.sampling_binding.content_sha256,
            "schema_version": "1.0.0",
            "split_role": "DEVELOPMENT_TEST1",
        }
        self.receipt = FormalV4RuntimeAuthorizationReceiptV1(
            authorization_id=receipt_base["authorization_id"],
            authority_hash=receipt_base["authority_hash"],
            portfolio_id=receipt_base["portfolio_id"],
            descriptor_set_hash=receipt_base["descriptor_set_hash"],
            numeric_authority_hash=receipt_base["numeric_authority_hash"],
            evaluator_contract_hash=receipt_base["evaluator_contract_hash"],
            runtime_config_hash=receipt_base["runtime_config_hash"],
            feature_contract_hash=receipt_base["feature_contract_hash"],
            file_contract_hash=receipt_base["file_contract_hash"],
            sampling_contract_hash=receipt_base["sampling_contract_hash"],
            execution_context_hash=receipt_base["execution_context_hash"],
            split_role=receipt_base["split_role"],
            authorization_hash=canonical_document_hash_v1(receipt_base),
        )
        self.window = FormalV4ObservationWindowV1(
            opportunity_id="OP-EXP05-001",
            relation_id=self.descriptor.relation_id,
            feature_contract_hash=self.feature_binding.content_sha256,
            file_contract_hash=self.file_binding.content_sha256,
            sampling_contract_hash=self.sampling_binding.content_sha256,
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

    def runtime_trace(
        self,
        outcome: str = "PASS",
        reason: str = "expected_response_observed",
        alarm: bool = False,
    ) -> FormalV4RuntimeTraceV1:
        payload = {
            "alarm_emitted": alarm,
            "authorization_hash": self.receipt.authorization_hash,
            "descriptor_hash": self.descriptor.descriptor_hash,
            "execution_context_hash": self.context.context_hash,
            "final_outcome": outcome,
            "opportunity_id": self.window.opportunity_id,
            "reason": reason,
            "relation_id": self.descriptor.relation_id,
            "runtime_version": FORMAL_V4_RUNTIME_VERSION,
        }
        return FormalV4RuntimeTraceV1(
            opportunity_id=self.window.opportunity_id,
            relation_id=self.descriptor.relation_id,
            descriptor_hash=self.descriptor.descriptor_hash,
            authorization_hash=self.receipt.authorization_hash,
            execution_context_hash=self.context.context_hash,
            final_outcome=outcome,
            reason=reason,
            alarm_emitted=alarm,
            trace_hash=canonical_document_hash_v1(payload),
        )

    def materialized(
        self,
        outcome: str = "PASS",
        reason: str = "expected_response_observed",
        alarm: bool = False,
    ) -> MaterializedFormalV4TraceV1:
        return materialize_formal_v4_trace_v1(
            runtime_trace=self.runtime_trace(outcome, reason, alarm),
            descriptor=self.descriptor,
            authority=self.authority,
            receipt=self.receipt,
            execution_context=self.context,
            observation_window=self.window,
        )


def rehash_explanation(explanation, **changes):
    provisional = replace(explanation, **changes)
    return replace(provisional, artifact_hash=provisional.expected_artifact_hash)


def rehash_receipt(receipt, **changes):
    provisional = replace(receipt, **changes, authorization_hash=h("temporary-authorization"))
    payload = provisional.to_dict()
    payload.pop("authorization_hash")
    return replace(provisional, authorization_hash=canonical_document_hash_v1(payload))


def rebind_runtime_trace(trace, *, receipt, context):
    provisional = replace(
        trace,
        authorization_hash=receipt.authorization_hash,
        execution_context_hash=context.context_hash,
        trace_hash=h("temporary-runtime-trace"),
    )
    payload = {
        "alarm_emitted": provisional.alarm_emitted,
        "authorization_hash": provisional.authorization_hash,
        "descriptor_hash": provisional.descriptor_hash,
        "execution_context_hash": provisional.execution_context_hash,
        "final_outcome": provisional.final_outcome,
        "opportunity_id": provisional.opportunity_id,
        "reason": provisional.reason,
        "relation_id": provisional.relation_id,
        "runtime_version": FORMAL_V4_RUNTIME_VERSION,
    }
    return replace(provisional, trace_hash=canonical_document_hash_v1(payload))


class ExplanationFidelityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = ExplanationFixture()

    def test_contract_is_formal_v4_specific_and_not_a_scientific_runner(self) -> None:
        trace = self.fx.materialized()
        self.assertEqual(trace.runtime_version, FORMAL_V4_RUNTIME_VERSION)
        self.assertEqual(trace.trace_contract_hash, FORMAL_V4_TRACE_CONTRACT_HASH)
        self.assertFalse(trace.scientific_runner_authorized)
        self.assertFalse(EXP05_SCIENTIFIC_RUNNER_AUTHORIZED)
        self.assertNotIn("canonical_runtime_trace", trace.to_dict())
        self.assertNotIn("RuntimeTraceV1", trace.to_dict().values())

    def test_materialized_trace_is_public_safe_and_exactly_bound(self) -> None:
        trace = self.fx.materialized()
        validate_materialized_formal_v4_trace_v1(trace)
        document = trace.to_dict()
        self.assertFalse(document["raw_numeric_values_embedded"])
        self.assertFalse(document["raw_observations_embedded"])
        self.assertFalse(document["labels_accessed"])
        self.assertEqual(document["source"], self.fx.descriptor.source)
        self.assertEqual(document["target"], self.fx.descriptor.target)
        self.assertEqual(len(document["ordered_numeric_reference_bindings"]), 10)
        for forbidden in ("source_pre_values", "source_post_values", "target_baseline_values", "target_response_values"):
            self.assertNotIn(forbidden, document)

    def test_observation_hash_binds_exact_values_without_materializing_them(self) -> None:
        first = hash_formal_v4_observation_window_v1(self.fx.window)
        changed = replace(self.fx.window, target_response_values=(12.0, 12.0))
        second = hash_formal_v4_observation_window_v1(changed)
        self.assertNotEqual(first, second)
        self.assertEqual(self.fx.materialized().observation_window_hash, first)

    def test_all_closed_outcome_reason_templates_pass(self) -> None:
        cases = (
            ("PASS", "expected_response_observed", False),
            ("FAIL", "expected_response_not_observed", True),
            ("ABSTAIN", "incomplete_source_window", False),
            ("ABSTAIN", "source_not_triggered", False),
            ("ABSTAIN", "incomplete_target_response_window", False),
        )
        for outcome, reason, alarm in cases:
            with self.subTest(outcome=outcome, reason=reason):
                trace = self.fx.materialized(outcome, reason, alarm)
                explanation = render_formal_v4_explanation_v1(trace)
                result = validate_formal_v4_explanation_fidelity_v1(trace, explanation)
                self.assertTrue(result.all_checks_passed)
                self.assertEqual(tuple(item.check_id for item in result.checks), EXP05_FIDELITY_CHECK_IDS)
                if outcome == "ABSTAIN":
                    self.assertNotIn("응답을 확인했습니다", explanation.natural_language_text)
                if reason in {"incomplete_source_window", "source_not_triggered"}:
                    self.assertIn("target response는 평가하지 않았습니다", explanation.natural_language_text)

    def test_renderer_is_byte_deterministic_and_llm_free(self) -> None:
        trace = self.fx.materialized()
        first = render_formal_v4_explanation_v1(trace)
        second = render_formal_v4_explanation_v1(trace)
        self.assertEqual(canonical_json_bytes_v1(first.to_dict()), canonical_json_bytes_v1(second.to_dict()))
        self.assertEqual(first.artifact_hash, second.artifact_hash)
        self.assertEqual(first.renderer_version, EXP05_RENDERER_VERSION)
        self.assertEqual(first.renderer_contract_hash, EXP05_RENDERER_CONTRACT_HASH)
        self.assertFalse(first.human_usefulness_evaluated)

    def test_runtime_trace_hash_and_outcome_mutations_fail_closed(self) -> None:
        wrong_hash = replace(self.fx.runtime_trace(), trace_hash=h("wrong"))
        with self.assertRaises(ExplanationFidelityError):
            materialize_formal_v4_trace_v1(
                runtime_trace=wrong_hash,
                descriptor=self.fx.descriptor,
                authority=self.fx.authority,
                receipt=self.fx.receipt,
                execution_context=self.fx.context,
                observation_window=self.fx.window,
            )
        invalid = self.fx.runtime_trace("PASS", "expected_response_not_observed", False)
        with self.assertRaises(ExplanationFidelityError):
            materialize_formal_v4_trace_v1(
                runtime_trace=invalid,
                descriptor=self.fx.descriptor,
                authority=self.fx.authority,
                receipt=self.fx.receipt,
                execution_context=self.fx.context,
                observation_window=self.fx.window,
            )

    def test_stale_portfolio_authorization_and_context_fail_closed(self) -> None:
        wrong_authority = replace(self.fx.authority, portfolio_id="STALE-PORTFOLIO")
        with self.assertRaises(ExplanationFidelityError):
            materialize_formal_v4_trace_v1(
                runtime_trace=self.fx.runtime_trace(), descriptor=self.fx.descriptor,
                authority=wrong_authority, receipt=self.fx.receipt,
                execution_context=self.fx.context, observation_window=self.fx.window,
            )
        stale_receipt = replace(self.fx.receipt, authorization_hash=h("stale"))
        with self.assertRaises(ExplanationFidelityError):
            materialize_formal_v4_trace_v1(
                runtime_trace=self.fx.runtime_trace(), descriptor=self.fx.descriptor,
                authority=self.fx.authority, receipt=stale_receipt,
                execution_context=self.fx.context, observation_window=self.fx.window,
            )
        stale_context = replace(self.fx.context, source_commit=commit("stale"))
        with self.assertRaises(ExplanationFidelityError):
            materialize_formal_v4_trace_v1(
                runtime_trace=self.fx.runtime_trace(), descriptor=self.fx.descriptor,
                authority=self.fx.authority, receipt=self.fx.receipt,
                execution_context=stale_context, observation_window=self.fx.window,
            )

    def test_runtime_config_and_cross_plane_authority_mismatches_fail_closed(self) -> None:
        runtime_config_mismatch = rehash_receipt(
            self.fx.receipt, runtime_config_hash=h("different-runtime-config")
        )
        rebound_trace = rebind_runtime_trace(
            self.fx.runtime_trace(), receipt=runtime_config_mismatch, context=self.fx.context
        )
        with self.assertRaises(ExplanationFidelityError):
            materialize_formal_v4_trace_v1(
                runtime_trace=rebound_trace, descriptor=self.fx.descriptor,
                authority=self.fx.authority, receipt=runtime_config_mismatch,
                execution_context=self.fx.context, observation_window=self.fx.window,
            )

        different_feature = binding("different-feature")
        changed_context = replace(self.fx.context, feature_contract_binding=different_feature)
        changed_receipt = rehash_receipt(
            self.fx.receipt,
            execution_context_hash=changed_context.context_hash,
            feature_contract_hash=different_feature.content_sha256,
        )
        changed_window = replace(
            self.fx.window, feature_contract_hash=different_feature.content_sha256
        )
        changed_trace = rebind_runtime_trace(
            self.fx.runtime_trace(), receipt=changed_receipt, context=changed_context
        )
        with self.assertRaises(ExplanationFidelityError):
            materialize_formal_v4_trace_v1(
                runtime_trace=changed_trace, descriptor=self.fx.descriptor,
                authority=self.fx.authority, receipt=changed_receipt,
                execution_context=changed_context, observation_window=changed_window,
            )

    def test_descriptor_numeric_and_horizon_substitutions_fail_closed(self) -> None:
        wrong_descriptor = replace(self.fx.descriptor, source="OTHER_SOURCE")
        with self.assertRaises(ExplanationFidelityError):
            materialize_formal_v4_trace_v1(
                runtime_trace=self.fx.runtime_trace(), descriptor=wrong_descriptor,
                authority=self.fx.authority, receipt=self.fx.receipt,
                execution_context=self.fx.context, observation_window=self.fx.window,
            )
        wrong_window = replace(self.fx.window, target_response_start_index=106)
        with self.assertRaises(ExplanationFidelityError):
            materialize_formal_v4_trace_v1(
                runtime_trace=self.fx.runtime_trace(), descriptor=self.fx.descriptor,
                authority=self.fx.authority, receipt=self.fx.receipt,
                execution_context=self.fx.context, observation_window=wrong_window,
            )
        with self.assertRaises(ExplanationFidelityError):
            replace(self.fx.materialized(), ordered_numeric_reference_bindings=tuple(reversed(self.fx.numeric_refs)))

    def test_materialized_trace_hash_mutation_fails_closed(self) -> None:
        with self.assertRaises(ExplanationFidelityError):
            validate_materialized_formal_v4_trace_v1(replace(self.fx.materialized(), self_hash=h("tampered")))

    def test_new_variable_number_and_causal_text_are_detected(self) -> None:
        trace = self.fx.materialized()
        explanation = render_formal_v4_explanation_v1(trace)
        mutations = (
            rehash_explanation(explanation, natural_language_text=explanation.natural_language_text + " OTHER_SENSOR도 확인했습니다."),
            rehash_explanation(explanation, natural_language_text=explanation.natural_language_text + " 추가 기준은 99입니다."),
            rehash_explanation(explanation, natural_language_text=explanation.natural_language_text + " 이것이 root cause입니다.", causal_claim_made=True, root_cause_claim_made=True),
        )
        expected_failed_checks = ("NO_NEW_VARIABLE", "NO_NEW_NUMBER", "NO_CAUSAL_CLAIM")
        for mutation, expected_check in zip(mutations, expected_failed_checks):
            with self.subTest(check=expected_check):
                result = validate_formal_v4_explanation_fidelity_v1(trace, mutation)
                self.assertFalse(result.all_checks_passed)
                failed = {item.check_id for item in result.checks if not item.passed}
                self.assertIn(expected_check, failed)
                self.assertIn("DETERMINISTIC_REPLAY", failed)

    def test_structured_field_and_numeric_provenance_mutations_fail(self) -> None:
        trace = self.fx.materialized()
        explanation = render_formal_v4_explanation_v1(trace)
        cases = (
            (rehash_explanation(explanation, source="OTHER_SOURCE"), "SOURCE_MATCH"),
            (rehash_explanation(explanation, target="OTHER_TARGET"), "TARGET_MATCH"),
            (rehash_explanation(explanation, source_direction="step_down"), "SOURCE_DIRECTION_MATCH"),
            (rehash_explanation(explanation, target_direction="decrease"), "TARGET_DIRECTION_MATCH"),
            (rehash_explanation(explanation, selected_horizon_seconds=10), "HORIZON_MATCH"),
            (rehash_explanation(explanation, numeric_authority_hash=h("wrong-numeric")), "NUMERIC_PROVENANCE_MATCH"),
            (rehash_explanation(explanation, final_outcome="FAIL", reason="expected_response_not_observed", alarm_emitted=True), "OUTCOME_MATCH"),
        )
        for mutation, expected_check in cases:
            with self.subTest(check=expected_check):
                result = validate_formal_v4_explanation_fidelity_v1(trace, mutation)
                failed = {item.check_id for item in result.checks if not item.passed}
                self.assertIn(expected_check, failed)

    def test_renderer_contract_and_artifact_mutation_fail_deterministic_replay(self) -> None:
        trace = self.fx.materialized()
        explanation = render_formal_v4_explanation_v1(trace)
        mutations = (
            replace(explanation, artifact_hash=h("tampered")),
            rehash_explanation(explanation, renderer_version="UNKNOWN-RENDERER"),
            rehash_explanation(explanation, renderer_contract_hash=h("wrong-contract")),
        )
        for mutation in mutations:
            result = validate_formal_v4_explanation_fidelity_v1(trace, mutation)
            failed = {item.check_id for item in result.checks if not item.passed}
            self.assertIn("DETERMINISTIC_REPLAY", failed)

    def test_module_has_no_runtime_provider_random_time_or_dynamic_execution_dependency(self) -> None:
        source = (Path(__file__).parents[1] / "src/paperworks/validation_v2/explanation_fidelity_v1.py").read_text(encoding="utf-8")
        import_lines = [line.strip() for line in source.splitlines() if line.startswith("import ") or line.startswith("from ")]
        joined = "\n".join(import_lines)
        for forbidden in ("openai", "requests", "httpx", "random", "datetime", "subprocess"):
            self.assertNotIn(forbidden, joined)
        for forbidden_call in ("eval(", "exec(", "compile("):
            self.assertNotIn(forbidden_call, source)


if __name__ == "__main__":
    unittest.main()
