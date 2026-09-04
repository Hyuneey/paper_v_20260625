"""Single external-normal runner. No test, labels, credentials or provider."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import gzip
import json
import math
import os
import shutil
import subprocess
import urllib.parse
import urllib.request
import numpy as np
import pandas as pd
from paperworks.data.hai_xver_normal_v1 import validate_contract,validate_header,sha256_file,git_blob_sha1_file,PIN
from paperworks.data.hai_provenance_v1 import _read_header,audit_csv_structure
from paperworks.validation_v2.exp03b_contract_v1 import require,digest
from paperworks.validation_v2.exp03b_custody_v1 import seal,publish,replay
from remediate_hai_2305_distribution import _download_one_archive,_extract_exact_member,_opener

ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/'research_control_center/validation_v2/dg04_xver_prep'


def cache_root():
    base=Path(os.environ['LOCALAPPDATA']) if os.name=='nt' else Path.home()/'.cache'
    target=base/'paper_v_20260625'/'official_hai_external_normal'/PIN
    require(not target.is_symlink() and not target.resolve().is_relative_to(ROOT.resolve()),'EXTERNAL_PRIVATE_ROOT')
    return target


def acquire(root, row):
    version=row['version'];path=root/row['materialized_relative_path']
    path.parent.mkdir(parents=True,exist_ok=True)
    require(not path.is_symlink(),'SYMLINK')
    if path.exists():
        receipt=path.with_suffix('.custody.json')
        require(receipt.exists(),'UNRECEIPTED_EXISTING_NORMAL_FILE')
        old=json.loads(receipt.read_text());replay(old)
        require(sha256_file(path)==old['sha256'] and old['official_identity']==row,'EXISTING_IDENTITY')
        return path,old['sha256'],0
    if version=='22.04':
        archive=path.with_suffix('.archive')
        url='https://www.kaggle.com/api/v1/datasets/download/icsdataset/hai-security-dataset/'+urllib.parse.quote(row['materialized_relative_path'],safe='')+'?datasetVersionNumber=10'
        _download_one_archive(url=url,destination=archive,allowed_hosts=('www.kaggle.com','storage.googleapis.com'))
        # Only the exact requested normal member may be extracted by the unchanged historical primitive.
        extracted=_extract_exact_member(archive=archive,expected_relative_path=row['materialized_relative_path'],destination_root=root/'staging')
        require(extracted.stat().st_size==row['size_bytes'] and sha256_file(extracted)==row['sha256'],'NORMAL_BYTE_EQUIVALENCE')
        os.rename(extracted,path)
        size=archive.stat().st_size
    else:
        compressed=path.with_suffix('.csv.gz')
        request=urllib.request.Request(f'https://raw.githubusercontent.com/icsdataset/hai/{PIN}/'+row['official_relative_path'],headers={'User-Agent':'paperworks-xver-normal/1.0'})
        temporary=compressed.with_suffix('.gz.partial')
        with _opener(('raw.githubusercontent.com',)).open(request,timeout=300) as response, temporary.open('xb') as out:
            total=0
            while chunk:=response.read(1024*1024):
                total+=len(chunk);require(total<=row['git_blob_size'],'NORMAL_GZIP_SIZE_LIMIT');out.write(chunk)
            out.flush();os.fsync(out.fileno())
        require(temporary.stat().st_size==row['git_blob_size'] and git_blob_sha1_file(temporary)==row['git_blob_sha1'],'GIT_GZIP_BYTE_IDENTITY')
        os.rename(temporary,compressed)
        temporary=path.with_suffix('.csv.partial')
        with gzip.open(compressed,'rb') as source,temporary.open('xb') as out:
            total=0
            while chunk:=source.read(1024*1024):
                total+=len(chunk);require(total<=row['official_distribution_size'],'DECOMPRESSED_SIZE_LIMIT');out.write(chunk)
            out.flush();os.fsync(out.fileno())
        require(total==row['official_distribution_size'],'DECOMPRESSED_OFFICIAL_SIZE')
        os.rename(temporary,path);size=compressed.stat().st_size
    h=sha256_file(path)
    publish(path.with_suffix('.custody.json'),seal({'official_identity':row,'sha256':h,'content_bytes':path.stat().st_size,
        'payload_transport_bytes':size,'dataset':'HAI','version':version,'normal_only':True}))
    return path,h,size


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--version',choices=('22.04','21.03'),required=True);args=parser.parse_args()
    contract=json.loads((PUB/'XVER_NORMAL_MATERIALIZATION_CONTRACT_V1.json').read_text());validate_contract(contract)
    require((PUB/'STAGE_A_INDEPENDENT_QA_V1.md').is_file(),'STAGE_A_REQUIRED')
    root=cache_root();records=[];canonical=None
    for row in [r for r in contract['records'] if r['version']==args.version]:
        print(json.dumps({'phase':'NORMAL_ACQUISITION','split':row['symbolic_id']}),flush=True)
        path,h,networkbytes=acquire(root,row)
        _,header,delimiter=_read_header(path);validate_header(header,args.version)
        if canonical is None:canonical=header
        require(header==canonical,'VERSION_HEADER_ORDER')
        audit=audit_csv_structure(path,relative_path=row['materialized_relative_path'],expected_point_count=86 if args.version=='22.04' else 78,canonical_header=canonical,official_train_normal_description_verified=True).to_dict()
        require(audit['file_sha256']==h and audit['timestamps_strictly_increasing'] and audit['distinct_timestamp_delta_seconds']==[1.0] and
                audit['malformed_row_count']==0 and audit['inconsistent_field_count_rows']==0 and audit['normal_file_status']=='normal_only_verified','NORMAL_SCHEMA_SAMPLING')
        finite_rows=0
        for chunk in pd.read_csv(path,sep=delimiter,usecols=header[1:],dtype='float64',chunksize=20000):
            require(np.isfinite(chunk.to_numpy()).all(),'NONFINITE_NORMAL_FEATURE')
            finite_rows+=len(chunk)
        require(finite_rows==audit['row_count'],'FINITE_CENSUS')
        private=seal({'contract_hash':contract['self_hash'],'official_identity':row,'absolute_path':str(path.resolve()),'schema':header,'audit':audit,'finite_values':'PASS'})
        publish(path.with_suffix('.schema.json'),private)
        record={'symbolic_id':row['symbolic_id'],'version':args.version,'split':row['split'],'sha256':h,
            'bytes':path.stat().st_size,'row_count':audit['row_count'],'header_hash':audit['header_sha256'],
            'feature_order_hash':digest(header[1:]),'sample_interval_seconds':1,'timestamp_continuity':'PASS',
            'schema_status':'PASS','finite_values':'PASS','private_manifest_hash':private['self_hash'],'network_payload_bytes_this_run':networkbytes}
        records.append(record)
        print(json.dumps({'phase':'NORMAL_CUSTODY','split':row['symbolic_id'],'status':'PASS','rows':audit['row_count']}),flush=True)
    receipt=seal({'schema':'xver_normal_custody_receipt_v1','version':args.version,'status':'NORMAL_ONLY_CUSTODY_READY',
        'contract_hash':contract['self_hash'],'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'issued_at_utc':datetime.now(timezone.utc).isoformat(),'records':records,
        'test1':0,'test2':0,'external_attacks':0,'labels':0,'provider':0,'private_exposures':0})
    publish(PUB/f'HAI{args.version[:2]}_NORMAL_CUSTODY_RECEIPT_V1.json',receipt)
    print(json.dumps({'status':receipt['status'],'version':args.version,'self_hash':receipt['self_hash']}))


if __name__=='__main__':
    try:main()
    except Exception as e:
        code=str(e) if isinstance(e,ValueError) and str(e).replace('_','').isalnum() else type(e).__name__
        print(json.dumps({'status':'BLOCKED_NORMAL_DATA_CUSTODY','issue':code}),flush=True);raise SystemExit(2)
