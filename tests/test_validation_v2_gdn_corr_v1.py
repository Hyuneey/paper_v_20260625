from __future__ import annotations

import unittest

import numpy as np

from paperworks.validation_v2.exp01_scientific_v1 import PAIR_UNIVERSE
from paperworks.validation_v2.gdn_corr_v1 import (
    GDNCorrError,
    corrected_functional_consensus_r1,
    corrected_meta_stat_scores_r1,
    deterministic_ranking_r1,
    fit_transform_policy_v1,
    matched_random_controls_r1,
    observed_percentiles_r1,
    purged_contiguous_validation_plan_v1,
    ranking_membership_percentiles_r1,
    signed_edgemask_evidence_r1,
)
from paperworks.validation_v2.gdn_corr_contract_v1 import (
    Exp01CDispositionEvidenceV1,
    LearnedGraphDisposition,
    apply_exp01c_disposition_v1,
    exp01b_r1_contract_document_v1,
    exp01c_preregistration_document_v1,
)


class CorrectedRankingTests(unittest.TestCase):
    def test_last_observed_is_positive_and_absent_is_zero(self) -> None:
        first, second, absent = PAIR_UNIVERSE[:3]
        result = observed_percentiles_r1({first: 2.0, second: 1.0}, target_local=False)
        self.assertEqual(result[first], 1.0)
        self.assertEqual(result[second], 0.5)
        self.assertEqual(result[absent], 0.0)

    def test_equal_scores_receive_equal_evidence(self) -> None:
        same_target = (PAIR_UNIVERSE[0], PAIR_UNIVERSE[12])
        result = observed_percentiles_r1({same_target[0]: 3.0, same_target[1]: 3.0}, target_local=True)
        self.assertEqual(result[same_target[0]], result[same_target[1]])
        self.assertEqual(result[same_target[0]], 1.0)

    def test_insertion_order_does_not_change_scores_or_ranking(self) -> None:
        pairs = PAIR_UNIVERSE[:5]
        left = observed_percentiles_r1(dict(zip(pairs, (4, 3, 3, 2, 1))), target_local=False)
        right = observed_percentiles_r1(dict(reversed(tuple(zip(pairs, (4, 3, 3, 2, 1))))), target_local=False)
        self.assertEqual(left, right)
        self.assertEqual(deterministic_ranking_r1(left), deterministic_ranking_r1(right))

    def test_membership_worst_is_positive(self) -> None:
        ranking = PAIR_UNIVERSE[:20]
        values = ranking_membership_percentiles_r1(ranking)
        self.assertEqual(values[ranking[-1]], 1 / 20)
        self.assertEqual(values[PAIR_UNIVERSE[20]], 0.0)

    def test_meta_stat_top_budget_is_exact_union(self) -> None:
        meta = PAIR_UNIVERSE[:20]
        stat = PAIR_UNIVERSE[10:30]
        scores, union = corrected_meta_stat_scores_r1(meta_ranking=meta, stat_ranking=stat)
        self.assertEqual(set(deterministic_ranking_r1(scores)[: len(union)]), set(union))

    def test_aggregate_and_augmented_helpers_are_complete(self) -> None:
        from paperworks.validation_v2.gdn_corr_v1 import (
            aggregate_seed_percentiles_r1, augmented_scores_r1,
        )

        complete = {pair: 0.25 for pair in PAIR_UNIVERSE}
        aggregate = aggregate_seed_percentiles_r1({11: complete, 23: complete, 37: complete})
        baseline, augmented = augmented_scores_r1(
            meta=complete, stat=complete, functional=aggregate,
        )
        self.assertEqual(set(baseline), set(PAIR_UNIVERSE))
        self.assertEqual(set(augmented), set(PAIR_UNIVERSE))
        self.assertTrue(all(value == 0.25 for value in augmented.values()))


class CorrectedFunctionalTests(unittest.TestCase):
    def test_negative_and_neutral_are_not_positive_evidence(self) -> None:
        positive, neutral, negative = PAIR_UNIVERSE[:3]
        result = signed_edgemask_evidence_r1({positive: 1.0, neutral: 0.0, negative: -1.0})
        self.assertEqual(result.positive_scores, {positive: 1.0})
        self.assertIn(neutral, result.neutral_pairs)
        self.assertIn(negative, result.counterevidence_pairs)

    def test_attention_cannot_override_negative_edge_mask(self) -> None:
        pair = PAIR_UNIVERSE[0]
        attention = {item: 1.0 for item in PAIR_UNIVERSE}
        result = corrected_functional_consensus_r1(raw_edge_mask={pair: -0.2}, attention_percentiles=attention)
        self.assertEqual(result[pair], 0.0)

    def test_controls_exclude_full_focal_set_and_do_not_repeat(self) -> None:
        target = PAIR_UNIVERSE[0][1]
        eligible = tuple(pair for pair in PAIR_UNIVERSE if pair[1] == target)
        focal = eligible[:4]
        assignments, unmatched = matched_random_controls_r1(
            focal_edges=focal, eligible_graph_edges=eligible, seed=11, view="TRAIN1_ONLY",
        )
        self.assertFalse(unmatched)
        self.assertTrue(set(assignments.values()).isdisjoint(focal))
        self.assertEqual(len(assignments), len(set(assignments.values())))
        self.assertTrue(all(edge[1] == control[1] for edge, control in assignments.items()))

    def test_insufficient_controls_are_explicit(self) -> None:
        target = PAIR_UNIVERSE[0][1]
        eligible = tuple(pair for pair in PAIR_UNIVERSE if pair[1] == target)[:3]
        assignments, unmatched = matched_random_controls_r1(
            focal_edges=eligible[:2], eligible_graph_edges=eligible, seed=23, view="TRAIN2_ONLY",
        )
        self.assertEqual(len(assignments), 1)
        self.assertEqual(len(unmatched), 1)


class HAIReadinessPrimitiveTests(unittest.TestCase):
    def test_scaler_is_fit_to_supplied_training_matrix_only(self) -> None:
        train = np.array([[1.0, 10.0], [3.0, 20.0], [5.0, 100.0]])
        transformed, receipt = fit_transform_policy_v1(train, policy="TRAIN_ONLY_ROBUST_MEDIAN_IQR")
        self.assertEqual(receipt["fit_scope"], "TRAINING_VIEW_ONLY")
        self.assertEqual(receipt["fit_row_count"], 3)
        self.assertAlmostEqual(float(np.median(transformed[:, 0])), 0.0)

    def test_purged_validation_has_zero_raw_timestamp_overlap(self) -> None:
        plan = purged_contiguous_validation_plan_v1(
            segment_lengths=(300, 320), seed=11, history=5,
            max_horizon=62, validation_ratio=0.2,
        )
        self.assertEqual(plan.raw_timestamp_overlap_count, 0)
        self.assertEqual(len(plan.validation_blocks), 2)
        for segment_index, start, stop in plan.validation_blocks:
            self.assertTrue(start < stop)
            local_rows = tuple(local for file_index, local in plan.validation_window_indices if file_index == segment_index)
            self.assertEqual(local_rows, tuple(range(start, stop)))
        self.assertEqual(plan.purge_rows, 66)

    def test_interval_purge_matches_raw_support_oracle(self) -> None:
        from paperworks.validation_v2.gdn_corr_v1 import window_raw_support_v1

        history, maximum = 5, 12
        plan = purged_contiguous_validation_plan_v1(
            segment_lengths=(70, 75), seed=23, history=history,
            max_horizon=maximum, validation_ratio=0.2,
        )
        validation_support = {
            (file_index, row)
            for file_index, local in plan.validation_window_indices
            for row in window_raw_support_v1(
                stop=history + local, history=history, max_horizon=maximum,
            )
        }
        available = (70 - history - maximum + 1, 75 - history - maximum + 1)
        oracle = tuple(
            (file_index, local)
            for file_index, count in enumerate(available)
            for local in range(count)
            if not {
                (file_index, row) for row in window_raw_support_v1(
                    stop=history + local, history=history, max_horizon=maximum,
                )
            } & validation_support
        )
        self.assertEqual(plan.train_window_indices, oracle)

    def test_purged_validation_fails_on_short_file(self) -> None:
        with self.assertRaises(GDNCorrError):
            purged_contiguous_validation_plan_v1(
                segment_lengths=(60, 60, 60, 60, 60, 60), seed=11,
                history=5, max_horizon=62, validation_ratio=0.2,
            )


class FrozenContractTests(unittest.TestCase):
    def test_contracts_are_self_hashed_and_prohibit_test_inputs(self) -> None:
        digest = "a" * 64
        r1 = exp01b_r1_contract_document_v1(
            source_commit="b" * 40, implementation_hashes={"implementation": digest},
        )
        prereg = exp01c_preregistration_document_v1(
            source_commit="b" * 40, implementation_hashes={"implementation": digest},
        )
        self.assertEqual(r1["status"], "FROZEN_BEFORE_CORRECTED_RESULT_ACCESS")
        self.assertIn("test1", r1["prohibited_inputs"])
        self.assertEqual(prereg["status"], "FROZEN_BEFORE_TRAINING")
        self.assertEqual(prereg["run_count"], 9)
        self.assertEqual(prereg["validation"]["raw_timestamp_overlap_allowed"], 0)

    def test_disposition_is_fail_closed(self) -> None:
        base = dict(
            yield_improved=True, ndcg_improved=False,
            other_metric_not_degraded=True, seed_stability_pass=True,
            split_stability_pass=True, unique_formal_v4_rule_count=1,
            stable_positive_event_conditioned_count=1,
            matched_random_pass=True, stable_positive_normal_confirmed_count=1,
        )
        self.assertEqual(
            apply_exp01c_disposition_v1(Exp01CDispositionEvidenceV1(**base)),
            LearnedGraphDisposition.PRIMARY,
        )
        base["matched_random_pass"] = False
        self.assertEqual(
            apply_exp01c_disposition_v1(Exp01CDispositionEvidenceV1(**base)),
            LearnedGraphDisposition.SUPPORTING,
        )
        base["stable_positive_normal_confirmed_count"] = 0
        self.assertEqual(
            apply_exp01c_disposition_v1(Exp01CDispositionEvidenceV1(**base)),
            LearnedGraphDisposition.ABLATION,
        )


if __name__ == "__main__":
    unittest.main()
