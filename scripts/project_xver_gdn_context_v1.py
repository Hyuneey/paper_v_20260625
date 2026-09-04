"""New append-only context projections; never deserialize excluded fields."""
from pathlib import Path
from hashlib import sha256
import json
import subprocess
from paperworks.data.hai_normal_projection_v2 import project
from paperworks.data.hai_xver_normal_v1 import sha256_file
from paperworks.validation_v2.exp03b_custody_v1 import seal, publish, replay
from paperworks.validation_v2.exp03b_contract_v1 import require, digest
from materialize_xver_normal_v1 import cache_root

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT/'research_control_center/validation_v2/xver_normal'
PARENT = ROOT/'research_control_center/validation_v2/dg04_xver_prep'


def main() -> None:
    path = PUBLIC/'GDN_CONTEXT_PROJECTION_CONTRACT_V1.json'
    contract = json.loads(path.read_text()); replay(contract)
    require(contract['splits']==['train1','train2'] and contract['provider_calls_allowed'] is False
            and contract['label_values_parsed'] is False and contract['label_values_validated'] is False
            and contract['label_values_used'] is False, 'CONTEXT_PROJECTION_SCOPE')
    head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    require(path.read_bytes() == subprocess.check_output(['git','show',head+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT),'UNCOMMITTED_CONTEXT_CONTRACT')
    for name,h in contract['implementation_hashes'].items():
        require(sha256((ROOT/name).read_bytes()).hexdigest()==h,'PROJECTION_IMPLEMENTATION')
        require((ROOT/name).read_bytes()==subprocess.check_output(['git','show',head+':'+name],cwd=ROOT),'UNCOMMITTED_IMPLEMENTATION')
    for item in contract['records']:
        v=item['version'][:2]
        mapping=json.loads((PUBLIC/f'HAI{v}_GDN_CONTEXT_MAPPING_V1.json').read_text());replay(mapping)
        require(mapping['self_hash']==item['context_hash'] and mapping['context_order']==item['features'],'MAPPING_CHANGED')
        custody=json.loads((PARENT/f'HAI{v}_NORMAL_PROJECTION_RECEIPT_V2.json').read_text());replay(custody)
        require(custody['self_hash']==item['parent_projection_hash'],'PARENT_CUSTODY_CHANGED')
        selected=[r for r in custody['records'] if r['official_source_identity']['split'] in contract['splits']]
        require(sorted(r['official_source_identity']['split'] for r in selected)==['train1','train2'],
                'EXACT_TWO_SPLIT_CUSTODY')
        results=[]
        for row in selected:
            official=row['official_source_identity']
            require(official['version']==item['version'] and row['dataset_version']==item['version'], 'VERSION_IDENTITY')
            source=cache_root()/official['materialized_relative_path']
            require(source.is_file() and not source.is_symlink() and sha256_file(source)==row['raw_container_hash'],'RAW_NORMAL_CUSTODY')
            target=cache_root()/'xver_normal_v1/context'/f"{row['source_file_identity']}.csv"
            receipt_path=target.with_suffix('.receipt.json')
            if receipt_path.exists():
                result=json.loads(receipt_path.read_text());replay(result)
                require(result['contract_hash']==contract['self_hash'] and sha256_file(target)==result['projection_hash'],'CONTEXT_CACHE')
            else:
                projected=project(source,target,tuple(item['features']),allowlist_hash=digest(item['features']))
                require(projected['row_count']==row['row_count'] and sha256_file(source)==row['raw_container_hash'],'PROJECTION_REPLAY')
                result=seal({'schema':'xver_context_projection_receipt_v1','source_commit':head,
                    'dataset_version':item['version'],'source_file_identity':row['source_file_identity'],
                    'raw_container_hash':row['raw_container_hash'],'contract_hash':contract['self_hash'],
                    'mapping_hash':mapping['self_hash'],**projected})
                publish(receipt_path,result)
            require(result['dataset_version']==item['version'] and result['source_file_identity']==row['source_file_identity']
                    and result['mapping_hash']==mapping['self_hash'] and result['row_count']==row['row_count']
                    and result['projected_feature_identities']==item['features']
                    and result['raw_container_hash']==row['raw_container_hash'],'CONTEXT_RECEIPT_IDENTITY')
            results.append(result)
        document=seal({'schema':'xver_context_projection_bundle_v1','version':item['version'],
                       'status':'LABEL_VALUE_BLIND_NORMAL_FEATURE_PROJECTION','records':results,
                       'label_values_parsed':False,'provider_calls':0,'scientific_GDN_runs':0})
        publish(PUBLIC/f'HAI{v}_GDN_CONTEXT_PROJECTION_RECEIPT_V1.json',document)
        print(json.dumps({'version':item['version'],'projected_files':len(results),'hash':document['self_hash']}),flush=True)


if __name__=='__main__':
    try: main()
    except Exception as error:
        print(json.dumps({'status':'BLOCKED_NORMAL_DATA_CUSTODY','error_type':type(error).__name__}))
        raise SystemExit(2)
