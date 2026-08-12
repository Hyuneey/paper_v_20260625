"""Concrete future-live composition for the audited R2R dependency graph.

The module performs no work at import time and contains no credential lookup.
It converts explicit external paths into callbacks consumed by the runner's
dependency-ordered boundary.  A future authorization may make those callbacks
reachable; this implementation task invokes none of them against real data.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping

from paperworks.v6.task039e3_r2r_authorization_v1 import (
    PROTOCOL_BUNDLE_HASH,
    PROTOCOL_RECEIPT_HASH,
    FORENSIC_BUNDLE_HASH,
    FORENSIC_RECEIPT_HASH,
    ValidatedR2RAuthorizationV1,
    validate_r2r_authorization_v1,
)
from paperworks.v6.task039e3_r2r_capability_reuse_v1 import (
    ValidatedCapabilityReuseR2RV1,
    capability_observation_from_reconstruction_v1,
    validate_capability_reuse_v1,
)
from paperworks.v6.task039e3_r2r_execution_v1 import (
    EXPECTED_EMPTY_LEDGER_KINDS,
    FreshLedgerObservationR2RV1,
    build_lifetime_accounting_v1,
    run_injected_r2r_scientific_cohort_v1,
    validate_empty_fresh_cohort_ledgers_v1,
)
from paperworks.v6.task039e3_r2r_failure_finalizer_v1 import (
    FAILURE_ARTIFACT_NAME,
    write_terminal_failure_receipt_r2r_v1,
)
from paperworks.v6.task039e3_r2r_live_transport_v1 import (
    R2RLiveOpenAIChatCompletionsTransportV1,
    R2RLiveTransportAttemptCustodyV1,
)
from paperworks.v6.task039e3_r2r_precontact_v1 import (
    GuardedR2RRootsV1,
    R2RLivePathDependenciesV1,
    R2RObservedIntegrityStateV1,
    R2RPostContactIntegrityGuardV1,
    R2RSourceBlobIdentityV1,
    R2R_SCIENTIFIC_ACCOUNTING_BEHAVIOR_HASH_V1,
    capture_r2r_integrity_snapshot_v1,
    validate_r2r_execution_roots_v1,
)
from paperworks.v6.task039e3_r2r_result_finalizer_v1 import (
    build_capability_reuse_binding_r2r_v1,
    finalize_successful_r2r_scientific_result_v1,
    provider_custody_binding_from_reconstruction_r2r_v1,
    result_authority_bindings_from_r2r_authorization_v1,
)
from paperworks.v6.task039e3_recovery_execution_v3 import (
    TransactionalScientificProviderLedgerV3,
)
from paperworks.v6.task039e3_recovery_integrity_v3 import (
    FROZEN_RETRY_POLICY_HASH_V3,
    FROZEN_SAMPLING_CONFIGURATION_HASH_V3,
    FROZEN_SCIENTIFIC_CALL_BUDGET_HASH_V3,
)
from paperworks.v6.task039e3_recovery_serialization_v1 import (
    verify_public_artifact_v1,
)
from paperworks.v6.task039e3_recovery_transactional_custody_v3 import (
    TransactionalHashChainCustodyV3,
    reconstruct_transactional_ledger_v3,
)
from paperworks.v6.task039e3_scientific_execution_v1 import (
    DurableConstructionOutcomeLedgerV1,
    DurableConstructionProposalLedgerV1,
    DurableDirectNumberLedgerV1,
    PRIVATE_LEDGER_FILE,
    load_real_evidence_schedule_v1,
    validate_public_preflight_v1,
)
from paperworks.v6.task039e3_recovery_science_v2 import ScientificLedgersV2


PROTOCOL_RECEIPT_PATH = (
    "docs/task_reports/TASK-039E3_R2_SCIENTIFIC_RECOVERY_PROTOCOL_RECEIPT.json"
)
FORENSIC_RECEIPT_PATH = (
    "docs/task_reports/TASK-039E3_R2_FAILURE_FORENSIC_RECEIPT.json"
)
INDEPENDENT_AUDIT_PASS_STATUS = "passed_task039e3_r2r_independent_audit"
INDEPENDENT_AUDIT_RECEIPT_PATH = (
    "docs/task_reports/TASK-039E3_R2R_AUDIT_RECEIPT.json"
)


class TASK039E3R2RLiveExecutionError(RuntimeError):
    """An exact future-live authority or custody invariant differs."""


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TASK039E3R2RLiveExecutionError(f"JSON object required: {path.name}")
    return value


@dataclass(frozen=True)
class R2RAuthorityContextV1:
    document: Mapping[str, Any]
    validated: ValidatedR2RAuthorizationV1


@dataclass(frozen=True)
class R2RGitSourceContextV1:
    repository_root: Path
    source_manifest: Mapping[str, Any]
    source_blobs: tuple[R2RSourceBlobIdentityV1, ...]
    scientific_source_hashes: Mapping[str, str]
    public_preflight: Mapping[str, Any]


@dataclass(frozen=True)
class R2RForensicProtocolContextV1:
    protocol_receipt_hash: str
    forensic_receipt_hash: str
    audit_receipt_hash: str


@dataclass
class R2RFreshLiveLedgersV1:
    recovery_root: Path
    observations: tuple[FreshLedgerObservationR2RV1, ...]
    scientific_custody: TransactionalHashChainCustodyV3 | None = None
    http_error_custody: TransactionalHashChainCustodyV3 | None = None
    provider: TransactionalScientificProviderLedgerV3 | None = None
    proposal: DurableConstructionProposalLedgerV1 | None = None
    outcome: DurableConstructionOutcomeLedgerV1 | None = None
    direct_number: DurableDirectNumberLedgerV1 | None = None
    transport: R2RLiveOpenAIChatCompletionsTransportV1 | None = None

    def close_working_ledgers(self) -> None:
        for ledger in (self.provider, self.proposal, self.outcome, self.direct_number):
            close = getattr(ledger, "close", None)
            if callable(close):
                close()


def _verify_authority_artifact(path: Path, expected_hash: str) -> Mapping[str, Any]:
    document = verify_public_artifact_v1(_load_object(path))
    if document.get("artifact_hash") != expected_hash:
        raise TASK039E3R2RLiveExecutionError(f"authority differs: {path.name}")
    return document


def _git_bytes(repository: Path, *arguments: str, text: bool = False) -> Any:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
    ).stdout


def _validate_git_source(
    repository: Path,
    authorization: R2RAuthorityContextV1,
    manifest_path: Path,
) -> R2RGitSourceContextV1:
    manifest = verify_public_artifact_v1(_load_object(manifest_path))
    expected_hash = authorization.validated.implementation_source_manifest_hash
    if manifest.get("artifact_hash") != expected_hash:
        raise TASK039E3R2RLiveExecutionError("R2R source manifest authority differs")
    head = _git_bytes(repository, "rev-parse", "HEAD", text=True).strip()
    if head != authorization.validated.implementation_commit_a:
        raise TASK039E3R2RLiveExecutionError("R2R execution Commit A differs")
    if manifest.get("described_commit") != head:
        raise TASK039E3R2RLiveExecutionError("R2R manifest described commit differs")
    if _git_bytes(repository, "status", "--porcelain=v1", text=True):
        raise TASK039E3R2RLiveExecutionError("R2R execution worktree is not clean")
    if subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=repository, check=False
    ).returncode != 0:
        raise TASK039E3R2RLiveExecutionError("R2R execution index is not clean")
    records = manifest.get("source_records")
    if not isinstance(records, list) or not records:
        raise TASK039E3R2RLiveExecutionError("R2R source records are absent")
    identities: list[R2RSourceBlobIdentityV1] = []
    source_hashes: dict[str, str] = {}
    for record in records:
        if not isinstance(record, Mapping) or not isinstance(
            record.get("repository_path"), str
        ):
            raise TASK039E3R2RLiveExecutionError("R2R source record differs")
        relative = str(record["repository_path"])
        git_blob = _git_bytes(repository, "rev-parse", f"{head}:{relative}", text=True).strip()
        git_content = _git_bytes(repository, "show", f"{head}:{relative}")
        worktree_content = (repository / relative).read_bytes()
        byte_hash = sha256(git_content).hexdigest()
        if (
            git_blob != record.get("git_blob_sha")
            or byte_hash != record.get("sha256")
            or worktree_content != git_content
        ):
            raise TASK039E3R2RLiveExecutionError(
                f"R2R exact source identity differs: {relative}"
            )
        identities.append(R2RSourceBlobIdentityV1(relative, git_blob, byte_hash))
        source_hashes[relative] = byte_hash
    return R2RGitSourceContextV1(
        repository_root=repository,
        source_manifest=manifest,
        source_blobs=tuple(identities),
        scientific_source_hashes=source_hashes,
        public_preflight=validate_public_preflight_v1(repository),
    )


def _validate_forensic_protocol(
    repository: Path,
    audit_receipt_path: Path,
    authorization: R2RAuthorityContextV1,
    git_source: R2RGitSourceContextV1,
) -> R2RForensicProtocolContextV1:
    protocol = _verify_authority_artifact(
        repository / PROTOCOL_RECEIPT_PATH, PROTOCOL_RECEIPT_HASH
    )
    forensic = _verify_authority_artifact(
        repository / FORENSIC_RECEIPT_PATH, FORENSIC_RECEIPT_HASH
    )
    if protocol.get("protocol_bundle_hash") != PROTOCOL_BUNDLE_HASH:
        raise TASK039E3R2RLiveExecutionError("recovery protocol bundle differs")
    if forensic.get("forensic_bundle_hash") != FORENSIC_BUNDLE_HASH:
        raise TASK039E3R2RLiveExecutionError("forensic bundle differs")
    audit_bytes = audit_receipt_path.read_bytes()
    audit = verify_public_artifact_v1(json.loads(audit_bytes.decode("utf-8")))
    if (
        audit.get("artifact_hash")
        != authorization.validated.independent_audit_receipt_hash
        or audit.get("status") != INDEPENDENT_AUDIT_PASS_STATUS
        or audit.get("blocking_finding_count") != 0
        or audit.get("implementation_commit_a")
        != authorization.validated.implementation_commit_a
        or audit.get("implementation_source_manifest_hash")
        != authorization.validated.implementation_source_manifest_hash
        or audit.get("audit_bundle_hash")
        != authorization.validated.independent_audit_bundle_hash
    ):
        raise TASK039E3R2RLiveExecutionError("R2R independent audit authority differs")
    exact_git_receipt = _git_bytes(
        repository,
        "show",
        (
            f"{authorization.validated.independent_audit_commit_b}:"
            f"{INDEPENDENT_AUDIT_RECEIPT_PATH}"
        ),
    )
    if exact_git_receipt != audit_bytes:
        raise TASK039E3R2RLiveExecutionError(
            "R2R independent audit exact Git receipt differs"
        )
    return R2RForensicProtocolContextV1(
        protocol_receipt_hash=str(protocol["artifact_hash"]),
        forensic_receipt_hash=str(forensic["artifact_hash"]),
        audit_receipt_hash=str(audit["artifact_hash"]),
    )


def _typed_accounting(
    result: Any, transport: R2RLiveOpenAIChatCompletionsTransportV1
) -> dict[str, Any]:
    lifetime = build_lifetime_accounting_v1(result.scientific_logical_calls)
    attempts = len(transport.attempt_custody)
    return {
        "historical_aborted_r2_scientific_logical_calls": 1,
        "historical_aborted_r2_provider_authored_scientific_responses": 0,
        "r2r_t1_logical_calls": result.t1_logical_calls,
        "r2r_t1b_logical_calls": result.t1b_logical_calls,
        "r2r_t2_logical_calls": result.t2_logical_calls,
        "r2r_direct_number_logical_calls": result.direct_number_logical_calls,
        "r2r_scientific_logical_calls": result.scientific_logical_calls,
        "lifetime_scientific_logical_call_attempts": (
            lifetime.lifetime_scientific_logical_call_attempts
        ),
        "r2r_scientific_transport_attempts": attempts,
        "r2r_scientific_transport_retries": attempts - result.scientific_logical_calls,
        "scientific_concurrency": 1,
        "scientific_generation_retries": 0,
        "historical_partial_records_reused": 0,
        "additional_capability_probes": 0,
        "cumulative_real_provider_capability_probes": 2,
        "local_compatibility_slots": 0,
    }


def _failure_provider_observation(
    provider_records: tuple[Any, ...],
) -> dict[str, Any]:
    if not provider_records:
        return {
            "last_attempted_scientific_slot": None,
            "actual_returned_model": None,
            "actual_response_id": None,
            "terminal_slot_state": None,
        }
    last = provider_records[-1]
    metadata = last.provider_response_metadata
    return {
        "last_attempted_scientific_slot": last.slot.to_dict(),
        "actual_returned_model": metadata.get("model"),
        "actual_response_id": metadata.get("response_id"),
        "terminal_slot_state": last.terminal_slot_state,
    }


def _postcontact_failure_integrity_status(
    transport: R2RLiveOpenAIChatCompletionsTransportV1 | None,
    integrity: R2RPostContactIntegrityGuardV1,
) -> str:
    if integrity.blocked:
        return "integrity_changed_blocked"
    if transport is None or transport.calls == 0:
        return "not_started"
    try:
        integrity.assert_unchanged_before_provider_attempt()
    except Exception:
        return "integrity_changed_blocked"
    return "verified_unchanged"


def build_r2r_live_dependencies_v1(args: Any) -> R2RLivePathDependenciesV1:
    """Build the concrete callback graph; no callback is executed here."""

    repository = Path(args.repository_root)
    authorization_path = Path(args.r2r_authorization)
    source_manifest_path = Path(args.r2r_source_manifest)
    audit_receipt_path = Path(args.r2r_audit_receipt)
    capability_receipt_path = Path(args.capability_receipt)
    capability_ledger_root = Path(args.capability_ledger_root)
    state: dict[str, Any] = {}

    def authorization_guard() -> R2RAuthorityContextV1:
        document = _load_object(authorization_path)
        context = R2RAuthorityContextV1(document, validate_r2r_authorization_v1(document))
        state["authorization"] = context
        return context

    def git_source_guard(auth: R2RAuthorityContextV1) -> R2RGitSourceContextV1:
        context = _validate_git_source(repository, auth, source_manifest_path)
        state["git_source"] = context
        return context

    def forensic_guard(
        auth: R2RAuthorityContextV1, git_source: R2RGitSourceContextV1
    ) -> R2RForensicProtocolContextV1:
        context = _validate_forensic_protocol(
            repository, audit_receipt_path, auth, git_source
        )
        state["forensic"] = context
        return context

    def capability_guard(
        _auth: R2RAuthorityContextV1,
    ) -> ValidatedCapabilityReuseR2RV1:
        reconstruction = reconstruct_transactional_ledger_v3(
            capability_ledger_root, ledger_kind="recovery_capability"
        )
        validated = validate_capability_reuse_v1(
            private_capability_receipt=_load_object(capability_receipt_path),
            ledger_observation=capability_observation_from_reconstruction_v1(
                reconstruction
            ),
        )
        state["capability"] = validated
        return validated

    def root_guard() -> GuardedR2RRootsV1:
        roots = validate_r2r_execution_roots_v1(
            repository_root=repository,
            e1_private_root=args.e1_private_root,
            capability_ledger_root=capability_ledger_root,
            recovery_private_root=args.recovery_private_root,
            public_output_root=args.public_output_root,
        )
        state["roots"] = roots
        return roots

    def fresh_guard(roots: GuardedR2RRootsV1) -> R2RFreshLiveLedgersV1:
        observations = tuple(
            FreshLedgerObservationR2RV1(kind, 0, None)
            for kind in EXPECTED_EMPTY_LEDGER_KINDS
        )
        validate_empty_fresh_cohort_ledgers_v1(observations)
        ledgers = R2RFreshLiveLedgersV1(roots.recovery_private_root, observations)
        state["ledgers"] = ledgers
        return ledgers

    def integrity_guard(
        auth: R2RAuthorityContextV1,
        git_source: R2RGitSourceContextV1,
        _forensic: R2RForensicProtocolContextV1,
        _capability: ValidatedCapabilityReuseR2RV1,
        _roots: GuardedR2RRootsV1,
        _ledgers: R2RFreshLiveLedgersV1,
    ) -> R2RPostContactIntegrityGuardV1:
        def observed() -> R2RObservedIntegrityStateV1:
            current = _validate_git_source(repository, auth, source_manifest_path)
            return R2RObservedIntegrityStateV1(
                execution_commit=auth.validated.implementation_commit_a,
                source_manifest_hash=auth.validated.implementation_source_manifest_hash,
                source_blobs=current.source_blobs,
                authorization_hash=auth.validated.self_hash,
                recovery_main_provider_schema_v2_hash=str(
                    auth.document["recovery_main_provider_schema_v2_hash"]
                ),
                main_prompt_hash=str(auth.document["main_prompt_hash"]),
                t2_followup_prompt_hash=str(auth.document["t2_followup_prompt_hash"]),
                direct_number_prompt_hash=str(auth.document["direct_number_prompt_hash"]),
                direct_number_schema_hash=str(
                    auth.document["direct_number_provider_schema_hash"]
                ),
                exact_model=str(auth.document["exact_model"]),
                endpoint=str(auth.document["endpoint"]),
                sampling_configuration_hash=FROZEN_SAMPLING_CONFIGURATION_HASH_V3,
                timeout_seconds=float(auth.document["urlopen_timeout_seconds"]),
                retry_policy_hash=FROZEN_RETRY_POLICY_HASH_V3,
                relation_schedule_hash=str(auth.document["relation_schedule_hash"]),
                scientific_concurrency=int(auth.document["scientific_concurrency"]),
                scientific_call_budget_hash=FROZEN_SCIENTIFIC_CALL_BUDGET_HASH_V3,
                scientific_accounting_behavior_hash=(
                    R2R_SCIENTIFIC_ACCOUNTING_BEHAVIOR_HASH_V1
                ),
                recovery_execution_configuration_hash=str(
                    auth.document["recovery_execution_configuration_hash"]
                ),
            )

        snapshot = capture_r2r_integrity_snapshot_v1(observed())
        guard = R2RPostContactIntegrityGuardV1(snapshot, observed)
        state["integrity"] = guard
        return guard

    def transport_factory(
        credential: str,
        _integrity: R2RPostContactIntegrityGuardV1,
        ledgers: R2RFreshLiveLedgersV1,
    ) -> R2RLiveOpenAIChatCompletionsTransportV1:
        scientific_root = ledgers.recovery_root / "scientific_r2r_v1"
        scientific_root.mkdir(exist_ok=False)
        ledgers.scientific_custody = TransactionalHashChainCustodyV3(
            scientific_root / "provider",
            ledger_kind="scientific_provider",
            allowed_logical_call_kind="scientific",
        )
        ledgers.http_error_custody = TransactionalHashChainCustodyV3(
            scientific_root / "http_error_attempts",
            ledger_kind="http_error_custody",
            allowed_logical_call_kind="http_error_attempt",
        )

        def commit_http_error(item: R2RLiveTransportAttemptCustodyV1) -> None:
            assert ledgers.http_error_custody is not None
            payload = item.to_dict()
            ledgers.http_error_custody.append(
                logical_call_kind="http_error_attempt",
                slot_identity=str(payload["record_hash"]),
                payload=payload,
            )

        transport = R2RLiveOpenAIChatCompletionsTransportV1(
            api_key=credential,
            http_error_custody_committer=commit_http_error,
            require_durable_http_error_custody=True,
        )
        ledgers.transport = transport
        ledgers.provider = TransactionalScientificProviderLedgerV3(
            ledgers.scientific_custody,
            attempt_supplier=lambda: transport.attempt_custody,
        )
        ledgers.proposal = DurableConstructionProposalLedgerV1(
            scientific_root / "proposals_working.jsonl"
        )
        ledgers.outcome = DurableConstructionOutcomeLedgerV1(
            scientific_root / "outcomes_working.jsonl"
        )
        ledgers.direct_number = DurableDirectNumberLedgerV1(
            scientific_root / "direct_working.jsonl"
        )
        return transport

    def e1_loader(roots: GuardedR2RRootsV1) -> tuple[Any, ...]:
        git_source: R2RGitSourceContextV1 = state["git_source"]
        schedule = tuple(
            git_source.public_preflight["schedule"]["relation_identities"]
        )
        return tuple(
            load_real_evidence_schedule_v1(
                private_ledger_path=roots.e1_private_root / PRIVATE_LEDGER_FILE,
                public_cohort=git_source.public_preflight["cohort"],
                relation_identities=schedule,
            )
        )

    def scientific_runner(
        evidence: tuple[Any, ...],
        transport: Any,
        ledgers: R2RFreshLiveLedgersV1,
        integrity: R2RPostContactIntegrityGuardV1,
    ) -> Any:
        git_source: R2RGitSourceContextV1 = state["git_source"]
        if not all((ledgers.provider, ledgers.proposal, ledgers.outcome, ledgers.direct_number)):
            raise TASK039E3R2RLiveExecutionError("R2R scientific ledgers are unavailable")
        schedule = tuple(
            git_source.public_preflight["schedule"]["relation_identities"]
        )
        try:
            return run_injected_r2r_scientific_cohort_v1(
                relation_identities=schedule,
                evidence_records=evidence,
                transport=transport,
                ledgers=ScientificLedgersV2(
                    provider=ledgers.provider,
                    proposal=ledgers.proposal,
                    outcome=ledgers.outcome,
                    direct_number=ledgers.direct_number,
                ),
                progress=lambda _message: integrity.assert_unchanged_before_provider_attempt(),
            )
        finally:
            ledgers.close_working_ledgers()

    def success_finalizer(
        science: Any,
        auth: R2RAuthorityContextV1,
        git_source: R2RGitSourceContextV1,
        _forensic: R2RForensicProtocolContextV1,
        capability: ValidatedCapabilityReuseR2RV1,
        ledgers: R2RFreshLiveLedgersV1,
        integrity: R2RPostContactIntegrityGuardV1,
        roots: GuardedR2RRootsV1,
    ) -> Mapping[str, Any]:
        integrity.assert_unchanged_before_provider_attempt()
        if ledgers.scientific_custody is None or ledgers.transport is None:
            raise TASK039E3R2RLiveExecutionError("R2R final custody is unavailable")
        finalized = finalize_successful_r2r_scientific_result_v1(
            repository_root=repository,
            recovery_private_root=roots.recovery_private_root,
            public_output_root=roots.public_output_root,
            protected_private_roots=(roots.e1_private_root, roots.capability_ledger_root),
            execution_commit=auth.validated.implementation_commit_a,
            source_manifest_hash=auth.validated.implementation_source_manifest_hash,
            authorization_hash=auth.validated.self_hash,
            configuration_fingerprint=integrity.snapshot.fingerprint,
            postcontact_integrity_status="verified_unchanged",
            authority_bindings=result_authority_bindings_from_r2r_authorization_v1(
                auth.document
            ),
            capability_reuse_binding=build_capability_reuse_binding_r2r_v1(capability),
            scientific_provider_binding=(
                provider_custody_binding_from_reconstruction_r2r_v1(
                    ledgers.scientific_custody.reconstruct()
                )
            ),
            scientific_provider_records=[
                record["payload"] for record in ledgers.scientific_custody.records
            ],
            proposal_records=ledgers.proposal.records if ledgers.proposal else (),
            outcome_records=ledgers.outcome.records if ledgers.outcome else (),
            direct_number_records=(
                ledgers.direct_number.records if ledgers.direct_number else ()
            ),
            typed_accounting=_typed_accounting(science, ledgers.transport),
            scientific_source_hashes=git_source.scientific_source_hashes,
        )
        return {
            "status": finalized.status,
            "execution_receipt_hash": finalized.execution_receipt_hash,
        }

    def failure_finalizer(
        failure: BaseException, roots: GuardedR2RRootsV1
    ) -> Mapping[str, Any]:
        ledgers: R2RFreshLiveLedgersV1 | None = state.get("ledgers")
        if ledgers is not None:
            try:
                ledgers.close_working_ledgers()
            except Exception:
                pass
        auth: R2RAuthorityContextV1 = state["authorization"]
        integrity: R2RPostContactIntegrityGuardV1 = state["integrity"]
        transport = ledgers.transport if ledgers is not None else None
        provider_records = ledgers.provider.records if ledgers and ledgers.provider else ()
        provider_observation = _failure_provider_observation(provider_records)
        context = {
            "execution_commit": auth.validated.implementation_commit_a,
            "source_manifest_hash": auth.validated.implementation_source_manifest_hash,
            "authorization_hash": auth.validated.self_hash,
            "configuration_fingerprint": integrity.snapshot.fingerprint,
            "capability_reuse_status": "PASS_REUSED",
            "capability_provider_ledger_head_hash": str(
                auth.document["capability_provider_ledger_head_hash"]
            ),
            "scientific_provider_ledger_head_hash": (
                ledgers.scientific_custody.authoritative_head_hash
                if ledgers and ledgers.scientific_custody
                else None
            ),
            "last_attempted_scientific_slot": provider_observation[
                "last_attempted_scientific_slot"
            ],
            "completed_r2r_scientific_logical_calls": len(provider_records),
            "r2r_scientific_transport_attempts": (
                len(transport.attempt_custody) if transport is not None else 0
            ),
            "proposal_committed_count": (
                len(ledgers.proposal.records) if ledgers and ledgers.proposal else 0
            ),
            "outcome_committed_count": (
                len(ledgers.outcome.records) if ledgers and ledgers.outcome else 0
            ),
            "direct_number_committed_count": (
                len(ledgers.direct_number.records)
                if ledgers and ledgers.direct_number
                else 0
            ),
            "postcontact_integrity_status": _postcontact_failure_integrity_status(
                transport, integrity
            ),
            "actual_returned_model": provider_observation["actual_returned_model"],
            "actual_response_id": provider_observation["actual_response_id"],
            "terminal_slot_state": provider_observation["terminal_slot_state"],
        }
        return write_terminal_failure_receipt_r2r_v1(
            destination=roots.public_output_root / FAILURE_ARTIFACT_NAME,
            failure_stage="r2r_scientific_execution_or_finalization",
            failure=failure,
            context=context,
        )

    return R2RLivePathDependenciesV1(
        authorization_guard=authorization_guard,
        git_source_manifest_guard=git_source_guard,
        forensic_protocol_guard=forensic_guard,
        capability_reuse_guard=capability_guard,
        execution_root_guard=root_guard,
        fresh_ledger_guard=fresh_guard,
        integrity_snapshot_guard=integrity_guard,
        credential_loader=lambda: (_ for _ in ()).throw(
            TASK039E3R2RLiveExecutionError("runner must install sole credential loader")
        ),
        transport_factory=transport_factory,
        e1_loader=e1_loader,
        scientific_runner=scientific_runner,
        success_finalizer=success_finalizer,
        failure_finalizer=failure_finalizer,
    )


__all__ = [
    "INDEPENDENT_AUDIT_PASS_STATUS",
    "R2RAuthorityContextV1",
    "R2RForensicProtocolContextV1",
    "R2RFreshLiveLedgersV1",
    "R2RGitSourceContextV1",
    "TASK039E3R2RLiveExecutionError",
    "_failure_provider_observation",
    "_postcontact_failure_integrity_status",
    "build_r2r_live_dependencies_v1",
]
