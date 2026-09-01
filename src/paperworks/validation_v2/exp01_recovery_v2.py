"""Fail-closed lineage for resuming interrupted Validation V2 EXP-01.

The original twelve training runs are immutable inputs.  This module records
their post-interruption recovery without pretending that the recovery receipt
was an external creation-time anchor, and keeps cumulative scientific access
accounting separate from the resumed process.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping, Sequence

from paperworks.validation_v2.exp01_checkpoint_v2 import Exp01CheckpointReceiptV2
from paperworks.validation_v2.exp01_scientific_v1 import EXPECTED_SCHEDULE
from paperworks.v6.common import require_sha256, stable_hash_v1


ORIGIN_TRAINING_SOURCE_COMMIT = "6e2360da4f8d0be87daf602023b82ab54f792a58"
ORIGIN_TRAINING_CODE_AUTHORITY_HASH = (
    "cf1ccb2720aa64e49c6798adc43cc2fd2d90dc16aa8d6af6287ecda27fc997d0"
)
ORIGIN_TRAINING_CONFIG_HASH = (
    "68fbd006af1bc71468c157ba90888f54b8c0cbeba1aa7aba1121701a5b87870e"
)
RECOVERY_SCHEMA = "paperworks.validation_v2.exp01_interrupted_checkpoint_recovery_receipt_v2"
RECOVERY_SCHEMA_VERSION = "2.0.0"

INTERRUPTED_ACCESS_COUNTERS: Mapping[str, int] = {
    "train1_opens": 1,
    "train2_opens": 1,
    "train3_opens": 1,
    "train4_opens": 0,
    "test1_accesses": 0,
    "test2_accesses": 0,
    "heldout_accesses": 0,
    "label_accesses": 0,
    "provider_calls": 0,
}


class Exp01RecoveryError(RuntimeError):
    """Raised when interrupted EXP-01 lineage cannot be recovered exactly."""


def expected_checkpoint_names_v2() -> tuple[str, ...]:
    return tuple(
        f"run_{order:02d}_{arm}_{view}_seed_{seed}.pt"
        for order, (arm, view, seed) in enumerate(EXPECTED_SCHEDULE, start=1)
    )


def build_interrupted_checkpoint_recovery_receipt_v2(
    *,
    checkpoint_receipts: Sequence[Exp01CheckpointReceiptV2],
    snapshot_source_commit: str,
    issued_at_utc: str | None = None,
) -> dict[str, object]:
    """Create a public-safe post-interruption snapshot of all twelve states."""

    if len(snapshot_source_commit) != 40 or any(ch not in "0123456789abcdef" for ch in snapshot_source_commit):
        raise Exp01RecoveryError("snapshot source commit must be a lowercase Git SHA")
    receipts = tuple(checkpoint_receipts)
    if len(receipts) != len(EXPECTED_SCHEDULE):
        raise Exp01RecoveryError("exact twelve-checkpoint recovery set is required")
    observed_schedule = tuple((item.arm_id, item.view_id, item.seed) for item in receipts)
    if observed_schedule != EXPECTED_SCHEDULE:
        raise Exp01RecoveryError("checkpoint recovery schedule differs from frozen schedule")
    expected_run_ids = tuple(
        f"run_{order:02d}_{arm}_{view}_seed_{seed}"
        for order, (arm, view, seed) in enumerate(EXPECTED_SCHEDULE, start=1)
    )
    if tuple(item.run_id for item in receipts) != expected_run_ids:
        raise Exp01RecoveryError("checkpoint recovery run identities differ")
    if any(item.code_authority_hash != ORIGIN_TRAINING_CODE_AUTHORITY_HASH for item in receipts):
        raise Exp01RecoveryError("checkpoint origin code authority differs")
    if any(item.training_config_hash != ORIGIN_TRAINING_CONFIG_HASH for item in receipts):
        raise Exp01RecoveryError("checkpoint training configuration differs")
    if any(not item.reopened for item in receipts):
        raise Exp01RecoveryError("every recovered checkpoint must pass reopen replay")
    for item in receipts:
        if item.receipt_hash != stable_hash_v1(item.to_dict(include_hash=False)):
            raise Exp01RecoveryError("checkpoint recovery receipt hash differs")
        for value in (item.state_hash, item.file_sha256, item.receipt_hash):
            require_sha256(value, "checkpoint recovery identity")
    timestamp = issued_at_utc or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    content: dict[str, object] = {
        "schema": RECOVERY_SCHEMA,
        "schema_version": RECOVERY_SCHEMA_VERSION,
        "status": "RECOVERED_FOR_POSTPROCESSING_ONLY_PENDING_RESUME",
        "training_source_commit": ORIGIN_TRAINING_SOURCE_COMMIT,
        "snapshot_source_commit": snapshot_source_commit,
        "checkpoint_origin_code_authority_hash": ORIGIN_TRAINING_CODE_AUTHORITY_HASH,
        "training_config_hash": ORIGIN_TRAINING_CONFIG_HASH,
        "issued_at_utc": timestamp,
        "checkpoint_count": len(receipts),
        "schedule": [list(row) for row in EXPECTED_SCHEDULE],
        "checkpoint_receipt_hashes": [item.receipt_hash for item in receipts],
        "checkpoint_file_hashes": [item.file_sha256 for item in receipts],
        "checkpoint_state_hashes": [item.state_hash for item in receipts],
        "checkpoint_recovery_set_hash": stable_hash_v1(
            {"receipts": [item.to_dict() for item in receipts]}
        ),
        "custody_timing": "POST_INTERRUPTION_RECOVERY_SNAPSHOT",
        "creation_time_external_anchor": False,
        "training_reexecuted": False,
        "interrupted_attempt_public_result_exists": False,
        "interrupted_attempt_access_counters": dict(INTERRUPTED_ACCESS_COUNTERS),
        "interrupted_attempt_counter_basis": "OBSERVED_PROCESS_STACK_AND_FROZEN_RUNNER_STAGE_ORDER",
        "claim_boundary": "CHECKPOINT_RECOVERY_IS_NOT_A_SCIENTIFIC_RESULT",
        "redaction": "NO_PRIVATE_PATHS_VALUES_SCORES_LOSSES_OR_CHECKPOINT_BYTES",
    }
    return {**content, "receipt_self_hash": stable_hash_v1(content)}


def verify_interrupted_checkpoint_recovery_receipt_v2(
    document: Mapping[str, object],
) -> str:
    """Replay a public recovery receipt before any scientific data access."""

    supplied = str(document.get("receipt_self_hash", ""))
    require_sha256(supplied, "receipt_self_hash")
    content = {key: value for key, value in document.items() if key != "receipt_self_hash"}
    if stable_hash_v1(content) != supplied:
        raise Exp01RecoveryError("checkpoint recovery receipt self-hash mismatch")
    required = {
        "schema",
        "schema_version",
        "status",
        "training_source_commit",
        "snapshot_source_commit",
        "checkpoint_origin_code_authority_hash",
        "training_config_hash",
        "issued_at_utc",
        "checkpoint_count",
        "schedule",
        "checkpoint_receipt_hashes",
        "checkpoint_file_hashes",
        "checkpoint_state_hashes",
        "checkpoint_recovery_set_hash",
        "custody_timing",
        "creation_time_external_anchor",
        "training_reexecuted",
        "interrupted_attempt_public_result_exists",
        "interrupted_attempt_access_counters",
        "interrupted_attempt_counter_basis",
        "claim_boundary",
        "redaction",
    }
    if set(content) != required:
        raise Exp01RecoveryError("checkpoint recovery receipt fields differ")
    expected_values = {
        "schema": RECOVERY_SCHEMA,
        "schema_version": RECOVERY_SCHEMA_VERSION,
        "status": "RECOVERED_FOR_POSTPROCESSING_ONLY_PENDING_RESUME",
        "training_source_commit": ORIGIN_TRAINING_SOURCE_COMMIT,
        "checkpoint_origin_code_authority_hash": ORIGIN_TRAINING_CODE_AUTHORITY_HASH,
        "training_config_hash": ORIGIN_TRAINING_CONFIG_HASH,
        "checkpoint_count": len(EXPECTED_SCHEDULE),
        "schedule": [list(row) for row in EXPECTED_SCHEDULE],
        "custody_timing": "POST_INTERRUPTION_RECOVERY_SNAPSHOT",
        "creation_time_external_anchor": False,
        "training_reexecuted": False,
        "interrupted_attempt_public_result_exists": False,
        "interrupted_attempt_access_counters": dict(INTERRUPTED_ACCESS_COUNTERS),
        "claim_boundary": "CHECKPOINT_RECOVERY_IS_NOT_A_SCIENTIFIC_RESULT",
        "redaction": "NO_PRIVATE_PATHS_VALUES_SCORES_LOSSES_OR_CHECKPOINT_BYTES",
    }
    if any(content.get(name) != value for name, value in expected_values.items()):
        raise Exp01RecoveryError("checkpoint recovery receipt authority differs")
    snapshot_source_commit = str(content.get("snapshot_source_commit", ""))
    if len(snapshot_source_commit) != 40 or any(
        ch not in "0123456789abcdef" for ch in snapshot_source_commit
    ):
        raise Exp01RecoveryError("checkpoint recovery snapshot commit differs")
    for field in (
        "checkpoint_receipt_hashes",
        "checkpoint_file_hashes",
        "checkpoint_state_hashes",
    ):
        values = content.get(field)
        if not isinstance(values, list) or len(values) != len(EXPECTED_SCHEDULE):
            raise Exp01RecoveryError(f"{field} cardinality differs")
        for value in values:
            require_sha256(str(value), field)
    require_sha256(str(content.get("checkpoint_recovery_set_hash", "")), "checkpoint_recovery_set_hash")
    return supplied


def cumulative_access_counters_v2(resume_counters: Mapping[str, int]) -> dict[str, int]:
    """Add known interrupted and resumed attempts without hiding either ledger."""

    expected = set(INTERRUPTED_ACCESS_COUNTERS)
    if set(resume_counters) != expected or any(
        not isinstance(value, int) or value < 0 for value in resume_counters.values()
    ):
        raise Exp01RecoveryError("resume access counters differ from the frozen counter schema")
    return {
        name: int(INTERRUPTED_ACCESS_COUNTERS[name]) + int(resume_counters[name])
        for name in sorted(expected)
    }


__all__ = [
    "Exp01RecoveryError",
    "INTERRUPTED_ACCESS_COUNTERS",
    "ORIGIN_TRAINING_CODE_AUTHORITY_HASH",
    "ORIGIN_TRAINING_CONFIG_HASH",
    "ORIGIN_TRAINING_SOURCE_COMMIT",
    "build_interrupted_checkpoint_recovery_receipt_v2",
    "cumulative_access_counters_v2",
    "expected_checkpoint_names_v2",
    "verify_interrupted_checkpoint_recovery_receipt_v2",
]
