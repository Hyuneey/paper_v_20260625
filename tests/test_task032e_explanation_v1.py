from __future__ import annotations

import dataclasses
import json
import unittest
from pathlib import Path

from paperworks.contracts import (
    ExplanationV1Error,
    canonical_explanation_record_sha256,
    execute_delayed_response_rule,
    explanation_record_to_dict,
    load_runtime_window,
    parse_explanation_record,
    render_delayed_response_explanation,
    runtime_trace_to_dict,
    serialize_explanation_record,
    verify_contract_artifact_hash,
)
from tests.test_task032e_runtime_authority import authorized_bundle


ROOT = Path(__file__).resolve().parents[1]


def rendered(name: str):
    bundle = authorized_bundle()
    window = load_runtime_window(ROOT / f"fixtures/task032e/{name}.json")
    execution = execute_delayed_response_rule(bundle, window)
    return bundle, window, execution, render_delayed_response_explanation(bundle, execution, window)


class Task032EExplanationV1Tests(unittest.TestCase):
    def test_evaluated_traces_render_structurally_valid_explanations(self) -> None:
        expected = {
            "window_response_present": "The expected delayed response was observed.",
            "window_response_missing": "The expected delayed response was not observed.",
            "window_no_trigger": "The trigger condition was not observed.",
        }
        for name, observed in expected.items():
            _, _, _, record = rendered(name)
            self.assertEqual(record.observed_behavior, observed)
            self.assertEqual(parse_explanation_record(explanation_record_to_dict(record)), record)
            self.assertEqual(canonical_explanation_record_sha256(record), record.artifact_hash)
            self.assertEqual(verify_contract_artifact_hash(explanation_record_to_dict(record)), record.artifact_hash)

    def test_abstention_explanation_has_no_anomaly_label(self) -> None:
        _, _, _, record = rendered("window_multiple_triggers")
        self.assertIn("abstained", record.observed_behavior)
        self.assertTrue(record.rule_result.available)
        self.assertTrue(record.rule_result.abstained)
        self.assertIsNone(record.rule_result.binary_label)
        self.assertIsNone(record.rule_result.score)

    def test_references_are_exact_and_detector_fusion_unavailable(self) -> None:
        bundle, window, execution, record = rendered("window_response_missing")
        rule = bundle.accepted_rule
        self.assertEqual(record.execution_id, execution.trace.execution_id)
        self.assertEqual(record.rule_hash, rule.verified_rule_hash)
        self.assertEqual(record.verifier_result_ref, bundle.verifier_result.verifier_result_id)
        self.assertEqual(record.time_interval.input_window_id, window.input_window_id)
        self.assertEqual(record.parameter_refs, rule.parameter_refs)
        self.assertEqual(record.evidence_refs, rule.evidence_refs)
        self.assertEqual(record.normal_reference_refs, rule.normal_reference_refs)
        self.assertEqual(record.graph_edge_refs, rule.graph_edge_refs)
        self.assertFalse(record.detector_result.available)
        self.assertFalse(record.fusion_result.available)

    def test_observed_lag_and_unsupported_claims_are_absent(self) -> None:
        _, _, _, record = rendered("window_response_present")
        self.assertIsNone(record.lag.observed)
        self.assertFalse(record.causal_claim_made)
        self.assertFalse(record.root_cause_claim_made)
        text = record.natural_language_text.lower()
        self.assertNotIn("root cause", text)
        self.assertNotIn("causes", text)

    def test_rendering_and_serialization_are_deterministic(self) -> None:
        first = rendered("window_response_present")[3]
        second = rendered("window_response_present")[3]
        self.assertEqual(first, second)
        self.assertEqual(serialize_explanation_record(first), serialize_explanation_record(second))

    def test_invalid_or_mismatched_trace_cannot_render(self) -> None:
        bundle, window, execution, _ = rendered("window_response_present")
        bad_trace = dataclasses.replace(execution.trace, rule_hash="f" * 64)
        bad_execution = dataclasses.replace(execution, trace=bad_trace)
        with self.assertRaises(ExplanationV1Error):
            render_delayed_response_explanation(bundle, bad_execution, window)
        other = load_runtime_window(ROOT / "fixtures/task032e/window_response_missing.json")
        with self.assertRaises(ExplanationV1Error) as caught:
            render_delayed_response_explanation(bundle, execution, other)
        self.assertEqual(caught.exception.issue_code, "EXPLANATION_TRACE_BINDING_MISMATCH")

    def test_rendering_revalidates_authorization_and_execution_id(self) -> None:
        bundle, window, execution, expected = rendered("window_response_present")
        self.assertEqual(render_delayed_response_explanation(bundle, execution, window), expected)

        changed_receipt = dataclasses.replace(bundle.receipt, graph_hash="f" * 64)
        with self.assertRaises(ExplanationV1Error) as changed_receipt_error:
            render_delayed_response_explanation(
                dataclasses.replace(bundle, receipt=changed_receipt), execution, window
            )
        self.assertEqual(
            changed_receipt_error.exception.issue_code,
            "EXPLANATION_AUTHORIZATION_INVALID",
        )

        changed_artifacts = dataclasses.replace(
            bundle.artifacts,
            graph=dataclasses.replace(bundle.artifacts.graph, artifact_hash="f" * 64),
        )
        with self.assertRaises(ExplanationV1Error) as retained_capability_error:
            render_delayed_response_explanation(
                dataclasses.replace(bundle, artifacts=changed_artifacts), execution, window
            )
        self.assertEqual(
            retained_capability_error.exception.issue_code,
            "EXPLANATION_AUTHORIZATION_INVALID",
        )

        with self.assertRaises(ExplanationV1Error) as execution_id_error:
            render_delayed_response_explanation(
                bundle,
                dataclasses.replace(execution, authorization_id="AUTH-AAAAAAAAAAAAAAAAAAAA"),
                window,
            )
        self.assertEqual(
            execution_id_error.exception.issue_code,
            "EXPLANATION_AUTHORIZATION_ID_MISMATCH",
        )

    def test_tracked_explanation_fixtures_match_rendering(self) -> None:
        mapping = {
            "response_present": "window_response_present",
            "response_missing": "window_response_missing",
            "no_trigger": "window_no_trigger",
            "abstained": "window_multiple_triggers",
        }
        for output_name, input_name in mapping.items():
            expected = json.loads((ROOT / f"fixtures/task032e/explanation_{output_name}.json").read_text(encoding="utf-8"))
            record = rendered(input_name)[3]
            self.assertEqual(explanation_record_to_dict(record), expected)
            self.assertEqual(parse_explanation_record(expected), record)


if __name__ == "__main__":
    unittest.main()
