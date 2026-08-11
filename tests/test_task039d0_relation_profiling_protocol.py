from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from paperworks.v6.continuous_step_protocol_v1 import (
    SustainedStepEventV1,
    cluster_step_events_v1,
    evaluate_step_candidate_v1,
    evaluate_target_response_v1,
)
from paperworks.v6.relation_profiling_protocol_v1 import (
    ARTIFACT_CLASS_BY_TYPE,
    CANDIDATE_COHORT_HASH,
    CANDIDATE_IDENTITY_LIST_HASH,
    FIT_FILES,
    FROZEN_SOURCES,
    RelationProfilingProtocolError,
    assert_arm_blind_identity_record_v1,
    authorize_br2_reference_v1,
    authorize_value_access_v1,
    build_task039d0_artifacts_v1,
    classify_all_source_isolation_v1,
    derive_multi_file_source_parameters_v1,
    derive_multi_file_target_scale_v1,
    DirectionalRelationIdentityV1,
    multi_file_robust_scale_v1,
    profiling_identity_from_candidate_v1,
    q75_linear_v1,
    rank_direction_horizon_v1,
    selected_fit_gate_v1,
    train3_confirmation_gate_v1,
    verify_self_hash_v1,
)
from paperworks.v6.schema_registry_v1 import load_v6_schema_registry_v1


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"


def _cohort() -> dict:
    return json.loads((REPORTS / "TASK-039C_CANDIDATE_PROFILING_COHORT.json").read_text(encoding="utf-8"))


def _direction_record(**overrides: object) -> dict:
    value = {
        "target_direction": "increase",
        "horizon_seconds": 10,
        "pooled_directional_consistency": 0.8,
        "pooled_robust_effect_ratio": 3.0,
        "train1_selected_consistency": 0.7,
        "train1_opposite_consistency": 0.2,
        "train2_selected_consistency": 0.7,
        "train2_opposite_consistency": 0.2,
    }
    value.update(overrides)
    return value


class Task039D0IdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.artifacts = build_task039d0_artifacts_v1(_cohort())

    def test_exact_cohort_and_47_unique_identities(self) -> None:
        view = self.artifacts["profiling_identity_view"].to_dict()
        self.assertEqual(view["cohort_hash"], CANDIDATE_COHORT_HASH)
        self.assertEqual(view["identity_list_hash"], CANDIDATE_IDENTITY_LIST_HASH)
        self.assertEqual(view["candidate_count"], 47)
        pairs = [(item["source"], item["target"]) for item in view["candidates"]]
        self.assertEqual(len(pairs), 47)
        self.assertEqual(len(set(pairs)), 47)

    def test_cohort_mismatch_and_duplicate_rejected(self) -> None:
        cohort = _cohort()
        cohort["artifact_hash"] = "0" * 64
        with self.assertRaises(RelationProfilingProtocolError):
            build_task039d0_artifacts_v1(cohort)

    def test_out_of_cohort_identity_rejected_by_bound_view(self) -> None:
        cohort = _cohort()
        cohort["candidate_identity_list"][0]["target"] = "P1_NOT_A_TARGET"
        content = {key: value for key, value in cohort.items() if key != "artifact_hash"}
        from paperworks.v6.common import stable_hash_v1
        cohort["artifact_hash"] = stable_hash_v1(content)
        with self.assertRaises(RelationProfilingProtocolError):
            build_task039d0_artifacts_v1(cohort)

    def test_profiler_record_rejects_arm_fields(self) -> None:
        record = profiling_identity_from_candidate_v1(_cohort()["candidates"][0])
        for field, value in (("meta_rank", 1), ("stat_correlation", 0.5), ("gdn_similarity", 0.2), ("origin_arms", ["META"])):
            with self.subTest(field=field), self.assertRaises(Exception):
                assert_arm_blind_identity_record_v1({**record, field: value})

    def test_same_pair_projection_is_provenance_invariant(self) -> None:
        a = {"source": "P1_FCV01D", "target": "P1_FT01", "origin_arms": ["META"], "META": {"rank": 1}}
        b = {"source": "P1_FCV01D", "target": "P1_FT01", "origin_arms": ["GDN"], "GDN": {"rank": 20}}
        self.assertEqual(profiling_identity_from_candidate_v1(a), profiling_identity_from_candidate_v1(b))

    def test_artifacts_are_self_hashed_closed_and_round_trip(self) -> None:
        for artifact in self.artifacts.values():
            document = artifact.to_dict()
            verify_self_hash_v1(document)
            parsed = ARTIFACT_CLASS_BY_TYPE[document["artifact_type"]].from_dict(document)
            self.assertEqual(parsed.artifact_hash, artifact.artifact_hash)
            with self.assertRaises(Exception):
                ARTIFACT_CLASS_BY_TYPE[document["artifact_type"]].from_dict({**document, "unknown": 1})

    def test_closed_direction_and_authority_enums_reject_mutation(self) -> None:
        with self.assertRaises(RelationProfilingProtocolError):
            DirectionalRelationIdentityV1({
                "source": "P1_FCV01D", "source_step_direction": "sideways",
                "target": "P1_FT01", "target_response_direction": "increase",
                "selected_horizon_is_identity": False,
                "relation_family": "continuous_step_delayed_response_v1",
            })


class Task039D0ScaleAndEventTests(unittest.TestCase):
    def test_no_cross_file_difference(self) -> None:
        self.assertEqual(multi_file_robust_scale_v1(([0.0] * 10, [100.0] * 10)), 1e-12)

    def test_exact_mad_scale(self) -> None:
        observed = multi_file_robust_scale_v1(([0, 1, 3], [5, 8, 12]))
        self.assertAlmostEqual(observed, 1.4826, places=12)

    def test_q75_linear(self) -> None:
        self.assertEqual(q75_linear_v1([0.0, 10.0]), 7.5)
        self.assertEqual(q75_linear_v1([0.0, 1.0, 2.0, 3.0, 4.0]), 3.0)

    def test_minimum_amplitude_count(self) -> None:
        result = derive_multi_file_source_parameters_v1(([0.0] * 20, [0.0] * 20))
        self.assertEqual(result["status"], "insufficient_nontrivial_amplitudes")
        self.assertLess(result["nontrivial_amplitude_count"], 20)

    def test_threshold_and_stability_formulas(self) -> None:
        values = []
        for level in range(14):
            values.extend([float(level)] * 6)
        result = derive_multi_file_source_parameters_v1((values, values))
        self.assertEqual(result["status"], "supported")
        self.assertGreaterEqual(result["source_step_threshold"], 5 * result["source_noise_scale"])
        self.assertEqual(
            result["source_stability_tolerance"],
            max(3 * result["source_noise_scale"], 0.1 * result["source_step_threshold"]),
        )

    def test_target_scale_reuses_same_file_local_formula(self) -> None:
        self.assertEqual(derive_multi_file_target_scale_v1(([1.0] * 8, [9.0] * 8)), 1e-12)

    def test_step_boundaries_directions_and_stability(self) -> None:
        up = [0.0] * 5 + [10.0] * 5
        self.assertEqual(evaluate_step_candidate_v1(up, 5, source_step_threshold=10.0, source_stability_tolerance=0.0).event.direction, "step_up")
        down = [10.0] * 5 + [0.0] * 5
        self.assertEqual(evaluate_step_candidate_v1(down, 5, source_step_threshold=10.0, source_stability_tolerance=0.0).event.direction, "step_down")
        self.assertIsNone(evaluate_step_candidate_v1(up, 4, source_step_threshold=1.0, source_stability_tolerance=0.0).event)
        unstable = [0, 0, 0, 2, 2] + [10] * 5
        self.assertIsNone(evaluate_step_candidate_v1(unstable, 5, source_step_threshold=5.0, source_stability_tolerance=0.0).event)

    def test_refractory_single_link_largest_and_earliest_tie(self) -> None:
        events = [
            SustainedStepEventV1(10, "step_up", 0, 3, 3, 1, 1),
            SustainedStepEventV1(19, "step_up", 0, 4, 4, 1, 1),
            SustainedStepEventV1(28, "step_up", 0, 4, 4, 1, 1),
        ]
        kept = cluster_step_events_v1(events)
        self.assertEqual([item.event_index for item in kept], [19])

    def test_isolation_inclusive_two_and_all_sources(self) -> None:
        empty = {source: () for source in FROZEN_SOURCES}
        event = SustainedStepEventV1(10, "step_up", 0, 2, 2, 1, 1)
        other = SustainedStepEventV1(12, "step_down", 2, 0, -2, 1, 1)
        empty[FROZEN_SOURCES[0]] = (event,)
        empty[FROZEN_SOURCES[1]] = (other,)
        result = classify_all_source_isolation_v1(empty)
        self.assertFalse(result[FROZEN_SOURCES[0]][0][1])
        with self.assertRaises(RelationProfilingProtocolError):
            classify_all_source_isolation_v1({FROZEN_SOURCES[0]: (event,)})


class Task039D0TargetSelectionGateTests(unittest.TestCase):
    def test_target_horizons_baseline_window_and_censoring(self) -> None:
        values = [0.0] * 5 + [0.0] + [3.0] * 70
        for horizon in (1, 5, 10, 30, 60):
            result = evaluate_target_response_v1(values, event_index=5, horizon_seconds=horizon, target_noise_scale=1.0, target_direction="increase")
            self.assertFalse(result.right_censored)
            self.assertTrue(result.direction_matches)
        self.assertTrue(evaluate_target_response_v1(values[:12], event_index=5, horizon_seconds=5, target_noise_scale=1.0, target_direction="increase").right_censored)

    def test_increase_decrease_and_neutral_thresholds(self) -> None:
        increase = [0.0] * 6 + [2.0] * 5
        result = evaluate_target_response_v1(increase, event_index=5, horizon_seconds=1, target_noise_scale=1.0, target_direction="increase")
        self.assertTrue(result.direction_matches)
        exact = [0.0] * 6 + [1.0] * 5
        self.assertFalse(evaluate_target_response_v1(exact, event_index=5, horizon_seconds=1, target_noise_scale=1.0, target_direction="increase").direction_matches)

    def test_strict_direction_agreement_equality_rejected(self) -> None:
        self.assertIsNone(rank_direction_horizon_v1([_direction_record(train1_selected_consistency=0.2, train1_opposite_consistency=0.2)]))

    def test_selection_order(self) -> None:
        records = [
            _direction_record(horizon_seconds=30, pooled_directional_consistency=0.8, pooled_robust_effect_ratio=4.0),
            _direction_record(horizon_seconds=10, pooled_directional_consistency=0.8, pooled_robust_effect_ratio=4.0),
            _direction_record(target_direction="decrease", horizon_seconds=10, pooled_directional_consistency=0.8, pooled_robust_effect_ratio=4.0),
            _direction_record(horizon_seconds=60, pooled_directional_consistency=0.9, pooled_robust_effect_ratio=2.0),
        ]
        self.assertEqual(rank_direction_horizon_v1(records)["horizon_seconds"], 60)
        tied = [item for item in records if item["pooled_directional_consistency"] == 0.8]
        self.assertEqual(rank_direction_horizon_v1(tied)["target_direction"], "decrease")
        self.assertEqual(rank_direction_horizon_v1(tied)["horizon_seconds"], 10)

    def test_fit_gate_every_boundary_and_no_fallback(self) -> None:
        passing = {
            **_direction_record(), "total_usable_responses": 20,
            "train1_usable_responses": 5, "train2_usable_responses": 5,
            "pooled_directional_consistency": 0.70,
            "train1_selected_consistency": 0.60, "train1_opposite_consistency": 0.20,
            "train2_selected_consistency": 0.60, "train2_opposite_consistency": 0.20,
            "pooled_robust_effect_ratio": 2.0,
        }
        self.assertTrue(selected_fit_gate_v1(passing))
        for field, below in (("total_usable_responses", 19), ("train1_usable_responses", 4), ("train2_usable_responses", 4), ("pooled_directional_consistency", 0.699), ("train1_selected_consistency", 0.599), ("train2_selected_consistency", 0.599), ("pooled_robust_effect_ratio", 1.999)):
            with self.subTest(field=field):
                self.assertFalse(selected_fit_gate_v1({**passing, field: below}))
        selected = rank_direction_horizon_v1([_direction_record(pooled_directional_consistency=0.9), _direction_record(target_direction="decrease", pooled_directional_consistency=0.8)])
        self.assertEqual(selected["target_direction"], "increase")

    def test_train3_gate_boundaries_and_strict_direction(self) -> None:
        args = dict(usable_responses=5, source_direction_unchanged=True, selected_consistency=0.60, opposite_consistency=0.20, robust_effect_ratio=1.0, fit_parameters_reused_without_retuning=True)
        self.assertTrue(train3_confirmation_gate_v1(**args))
        self.assertFalse(train3_confirmation_gate_v1(**{**args, "usable_responses": 4}))
        self.assertFalse(train3_confirmation_gate_v1(**{**args, "selected_consistency": 0.20, "opposite_consistency": 0.20}))
        self.assertFalse(train3_confirmation_gate_v1(**{**args, "robust_effect_ratio": 0.999}))
        self.assertFalse(train3_confirmation_gate_v1(**{**args, "fit_parameters_reused_without_retuning": False}))


class Task039D0AuthorityAndReportTests(unittest.TestCase):
    def test_d0_and_prohibited_files_denied_d1_fit_only_allowed(self) -> None:
        with self.assertRaises(RelationProfilingProtocolError):
            authorize_value_access_v1(task_id="TASK-039D0", relative_file=FIT_FILES[0])
        for name in ("hai-train3.csv", "hai-train4.csv", "test", "labels", "attacks"):
            with self.subTest(name=name), self.assertRaises(RelationProfilingProtocolError):
                authorize_value_access_v1(task_id="TASK-039D1", relative_file=name)
        for name in FIT_FILES:
            authorize_value_access_v1(task_id="TASK-039D1", relative_file=name)

    def test_br2_pair_result_guard(self) -> None:
        authorize_br2_reference_v1(purpose="lineage_hash_verification", artifact_name="task039br2_execution_receipt")
        with self.assertRaises(RelationProfilingProtocolError):
            authorize_br2_reference_v1(purpose="scientific_input", artifact_name="fit_supported_pairs")

    def test_authorization_is_d1_only(self) -> None:
        auth = json.loads((REPORTS / "TASK-039D1_AUTHORIZATION.json").read_text(encoding="utf-8"))
        self.assertTrue(auth["train1_authorized"] and auth["train2_authorized"])
        self.assertFalse(auth["train3_authorized"] or auth["train4_authorized"])
        self.assertFalse(auth["rule_v2_authorized"] or auth["agent_authorized"] or auth["detector_runtime_authorized"])
        self.assertFalse(auth["candidate_arm_evidence_visible_to_profiler"])

    def test_bundle_has_no_real_result_or_authority_leak(self) -> None:
        bundle = json.loads((REPORTS / "TASK-039D0_PROTOCOL_BUNDLE.json").read_text(encoding="utf-8"))
        self.assertEqual(bundle["status"], "passed_task039d0_relation_profiling_protocol_freeze")
        self.assertFalse(bundle["real_hai_feature_access"])
        self.assertFalse(bundle["d2_execution_authorized"])
        self.assertFalse(bundle["rule_v2_authorized"])
        self.assertEqual(bundle["unresolved_fields"], [])

    def test_all_new_schemas_registered_and_closed(self) -> None:
        registry = load_v6_schema_registry_v1(repository_root=ROOT)
        self.assertEqual(len(registry.artifact_types), 118)
        for artifact_type in ARTIFACT_CLASS_BY_TYPE:
            schema = registry.schema_for(artifact_type)
            self.assertFalse(schema["additionalProperties"])

    def test_all_d0_instances_validate_draft_2020_12_schemas(self) -> None:
        artifacts = build_task039d0_artifacts_v1(_cohort())
        directional = DirectionalRelationIdentityV1({
            "source": "P1_FCV01D", "source_step_direction": "step_up",
            "target": "P1_FT01", "target_response_direction": "increase",
            "selected_horizon_is_identity": False,
            "relation_family": "continuous_step_delayed_response_v1",
        })
        documents = [item.to_dict() for item in artifacts.values()] + [directional.to_dict()]
        registry = load_v6_schema_registry_v1(repository_root=ROOT)
        for document in documents:
            validator = Draft202012Validator(registry.schema_for(document["artifact_type"]))
            self.assertEqual(list(validator.iter_errors(document)), [])
            self.assertNotEqual(list(validator.iter_errors({**document, "unknown": True})), [])


if __name__ == "__main__":
    unittest.main()
