"""Single-writer append-only EXP-03 custody and exact-host Responses transport.

Tests inject transport. Imports never read credentials or contact a provider.
No automatic retry/restart: an interrupted run requires explicit reconciliation.
"""
from __future__ import annotations

from decimal import Decimal
import hashlib
import http.client
import json
import os
from pathlib import Path
import time
from typing import Any, Callable

from .exp03_live_contract_v1 import (
    MODEL, INPUT_CAP, OUTPUT_CAP, PROMPT, schema, h, cost, budget_guard, input_upper_bound,
    validate_projection_content, request_document, feedback_for,
)
from .private_vault_v1 import publish_private_bytes_v1, validate_private_path_v1


def encoded(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()


class ProviderCustodyStop(ValueError):
    """Safe, constant issue code only; never interpolate provider bodies."""


def exact_request_guard(request: dict[str, Any]) -> None:
    constants = {
        "model": MODEL, "instructions": PROMPT, "reasoning": {"effort": "none"},
        "temperature": 0.7, "top_p": 1.0, "max_output_tokens": OUTPUT_CAP,
        "store": False, "service_tier": "default", "tools": [], "stream": False,
        "text": {"format": {"type": "json_schema", "name": "exp03_rule_v1", "strict": True, "schema": schema()}},
    }
    if set(request) != {*constants, "input"} or any(encoded(request[k]) != encoded(v) for k, v in constants.items()):
        raise ProviderCustodyStop("REQUEST_POLICY_MISMATCH")
    if type(request["input"]) is not str or input_upper_bound(request) > INPUT_CAP:
        raise ProviderCustodyStop("REQUEST_INPUT_CAP")
    user = json.loads(request["input"])
    if type(user) is not dict or set(user) not in ({"relation"}, {"relation", "feedback"}):
        raise ProviderCustodyStop("EGRESS_CLOSED_INPUT")
    validate_projection_content(user["relation"])
    if "feedback" in user:
        fb = user["feedback"]
        if type(fb) is not dict or set(fb) != {"action", "issue_codes", "same_corpus_numeric_reference_ids"}:
            raise ProviderCustodyStop("EGRESS_CLOSED_FEEDBACK")
        if fb["action"] not in {"revise", "retrieve"} or fb["issue_codes"] != ["NUMERIC_REFERENCE_MISMATCH"]:
            raise ProviderCustodyStop("EGRESS_FEEDBACK_CODES")
        if fb["same_corpus_numeric_reference_ids"] != (user["relation"]["numeric_reference_ids"] if fb["action"] == "retrieve" else []):
            raise ProviderCustodyStop("EGRESS_FOREIGN_RETRIEVAL")


_PERMIT_KEY = object()


class _DispatchPermit:
    def __init__(self, key, ledger_path: Path, reservation: dict[str, Any]):
        if key is not _PERMIT_KEY:
            raise ProviderCustodyStop("RECEIPT_FIRST_PERMIT_REQUIRED")
        self.path, self.reservation, self.used = ledger_path, reservation, False

    def consume(self, request: dict[str, Any]) -> None:
        if self.used or replay_ledger(self.path)[-1] != self.reservation:
            raise ProviderCustodyStop("STALE_OR_CONSUMED_DISPATCH_PERMIT")
        payload = self.reservation["payload"]
        if self.reservation["kind"] != "CALL_RESERVED" or payload["request_hash"] != hashlib.sha256(encoded(request)).hexdigest():
            raise ProviderCustodyStop("DISPATCH_RESERVATION_MISMATCH")
        # A second object/process cannot resend a consumed slot after a crash.
        with (self.path.parent / (payload["slot"] + "-dispatch.once")).open("xb") as marker:
            marker.write(encoded({"reservation_hash": self.reservation["self_hash"]}))
            marker.flush()
            os.fsync(marker.fileno())
        self.used = True


def official_transport(request: dict[str, Any], *, authorization_ticket=None) -> tuple[int, bytes, float]:
    """One HTTPS attempt, no proxy/redirect/retry; errors have no retained body."""
    exact_request_guard(request)
    if type(authorization_ticket) is not _DispatchPermit:
        raise ProviderCustodyStop("RECEIPT_FIRST_PERMIT_REQUIRED")
    authorization_ticket.consume(request)
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ProviderCustodyStop("CREDENTIAL_UNAVAILABLE")
    connection = http.client.HTTPSConnection("api.openai.com", timeout=60)
    started = time.monotonic()
    try:
        connection.request("POST", "/v1/responses", body=encoded(request), headers={
            "Authorization": "Bearer " + key, "Content-Type": "application/json",
        })
        response = connection.getresponse()
        status = response.status
        raw = response.read(1048577) if status == 200 else b""
        if len(raw) > 1048576:
            raise ProviderCustodyStop("RESPONSE_SIZE_LIMIT")
        return status, raw, (time.monotonic() - started) * 1000
    except (OSError, http.client.HTTPException):
        raise ProviderCustodyStop("UNCERTAIN_PROVIDER_TRANSPORT") from None
    finally:
        connection.close()
        key = None


def replay_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    raw = path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        raise ProviderCustodyStop("PARTIAL_LEDGER_APPEND")
    rows = []
    previous = "0" * 64
    for line in raw.splitlines():
        row = json.loads(line)
        body = {k: v for k, v in row.items() if k != "self_hash"}
        if row["self_hash"] != h(body) or row["previous_hash"] != previous or row["sequence"] != len(rows) + 1:
            raise ProviderCustodyStop("LEDGER_CHAIN_MISMATCH")
        previous = row["self_hash"]
        rows.append(row)
    return rows


class SingleWriterLedger:
    def __init__(self, root: Path, *, allowed_root: Path, contract_hash: str,
                 schedule: list[tuple[str, str, int]], projections: dict[str, dict[str, Any]],
                 authorization: Any, transport: Callable = official_transport):
        self.root = validate_private_path_v1(root, allowed_root=allowed_root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "CALL_OUTPUT_COST_LATENCY_LEDGER.jsonl"
        self.contract_hash = contract_hash
        self.schedule = schedule
        self.transport = transport
        self.projections = json.loads(encoded(projections))
        self.authorization = authorization
        self.tip, self.sequence = "0" * 64, 0
        # Retained lock marks ownership and disallows automatic restart/resend.
        with (self.root / "SINGLE_WRITER_LOCK.json").open("xb") as stream:
            stream.write(encoded({"contract_hash": contract_hash, "pid": os.getpid()}))
            stream.flush()
            os.fsync(stream.fileno())
        if self.path.exists():
            raise ProviderCustodyStop("EXISTING_RUN_REQUIRES_RECONCILIATION")
        self.calls, self.input_tokens, self.output_tokens = 0, 0, 0
        self.usd = Decimal(0)
        self.outstanding = None
        self.history: dict[tuple[str, str, int], list[dict[str, Any]]] = {}
        self.completed: list[tuple[str, str, int]] = []
        self.append("RUN_STARTED", {"scientific_concurrency": 1})

    def append(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        rows = self.checked_rows()
        body = {"sequence": len(rows) + 1, "previous_hash": rows[-1]["self_hash"] if rows else "0" * 64,
                "contract_hash": self.contract_hash, "kind": kind, "payload": payload}
        row = {**body, "self_hash": h(body)}
        with self.path.open("ab") as stream:
            stream.write(encoded(row) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        if replay_ledger(self.path)[-1] != row:
            raise ProviderCustodyStop("DURABLE_LEDGER_REPLAY_FAILED")
        self.tip, self.sequence = row["self_hash"], row["sequence"]
        return row

    def checked_rows(self) -> list[dict[str, Any]]:
        rows = replay_ledger(self.path)
        if len(rows) != self.sequence or (rows[-1]["self_hash"] if rows else "0" * 64) != self.tip:
            raise ProviderCustodyStop("LEDGER_ROLLBACK_OR_FOREIGN_APPEND")
        return rows

    def call(self, key: tuple[str, str, int], index: int, request: dict[str, Any]) -> dict[str, Any]:
        exact_request_guard(request)
        self.checked_rows()
        if self.outstanding is not None or key not in self.schedule or len(self.completed) >= len(self.schedule):
            raise ProviderCustodyStop("OUTSTANDING_OR_FOREIGN_SLOT")
        if key != self.schedule[len(self.completed)]:
            raise ProviderCustodyStop("SCHEDULE_ORDER_MISMATCH")
        prior = self.history.get(key, [])
        expected_feedback = prior[-1].get("next_feedback") if prior and key[1] == "T2" else None
        expected_request = request_document(self.projections[key[0]], self.authorization, expected_feedback)
        if encoded(request) != encoded(expected_request):
            raise ProviderCustodyStop("REQUEST_NOT_FROZEN_SCHEDULE_PROJECTION")
        if index != len(prior) + 1 or index > (1 if key[1] == "T1" else 3) or key[1] == "T0":
            raise ProviderCustodyStop("FOURTH_OR_DUPLICATE_CALL")
        if prior and key[1] == "T2" and not prior[-1].get("continue_t2", False):
            raise ProviderCustodyStop("T2_CALL_AFTER_TERMINAL")
        next_cost = self.usd + cost(INPUT_CAP, OUTPUT_CAP)
        budget_guard(self.calls + 1, self.input_tokens + INPUT_CAP, self.output_tokens + OUTPUT_CAP, next_cost)
        slot = f"{len(self.completed):04d}-{index}"
        request_hash = hashlib.sha256(encoded(request)).hexdigest()
        publish_private_bytes_v1(self.root / (slot + "-request.json"), encoded(request))
        reservation = self.append("CALL_RESERVED", {"slot": slot, "key": list(key), "index": index,
            "request_hash": request_hash, "input_token_upper_bound": input_upper_bound(request),
            "maximum_input_liability": INPUT_CAP, "maximum_output_liability": OUTPUT_CAP,
            "maximum_usd_liability": str(cost(INPUT_CAP, OUTPUT_CAP))})
        self.calls += 1
        self.outstanding = slot
        try:
            if self.transport is official_transport:
                status, raw, latency = self.transport(request, authorization_ticket=_DispatchPermit(_PERMIT_KEY, self.path, reservation))
            else:
                status, raw, latency = self.transport(request)
            if status != 200:
                raise ProviderCustodyStop("PROVIDER_HTTP_" + str(status))
            publish_private_bytes_v1(self.root / (slot + "-response.json"), raw)
            response = json.loads(raw)
            usage = response.get("usage")
            if response.get("model") != MODEL or type(usage) is not dict:
                raise ProviderCustodyStop("RESPONSE_MODEL_OR_USAGE_MISMATCH")
            it, ot = usage.get("input_tokens"), usage.get("output_tokens")
            if any(type(n) is not int or n < 0 for n in (it, ot)) or it > INPUT_CAP or ot > OUTPUT_CAP or usage.get("total_tokens") != it + ot:
                raise ProviderCustodyStop("PROVIDER_USAGE_CAP_OR_SCHEMA")
            if type(latency) not in (int, float) or not (0 <= latency < float("inf")):
                raise ProviderCustodyStop("LATENCY_INVALID")
            self.input_tokens += it
            self.output_tokens += ot
            self.usd += cost(it, ot)
            budget_guard(self.calls, self.input_tokens, self.output_tokens, self.usd)
            response_hash = hashlib.sha256(raw).hexdigest()
            result = {"slot": slot, "key": list(key), "index": index, "request_hash": request_hash,
                      "response_hash": response_hash, "input_tokens": it, "output_tokens": ot,
                      "cost_usd": str(cost(it, ot)), "latency_ms": latency,
                      "model": MODEL, "response_status": response.get("status")}
            self.append("CALL_SETTLED", result)
            self.outstanding = None
            self.history.setdefault(key, []).append(result)
            return {**result, "response": response}
        except Exception as error:
            code = str(error) if isinstance(error, ProviderCustodyStop) else "PROVIDER_RESPONSE_CUSTODY_OR_PARSE_FAILURE"
            self.append("CALL_UNRESOLVED_STOP", {"slot": slot, "issue_code": code,
                "maximum_input_liability": INPUT_CAP, "maximum_output_liability": OUTPUT_CAP,
                "maximum_usd_liability": str(cost(INPUT_CAP, OUTPUT_CAP)), "automatic_resend": False})
            raise ProviderCustodyStop(code) from None

    def verdict(self, key: tuple[str, str, int], verdict: dict[str, Any], *, continue_t2: bool) -> None:
        if not self.history.get(key):
            raise ProviderCustodyStop("VERDICT_WITHOUT_CALL")
        if continue_t2 and (key[1] != "T2" or verdict["status"] != "VERIFIER_REJECTION" or len(self.history[key]) >= 3):
            raise ProviderCustodyStop("INVALID_T2_CONTINUATION")
        self.history[key][-1]["continue_t2"] = continue_t2
        if continue_t2:
            retrieved = any(r.get("next_feedback", {}).get("action") == "retrieve" for r in self.history[key][:-1])
            self.history[key][-1]["next_feedback"] = feedback_for(verdict, retrieved, self.projections[key[0]])
        self.append("VERIFIER_CONTROLLER", {"key": list(key), "verdict": verdict, "continue_t2": continue_t2})

    def terminal(self, key: tuple[str, str, int], document: dict[str, Any]) -> None:
        if self.outstanding is not None or key != self.schedule[len(self.completed)]:
            raise ProviderCustodyStop("TERMINAL_ORDER_OR_CUSTODY")
        actual = len(self.history.get(key, []))
        if (key[1] == "T0" and actual != 0) or (key[1] == "T1" and actual != 1) or (key[1] == "T1-B" and actual != 3) or (key[1] == "T2" and not 1 <= actual <= 3):
            raise ProviderCustodyStop("TERMINAL_CALL_COUNT")
        publish_private_bytes_v1(self.root / f"terminal-{len(self.completed):04d}.json", encoded(document))
        self.append("TERMINAL_FROZEN", {"key": list(key), "terminal_hash": h(document), "outcome": document["outcome"]})
        self.completed.append(key)
