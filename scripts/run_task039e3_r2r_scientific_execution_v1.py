#!/usr/bin/env python3
"""Future-live R2R recovery entrypoint with an offline authority boundary.

No real R2R authorization exists in this task, so only ``--offline-self-check``
is invoked here.  The normal argument surface and dependency-ordered live path
are present for a later independent audit and authorization.  Tests inject all
effects; imports and self-checks perform no environment or provider access.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
from typing import Callable, Sequence

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
from paperworks.v6.task039e3_r2r_precontact_v1 import (
    R2RLivePathDependenciesV1,
    R2RLivePathResultV1,
    run_r2r_live_execution_path_v1,
)
from paperworks.v6.task039e3_r2r_failure_finalizer_v1 import (
    DOUBLE_FAULT_CLASSIFICATION,
    TASK039E3R2RFailureReceiptDoubleFault,
    TASK039E3R2RGuardedExecutionFailure,
)
from paperworks.v6.task039e3_r2r_live_execution_v1 import (
    build_r2r_live_dependencies_v1,
)


OFFLINE_ONLY_STATUS = "r2r_request_contract_ready_for_independent_audit"


def _credential_loader_v1() -> str:
    """The sole future credential lookup, reached only after all guards."""

    value = os.environ.get("OPENAI_API_KEY")
    if not value:
        raise ValueError("blocked_task039e3_r2r_credential_unavailable")
    return value


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


def _validate_live_argument_paths_v1(args: argparse.Namespace) -> None:
    names = (
        "repository_root",
        "r2r_authorization",
        "r2r_source_manifest",
        "r2r_audit_receipt",
        "capability_receipt",
        "capability_ledger_root",
        "e1_private_root",
        "recovery_private_root",
        "public_output_root",
    )
    missing = tuple(name for name in names if getattr(args, name) is None)
    if missing:
        raise ValueError(f"R2R live arguments are incomplete: {','.join(missing)}")
    for name in names:
        if not Path(getattr(args, name)).is_absolute():
            raise ValueError(f"R2R live argument must be absolute: {name}")


def run_future_live_path_v1(
    dependencies: R2RLivePathDependenciesV1,
) -> R2RLivePathResultV1:
    """Expose the audited dependency graph without constructing authority."""

    return run_r2r_live_execution_path_v1(dependencies)


def main(
    argv: Sequence[str] | None = None,
    *,
    live_dependencies_factory: Callable[
        [argparse.Namespace], R2RLivePathDependenciesV1
    ] | None = None,
) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline-self-check", action="store_true")
    parser.add_argument("--repository-root")
    parser.add_argument("--r2r-authorization")
    parser.add_argument("--r2r-source-manifest")
    parser.add_argument("--r2r-audit-receipt")
    parser.add_argument("--capability-receipt")
    parser.add_argument("--capability-ledger-root")
    parser.add_argument("--e1-private-root")
    parser.add_argument("--recovery-private-root")
    parser.add_argument("--public-output-root")
    args = parser.parse_args(argv)
    if args.offline_self_check:
        print(json.dumps(offline_self_check_v1(), sort_keys=True, separators=(",", ":")))
        return 0
    _validate_live_argument_paths_v1(args)
    if live_dependencies_factory is None:
        live_dependencies_factory = build_r2r_live_dependencies_v1
    dependencies = replace(
        live_dependencies_factory(args), credential_loader=_credential_loader_v1
    )
    try:
        result = run_future_live_path_v1(dependencies)
    except TASK039E3R2RGuardedExecutionFailure as failure:
        print(json.dumps({"status": failure.failure_receipt["status"]}, sort_keys=True))
        return 5
    except TASK039E3R2RFailureReceiptDoubleFault:
        print(json.dumps({"status": DOUBLE_FAULT_CLASSIFICATION}, sort_keys=True))
        return 6
    print(json.dumps(result.terminal_result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
