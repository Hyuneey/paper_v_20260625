"""Immutable V11 candidate release gate.

This module deliberately does not extend the historical V5--V10 manifest
semantics.  V11 binds the closed scenario/P1 roots and resolves the frozen V5
kernel by object identity before either a rehearsal or eventual real run.
"""
from __future__ import annotations

from hashlib import sha256
import importlib
import inspect
import json
from pathlib import Path
from typing import Any, Mapping


PREACCESS_MODE = "PREACCESS_SYNTHETIC_QUALIFICATION"
REAL_MODE = "REAL_HELDOUT_EXECUTION"
KERNEL_MODULE = "paperworks.validation_v2.dg05_production_route_v5"
KERNEL_SYMBOL = "execute_prediction_schedule_v5"


class DG05ProductionChainV11Error(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("ascii")


def digest(value: Any) -> str:
    return sha256(canonical_bytes(value)).hexdigest()


def self_hashed(value: Mapping[str, Any]) -> dict[str, Any]:
    return {**value, "self_hash": digest(value)}


def file_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def load_self_hashed(path: Path, schema: str | None = None) -> dict[str, Any]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("ascii"))
    if (raw != canonical_bytes(value) + b"\n" or
            value.get("self_hash") != digest({k: v for k, v in value.items() if k != "self_hash"}) or
            (schema is not None and value.get("schema") != schema)):
        raise DG05ProductionChainV11Error("V11_AUTHORITY_REPLAY_FAILED")
    return value


def resolve_frozen_kernel_v11(repository_root: Path) -> dict[str, str]:
    """Resolve the live callable and its bytes; never trust a route-name string."""
    module = importlib.import_module(KERNEL_MODULE)
    callable_value = getattr(module, KERNEL_SYMBOL, None)
    if not callable(callable_value) or callable_value.__module__ != KERNEL_MODULE:
        raise DG05ProductionChainV11Error("V11_KERNEL_CALLABLE_SUBSTITUTION")
    source = Path(inspect.getsourcefile(callable_value) or "").resolve()
    root = repository_root.resolve()
    if root not in source.parents:
        raise DG05ProductionChainV11Error("V11_KERNEL_SOURCE_OUTSIDE_REPOSITORY")
    return {"module": KERNEL_MODULE, "symbol": KERNEL_SYMBOL,
            "relative_path": source.relative_to(root).as_posix(),
            "source_byte_hash": file_hash(source)}


def build_v11_candidate_manifest(*, repository_root: Path, source_commit: str,
                                authority_hashes: Mapping[str, str],
                                implementation_paths: Mapping[str, Path],
                                qualification_hashes: Mapping[str, str],
                                status: str = "CANDIDATE_AWAITING_EXACT_USER_APPROVAL") -> dict[str, Any]:
    required_roots = {
        "physical_custody", "normal_registry", "scenario_authority", "unified_p1",
        "dec031", "dec034", "dec035", "dec036", "dec037", "scientific_preregistration",
    }
    if set(authority_hashes) != required_roots or any(type(v) is not str or len(v) != 64 for v in authority_hashes.values()):
        raise DG05ProductionChainV11Error("V11_COMPLETE_ROOT_CENSUS_REQUIRED")
    required_implementation = {
        "scenario_adapter", "custodian", "production_route", "frozen_v5_kernel",
        "fresh_process_launcher", "root_verifier", "release_gate",
    }
    if set(implementation_paths) != required_implementation:
        raise DG05ProductionChainV11Error("V11_COMPLETE_IMPLEMENTATION_CENSUS_REQUIRED")
    root = repository_root.resolve()
    implementations: list[dict[str, str]] = []
    for name, path in sorted(implementation_paths.items()):
        resolved = path.resolve()
        if root not in resolved.parents or not resolved.is_file() or resolved.is_symlink():
            raise DG05ProductionChainV11Error("V11_IMPLEMENTATION_PATH_INVALID")
        implementations.append({"logical_name": name,
                                "relative_path": resolved.relative_to(root).as_posix(),
                                "byte_hash": file_hash(resolved)})
    expected_qualification = {"root_replay", "kernel_parity", "fresh_process", "independent_qa", "privacy", "adversarial", "rehearsal"}
    if set(qualification_hashes) != expected_qualification:
        raise DG05ProductionChainV11Error("V11_QUALIFICATION_CENSUS_REQUIRED")
    kernel = resolve_frozen_kernel_v11(root)
    if status not in {"CANDIDATE_AWAITING_EXACT_USER_APPROVAL", "TECHNICAL_PREQUALIFICATION_ONLY"}:
        raise DG05ProductionChainV11Error("V11_RELEASE_STATUS_REQUIRED")
    return self_hashed({
        "schema": "dg05_executable_v11_candidate_manifest_v1",
        "designation": "DG05_EXECUTABLE_V11",
        "status": status,
        "approval_status": "NOT_APPROVED",
        "implementation_source_commit": source_commit,
        "authority_hashes": dict(sorted(authority_hashes.items())),
        "implementation_authorities": implementations,
        "frozen_kernel": kernel,
        "qualification_hashes": dict(sorted(qualification_hashes.items())),
        "heldout_predictions_observed": 0,
        "heldout_metrics_observed": 0,
        "alternate_scientific_route": False,
        "synthetic_fallback_authorized": False,
    })


def initialize_v11_candidate(*, manifest_path: Path, repository_root: Path,
                             expected_hash: str, mode: str,
                             user_approved_release_hash: str | None = None) -> dict[str, Any]:
    manifest = load_self_hashed(manifest_path, "dg05_executable_v11_candidate_manifest_v1")
    root = repository_root.resolve()
    if manifest.get("self_hash") != expected_hash or manifest.get("status") not in {"CANDIDATE_AWAITING_EXACT_USER_APPROVAL", "TECHNICAL_PREQUALIFICATION_ONLY"}:
        raise DG05ProductionChainV11Error("V11_RELEASE_ROOT_REPLAY_FAILED")
    for item in manifest.get("implementation_authorities", []):
        path = (root / item["relative_path"]).resolve()
        if root not in path.parents or not path.is_file() or path.is_symlink() or file_hash(path) != item["byte_hash"]:
            raise DG05ProductionChainV11Error("V11_IMPLEMENTATION_BYTE_REPLAY_FAILED")
    current_kernel = resolve_frozen_kernel_v11(root)
    if current_kernel != manifest.get("frozen_kernel"):
        raise DG05ProductionChainV11Error("V11_KERNEL_IDENTITY_REPLAY_FAILED")
    if mode == PREACCESS_MODE:
        state, protected = "PREACCESS_V11_CANDIDATE_INITIALIZED", False
    elif mode == REAL_MODE:
        if manifest.get("status") != "CANDIDATE_AWAITING_EXACT_USER_APPROVAL":
            raise DG05ProductionChainV11Error("V11_TECHNICAL_PREQUALIFICATION_NOT_EXECUTABLE")
        if user_approved_release_hash != manifest["self_hash"]:
            raise DG05ProductionChainV11Error("EXACT_V11_USER_APPROVAL_REQUIRED")
        state, protected = "APPROVED_V11_REAL_EXECUTION_INITIALIZED", True
    else:
        raise DG05ProductionChainV11Error("V11_MODE_REQUIRED")
    return self_hashed({"schema": "dg05_v11_candidate_state_v1", "state": state,
                        "mode": mode, "release_manifest_hash": manifest["self_hash"],
                        "protected_access_authorized": protected,
                        "kernel": current_kernel, "heldout_prediction_cells": 0,
                        "metric_cells": 0})
