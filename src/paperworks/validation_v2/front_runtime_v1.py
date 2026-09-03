"""One prepared runtime pass and lossless EXP05 trace capture for EXP04.

Trigger semantics are reused from frozen EXP02; this module only assembles
bounded windows and projects their logical decision coordinates.
"""
from __future__ import annotations
from bisect import bisect_left
from typing import Any, Iterator, Sequence

from .exp02_bindings_v2a import extract_candidate_specific_events_v1, _parameters, _nearest_distance
from .exp04_protocol_v1 import exp04_opportunity_id_v1
from .exp05_runner_v1 import _materialize_formal_v4_runtime_trace_v1, validate_exp05_run_authorization_v1
from .formal_v4_authority_v1 import load_formal_v4_numeric_value_map_v1
from .runtime_v1 import (
    FormalV4ObservationWindowV1, prepare_formal_v4_runtime_session_v1,
    execute_prepared_formal_v4_rule_v1, finalize_formal_v4_runtime_session_v1,
)


def iter_rule_windows_v1(*, bundle, context, root, matrix: Any, feature_order: Sequence[str], file_id: str) -> Iterator[FormalV4ObservationWindowV1]:
    """Candidate-specific event cache; both directions in other-source universe."""
    order = {name:i for i,name in enumerate(feature_order)}
    numerics = dict(load_formal_v4_numeric_value_map_v1(descriptors=bundle.authority.descriptors,
        numeric_authority_binding=bundle.authority.numeric_authority_binding,repository_root=root))
    parameters, events_by_relation, events_cache, sources, own = {}, {}, {}, {}, {}
    for descriptor in bundle.authority.descriptors:
        params = _parameters(tuple((role,value) for role,_reference,value in numerics[descriptor.relation_id]))
        if (params.source_pre_count,params.source_post_count,params.minimum_source_stability_fraction) != (5,5,0.8):
            raise ValueError("FROZEN_SOURCE_EVENT_CONTRACT_MISMATCH")
        parameters[descriptor.relation_id] = params
        key = (descriptor.source,params.source_step_threshold,params.source_stability_tolerance,
               params.source_pre_count,params.source_post_count,params.minimum_source_stability_fraction)
        if key not in events_cache:
            events_cache[key] = extract_candidate_specific_events_v1(matrix[:,order[descriptor.source]], threshold=params.source_step_threshold,tolerance=params.source_stability_tolerance)
        events = events_cache[key]
        events_by_relation[descriptor.relation_id] = tuple(e for e in events if e.direction == descriptor.source_direction)
        own[descriptor.relation_id] = tuple(e.event_index for e in events)
        sources.setdefault(descriptor.source,set()).update(e.event_index for e in events)
    other = {source:tuple(sorted(set().union(*(indices for s,indices in sources.items() if s != source)))) for source in sources}
    for descriptor in bundle.authority.descriptors:
        p = parameters[descriptor.relation_id]
        source, target = matrix[:,order[descriptor.source]], matrix[:,order[descriptor.target]]
        for event in events_by_relation[descriptor.relation_id]:
            event_index = event.event_index
            start = event_index + descriptor.selected_horizon_seconds
            end = start + p.target_response_count
            index = bisect_left(own[descriptor.relation_id],event_index)
            previous = None if index == 0 else float(event_index-own[descriptor.relation_id][index-1])
            yield FormalV4ObservationWindowV1(
                opportunity_id=exp04_opportunity_id_v1(file_id=file_id,row_index=end-1,rule_id=descriptor.relation_id),
                relation_id=descriptor.relation_id, feature_contract_hash=context.feature_contract_binding.content_sha256,
                file_contract_hash=context.file_contract_binding.content_sha256,sampling_contract_hash=context.sampling_contract_binding.content_sha256,
                event_index=event_index,target_response_start_index=start,
                source_pre_values=tuple(float(v) for v in source[event_index-p.source_pre_count:event_index]),
                source_post_values=tuple(float(v) for v in source[event_index:event_index+p.source_post_count]),
                target_baseline_values=tuple(float(v) for v in target[event_index-p.target_baseline_count:event_index]),
                target_response_values=tuple(float(v) for v in target[start:min(end,len(target))]),
                seconds_since_previous_source_trigger=previous,
                seconds_to_nearest_other_source_trigger=_nearest_distance(event_index,other[descriptor.source]),
                future_window_complete=end<=len(target))


def iter_evaluated_units_v1(*, bundle, context, root, authorization, windows, finalization_receipts: list):
    """One session, all native outcomes, no second Rule execution for EXP05."""
    validate_exp05_run_authorization_v1(authorization,bundle=bundle,execution_context=context)
    session = prepare_formal_v4_runtime_session_v1(bundle,execution_context=context,repository_root=root)
    try:
        for window in windows:
            trace = execute_prepared_formal_v4_rule_v1(session,window=window)
            unit = _materialize_formal_v4_runtime_trace_v1(bundle,authorization=authorization,
                execution_context=context,window=window,runtime_trace=trace)
            yield window,trace,unit
    finally:
        finalization_receipts.append(finalize_formal_v4_runtime_session_v1(session))
