"""Portable, file-local common metric contract for VALIDATION V2.

The module is pure computation over already-authorized, normalized records.  It
does not read datasets, predictions, labels, or held-out assets.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Mapping

from .formal_v4_authority_v1 import canonical_document_hash_v1
from .prediction_custody_v1 import (
    D1PredictionArtifactV2,
    DurablePredictionFreezeReceiptV1,
    validate_durable_prediction_freeze_receipt_v1,
    validate_prediction_document_v1,
)
from .protocol_v1 import ValidationProtocolV1, validate_validation_protocol_v1
from .runtime_v1 import FORMAL_V4_RUNTIME_VERSION, FormalV4RuntimeTraceV1


HEX = frozenset("0123456789abcdef")


class MetricContractError(RuntimeError):
    pass


class D1MetricOutcomeV1(str, Enum):
    FAIL = "FAIL"
    PASS = "PASS"
    ABSTAIN = "ABSTAIN"
    SYSTEM_ERROR = "SYSTEM_ERROR"


def _fail(code: str) -> None:
    raise MetricContractError(code)


def _sha(value: str, code: str) -> None:
    if type(value) is not str or len(value) != 64 or set(value) - HEX:
        _fail(code)


def _identifier(value: str, code: str) -> None:
    if type(value) is not str or not value or any(ch in value for ch in ("/", "\\", ":")) or value in (".", ".."):
        _fail(code)


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _self_hash(value: Mapping[str, Any]) -> str:
    return sha256(_canonical_bytes({key: item for key, item in value.items() if key != "self_hash"})).hexdigest()


def _decimal_ratio(numerator: int, denominator: int) -> str:
    with localcontext() as context:
        context.prec = 34
        value = Decimal(numerator) / Decimal(denominator)
    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered or "0"


@dataclass(frozen=True)
class CommonMetricContractV1:
    protocol_hash: str
    sampling_seconds: int
    coordinate_scope: str
    timestamp_validation: str
    event_construction: str
    event_hit_rule: str
    point_adjustment: str
    episode_construction: str
    episode_allowed_gap_seconds: int
    mixed_episode_policy: str
    normal_exposure: str
    far_formula: str
    zero_attack_events: str
    zero_normal_exposure: str
    d1_system_error_policy: str
    contract_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "schema": "paperworks.validation_v2.common_metric_contract_v1",
            "schema_version": "1.0.0",
            **{name: value for name, value in self.__dict__.items() if name != "contract_hash"},
        }

    def to_dict(self) -> dict[str, Any]:
        value = self.body_dict()
        value["contract_hash"] = self.contract_hash
        return value


def build_common_metric_contract_v1(protocol: ValidationProtocolV1) -> CommonMetricContractV1:
    validate_validation_protocol_v1(protocol)
    policy = protocol.event_metric_policy
    provisional = CommonMetricContractV1(
        protocol_hash=protocol.protocol_hash,
        sampling_seconds=policy.sampling_seconds,
        coordinate_scope=policy.coordinate_scope,
        timestamp_validation=policy.timestamp_validation,
        event_construction=policy.event_construction,
        event_hit_rule=policy.event_hit_rule,
        point_adjustment=policy.point_adjustment,
        episode_construction=policy.episode_construction,
        episode_allowed_gap_seconds=policy.episode_allowed_gap_seconds,
        mixed_episode_policy=policy.mixed_episode_policy,
        normal_exposure=policy.normal_exposure,
        far_formula=policy.far_formula,
        zero_attack_events=policy.zero_attack_events,
        zero_normal_exposure=policy.zero_normal_exposure,
        d1_system_error_policy=policy.d1_system_error_policy,
        contract_hash="",
    )
    return CommonMetricContractV1(
        **{**provisional.__dict__, "contract_hash": sha256(_canonical_bytes(provisional.body_dict())).hexdigest()}
    )


def validate_common_metric_contract_v1(contract: CommonMetricContractV1, *, protocol: ValidationProtocolV1) -> str:
    if type(contract) is not CommonMetricContractV1:
        _fail("WRONG_METRIC_CONTRACT_TYPE")
    if contract != build_common_metric_contract_v1(protocol):
        _fail("METRIC_CONTRACT_REPLAY_MISMATCH")
    return contract.contract_hash


def _validate_contract_integrity(contract: CommonMetricContractV1) -> None:
    if type(contract) is not CommonMetricContractV1:
        _fail("WRONG_METRIC_CONTRACT_TYPE")
    _sha(contract.protocol_hash, "INVALID_PROTOCOL_HASH")
    _sha(contract.contract_hash, "INVALID_METRIC_CONTRACT_HASH")
    if contract.contract_hash != sha256(_canonical_bytes(contract.body_dict())).hexdigest():
        _fail("METRIC_CONTRACT_SELF_HASH_MISMATCH")


def _validate_contract_protocol_binding(
    contract: CommonMetricContractV1, protocol: ValidationProtocolV1,
) -> None:
    _validate_contract_integrity(contract)
    validate_common_metric_contract_v1(contract, protocol=protocol)


@dataclass(frozen=True)
class PredictionCoordinateV1:
    file_id: str
    feature_file_sha256: str
    row_index: int
    timestamp_second: int

    def __post_init__(self) -> None:
        _identifier(self.file_id, "INVALID_FILE_ID")
        _sha(self.feature_file_sha256, "INVALID_FEATURE_FILE_HASH")
        if type(self.row_index) is not int or self.row_index < 0:
            _fail("INVALID_ROW_INDEX")
        if type(self.timestamp_second) is not int:
            _fail("INVALID_TIMESTAMP_SECOND")

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class BooleanAlarmInputV1:
    coordinate: PredictionCoordinateV1
    alarm: bool

    def __post_init__(self) -> None:
        if type(self.coordinate) is not PredictionCoordinateV1:
            _fail("WRONG_COORDINATE_TYPE")
        if type(self.alarm) is not bool:
            _fail("INVALID_BOOLEAN_ALARM")


@dataclass(frozen=True)
class D1OutcomeInputV1:
    file_id: str
    feature_file_sha256: str
    event_row_index: int
    target_response_start_index: int
    response_window_seconds: int
    selected_horizon_seconds: int
    decision_row_index: int
    decision_timestamp_second: int
    trace: FormalV4RuntimeTraceV1

    def __post_init__(self) -> None:
        _identifier(self.file_id, "INVALID_FILE_ID")
        _sha(self.feature_file_sha256, "INVALID_FEATURE_FILE_HASH")
        for value in (self.event_row_index, self.target_response_start_index, self.response_window_seconds,
                      self.selected_horizon_seconds, self.decision_row_index):
            if type(value) is not int or value < 0:
                _fail("INVALID_D1_OUTCOME_INDEX")
        if self.response_window_seconds <= 0 or self.selected_horizon_seconds <= 0:
            _fail("INVALID_D1_WINDOW_LENGTH")
        if self.target_response_start_index != self.event_row_index + self.selected_horizon_seconds:
            _fail("D1_HORIZON_BINDING_MISMATCH")
        if self.decision_row_index != self.target_response_start_index + self.response_window_seconds - 1:
            _fail("D1_DECISION_ROW_BINDING_MISMATCH")
        if type(self.decision_row_index) is not int or self.decision_row_index < 0:
            _fail("INVALID_ROW_INDEX")
        if type(self.decision_timestamp_second) is not int:
            _fail("INVALID_TIMESTAMP_SECOND")
        if type(self.trace) is not FormalV4RuntimeTraceV1:
            _fail("D1_TRACE_MUST_BE_FORMAL_V4_TRACE")
        try:
            outcome = D1MetricOutcomeV1(self.trace.final_outcome)
        except ValueError:
            _fail("D1_TRACE_OUTCOME_UNKNOWN")
        if outcome is D1MetricOutcomeV1.SYSTEM_ERROR:
            _fail("D1_SYSTEM_ERROR_CANNOT_BECOME_NO_ALARM")
        if self.trace.alarm_emitted is not (outcome is D1MetricOutcomeV1.FAIL):
            _fail("D1_TRACE_ALARM_OUTCOME_MISMATCH")
        payload = {
            "alarm_emitted": self.trace.alarm_emitted,
            "authorization_hash": self.trace.authorization_hash,
            "descriptor_hash": self.trace.descriptor_hash,
            "execution_context_hash": self.trace.execution_context_hash,
            "final_outcome": self.trace.final_outcome,
            "opportunity_id": self.trace.opportunity_id,
            "reason": self.trace.reason,
            "relation_id": self.trace.relation_id,
            "runtime_version": FORMAL_V4_RUNTIME_VERSION,
        }
        if self.trace.trace_hash != canonical_document_hash_v1(payload):
            _fail("D1_TRACE_HASH_REPLAY_MISMATCH")

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_id": self.file_id,
            "feature_file_sha256": self.feature_file_sha256,
            "event_row_index": self.event_row_index,
            "target_response_start_index": self.target_response_start_index,
            "response_window_seconds": self.response_window_seconds,
            "selected_horizon_seconds": self.selected_horizon_seconds,
            "decision_row_index": self.decision_row_index,
            "decision_timestamp_second": self.decision_timestamp_second,
            "trace": self.trace.to_dict(),
        }


@dataclass(frozen=True)
class CommonAlarmPointV1:
    coordinate: PredictionCoordinateV1
    alarm: bool
    native_states: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"coordinate": self.coordinate.to_dict(), "alarm": self.alarm, "native_states": list(self.native_states)}


@dataclass(frozen=True)
class CommonAlarmTimelineV1:
    method_id: str
    config_id: str
    source_prediction_sha256: str
    prediction_freeze_receipt_sha256: str
    adapter_id: str
    native_evidence_sha256: str
    file_series_hash: str
    protocol_hash: str
    metric_contract_hash: str
    points: tuple[CommonAlarmPointV1, ...]
    native_state_counts: tuple[tuple[str, int], ...]
    self_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "schema": "paperworks.validation_v2.common_alarm_timeline_v1",
            "schema_version": "1.0.0",
            "method_id": self.method_id,
            "config_id": self.config_id,
            "source_prediction_sha256": self.source_prediction_sha256,
            "prediction_freeze_receipt_sha256": self.prediction_freeze_receipt_sha256,
            "adapter_id": self.adapter_id,
            "native_evidence_sha256": self.native_evidence_sha256,
            "file_series_hash": self.file_series_hash,
            "protocol_hash": self.protocol_hash,
            "metric_contract_hash": self.metric_contract_hash,
            "points": [point.to_dict() for point in self.points],
            "native_state_counts": [[name, count] for name, count in self.native_state_counts],
        }

    def to_dict(self) -> dict[str, Any]:
        value = self.body_dict()
        value["self_hash"] = self.self_hash
        return value


def _validate_coordinates(coordinates: tuple[PredictionCoordinateV1, ...]) -> None:
    if type(coordinates) is not tuple or not coordinates:
        _fail("COORDINATES_MUST_BE_NONEMPTY_TUPLE")
    if any(type(item) is not PredictionCoordinateV1 for item in coordinates):
        _fail("WRONG_COORDINATE_TYPE")
    keys = tuple((item.file_id, item.row_index) for item in coordinates)
    if keys != tuple(sorted(keys)) or len(keys) != len(set(keys)):
        _fail("COORDINATES_MUST_BE_SORTED_UNIQUE")
    groups: dict[str, list[PredictionCoordinateV1]] = {}
    for item in coordinates:
        groups.setdefault(item.file_id, []).append(item)
    for items in groups.values():
        hashes = {item.feature_file_sha256 for item in items}
        if len(hashes) != 1:
            _fail("INCONSISTENT_FEATURE_FILE_HASH")
        for expected_index, item in enumerate(items):
            if item.row_index != expected_index:
                _fail("FILE_LOCAL_ROW_INDEX_GAP_OR_OFFSET")
            if expected_index and item.timestamp_second != items[expected_index - 1].timestamp_second + 1:
                _fail("NON_ONE_SECOND_TIMESTAMP_SEQUENCE")


@dataclass(frozen=True)
class FileSecondSeriesAuthorityV1:
    dataset_id: str
    sampling_contract_hash: str
    coordinates: tuple[PredictionCoordinateV1, ...]
    file_rows: tuple[tuple[str, str, int, str], ...]
    self_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "schema": "paperworks.validation_v2.file_second_series_authority_v1",
            "schema_version": "1.0.0",
            "dataset_id": self.dataset_id,
            "sampling_contract_hash": self.sampling_contract_hash,
            "coordinates": [item.to_dict() for item in self.coordinates],
            "file_rows": [list(item) for item in self.file_rows],
        }

    def to_dict(self) -> dict[str, Any]:
        value = self.body_dict()
        value["self_hash"] = self.self_hash
        return value


def build_file_second_series_authority_v1(
    *, dataset_id: str, sampling_contract_hash: str,
    coordinates: tuple[PredictionCoordinateV1, ...],
) -> FileSecondSeriesAuthorityV1:
    _identifier(dataset_id, "INVALID_DATASET_ID")
    _sha(sampling_contract_hash, "INVALID_SAMPLING_CONTRACT_HASH")
    _validate_coordinates(coordinates)
    groups: dict[str, list[PredictionCoordinateV1]] = {}
    for item in coordinates:
        groups.setdefault(item.file_id, []).append(item)
    file_rows = tuple(
        (
            file_id,
            items[0].feature_file_sha256,
            len(items),
            sha256(_canonical_bytes({
                "file_id": file_id,
                "timestamps": [item.timestamp_second for item in items],
            })).hexdigest(),
        )
        for file_id, items in sorted(groups.items())
    )
    provisional = FileSecondSeriesAuthorityV1(
        dataset_id=dataset_id, sampling_contract_hash=sampling_contract_hash,
        coordinates=coordinates, file_rows=file_rows, self_hash="",
    )
    return FileSecondSeriesAuthorityV1(
        **{**provisional.__dict__, "self_hash": _self_hash(provisional.body_dict())}
    )


def validate_file_second_series_authority_v1(authority: FileSecondSeriesAuthorityV1) -> str:
    if type(authority) is not FileSecondSeriesAuthorityV1:
        _fail("WRONG_FILE_SERIES_AUTHORITY_TYPE")
    replay = build_file_second_series_authority_v1(
        dataset_id=authority.dataset_id,
        sampling_contract_hash=authority.sampling_contract_hash,
        coordinates=authority.coordinates,
    )
    if authority != replay:
        _fail("FILE_SERIES_AUTHORITY_REPLAY_MISMATCH")
    return authority.self_hash


def _build_timeline(
    *, method_id: str, config_id: str, source_prediction_sha256: str,
    prediction_freeze_receipt_sha256: str, adapter_id: str, native_evidence_sha256: str,
    file_series_hash: str,
    contract: CommonMetricContractV1, points: tuple[CommonAlarmPointV1, ...],
    native_state_counts: tuple[tuple[str, int], ...],
) -> CommonAlarmTimelineV1:
    _identifier(method_id, "INVALID_METHOD_ID")
    _identifier(config_id, "INVALID_CONFIG_ID")
    _sha(source_prediction_sha256, "INVALID_SOURCE_PREDICTION_HASH")
    _sha(prediction_freeze_receipt_sha256, "INVALID_PREDICTION_FREEZE_RECEIPT_HASH")
    _identifier(adapter_id, "INVALID_ADAPTER_ID")
    _sha(native_evidence_sha256, "INVALID_NATIVE_EVIDENCE_HASH")
    _sha(file_series_hash, "INVALID_FILE_SERIES_HASH")
    _sha(contract.contract_hash, "INVALID_METRIC_CONTRACT_HASH")
    _validate_coordinates(tuple(point.coordinate for point in points))
    if tuple(sorted(native_state_counts)) != native_state_counts:
        _fail("NATIVE_STATE_COUNTS_MUST_BE_SORTED")
    provisional = CommonAlarmTimelineV1(
        method_id=method_id, config_id=config_id,
        source_prediction_sha256=source_prediction_sha256,
        prediction_freeze_receipt_sha256=prediction_freeze_receipt_sha256,
        adapter_id=adapter_id, native_evidence_sha256=native_evidence_sha256,
        file_series_hash=file_series_hash,
        protocol_hash=contract.protocol_hash, metric_contract_hash=contract.contract_hash,
        points=points, native_state_counts=native_state_counts, self_hash="",
    )
    return CommonAlarmTimelineV1(**{**provisional.__dict__, "self_hash": _self_hash(provisional.body_dict())})


def adapt_boolean_alarm_timeline_v1(
    *, method_id: str, config_id: str, source_prediction_sha256: str,
    prediction_freeze_receipt_sha256: str,
    contract: CommonMetricContractV1, protocol: ValidationProtocolV1,
    file_series: FileSecondSeriesAuthorityV1,
    records: tuple[BooleanAlarmInputV1, ...],
) -> CommonAlarmTimelineV1:
    _validate_contract_protocol_binding(contract, protocol)
    validate_file_second_series_authority_v1(file_series)
    if type(records) is not tuple or not records or any(type(item) is not BooleanAlarmInputV1 for item in records):
        _fail("BOOLEAN_RECORDS_MUST_BE_NONEMPTY_EXACT_TUPLE")
    if tuple(item.coordinate for item in records) != file_series.coordinates:
        _fail("BOOLEAN_PREDICTION_FILE_SERIES_COVERAGE_MISMATCH")
    points = tuple(
        CommonAlarmPointV1(item.coordinate, item.alarm, ("ALARM" if item.alarm else "NO_ALARM",))
        for item in records
    )
    counts = (
        ("ALARM", sum(item.alarm for item in records)),
        ("NO_ALARM", sum(not item.alarm for item in records)),
    )
    return _build_timeline(
        method_id=method_id, config_id=config_id, source_prediction_sha256=source_prediction_sha256,
        prediction_freeze_receipt_sha256=prediction_freeze_receipt_sha256,
        adapter_id="DENSE_BOOLEAN_V1", native_evidence_sha256=source_prediction_sha256,
        file_series_hash=file_series.self_hash,
        contract=contract, points=points, native_state_counts=counts,
    )


def adapt_d1_alarm_timeline_v1(
    *, prediction_artifact: D1PredictionArtifactV2,
    freeze_receipt: DurablePredictionFreezeReceiptV1,
    contract: CommonMetricContractV1, protocol: ValidationProtocolV1,
    file_series: FileSecondSeriesAuthorityV1,
    outcomes: tuple[D1OutcomeInputV1, ...],
) -> CommonAlarmTimelineV1:
    _validate_contract_protocol_binding(contract, protocol)
    validate_file_second_series_authority_v1(file_series)
    if type(prediction_artifact) is not D1PredictionArtifactV2:
        _fail("D1_PREDICTION_ARTIFACT_MUST_BE_EXACT_TYPE")
    validate_prediction_document_v1(
        prediction_artifact.to_document(), expected_authority_hash=prediction_artifact.authority_hash,
    )
    validate_durable_prediction_freeze_receipt_v1(freeze_receipt)
    artifact_document = prediction_artifact.to_document()
    expected_receipt_bindings = (
        artifact_document["self_hash"], prediction_artifact.authority_hash,
        prediction_artifact.runtime_authorization_hash, prediction_artifact.execution_context_hash,
        prediction_artifact.source_commit, prediction_artifact.portfolio_hash,
        prediction_artifact.file_contract_hash, len(prediction_artifact.records),
    )
    actual_receipt_bindings = (
        freeze_receipt.prediction_self_hash, freeze_receipt.authority_hash,
        freeze_receipt.runtime_authorization_hash, freeze_receipt.execution_context_hash,
        freeze_receipt.source_commit, freeze_receipt.portfolio_hash,
        freeze_receipt.file_contract_hash, freeze_receipt.record_count,
    )
    if actual_receipt_bindings != expected_receipt_bindings:
        _fail("D1_FREEZE_RECEIPT_ARTIFACT_BINDING_MISMATCH")
    receipt_content_sha256 = sha256(_canonical_bytes(freeze_receipt.to_document())).hexdigest()
    coordinates = file_series.coordinates
    expected_coordinate_bindings = tuple(
        (item.file_id, item.feature_file_sha256, item.row_index)
        for item in coordinates
    )
    artifact_coordinate_bindings = tuple(
        (item.file_id, item.file_content_sha256, item.row_index)
        for item in prediction_artifact.records
    )
    if artifact_coordinate_bindings != expected_coordinate_bindings:
        _fail("D1_PREDICTION_COORDINATE_COVERAGE_MISMATCH")
    if type(outcomes) is not tuple or any(type(item) is not D1OutcomeInputV1 for item in outcomes):
        _fail("D1_OUTCOMES_MUST_BE_EXACT_TUPLE")
    known = {(item.file_id, item.row_index) for item in coordinates}
    seen: set[str] = set()
    grouped: dict[tuple[str, int], list[D1OutcomeInputV1]] = {}
    coordinate_map = {(item.file_id, item.row_index): item for item in coordinates}
    for item in outcomes:
        key = (item.file_id, item.decision_row_index)
        if key not in known:
            _fail("D1_OUTCOME_COORDINATE_OUT_OF_RANGE")
        if item.trace.trace_hash in seen:
            _fail("DUPLICATE_D1_TRACE_OUTCOME")
        seen.add(item.trace.trace_hash)
        coordinate = coordinate_map[key]
        if item.feature_file_sha256 != coordinate.feature_file_sha256 or item.decision_timestamp_second != coordinate.timestamp_second:
            _fail("D1_DECISION_COORDINATE_BINDING_MISMATCH")
        if item.trace.authorization_hash != prediction_artifact.runtime_authorization_hash:
            _fail("D1_RUNTIME_AUTHORITY_MISMATCH")
        if item.trace.execution_context_hash != prediction_artifact.execution_context_hash:
            _fail("D1_EXECUTION_CONTEXT_MISMATCH")
        grouped.setdefault(key, []).append(item)
    native_outcome_bundle_sha256 = sha256(_canonical_bytes({
        "schema": "paperworks.validation_v2.d1_native_outcome_bundle_v1",
        "schema_version": "1.0.0",
        "prediction_self_hash": artifact_document["self_hash"],
        "records": [item.to_dict() for item in sorted(
            outcomes,
            key=lambda item: (item.file_id, item.decision_row_index, item.trace.trace_hash),
        )],
    })).hexdigest()
    counter = {state.value: 0 for state in D1MetricOutcomeV1}
    counter["NO_OPPORTUNITY"] = 0
    points: list[CommonAlarmPointV1] = []
    for coordinate, prediction_record in zip(coordinates, prediction_artifact.records):
        materialized = grouped.get((coordinate.file_id, coordinate.row_index), [])
        if not materialized:
            if prediction_record.alarm:
                _fail("D1_BOOLEAN_ALARM_WITHOUT_FAIL_OUTCOME")
            counter["NO_OPPORTUNITY"] += 1
            points.append(CommonAlarmPointV1(coordinate, False, ("NO_OPPORTUNITY",)))
            continue
        states = tuple(D1MetricOutcomeV1(item.trace.final_outcome) for item in materialized)
        for state in states:
            counter[state.value] += 1
        names = tuple(sorted(state.value for state in states))
        expected_alarm = D1MetricOutcomeV1.FAIL.value in names
        if prediction_record.alarm is not expected_alarm:
            _fail("D1_BOOLEAN_NATIVE_OUTCOME_MISMATCH")
        fail_records = tuple(item for item in materialized if item.trace.final_outcome == "FAIL")
        rule_ids = tuple(sorted({item.trace.relation_id for item in fail_records}))
        trace_hashes = tuple(sorted({item.trace.trace_hash for item in fail_records}))
        if prediction_record.contributing_rule_ids != rule_ids or prediction_record.trace_hashes != trace_hashes:
            _fail("D1_PREDICTION_PROVENANCE_RECONCILIATION_MISMATCH")
        points.append(CommonAlarmPointV1(coordinate, prediction_record.alarm, names))
    counts = tuple(sorted((name, count) for name, count in counter.items() if name != "SYSTEM_ERROR"))
    return _build_timeline(
        method_id=prediction_artifact.method_id, config_id=prediction_artifact.config_id,
        source_prediction_sha256=freeze_receipt.prediction_bytes_sha256,
        prediction_freeze_receipt_sha256=receipt_content_sha256,
        adapter_id="D1_NATIVE_RECONCILED_V1", native_evidence_sha256=native_outcome_bundle_sha256,
        file_series_hash=file_series.self_hash,
        contract=contract, points=tuple(points), native_state_counts=counts,
    )


@dataclass(frozen=True)
class LabelPointV1:
    coordinate: PredictionCoordinateV1
    label: int

    def __post_init__(self) -> None:
        if type(self.coordinate) is not PredictionCoordinateV1:
            _fail("WRONG_COORDINATE_TYPE")
        if type(self.label) is not int or self.label not in (0, 1):
            _fail("INVALID_STRICT_BINARY_LABEL")

    def to_dict(self) -> dict[str, Any]:
        return {"coordinate": self.coordinate.to_dict(), "label": self.label}


@dataclass(frozen=True)
class LabelTimelineV1:
    dataset_id: str
    label_authority_sha256: str
    file_series_hash: str
    points: tuple[LabelPointV1, ...]
    self_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "schema": "paperworks.validation_v2.label_timeline_v1",
            "schema_version": "1.0.0", "dataset_id": self.dataset_id,
            "label_authority_sha256": self.label_authority_sha256,
            "file_series_hash": self.file_series_hash,
            "points": [item.to_dict() for item in self.points],
        }

    def to_dict(self) -> dict[str, Any]:
        value = self.body_dict()
        value["self_hash"] = self.self_hash
        return value


def build_label_timeline_v1(
    *, dataset_id: str, label_authority_sha256: str,
    file_series: FileSecondSeriesAuthorityV1, points: tuple[LabelPointV1, ...],
) -> LabelTimelineV1:
    _identifier(dataset_id, "INVALID_DATASET_ID")
    _sha(label_authority_sha256, "INVALID_LABEL_AUTHORITY_HASH")
    validate_file_second_series_authority_v1(file_series)
    if type(points) is not tuple or not points or any(type(item) is not LabelPointV1 for item in points):
        _fail("LABEL_POINTS_MUST_BE_NONEMPTY_EXACT_TUPLE")
    _validate_coordinates(tuple(item.coordinate for item in points))
    if tuple(item.coordinate for item in points) != file_series.coordinates:
        _fail("LABEL_FILE_SERIES_COVERAGE_MISMATCH")
    provisional = LabelTimelineV1(dataset_id, label_authority_sha256, file_series.self_hash, points, "")
    return LabelTimelineV1(**{**provisional.__dict__, "self_hash": _self_hash(provisional.body_dict())})


@dataclass(frozen=True, order=True)
class FileIntervalV1:
    file_id: str
    start_index: int
    end_index_exclusive: int
    start_timestamp_second: int
    end_timestamp_second_exclusive: int

    def __post_init__(self) -> None:
        _identifier(self.file_id, "INVALID_FILE_ID")
        if type(self.start_index) is not int or type(self.end_index_exclusive) is not int:
            _fail("INVALID_INTERVAL_INDEX")
        if self.start_index < 0 or self.end_index_exclusive <= self.start_index:
            _fail("INVALID_HALF_OPEN_INTERVAL")
        if self.end_timestamp_second_exclusive - self.start_timestamp_second != self.end_index_exclusive - self.start_index:
            _fail("INTERVAL_TIMEBASE_MISMATCH")

    @property
    def event_id(self) -> str:
        return f"{self.file_id}#{self.start_index}:{self.end_index_exclusive}"

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def _intervals_from_points(points: tuple[tuple[PredictionCoordinateV1, bool], ...]) -> tuple[FileIntervalV1, ...]:
    intervals: list[FileIntervalV1] = []
    groups: dict[str, list[tuple[PredictionCoordinateV1, bool]]] = {}
    for coordinate, selected in points:
        groups.setdefault(coordinate.file_id, []).append((coordinate, selected))
    for file_id in sorted(groups):
        active: PredictionCoordinateV1 | None = None
        prior: PredictionCoordinateV1 | None = None
        for coordinate, selected in groups[file_id]:
            if selected and active is None:
                active = coordinate
            if not selected and active is not None:
                assert prior is not None
                intervals.append(FileIntervalV1(
                    active.file_id, active.row_index, prior.row_index + 1,
                    active.timestamp_second, prior.timestamp_second + 1,
                ))
                active = None
            prior = coordinate
        if active is not None and prior is not None:
            intervals.append(FileIntervalV1(
                active.file_id, active.row_index, prior.row_index + 1,
                active.timestamp_second, prior.timestamp_second + 1,
            ))
    return tuple(intervals)


def derive_attack_event_units_v1(
    labels: LabelTimelineV1, *, file_series: FileSecondSeriesAuthorityV1,
) -> tuple[FileIntervalV1, ...]:
    if type(labels) is not LabelTimelineV1:
        _fail("WRONG_LABEL_TIMELINE_TYPE")
    validate_label_timeline_v1(labels, file_series=file_series)
    return _intervals_from_points(tuple((item.coordinate, item.label == 1) for item in labels.points))


def form_alarm_episodes_v1(
    prediction: CommonAlarmTimelineV1, *, file_series: FileSecondSeriesAuthorityV1,
) -> tuple[FileIntervalV1, ...]:
    if type(prediction) is not CommonAlarmTimelineV1:
        _fail("WRONG_ALARM_TIMELINE_TYPE")
    validate_common_alarm_timeline_v1(prediction, file_series=file_series)
    return _intervals_from_points(tuple((item.coordinate, item.alarm) for item in prediction.points))


def _overlap(left: FileIntervalV1, right: FileIntervalV1) -> bool:
    return left.file_id == right.file_id and left.start_index < right.end_index_exclusive and right.start_index < left.end_index_exclusive


def _match_event_episode_overlaps_v1(
    events: tuple[FileIntervalV1, ...],
    episodes: tuple[FileIntervalV1, ...],
) -> tuple[tuple[bool, ...], tuple[bool, ...]]:
    """Match disjoint intervals in linear time per file.

    Event units and alarm episodes are both maximal, disjoint runs produced by
    ``_intervals_from_points``.  The two-pointer sweep is therefore exactly
    equivalent to the prior all-pairs overlap oracle while avoiding quadratic
    work when a method emits many episodes.
    """

    event_groups: dict[str, list[tuple[int, FileIntervalV1]]] = {}
    episode_groups: dict[str, list[tuple[int, FileIntervalV1]]] = {}
    for index, event in enumerate(events):
        event_groups.setdefault(event.file_id, []).append((index, event))
    for index, episode in enumerate(episodes):
        episode_groups.setdefault(episode.file_id, []).append((index, episode))

    event_hits = [False] * len(events)
    episode_hits = [False] * len(episodes)
    for file_id in event_groups.keys() & episode_groups.keys():
        file_events = event_groups[file_id]
        file_episodes = episode_groups[file_id]
        event_cursor = 0
        episode_cursor = 0
        while event_cursor < len(file_events) and episode_cursor < len(file_episodes):
            event_index, event = file_events[event_cursor]
            episode_index, episode = file_episodes[episode_cursor]
            if event.end_index_exclusive <= episode.start_index:
                event_cursor += 1
                continue
            if episode.end_index_exclusive <= event.start_index:
                episode_cursor += 1
                continue
            event_hits[event_index] = True
            episode_hits[episode_index] = True
            if event.end_index_exclusive <= episode.end_index_exclusive:
                event_cursor += 1
            if episode.end_index_exclusive <= event.end_index_exclusive:
                episode_cursor += 1
    return tuple(event_hits), tuple(episode_hits)


@dataclass(frozen=True)
class MetricValueV1:
    metric_id: str
    numerator: int
    denominator: int
    ratio_numerator: int
    ratio_denominator: int
    unit: str
    defined: bool
    value_decimal: str | None
    undefined_reason: str | None

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def _metric(metric_id: str, numerator: int, denominator: int, *, scale: int, unit: str, undefined_reason: str) -> MetricValueV1:
    if denominator == 0:
        return MetricValueV1(metric_id, numerator, denominator, numerator * scale, 0, unit, False, None, undefined_reason)
    ratio_numerator = numerator * scale
    return MetricValueV1(
        metric_id, numerator, denominator, ratio_numerator, denominator, unit, True,
        _decimal_ratio(ratio_numerator, denominator), None,
    )


@dataclass(frozen=True)
class CommonEvaluationResultV1:
    method_id: str
    config_id: str
    protocol_hash: str
    metric_contract_hash: str
    prediction_timeline_hash: str
    label_timeline_hash: str
    attack_events: tuple[FileIntervalV1, ...]
    attack_detection: tuple[tuple[str, bool], ...]
    alarm_seconds: int
    alarm_episodes: tuple[FileIntervalV1, ...]
    normal_false_episodes: int
    normal_exposure_seconds: int
    recall: MetricValueV1
    far_per_hour: MetricValueV1
    native_state_counts: tuple[tuple[str, int], ...]
    self_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "schema": "paperworks.validation_v2.common_evaluation_result_v1",
            "schema_version": "1.0.0",
            "method_id": self.method_id, "config_id": self.config_id,
            "protocol_hash": self.protocol_hash, "metric_contract_hash": self.metric_contract_hash,
            "prediction_timeline_hash": self.prediction_timeline_hash,
            "label_timeline_hash": self.label_timeline_hash,
            "attack_events": [item.to_dict() for item in self.attack_events],
            "attack_detection": [[name, detected] for name, detected in self.attack_detection],
            "alarm_seconds": self.alarm_seconds,
            "alarm_episodes": [item.to_dict() for item in self.alarm_episodes],
            "normal_false_episodes": self.normal_false_episodes,
            "normal_exposure_seconds": self.normal_exposure_seconds,
            "recall": self.recall.to_dict(), "far_per_hour": self.far_per_hour.to_dict(),
            "native_state_counts": [[name, count] for name, count in self.native_state_counts],
        }

    def to_dict(self) -> dict[str, Any]:
        value = self.body_dict()
        value["self_hash"] = self.self_hash
        return value


def evaluate_common_timeline_v1(
    *, contract: CommonMetricContractV1, protocol: ValidationProtocolV1,
    file_series: FileSecondSeriesAuthorityV1,
    prediction: CommonAlarmTimelineV1, labels: LabelTimelineV1,
) -> CommonEvaluationResultV1:
    if type(contract) is not CommonMetricContractV1 or type(prediction) is not CommonAlarmTimelineV1 or type(labels) is not LabelTimelineV1:
        _fail("WRONG_EVALUATION_INPUT_TYPE")
    _validate_contract_protocol_binding(contract, protocol)
    validate_common_alarm_timeline_v1(prediction, file_series=file_series)
    validate_label_timeline_v1(labels, file_series=file_series)
    if prediction.metric_contract_hash != contract.contract_hash or prediction.protocol_hash != contract.protocol_hash:
        _fail("PREDICTION_METRIC_AUTHORITY_MISMATCH")
    if prediction.file_series_hash != labels.file_series_hash:
        _fail("PREDICTION_LABEL_FILE_SERIES_MISMATCH")
    prediction_coordinates = tuple(point.coordinate for point in prediction.points)
    label_coordinates = tuple(point.coordinate for point in labels.points)
    if prediction_coordinates != label_coordinates:
        _fail("PREDICTION_LABEL_ALIGNMENT_REJECTED")
    events = derive_attack_event_units_v1(labels, file_series=file_series)
    episodes = form_alarm_episodes_v1(prediction, file_series=file_series)
    event_hits, episode_hits = _match_event_episode_overlaps_v1(events, episodes)
    detection = tuple((event.event_id, detected) for event, detected in zip(events, event_hits))
    normal_false = sum(not detected for detected in episode_hits)
    exposure = sum(point.label == 0 for point in labels.points)
    recall = _metric("ATTACK_EVENT_RECALL", sum(value for _, value in detection), len(events), scale=1, unit="RATIO", undefined_reason="NO_ATTACK_EVENTS")
    far = _metric("NORMAL_FAR_EPISODES_PER_HOUR", normal_false, exposure, scale=3600, unit="EPISODES_PER_HOUR", undefined_reason="NO_NORMAL_EXPOSURE")
    provisional = CommonEvaluationResultV1(
        method_id=prediction.method_id, config_id=prediction.config_id,
        protocol_hash=contract.protocol_hash, metric_contract_hash=contract.contract_hash,
        prediction_timeline_hash=prediction.self_hash, label_timeline_hash=labels.self_hash,
        attack_events=events, attack_detection=detection,
        alarm_seconds=sum(point.alarm for point in prediction.points), alarm_episodes=episodes,
        normal_false_episodes=normal_false, normal_exposure_seconds=exposure,
        recall=recall, far_per_hour=far, native_state_counts=prediction.native_state_counts,
        self_hash="",
    )
    return CommonEvaluationResultV1(**{**provisional.__dict__, "self_hash": _self_hash(provisional.body_dict())})


@dataclass(frozen=True)
class CommonComparisonResultV1:
    baseline_method_id: str
    candidate_method_id: str
    baseline_result_hash: str
    candidate_result_hash: str
    both: int
    baseline_only: int
    candidate_only: int
    neither: int
    incremental_detected_units: int
    incremental_false_episodes: int
    baseline_miss_recovery: MetricValueV1
    incremental_recall: MetricValueV1
    incremental_far_per_hour: MetricValueV1
    self_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "schema": "paperworks.validation_v2.common_comparison_result_v1",
            "schema_version": "1.0.0",
            "baseline_method_id": self.baseline_method_id,
            "candidate_method_id": self.candidate_method_id,
            "baseline_result_hash": self.baseline_result_hash,
            "candidate_result_hash": self.candidate_result_hash,
            "both": self.both,
            "baseline_only": self.baseline_only,
            "candidate_only": self.candidate_only,
            "neither": self.neither,
            "incremental_detected_units": self.incremental_detected_units,
            "incremental_false_episodes": self.incremental_false_episodes,
            "baseline_miss_recovery": self.baseline_miss_recovery.to_dict(),
            "incremental_recall": self.incremental_recall.to_dict(),
            "incremental_far_per_hour": self.incremental_far_per_hour.to_dict(),
        }

    def to_dict(self) -> dict[str, Any]:
        value = self.body_dict()
        value["self_hash"] = self.self_hash
        return value


def compare_common_results_v1(
    *, contract: CommonMetricContractV1, protocol: ValidationProtocolV1,
    baseline: CommonEvaluationResultV1, candidate: CommonEvaluationResultV1,
) -> CommonComparisonResultV1:
    if type(baseline) is not CommonEvaluationResultV1 or type(candidate) is not CommonEvaluationResultV1:
        _fail("WRONG_COMPARISON_INPUT_TYPE")
    _validate_contract_protocol_binding(contract, protocol)
    if baseline.self_hash != _self_hash(baseline.body_dict()) or candidate.self_hash != _self_hash(candidate.body_dict()):
        _fail("COMPARISON_INPUT_SELF_HASH_MISMATCH")
    if baseline.metric_contract_hash != candidate.metric_contract_hash or baseline.label_timeline_hash != candidate.label_timeline_hash:
        _fail("CROSS_METHOD_AUTHORITY_MISMATCH")
    if baseline.metric_contract_hash != contract.contract_hash or baseline.protocol_hash != protocol.protocol_hash:
        _fail("CROSS_METHOD_CONTRACT_BINDING_MISMATCH")
    if baseline.normal_exposure_seconds != candidate.normal_exposure_seconds:
        _fail("CROSS_METHOD_NORMAL_EXPOSURE_MISMATCH")
    if tuple(name for name, _ in baseline.attack_detection) != tuple(name for name, _ in candidate.attack_detection):
        _fail("CROSS_METHOD_EVENT_IDENTITY_MISMATCH")
    pairs = tuple(zip((value for _, value in baseline.attack_detection), (value for _, value in candidate.attack_detection)))
    both = sum(left and right for left, right in pairs)
    baseline_only = sum(left and not right for left, right in pairs)
    candidate_only = sum(not left and right for left, right in pairs)
    neither = sum(not left and not right for left, right in pairs)
    incremental_detected = candidate_only - baseline_only
    incremental_false = candidate.normal_false_episodes - baseline.normal_false_episodes
    provisional = CommonComparisonResultV1(
        baseline_method_id=baseline.method_id, candidate_method_id=candidate.method_id,
        baseline_result_hash=baseline.self_hash, candidate_result_hash=candidate.self_hash,
        both=both, baseline_only=baseline_only, candidate_only=candidate_only, neither=neither,
        incremental_detected_units=incremental_detected,
        incremental_false_episodes=incremental_false,
        baseline_miss_recovery=_metric(
            "BASELINE_MISS_RECOVERY", candidate_only, candidate_only + neither,
            scale=1, unit="RATIO", undefined_reason="NO_BASELINE_MISSED_ATTACK_EVENTS",
        ),
        incremental_recall=_metric(
            "INCREMENTAL_ATTACK_EVENT_RECALL", incremental_detected, len(pairs),
            scale=1, unit="RATIO", undefined_reason="NO_ATTACK_EVENTS",
        ),
        incremental_far_per_hour=_metric(
            "INCREMENTAL_NORMAL_FAR_EPISODES_PER_HOUR", incremental_false,
            baseline.normal_exposure_seconds, scale=3600, unit="EPISODES_PER_HOUR",
            undefined_reason="NO_NORMAL_EXPOSURE",
        ),
        self_hash="",
    )
    return CommonComparisonResultV1(**{**provisional.__dict__, "self_hash": _self_hash(provisional.body_dict())})


@dataclass(frozen=True)
class CommonEvaluationBundleV1:
    execution_scope: str
    scientific_eligible: bool
    protocol_hash: str
    metric_contract_hash: str
    result_hashes: tuple[str, ...]
    comparison_hashes: tuple[str, ...]
    self_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "schema": "paperworks.validation_v2.common_evaluation_bundle_v1",
            "schema_version": "1.0.0",
            "execution_scope": self.execution_scope,
            "scientific_eligible": self.scientific_eligible,
            "protocol_hash": self.protocol_hash,
            "metric_contract_hash": self.metric_contract_hash,
            "result_hashes": list(self.result_hashes),
            "comparison_hashes": list(self.comparison_hashes),
        }

    def to_dict(self) -> dict[str, Any]:
        value = self.body_dict()
        value["self_hash"] = self.self_hash
        return value


def aggregate_synthetic_common_evaluation_v1(
    *, contract: CommonMetricContractV1, protocol: ValidationProtocolV1,
    results: tuple[CommonEvaluationResultV1, ...],
    comparisons: tuple[CommonComparisonResultV1, ...] = (),
) -> CommonEvaluationBundleV1:
    """Create the tracked Stage-1 bundle; scientific inputs are unauthorized here."""

    if type(contract) is not CommonMetricContractV1:
        _fail("WRONG_METRIC_CONTRACT_TYPE")
    _validate_contract_protocol_binding(contract, protocol)
    if type(results) is not tuple or not results or any(type(item) is not CommonEvaluationResultV1 for item in results):
        _fail("RESULTS_MUST_BE_NONEMPTY_EXACT_TUPLE")
    if type(comparisons) is not tuple or any(type(item) is not CommonComparisonResultV1 for item in comparisons):
        _fail("COMPARISONS_MUST_BE_EXACT_TUPLE")
    if any(item.metric_contract_hash != contract.contract_hash or item.protocol_hash != contract.protocol_hash for item in results):
        _fail("BUNDLE_RESULT_AUTHORITY_MISMATCH")
    if any(item.self_hash != _self_hash(item.body_dict()) for item in results):
        _fail("BUNDLE_RESULT_SELF_HASH_MISMATCH")
    if any(item.self_hash != _self_hash(item.body_dict()) for item in comparisons):
        _fail("BUNDLE_COMPARISON_SELF_HASH_MISMATCH")
    result_hashes = tuple(sorted(item.self_hash for item in results))
    if len(result_hashes) != len(set(result_hashes)):
        _fail("DUPLICATE_RESULT_HASH")
    known_result_hashes = set(result_hashes)
    for item in comparisons:
        if item.baseline_result_hash not in known_result_hashes or item.candidate_result_hash not in known_result_hashes:
            _fail("BUNDLE_COMPARISON_RESULT_MISSING")
        result_by_hash = {result.self_hash: result for result in results}
        baseline = result_by_hash[item.baseline_result_hash]
        candidate = result_by_hash[item.candidate_result_hash]
        if item != compare_common_results_v1(
            contract=contract, protocol=protocol, baseline=baseline, candidate=candidate,
        ):
            _fail("BUNDLE_COMPARISON_REPLAY_MISMATCH")
    comparison_hashes = tuple(sorted(item.self_hash for item in comparisons))
    if len(comparison_hashes) != len(set(comparison_hashes)):
        _fail("DUPLICATE_COMPARISON_HASH")
    provisional = CommonEvaluationBundleV1(
        execution_scope="SYNTHETIC_CONTRACT_ONLY", scientific_eligible=False,
        protocol_hash=contract.protocol_hash, metric_contract_hash=contract.contract_hash,
        result_hashes=result_hashes, comparison_hashes=comparison_hashes, self_hash="",
    )
    return CommonEvaluationBundleV1(**{**provisional.__dict__, "self_hash": _self_hash(provisional.body_dict())})


def validate_common_alarm_timeline_v1(
    timeline: CommonAlarmTimelineV1, *, file_series: FileSecondSeriesAuthorityV1,
) -> str:
    if type(timeline) is not CommonAlarmTimelineV1:
        _fail("WRONG_ALARM_TIMELINE_TYPE")
    _identifier(timeline.method_id, "INVALID_METHOD_ID")
    _identifier(timeline.config_id, "INVALID_CONFIG_ID")
    _sha(timeline.source_prediction_sha256, "INVALID_SOURCE_PREDICTION_HASH")
    _sha(timeline.prediction_freeze_receipt_sha256, "INVALID_PREDICTION_FREEZE_RECEIPT_HASH")
    _identifier(timeline.adapter_id, "INVALID_ADAPTER_ID")
    _sha(timeline.native_evidence_sha256, "INVALID_NATIVE_EVIDENCE_HASH")
    _sha(timeline.file_series_hash, "INVALID_FILE_SERIES_HASH")
    _sha(timeline.protocol_hash, "INVALID_PROTOCOL_HASH")
    _sha(timeline.metric_contract_hash, "INVALID_METRIC_CONTRACT_HASH")
    validate_file_second_series_authority_v1(file_series)
    if timeline.file_series_hash != file_series.self_hash or tuple(item.coordinate for item in timeline.points) != file_series.coordinates:
        _fail("ALARM_TIMELINE_FILE_SERIES_COVERAGE_MISMATCH")
    _validate_coordinates(tuple(item.coordinate for item in timeline.points))
    if any(type(item) is not CommonAlarmPointV1 for item in timeline.points):
        _fail("INVALID_ALARM_POINT")
    if any(type(item.alarm) is not bool or type(item.native_states) is not tuple or not item.native_states for item in timeline.points):
        _fail("INVALID_ALARM_POINT")
    if tuple(sorted(timeline.native_state_counts)) != timeline.native_state_counts:
        _fail("NATIVE_STATE_COUNTS_MUST_BE_SORTED")
    if any(type(name) is not str or not name or type(count) is not int or count < 0 for name, count in timeline.native_state_counts):
        _fail("INVALID_NATIVE_STATE_COUNT")
    if timeline.adapter_id == "DENSE_BOOLEAN_V1":
        for item in timeline.points:
            expected = ("ALARM",) if item.alarm else ("NO_ALARM",)
            if item.native_states != expected:
                _fail("DENSE_BOOLEAN_NATIVE_STATE_MISMATCH")
        expected_counts = (
            ("ALARM", sum(item.alarm for item in timeline.points)),
            ("NO_ALARM", sum(not item.alarm for item in timeline.points)),
        )
    elif timeline.adapter_id == "D1_NATIVE_RECONCILED_V1":
        allowed = {"PASS", "FAIL", "ABSTAIN", "NO_OPPORTUNITY"}
        flattened: list[str] = []
        for item in timeline.points:
            if tuple(sorted(item.native_states)) != item.native_states or set(item.native_states) - allowed:
                _fail("D1_NATIVE_STATE_INVALID")
            if "NO_OPPORTUNITY" in item.native_states and item.native_states != ("NO_OPPORTUNITY",):
                _fail("D1_NO_OPPORTUNITY_MIXED_WITH_OUTCOME")
            if item.alarm is not ("FAIL" in item.native_states):
                _fail("D1_FAIL_ONLY_ALARM_MISMATCH")
            flattened.extend(item.native_states)
        expected_counts = tuple(sorted((name, flattened.count(name)) for name in allowed))
    else:
        _fail("UNKNOWN_ALARM_ADAPTER")
    if timeline.native_state_counts != expected_counts:
        _fail("NATIVE_STATE_COUNT_REPLAY_MISMATCH")
    if timeline.self_hash != _self_hash(timeline.body_dict()):
        _fail("ALARM_TIMELINE_SELF_HASH_MISMATCH")
    return timeline.self_hash


def validate_label_timeline_v1(
    labels: LabelTimelineV1, *, file_series: FileSecondSeriesAuthorityV1,
) -> str:
    if type(labels) is not LabelTimelineV1:
        _fail("WRONG_LABEL_TIMELINE_TYPE")
    _identifier(labels.dataset_id, "INVALID_DATASET_ID")
    _sha(labels.label_authority_sha256, "INVALID_LABEL_AUTHORITY_HASH")
    _sha(labels.file_series_hash, "INVALID_FILE_SERIES_HASH")
    validate_file_second_series_authority_v1(file_series)
    if labels.file_series_hash != file_series.self_hash or tuple(item.coordinate for item in labels.points) != file_series.coordinates:
        _fail("LABEL_TIMELINE_FILE_SERIES_COVERAGE_MISMATCH")
    _validate_coordinates(tuple(item.coordinate for item in labels.points))
    if any(type(item.label) is not int or item.label not in (0, 1) for item in labels.points):
        _fail("INVALID_STRICT_BINARY_LABEL")
    if labels.self_hash != _self_hash(labels.body_dict()):
        _fail("LABEL_TIMELINE_SELF_HASH_MISMATCH")
    return labels.self_hash


def validate_common_evaluation_result_v1(
    result: CommonEvaluationResultV1, *, contract: CommonMetricContractV1,
    protocol: ValidationProtocolV1, prediction: CommonAlarmTimelineV1,
    labels: LabelTimelineV1, file_series: FileSecondSeriesAuthorityV1,
) -> str:
    if type(result) is not CommonEvaluationResultV1:
        _fail("WRONG_EVALUATION_RESULT_TYPE")
    if result != evaluate_common_timeline_v1(
        contract=contract, protocol=protocol, file_series=file_series,
        prediction=prediction, labels=labels,
    ):
        _fail("EVALUATION_RESULT_REPLAY_MISMATCH")
    return result.self_hash


def validate_common_comparison_result_v1(
    comparison: CommonComparisonResultV1, *, baseline: CommonEvaluationResultV1,
    candidate: CommonEvaluationResultV1, contract: CommonMetricContractV1,
    protocol: ValidationProtocolV1,
) -> str:
    if type(comparison) is not CommonComparisonResultV1:
        _fail("WRONG_COMPARISON_RESULT_TYPE")
    if comparison != compare_common_results_v1(contract=contract, protocol=protocol, baseline=baseline, candidate=candidate):
        _fail("COMPARISON_RESULT_REPLAY_MISMATCH")
    return comparison.self_hash


def validate_common_evaluation_bundle_v1(
    bundle: CommonEvaluationBundleV1, *, contract: CommonMetricContractV1,
    protocol: ValidationProtocolV1, results: tuple[CommonEvaluationResultV1, ...],
    comparisons: tuple[CommonComparisonResultV1, ...] = (),
) -> str:
    if type(bundle) is not CommonEvaluationBundleV1:
        _fail("WRONG_EVALUATION_BUNDLE_TYPE")
    if bundle != aggregate_synthetic_common_evaluation_v1(contract=contract, protocol=protocol, results=results, comparisons=comparisons):
        _fail("EVALUATION_BUNDLE_REPLAY_MISMATCH")
    return bundle.self_hash


__all__ = [
    "BooleanAlarmInputV1", "CommonAlarmPointV1", "CommonAlarmTimelineV1", "CommonEvaluationBundleV1",
    "CommonComparisonResultV1", "CommonEvaluationResultV1", "CommonMetricContractV1",
    "D1MetricOutcomeV1", "D1OutcomeInputV1", "FileIntervalV1", "FileSecondSeriesAuthorityV1", "LabelPointV1",
    "LabelTimelineV1", "MetricContractError", "MetricValueV1", "PredictionCoordinateV1",
    "adapt_boolean_alarm_timeline_v1", "adapt_d1_alarm_timeline_v1", "aggregate_synthetic_common_evaluation_v1",
    "build_common_metric_contract_v1", "build_file_second_series_authority_v1", "build_label_timeline_v1",
    "compare_common_results_v1", "derive_attack_event_units_v1", "evaluate_common_timeline_v1",
    "form_alarm_episodes_v1", "validate_common_alarm_timeline_v1", "validate_common_comparison_result_v1",
    "validate_common_evaluation_bundle_v1", "validate_common_evaluation_result_v1",
    "validate_common_metric_contract_v1", "validate_file_second_series_authority_v1", "validate_label_timeline_v1",
]
