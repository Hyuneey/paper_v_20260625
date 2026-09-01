"""Single-runner orchestration for the frozen 12-run EXP-01 matrix."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from paperworks.gdn.exp01_upstream_backend_v2 import (
    evaluate_fixed_checkpoint_mse_v2,
    replay_exp01_checkpoint_graph_v2,
    train_exp01_seed_v2,
)
from paperworks.gdn.upstream_candidate_backend_v1 import UpstreamGDNTrainingConfigV1
from paperworks.validation_v2.exp01_checkpoint_v2 import (
    Exp01CheckpointReceiptV2,
    persist_private_checkpoint_v2,
    recover_existing_private_checkpoint_v2,
    reopen_private_checkpoint_v2,
)
from paperworks.validation_v2.exp01_relation_confirmation_v2 import (
    ConfirmationEvaluatorV2,
    confirm_candidate_union_arm_blind_v2,
)
from paperworks.validation_v2.exp01_scientific_v1 import (
    ArmId,
    CandidateAggregateReceiptV1,
    CheckpointSetReceiptV1,
    EXPECTED_AGGREGATES,
    EXPECTED_SCHEDULE,
    EXP01_SCIENTIFIC_CONTRACT_HASH,
    FROZEN_NEIGHBOR_POLICY_HASH,
    CORRECTED_NEIGHBOR_POLICY_HASH,
    PAIR_UNIVERSE,
    PUBLIC_DATA_AUTHORITY_HASH,
    SEEDS,
    Stage,
    ViewId,
    advance_stage_v1,
    build_backend_execution_receipt_v1,
    build_candidate_aggregate_receipt_v1,
    build_candidate_union_authority_v1,
    build_checkpoint_set_receipt_v1,
    build_inclusion_evidence_handoff_v1,
    build_mask_intervention_receipt_v1,
    build_public_data_authority_v1,
    build_seed_projection_v1,
    build_view_receipt_v1,
    initial_stage_state_v1,
)
from paperworks.v6.common import require_sha256, stable_hash_v1


class Exp01ExecutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class Exp01ViewInputV2:
    view_id: ViewId
    segments: tuple[Any, ...]
    read_receipt_hashes: tuple[str, ...]

    def __post_init__(self) -> None:
        expected = {
            ViewId.COMBINED: 2, ViewId.TRAIN1_ONLY: 1, ViewId.TRAIN2_ONLY: 1,
        }[self.view_id]
        if len(self.segments) != expected or len(self.read_receipt_hashes) != expected:
            raise Exp01ExecutionError("view does not preserve exact file-local segment count")
        for value in self.read_receipt_hashes:
            require_sha256(value, "read_receipt_hash")


@dataclass(frozen=True)
class Exp01ExecutionResultV2:
    checkpoint_set: CheckpointSetReceiptV1
    aggregates: tuple[CandidateAggregateReceiptV1, ...]
    confirmation_receipt_hash: str
    primary_mask_pairs: tuple[tuple[str, str], ...]
    intervention_receipt_hashes: tuple[str, str, str]
    checkpoint_receipts: tuple[Exp01CheckpointReceiptV2, ...]
    inclusion_handoff_hash: str
    access_counters: Mapping[str, int]
    result_hash: str

    def public_document(self) -> dict[str, object]:
        return {
            "schema": "paperworks.validation_v2.exp01_execution_public_receipt_v2",
            "schema_version": "2.0.0",
            "status": "COMPLETE_PENDING_INDEPENDENT_QA",
            "contract_hash": EXP01_SCIENTIFIC_CONTRACT_HASH,
            "schedule": [list(row) for row in EXPECTED_SCHEDULE],
            "checkpoint_set_hash": self.checkpoint_set.receipt_hash,
            "candidate_aggregate_hashes": [item.receipt_hash for item in self.aggregates],
            "confirmation_receipt_hash": self.confirmation_receipt_hash,
            "primary_mask_pair_set_hash": stable_hash_v1({"pairs": self.primary_mask_pairs}),
            "primary_mask_pair_count": len(self.primary_mask_pairs),
            "intervention_receipt_hashes": list(self.intervention_receipt_hashes),
            "private_checkpoint_receipt_hashes": [item.receipt_hash for item in self.checkpoint_receipts],
            "inclusion_handoff_hash": self.inclusion_handoff_hash,
            "access_counters": dict(self.access_counters),
            "claim_boundary": "NORMAL_DATA_CANDIDATE_GUIDANCE_NOT_CAUSALITY_OR_DETECTION_PERFORMANCE",
            "redaction": "NO_PRIVATE_PATHS_VALUES_SCORES_LOSSES_OR_CHECKPOINT_BYTES",
            "result_hash": self.result_hash,
        }


def _view_hash(view: Exp01ViewInputV2) -> str:
    return stable_hash_v1(
        {
            "view_id": view.view_id.value,
            "read_receipt_hashes": view.read_receipt_hashes,
            "segment_row_counts": [len(segment) for segment in view.segments],
            "file_local": True,
        }
    )


def _primary_mask(
    *,
    checkpoint_set: CheckpointSetReceiptV1,
    aggregates: tuple[CandidateAggregateReceiptV1, ...],
    confirmed_pairs: Sequence[tuple[str, str]],
    meta_top20: Sequence[tuple[str, str]],
    stat_top20: Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    by_key = {(item.arm_id, item.view_id): item for item in aggregates}
    combined = by_key[(ArmId.CORRECTED_SELF_EXCLUDED.value, ViewId.COMBINED.value)]
    train1 = by_key[(ArmId.CORRECTED_SELF_EXCLUDED.value, ViewId.TRAIN1_ONLY.value)]
    train2 = by_key[(ArmId.CORRECTED_SELF_EXCLUDED.value, ViewId.TRAIN2_ONLY.value)]
    corrected_seeds = tuple(
        item for item in checkpoint_set.seed_receipts
        if item.arm_id == ArmId.CORRECTED_SELF_EXCLUDED.value and item.view_id == ViewId.COMBINED.value
    )
    if tuple(item.seed for item in corrected_seeds) != SEEDS:
        raise Exp01ExecutionError("corrected combined seed set is incomplete")
    confirmed = set(confirmed_pairs)
    comparator = set(meta_top20) | set(stat_top20)
    split_stable = set(train1.top20) & set(train2.top20)
    stable = {
        pair for pair in combined.top20
        if sum(pair in seed.graph_edges for seed in corrected_seeds) >= 2
    }
    primary = tuple(
        pair for pair in combined.top20
        if pair not in comparator and pair in split_stable and pair in stable and pair in confirmed
    )
    # The frozen intervention receipt requires one common mask to exist in all
    # three fixed graphs.  Never silently narrow a 2/3-stable scientific mask.
    if any(not set(primary).issubset(set(seed.graph_edges)) for seed in corrected_seeds):
        raise Exp01ExecutionError(
            "EXP01_FROZEN_CONTRACT_CONFLICT_PRIMARY_MASK_2_OF_3_VS_SHARED_ALL_SEEDS"
        )
    return primary


def execute_exp01_matrix_v2(
    *,
    views: Mapping[ViewId, Exp01ViewInputV2],
    train4_provider: Callable[[], tuple[tuple[Any, ...], str]],
    feature_order: Sequence[str],
    private_checkpoint_root: Path,
    code_authority_hash: str,
    confirmation_evaluator: ConfirmationEvaluatorV2,
    meta_top20: Sequence[tuple[str, str]],
    stat_top20: Sequence[tuple[str, str]],
    config: UpstreamGDNTrainingConfigV1 | None = None,
) -> Exp01ExecutionResultV2:
    """Execute the exact schedule sequentially, then confirm and intervene."""

    require_sha256(code_authority_hash, "code_authority_hash")
    if tuple(views) != (ViewId.COMBINED, ViewId.TRAIN1_ONLY, ViewId.TRAIN2_ONLY):
        raise Exp01ExecutionError("exact combined/train1/train2 view order is required")
    feature_tuple = tuple(feature_order)
    if len(feature_tuple) != 37 or len(set(feature_tuple)) != 37:
        raise Exp01ExecutionError("exact 37-feature context is required")
    if len(meta_top20) != 20 or len(stat_top20) != 20:
        raise Exp01ExecutionError("exact unpadded META and STAT Top-20 references are required")
    if any(pair not in PAIR_UNIVERSE for pair in (*meta_top20, *stat_top20)):
        raise Exp01ExecutionError("comparator pair lies outside frozen universe")
    training_config = config or UpstreamGDNTrainingConfigV1()
    authority = build_public_data_authority_v1()
    view_receipts = tuple(
        build_view_receipt_v1(
            view_id=view_id,
            authority_hash=authority.authority_hash,
            materialized_input_hash=_view_hash(views[view_id]),
        )
        for view_id in (ViewId.COMBINED, ViewId.TRAIN1_ONLY, ViewId.TRAIN2_ONLY)
    )
    receipt_by_view = {ViewId(item.view_id): item for item in view_receipts}
    checkpoint_receipts: list[Exp01CheckpointReceiptV2] = []
    checkpoint_paths: dict[tuple[str, str, int], Path] = {}
    seed_projections = []
    for order, (arm_value, view_value, seed) in enumerate(EXPECTED_SCHEDULE, start=1):
        arm = ArmId(arm_value)
        view_id = ViewId(view_value)
        trained = train_exp01_seed_v2(
            arm_id=arm,
            segments=views[view_id].segments,
            feature_order=feature_tuple,
            candidate_pairs=PAIR_UNIVERSE,
            seed=seed,
            config=training_config,
        )
        run_id = f"run_{order:02d}_{arm.value}_{view_id.value}_seed_{seed}"
        checkpoint_path, checkpoint = persist_private_checkpoint_v2(
            private_root=private_checkpoint_root,
            run_id=run_id,
            arm_id=arm.value,
            view_id=view_id.value,
            seed=seed,
            code_authority_hash=code_authority_hash,
            training_config_hash=training_config.hyperparameter_hash,
            state_dict=trained.best_state_dict,
        )
        checkpoint_receipts.append(checkpoint)
        checkpoint_paths[(arm.value, view_id.value, seed)] = checkpoint_path
        backend = build_backend_execution_receipt_v1(
            arm_id=arm.value,
            view_receipt=receipt_by_view[view_id],
            seed=seed,
            checkpoint_hash=checkpoint.state_hash,
            graph_edges=trained.graph_edges,
            forward_graph_hash=trained.forward_graph_hash,
            extraction_graph_hash=trained.extraction_graph_hash,
            neighbor_policy_hash=(
                FROZEN_NEIGHBOR_POLICY_HASH
                if arm is ArmId.FROZEN_SELF_ELIGIBLE else CORRECTED_NEIGHBOR_POLICY_HASH
            ),
        )
        seed_projections.append(build_seed_projection_v1(backend_receipt=backend))
    checkpoint_set = build_checkpoint_set_receipt_v1(
        authority_hash=PUBLIC_DATA_AUTHORITY_HASH,
        view_receipts=view_receipts,
        seed_receipts=tuple(seed_projections),
    )
    aggregates = tuple(
        build_candidate_aggregate_receipt_v1(
            arm_id=ArmId(arm), view_id=ViewId(view), checkpoint_set=checkpoint_set,
        )
        for arm, view in EXPECTED_AGGREGATES
    )
    candidate_union = build_candidate_union_authority_v1(candidate_aggregates=aggregates)
    _, confirmation, confirmation_outcome = confirm_candidate_union_arm_blind_v2(
        candidate_union=candidate_union, evaluator=confirmation_evaluator,
    )
    primary_mask = _primary_mask(
        checkpoint_set=checkpoint_set,
        aggregates=aggregates,
        confirmed_pairs=confirmation.confirmed_pairs,
        meta_top20=meta_top20,
        stat_top20=stat_top20,
    )
    train4_segments, train4_read_receipt_hash = train4_provider()
    if len(train4_segments) != 1:
        raise Exp01ExecutionError("train4 must be one file-local segment")
    require_sha256(train4_read_receipt_hash, "train4_read_receipt_hash")
    corrected_combined = tuple(
        item for item in checkpoint_set.seed_receipts
        if item.arm_id == ArmId.CORRECTED_SELF_EXCLUDED.value and item.view_id == ViewId.COMBINED.value
    )
    interventions = []
    numeric_private = []
    for seed_receipt in corrected_combined:
        checkpoint_index = EXPECTED_SCHEDULE.index(
            (seed_receipt.arm_id, seed_receipt.view_id, seed_receipt.seed)
        )
        checkpoint_receipt = checkpoint_receipts[checkpoint_index]
        payload = reopen_private_checkpoint_v2(
            checkpoint_paths[(seed_receipt.arm_id, seed_receipt.view_id, seed_receipt.seed)],
            expected_receipt=checkpoint_receipt,
        )
        baseline = evaluate_fixed_checkpoint_mse_v2(
            arm_id=ArmId.CORRECTED_SELF_EXCLUDED,
            state_dict=payload["state_dict"],
            segments=train4_segments,
            feature_order=feature_tuple,
            graph_edges=seed_receipt.graph_edges,
            config=training_config,
        )
        intervened_edges = tuple(edge for edge in seed_receipt.graph_edges if edge not in set(primary_mask))
        masked = (
            evaluate_fixed_checkpoint_mse_v2(
                arm_id=ArmId.CORRECTED_SELF_EXCLUDED,
                state_dict=payload["state_dict"],
                segments=train4_segments,
                feature_order=feature_tuple,
                graph_edges=intervened_edges,
                config=training_config,
            )
            if primary_mask else baseline
        )
        baseline_hash = stable_hash_v1(
            {"seed": seed_receipt.seed, "metric": "MSE", "value": baseline,
             "train4_read_receipt_hash": train4_read_receipt_hash}
        )
        intervention_hash = (
            stable_hash_v1(
                {"seed": seed_receipt.seed, "metric": "MSE", "value": masked,
                 "train4_read_receipt_hash": train4_read_receipt_hash,
                 "primary_mask_pair_set_hash": stable_hash_v1({"pairs": primary_mask})}
            )
            if primary_mask else baseline_hash
        )
        interventions.append(build_mask_intervention_receipt_v1(
            corrected_seed_receipt=seed_receipt,
            checkpoint_set=checkpoint_set,
            primary_mask_pairs=primary_mask,
            baseline_graph_edges=seed_receipt.graph_edges,
            intervened_graph_edges=intervened_edges,
            baseline_metric_hash=baseline_hash,
            intervention_metric_hash=intervention_hash,
        ))
        numeric_private.append((seed_receipt.seed, baseline, masked, masked - baseline))
    stage = initial_stage_state_v1()
    for next_stage, evidence in (
        (Stage.AUTHORITY_BOUND, authority),
        (Stage.VIEWS_MATERIALIZED, view_receipts),
        (Stage.SEEDS_COMPLETED, checkpoint_set),
        (Stage.CANDIDATES_AGGREGATED, aggregates),
        (Stage.PROFILING_CONFIRMED, confirmation),
        (Stage.MASK_INTERVENTION_COMPLETED, tuple(interventions)),
    ):
        stage = advance_stage_v1(stage, next_stage=next_stage, evidence=evidence)
    inclusion_evidence_hash = stable_hash_v1(
        {"primary_mask_pairs": primary_mask, "private_train4_metrics": numeric_private}
    )
    handoff = build_inclusion_evidence_handoff_v1(
        final_state=stage,
        authority=authority,
        checkpoint_set=checkpoint_set,
        candidate_aggregates=aggregates,
        confirmation=confirmation,
        interventions=tuple(interventions),
        inclusion_evidence_hash=inclusion_evidence_hash,
    )
    counters = {
        "train1_opens": 1, "train2_opens": 1,
        "train3_opens": confirmation_outcome.train3_open_count, "train4_opens": 1,
        "test1_accesses": 0, "test2_accesses": 0, "heldout_accesses": 0,
        "label_accesses": 0, "provider_calls": 0,
    }
    result_hash = stable_hash_v1(
        {
            "checkpoint_set_hash": checkpoint_set.receipt_hash,
            "aggregate_hashes": [item.receipt_hash for item in aggregates],
            "confirmation_hash": confirmation.receipt_hash,
            "intervention_hashes": [item.receipt_hash for item in interventions],
            "handoff_hash": handoff.handoff_hash,
            "access_counters": counters,
        }
    )
    return Exp01ExecutionResultV2(
        checkpoint_set=checkpoint_set,
        aggregates=aggregates,
        confirmation_receipt_hash=confirmation.receipt_hash,
        primary_mask_pairs=primary_mask,
        intervention_receipt_hashes=tuple(item.receipt_hash for item in interventions),  # type: ignore[arg-type]
        checkpoint_receipts=tuple(checkpoint_receipts),
        inclusion_handoff_hash=handoff.handoff_hash,
        access_counters=counters,
        result_hash=result_hash,
    )


def resume_exp01_postprocessing_v2(
    *,
    views: Mapping[ViewId, Exp01ViewInputV2],
    train4_provider: Callable[[], tuple[tuple[Any, ...], str]],
    feature_order: Sequence[str],
    private_checkpoint_root: Path,
    checkpoint_origin_code_hash: str,
    confirmation_evaluator: ConfirmationEvaluatorV2,
    meta_top20: Sequence[tuple[str, str]],
    stat_top20: Sequence[tuple[str, str]],
    config: UpstreamGDNTrainingConfigV1 | None = None,
) -> Exp01ExecutionResultV2:
    """Resume only the post-training stages from twelve verified checkpoints."""

    require_sha256(checkpoint_origin_code_hash, "checkpoint_origin_code_hash")
    if tuple(views) != (ViewId.COMBINED, ViewId.TRAIN1_ONLY, ViewId.TRAIN2_ONLY):
        raise Exp01ExecutionError("exact combined/train1/train2 view order is required")
    feature_tuple = tuple(feature_order)
    if len(feature_tuple) != 37 or len(set(feature_tuple)) != 37:
        raise Exp01ExecutionError("exact 37-feature context is required")
    if len(meta_top20) != 20 or len(stat_top20) != 20:
        raise Exp01ExecutionError("exact unpadded META and STAT Top-20 references are required")
    if any(pair not in PAIR_UNIVERSE for pair in (*meta_top20, *stat_top20)):
        raise Exp01ExecutionError("comparator pair lies outside frozen universe")
    training_config = config or UpstreamGDNTrainingConfigV1()
    authority = build_public_data_authority_v1()
    view_receipts = tuple(
        build_view_receipt_v1(
            view_id=view_id,
            authority_hash=authority.authority_hash,
            materialized_input_hash=_view_hash(views[view_id]),
        )
        for view_id in (ViewId.COMBINED, ViewId.TRAIN1_ONLY, ViewId.TRAIN2_ONLY)
    )
    receipt_by_view = {ViewId(item.view_id): item for item in view_receipts}
    checkpoint_receipts: list[Exp01CheckpointReceiptV2] = []
    checkpoint_payloads: dict[tuple[str, str, int], Mapping[str, Any]] = {}
    seed_projections = []
    expected_names = set()
    for order, (arm_value, view_value, seed) in enumerate(EXPECTED_SCHEDULE, start=1):
        arm = ArmId(arm_value)
        view_id = ViewId(view_value)
        run_id = f"run_{order:02d}_{arm.value}_{view_id.value}_seed_{seed}"
        expected_names.add(f"{run_id}.pt")
        _, checkpoint, payload = recover_existing_private_checkpoint_v2(
            private_root=private_checkpoint_root,
            run_id=run_id,
            arm_id=arm.value,
            view_id=view_id.value,
            seed=seed,
            expected_code_authority_hash=checkpoint_origin_code_hash,
            expected_training_config_hash=training_config.hyperparameter_hash,
        )
        replay = replay_exp01_checkpoint_graph_v2(
            arm_id=arm,
            state_dict=payload["state_dict"],
            segments=views[view_id].segments,
            feature_order=feature_tuple,
            candidate_pairs=PAIR_UNIVERSE,
            seed=seed,
            config=training_config,
        )
        checkpoint_receipts.append(checkpoint)
        key = (arm.value, view_id.value, seed)
        checkpoint_payloads[key] = payload
        backend = build_backend_execution_receipt_v1(
            arm_id=arm.value,
            view_receipt=receipt_by_view[view_id],
            seed=seed,
            checkpoint_hash=checkpoint.state_hash,
            graph_edges=replay.graph_edges,
            forward_graph_hash=replay.forward_graph_hash,
            extraction_graph_hash=replay.extraction_graph_hash,
            neighbor_policy_hash=(
                FROZEN_NEIGHBOR_POLICY_HASH
                if arm is ArmId.FROZEN_SELF_ELIGIBLE else CORRECTED_NEIGHBOR_POLICY_HASH
            ),
        )
        seed_projections.append(build_seed_projection_v1(backend_receipt=backend))
    actual_names = {path.name for path in private_checkpoint_root.resolve(strict=True).iterdir() if path.is_file()}
    if actual_names != expected_names:
        raise Exp01ExecutionError("checkpoint recovery namespace contains missing, extra, or partial files")

    checkpoint_set = build_checkpoint_set_receipt_v1(
        authority_hash=PUBLIC_DATA_AUTHORITY_HASH,
        view_receipts=view_receipts,
        seed_receipts=tuple(seed_projections),
    )
    aggregates = tuple(
        build_candidate_aggregate_receipt_v1(
            arm_id=ArmId(arm), view_id=ViewId(view), checkpoint_set=checkpoint_set,
        )
        for arm, view in EXPECTED_AGGREGATES
    )
    candidate_union = build_candidate_union_authority_v1(candidate_aggregates=aggregates)
    _, confirmation, confirmation_outcome = confirm_candidate_union_arm_blind_v2(
        candidate_union=candidate_union, evaluator=confirmation_evaluator,
    )
    primary_mask = _primary_mask(
        checkpoint_set=checkpoint_set,
        aggregates=aggregates,
        confirmed_pairs=confirmation.confirmed_pairs,
        meta_top20=meta_top20,
        stat_top20=stat_top20,
    )
    train4_segments, train4_read_receipt_hash = train4_provider()
    if len(train4_segments) != 1:
        raise Exp01ExecutionError("train4 must be one file-local segment")
    require_sha256(train4_read_receipt_hash, "train4_read_receipt_hash")
    corrected_combined = tuple(
        item for item in checkpoint_set.seed_receipts
        if item.arm_id == ArmId.CORRECTED_SELF_EXCLUDED.value and item.view_id == ViewId.COMBINED.value
    )
    interventions = []
    numeric_private = []
    for seed_receipt in corrected_combined:
        key = (seed_receipt.arm_id, seed_receipt.view_id, seed_receipt.seed)
        payload = checkpoint_payloads[key]
        baseline = evaluate_fixed_checkpoint_mse_v2(
            arm_id=ArmId.CORRECTED_SELF_EXCLUDED,
            state_dict=payload["state_dict"],
            segments=train4_segments,
            feature_order=feature_tuple,
            graph_edges=seed_receipt.graph_edges,
            config=training_config,
        )
        intervened_edges = tuple(edge for edge in seed_receipt.graph_edges if edge not in set(primary_mask))
        masked = (
            evaluate_fixed_checkpoint_mse_v2(
                arm_id=ArmId.CORRECTED_SELF_EXCLUDED,
                state_dict=payload["state_dict"],
                segments=train4_segments,
                feature_order=feature_tuple,
                graph_edges=intervened_edges,
                config=training_config,
            )
            if primary_mask else baseline
        )
        baseline_hash = stable_hash_v1(
            {"seed": seed_receipt.seed, "metric": "MSE", "value": baseline,
             "train4_read_receipt_hash": train4_read_receipt_hash}
        )
        intervention_hash = (
            stable_hash_v1(
                {"seed": seed_receipt.seed, "metric": "MSE", "value": masked,
                 "train4_read_receipt_hash": train4_read_receipt_hash,
                 "primary_mask_pair_set_hash": stable_hash_v1({"pairs": primary_mask})}
            )
            if primary_mask else baseline_hash
        )
        interventions.append(build_mask_intervention_receipt_v1(
            corrected_seed_receipt=seed_receipt,
            checkpoint_set=checkpoint_set,
            primary_mask_pairs=primary_mask,
            baseline_graph_edges=seed_receipt.graph_edges,
            intervened_graph_edges=intervened_edges,
            baseline_metric_hash=baseline_hash,
            intervention_metric_hash=intervention_hash,
        ))
        numeric_private.append((seed_receipt.seed, baseline, masked, masked - baseline))
    stage = initial_stage_state_v1()
    for next_stage, evidence in (
        (Stage.AUTHORITY_BOUND, authority),
        (Stage.VIEWS_MATERIALIZED, view_receipts),
        (Stage.SEEDS_COMPLETED, checkpoint_set),
        (Stage.CANDIDATES_AGGREGATED, aggregates),
        (Stage.PROFILING_CONFIRMED, confirmation),
        (Stage.MASK_INTERVENTION_COMPLETED, tuple(interventions)),
    ):
        stage = advance_stage_v1(stage, next_stage=next_stage, evidence=evidence)
    inclusion_evidence_hash = stable_hash_v1(
        {"primary_mask_pairs": primary_mask, "private_train4_metrics": numeric_private}
    )
    handoff = build_inclusion_evidence_handoff_v1(
        final_state=stage,
        authority=authority,
        checkpoint_set=checkpoint_set,
        candidate_aggregates=aggregates,
        confirmation=confirmation,
        interventions=tuple(interventions),
        inclusion_evidence_hash=inclusion_evidence_hash,
    )
    counters = {
        "train1_opens": 1, "train2_opens": 1,
        "train3_opens": confirmation_outcome.train3_open_count, "train4_opens": 1,
        "test1_accesses": 0, "test2_accesses": 0, "heldout_accesses": 0,
        "label_accesses": 0, "provider_calls": 0,
    }
    result_hash = stable_hash_v1(
        {
            "checkpoint_set_hash": checkpoint_set.receipt_hash,
            "aggregate_hashes": [item.receipt_hash for item in aggregates],
            "confirmation_hash": confirmation.receipt_hash,
            "intervention_hashes": [item.receipt_hash for item in interventions],
            "handoff_hash": handoff.handoff_hash,
            "access_counters": counters,
        }
    )
    return Exp01ExecutionResultV2(
        checkpoint_set=checkpoint_set,
        aggregates=aggregates,
        confirmation_receipt_hash=confirmation.receipt_hash,
        primary_mask_pairs=primary_mask,
        intervention_receipt_hashes=tuple(item.receipt_hash for item in interventions),  # type: ignore[arg-type]
        checkpoint_receipts=tuple(checkpoint_receipts),
        inclusion_handoff_hash=handoff.handoff_hash,
        access_counters=counters,
        result_hash=result_hash,
    )


__all__ = [
    "Exp01ExecutionError", "Exp01ExecutionResultV2", "Exp01ViewInputV2",
    "execute_exp01_matrix_v2", "resume_exp01_postprocessing_v2",
]
