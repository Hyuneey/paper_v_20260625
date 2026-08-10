from __future__ import annotations

import json
import unittest
from pathlib import Path

from paperworks.v6.candidate_discovery_protocol_v1 import (
    ArmCandidateV1,
    CandidateDiscoveryProtocolBundleV1,
    CandidateDiscoveryProtocolError,
    GDNRankInputV1,
    MetadataRankInputV1,
    StatisticalRankInputV1,
    assert_candidate_in_universe_v1,
    authorize_br2_pair_artifact_use_v1,
    authorize_candidate_arm_value_access_v1,
    build_default_candidate_discovery_bundle_v1,
    derive_candidate_budget_views_v1,
    integrate_candidate_union_v1,
    rank_gdn_candidates_v1,
    rank_metadata_candidates_v1,
    rank_statistical_candidates_v1,
    select_statistical_horizon_v1,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/v6/task039c0_candidate_discovery_protocol.json"


class Task039C0CandidateProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        cls.bundle = build_default_candidate_discovery_bundle_v1(config=cls.config)

    def test_exact_source_and_target_identity_binding(self) -> None:
        universe = self.bundle.universe_policy
        self.assertEqual(len(universe.source_variables), 12)
        self.assertEqual(len(universe.target_variables), 12)
        self.assertEqual(universe.eligible_pair_count, 144)
        self.assertEqual(universe.source_target_overlap_count, 0)

    def test_source_identity_mutation_fails(self) -> None:
        payload = self.bundle.universe_policy.to_dict()
        payload["source_variables"][0] = "P1_CHANGED"
        with self.assertRaises(CandidateDiscoveryProtocolError):
            type(self.bundle.universe_policy).from_dict(payload)

    def test_target_identity_mutation_fails(self) -> None:
        payload = self.bundle.universe_policy.to_dict()
        payload["target_metadata_refs"][0] = "0" * 64
        with self.assertRaises(CandidateDiscoveryProtocolError):
            type(self.bundle.universe_policy).from_dict(payload)

    def test_source_role_rejection(self) -> None:
        payload = self.bundle.universe_policy.to_dict()
        payload["source_semantic_roles"][0] = "process_sensor"
        with self.assertRaises(CandidateDiscoveryProtocolError):
            type(self.bundle.universe_policy).from_dict(payload)

    def test_target_role_rejection(self) -> None:
        payload = self.bundle.universe_policy.to_dict()
        payload["target_semantic_roles"][0] = "control_command"
        with self.assertRaises(CandidateDiscoveryProtocolError):
            type(self.bundle.universe_policy).from_dict(payload)

    def test_out_of_universe_candidate_rejection(self) -> None:
        with self.assertRaises(CandidateDiscoveryProtocolError):
            assert_candidate_in_universe_v1(
                self.bundle.universe_policy, "P1_UNKNOWN", "P1_FT01"
            )

    def test_in_universe_candidate_accepted(self) -> None:
        assert_candidate_in_universe_v1(
            self.bundle.universe_policy, "P1_FCV01D", "P1_FT01"
        )

    def test_br2_relation_content_access_rejected(self) -> None:
        with self.assertRaises(CandidateDiscoveryProtocolError):
            authorize_br2_pair_artifact_use_v1(
                self.bundle.data_access_policy,
                artifact_kind="BR2_directional_fit_records",
                requested_mode="candidate_ranking",
            )

    def test_br2_relation_hash_verification_allowed(self) -> None:
        authorize_br2_pair_artifact_use_v1(
            self.bundle.data_access_policy,
            artifact_kind="BR2_directional_fit_records",
            requested_mode="lineage_hash_verification",
        )

    def test_budget_views_reuse_one_ranking(self) -> None:
        ranking = tuple((f"S{i:02d}", f"T{i:02d}") for i in range(45))
        views = derive_candidate_budget_views_v1(ranking)
        self.assertEqual(views.top10, ranking[:10])
        self.assertEqual(views.top20, ranking[:20])
        self.assertEqual(views.top40, ranking[:40])

    def test_budget_views_do_not_pad(self) -> None:
        ranking = (("S1", "T1"), ("S2", "T2"))
        views = derive_candidate_budget_views_v1(ranking)
        self.assertEqual(views.top20, ranking)
        self.assertEqual(views.candidate_shortfall[20], 18)

    def test_duplicate_budget_ranking_rejected(self) -> None:
        with self.assertRaises(CandidateDiscoveryProtocolError):
            derive_candidate_budget_views_v1((("S", "T"), ("S", "T")))

    def test_metadata_tier_and_reference_ordering(self) -> None:
        entries = (
            MetadataRankInputV1("S3", "T3", "M3_SUBSYSTEM_SUPPORTED", 4),
            MetadataRankInputV1("S2", "T2", "M1_EXPLICIT", 1),
            MetadataRankInputV1("S1", "T1", "M1_EXPLICIT", 2),
            MetadataRankInputV1("S0", "T0", "M2_GRAPH_ADJACENT", 9),
        )
        ranked = rank_metadata_candidates_v1(entries)
        self.assertEqual([item.source for item in ranked], ["S1", "S2", "S0", "S3"])

    def test_statistical_sign_stability(self) -> None:
        selection = select_statistical_horizon_v1(
            {1: (0.2, 0.3), 5: (-0.1, -0.4), 10: (0.1, -0.2), 30: (0.0, 0.4), 60: (0.05, 0.05)}
        )
        self.assertEqual(selection.status, "cross_file_sign_stable")
        self.assertEqual(selection.selected_horizon, 1)
        self.assertEqual(selection.score, 0.2)

    def test_statistical_exact_zero_is_unstable(self) -> None:
        selection = select_statistical_horizon_v1(
            {h: (0.0, 0.1) for h in (1, 5, 10, 30, 60)}
        )
        self.assertEqual(selection.status, "direction_unstable")
        self.assertEqual(selection.score, 0.0)

    def test_statistical_horizon_tie_prefers_shorter(self) -> None:
        selection = select_statistical_horizon_v1(
            {1: (0.3, 0.2), 5: (0.2, 0.8), 10: (-0.1, 0.2), 30: (-0.1, 0.1), 60: (0.1, -0.1)}
        )
        self.assertEqual(selection.selected_horizon, 1)

    def test_statistical_ranking_stable_before_unstable(self) -> None:
        unstable = select_statistical_horizon_v1(
            {h: (0.1, -0.1) for h in (1, 5, 10, 30, 60)}
        )
        stable = select_statistical_horizon_v1(
            {h: (0.2, 0.3) for h in (1, 5, 10, 30, 60)}
        )
        ranked = rank_statistical_candidates_v1(
            (
                StatisticalRankInputV1("A", "A", unstable),
                StatisticalRankInputV1("Z", "Z", stable),
            )
        )
        self.assertEqual(ranked[0].source, "Z")

    def test_no_arbitrary_statistical_threshold(self) -> None:
        self.assertIsNone(
            self.bundle.statistical_policy.arbitrary_minimum_correlation_threshold
        )

    def test_gdn_fidelity_and_smoke_boundaries(self) -> None:
        policy = self.bundle.gdn_policy
        self.assertEqual(policy.required_fidelity_class, "upstream_aligned_validated")
        self.assertFalse(policy.smoke_backends_allowed_as_gdn)
        self.assertEqual(policy.seeds, (11, 23, 37))

    def test_gdn_ranking_frequency_before_similarity(self) -> None:
        ranked = rank_gdn_candidates_v1(
            (
                GDNRankInputV1("A", "A", 1.0 / 3.0, 0.99),
                GDNRankInputV1("B", "B", 2.0 / 3.0, 0.01),
                GDNRankInputV1("C", "C", 2.0 / 3.0, 0.50),
            )
        )
        self.assertEqual([item.source for item in ranked], ["C", "B", "A"])

    def test_gdn_attention_and_xai_not_primary(self) -> None:
        policy = self.bundle.gdn_policy
        self.assertEqual(policy.attention_evidence_role, "supplementary_graph_evidence")
        self.assertFalse(policy.attention_causal_claim_allowed)
        self.assertFalse(policy.post_hoc_xai_primary)

    def test_unscored_union_deduplicates_and_preserves_provenance(self) -> None:
        meta = ArmCandidateV1("P1_FCV01D", "P1_FT01", ("a" * 64,))
        stat = ArmCandidateV1("P1_FCV01D", "P1_FT01", ("b" * 64,))
        other = ArmCandidateV1("P1_FCV02D", "P1_FT02", ("c" * 64,))
        union = integrate_candidate_union_v1(
            universe=self.bundle.universe_policy,
            meta_top20=(meta,),
            stat_top20=(stat,),
            gdn_top20=(other,),
        )
        self.assertEqual(len(union), 2)
        self.assertEqual(union[0].origin_arms, ("META", "STAT"))
        self.assertEqual(union[0].meta_rank, 1)
        self.assertEqual(union[0].stat_rank, 1)

    def test_cross_arm_numerical_score_is_prohibited(self) -> None:
        policy = self.bundle.integration_policy
        self.assertFalse(policy.merged_numerical_score_allowed)
        self.assertFalse(policy.cross_method_union_ranking_allowed)

    def test_arm_data_permission_matrix(self) -> None:
        policy = self.bundle.data_access_policy
        for arm in ("STAT", "GDN"):
            authorize_candidate_arm_value_access_v1(
                policy,
                arm=arm,
                process_id="P1",
                relative_file="hai-23.05/hai-train1.csv",
            )
        with self.assertRaises(CandidateDiscoveryProtocolError):
            authorize_candidate_arm_value_access_v1(
                policy,
                arm="META",
                process_id="P1",
                relative_file="hai-23.05/hai-train1.csv",
            )

    def test_train3_train4_test_and_other_process_rejected(self) -> None:
        policy = self.bundle.data_access_policy
        for relative in (
            "hai-23.05/hai-train3.csv",
            "hai-23.05/hai-train4.csv",
            "hai-23.05/hai-test1.csv",
        ):
            with self.assertRaises(CandidateDiscoveryProtocolError):
                authorize_candidate_arm_value_access_v1(
                    policy, arm="STAT", process_id="P1", relative_file=relative
                )
        with self.assertRaises(CandidateDiscoveryProtocolError):
            authorize_candidate_arm_value_access_v1(
                policy,
                arm="GDN",
                process_id="P3",
                relative_file="hai-23.05/hai-train1.csv",
            )

    def test_protocol_grants_no_task039d_or_execution_authority(self) -> None:
        self.assertFalse(self.bundle.real_hai_feature_access)
        self.assertFalse(self.bundle.candidate_discovery_executed)
        self.assertFalse(self.bundle.final_candidate_universe_created)
        self.assertFalse(self.bundle.task039d_authorized)
        self.assertFalse(self.bundle.main_merge_authorized)

    def test_round_trip_and_deterministic_hash(self) -> None:
        payload = self.bundle.to_dict()
        round_trip = CandidateDiscoveryProtocolBundleV1.from_dict(payload)
        self.assertEqual(round_trip.to_dict(), payload)

    def test_unknown_field_rejected(self) -> None:
        payload = self.bundle.to_dict()
        payload["unexpected"] = True
        with self.assertRaises(CandidateDiscoveryProtocolError):
            CandidateDiscoveryProtocolBundleV1.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
