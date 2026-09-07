"""Typed, replay-derived V11R2R1 no-contact preflight receipts.

This module deliberately consumes the *actual* complete-preflight replay
bundle.  It has no authority replay of its own and, in particular, must never
turn expected census constants into evidence.  The runner uses the same
verifier after a fresh real-mode replay before it can consume the execution
ledger.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

from .dg05_production_chain_v11 import canonical_bytes, load_self_hashed, self_hashed


class DG05V11R2R1PreflightReceiptError(ValueError):
    """A typed receipt is missing, mutated, or disagrees with fresh replay."""


_SCHEMA = "dg05_v11r2r1_real_preflight_receipt_v1"
_BUNDLE_SCHEMA = "dg05_v11r2r1_complete_real_preflight_authority_replay_v1"
_REQUIRED_BUNDLE_HASHES = (
    "implementation_replay_hash",
    "execution_binding_hash",
    "execution_binding_replay_hash",
    "v5_kernel_hash",
    "legacy_hash",
    "v4_hash",
    "v4_closure_hash",
    "v1_hash",
    "legacy_predecessor_replay_hash",
    "physical_hash",
    "framing_hash",
    "production_executor_hash",
    "normal_authority_hash",
    "scenario_hash",
    "p1_hash",
    "crosswalk_hash",
    "crosswalk_replay_hash",
    "execution_scope_id",
    "ledger_status_hash",
)


def _hash(value: object, code: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise DG05V11R2R1PreflightReceiptError(code)
    return value


def _require_zero_contact(document: Mapping[str, Any], code: str) -> None:
    if any(document.get(key) != 0 for key in (
        "heldout_rows_parsed", "heldout_predictions", "heldout_metrics",
    )):
        raise DG05V11R2R1PreflightReceiptError(code)


def _validate_replay_bundle(bundle: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(bundle)
    if value.get("schema") != _BUNDLE_SCHEMA or value.get("status") != "PASS":
        raise DG05V11R2R1PreflightReceiptError("V11R2R1_COMPLETE_REPLAY_REQUIRED")
    expected = self_hashed({key: item for key, item in value.items() if key != "self_hash"})
    if expected != value:
        raise DG05V11R2R1PreflightReceiptError("V11R2R1_COMPLETE_REPLAY_SELF_HASH_REQUIRED")
    for key in _REQUIRED_BUNDLE_HASHES:
        _hash(value.get(key), "V11R2R1_COMPLETE_REPLAY_FIELD_REQUIRED")
    _require_zero_contact(value, "V11R2R1_COMPLETE_REPLAY_CONTACT_REJECTED")
    return value


def _validate_approval_replay(approval_replay: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(approval_replay)
    if value.get("status") != "PASS":
        raise DG05V11R2R1PreflightReceiptError("V11R2R1_RUNTIME_APPROVAL_REPLAY_REQUIRED")
    expected = self_hashed({key: item for key, item in value.items() if key != "self_hash"})
    if expected != value:
        raise DG05V11R2R1PreflightReceiptError("V11R2R1_RUNTIME_APPROVAL_REPLAY_SELF_HASH_REQUIRED")
    for key in ("release_hash", "final_closure_hash", "execution_binding_hash"):
        _hash(value.get(key), "V11R2R1_RUNTIME_APPROVAL_FIELD_REQUIRED")
    return value


def _validate_ledger_unused(status: Mapping[str, Any], scope_id: str) -> dict[str, Any]:
    value = dict(status)
    if value.get("status") != "UNUSED" or value.get("execution_scope_id") != scope_id:
        raise DG05V11R2R1PreflightReceiptError("V11R2R1_EXECUTION_LEDGER_NOT_UNUSED")
    expected = self_hashed({key: item for key, item in value.items() if key != "self_hash"})
    if expected != value:
        raise DG05V11R2R1PreflightReceiptError("V11R2R1_LEDGER_STATUS_SELF_HASH_REQUIRED")
    return value


def build_real_preflight_receipt_v11r2r1(*, manifest: Mapping[str, Any],
                                          approval_replay: Mapping[str, Any],
                                          replay_bundle: Mapping[str, Any],
                                          ledger_status: Mapping[str, Any]) -> dict[str, Any]:
    """Bind a PASS receipt only to already validated, actual replay evidence."""
    approval = _validate_approval_replay(approval_replay)
    bundle = _validate_replay_bundle(replay_bundle)
    release_hash = _hash(manifest.get("self_hash"), "V11R2R1_RELEASE_HASH_REQUIRED")
    binding_hash = _hash(manifest.get("execution_binding_hash"), "V11R2R1_EXECUTION_BINDING_REQUIRED")
    if approval["release_hash"] != release_hash or approval["execution_binding_hash"] != binding_hash:
        raise DG05V11R2R1PreflightReceiptError("V11R2R1_APPROVAL_MANIFEST_MISMATCH")
    if bundle["execution_binding_hash"] != binding_hash:
        raise DG05V11R2R1PreflightReceiptError("V11R2R1_REPLAY_BINDING_MISMATCH")
    if bundle["scenario_hash"] != manifest.get("scenario_authority_hash"):
        raise DG05V11R2R1PreflightReceiptError("V11R2R1_REPLAY_SCENARIO_MISMATCH")
    if bundle["p1_hash"] != manifest.get("p1_authority_hash"):
        raise DG05V11R2R1PreflightReceiptError("V11R2R1_REPLAY_P1_MISMATCH")
    if bundle["crosswalk_hash"] != manifest.get("source_file_crosswalk_hash"):
        raise DG05V11R2R1PreflightReceiptError("V11R2R1_REPLAY_CROSSWALK_MISMATCH")
    ledger = _validate_ledger_unused(ledger_status, bundle["execution_scope_id"])
    # All census values are intentionally absent: validated replay receipt
    # hashes, not expected constants, are the authority for those counts.
    return self_hashed({
        "schema": _SCHEMA,
        "status": "REAL_PREFLIGHT_PASS_NO_FEATURE_ACCESS",
        "release_hash": release_hash,
        "final_closure_hash": approval["final_closure_hash"],
        "execution_binding_hash": binding_hash,
        "implementation_source_commit": manifest.get("implementation_source_commit"),
        "implementation_replay_receipt_hash": bundle["implementation_replay_hash"],
        "complete_replay_bundle_hash": bundle["self_hash"],
        "execution_binding_replay_hash": bundle["execution_binding_replay_hash"],
        "v5_kernel_hash": bundle["v5_kernel_hash"],
        "legacy_predecessor_replay_hashes": {
            "legacy_release": bundle["legacy_hash"],
            "predecessor_v4_manifest": bundle["v4_hash"],
            "predecessor_v4_closure": bundle["v4_closure_hash"],
            "historical_v1_manifest": bundle["v1_hash"],
        },
        "legacy_predecessor_replay_hash": bundle["legacy_predecessor_replay_hash"],
        "physical_custody_replay_hash": bundle["physical_hash"],
        "container_framing_replay_hash": bundle["framing_hash"],
        "production_executor_replay_hash": bundle["production_executor_hash"],
        "normal_authority_replay_hash": bundle["normal_authority_hash"],
        "scenario_authority_hash": bundle["scenario_hash"],
        "p1_authority_hash": bundle["p1_hash"],
        "source_file_crosswalk_hash": bundle["crosswalk_hash"],
        "source_file_crosswalk_replay_hash": bundle["crosswalk_replay_hash"],
        "execution_scope_id": bundle["execution_scope_id"],
        "ledger_status_hash": ledger["self_hash"],
        "ledger_status": "UNUSED",
        "heldout_rows_parsed": 0,
        "heldout_predictions": 0,
        "heldout_metrics": 0,
        "execution_consumed": False,
    })


def persist_real_preflight_receipt_v11r2r1(*, path: Path, receipt: Mapping[str, Any]) -> None:
    """Append-only persistence; callers cannot overwrite a preflight result."""
    expected = self_hashed({key: value for key, value in receipt.items() if key != "self_hash"})
    if dict(receipt) != expected or receipt.get("schema") != _SCHEMA:
        raise DG05V11R2R1PreflightReceiptError("V11R2R1_PREFLIGHT_RECEIPT_SELF_HASH_REQUIRED")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise DG05V11R2R1PreflightReceiptError("V11R2R1_PREFLIGHT_RECEIPT_EXISTS") from exc
    try:
        with os.fdopen(fd, "wb", closefd=True) as stream:
            stream.write(canonical_bytes(dict(receipt)) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        try:
            os.close(fd)
        except OSError:
            pass


def verify_real_preflight_receipt_v11r2r1(*, receipt_path: Path,
                                           manifest: Mapping[str, Any],
                                           approval_replay: Mapping[str, Any],
                                           fresh_replay_bundle: Mapping[str, Any],
                                           ledger_status: Mapping[str, Any]) -> dict[str, Any]:
    """Require stored and freshly replayed immutable preconditions to agree."""
    receipt = load_self_hashed(receipt_path, _SCHEMA)
    expected = build_real_preflight_receipt_v11r2r1(
        manifest=manifest,
        approval_replay=approval_replay,
        replay_bundle=fresh_replay_bundle,
        ledger_status=ledger_status,
    )
    # The ledger status is environmental, so compare immutable receipt
    # bindings and require a fresh UNUSED status separately, not path details.
    keys = tuple(key for key in expected if key not in {"self_hash", "ledger_status_hash"})
    if any(receipt.get(key) != expected.get(key) for key in keys):
        raise DG05V11R2R1PreflightReceiptError("V11R2R1_STORED_PREFLIGHT_FRESH_REPLAY_MISMATCH")
    _require_zero_contact(receipt, "V11R2R1_PREFLIGHT_CONTACT_REJECTED")
    if receipt.get("execution_consumed") is not False or receipt.get("ledger_status") != "UNUSED":
        raise DG05V11R2R1PreflightReceiptError("V11R2R1_PREFLIGHT_LEDGER_STATUS_REQUIRED")
    return receipt


__all__ = [
    "DG05V11R2R1PreflightReceiptError",
    "build_real_preflight_receipt_v11r2r1",
    "persist_real_preflight_receipt_v11r2r1",
    "verify_real_preflight_receipt_v11r2r1",
]
