"""Release-scoped, durable, fail-closed one-time execution ledger."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

from .dg05_production_chain_v11 import canonical_bytes, digest, load_self_hashed, self_hashed


class DG05V11R2ExecutionLedgerError(ValueError):
    pass


_SCHEMA = "dg05_v11r2_execution_ledger_state_v1"
_FILE_BY_STATE = {
    "REAL_EXECUTION_STARTED": "REAL_EXECUTION_STARTED.json",
    "SCIENTIFIC_CONTACT_GUARD_COMMITTED": "SCIENTIFIC_CONTACT_GUARD_COMMITTED.json",
    "PREDICTIONS_FROZEN": "PREDICTIONS_FROZEN.json",
    "METRICS_FROZEN": "METRICS_FROZEN.json",
    "TERMINAL_COMPLETE": "TERMINAL_COMPLETE.json",
    "PRECONTACT_ABORTED": "PRECONTACT_ABORTED.json",
    "TERMINAL_FAILED_AFTER_SCIENTIFIC_CONTACT": "TERMINAL_FAILED_AFTER_SCIENTIFIC_CONTACT.json",
}
_TERMINAL_TRANSITIONS = {
    "REAL_EXECUTION_STARTED": {"PRECONTACT_ABORTED"},
    "SCIENTIFIC_CONTACT_GUARD_COMMITTED": {"PREDICTIONS_FROZEN", "TERMINAL_FAILED_AFTER_SCIENTIFIC_CONTACT"},
    "PREDICTIONS_FROZEN": {"METRICS_FROZEN", "TERMINAL_FAILED_AFTER_SCIENTIFIC_CONTACT"},
    "METRICS_FROZEN": {"TERMINAL_COMPLETE", "TERMINAL_FAILED_AFTER_SCIENTIFIC_CONTACT"},
}


def execution_scope_id_v11r2(*, release_hash: str, final_closure_hash: str, execution_binding_hash: str) -> str:
    return digest({"release_hash": release_hash, "final_closure_hash": final_closure_hash,
                   "execution_binding_hash": execution_binding_hash})


def ledger_scope_status_v11r2(*, ledger_root: Path, release_hash: str,
                              final_closure_hash: str, execution_binding_hash: str) -> dict[str, Any]:
    """Read the release-scoped ledger without creating or repairing it.

    Any existing scope directory is consumed.  This deliberately treats an
    interrupted/unknown state as non-retryable rather than attempting repair.
    """
    scope = execution_scope_id_v11r2(
        release_hash=release_hash,
        final_closure_hash=final_closure_hash,
        execution_binding_hash=execution_binding_hash,
    )
    scope_path = ledger_root / scope
    if not scope_path.exists():
        return self_hashed({"schema": "dg05_v11r2_execution_ledger_scope_status_v1",
                            "status": "UNUSED", "execution_scope_id": scope,
                            "state_hashes": {}})
    if not scope_path.is_dir() or scope_path.is_symlink():
        raise DG05V11R2ExecutionLedgerError("V11R2_EXECUTION_SCOPE_ALREADY_CONSUMED")
    state_hashes: dict[str, str] = {}
    for state, filename in _FILE_BY_STATE.items():
        path = scope_path / filename
        if not path.exists():
            continue
        if path.is_symlink() or not path.is_file():
            raise DG05V11R2ExecutionLedgerError("V11R2_EXECUTION_LEDGER_STATE_INVALID")
        try:
            document = load_self_hashed(path, _SCHEMA)
        except Exception as exc:
            raise DG05V11R2ExecutionLedgerError("V11R2_EXECUTION_LEDGER_STATE_INVALID") from exc
        if document.get("state") != state or document.get("execution_scope_id") != scope:
            raise DG05V11R2ExecutionLedgerError("V11R2_EXECUTION_LEDGER_STATE_INVALID")
        state_hashes[state] = document["self_hash"]
    return self_hashed({"schema": "dg05_v11r2_execution_ledger_scope_status_v1",
                        "status": "CONSUMED", "execution_scope_id": scope,
                        "state_hashes": state_hashes})


def _durable_exclusive_json(path: Path, document: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise DG05V11R2ExecutionLedgerError("V11R2_EXECUTION_SCOPE_ALREADY_CONSUMED") from exc
    try:
        with os.fdopen(fd, "wb", closefd=True) as stream:
            stream.write(canonical_bytes(dict(document)) + b"\n")
            stream.flush(); os.fsync(stream.fileno())
    finally:
        # fdopen owns a successfully opened descriptor; the defensive branch
        # only applies if constructing the stream itself failed.
        try: os.close(fd)
        except OSError: pass
    try:
        directory_fd = os.open(str(path.parent), os.O_RDONLY)
        try: os.fsync(directory_fd)
        finally: os.close(directory_fd)
    except OSError:
        # Directory fsync is not exposed by Windows; file fsync remains
        # required and the immutable exclusive record is still fail-closed.
        pass


def _document(*, state: str, scope_id: str, release_hash: str, final_closure_hash: str,
              execution_binding_hash: str, preflight_receipt_hash: str, physical_custody_hash: str,
              output_namespace: str, predecessor_hash: str | None) -> dict[str, Any]:
    return self_hashed({"schema": _SCHEMA, "state": state,
                        "execution_scope_id": scope_id, "release_hash": release_hash,
                        "final_closure_hash": final_closure_hash, "execution_binding_hash": execution_binding_hash,
                        "preflight_receipt_hash": preflight_receipt_hash,
                        "physical_custody_hash": physical_custody_hash, "output_namespace": output_namespace,
                        "predecessor_state_hash": predecessor_hash,
                        "retry_policy": "NO_AUTOMATIC_RETRY;CONTACT_GUARD_CONSUMES_SCOPE"})


def start_real_execution_v11r2(*, ledger_root: Path, release_hash: str, final_closure_hash: str,
                                execution_binding_hash: str, preflight_receipt_hash: str,
                                physical_custody_hash: str, output_namespace: str) -> dict[str, Any]:
    scope = execution_scope_id_v11r2(release_hash=release_hash, final_closure_hash=final_closure_hash,
                                     execution_binding_hash=execution_binding_hash)
    status = ledger_scope_status_v11r2(
        ledger_root=ledger_root, release_hash=release_hash,
        final_closure_hash=final_closure_hash, execution_binding_hash=execution_binding_hash,
    )
    if status["status"] != "UNUSED":
        raise DG05V11R2ExecutionLedgerError("V11R2_EXECUTION_SCOPE_ALREADY_CONSUMED")
    path = ledger_root / scope / _FILE_BY_STATE["REAL_EXECUTION_STARTED"]
    state = _document(state="REAL_EXECUTION_STARTED", scope_id=scope, release_hash=release_hash,
                      final_closure_hash=final_closure_hash, execution_binding_hash=execution_binding_hash,
                      preflight_receipt_hash=preflight_receipt_hash, physical_custody_hash=physical_custody_hash,
                      output_namespace=output_namespace, predecessor_hash=None)
    _durable_exclusive_json(path, state)
    return state


def append_contact_guard_v11r2(*, ledger_root: Path, start_state: Mapping[str, Any]) -> dict[str, Any]:
    if start_state.get("state") != "REAL_EXECUTION_STARTED":
        raise DG05V11R2ExecutionLedgerError("V11R2_START_STATE_REQUIRED")
    _require_durable_predecessor(ledger_root=ledger_root, predecessor=start_state)
    state = _document(state="SCIENTIFIC_CONTACT_GUARD_COMMITTED", scope_id=start_state["execution_scope_id"],
                      release_hash=start_state["release_hash"], final_closure_hash=start_state["final_closure_hash"],
                      execution_binding_hash=start_state["execution_binding_hash"], preflight_receipt_hash=start_state["preflight_receipt_hash"],
                      physical_custody_hash=start_state["physical_custody_hash"], output_namespace=start_state["output_namespace"],
                      predecessor_hash=start_state["self_hash"])
    _durable_exclusive_json(ledger_root / state["execution_scope_id"] / _FILE_BY_STATE["SCIENTIFIC_CONTACT_GUARD_COMMITTED"], state)
    return state


def append_terminal_state_v11r2(*, ledger_root: Path, predecessor: Mapping[str, Any], state_name: str) -> dict[str, Any]:
    if state_name not in _FILE_BY_STATE or state_name == "SCIENTIFIC_CONTACT_GUARD_COMMITTED":
        raise DG05V11R2ExecutionLedgerError("V11R2_LEDGER_STATE_REQUIRED")
    previous = predecessor.get("state")
    if state_name not in _TERMINAL_TRANSITIONS.get(previous, set()):
        raise DG05V11R2ExecutionLedgerError("V11R2_LEDGER_TRANSITION_REQUIRED")
    _require_durable_predecessor(ledger_root=ledger_root, predecessor=predecessor)
    state = _document(state=state_name, scope_id=predecessor["execution_scope_id"], release_hash=predecessor["release_hash"],
                      final_closure_hash=predecessor["final_closure_hash"], execution_binding_hash=predecessor["execution_binding_hash"],
                      preflight_receipt_hash=predecessor["preflight_receipt_hash"], physical_custody_hash=predecessor["physical_custody_hash"],
                      output_namespace=predecessor["output_namespace"], predecessor_hash=predecessor["self_hash"])
    _durable_exclusive_json(ledger_root / state["execution_scope_id"] / _FILE_BY_STATE[state_name], state)
    return state


def _require_durable_predecessor(*, ledger_root: Path, predecessor: Mapping[str, Any]) -> None:
    """Reject forged/in-memory-only predecessor states before a transition."""
    state_name = predecessor.get("state")
    scope = predecessor.get("execution_scope_id")
    if state_name not in _FILE_BY_STATE or not isinstance(scope, str):
        raise DG05V11R2ExecutionLedgerError("V11R2_LEDGER_PREDECESSOR_REQUIRED")
    path = ledger_root / scope / _FILE_BY_STATE[state_name]
    try:
        durable = load_self_hashed(path, _SCHEMA)
    except Exception as exc:
        raise DG05V11R2ExecutionLedgerError("V11R2_LEDGER_PREDECESSOR_REQUIRED") from exc
    if durable != dict(predecessor):
        raise DG05V11R2ExecutionLedgerError("V11R2_LEDGER_PREDECESSOR_REQUIRED")


__all__ = ["DG05V11R2ExecutionLedgerError", "execution_scope_id_v11r2", "ledger_scope_status_v11r2", "start_real_execution_v11r2",
           "append_contact_guard_v11r2", "append_terminal_state_v11r2"]
