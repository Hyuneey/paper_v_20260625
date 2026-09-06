"""Prospective DEC-031 runtime-trace adapter over frozen DG-05 methods.

The adapter reuses the exact frozen detector, Rule evaluator, parameter and
Fusion implementations.  Its only change is evidence enrichment: every Rule
gets an explicit runtime row, including configured Rules with zero formed
opportunities.  A baseline execution is compared byte-for-byte at the dense
alarm level so trace enrichment cannot change scientific predictions.
"""
from __future__ import annotations

from bisect import bisect_left
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

from .dg05_execution_closure_v1 import (
    DG05ProductionExecutorV1,
    MethodDispatchEntryV1,
    fuse_dense_masks_v1,
)
from .dg05_dec031_v1 import derive_four_way_runtime_census_v1
from .dg05_dec031_v1 import build_physical_timeline_authority_v1, require_valid_physical_timeline_v1


class DG05RuntimeAdapterV4Error(ValueError):
    """Raised when trace enrichment diverges from the frozen runtime."""


def _execute_detector_v4(
    *, executor: DG05ProductionExecutorV1, panel_id: str, detector_id: str,
    feature_order: tuple[str, ...], matrix: Any, projection: Any,
) -> tuple[bool, ...]:
    """Use frozen scoring, correcting only the HAI23 IF field accessor."""
    from .multipanel_custody_v1 import FROZEN_PANEL_ORDER_V2
    if panel_id != FROZEN_PANEL_ORDER_V2[0] or detector_id != "ISOLATION_FOREST":
        return executor._detector(panel_id, detector_id, feature_order, matrix, projection)[0]
    from .dg05_execution_closure_v1 import _score_hai23_isolation_forest_v1
    model, threshold, authority = executor._load_detector(panel_id, detector_id)
    executor._validate_bound_implementation(authority)
    if (
        tuple(model.fit_receipt.feature_ids) != feature_order
        or model.fit_receipt.self_hash != authority.fit_authority_hash
        or threshold.self_hash != authority.threshold_authority_hash
    ):
        raise DG05RuntimeAdapterV4Error("HAI23_IF_AUTHORITY_REPLAY_MISMATCH")
    try:
        import numpy as np
        scores = _score_hai23_isolation_forest_v1(model, matrix)
        return tuple(bool(value) for value in np.asarray(scores > float(threshold.threshold), dtype=np.bool_))
    except Exception as exc:
        raise DG05RuntimeAdapterV4Error("BOUND_HAI23_IF_EXECUTION_FAILED") from exc


def execute_rule_with_four_way_trace_v4(
    *,
    executor: DG05ProductionExecutorV1,
    panel_id: str,
    portfolio_role: str,
    feature_order: tuple[str, ...],
    matrix: Any,
    file_id: str,
    timestamps: Sequence[str],
) -> tuple[tuple[bool, ...], dict[str, Any]]:
    """Execute frozen Rule semantics and add exact DEC-031 evidence."""
    executor.validate()
    baseline_alarms, baseline = executor._rule(panel_id, portfolio_role, feature_order, matrix, file_id)
    relations, numeric, authority = executor._load_rule_asset(panel_id, portfolio_role)
    from paperworks.validation_v2.exp02_bindings_v2a import (
        _nearest_distance,
        _parameters,
        extract_candidate_specific_events_v1,
    )
    from paperworks.validation_v2.runtime_v1 import evaluate_formal_v4_semantics_v1

    order = {name: index for index, name in enumerate(feature_order)}
    if any(row["source"] not in order or row["target"] not in order for row in relations):
        raise DG05RuntimeAdapterV4Error("RULE_RUNTIME_FEATURE_ORDER_MISMATCH")
    parameters = {relation_id: _parameters(values) for relation_id, values in numeric.items()}
    own: dict[str, tuple[int, ...]] = {}
    events_by_relation: dict[str, tuple[Any, ...]] = {}
    source_events: dict[str, set[int]] = {}
    for relation in relations:
        relation_id = relation["relation_id"]
        values = parameters[relation_id]
        events = extract_candidate_specific_events_v1(
            matrix[:, order[relation["source"]]],
            threshold=values.source_step_threshold,
            tolerance=values.source_stability_tolerance,
        )
        events_by_relation[relation_id] = tuple(
            event for event in events if event.direction == relation["source_direction"]
        )
        own[relation_id] = tuple(event.event_index for event in events)
        source_events.setdefault(relation["source"], set()).update(event.event_index for event in events)
    other = {
        source: tuple(
            sorted(set().union(*(indices for name, indices in source_events.items() if name != source)))
        )
        for source in source_events
    }

    per_rule: list[dict[str, Any]] = []
    enriched_alarms = [False] * len(matrix)
    fail_sources: dict[int, set[str]] = {}
    for relation in sorted(relations, key=lambda row: row["relation_id"]):
        relation_id = relation["relation_id"]
        values = parameters[relation_id]
        source = matrix[:, order[relation["source"]]]
        target = matrix[:, order[relation["target"]]]
        counts = {name: 0 for name in ("PASS", "FAIL", "ABSTAIN", "SYSTEM_ERROR")}
        fail_rows: list[int] = []
        for event in events_by_relation[relation_id]:
            event_index = event.event_index
            start = event_index + relation["selected_horizon_seconds"]
            end = start + values.target_response_count
            location = bisect_left(own[relation_id], event_index)
            previous = None if location == 0 else float(event_index - own[relation_id][location - 1])
            outcome = evaluate_formal_v4_semantics_v1(
                source_direction=relation["source_direction"],
                target_direction=relation["target_direction"],
                parameters=values,
                source_pre_values=tuple(float(item) for item in source[event_index-values.source_pre_count:event_index]),
                source_post_values=tuple(float(item) for item in source[event_index:event_index+values.source_post_count]),
                target_baseline_values=tuple(float(item) for item in target[event_index-values.target_baseline_count:event_index]),
                target_response_values=tuple(float(item) for item in target[start:min(end, len(target))]),
                seconds_since_previous_source_trigger=previous,
                seconds_to_nearest_other_source_trigger=_nearest_distance(event_index, other[relation["source"]]),
                future_window_complete=end <= len(target),
            )
            counts[outcome.outcome] += 1
            decision = end - 1
            if outcome.outcome == "FAIL" and 0 <= decision < len(enriched_alarms):
                fail_rows.append(decision)
                enriched_alarms[decision] = True
                fail_sources.setdefault(decision, set()).add(relation["source"])
        if fail_rows != sorted(set(fail_rows)):
            raise DG05RuntimeAdapterV4Error("DUPLICATE_RULE_FAIL_ROW_PROVENANCE")
        per_rule.append(
            {
                "rule_id": relation_id,
                "source_id": relation["source"],
                "opportunities": sum(counts.values()),
                "pass": counts["PASS"],
                "fail": counts["FAIL"],
                "abstain": counts["ABSTAIN"],
                "system_errors": counts["SYSTEM_ERROR"],
                "evaluation_invocations": sum(counts.values()),
                "evaluated_system_errors": counts["SYSTEM_ERROR"],
                "fail_rows": fail_rows,
            }
        )

    alarms = tuple(enriched_alarms)
    if alarms != tuple(baseline_alarms):
        raise DG05RuntimeAdapterV4Error("TRACE_ENRICHMENT_ALARM_DIVERGENCE")
    trace_sources = baseline.get("fail_sources_by_row")
    enriched_sources = {str(index): sorted(values) for index, values in sorted(fail_sources.items())}
    if trace_sources != enriched_sources:
        raise DG05RuntimeAdapterV4Error("TRACE_ENRICHMENT_SOURCE_PROVENANCE_DIVERGENCE")
    totals = {
        field: sum(row[field] for row in per_rule)
        for field in (
            "opportunities", "pass", "fail", "abstain", "system_errors",
            "evaluation_invocations", "evaluated_system_errors",
        )
    }
    for field in ("opportunities", "pass", "fail", "abstain", "system_errors"):
        if totals[field] != baseline[field]:
            raise DG05RuntimeAdapterV4Error("TRACE_ENRICHMENT_COUNT_DIVERGENCE")
    rule_alarm_rows = [index for index, value in enumerate(alarms) if value]
    trace = {
        **totals,
        "file_id": file_id,
        "per_rule_runtime": per_rule,
        "rule_alarm_rows": rule_alarm_rows,
        "rule_component_alarm_rows": rule_alarm_rows,
        "fail_sources_by_row": {str(index): sorted(values) for index, values in sorted(fail_sources.items())},
        "runtime_use_authority_hash": authority.runtime_use_authority_hash,
        "runtime_finalization_count": 1,
        "configured_rule_sources": {
            relation["relation_id"]: relation["source"]
            for relation in sorted(relations, key=lambda row: row["relation_id"])
        },
        "trace_enrichment_alarm_equivalence": True,
        "baseline_trace_hash": sha256(
            json.dumps(baseline, sort_keys=True, separators=(",", ":")).encode("ascii")
        ).hexdigest(),
    }
    census = derive_four_way_runtime_census_v1(
        configured_rule_sources=trace["configured_rule_sources"],
        file_timestamps={file_id: timestamps},
        traces=[trace],
    )
    trace["four_way_runtime_census"] = census
    return alarms, trace


def execute_normal_method_v4(
    *,
    executor: DG05ProductionExecutorV1,
    entry: MethodDispatchEntryV1,
    feature_order: tuple[str, ...],
    matrix: Any,
    file_id: str,
    projection_hash: str,
    timestamps: Sequence[str],
) -> tuple[tuple[bool, ...], Mapping[str, Any] | None]:
    """Dispatch an already-frozen method on an authorized normal projection."""
    from .dg05_execution_closure_v1 import _METHOD_RUNTIME_BINDING_V1

    bound_entry = executor.dispatch_registry.lookup(entry.panel_id, entry.method_id)
    if bound_entry.document() != entry.document():
        raise DG05RuntimeAdapterV4Error("DISPATCH_ENTRY_AUTHORITY_MISMATCH")
    timeline = build_physical_timeline_authority_v1(
        panel_id=entry.panel_id, file_id=file_id, timestamps=timestamps,
        physical_file_authority_hash=projection_hash,
        projection_authority_hash=projection_hash,
        source_commit=executor.executable_manifest.source_commit,
    )
    require_valid_physical_timeline_v1(timeline)
    executor.validate()
    detector_id, role = _METHOD_RUNTIME_BINDING_V1[entry.method_id]
    detector = (
        _execute_detector_v4(
            executor=executor, panel_id=entry.panel_id, detector_id=detector_id,
            feature_order=feature_order, matrix=matrix,
            projection=_NormalProjection(file_id, len(matrix), projection_hash),
        )
        if detector_id else None
    )
    rule, trace = (
        execute_rule_with_four_way_trace_v4(
            executor=executor,
            panel_id=entry.panel_id,
            portfolio_role=role,
            feature_order=feature_order,
            matrix=matrix,
            file_id=file_id,
            timestamps=timestamps,
        )
        if role else (None, None)
    )
    if detector is not None and rule is not None:
        fused = fuse_dense_masks_v1(detector, trace["fail_sources_by_row"])
        return fused, {
            **trace,
            "rule_component_alarm_rows": trace["rule_alarm_rows"],
            "fusion_base_alarm_rows": [index for index, value in enumerate(detector) if value],
            "fusion_output_alarm_rows": [index for index, value in enumerate(fused) if value],
            "base_preservation": all((not base) or output for base, output in zip(detector, fused, strict=True)),
        }
    if rule is not None:
        return rule, trace
    if detector is not None:
        return detector, None
    raise DG05RuntimeAdapterV4Error("FROZEN_METHOD_BINDING_ABSENT")


class _NormalProjection:
    """Minimum read-only shape expected by the frozen external scorer."""

    def __init__(self, file_id: str, row_count: int, projection_hash: str) -> None:
        self.file_id = file_id
        self.row_count = row_count
        self.projection_hash = projection_hash


__all__ = [
    "DG05RuntimeAdapterV4Error",
    "execute_normal_method_v4",
    "execute_rule_with_four_way_trace_v4",
]
