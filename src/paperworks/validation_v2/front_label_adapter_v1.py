"""Exact timestamp/0-1 parsing, usable only inside opaque evaluation custody."""
from __future__ import annotations
import csv
from hashlib import sha256
import io
from typing import Callable

from .evaluation_custody_v1 import consume_evaluation_label_access_v1, validate_evaluation_label_capability_v1


def parse_labels_v1(payload:bytes,*,expected_hash:str,expected_size:int,timestamps:tuple[str,...]) -> tuple[int,...]:
    if len(payload)!=expected_size or sha256(payload).hexdigest()!=expected_hash:
        raise ValueError("LABEL_BYTE_IDENTITY_MISMATCH")
    reader=csv.reader(io.StringIO(payload.decode("utf-8-sig"),newline=""))
    if next(reader,None)!=["timestamp","label"]:
        raise ValueError("LABEL_HEADER_MISMATCH")
    values=[]
    for index,row in enumerate(reader):
        if index>=len(timestamps) or len(row)!=2 or row[0]!=timestamps[index] or row[1] not in ("0","1"):
            raise ValueError("LABEL_COORDINATE_OR_TOKEN_MISMATCH")
        values.append(int(row[1]))
    if len(values)!=len(timestamps):raise ValueError("LABEL_ROW_CENSUS_MISMATCH")
    return tuple(values)


def consume_exact_labels_v1(capability,*,reader:Callable[[],bytes],expected_hash:str,expected_size:int,
    timestamps:tuple[str,...],exact_method_ids:tuple[str,...],evaluation_policy_hash:str,
    metric_contract_hash:str,source_commit:str) -> tuple[int,...]:
    validate_evaluation_label_capability_v1(capability,exact_method_ids=exact_method_ids,
        evaluation_policy_hash=evaluation_policy_hash,metric_contract_hash=metric_contract_hash,source_commit=source_commit)
    return consume_evaluation_label_access_v1(capability,lambda:parse_labels_v1(reader(),expected_hash=expected_hash,
        expected_size=expected_size,timestamps=timestamps))
