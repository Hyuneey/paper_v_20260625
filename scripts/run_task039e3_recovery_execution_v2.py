#!/usr/bin/env python3
"""Future R2 V2 entry point for the R1C-remediated recovery path.

R1C never invokes this runner.  A separately supplied R2 V2 authorization and
R1C source manifest are validated outside the Git worktree.  The single
credential lookup is dependency-ordered after every public pre-contact guard.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any

from paperworks.v6.task039e3_recovery_authorization_v2 import (
    HISTORICAL_CAPABILITY_RECEIPT_HASH,
    HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
    run_ordered_precontact_guards_v2,
)
from paperworks.v6.task039e3_recovery_execution_v2 import (
    collect_git_execution_state_v2,
    load_prior_authority_state_v2,
    run_capability_then_science_v2,
)
from paperworks.v6.task039e3_recovery_live_transport_v2 import (
    RecoveryLiveOpenAIChatCompletionsTransportV2,
)
from paperworks.v6.task039e3_scientific_execution_v1 import (
    validate_public_preflight_v1,
)


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path.name}")
    return value


def _credential_loader() -> str:
    """The sole future credential lookup, reached only after all guards."""

    value = os.environ.get("OPENAI_API_KEY")
    if not value:
        raise ValueError("blocked_task039e3_credential_unavailable")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", required=True)
    parser.add_argument("--r2-authorization", required=True)
    parser.add_argument("--r1c-source-manifest", required=True)
    parser.add_argument("--e1-private-root", required=True)
    parser.add_argument("--historical-e3-private-root", required=True)
    parser.add_argument("--recovery-e3-private-root", required=True)
    args = parser.parse_args()

    repository = Path(args.repository_root).resolve(strict=True)
    authorization = _load_object(Path(args.r2_authorization).resolve(strict=True))
    source_manifest = _load_object(Path(args.r1c_source_manifest).resolve(strict=True))
    bootstrap = run_ordered_precontact_guards_v2(
        authorization_document=authorization,
        prior_authority_state_loader=lambda: load_prior_authority_state_v2(repository),
        git_state_loader=lambda: collect_git_execution_state_v2(
            repository, source_manifest
        ),
        repository_root=repository,
        e1_private_value=args.e1_private_root,
        historical_e3_private_value=args.historical_e3_private_root,
        recovery_e3_private_value=args.recovery_e3_private_root,
        historical_capability_receipt_hash=HISTORICAL_CAPABILITY_RECEIPT_HASH,
        historical_provider_ledger_head_hash=HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
        scientific_preflight_loader=lambda: validate_public_preflight_v1(repository),
        credential_loader=_credential_loader,
    )

    transport = RecoveryLiveOpenAIChatCompletionsTransportV2(
        api_key=bootstrap.credential
    )
    schedule = tuple(bootstrap.scientific_preflight["schedule"]["relation_identities"])
    result = run_capability_then_science_v2(
        execution_commit=bootstrap.git_state.head_commit,
        source_manifest_hash=bootstrap.git_state.source_manifest_hash,
        r2_authorization_hash=bootstrap.authorization.self_hash,
        e1_private_root=bootstrap.private_roots.e1_private_root,
        recovery_private_root=bootstrap.private_roots.recovery_e3_private_root,
        public_cohort=bootstrap.scientific_preflight["cohort"],
        relation_identities=schedule,
        transport=transport,
    )
    status = str(result["status"])
    print(json.dumps({"status": status}, sort_keys=True))
    if status == "blocked_task039e3_recovery_capability_gate":
        return 4
    if status.startswith("failed_"):
        return 5
    return 0


if __name__ == "__main__":
    sys.exit(main())
