"""Capability-scoped DG-05 label/scenario custodian.

This module intentionally imports no prediction, detector, Rule, metric, or
result module.  It is designed to run in a fresh process with a minimal JSON
request and explicit filesystem roots.  The lease is consumed before the
approved source is opened, including on reader failure.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import secrets
from typing import Any, Mapping, Sequence


class CustodianIsolationError(ValueError):
    pass


REQUEST_FIELDS = frozenset({
    "schema", "opaque_lease", "lease_receipt", "global_freeze_hash",
    "executable_manifest_hash", "approved_input", "approved_output", "public_authority_hashes",
    "consumed_receipt", "resource_policy", "allowed_scenario_bindings",
    "approved_source_byte_hash", "authority_mode", "nominal_counts",
})
FORBIDDEN_TOKENS = frozenset({"prediction", "alarm", "method", "result", "score", "portfolio", "model"})


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _sha(value: str) -> None:
    if type(value) is not str or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise CustodianIsolationError("SHA256_REQUIRED")


def _inside(path: Path, root: Path) -> bool:
    path, root = path.resolve(), root.resolve()
    return path != root and root in path.parents


def _mapping_keys(value: Any):
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key)
            yield from _mapping_keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _mapping_keys(item)


def validate_request_v1(request: Mapping[str, Any], *, input_root: Path, output_root: Path,
                        forbidden_roots: Sequence[Path]) -> None:
    if set(request) != REQUEST_FIELDS or request.get("schema") != "isolated_label_scenario_custodian_request_v1":
        raise CustodianIsolationError("MINIMAL_CUSTODIAN_SCHEMA_REQUIRED")
    if any(any(token in key.lower() for token in FORBIDDEN_TOKENS) for key in _mapping_keys(request)):
        raise CustodianIsolationError("PREDICTION_CAPABILITY_PROHIBITED")
    receipt = request.get("lease_receipt")
    if type(receipt) is not dict or receipt.get("self_hash") != sha256(_canonical({k: v for k, v in receipt.items() if k != "self_hash"})).hexdigest():
        raise CustodianIsolationError("VALID_LEASE_RECEIPT_REQUIRED")
    if sha256(request["opaque_lease"].encode("utf-8")).hexdigest() != receipt.get("token_hash"):
        raise CustodianIsolationError("LEASE_TOKEN_BINDING_MISMATCH")
    for field in ("global_freeze_hash", "executable_manifest_hash"):
        _sha(request[field])
    _sha(request["approved_source_byte_hash"])
    if request["authority_mode"] not in ("PRODUCTION", "SYNTHETIC_REHEARSAL"):
        raise CustodianIsolationError("CUSTODIAN_AUTHORITY_MODE_REQUIRED")
    if type(request["nominal_counts"]) is not dict or any(type(v) is not int or v < 0 for v in request["nominal_counts"].values()):
        raise CustodianIsolationError("NOMINAL_SCENARIO_COUNTS_REQUIRED")
    if receipt.get("global_freeze_hash") != request["global_freeze_hash"] or receipt.get("executable_manifest_hash") != request["executable_manifest_hash"]:
        raise CustodianIsolationError("LEASE_AUTHORITY_BINDING_MISMATCH")
    if type(request["public_authority_hashes"]) is not list or not request["public_authority_hashes"]:
        raise CustodianIsolationError("PUBLIC_AUTHORITIES_REQUIRED")
    for value in request["public_authority_hashes"]:
        _sha(value)
    policy = request.get("resource_policy")
    if type(policy) is not dict or policy.get("self_hash") != sha256(_canonical({k: v for k, v in policy.items() if k != "self_hash"})).hexdigest():
        raise CustodianIsolationError("MANIFEST_BOUND_RESOURCE_POLICY_REQUIRED")
    if Path(policy.get("input_root", "")).resolve() != input_root.resolve() or Path(policy.get("output_root", "")).resolve() != output_root.resolve() or tuple(Path(v).resolve() for v in policy.get("forbidden_roots", [])) != tuple(Path(v).resolve() for v in forbidden_roots):
        raise CustodianIsolationError("RESOURCE_POLICY_RUNTIME_MISMATCH")
    bindings = request.get("allowed_scenario_bindings")
    if type(bindings) is not list or not bindings:
        raise CustodianIsolationError("SCENARIO_BINDINGS_REQUIRED")
    required_binding = {"panel_id", "dataset_version", "file_id", "physical_file_authority_hash", "timestamp_authority_hash", "official_source_hash"}
    for binding in bindings:
        if type(binding) is not dict or set(binding) != required_binding:
            raise CustodianIsolationError("SCENARIO_BINDING_SCHEMA_REQUIRED")
        for field in ("physical_file_authority_hash", "timestamp_authority_hash", "official_source_hash"):
            _sha(binding[field])
    paths = [Path(request[name]).resolve() for name in ("approved_input", "approved_output", "consumed_receipt")]
    if not _inside(paths[0], input_root) or not _inside(paths[1], output_root) or not _inside(paths[2], output_root):
        raise CustodianIsolationError("RESOURCE_ALLOWLIST_VIOLATION")
    for path in paths:
        if any(path == root.resolve() or root.resolve() in path.parents for root in forbidden_roots):
            raise CustodianIsolationError("FORBIDDEN_NAMESPACE_ACCESS")


def _exclusive_write(path: Path, payload: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    except FileExistsError as exc:
        raise CustodianIsolationError("SINGLE_CONSUME_OR_APPEND_ONLY_CONFLICT") from exc
    finally:
        if temporary.exists():
            temporary.unlink()
    return sha256(payload).hexdigest()


def consume_and_extract_v1(request: Mapping[str, Any], *, input_root: Path, output_root: Path,
                           forbidden_roots: Sequence[Path]) -> dict[str, Any]:
    validate_request_v1(request, input_root=input_root, output_root=output_root, forbidden_roots=forbidden_roots)
    consumed_body = {
        "schema": "label_scenario_lease_consumed_v1",
        "issue_receipt_hash": request["lease_receipt"]["self_hash"],
        "global_freeze_hash": request["global_freeze_hash"],
        "executable_manifest_hash": request["executable_manifest_hash"],
        "token_hash": sha256(request["opaque_lease"].encode("utf-8")).hexdigest(),
        "consume_count": 1,
    }
    consumed = {**consumed_body, "self_hash": sha256(_canonical(consumed_body)).hexdigest()}
    _exclusive_write(Path(request["consumed_receipt"]), _canonical(consumed) + b"\n")
    # Reader failure occurs after durable consume, so the lease cannot be reused.
    source_path = Path(request["approved_input"])
    source_bytes = source_path.read_bytes()
    if sha256(source_bytes).hexdigest() != request["approved_source_byte_hash"]:
        raise CustodianIsolationError("LEASED_SOURCE_BYTE_HASH_MISMATCH")
    source = json.loads(source_bytes.decode("utf-8"))
    if type(source) is not dict or set(source) != {"schema", "records"} or source["schema"] != "approved_official_scenario_source_v1":
        raise CustodianIsolationError("APPROVED_SCENARIO_SOURCE_SCHEMA_REQUIRED")
    allowed = {(b["panel_id"], b["dataset_version"], b["file_id"]): b for b in request["allowed_scenario_bindings"]}
    required_record = {"panel_id", "dataset_version", "file_id", "scenario_id", "closed_intervals", "attacked_identities", "explicit_affected_processes"}
    bound_records = []
    for record in source["records"]:
        if type(record) is not dict or set(record) != required_record:
            raise CustodianIsolationError("OFFICIAL_SCENARIO_RECORD_SCHEMA_REQUIRED")
        binding = allowed.get((record["panel_id"], record["dataset_version"], record["file_id"]))
        if binding is None or binding["official_source_hash"] != request["approved_source_byte_hash"]:
            raise CustodianIsolationError("OFFICIAL_SCENARIO_FILE_BINDING_MISMATCH")
        if not record["scenario_id"] or not record["closed_intervals"] or not record["attacked_identities"]:
            raise CustodianIsolationError("OFFICIAL_SCENARIO_CONTENT_REQUIRED")
        for interval in record["closed_intervals"]:
            if type(interval) is not list or len(interval) != 2:
                raise CustodianIsolationError("CLOSED_INTERVAL_REQUIRED")
        bound_records.append({**record, "physical_file_authority_hash": binding["physical_file_authority_hash"],
                              "timestamp_authority_hash": binding["timestamp_authority_hash"],
                              "official_source_hash": binding["official_source_hash"]})
    actual = {panel: sum(record["panel_id"] == panel for record in bound_records) for panel in request["nominal_counts"]}
    if actual != request["nominal_counts"]:
        raise CustodianIsolationError("LEASED_SCENARIO_CENSUS_MISMATCH")
    if request["authority_mode"] == "PRODUCTION" and sorted(request["nominal_counts"].values()) != [38, 50, 58]:
        raise CustodianIsolationError("FROZEN_PRODUCTION_SCENARIO_COUNTS_REQUIRED")
    output_body = {
        "schema": "isolated_label_scenario_custodian_output_v1",
        "lease_consumed_hash": consumed["self_hash"],
        "global_freeze_hash": request["global_freeze_hash"],
        "records": bound_records,
        "approved_source_byte_hash": request["approved_source_byte_hash"],
        "nominal_counts": request["nominal_counts"],
        "allowed_scenario_binding_hash": sha256(_canonical(request["allowed_scenario_bindings"])).hexdigest(),
        "prediction_capability": False,
    }
    output = {**output_body, "self_hash": sha256(_canonical(output_body)).hexdigest()}
    output_hash = _exclusive_write(Path(request["approved_output"]), _canonical(output) + b"\n")
    return {"consume_receipt_hash": consumed["self_hash"], "output_self_hash": output["self_hash"], "output_byte_hash": output_hash}


__all__ = ["CustodianIsolationError", "REQUEST_FIELDS", "FORBIDDEN_TOKENS", "validate_request_v1", "consume_and_extract_v1"]
