from __future__ import annotations

import dataclasses
import unittest
from types import SimpleNamespace

from paperworks.validation_v2.exp01_scientific_v1 import (
    ArmId, BACKEND_CLASSIFICATION, BackendExecutionReceiptV1, CORRECTED_NEIGHBOR_POLICY_HASH,
    EXPECTED_AGGREGATES, EXPECTED_SCHEDULE, EXP01_SCIENTIFIC_CONTRACT_HASH,
    Exp01ScientificContractError, FROZEN_NEIGHBOR_POLICY_HASH, PAIR_UNIVERSE,
    PREREGISTRATION_HASH, PUBLIC_DATA_AUTHORITY_HASH, SEEDS, Stage, StageStateV1,
    TRAINING_CONFIG_HASH, UPSTREAM_GDN_COMMIT, ViewId, advance_stage_v1,
    build_backend_execution_receipt_v1, build_candidate_aggregate_receipt_v1,
    build_candidate_union_authority_v1, build_checkpoint_set_receipt_v1,
    build_confirmation_receipt_v1, build_inclusion_evidence_handoff_v1,
    build_mask_intervention_receipt_v1, build_profiling_submission_v1,
    build_public_data_authority_v1, build_seed_projection_v1,
    build_view_receipt_v1, initial_stage_state_v1,
)
from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER


def graph_edges() -> tuple[tuple[str, str], ...]:
    rows: list[tuple[str, str]] = []
    for target_index, target in enumerate(P1_FEATURE_ORDER):
        sources = [P1_FEATURE_ORDER[(target_index + offset) % len(P1_FEATURE_ORDER)] for offset in range(1, 6)]
        if target == PAIR_UNIVERSE[0][1] and PAIR_UNIVERSE[0][0] not in sources:
            sources[0] = PAIR_UNIVERSE[0][0]
        rows.extend((source, target) for source in sources)
    return tuple(rows)


class ValidationV2Exp01ScientificV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.authority = build_public_data_authority_v1()
        self.views = tuple(
            build_view_receipt_v1(
                view_id=view, authority_hash=self.authority.authority_hash,
                materialized_input_hash=stable_hash_v1({"view": view.value}),
            ) for view in ViewId
        )
        self.edges = graph_edges()
        self.backends = tuple(
            build_backend_execution_receipt_v1(
                arm_id=arm, seed=seed,
                view_receipt=next(item for item in self.views if item.view_id == view),
                checkpoint_hash=stable_hash_v1({"checkpoint": [arm, view, seed]}),
                graph_edges=self.edges,
            ) for arm, view, seed in EXPECTED_SCHEDULE
        )
        self.seeds = tuple(build_seed_projection_v1(backend_receipt=item) for item in self.backends)
        self.checkpoints = build_checkpoint_set_receipt_v1(
            authority_hash=self.authority.authority_hash,
            view_receipts=self.views, seed_receipts=self.seeds,
        )
        self.aggregates = tuple(
            build_candidate_aggregate_receipt_v1(
                arm_id=ArmId(arm), view_id=ViewId(view), checkpoint_set=self.checkpoints,
            ) for arm, view in EXPECTED_AGGREGATES
        )
        self.candidate_union = build_candidate_union_authority_v1(candidate_aggregates=self.aggregates)
        self.submission = build_profiling_submission_v1(candidate_union=self.candidate_union)
        self.confirmation = build_confirmation_receipt_v1(
            candidate_union=self.candidate_union,
            submission=self.submission, decision_ledger_hash=stable_hash_v1({"ledger": "arm-blind"}),
            confirmed_pairs=self.submission.candidate_pairs, rejected_pairs=(),
        )
        mask = (PAIR_UNIVERSE[0],)
        corrected_combined = {
            item.seed: item for item in self.seeds
            if item.arm_id == ArmId.CORRECTED_SELF_EXCLUDED.value and item.view_id == ViewId.COMBINED.value
        }
        intervened = tuple(edge for edge in self.edges if edge not in set(mask))
        self.interventions = tuple(
            build_mask_intervention_receipt_v1(
                corrected_seed_receipt=corrected_combined[seed], checkpoint_set=self.checkpoints,
                primary_mask_pairs=mask, baseline_graph_edges=self.edges,
                intervened_graph_edges=intervened,
                baseline_metric_hash=stable_hash_v1({"baseline": seed}),
                intervention_metric_hash=stable_hash_v1({"intervention": seed}),
            ) for seed in SEEDS
        )

    def stage_through_mask(self):
        state = initial_stage_state_v1()
        for stage, evidence in (
            (Stage.AUTHORITY_BOUND, self.authority),
            (Stage.VIEWS_MATERIALIZED, self.views),
            (Stage.SEEDS_COMPLETED, self.checkpoints),
            (Stage.CANDIDATES_AGGREGATED, self.aggregates),
            (Stage.PROFILING_CONFIRMED, self.confirmation),
            (Stage.MASK_INTERVENTION_COMPLETED, self.interventions),
        ):
            state = advance_stage_v1(state, next_stage=stage, evidence=evidence)
        return state

    def test_public_authority_is_exact_and_normal_only(self) -> None:
        self.assertEqual(PUBLIC_DATA_AUTHORITY_HASH, self.authority.authority_hash)
        self.assertEqual(37, len(self.authority.feature_order))
        self.assertEqual(144, len(PAIR_UNIVERSE))
        self.assertEqual(EXP01_SCIENTIFIC_CONTRACT_HASH, self.authority.contract_hash)
        self.assertFalse(self.authority.labels_authorized)
        with self.assertRaises(Exp01ScientificContractError):
            dataclasses.replace(self.authority, test1_authorized=True, authority_hash="")

    def test_view_cannot_substitute_authority_even_with_rehash(self) -> None:
        with self.assertRaisesRegex(Exp01ScientificContractError, "stale or foreign"):
            build_view_receipt_v1(
                view_id=ViewId.COMBINED, authority_hash="a" * 64,
                materialized_input_hash="b" * 64,
            )

    def test_seed_authority_freezes_backend_config_and_neighbor_policy(self) -> None:
        seed = self.seeds[0]
        self.assertEqual(PREREGISTRATION_HASH, seed.preregistration_hash)
        self.assertEqual(TRAINING_CONFIG_HASH, seed.training_config_hash)
        self.assertEqual(UPSTREAM_GDN_COMMIT, seed.upstream_commit)
        self.assertEqual(BACKEND_CLASSIFICATION, seed.backend_classification)
        self.assertEqual(FROZEN_NEIGHBOR_POLICY_HASH, seed.neighbor_policy_hash)
        corrected = next(item for item in self.seeds if item.arm_id == ArmId.CORRECTED_SELF_EXCLUDED.value)
        self.assertEqual(CORRECTED_NEIGHBOR_POLICY_HASH, corrected.neighbor_policy_hash)
        with self.assertRaisesRegex(Exp01ScientificContractError, "authority changed"):
            dataclasses.replace(corrected.backend_receipt, training_config_hash="9" * 64, receipt_hash="")

    def test_seed_graph_is_exact_top5_and_corrected_excludes_self(self) -> None:
        corrected = next(item for item in self.seeds if item.arm_id == ArmId.CORRECTED_SELF_EXCLUDED.value)
        self.assertEqual(37 * 5, len(corrected.graph_edges))
        self.assertFalse(any(source == target for source, target in corrected.graph_edges))
        with self.assertRaisesRegex(Exp01ScientificContractError, "graph identities"):
            dataclasses.replace(corrected.backend_receipt, extraction_graph_hash="9" * 64, receipt_hash="")
        self.assertNotIn("graph_edges", corrected.to_dict())
        self.assertNotIn("graph_edges", corrected.backend_receipt.to_dict())

    def test_checkpoint_set_requires_exact_typed_views_and_schedule(self) -> None:
        self.assertEqual(3, len(self.checkpoints.view_receipts))
        self.assertEqual(12, len(self.checkpoints.seed_receipts))
        with self.assertRaisesRegex(Exp01ScientificContractError, "exactly three"):
            build_checkpoint_set_receipt_v1(
                authority_hash=self.authority.authority_hash,
                view_receipts=(*self.views, self.views[0]), seed_receipts=self.seeds,
            )
        with self.assertRaisesRegex(Exp01ScientificContractError, "exact ordered"):
            build_checkpoint_set_receipt_v1(
                authority_hash=self.authority.authority_hash,
                view_receipts=self.views, seed_receipts=tuple(reversed(self.seeds)),
            )
        fake_views = tuple(SimpleNamespace(**item.__dict__) for item in self.views)
        with self.assertRaisesRegex(Exp01ScientificContractError, "exact typed"):
            build_checkpoint_set_receipt_v1(
                authority_hash=self.authority.authority_hash,
                view_receipts=fake_views, seed_receipts=self.seeds,
            )

    def test_aggregate_requires_typed_checkpoint_and_unpadded_prefixes(self) -> None:
        aggregate = build_candidate_aggregate_receipt_v1(
            arm_id=ArmId.CORRECTED_SELF_EXCLUDED, view_id=ViewId.COMBINED,
            checkpoint_set=self.checkpoints,
        )
        self.assertEqual(
            (min(10, len(aggregate.ranked_pairs)), min(20, len(aggregate.ranked_pairs)), min(40, len(aggregate.ranked_pairs))),
            (len(aggregate.top10), len(aggregate.top20), len(aggregate.top40)),
        )
        with self.assertRaises(Exp01ScientificContractError):
            dataclasses.replace(aggregate, top10=aggregate.top10[:-1], receipt_hash="")
        with self.assertRaisesRegex(Exp01ScientificContractError, "staged checkpoint|does not replay"):
            build_candidate_aggregate_receipt_v1(
                arm_id=ArmId.CORRECTED_SELF_EXCLUDED, view_id=ViewId.COMBINED,
                checkpoint_set=self.checkpoints, ranked_pairs=tuple(reversed(aggregate.ranked_pairs)),
            )

    def test_empty_candidate_ranking_is_explicit_and_unpadded(self) -> None:
        source_names = {source for source, _ in PAIR_UNIVERSE}
        empty_edges = tuple(
            (source, target)
            for target in P1_FEATURE_ORDER
            for source in tuple(name for name in P1_FEATURE_ORDER if name not in source_names and name != target)[:5]
        )
        empty_backends = tuple(
            build_backend_execution_receipt_v1(
                arm_id=arm, seed=seed,
                view_receipt=next(item for item in self.views if item.view_id == view),
                checkpoint_hash=stable_hash_v1({"empty_checkpoint": [arm, view, seed]}),
                graph_edges=empty_edges,
            ) for arm, view, seed in EXPECTED_SCHEDULE
        )
        empty_checkpoints = build_checkpoint_set_receipt_v1(
            authority_hash=self.authority.authority_hash,
            view_receipts=self.views,
            seed_receipts=tuple(build_seed_projection_v1(backend_receipt=item) for item in empty_backends),
        )
        empty = build_candidate_aggregate_receipt_v1(
            arm_id=ArmId.CORRECTED_SELF_EXCLUDED, view_id=ViewId.COMBINED,
            checkpoint_set=empty_checkpoints,
        )
        self.assertEqual((), empty.top10)
        self.assertTrue(empty.to_dict()["empty_outcome"])
        empty_aggregates = tuple(
            build_candidate_aggregate_receipt_v1(
                arm_id=ArmId(arm), view_id=ViewId(view), checkpoint_set=empty_checkpoints,
            ) for arm, view in EXPECTED_AGGREGATES
        )
        empty_union = build_candidate_union_authority_v1(candidate_aggregates=empty_aggregates)
        submission = build_profiling_submission_v1(candidate_union=empty_union)
        confirmation = build_confirmation_receipt_v1(
            candidate_union=empty_union,
            submission=submission, decision_ledger_hash="a" * 64,
            confirmed_pairs=(), rejected_pairs=(),
        )
        self.assertEqual(0, confirmation.candidate_count)

    def test_profiling_is_one_arm_blind_union(self) -> None:
        submission = self.submission
        expected = tuple(pair for pair in PAIR_UNIVERSE if any(pair in aggregate.top20 for aggregate in self.aggregates))
        self.assertEqual(expected, submission.candidate_pairs)
        self.assertFalse(submission.arm_identity_exposed)
        mutated = dataclasses.replace(submission, candidate_pairs=PAIR_UNIVERSE[20:21], submission_hash="")
        mutated = dataclasses.replace(mutated, submission_hash=stable_hash_v1(mutated.to_dict(include_hash=False)))
        with self.assertRaisesRegex(Exp01ScientificContractError, "does not replay"):
            build_confirmation_receipt_v1(
                candidate_union=self.candidate_union, submission=mutated,
                decision_ledger_hash="a" * 64, confirmed_pairs=mutated.candidate_pairs, rejected_pairs=(),
            )

    def test_confirmation_partition_and_count_replay_submission(self) -> None:
        confirmation = self.confirmation
        self.assertEqual(len(confirmation.submission.candidate_pairs), confirmation.candidate_count)
        with self.assertRaisesRegex(Exp01ScientificContractError, "count"):
            dataclasses.replace(confirmation, candidate_count=19, receipt_hash="")
        with self.assertRaisesRegex(Exp01ScientificContractError, "partition"):
            dataclasses.replace(confirmation, confirmed_pairs=(), rejected_pairs=(), receipt_hash="")

    def test_mask_intervention_proves_exact_removal_without_refill(self) -> None:
        receipt = self.interventions[0]
        self.assertEqual(0, receipt.added_edge_count)
        self.assertFalse(receipt.refill_performed)
        self.assertEqual(set(receipt.intervened_graph_edges), set(receipt.baseline_graph_edges) - set(receipt.primary_mask_pairs))
        with self.assertRaisesRegex(Exp01ScientificContractError, "exact removal"):
            dataclasses.replace(receipt, intervened_graph_edges=receipt.baseline_graph_edges, receipt_hash="")
        reordered = tuple(reversed(receipt.intervened_graph_edges))
        with self.assertRaisesRegex(Exp01ScientificContractError, "exact removal"):
            dataclasses.replace(receipt, intervened_graph_edges=reordered, receipt_hash="")

    def test_empty_mask_has_explicit_not_applicable_status(self) -> None:
        seed = next(
            item for item in self.seeds
            if item.arm_id == ArmId.CORRECTED_SELF_EXCLUDED.value
            and item.view_id == ViewId.COMBINED.value and item.seed == SEEDS[0]
        )
        receipt = build_mask_intervention_receipt_v1(
            corrected_seed_receipt=seed, checkpoint_set=self.checkpoints,
            primary_mask_pairs=(), baseline_graph_edges=self.edges,
            intervened_graph_edges=self.edges,
            baseline_metric_hash="a" * 64, intervention_metric_hash="a" * 64,
        )
        self.assertEqual("NOT_APPLICABLE_EMPTY_PRIMARY_MASK", receipt.intervention_status)
        with self.assertRaisesRegex(Exp01ScientificContractError, "preserve"):
            dataclasses.replace(receipt, intervention_metric_hash="b" * 64, receipt_hash="")

    def test_mask_intervention_rejects_foreign_seed_and_mask(self) -> None:
        frozen_seed = next(item for item in self.seeds if item.arm_id == ArmId.FROZEN_SELF_ELIGIBLE.value)
        with self.assertRaisesRegex(Exp01ScientificContractError, "corrected combined"):
            dataclasses.replace(self.interventions[0], corrected_seed_receipt=frozen_seed, receipt_hash="")
        with self.assertRaisesRegex(Exp01ScientificContractError, "nonexistent"):
            dataclasses.replace(self.interventions[0], primary_mask_pairs=(PAIR_UNIVERSE[-1],), receipt_hash="")

    def test_stage_machine_requires_typed_evidence_not_arbitrary_hashes(self) -> None:
        state = initial_stage_state_v1()
        with self.assertRaisesRegex(Exp01ScientificContractError, "typed authority"):
            advance_stage_v1(state, next_stage=Stage.AUTHORITY_BOUND, evidence="a" * 64)
        state = advance_stage_v1(state, next_stage=Stage.AUTHORITY_BOUND, evidence=self.authority)
        with self.assertRaisesRegex(Exp01ScientificContractError, "out of order"):
            advance_stage_v1(state, next_stage=Stage.SEEDS_COMPLETED, evidence=self.checkpoints)

    def test_mask_stage_requires_exact_seeds_and_shared_mask(self) -> None:
        state = initial_stage_state_v1()
        for stage, evidence in (
            (Stage.AUTHORITY_BOUND, self.authority), (Stage.VIEWS_MATERIALIZED, self.views),
            (Stage.SEEDS_COMPLETED, self.checkpoints), (Stage.CANDIDATES_AGGREGATED, self.aggregates),
            (Stage.PROFILING_CONFIRMED, self.confirmation),
        ):
            state = advance_stage_v1(state, next_stage=stage, evidence=evidence)
        with self.assertRaisesRegex(Exp01ScientificContractError, "exact seeds"):
            advance_stage_v1(
                state, next_stage=Stage.MASK_INTERVENTION_COMPLETED,
                evidence=(self.interventions[0], self.interventions[0], self.interventions[2]),
            )

    def test_stage_rejects_candidate_and_mask_predecessor_substitution(self) -> None:
        alternate_backends = tuple(
            build_backend_execution_receipt_v1(
                arm_id=arm, seed=seed,
                view_receipt=next(item for item in self.views if item.view_id == view),
                checkpoint_hash=stable_hash_v1({"alternate": [arm, view, seed]}),
                graph_edges=self.edges,
            ) for arm, view, seed in EXPECTED_SCHEDULE
        )
        alternate_checkpoints = build_checkpoint_set_receipt_v1(
            authority_hash=self.authority.authority_hash, view_receipts=self.views,
            seed_receipts=tuple(build_seed_projection_v1(backend_receipt=item) for item in alternate_backends),
        )
        alternate_aggregates = tuple(
            build_candidate_aggregate_receipt_v1(
                arm_id=ArmId(arm), view_id=ViewId(view), checkpoint_set=alternate_checkpoints,
            ) for arm, view in EXPECTED_AGGREGATES
        )
        state = initial_stage_state_v1()
        for stage, evidence in (
            (Stage.AUTHORITY_BOUND, self.authority), (Stage.VIEWS_MATERIALIZED, self.views),
            (Stage.SEEDS_COMPLETED, self.checkpoints),
        ):
            state = advance_stage_v1(state, next_stage=stage, evidence=evidence)
        with self.assertRaisesRegex(Exp01ScientificContractError, "staged checkpoint"):
            advance_stage_v1(state, next_stage=Stage.CANDIDATES_AGGREGATED, evidence=alternate_aggregates)

    def test_final_handoff_replays_complete_typed_lineage(self) -> None:
        handoff = build_inclusion_evidence_handoff_v1(
            final_state=self.stage_through_mask(), authority=self.authority,
            checkpoint_set=self.checkpoints, candidate_aggregates=self.aggregates,
            confirmation=self.confirmation, interventions=self.interventions,
            inclusion_evidence_hash="d" * 64,
        )
        self.assertFalse(handoff.scientific_result_claimed)
        self.assertEqual(handoff.handoff_hash, stable_hash_v1(handoff.to_dict(include_hash=False)))
        ready = advance_stage_v1(
            self.stage_through_mask(), next_stage=Stage.INCLUSION_HANDOFF_READY, evidence=handoff,
        )
        self.assertEqual(Stage.INCLUSION_HANDOFF_READY.value, ready.stage)

    def test_final_handoff_rejects_duplicate_or_unbound_lineage(self) -> None:
        with self.assertRaises(Exp01ScientificContractError):
            build_inclusion_evidence_handoff_v1(
                final_state=self.stage_through_mask(), authority=self.authority,
                checkpoint_set=self.checkpoints,
                candidate_aggregates=(self.aggregates[0], self.aggregates[0], *self.aggregates[2:]),
                confirmation=self.confirmation, interventions=self.interventions,
                inclusion_evidence_hash="d" * 64,
            )
        with self.assertRaises(Exp01ScientificContractError):
            dataclasses.replace(
                build_inclusion_evidence_handoff_v1(
                    final_state=self.stage_through_mask(), authority=self.authority,
                    checkpoint_set=self.checkpoints, candidate_aggregates=self.aggregates,
                    confirmation=self.confirmation, interventions=self.interventions,
                    inclusion_evidence_hash="d" * 64,
                ),
                candidate_aggregate_hashes=(*tuple(item.receipt_hash for item in self.aggregates), "e" * 64),
                handoff_hash="",
            )

    def test_handoff_replays_chain_and_rejects_coordinated_forged_state(self) -> None:
        alternate_backends = tuple(
            build_backend_execution_receipt_v1(
                arm_id=arm, seed=seed,
                view_receipt=next(item for item in self.views if item.view_id == view),
                checkpoint_hash=stable_hash_v1({"forged_checkpoint": [arm, view, seed]}),
                graph_edges=self.edges,
            ) for arm, view, seed in EXPECTED_SCHEDULE
        )
        alternate_checkpoints = build_checkpoint_set_receipt_v1(
            authority_hash=self.authority.authority_hash, view_receipts=self.views,
            seed_receipts=tuple(build_seed_projection_v1(backend_receipt=item) for item in alternate_backends),
        )
        alternate_aggregates = tuple(
            build_candidate_aggregate_receipt_v1(
                arm_id=ArmId(arm), view_id=ViewId(view), checkpoint_set=alternate_checkpoints,
            ) for arm, view in EXPECTED_AGGREGATES
        )
        alternate_union = build_candidate_union_authority_v1(candidate_aggregates=alternate_aggregates)
        alternate_submission = build_profiling_submission_v1(candidate_union=alternate_union)
        alternate_confirmation = build_confirmation_receipt_v1(
            candidate_union=alternate_union, submission=alternate_submission,
            decision_ledger_hash="b" * 64,
            confirmed_pairs=alternate_submission.candidate_pairs, rejected_pairs=(),
        )
        mixed_hashes = (
            self.authority.authority_hash,
            stable_hash_v1({"view_receipt_hashes": list(self.checkpoints.view_receipt_hashes)}),
            self.checkpoints.receipt_hash,
            stable_hash_v1({"candidate_aggregate_hashes": [item.receipt_hash for item in alternate_aggregates]}),
            alternate_confirmation.receipt_hash,
            stable_hash_v1({"intervention_receipt_hashes": [item.receipt_hash for item in self.interventions]}),
        )
        forged = StageStateV1(
            stage=Stage.MASK_INTERVENTION_COMPLETED.value,
            completed_receipt_hashes=mixed_hashes, previous_state_hash="f" * 64,
        )
        forged = dataclasses.replace(forged, state_hash=stable_hash_v1(forged.to_dict(include_hash=False)))
        with self.assertRaisesRegex(Exp01ScientificContractError, "staged checkpoint|does not replay"):
            build_inclusion_evidence_handoff_v1(
                final_state=forged, authority=self.authority,
                checkpoint_set=self.checkpoints, candidate_aggregates=alternate_aggregates,
                confirmation=alternate_confirmation, interventions=self.interventions,
                inclusion_evidence_hash="d" * 64,
            )

    def test_no_prohibited_access_is_authorized(self) -> None:
        self.assertFalse(self.authority.test1_authorized)
        self.assertFalse(self.authority.test2_authorized)
        self.assertFalse(self.authority.heldout_authorized)
        self.assertTrue(all(not item.labels_accessed and not item.test_accessed for item in self.seeds))


if __name__ == "__main__":
    unittest.main()
