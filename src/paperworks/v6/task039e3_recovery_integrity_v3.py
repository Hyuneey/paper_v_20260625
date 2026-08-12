"""Deterministic post-contact integrity guard for TASK-039E3 R1D2.

The module is deliberately I/O agnostic.  An execution coordinator captures
one complete pre-contact observation and injects a loader that reconstructs
that observation from current Git/configuration state.  The guard checks the
loader before and after every provider attempt and at every later authority
boundary.  It has no credential reader, provider client, evidence loader, or
scientific implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1, sha256
import math
import re
from typing import Any, Callable, Mapping, Sequence, TypeVar

from paperworks.v6.common import freeze_json, stable_hash_v1, thaw_json
from paperworks.v6.task039e2_execution_configuration_v1 import EXACT_MODEL
from paperworks.v6.task039e3_execution_prep_v1 import EXECUTION_SCHEDULE_HASH
from paperworks.v6.task039e3_recovery_capability_v1 import (
    RECOVERY_CAPABILITY_PROMPT_SHA256,
    RECOVERY_CAPABILITY_SCHEMA_SHA256,
)


URLOPEN_TIMEOUT_SECONDS = 30.0
TRANSPORT_RETRY_DELAYS_SECONDS = (2, 4)
SCIENTIFIC_CONCURRENCY = 1
MINIMUM_SCIENTIFIC_LOGICAL_CALLS = 252
MAXIMUM_SCIENTIFIC_LOGICAL_CALLS = 336

_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
_GIT_OBJECT_RE = re.compile(r"^[a-f0-9]{40}$")

_SAMPLING_CONFIGURATION_MUTABLE: dict[str, Any] = {
    "model": EXACT_MODEL,
    "reasoning_effort": "none",
    "temperature": 0.7,
    "top_p": 1.0,
    "max_completion_tokens": 1024,
    "n": 1,
    "seed": None,
    "seed_used": False,
    "seed_determinism_claimed": False,
    "presence_penalty": 0,
    "frequency_penalty": 0,
    "stream": False,
    "store": False,
    "tools": [],
    "tool_choice": None,
}
FROZEN_SAMPLING_CONFIGURATION_V3: Mapping[str, Any] = freeze_json(
    _SAMPLING_CONFIGURATION_MUTABLE
)
FROZEN_SAMPLING_CONFIGURATION_HASH_V3 = stable_hash_v1(
    FROZEN_SAMPLING_CONFIGURATION_V3
)

_RETRY_POLICY_MUTABLE: dict[str, Any] = {
    "schema_version": "1.0.0",
    "artifact_type": "task039e2_transport_retry_policy_v1",
    "maximum_transport_retries_per_request": 2,
    "scientific_generation_retries": 0,
    "retryable_no_response_outcomes": [
        "connection_failure",
        "connection_reset",
        "timeout_before_response",
        "http_429",
        "http_5xx",
    ],
    "non_retryable_outcomes": [
        "http_400",
        "http_401",
        "http_403",
        "provider_refusal",
        "schema_invalid_response",
        "malformed_scientific_output",
        "verifier_rejection",
        "low_quality_proposal",
    ],
    "fixed_retry_delays_seconds": [2, 4],
    "retry_after_429_policy": "valid_retry_after_overrides_corresponding_fixed_delay",
    "retry_after_validity_policy": "provider_header_must_parse_as_standard_retry_after",
    "response_failures_consume_scientific_call": True,
    "retry_exhaustion_outcome": "abort_full_scientific_run",
    "relation_skip_allowed": False,
}
FROZEN_RETRY_POLICY_V3: Mapping[str, Any] = freeze_json(_RETRY_POLICY_MUTABLE)
FROZEN_RETRY_POLICY_HASH_V3 = stable_hash_v1(FROZEN_RETRY_POLICY_V3)

_SCIENTIFIC_CALL_BUDGET_MUTABLE: dict[str, Any] = {
    "relation_count": 42,
    "t1_logical_calls": 42,
    "t1b_logical_calls": 126,
    "minimum_t2_logical_calls": 42,
    "maximum_t2_logical_calls": 126,
    "direct_number_logical_calls": 42,
    "minimum_scientific_logical_calls": MINIMUM_SCIENTIFIC_LOGICAL_CALLS,
    "maximum_scientific_logical_calls": MAXIMUM_SCIENTIFIC_LOGICAL_CALLS,
    "scientific_call_formula": "210_plus_actual_t2_calls",
    "scientific_concurrency": SCIENTIFIC_CONCURRENCY,
    "scientific_generation_retries": 0,
    "local_compatibility_slots": 0,
}
FROZEN_SCIENTIFIC_CALL_BUDGET_V3: Mapping[str, Any] = freeze_json(
    _SCIENTIFIC_CALL_BUDGET_MUTABLE
)
FROZEN_SCIENTIFIC_CALL_BUDGET_HASH_V3 = stable_hash_v1(
    FROZEN_SCIENTIFIC_CALL_BUDGET_V3
)


class TASK039E3RecoveryIntegrityV3Error(RuntimeError):
    """Raised when the immutable R1D2 execution boundary differs."""


def _require_sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise TASK039E3RecoveryIntegrityV3Error(
            f"{name} must be a lowercase SHA-256"
        )
    return value


def _require_git_object(value: object, name: str) -> str:
    if not isinstance(value, str) or _GIT_OBJECT_RE.fullmatch(value) is None:
        raise TASK039E3RecoveryIntegrityV3Error(
            f"{name} must be an exact 40-character Git object id"
        )
    return value


def _require_repository_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise TASK039E3RecoveryIntegrityV3Error("source path must be non-empty")
    normalized = value.replace("\\", "/")
    parts = normalized.split("/")
    if (
        normalized.startswith("/")
        or re.match(r"^[A-Za-z]:", normalized) is not None
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise TASK039E3RecoveryIntegrityV3Error(
            "source path must be a traversal-free repository-relative path"
        )
    return normalized


def git_blob_sha1_v3(content: bytes) -> str:
    """Return the SHA-1 Git blob id for exact bytes without invoking Git."""

    if not isinstance(content, bytes):
        raise TASK039E3RecoveryIntegrityV3Error("source content must be bytes")
    header = f"blob {len(content)}\0".encode("ascii")
    return sha1(header + content).hexdigest()


@dataclass(frozen=True, order=True)
class FrozenSourceBlobV3:
    """One exact source blob bound into the execution snapshot."""

    repository_path: str
    git_blob_sha: str
    sha256: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "repository_path", _require_repository_path(self.repository_path)
        )
        _require_git_object(self.git_blob_sha, "source Git blob")
        _require_sha256(self.sha256, "source byte hash")

    @classmethod
    def from_bytes(cls, repository_path: str, content: bytes) -> "FrozenSourceBlobV3":
        return cls(
            repository_path=repository_path,
            git_blob_sha=git_blob_sha1_v3(content),
            sha256=sha256(content).hexdigest(),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "repository_path": self.repository_path,
            "git_blob_sha": self.git_blob_sha,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class ObservedExecutionIntegrityStateV3:
    """A complete observation of active source and execution configuration."""

    head_commit: str
    source_manifest_hash: str
    source_blobs: tuple[FrozenSourceBlobV3, ...]
    exact_model: str
    capability_prompt_hash: str
    capability_schema_hash: str
    sampling_configuration: Mapping[str, Any]
    sampling_configuration_hash: str
    urlopen_timeout_seconds: float
    retry_wait_seconds: tuple[int, int]
    retry_policy: Mapping[str, Any]
    retry_policy_hash: str
    relation_schedule_hash: str
    scientific_concurrency: int
    scientific_call_budget: Mapping[str, Any]
    scientific_call_budget_hash: str
    scientific_accounting_behavior_hash: str
    r2_authorization_hash: str

    def __post_init__(self) -> None:
        _require_git_object(self.head_commit, "execution Git HEAD")
        for name in (
            "source_manifest_hash",
            "capability_prompt_hash",
            "capability_schema_hash",
            "sampling_configuration_hash",
            "retry_policy_hash",
            "relation_schedule_hash",
            "scientific_call_budget_hash",
            "scientific_accounting_behavior_hash",
            "r2_authorization_hash",
        ):
            _require_sha256(getattr(self, name), name)
        if not self.source_blobs:
            raise TASK039E3RecoveryIntegrityV3Error(
                "at least one active source blob is required"
            )
        blobs = tuple(sorted(self.source_blobs, key=lambda item: item.repository_path))
        if len({item.repository_path for item in blobs}) != len(blobs):
            raise TASK039E3RecoveryIntegrityV3Error(
                "active source paths must be unique"
            )
        object.__setattr__(self, "source_blobs", blobs)
        object.__setattr__(
            self, "sampling_configuration", freeze_json(self.sampling_configuration)
        )
        object.__setattr__(self, "retry_policy", freeze_json(self.retry_policy))
        object.__setattr__(
            self, "scientific_call_budget", freeze_json(self.scientific_call_budget)
        )
        if type(self.urlopen_timeout_seconds) is not float or not math.isfinite(
            self.urlopen_timeout_seconds
        ):
            raise TASK039E3RecoveryIntegrityV3Error(
                "urlopen timeout must be a finite number"
            )
        if (
            len(self.retry_wait_seconds) != 2
            or any(type(value) is not int for value in self.retry_wait_seconds)
        ):
            raise TASK039E3RecoveryIntegrityV3Error(
                "retry waits must be two exact integer seconds values"
            )
        if type(self.scientific_concurrency) is not int:
            raise TASK039E3RecoveryIntegrityV3Error(
                "scientific concurrency must be an integer"
            )

    def to_fingerprint_payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "task039e3_execution_integrity_snapshot_v3",
            "head_commit": self.head_commit,
            "source_manifest_hash": self.source_manifest_hash,
            "source_blobs": [item.to_dict() for item in self.source_blobs],
            "exact_model": self.exact_model,
            "capability_prompt_hash": self.capability_prompt_hash,
            "capability_schema_hash": self.capability_schema_hash,
            "sampling_configuration": thaw_json(self.sampling_configuration),
            "sampling_configuration_hash": self.sampling_configuration_hash,
            "urlopen_timeout_seconds": float(self.urlopen_timeout_seconds),
            "retry_wait_seconds": list(self.retry_wait_seconds),
            "retry_policy": thaw_json(self.retry_policy),
            "retry_policy_hash": self.retry_policy_hash,
            "relation_schedule_hash": self.relation_schedule_hash,
            "scientific_concurrency": self.scientific_concurrency,
            "scientific_call_budget": thaw_json(self.scientific_call_budget),
            "scientific_call_budget_hash": self.scientific_call_budget_hash,
            "scientific_accounting_behavior_hash": (
                self.scientific_accounting_behavior_hash
            ),
            "r2_authorization_hash": self.r2_authorization_hash,
        }

    @property
    def execution_configuration_fingerprint(self) -> str:
        return stable_hash_v1(self.to_fingerprint_payload())


def build_frozen_execution_integrity_state_v3(
    *,
    head_commit: str,
    source_manifest_hash: str,
    source_blobs: Sequence[FrozenSourceBlobV3],
    scientific_accounting_behavior_hash: str,
    r2_authorization_hash: str,
) -> ObservedExecutionIntegrityStateV3:
    """Build the exact frozen state while leaving live observation to the caller."""

    state = ObservedExecutionIntegrityStateV3(
        head_commit=head_commit,
        source_manifest_hash=source_manifest_hash,
        source_blobs=tuple(source_blobs),
        exact_model=EXACT_MODEL,
        capability_prompt_hash=RECOVERY_CAPABILITY_PROMPT_SHA256,
        capability_schema_hash=RECOVERY_CAPABILITY_SCHEMA_SHA256,
        sampling_configuration=FROZEN_SAMPLING_CONFIGURATION_V3,
        sampling_configuration_hash=FROZEN_SAMPLING_CONFIGURATION_HASH_V3,
        urlopen_timeout_seconds=URLOPEN_TIMEOUT_SECONDS,
        retry_wait_seconds=TRANSPORT_RETRY_DELAYS_SECONDS,
        retry_policy=FROZEN_RETRY_POLICY_V3,
        retry_policy_hash=FROZEN_RETRY_POLICY_HASH_V3,
        relation_schedule_hash=EXECUTION_SCHEDULE_HASH,
        scientific_concurrency=SCIENTIFIC_CONCURRENCY,
        scientific_call_budget=FROZEN_SCIENTIFIC_CALL_BUDGET_V3,
        scientific_call_budget_hash=FROZEN_SCIENTIFIC_CALL_BUDGET_HASH_V3,
        scientific_accounting_behavior_hash=scientific_accounting_behavior_hash,
        r2_authorization_hash=r2_authorization_hash,
    )
    validate_initial_integrity_state_v3(state)
    return state


def validate_initial_integrity_state_v3(
    state: ObservedExecutionIntegrityStateV3,
) -> None:
    """Validate every frozen protocol field before credential access."""

    if not isinstance(state, ObservedExecutionIntegrityStateV3):
        raise TASK039E3RecoveryIntegrityV3Error(
            "observed execution integrity state V3 is required"
        )
    exact_values = (
        (state.exact_model, EXACT_MODEL, "exact model"),
        (
            state.capability_prompt_hash,
            RECOVERY_CAPABILITY_PROMPT_SHA256,
            "capability prompt hash",
        ),
        (
            state.capability_schema_hash,
            RECOVERY_CAPABILITY_SCHEMA_SHA256,
            "capability schema hash",
        ),
        (
            thaw_json(state.sampling_configuration),
            thaw_json(FROZEN_SAMPLING_CONFIGURATION_V3),
            "sampling configuration",
        ),
        (
            state.sampling_configuration_hash,
            FROZEN_SAMPLING_CONFIGURATION_HASH_V3,
            "sampling configuration hash",
        ),
        (state.urlopen_timeout_seconds, URLOPEN_TIMEOUT_SECONDS, "timeout"),
        (
            tuple(state.retry_wait_seconds),
            TRANSPORT_RETRY_DELAYS_SECONDS,
            "retry waits",
        ),
        (
            thaw_json(state.retry_policy),
            thaw_json(FROZEN_RETRY_POLICY_V3),
            "retry policy",
        ),
        (state.retry_policy_hash, FROZEN_RETRY_POLICY_HASH_V3, "retry policy hash"),
        (state.relation_schedule_hash, EXECUTION_SCHEDULE_HASH, "schedule hash"),
        (
            state.scientific_concurrency,
            SCIENTIFIC_CONCURRENCY,
            "scientific concurrency",
        ),
        (
            thaw_json(state.scientific_call_budget),
            thaw_json(FROZEN_SCIENTIFIC_CALL_BUDGET_V3),
            "scientific call budget",
        ),
        (
            state.scientific_call_budget_hash,
            FROZEN_SCIENTIFIC_CALL_BUDGET_HASH_V3,
            "scientific call budget hash",
        ),
    )
    for observed, expected, name in exact_values:
        if type(observed) is not type(expected) or observed != expected:
            raise TASK039E3RecoveryIntegrityV3Error(f"{name} differs")
    if stable_hash_v1(state.sampling_configuration) != state.sampling_configuration_hash:
        raise TASK039E3RecoveryIntegrityV3Error(
            "sampling configuration content/hash binding differs"
        )
    if stable_hash_v1(state.retry_policy) != state.retry_policy_hash:
        raise TASK039E3RecoveryIntegrityV3Error(
            "retry policy content/hash binding differs"
        )
    if stable_hash_v1(state.scientific_call_budget) != state.scientific_call_budget_hash:
        raise TASK039E3RecoveryIntegrityV3Error(
            "scientific call budget content/hash binding differs"
        )


def capture_execution_integrity_snapshot_v3(
    state: ObservedExecutionIntegrityStateV3,
) -> "ExecutionIntegritySnapshotV3":
    """Freeze the validated pre-contact state and its canonical fingerprint."""

    validate_initial_integrity_state_v3(state)
    return ExecutionIntegritySnapshotV3(
        state=state,
        execution_configuration_fingerprint=state.execution_configuration_fingerprint,
    )


@dataclass(frozen=True)
class ExecutionIntegritySnapshotV3:
    state: ObservedExecutionIntegrityStateV3
    execution_configuration_fingerprint: str

    def __post_init__(self) -> None:
        validate_initial_integrity_state_v3(self.state)
        _require_sha256(
            self.execution_configuration_fingerprint,
            "execution configuration fingerprint",
        )
        if (
            self.execution_configuration_fingerprint
            != self.state.execution_configuration_fingerprint
        ):
            raise TASK039E3RecoveryIntegrityV3Error(
                "execution configuration fingerprint differs"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.state.to_fingerprint_payload(),
            "execution_configuration_fingerprint": (
                self.execution_configuration_fingerprint
            ),
        }


@dataclass(frozen=True)
class IntegrityCheckV3:
    stage: str
    status: str
    execution_configuration_fingerprint: str


_ResultT = TypeVar("_ResultT")


class PostContactIntegrityGuardV3:
    """Permanent fail-closed guard around all future provider attempts/phases."""

    def __init__(
        self,
        *,
        snapshot: ExecutionIntegritySnapshotV3,
        observed_state_loader: Callable[[], ObservedExecutionIntegrityStateV3],
    ) -> None:
        if not isinstance(snapshot, ExecutionIntegritySnapshotV3):
            raise TASK039E3RecoveryIntegrityV3Error(
                "execution integrity snapshot V3 is required"
            )
        if not callable(observed_state_loader):
            raise TASK039E3RecoveryIntegrityV3Error(
                "observed execution-state loader is required"
            )
        self._snapshot = snapshot
        self._loader = observed_state_loader
        self._blocked = False
        self._failure_stage: str | None = None
        self._provider_contact_started = False
        self._provider_attempts_started = 0
        self._attempt_in_progress = False
        self._checks: list[IntegrityCheckV3] = []

    @property
    def blocked(self) -> bool:
        return self._blocked

    @property
    def execution_configuration_fingerprint(self) -> str:
        return self._snapshot.execution_configuration_fingerprint

    @property
    def postcontact_integrity_status(self) -> str:
        if self._blocked:
            return "failed_changed"
        if not self._provider_contact_started:
            return "not_started"
        return "verified_unchanged"

    @property
    def provider_contact_started(self) -> bool:
        return self._provider_contact_started

    @property
    def provider_attempts_started(self) -> int:
        return self._provider_attempts_started

    @property
    def failure_stage(self) -> str | None:
        return self._failure_stage

    @property
    def checks(self) -> tuple[IntegrityCheckV3, ...]:
        return tuple(self._checks)

    @property
    def automatic_resume_authorized(self) -> bool:
        return False

    @property
    def provider_recontact_authorized(self) -> bool:
        return False

    def _block(self, stage: str, detail: str) -> None:
        self._blocked = True
        if self._failure_stage is None:
            self._failure_stage = stage
        self._checks.append(
            IntegrityCheckV3(
                stage=stage,
                status="integrity_mismatch",
                execution_configuration_fingerprint=(
                    self._snapshot.execution_configuration_fingerprint
                ),
            )
        )
        raise TASK039E3RecoveryIntegrityV3Error(
            f"post-contact integrity mismatch at {stage}: {detail}"
        )

    def assert_integrity(self, stage: str) -> str:
        """Reconstruct and compare all frozen state; permanently block on drift."""

        if not isinstance(stage, str) or not stage:
            raise TASK039E3RecoveryIntegrityV3Error(
                "integrity-check stage must be non-empty"
            )
        if self._blocked:
            raise TASK039E3RecoveryIntegrityV3Error(
                "execution is permanently blocked after integrity mismatch"
            )
        try:
            observed = self._loader()
            if not isinstance(observed, ObservedExecutionIntegrityStateV3):
                raise TASK039E3RecoveryIntegrityV3Error(
                    "observed state loader returned the wrong type"
                )
            observed_fingerprint = observed.execution_configuration_fingerprint
        except Exception as exc:
            self._block(stage, f"state reconstruction failed: {type(exc).__name__}")
        if observed_fingerprint != self._snapshot.execution_configuration_fingerprint:
            self._block(stage, "execution configuration fingerprint differs")
        self._checks.append(
            IntegrityCheckV3(
                stage=stage,
                status="verified_unchanged",
                execution_configuration_fingerprint=observed_fingerprint,
            )
        )
        return "verified_unchanged"

    def execute_provider_attempt(
        self, attempt: Callable[[], _ResultT]
    ) -> _ResultT:
        """Check immediately around one attempt; never retry or access secrets."""

        if not callable(attempt):
            raise TASK039E3RecoveryIntegrityV3Error(
                "provider attempt callable is required"
            )
        if self._attempt_in_progress:
            raise TASK039E3RecoveryIntegrityV3Error(
                "parallel provider attempts are prohibited"
            )
        self.assert_integrity("before_provider_attempt")
        self._attempt_in_progress = True
        self._provider_contact_started = True
        self._provider_attempts_started += 1
        try:
            result = attempt()
        except Exception as provider_error:
            self._attempt_in_progress = False
            try:
                self.assert_integrity("after_provider_attempt")
            except TASK039E3RecoveryIntegrityV3Error as integrity_error:
                raise integrity_error from provider_error
            raise
        self._attempt_in_progress = False
        self.assert_integrity("after_provider_attempt")
        return result

    def assert_before_e1_access(self) -> str:
        return self.assert_integrity("before_e1_access")

    def assert_before_scientific_phase(self) -> str:
        return self.assert_integrity("before_scientific_phase")

    def assert_at_relation_boundary(self) -> str:
        return self.assert_integrity("scientific_relation_boundary")

    def assert_before_metrics_finalization(self) -> str:
        return self.assert_integrity("before_metrics_finalization")

    def assert_before_public_finalization(self) -> str:
        return self.assert_integrity("before_public_finalization")

    def assert_before_terminal_pass(self) -> str:
        if not self._provider_contact_started:
            raise TASK039E3RecoveryIntegrityV3Error(
                "terminal PASS requires a provider-contact boundary"
            )
        return self.assert_integrity("before_terminal_pass")


__all__ = [
    "EXACT_MODEL",
    "EXECUTION_SCHEDULE_HASH",
    "ExecutionIntegritySnapshotV3",
    "FROZEN_RETRY_POLICY_HASH_V3",
    "FROZEN_RETRY_POLICY_V3",
    "FROZEN_SAMPLING_CONFIGURATION_HASH_V3",
    "FROZEN_SAMPLING_CONFIGURATION_V3",
    "FROZEN_SCIENTIFIC_CALL_BUDGET_HASH_V3",
    "FROZEN_SCIENTIFIC_CALL_BUDGET_V3",
    "FrozenSourceBlobV3",
    "IntegrityCheckV3",
    "MAXIMUM_SCIENTIFIC_LOGICAL_CALLS",
    "MINIMUM_SCIENTIFIC_LOGICAL_CALLS",
    "ObservedExecutionIntegrityStateV3",
    "PostContactIntegrityGuardV3",
    "RECOVERY_CAPABILITY_PROMPT_SHA256",
    "RECOVERY_CAPABILITY_SCHEMA_SHA256",
    "SCIENTIFIC_CONCURRENCY",
    "TASK039E3RecoveryIntegrityV3Error",
    "TRANSPORT_RETRY_DELAYS_SECONDS",
    "URLOPEN_TIMEOUT_SECONDS",
    "build_frozen_execution_integrity_state_v3",
    "capture_execution_integrity_snapshot_v3",
    "git_blob_sha1_v3",
    "validate_initial_integrity_state_v3",
]
