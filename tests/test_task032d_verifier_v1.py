from __future__ import annotations

import copy
import dataclasses
import json
import unittest
from pathlib import Path

from paperworks.contracts import (
    DelayedResponseArtifactCollectionV1,
    DelayedResponseVerifierPolicyV1,
    adapt_phase1_calibration_parameter,
    evidence_package_to_dict,
    load_calibration_parameter,
    load_candidate_graph,
    load_delayed_response_rule,
    load_evidence_package,
    parse_calibration_parameter,
    parse_candidate_graph,
    parse_delayed_response_rule,
    parse_evidence_package,
    verifier_result_to_dict,
    verify_delayed_response_rule,
    with_computed_artifact_hash,
)


ROOT = Path(__file__).resolve().parents[1]
PARAMETER_FILES = {
    "lag": "parameter_lag.json",
    "tolerance": "parameter_tolerance.json",
    "duration": "parameter_duration.json",
    "support": "parameter_support.json",
    "severity": "parameter_severity.json",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def aligned_bundle():
    rule = load_delayed_response_rule(ROOT / "fixtures/task032d/rule_candidate.json")
    graph = load_candidate_graph(ROOT / "fixtures/task032c/graph_delayed_response.json")
    evidence = load_evidence_package(ROOT / "fixtures/task032c/evidence_delayed_response.json")
    parameters = tuple(load_calibration_parameter(ROOT / "fixtures/task032d" / name) for name in PARAMETER_FILES.values())
    policy = DelayedResponseVerifierPolicyV1.from_dict(load_json(ROOT / "fixtures/task032d/verifier_policy.json"))
    return rule, DelayedResponseArtifactCollectionV1(graph, evidence, parameters), policy


def outcome_codes(rule, artifacts, policy, library=()):
    outcome = verify_delayed_response_rule(rule, artifacts, policy=policy, accepted_library=library)
    return outcome, [issue.code for issue in outcome.verifier_result.violations]


def modified_rule(mutator):
    document = load_json(ROOT / "fixtures/task032d/rule_candidate.json")
    mutator(document)
    return parse_delayed_response_rule(document)


def modified_graph(mutator):
    document = load_json(ROOT / "fixtures/task032c/graph_delayed_response.json")
    mutator(document)
    return parse_candidate_graph(with_computed_artifact_hash(document))


def modified_evidence(mutator):
    document = load_json(ROOT / "fixtures/task032c/evidence_delayed_response.json")
    mutator(document)
    return parse_evidence_package(with_computed_artifact_hash(document))


def modified_parameter(name, mutator):
    document = load_json(ROOT / "fixtures/task032d" / PARAMETER_FILES[name])
    mutator(document)
    return parse_calibration_parameter(with_computed_artifact_hash(document))


def replace_parameter(artifacts, replacement=None, *, omit=None):
    parameters = []
    for parameter in artifacts.parameters:
        if parameter.parameter_id == omit:
            continue
        if replacement is not None and parameter.parameter_id == replacement.parameter_id:
            parameters.append(replacement)
        else:
            parameters.append(parameter)
    return DelayedResponseArtifactCollectionV1(artifacts.graph, artifacts.evidence, tuple(parameters))


class Task032DVerifierTests(unittest.TestCase):
    def assert_issue(self, expected, *, rule=None, artifacts=None, policy=None, library=()):
        base_rule, base_artifacts, base_policy = aligned_bundle()
        outcome, codes = outcome_codes(rule or base_rule, artifacts or base_artifacts, policy or base_policy, library)
        self.assertIn(expected, codes, codes)
        self.assertIsNone(outcome.accepted_rule)
        self.assertFalse(outcome.runtime_authorized)
        return outcome

    def test_candidate_authority_preclaims_are_rejected(self) -> None:
        accepted = modified_rule(lambda doc: doc.update(status="accepted"))
        self.assert_issue("RULE_AUTHORITY_PRECLAIMED", rule=accepted)
        prefilled = modified_rule(lambda doc: doc.update(verified_rule_hash="f" * 64))
        self.assert_issue("RULE_AUTHORITY_PRECLAIMED", rule=prefilled)

    def test_graph_reference_direction_and_types(self) -> None:
        rule, artifacts, policy = aligned_bundle()
        missing = modified_graph(lambda doc: doc.update(edges=[]))
        self.assert_issue("GRAPH_EDGE_NOT_FOUND", artifacts=DelayedResponseArtifactCollectionV1(missing, artifacts.evidence, artifacts.parameters))
        reversed_graph = modified_graph(lambda doc: doc["edges"][0].update(source_node="NODE-SEN-032C", target_node="NODE-ACT-032C"))
        self.assert_issue("GRAPH_DIRECTION_MISMATCH", artifacts=DelayedResponseArtifactCollectionV1(reversed_graph, artifacts.evidence, artifacts.parameters))
        source_type = modified_graph(lambda doc: doc["nodes"][0].update(node_type="sensor", data_type="continuous"))
        self.assert_issue("SOURCE_TYPE_MISMATCH", artifacts=DelayedResponseArtifactCollectionV1(source_type, artifacts.evidence, artifacts.parameters))
        target_type = modified_graph(lambda doc: doc["nodes"][1].update(node_type="actuator", data_type="binary"))
        self.assert_issue("TARGET_TYPE_MISMATCH", artifacts=DelayedResponseArtifactCollectionV1(target_type, artifacts.evidence, artifacts.parameters))

    def test_subsystem_and_relation_family_mismatch(self) -> None:
        rule, artifacts, _ = aligned_bundle()
        graph = modified_graph(lambda doc: doc["nodes"][0].update(subsystem="other_subsystem"))
        self.assert_issue("SUBSYSTEM_MISMATCH", artifacts=DelayedResponseArtifactCollectionV1(graph, artifacts.evidence, artifacts.parameters))
        unsupported = dataclasses.replace(rule, relation_type="range")
        self.assert_issue("RELATION_FAMILY_UNSUPPORTED", rule=unsupported)

    def test_evidence_variable_regime_dataset_and_raw_boundaries(self) -> None:
        rule, artifacts, _ = aligned_bundle()
        source = modified_evidence(lambda doc: doc.update(source_variables=["ActuatorC"]))
        self.assert_issue("EVIDENCE_VARIABLE_MISMATCH", artifacts=DelayedResponseArtifactCollectionV1(artifacts.graph, source, artifacts.parameters))
        def change_regime(doc):
            doc["operating_regime"] = "REGIME-OTHER-032D"
            doc["matched_normal_reference"]["operating_regime"] = "REGIME-OTHER-032D"
        regime = modified_evidence(change_regime)
        self.assert_issue("EVIDENCE_REGIME_MISMATCH", artifacts=DelayedResponseArtifactCollectionV1(artifacts.graph, regime, artifacts.parameters))
        dataset = modified_evidence(lambda doc: doc.update(dataset_version="synthetic-other-v1"))
        self.assert_issue("EVIDENCE_DATASET_MISMATCH", artifacts=DelayedResponseArtifactCollectionV1(artifacts.graph, dataset, artifacts.parameters))
        raw_doc = load_json(ROOT / "fixtures/task032c/evidence_delayed_response.json")
        raw_doc["raw_values_included"] = True
        raw_hash = with_computed_artifact_hash(raw_doc)["artifact_hash"]
        raw = dataclasses.replace(artifacts.evidence, raw_values_included=True, artifact_hash=raw_hash)
        self.assert_issue("STRUCTURAL_BINDING_INVALID", artifacts=DelayedResponseArtifactCollectionV1(artifacts.graph, raw, artifacts.parameters))

    def test_normal_reference_and_missing_parameter(self) -> None:
        rule, artifacts, _ = aligned_bundle()
        missing_normal = modified_rule(lambda doc: doc.update(normal_reference_refs=["NREF-OTHER-032D"]))
        self.assert_issue("NORMAL_REFERENCE_INVALID", rule=missing_normal)
        missing_parameter = replace_parameter(artifacts, omit="PARAM-TOL-032")
        self.assert_issue("PARAMETER_MISSING", artifacts=missing_parameter)

    def test_parameter_approval_stability_and_uncertainty(self) -> None:
        _, artifacts, policy = aligned_bundle()
        not_approved = modified_parameter("tolerance", lambda doc: doc.update(approval_status="calibrated", approved_by=None, approval_date=None))
        self.assert_issue("PARAMETER_NOT_APPROVED", artifacts=replace_parameter(artifacts, not_approved))
        def make_unstable(doc):
            doc.update(approval_status="unstable", approved_by=None, approval_date=None)
            doc["stability_summary"]["status"] = "unstable"
        unstable = modified_parameter("tolerance", make_unstable)
        self.assert_issue("PARAMETER_UNSTABLE", artifacts=replace_parameter(artifacts, unstable))
        high = modified_parameter("tolerance", lambda doc: doc["uncertainty"].update(status="high"))
        self.assert_issue("PARAMETER_UNCERTAINTY_PROHIBITED", artifacts=replace_parameter(artifacts, high), policy=policy)

    def test_parameter_provenance_mismatches(self) -> None:
        _, artifacts, _ = aligned_bundle()
        cases = (
            ("PARAMETER_VARIABLE_MISMATCH", lambda doc: doc.update(source_variables=["ActuatorC"])),
            ("PARAMETER_REGIME_MISMATCH", lambda doc: doc.update(operating_regime="REGIME-OTHER-032D")),
            ("PARAMETER_DATASET_MISMATCH", lambda doc: doc.update(dataset_version="synthetic-other-v1")),
        )
        for code, mutator in cases:
            with self.subTest(code=code):
                changed = modified_parameter("tolerance", mutator)
                self.assert_issue(code, artifacts=replace_parameter(artifacts, changed))

    def test_unit_lag_range_and_window_bindings(self) -> None:
        _, artifacts, _ = aligned_bundle()
        tolerance = modified_parameter("tolerance", lambda doc: doc.update(unit="other_units"))
        self.assert_issue("TOLERANCE_UNIT_MISMATCH", artifacts=replace_parameter(artifacts, tolerance))
        lag = modified_parameter("lag", lambda doc: doc.update(value=4))
        self.assert_issue("LAG_MAXIMUM_MISMATCH", artifacts=replace_parameter(artifacts, lag))
        graph = modified_graph(lambda doc: doc["edges"][0]["lag_candidate_range"].update(maximum=4))
        self.assert_issue("LAG_OUTSIDE_GRAPH_RANGE", artifacts=DelayedResponseArtifactCollectionV1(graph, artifacts.evidence, artifacts.parameters))
        evidence = modified_evidence(lambda doc: doc["candidate_lag_range"].update(maximum=4))
        self.assert_issue("LAG_OUTSIDE_EVIDENCE_RANGE", artifacts=DelayedResponseArtifactCollectionV1(artifacts.graph, evidence, artifacts.parameters))
        duration = modified_parameter("duration", lambda doc: doc.update(value=4))
        self.assert_issue("WINDOW_DURATION_MISMATCH", artifacts=replace_parameter(artifacts, duration))

    def test_support_and_severity_completeness(self) -> None:
        _, artifacts, _ = aligned_bundle()
        support = modified_parameter("support", lambda doc: doc.update(value=11))
        self.assert_issue("INSUFFICIENT_SUPPORT", artifacts=replace_parameter(artifacts, support))
        missing = replace_parameter(artifacts, omit="PARAM-SEVERITY-032")
        self.assert_issue("PARAMETER_MISSING", artifacts=missing)
        source = load_json(ROOT / "fixtures/task032c/phase1_calibration_magnitude.json")
        mapping = {
            "source_parameter_name": source["parameter_name"], "source_method": source["method"],
            "target_parameter_id": "PARAM-SEVERITY-033", "target_parameter_role": "severity_boundary",
            "calibration_method": "robust_range", "relation_family": "delayed_response",
            "source_variables": ["ActuatorA"], "target_variables": ["SensorB"],
            "operating_regime": "REGIME-SYNTHETIC-032C", "calibration_window_refs": ["WIN-EVENT-032C"],
            "normal_reference_refs": ["NREF-SYNTHETIC-032C"], "dataset_version": "synthetic-task032c-v1",
            "code_commit": "0f3d27f", "calibrator_version": "adapter-prohibited",
            "sample_support": {"event_count": 12, "matched_count": 10, "normal_reference_count": 12, "minimum_required": 5},
            "stability_summary": {"status": "stable", "method": "bootstrap", "replicate_count": 10, "variation_measure": 0.1},
            "confidence_interval": {"level": 0.95, "lower": 0.1, "upper": 0.9, "method": "robust_quantile"},
            "uncertainty": {"status": "bounded", "sources": ["sampling"]},
            "target_approval_status": "calibrated", "source_context_status": "calibration_normal",
        }
        result = adapt_phase1_calibration_parameter(source, mapping=mapping)
        self.assertEqual(result.status, "unsupported_source")
        self.assertFalse(result.target_artifact_created)

    def test_structural_duplicate_is_rejected_without_behavioral_claim(self) -> None:
        rule, artifacts, policy = aligned_bundle()
        accepted = verify_delayed_response_rule(rule, artifacts, policy=policy)
        duplicate, codes = outcome_codes(rule, artifacts, policy, (accepted,))
        self.assertIn("STRUCTURAL_DUPLICATE", codes)
        self.assertEqual(duplicate.verifier_result.status, "rejected")
        self.assertEqual(duplicate.verifier_result.duplicate_records[0].relation, "structural_duplicate")
        self.assertNotIn("behavioral_duplicate", json.dumps(verifier_result_to_dict(duplicate.verifier_result)))

    def test_non_repairable_provenance_and_deterministic_issue_order(self) -> None:
        rule, artifacts, policy = aligned_bundle()
        bad = modified_parameter("tolerance", lambda doc: doc.update(dataset_version="synthetic-other-v1", operating_regime="REGIME-OTHER-032D"))
        changed = replace_parameter(artifacts, bad)
        first = verify_delayed_response_rule(rule, changed, policy=policy)
        second = verify_delayed_response_rule(rule, changed, policy=policy)
        self.assertEqual(first, second)
        self.assertEqual(first.verifier_result.status, "rejected")
        order = [(issue.stage, issue.code, issue.field) for issue in first.verifier_result.violations]
        self.assertEqual(order, sorted(order))
        self.assertIn("verified_parameter_values", first.verifier_result.non_repairable_fields)


if __name__ == "__main__":
    unittest.main()
