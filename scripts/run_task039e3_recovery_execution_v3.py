#!/usr/bin/env python3
"""Future R2 entry point for the final-audit-bound V3 recovery path.

R1D2 never invokes this runner.  Its external authorization, final audit
receipt, source manifest, and four protected result roots must all validate
before the sole credential lookup can be reached.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_recovery_authorization_v3 import (
    HISTORICAL_CAPABILITY_RECEIPT_HASH,
    HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
    load_audit_receipt_git_blob_v3,
    run_ordered_precontact_guards_v3,
)
from paperworks.v6.task039e3_recovery_execution_v3 import (
    TASK039E3RecoveryFailureReceiptDoubleFaultV3Error,
    TASK039E3RecoveryGuardedExecutionFailureV3Error,
    collect_git_execution_state_v3,
    load_prior_authority_state_v3,
    run_capability_then_science_v3,
    validate_execution_roots_v3,
)
from paperworks.v6.task039e3_recovery_integrity_v3 import (
    FROZEN_RETRY_POLICY_HASH_V3,
    FROZEN_RETRY_POLICY_V3,
    FROZEN_SAMPLING_CONFIGURATION_HASH_V3,
    FROZEN_SAMPLING_CONFIGURATION_V3,
    FROZEN_SCIENTIFIC_CALL_BUDGET_HASH_V3,
    FROZEN_SCIENTIFIC_CALL_BUDGET_V3,
    FrozenSourceBlobV3,
    ObservedExecutionIntegrityStateV3,
    PostContactIntegrityGuardV3,
    capture_execution_integrity_snapshot_v3,
)
from paperworks.v6.task039e3_recovery_live_transport_v3 import (
    RecoveryLiveOpenAIChatCompletionsTransportV3,
    RETRY_DELAYS_SECONDS,
    URLOPEN_TIMEOUT_SECONDS,
)
from paperworks.v6.task039e3_recovery_capability_v1 import (
    RECOVERY_CAPABILITY_PROMPT_SHA256,
    RECOVERY_CAPABILITY_SCHEMA_SHA256,
)
from paperworks.v6.task039e2_execution_configuration_v1 import EXACT_MODEL
from paperworks.v6.task039e3_execution_prep_v1 import EXECUTION_SCHEDULE_HASH
from paperworks.v6.task039e3_scientific_execution_v1 import validate_public_preflight_v1


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path.name}")
    return value


def _credential_loader() -> str:
    value = os.environ.get("OPENAI_API_KEY")
    if not value:
        raise ValueError("blocked_task039e3_credential_unavailable")
    return value


def _source_blobs(repository: Path, manifest: Mapping[str, Any]) -> tuple[FrozenSourceBlobV3, ...]:
    records = manifest.get("source_records")
    if not isinstance(records, list) or not records:
        raise ValueError("R1D2 source manifest records unavailable")
    result: list[FrozenSourceBlobV3] = []
    for record in records:
        if not isinstance(record, Mapping) or not isinstance(record.get("repository_path"), str):
            raise ValueError("R1D2 source manifest record differs")
        path = repository / str(record["repository_path"])
        data = path.read_bytes()
        result.append(
            FrozenSourceBlobV3(
                repository_path=str(record["repository_path"]),
                git_blob_sha=str(record["git_blob_sha"]),
                sha256=sha256(data).hexdigest(),
            )
        )
    return tuple(result)


def _observed_integrity_state(
    *,
    repository: Path,
    manifest: Mapping[str, Any],
    authorization_hash: str,
) -> ObservedExecutionIntegrityStateV3:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repository, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.strip()
    from paperworks.v6 import task039e3_recovery_execution_v3 as accounting_module
    from paperworks.v6 import task039e3_recovery_integrity_v3 as integrity_module
    from paperworks.v6 import task039e3_recovery_live_transport_v3 as transport_module
    from paperworks.v6 import task039e3_recovery_capability_v1 as capability_module
    from paperworks.v6 import task039e2_execution_configuration_v1 as config_module
    from paperworks.v6 import task039e3_execution_prep_v1 as schedule_module

    return ObservedExecutionIntegrityStateV3(
        head_commit=head,
        source_manifest_hash=str(manifest["artifact_hash"]),
        source_blobs=_source_blobs(repository, manifest),
        exact_model=transport_module.EXACT_MODEL,
        capability_prompt_hash=capability_module.RECOVERY_CAPABILITY_PROMPT_SHA256,
        capability_schema_hash=capability_module.RECOVERY_CAPABILITY_SCHEMA_SHA256,
        sampling_configuration=integrity_module.FROZEN_SAMPLING_CONFIGURATION_V3,
        sampling_configuration_hash=integrity_module.FROZEN_SAMPLING_CONFIGURATION_HASH_V3,
        urlopen_timeout_seconds=transport_module.URLOPEN_TIMEOUT_SECONDS,
        retry_wait_seconds=tuple(int(value) for value in transport_module.RETRY_DELAYS_SECONDS),
        retry_policy=integrity_module.FROZEN_RETRY_POLICY_V3,
        retry_policy_hash=integrity_module.FROZEN_RETRY_POLICY_HASH_V3,
        relation_schedule_hash=schedule_module.EXECUTION_SCHEDULE_HASH,
        scientific_concurrency=integrity_module.SCIENTIFIC_CONCURRENCY,
        scientific_call_budget=integrity_module.FROZEN_SCIENTIFIC_CALL_BUDGET_V3,
        scientific_call_budget_hash=integrity_module.FROZEN_SCIENTIFIC_CALL_BUDGET_HASH_V3,
        scientific_accounting_behavior_hash=stable_hash_v1(
            {"source": accounting_module.build_typed_accounting_v3.__code__.co_code.hex()}
        ),
        r2_authorization_hash=authorization_hash,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", required=True)
    parser.add_argument("--r2-authorization", required=True)
    parser.add_argument("--final-audit-receipt", required=True)
    parser.add_argument("--r1d2-source-manifest", required=True)
    parser.add_argument("--e1-private-root", required=True)
    parser.add_argument("--historical-e3-private-root", required=True)
    parser.add_argument("--recovery-e3-private-root", required=True)
    parser.add_argument("--public-output-root", required=True)
    args = parser.parse_args()

    repository = Path(args.repository_root).resolve(strict=True)
    authorization = _load_object(Path(args.r2_authorization).resolve(strict=True))
    final_audit = _load_object(Path(args.final_audit_receipt).resolve(strict=True))
    source_manifest = _load_object(Path(args.r1d2_source_manifest).resolve(strict=True))
    roots = lambda: validate_execution_roots_v3(
        repository_root=repository,
        e1_private_value=args.e1_private_root,
        historical_e3_private_value=args.historical_e3_private_root,
        recovery_e3_private_value=args.recovery_e3_private_root,
        public_output_value=args.public_output_root,
    )
    bootstrap = run_ordered_precontact_guards_v3(
        authorization_document=authorization,
        prior_authority_state_loader=lambda: load_prior_authority_state_v3(repository),
        git_state_loader=lambda: collect_git_execution_state_v3(repository, source_manifest),
        external_audit_receipt=final_audit,
        git_receipt_blob_loader=lambda commit, path: load_audit_receipt_git_blob_v3(
            repository, commit, path
        ),
        historical_capability_receipt_hash=HISTORICAL_CAPABILITY_RECEIPT_HASH,
        historical_provider_ledger_head_hash=HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
        root_guard_loader=roots,
        scientific_preflight_loader=lambda: validate_public_preflight_v1(repository),
        credential_loader=_credential_loader,
    )

    observed = lambda: _observed_integrity_state(
        repository=repository,
        manifest=source_manifest,
        authorization_hash=bootstrap.authorization.self_hash,
    )
    snapshot = capture_execution_integrity_snapshot_v3(observed())
    integrity = PostContactIntegrityGuardV3(
        snapshot=snapshot, observed_state_loader=observed
    )
    transport = RecoveryLiveOpenAIChatCompletionsTransportV3(
        api_key=bootstrap.credential
    )
    schedule = tuple(bootstrap.scientific_preflight["schedule"]["relation_identities"])
    try:
        result = run_capability_then_science_v3(
            repository_root=repository,
            execution_commit=bootstrap.git_state.head_commit,
            source_manifest_hash=bootstrap.git_state.source_manifest_hash,
            r2_authorization_hash=bootstrap.authorization.self_hash,
            authority_bindings={
                "r0_bundle_hash": authorization["r0_bundle_hash"],
                "r1a_timeout_authority_hash": authorization["r1a_timeout_authority_hash"],
                "r1b_commit_b": authorization["r1b_commit_b"],
                "r1c_commit_b": authorization["r1c_commit_b"],
                "r1c_audit_bundle_hash": authorization["r1c_independent_audit_bundle_hash"],
                "r1d2_commit_a": authorization["r1d2_commit_a"],
                "r1d2_commit_b": authorization["r1d2_commit_b"],
                "r1d2_source_manifest_hash": authorization["r1d2_source_manifest_hash"],
                "r1d2_audit_commit_b": authorization["r1d2_audit_commit_b"],
                "r1d2_independent_audit_bundle_hash": authorization["r1d2_independent_audit_bundle_hash"],
                "r1d2_audit_receipt_hash": authorization["r1d2_audit_receipt_hash"],
                "r2_authorization_hash": bootstrap.authorization.self_hash,
            },
            scientific_source_hashes={
                record.repository_path: record.sha256
                for record in snapshot.state.source_blobs
            },
            e1_private_root=bootstrap.guarded_roots.e1_private_root,
            historical_e3_private_root=bootstrap.guarded_roots.historical_e3_private_root,
            recovery_private_root=bootstrap.guarded_roots.recovery_e3_private_root,
            public_output_root=bootstrap.guarded_roots.public_output_root,
            public_cohort=bootstrap.scientific_preflight["cohort"],
            relation_identities=schedule,
            transport=transport,
            integrity_guard=integrity,
        )
    except TASK039E3RecoveryGuardedExecutionFailureV3Error as failure:
        print(json.dumps({"status": failure.failure_receipt["status"]}, sort_keys=True))
        return 5
    except TASK039E3RecoveryFailureReceiptDoubleFaultV3Error:
        print(json.dumps({"status": "double_fault_failure_receipt_persistence_failed"}, sort_keys=True))
        return 6
    print(json.dumps({"status": result["status"]}, sort_keys=True))
    if result["status"] == "blocked_task039e3_recovery_capability_gate":
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
