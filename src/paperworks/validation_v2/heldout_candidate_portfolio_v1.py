"""Pure retained-membership validation. No runtime or attack authorization."""
from __future__ import annotations
from collections import Counter
from .exp03b_contract_v1 import require, digest
from .exp03b_custody_v1 import seal, replay


def semantic_key(row: dict) -> tuple:
    return (row['source'], row['target'], row['source_direction'], row['target_direction'],
            row['selected_horizon_seconds'])


def retained_descriptors(descriptors: list[dict], states: list, pairs: dict) -> list[dict]:
    keys = set()
    for cid, semantic, status in states:
        require(cid in pairs, 'UNKNOWN_GUARD_PAIR')
        if status == 'RETAINED':
            source, target = pairs[cid]
            key = (source, target, semantic['source_direction'], semantic['target_direction'], semantic['horizon_seconds'])
            require(key not in keys, 'DUPLICATE_RETAINED_RELATION')
            keys.add(key)
    all_keys = [semantic_key(row) for row in descriptors]
    require(len(all_keys) == len(set(all_keys)), 'DUPLICATE_DESCRIPTOR_SEMANTICS')
    require(keys <= set(all_keys), 'RETAINED_DESCRIPTOR_MISSING')
    return [row for row in descriptors if semantic_key(row) in keys]


def census(rows: list[dict]) -> dict:
    keys = [semantic_key(row) for row in rows]
    return {'pair_count': len({x[:2] for x in keys}), 'rule_count': len(keys),
            'source_count': len({x[0] for x in keys}), 'target_count': len({x[1] for x in keys}),
            'horizon_distribution': dict(sorted(Counter(str(x[4]) for x in keys).items()))}


def compare(left: list[dict], right: list[dict]) -> dict:
    a, b = {semantic_key(x) for x in left}, {semantic_key(x) for x in right}
    dirs_a, dirs_b = {x[:4]: x[4] for x in a}, {x[:4]: x[4] for x in b}
    common_dirs = set(dirs_a) & set(dirs_b)
    common_pairs = {x[:2] for x in a} & {x[:2] for x in b}
    return {'pair_overlap': len(common_pairs), 'directional_overlap': len(common_dirs),
            'exact_semantic_overlap': len(a & b), 'left_only_rules': len(a - b),
            'right_only_rules': len(b - a),
            'horizon_agreement': sum(dirs_a[x] == dirs_b[x] for x in common_dirs),
            'horizon_disagreement': sum(dirs_a[x] != dirs_b[x] for x in common_dirs),
            'direction_disagreement_pairs': sum({x[2:4] for x in a if x[:2] == p} !=
                                                {x[2:4] for x in b if x[:2] == p} for p in common_pairs)}


def candidate_manifest(*, arm: str, repeat: int, descriptors: list[dict], lineage: dict,
                       method_lock_hash: str, source_commit: str, guard_census: dict,
                       stage_counts: dict) -> dict:
    require(arm in ('T0', 'T2') and repeat == 1, 'PREASSIGNED_REPEAT_REQUIRED')
    require(descriptors and len({semantic_key(r) for r in descriptors}) == len(descriptors), 'INVALID_CANDIDATE_PORTFOLIO')
    require(all(r['relation_id'] in lineage for r in descriptors), 'LINEAGE_REQUIRED')
    prefix = 'DETERMINISTIC_T0' if arm == 'T0' else 'AGENTIC_T2'
    value = seal({'schema': 'heldout_candidate_portfolio_v1',
        'portfolio_id': prefix + '_HELDOUT_CANDIDATE_PORTFOLIO_V1',
        'status': 'HELDOUT_CANDIDATE', 'arm': arm, 'repeat': repeat,
        'production_authorized': False, 'attack_access_authorized': False,
        'method_lock_hash': method_lock_hash, 'source_commit': source_commit,
        'authority_family': 'FORMAL_V4', 'census': census(descriptors), 'stage_counts': stage_counts,
        'ordered_descriptor_hashes': [d['descriptor_hash'] for d in descriptors],
        'descriptor_set_digest': digest([d['descriptor_hash'] for d in descriptors]),
        'rules': [{'rule_id': prefix + '-RULE-' + digest(d['descriptor_hash'])[:24],
                   'descriptor': d, 'lineage': lineage[d['relation_id']]} for d in descriptors],
        'frozen_train4_census': guard_census,
        'guard_context': 'ORIGINAL_FROZEN_ARM_GROUP_CROSS_SOURCE_UNIVERSE_NOT_RECOMPUTED',
        'opportunity_relation_coverage': 'NOT_RETAINED_IN_FROZEN_AGGREGATE'})
    replay(value)
    return value
