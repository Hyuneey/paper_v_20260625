"""Bounded full-unit custody: exact original EXP05 documents in atomic JSONL."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path

from .exp05_custody_v1 import _full_unit_document, _replay_full_unit_document
from .gdn_sidecar_v1 import seal
from .private_vault_v1 import publish_private_bytes_v1, file_identity_v1


def publish_full_unit_batch_v2(*, units: tuple, artifact_path: Path, receipt_path: Path) -> dict:
    if not units or len(units)>256:
        raise ValueError("FULL_UNIT_BATCH_SIZE_INVALID")
    docs = tuple(_full_unit_document(unit) for unit in units)
    content = b"".join((json.dumps(doc,ensure_ascii=True,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode() for doc in docs)
    publish_private_bytes_v1(artifact_path,content)
    receipt = seal({"schema":"exp05_full_unit_batch_receipt_v2", "artifact_sha256":sha256(content).hexdigest(),
        "byte_count":len(content),"unit_count":len(units),"unit_hashes":[u.unit_hash for u in units],
        "opportunity_ids":[u.materialized_trace.opportunity_id for u in units],
        "file_fsync":True,"closed_reopened":True,"publication":"NO_OVERWRITE_LINK",
        "full_documents_preserved":True,"acceptance":"PROVISIONAL_UNTIL_FULL_CENSUS_FINALIZATION"})
    publish_private_bytes_v1(receipt_path,(json.dumps(receipt,sort_keys=True,separators=(",",":"))+"\n").encode())
    replay_full_unit_batch_v2(artifact_path=artifact_path,receipt_path=receipt_path,expected_receipt=receipt)
    return receipt


def replay_full_unit_batch_v2(*, artifact_path: Path, receipt_path: Path, expected_receipt: dict) -> tuple:
    from .gdn_sidecar_v1 import replay
    receipt = json.loads(receipt_path.read_text())
    replay(receipt)
    # Hash and parse the same bounded immutable byte buffer.
    payload=artifact_path.read_bytes()
    if receipt != expected_receipt or (sha256(payload).hexdigest(),len(payload))!=(receipt["artifact_sha256"],receipt["byte_count"]):
        raise ValueError("FULL_UNIT_BATCH_RECEIPT_MISMATCH")
    units = tuple(_replay_full_unit_document(json.loads(line)) for line in payload.decode("utf-8").splitlines())
    if (len(units)!=receipt["unit_count"] or [u.unit_hash for u in units]!=receipt["unit_hashes"]
        or [u.materialized_trace.opportunity_id for u in units]!=receipt["opportunity_ids"]):
        raise ValueError("FULL_UNIT_BATCH_CENSUS_MISMATCH")
    return units
