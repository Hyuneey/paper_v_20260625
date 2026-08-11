from __future__ import annotations

import copy
import unittest

from paperworks.profiling.task039d2_audit_accounting_v1 import (
    CommitABSeparationV1,
    TASK039D2AuditPreparationError,
    derive_direction_confirmation_partition_v1,
    derive_pair_confirmation_partition_v1,
    reconstruct_arm_metrics_v1,
    verify_private_confirmation_ledger_v1,
    verify_synthetic_replay_matches_outcomes_v1,
)
from paperworks.profiling.task039d2_audit_reference_v1 import (
    replay_synthetic_directions_reference_v1,
)
from paperworks.v6.relation_profiling_protocol_v1 import (
    FROZEN_SOURCES,
    FROZEN_TARGETS,
)
from tests.task039d2_audit_support import (
    fake_hash,
    make_arm_provenance,
    make_confirmation_ledger,
    make_input_set,
    rehash_ledger,
    response_target,
    stepped_source,
    synthetic_value_map,
)


def _ordered_pairs(input_set):
    return tuple(
        dict.fromkeys(
            (item.source, item.target) for item in input_set.directional_inputs
        )
    )


def _identities_for_pair(input_set, pair):
    return [
        (item.source, item.target, item.source_step_direction)
        for item in input_set.directional_inputs
        if (item.source, item.target) == pair
    ]


class D2LedgerAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.input_set = make_input_set()

    def test_exact_45_directions_and_25_pairs_are_required(self) -> None:
        self.assertEqual(len(self.input_set.directional_inputs), 45)
        self.assertEqual(len(_ordered_pairs(self.input_set)), 25)
        with self.assertRaisesRegex(
            TASK039D2AuditPreparationError, "exactly 45"
        ):
            type(self.input_set)(
                directional_inputs=self.input_set.directional_inputs[:-1],
                source_parameters=self.input_set.source_parameters,
                target_parameters=self.input_set.target_parameters,
                d1_source_ledger_hash=self.input_set.d1_source_ledger_hash,
                d1_target_ledger_hash=self.input_set.d1_target_ledger_hash,
                d1_directional_ledger_hash=self.input_set.d1_directional_ledger_hash,
            )

    def test_private_ledger_and_each_record_self_hash_verify(self) -> None:
        ledger = make_confirmation_ledger(self.input_set)
        outcomes = verify_private_confirmation_ledger_v1(
            ledger, input_set=self.input_set
        )
        self.assertEqual(outcomes.private_ledger_hash, ledger["artifact_hash"])
        tampered = copy.deepcopy(ledger)
        tampered["records"][0]["usable_response_count"] = 99
        with self.assertRaisesRegex(
            TASK039D2AuditPreparationError, "ledger self-hash mismatch"
        ):
            verify_private_confirmation_ledger_v1(
                tampered, input_set=self.input_set
            )

    def test_exact_d1_record_hash_mutation_fails_after_valid_rehash(self) -> None:
        ledger = make_confirmation_ledger(self.input_set)
        ledger["records"][0]["d1_directional_record_hash"] = fake_hash(
            "wrong-but-well-formed-D1-hash"
        )
        rehash_ledger(ledger, record_index=0)
        with self.assertRaisesRegex(
            TASK039D2AuditPreparationError, "immutable D1 binding"
        ):
            verify_private_confirmation_ledger_v1(
                ledger, input_set=self.input_set
            )

    def test_claimed_status_must_match_independent_gate(self) -> None:
        ledger = make_confirmation_ledger(self.input_set)
        ledger["records"][0]["status"] = "calibration_confirmed"
        rehash_ledger(ledger, record_index=0)
        with self.assertRaisesRegex(
            TASK039D2AuditPreparationError, "independent frozen gate"
        ):
            verify_private_confirmation_ledger_v1(
                ledger, input_set=self.input_set
            )

    def test_direction_partition_and_three_pair_derivations(self) -> None:
        pairs = _ordered_pairs(self.input_set)
        statuses = {}
        # Pair 0: both directions confirm.
        for identity in _identities_for_pair(self.input_set, pairs[0]):
            statuses[identity] = "calibration_confirmed"
        # Pair 1: exactly one direction confirms.
        statuses[_identities_for_pair(self.input_set, pairs[1])[0]] = (
            "calibration_confirmed"
        )
        # Pair 2 remains all-conflict.
        outcomes = verify_private_confirmation_ledger_v1(
            make_confirmation_ledger(self.input_set, status_by_identity=statuses),
            input_set=self.input_set,
        )
        partition = derive_pair_confirmation_partition_v1(outcomes)
        direction_partition = derive_direction_confirmation_partition_v1(outcomes)
        self.assertIn(pairs[0], partition.confirmed_pairs)
        self.assertIn(pairs[1], partition.confirmed_pairs)
        self.assertIn(pairs[2], partition.conflict_pairs)
        self.assertEqual(len(partition.confirmed_pairs), 2)
        self.assertEqual(len(partition.conflict_pairs), 23)
        self.assertEqual(len(direction_partition.confirmed_directions), 3)
        self.assertEqual(len(direction_partition.conflict_directions), 42)

    def test_completed_metrics_must_match_independent_45_direction_replay(self) -> None:
        replayed = replay_synthetic_directions_reference_v1(
            directional_inputs=self.input_set.directional_inputs,
            source_parameters=self.input_set.source_parameters,
            target_parameters=self.input_set.target_parameters,
            value_map=synthetic_value_map(
                source_values={
                    FROZEN_SOURCES[0]: stepped_source(direction="step_up")
                },
                target_values={
                    FROZEN_TARGETS[0]: response_target(direction="increase")
                },
            ),
        )
        statuses = {
            (item.source, item.target, item.source_step_direction): item.status
            for item in replayed
        }
        metrics = {
            (item.source, item.target, item.source_step_direction): {
                "usable_response_count": item.usable_response_count,
                "right_censored_count": item.right_censored_count,
                "source_direction_unchanged": True,
                "selected_consistency": item.selected_consistency,
                "opposite_consistency": item.opposite_consistency,
                "robust_effect_ratio": item.robust_effect_ratio,
            }
            for item in replayed
        }
        ledger = make_confirmation_ledger(
            self.input_set,
            status_by_identity=statuses,
            metrics_by_identity=metrics,
        )
        outcomes = verify_private_confirmation_ledger_v1(
            ledger, input_set=self.input_set
        )
        verify_synthetic_replay_matches_outcomes_v1(
            replayed=replayed, outcomes=outcomes
        )
        ledger["records"][0]["right_censored_count"] += 1
        rehash_ledger(ledger, record_index=0)
        changed = verify_private_confirmation_ledger_v1(
            ledger, input_set=self.input_set
        )
        with self.assertRaisesRegex(
            TASK039D2AuditPreparationError, "does not match"
        ):
            verify_synthetic_replay_matches_outcomes_v1(
                replayed=replayed, outcomes=changed
            )


class D0ArmMetricReconstructionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.input_set = make_input_set()
        self.pairs = _ordered_pairs(self.input_set)

    def _outcomes(self):
        statuses = {}
        for pair_index, confirm_count in ((0, 2), (1, 1), (3, 1), (4, 1), (5, 1)):
            for identity in _identities_for_pair(
                self.input_set, self.pairs[pair_index]
            )[:confirm_count]:
                statuses[identity] = "calibration_confirmed"
        return verify_private_confirmation_ledger_v1(
            make_confirmation_ledger(self.input_set, status_by_identity=statuses),
            input_set=self.input_set,
        )

    def test_arm_metrics_transfer_coverage_and_overlap(self) -> None:
        arm_sets = (
            make_arm_provenance(
                self.input_set,
                arm="META",
                supported_pairs={
                    self.pairs[0], self.pairs[1], self.pairs[2], self.pairs[5]
                },
            ),
            make_arm_provenance(
                self.input_set,
                arm="STAT",
                supported_pairs={self.pairs[1], self.pairs[3], self.pairs[5]},
            ),
            make_arm_provenance(
                self.input_set,
                arm="GDN",
                supported_pairs={self.pairs[1], self.pairs[4]},
            ),
        )
        audit = reconstruct_arm_metrics_v1(
            outcomes=self._outcomes(), arm_provenance=arm_sets
        )
        metrics = {item.arm: item for item in audit.arm_metrics}
        self.assertEqual(metrics["META"].fit_supported_pair_count, 4)
        self.assertEqual(metrics["META"].confirmed_pair_count, 3)
        self.assertEqual(metrics["META"].pair_fit_support_yield, 4 / 20)
        self.assertEqual(metrics["META"].confirmed_relation_yield, 3 / 20)
        self.assertEqual(metrics["META"].pair_transfer, 3 / 4)
        self.assertEqual(metrics["META"].fit_supported_direction_count, 8)
        self.assertEqual(metrics["META"].confirmed_direction_count, 4)
        self.assertEqual(metrics["META"].directional_transfer, 4 / 8)
        self.assertEqual(metrics["META"].confirmed_source_count, 3)
        self.assertEqual(metrics["META"].confirmed_source_rate, 3 / 12)
        self.assertEqual(metrics["META"].confirmed_target_count, 1)
        self.assertEqual(metrics["META"].confirmed_target_rate, 1 / 12)
        self.assertEqual(audit.overlap.unique_meta, {self.pairs[0]})
        self.assertEqual(audit.overlap.unique_stat, {self.pairs[3]})
        self.assertEqual(audit.overlap.unique_gdn, {self.pairs[4]})
        self.assertEqual(audit.overlap.shared_two_arms, {self.pairs[5]})
        self.assertEqual(
            audit.overlap.shared_all_applicable_arms, {self.pairs[1]}
        )

    def test_zero_transfer_denominators_are_zero(self) -> None:
        arm_sets = tuple(
            make_arm_provenance(
                self.input_set, arm=arm, supported_pairs=set()
            )
            for arm in ("META", "STAT", "GDN")
        )
        audit = reconstruct_arm_metrics_v1(
            outcomes=self._outcomes(), arm_provenance=arm_sets
        )
        for metrics in audit.arm_metrics:
            self.assertEqual(metrics.fit_supported_pair_count, 0)
            self.assertEqual(metrics.fit_supported_direction_count, 0)
            self.assertEqual(metrics.pair_transfer, 0.0)
            self.assertEqual(metrics.directional_transfer, 0.0)

    def test_outcomes_freeze_before_provenance_and_arm_contract_is_blind(self) -> None:
        outcome_fields = set(self._outcomes().directions[0].__dataclass_fields__)
        prohibited = {
            "meta_rank",
            "meta_tier",
            "stat_score",
            "stat_horizon",
            "gdn_rank",
            "gdn_similarity",
            "gdn_frequency",
            "origin_arms",
            "overlap_category",
        }
        self.assertTrue(outcome_fields.isdisjoint(prohibited))
        with self.assertRaises(TypeError):
            type(make_arm_provenance(
                self.input_set, arm="META", supported_pairs=set()
            ))(arm="META", pairs=frozenset(), meta_rank=1)


class CommitSeparationAuditTests(unittest.TestCase):
    def test_commit_a_b_separation_accepts_result_only_descendant(self) -> None:
        receipt = CommitABSeparationV1(
            commit_a="a" * 40,
            commit_b="b" * 40,
            commit_b_first_parent="a" * 40,
            commit_a_scientific_tree_hash=fake_hash("scientific-tree"),
            commit_b_scientific_tree_hash=fake_hash("scientific-tree"),
            commit_b_changed_paths=(
                "docs/task_reports/TASK-039D2_RESULT.json",
                "docs/task_reports/TASK-039D2_REPORT.md",
            ),
        )
        self.assertNotEqual(receipt.commit_a, receipt.commit_b)

    def test_commit_b_scientific_change_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            TASK039D2AuditPreparationError, "scientific implementation"
        ):
            CommitABSeparationV1(
                commit_a="a" * 40,
                commit_b="b" * 40,
                commit_b_first_parent="a" * 40,
                commit_a_scientific_tree_hash=fake_hash("tree-A"),
                commit_b_scientific_tree_hash=fake_hash("tree-B"),
                commit_b_changed_paths=(
                    "docs/task_reports/TASK-039D2_RESULT.json",
                ),
            )


if __name__ == "__main__":
    unittest.main()
