"""Prospective EXP-02 normal-only numeric-policy contracts.

This module freezes a provider-free candidate space and a train4-only
selection contract.  It does not read scientific data, create runtime
authority, authorize labels, or execute a policy.  A later scientific adapter
must bind the pure contracts here to authorized normal-only inputs and Formal
V4 numeric authority artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from hashlib import sha256
import json
import math
import re
from typing import Any, Mapping, Sequence

from .formal_v4_authority_v1 import V4_HORIZONS_SECONDS, V4_NUMERIC_ROLES
from .protocol_v1 import (
    ProtocolOperationV1,
    SplitRoleV1,
    ValidationProtocolV1,
    validate_validation_protocol_v1,
)


EXP02_NUMERIC_POLICY_VERSION = "VALIDATION_V2_EXP02_NUMERIC_POLICY_V1"
EXP02_FIT_SPLITS = ("train1", "train2")
EXP02_CONFIRMATION_SPLIT = "train3"
EXP02_SELECTION_SPLIT = "train4"
EXP02_DEVELOPMENT_SPLIT = "test1"
EXP02_PROVIDER_CALLS_REQUIRED = False

COMMON_THRESHOLD_NOISE_MULTIPLIER = "5"
COMMON_AMPLITUDE_QUANTILE = "0.75"
COMMON_STABILITY_NOISE_MULTIPLIER = "3"
COMMON_STABILITY_THRESHOLD_FRACTION = "0.10"
TARGET_NOISE_SCALE_MULTIPLIER = "1"

# Closed before train4 selection.  Cartesian size: 3 * 3 * 2 * 2 = 36.
RELATION_THRESHOLD_NOISE_MULTIPLIERS = ("3", "5", "7")
RELATION_AMPLITUDE_QUANTILES = ("0.50", "0.75", "0.90")
RELATION_STABILITY_NOISE_MULTIPLIERS = ("2", "3")
RELATION_STABILITY_THRESHOLD_FRACTIONS = ("0.05", "0.10")

FROZEN_WINDOW_VALUES = (
    ("source_pre_window_seconds", "5"),
    ("source_post_window_seconds", "5"),
    ("minimum_source_stability_fraction", "0.8"),
    ("source_refractory_seconds", "10"),
    ("cross_source_isolation_radius_seconds", "2"),
    ("target_baseline_window_seconds", "5"),
    ("target_response_window_seconds", "3"),
)

COMMON_FORMULA_IDS = (
    "source_step_threshold=max(5*source_scope_noise,Q75(source_scope_nontrivial_step_amplitude))",
    "source_stability_tolerance=max(3*source_scope_noise,0.10*source_step_threshold)",
    "target_noise_scale=1*target_scope_first_difference_robust_scale",
    "split_pooling=max(train1_derived_value,train2_derived_value)",
)
RELATION_FORMULA_IDS = (
    "source_step_threshold=max(grid_noise_multiplier*relation_noise,Qgrid(relation_nontrivial_step_amplitude))",
    "source_stability_tolerance=max(grid_noise_multiplier*relation_noise,grid_threshold_fraction*source_step_threshold)",
    "target_noise_scale=1*relation_target_first_difference_robust_scale",
    "split_pooling=max(train1_derived_value,train2_derived_value)",
)
FIT_SPLIT_VARIABILITY_STATISTIC = (
    "MAX_ROLE_SYMMETRIC_RELATIVE_DIFFERENCE;"
    "2*abs(train1-train2)/(abs(train1)+abs(train2));both_zero=0"
)
GUARD_POLICY = (
    "STRICT_NONINFERIOR_TO_COMMON:relation_retention>=baseline;"
    "opportunity_coverage>=baseline;evaluation_coverage>=baseline"
)
COMPLEXITY_ORDER = (
    "COMMON_FIXED_NORMALIZED_V1",
    "RELATION_SPECIFIC_NORMAL_ONLY_V1",
    "DIAGNOSTIC_LLM_PROPOSAL_ONLY",
)

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_GIT_COMMIT = re.compile(r"^[0-9a-f]{40}$")


class NumericPolicyError(ValueError):
    def __init__(self, issue_code: str, message: str) -> None:
        super().__init__(f"{issue_code}: {message}")
        self.issue_code = issue_code
        self.message = message


class NumericPolicyFamilyV1(str, Enum):
    COMMON_FIXED_NORMALIZED_V1 = "COMMON_FIXED_NORMALIZED_V1"
    RELATION_SPECIFIC_NORMAL_ONLY_V1 = "RELATION_SPECIFIC_NORMAL_ONLY_V1"
    DIAGNOSTIC_LLM_PROPOSAL_ONLY = "DIAGNOSTIC_LLM_PROPOSAL_ONLY"


class NumericRoleScopeV1(str, Enum):
    GLOBAL = "GLOBAL"
    SOURCE = "SOURCE"
    TARGET = "TARGET"
    RELATION = "RELATION"


def _fail(code: str, message: str) -> None:
    raise NumericPolicyError(code, message)


def _canonical_bytes(document: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(document), sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _hash_document(document: Mapping[str, Any]) -> str:
    return sha256(_canonical_bytes(document)).hexdigest()


def _text(value: object, name: str) -> str:
    if type(value) is not str or not value:
        _fail("EXP02_TEXT_INVALID", f"{name} must be a non-empty exact string")
    return value


def _sha(value: object, name: str) -> str:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        _fail("EXP02_HASH_INVALID", f"{name} must be lowercase SHA-256")
    return value


def _commit(value: object) -> str:
    if type(value) is not str or _GIT_COMMIT.fullmatch(value) is None:
        _fail("EXP02_SOURCE_COMMIT_INVALID", "source_commit must be a 40-character Git commit")
    return value


def _strict_int(value: object, name: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        _fail("EXP02_INTEGER_INVALID", f"{name} must be an exact integer >= {minimum}")
    return value


def _finite_nonnegative(value: object, name: str, *, positive: bool = False) -> float:
    if type(value) is not float or not math.isfinite(value):
        _fail("EXP02_FLOAT_INVALID", f"{name} must be a finite exact float")
    if value < 0.0 or (positive and value <= 0.0):
        _fail("EXP02_FLOAT_DOMAIN_INVALID", f"{name} is outside its domain")
    return value


def _decimal_literal(value: object, allowed: tuple[str, ...], name: str) -> str:
    if type(value) is not str or value not in allowed:
        _fail("EXP02_GRID_LITERAL_INVALID", f"{name} is outside the frozen grid")
    return value


def _as_float(value: str) -> float:
    return float(value)


@dataclass(frozen=True)
class ConfirmedRelationIdentityV1:
    relation_id: str
    source: str
    target: str
    source_direction: str
    target_direction: str
    selected_horizon_seconds: int
    relation_binding_hash: str

    def __post_init__(self) -> None:
        _text(self.relation_id, "relation_id")
        _text(self.source, "source")
        _text(self.target, "target")
        if self.source == self.target:
            _fail("EXP02_SELF_RELATION", "source and target must differ")
        if self.source_direction not in ("step_up", "step_down"):
            _fail("EXP02_SOURCE_DIRECTION_INVALID", "source direction is outside Formal V4")
        if self.target_direction not in ("increase", "decrease"):
            _fail("EXP02_TARGET_DIRECTION_INVALID", "target direction is outside Formal V4")
        if type(self.selected_horizon_seconds) is not int or self.selected_horizon_seconds not in V4_HORIZONS_SECONDS:
            _fail("EXP02_HORIZON_INVALID", "selected horizon must be frozen in the Formal V4 set")
        _sha(self.relation_binding_hash, "relation_binding_hash")

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class ConfirmedCohortAuthorityV1:
    cohort_id: str
    source_commit: str
    confirmation_split: str
    confirmation_artifact_hash: str
    relations: tuple[ConfirmedRelationIdentityV1, ...]
    cohort_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_exp02_confirmed_cohort_authority_v1",
            "cohort_id": self.cohort_id,
            "confirmation_artifact_hash": self.confirmation_artifact_hash,
            "confirmation_split": self.confirmation_split,
            "relations": [item.to_dict() for item in self.relations],
            "schema_version": "1.0.0",
            "source_commit": self.source_commit,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body_dict(), "cohort_hash": self.cohort_hash}


def build_confirmed_cohort_authority_v1(
    *, cohort_id: str, source_commit: str, confirmation_artifact_hash: str,
    relations: Sequence[ConfirmedRelationIdentityV1],
) -> ConfirmedCohortAuthorityV1:
    _text(cohort_id, "cohort_id")
    _commit(source_commit)
    _sha(confirmation_artifact_hash, "confirmation_artifact_hash")
    if type(relations) not in (tuple, list) or not relations:
        _fail("EXP02_COHORT_EMPTY", "confirmed cohort must be non-empty")
    if any(type(item) is not ConfirmedRelationIdentityV1 for item in relations):
        _fail("EXP02_COHORT_RELATION_TYPE_INVALID", "cohort relation type differs")
    ordered = tuple(sorted(relations, key=lambda item: item.relation_id))
    if len({item.relation_id for item in ordered}) != len(ordered):
        _fail("EXP02_COHORT_RELATION_DUPLICATE", "relation IDs must be unique")
    provisional = ConfirmedCohortAuthorityV1(
        cohort_id, source_commit, EXP02_CONFIRMATION_SPLIT,
        confirmation_artifact_hash, ordered, "",
    )
    return ConfirmedCohortAuthorityV1(
        **{**provisional.__dict__, "cohort_hash": _hash_document(provisional.body_dict())}
    )


def validate_confirmed_cohort_authority_v1(value: ConfirmedCohortAuthorityV1) -> str:
    if type(value) is not ConfirmedCohortAuthorityV1:
        _fail("EXP02_COHORT_TYPE_INVALID", "cohort authority type differs")
    expected = build_confirmed_cohort_authority_v1(
        cohort_id=value.cohort_id, source_commit=value.source_commit,
        confirmation_artifact_hash=value.confirmation_artifact_hash,
        relations=value.relations,
    )
    if value != expected:
        _fail("EXP02_COHORT_REPLAY_MISMATCH", "cohort authority differs from replay")
    return value.cohort_hash


@dataclass(frozen=True)
class RelationSpecificGridPointV1:
    threshold_noise_multiplier: str
    amplitude_quantile: str
    stability_noise_multiplier: str
    stability_threshold_fraction: str

    def __post_init__(self) -> None:
        _decimal_literal(self.threshold_noise_multiplier, RELATION_THRESHOLD_NOISE_MULTIPLIERS, "threshold_noise_multiplier")
        _decimal_literal(self.amplitude_quantile, RELATION_AMPLITUDE_QUANTILES, "amplitude_quantile")
        _decimal_literal(self.stability_noise_multiplier, RELATION_STABILITY_NOISE_MULTIPLIERS, "stability_noise_multiplier")
        _decimal_literal(self.stability_threshold_fraction, RELATION_STABILITY_THRESHOLD_FRACTIONS, "stability_threshold_fraction")

    @property
    def grid_id(self) -> str:
        return (
            f"n{self.threshold_noise_multiplier}-q{self.amplitude_quantile}-"
            f"s{self.stability_noise_multiplier}-f{self.stability_threshold_fraction}"
        )

    def to_dict(self) -> dict[str, str]:
        return dict(self.__dict__)


def frozen_relation_specific_grid_v1() -> tuple[RelationSpecificGridPointV1, ...]:
    return tuple(
        RelationSpecificGridPointV1(n, q, s, f)
        for n in RELATION_THRESHOLD_NOISE_MULTIPLIERS
        for q in RELATION_AMPLITUDE_QUANTILES
        for s in RELATION_STABILITY_NOISE_MULTIPLIERS
        for f in RELATION_STABILITY_THRESHOLD_FRACTIONS
    )


def _role_scopes(family: NumericPolicyFamilyV1) -> tuple[tuple[str, str], ...]:
    if family is NumericPolicyFamilyV1.COMMON_FIXED_NORMALIZED_V1:
        data_scopes = ("SOURCE", "SOURCE", "TARGET")
    elif family is NumericPolicyFamilyV1.RELATION_SPECIFIC_NORMAL_ONLY_V1:
        data_scopes = ("RELATION", "RELATION", "RELATION")
    else:
        data_scopes = ("RELATION", "RELATION", "RELATION")
    return tuple(zip(V4_NUMERIC_ROLES, data_scopes + ("GLOBAL",) * 7))


@dataclass(frozen=True)
class NumericPolicyCandidateV1:
    candidate_id: str
    family: NumericPolicyFamilyV1
    cohort_hash: str
    normal_fit_input_hash: str
    source_commit: str
    fit_splits: tuple[str, str]
    formula_ids: tuple[str, ...]
    role_scopes: tuple[tuple[str, str], ...]
    grid_point: RelationSpecificGridPointV1 | None
    provider_required: bool
    validity_authority: bool
    runtime_authority: bool
    candidate_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_exp02_numeric_policy_candidate_v1",
            "candidate_id": self.candidate_id,
            "cohort_hash": self.cohort_hash,
            "family": self.family.value,
            "fit_splits": list(self.fit_splits),
            "formula_ids": list(self.formula_ids),
            "grid_point": None if self.grid_point is None else self.grid_point.to_dict(),
            "normal_fit_input_hash": self.normal_fit_input_hash,
            "provider_required": self.provider_required,
            "role_scopes": [list(item) for item in self.role_scopes],
            "runtime_authority": self.runtime_authority,
            "schema_version": "1.0.0",
            "source_commit": self.source_commit,
            "validity_authority": self.validity_authority,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body_dict(), "candidate_hash": self.candidate_hash}


def _build_candidate(
    *, family: NumericPolicyFamilyV1, cohort_hash: str,
    normal_fit_input_hash: str, source_commit: str,
    grid_point: RelationSpecificGridPointV1 | None,
) -> NumericPolicyCandidateV1:
    _sha(cohort_hash, "cohort_hash")
    _sha(normal_fit_input_hash, "normal_fit_input_hash")
    _commit(source_commit)
    if family is NumericPolicyFamilyV1.COMMON_FIXED_NORMALIZED_V1:
        if grid_point is not None:
            _fail("EXP02_COMMON_GRID_PROHIBITED", "common policy has no grid point")
        candidate_id = family.value
        formula_ids = COMMON_FORMULA_IDS
    elif family is NumericPolicyFamilyV1.RELATION_SPECIFIC_NORMAL_ONLY_V1:
        if type(grid_point) is not RelationSpecificGridPointV1:
            _fail("EXP02_RELATION_GRID_REQUIRED", "relation-specific policy requires a grid point")
        candidate_id = f"{family.value}:{grid_point.grid_id}"
        formula_ids = RELATION_FORMULA_IDS
    else:
        _fail("EXP02_DIAGNOSTIC_NOT_MAIN_CANDIDATE", "provider diagnostic is outside the main candidate set")
    provisional = NumericPolicyCandidateV1(
        candidate_id, family, cohort_hash, normal_fit_input_hash, source_commit,
        EXP02_FIT_SPLITS, formula_ids, _role_scopes(family), grid_point,
        False, False, False, "",
    )
    return NumericPolicyCandidateV1(
        **{**provisional.__dict__, "candidate_hash": _hash_document(provisional.body_dict())}
    )


def build_numeric_policy_candidate_set_v1(
    *, cohort: ConfirmedCohortAuthorityV1, normal_fit_input_hash: str,
    source_commit: str,
) -> tuple[NumericPolicyCandidateV1, ...]:
    validate_confirmed_cohort_authority_v1(cohort)
    if source_commit != cohort.source_commit:
        _fail("EXP02_COHORT_SOURCE_COMMIT_MISMATCH", "candidate and cohort commits differ")
    candidates = [
        _build_candidate(
            family=NumericPolicyFamilyV1.COMMON_FIXED_NORMALIZED_V1,
            cohort_hash=cohort.cohort_hash, normal_fit_input_hash=normal_fit_input_hash,
            source_commit=source_commit, grid_point=None,
        )
    ]
    candidates.extend(
        _build_candidate(
            family=NumericPolicyFamilyV1.RELATION_SPECIFIC_NORMAL_ONLY_V1,
            cohort_hash=cohort.cohort_hash, normal_fit_input_hash=normal_fit_input_hash,
            source_commit=source_commit, grid_point=point,
        )
        for point in frozen_relation_specific_grid_v1()
    )
    return tuple(candidates)


def validate_numeric_policy_candidate_v1(value: NumericPolicyCandidateV1) -> str:
    if type(value) is not NumericPolicyCandidateV1:
        _fail("EXP02_CANDIDATE_TYPE_INVALID", "candidate type differs")
    expected = _build_candidate(
        family=value.family, cohort_hash=value.cohort_hash,
        normal_fit_input_hash=value.normal_fit_input_hash,
        source_commit=value.source_commit, grid_point=value.grid_point,
    )
    if value != expected:
        _fail("EXP02_CANDIDATE_REPLAY_MISMATCH", "candidate differs from frozen replay")
    if tuple(role for role, _ in value.role_scopes) != V4_NUMERIC_ROLES:
        _fail("EXP02_ROLE_ORDER_INVALID", "all ten Formal V4 roles are required in order")
    return value.candidate_hash


def candidate_set_hash_v1(candidates: Sequence[NumericPolicyCandidateV1]) -> str:
    if type(candidates) not in (tuple, list) or not candidates:
        _fail("EXP02_CANDIDATE_SET_EMPTY", "candidate set must be non-empty")
    for item in candidates:
        validate_numeric_policy_candidate_v1(item)
    ordered = tuple(sorted(candidates, key=lambda item: item.candidate_id))
    if len({item.candidate_id for item in ordered}) != len(ordered):
        _fail("EXP02_CANDIDATE_DUPLICATE", "candidate IDs duplicate")
    if sum(item.family is NumericPolicyFamilyV1.COMMON_FIXED_NORMALIZED_V1 for item in ordered) != 1:
        _fail("EXP02_COMMON_BASELINE_CARDINALITY", "exactly one common baseline is required")
    if len(ordered) != 1 + len(frozen_relation_specific_grid_v1()):
        _fail("EXP02_CANDIDATE_GRID_INCOMPLETE", "closed 36-point grid plus baseline is required")
    return _hash_document({"candidate_hashes": [item.candidate_hash for item in ordered]})


@dataclass(frozen=True)
class SplitNormalSummaryV1:
    split_id: str
    relation_id: str
    source: str
    target: str
    source_scope_noise: float
    source_scope_q50: float
    source_scope_q75: float
    source_scope_q90: float
    target_scope_noise: float
    relation_noise: float
    relation_q50: float
    relation_q75: float
    relation_q90: float
    relation_target_noise: float
    summary_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_exp02_split_normal_summary_v1",
            **{key: value for key, value in self.__dict__.items() if key != "summary_hash"},
            "schema_version": "1.0.0",
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body_dict(), "summary_hash": self.summary_hash}


def build_split_normal_summary_v1(
    *, split_id: str, relation_id: str, source: str, target: str,
    source_scope_noise: float, source_scope_quantiles: tuple[float, float, float],
    target_scope_noise: float, relation_noise: float,
    relation_quantiles: tuple[float, float, float], relation_target_noise: float,
) -> SplitNormalSummaryV1:
    if split_id not in EXP02_FIT_SPLITS:
        _fail("EXP02_NUMERIC_FIT_SPLIT_PROHIBITED", "numeric derivation is train1/train2 only")
    for name, value in (("relation_id", relation_id), ("source", source), ("target", target)):
        _text(value, name)
    if source == target:
        _fail("EXP02_SELF_RELATION", "source and target must differ")
    if type(source_scope_quantiles) is not tuple or len(source_scope_quantiles) != 3:
        _fail("EXP02_QUANTILE_TUPLE_INVALID", "source quantiles must be an exact q50/q75/q90 tuple")
    if type(relation_quantiles) is not tuple or len(relation_quantiles) != 3:
        _fail("EXP02_QUANTILE_TUPLE_INVALID", "relation quantiles must be an exact q50/q75/q90 tuple")
    # The frozen V2A binding defines source noise as the median of all finite
    # absolute first differences.  A piecewise-constant control source may
    # therefore have an exact zero noise floor.  Directional/source amplitude
    # quantiles and target scales must remain strictly positive so the derived
    # threshold and Formal V4 response boundary are executable.
    _finite_nonnegative(source_scope_noise, "source_scope_noise")
    _finite_nonnegative(relation_noise, "relation_noise")
    for index, value in enumerate(source_scope_quantiles):
        _finite_nonnegative(value, f"source_scope_quantile_{index}", positive=True)
    for index, value in enumerate(relation_quantiles):
        _finite_nonnegative(value, f"relation_quantile_{index}", positive=True)
    _finite_nonnegative(target_scope_noise, "target_scope_noise", positive=True)
    _finite_nonnegative(relation_target_noise, "relation_target_noise", positive=True)
    if not (source_scope_quantiles[0] <= source_scope_quantiles[1] <= source_scope_quantiles[2]):
        _fail("EXP02_QUANTILE_ORDER_INVALID", "source quantiles must be ordered")
    if not (relation_quantiles[0] <= relation_quantiles[1] <= relation_quantiles[2]):
        _fail("EXP02_QUANTILE_ORDER_INVALID", "relation quantiles must be ordered")
    provisional = SplitNormalSummaryV1(
        split_id, relation_id, source, target, source_scope_noise,
        source_scope_quantiles[0], source_scope_quantiles[1], source_scope_quantiles[2],
        target_scope_noise, relation_noise, relation_quantiles[0],
        relation_quantiles[1], relation_quantiles[2], relation_target_noise, "",
    )
    return SplitNormalSummaryV1(
        **{**provisional.__dict__, "summary_hash": _hash_document(provisional.body_dict())}
    )


def validate_split_normal_summary_v1(value: SplitNormalSummaryV1) -> str:
    if type(value) is not SplitNormalSummaryV1:
        _fail("EXP02_NORMAL_SUMMARY_TYPE_INVALID", "normal summary type differs")
    expected = build_split_normal_summary_v1(
        split_id=value.split_id, relation_id=value.relation_id,
        source=value.source, target=value.target,
        source_scope_noise=value.source_scope_noise,
        source_scope_quantiles=(value.source_scope_q50, value.source_scope_q75, value.source_scope_q90),
        target_scope_noise=value.target_scope_noise, relation_noise=value.relation_noise,
        relation_quantiles=(value.relation_q50, value.relation_q75, value.relation_q90),
        relation_target_noise=value.relation_target_noise,
    )
    if value != expected:
        _fail("EXP02_NORMAL_SUMMARY_REPLAY_MISMATCH", "normal summary differs from replay")
    return value.summary_hash


def _quantile(summary: SplitNormalSummaryV1, *, relation: bool, quantile: str) -> float:
    suffix = {"0.50": "q50", "0.75": "q75", "0.90": "q90"}[quantile]
    return getattr(summary, f"relation_{suffix}" if relation else f"source_scope_{suffix}")


def derive_role_values_for_split_v1(
    *, candidate: NumericPolicyCandidateV1, summary: SplitNormalSummaryV1,
) -> tuple[tuple[str, float], ...]:
    validate_numeric_policy_candidate_v1(candidate)
    validate_split_normal_summary_v1(summary)
    relation_specific = candidate.family is NumericPolicyFamilyV1.RELATION_SPECIFIC_NORMAL_ONLY_V1
    if relation_specific:
        assert candidate.grid_point is not None
        point = candidate.grid_point
        noise = summary.relation_noise
        amplitude = _quantile(summary, relation=True, quantile=point.amplitude_quantile)
        threshold_multiplier = _as_float(point.threshold_noise_multiplier)
        stability_multiplier = _as_float(point.stability_noise_multiplier)
        stability_fraction = _as_float(point.stability_threshold_fraction)
        target_noise = summary.relation_target_noise
    else:
        noise = summary.source_scope_noise
        amplitude = summary.source_scope_q75
        threshold_multiplier = _as_float(COMMON_THRESHOLD_NOISE_MULTIPLIER)
        stability_multiplier = _as_float(COMMON_STABILITY_NOISE_MULTIPLIER)
        stability_fraction = _as_float(COMMON_STABILITY_THRESHOLD_FRACTION)
        target_noise = summary.target_scope_noise
    threshold = max(threshold_multiplier * noise, amplitude)
    tolerance = max(stability_multiplier * noise, stability_fraction * threshold)
    values: tuple[tuple[str, float], ...] = (
        ("source_step_threshold", threshold),
        ("source_stability_tolerance", tolerance),
        ("target_noise_scale", _as_float(TARGET_NOISE_SCALE_MULTIPLIER) * target_noise),
        *((role, float(value)) for role, value in FROZEN_WINDOW_VALUES),
    )
    if tuple(role for role, _ in values) != V4_NUMERIC_ROLES:
        _fail("EXP02_DERIVED_ROLE_ORDER_INVALID", "derived values must cover all Formal V4 roles")
    return values


def symmetric_relative_difference_v1(left: float, right: float) -> Fraction:
    _finite_nonnegative(left, "left")
    _finite_nonnegative(right, "right")
    if left == 0.0 and right == 0.0:
        return Fraction(0, 1)
    # Exact binary-float ratios make the statistic deterministic and replayable.
    l = Fraction.from_float(left)
    r = Fraction.from_float(right)
    return 2 * abs(l - r) / (abs(l) + abs(r))


def fit_split_variability_v1(
    *, candidate: NumericPolicyCandidateV1,
    summaries: tuple[SplitNormalSummaryV1, SplitNormalSummaryV1],
) -> Fraction:
    if type(summaries) is not tuple or len(summaries) != 2:
        _fail("EXP02_FIT_SUMMARY_PAIR_INVALID", "exact train1/train2 summary pair required")
    for item in summaries:
        validate_split_normal_summary_v1(item)
    by_split = {item.split_id: item for item in summaries}
    if tuple(sorted(by_split)) != EXP02_FIT_SPLITS or len(by_split) != 2:
        _fail("EXP02_FIT_SPLIT_COVERAGE_INVALID", "exact train1 and train2 summaries required")
    first, second = by_split["train1"], by_split["train2"]
    if (first.relation_id, first.source, first.target) != (second.relation_id, second.source, second.target):
        _fail("EXP02_CROSS_RELATION_VARIABILITY_PROHIBITED", "split variability is relation-local")
    left = dict(derive_role_values_for_split_v1(candidate=candidate, summary=first))
    right = dict(derive_role_values_for_split_v1(candidate=candidate, summary=second))
    return max(symmetric_relative_difference_v1(left[role], right[role]) for role in V4_NUMERIC_ROLES)


def derive_pooled_role_values_v1(
    *, candidate: NumericPolicyCandidateV1,
    summaries: tuple[SplitNormalSummaryV1, SplitNormalSummaryV1],
) -> tuple[tuple[str, float], ...]:
    """Materialize the frozen conservative max(train1, train2) policy."""

    if type(summaries) is not tuple or len(summaries) != 2:
        _fail("EXP02_FIT_SUMMARY_PAIR_INVALID", "exact train1/train2 summary pair required")
    if any(type(item) is not SplitNormalSummaryV1 for item in summaries):
        _fail("EXP02_FIT_SUMMARY_TYPE_INVALID", "split summary type differs")
    by_split = {item.split_id: item for item in summaries}
    if tuple(sorted(by_split)) != EXP02_FIT_SPLITS or len(by_split) != 2:
        _fail("EXP02_FIT_SPLIT_COVERAGE_INVALID", "exact train1 and train2 summaries required")
    first, second = by_split["train1"], by_split["train2"]
    for item in (first, second):
        validate_split_normal_summary_v1(item)
    if (first.relation_id, first.source, first.target) != (second.relation_id, second.source, second.target):
        _fail("EXP02_CROSS_RELATION_POOLING_PROHIBITED", "split pooling is relation-local")
    left = dict(derive_role_values_for_split_v1(candidate=candidate, summary=first))
    right = dict(derive_role_values_for_split_v1(candidate=candidate, summary=second))
    return tuple((role, max(left[role], right[role])) for role in V4_NUMERIC_ROLES)


@dataclass(frozen=True)
class ExactRatioV1:
    numerator: int
    denominator: int
    defined: bool
    undefined_reason: str | None

    @classmethod
    def build(cls, numerator: int, denominator: int, *, empty_reason: str) -> "ExactRatioV1":
        _strict_int(numerator, "numerator")
        _strict_int(denominator, "denominator")
        if denominator == 0:
            if numerator != 0:
                _fail("EXP02_RATIO_IMPOSSIBLE", "nonzero numerator with empty denominator")
            return cls(0, 0, False, empty_reason)
        if numerator > denominator and "EXPOSURE" not in empty_reason:
            _fail("EXP02_RATIO_NUMERATOR_EXCEEDS_DENOMINATOR", "bounded ratio numerator exceeds denominator")
        return cls(numerator, denominator, True, None)

    @property
    def fraction(self) -> Fraction:
        if not self.defined:
            _fail("EXP02_UNDEFINED_RATIO_ACCESS", "undefined ratio has no numeric value")
        return Fraction(self.numerator, self.denominator)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class NormalPolicySelectionAuthorityV1:
    authority_id: str
    protocol_hash: str
    source_commit: str
    split_id: str
    candidate_set_hash: str
    cohort_hash: str
    cohort_relations: int
    train4_input_hash: str
    normal_exposure_seconds: int
    metric_contract_hash: str
    selection_only: bool
    runtime_authority: bool
    labels_allowed: bool
    authority_hash: str

    def __post_init__(self) -> None:
        for name in ("selection_only", "runtime_authority", "labels_allowed"):
            if type(getattr(self, name)) is not bool:
                _fail("EXP02_SELECTION_AUTHORITY_BOOLEAN_INVALID", f"{name} must be an exact Boolean")
        _strict_int(self.cohort_relations, "cohort_relations")
        _strict_int(self.normal_exposure_seconds, "normal_exposure_seconds")
        if self.cohort_relations <= 0 or self.normal_exposure_seconds <= 0:
            _fail("EXP02_SELECTION_AUTHORITY_COUNT_INVALID", "cohort and exposure must be positive")

    def body_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_exp02_normal_selection_authority_v1",
            **{key: value for key, value in self.__dict__.items() if key != "authority_hash"},
            "schema_version": "1.0.0",
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body_dict(), "authority_hash": self.authority_hash}


def build_normal_policy_selection_authority_v1(
    *, protocol: ValidationProtocolV1, candidate_set_hash: str,
    cohort_hash: str, cohort_relations: int, train4_input_hash: str,
    normal_exposure_seconds: int, metric_contract_hash: str,
) -> NormalPolicySelectionAuthorityV1:
    validate_validation_protocol_v1(protocol)
    for name, value in (
        ("candidate_set_hash", candidate_set_hash),
        ("cohort_hash", cohort_hash), ("train4_input_hash", train4_input_hash),
        ("metric_contract_hash", metric_contract_hash),
    ):
        _sha(value, name)
    _strict_int(cohort_relations, "cohort_relations")
    _strict_int(normal_exposure_seconds, "normal_exposure_seconds")
    if cohort_relations <= 0 or normal_exposure_seconds <= 0:
        _fail("EXP02_SELECTION_AUTHORITY_COUNT_INVALID", "cohort and exposure must be positive")
    assignments = {item.split_id: item for item in protocol.split_assignments}
    selection = assignments.get(EXP02_SELECTION_SPLIT)
    if (
        selection is None
        or selection.role is not SplitRoleV1.NORMAL_POLICY_SELECTION_SANITY
        or selection.labels_allowed
        or ProtocolOperationV1.NORMAL_POLICY_SELECTION not in selection.allowed_operations
    ):
        _fail("EXP02_PROTOCOL_SELECTION_ROLE_INVALID", "protocol does not authorize label-free train4 selection")
    provisional = NormalPolicySelectionAuthorityV1(
        "EXP02-TRAIN4-SELECTION-AUTHORITY-V1", protocol.protocol_hash, protocol.source_commit,
        EXP02_SELECTION_SPLIT, candidate_set_hash, cohort_hash, cohort_relations, train4_input_hash,
        normal_exposure_seconds, metric_contract_hash, True, False, False, "",
    )
    return NormalPolicySelectionAuthorityV1(
        **{**provisional.__dict__, "authority_hash": _hash_document(provisional.body_dict())}
    )


def validate_normal_policy_selection_authority_v1(
    value: NormalPolicySelectionAuthorityV1, *, protocol: ValidationProtocolV1,
) -> str:
    if type(value) is not NormalPolicySelectionAuthorityV1:
        _fail("EXP02_SELECTION_AUTHORITY_TYPE_INVALID", "selection authority type differs")
    expected = build_normal_policy_selection_authority_v1(
        protocol=protocol,
        candidate_set_hash=value.candidate_set_hash, cohort_hash=value.cohort_hash,
        cohort_relations=value.cohort_relations,
        train4_input_hash=value.train4_input_hash,
        normal_exposure_seconds=value.normal_exposure_seconds,
        metric_contract_hash=value.metric_contract_hash,
    )
    if value != expected:
        _fail("EXP02_SELECTION_AUTHORITY_REPLAY_MISMATCH", "selection authority differs from replay")
    if value.runtime_authority or value.labels_allowed or not value.selection_only:
        _fail("EXP02_SELECTION_AUTHORITY_ESCALATION", "train4 authority is selection-only")
    return value.authority_hash


@dataclass(frozen=True)
class NumericPolicySelectionSummaryV1:
    candidate_hash: str
    selection_authority_hash: str
    cohort_hash: str
    retained_relations: int
    cohort_relations: int
    opportunity_relations: int
    pass_count: int
    fail_count: int
    abstain_count: int
    unsupported_relation_count: int
    system_error_count: int
    false_alarm_seconds: int
    false_alarm_episodes: int
    normal_exposure_seconds: int
    split_variability_numerator: int
    split_variability_denominator: int
    summary_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_exp02_numeric_policy_selection_summary_v1",
            **{key: value for key, value in self.__dict__.items() if key != "summary_hash"},
            "schema_version": "1.0.0",
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body_dict(), "summary_hash": self.summary_hash}

    @property
    def relation_retention(self) -> ExactRatioV1:
        return ExactRatioV1.build(self.retained_relations, self.cohort_relations, empty_reason="EMPTY_CONFIRMED_COHORT")

    @property
    def opportunity_coverage(self) -> ExactRatioV1:
        return ExactRatioV1.build(self.opportunity_relations, self.retained_relations, empty_reason="ZERO_RETAINED_RELATIONS")

    @property
    def evaluation_coverage(self) -> ExactRatioV1:
        evaluated = self.pass_count + self.fail_count
        total = evaluated + self.abstain_count
        return ExactRatioV1.build(evaluated, total, empty_reason="ZERO_RUNTIME_OPPORTUNITIES")

    @property
    def abstain_rate(self) -> ExactRatioV1:
        total = self.pass_count + self.fail_count + self.abstain_count
        return ExactRatioV1.build(self.abstain_count, total, empty_reason="ZERO_RUNTIME_OPPORTUNITIES")

    @property
    def false_alarm_seconds_per_hour(self) -> ExactRatioV1:
        return ExactRatioV1.build(self.false_alarm_seconds * 3600, self.normal_exposure_seconds, empty_reason="ZERO_NORMAL_EXPOSURE")

    @property
    def false_alarm_episodes_per_hour(self) -> ExactRatioV1:
        return ExactRatioV1.build(self.false_alarm_episodes * 3600, self.normal_exposure_seconds, empty_reason="ZERO_NORMAL_EXPOSURE")

    @property
    def split_variability(self) -> Fraction:
        if self.split_variability_denominator == 0:
            _fail("EXP02_UNDEFINED_SPLIT_VARIABILITY", "split variability denominator is zero")
        return Fraction(self.split_variability_numerator, self.split_variability_denominator)


def build_numeric_policy_selection_summary_v1(
    *, candidate: NumericPolicyCandidateV1,
    selection_authority: NormalPolicySelectionAuthorityV1,
    protocol: ValidationProtocolV1,
    retained_relations: int, cohort_relations: int, opportunity_relations: int,
    pass_count: int, fail_count: int, abstain_count: int, system_error_count: int,
    unsupported_relation_count: int = 0,
    false_alarm_seconds: int, false_alarm_episodes: int,
    normal_exposure_seconds: int, split_variability: Fraction,
) -> NumericPolicySelectionSummaryV1:
    validate_numeric_policy_candidate_v1(candidate)
    validate_normal_policy_selection_authority_v1(selection_authority, protocol=protocol)
    if candidate.cohort_hash != selection_authority.cohort_hash:
        _fail("EXP02_SELECTION_COHORT_MISMATCH", "candidate and selection cohort differ")
    for name, value in (
        ("retained_relations", retained_relations), ("cohort_relations", cohort_relations),
        ("opportunity_relations", opportunity_relations), ("pass_count", pass_count),
        ("fail_count", fail_count), ("abstain_count", abstain_count),
        ("unsupported_relation_count", unsupported_relation_count),
        ("system_error_count", system_error_count), ("false_alarm_seconds", false_alarm_seconds),
        ("false_alarm_episodes", false_alarm_episodes),
        ("normal_exposure_seconds", normal_exposure_seconds),
    ):
        _strict_int(value, name)
    if retained_relations > cohort_relations or opportunity_relations > retained_relations:
        _fail("EXP02_SELECTION_COUNT_INCONSISTENT", "retention/opportunity counts are inconsistent")
    if false_alarm_seconds > normal_exposure_seconds:
        _fail("EXP02_FALSE_ALARM_SECONDS_EXCEED_EXPOSURE", "alarm seconds exceed exposure")
    if false_alarm_episodes > false_alarm_seconds:
        _fail("EXP02_FALSE_ALARM_EPISODES_EXCEED_SECONDS", "false-alarm episodes exceed alarm seconds")
    if cohort_relations != selection_authority.cohort_relations:
        _fail("EXP02_SELECTION_COHORT_CARDINALITY_MISMATCH", "summary cohort cardinality differs from authority")
    if normal_exposure_seconds != selection_authority.normal_exposure_seconds:
        _fail("EXP02_SELECTION_EXPOSURE_MISMATCH", "summary normal exposure differs from authority")
    if type(split_variability) is not Fraction or split_variability < 0:
        _fail("EXP02_SPLIT_VARIABILITY_INVALID", "split variability must be a nonnegative Fraction")
    if candidate.source_commit != selection_authority.source_commit:
        _fail("EXP02_SELECTION_SOURCE_COMMIT_MISMATCH", "candidate and selection authority commits differ")
    provisional = NumericPolicySelectionSummaryV1(
        candidate.candidate_hash, selection_authority.authority_hash,
        candidate.cohort_hash, retained_relations, cohort_relations,
        opportunity_relations, pass_count, fail_count, abstain_count,
        unsupported_relation_count, system_error_count, false_alarm_seconds, false_alarm_episodes,
        normal_exposure_seconds, split_variability.numerator,
        split_variability.denominator, "",
    )
    # Force undefined semantics to be materialized during construction.
    _ = (
        provisional.relation_retention, provisional.opportunity_coverage,
        provisional.evaluation_coverage, provisional.abstain_rate,
        provisional.false_alarm_seconds_per_hour,
        provisional.false_alarm_episodes_per_hour, provisional.split_variability,
    )
    return NumericPolicySelectionSummaryV1(
        **{**provisional.__dict__, "summary_hash": _hash_document(provisional.body_dict())}
    )


def validate_numeric_policy_selection_summary_v1(
    value: NumericPolicySelectionSummaryV1, *, candidate: NumericPolicyCandidateV1,
    selection_authority: NormalPolicySelectionAuthorityV1, protocol: ValidationProtocolV1,
) -> str:
    if type(value) is not NumericPolicySelectionSummaryV1:
        _fail("EXP02_SELECTION_SUMMARY_TYPE_INVALID", "selection summary type differs")
    expected = build_numeric_policy_selection_summary_v1(
        candidate=candidate, selection_authority=selection_authority, protocol=protocol,
        retained_relations=value.retained_relations, cohort_relations=value.cohort_relations,
        opportunity_relations=value.opportunity_relations, pass_count=value.pass_count,
        fail_count=value.fail_count, abstain_count=value.abstain_count,
        unsupported_relation_count=value.unsupported_relation_count,
        system_error_count=value.system_error_count,
        false_alarm_seconds=value.false_alarm_seconds,
        false_alarm_episodes=value.false_alarm_episodes,
        normal_exposure_seconds=value.normal_exposure_seconds,
        split_variability=Fraction(value.split_variability_numerator, value.split_variability_denominator),
    )
    if value != expected:
        _fail("EXP02_SELECTION_SUMMARY_REPLAY_MISMATCH", "selection summary differs from replay")
    return value.summary_hash


@dataclass(frozen=True)
class NumericPolicySelectionResultV1:
    candidate_set_hash: str
    selection_authority_hash: str
    selected_candidate_hash: str
    selected_candidate_id: str
    eligible_candidate_hashes: tuple[str, ...]
    rejected: tuple[tuple[str, str], ...]
    selection_rule: str
    result_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_exp02_numeric_policy_selection_result_v1",
            **{key: list(value) if type(value) is tuple else value for key, value in self.__dict__.items() if key != "result_hash"},
            "schema_version": "1.0.0",
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body_dict(), "result_hash": self.result_hash}


def validate_numeric_policy_selection_result_v1(
    value: NumericPolicySelectionResultV1,
    *,
    candidates: Sequence[NumericPolicyCandidateV1],
    selection_authority: NormalPolicySelectionAuthorityV1,
    protocol: ValidationProtocolV1,
) -> str:
    if type(value) is not NumericPolicySelectionResultV1:
        _fail("EXP02_SELECTION_RESULT_TYPE_INVALID", "selection result type differs")
    validate_normal_policy_selection_authority_v1(selection_authority, protocol=protocol)
    if value.result_hash != _hash_document(value.body_dict()):
        _fail("EXP02_SELECTION_RESULT_HASH_MISMATCH", "selection result self-hash differs")
    by_hash = {item.candidate_hash: item for item in candidates}
    if len(by_hash) != len(candidates) or candidate_set_hash_v1(candidates) != value.candidate_set_hash:
        _fail("EXP02_SELECTION_RESULT_CANDIDATE_SET_MISMATCH", "result candidate set differs")
    if value.selection_authority_hash != selection_authority.authority_hash:
        _fail("EXP02_SELECTION_RESULT_AUTHORITY_MISMATCH", "result authority differs")
    selected = by_hash.get(value.selected_candidate_hash)
    if selected is None or selected.candidate_id != value.selected_candidate_id:
        _fail("EXP02_SELECTION_RESULT_SELECTED_MISMATCH", "selected candidate identity differs")
    eligible = tuple(value.eligible_candidate_hashes)
    rejected = tuple(hash_value for hash_value, _ in value.rejected)
    if (
        len(set(eligible)) != len(eligible)
        or len(set(rejected)) != len(rejected)
        or set(eligible) & set(rejected)
        or set(eligible) | set(rejected) != set(by_hash)
        or value.selected_candidate_hash not in eligible
    ):
        _fail("EXP02_SELECTION_RESULT_PARTITION_INVALID", "eligible/rejected partition differs")
    return value.result_hash


def _complexity(candidate: NumericPolicyCandidateV1) -> int:
    return COMPLEXITY_ORDER.index(candidate.family.value)


def _require_defined(metric: ExactRatioV1, name: str) -> Fraction:
    if not metric.defined:
        _fail("EXP02_SELECTION_METRIC_UNDEFINED", f"{name}:{metric.undefined_reason}")
    return metric.fraction


def select_numeric_policy_on_train4_v1(
    *, candidates: Sequence[NumericPolicyCandidateV1],
    summaries: Sequence[NumericPolicySelectionSummaryV1],
    selection_authority: NormalPolicySelectionAuthorityV1,
    protocol: ValidationProtocolV1,
) -> NumericPolicySelectionResultV1:
    candidate_hash = candidate_set_hash_v1(candidates)
    validate_normal_policy_selection_authority_v1(selection_authority, protocol=protocol)
    if candidate_hash != selection_authority.candidate_set_hash:
        _fail("EXP02_SELECTION_CANDIDATE_SET_MISMATCH", "selection authority binds another candidate set")
    by_hash = {item.candidate_hash: item for item in candidates}
    if type(summaries) not in (tuple, list) or len(summaries) != len(candidates):
        _fail("EXP02_SELECTION_SUMMARY_COVERAGE_INVALID", "one summary per candidate is required")
    summary_by_hash: dict[str, NumericPolicySelectionSummaryV1] = {}
    for summary in summaries:
        if type(summary) is not NumericPolicySelectionSummaryV1 or summary.candidate_hash not in by_hash:
            _fail("EXP02_SELECTION_SUMMARY_FOREIGN", "summary candidate is foreign")
        if summary.candidate_hash in summary_by_hash:
            _fail("EXP02_SELECTION_SUMMARY_DUPLICATE", "summary candidate duplicates")
        validate_numeric_policy_selection_summary_v1(
            summary, candidate=by_hash[summary.candidate_hash],
            selection_authority=selection_authority, protocol=protocol,
        )
        summary_by_hash[summary.candidate_hash] = summary
    baseline_candidates = [item for item in candidates if item.family is NumericPolicyFamilyV1.COMMON_FIXED_NORMALIZED_V1]
    baseline = summary_by_hash[baseline_candidates[0].candidate_hash]
    if baseline.system_error_count != 0 or baseline.unsupported_relation_count != 0:
        _fail("EXP02_BASELINE_EXPLICIT_FAILURE", "common baseline has a system or unsupported-relation failure")
    baseline_guards = (
        _require_defined(baseline.relation_retention, "baseline_relation_retention"),
        _require_defined(baseline.opportunity_coverage, "baseline_opportunity_coverage"),
        _require_defined(baseline.evaluation_coverage, "baseline_evaluation_coverage"),
    )
    eligible: list[tuple[tuple[Any, ...], NumericPolicyCandidateV1]] = []
    rejected: list[tuple[str, str]] = []
    for candidate in sorted(candidates, key=lambda item: item.candidate_id):
        summary = summary_by_hash[candidate.candidate_hash]
        reason: str | None = None
        if summary.unsupported_relation_count != 0:
            reason = "UNSUPPORTED_RELATION_NONZERO"
        elif summary.system_error_count != 0:
            reason = "SYSTEM_ERROR_NONZERO"
        else:
            try:
                guards = (
                    _require_defined(summary.relation_retention, "relation_retention"),
                    _require_defined(summary.opportunity_coverage, "opportunity_coverage"),
                    _require_defined(summary.evaluation_coverage, "evaluation_coverage"),
                )
                if any(observed < required for observed, required in zip(guards, baseline_guards)):
                    reason = "STRICT_NONINFERIORITY_GUARD_FAILED"
                else:
                    key = (
                        _require_defined(summary.false_alarm_seconds_per_hour, "false_alarm_seconds_per_hour"),
                        _require_defined(summary.false_alarm_episodes_per_hour, "false_alarm_episodes_per_hour"),
                        _require_defined(summary.abstain_rate, "abstain_rate"),
                        summary.split_variability,
                        _complexity(candidate), candidate.candidate_id,
                    )
                    eligible.append((key, candidate))
            except NumericPolicyError as exc:
                reason = exc.issue_code
        if reason is not None:
            rejected.append((candidate.candidate_hash, reason))
    if not eligible:
        _fail("EXP02_NO_ELIGIBLE_POLICY", "no candidate satisfies the frozen selection contract")
    selected = min(eligible, key=lambda item: item[0])[1]
    provisional = NumericPolicySelectionResultV1(
        candidate_hash, selection_authority.authority_hash,
        selected.candidate_hash, selected.candidate_id,
        tuple(sorted(item.candidate_hash for _, item in eligible)),
        tuple(sorted(rejected)),
        "LEXICOGRAPHIC:FALSE_SECONDS,FALSE_EPISODES,ABSTAIN,MAX_SPLIT_VARIABILITY,FAMILY_COMPLEXITY,CANDIDATE_ID",
        "",
    )
    return NumericPolicySelectionResultV1(
        **{**provisional.__dict__, "result_hash": _hash_document(provisional.body_dict())}
    )


@dataclass(frozen=True)
class DiagnosticNumericProposalV1:
    proposal_id: str
    provider_receipt_hash: str
    validity_authority: bool = False
    runtime_authority: bool = False
    may_select_main_policy: bool = False

    def __post_init__(self) -> None:
        _text(self.proposal_id, "proposal_id")
        _sha(self.provider_receipt_hash, "provider_receipt_hash")
        if self.validity_authority or self.runtime_authority or self.may_select_main_policy:
            _fail("EXP02_DIAGNOSTIC_AUTHORITY_ESCALATION", "LLM diagnostic cannot govern the main experiment")


__all__ = [
    "COMMON_FORMULA_IDS", "COMPLEXITY_ORDER", "ConfirmedCohortAuthorityV1",
    "ConfirmedRelationIdentityV1", "DiagnosticNumericProposalV1", "EXP02_CONFIRMATION_SPLIT",
    "EXP02_DEVELOPMENT_SPLIT", "EXP02_FIT_SPLITS", "EXP02_NUMERIC_POLICY_VERSION",
    "EXP02_PROVIDER_CALLS_REQUIRED", "EXP02_SELECTION_SPLIT", "ExactRatioV1",
    "FIT_SPLIT_VARIABILITY_STATISTIC", "FROZEN_WINDOW_VALUES", "GUARD_POLICY",
    "NormalPolicySelectionAuthorityV1", "NumericPolicyCandidateV1", "NumericPolicyError",
    "NumericPolicyFamilyV1", "NumericPolicySelectionResultV1", "NumericPolicySelectionSummaryV1",
    "NumericRoleScopeV1", "RELATION_FORMULA_IDS", "RelationSpecificGridPointV1",
    "SplitNormalSummaryV1", "build_confirmed_cohort_authority_v1",
    "build_normal_policy_selection_authority_v1", "build_numeric_policy_candidate_set_v1",
    "build_numeric_policy_selection_summary_v1", "build_split_normal_summary_v1",
    "candidate_set_hash_v1", "derive_role_values_for_split_v1", "derive_pooled_role_values_v1",
    "fit_split_variability_v1", "frozen_relation_specific_grid_v1",
    "select_numeric_policy_on_train4_v1", "symmetric_relative_difference_v1",
    "validate_confirmed_cohort_authority_v1", "validate_normal_policy_selection_authority_v1",
    "validate_numeric_policy_candidate_v1", "validate_numeric_policy_selection_result_v1",
    "validate_numeric_policy_selection_summary_v1",
    "validate_split_normal_summary_v1",
]
