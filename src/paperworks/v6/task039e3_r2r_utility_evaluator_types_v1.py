"""Shared, side-effect-free types for Utility Evaluator V1.

This module contains no file, environment, network, provider, or private
authority access.  ``SYNTHETIC_CONTRACT_ONLY`` is a structurally separate
execution plane and can never be promoted to scientific utility evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
import hashlib
import json
import math
from typing import Any


EVALUATOR_VERSION = "TASK039E3_R2R_UTILITY_EVALUATOR_V1"
SYNTHETIC_CONTRACT_ONLY = "SYNTHETIC_CONTRACT_ONLY"
REAL_AUTHORIZED_UTILITY_EXECUTION = "REAL_AUTHORIZED_UTILITY_EXECUTION"
REAL_UTILITY_EXECUTION_AUTHORIZED = False


class UtilityEvaluatorV1Error(ValueError):
    """A fail-closed evaluator authority, input, execution, or metric error."""


def canonical_json_bytes_v1(payload: object) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def stable_hash_v1(payload: object) -> str:
    return hashlib.sha256(canonical_json_bytes_v1(payload)).hexdigest()


def strict_str_v1(value: object, name: str) -> str:
    if type(value) is not str or not value:
        raise UtilityEvaluatorV1Error(f"{name} must be an exact nonempty string")
    return value


def strict_sha256_v1(value: object, name: str) -> str:
    text = strict_str_v1(value, name)
    if len(text) != 64 or any(char not in "0123456789abcdef" for char in text):
        raise UtilityEvaluatorV1Error(f"{name} must be a lowercase SHA-256")
    return text


def strict_int_v1(value: object, name: str, *, minimum: int | None = None) -> int:
    if type(value) is not int:
        raise UtilityEvaluatorV1Error(f"{name} must be an exact integer")
    if minimum is not None and value < minimum:
        raise UtilityEvaluatorV1Error(f"{name} is below its canonical minimum")
    return value


def strict_bool_v1(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise UtilityEvaluatorV1Error(f"{name} must be an exact boolean")
    return value


def strict_float_v1(
    value: object,
    name: str,
    *,
    positive: bool = False,
    nonnegative: bool = False,
) -> float:
    if type(value) is not float or not math.isfinite(value):
        raise UtilityEvaluatorV1Error(f"{name} must be an exact finite float")
    if positive and value <= 0.0:
        raise UtilityEvaluatorV1Error(f"{name} must be positive")
    if nonnegative and value < 0.0:
        raise UtilityEvaluatorV1Error(f"{name} must be nonnegative")
    return value


def strict_tuple_v1(value: object, name: str) -> tuple[object, ...]:
    if type(value) is not tuple:
        raise UtilityEvaluatorV1Error(f"{name} must be an exact tuple")
    return value


def dataclass_payload_v1(value: object, *, exclude: tuple[str, ...] = ()) -> dict[str, Any]:
    if not is_dataclass(value) or isinstance(value, type):
        raise UtilityEvaluatorV1Error("canonical payload requires a dataclass instance")
    return {
        field.name: _json_value_v1(getattr(value, field.name))
        for field in fields(value)
        if field.name not in exclude
    }


def _json_value_v1(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return dataclass_payload_v1(value)
    if type(value) is tuple:
        return [_json_value_v1(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_value_v1(item) for key, item in value.items()}
    return value


SYNTHETIC_AUTHORITY_IDENTITY = stable_hash_v1(
    {
        "artifact_type": "task039e3_r2r_utility_evaluator_v1_synthetic_authority",
        "evaluator_version": EVALUATOR_VERSION,
        "execution_mode": SYNTHETIC_CONTRACT_ONLY,
        "scientific_eligibility": False,
        "real_private_authority": False,
        "real_hai": False,
        "real_labels": False,
    }
)


@dataclass(frozen=True)
class SyntheticFeatureRowV1:
    physical_row_index: int
    timestamp_second: int
    feature_values: tuple[tuple[str, float], ...]
    row_identity: str


@dataclass(frozen=True)
class SyntheticFeatureFrameV1:
    execution_mode: str
    synthetic_authority_identity: str
    dataset_manifest_identity: str
    split_identity: str
    source_file_identity: str
    feature_schema_authority_hash: str
    ordered_features: tuple[str, ...]
    rows: tuple[SyntheticFeatureRowV1, ...]
    frame_hash: str


@dataclass(frozen=True)
class RetainedSourceEventV1:
    source: str
    physical_row_index: int
    direction: str
    amplitude: float
    source_event_identity: str


@dataclass(frozen=True)
class IsolatedSourceEventV1:
    retained_event: RetainedSourceEventV1
    source_census_identity: str
    isolation_policy_hash: str
    isolated_event_identity: str


@dataclass(frozen=True)
class CanonicalOpportunityEnvelopeV1:
    isolated_source_event_identity: str
    canonical_opportunity: object
    envelope_hash: str


@dataclass(frozen=True)
class FullCensusResultV1:
    execution_mode: str
    source_census_identity: str
    raw_source_event_count: int
    retained_source_event_count: int
    isolated_source_event_count: int
    relation_opportunities: tuple[CanonicalOpportunityEnvelopeV1, ...]
    denominator_policy: str
    census_hash: str


@dataclass(frozen=True)
class RuleExecutionResultV1:
    execution_mode: str
    opportunity_id: str
    source_event_identity: str
    relation_binding_hash: str
    source_qualification_identity: str | None
    target_evaluation_identity: str | None
    final_state: str
    alarm_emitted: bool
    decision_physical_row_index: int | None
    numeric_reference_identities: tuple[str, ...]
    evaluator_computation_identity: str
    trace_hash: str


@dataclass(frozen=True)
class EvaluatorAccessCountersV1:
    main_private_registry_reads: int = 0
    supplement_private_registry_reads: int = 0
    private_locator_reads: int = 0
    hai_train1_reads: int = 0
    hai_train2_reads: int = 0
    hai_train3_reads: int = 0
    hai_train4_reads: int = 0
    hai_test1_reads: int = 0
    hai_test2_reads: int = 0
    label_reads: int = 0
    attack_interval_reads: int = 0
    detector_executions: int = 0
    real_utility_computations: int = 0
    provider_calls: int = 0
    scientific_llm_calls: int = 0
    api_key_access: bool = False
    network_requests: int = 0


ZERO_REAL_ACCESS_COUNTERS = EvaluatorAccessCountersV1()


__all__ = [
    "EVALUATOR_VERSION",
    "SYNTHETIC_CONTRACT_ONLY",
    "REAL_AUTHORIZED_UTILITY_EXECUTION",
    "REAL_UTILITY_EXECUTION_AUTHORIZED",
    "SYNTHETIC_AUTHORITY_IDENTITY",
    "UtilityEvaluatorV1Error",
    "canonical_json_bytes_v1",
    "stable_hash_v1",
    "strict_str_v1",
    "strict_sha256_v1",
    "strict_int_v1",
    "strict_bool_v1",
    "strict_float_v1",
    "strict_tuple_v1",
    "dataclass_payload_v1",
    "SyntheticFeatureRowV1",
    "SyntheticFeatureFrameV1",
    "RetainedSourceEventV1",
    "IsolatedSourceEventV1",
    "CanonicalOpportunityEnvelopeV1",
    "FullCensusResultV1",
    "RuleExecutionResultV1",
    "EvaluatorAccessCountersV1",
    "ZERO_REAL_ACCESS_COUNTERS",
]
