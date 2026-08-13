"""Dependency-ordered R2R live-path boundary.

This module contains no provider client, environment access, capability probe,
or private-data loader.  The future executable runner supplies those operations
as narrow callbacks.  Keeping the boundary explicit makes it possible to prove
offline that every authority/root/custody guard runs before the sole credential
lookup and that E1 remains unread until fresh ledgers and integrity state exist.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Generic, TypeVar

from paperworks.v6.common import require_sha256, stable_hash_v1
from paperworks.v6.task039e3_execution_prep_v1 import MockProviderTransportV1
from paperworks.v6.task039e3_r2r_authorization_v1 import (
    DIRECT_NUMBER_PROMPT_HASH,
    DIRECT_NUMBER_SCHEMA_HASH,
    EXACT_ENDPOINT,
    EXACT_MODEL,
    MAIN_PROMPT_HASH,
    RECOVERY_SCHEMA_V2_HASH,
    RELATION_SCHEDULE_HASH,
    T2_FOLLOWUP_PROMPT_HASH,
)
from paperworks.v6.task039e3_r2r_failure_finalizer_v1 import (
    TASK039E3R2RFailureReceiptDoubleFault,
    TASK039E3R2RGuardedExecutionFailure,
)
from paperworks.v6.task039e3_r2r_execution_v1 import (
    HISTORICAL_ORIGINAL_R2_SCIENTIFIC_LOGICAL_CALLS,
    HISTORICAL_PARTIAL_R2R_SCIENTIFIC_LOGICAL_CALLS,
    HISTORICAL_SCIENTIFIC_LOGICAL_CALLS_TOTAL,
    HISTORICAL_ZERO_CONTACT_R2R_SCIENTIFIC_LOGICAL_CALLS,
)


class TASK039E3R2RPrecontactError(ValueError):
    """A future R2R execution boundary was not satisfied."""


class TASK039E3R2RDoubleFaultError(RuntimeError):
    """Execution failed and sanitized failure persistence also failed."""


R2R_SCIENTIFIC_ACCOUNTING_BEHAVIOR_HASH_V1 = stable_hash_v1(
    {
        "historical_aborted_r2_scientific_logical_calls": (
            HISTORICAL_ORIGINAL_R2_SCIENTIFIC_LOGICAL_CALLS
        ),
        "historical_original_r2_scientific_logical_calls": (
            HISTORICAL_ORIGINAL_R2_SCIENTIFIC_LOGICAL_CALLS
        ),
        "historical_zero_contact_r2r_scientific_logical_calls": (
            HISTORICAL_ZERO_CONTACT_R2R_SCIENTIFIC_LOGICAL_CALLS
        ),
        "historical_partial_r2r_scientific_logical_calls": (
            HISTORICAL_PARTIAL_R2R_SCIENTIFIC_LOGICAL_CALLS
        ),
        "historical_scientific_logical_calls_total": (
            HISTORICAL_SCIENTIFIC_LOGICAL_CALLS_TOTAL
        ),
        "historical_partial_records_reused": 0,
        "relations": 42,
        "t1_logical_calls": 42,
        "t1b_logical_calls": 126,
        "t2_logical_calls_minimum": 42,
        "t2_logical_calls_maximum": 126,
        "direct_number_logical_calls": 42,
        "r2r_scientific_logical_calls_minimum": 252,
        "r2r_scientific_logical_calls_maximum": 336,
        "lifetime_accounting": "6_plus_actual_r2r_scientific_logical_calls",
        "scientific_concurrency": 1,
        "scientific_generation_retries": 0,
    }
)


@dataclass(frozen=True)
class GuardedR2RRootsV1:
    repository_root: Path
    e1_private_root: Path
    capability_ledger_root: Path
    recovery_private_root: Path
    public_output_root: Path


@dataclass(frozen=True)
class R2RLivePathResultV1:
    terminal_result: Any
    completed_stage_order: tuple[str, ...]
    credential_loader_calls: int = 1
    capability_probe_calls: int = 0
    historical_partial_records_reused: int = 0


@dataclass(frozen=True)
class R2RSourceBlobIdentityV1:
    repository_path: str
    git_blob_sha: str
    sha256: str


@dataclass(frozen=True)
class R2RObservedIntegrityStateV1:
    """All material execution inputs that remain frozen after contact."""

    execution_commit: str
    source_manifest_hash: str
    source_blobs: tuple[R2RSourceBlobIdentityV1, ...]
    authorization_hash: str
    recovery_main_provider_schema_v2_hash: str
    main_prompt_hash: str
    t2_followup_prompt_hash: str
    direct_number_prompt_hash: str
    direct_number_schema_hash: str
    exact_model: str
    endpoint: str
    sampling_configuration_hash: str
    timeout_seconds: float
    retry_policy_hash: str
    relation_schedule_hash: str
    scientific_concurrency: int
    scientific_call_budget_hash: str
    scientific_accounting_behavior_hash: str
    recovery_execution_configuration_hash: str


@dataclass(frozen=True)
class R2RIntegritySnapshotV1:
    state: R2RObservedIntegrityStateV1
    fingerprint: str


def _validate_integrity_state_v1(state: R2RObservedIntegrityStateV1) -> None:
    if len(state.execution_commit) != 40 or any(
        char not in "0123456789abcdef" for char in state.execution_commit
    ):
        raise TASK039E3R2RPrecontactError("R2R execution commit is invalid")
    hash_values = (
        state.source_manifest_hash,
        state.authorization_hash,
        state.recovery_main_provider_schema_v2_hash,
        state.main_prompt_hash,
        state.t2_followup_prompt_hash,
        state.direct_number_prompt_hash,
        state.direct_number_schema_hash,
        state.sampling_configuration_hash,
        state.retry_policy_hash,
        state.relation_schedule_hash,
        state.scientific_call_budget_hash,
        state.scientific_accounting_behavior_hash,
        state.recovery_execution_configuration_hash,
    )
    for index, value in enumerate(hash_values):
        try:
            require_sha256(value, f"R2R integrity hash {index}")
        except (TypeError, ValueError) as exc:
            raise TASK039E3R2RPrecontactError("R2R integrity hash is invalid") from exc
    expected = {
        "recovery_main_provider_schema_v2_hash": RECOVERY_SCHEMA_V2_HASH,
        "main_prompt_hash": MAIN_PROMPT_HASH,
        "t2_followup_prompt_hash": T2_FOLLOWUP_PROMPT_HASH,
        "direct_number_prompt_hash": DIRECT_NUMBER_PROMPT_HASH,
        "direct_number_schema_hash": DIRECT_NUMBER_SCHEMA_HASH,
        "exact_model": EXACT_MODEL,
        "endpoint": EXACT_ENDPOINT,
        "timeout_seconds": 30.0,
        "relation_schedule_hash": RELATION_SCHEDULE_HASH,
        "scientific_concurrency": 1,
        "scientific_accounting_behavior_hash": (
            R2R_SCIENTIFIC_ACCOUNTING_BEHAVIOR_HASH_V1
        ),
    }
    for field, exact in expected.items():
        if getattr(state, field) != exact:
            raise TASK039E3R2RPrecontactError(f"R2R integrity {field} differs")
    if not state.source_blobs:
        raise TASK039E3R2RPrecontactError("R2R source identities are absent")
    if len({item.repository_path for item in state.source_blobs}) != len(
        state.source_blobs
    ):
        raise TASK039E3R2RPrecontactError("R2R source identities are duplicated")
    for item in state.source_blobs:
        if (
            not item.repository_path
            or len(item.git_blob_sha) != 40
            or any(char not in "0123456789abcdef" for char in item.git_blob_sha)
        ):
            raise TASK039E3R2RPrecontactError("R2R source identity is invalid")
        try:
            require_sha256(item.sha256, "R2R source byte hash")
        except (TypeError, ValueError) as exc:
            raise TASK039E3R2RPrecontactError(
                "R2R source byte hash is invalid"
            ) from exc


def capture_r2r_integrity_snapshot_v1(
    state: R2RObservedIntegrityStateV1,
) -> R2RIntegritySnapshotV1:
    _validate_integrity_state_v1(state)
    return R2RIntegritySnapshotV1(
        state=state,
        fingerprint=stable_hash_v1(asdict(state)),
    )


@dataclass(frozen=True)
class R2RPostContactIntegrityGuardV1:
    snapshot: R2RIntegritySnapshotV1
    observed_state_loader: Callable[[], R2RObservedIntegrityStateV1]
    _blocked: bool = field(default=False, init=False, compare=False)

    @property
    def blocked(self) -> bool:
        return self._blocked

    def assert_unchanged_before_provider_attempt(self) -> None:
        if self._blocked:
            raise TASK039E3R2RPrecontactError(
                "R2R execution is permanently blocked after integrity drift"
            )
        try:
            observed = self.observed_state_loader()
            _validate_integrity_state_v1(observed)
            changed = stable_hash_v1(asdict(observed)) != self.snapshot.fingerprint
        except Exception:
            object.__setattr__(self, "_blocked", True)
            raise
        if changed:
            object.__setattr__(self, "_blocked", True)
            raise TASK039E3R2RPrecontactError(
                "R2R post-contact integrity changed before provider attempt"
            )

    def invoke_guarded_provider_attempt(self, attempt: Callable[[], _TerminalT]) -> _TerminalT:
        self.assert_unchanged_before_provider_attempt()
        return attempt()


@dataclass(frozen=True)
class R2RIntegrityGuardedTransportV1(MockProviderTransportV1):
    """Require the complete R2R fingerprint before every provider attempt."""

    transport: Any
    integrity_guard: R2RPostContactIntegrityGuardV1

    @property
    def calls(self) -> int:
        return self.transport.calls

    @property
    def request_hashes(self) -> tuple[str, ...]:
        return self.transport.request_hashes

    @property
    def attempt_custody(self) -> tuple[Any, ...]:
        return self.transport.attempt_custody

    def send(self, request: Any) -> Any:
        return self.integrity_guard.invoke_guarded_provider_attempt(
            lambda: self.transport.send(request)
        )


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _resolved_existing_directory(value: str | Path, label: str) -> Path:
    raw = Path(value)
    if not raw.is_absolute():
        raise TASK039E3R2RPrecontactError(f"{label} must be absolute")
    if any(part == ".." for part in raw.parts):
        raise TASK039E3R2RPrecontactError(f"{label} contains traversal")
    cursor = raw
    while True:
        is_junction = getattr(cursor, "is_junction", lambda: False)
        if cursor.is_symlink() or is_junction():
            raise TASK039E3R2RPrecontactError(
                f"{label} cannot traverse a symlink or junction"
            )
        if cursor.parent == cursor:
            break
        cursor = cursor.parent
    try:
        resolved = raw.resolve(strict=True)
    except OSError as exc:
        raise TASK039E3R2RPrecontactError(f"{label} is unavailable") from exc
    if not resolved.is_dir():
        raise TASK039E3R2RPrecontactError(f"{label} must be a directory")
    return resolved


def validate_r2r_execution_roots_v1(
    *,
    repository_root: str | Path,
    e1_private_root: str | Path,
    capability_ledger_root: str | Path,
    recovery_private_root: str | Path,
    public_output_root: str | Path,
) -> GuardedR2RRootsV1:
    """Validate future roots without opening private content.

    The recovery and public roots must already exist and be empty.  A separate
    offline-audited setup step may create them; this validator never deletes,
    cleans, or replaces execution state.
    """

    roots = GuardedR2RRootsV1(
        repository_root=_resolved_existing_directory(repository_root, "repository root"),
        e1_private_root=_resolved_existing_directory(e1_private_root, "E1 private root"),
        capability_ledger_root=_resolved_existing_directory(
            capability_ledger_root, "capability ledger root"
        ),
        recovery_private_root=_resolved_existing_directory(
            recovery_private_root, "R2R recovery private root"
        ),
        public_output_root=_resolved_existing_directory(
            public_output_root, "R2R public output root"
        ),
    )
    values = tuple(roots.__dict__.values())
    if len(set(values)) != len(values):
        raise TASK039E3R2RPrecontactError("R2R execution roots must be distinct")
    for index, left in enumerate(values):
        for right in values[index + 1 :]:
            if _is_relative_to(left, right) or _is_relative_to(right, left):
                raise TASK039E3R2RPrecontactError(
                    "R2R execution roots must not be nested"
                )
    if any(_is_relative_to(item, roots.repository_root) for item in values[1:]):
        raise TASK039E3R2RPrecontactError(
            "R2R execution roots must remain outside Git"
        )
    for label, path in (
        ("R2R recovery private root", roots.recovery_private_root),
        ("R2R public output root", roots.public_output_root),
    ):
        try:
            next(path.iterdir())
        except StopIteration:
            pass
        else:
            raise TASK039E3R2RPrecontactError(f"{label} must be empty")
    return roots


_AuthorizationT = TypeVar("_AuthorizationT")
_GitSourceT = TypeVar("_GitSourceT")
_ForensicT = TypeVar("_ForensicT")
_CapabilityT = TypeVar("_CapabilityT")
_LedgersT = TypeVar("_LedgersT")
_SnapshotT = TypeVar("_SnapshotT")
_CredentialT = TypeVar("_CredentialT")
_TransportT = TypeVar("_TransportT")
_EvidenceT = TypeVar("_EvidenceT")
_ScienceT = TypeVar("_ScienceT")
_TerminalT = TypeVar("_TerminalT")


@dataclass(frozen=True)
class R2RLivePathDependenciesV1(
    Generic[
        _AuthorizationT,
        _GitSourceT,
        _ForensicT,
        _CapabilityT,
        _LedgersT,
        _SnapshotT,
        _CredentialT,
        _TransportT,
        _EvidenceT,
        _ScienceT,
        _TerminalT,
    ]
):
    authorization_guard: Callable[[], _AuthorizationT]
    git_source_manifest_guard: Callable[[_AuthorizationT], _GitSourceT]
    forensic_protocol_guard: Callable[[_AuthorizationT, _GitSourceT], _ForensicT]
    capability_reuse_guard: Callable[[_AuthorizationT], _CapabilityT]
    execution_root_guard: Callable[[], GuardedR2RRootsV1]
    fresh_ledger_guard: Callable[[GuardedR2RRootsV1], _LedgersT]
    integrity_snapshot_guard: Callable[
        [
            _AuthorizationT,
            _GitSourceT,
            _ForensicT,
            _CapabilityT,
            GuardedR2RRootsV1,
            _LedgersT,
        ],
        _SnapshotT,
    ]
    credential_loader: Callable[[], _CredentialT]
    transport_factory: Callable[[_CredentialT, _SnapshotT, _LedgersT], _TransportT]
    e1_loader: Callable[[GuardedR2RRootsV1], _EvidenceT]
    scientific_runner: Callable[[_EvidenceT, _TransportT, _LedgersT, _SnapshotT], _ScienceT]
    success_finalizer: Callable[
        [
            _ScienceT,
            _AuthorizationT,
            _GitSourceT,
            _ForensicT,
            _CapabilityT,
            _LedgersT,
            _SnapshotT,
            GuardedR2RRootsV1,
        ],
        _TerminalT,
    ]
    failure_finalizer: Callable[[BaseException, GuardedR2RRootsV1], Any]


def run_r2r_live_execution_path_v1(
    dependencies: R2RLivePathDependenciesV1[Any, ...],
    *,
    stage_sink: Callable[[str], None] | None = None,
) -> R2RLivePathResultV1:
    """Execute the future dependency graph with one credential boundary.

    There is deliberately no capability-probe callback.  Capability authority
    can only be supplied by validating the already durable PASS custody.
    """

    stages: list[str] = []

    def mark(value: str) -> None:
        stages.append(value)
        if stage_sink is not None:
            stage_sink(value)

    authorization = dependencies.authorization_guard()
    mark("authorization_validated")
    git_source = dependencies.git_source_manifest_guard(authorization)
    mark("git_and_source_manifest_validated")
    forensic = dependencies.forensic_protocol_guard(authorization, git_source)
    mark("forensic_and_protocol_authority_validated")
    capability = dependencies.capability_reuse_guard(authorization)
    mark("durable_capability_pass_reused")
    roots = dependencies.execution_root_guard()
    mark("execution_roots_validated")
    ledgers = dependencies.fresh_ledger_guard(roots)
    mark("fresh_empty_ledgers_validated_before_e1")
    snapshot = dependencies.integrity_snapshot_guard(
        authorization, git_source, forensic, capability, roots, ledgers
    )
    if not isinstance(snapshot, R2RPostContactIntegrityGuardV1):
        raise TASK039E3R2RPrecontactError(
            "R2R integrity guard is not armed before the credential boundary"
        )
    mark("postcontact_integrity_snapshot_prepared")

    credential = dependencies.credential_loader()
    mark("sole_credential_lookup_completed")
    try:
        raw_transport = dependencies.transport_factory(credential, snapshot, ledgers)
        transport = R2RIntegrityGuardedTransportV1(raw_transport, snapshot)
        mark("r2r_transport_constructed")
        evidence = dependencies.e1_loader(roots)
        mark("e1_loaded_after_credential_and_fresh_ledgers")
        science = dependencies.scientific_runner(evidence, transport, ledgers, snapshot)
        mark("fresh_full_scientific_cohort_completed")
        terminal = dependencies.success_finalizer(
            science,
            authorization,
            git_source,
            forensic,
            capability,
            ledgers,
            snapshot,
            roots,
        )
        mark("terminal_success_receipt_verified")
    except BaseException as failure:
        try:
            receipt = dependencies.failure_finalizer(failure, roots)
        except BaseException as persistence_failure:
            raise TASK039E3R2RFailureReceiptDoubleFault(
                failure, persistence_failure
            ) from failure
        raise TASK039E3R2RGuardedExecutionFailure(failure, receipt) from failure
    return R2RLivePathResultV1(
        terminal_result=terminal,
        completed_stage_order=tuple(stages),
    )


__all__ = [
    "GuardedR2RRootsV1",
    "R2RIntegritySnapshotV1",
    "R2RIntegrityGuardedTransportV1",
    "R2RLivePathDependenciesV1",
    "R2RLivePathResultV1",
    "R2RObservedIntegrityStateV1",
    "R2RPostContactIntegrityGuardV1",
    "R2RSourceBlobIdentityV1",
    "R2R_SCIENTIFIC_ACCOUNTING_BEHAVIOR_HASH_V1",
    "TASK039E3R2RDoubleFaultError",
    "TASK039E3R2RPrecontactError",
    "capture_r2r_integrity_snapshot_v1",
    "run_r2r_live_execution_path_v1",
    "validate_r2r_execution_roots_v1",
]
