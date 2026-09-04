"""Normal-projection-only custody utilities, with no network/provider imports."""
import csv
import json
import os
import subprocess
from pathlib import Path
import numpy as np
from paperworks.data.hai_xver_normal_v1 import PIN, sha256_file
from paperworks.validation_v2.exp03b_contract_v1 import require, digest
from paperworks.validation_v2.exp03b_custody_v1 import publish, replay, seal

ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/'research_control_center/validation_v2/xver_normal'
PARENT=ROOT/'research_control_center/validation_v2/dg04_xver_prep'


def cache_root():
    require(os.name=='nt','APPROVED_WINDOWS_CUSTODY')
    path=Path(os.environ['LOCALAPPDATA'])/'paper_v_20260625/official_hai_external_normal'/PIN
    require(path.is_dir() and not path.is_symlink() and not path.resolve().is_relative_to(ROOT.resolve()),'EXTERNAL_PRIVATE_ROOT')
    return path


def private_root():return cache_root()/'xver_execution_v1'


def document(path):
    value=json.loads(path.read_text(encoding='utf-8'));replay(value);return value


def version_authorities(version):
    require(version in ('22.04','21.03'),'VERSION_SCOPE')
    v=version[:2]
    context=document(PUB/f'HAI{v}_GDN_CONTEXT_MAPPING_V1.json')
    candidate=document(PARENT/f'HAI{v}_META_STAT_CANDIDATE_AUTHORITY_V2.json')
    roles=document(PARENT/f'HAI{v}_CANDIDATE_CONTRACT_V2.json')
    require(context['version']==candidate['version']==roles['version']==version,'VERSION_AUTHORITY')
    pairs=tuple((r['source'],r['target']) for r in candidate['pairs'])
    require(pairs==tuple(sorted(set(pairs))) and set(pairs)<=set(map(tuple,roles['pairs'])),'CANDIDATE_IDENTITIES')
    return context,candidate,roles,pairs


def load_projection(version,split,*,context=False):
    require(version in ('22.04','21.03'),'VERSION_SCOPE')
    allowed=('train1','train2') if context else (tuple('train'+str(n) for n in range(1,7)) if version=='22.04' else ('train1','train2','train3'))
    require(split in allowed,'PROJECTION_SPLIT_SCOPE')
    bundle=document((PUB if context else PARENT)/f"HAI{version[:2]}_{'GDN_CONTEXT_PROJECTION_RECEIPT_V1' if context else 'NORMAL_PROJECTION_RECEIPT_V2'}.json")
    symbolic=f'HAI{version[:2]}_{split.upper()}'
    row=next(r for r in bundle['records'] if r['source_file_identity']==symbolic);replay(row)
    require(row['dataset_version']==version and row['label_values_parsed'] is False
            and row['label_values_validated'] is False and row['label_values_used'] is False,'LABEL_VALUE_BLIND')
    order=tuple(row['projected_feature_identities'])
    path=cache_root()/('xver_normal_v1/context' if context else 'projections_v2')/(symbolic+'.csv')
    require(not path.is_symlink() and sha256_file(path)==row['projection_hash'],'PROJECTION_HASH')
    with path.open(encoding='utf-8',newline='') as stream:header=next(csv.reader(stream))
    require(tuple(header)==(row['timestamp_identity'],)+order,'POSITIVE_PROJECTION_HEADER')
    require(len(order)==len(set(order)) and all(x.startswith('P1_') for x in order),'FEATURE_ALLOWLIST')
    # Only the already sealed, label-free projection is deserialized; no raw container path exists here.
    matrix=np.loadtxt(path,delimiter=',',skiprows=1,usecols=tuple(range(1,len(order)+1)),dtype=np.float64,ndmin=2)
    require(matrix.shape==(row['row_count'],len(order)) and np.isfinite(matrix).all(),'PROJECTION_FINITE_SHAPE')
    require(sha256_file(path)==row['projection_hash'],'PROJECTION_UNCHANGED')
    return matrix,order,row


def head():return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()


def committed(path):
    require(path.read_bytes()==subprocess.check_output(['git','show',head()+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT),'UNCOMMITTED_EXECUTION_AUTHORITY')
