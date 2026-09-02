"""Frozen, data-free contracts for EXP-01B GDN Prediction-XAI.

The contracts in this module do not import Torch, open HAI data, train a
model, or authorize test data.  They exist so the compute backend and all
result-dependent choices are fixed before the first scientific run.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from paperworks.gdn.upstream_candidate_backend_v1 import UPSTREAM_GDN_COMMIT
from paperworks.validation_v2.exp01_scientific_v1 import (
    FEATURE_ORDER_HASH,
    PAIR_UNIVERSE_HASH,
    SEEDS,
)
from paperworks.v6.common import require_sha256, stable_hash_v1


EXPERIMENT_ID = "EXP-01B-GDN-XAI-V1"
SCHEMA_VERSION = "1.0.0"
VIEWS = ("TRAIN1_TRAIN2_COMBINED", "TRAIN1_ONLY", "TRAIN2_ONLY")
EVIDENCE_ARMS = (
    "GDN_EMBEDDING",
    "GDN_ATTENTION",
    "GDN_EDGEMASK",
    "GDN_SOURCE_OCCLUSION",
    "GDN_FUNCTIONAL_CONSENSUS",
)
EVALUATION_BUDGETS = (10, 20, 29, 40)
PRIMARY_BUDGET = 29
ATTENTION_ATOL = 1e-7
ATTENTION_RTOL = 1e-6
RELATIVE_DELTA_EPSILON = 1e-12
OCCLUSION_BLOCK_WIDTH = 5
SOURCE_OCCLUSION_TRANSFORM = "FIXED_SEED_WITHIN_FILE_SOURCE_HISTORY_BLOCK_PERMUTATION_V1"
RANK_TIE_POLICY = "LEXICAL_PAIR_IDENTITY_ASCENDING"
PERCENTILE_POLICY = "TARGET_LOCAL_BEST_ONE_WORST_ZERO_LEXICAL_TIES_V1"
REFERENCE_WORDING = "normal-confirmed relation reference"


class Exp01BContractError(ValueError):
    """Fail-closed EXP-01B contract error."""


class ComputeBackend(str, Enum):
    CUDA = "cuda"
    CPU_FALLBACK = "cpu_fallback"


def _environment_body_v1(
    *, backend: ComputeBackend, python_version: str, torch_version: str,
    cuda_build: str, driver_version: str, gpu_model: str, dtype: str,
    deterministic_flags: tuple[tuple[str, bool], ...], synthetic_smoke_passed: bool,
    model_device: str, tensor_device: str,
) -> dict[str, Any]:
    return {
        "schema": "paperworks.validation_v2.exp01b_environment_freeze_v1",
        "schema_version": SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "backend": backend.value,
        "python_version": python_version,
        "torch_version": torch_version,
        "cuda_build": cuda_build,
        "driver_version": driver_version,
        "gpu_model": gpu_model,
        "dtype": dtype,
        "deterministic_flags": dict(deterministic_flags),
        "synthetic_smoke_passed": synthetic_smoke_passed,
        "model_device": model_device,
        "tensor_device": tensor_device,
    }


@dataclass(frozen=True)
class Exp01BTrainingConfigV1:
    """Architecture/hyperparameter freeze inherited without tuning."""

    batch_size: int = 32
    epochs: int = 30
    slide_window: int = 5
    slide_stride: int = 1
    embedding_dim: int = 64
    out_layer_num: int = 1
    learned_graph_topk: int = 5
    validation_ratio: float = 0.2
    learning_rate: float = 0.001
    weight_decay: float = 0.0
    early_stopping_patience: int = 15
    dropout: float = 0.2
    dtype: str = "float32"
    corrected_neighbor_policy: str = "SELF_EXCLUDED_STABLE_TOPK_V1"
    seeds: tuple[int, ...] = SEEDS
    views: tuple[str, ...] = VIEWS

    def __post_init__(self) -> None:
        if self.seeds != (11, 23, 37) or self.views != VIEWS:
            raise Exp01BContractError("EXP-01B schedule changed")
        if self.learned_graph_topk != 5 or self.corrected_neighbor_policy != "SELF_EXCLUDED_STABLE_TOPK_V1":
            raise Exp01BContractError("corrected self-excluded Top-5 is mandatory")
        if self.dtype != "float32" or self.slide_window != OCCLUSION_BLOCK_WIDTH:
            raise Exp01BContractError("frozen dtype/window changed")

    @property
    def training_config_hash(self) -> str:
        return stable_hash_v1(self.to_document())

    def to_document(self) -> dict[str, Any]:
        return {
            "batch_size": self.batch_size,
            "epochs": self.epochs,
            "slide_window": self.slide_window,
            "slide_stride": self.slide_stride,
            "embedding_dim": self.embedding_dim,
            "out_layer_num": self.out_layer_num,
            "learned_graph_topk": self.learned_graph_topk,
            "validation_ratio": self.validation_ratio,
            "learning_rate": self.learning_rate,
            "weight_decay": self.weight_decay,
            "early_stopping_patience": self.early_stopping_patience,
            "dropout": self.dropout,
            "dtype": self.dtype,
            "corrected_neighbor_policy": self.corrected_neighbor_policy,
            "seeds": list(self.seeds),
            "views": list(self.views),
        }


@dataclass(frozen=True)
class Exp01BEnvironmentFreezeV1:
    """Actual one-backend identity that must be issued before run 1."""

    backend: ComputeBackend
    python_version: str
    torch_version: str
    cuda_build: str
    driver_version: str
    gpu_model: str
    dtype: str
    deterministic_flags: tuple[tuple[str, bool], ...]
    environment_hash: str
    synthetic_smoke_passed: bool
    model_device: str
    tensor_device: str

    def __post_init__(self) -> None:
        require_sha256(self.environment_hash, "environment_hash")
        if self.environment_hash != stable_hash_v1(self.body_document()):
            raise Exp01BContractError("environment self hash mismatch")
        if not self.synthetic_smoke_passed:
            raise Exp01BContractError("synthetic backend smoke must pass before run 1")
        if self.dtype != "float32":
            raise Exp01BContractError("EXP-01B dtype changed")
        expected = "cuda" if self.backend is ComputeBackend.CUDA else "cpu"
        if self.model_device != expected or self.tensor_device != expected:
            raise Exp01BContractError("model and tensors must use the frozen backend")
        if self.backend is ComputeBackend.CUDA and (
            not self.cuda_build or self.cuda_build.startswith("NONE") or "5060" not in self.gpu_model
        ):
            raise Exp01BContractError("CUDA backend must identify the approved RTX 5060-class device")
        if self.backend is ComputeBackend.CPU_FALLBACK and self.cuda_build not in {
            "NONE_CPU_BUILD", "CUDA_UNAVAILABLE_IN_SEPARATE_FALLBACK_ENVIRONMENT"
        }:
            raise Exp01BContractError("CPU fallback identity is ambiguous")

    def body_document(self) -> dict[str, Any]:
        return _environment_body_v1(
            backend=self.backend, python_version=self.python_version,
            torch_version=self.torch_version, cuda_build=self.cuda_build,
            driver_version=self.driver_version, gpu_model=self.gpu_model,
            dtype=self.dtype, deterministic_flags=self.deterministic_flags,
            synthetic_smoke_passed=self.synthetic_smoke_passed,
            model_device=self.model_device, tensor_device=self.tensor_device,
        )


def build_environment_freeze_v1(
    *, backend: ComputeBackend, python_version: str, torch_version: str,
    cuda_build: str, driver_version: str, gpu_model: str,
    deterministic_flags: Mapping[str, bool], synthetic_smoke_passed: bool,
    model_device: str, tensor_device: str,
) -> Exp01BEnvironmentFreezeV1:
    flags = tuple(sorted((str(key), value) for key, value in deterministic_flags.items()))
    if not flags or any(type(value) is not bool for _, value in flags):
        raise Exp01BContractError("strict deterministic flags are required")
    digest = stable_hash_v1(_environment_body_v1(
        backend=backend, python_version=python_version, torch_version=torch_version,
        cuda_build=cuda_build, driver_version=driver_version, gpu_model=gpu_model,
        dtype="float32", deterministic_flags=flags,
        synthetic_smoke_passed=synthetic_smoke_passed,
        model_device=model_device, tensor_device=tensor_device,
    ))
    return Exp01BEnvironmentFreezeV1(
        backend=backend, python_version=python_version, torch_version=torch_version,
        cuda_build=cuda_build, driver_version=driver_version, gpu_model=gpu_model,
        dtype="float32", deterministic_flags=flags, environment_hash=digest,
        synthetic_smoke_passed=synthetic_smoke_passed,
        model_device=model_device, tensor_device=tensor_device,
    )


def preregistration_body_v1() -> dict[str, Any]:
    config = Exp01BTrainingConfigV1()
    return {
        "schema": "paperworks.validation_v2.exp01b_preregistration_v1",
        "schema_version": SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "title": "GDN Prediction-based Relation Extraction Comparison",
        "status": "FROZEN_BEFORE_SCIENTIFIC_EXECUTION",
        "research_question": (
            "Among embedding similarity, graph attention, functional edge masking, and "
            "source-history occlusion, which GDN-derived evidence most stably ranks "
            "normal-confirmed source-to-target relations?"
        ),
        "input_roles": {
            "train1_train2": "GDN_TRAINING_AND_CANDIDATE_EVIDENCE",
            "train3": "ARM_BLIND_NORMAL_RELATION_REFERENCE",
            "train4": "FIXED_CHECKPOINT_FUNCTIONAL_FIDELITY",
        },
        "prohibited_inputs": ["test1", "test1_labels", "test2", "heldout", "provider_data"],
        "training_config": config.to_document(),
        "training_config_hash": config.training_config_hash,
        "schedule": [
            {"view": view, "seed": seed, "backend": "ONE_BACKEND_FROZEN_BEFORE_RUN_1"}
            for view in VIEWS for seed in SEEDS
        ],
        "run_count": 9,
        "compute_policy": {
            "primary": "SEPARATE_OFFICIAL_CUDA_PYTORCH_ENVIRONMENT",
            "fallback": "ONE_SEPARATE_CPU_ENVIRONMENT_FROZEN_BEFORE_RUN_1",
            "backend_mixing": "PROHIBITED",
            "synthetic_smoke_required": True,
        },
        "upstream_gdn_commit": UPSTREAM_GDN_COMMIT,
        "feature_order_hash": FEATURE_ORDER_HASH,
        "pair_universe_hash": PAIR_UNIVERSE_HASH,
        "corrected_self_exclusion": True,
        "evidence_arms": list(EVIDENCE_ARMS),
        "attention_capture": {
            "post_normalization_weights_used_for_target_prediction": True,
            "direction": "SOURCE_TO_TARGET",
            "atol": ATTENTION_ATOL,
            "rtol": ATTENTION_RTOL,
            "output_invariance_required": True,
            "unavailable_is_nonblocking": True,
        },
        "edge_mask": {
            "primary_functional_arm": True,
            "fixed_checkpoint": True,
            "target_specific_mse": True,
            "relative_delta_epsilon": RELATIVE_DELTA_EPSILON,
            "no_edge_refill": True,
            "matched_random": ["target", "graph_membership_eligibility", "seed", "view", "mask_cardinality"],
        },
        "source_occlusion": {
            "secondary_robustness_only": True,
            "transform": SOURCE_OCCLUSION_TRANSFORM,
            "block_width": OCCLUSION_BLOCK_WIDTH,
            "file_local": True,
            "cross_split_mixing": False,
        },
        "rank_policy": {
            "within_target": True,
            "percentile": PERCENTILE_POLICY,
            "seed_aggregation": "MEDIAN_PERCENTILE",
            "view_aggregation": "SEPARATE_AND_COMBINED",
            "tie": RANK_TIE_POLICY,
            "functional_consensus": "MEAN_EDGEMASK_ATTENTION_OR_EDGEMASK_IF_ATTENTION_UNAVAILABLE",
            "embedding_is_baseline_only": True,
        },
        "evaluation_budgets": list(EVALUATION_BUDGETS),
        "primary_budget": PRIMARY_BUDGET,
        "primary_budget_authority": "FROZEN_META_STAT_UNION_COUNT_MUST_REPLAY_AS_29_BEFORE_RESULT_EVALUATION",
        "reference": {
            "pair_count": 144,
            "construction": "TRAIN1_TRAIN2_PROFILE_THEN_TRAIN3_ARM_BLIND_CONFIRMATION",
            "wording": REFERENCE_WORDING,
            "causal_ground_truth": False,
        },
        "augmented_rank": {
            "meta_stat_score": "MEAN_META_STAT_PERCENTILES",
            "augmented_score": "MEAN_META_STAT_GDN_FUNCTIONAL_CONSENSUS_PERCENTILES",
            "missing_membership_percentile": 0.0,
            "weights": "EQUAL_FIXED",
            "weight_tuning": False,
            "same_total_budget": True,
        },
        "disposition_rule": "FROZEN_THREE_WAY_EXP01B_GDN_DISPOSITION_V1",
        "claim_boundary": "NORMAL_CONFIRMED_PREDICTIVE_OR_FUNCTIONAL_EVIDENCE_NOT_CAUSALITY",
        "post_result_change_allowed": False,
        "test_accesses_authorized": 0,
        "label_accesses_authorized": 0,
    }


def preregistration_document_v1() -> dict[str, Any]:
    body = preregistration_body_v1()
    return {**body, "preregistration_hash": stable_hash_v1(body)}


def validate_environment_schedule_v1(
    environments: Mapping[tuple[str, int], Exp01BEnvironmentFreezeV1],
) -> None:
    expected = {(view, seed) for view in VIEWS for seed in SEEDS}
    if set(environments) != expected:
        raise Exp01BContractError("exact nine-run environment schedule required")
    backend = {item.backend for item in environments.values()}
    identity = {item.environment_hash for item in environments.values()}
    if len(backend) != 1 or len(identity) != 1:
        raise Exp01BContractError("EXP-01B cannot mix compute backends or environments")


__all__ = [
    "ATTENTION_ATOL", "ATTENTION_RTOL", "ComputeBackend", "EVALUATION_BUDGETS",
    "EXPERIMENT_ID", "Exp01BContractError", "Exp01BEnvironmentFreezeV1",
    "Exp01BTrainingConfigV1", "OCCLUSION_BLOCK_WIDTH", "PRIMARY_BUDGET",
    "RELATIVE_DELTA_EPSILON", "SOURCE_OCCLUSION_TRANSFORM", "VIEWS",
    "build_environment_freeze_v1", "preregistration_body_v1", "preregistration_document_v1",
    "validate_environment_schedule_v1",
]
