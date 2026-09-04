"""Public-only closure of exact scientific run slots, not scientific execution."""
from xver_execution_common import PUB, PARENT, document, require


def scientific_receipts(version):
    context = document(PUB / f'HAI{version[:2]}_GDN_CONTEXT_MAPPING_V1.json')
    candidate = document(PARENT / f'HAI{version[:2]}_META_STAT_CANDIDATE_AUTHORITY_V2.json')
    authority = document(PUB / 'GDN_EXECUTION_AUTHORITY_V2.json')
    records = []
    for split in ('train1', 'train2'):
        for seed in (11, 23, 37):
            r = document(PUB / 'runs' / f'HAI{version[:2]}_{split.upper()}_SEED{seed}_RECEIPT_V1.json')
            require((r['version'], r['split'], r['seed']) == (version, split, seed), 'SCIENTIFIC_SLOT_IDENTITY')
            require(r['status'] == 'PASS' and r['scope'] == 'SCIENTIFIC', 'SCIENTIFIC_SLOT_COMPLETE')
            require(r['authority_hash'] == authority['self_hash'] and r['node_count'] == context['context_count'], 'SCIENTIFIC_SLOT_AUTHORITY')
            require(r['candidate_count'] == candidate['candidate_count'] and r['global_row_count'] == 5 * candidate['candidate_count'] and r['auxiliary_row_count'] == 10 * candidate['candidate_count'], 'SCIENTIFIC_SLOT_CENSUS')
            require(all(r[k] == 0 for k in ('provider_calls', 'credential_reads', 'attack_accesses', 'raw_timestamp_overlap')), 'SCIENTIFIC_SLOT_SAFETY')
            require(r['excluded_label_values_parsed'] is False and r['global_auxiliary_fused'] is False, 'SCIENTIFIC_SLOT_FIREWALL')
            records.append(r)
    require(len({r['run_identity_hash'] for r in records}) == 6, 'UNIQUE_SCIENTIFIC_IDENTITIES')
    return records
