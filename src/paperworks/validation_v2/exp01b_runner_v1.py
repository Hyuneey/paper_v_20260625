"""Scientific runner for the separately preregistered EXP-01B experiment.

The runner accepts already-authorized normal-only matrices and never owns a
label, test, or held-out input capability.  Its output is aggregate/sanitized;
private matrices and checkpoint paths are deliberately not serializable.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import csv
import io
import json
import math
import os
from pathlib import Path
import statistics
from typing import Any, Callable, Mapping, Sequence

from paperworks.validation_v2.exp01_relation_confirmation_v2 import (
    ArmBlindRelationExecutionV2,
    fit_and_confirm_arbitrary_union_v2,
)
from paperworks.validation_v2.exp01_scientific_v1 import (
    PAIR_UNIVERSE,
    SOURCE_VARIABLES,
    TARGET_VARIABLES,
)
from paperworks.validation_v2.exp01b_backend_v1 import (
    Exp01BCheckpointEvidenceV1,
    Exp01BDeviceTrainingConfigV1,
    evaluate_exp01b_checkpoint_v1,
    train_exp01b_seed_v1,
)
from paperworks.validation_v2.exp01b_checkpoint_v1 import (
    Exp01BCheckpointReceiptV1,
    checkpoint_set_receipt_v1,
    persist_private_checkpoint_v1,
)
from paperworks.validation_v2.exp01b_contract_v1 import (
    EVALUATION_BUDGETS,
    PRIMARY_BUDGET,
    Exp01BEnvironmentFreezeV1,
    VIEWS,
)
from paperworks.validation_v2.exp01b_functional_v1 import matched_random_controls_v1
from paperworks.validation_v2.exp01b_ranking_v1 import (
    DispositionEvidenceV1,
    GDNDisposition,
    aggregate_seed_percentiles_v1,
    apply_frozen_disposition_rule_v1,
    deterministic_ranking_v1,
    directional_relation_yield_at_k_v1,
    equal_weight_augmented_scores_v1,
    functional_consensus_v1,
    jaccard_at_k_v1,
    precision_recall_ndcg_at_k_v1,
    ranking_membership_percentiles_v1,
    target_local_percentiles_v1,
)
from paperworks.v6.common import require_sha256, stable_hash_v1
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER


class Exp01BRunnerError(RuntimeError):
    pass


class Exp01BScientificInputsV1:
    __slots__ = ("train1", "train2", "train3", "train4", "receipt_hashes")

    def __init__(
        self, *, train1: Any, train2: Any, train3: Any, train4: Any,
        receipt_hashes: Mapping[str, str],
    ) -> None:
        if set(receipt_hashes) != {"train1", "train2", "train3", "train4"}:
            raise Exp01BRunnerError("exact normal split receipts are required")
        for split, digest in receipt_hashes.items():
            require_sha256(digest, f"{split}_receipt_hash")
        self.train1, self.train2, self.train3, self.train4 = train1, train2, train3, train4
        self.receipt_hashes = dict(receipt_hashes)

    def __repr__(self) -> str:
        return "Exp01BScientificInputsV1(<private normal-only matrices redacted>)"


@dataclass(frozen=True)
class FormalV4RuleConversionInputV1:
    authority_hash: str
    executable_pairs: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        require_sha256(self.authority_hash, "rule_conversion_authority_hash")
        if len(self.executable_pairs) != len(set(self.executable_pairs)):
            raise Exp01BRunnerError("rule conversion pairs duplicate")
        if any(pair not in PAIR_UNIVERSE for pair in self.executable_pairs):
            raise Exp01BRunnerError("rule conversion pair exceeds normal reference")


@dataclass(frozen=True)
class Exp01BRunResultV1:
    public_document: Mapping[str, Any]
    ranking_rows: tuple[Mapping[str, Any], ...]
    stability_rows: tuple[Mapping[str, Any], ...]
    functional_rows: tuple[Mapping[str, Any], ...]
    rule_conversion_rows: tuple[Mapping[str, Any], ...]
    disposition: GDNDisposition
    checkpoint_receipts: tuple[Exp01BCheckpointReceiptV1, ...]


Trainer = Callable[..., Any]
Evaluator = Callable[..., Exp01BCheckpointEvidenceV1]
Confirmer = Callable[..., ArmBlindRelationExecutionV2]


def _view_segments(inputs: Exp01BScientificInputsV1, view: str) -> tuple[Any, ...]:
    if view == "TRAIN1_TRAIN2_COMBINED":
        return (inputs.train1, inputs.train2)
    if view == "TRAIN1_ONLY":
        return (inputs.train1,)
    if view == "TRAIN2_ONLY":
        return (inputs.train2,)
    raise Exp01BRunnerError("unknown frozen view")


def _mean_pairwise_jaccard(rankings: Mapping[int, Sequence[tuple[str, str]]], k: int) -> float:
    pairs = ((11, 23), (11, 37), (23, 37))
    return statistics.mean(jaccard_at_k_v1(rankings[left], rankings[right], k=k) for left, right in pairs)


def _median_raw_by_pair(
    evidence: Mapping[tuple[str, int], Exp01BCheckpointEvidenceV1],
    *, view: str, field: str,
) -> dict[tuple[str, str], float]:
    return {
        pair: float(statistics.median(
            float(getattr(evidence[(view, seed)], field).get(pair, 0.0))
            for seed in (11, 23, 37)
        ))
        for pair in PAIR_UNIVERSE
    }


def _matched_random_seed_comparison(
    *, record: Exp01BCheckpointEvidenceV1, seed: int, k: int,
) -> tuple[bool, int]:
    focal = tuple(
        pair for pair in deterministic_ranking_v1(target_local_percentiles_v1(record.edge_mask_scores))[:k]
        if pair in record.edge_mask_scores
    )
    comparisons: list[tuple[float, float]] = []
    eligible = tuple(record.edge_mask_control_scores)
    for pair in focal:
        try:
            control = matched_random_controls_v1(
                focal_edges=(pair,), eligible_graph_edges=eligible, seed=seed,
            )[pair][0]
        except ValueError:
            continue
        comparisons.append((float(record.edge_mask_scores[pair]), float(record.edge_mask_control_scores[control])))
    if not comparisons:
        return False, 0
    return (
        statistics.median(item[0] for item in comparisons) > statistics.median(item[1] for item in comparisons),
        len(comparisons),
    )


def run_exp01b_v1(
    *, scientific_inputs: Exp01BScientificInputsV1,
    environment: Exp01BEnvironmentFreezeV1,
    private_checkpoint_root: Path,
    meta_ranking: Sequence[tuple[str, str]],
    stat_ranking: Sequence[tuple[str, str]],
    rule_conversion: FormalV4RuleConversionInputV1,
    torch_module: Any,
    trainer: Trainer = train_exp01b_seed_v1,
    evaluator: Evaluator = evaluate_exp01b_checkpoint_v1,
    confirmer: Confirmer = fit_and_confirm_arbitrary_union_v2,
) -> Exp01BRunResultV1:
    if not environment.synthetic_smoke_passed:
        raise Exp01BRunnerError("environment smoke did not pass")
    device = "cuda" if environment.backend.value == "cuda" else "cpu"
    config = Exp01BDeviceTrainingConfigV1(device=device)
    if config.device != environment.model_device or config.device != environment.tensor_device:
        raise Exp01BRunnerError("training device differs from frozen environment")
    if config.functional_variant_chunk_size != environment.functional_variant_chunk_size:
        raise Exp01BRunnerError("functional variant chunk differs from frozen environment")
    meta_percentile = ranking_membership_percentiles_v1(meta_ranking)
    stat_percentile = ranking_membership_percentiles_v1(stat_ranking)
    provisional_meta_stat, _ = equal_weight_augmented_scores_v1(
        meta=meta_percentile, stat=stat_percentile,
        gdn_functional_consensus={pair: 0.0 for pair in PAIR_UNIVERSE},
    )
    meta_stat_ranking = deterministic_ranking_v1(provisional_meta_stat)
    # The frozen primary budget is valid only if Track A replays the 29-pair union.
    if len(set(meta_ranking) | set(stat_ranking)) != PRIMARY_BUDGET:
        raise Exp01BRunnerError("META+STAT primary budget did not replay as 29")

    confirmation = confirmer(
        candidate_pairs=PAIR_UNIVERSE,
        train1_matrix=scientific_inputs.train1,
        train2_matrix=scientific_inputs.train2,
        train3_matrix=scientific_inputs.train3,
        feature_order=P1_FEATURE_ORDER,
        train1_read_receipt_hash=scientific_inputs.receipt_hashes["train1"],
        train2_read_receipt_hash=scientific_inputs.receipt_hashes["train2"],
        train3_read_receipt_hash=scientific_inputs.receipt_hashes["train3"],
    )
    ledger = confirmation.private_ledger
    directional = tuple(
        row for row in ledger.get("directional_confirmation", ()) if bool(row.get("confirmed"))
    )
    confirmed_pairs = frozenset((str(row["source"]), str(row["target"])) for row in directional)
    if not confirmed_pairs:
        raise Exp01BRunnerError("normal-confirmed reference is empty")

    receipts: list[Exp01BCheckpointReceiptV1] = []
    evidence: dict[tuple[str, int], Exp01BCheckpointEvidenceV1] = {}
    for view in VIEWS:
        for seed in (11, 23, 37):
            trained = trainer(
                segments=_view_segments(scientific_inputs, view),
                feature_order=P1_FEATURE_ORDER, seed=seed, config=config,
            )
            run_id = f"exp01b-{view.lower().replace('_', '-')}-seed-{seed}"
            _, receipt = persist_private_checkpoint_v1(
                torch_module=torch_module, private_root=private_checkpoint_root,
                run_id=run_id, view=view, seed=seed,
                state_dict=trained.best_state_dict,
                training_config_hash=config.hyperparameter_hash,
                environment_hash=environment.environment_hash,
                graph_hash=trained.forward_graph_hash,
            )
            receipts.append(receipt)
            evidence[(view, seed)] = evaluator(
                state_dict=trained.best_state_dict,
                train4_segments=(scientific_inputs.train4,),
                feature_order=P1_FEATURE_ORDER,
                graph_edges=trained.graph_edges,
                view=view, seed=seed, config=config,
            )
    checkpoint_set = checkpoint_set_receipt_v1(receipts)

    view_consensus: dict[str, dict[tuple[str, str], float]] = {}
    arm_rankings: dict[tuple[str, str, int], tuple[tuple[str, str], ...]] = {}
    attention_available = all(record.attention_scores is not None for record in evidence.values())
    stability_rows: list[Mapping[str, Any]] = []
    for view in VIEWS:
        edge_by_seed = {
            seed: target_local_percentiles_v1(evidence[(view, seed)].edge_mask_scores)
            for seed in (11, 23, 37)
        }
        attention_by_seed = (
            {
                seed: target_local_percentiles_v1(evidence[(view, seed)].attention_scores or {})
                for seed in (11, 23, 37)
            }
            if attention_available else None
        )
        edge = aggregate_seed_percentiles_v1(edge_by_seed)
        attention = aggregate_seed_percentiles_v1(attention_by_seed) if attention_by_seed else None
        view_consensus[view] = functional_consensus_v1(edge_mask=edge, attention=attention)
        for arm, maps in (
            ("GDN_EDGEMASK", edge_by_seed),
            ("GDN_ATTENTION", attention_by_seed),
        ):
            if maps is None:
                continue
            seed_rankings = {seed: deterministic_ranking_v1(values) for seed, values in maps.items()}
            for seed, ranking in seed_rankings.items():
                arm_rankings[(arm, view, seed)] = ranking
            for k in EVALUATION_BUDGETS:
                stability_rows.append({
                    "arm": arm, "view": view, "k": k,
                    "seed_jaccard_mean": _mean_pairwise_jaccard(seed_rankings, k),
                })

    primary_consensus = view_consensus["TRAIN1_TRAIN2_COMBINED"]
    meta_stat_scores, augmented_scores = equal_weight_augmented_scores_v1(
        meta=meta_percentile, stat=stat_percentile,
        gdn_functional_consensus=primary_consensus,
    )
    baseline_ranking = deterministic_ranking_v1(meta_stat_scores)
    augmented_ranking = deterministic_ranking_v1(augmented_scores)
    ranking_rows: list[Mapping[str, Any]] = []
    directional_pairs = tuple((str(row["source"]), str(row["target"])) for row in directional)
    for name, ranking in (("META_STAT", baseline_ranking), ("META_STAT_GDN_AUGMENTED", augmented_ranking)):
        for k in EVALUATION_BUDGETS:
            metrics = precision_recall_ndcg_at_k_v1(ranking, confirmed_pairs=confirmed_pairs, k=k)
            ranking_rows.append({
                "arm": name, **metrics,
                "confirmed_directional_relation_yield": directional_relation_yield_at_k_v1(
                    ranking, directional_relation_pairs=directional_pairs, k=k,
                ),
            })
    baseline_primary = precision_recall_ndcg_at_k_v1(
        baseline_ranking, confirmed_pairs=confirmed_pairs, k=PRIMARY_BUDGET,
    )
    augmented_primary = precision_recall_ndcg_at_k_v1(
        augmented_ranking, confirmed_pairs=confirmed_pairs, k=PRIMARY_BUDGET,
    )

    split_flags: dict[str, bool] = {}
    for view in ("TRAIN1_ONLY", "TRAIN2_ONLY"):
        _, split_augmented_scores = equal_weight_augmented_scores_v1(
            meta=meta_percentile, stat=stat_percentile,
            gdn_functional_consensus=view_consensus[view],
        )
        split_metrics = precision_recall_ndcg_at_k_v1(
            deterministic_ranking_v1(split_augmented_scores),
            confirmed_pairs=confirmed_pairs, k=PRIMARY_BUDGET,
        )
        split_flags[f"{view}_yield"] = int(split_metrics["confirmed_pair_yield"]) >= int(baseline_primary["confirmed_pair_yield"])
        split_flags[f"{view}_ndcg"] = float(split_metrics["ndcg"]) >= float(baseline_primary["ndcg"])

    gdn_ranking = deterministic_ranking_v1(primary_consensus)
    unique = frozenset(gdn_ranking[:PRIMARY_BUDGET]) - frozenset(baseline_ranking[:PRIMARY_BUDGET])
    unique_confirmed = unique & confirmed_pairs
    unique_converted = unique_confirmed & frozenset(rule_conversion.executable_pairs)
    combined_edge_raw = _median_raw_by_pair(evidence, view="TRAIN1_TRAIN2_COMBINED", field="edge_mask_scores")
    functional_top = [combined_edge_raw[pair] for pair in gdn_ranking[:PRIMARY_BUDGET] if pair in combined_edge_raw]
    positive_median = bool(functional_top) and statistics.median(functional_top) > 0
    exceeds_random = 0
    matched_counts: dict[int, int] = {}
    for seed in (11, 23, 37):
        exceeds, matched = _matched_random_seed_comparison(
            record=evidence[("TRAIN1_TRAIN2_COMBINED", seed)], seed=seed, k=PRIMARY_BUDGET,
        )
        exceeds_random += int(exceeds)
        matched_counts[seed] = matched
    stable_unique = sum(
        sum(float(evidence[("TRAIN1_TRAIN2_COMBINED", seed)].edge_mask_scores.get(pair, 0.0)) > 0 for seed in (11, 23, 37)) >= 2
        for pair in unique_confirmed
    )
    baseline_set = frozenset(baseline_ranking[:PRIMARY_BUDGET])
    stable_baseline_functional = sum(
        sum(float(evidence[("TRAIN1_TRAIN2_COMBINED", seed)].edge_mask_scores.get(pair, 0.0)) > 0 for seed in (11, 23, 37)) >= 2
        for pair in baseline_set & confirmed_pairs
    )
    disposition_evidence = DispositionEvidenceV1(
        augmented_confirmed_yield=int(augmented_primary["confirmed_pair_yield"]),
        baseline_confirmed_yield=int(baseline_primary["confirmed_pair_yield"]),
        augmented_ndcg=float(augmented_primary["ndcg"]),
        baseline_ndcg=float(baseline_primary["ndcg"]),
        train1_yield_non_degraded=split_flags["TRAIN1_ONLY_yield"],
        train2_yield_non_degraded=split_flags["TRAIN2_ONLY_yield"],
        train1_ndcg_non_degraded=split_flags["TRAIN1_ONLY_ndcg"],
        train2_ndcg_non_degraded=split_flags["TRAIN2_ONLY_ndcg"],
        gdn_unique_confirmed_pairs=len(unique_confirmed),
        gdn_unique_executable_rule_pairs=len(unique_converted),
        positive_median_top_edge_mask=positive_median,
        combined_seeds_edge_mask_exceeds_random=exceeds_random,
        stable_unique_positive_pairs_two_seeds=stable_unique,
        stable_meta_stat_functional_pairs_two_seeds=stable_baseline_functional,
    )
    disposition = apply_frozen_disposition_rule_v1(disposition_evidence)

    functional_rows: list[Mapping[str, Any]] = []
    for (view, seed), record in sorted(evidence.items()):
        for arm, values in (
            ("GDN_EDGEMASK", record.edge_mask_scores),
            ("GDN_SOURCE_OCCLUSION", record.occlusion_scores),
        ):
            for (source, target), score in sorted(values.items()):
                functional_rows.append({
                    "arm": arm, "view": view, "seed": seed,
                    "source": source, "target": target, "relative_delta_mse": float(score),
                })
    rule_rows = tuple({
        "source": pair[0], "target": pair[1],
        "normal_confirmed": pair in confirmed_pairs,
        "formal_v4_executable": pair in set(rule_conversion.executable_pairs),
        "gdn_unique_at_primary_budget": pair in unique,
    } for pair in sorted(confirmed_pairs | set(rule_conversion.executable_pairs)))
    body: dict[str, Any] = {
        "schema": "paperworks.validation_v2.exp01b_frozen_result_v1",
        "schema_version": "1.0.0",
        "experiment_id": "EXP-01B-GDN-XAI-V1",
        "status": "COMPLETE_NORMAL_ONLY",
        "backend": environment.backend.value,
        "environment_hash": environment.environment_hash,
        "training_config_hash": config.hyperparameter_hash,
        "checkpoint_set_receipt_hash": checkpoint_set["receipt_hash"],
        "run_count": 9,
        "attention_status": "AVAILABLE_INVARIANCE_PASS" if attention_available else "ATTENTION_ARM_UNAVAILABLE_NONBLOCKING",
        "reference_pair_count": 144,
        "normal_confirmed_pair_count": len(confirmed_pairs),
        "normal_confirmed_directional_relation_count": len(directional),
        "reference_wording": "normal-confirmed relation reference",
        "causal_ground_truth": False,
        "primary_budget": PRIMARY_BUDGET,
        "baseline_confirmed_pair_yield": baseline_primary["confirmed_pair_yield"],
        "augmented_confirmed_pair_yield": augmented_primary["confirmed_pair_yield"],
        "baseline_ndcg": baseline_primary["ndcg"],
        "augmented_ndcg": augmented_primary["ndcg"],
        "gdn_unique_confirmed_pair_count": len(unique_confirmed),
        "gdn_unique_executable_rule_pair_count": len(unique_converted),
        "edge_mask_exceeds_matched_random_combined_seed_count": exceeds_random,
        "matched_random_comparison_counts": matched_counts,
        "disposition": disposition.value,
        "disposition_evidence": disposition_evidence.__dict__,
        "rule_conversion_authority_hash": rule_conversion.authority_hash,
        "train_splits": ["train1", "train2"],
        "reference_confirmation_split": "train3",
        "functional_split": "train4",
        "test1_accesses": 0,
        "label_accesses": 0,
        "test2_accesses": 0,
        "heldout_accesses": 0,
        "provider_calls": 0,
        "private_paths_disclosed": False,
    }
    public = {**body, "result_hash": stable_hash_v1(body)}
    return Exp01BRunResultV1(
        public_document=public,
        ranking_rows=tuple(ranking_rows), stability_rows=tuple(stability_rows),
        functional_rows=tuple(functional_rows), rule_conversion_rows=rule_rows,
        disposition=disposition, checkpoint_receipts=tuple(receipts),
    )


def write_sanitized_exp01b_outputs_v1(*, result: Exp01BRunResultV1, output_root: Path) -> None:
    """Atomically persist public-safe aggregate result files."""

    if not output_root.is_absolute():
        raise Exp01BRunnerError("output root must be absolute")
    output_root.mkdir(parents=True, exist_ok=True)
    documents = {
        "EXP01B_DISPOSITION.json": result.public_document,
        "EXP01B_CHECKPOINT_SET_RECEIPT.json": checkpoint_set_receipt_v1(result.checkpoint_receipts),
    }
    for name, document in documents.items():
        final = output_root / name
        temporary = output_root / f".{name}.{os.getpid()}.tmp"
        payload = (json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
        with temporary.open("wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, final)
        if sha256(final.read_bytes()).hexdigest() != sha256(payload).hexdigest():
            raise Exp01BRunnerError("public result replay mismatch")

    tables = {
        "EXP01B_RANKING_RESULTS.csv": result.ranking_rows,
        "EXP01B_STABILITY_RESULTS.csv": result.stability_rows,
        "EXP01B_FUNCTIONAL_RESULTS.csv": result.functional_rows,
        "EXP01B_RULE_CONVERSION_RESULTS.csv": result.rule_conversion_rows,
    }
    for name, rows in tables.items():
        if not rows:
            raise Exp01BRunnerError(f"public result table is empty: {name}")
        columns = tuple(rows[0])
        if any(tuple(row) != columns for row in rows):
            raise Exp01BRunnerError(f"public result table columns are inconsistent: {name}")
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        payload = buffer.getvalue().encode("utf-8")
        final = output_root / name
        temporary = output_root / f".{name}.{os.getpid()}.tmp"
        with temporary.open("wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, final)
        if sha256(final.read_bytes()).hexdigest() != sha256(payload).hexdigest():
            raise Exp01BRunnerError("public table replay mismatch")


__all__ = [
    "Exp01BRunResultV1", "Exp01BRunnerError", "Exp01BScientificInputsV1",
    "FormalV4RuleConversionInputV1", "run_exp01b_v1",
    "write_sanitized_exp01b_outputs_v1",
]
