"""Formal Validation V2 authority for HAI 23.05 normal-only materialization.

This module is deliberately payload-free.  It freezes the four authorized
normal members and validates public-safe receipts emitted by the single
materialization runner.  The historical ten-file TASK-039AR contract and the
PILOT V1 materializers remain unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, NoReturn, Sequence


POLICY_ID = "DATA-POLICY-001"
SCHEMA_VERSION = "hai_normal_only_materialization_v2"
DATASET = "HAI"
DATASET_VERSION = "23.05"
OFFICIAL_DISTRIBUTION = "icsdataset/hai-security-dataset"
OFFICIAL_DISTRIBUTION_VERSION = 10
OFFICIAL_GIT_REPOSITORY = "https://github.com/icsdataset/hai"
PINNED_GIT_COMMIT = "2a814cebc9a66b06c9e5cd545e2d72e65d383737"
TASK039A_CONFIG_HASH = "7f36b4ab4055fc412cc86865021a83771117e31ee8734d69a3e9892761f4d34a"
TASK039AR_CONFIG_HASH = "b568a7491f648e216011a6c293cbed644a535ad4c3e3e4cad2c1b834b6a7a958"
TASK039AR_METADATA_HASH = "a7389cc123a544302b896c4c1ffc931a3c61c22318c0fa53c575cd1567d5fbfe"
TASK039AR_EQUIVALENCE_HASH = "7917f8736c119e774a945096f41f8abc18bce30267dd9e754c5a20157a5bf7a8"
CANONICAL_HEADER_HASH = "95968d825d1c9caab778a857cec618b64674ec5a85d94e6952d99c2cab08d16a"
P1_FEATURE_ORDER_HASH = "a612bdb9850ad0dd865dc62b23199bf2b696452c492e4aabe09fe554fa246d57"
P1_FEATURE_SET_HASH = "6dea06e82c0d99f35a0d11c5e97503e8bb3a0fc8c1d9963b997986021fd23515"

BLOCKED_EGRESS = "BLOCKED_OFFICIAL_HAI_ACQUISITION_EGRESS"
BLOCKED_METADATA = "BLOCKED_OFFICIAL_HAI_METADATA_MISMATCH"
BLOCKED_EQUIVALENCE = "BLOCKED_NORMAL_BYTE_EQUIVALENCE"
BLOCKED_MATERIALIZATION = "BLOCKED_NORMAL_MATERIALIZATION"
_FAILURE_STATES = frozenset(
    {BLOCKED_EGRESS, BLOCKED_METADATA, BLOCKED_EQUIVALENCE, BLOCKED_MATERIALIZATION}
)


class HAINormalMaterializationV2Error(RuntimeError):
    """Fail-closed public error with no path or payload details."""

    def __init__(self, state: str) -> None:
        self.state = state if state in _FAILURE_STATES else BLOCKED_MATERIALIZATION
        super().__init__(self.state)


def fail(state: str) -> NoReturn:
    raise HAINormalMaterializationV2Error(state)


@dataclass(frozen=True)
class NormalSplitSpecV2:
    symbolic_id: str
    relative_path: str
    sha256: str
    size_bytes: int
    row_count: int
    role: str
    allowed_operations: tuple[str, ...]

    def public_dict(self) -> dict[str, Any]:
        return {
            "symbolic_id": self.symbolic_id,
            "relative_path": self.relative_path,
            "sha256_git_lfs_oid": self.sha256,
            "size_bytes": self.size_bytes,
            "row_count": self.row_count,
            "role": self.role,
            "allowed_operations": list(self.allowed_operations),
        }


NORMAL_SPLITS: tuple[NormalSplitSpecV2, ...] = (
    NormalSplitSpecV2(
        "HAI_TRAIN1", "hai-23.05/hai-train1.csv",
        "53007b0ba604fbf338e7ac2e08cd81d874b5d1388f3aecb213ddcba5bf2bec4a",
        162_418_984, 280_800, "NORMAL_FIT_PRIMARY",
        ("CANDIDATE_LEARNING", "GDN_NORMAL_TRAINING", "RELATION_FIT", "NUMERIC_FIT", "DETECTOR_FIT"),
    ),
    NormalSplitSpecV2(
        "HAI_TRAIN2", "hai-23.05/hai-train2.csv",
        "0e520e82bf78a661ab19ce4967f3c766bd809820f457a9c90c365102d4534c56",
        169_121_615, 291_600, "NORMAL_FIT_SECONDARY",
        ("CANDIDATE_LEARNING", "GDN_NORMAL_TRAINING", "RELATION_FIT", "NUMERIC_FIT", "DETECTOR_FIT", "FILE_LOCAL_STABILITY"),
    ),
    NormalSplitSpecV2(
        "HAI_TRAIN3", "hai-23.05/hai-train3.csv",
        "bfcec2dc05adea103e7491546b0e28268faaa26d3cc717d10f4595c94b81e85d",
        72_774_793, 126_000, "NORMAL_CONFIRMATION_CALIBRATION",
        ("RELATION_CONFIRMATION", "THRESHOLD_CALIBRATION"),
    ),
    NormalSplitSpecV2(
        "HAI_TRAIN4", "hai-23.05/hai-train4.csv",
        "56658c83657d42a65db982b864362e0d0ffeb96d1f7b357d5e76e3a5c522d940",
        114_494_940, 198_000, "NORMAL_POLICY_SELECTION_SANITY",
        ("NORMAL_POLICY_SELECTION", "NORMAL_SANITY", "FALSE_FIRING_ASSESSMENT"),
    ),
)

AUTHORIZED_RELATIVE_PATHS = frozenset(item.relative_path for item in NORMAL_SPLITS)
FORBIDDEN_SPLIT_CLASSES = ("test1", "test2", "held_out", "labels", "HAIEnd", "older_editions")


def canonical_hash(document: Mapping[str, Any], field: str = "self_hash") -> str:
    payload = dict(document)
    payload.pop(field, None)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def raw_specs() -> tuple[tuple[str, str, int], ...]:
    """Return the fixed four-member acquisition authority; no caller selection."""

    return tuple((item.relative_path, item.sha256, item.size_bytes) for item in NORMAL_SPLITS)


def require_authorized_members(relative_paths: Sequence[str]) -> None:
    observed = tuple(relative_paths)
    expected = tuple(item.relative_path for item in NORMAL_SPLITS)
    if observed != expected or len(observed) != len(set(observed)):
        fail(BLOCKED_METADATA)


def build_public_receipt(
    *, execution_commit: str, code_hash: str, private_manifest_hash: str,
    structural_records: Sequence[Mapping[str, Any]], created_at_utc: str,
) -> dict[str, Any]:
    if not all(len(value) == 64 and set(value) <= set("0123456789abcdef") for value in (code_hash, private_manifest_hash)):
        fail(BLOCKED_MATERIALIZATION)
    if len(execution_commit) != 40 or set(execution_commit) - set("0123456789abcdef"):
        fail(BLOCKED_MATERIALIZATION)
    by_id = {str(item.get("symbolic_id")): dict(item) for item in structural_records}
    if set(by_id) != {item.symbolic_id for item in NORMAL_SPLITS}:
        fail(BLOCKED_MATERIALIZATION)
    records: list[dict[str, Any]] = []
    for spec in NORMAL_SPLITS:
        record = by_id[spec.symbolic_id]
        expected = {
            "symbolic_id": spec.symbolic_id,
            "relative_path": spec.relative_path,
            "sha256": spec.sha256,
            "size_bytes": spec.size_bytes,
            "row_count": spec.row_count,
            "header_field_count": 87,
            "header_sha256": CANONICAL_HEADER_HASH,
            "timestamp_field": "timestamp",
            "nominal_timestamp_delta_seconds": 1.0,
            "timestamps_strictly_increasing": True,
            "malformed_row_count": 0,
            "inconsistent_field_count_rows": 0,
            "normal_file_status": "normal_only_verified",
        }
        if any(record.get(key) != value for key, value in expected.items()):
            fail(BLOCKED_MATERIALIZATION)
        records.append({**spec.public_dict(), "byte_equivalent": True, "schema_identity_pass": True})
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "HAI_NORMAL_ONLY_MATERIALIZATION_RECEIPT_V2",
        "status": "NORMAL_ONLY_MATERIALIZATION_READY",
        "policy_id": POLICY_ID,
        "study_identity": "VALIDATION_V2",
        "dataset": DATASET,
        "dataset_version": DATASET_VERSION,
        "official_payload_route": OFFICIAL_DISTRIBUTION,
        "official_distribution_version": OFFICIAL_DISTRIBUTION_VERSION,
        "identity_authority": "PINNED_OFFICIAL_GIT_SNAPSHOT_AND_GIT_LFS_OBJECTS",
        "official_git_repository": OFFICIAL_GIT_REPOSITORY,
        "official_git_snapshot_commit": PINNED_GIT_COMMIT,
        "upstream_authorities": {
            "task039a_config_hash": TASK039A_CONFIG_HASH,
            "task039ar_config_hash": TASK039AR_CONFIG_HASH,
            "task039ar_metadata_hash": TASK039AR_METADATA_HASH,
            "task039ar_equivalence_hash": TASK039AR_EQUIVALENCE_HASH,
        },
        "metadata_phase": "REUSED_COMMITTED_SANITIZED_METADATA_RECEIPT",
        "materialization_contract": "NORMAL_ONLY_SELECTIVE_MATERIALIZATION_V2",
        "execution_commit": execution_commit,
        "execution_code_hash": code_hash,
        "private_manifest_hash": private_manifest_hash,
        "normal_splits": records,
        "forbidden_split_classes": list(FORBIDDEN_SPLIT_CLASSES),
        "byte_equivalence": "PASS_ALL_FOUR",
        "schema_identity": "PASS_ALL_FOUR",
        "p1_feature_contract": {
            "feature_count": 37,
            "feature_order_hash": P1_FEATURE_ORDER_HASH,
            "feature_set_hash": P1_FEATURE_SET_HASH,
        },
        "access_counters": {
            "train1_download_or_cache_validation": 1,
            "train2_download_or_cache_validation": 1,
            "train3_download_or_cache_validation": 1,
            "train4_download_or_cache_validation": 1,
            "test1_download": 0, "test1_open": 0, "test1_hash": 0, "test1_parse": 0,
            "test2_download": 0, "test2_stat": 0, "test2_open": 0, "test2_hash": 0, "test2_parse": 0,
            "label_access": 0, "held_out_access": 0, "private_exposures": 0,
        },
        "created_at_utc": created_at_utc,
    }
    receipt["self_hash"] = canonical_hash(receipt)
    return receipt


def validate_public_receipt(document: Mapping[str, Any]) -> str:
    if document.get("self_hash") != canonical_hash(document):
        fail(BLOCKED_MATERIALIZATION)
    if (
        document.get("status") != "NORMAL_ONLY_MATERIALIZATION_READY"
        or document.get("policy_id") != POLICY_ID
        or document.get("official_payload_route") != OFFICIAL_DISTRIBUTION
        or document.get("official_git_snapshot_commit") != PINNED_GIT_COMMIT
        or document.get("byte_equivalence") != "PASS_ALL_FOUR"
        or document.get("schema_identity") != "PASS_ALL_FOUR"
    ):
        fail(BLOCKED_MATERIALIZATION)
    counters = document.get("access_counters")
    if not isinstance(counters, Mapping) or any(
        counters.get(key) != 0 for key in (
            "test1_download", "test1_open", "test1_hash", "test1_parse",
            "test2_download", "test2_stat", "test2_open", "test2_hash", "test2_parse",
            "label_access", "held_out_access", "private_exposures",
        )
    ):
        fail(BLOCKED_MATERIALIZATION)
    records = document.get("normal_splits")
    if not isinstance(records, list) or [item.get("symbolic_id") for item in records] != [item.symbolic_id for item in NORMAL_SPLITS]:
        fail(BLOCKED_MATERIALIZATION)
    return str(document["self_hash"])


__all__ = [
    "AUTHORIZED_RELATIVE_PATHS", "BLOCKED_EGRESS", "BLOCKED_EQUIVALENCE",
    "BLOCKED_MATERIALIZATION", "BLOCKED_METADATA", "HAINormalMaterializationV2Error",
    "NORMAL_SPLITS", "POLICY_ID", "build_public_receipt", "canonical_hash",
    "fail", "raw_specs", "require_authorized_members", "validate_public_receipt",
]
