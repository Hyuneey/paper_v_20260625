"""Freeze exact public official normal inventory. Never acquire CSV/gzip bytes."""
from pathlib import Path
from hashlib import sha1, sha256
import json
import urllib.request
import os
from paperworks.validation_v2.exp03b_custody_v1 import seal,publish,replay
from paperworks.validation_v2.exp03b_contract_v1 import require,digest
from remediate_hai_2305_distribution import _opener

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'research_control_center/validation_v2/dg04_xver_prep'
PIN='2a814cebc9a66b06c9e5cd545e2d72e65d383737'


def fetch(url, limit):
    request=urllib.request.Request(url,headers={'User-Agent':'paperworks-normal-only-metadata/1.0'})
    with _opener(('api.github.com','raw.githubusercontent.com')).open(request,timeout=45) as response:
        data=response.read(limit+1)
    require(len(data)<=limit,'METADATA_SIZE_LIMIT')
    return data


def main():
    tree=json.loads(fetch(f'https://api.github.com/repos/icsdataset/hai/git/trees/{PIN}?recursive=1',2_000_000))
    require(tree['sha']==PIN and not tree.get('truncated'),'OFFICIAL_TREE_IDENTITY')
    index={x['path']:x for x in tree['tree']}
    historical=json.loads((ROOT/'docs/task_reports/TASK-039AR_KAGGLE_METADATA_FREEZE.json').read_text())
    require(digest({k:v for k,v in historical.items() if k!='artifact_hash'})==historical['artifact_hash']=='a7389cc123a544302b896c4c1ffc931a3c61c22318c0fa53c575cd1567d5fbfe','FROZEN_METADATA')
    inventory={r['name']:r for r in historical['complete_file_inventory']}
    records=[]
    for version,count in (('22.04',6),('21.03',3)):
        for split in range(1,count+1):
            relative=f'hai-{version}/train{split}.csv';gitpath=relative+('.gz' if version=='21.03' else '')
            entry=index[gitpath];require(entry['type']=='blob','NORMAL_IDENTITY_TYPE')
            row={'version':version,'split':f'train{split}','symbolic_id':f'HAI{version[:2]}_TRAIN{split}',
                'official_relative_path':gitpath,'materialized_relative_path':relative,'git_blob_sha1':entry['sha'],
                'git_blob_size':entry['size'],'official_distribution_size':inventory[relative]['advertised_size_bytes']}
            if version=='22.04':
                pointer=fetch(f'https://raw.githubusercontent.com/icsdataset/hai/{PIN}/{gitpath}',1024)
                require(sha1(b'blob '+str(len(pointer)).encode()+b'\0'+pointer).hexdigest()==entry['sha'],'LFS_POINTER_GIT_IDENTITY')
                lines=pointer.decode('ascii').splitlines()
                require(lines[0]=='version https://git-lfs.github.com/spec/v1' and lines[1].startswith('oid sha256:'),'LFS_POINTER_SCHEMA')
                row.update(identity_type='PINNED_GIT_LFS_SHA256',sha256=lines[1][11:],size_bytes=int(lines[2][5:]),route='KAGGLE_SELECTIVE_VERSION_10')
                require(row['size_bytes']==row['official_distribution_size'],'KAGGLE_SIZE_MISMATCH')
            else:row.update(identity_type='PINNED_GIT_GZIP_BLOB_DETERMINISTIC_DECOMPRESSION',route='PINNED_OFFICIAL_GIT_RAW_NORMAL_GZIP')
            records.append(row)
    manual=index['hai_dataset_technical_details.pdf']
    require(manual['sha']=='18cb88514176e1c641f584cf24ac8e9559432b38','MANUAL_GIT_IDENTITY')
    doc=seal({'schema':'xver_normal_materialization_contract_v1','official_repository':'https://github.com/icsdataset/hai',
        'pinned_commit':PIN,'metadata_receipt_hash':historical['artifact_hash'],'records':records,
        'manual_git_blob_sha1':manual['sha'],'manual_table_pdf_pages':[13,14],
        'provider_calls_allowed':False,'attack_access_allowed':False,'label_columns_allowed':False,
        'normal_schema_policy':'EXACT_VERSION_POINT_COUNT_NO_LABEL_COLUMNS_STRICT_ONE_SECOND_FINITE_NUMERIC',
        'payload_acquired':False,'HAI21_route_rationale':'Official Git stores gzip bytes, not LFS; pinned Git blob plus decompression preserves source authority. HAI23 legacy code unchanged.',
        'implementation_hash':sha256(Path(__file__).read_bytes()).hexdigest()})
    publish(DEST/'XVER_NORMAL_MATERIALIZATION_CONTRACT_V1.json',doc)
    # Official manual only; restricted page extraction is performed separately.
    cache=ROOT/'tmp/dg04_xver_public_manual';cache.mkdir(parents=True,exist_ok=True)
    path=cache/'hai_dataset_technical_details.pdf'
    if not path.exists():
        raw=fetch(f'https://raw.githubusercontent.com/icsdataset/hai/{PIN}/hai_dataset_technical_details.pdf',30_000_000)
        require(sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==manual['sha'],'MANUAL_BYTES')
        with path.open('xb') as out:out.write(raw);out.flush();os.fsync(out.fileno())
    print(json.dumps({'status':'NORMAL_METADATA_FROZEN','normal_files':len(records),'self_hash':doc['self_hash'],'scientific_payloads_acquired':0}))


if __name__=='__main__':
    try:main()
    except Exception as e:print(json.dumps({'status':'BLOCKED_NORMAL_DATA_CUSTODY','error_type':type(e).__name__}));raise SystemExit(2)
