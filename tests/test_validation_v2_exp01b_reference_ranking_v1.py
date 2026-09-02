from __future__ import annotations

import unittest

from paperworks.validation_v2.exp01_scientific_v1 import PAIR_UNIVERSE
from paperworks.validation_v2.exp01b_ranking_v1 import (
    DispositionEvidenceV1,
    GDNDisposition,
    aggregate_seed_percentiles_v1,
    apply_frozen_disposition_rule_v1,
    deterministic_ranking_v1,
    directional_relation_yield_at_k_v1,
    equal_weight_augmented_scores_v1,
    functional_consensus_v1,
    precision_recall_ndcg_at_k_v1,
    target_local_percentiles_v1,
)
from paperworks.validation_v2.exp01b_reference_v1 import full_arm_blind_pair_reference_v1


class Exp01BReferenceRankingTests(unittest.TestCase):
    def test_reference_is_complete_arm_blind_144_pair_universe(self) -> None:
        self.assertEqual(full_arm_blind_pair_reference_v1(), PAIR_UNIVERSE)
        self.assertEqual(len(PAIR_UNIVERSE), 144)

    def test_target_local_percentiles_use_lexical_tie_and_absent_zero(self) -> None:
        left, right, absent = PAIR_UNIVERSE[0], PAIR_UNIVERSE[12], PAIR_UNIVERSE[24]
        self.assertEqual(left[1], right[1])
        values = target_local_percentiles_v1({right: 2.0, left: 2.0})
        self.assertEqual(values[min(left, right)], 1.0)
        self.assertEqual(values[max(left, right)], 0.0)
        self.assertEqual(values[absent], 0.0)

    def test_consensus_augmentation_and_binary_ndcg_are_deterministic(self) -> None:
        seeds = {
            seed: target_local_percentiles_v1({PAIR_UNIVERSE[seed % 5]: float(seed)})
            for seed in (11, 23, 37)
        }
        edge = aggregate_seed_percentiles_v1(seeds)
        consensus = functional_consensus_v1(edge_mask=edge, attention=None)
        meta = {pair: 0.0 for pair in PAIR_UNIVERSE}
        stat = {pair: 0.0 for pair in PAIR_UNIVERSE}
        baseline, augmented = equal_weight_augmented_scores_v1(
            meta=meta, stat=stat, gdn_functional_consensus=consensus,
        )
        self.assertEqual(set(baseline), set(PAIR_UNIVERSE))
        ranking = deterministic_ranking_v1(augmented)
        metrics = precision_recall_ndcg_at_k_v1(
            ranking, confirmed_pairs={ranking[0], ranking[2]}, k=10,
        )
        self.assertEqual(metrics["confirmed_pair_yield"], 2)
        self.assertGreater(metrics["ndcg"], 0)
        self.assertEqual(
            directional_relation_yield_at_k_v1(
                ranking, directional_relation_pairs=(ranking[0], ranking[0], ranking[4]), k=3,
            ),
            2,
        )

    def _evidence(self, **changes):
        values = dict(
            augmented_confirmed_yield=11,
            baseline_confirmed_yield=10,
            augmented_ndcg=0.8,
            baseline_ndcg=0.7,
            train1_yield_non_degraded=True,
            train2_yield_non_degraded=True,
            train1_ndcg_non_degraded=True,
            train2_ndcg_non_degraded=True,
            gdn_unique_confirmed_pairs=1,
            gdn_unique_executable_rule_pairs=1,
            positive_median_top_edge_mask=True,
            combined_seeds_edge_mask_exceeds_random=2,
            stable_unique_positive_pairs_two_seeds=1,
            stable_meta_stat_functional_pairs_two_seeds=1,
        )
        values.update(changes)
        return DispositionEvidenceV1(**values)

    def test_frozen_three_way_disposition(self) -> None:
        self.assertIs(
            apply_frozen_disposition_rule_v1(self._evidence()),
            GDNDisposition.PRIMARY_AUGMENTATION,
        )
        supporting = self._evidence(
            augmented_confirmed_yield=10,
            augmented_ndcg=0.7,
            stable_unique_positive_pairs_two_seeds=1,
            gdn_unique_executable_rule_pairs=0,
        )
        self.assertIs(apply_frozen_disposition_rule_v1(supporting), GDNDisposition.SUPPORTING_EVIDENCE)
        ablation = self._evidence(
            augmented_confirmed_yield=9,
            augmented_ndcg=0.6,
            train1_yield_non_degraded=False,
            train2_yield_non_degraded=False,
            train1_ndcg_non_degraded=False,
            train2_ndcg_non_degraded=False,
            gdn_unique_confirmed_pairs=0,
            gdn_unique_executable_rule_pairs=0,
            positive_median_top_edge_mask=False,
            combined_seeds_edge_mask_exceeds_random=0,
            stable_unique_positive_pairs_two_seeds=0,
            stable_meta_stat_functional_pairs_two_seeds=0,
        )
        self.assertIs(apply_frozen_disposition_rule_v1(ablation), GDNDisposition.ABLATION_ONLY)


if __name__ == "__main__":
    unittest.main()
