"""Sole normal-container and allowlist-projection writer; never reads labels."""
from pathlib import Path
from hashlib import sha256
import argparse
import json
import subprocess
import time
from paperworks.validation_v2.exp03b_custody_v1 import seal, publish, replay
from paperworks.validation_v2.exp03b_contract_v1 import require, digest
from paperworks.data.hai_xver_normal_v1 import validate_contract, sha256_file
from paperworks.data.hai_normal_projection_v2 import project
from materialize_xver_normal_v1 import cache_root, acquire

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT/'research_control_center/validation_v2/dg04_xver_prep'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', choices=('22.04','21.03'), required=True)
    args = parser.parse_args()
    contract = json.loads((PUB/'NORMAL_SCHEMA_ONLY_PROJECTION_CONTRACT_V2.json').read_text()); replay(contract)
    old = json.loads((PUB/'XVER_NORMAL_MATERIALIZATION_CONTRACT_V1.json').read_text()); validate_contract(old)
    require(contract['historical_transport_contract_hash'] == old['self_hash'], 'TRANSPORT_AUTHORITY')
    require(contract['approval'] == 'NORMAL_DATA_CUSTODY_SCHEMA_ONLY_ALLOWLIST_PROJECTION' and
            contract['status'] == 'USER_APPROVED' and contract['provider_calls_allowed'] is False and
            contract['attack_files_allowed'] is False and contract['excluded_values_decoded'] is False and
            contract['excluded_values_validated'] is False, 'PROJECTION_AUTHORIZATION')
    mapping = json.loads((PUB/'P1_FEATURE_MAPPING_AUTHORITY_V1.json').read_text()); replay(mapping)
    require(mapping['self_hash'] == contract['mapping_hash'], 'MAPPING_AUTHORITY')
    for version in ('22.04','21.03'):
        require(contract['features'][version] == [r[f'hai{version[:2]}_identity'] for r in mapping['rows']
                if r[f'hai{version[:2]}_mapping'] == 'EXACT_MATCH'], 'ORDERED_MAPPING_ALLOWLIST')
    for relative, h in contract['implementation_hashes'].items():
        require(sha256((ROOT/relative).read_bytes()).hexdigest() == h, 'PROJECTION_CODE_FREEZE')
    source_commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    require(subprocess.run(['git','merge-base','--is-ancestor',contract['resume_head'],source_commit],cwd=ROOT).returncode == 0,
            'RESUME_ANCESTRY')
    for name in ('NORMAL_SCHEMA_ONLY_PROJECTION_CONTRACT_V2.json','P1_FEATURE_MAPPING_AUTHORITY_V1.json',
                 'XVER_NORMAL_MATERIALIZATION_CONTRACT_V1.json'):
        relative = (PUB/name).relative_to(ROOT).as_posix()
        require((PUB/name).read_bytes() == subprocess.check_output(['git','show',source_commit+':'+relative],cwd=ROOT),
                'UNCOMMITTED_PROJECTION_AUTHORITY')
    for relative, h in contract['implementation_hashes'].items():
        require(sha256(subprocess.check_output(['git','show',source_commit+':'+relative],cwd=ROOT)).hexdigest() == h, 'UNCOMMITTED_PROJECTION_CODE')
    root = cache_root()
    records = []
    for row in [r for r in old['records'] if r['version'] == args.version]:
        print(json.dumps({'phase':'NORMAL_CONTAINER','symbolic_id':row['symbolic_id']}),flush=True)
        path, raw_hash, transferred = acquire(root, row)
        destination = root/'projections_v2'/f"{row['symbolic_id']}.csv"
        receipt_path = destination.with_suffix('.receipt.json')
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_text()); replay(receipt)
            require(receipt['contract_hash'] == contract['self_hash'] and receipt['raw_container_hash'] == raw_hash and
                    sha256_file(destination) == receipt['projection_hash'], 'CACHED_PROJECTION_AUTHORITY')
        else:
            start = time.perf_counter()
            result = project(path, destination, tuple(contract['features'][args.version]),
                             allowlist_hash=digest(contract['features'][args.version]))
            require(sha256_file(path) == raw_hash, 'CONTAINER_CHANGED_DURING_PROJECTION')
            receipt = seal({'schema':'label_blind_normal_projection_receipt_v2','dataset_version':args.version,
                'source_file_identity':row['symbolic_id'], 'official_source_identity':row,
                'raw_container_hash':raw_hash, 'contract_hash':contract['self_hash'],
                'source_commit':source_commit, 'reader_configuration':'BINARY_CSV_SPANS_SELECTED_ONLY_UTF8_FLOAT64',
                'projection_implementation_identity':contract['implementation_hashes']['src/paperworks/data/hai_normal_projection_v2.py'],
                'wall_seconds':time.perf_counter()-start, **result})
            publish(receipt_path, receipt)
        records.append(receipt)
        print(json.dumps({'phase':'PROJECTION_PASS','symbolic_id':row['symbolic_id'],
                         'rows':receipt['row_count'],'hash':receipt['projection_hash']}),flush=True)
    bundle = seal({'schema':'xver_label_blind_normal_custody_v2','version':args.version,
        'status':'NORMAL_ONLY_CUSTODY_READY','records':records,'contract_hash':contract['self_hash'],
        'test1_accesses':0,'test2_accesses':0,'attack_file_accesses':0,'label_values_parsed':False,
        'provider_calls':0,'private_exposures':0})
    publish(PUB/f'HAI{args.version[:2]}_NORMAL_PROJECTION_RECEIPT_V2.json',bundle)
    print(json.dumps({'version':args.version,'status':bundle['status'],'hash':bundle['self_hash']}),flush=True)


if __name__ == '__main__':
    try: main()
    except Exception as error:
        # Never print raw values, server response, traceback or private paths.
        issue = str(error) if isinstance(error,ValueError) and str(error).replace('_','').isalnum() else type(error).__name__
        print(json.dumps({'status':'BLOCKED_NORMAL_DATA_CUSTODY','issue':issue}),flush=True)
        raise SystemExit(2)
