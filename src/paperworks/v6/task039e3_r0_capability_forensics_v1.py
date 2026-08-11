"""Independent offline forensics for the TASK-039E3 capability block.

This module deliberately has no provider transport, credential, E1 evidence, or
HAI dependency.  It validates preserved custody and Git objects supplied by an
offline audit caller.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
from types import MappingProxyType
from typing import Any, Mapping, Sequence


EXACT_MODEL = "gpt-5.4-2026-03-05"
EXPECTED_REQUEST_HASH = (
    "fc35aa1ce3f68eb8635a634bf47050f0ba4cda7caf2caa4e13a947845cdd3138"
)
EXPECTED_CAPABILITY_RECEIPT_HASH = (
    "e36098690f2c4c018b8ed5f339d46870fbbe0561f52c117cd2525a63d155c279"
)
EXPECTED_PROVIDER_LEDGER_HASH = (
    "656d81ded2f166175adf2717abc226c325cd4a9fcbcee5306f4ea35c7465d254"
)
EXPECTED_PRIVATE_FILES = (
    "construction_outcomes.jsonl",
    "direct_number.jsonl",
    "proposals_validity.jsonl",
    "provider_calls.jsonl",
)
PROHIBITED_PUBLIC_MARKERS = (
    "authorization: bearer",
    "bearer ",
    "openai_api_key",
    "raw_prompt",
    "calibrated_numeric_evidence",
    "individual_proposal",
    "private_relation_payload",
    "chain_of_thought",
)


class TASK039E3R0ForensicError(ValueError):
    """Raised when offline forensic evidence violates its frozen contract."""


def canonical_json_v1(value: Any) -> str:
    """Return canonical JSON without accepting non-finite values."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def stable_hash_v1(value: Any) -> str:
    """Hash canonical JSON with SHA-256."""

    return sha256(canonical_json_v1(value).encode("utf-8")).hexdigest()


def with_self_hash_v1(content: Mapping[str, Any]) -> dict[str, Any]:
    """Copy a public artifact and attach its deterministic self-hash."""

    document = dict(content)
    document["artifact_hash"] = stable_hash_v1(document)
    return document


def verify_self_hash_v1(document: Mapping[str, Any], expected: str | None = None) -> str:
    """Verify an artifact hash without importing production E3 code."""

    observed = document.get("artifact_hash")
    if not isinstance(observed, str):
        raise TASK039E3R0ForensicError("artifact hash is missing")
    content = {key: value for key, value in document.items() if key != "artifact_hash"}
    if stable_hash_v1(content) != observed:
        raise TASK039E3R0ForensicError("artifact self-hash differs")
    if expected is not None and observed != expected:
        raise TASK039E3R0ForensicError("artifact binding differs")
    return observed


def read_json_object_v1(path: Path) -> dict[str, Any]:
    """Read one ordinary JSON object from an explicitly supplied path."""

    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise TASK039E3R0ForensicError(f"JSON object required: {path.name}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise TASK039E3R0ForensicError(
                    f"JSON object required at {path.name}:{line_number}"
                )
            records.append(value)
    return records


def audit_private_custody_v1(private_root: Path) -> dict[str, Any]:
    """Audit the historical E3 provider custody without mutating it."""

    root = private_root.resolve(strict=True)
    if root.is_symlink() or not root.is_dir():
        raise TASK039E3R0ForensicError("historical private root is not a real directory")
    names = tuple(sorted(item.name for item in root.iterdir() if item.is_file()))
    if names != EXPECTED_PRIVATE_FILES:
        raise TASK039E3R0ForensicError("historical private file inventory differs")
    for name in EXPECTED_PRIVATE_FILES[:-1]:
        if (root / name).stat().st_size != 0:
            raise TASK039E3R0ForensicError(f"unexpected scientific custody: {name}")

    records = _read_jsonl(root / "provider_calls.jsonl")
    if len(records) != 1:
        raise TASK039E3R0ForensicError("logical capability slot count differs")
    previous: str | None = None
    slot_hashes: set[str] = set()
    for sequence, record in enumerate(records):
        if record.get("sequence_index") != sequence:
            raise TASK039E3R0ForensicError("provider sequence differs")
        if record.get("previous_record_hash") != previous:
            raise TASK039E3R0ForensicError("provider hash chain differs")
        slot = record.get("slot")
        if not isinstance(slot, dict) or stable_hash_v1(slot) != record.get("slot_hash"):
            raise TASK039E3R0ForensicError("provider slot hash differs")
        if record["slot_hash"] in slot_hashes:
            raise TASK039E3R0ForensicError("duplicate provider slot")
        slot_hashes.add(record["slot_hash"])
        content = {key: value for key, value in record.items() if key != "record_hash"}
        if stable_hash_v1(content) != record.get("record_hash"):
            raise TASK039E3R0ForensicError("provider record hash differs")
        previous = record["record_hash"]
    ledger_hash = stable_hash_v1(
        {
            "artifact_type": "provider_call_ledger_v1",
            "record_hashes": [record["record_hash"] for record in records],
        }
    )
    if ledger_hash != EXPECTED_PROVIDER_LEDGER_HASH:
        raise TASK039E3R0ForensicError("provider ledger head differs")

    record = records[0]
    slot = record["slot"]
    metadata = record.get("provider_response_metadata")
    attempts = record.get("transport_attempts")
    if not isinstance(metadata, dict) or not isinstance(attempts, list):
        raise TASK039E3R0ForensicError("provider custody structure differs")
    if record.get("request_hash") != EXPECTED_REQUEST_HASH:
        raise TASK039E3R0ForensicError("capability request hash differs")
    if slot.get("arm") != "CAPABILITY" or slot.get("scientific") is not False:
        raise TASK039E3R0ForensicError("historical slot is not capability-only")
    if len(attempts) != 1 or attempts[0].get("attempt_number") != 1:
        raise TASK039E3R0ForensicError("historical transport attempts differ")
    if metadata.get("model") != EXACT_MODEL:
        raise TASK039E3R0ForensicError("historical returned model differs")
    if record.get("parse_status") != "block_snapshot":
        raise TASK039E3R0ForensicError("historical parse status differs")
    if record.get("response_present") is not True:
        raise TASK039E3R0ForensicError("historical response-presence differs")
    if any(
        record.get(name) is not False
        for name in ("api_key_stored", "authorization_header_stored", "chain_of_thought_stored")
    ):
        raise TASK039E3R0ForensicError("prohibited provider custody field is present")
    sanitized_for_scan = {
        key: value
        for key, value in record.items()
        if key
        not in {"api_key_stored", "authorization_header_stored", "chain_of_thought_stored"}
    }
    serialized = canonical_json_v1(sanitized_for_scan).lower()
    if any(marker in serialized for marker in PROHIBITED_PUBLIC_MARKERS):
        raise TASK039E3R0ForensicError("prohibited material found in provider custody")

    return {
        "record": record,
        "provider_ledger_hash": ledger_hash,
        "provider_record_hash": record["record_hash"],
        "logical_capability_slots": 1,
        "logical_scientific_slots": 0,
        "transport_attempts": 1,
        "transport_retries": 0,
        "empty_scientific_ledgers": True,
    }


def frozen_checker_outcome_v1(
    model_snapshot: str, structured_output_supported: bool
) -> str:
    """Reproduce the exact historical checker decision table offline."""

    if model_snapshot != EXACT_MODEL or not structured_output_supported:
        return "block_snapshot"
    return "pass"


def classify_historical_checker_subcondition_v1(record: Mapping[str, Any]) -> str:
    """Classify the old self-report failure only when parsed fields were retained."""

    payload = record.get("parsed_capability_payload")
    if not isinstance(payload, Mapping):
        return "unable_to_determine"
    snapshot = payload.get("model_snapshot")
    structured = payload.get("structured_output_supported")
    if not isinstance(snapshot, str) or type(structured) is not bool:
        return "unable_to_determine"
    snapshot_failed = snapshot != EXACT_MODEL
    structured_failed = not structured
    if snapshot_failed and structured_failed:
        return "both_synthetic_self_report_conditions_failed"
    if snapshot_failed:
        return "synthetic_snapshot_self_report_mismatch"
    if structured_failed:
        return "synthetic_structured_support_self_report_false"
    return "different_checker_path"


def reconcile_public_capability_v1(
    record: Mapping[str, Any], public_document: Mapping[str, Any]
) -> dict[str, Any]:
    """Compare every reconstructible public field with private custody."""

    verify_self_hash_v1(public_document, EXPECTED_CAPABILITY_RECEIPT_HASH)
    metadata = record["provider_response_metadata"]
    expected = {
        "status": "blocked_task039e3_capability_gate",
        "execution_code_commit": "48b79643088ce1a0179191d7ddae4c97dc8dece9",
        "exact_model": EXACT_MODEL,
        "response_id": metadata.get("response_id"),
        "returned_model": metadata.get("model"),
        "finish_reason": metadata.get("finish_reason"),
        "structured_parse_status": record.get("parse_status"),
        "transport_attempts": len(record.get("transport_attempts", [])),
        "usage": metadata.get("token_usage"),
        "passed": False,
        "scientific_calls": 0,
        "configuration_modified_after_probe": False,
    }
    differences = {
        key: {"expected": value, "observed": public_document.get(key)}
        for key, value in expected.items()
        if public_document.get(key) != value
    }
    return {
        "reconstructible_fields_match": not differences,
        "field_differences": differences,
        "system_fingerprint_reconstructible_from_provider_ledger": False,
        "system_fingerprint_public_value": public_document.get("system_fingerprint"),
        "exact_full_reconciliation_established": False,
        "exact_full_reconciliation_blocker": (
            "system fingerprint and parsed self-report fields were not retained in private custody"
        ),
    }


def reproduce_shallow_serialization_defect_v1() -> dict[str, Any]:
    """Reproduce the nested immutable-mapping failure without production I/O."""

    nested = MappingProxyType({"total_tokens": 101})
    shallow = dict({"usage": nested})
    try:
        json.dumps(shallow, sort_keys=True)
    except TypeError as exc:
        return {
            "reproduced": True,
            "exception_class": type(exc).__name__,
            "sanitized_message": str(exc),
            "triggering_logical_type": type(nested).__name__,
        }
    raise TASK039E3R0ForensicError("serialization defect did not reproduce")


def git_blob_manifest_v1(
    repository_root: Path, commit: str, paths: Sequence[str]
) -> dict[str, Any]:
    """Hash exact Git blob bytes, avoiding worktree line-ending conversion."""

    entries: dict[str, str] = {}
    for path in paths:
        completed = subprocess.run(
            ["git", "-C", str(repository_root), "show", f"{commit}:{path}"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        entries[path] = sha256(completed.stdout).hexdigest()
    return {
        "commit": commit,
        "entries": entries,
        "manifest_hash": stable_hash_v1({"commit": commit, "entries": entries}),
    }


def scan_public_text_v1(text: str) -> tuple[str, ...]:
    """Return prohibited marker hits in sanitized public text."""

    lowered = text.lower()
    return tuple(marker for marker in PROHIBITED_PUBLIC_MARKERS if marker in lowered)


__all__ = [
    "EXACT_MODEL",
    "EXPECTED_CAPABILITY_RECEIPT_HASH",
    "EXPECTED_PROVIDER_LEDGER_HASH",
    "TASK039E3R0ForensicError",
    "audit_private_custody_v1",
    "classify_historical_checker_subcondition_v1",
    "frozen_checker_outcome_v1",
    "git_blob_manifest_v1",
    "read_json_object_v1",
    "reconcile_public_capability_v1",
    "reproduce_shallow_serialization_defect_v1",
    "scan_public_text_v1",
    "stable_hash_v1",
    "verify_self_hash_v1",
    "with_self_hash_v1",
]
