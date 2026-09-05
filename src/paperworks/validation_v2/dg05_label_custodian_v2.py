"""Multi-source fresh-process DG-05 label/scenario custodian.

V2 closes the production mismatch in the V1 request: one lease may cover the
three version-specific official sources, but every source and scenario binding
remains explicit.  This module provides application-level capability and path
guards; it does not claim operating-system sandbox isolation.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import secrets
from typing import Any, Mapping


class CustodianV2Error(ValueError):
    """Raised before or after the one-shot lease is durably consumed."""


PANEL_VERSION = {
    "HAI23_TEST2_PRIMARY_HELDOUT_V1": "23.05",
    "HAI22_EXTERNAL_REPLICATION_V1": "22.04",
    "HAI21_EXTERNAL_REPLICATION_V1": "21.03",
}
FORBIDDEN_TOKENS = frozenset(
    {"prediction", "alarm", "method", "result", "score", "portfolio", "model", "provider"}
)
REQUEST_FIELDS = frozenset(
    {
        "schema",
        "opaque_lease",
        "lease_receipt",
        "global_freeze_hash",
        "predecessor_state_hash",
        "lease_issue_predecessor_hash",
        "executable_manifest_hash",
        "approved_source_ids",
        "approved_output_name",
        "public_authority_hashes",
        "resource_policy_hash",
        "allowed_scenario_bindings",
        "authority_mode",
        "nominal_counts",
    }
)
POLICY_FIELDS = frozenset(
    {
        "schema",
        "input_root",
        "output_root",
        "forbidden_roots",
        "approved_sources",
        "executable_manifest_hash",
        "scenario_adapter_implementation_hash",
        "resource_policy_contract_hash",
        "source_commit",
        "self_hash",
    }
)
SOURCE_FIELDS = frozenset(
    {"source_id", "path", "byte_hash", "official_source_hash", "dataset_version", "source_format", "adapter_id"}
)
BINDING_FIELDS = frozenset(
    {
        "source_id",
        "panel_id",
        "dataset_version",
        "file_id",
        "physical_file_authority_hash",
        "timestamp_authority_hash",
        "official_source_hash",
    }
)

ADAPTER_CONTRACTS = {
    "SYNTHETIC_OFFICIAL_SCENARIO_FIXTURE_V2": {
        "source_format": "SYNTHETIC_JSON_V2",
        "authority_mode": "SYNTHETIC_REHEARSAL",
        "source_schema": "synthetic_raw_official_scenario_fixture_v2",
    },
    "HAI_OFFICIAL_SCENARIO_METADATA_V2": {
        "source_format": "HAI_OFFICIAL_SCENARIO_METADATA_V2",
        "authority_mode": "PRODUCTION",
        "source_schema": "hai_official_scenario_metadata_raw_v2",
    },
}


def canonical_bytes_v2(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def self_hashed_v2(body: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(body)
    return {**value, "self_hash": sha256(canonical_bytes_v2(value)).hexdigest()}


def _sha(value: Any, field: str) -> None:
    if type(value) is not str or len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise CustodianV2Error(f"SHA256_REQUIRED:{field}")


def _mapping_keys(value: Any):
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key)
            yield from _mapping_keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _mapping_keys(item)


def _inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _load_policy(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8"))
    body = {key: item for key, item in value.items() if key != "self_hash"}
    if (
        set(value) != POLICY_FIELDS
        or value.get("schema") != "custodian_resource_policy_authority_v2"
        or value.get("self_hash") != sha256(canonical_bytes_v2(body)).hexdigest()
        or raw != canonical_bytes_v2(value) + b"\n"
    ):
        raise CustodianV2Error("VALID_PRIVATE_RESOURCE_POLICY_V2_REQUIRED")
    for field in ("executable_manifest_hash", "scenario_adapter_implementation_hash", "resource_policy_contract_hash"):
        _sha(value[field], field)
    if value["scenario_adapter_implementation_hash"] != sha256(Path(__file__).read_bytes()).hexdigest():
        raise CustodianV2Error("EXECUTED_CUSTODIAN_IMPLEMENTATION_MISMATCH")
    if type(value.get("source_commit")) is not str or len(value["source_commit"]) != 40:
        raise CustodianV2Error("RESOURCE_POLICY_SOURCE_COMMIT_REQUIRED")
    input_root = Path(value["input_root"]).resolve()
    output_root = Path(value["output_root"]).resolve()
    forbidden = tuple(Path(item).resolve() for item in value["forbidden_roots"])
    if (
        not forbidden
        or _inside(input_root, output_root)
        or _inside(output_root, input_root)
        or any(_inside(input_root, root) or _inside(output_root, root) for root in forbidden)
    ):
        raise CustodianV2Error("RESOURCE_POLICY_NAMESPACE_OVERLAP")
    sources = value.get("approved_sources")
    if type(sources) is not list or not sources or len({row.get("source_id") for row in sources}) != len(sources):
        raise CustodianV2Error("UNIQUE_APPROVED_SOURCE_REGISTRY_REQUIRED")
    for source in sources:
        if type(source) is not dict or set(source) != SOURCE_FIELDS:
            raise CustodianV2Error("APPROVED_SOURCE_POLICY_SCHEMA_REQUIRED")
        source_path = Path(source["path"]).resolve()
        if (
            source_path.is_symlink()
            or not source_path.is_file()
            or not _inside(source_path, input_root)
            or any(_inside(source_path, root) for root in forbidden)
        ):
            raise CustodianV2Error("APPROVED_SOURCE_OUTSIDE_RESOURCE_POLICY")
        _sha(source["byte_hash"], "byte_hash")
        _sha(source["official_source_hash"], "official_source_hash")
        contract = ADAPTER_CONTRACTS.get(source["adapter_id"])
        if contract is None or source["source_format"] != contract["source_format"]:
            raise CustodianV2Error("APPROVED_SOURCE_ADAPTER_FORMAT_MISMATCH")
    return value


def validate_request_v2(request: Mapping[str, Any], *, resource_policy: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    if set(request) != REQUEST_FIELDS or request.get("schema") != "isolated_label_scenario_custodian_request_v2":
        raise CustodianV2Error("MINIMAL_CUSTODIAN_V2_SCHEMA_REQUIRED")
    if any(any(token in key.lower() for token in FORBIDDEN_TOKENS) for key in _mapping_keys(request)):
        raise CustodianV2Error("PREDICTION_CAPABILITY_PROHIBITED")
    if request.get("resource_policy_hash") != resource_policy.get("self_hash"):
        raise CustodianV2Error("RESOURCE_POLICY_HASH_MISMATCH")
    if request.get("executable_manifest_hash") != resource_policy.get("executable_manifest_hash"):
        raise CustodianV2Error("RESOURCE_POLICY_MANIFEST_MISMATCH")
    receipt = request.get("lease_receipt")
    if type(receipt) is not dict:
        raise CustodianV2Error("VALID_LEASE_RECEIPT_REQUIRED")
    body = {key: item for key, item in receipt.items() if key != "self_hash"}
    if receipt.get("self_hash") != sha256(canonical_bytes_v2(body)).hexdigest():
        raise CustodianV2Error("VALID_LEASE_RECEIPT_REQUIRED")
    if sha256(str(request["opaque_lease"]).encode("utf-8")).hexdigest() != receipt.get("token_hash"):
        raise CustodianV2Error("LEASE_TOKEN_BINDING_MISMATCH")
    if (
        receipt.get("schema") != "single_use_label_scenario_lease_v3"
        or receipt.get("issue_count") != 1
        or receipt.get("consume_limit") != 1
        or receipt.get("state_hash") != request.get("lease_issue_predecessor_hash")
    ):
        raise CustodianV2Error("ONE_SHOT_LEASE_AUTHORITY_REQUIRED")
    for field in ("global_freeze_hash", "predecessor_state_hash", "lease_issue_predecessor_hash", "executable_manifest_hash", "resource_policy_hash"):
        _sha(request[field], field)
    if any(receipt.get(field) != request[field] for field in ("global_freeze_hash", "executable_manifest_hash", "resource_policy_hash")):
        raise CustodianV2Error("LEASE_AUTHORITY_BINDING_MISMATCH")
    if request["authority_mode"] not in ("PRODUCTION", "SYNTHETIC_REHEARSAL"):
        raise CustodianV2Error("CUSTODIAN_AUTHORITY_MODE_REQUIRED")
    source_ids = request.get("approved_source_ids")
    if type(source_ids) is not list or not source_ids or source_ids != sorted(set(source_ids)):
        raise CustodianV2Error("CANONICAL_APPROVED_SOURCE_IDS_REQUIRED")
    registry = {row["source_id"]: row for row in resource_policy["approved_sources"]}
    try:
        sources = tuple(registry[source_id] for source_id in source_ids)
    except KeyError as exc:
        raise CustodianV2Error("EXACT_APPROVED_SOURCE_REQUIRED") from exc
    if any(ADAPTER_CONTRACTS[source["adapter_id"]]["authority_mode"] != request["authority_mode"] for source in sources):
        raise CustodianV2Error("SOURCE_ADAPTER_AUTHORITY_MODE_MISMATCH")
    bindings = request.get("allowed_scenario_bindings")
    if type(bindings) is not list or not bindings:
        raise CustodianV2Error("SCENARIO_BINDINGS_REQUIRED")
    source_by_id = {source["source_id"]: source for source in sources}
    for binding in bindings:
        if type(binding) is not dict or set(binding) != BINDING_FIELDS:
            raise CustodianV2Error("SCENARIO_BINDING_SCHEMA_REQUIRED")
        source = source_by_id.get(binding["source_id"])
        if source is None or binding["dataset_version"] != PANEL_VERSION.get(binding["panel_id"]):
            raise CustodianV2Error("SCENARIO_PANEL_VERSION_MISMATCH")
        version_bound = source["dataset_version"] == binding["dataset_version"]
        if request["authority_mode"] == "SYNTHETIC_REHEARSAL" and source["dataset_version"] == "MULTI_VERSION_23_22_21":
            version_bound = True
        if not version_bound or binding["official_source_hash"] != source["official_source_hash"]:
            raise CustodianV2Error("SCENARIO_SOURCE_BINDING_MISMATCH")
        for field in ("physical_file_authority_hash", "timestamp_authority_hash", "official_source_hash"):
            _sha(binding[field], field)
    nominal = request.get("nominal_counts")
    if type(nominal) is not dict or any(type(value) is not int or value < 0 for value in nominal.values()):
        raise CustodianV2Error("NOMINAL_SCENARIO_COUNTS_REQUIRED")
    if type(request.get("public_authority_hashes")) is not list or not request["public_authority_hashes"]:
        raise CustodianV2Error("PUBLIC_AUTHORITIES_REQUIRED")
    for value in request["public_authority_hashes"]:
        _sha(value, "public_authority_hash")
    for name in (request["approved_output_name"],):
        if Path(name).name != name or name in (".", ".."):
            raise CustodianV2Error("OUTPUT_BASENAME_REQUIRED")
    return sources


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
        raise CustodianV2Error("SINGLE_CONSUME_OR_APPEND_ONLY_CONFLICT") from exc
    finally:
        if temporary.exists():
            temporary.unlink()
    return sha256(payload).hexdigest()


def _adapt_source(raw: bytes, *, adapter_id: str) -> list[dict[str, Any]]:
    value = json.loads(raw.decode("utf-8"))
    contract = ADAPTER_CONTRACTS.get(adapter_id)
    if contract is None:
        raise CustodianV2Error("APPROVED_SOURCE_ADAPTER_REQUIRED")
    expected = contract["source_schema"]
    if type(value) is not dict or set(value) != {"schema", "records"} or value.get("schema") != expected:
        raise CustodianV2Error("RAW_SOURCE_ADAPTER_SCHEMA_REQUIRED")
    if type(value["records"]) is not list:
        raise CustodianV2Error("RAW_SOURCE_RECORDS_REQUIRED")
    return value["records"]


def consume_and_extract_v2(request: Mapping[str, Any], *, resource_policy_authority_path: Path) -> dict[str, Any]:
    policy = _load_policy(resource_policy_authority_path)
    sources = validate_request_v2(request, resource_policy=policy)
    output_root = Path(policy["output_root"]).resolve()
    consumed_body = {
        "schema": "label_scenario_lease_consumed_v2",
        "issue_receipt_hash": request["lease_receipt"]["self_hash"],
        "global_freeze_hash": request["global_freeze_hash"],
        "predecessor_state_hash": request["predecessor_state_hash"],
        "executable_manifest_hash": request["executable_manifest_hash"],
        "resource_policy_hash": request["resource_policy_hash"],
        "token_hash": sha256(request["opaque_lease"].encode("utf-8")).hexdigest(),
        "consume_count": 1,
    }
    consumed = self_hashed_v2(consumed_body)
    # The consume marker is token-keyed, not caller-named.  Reusing one lease
    # therefore collides with the same append-only path even if other request
    # fields are changed.
    consumed_name = f"lease-consumed-{consumed_body['token_hash']}.json"
    _exclusive_write(output_root / consumed_name, canonical_bytes_v2(consumed) + b"\n")

    bindings = {
        (row["source_id"], row["panel_id"], row["dataset_version"], row["file_id"]): row
        for row in request["allowed_scenario_bindings"]
    }
    required_record = {
        "panel_id",
        "dataset_version",
        "file_id",
        "scenario_id",
        "closed_intervals",
        "attacked_identities",
        "explicit_affected_processes",
    }
    bound_records: list[dict[str, Any]] = []
    source_receipts = []
    for source in sources:
        source_path = Path(source["path"]).resolve()
        input_root = Path(policy["input_root"]).resolve()
        forbidden = tuple(Path(item).resolve() for item in policy["forbidden_roots"])
        if not source_path.is_file() or not _inside(source_path, input_root) or any(_inside(source_path, root) for root in forbidden):
            raise CustodianV2Error("APPROVED_SOURCE_OUTSIDE_RESOURCE_POLICY")
        raw = source_path.read_bytes()
        if sha256(raw).hexdigest() != source["byte_hash"]:
            raise CustodianV2Error("LEASED_SOURCE_BYTE_HASH_MISMATCH")
        for record in _adapt_source(raw, adapter_id=source["adapter_id"]):
            if type(record) is not dict or set(record) != required_record:
                raise CustodianV2Error("OFFICIAL_SCENARIO_RECORD_SCHEMA_REQUIRED")
            binding = bindings.get((source["source_id"], record["panel_id"], record["dataset_version"], record["file_id"]))
            if binding is None or not record["scenario_id"] or not record["closed_intervals"] or not record["attacked_identities"]:
                raise CustodianV2Error("OFFICIAL_SCENARIO_FILE_BINDING_MISMATCH")
            if any(type(interval) is not list or len(interval) != 2 for interval in record["closed_intervals"]):
                raise CustodianV2Error("CLOSED_INTERVAL_REQUIRED")
            bound_records.append(
                {
                    **record,
                    "physical_file_authority_hash": binding["physical_file_authority_hash"],
                    "timestamp_authority_hash": binding["timestamp_authority_hash"],
                    "official_source_hash": binding["official_source_hash"],
                }
            )
        source_receipts.append({"source_id": source["source_id"], "byte_hash": source["byte_hash"], "official_source_hash": source["official_source_hash"]})

    actual = {panel: sum(record["panel_id"] == panel for record in bound_records) for panel in request["nominal_counts"]}
    if actual != request["nominal_counts"]:
        raise CustodianV2Error("LEASED_SCENARIO_CENSUS_MISMATCH")
    if request["authority_mode"] == "PRODUCTION":
        if actual != {"HAI23_TEST2_PRIMARY_HELDOUT_V1": 38, "HAI22_EXTERNAL_REPLICATION_V1": 58, "HAI21_EXTERNAL_REPLICATION_V1": 50}:
            raise CustodianV2Error("FROZEN_PRODUCTION_SCENARIO_COUNTS_REQUIRED")
        if {source["dataset_version"] for source in sources} != {"23.05", "22.04", "21.03"}:
            raise CustodianV2Error("THREE_VERSION_PRODUCTION_SOURCE_SET_REQUIRED")
    output_body = {
        "schema": "isolated_label_scenario_custodian_output_v2",
        "lease_consumed_hash": consumed["self_hash"],
        "global_freeze_hash": request["global_freeze_hash"],
        "predecessor_state_hash": request["predecessor_state_hash"],
        "executable_manifest_hash": request["executable_manifest_hash"],
        "authority_mode": request["authority_mode"],
        "resource_policy_hash": request["resource_policy_hash"],
        "scenario_adapter_implementation_hash": policy["scenario_adapter_implementation_hash"],
        "source_receipts": sorted(source_receipts, key=lambda row: row["source_id"]),
        "records": sorted(bound_records, key=lambda row: (row["panel_id"], row["file_id"], row["scenario_id"])),
        "nominal_counts": request["nominal_counts"],
        "allowed_scenario_binding_hash": sha256(canonical_bytes_v2(request["allowed_scenario_bindings"])).hexdigest(),
        "prediction_capability": False,
    }
    output = self_hashed_v2(output_body)
    output_hash = _exclusive_write(output_root / request["approved_output_name"], canonical_bytes_v2(output) + b"\n")
    return {
        "schema": "fresh_process_custodian_completion_v2",
        "consume_receipt_hash": consumed["self_hash"],
        "output_self_hash": output["self_hash"],
        "output_byte_hash": output_hash,
        "authority_mode": request["authority_mode"],
        "executable_manifest_hash": request["executable_manifest_hash"],
    }


__all__ = [
    "CustodianV2Error",
    "REQUEST_FIELDS",
    "canonical_bytes_v2",
    "self_hashed_v2",
    "validate_request_v2",
    "consume_and_extract_v2",
]
