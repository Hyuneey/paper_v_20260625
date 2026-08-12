#!/usr/bin/env python3
"""Offline-only R2R recovery entrypoint frozen for future independent audit.

This remediation task creates no real R2R authorization and grants no live
execution authority.  The only currently reachable command is a deterministic
offline contract self-check.  A later audited authorization task must add the
external live authority path; this file deliberately has no credential loader
or provider invocation.
"""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from paperworks.v6.task039e3_r2r_authorization_v1 import TASK_ID
from paperworks.v6.task039e3_r2r_execution_v1 import (
    EXPECTED_EMPTY_LEDGER_KINDS,
    RECOVERY_EXECUTION_MODE,
    R2R_ARM_RUNNERS_V1,
)
from paperworks.v6.task039e3_r2r_live_transport_v1 import (
    HTTP_ERROR_BODY_READ_LIMIT_BYTES,
    MAXIMUM_RETAINED_HTTP_ERROR_BODY_BYTES,
    R2RLiveOpenAIChatCompletionsTransportV1,
)
from paperworks.v6.task039e3_r2r_request_contract_v1 import (
    DIRECT_NUMBER_SCHEMA_POLICY,
    RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH,
    assert_r2r_request_contract_v1,
)


OFFLINE_ONLY_STATUS = "r2r_request_contract_ready_for_independent_audit"


def offline_self_check_v1() -> dict[str, object]:
    """Return sanitized deterministic implementation facts without I/O."""

    assert_r2r_request_contract_v1()
    if R2R_ARM_RUNNERS_V1.t0 is R2R_ARM_RUNNERS_V1.t1:
        raise ValueError("R2R arm identities differ")
    if not issubclass(R2RLiveOpenAIChatCompletionsTransportV1, object):
        raise ValueError("R2R transport type unavailable")
    return {
        "task_id": TASK_ID,
        "status": OFFLINE_ONLY_STATUS,
        "recovery_execution_mode": RECOVERY_EXECUTION_MODE,
        "recovery_main_provider_schema_v2_hash": (
            RECOVERY_MAIN_PROVIDER_SCHEMA_V2_HASH
        ),
        "direct_number_schema_policy": DIRECT_NUMBER_SCHEMA_POLICY,
        "fresh_ledger_kinds": list(EXPECTED_EMPTY_LEDGER_KINDS),
        "maximum_retained_http_error_body_bytes": (
            MAXIMUM_RETAINED_HTTP_ERROR_BODY_BYTES
        ),
        "maximum_http_error_body_read_bytes": HTTP_ERROR_BODY_READ_LIMIT_BYTES,
        "provider_contact_authorized": False,
        "capability_probe_authorized": False,
        "scientific_execution_authorized": False,
        "resume_authorized": False,
        "rule_v2_authorized": False,
        "runtime_authority": False,
        "utility_evaluation_authorized": False,
        "winner_selected": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline-self-check", action="store_true", required=True)
    args = parser.parse_args(argv)
    if args.offline_self_check:
        print(json.dumps(offline_self_check_v1(), sort_keys=True, separators=(",", ":")))
        return 0
    raise ValueError("R2R live execution authority is unavailable")


if __name__ == "__main__":
    raise SystemExit(main())
