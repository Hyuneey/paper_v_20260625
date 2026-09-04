"""Split-local structural-only extraction; schema-bound source intersection.

No numeric option loop, hidden confirmation, global or auxiliary GDN handle.
The arithmetic is the structural prefix of frozen EXP03B evidence generation.
"""
import statistics
from .exp03b_contract_v1 import SemanticTupleV1, StructuralTupleEvidenceV1, SOURCES, TARGETS, HORIZONS, require, digest
from .exp03b_evidence_v1 import slice_id
from .exp03b_numeric_v1 import nearest
from .exp03b_semantic_v2 import Train1SemanticEvidenceV2
from .exp03b_hidden_v2 import Train2SemanticEvidenceV2
from .exp02_bindings_v2a import extract_candidate_specific_events_v1
from paperworks.v6.continuous_step_protocol_v1 import derive_source_screening_parameters_v1, robust_one_step_scale_v1


def build_structural(*, split, matrix, feature_order, pairs, all_sources, all_targets, input_hash):
    import numpy as np
    require(split in ('train1', 'train2'), 'PROVIDER_VERIFIER_SPLITS_ONLY')
    array = np.asarray(matrix, dtype=np.float64)
    require(array.ndim == 2 and array.shape[1] == len(feature_order) and np.isfinite(array).all(), 'SPLIT_MATRIX_INVALID')
    require(len(set(feature_order)) == len(feature_order) and len(set(pairs)) == len(pairs), 'DUPLICATE_IDENTITY')
    columns = {name: array[:, i] for i, name in enumerate(feature_order)}
    require(bool(all_sources) and bool(all_targets) and len(set(all_sources)) == len(all_sources) and set(all_sources + all_targets) <= set(columns), 'ISOLATION_SOURCE_UNIVERSE')
    require(all(s in all_sources and t in all_targets for s, t in pairs), 'PAIR_ROLE_UNIVERSE')
    structural_events = {}
    for source in all_sources:
        p = derive_source_screening_parameters_v1(tuple(map(float, columns[source])))
        structural_events[source] = () if p.source_step_threshold is None else extract_candidate_specific_events_v1(columns[source], threshold=p.source_step_threshold, tolerance=p.source_stability_tolerance)
    scales = {target: robust_one_step_scale_v1(tuple(map(float, columns[target]))) for target in {t for _, t in pairs}}
    bundles = []
    for pair in pairs:
        source, target = pair
        others = tuple(sorted({e.event_index for s, events in structural_events.items() if s != source for e in events}))
        rows = []
        for sd in SOURCES:
            events = [e for e in structural_events[source] if e.direction == sd and (nearest(e.event_index, others) is None or nearest(e.event_index, others) > 2)]
            for h in HORIZONS:
                responses = [float(statistics.median(columns[target][e.event_index+h:e.event_index+h+3])) - float(statistics.median(columns[target][e.event_index-5:e.event_index])) for e in events if e.event_index >= 5 and e.event_index+h+3 <= len(array)]
                count = len(responses); scale = scales[target]
                up = sum(x > scale for x in responses)/count if count else 0.
                down = sum(x < -scale for x in responses)/count if count else 0.
                effect = abs(float(statistics.median(responses)))/scale if count else 0.
                for td in TARGETS:
                    semantic = SemanticTupleV1(sd, td, h)
                    rows.append(StructuralTupleEvidenceV1(semantic, count, up if td == 'increase' else down, down if td == 'increase' else up, effect, slice_id(split, pair, semantic, 'structure')))
        kind = Train1SemanticEvidenceV2 if split == 'train1' else Train2SemanticEvidenceV2
        bundles.append(kind('EXP03B-CAND-'+digest({'source': source, 'target': target})[:20], source, target, input_hash, tuple(sorted(rows, key=lambda r: r.semantic))))
    return tuple(bundles)
