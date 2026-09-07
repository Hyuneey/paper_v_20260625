"""Release-scoped, durable, fail-closed one-time execution ledger."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

from .dg05_production_chain_v11 import canonical_bytes, digest, self_hashed


class DG05V11R2ExecutionLedgerError(ValueError):
    pass


def execution_scope_id_v11r2(*, release_hash: str, final_closure_hash: str, execution_binding_hash: str) -> str:
    return digest({"release_hash": release_hash, "final_closure_hash": final_closure_hash,
                   "execution_binding_hash": execution_binding_hash})


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
    return self_hashed({"schema": "dg05_v11r2_execution_ledger_state_v1", "state": state,
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
    path = ledger_root / scope / "REAL_EXECUTION_STARTED.json"
    state = _document(state="REAL_EXECUTION_STARTED", scope_id=scope, release_hash=release_hash,
                      final_closure_hash=final_closure_hash, execution_binding_hash=execution_binding_hash,
                      preflight_receipt_hash=preflight_receipt_hash, physical_custody_hash=physical_custody_hash,
                      output_namespace=output_namespace, predecessor_hash=None)
    _durable_exclusive_json(path, state)
    return state


def append_contact_guard_v11r2(*, ledger_root: Path, start_state: Mapping[str, Any]) -> dict[str, Any]:
    if start_state.get("state") != "REAL_EXECUTION_STARTED":
        raise DG05V11R2ExecutionLedgerError("V11R2_START_STATE_REQUIRED")
    state = _document(state="SCIENTIFIC_CONTACT_GUARD_COMMITTED", scope_id=start_state["execution_scope_id"],
                      release_hash=start_state["release_hash"], final_closure_hash=start_state["final_closure_hash"],
                      execution_binding_hash=start_state["execution_binding_hash"], preflight_receipt_hash=start_state["preflight_receipt_hash"],
                      physical_custody_hash=start_state["physical_custody_hash"], output_namespace=start_state["output_namespace"],
                      predecessor_hash=start_state["self_hash"])
    _durable_exclusive_json(ledger_root / state["execution_scope_id"] / "SCIENTIFIC_CONTACT_GUARD_COMMITTED.json", state)
    return state


def append_terminal_state_v11r2(*, ledger_root: Path, predecessor: Mapping[str, Any], state_name: str) -> dict[str, Any]:
    if state_name not in {"PREDICTIONS_FROZEN", "METRICS_FROZEN", "TERMINAL_COMPLETE", "PRECONTACT_ABORTED", "TERMINAL_FAILED_AFTER_SCIENTIFIC_CONTACT"}:
        raise DG05V11R2ExecutionLedgerError("V11R2_LEDGER_STATE_REQUIRED")
    state = _document(state=state_name, scope_id=predecessor["execution_scope_id"], release_hash=predecessor["release_hash"],
                      final_closure_hash=predecessor["final_closure_hash"], execution_binding_hash=predecessor["execution_binding_hash"],
                      preflight_receipt_hash=predecessor["preflight_receipt_hash"], physical_custody_hash=predecessor["physical_custody_hash"],
                      output_namespace=predecessor["output_namespace"], predecessor_hash=predecessor["self_hash"])
    _durable_exclusive_json(ledger_root / state["execution_scope_id"] / f"{state_name}.json", state)
    return state


__all__ = ["DG05V11R2ExecutionLedgerError", "execution_scope_id_v11r2", "start_real_execution_v11r2",
           "append_contact_guard_v11r2", "append_terminal_state_v11r2"]
