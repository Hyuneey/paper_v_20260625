"""Single approved snapshot metadata GET; never a generation or data request.

No redirects, proxies, alternate hosts, retries, raw error bodies, or secret
logging. A durable reservation precedes credential use/contact. An existing
reservation prevents repeat contact, including after an uncertain crash.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import http.client
import json
import os
from pathlib import Path
import time
from typing import Any

MODEL = "gpt-5.4-mini-2026-03-17"
HOST = "api.openai.com"
ENDPOINT = "/v1/models/" + MODEL
BASE = "research_control_center/validation_v2/exp03"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()


def persist_new(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    doc = dict(payload)
    doc["self_hash"] = hashlib.sha256(canonical(doc)).hexdigest()
    raw = canonical(doc) + b"\n"
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    if path.read_bytes() != raw:
        raise ValueError("PERSISTENCE_REPLAY_FAILED")
    return doc


def check_approval(value: dict[str, Any]) -> None:
    expected = {
        "decision": "APPROVED_WITH_FIXED_SNAPSHOT", "model_snapshot": MODEL,
        "maximum_generation_calls": 819, "scientific_concurrency": 1,
        "maximum_input_tokens": 3354624, "maximum_output_tokens": 1677312,
        "maximum_total_tokens": 5031936, "maximum_standard_api_usd": "10.07",
        "moving_alias_allowed": False, "fallback_allowed": False,
    }
    if any(type(value.get(k)) is not type(v) or value[k] != v for k, v in expected.items()):
        raise ValueError("APPROVAL_MISMATCH")


def run(root: Path) -> dict[str, Any]:
    approval_path = root / BASE / "DG03_FIXED_SNAPSHOT_APPROVAL_V1.json"
    approval_bytes = approval_path.read_bytes()
    check_approval(json.loads(approval_bytes))
    reservation_path = root / BASE / "MODEL_ACCESS_RESERVATION_V1.json"
    result_path = root / BASE / "MODEL_ACCESS_RECEIPT_V1.json"
    if reservation_path.exists() or result_path.exists():
        raise ValueError("EXISTING_METADATA_CONTACT_NOT_REPEATED")
    reservation = persist_new(reservation_path, {
        "schema": "paperworks.exp03.metadata_contact_reservation_v1",
        "approval_sha256": hashlib.sha256(approval_bytes).hexdigest(),
        "method": "GET", "host": HOST, "endpoint": ENDPOINT,
        "body": None, "maximum_attempts": 1, "redirects_allowed": False,
        "generation_calls": 0, "scientific_data_sent": False,
        "created_utc": datetime.now(timezone.utc).isoformat(),
    })
    status, http_status, attempts = "BLOCKED_CREDENTIAL_UNAVAILABLE", None, 0
    matched = False
    started = time.monotonic()
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        connection = http.client.HTTPSConnection(HOST, timeout=30)
        try:
            attempts = 1
            connection.request("GET", ENDPOINT, headers={"Authorization": "Bearer " + key})
            response = connection.getresponse()
            http_status = response.status
            if http_status == 200:
                raw = response.read(65537)
                if len(raw) > 65536:
                    status = "BLOCKED_MODEL_METADATA_OVERSIZE"
                else:
                    document = json.loads(raw)
                    matched = document.get("id") == MODEL and document.get("object") == "model"
                    status = "MODEL_METADATA_ACCESS_PASS" if matched else "BLOCKED_MODEL_IDENTITY_MISMATCH"
            else:
                # Never read an error body: it may echo a credential or request.
                status = {
                    401: "BLOCKED_PROVIDER_AUTHENTICATION",
                    403: "BLOCKED_PROVIDER_PERMISSION",
                    404: "BLOCKED_EXACT_SNAPSHOT_ACCESS",
                    429: "BLOCKED_PROVIDER_RATE_OR_QUOTA",
                }.get(http_status, "BLOCKED_PROVIDER_METADATA_HTTP")
        except (OSError, http.client.HTTPException):
            status = "BLOCKED_PROVIDER_METADATA_EGRESS"
        except (ValueError, TypeError, AttributeError):
            status = "BLOCKED_MODEL_METADATA_PARSE"
        finally:
            connection.close()
            key = None
    return persist_new(result_path, {
        "schema": "paperworks.exp03.model_access_receipt_v1",
        "reservation_hash": reservation["self_hash"], "status": status,
        "http_status": http_status, "metadata_http_attempts": attempts,
        "model_snapshot": MODEL, "exact_model_id_matched": matched,
        "latency_ms": round((time.monotonic() - started) * 1000, 3),
        "generation_calls": 0, "generation_capability_verified": False,
        "input_tokens": 0, "output_tokens": 0, "generation_cost_usd": "0",
        "scientific_data_sent": False, "credentials_persisted": False,
        "raw_error_body_read": False, "private_exposures": 0,
        "test1_accesses": 0, "test2_accesses": 0, "heldout_accesses": 0,
    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-approved-metadata-get", action="store_true", required=True)
    parser.parse_args()
    try:
        result = run(Path(__file__).resolve().parents[1])
        print(json.dumps({k: result[k] for k in ("status", "http_status", "generation_calls", "self_hash")}))
        if result["status"] != "MODEL_METADATA_ACCESS_PASS":
            raise SystemExit(2)
    except Exception:
        # Do not print paths, headers, credentials, response bodies, or traceback.
        print('{"status":"BLOCKED_METADATA_PREFLIGHT_LOCAL_GUARD"}')
        raise SystemExit(1)
