#!/usr/bin/env python3
"""Future R2 runner for the frozen TASK-039E3 recovery implementation.

R1B does not invoke this script.  The credential lookup is dependency-ordered
after authorization, Git/source, historical-binding, and private-root guards.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any

from paperworks.v6.task039e3_live_transport_v1 import (
    LiveOpenAIChatCompletionsTransportV1,
)
from paperworks.v6.task039e3_recovery_authorization_v1 import (
    HISTORICAL_CAPABILITY_RECEIPT_HASH,
    HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
    run_ordered_precontact_guards_v1,
)
from paperworks.v6.task039e3_recovery_execution_v1 import (
    build_recovery_capability_receipt_v1,
    build_recovery_run_identity_v1,
    collect_git_execution_state_v1,
    execute_recovery_probe_v1,
    load_prior_authority_state_v1,
    run_frozen_science_after_recovery_gate_v1,
    run_recovery_capability_phase_v1,
    write_recovery_capability_private_custody_v1,
    write_recovery_public_artifacts_v1,
)
from paperworks.v6.task039e3_recovery_serialization_v1 import (
    write_public_artifact_atomic_v1,
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
    """The sole credential lookup; callers may reach it only after all guards."""

    value = os.environ.get("OPENAI_API_KEY")
    if not value:
        raise ValueError("blocked_task039e3_credential_unavailable")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", required=True)
    parser.add_argument("--r2-authorization", required=True)
    parser.add_argument("--r1b-source-manifest", required=True)
    parser.add_argument("--e1-private-root", required=True)
    parser.add_argument("--historical-e3-private-root", required=True)
    parser.add_argument("--recovery-e3-private-root", required=True)
    args = parser.parse_args()

    repository = Path(args.repository_root).resolve(strict=True)
    authorization = _load_object(Path(args.r2_authorization).resolve(strict=True))
    source_manifest = _load_object(Path(args.r1b_source_manifest).resolve(strict=True))
    state: dict[str, Any] = {}

    def precontact_guard_runner() -> Any:
        return run_ordered_precontact_guards_v1(
            authorization_document=authorization,
            prior_authority_state_loader=lambda: load_prior_authority_state_v1(
                repository
            ),
            git_state_loader=lambda: collect_git_execution_state_v1(
                repository, source_manifest
            ),
            repository_root=repository,
            e1_private_value=args.e1_private_root,
            historical_e3_private_value=args.historical_e3_private_root,
            recovery_e3_private_value=args.recovery_e3_private_root,
            historical_capability_receipt_hash=HISTORICAL_CAPABILITY_RECEIPT_HASH,
            historical_provider_ledger_head_hash=HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
            scientific_preflight_loader=lambda: validate_public_preflight_v1(
                repository
            ),
            credential_loader=_credential_loader,
        )

    def probe_executor(bootstrap: Any) -> Any:
        transport = LiveOpenAIChatCompletionsTransportV1(api_key=bootstrap.credential)
        execution = execute_recovery_probe_v1(transport)
        state["transport"] = transport
        state["execution"] = execution
        return execution.gate

    def custody_writer(_gate: Any) -> str:
        bootstrap = state.get("bootstrap")
        execution = state["execution"]
        git_state = collect_git_execution_state_v1(repository, source_manifest)
        run_identity = build_recovery_run_identity_v1(
            r1b_commit=git_state.head_commit,
            source_manifest_hash=git_state.source_manifest_hash,
            r2_authorization_hash=authorization["self_hash"],
        )
        transport = state["transport"]
        fingerprint = (
            transport.attempt_custody[-1].system_fingerprint
            if transport.attempt_custody
            else None
        )
        private_root = Path(args.recovery_e3_private_root).resolve(strict=True)
        custody = write_recovery_capability_private_custody_v1(
            recovery_private_root=private_root,
            run_identity=run_identity,
            execution=execution,
        )
        state["capability_custody"] = custody
        receipt = build_recovery_capability_receipt_v1(
            run_identity=run_identity,
            execution_commit=git_state.head_commit,
            source_manifest_hash=git_state.source_manifest_hash,
            r2_authorization_hash=authorization["self_hash"],
            execution=execution,
            custody_binding=custody,
            system_fingerprint=fingerprint,
        )
        state["capability_receipt"] = receipt
        written = write_public_artifact_atomic_v1(
            private_root / "TASK039E3_RECOVERY_CAPABILITY_RECEIPT.json", receipt
        )
        return written["artifact_hash"]

    def e1_gate_loader(bootstrap: Any) -> Any:
        # The frozen scientific executor performs the actual ledger read.  This
        # callback opens the gate only after the receipt has been durably frozen.
        return {"bootstrap": bootstrap, "preflight": bootstrap.scientific_preflight}

    def guarded() -> Any:
        bootstrap = precontact_guard_runner()
        state["bootstrap"] = bootstrap
        return bootstrap

    phase = run_recovery_capability_phase_v1(
        precontact_guard_runner=guarded,
        probe_executor=probe_executor,
        custody_writer=custody_writer,
        e1_loader=e1_gate_loader,
    )
    if phase.gate_status == "BLOCK":
        write_recovery_public_artifacts_v1(
            repository, {"capability": state["capability_receipt"]}
        )
        print(json.dumps({"status": "blocked_task039e3_recovery_capability_gate"}))
        return 4

    bootstrap = phase.bootstrap
    scientific_private_root = bootstrap.private_roots.recovery_e3_private_root / "scientific"
    scientific_private_root.mkdir(exist_ok=False)
    artifacts = run_frozen_science_after_recovery_gate_v1(
        repository_root=repository,
        execution_commit=bootstrap.git_state.head_commit,
        e1_private_root=bootstrap.private_roots.e1_private_root,
        recovery_private_root=scientific_private_root,
        live_transport=state["transport"],
        preflight=bootstrap.scientific_preflight,
        recovery_execution=state["execution"],
        recovery_capability_receipt=state["capability_receipt"],
        recovery_capability_custody=state["capability_custody"],
        source_manifest=source_manifest,
    )
    write_recovery_public_artifacts_v1(repository, artifacts)
    status = artifacts.get("receipt", artifacts.get("failure", {})).get(
        "status", "failed_task039e3_scientific_execution"
    )
    print(json.dumps({"status": status}, sort_keys=True))
    return 0 if "receipt" in artifacts else 5


if __name__ == "__main__":
    sys.exit(main())
