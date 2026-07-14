"""Immutable TASK-030 deterministic calibration parameter model."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from paperworks.contracts.artifact_hashing import (
    ContractArtifactHashError,
    canonical_contract_artifact_sha256,
    verify_contract_artifact_hash,
)
from paperworks.contracts.schema_registry import SchemaRegistry, load_schema_registry


SUPPORTED_PARAMETER_ROLES = frozenset({"lag_minimum", "lag_maximum", "response_delay", "tolerance", "persistence_duration", "minimum_support"})
SUPPORTED_PARAMETER_PREFIXES = ("PARAM-LAG-", "PARAM-TOL-", "PARAM-DURATION-", "PARAM-SUPPORT-")


class ParameterV1ModelError(ValueError):
    def __init__(self, issue_code: str, field_path: str, message: str) -> None:
        super().__init__(f"{issue_code} at {field_path}: {message}")
        self.issue_code = issue_code
        self.field_path = field_path
        self.message = message


@dataclass(frozen=True)
class ParameterSampleSupportV1:
    event_count: int
    matched_count: int
    normal_reference_count: int
    minimum_required: int


@dataclass(frozen=True)
class ParameterStabilityV1:
    status: str
    method: str
    replicate_count: int
    variation_measure: int | float | None


@dataclass(frozen=True)
class ParameterConfidenceIntervalV1:
    level: int | float
    lower: int | float
    upper: int | float
    method: str


@dataclass(frozen=True)
class ParameterUncertaintyV1:
    status: str
    sources: tuple[str, ...]


@dataclass(frozen=True)
class CalibrationParameterV1:
    schema_version: str
    parameter_id: str
    parameter_version: str
    parameter_role: str
    value: int | float
    unit: str
    relation_family: str
    source_variables: tuple[str, ...]
    target_variables: tuple[str, ...]
    operating_regime: str
    calibration_method: str
    calibration_split: str
    calibration_window_refs: tuple[str, ...]
    normal_reference_refs: tuple[str, ...]
    sample_support: ParameterSampleSupportV1
    stability_summary: ParameterStabilityV1
    confidence_interval: ParameterConfidenceIntervalV1
    uncertainty: ParameterUncertaintyV1
    dataset_version: str
    code_commit: str
    calibrator_version: str
    artifact_hash: str
    approval_status: str
    approved_by: str | None
    approval_date: str | None

    @property
    def runtime_authorized(self) -> bool:
        return False


def parse_calibration_parameter(
    document: Mapping[str, object], *, registry: SchemaRegistry | None = None
) -> CalibrationParameterV1:
    snapshot = copy.deepcopy(dict(document))
    report = (registry or load_schema_registry()).validate_artifact("parameter_registry", snapshot)
    if report.status != "valid":
        issue = report.issues[0] if report.issues else None
        _fail("PARAMETER_V1_STRUCTURAL_INVALID", issue.instance_path if issue else "/", issue.issue_code if issue else "registry error")
    try:
        verify_contract_artifact_hash(snapshot)
    except ContractArtifactHashError as exc:
        _fail(exc.issue_code, "/artifact_hash", exc.message)
    parameter = _typed_parameter(snapshot)
    _validate_parameter(parameter)
    return parameter


def load_calibration_parameter(path: str | Path, *, registry: SchemaRegistry | None = None) -> CalibrationParameterV1:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ParameterV1ModelError("PARAMETER_V1_STRUCTURAL_INVALID", "/", "artifact is not readable UTF-8 JSON") from exc
    if not isinstance(document, dict):
        _fail("PARAMETER_V1_STRUCTURAL_INVALID", "/", "artifact must be a JSON object")
    return parse_calibration_parameter(document, registry=registry)


def calibration_parameter_to_dict(parameter: CalibrationParameterV1) -> dict[str, Any]:
    return {
        "schema_version": parameter.schema_version, "parameter_id": parameter.parameter_id,
        "parameter_version": parameter.parameter_version, "parameter_role": parameter.parameter_role,
        "value": parameter.value, "unit": parameter.unit, "relation_family": parameter.relation_family,
        "source_variables": list(parameter.source_variables), "target_variables": list(parameter.target_variables),
        "operating_regime": parameter.operating_regime, "calibration_method": parameter.calibration_method,
        "calibration_split": parameter.calibration_split, "calibration_window_refs": list(parameter.calibration_window_refs),
        "normal_reference_refs": list(parameter.normal_reference_refs),
        "sample_support": {"event_count": parameter.sample_support.event_count,
            "matched_count": parameter.sample_support.matched_count,
            "normal_reference_count": parameter.sample_support.normal_reference_count,
            "minimum_required": parameter.sample_support.minimum_required},
        "stability_summary": {"status": parameter.stability_summary.status, "method": parameter.stability_summary.method,
            "replicate_count": parameter.stability_summary.replicate_count,
            "variation_measure": parameter.stability_summary.variation_measure},
        "confidence_interval": {"level": parameter.confidence_interval.level,
            "lower": parameter.confidence_interval.lower, "upper": parameter.confidence_interval.upper,
            "method": parameter.confidence_interval.method},
        "uncertainty": {"status": parameter.uncertainty.status, "sources": list(parameter.uncertainty.sources)},
        "dataset_version": parameter.dataset_version, "code_commit": parameter.code_commit,
        "calibrator_version": parameter.calibrator_version, "artifact_hash": parameter.artifact_hash,
        "approval_status": parameter.approval_status, "approved_by": parameter.approved_by,
        "approval_date": parameter.approval_date,
    }


def serialize_calibration_parameter(parameter: CalibrationParameterV1) -> str:
    return json.dumps(calibration_parameter_to_dict(parameter), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def canonical_calibration_parameter_sha256(parameter: CalibrationParameterV1) -> str:
    return canonical_contract_artifact_sha256(calibration_parameter_to_dict(parameter))


def _typed_parameter(document: Mapping[str, Any]) -> CalibrationParameterV1:
    support, stability, interval, uncertainty = document["sample_support"], document["stability_summary"], document["confidence_interval"], document["uncertainty"]
    return CalibrationParameterV1(
        schema_version=document["schema_version"], parameter_id=document["parameter_id"], parameter_version=document["parameter_version"],
        parameter_role=document["parameter_role"], value=document["value"], unit=document["unit"], relation_family=document["relation_family"],
        source_variables=tuple(document["source_variables"]), target_variables=tuple(document["target_variables"]),
        operating_regime=document["operating_regime"], calibration_method=document["calibration_method"], calibration_split=document["calibration_split"],
        calibration_window_refs=tuple(document["calibration_window_refs"]), normal_reference_refs=tuple(document["normal_reference_refs"]),
        sample_support=ParameterSampleSupportV1(support["event_count"], support["matched_count"], support["normal_reference_count"], support["minimum_required"]),
        stability_summary=ParameterStabilityV1(stability["status"], stability["method"], stability["replicate_count"], stability["variation_measure"]),
        confidence_interval=ParameterConfidenceIntervalV1(interval["level"], interval["lower"], interval["upper"], interval["method"]),
        uncertainty=ParameterUncertaintyV1(uncertainty["status"], tuple(uncertainty["sources"])),
        dataset_version=document["dataset_version"], code_commit=document["code_commit"], calibrator_version=document["calibrator_version"],
        artifact_hash=document["artifact_hash"], approval_status=document["approval_status"], approved_by=document["approved_by"], approval_date=document["approval_date"],
    )


def _validate_parameter(parameter: CalibrationParameterV1) -> None:
    if parameter.parameter_role not in SUPPORTED_PARAMETER_ROLES:
        _fail("PARAMETER_V1_UNSUPPORTED_ROLE", "/parameter_role", "role is outside delayed-response MVP")
    if not parameter.parameter_id.startswith(SUPPORTED_PARAMETER_PREFIXES):
        _fail("PARAMETER_V1_UNSUPPORTED_PREFIX", "/parameter_id", "parameter prefix is outside delayed-response MVP")
    if parameter.relation_family != "delayed_response":
        _fail("PARAMETER_V1_RELATION_FAMILY", "/relation_family", "only delayed_response is supported")
    if len(parameter.source_variables) != 1 or len(parameter.target_variables) != 1:
        _fail("PARAMETER_V1_CARDINALITY", "/source_variables", "exactly one source and one target are required")
    if parameter.confidence_interval.lower > parameter.confidence_interval.upper:
        _fail("PARAMETER_V1_CONFIDENCE_ORDER", "/confidence_interval", "confidence interval is inverted")
    if parameter.sample_support.matched_count > parameter.sample_support.event_count:
        _fail("PARAMETER_V1_SUPPORT_COUNTS", "/sample_support/matched_count", "matched count exceeds event count")
    if parameter.sample_support.normal_reference_count < 0:
        _fail("PARAMETER_V1_SUPPORT_COUNTS", "/sample_support/normal_reference_count", "normal reference count is negative")
    stability = parameter.stability_summary
    if stability.status == "not_estimated" and (stability.method != "not_estimated" or stability.replicate_count != 0 or stability.variation_measure is not None):
        _fail("PARAMETER_V1_STABILITY", "/stability_summary", "not-estimated stability fields are inconsistent")
    if stability.status in {"stable", "unstable"} and stability.method == "not_estimated":
        _fail("PARAMETER_V1_STABILITY", "/stability_summary", "estimated stability requires an estimation method")
    if parameter.approval_status in {"calibrated", "approved"} and stability.status != "stable":
        _fail("PARAMETER_V1_STATUS_STABILITY", "/approval_status", "calibrated or approved status requires stable calibration")
    if parameter.approval_status == "unstable" and stability.status != "unstable":
        _fail("PARAMETER_V1_STATUS_STABILITY", "/approval_status", "unstable approval status requires unstable stability")
    if parameter.approval_status == "approved":
        if parameter.approved_by is None or parameter.approval_date is None:
            _fail("PARAMETER_V1_APPROVER_MISSING", "/approved_by", "approved parameter requires approver and date")


def _fail(code: str, path: str, message: str) -> None:
    raise ParameterV1ModelError(code, path, message)
