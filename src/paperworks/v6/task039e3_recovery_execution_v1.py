"""Additive TASK-039E3 recovery execution boundaries.

The module replaces only the historical capability-gate and public-writer
boundaries.  It reuses the audited live transport and frozen scientific
orchestration.  Every operational dependency is injected so unit tests remain
provider-offline and private-data-free.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Callable, Mapping, Sequence, TypeVar

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_execution_prep_v1 import (
    EXACT_MODEL,
    MAXIMUM_TRANSPORT_RETRIES,
    FrozenProviderRequestV1,
    MockProviderResponseV1,
    MockProviderTransportV1,
    ProviderCallLedgerV1,
    ProviderCallSlotV1,
    ProviderTransportAttemptV1,
    TASK039E3PreparationError,
    TRANSPORT_RETRY_DELAYS_SECONDS,
)
from paperworks.v6.task039e3_live_transport_v1 import (
    CALL_TIMEOUT_SECONDS,
    LiveOpenAIChatCompletionsTransportV1,
)
from paperworks.v6.task039e3_recovery_authorization_v1 import (
    GitExecutionStateV1,
    PriorAuthorityStateV1,
    R0_BUNDLE_HASH,
    R0_COMMIT,
    R1A_COMMIT,
    R1A_RECEIPT_HASH,
    R1A_TIMEOUT_AUTHORITY_HASH,
)
from paperworks.v6.task039e3_recovery_capability_v1 import (
    RecoveryCapabilityGateResultV1,
    RecoveryProbeAccountingV1,
    build_recovery_capability_request_v1,
    evaluate_recovery_capability_response_v1,
)
from paperworks.v6.task039e3_recovery_serialization_v1 import (
    finalize_public_artifact_v1,
    verify_public_artifact_v1,
    write_public_artifact_atomic_v1,
)
from paperworks.v6.task039e3_scientific_execution_v1 import (
    compute_scientific_source_hashes_v1,
    run_authorized_scientific_execution_v1,
)


RECOVERY_STATUS_PASS = "passed_task039e3_recovery_capability_gate"
RECOVERY_STATUS_BLOCK = "blocked_task039e3_recovery_capability_gate"
RECOVERY_TIMEOUT_SECONDS = 30.0
_RETRYABLE_OUTCOMES = frozenset(
    {
        "connection_failure",
        "connection_reset",
        "timeout_before_response",
        "http_429",
        "http_5xx",
    }
)


class TASK039E3RecoveryExecutionError(ValueError):
    """Raised when a recovery execution boundary differs from frozen policy."""


@dataclass(frozen=True)
class RecoveryProbeExecutionV1:
    request: FrozenProviderRequestV1
    response: MockProviderResponseV1
    gate: RecoveryCapabilityGateResultV1
    accounting: RecoveryProbeAccountingV1
    transport_attempts: int
    transport_retries: int
    attempt_records: tuple[Mapping[str, Any], ...]

    def __post_init__(self) -> None:
        if self.accounting.current_recovery_probe_count != 1:
            raise TASK039E3RecoveryExecutionError(
                "recovery probe execution must allocate one logical probe"
            )
        if self.transport_attempts not in {1, 2, 3}:
            raise TASK039E3RecoveryExecutionError("transport attempt count differs")
        if self.transport_retries != self.transport_attempts - 1:
            raise TASK039E3RecoveryExecutionError("transport retry count differs")
        if len(self.attempt_records) != self.transport_attempts:
            raise TASK039E3RecoveryExecutionError("transport attempt custody differs")


def execute_recovery_probe_v1(
    transport: MockProviderTransportV1,
) -> RecoveryProbeExecutionV1:
    """Execute at most one logical recovery probe through an injected transport."""

    if not isinstance(transport, MockProviderTransportV1):
        raise TASK039E3RecoveryExecutionError(
            "recovery probe requires the frozen provider transport interface"
        )
    request = build_recovery_capability_request_v1()
    accounting = RecoveryProbeAccountingV1().after_logical_recovery_probe()
    response: MockProviderResponseV1 | None = None
    attempt_records: list[dict[str, Any]] = []
    attempts = 0
    for attempts in range(1, MAXIMUM_TRANSPORT_RETRIES + 2):
        response = transport.send(request)
        attempt_records.append(
            {
                "attempt_number": attempts,
                "outcome": response.outcome,
                "status_code": response.status_code,
                "response_present": response.response_present,
            }
        )
        retryable = (
            not response.response_present and response.outcome in _RETRYABLE_OUTCOMES
        )
        if response.response_present or not retryable:
            break
    if response is None:
        raise TASK039E3RecoveryExecutionError("recovery probe returned no transport event")
    gate = evaluate_recovery_capability_response_v1(response)
    return RecoveryProbeExecutionV1(
        request=request,
        response=response,
        gate=gate,
        accounting=accounting,
        transport_attempts=attempts,
        transport_retries=attempts - 1,
        attempt_records=tuple(attempt_records),
    )


@dataclass(frozen=True)
class RecoveryCapabilityCustodyBindingV1:
    provider_ledger_hash: str
    provider_ledger_head_hash: str
    record_count: int = 1


def write_recovery_capability_private_custody_v1(
    *,
    recovery_private_root: Path,
    run_identity: str,
    execution: RecoveryProbeExecutionV1,
) -> RecoveryCapabilityCustodyBindingV1:
    """Durably freeze the real corrected probe before any E1 access."""

    if not recovery_private_root.is_dir():
        raise TASK039E3RecoveryExecutionError("recovery private root is absent")
    slot = ProviderCallSlotV1(
        None,
        stable_hash_v1({"fixture": "SYNTHETIC_CAPABILITY_CHECK"}),
        "CAPABILITY",
        1,
        False,
    )
    attempts = tuple(
        ProviderTransportAttemptV1(
            attempt_number=int(item["attempt_number"]),
            outcome=str(item["outcome"]),
            response_present=bool(item["response_present"]),
            status_code=(
                int(item["status_code"])
                if item["status_code"] is not None
                else None
            ),
            retry_eligible=(
                not bool(item["response_present"])
                and str(item["outcome"]) in _RETRYABLE_OUTCOMES
            ),
            planned_retry_delay_seconds=(
                TRANSPORT_RETRY_DELAYS_SECONDS[int(item["attempt_number"]) - 1]
                if not bool(item["response_present"])
                and str(item["outcome"]) in _RETRYABLE_OUTCOMES
                and int(item["attempt_number"]) <= MAXIMUM_TRANSPORT_RETRIES
                else None
            ),
        )
        for item in execution.attempt_records
    )
    terminal_state = (
        "completed_refusal"
        if execution.response.refusal
        else (
            "completed_structured"
            if execution.gate.structured_parse_pass
            else (
                "transport_exhausted"
                if not execution.response.response_present
                else "completed_invalid_response"
            )
        )
    )
    ledger = ProviderCallLedgerV1()
    provider_record = ledger.append(
        slot=slot,
        request_hash=execution.request.request_hash,
        response_present=execution.response.response_present,
        provider_response_metadata={
            "outcome": execution.response.outcome,
            "status_code": execution.response.status_code,
            "response_id": execution.response.response_id,
            "model": execution.response.model,
            "finish_reason": execution.response.finish_reason,
            "token_usage": (
                dict(execution.response.token_usage)
                if execution.response.token_usage is not None
                else None
            ),
        },
        transport_attempts=attempts,
        parse_status=(
            "passed"
            if execution.gate.structured_parse_pass
            and execution.gate.schema_validation_pass
            else "rejected"
        ),
        proposal_core_hash=None,
        terminal_slot_state=terminal_state,
    )
    record_content = {
        "run_identity": run_identity,
        "previous_record_hash": None,
        "provider_record": provider_record.to_dict(),
    }
    record = {**record_content, "record_hash": stable_hash_v1(record_content)}
    ledger_hash = stable_hash_v1(
        {
            "artifact_type": "task039e3_recovery_capability_provider_ledger_v1",
            "run_identity": run_identity,
            "record_hashes": [record["record_hash"]],
        }
    )
    path = recovery_private_root / "recovery_capability_provider_calls.jsonl"
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(
                record,
                handle,
                ensure_ascii=True,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise TASK039E3RecoveryExecutionError(
            "recovery capability provider custody could not be frozen"
        ) from exc
    return RecoveryCapabilityCustodyBindingV1(
        provider_ledger_hash=ledger_hash,
        provider_ledger_head_hash=record["record_hash"],
    )


@dataclass(frozen=True)
class RecoveryCapabilityPhaseResultV1:
    gate_status: str
    custody_receipt_hash: str
    e1_gate_open: bool
    e1_loaded: bool
    bootstrap: Any
    e1_value: Any = None

    def __post_init__(self) -> None:
        if self.gate_status not in {"PASS", "BLOCK"}:
            raise TASK039E3RecoveryExecutionError("recovery gate status differs")
        if self.e1_gate_open != (self.gate_status == "PASS"):
            raise TASK039E3RecoveryExecutionError("E1 gate differs from capability result")
        if self.e1_loaded != self.e1_gate_open:
            raise TASK039E3RecoveryExecutionError("E1 load state differs")
        if not isinstance(self.custody_receipt_hash, str) or not self.custody_receipt_hash:
            raise TASK039E3RecoveryExecutionError("capability custody was not frozen")


_BootstrapT = TypeVar("_BootstrapT")
_EvidenceT = TypeVar("_EvidenceT")


def run_recovery_capability_phase_v1(
    *,
    precontact_guard_runner: Callable[[], _BootstrapT],
    probe_executor: Callable[[_BootstrapT], RecoveryCapabilityGateResultV1],
    custody_writer: Callable[[RecoveryCapabilityGateResultV1], str],
    e1_loader: Callable[[_BootstrapT], _EvidenceT],
) -> RecoveryCapabilityPhaseResultV1:
    """Enforce guards -> one probe -> durable custody -> conditional E1 access."""

    bootstrap = precontact_guard_runner()
    gate = probe_executor(bootstrap)
    if not isinstance(gate, RecoveryCapabilityGateResultV1):
        raise TASK039E3RecoveryExecutionError("probe executor returned an invalid gate")
    custody_hash = custody_writer(gate)
    if gate.gate_status == "BLOCK":
        return RecoveryCapabilityPhaseResultV1(
            gate_status="BLOCK",
            custody_receipt_hash=custody_hash,
            e1_gate_open=False,
            e1_loaded=False,
            bootstrap=bootstrap,
        )
    evidence = e1_loader(bootstrap)
    return RecoveryCapabilityPhaseResultV1(
        gate_status="PASS",
        custody_receipt_hash=custody_hash,
        e1_gate_open=True,
        e1_loaded=True,
        bootstrap=bootstrap,
        e1_value=evidence,
    )


def build_recovery_capability_receipt_v1(
    *,
    run_identity: str,
    execution_commit: str,
    source_manifest_hash: str,
    r2_authorization_hash: str,
    execution: RecoveryProbeExecutionV1,
    custody_binding: RecoveryCapabilityCustodyBindingV1,
    system_fingerprint: str | None = None,
) -> dict[str, Any]:
    """Build the sanitized recovery capability receipt from mapped metadata."""

    response = execution.response
    content = {
        "schema_version": "1.0.0",
        "artifact_type": "task039e3_recovery_capability_gate_receipt_v1",
        "task_id": "TASK-039E3-R2_RECOVERY_EXECUTION",
        "status": (
            RECOVERY_STATUS_PASS
            if execution.gate.gate_status == "PASS"
            else RECOVERY_STATUS_BLOCK
        ),
        "run_identity": run_identity,
        "historical_capability_probe_count": 1,
        "current_recovery_probe_count": 1,
        "cumulative_capability_probe_count": 2,
        "r1b_commit_a": execution_commit,
        "r1b_source_manifest_hash": source_manifest_hash,
        "r2_authorization_hash": r2_authorization_hash,
        "r0_bundle_hash": R0_BUNDLE_HASH,
        "r1a_timeout_authority_hash": R1A_TIMEOUT_AUTHORITY_HASH,
        "r1a_receipt_hash": R1A_RECEIPT_HASH,
        "provider": "openai",
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "requested_model": EXACT_MODEL,
        "returned_model": response.model,
        "response_id": response.response_id,
        "finish_reason": response.finish_reason,
        "usage": dict(response.token_usage) if response.token_usage is not None else None,
        "system_fingerprint": system_fingerprint,
        "transport_attempts": execution.transport_attempts,
        "transport_retries": execution.transport_retries,
        "provider_ledger_hash": custody_binding.provider_ledger_hash,
        "provider_ledger_head_hash": custody_binding.provider_ledger_head_hash,
        "refusal_present": response.refusal,
        "structured_parse_pass": execution.gate.structured_parse_pass,
        "schema_validation_pass": execution.gate.schema_validation_pass,
        "fixture_id_match": execution.gate.fixture_id_match,
        "capability_token_match": execution.gate.capability_token_match,
        "model_identity_match": execution.gate.model_identity_match,
        "gate_status": execution.gate.gate_status,
        "configuration_changed": False,
        "previous_historical_capability_receipt_hash": (
            "e36098690f2c4c018b8ed5f339d46870fbbe0561f52c117cd2525a63d155c279"
        ),
        "previous_historical_provider_ledger_head_hash": (
            "656d81ded2f166175adf2717abc226c325cd4a9fcbcee5306f4ea35c7465d254"
        ),
        "credential_persisted": False,
        "authorization_header_persisted": False,
    }
    return finalize_public_artifact_v1(content)


class RecoveryScientificCompatibilityTransportV1(MockProviderTransportV1):
    """Bridge a passed corrected gate into the frozen scientific top level.

    The first call is a local compatibility acknowledgement and never contacts
    the provider.  Its content is generated deterministically only after the
    corrected gate has passed; therefore it carries no model self-report
    authority.  All subsequent scientific calls delegate unchanged.
    """

    def __init__(
        self,
        *,
        delegate: LiveOpenAIChatCompletionsTransportV1,
        recovery_response: MockProviderResponseV1,
    ) -> None:
        if recovery_response.model != EXACT_MODEL or not recovery_response.response_present:
            raise TASK039E3RecoveryExecutionError(
                "compatibility bridge requires a passed corrected provider response"
            )
        self._delegate = delegate
        self._response = recovery_response
        self._compatibility_sent = False

    @property
    def calls(self) -> int:
        return self._delegate.calls

    @property
    def request_hashes(self) -> tuple[str, ...]:
        return self._delegate.request_hashes

    @property
    def attempt_custody(self) -> Any:
        return self._delegate.attempt_custody

    def send(self, request: FrozenProviderRequestV1) -> MockProviderResponseV1:
        if not self._compatibility_sent:
            self._compatibility_sent = True
            return MockProviderResponseV1(
                response_present=True,
                outcome="local_corrected_gate_compatibility_acknowledgement",
                status_code=200,
                model=self._response.model,
                content=json.dumps(
                    {
                        "model_snapshot": EXACT_MODEL,
                        "structured_output_supported": True,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                refusal=False,
                finish_reason=self._response.finish_reason,
                response_id=self._response.response_id,
                token_usage=self._response.token_usage,
            )
        return self._delegate.send(request)


def run_frozen_science_after_recovery_gate_v1(
    *,
    repository_root: Path,
    execution_commit: str,
    e1_private_root: Path,
    recovery_private_root: Path,
    live_transport: LiveOpenAIChatCompletionsTransportV1,
    preflight: Mapping[str, Any],
    recovery_execution: RecoveryProbeExecutionV1,
    recovery_capability_receipt: Mapping[str, Any],
    recovery_capability_custody: RecoveryCapabilityCustodyBindingV1,
    source_manifest: Mapping[str, Any],
    progress: Any = print,
) -> dict[str, dict[str, Any]]:
    """Run the unchanged arm orchestration after the corrected gate passes."""

    if recovery_execution.gate.gate_status != "PASS":
        raise TASK039E3RecoveryExecutionError("scientific execution requires capability PASS")
    if float(CALL_TIMEOUT_SECONDS) != RECOVERY_TIMEOUT_SECONDS:
        raise TASK039E3RecoveryExecutionError("R1A recovery timeout differs")
    adapter = RecoveryScientificCompatibilityTransportV1(
        delegate=live_transport,
        recovery_response=recovery_execution.response,
    )
    source_hashes = compute_scientific_source_hashes_v1(repository_root)
    artifacts = run_authorized_scientific_execution_v1(
        repository_root=repository_root,
        execution_commit=execution_commit,
        e1_private_root=e1_private_root,
        e3_private_root=recovery_private_root,
        transport=adapter,  # type: ignore[arg-type]
        preflight=preflight,
        source_hashes=source_hashes,
        progress=progress,
    )
    post_state = collect_git_execution_state_v1(repository_root, source_manifest)
    if (
        post_state.head_commit != execution_commit
        or not post_state.worktree_clean
        or not post_state.index_clean
        or not post_state.source_blobs_match_manifest
    ):
        raise TASK039E3RecoveryExecutionError(
            "R1B source or configuration changed after provider contact"
        )
    if "failure" in artifacts:
        failure_content = {
            key: value
            for key, value in artifacts["failure"].items()
            if key != "artifact_hash"
        }
        failure_content["recovery_capability_provider_ledger_hash"] = (
            recovery_capability_custody.provider_ledger_hash
        )
        failure_content["recovery_capability_provider_ledger_head_hash"] = (
            recovery_capability_custody.provider_ledger_head_hash
        )
        artifacts["failure"] = finalize_public_artifact_v1(failure_content)
        return artifacts
    if "receipt" not in artifacts:
        return artifacts
    capability = verify_public_artifact_v1(recovery_capability_receipt)
    custody_content = {
        key: value
        for key, value in artifacts["custody"].items()
        if key != "artifact_hash"
    }
    custody_content["recovery_capability_provider_ledger_hash"] = (
        recovery_capability_custody.provider_ledger_hash
    )
    custody_content["recovery_capability_provider_ledger_head_hash"] = (
        recovery_capability_custody.provider_ledger_head_hash
    )
    custody_content["compatibility_acknowledgement_scientific_authority"] = False
    artifacts["custody"] = finalize_public_artifact_v1(custody_content)
    private_content = {
        key: value
        for key, value in artifacts["private_bindings"].items()
        if key != "artifact_hash"
    }
    private_content["recovery_capability_provider_ledger_hash"] = (
        recovery_capability_custody.provider_ledger_hash
    )
    private_content["recovery_capability_provider_ledger_head_hash"] = (
        recovery_capability_custody.provider_ledger_head_hash
    )
    artifacts["private_bindings"] = finalize_public_artifact_v1(private_content)
    receipt_content = {
        key: value
        for key, value in artifacts["receipt"].items()
        if key != "artifact_hash"
    }
    receipt_content["capability_receipt_hash"] = capability["artifact_hash"]
    receipt_content["provider_custody_binding_hash"] = artifacts["custody"][
        "artifact_hash"
    ]
    receipt_content["private_ledger_bindings_hash"] = artifacts[
        "private_bindings"
    ]["artifact_hash"]
    receipt_content["recovery_capability_provider_ledger_hash"] = (
        recovery_capability_custody.provider_ledger_hash
    )
    receipt_content["corrected_recovery_capability_gate"] = True
    receipt_content["historical_self_report_authority"] = False
    artifacts["capability"] = capability
    artifacts["receipt"] = finalize_public_artifact_v1(receipt_content)
    return artifacts


RECOVERY_PUBLIC_ARTIFACT_NAMES = {
    "capability": "TASK-039E3_R2_RECOVERY_CAPABILITY_GATE.json",
    "custody": "TASK-039E3_R2_PROVIDER_CUSTODY_BINDING.json",
    "private_bindings": "TASK-039E3_R2_PRIVATE_LEDGER_BINDINGS.json",
    "construction_metrics": "TASK-039E3_R2_CONSTRUCTION_METRICS.json",
    "direct_metrics": "TASK-039E3_R2_DIRECT_NUMBER_METRICS.json",
    "summary": "TASK-039E3_R2_EXECUTION_SUMMARY.json",
    "access": "TASK-039E3_R2_DATA_ACCESS_AUDIT.json",
    "receipt": "TASK-039E3_R2_EXECUTION_RECEIPT.json",
    "failure": "TASK-039E3_R2_EXECUTION_FAILURE.json",
}


def write_recovery_public_artifacts_v1(
    repository_root: Path, artifacts: Mapping[str, Mapping[str, Any]]
) -> dict[str, str]:
    """Write only recovery-namespaced public artifacts through the safe writer."""

    report_root = repository_root / "docs" / "task_reports"
    hashes: dict[str, str] = {}
    for key, document in artifacts.items():
        filename = RECOVERY_PUBLIC_ARTIFACT_NAMES.get(key)
        if filename is None:
            continue
        written = write_public_artifact_atomic_v1(report_root / filename, document)
        hashes[key] = written["artifact_hash"]
    return hashes


def build_recovery_run_identity_v1(
    *, r1b_commit: str, source_manifest_hash: str, r2_authorization_hash: str
) -> str:
    return stable_hash_v1(
        {
            "historical_capability_block_commit": (
                "52a8cec2d170f9b8e3c5c0ac048115ffad93e018"
            ),
            "r0_commit": "d5164aa93cc4c3efb6a343e0890b554f436a7e39",
            "r1a_commit": "260b91be463815bc5bb453ca2cc05cec741aacc3",
            "r1b_commit": r1b_commit,
            "source_manifest_hash": source_manifest_hash,
            "r2_authorization_hash": r2_authorization_hash,
            "exact_model": EXACT_MODEL,
        }
    )


def _verify_bound_artifact_v1(
    path: Path, *, hash_field: str, expected_hash: str
) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TASK039E3RecoveryExecutionError(
            f"public authority artifact unavailable: {path.name}"
        ) from exc
    if not isinstance(document, dict) or document.get(hash_field) != expected_hash:
        raise TASK039E3RecoveryExecutionError(
            f"public authority binding differs: {path.name}"
        )
    content = {key: value for key, value in document.items() if key != hash_field}
    if stable_hash_v1(content) != expected_hash:
        raise TASK039E3RecoveryExecutionError(
            f"public authority self-hash differs: {path.name}"
        )
    return document


def load_prior_authority_state_v1(repository_root: Path) -> PriorAuthorityStateV1:
    """Independently verify the committed R0 and R1A authority artifacts."""

    reports = repository_root / "docs" / "task_reports"
    r0 = _verify_bound_artifact_v1(
        reports / "TASK-039E3_R0_RECEIPT.json",
        hash_field="artifact_hash",
        expected_hash=R0_BUNDLE_HASH,
    )
    if r0.get("component_artifact_hashes", {}).get("recovery") != (
        "8b1b55c4ed96b0642737e616dd60b271684d59738c8186211abb9c6c46cd1362"
    ):
        raise TASK039E3RecoveryExecutionError("R0 recovery protocol binding differs")
    r1a_authority = _verify_bound_artifact_v1(
        reports / "TASK-039E3_R1A_TIMEOUT_AUTHORITY.json",
        hash_field="self_hash",
        expected_hash=R1A_TIMEOUT_AUTHORITY_HASH,
    )
    r1a_receipt = _verify_bound_artifact_v1(
        reports / "TASK-039E3_R1A_RECEIPT.json",
        hash_field="self_hash",
        expected_hash=R1A_RECEIPT_HASH,
    )
    if (
        r1a_authority.get("recovery_timeout_amendment_seconds") != 30.0
        or r1a_authority.get("retroactive_e2_reinterpretation") is not False
        or r1a_receipt.get("timeout_authority_hash") != R1A_TIMEOUT_AUTHORITY_HASH
    ):
        raise TASK039E3RecoveryExecutionError("R1A timeout authority differs")
    return PriorAuthorityStateV1(
        r0_commit=R0_COMMIT,
        r0_bundle_hash=R0_BUNDLE_HASH,
        r1a_commit=R1A_COMMIT,
        r1a_timeout_authority_hash=R1A_TIMEOUT_AUTHORITY_HASH,
        r1a_receipt_hash=R1A_RECEIPT_HASH,
    )


def collect_git_execution_state_v1(
    repository_root: Path, source_manifest: Mapping[str, Any]
) -> GitExecutionStateV1:
    """Collect exact Git/blob facts without reading credentials or private roots."""

    manifest = verify_public_artifact_v1(source_manifest)

    def run(*arguments: str, text: bool = True) -> Any:
        return subprocess.run(
            ["git", *arguments],
            cwd=repository_root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=text,
        ).stdout

    head = run("rev-parse", "HEAD").strip()
    status = run("status", "--porcelain=v1")
    cached = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=repository_root, check=False
    ).returncode
    records = manifest.get("source_records")
    blob_match = isinstance(records, list)
    if blob_match:
        for record in records:
            if not isinstance(record, Mapping):
                blob_match = False
                break
            relative = record.get("repository_path")
            if not isinstance(relative, str):
                blob_match = False
                break
            observed_blob = run("rev-parse", f"{head}:{relative}").strip()
            observed_bytes = run("show", f"{head}:{relative}", text=False)
            if (
                observed_blob != record.get("git_blob_sha")
                or sha256(observed_bytes).hexdigest() != record.get("sha256")
            ):
                blob_match = False
                break
    return GitExecutionStateV1(
        head_commit=head,
        worktree_clean=not bool(status),
        index_clean=cached == 0,
        source_manifest_hash=manifest["artifact_hash"],
        source_blobs_match_manifest=blob_match,
    )


__all__ = [
    "RECOVERY_PUBLIC_ARTIFACT_NAMES",
    "RECOVERY_STATUS_BLOCK",
    "RECOVERY_STATUS_PASS",
    "RecoveryCapabilityPhaseResultV1",
    "RecoveryCapabilityCustodyBindingV1",
    "RecoveryProbeExecutionV1",
    "RecoveryScientificCompatibilityTransportV1",
    "TASK039E3RecoveryExecutionError",
    "build_recovery_capability_receipt_v1",
    "build_recovery_run_identity_v1",
    "collect_git_execution_state_v1",
    "execute_recovery_probe_v1",
    "load_prior_authority_state_v1",
    "run_frozen_science_after_recovery_gate_v1",
    "run_recovery_capability_phase_v1",
    "write_recovery_public_artifacts_v1",
    "write_recovery_capability_private_custody_v1",
]
