"""Freeze the explicitly approved schema-only amendment before normal I/O."""
from pathlib import Path
from hashlib import sha256
import json
from paperworks.validation_v2.exp03b_custody_v1 import seal, publish, replay

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT/'research_control_center/validation_v2/dg04_xver_prep'


def main():
    old = json.loads((PUB/'XVER_NORMAL_MATERIALIZATION_CONTRACT_V1.json').read_text()); replay(old)
    mapping = json.loads((PUB/'P1_FEATURE_MAPPING_AUTHORITY_V1.json').read_text()); replay(mapping)
    files = ['src/paperworks/data/hai_normal_projection_v2.py', 'scripts/materialize_xver_projection_v2.py',
             'scripts/materialize_xver_normal_v1.py', 'tests/test_hai_normal_projection_v2.py']
    value = seal({'schema': 'normal_schema_only_projection_contract_v2',
        'approval': 'NORMAL_DATA_CUSTODY_SCHEMA_ONLY_ALLOWLIST_PROJECTION', 'status': 'USER_APPROVED',
        'supersedes_only': 'V1 label-free-container schema gate; historical source/byte identities unchanged',
        'historical_transport_contract_hash': old['self_hash'], 'mapping_hash': mapping['self_hash'],
        'resume_head': '77f340f6257054007b4e934d70d3a4a9e76803ec',
        'projection_policy': 'TIMESTAMP_PLUS_APPROVED_FEATURE_ALLOWLIST',
        'features': {v: [r[f'hai{v[:2]}_identity'] for r in mapping['rows']
                         if r[f'hai{v[:2]}_mapping'] == 'EXACT_MATCH'] for v in ('22.04', '21.03')},
        'timestamp_schema_allowlist': ['timestamp', 'time'],
        'unknown_fields': 'EXCLUDE_WITHOUT_VALUE_DESERIALIZATION',
        'excluded_values_decoded': False, 'excluded_values_validated': False,
        'raw_container_byte_traversal_allowed': True,
        'normal_role_authority': 'PINNED_OFFICIAL_NORMAL_FILE_IDENTITY_NOT_LABEL_VALUES',
        'hai21_partition': {'n': 'projected row_count', 'mid': 'floor(n/2)', 'purge_seconds': 60,
             'A': '[0,mid-30)', 'B': '[mid+30,n)', 'context_basis':
             'max(history5,source_pre5,source_post5,refractory10,isolation2,baseline5,response3,horizon60)',
             'no_cross_partition_context': True},
        'provider_calls_allowed': False, 'attack_files_allowed': False,
        'implementation_hashes': {p: sha256((ROOT/p).read_bytes()).hexdigest() for p in files}})
    publish(PUB/'NORMAL_SCHEMA_ONLY_PROJECTION_CONTRACT_V2.json', value)
    print(json.dumps({'status': 'FROZEN', 'hash': value['self_hash'], 'features': {v:len(f) for v,f in value['features'].items()}}))


if __name__ == '__main__': main()
