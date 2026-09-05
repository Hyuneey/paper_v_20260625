"""Fresh-process, manifest-bound DG-05 label/scenario custodian.

The request cannot authorize its own filesystem roots.  A separately persisted
private resource policy is reopened first, the lease is durably consumed, and
only then does a closed source adapter open the approved raw source.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import secrets
from typing import Any, Mapping


class CustodianIsolationError(ValueError):
    pass


REQUEST_FIELDS = frozenset({
    "schema", "opaque_lease", "lease_receipt", "global_freeze_hash",
    "executable_manifest_hash", "approved_source_id", "approved_output_name",
    "public_authority_hashes", "consumed_receipt_name", "resource_policy_hash",
    "allowed_scenario_bindings", "authority_mode", "nominal_counts",
})
FORBIDDEN_TOKENS = frozenset({"prediction", "alarm", "method", "result", "score", "portfolio", "model", "provider"})
PANEL_VERSION = {
    "HAI23_TEST2_PRIMARY_HELDOUT_V1": "23.05",
    "HAI22_EXTERNAL_REPLICATION_V1": "22.04",
    "HAI21_EXTERNAL_REPLICATION_V1": "21.03",
}
POLICY_FIELDS = frozenset({
    "schema", "input_root", "output_root", "forbidden_roots", "approved_sources",
    "executable_manifest_hash", "scenario_adapter_implementation_hash",
    "resource_policy_contract_hash", "source_commit", "self_hash",
})


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _sha(value: str) -> None:
    if type(value) is not str or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise CustodianIsolationError("SHA256_REQUIRED")


def _mapping_keys(value: Any):
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key)
            yield from _mapping_keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _mapping_keys(item)


def _load_policy(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8"))
    body = {k: v for k, v in value.items() if k != "self_hash"}
    if set(value) != POLICY_FIELDS or value.get("schema") != "custodian_resource_policy_authority_v1" or value.get("self_hash") != sha256(_canonical(body)).hexdigest():
        raise CustodianIsolationError("VALID_PRIVATE_RESOURCE_POLICY_REQUIRED")
    if raw != _canonical(value) + b"\n":
        raise CustodianIsolationError("RESOURCE_POLICY_CANONICAL_BYTES_REQUIRED")
    if type(value.get("approved_sources")) is not list or not value["approved_sources"]:
        raise CustodianIsolationError("APPROVED_SOURCE_REGISTRY_REQUIRED")
    for field in ("executable_manifest_hash", "scenario_adapter_implementation_hash", "resource_policy_contract_hash"):
        _sha(value[field])
    if type(value.get("source_commit")) is not str or len(value["source_commit"]) != 40:
        raise CustodianIsolationError("RESOURCE_POLICY_SOURCE_COMMIT_REQUIRED")
    input_root, output_root = Path(value["input_root"]).resolve(), Path(value["output_root"]).resolve()
    forbidden = tuple(Path(item).resolve() for item in value["forbidden_roots"])
    if input_root == output_root or any(root in input_root.parents or root in output_root.parents or root in (input_root, output_root) for root in forbidden):
        raise CustodianIsolationError("RESOURCE_POLICY_NAMESPACE_OVERLAP")
    for source in value["approved_sources"]:
        source_path = Path(source.get("path", "")).resolve()
        if input_root not in source_path.parents or any(root == source_path or root in source_path.parents for root in forbidden):
            raise CustodianIsolationError("APPROVED_SOURCE_OUTSIDE_RESOURCE_POLICY")
    return value


def validate_request_v1(request: Mapping[str, Any], *, resource_policy: Mapping[str, Any]) -> dict[str, Any]:
    if set(request) != REQUEST_FIELDS or request.get("schema") != "isolated_label_scenario_custodian_request_v1":
        raise CustodianIsolationError("MINIMAL_CUSTODIAN_SCHEMA_REQUIRED")
    if any(any(token in key.lower() for token in FORBIDDEN_TOKENS) for key in _mapping_keys(request)):
        raise CustodianIsolationError("PREDICTION_CAPABILITY_PROHIBITED")
    policy_body = {k: v for k, v in resource_policy.items() if k != "self_hash"}
    if set(resource_policy) != POLICY_FIELDS or resource_policy.get("schema") != "custodian_resource_policy_authority_v1" or resource_policy.get("self_hash") != sha256(_canonical(policy_body)).hexdigest():
        raise CustodianIsolationError("VALID_PRIVATE_RESOURCE_POLICY_REQUIRED")
    if request["resource_policy_hash"] != resource_policy["self_hash"]:
        raise CustodianIsolationError("RESOURCE_POLICY_HASH_MISMATCH")
    if request["executable_manifest_hash"] != resource_policy.get("executable_manifest_hash"):
        raise CustodianIsolationError("RESOURCE_POLICY_MANIFEST_MISMATCH")
    receipt = request.get("lease_receipt")
    if type(receipt) is not dict or receipt.get("self_hash") != sha256(_canonical({k: v for k, v in receipt.items() if k != "self_hash"})).hexdigest():
        raise CustodianIsolationError("VALID_LEASE_RECEIPT_REQUIRED")
    if sha256(request["opaque_lease"].encode("utf-8")).hexdigest() != receipt.get("token_hash"):
        raise CustodianIsolationError("LEASE_TOKEN_BINDING_MISMATCH")
    for field in ("global_freeze_hash", "executable_manifest_hash", "resource_policy_hash"):
        _sha(request[field])
    if receipt.get("global_freeze_hash") != request["global_freeze_hash"] or receipt.get("executable_manifest_hash") != request["executable_manifest_hash"] or receipt.get("resource_policy_hash") != request["resource_policy_hash"]:
        raise CustodianIsolationError("LEASE_AUTHORITY_BINDING_MISMATCH")
    if request["authority_mode"] not in ("PRODUCTION", "SYNTHETIC_REHEARSAL"):
        raise CustodianIsolationError("CUSTODIAN_AUTHORITY_MODE_REQUIRED")
    sources = [row for row in resource_policy["approved_sources"] if row.get("source_id") == request["approved_source_id"]]
    if len(sources) != 1:
        raise CustodianIsolationError("EXACT_APPROVED_SOURCE_REQUIRED")
    source = sources[0]
    expected_source_fields = {"source_id", "path", "byte_hash", "official_source_hash", "dataset_version", "source_format", "adapter_id"}
    if set(source) != expected_source_fields:
        raise CustodianIsolationError("APPROVED_SOURCE_POLICY_SCHEMA_REQUIRED")
    for field in ("byte_hash", "official_source_hash"):
        _sha(source[field])
    expected_source_contract = {
        "SYNTHETIC_OFFICIAL_SCENARIO_FIXTURE_V1": "SYNTHETIC_JSON_V1",
        "HAI_OFFICIAL_SCENARIO_METADATA_V1": "HAI_OFFICIAL_SCENARIO_METADATA_RAW_V1",
    }
    if expected_source_contract.get(source["adapter_id"]) != source["source_format"]:
        raise CustodianIsolationError("SOURCE_FORMAT_ADAPTER_BINDING_MISMATCH")
    if request["authority_mode"] == "PRODUCTION" and source["adapter_id"] != "HAI_OFFICIAL_SCENARIO_METADATA_V1":
        raise CustodianIsolationError("PRODUCTION_OFFICIAL_ADAPTER_REQUIRED")
    if request["authority_mode"] == "SYNTHETIC_REHEARSAL" and source["adapter_id"] != "SYNTHETIC_OFFICIAL_SCENARIO_FIXTURE_V1":
        raise CustodianIsolationError("SYNTHETIC_ADAPTER_REQUIRED")
    bindings = request.get("allowed_scenario_bindings")
    required_binding = {"panel_id", "dataset_version", "file_id", "physical_file_authority_hash", "timestamp_authority_hash", "official_source_hash"}
    if type(bindings) is not list or not bindings:
        raise CustodianIsolationError("SCENARIO_BINDINGS_REQUIRED")
    for binding in bindings:
        if type(binding) is not dict or set(binding) != required_binding:
            raise CustodianIsolationError("SCENARIO_BINDING_SCHEMA_REQUIRED")
        if binding["dataset_version"] != PANEL_VERSION.get(binding["panel_id"]):
            raise CustodianIsolationError("SCENARIO_PANEL_VERSION_MISMATCH")
        version_bound = (binding["dataset_version"] == source["dataset_version"] or
                         (request["authority_mode"] == "SYNTHETIC_REHEARSAL" and source["dataset_version"] == "MULTI_VERSION_23_22_21"))
        if not version_bound or binding["official_source_hash"] != source["official_source_hash"]:
            raise CustodianIsolationError("SCENARIO_SOURCE_BINDING_MISMATCH")
        for field in ("physical_file_authority_hash", "timestamp_authority_hash", "official_source_hash"):
            _sha(binding[field])
    if type(request["nominal_counts"]) is not dict or any(type(v) is not int or v < 0 for v in request["nominal_counts"].values()):
        raise CustodianIsolationError("NOMINAL_SCENARIO_COUNTS_REQUIRED")
    if type(request["public_authority_hashes"]) is not list or not request["public_authority_hashes"]:
        raise CustodianIsolationError("PUBLIC_AUTHORITIES_REQUIRED")
    for value in request["public_authority_hashes"]:
        _sha(value)
    if any(Path(name).name != name or name in (".", "..") for name in (request["approved_output_name"], request["consumed_receipt_name"])):
        raise CustodianIsolationError("OUTPUT_BASENAME_REQUIRED")
    return source


def _exclusive_write(path: Path, payload: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(payload); stream.flush(); os.fsync(stream.fileno())
        os.link(temporary, path)
    except FileExistsError as exc:
        raise CustodianIsolationError("SINGLE_CONSUME_OR_APPEND_ONLY_CONFLICT") from exc
    finally:
        if temporary.exists(): temporary.unlink()
    return sha256(payload).hexdigest()


def _adapt_source(raw: bytes, *, adapter_id: str) -> list[dict[str, Any]]:
    value = json.loads(raw.decode("utf-8"))
    expected_schema = {
        "SYNTHETIC_OFFICIAL_SCENARIO_FIXTURE_V1": "synthetic_raw_official_scenario_fixture_v1",
        "HAI_OFFICIAL_SCENARIO_METADATA_V1": "hai_official_scenario_metadata_raw_v1",
    }.get(adapter_id)
    if expected_schema is None or type(value) is not dict or set(value) != {"schema", "records"} or value["schema"] != expected_schema:
        raise CustodianIsolationError("RAW_SOURCE_ADAPTER_SCHEMA_REQUIRED")
    return value["records"]


def consume_and_extract_v1(request: Mapping[str, Any], *, resource_policy_authority_path: Path) -> dict[str, Any]:
    policy = _load_policy(resource_policy_authority_path)
    source_policy = validate_request_v1(request, resource_policy=policy)
    output_root = Path(policy["output_root"]).resolve()
    source_path = Path(source_policy["path"]).resolve()
    forbidden = tuple(Path(value).resolve() for value in policy["forbidden_roots"])
    if any(source_path == root or root in source_path.parents for root in forbidden):
        raise CustodianIsolationError("FORBIDDEN_NAMESPACE_ACCESS")
    consumed_path = output_root / request["consumed_receipt_name"]
    output_path = output_root / request["approved_output_name"]
    consumed_body = {"schema": "label_scenario_lease_consumed_v1", "issue_receipt_hash": request["lease_receipt"]["self_hash"],
                     "global_freeze_hash": request["global_freeze_hash"], "executable_manifest_hash": request["executable_manifest_hash"],
                     "resource_policy_hash": request["resource_policy_hash"],
                     "token_hash": sha256(request["opaque_lease"].encode("utf-8")).hexdigest(), "consume_count": 1}
    consumed = {**consumed_body, "self_hash": sha256(_canonical(consumed_body)).hexdigest()}
    _exclusive_write(consumed_path, _canonical(consumed) + b"\n")
    # Any read/adapter failure happens after durable lease consumption.
    source_bytes = source_path.read_bytes()
    if sha256(source_bytes).hexdigest() != source_policy["byte_hash"]:
        raise CustodianIsolationError("LEASED_SOURCE_BYTE_HASH_MISMATCH")
    records = _adapt_source(source_bytes, adapter_id=source_policy["adapter_id"])
    allowed = {(b["panel_id"], b["dataset_version"], b["file_id"]): b for b in request["allowed_scenario_bindings"]}
    required_record = {"panel_id", "dataset_version", "file_id", "scenario_id", "closed_intervals", "attacked_identities", "explicit_affected_processes"}
    bound_records = []
    for record in records:
        if type(record) is not dict or set(record) != required_record:
            raise CustodianIsolationError("OFFICIAL_SCENARIO_RECORD_SCHEMA_REQUIRED")
        binding = allowed.get((record["panel_id"], record["dataset_version"], record["file_id"]))
        if binding is None or record["dataset_version"] != PANEL_VERSION.get(record["panel_id"]):
            raise CustodianIsolationError("OFFICIAL_SCENARIO_FILE_BINDING_MISMATCH")
        if not record["scenario_id"] or not record["closed_intervals"] or not record["attacked_identities"]:
            raise CustodianIsolationError("OFFICIAL_SCENARIO_CONTENT_REQUIRED")
        if any(type(interval) is not list or len(interval) != 2 for interval in record["closed_intervals"]):
            raise CustodianIsolationError("CLOSED_INTERVAL_REQUIRED")
        bound_records.append({**record, "physical_file_authority_hash": binding["physical_file_authority_hash"],
                              "timestamp_authority_hash": binding["timestamp_authority_hash"],
                              "official_source_hash": binding["official_source_hash"]})
    actual = {panel: sum(record["panel_id"] == panel for record in bound_records) for panel in request["nominal_counts"]}
    if actual != request["nominal_counts"]:
        raise CustodianIsolationError("LEASED_SCENARIO_CENSUS_MISMATCH")
    if request["authority_mode"] == "PRODUCTION" and sorted(request["nominal_counts"].values()) != [38, 50, 58]:
        raise CustodianIsolationError("FROZEN_PRODUCTION_SCENARIO_COUNTS_REQUIRED")
    output_body = {"schema": "isolated_label_scenario_custodian_output_v1", "lease_consumed_hash": consumed["self_hash"],
                   "global_freeze_hash": request["global_freeze_hash"], "resource_policy_hash": request["resource_policy_hash"],
                   "scenario_adapter_id": source_policy["adapter_id"], "scenario_adapter_implementation_hash": policy["scenario_adapter_implementation_hash"],
                   "records": bound_records, "approved_source_byte_hash": source_policy["byte_hash"],
                   "official_source_hash": source_policy["official_source_hash"], "nominal_counts": request["nominal_counts"],
                   "allowed_scenario_binding_hash": sha256(_canonical(request["allowed_scenario_bindings"])).hexdigest(),
                   "prediction_capability": False}
    output = {**output_body, "self_hash": sha256(_canonical(output_body)).hexdigest()}
    output_hash = _exclusive_write(output_path, _canonical(output) + b"\n")
    return {"consume_receipt_hash": consumed["self_hash"], "output_self_hash": output["self_hash"], "output_byte_hash": output_hash}


__all__ = ["CustodianIsolationError", "REQUEST_FIELDS", "FORBIDDEN_TOKENS", "validate_request_v1", "consume_and_extract_v1"]
