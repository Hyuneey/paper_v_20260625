"""Prospective DEC-031 scenario, time-axis, and runtime bindings.

This module is pure and pre-access.  It accepts already-projected timestamp and
runtime records; it has no data-discovery, provider, credential, or protected
resource interface.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Mapping, Sequence

from .dg05_production_chain_v1 import digest_v1, self_hashed_v1


class DG05Dec031Error(ValueError):
    """Raised when a DEC-031 scientific binding is violated."""


DEC031_DECISION = "APPROVED_WITH_FAIL_CLOSED_TIME_AXIS_AND_SCOPED_NORMAL_SOURCE_MATERIALIZATION"
DEC031_BINDINGS = (
    "HIT_INTERVAL_LOCAL_DELAY",
    "FAIL_FILE_ON_DUPLICATE_TIMESTAMP",
    "FAIL_FILE_ON_NON_UNIT_GAP",
    "FOUR_WAY_RUNTIME_IDENTITY_CENSUS",
    "NORMAL_SOURCE_DISCOVERY_THEN_SCOPED_MATERIALIZATION_IF_ABSENT",
)


def _parse_timestamp(value: Any) -> datetime:
    if type(value) is not str or not value:
        raise DG05Dec031Error("PHYSICAL_TIMESTAMP_STRING_REQUIRED")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise DG05Dec031Error("PHYSICAL_TIMESTAMP_PARSE_FAILED") from exc
    return parsed


def _validate_timestamp_vector(timestamps: Sequence[str]) -> tuple[datetime, ...]:
    if not timestamps:
        raise DG05Dec031Error("PHYSICAL_TIMESTAMP_ROWS_REQUIRED")
    parsed = tuple(_parse_timestamp(value) for value in timestamps)
    if len(set(parsed)) != len(parsed):
        raise DG05Dec031Error("INVALID_TIMESTAMP_AUTHORITY_DUPLICATE")
    try:
        deltas = tuple(
            (current - previous).total_seconds()
            for previous, current in zip(parsed, parsed[1:])
        )
    except TypeError as exc:
        raise DG05Dec031Error("MIXED_TIMESTAMP_TIMEZONE_AUTHORITY") from exc
    if any(delta != 1.0 for delta in deltas):
        raise DG05Dec031Error("INVALID_TIMESTAMP_AUTHORITY_NON_UNIT_GAP")
    return parsed


def build_physical_timeline_authority_v1(
    *,
    panel_id: str,
    file_id: str,
    timestamps: Sequence[str],
    physical_file_authority_hash: str,
    projection_authority_hash: str,
    source_commit: str,
) -> dict[str, Any]:
    """Build a typed valid/invalid timeline authority without repairing rows."""
    if not panel_id or not file_id or not timestamps:
        raise DG05Dec031Error("TIMELINE_IDENTITY_AND_ROWS_REQUIRED")
    parsed = tuple(_parse_timestamp(value) for value in timestamps)
    timestamp_hash = digest_v1(list(timestamps))
    if len(set(parsed)) != len(parsed):
        status = "INVALID_TIMESTAMP_AUTHORITY_DUPLICATE"
    else:
        try:
            deltas = tuple((current - previous).total_seconds() for previous, current in zip(parsed, parsed[1:]))
        except TypeError as exc:
            raise DG05Dec031Error("MIXED_TIMESTAMP_TIMEZONE_AUTHORITY") from exc
        status = "VALID_PHYSICAL_ONE_SECOND_TIMESTAMP_AUTHORITY"
        if any(delta != 1.0 for delta in deltas):
            status = "INVALID_TIMESTAMP_AUTHORITY_NON_UNIT_GAP"
    return self_hashed_v1(
        {
            "schema": "dg05_physical_timeline_authority_v1",
            "panel_id": panel_id,
            "file_id": file_id,
            "status": status,
            "time_coordinate": "PHYSICAL_TIMESTAMP",
            "required_step_seconds": 1,
            "row_count": len(parsed),
            "timestamp_vector_hash": timestamp_hash,
            "physical_file_authority_hash": physical_file_authority_hash,
            "projection_authority_hash": projection_authority_hash,
            "duplicate_repair": "PROHIBITED",
            "gap_repair": "PROHIBITED",
            "source_commit": source_commit,
        }
    )


def require_valid_physical_timeline_v1(authority: Mapping[str, Any]) -> None:
    body = {key: value for key, value in authority.items() if key != "self_hash"}
    if (
        authority.get("schema") != "dg05_physical_timeline_authority_v1"
        or authority.get("self_hash") != digest_v1(body)
    ):
        raise DG05Dec031Error("TIMELINE_AUTHORITY_REPLAY_FAILED")
    status = authority.get("status")
    if status == "INVALID_TIMESTAMP_AUTHORITY_DUPLICATE":
        raise DG05Dec031Error(status)
    if status == "INVALID_TIMESTAMP_AUTHORITY_NON_UNIT_GAP":
        raise DG05Dec031Error(status)
    if status != "VALID_PHYSICAL_ONE_SECOND_TIMESTAMP_AUTHORITY":
        raise DG05Dec031Error("VALID_PHYSICAL_TIMESTAMP_AUTHORITY_REQUIRED")


def _seconds_decimal(start: datetime, end: datetime) -> str:
    try:
        delta = end - start
    except TypeError as exc:
        raise DG05Dec031Error("MIXED_TIMESTAMP_TIMEZONE_AUTHORITY") from exc
    microseconds = (
        delta.days * 86_400_000_000
        + delta.seconds * 1_000_000
        + delta.microseconds
    )
    value = Decimal(microseconds) / Decimal(1_000_000)
    # Six decimal places preserve physical microsecond precision without the
    # integer truncation used by the historical bridge.
    return format(value, ".6f")


def interval_local_detection_v1(
    *,
    alarm_timestamps: Sequence[str],
    closed_intervals: Sequence[Sequence[str]],
) -> dict[str, Any]:
    """Return one-scenario hit and interval-local physical-time delay."""
    alarms = tuple(sorted(_parse_timestamp(value) for value in alarm_timestamps))
    intervals: list[tuple[int, datetime, datetime]] = []
    for ordinal, value in enumerate(closed_intervals):
        if type(value) not in (list, tuple) or len(value) != 2:
            raise DG05Dec031Error("VALID_CLOSED_INTERVALS_REQUIRED")
        start, end = _parse_timestamp(value[0]), _parse_timestamp(value[1])
        try:
            invalid = start > end
        except TypeError as exc:
            raise DG05Dec031Error("MIXED_TIMESTAMP_TIMEZONE_AUTHORITY") from exc
        if invalid:
            raise DG05Dec031Error("VALID_CLOSED_INTERVALS_REQUIRED")
        intervals.append((ordinal, start, end))
    if not intervals:
        raise DG05Dec031Error("VALID_CLOSED_INTERVALS_REQUIRED")

    earliest_hit: datetime | None = None
    containing: list[tuple[int, datetime, datetime]] = []
    for alarm in alarms:
        local = [row for row in intervals if row[1] <= alarm <= row[2]]
        if local:
            earliest_hit = alarm
            containing = local
            break
    if earliest_hit is None:
        return {
            "scenario_outcome": "MISS",
            "earliest_hit_timestamp": None,
            "containing_interval_index": None,
            "containing_interval_start": None,
            "interval_local_delay_seconds": None,
            "detection_delay_status": "NOT_DETECTED",
            "delay_terminology": "INTERVAL_LOCAL_DETECTION_DELAY",
        }
    # Earliest start wins; canonical authority order resolves equal starts.
    ordinal, start, _end = min(containing, key=lambda row: (row[1], row[0]))
    return {
        "scenario_outcome": "HIT",
        "earliest_hit_timestamp": earliest_hit.isoformat(),
        "containing_interval_index": ordinal,
        "containing_interval_start": start.isoformat(),
        "interval_local_delay_seconds": _seconds_decimal(start, earliest_hit),
        "detection_delay_status": "DEFINED",
        "delay_terminology": "INTERVAL_LOCAL_DETECTION_DELAY",
    }


def build_timeline_failure_receipts_v1(
    *,
    panel_id: str,
    file_id: str,
    method_authority_hashes: Mapping[str, str],
    timeline_authority: Mapping[str, Any],
    release_manifest_hash: str,
) -> tuple[dict[str, Any], ...]:
    """Represent a file-level timeline failure for every expected method cell."""
    body = {key: value for key, value in timeline_authority.items() if key != "self_hash"}
    if timeline_authority.get("self_hash") != digest_v1(body):
        raise DG05Dec031Error("TIMELINE_AUTHORITY_REPLAY_FAILED")
    status = timeline_authority.get("status")
    if status not in {
        "INVALID_TIMESTAMP_AUTHORITY_DUPLICATE",
        "INVALID_TIMESTAMP_AUTHORITY_NON_UNIT_GAP",
    }:
        raise DG05Dec031Error("INVALID_TIMELINE_AUTHORITY_REQUIRED")
    receipts = []
    for method_id, method_hash in sorted(method_authority_hashes.items()):
        receipts.append(
            self_hashed_v1(
                {
                    "schema": "dg05_prediction_terminal_receipt_v4",
                    "cell_id": digest_v1([panel_id, file_id, method_id]),
                    "panel_id": panel_id,
                    "file_id": file_id,
                    "method_id": method_id,
                    "status": "METHOD_FAILURE",
                    "failure_code": status,
                    "timeline_authority_hash": timeline_authority["self_hash"],
                    "method_authority_hash": method_hash,
                    "release_manifest_hash": release_manifest_hash,
                    "prediction_artifact_hash": None,
                    "runtime_trace_hash": None,
                    "scientific_prediction_invoked": False,
                    "partial_file_result_allowed": False,
                }
            )
        )
    return tuple(receipts)


_COUNT_FIELDS = (
    "opportunities",
    "pass",
    "fail",
    "abstain",
    "system_errors",
    "evaluation_invocations",
    "evaluated_system_errors",
)


def derive_four_way_runtime_census_v1(
    *,
    configured_rule_sources: Mapping[str, str],
    file_timestamps: Mapping[str, Sequence[str]],
    traces: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Derive configured/formed/evaluated/alarming identities from exact traces."""
    configured = dict(configured_rule_sources)
    if not configured or any(not key or not value for key, value in configured.items()):
        raise DG05Dec031Error("CONFIGURED_RULE_SOURCE_AUTHORITY_REQUIRED")
    if set(file_timestamps) != {str(trace.get("file_id")) for trace in traces} or not traces:
        raise DG05Dec031Error("COMPLETE_RUNTIME_FILE_CENSUS_REQUIRED")

    parsed_by_file: dict[str, tuple[datetime, ...]] = {}
    for file_id, timestamps in file_timestamps.items():
        parsed_by_file[file_id] = _validate_timestamp_vector(timestamps)

    totals = {field: 0 for field in _COUNT_FIELDS}
    formed: set[str] = set()
    evaluated: set[str] = set()
    alarming: set[str] = set()
    system_error_rules: set[str] = set()
    union_alarm_seconds: set[tuple[str, datetime]] = set()
    episode_count = 0

    for trace in traces:
        file_id = trace["file_id"]
        per_rule = trace.get("per_rule_runtime")
        if type(per_rule) is not list or {row.get("rule_id") for row in per_rule if type(row) is dict} != set(configured):
            raise DG05Dec031Error("EXACT_CONFIGURED_RULE_TRACE_CENSUS_REQUIRED")
        aggregate = {field: 0 for field in _COUNT_FIELDS}
        local_fail_rows: set[int] = set()
        seen: set[str] = set()
        for row in per_rule:
            required = {
                "rule_id", "source_id", *_COUNT_FIELDS, "fail_rows",
            }
            if type(row) is not dict or set(row) != required:
                raise DG05Dec031Error("FOUR_WAY_PER_RULE_RUNTIME_SCHEMA_REQUIRED")
            rule_id = row["rule_id"]
            if type(rule_id) is not str or rule_id in seen or row["source_id"] != configured.get(rule_id):
                raise DG05Dec031Error("RULE_SOURCE_OR_IDENTITY_AUTHORITY_MISMATCH")
            seen.add(rule_id)
            if any(type(row[field]) is not int or isinstance(row[field], bool) or row[field] < 0 for field in _COUNT_FIELDS):
                raise DG05Dec031Error("FOUR_WAY_RUNTIME_COUNT_INVALID")
            if row["opportunities"] != row["pass"] + row["fail"] + row["abstain"] + row["system_errors"]:
                raise DG05Dec031Error("FOUR_WAY_RUNTIME_OUTCOME_CENSUS_MISMATCH")
            if row["evaluated_system_errors"] > row["system_errors"]:
                raise DG05Dec031Error("EVALUATED_SYSTEM_ERROR_COUNT_INVALID")
            expected_invocations = row["pass"] + row["fail"] + row["abstain"] + row["evaluated_system_errors"]
            if row["evaluation_invocations"] != expected_invocations or row["evaluation_invocations"] > row["opportunities"]:
                raise DG05Dec031Error("EVALUATION_INVOCATION_CENSUS_MISMATCH")
            fail_rows = row["fail_rows"]
            if (
                type(fail_rows) is not list
                or fail_rows != sorted(set(fail_rows))
                or any(type(index) is not int or index < 0 or index >= len(parsed_by_file[file_id]) for index in fail_rows)
                or len(fail_rows) != row["fail"]
            ):
                raise DG05Dec031Error("RULE_FAIL_ROW_PROVENANCE_MISMATCH")
            local_fail_rows.update(fail_rows)
            for field in _COUNT_FIELDS:
                aggregate[field] += row[field]
                totals[field] += row[field]
            if row["opportunities"]:
                formed.add(rule_id)
            if row["evaluation_invocations"]:
                evaluated.add(rule_id)
            if row["fail"]:
                alarming.add(rule_id)
            if row["system_errors"]:
                system_error_rules.add(rule_id)
        if any(trace.get(field) != aggregate[field] for field in _COUNT_FIELDS):
            raise DG05Dec031Error("AGGREGATE_FOUR_WAY_RUNTIME_MISMATCH")
        if trace.get("rule_alarm_rows") != sorted(local_fail_rows):
            raise DG05Dec031Error("RULE_ALARM_ROW_UNION_MISMATCH")
        local_times = [parsed_by_file[file_id][index] for index in sorted(local_fail_rows)]
        episode_count += sum(
            ordinal == 0 or (value - local_times[ordinal - 1]).total_seconds() != 1
            for ordinal, value in enumerate(local_times)
        )
        union_alarm_seconds.update((file_id, value) for value in local_times)

    configured_ids = set(configured)
    source_sets = {
        "configured": {configured[rule_id] for rule_id in configured_ids},
        "formed": {configured[rule_id] for rule_id in formed},
        "evaluated": {configured[rule_id] for rule_id in evaluated},
        "alarming": {configured[rule_id] for rule_id in alarming},
    }
    return {
        **totals,
        "configured_rule_ids": sorted(configured_ids),
        "configured_rule_count": len(configured_ids),
        "formed_rule_ids": sorted(formed),
        "formed_rule_count": len(formed),
        "evaluated_rule_ids": sorted(evaluated),
        "evaluated_rule_count": len(evaluated),
        "alarming_rule_ids": sorted(alarming),
        "alarming_rule_count": len(alarming),
        "system_error_rule_ids": sorted(system_error_rules),
        "system_error_rule_count": len(system_error_rules),
        "configured_source_identities": sorted(source_sets["configured"]),
        "formed_source_identities": sorted(source_sets["formed"]),
        "evaluated_source_identities": sorted(source_sets["evaluated"]),
        "alarming_source_identities": sorted(source_sets["alarming"]),
        "physical_union_alarm_seconds": len(union_alarm_seconds),
        "physical_union_alarm_episodes": episode_count,
        "unqualified_participating_rules_field": "PROHIBITED",
    }


__all__ = [
    "DEC031_BINDINGS",
    "DEC031_DECISION",
    "DG05Dec031Error",
    "build_physical_timeline_authority_v1",
    "build_timeline_failure_receipts_v1",
    "derive_four_way_runtime_census_v1",
    "interval_local_detection_v1",
    "require_valid_physical_timeline_v1",
]
