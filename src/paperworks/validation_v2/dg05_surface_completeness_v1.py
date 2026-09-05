"""Static pre-access completeness oracle for DG-05 V3 declarations.

It opens only public contract/support authorities.  It has no prediction,
scenario, label, normal-value, provider, or credential capability.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any


class SurfaceCompletenessError(ValueError):
    pass


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def _load(path: Path, schema: str) -> dict[str, Any]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("ascii"))
    if raw != _canonical(value) + b"\n" or value.get("schema") != schema:
        raise SurfaceCompletenessError("NONCANONICAL_OR_SCHEMA_MISMATCH")
    body = {k: v for k, v in value.items() if k != "self_hash"}
    if value.get("self_hash") != sha256(_canonical(body)).hexdigest():
        raise SurfaceCompletenessError("SELF_HASH_MISMATCH")
    return value


def build_surface_support_declaration_v1(*, role: str, surface_ids: list[str], implementation_hash: str) -> dict[str, Any]:
    if role not in ("PRODUCTION_BUILDER", "INDEPENDENT_VERIFIER") or len(implementation_hash) != 64:
        raise SurfaceCompletenessError("INVALID_SUPPORT_DECLARATION")
    body = {"schema": "result_surface_support_declaration_v1", "role": role,
            "implementation_hash": implementation_hash, "surface_ids": sorted(surface_ids),
            "surface_count": len(surface_ids), "all_fields_typed": True, "authority_binding_required": True}
    return {**body, "self_hash": sha256(_canonical(body)).hexdigest()}


def verify_static_surface_completeness_from_paths_v1(*, contract_path: Path, expected_path: Path,
                                                     builder_support_path: Path, verifier_support_path: Path) -> dict[str, Any]:
    contract = _load(contract_path, "metric_surface_contract_v1")
    expected = _load(expected_path, "expected_result_surface_authority_v1")
    builder = _load(builder_support_path, "result_surface_support_declaration_v1")
    verifier = _load(verifier_support_path, "result_surface_support_declaration_v1")
    if (builder["role"], verifier["role"]) != ("PRODUCTION_BUILDER", "INDEPENDENT_VERIFIER"):
        raise SurfaceCompletenessError("SUPPORT_ROLE_MISMATCH")
    contract_ids = [v["surface_id"] for v in contract["surfaces"]]
    sets = tuple(set(values) for values in (contract_ids, expected["surface_ids"], builder["surface_ids"], verifier["surface_ids"]))
    if any(len(values) != len(set(values)) for values in (contract_ids, expected["surface_ids"], builder["surface_ids"], verifier["surface_ids"])):
        raise SurfaceCompletenessError("DUPLICATE_SURFACE_ID")
    if not (sets[0] == sets[1] == sets[2] == sets[3]):
        raise SurfaceCompletenessError("BLOCKED_METRIC_SURFACE_INCOMPLETE")
    body = {"schema": "result_surface_completeness_oracle_v1", "contract_hash": contract["self_hash"],
            "expected_hash": expected["self_hash"], "builder_support_hash": builder["self_hash"],
            "verifier_support_hash": verifier["self_hash"], "surface_count": len(sets[0]),
            "exact_set_equality": True, "data_access_capability": "PUBLIC_CONTRACTS_ONLY", "status": "PASS"}
    return {**body, "self_hash": sha256(_canonical(body)).hexdigest()}


__all__ = ["SurfaceCompletenessError", "build_surface_support_declaration_v1",
           "verify_static_surface_completeness_from_paths_v1"]
