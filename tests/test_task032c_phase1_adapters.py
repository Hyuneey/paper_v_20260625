from __future__ import annotations

import copy
import inspect
import json
import unittest
from pathlib import Path

from paperworks.contracts import (
    DelayedResponseArtifactCollectionV1,
    adapt_phase1_calibration_parameter,
    adapt_phase1_candidate_graph,
    adapt_phase1_evidence_package,
    load_calibration_parameter,
    load_candidate_graph,
    load_delayed_response_rule,
    load_evidence_package,
    validate_artifact,
    verify_contract_artifact_hash,
)
import paperworks.contracts.phase1_adapters as adapter_module


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "fixtures/task032c"


def load(name: str) -> dict:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def graph_context() -> dict:
    graph = load("graph_delayed_response.json")
    edge = graph["edges"][0]
    return {
        "dataset_version": graph["dataset_version"], "graph_id": graph["graph_id"],
        "candidate_universe_id": graph["candidate_universe_id"],
        "node_metadata": {node["variable_name"]: node for node in graph["nodes"]},
        "operating_regimes": edge["operating_regimes"], "edge_semantics": edge["edge_semantics"],
        "provenance": graph["provenance"], "lag_candidate_range": edge["lag_candidate_range"],
        "support": edge["support"], "confidence": edge["confidence"], "uncertainty": edge["uncertainty"],
    }


def evidence_context() -> dict:
    document = load("evidence_delayed_response.json")
    keys = ("evidence_id", "dataset_version", "event_anchor", "event_window", "pre_event_context",
            "post_event_context", "matched_normal_reference", "operating_regime", "candidate_lag_range",
            "selection_policy", "selection_policy_hash", "supported_claims")
    return {key: document[key] for key in keys}


def parameter_mapping(*, status: str = "calibrated", source_context_status: str = "calibration_normal") -> dict:
    target = load("parameter_lag_maximum.json")
    keys = ("relation_family", "source_variables", "target_variables", "operating_regime", "calibration_window_refs",
            "normal_reference_refs", "dataset_version", "code_commit", "calibrator_version", "sample_support",
            "stability_summary", "confidence_interval", "uncertainty")
    result = {key: target[key] for key in keys}
    result.update({"source_parameter_name": "delay_p95_seconds", "source_method": "empirical_delay_quantile",
                   "target_parameter_id": "PARAM-LAG-033", "target_parameter_role": "lag_maximum",
                   "calibration_method": "event_delay_distribution", "target_approval_status": status,
                   "source_context_status": source_context_status})
    return result


class Task032CPhase1AdapterTests(unittest.TestCase):
    def test_complete_graph_context_creates_hash_verified_target(self) -> None:
        universe, gdn, context = load("phase1_candidate_universe.json"), load("phase1_gdn_edges.json"), graph_context()
        before = copy.deepcopy((universe, gdn, context))
        result = adapt_phase1_candidate_graph(universe, context=context, gdn_edges=gdn)
        self.assertEqual(result.status, "created")
        self.assertTrue(result.target_artifact_created)
        target = result.target_artifact
        self.assertIsNotNone(target)
        self.assertEqual(validate_artifact("graph", target_to_dict(target)).status, "valid")
        self.assertEqual(verify_contract_artifact_hash(target_to_dict(target)), result.target_artifact_sha256)
        self.assertFalse(target.edges[0].causal_claim_allowed)
        self.assertEqual((universe, gdn, context), before)

    def test_graph_outside_universe_and_missing_context_fail_without_target(self) -> None:
        outside = load("phase1_gdn_edges.json"); outside["edges"][0]["target"] = "SensorOutside"
        invalid = adapt_phase1_candidate_graph(load("phase1_candidate_universe.json"), context=graph_context(), gdn_edges=outside)
        self.assertEqual(invalid.status, "invalid_source"); self.assertFalse(invalid.target_artifact_created)
        context = graph_context(); del context["node_metadata"]
        pending = adapt_phase1_candidate_graph(load("phase1_candidate_universe.json"), context=context)
        self.assertEqual(pending.status, "pending_context"); self.assertIsNone(pending.target_artifact)

    def test_complete_evidence_context_is_non_reconstructive(self) -> None:
        profile, pack = load("phase1_relation_profile.json"), load("phase1_relation_evidence_pack.json")
        before = copy.deepcopy((profile, pack))
        result = adapt_phase1_evidence_package(profile, pack, context=evidence_context())
        self.assertEqual(result.status, "created")
        target = result.target_artifact
        document = target_to_dict(target)
        self.assertEqual(validate_artifact("evidence_package", document).status, "valid")
        self.assertEqual(verify_contract_artifact_hash(document), result.target_artifact_sha256)
        serialized = json.dumps(document, sort_keys=True)
        self.assertNotIn("trigger_events", serialized); self.assertNotIn("response_events", serialized)
        self.assertFalse(document["raw_values_included"])
        self.assertEqual((profile, pack), before)

    def test_incomplete_evidence_context_returns_pending(self) -> None:
        context = evidence_context(); del context["matched_normal_reference"]
        result = adapt_phase1_evidence_package(load("phase1_relation_profile.json"), load("phase1_relation_evidence_pack.json"), context=context)
        self.assertEqual(result.status, "pending_context"); self.assertFalse(result.target_artifact_created)

    def test_explicit_calibration_mapping_creates_calibrated_not_approved(self) -> None:
        source, mapping = load("phase1_calibration_delay.json"), parameter_mapping()
        before = copy.deepcopy((source, mapping))
        result = adapt_phase1_calibration_parameter(source, mapping=mapping)
        self.assertEqual(result.status, "created")
        target = result.target_artifact
        self.assertEqual(target.approval_status, "calibrated")
        self.assertIsNone(target.approved_by); self.assertIsNone(target.approval_date)
        document = target_to_dict(target)
        self.assertEqual(validate_artifact("parameter_registry", document).status, "valid")
        self.assertEqual(verify_contract_artifact_hash(document), result.target_artifact_sha256)
        self.assertEqual((source, mapping), before)

    def test_parameter_missing_context_unsupported_mapping_and_promotion(self) -> None:
        missing = parameter_mapping(); del missing["uncertainty"]
        pending = adapt_phase1_calibration_parameter(load("phase1_calibration_delay.json"), mapping=missing)
        self.assertEqual(pending.status, "pending_context"); self.assertIsNone(pending.target_artifact)
        unsupported = parameter_mapping(); unsupported["source_method"] = "guessed_method"
        result = adapt_phase1_calibration_parameter(load("phase1_calibration_delay.json"), mapping=unsupported)
        self.assertEqual(result.status, "unsupported_source")
        approved = adapt_phase1_calibration_parameter(load("phase1_calibration_delay.json"), mapping=parameter_mapping(status="approved"))
        self.assertEqual(approved.status, "unsupported_source")
        smoke = adapt_phase1_calibration_parameter(load("phase1_calibration_delay.json"), mapping=parameter_mapping(source_context_status="synthetic_smoke"))
        self.assertEqual(smoke.status, "unsupported_source")

    def test_explicit_magnitude_mapping_preserves_value_and_unit(self) -> None:
        source = load("phase1_calibration_magnitude.json")
        mapping = parameter_mapping()
        mapping.update({
            "source_parameter_name": "minimum_response_magnitude",
            "source_method": "empirical_magnitude_quantile",
            "target_parameter_id": "PARAM-TOL-033",
            "target_parameter_role": "tolerance",
            "calibration_method": "median_absolute_deviation",
        })
        result = adapt_phase1_calibration_parameter(source, mapping=mapping)
        self.assertEqual(result.status, "created")
        self.assertEqual(result.target_artifact.value, source["value"])
        self.assertEqual(result.target_artifact.unit, source["unit"])

    def test_collection_is_lookup_only_and_non_authoritative(self) -> None:
        collection = DelayedResponseArtifactCollectionV1(
            load_candidate_graph(FIXTURE_ROOT / "graph_delayed_response.json"),
            load_evidence_package(FIXTURE_ROOT / "evidence_delayed_response.json"),
            tuple(load_calibration_parameter(FIXTURE_ROOT / name) for name in (
                "parameter_lag_maximum.json", "parameter_tolerance.json", "parameter_duration.json", "parameter_support.json")),
        )
        self.assertIn("GRAPH-SYNTHETIC-032C", collection.graph_by_id)
        self.assertIn("EDGE-ACTUATORA-SENSORB", collection.edge_by_id)
        self.assertIn("NREF-SYNTHETIC-032C", collection.normal_reference_by_id)
        self.assertFalse(collection.rule_binding_verified); self.assertFalse(collection.runtime_authorized)
        rule = load_delayed_response_rule(ROOT / "fixtures/task032b/delayed_response_candidate.json")
        self.assertFalse(rule.runtime_authorized)

    def test_adapter_module_does_not_import_optional_gdn_or_runtime(self) -> None:
        source = inspect.getsource(adapter_module)
        self.assertNotIn("paperworks.gdn", source)
        self.assertNotIn("paperworks.runtime", source)
        self.assertNotIn("paperworks.verification", source)


def target_to_dict(target):
    from paperworks.contracts import calibration_parameter_to_dict, candidate_graph_to_dict, evidence_package_to_dict
    if hasattr(target, "graph_id"):
        return candidate_graph_to_dict(target)
    if hasattr(target, "evidence_id"):
        return evidence_package_to_dict(target)
    return calibration_parameter_to_dict(target)


if __name__ == "__main__":
    unittest.main()
