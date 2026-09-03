"""Frozen prospective contracts for EXP-01B-R1 and EXP-01C-GDN-HAI-V1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from paperworks.validation_v2.exp01_scientific_v1 import (
    FEATURE_ORDER_HASH,
    PAIR_UNIVERSE_HASH,
)
from paperworks.validation_v2.exp01b_contract_v1 import (
    ATTENTION_ATOL,
    ATTENTION_RTOL,
    FUNCTIONAL_VARIANT_CHUNK_SIZE,
    REQUIRED_CUBLAS_WORKSPACE_CONFIG,
    REQUIRED_DETERMINISTIC_FLAGS,
    REQUIRED_PYTHONHASHSEED,
)
from paperworks.v6.common import require_sha256, stable_hash_v1


EXP01B_R1_ID = "EXP-01B-R1"
EXP01C_ID = "EXP-01C-GDN-HAI-V1"
EXP01C_HORIZONS = (1, 5, 10, 30, 60)
EXP01C_SEEDS = (11, 23, 37)
EXP01C_VIEWS = ("TRAIN1_TRAIN2_COMBINED", "TRAIN1_ONLY", "TRAIN2_ONLY")
EXP01C_K = (10, 20, 29, 40)


class GDNCorrContractError(ValueError):
    pass


class LearnedGraphDisposition(str, Enum):
    PRIMARY = "LEARNED_GRAPH_PRIMARY"
    SUPPORTING = "LEARNED_GRAPH_SUPPORTING"
    ABLATION = "LEARNED_GRAPH_ABLATION"


@dataclass(frozen=True)
class Exp01CConfigV1:
    device: str = "cuda"
    batch_size: int = 32
    epochs: int = 30
    history_rows: int = 5
    stride: int = 1
    embedding_dim: int = 64
    out_layer_num: int = 1
    out_layer_inter_dim: int = 128
    learned_graph_topk: int = 5
    validation_ratio: float = 0.2
    learning_rate: float = 0.001
    weight_decay: float = 0.0
    early_stopping_patience: int = 15
    dropout: float = 0.2
    dtype: str = "float32"
    horizons: tuple[int, ...] = EXP01C_HORIZONS
    seeds: tuple[int, ...] = EXP01C_SEEDS
    views: tuple[str, ...] = EXP01C_VIEWS
    scaling_policy: str = "NORMAL_ONLY_AUDIT_DETERMINISTIC_ROBUST_OR_RAW"
    validation_policy: str = "FILE_LOCAL_CONTIGUOUS_PURGED_RAW_SUPPORT_DISJOINT"
    loss_policy: str = "EQUAL_FEATURE_EQUAL_HORIZON_MEAN_SQUARED_ERROR"

    def __post_init__(self) -> None:
        if self.device != "cuda":
            raise GDNCorrContractError("EXP-01C requires the separately frozen CUDA environment")
        if (
            self.batch_size != 32 or self.epochs != 30 or self.history_rows != 5
            or self.stride != 1 or self.embedding_dim != 64
            or self.out_layer_num != 1 or self.out_layer_inter_dim != 128
            or self.learned_graph_topk != 5 or self.validation_ratio != 0.2
            or self.learning_rate != 0.001 or self.weight_decay != 0.0
            or self.early_stopping_patience != 15 or self.dropout != 0.2
            or self.dtype != "float32" or self.horizons != EXP01C_HORIZONS
            or self.seeds != EXP01C_SEEDS or self.views != EXP01C_VIEWS
        ):
            raise GDNCorrContractError("EXP-01C frozen architecture or schedule changed")

    def to_dict(self) -> dict[str, Any]:
        return {
            "device": self.device, "batch_size": self.batch_size,
            "epochs": self.epochs, "history_rows": self.history_rows,
            "stride": self.stride, "embedding_dim": self.embedding_dim,
            "out_layer_num": self.out_layer_num,
            "out_layer_inter_dim": self.out_layer_inter_dim,
            "learned_graph_topk": self.learned_graph_topk,
            "validation_ratio": self.validation_ratio,
            "learning_rate": self.learning_rate, "weight_decay": self.weight_decay,
            "early_stopping_patience": self.early_stopping_patience,
            "dropout": self.dropout, "dtype": self.dtype,
            "horizons": list(self.horizons), "seeds": list(self.seeds),
            "views": list(self.views), "scaling_policy": self.scaling_policy,
            "validation_policy": self.validation_policy,
            "loss_policy": self.loss_policy,
        }

    @property
    def config_hash(self) -> str:
        return stable_hash_v1(self.to_dict())


def exp01b_r1_contract_body_v1(
    *, source_commit: str, implementation_hashes: Mapping[str, str],
) -> dict[str, Any]:
    if len(source_commit) != 40 or any(character not in "0123456789abcdef" for character in source_commit):
        raise GDNCorrContractError("source commit must be a lowercase Git SHA")
    for name, digest in implementation_hashes.items():
        require_sha256(digest, f"implementation_hashes[{name}]")
    return {
        "schema": "paperworks.validation_v2.exp01b_r1_correction_contract_v1",
        "schema_version": "1.0.0",
        "experiment_id": EXP01B_R1_ID,
        "source_commit": source_commit,
        "status": "FROZEN_BEFORE_CORRECTED_RESULT_ACCESS",
        "immutable_parent_experiment": "EXP-01B-GDN-XAI-V1",
        "parent_result_freeze_hash": "ba405bb3cae4d46efb9c8a3c0fc57a099140be28516fe3993428e195980f2ed3",
        "corrections": {
            "percentile": "OBSERVED_COUNT_MINUS_FIRST_TIE_RANK_OVER_COUNT_ABSENT_ZERO",
            "tie": "EQUAL_RAW_SCORE_EQUAL_PERCENTILE_LEXICAL_DISPLAY_ONLY",
            "edge_mask": "POSITIVE_MAX_DELTA_ZERO_NEGATIVE_COUNTEREVIDENCE_TOLERANCE_1E_MINUS_12",
            "attention_override": "PROHIBITED_WHEN_EDGEMASK_NONPOSITIVE",
            "random_control": "WHOLE_FOCAL_EXCLUSION_TARGET_SEED_VIEW_GRAPH_CARDINALITY_NO_REPLACEMENT_WHEN_FEASIBLE",
            "rule_conversion": "GDN_UNIQUE_DIRECTIONAL_RELATION_THROUGH_EXP02_POLICY_AND_FORMAL_V4",
        },
        "existing_evidence_only": True,
        "retraining": False,
        "normal_data_roles": {"train1_train2": "GDN_UNIQUE_NUMERIC_AUTHORITY_ONLY"},
        "prohibited_inputs": ["test1", "labels", "test2", "heldout", "provider"],
        "implementation_hashes": dict(sorted(implementation_hashes.items())),
        "post_result_change_allowed": False,
    }


def exp01b_r1_contract_document_v1(
    *, source_commit: str, implementation_hashes: Mapping[str, str],
) -> dict[str, Any]:
    body = exp01b_r1_contract_body_v1(
        source_commit=source_commit, implementation_hashes=implementation_hashes,
    )
    return {**body, "contract_hash": stable_hash_v1(body)}


def exp01c_preregistration_body_v1(
    *, source_commit: str, implementation_hashes: Mapping[str, str],
) -> dict[str, Any]:
    config = Exp01CConfigV1()
    if len(source_commit) != 40 or any(character not in "0123456789abcdef" for character in source_commit):
        raise GDNCorrContractError("source commit must be a lowercase Git SHA")
    for name, digest in implementation_hashes.items():
        require_sha256(digest, f"implementation_hashes[{name}]")
    return {
        "schema": "paperworks.validation_v2.exp01c_gdn_hai_preregistration_v1",
        "schema_version": "1.0.0",
        "experiment_id": EXP01C_ID,
        "source_commit": source_commit,
        "status": "FROZEN_BEFORE_TRAINING",
        "research_question": (
            "Whether a HAI-adapted, normal-only, multi-horizon learned graph provides "
            "stable predictive or functional relation evidence beyond META+STAT."
        ),
        "frozen_baseline": {
            "experiment": "EXP-01B-GDN-XAI-V1",
            "model": "RAW_CURRENT_ONE_STEP",
            "retraining": False,
            "disposition": "GDN_ABLATION_ONLY",
        },
        "data_roles": {
            "train1_train2": "TRAIN_AND_NORMAL_RELATION_EVIDENCE",
            "train3": "ARM_BLIND_NORMAL_CONFIRMATION",
            "train4": "FIXED_CHECKPOINT_FUNCTIONAL_FIDELITY",
        },
        "prohibited_inputs": ["test1", "test1_labels", "test2", "heldout", "provider"],
        "configuration": config.to_dict(),
        "configuration_hash": config.config_hash,
        "run_schedule": [
            {"view": view, "seed": seed, "backend": "cuda"}
            for view in EXP01C_VIEWS for seed in EXP01C_SEEDS
        ],
        "run_count": 9,
        "architecture": {
            "shared_self_excluded_learned_graph": True,
            "direction": "SOURCE_TO_TARGET",
            "history_rows": 5,
            "multi_horizon_prediction_heads": list(EXP01C_HORIZONS),
            "target": "THREE_ROW_FUTURE_MEDIAN_AT_EACH_HORIZON",
            "loss": "EQUAL_FEATURE_EQUAL_HORIZON_MEAN_SQUARED_ERROR",
            "causal_claim": False,
        },
        "preprocessing_audit": {
            "policies": ["RAW_CURRENT", "TRAIN_ONLY_STANDARDIZED", "TRAIN_ONLY_ROBUST_MEDIAN_IQR"],
            "fit_scope": "EACH_TRAINING_VIEW_ONLY",
            "scale_ratio_material_threshold": 100.0,
            "raw_top5_mse_share_threshold": 0.50,
            "required_top5_share_reduction": 0.10,
            "selection": (
                "ROBUST_IF_SCALE_RATIO_AT_LEAST_100_AND_RAW_TOP5_SHARE_AT_LEAST_0.50_"
                "AND_ROBUST_REDUCES_TOP5_SHARE_BY_AT_LEAST_0.10_OTHERWISE_RAW"
            ),
            "attack_performance_used": False,
        },
        "validation": {
            "block": "ONE_CONTIGUOUS_BLOCK_PER_PHYSICAL_FILE",
            "ratio": 0.2,
            "purge_rows": 66,
            "purge_derivation": "HISTORY_5_MINUS_1_PLUS_MAX_RESPONSE_OFFSET_62",
            "raw_timestamp_overlap_allowed": 0,
            "cross_file_validation_block": False,
            "seed_deterministic": True,
        },
        "ranking": {
            "percentile": "EXP01B_R1_POSITIVE_OBSERVED_TIE_AWARE",
            "absent": 0.0,
            "edge_mask_positive_only": True,
            "random_controls": "EXP01B_R1_WHOLE_FOCAL_MATCH",
            "budgets": list(EXP01C_K),
            "primary_budget": 29,
            "weights": "EQUAL_FIXED_NO_TUNING",
        },
        "functional_xai": {
            "global_edge_mask": "LEARNED_GRAPH_MEMBERS_ONLY_BY_HORIZON",
            "event_conditioned_edge_mask": "NORMAL_SOURCE_STEPS_FILE_LOCAL_FROZEN_DIRECTION_AND_HORIZON",
            "all_pair_path": "EDGEMASK_IF_GRAPH_MEMBER_ELSE_SOURCE_OCCLUSION_WITH_NOT_GRAPH_MEMBER_STATE",
            "nonmember_edgemask": "NOT_IN_LEARNED_GRAPH_NOT_ZERO_MEASUREMENT",
            "attention_by_horizon": "SHARED_ENCODER_ATTENTION_REPORTED_PER_HORIZON_NOT_HEAD_SPECIFIC",
            "edge_mask_by_horizon": True,
        },
        "formal_v4_conversion": {
            "path": "GDN_UNIQUE_CONFIRMED_DIRECTIONAL_RELATION_TO_EXP02_POLICY_TO_FORMAL_V4",
            "same_criteria_as_v2a": True,
            "relaxed_criteria": False,
        },
        "disposition": {
            "PRIMARY": [
                "AT_K29_CONFIRMED_YIELD_OR_NDCG_STRICTLY_IMPROVES_OTHER_NOT_DEGRADE",
                "AUGMENTED_SEED_JACCARD_K29_NOT_BELOW_META_STAT_BASELINE",
                "TRAIN1_AND_TRAIN2_YIELD_AND_NDCG_NON_DEGRADED",
                "AT_LEAST_ONE_GDN_UNIQUE_FORMAL_V4_RULE",
                "AT_LEAST_ONE_NORMAL_CONFIRMED_PAIR_POSITIVE_EVENT_EDGEMASK_IN_AT_LEAST_2_OF_3_COMBINED_SEEDS",
                "EVENT_EDGEMASK_MEDIAN_EXCEEDS_FROZEN_MATCHED_RANDOM_IN_AT_LEAST_2_OF_3_COMBINED_SEEDS",
            ],
            "SUPPORTING": (
                "PRIMARY_FAILS_BUT_AT_LEAST_ONE_NORMAL_CONFIRMED_RELATION_HAS_"
                "POSITIVE_EVENT_EDGEMASK_IN_AT_LEAST_2_OF_3_COMBINED_SEEDS"
            ),
            "ABLATION": "OTHERWISE",
        },
        "compute": {
            "environment": "SEPARATE_FROZEN_CUDA_ENVIRONMENT",
            "backend_mixing": False,
            "cublas_workspace_config": REQUIRED_CUBLAS_WORKSPACE_CONFIG,
            "pythonhashseed": REQUIRED_PYTHONHASHSEED,
            "deterministic_flags": dict(REQUIRED_DETERMINISTIC_FLAGS),
            "functional_variant_chunk_size": FUNCTIONAL_VARIANT_CHUNK_SIZE,
        },
        "attention_capture": {
            "output_invariance_atol": ATTENTION_ATOL,
            "output_invariance_rtol": ATTENTION_RTOL,
            "causal_interpretation": False,
        },
        "feature_order_hash": FEATURE_ORDER_HASH,
        "pair_universe_hash": PAIR_UNIVERSE_HASH,
        "implementation_hashes": dict(sorted(implementation_hashes.items())),
        "hyperparameter_search": False,
        "post_result_change_allowed": False,
    }


def exp01c_preregistration_document_v1(
    *, source_commit: str, implementation_hashes: Mapping[str, str],
) -> dict[str, Any]:
    body = exp01c_preregistration_body_v1(
        source_commit=source_commit, implementation_hashes=implementation_hashes,
    )
    return {**body, "preregistration_hash": stable_hash_v1(body)}


@dataclass(frozen=True)
class Exp01CDispositionEvidenceV1:
    yield_improved: bool
    ndcg_improved: bool
    other_metric_not_degraded: bool
    seed_stability_pass: bool
    split_stability_pass: bool
    unique_formal_v4_rule_count: int
    stable_positive_event_conditioned_count: int
    matched_random_pass: bool
    stable_positive_normal_confirmed_count: int


def apply_exp01c_disposition_v1(evidence: Exp01CDispositionEvidenceV1) -> LearnedGraphDisposition:
    primary = (
        (evidence.yield_improved or evidence.ndcg_improved)
        and evidence.other_metric_not_degraded
        and evidence.seed_stability_pass
        and evidence.split_stability_pass
        and evidence.unique_formal_v4_rule_count >= 1
        and evidence.stable_positive_event_conditioned_count >= 1
        and evidence.matched_random_pass
    )
    if primary:
        return LearnedGraphDisposition.PRIMARY
    if evidence.stable_positive_normal_confirmed_count >= 1:
        return LearnedGraphDisposition.SUPPORTING
    return LearnedGraphDisposition.ABLATION


__all__ = [
    "EXP01B_R1_ID", "EXP01C_HORIZONS", "EXP01C_ID", "EXP01C_K",
    "EXP01C_SEEDS", "EXP01C_VIEWS", "Exp01CConfigV1",
    "Exp01CDispositionEvidenceV1", "GDNCorrContractError",
    "LearnedGraphDisposition", "apply_exp01c_disposition_v1",
    "exp01b_r1_contract_document_v1", "exp01c_preregistration_document_v1",
]
