"""Pre-access initializer for the additive DG-05 executable V3 package."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping


class DG05ExecutableV3Error(ValueError):
    pass


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def _load(path: Path, schema: str) -> dict[str, Any]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("ascii"))
    if raw != _canonical(value) + b"\n" or value.get("schema") != schema:
        raise DG05ExecutableV3Error("CANONICAL_SCHEMA_REPLAY_FAILED")
    body = {k: v for k, v in value.items() if k != "self_hash"}
    if value.get("self_hash") != sha256(_canonical(body)).hexdigest():
        raise DG05ExecutableV3Error("SELF_HASH_REPLAY_FAILED")
    return value


def initialize_dg05_executable_v3_preaccess(*, manifest_path: Path, closure_path: Path,
                                            nested_paths: Mapping[str, tuple[Path, str]],
                                            approved_manifest_hash: str | None) -> dict[str, Any]:
    """Replay V3 without granting attack access; approval must be a future hash."""
    manifest = _load(manifest_path, "dg05_executable_authority_manifest_v3")
    closure = _load(closure_path, "dg05_executable_closure_authority_v3")
    if manifest["self_hash"] != closure["executable_manifest_hash"]:
        raise DG05ExecutableV3Error("MANIFEST_CLOSURE_BINDING_MISMATCH")
    expected = {
        "contract": manifest["metric_surface_contract_hash"],
        "expected": manifest["expected_result_surface_hash"],
        "builder_support": manifest["builder_support_hash"],
        "verifier_support": manifest["verifier_support_hash"],
        "completeness": manifest["completeness_oracle_authority_hash"],
    }
    if set(nested_paths) != set(expected):
        raise DG05ExecutableV3Error("NESTED_AUTHORITY_CENSUS_MISMATCH")
    replayed = {}
    for key, (path, schema) in nested_paths.items():
        value = _load(path, schema)
        if value["self_hash"] != expected[key]:
            raise DG05ExecutableV3Error(f"NESTED_AUTHORITY_MISMATCH:{key}")
        replayed[key] = value["self_hash"]
    if approved_manifest_hash is None:
        status = "DG05_V3_USER_REAPPROVAL_REQUIRED"
        attack_access_authorized = False
    elif approved_manifest_hash != manifest["self_hash"]:
        raise DG05ExecutableV3Error("EXACT_V3_APPROVAL_HASH_REQUIRED")
    else:
        status = "DG05_V3_APPROVAL_HASH_REPLAYED"
        attack_access_authorized = True
    body = {"schema": "dg05_executable_v3_preaccess_state_v1", "state": status,
            "executable_manifest_hash": manifest["self_hash"], "closure_hash": closure["self_hash"],
            "nested_authorities": replayed, "attack_access_authorized": attack_access_authorized,
            "attack_test_accesses": 0, "label_scenario_accesses": 0}
    return {**body, "self_hash": sha256(_canonical(body)).hexdigest()}


__all__ = ["DG05ExecutableV3Error", "initialize_dg05_executable_v3_preaccess"]
