from __future__ import annotations

import copy
import dataclasses
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from paperworks.contracts import (
    SyntheticVerticalSliceError,
    canonical_vertical_slice_report_sha256,
    run_task032f_vertical_slice,
    synthetic_vertical_slice_report_to_dict,
)
import paperworks.contracts.vertical_slice_v1 as vertical_slice


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/contracts/task032f_synthetic_vertical_slice.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Task032FSyntheticVerticalSliceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = run_task032f_vertical_slice(CONFIG_PATH)

    def test_complete_path_is_created_verified_authorized_and_executed(self) -> None:
        report = self.report
        self.assertTrue(all(status == "created" for _, status in report.adapters.statuses))
        self.assertEqual(len(report.adapters.statuses), 6)
        self.assertEqual(len(report.adapters.parameter_lineage_matches), 4)
        self.assertTrue(all(matched for _, matched in report.adapters.parameter_lineage_matches))
        self.assertIn("PARAM-SEVERITY-032", dict(report.adapters.approved_parameter_hashes))
        self.assertTrue(report.verification.all_twenty_stages_passed)
        self.assertEqual(len(report.verification.stage_statuses), 20)
        self.assertTrue(all(status == "passed" for _, _, status in report.verification.stage_statuses))
        self.assertFalse(report.verification.runtime_authorized)
        self.assertEqual(
            report.verification.accepted_rule_hash,
            report.verification.verification_subject_hash,
        )
        self.assertEqual(len(report.runtime.scenarios), 8)
        self.assertTrue(all(item.contract_expectation_matched for item in report.runtime.scenarios))
        self.assertTrue(all(item.nine_steps_verified for item in report.runtime.scenarios))
        self.assertTrue(all(item.trace_binding_verified for item in report.runtime.scenarios))
        self.assertTrue(all(item.explanation_binding_verified for item in report.runtime.scenarios))

    def test_scenario_contract_states_and_no_detector_or_fusion_result(self) -> None:
        scenarios = {item.scenario_id: item for item in self.report.runtime.scenarios}
        self.assertFalse(scenarios["response_present"].violation_detected)
        self.assertTrue(scenarios["response_missing"].violation_detected)
        self.assertFalse(scenarios["no_trigger"].trigger_satisfied)
        self.assertEqual(scenarios["multiple_triggers"].abstention_reason, "multiple_triggers")
        self.assertEqual(scenarios["regime_mismatch"].abstention_reason, "regime_mismatch")
        self.assertEqual(scenarios["missing_input"].abstention_reason, "missing_input")
        self.assertEqual(
            scenarios["first_sample_trigger"].abstention_reason,
            "missing_pre_trigger_baseline",
        )
        self.assertEqual(
            scenarios["insufficient_coverage"].abstention_reason,
            "insufficient_post_trigger_coverage",
        )
        serialized = json.dumps(
            synthetic_vertical_slice_report_to_dict(self.report), sort_keys=True
        )
        self.assertNotIn("source_values", serialized)
        self.assertNotIn("target_values", serialized)
        self.assertNotIn("detector_result", serialized)
        self.assertNotIn("fusion_result", serialized)

    def test_report_hash_is_deterministic_and_covers_nonself_fields(self) -> None:
        self.assertEqual(
            canonical_vertical_slice_report_sha256(self.report), self.report.report_hash
        )
        changed = dataclasses.replace(self.report, config_hash="f" * 64)
        self.assertNotEqual(
            canonical_vertical_slice_report_sha256(changed), self.report.report_hash
        )
        tracked = load_json(
            ROOT / "docs/task_reports/TASK-032F_VERTICAL_SLICE_REPORT.json"
        )
        self.assertEqual(tracked, synthetic_vertical_slice_report_to_dict(self.report))

    def test_caller_config_is_not_mutated_and_parameter_order_is_canonical(self) -> None:
        config = load_json(CONFIG_PATH)
        before = copy.deepcopy(config)
        first = run_task032f_vertical_slice(config)
        self.assertEqual(config, before)
        reordered = copy.deepcopy(config)
        approved = reordered["canonical_artifacts"]["approved_parameters"]
        reordered["canonical_artifacts"]["approved_parameters"] = dict(
            reversed(list(approved.items()))
        )
        second = run_task032f_vertical_slice(reordered)
        self.assertEqual(first, second)

    def test_adapter_failures_stop_without_partial_report(self) -> None:
        config = load_json(CONFIG_PATH)
        missing_context = copy.deepcopy(config)
        del missing_context["adapter_contexts"]["graph"]["node_metadata"]
        with self.assertRaises(SyntheticVerticalSliceError) as pending:
            run_task032f_vertical_slice(missing_context)
        self.assertEqual(pending.exception.stage, "graph_adapter")
        self.assertEqual(set(pending.exception.to_failure_record()), {"stage", "issue_code", "message"})

        bad_gdn = load_json(ROOT / "fixtures/task032c/phase1_gdn_edges.json")
        bad_gdn["edges"][0]["target"] = "SensorOutside"
        with self.assertRaises(SyntheticVerticalSliceError) as outside:
            run_task032f_vertical_slice(config, document_overrides={"gdn_edges": bad_gdn})
        self.assertEqual(outside.exception.stage, "graph_adapter")

        bad_pack = load_json(ROOT / "fixtures/task032c/phase1_relation_evidence_pack.json")
        bad_pack["target"] = "OtherSensor"
        with self.assertRaises(SyntheticVerticalSliceError) as evidence:
            run_task032f_vertical_slice(
                config, document_overrides={"relation_evidence_pack": bad_pack}
            )
        self.assertEqual(evidence.exception.stage, "evidence_adapter")

        unsupported = copy.deepcopy(config)
        unsupported["adapter_contexts"]["parameters"]["calibration_delay"][
            "source_method"
        ] = "guessed_method"
        with self.assertRaises(SyntheticVerticalSliceError) as calibration:
            run_task032f_vertical_slice(unsupported)
        self.assertEqual(calibration.exception.stage, "parameter_adapter.calibration_delay")

    def test_missing_severity_and_candidate_reference_stop_before_runtime(self) -> None:
        config = load_json(CONFIG_PATH)
        missing_severity = copy.deepcopy(config)
        missing_severity["canonical_artifacts"]["severity_parameter"] = (
            "fixtures/task032f/missing_severity.json"
        )
        with self.assertRaises(SyntheticVerticalSliceError) as severity:
            run_task032f_vertical_slice(missing_severity)
        self.assertEqual(severity.exception.stage, "parameter_load")

        candidate = load_json(ROOT / "fixtures/task032d/rule_candidate.json")
        candidate["graph_edge_refs"] = ["EDGE-UNKNOWN-032F"]
        with self.assertRaises(SyntheticVerticalSliceError) as reference:
            run_task032f_vertical_slice(
                config, document_overrides={"candidate_rule": candidate}
            )
        self.assertEqual(reference.exception.stage, "candidate_reference_precheck")

    def test_verifier_rejection_and_modified_result_stop_before_authorization(self) -> None:
        config = load_json(CONFIG_PATH)
        candidate = load_json(ROOT / "fixtures/task032d/rule_candidate.json")
        candidate["subsystem"] = "other_subsystem"
        with self.assertRaises(SyntheticVerticalSliceError) as rejected:
            run_task032f_vertical_slice(
                config, document_overrides={"candidate_rule": candidate}
            )
        self.assertEqual(rejected.exception.stage, "verifier")

        original = vertical_slice.verify_delayed_response_rule

        def modified_result(*args, **kwargs):
            outcome = original(*args, **kwargs)
            return dataclasses.replace(
                outcome,
                verifier_result=dataclasses.replace(
                    outcome.verifier_result, artifact_hash="f" * 64
                ),
            )

        with patch.object(vertical_slice, "verify_delayed_response_rule", modified_result):
            with self.assertRaises(SyntheticVerticalSliceError) as modified:
                run_task032f_vertical_slice(config)
        self.assertEqual(modified.exception.stage, "verifier")

    def test_authorization_trace_and_explanation_mismatches_fail_closed(self) -> None:
        config = load_json(CONFIG_PATH)
        original_authorize = vertical_slice.authorize_delayed_response_runtime

        def modified_authorization(*args, **kwargs):
            bundle = original_authorize(*args, **kwargs)
            return dataclasses.replace(
                bundle,
                receipt=dataclasses.replace(bundle.receipt, graph_hash="f" * 64),
            )

        with patch.object(
            vertical_slice, "authorize_delayed_response_runtime", modified_authorization
        ):
            with self.assertRaises(SyntheticVerticalSliceError) as authorization:
                run_task032f_vertical_slice(config)
        self.assertEqual(authorization.exception.stage, "runtime_authorization")

        original_execute = vertical_slice.execute_delayed_response_rule

        def modified_trace(*args, **kwargs):
            execution = original_execute(*args, **kwargs)
            return dataclasses.replace(
                execution,
                trace=dataclasses.replace(execution.trace, artifact_hash="f" * 64),
            )

        with patch.object(vertical_slice, "execute_delayed_response_rule", modified_trace):
            with self.assertRaises(SyntheticVerticalSliceError) as trace:
                run_task032f_vertical_slice(config)
        self.assertTrue(trace.exception.stage.startswith("runtime."))

        def rejected_explanation(*args, **kwargs):
            raise vertical_slice.SyntheticVerticalSliceError(
                "explanation_binding", "EXPLANATION_AUTHORIZATION_INVALID", "rejected"
            )

        with patch.object(
            vertical_slice, "render_delayed_response_explanation", rejected_explanation
        ):
            with self.assertRaises(SyntheticVerticalSliceError) as explanation:
                run_task032f_vertical_slice(config)
        self.assertTrue(explanation.exception.stage.startswith("explanation."))

    def test_integration_module_has_no_prohibited_surfaces(self) -> None:
        source = (ROOT / "src/paperworks/contracts/vertical_slice_v1.py").read_text(
            encoding="utf-8"
        )
        for prohibited in (
            "paperworks.gdn",
            "paperworks.planning",
            "paperworks.runtime",
            "OpenAI",
            "Anthropic",
            "subprocess",
            "exec(",
            "eval(",
        ):
            self.assertNotIn(prohibited, source)


if __name__ == "__main__":
    unittest.main()
