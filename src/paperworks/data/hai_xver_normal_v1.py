"""External-version normal-only custody adapter. Historical HAI23 stays unchanged."""
from __future__ import annotations
from pathlib import Path
from hashlib import sha256, sha1
from paperworks.validation_v2.exp03b_contract_v1 import require
from paperworks.validation_v2.exp03b_custody_v1 import replay

PIN='2a814cebc9a66b06c9e5cd545e2d72e65d383737'
COUNTS={'22.04':6,'21.03':3}


def validate_contract(contract: dict) -> None:
    replay(contract)
    require(contract['pinned_commit']==PIN and contract['attack_access_allowed'] is False and
            contract['provider_calls_allowed'] is False and contract['label_columns_allowed'] is False,'XVER_AUTHORITY')
    expected={(version,f'train{i}') for version,count in COUNTS.items() for i in range(1,count+1)}
    require({(r['version'],r['split']) for r in contract['records']}==expected and len(contract['records'])==len(expected),'NORMAL_ALLOWLIST')
    for row in contract['records']:
        v,s=row['version'],row['split']; relative=f'hai-{v}/{s}.csv'
        require(row['materialized_relative_path']==relative and row['official_relative_path']==relative+('.gz' if v=='21.03' else ''),'NORMAL_PATH_IDENTITY')
        require(row['identity_type']==('PINNED_GIT_LFS_SHA256' if v=='22.04' else 'PINNED_GIT_GZIP_BLOB_DETERMINISTIC_DECOMPRESSION'),'IDENTITY_TYPE')


def validate_header(header: list[str], version: str) -> None:
    require(version in COUNTS,'VERSION')
    require(len(header)==len(set(header)) and all(header),'NORMAL_HEADER_DUPLICATE')
    require(not any('attack' in s.lower() or 'label' in s.lower() for s in header),'LABEL_COLUMN_REJECTED_BEFORE_ROWS')
    require(len(header)==1+(86 if version=='22.04' else 78),'NORMAL_POINT_COUNT')
    require(header[0].lower() in ('timestamp','time'),'NORMAL_TIMESTAMP_FIELD')


def sha256_file(path: Path) -> str:
    h=sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def git_blob_sha1_file(path: Path) -> str:
    h=sha1(b'blob '+str(path.stat().st_size).encode()+b'\0')
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
