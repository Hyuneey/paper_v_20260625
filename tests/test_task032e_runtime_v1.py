from __future__ import annotations

import copy
import dataclasses
import json
import math
import unittest
from pathlib import Path

from paperworks.contracts import (
    DelayedResponseArtifactCollectionV1,
    DelayedResponseVerifierPolicyV1,
    RuntimeV1Error,
    RuntimeWindowModelError,
    authorize_delayed_response_runtime,
    calibration_parameter_to_dict,
    canonical_runtime_trace_sha256,
    canonical_runtime_window_sha256,
    execute_delayed_response_rule,
    load_runtime_window,
    parse_calibration_parameter,
    parse_runtime_trace,
    parse_runtime_window,
    runtime_trace_to_dict,
    runtime_window_to_dict,
    verify_contract_artifact_hash,
    verify_delayed_response_rule,
    with_computed_artifact_hash,
)
from tests.test_task032d_authority_hash import aligned_bundle
from tests.test_task032e_runtime_authority import authorized_bundle


ROOT = Path(__file__).resolve().parents[1]


def window(name: str):
    return load_runtime_window(ROOT / f"fixtures/task032e/{name}.json")


class Task032ERuntimeV1Tests(unittest.TestCase):
    def test_valid_windows_parse_and_are_immutable(self) -> None:
        for name in ("window_response_present", "window_response_missing", "window_no_trigger", "window_multiple_triggers", "window_regime_mismatch", "window_missing_value"):
            item = window(name)
            self.assertEqual(canonical_runtime_window_sha256(item), canonical_runtime_window_sha256(runtime_window_to_dict(item)))
            with self.assertRaises(dataclasses.FrozenInstanceError):
                item.subsystem = "changed"  # type: ignore[misc]

    def test_window_validation_rejects_shape_binary_nonfinite_sampling_and_offsets(self) -> None:
        base = runtime_window_to_dict(window("window_response_present"))
        changes = (
            ("RUNTIME_WINDOW_LENGTH", lambda doc: doc["target_values"].pop()),
            ("RUNTIME_WINDOW_SOURCE_BINARY", lambda doc: doc["source_values"].__setitem__(0, 2)),
            ("RUNTIME_WINDOW_TARGET_FINITE", lambda doc: doc["target_values"].__setitem__(0, math.nan)),
            ("RUNTIME_WINDOW_TARGET_FINITE", lambda doc: doc["target_values"].__setitem__(0, math.inf)),
            ("RUNTIME_WINDOW_SAMPLING", lambda doc: doc["sampling_interval"].update(value=0)),
            ("RUNTIME_WINDOW_OFFSET_LENGTH", lambda doc: doc.update(end_offset=9)),
            ("RUNTIME_WINDOW_OFFSET_TYPE", lambda doc: doc.update(start_offset=0.5)),
        )
        for code, mutate in changes:
            document = copy.deepcopy(base)
            mutate(document)
            with self.assertRaises(RuntimeWindowModelError) as caught:
                parse_runtime_window(document)
            self.assertEqual(caught.exception.issue_code, code)

    def test_bare_rule_and_verifier_result_cannot_execute(self) -> None:
        bundle = authorized_bundle()
        item = window("window_response_present")
        for bare in (bundle.accepted_rule, bundle.verifier_result):
            with self.assertRaises(RuntimeV1Error) as caught:
                execute_delayed_response_rule(bare, item)  # type: ignore[arg-type]
            self.assertEqual(caught.exception.issue_code, "RUNTIME_NOT_AUTHORIZED")

    def test_response_present_missing_and_no_trigger_results(self) -> None:
        bundle = authorized_bundle()
        present = execute_delayed_response_rule(bundle, window("window_response_present"))
        self.assertEqual((present.trace.status, present.trace.trigger_satisfied, present.trace.expected_effect_satisfied, present.trace.violation_detected, present.trace.violation_score), ("evaluated", True, True, False, 0.0))
        self.assertEqual(present.response_index, 4)
        missing = execute_delayed_response_rule(bundle, window("window_response_missing"))
        self.assertEqual((missing.trace.status, missing.trace.expected_effect_satisfied, missing.trace.violation_detected, missing.trace.violation_score), ("evaluated", False, True, 1.0))
        no_trigger = execute_delayed_response_rule(bundle, window("window_no_trigger"))
        self.assertEqual((no_trigger.trace.trigger_satisfied, no_trigger.trace.expected_effect_satisfied, no_trigger.trace.violation_detected), (False, None, False))

    def test_multiple_regime_missing_first_and_coverage_abstain(self) -> None:
        bundle = authorized_bundle()
        expected = {
            "window_multiple_triggers": "multiple_triggers",
            "window_regime_mismatch": "regime_mismatch",
            "window_missing_value": "missing_input",
        }
        for name, reason in expected.items():
            outcome = execute_delayed_response_rule(bundle, window(name))
            self.assertTrue(outcome.trace.abstained)
            self.assertFalse(outcome.trace.violation_detected)
            self.assertEqual(outcome.abstention_reason, reason)
        base = runtime_window_to_dict(window("window_response_present"))
        first = copy.deepcopy(base)
        first["input_window_id"] = "WIN-FIRST-TRIGGER-032E"
        first["source_values"] = [1] * 9
        self.assertEqual(execute_delayed_response_rule(bundle, parse_runtime_window(first)).abstention_reason, "missing_pre_trigger_baseline")
        short = copy.deepcopy(base)
        short["input_window_id"] = "WIN-SHORT-COVERAGE-032E"
        short["source_values"] = short["source_values"][:5]
        short["target_values"] = short["target_values"][:5]
        short["end_offset"] = 4
        self.assertEqual(execute_delayed_response_rule(bundle, parse_runtime_window(short)).abstention_reason, "insufficient_post_trigger_coverage")
        wrong_variable = copy.deepcopy(base)
        wrong_variable["input_window_id"] = "WIN-VARIABLE-MISMATCH-032E"
        wrong_variable["source_variable"] = "OtherActuator"
        self.assertEqual(execute_delayed_response_rule(bundle, parse_runtime_window(wrong_variable)).abstention_reason, "input_variable_mismatch")

    def test_parameter_uncertainty_abstains_under_runtime_policy(self) -> None:
        candidate, artifacts, policy = aligned_bundle()
        changed = calibration_parameter_to_dict(artifacts.parameters[0])
        changed["uncertainty"]["status"] = "high"
        high = parse_calibration_parameter(with_computed_artifact_hash(changed))
        parameters = (high,) + artifacts.parameters[1:]
        changed_artifacts = DelayedResponseArtifactCollectionV1(artifacts.graph, artifacts.evidence, parameters)
        changed_policy = dataclasses.replace(policy, allowed_parameter_uncertainty=("bounded", "high"))
        verified = verify_delayed_response_rule(candidate, changed_artifacts, policy=changed_policy)
        bundle = authorize_delayed_response_runtime(verified.accepted_rule, verified.verifier_result, changed_artifacts, verifier_policy=changed_policy, created_at="2026-07-14T18:46:00Z")
        result = execute_delayed_response_rule(bundle, window("window_response_present"))
        self.assertEqual(result.abstention_reason, "parameter_uncertainty")

    def test_trace_has_nine_steps_all_parameters_and_valid_self_hash(self) -> None:
        bundle = authorized_bundle()
        trace = execute_delayed_response_rule(bundle, window("window_response_present")).trace
        self.assertEqual(len(trace.satisfaction_trace), 9)
        self.assertEqual(tuple(step.step for step in trace.satisfaction_trace), tuple(range(1, 10)))
        self.assertEqual(tuple(item.parameter_id for item in trace.parameter_values_used), tuple(sorted(bundle.accepted_rule.parameter_refs)))
        self.assertEqual(canonical_runtime_trace_sha256(trace), trace.artifact_hash)
        self.assertEqual(verify_contract_artifact_hash(runtime_trace_to_dict(trace)), trace.artifact_hash)
        self.assertEqual(parse_runtime_trace(runtime_trace_to_dict(trace)), trace)

    def test_execution_is_deterministic_and_input_preserving(self) -> None:
        bundle = authorized_bundle()
        item = window("window_response_present")
        before = copy.deepcopy((bundle, item))
        first = execute_delayed_response_rule(bundle, item)
        second = execute_delayed_response_rule(bundle, item)
        self.assertEqual(first, second)
        self.assertEqual((bundle, item), before)

    def test_tracked_runtime_trace_fixtures_match_execution(self) -> None:
        bundle = authorized_bundle()
        mapping = {
            "response_present": "window_response_present",
            "response_missing": "window_response_missing",
            "no_trigger": "window_no_trigger",
            "abstained": "window_multiple_triggers",
        }
        for output_name, input_name in mapping.items():
            expected = json.loads((ROOT / f"fixtures/task032e/runtime_trace_{output_name}.json").read_text(encoding="utf-8"))
            actual = execute_delayed_response_rule(bundle, window(input_name)).trace
            self.assertEqual(runtime_trace_to_dict(actual), expected)
            self.assertEqual(parse_runtime_trace(expected), actual)


if __name__ == "__main__":
    unittest.main()
