"""Preregistered, result-independent EXP-01 contribution contract.

The module contains only portable contract and analysis primitives.  It does
not read scientific data, train GDN, or authorize an experiment runner.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
import statistics
from typing import Iterable, Mapping, Sequence

from paperworks.gdn.upstream_candidate_backend_v2 import GDNNeighborPolicyV2
from paperworks.v6.common import require_sha256, stable_hash_v1


EXP01_SCHEMA = "paperworks.validation_v2.exp01_preregistration_v1"
EXP01_VERSION = "1.0.0"
EXP01_ANALYSIS_RECEIPT_SCHEMA = "paperworks.validation_v2.exp01_analysis_receipt_v1"
EXP01_EVIDENCE_SCHEMA = "paperworks.validation_v2.exp01_contribution_evidence_v1"
EXP01_SEEDS = (11, 23, 37)
EXP01_PRIMARY_K = 20
EXP01_SENSITIVITY_K = (10, 40)
EXP01_UPSTREAM_COMMIT = "9853899da860682669a134e4af315d036aab4eca"
EXP01_ARMS = (
    "META_REFERENCE",
    "STAT_REFERENCE",
    "GDN_FROZEN_SELF_ELIGIBLE",
    "GDN_CORRECTED_SELF_EXCLUDED",
)
EXP01_REQUIRED_VIEWS = ("TRAIN1_TRAIN2_COMBINED", "TRAIN1_ONLY", "TRAIN2_ONLY")
EXP01_FUNCTIONAL_THRESHOLD = "DELTA_GT_MAX_1E-12_OR_1E-9_TIMES_ABS_BASELINE"
EXP01_FAILURE_RULE = "INCOMPLETE_AUTHORITY_OR_EXECUTION_FAILS_CLOSED_NOT_NEGATIVE_EVIDENCE"
EXP01_SEED_STABILITY_RULE = "PAIR_PRESENT_IN_AT_LEAST_TWO_OF_SEEDS_11_23_37"
EXP01_SPLIT_STABILITY_RULE = "PAIR_PRESENT_IN_BOTH_TRAIN1_ONLY_AND_TRAIN2_ONLY"
EXP01_TOPK_PREFIX_RULE = "EXACT_UNPADDED_PREFIX_K_WITH_DUPLICATES_FORBIDDEN"
EXP01_PRIMARY_MASK_RULE = "CORRECTED_INTERSECT_UNIQUE_INTERSECT_SEED_STABLE_INTERSECT_SPLIT_STABLE_INTERSECT_CONFIRMED"
EXP01_INTERVENTION_RULE = "MASK_EXACT_PRIMARY_EDGES_AND_COMPARE_HELD_NORMAL_TRAIN4_MSE_PER_SEED"
EXP01_FUNCTIONAL_INCLUSION_RULE = "POSITIVE_DELTA_IN_AT_LEAST_TWO_SEEDS_AND_POSITIVE_MEDIAN"


class Exp01ContractError(ValueError):
    """Raised when EXP-01 preparation or result evidence is incomplete."""


class Exp01Disposition(str, Enum):
    RETAIN_GRAPH_GUIDED_CONDITIONALLY = "RETAIN_GRAPH_GUIDED_CONDITIONALLY"
    DEMOTE_GDN_TO_ABLATION = "DEMOTE_GDN_TO_ABLATION"
    GDN_CONTRIBUTION_UNRESOLVED_FAIL_CLOSED = "GDN_CONTRIBUTION_UNRESOLVED_FAIL_CLOSED"


def _pairs(values: Iterable[Sequence[str]]) -> frozenset[tuple[str, str]]:
    rows = tuple((str(item[0]), str(item[1])) for item in values)
    if len(rows) != len(set(rows)):
        raise Exp01ContractError("candidate pairs must not contain duplicate rows")
    result = frozenset(rows)
    if any(not source or not target or source == target for source, target in result):
        raise Exp01ContractError("candidate pairs must be non-empty directed non-self identities")
    return result


@dataclass(frozen=True)
class Exp01PreregistrationV1:
    source_commit: str
    protocol_hash: str
    candidate_universe_hash: str
    feature_contract_hash: str
    data_authority_hash: str
    neighbor_policy_hash: str
    training_config_hash: str
    seeds: tuple[int, ...] = EXP01_SEEDS
    primary_k: int = EXP01_PRIMARY_K
    sensitivity_k: tuple[int, ...] = EXP01_SENSITIVITY_K
    fit_roles: tuple[str, ...] = ("train1", "train2")
    confirmation_role: str = "train3"
    functional_role: str = "train4"
    test1_authorized: bool = False
    labels_authorized: bool = False
    test2_authorized: bool = False
    heldout_authorized: bool = False
    upstream_commit: str = EXP01_UPSTREAM_COMMIT
    arms: tuple[str, ...] = EXP01_ARMS
    required_views: tuple[str, ...] = EXP01_REQUIRED_VIEWS
    functional_threshold: str = EXP01_FUNCTIONAL_THRESHOLD
    failure_rule: str = EXP01_FAILURE_RULE
    seed_stability_rule: str = EXP01_SEED_STABILITY_RULE
    split_stability_rule: str = EXP01_SPLIT_STABILITY_RULE
    topk_prefix_rule: str = EXP01_TOPK_PREFIX_RULE
    primary_mask_rule: str = EXP01_PRIMARY_MASK_RULE
    intervention_rule: str = EXP01_INTERVENTION_RULE
    functional_inclusion_rule: str = EXP01_FUNCTIONAL_INCLUSION_RULE
    schema: str = EXP01_SCHEMA
    schema_version: str = EXP01_VERSION
    preregistration_hash: str = ""

    def __post_init__(self) -> None:
        if len(self.source_commit) != 40 or any(character not in "0123456789abcdef" for character in self.source_commit):
            raise Exp01ContractError("source_commit must be a full lowercase Git SHA")
        for name in (
            "protocol_hash",
            "candidate_universe_hash",
            "feature_contract_hash",
            "data_authority_hash",
            "neighbor_policy_hash",
            "training_config_hash",
        ):
            require_sha256(getattr(self, name), name)
        if self.seeds != EXP01_SEEDS or self.primary_k != 20 or self.sensitivity_k != (10, 40):
            raise Exp01ContractError("EXP-01 seed or Top-K policy changed")
        if self.fit_roles != ("train1", "train2") or self.confirmation_role != "train3" or self.functional_role != "train4":
            raise Exp01ContractError("EXP-01 normal split roles changed")
        for name in ("test1_authorized", "labels_authorized", "test2_authorized", "heldout_authorized"):
            if type(getattr(self, name)) is not bool:
                raise Exp01ContractError(f"{name} must be a strict Boolean")
            if getattr(self, name):
                raise Exp01ContractError("EXP-01 forbids labels, test partitions, and held-out inputs")
        if self.upstream_commit != EXP01_UPSTREAM_COMMIT or self.arms != EXP01_ARMS:
            raise Exp01ContractError("EXP-01 upstream or arm identities changed")
        if self.required_views != EXP01_REQUIRED_VIEWS:
            raise Exp01ContractError("EXP-01 required split views changed")
        if self.functional_threshold != EXP01_FUNCTIONAL_THRESHOLD or self.failure_rule != EXP01_FAILURE_RULE:
            raise Exp01ContractError("EXP-01 functional threshold or failure rule changed")
        if (
            self.seed_stability_rule != EXP01_SEED_STABILITY_RULE
            or self.split_stability_rule != EXP01_SPLIT_STABILITY_RULE
            or self.topk_prefix_rule != EXP01_TOPK_PREFIX_RULE
            or self.primary_mask_rule != EXP01_PRIMARY_MASK_RULE
            or self.intervention_rule != EXP01_INTERVENTION_RULE
            or self.functional_inclusion_rule != EXP01_FUNCTIONAL_INCLUSION_RULE
        ):
            raise Exp01ContractError("EXP-01 material analysis policy changed")
        if self.schema != EXP01_SCHEMA or self.schema_version != EXP01_VERSION:
            raise Exp01ContractError("EXP-01 schema identity changed")
        if self.preregistration_hash:
            require_sha256(self.preregistration_hash, "preregistration_hash")
            if self.preregistration_hash != stable_hash_v1(self.to_dict(include_hash=False)):
                raise Exp01ContractError("EXP-01 preregistration replay mismatch")

    def to_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        document: dict[str, object] = {
            "schema": self.schema,
            "schema_version": self.schema_version,
            "source_commit": self.source_commit,
            "protocol_hash": self.protocol_hash,
            "candidate_universe_hash": self.candidate_universe_hash,
            "feature_contract_hash": self.feature_contract_hash,
            "data_authority_hash": self.data_authority_hash,
            "neighbor_policy_hash": self.neighbor_policy_hash,
            "training_config_hash": self.training_config_hash,
            "seeds": list(self.seeds),
            "primary_k": self.primary_k,
            "sensitivity_k": list(self.sensitivity_k),
            "fit_roles": list(self.fit_roles),
            "confirmation_role": self.confirmation_role,
            "functional_role": self.functional_role,
            "test1_authorized": self.test1_authorized,
            "labels_authorized": self.labels_authorized,
            "test2_authorized": self.test2_authorized,
            "heldout_authorized": self.heldout_authorized,
            "upstream_commit": self.upstream_commit,
            "arms": list(self.arms),
            "required_views": list(self.required_views),
            "functional_threshold": self.functional_threshold,
            "failure_rule": self.failure_rule,
            "seed_stability_rule": self.seed_stability_rule,
            "split_stability_rule": self.split_stability_rule,
            "topk_prefix_rule": self.topk_prefix_rule,
            "primary_mask_rule": self.primary_mask_rule,
            "intervention_rule": self.intervention_rule,
            "functional_inclusion_rule": self.functional_inclusion_rule,
            "claim_boundary": "NORMAL_DATA_CANDIDATE_GUIDANCE_NOT_CAUSALITY_OR_DETECTION_PERFORMANCE",
            "inclusion_rule": "STABLE_UNIQUE_CONFIRMED_AND_FUNCTIONALLY_USED",
        }
        if include_hash:
            document["preregistration_hash"] = self.preregistration_hash
        return document


def build_exp01_preregistration_v1(
    *,
    source_commit: str,
    protocol_hash: str,
    candidate_universe_hash: str,
    feature_contract_hash: str,
    data_authority_hash: str,
    training_config_hash: str,
) -> Exp01PreregistrationV1:
    policy_hash = GDNNeighborPolicyV2().policy_hash
    provisional = Exp01PreregistrationV1(
        source_commit=source_commit,
        protocol_hash=protocol_hash,
        candidate_universe_hash=candidate_universe_hash,
        feature_contract_hash=feature_contract_hash,
        data_authority_hash=data_authority_hash,
        neighbor_policy_hash=policy_hash,
        training_config_hash=training_config_hash,
    )
    return Exp01PreregistrationV1(
        **{
            **provisional.__dict__,
            "preregistration_hash": stable_hash_v1(provisional.to_dict(include_hash=False)),
        }
    )


@dataclass(frozen=True)
class StabilityMetricV1:
    left_count: int
    right_count: int
    intersection_count: int
    union_count: int
    jaccard_numerator: int
    jaccard_denominator: int

    @property
    def jaccard(self) -> float | None:
        return None if self.jaccard_denominator == 0 else self.jaccard_numerator / self.jaccard_denominator


def compute_set_stability_v1(
    left: Iterable[Sequence[str]], right: Iterable[Sequence[str]]
) -> StabilityMetricV1:
    left_set = _pairs(left)
    right_set = _pairs(right)
    intersection = left_set & right_set
    union = left_set | right_set
    return StabilityMetricV1(
        left_count=len(left_set),
        right_count=len(right_set),
        intersection_count=len(intersection),
        union_count=len(union),
        jaccard_numerator=len(intersection),
        jaccard_denominator=len(union),
    )


def stable_seed_pairs_v1(
    pairs_by_seed: Mapping[int, Iterable[Sequence[str]]], *, minimum_seeds: int = 2
) -> frozenset[tuple[str, str]]:
    if tuple(sorted(pairs_by_seed)) != EXP01_SEEDS or minimum_seeds != 2:
        raise Exp01ContractError("seed stability requires exact seeds and a two-of-three rule")
    normalized = {seed: _pairs(pairs) for seed, pairs in pairs_by_seed.items()}
    union = frozenset().union(*normalized.values())
    return frozenset(pair for pair in union if sum(pair in normalized[seed] for seed in EXP01_SEEDS) >= 2)


def unique_candidate_pairs_v1(
    *,
    corrected_gdn: Iterable[Sequence[str]],
    meta: Iterable[Sequence[str]],
    stat: Iterable[Sequence[str]],
) -> frozenset[tuple[str, str]]:
    return _pairs(corrected_gdn) - _pairs(meta) - _pairs(stat)


@dataclass(frozen=True)
class Exp01AnalysisReceiptV1:
    """Self-hashed typed binding for an EXP-01 downstream analysis step."""

    receipt_type: str
    preregistration_hash: str
    candidate_universe_hash: str
    training_config_hash: str
    neighbor_policy_hash: str
    input_hashes: tuple[str, ...]
    output_hash: str
    schema: str = EXP01_ANALYSIS_RECEIPT_SCHEMA
    schema_version: str = "1.0.0"
    receipt_hash: str = ""

    def __post_init__(self) -> None:
        if self.receipt_type not in {"CHECKPOINT_SET", "PROVENANCE", "CONFIRMATION", "INTERVENTION"}:
            raise Exp01ContractError("unknown EXP-01 analysis receipt type")
        if self.schema != EXP01_ANALYSIS_RECEIPT_SCHEMA or self.schema_version != "1.0.0":
            raise Exp01ContractError("EXP-01 analysis receipt schema changed")
        for name in (
            "preregistration_hash",
            "candidate_universe_hash",
            "training_config_hash",
            "neighbor_policy_hash",
            "output_hash",
        ):
            require_sha256(getattr(self, name), name)
        if not self.input_hashes:
            raise Exp01ContractError("analysis receipt requires bound input hashes")
        for index, value in enumerate(self.input_hashes):
            require_sha256(value, f"input_hashes[{index}]")
        if self.receipt_hash:
            require_sha256(self.receipt_hash, "receipt_hash")
            if self.receipt_hash != stable_hash_v1(self.to_dict(include_hash=False)):
                raise Exp01ContractError("analysis receipt replay mismatch")

    def to_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        document: dict[str, object] = {
            "schema": self.schema,
            "schema_version": self.schema_version,
            "receipt_type": self.receipt_type,
            "preregistration_hash": self.preregistration_hash,
            "candidate_universe_hash": self.candidate_universe_hash,
            "training_config_hash": self.training_config_hash,
            "neighbor_policy_hash": self.neighbor_policy_hash,
            "input_hashes": list(self.input_hashes),
            "output_hash": self.output_hash,
        }
        if include_hash:
            document["receipt_hash"] = self.receipt_hash
        return document


def build_exp01_analysis_receipt_v1(**values: object) -> Exp01AnalysisReceiptV1:
    provisional = Exp01AnalysisReceiptV1(**values)
    return Exp01AnalysisReceiptV1(
        **{
            **provisional.__dict__,
            "receipt_hash": stable_hash_v1(provisional.to_dict(include_hash=False)),
        }
    )


@dataclass(frozen=True)
class Exp01ContributionEvidenceV1:
    preregistration_hash: str
    candidate_universe_hash: str
    training_config_hash: str
    neighbor_policy_hash: str
    seed_run_receipt_hashes: tuple[str, str, str]
    authority_complete: bool
    execution_complete: bool
    privacy_pass: bool
    all_required_seeds_complete: bool
    corrected_self_neighbor_count: int
    forward_extraction_match: bool
    corrected_top20_pairs: tuple[tuple[str, str], ...]
    unique_pairs: tuple[tuple[str, str], ...]
    seed_stable_pairs: tuple[tuple[str, str], ...]
    split_stable_pairs: tuple[tuple[str, str], ...]
    confirmed_pairs: tuple[tuple[str, str], ...]
    primary_mask_pairs: tuple[tuple[str, str], ...]
    masking_delta_by_seed: tuple[float, float, float]
    masking_baseline_by_seed: tuple[float, float, float]
    checkpoint_receipt: Exp01AnalysisReceiptV1
    provenance_receipt: Exp01AnalysisReceiptV1
    confirmation_receipt: Exp01AnalysisReceiptV1
    intervention_receipt: Exp01AnalysisReceiptV1
    prohibited_input_used: bool
    result_driven_change_used: bool
    failure_reason: str | None = None
    schema: str = EXP01_EVIDENCE_SCHEMA
    schema_version: str = "1.0.0"
    evidence_hash: str = ""

    def __post_init__(self) -> None:
        for field_name in ("corrected_self_neighbor_count",):
            value = getattr(self, field_name)
            if type(value) is not int or value < 0:
                raise Exp01ContractError(f"{field_name} must be a non-negative integer")
        if self.schema != EXP01_EVIDENCE_SCHEMA or self.schema_version != "1.0.0":
            raise Exp01ContractError("EXP-01 contribution-evidence schema changed")
        for name in ("preregistration_hash", "candidate_universe_hash", "training_config_hash", "neighbor_policy_hash"):
            require_sha256(getattr(self, name), name)
        if len(self.seed_run_receipt_hashes) != len(EXP01_SEEDS):
            raise Exp01ContractError("exactly three ordered seed-run receipts are required")
        for index, value in enumerate(self.seed_run_receipt_hashes):
            require_sha256(value, f"seed_run_receipt_hashes[{index}]")
        for name in (
            "authority_complete",
            "execution_complete",
            "privacy_pass",
            "all_required_seeds_complete",
            "forward_extraction_match",
            "prohibited_input_used",
            "result_driven_change_used",
        ):
            if type(getattr(self, name)) is not bool:
                raise Exp01ContractError(f"{name} must be a strict Boolean")
        sets = {
            "corrected": _pairs(self.corrected_top20_pairs),
            "unique": _pairs(self.unique_pairs),
            "seed": _pairs(self.seed_stable_pairs),
            "split": _pairs(self.split_stable_pairs),
            "confirmed": _pairs(self.confirmed_pairs),
            "mask": _pairs(self.primary_mask_pairs),
        }
        expected_mask = sets["corrected"] & sets["unique"] & sets["seed"] & sets["split"] & sets["confirmed"]
        if len(self.corrected_top20_pairs) > EXP01_PRIMARY_K:
            raise Exp01ContractError("corrected Top-20 exceeds the unpadded prefix bound")
        if sets["mask"] != expected_mask:
            raise Exp01ContractError("primary mask must replay the exact stable unique split-stable confirmed intersection")
        if len(self.masking_delta_by_seed) != len(EXP01_SEEDS) or len(self.masking_baseline_by_seed) != len(EXP01_SEEDS):
            raise Exp01ContractError("masking vectors must align exactly to seeds 11, 23, and 37")
        if any(type(value) not in (int, float) or not math.isfinite(float(value)) for value in (*self.masking_delta_by_seed, *self.masking_baseline_by_seed)):
            raise Exp01ContractError("masking evidence must contain finite real values")
        if any(value < 0 for value in self.masking_baseline_by_seed):
            raise Exp01ContractError("masking baseline MSE cannot be negative")
        if not expected_mask and any(float(value) != 0.0 for value in self.masking_delta_by_seed):
            raise Exp01ContractError("empty primary mask cannot carry a nonzero intervention result")
        complete = self.authority_complete and self.execution_complete and self.privacy_pass and self.all_required_seeds_complete
        if complete and self.failure_reason is not None:
            raise Exp01ContractError("complete evidence cannot carry failure_reason")
        if not complete and not self.failure_reason:
            raise Exp01ContractError("incomplete evidence requires an explicit failure_reason")
        common = (
            self.preregistration_hash,
            self.candidate_universe_hash,
            self.training_config_hash,
            self.neighbor_policy_hash,
        )
        receipts = (
            (self.checkpoint_receipt, "CHECKPOINT_SET"),
            (self.provenance_receipt, "PROVENANCE"),
            (self.confirmation_receipt, "CONFIRMATION"),
            (self.intervention_receipt, "INTERVENTION"),
        )
        for receipt, receipt_type in receipts:
            if not receipt.receipt_hash or receipt.receipt_type != receipt_type:
                raise Exp01ContractError("typed self-hashed analysis receipts are required")
            if (
                receipt.preregistration_hash,
                receipt.candidate_universe_hash,
                receipt.training_config_hash,
                receipt.neighbor_policy_hash,
            ) != common:
                raise Exp01ContractError("analysis receipt authority binding mismatch")
        if self.checkpoint_receipt.input_hashes != self.seed_run_receipt_hashes:
            raise Exp01ContractError("checkpoint receipt must bind the exact ordered seed receipts")
        if self.provenance_receipt.input_hashes != (self.checkpoint_receipt.receipt_hash,):
            raise Exp01ContractError("provenance receipt must bind the checkpoint receipt")
        if self.confirmation_receipt.input_hashes != (self.provenance_receipt.receipt_hash,):
            raise Exp01ContractError("confirmation receipt must bind the provenance receipt")
        if self.intervention_receipt.input_hashes != (
            self.confirmation_receipt.receipt_hash,
            self.checkpoint_receipt.receipt_hash,
        ):
            raise Exp01ContractError("intervention receipt must bind confirmation and checkpoint receipts")
        expected_outputs = {
            "CHECKPOINT_SET": stable_hash_v1({"seed_run_receipt_hashes": self.seed_run_receipt_hashes}),
            "PROVENANCE": stable_hash_v1({
                "corrected_top20_pairs": self.corrected_top20_pairs,
                "unique_pairs": self.unique_pairs,
                "seed_stable_pairs": self.seed_stable_pairs,
                "split_stable_pairs": self.split_stable_pairs,
            }),
            "CONFIRMATION": stable_hash_v1({"confirmed_pairs": self.confirmed_pairs}),
            "INTERVENTION": stable_hash_v1({
                "primary_mask_pairs": self.primary_mask_pairs,
                "masking_delta_by_seed": self.masking_delta_by_seed,
                "masking_baseline_by_seed": self.masking_baseline_by_seed,
            }),
        }
        for receipt, receipt_type in receipts:
            if receipt.output_hash != expected_outputs[receipt_type]:
                raise Exp01ContractError(f"{receipt_type} output binding mismatch")
        if self.evidence_hash:
            require_sha256(self.evidence_hash, "evidence_hash")
            if self.evidence_hash != stable_hash_v1(self.to_dict(include_hash=False)):
                raise Exp01ContractError("EXP-01 contribution evidence replay mismatch")

    def to_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        document: dict[str, object] = {
            "schema": self.schema,
            "schema_version": self.schema_version,
            "preregistration_hash": self.preregistration_hash,
            "candidate_universe_hash": self.candidate_universe_hash,
            "training_config_hash": self.training_config_hash,
            "neighbor_policy_hash": self.neighbor_policy_hash,
            "seed_run_receipt_hashes": list(self.seed_run_receipt_hashes),
            "authority_complete": self.authority_complete,
            "execution_complete": self.execution_complete,
            "privacy_pass": self.privacy_pass,
            "all_required_seeds_complete": self.all_required_seeds_complete,
            "corrected_self_neighbor_count": self.corrected_self_neighbor_count,
            "forward_extraction_match": self.forward_extraction_match,
            "corrected_top20_pairs": [list(pair) for pair in self.corrected_top20_pairs],
            "unique_pairs": [list(pair) for pair in self.unique_pairs],
            "seed_stable_pairs": [list(pair) for pair in self.seed_stable_pairs],
            "split_stable_pairs": [list(pair) for pair in self.split_stable_pairs],
            "confirmed_pairs": [list(pair) for pair in self.confirmed_pairs],
            "primary_mask_pairs": [list(pair) for pair in self.primary_mask_pairs],
            "masking_delta_by_seed": list(self.masking_delta_by_seed),
            "masking_baseline_by_seed": list(self.masking_baseline_by_seed),
            "checkpoint_receipt": self.checkpoint_receipt.to_dict(),
            "provenance_receipt": self.provenance_receipt.to_dict(),
            "confirmation_receipt": self.confirmation_receipt.to_dict(),
            "intervention_receipt": self.intervention_receipt.to_dict(),
            "prohibited_input_used": self.prohibited_input_used,
            "result_driven_change_used": self.result_driven_change_used,
            "failure_reason": self.failure_reason,
        }
        if include_hash:
            document["evidence_hash"] = self.evidence_hash
        return document

    @property
    def stable_unique_confirmed_count(self) -> int:
        return len(self.primary_mask_pairs)

    @property
    def masking_positive_seed_count(self) -> int:
        return sum(
            delta > max(1e-12, 1e-9 * abs(baseline))
            for delta, baseline in zip(self.masking_delta_by_seed, self.masking_baseline_by_seed)
        )

    @property
    def masking_median_delta_positive(self) -> bool:
        return statistics.median(self.masking_delta_by_seed) > 0.0


def evaluate_graph_guided_inclusion_rule_v1(
    evidence: Exp01ContributionEvidenceV1,
) -> Exp01Disposition:
    complete = (
        evidence.authority_complete
        and evidence.execution_complete
        and evidence.privacy_pass
        and evidence.all_required_seeds_complete
    )
    if not complete or evidence.prohibited_input_used or evidence.result_driven_change_used:
        return Exp01Disposition.GDN_CONTRIBUTION_UNRESOLVED_FAIL_CLOSED
    mechanics_pass = evidence.corrected_self_neighbor_count == 0 and evidence.forward_extraction_match
    contribution_pass = evidence.stable_unique_confirmed_count >= 1
    functional_pass = evidence.masking_positive_seed_count >= 2 and evidence.masking_median_delta_positive
    if mechanics_pass and contribution_pass and functional_pass:
        return Exp01Disposition.RETAIN_GRAPH_GUIDED_CONDITIONALLY
    return Exp01Disposition.DEMOTE_GDN_TO_ABLATION


def build_exp01_contribution_evidence_v1(**values: object) -> Exp01ContributionEvidenceV1:
    provisional = Exp01ContributionEvidenceV1(**values)
    return Exp01ContributionEvidenceV1(
        **{
            **provisional.__dict__,
            "evidence_hash": stable_hash_v1(provisional.to_dict(include_hash=False)),
        }
    )


__all__ = [
    "EXP01_PRIMARY_K",
    "EXP01_SCHEMA",
    "EXP01_SEEDS",
    "EXP01_SENSITIVITY_K",
    "EXP01_VERSION",
    "Exp01ContractError",
    "Exp01ContributionEvidenceV1",
    "Exp01AnalysisReceiptV1",
    "Exp01Disposition",
    "Exp01PreregistrationV1",
    "StabilityMetricV1",
    "build_exp01_preregistration_v1",
    "build_exp01_analysis_receipt_v1",
    "build_exp01_contribution_evidence_v1",
    "compute_set_stability_v1",
    "evaluate_graph_guided_inclusion_rule_v1",
    "stable_seed_pairs_v1",
    "unique_candidate_pairs_v1",
]
