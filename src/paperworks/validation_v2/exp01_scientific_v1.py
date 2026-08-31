"""Fail-closed scientific handoff contracts for Validation V2 EXP-01.

The module is computation-free.  It binds the exact normal-only authority,
the preregistered GDN backend/configuration, typed predecessor receipts, and
the stage order needed before an EXP-01 scientific runner may claim custody.
It never reads HAI, trains GDN, profiles relations, or creates a result.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Sequence

from paperworks.v6.common import require_sha256, stable_hash_v1
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER


SCHEMA_VERSION = "2.0.0"
DATASET_MANIFEST_ID = "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2"
OFFICIAL_SNAPSHOT_COMMIT = "2a814cebc9a66b06c9e5cd545e2d72e65d383737"
UPSTREAM_GDN_COMMIT = "9853899da860682669a134e4af315d036aab4eca"
BACKEND_CLASSIFICATION = "upstream_aligned_validated"
INTERNAL_NEIGHBOR_K = 5
TRAINING_CONFIG_HASH = "68fbd006af1bc71468c157ba90888f54b8c0cbeba1aa7aba1121701a5b87870e"
CORRECTED_NEIGHBOR_POLICY_HASH = "6ff16747c7ede1ced361a93ca644b3c0febd9dddf52e32ffbf9f117341f52626"
FROZEN_NEIGHBOR_POLICY_HASH = stable_hash_v1(
    {
        "upstream_commit": UPSTREAM_GDN_COMMIT,
        "topk": INTERNAL_NEIGHBOR_K,
        "diagonal_policy": "SELF_ELIGIBLE_UNMASKED_COSINE_DIAGONAL",
        "projection": "PROJECT_TO_FROZEN_144_PAIR_UNIVERSE_AFTER_TOPK",
    }
)
FEATURE_ORDER_HASH = "a612bdb9850ad0dd865dc62b23199bf2b696452c492e4aabe09fe554fa246d57"
PAIR_UNIVERSE_HASH = "fc072d3e18ce4623972c2cb64f6266727092ecae03fdb0f0dd929d705e1d8557"
SOURCE_IDENTITY_HASH = "0af3f80f18a3eab59b9783af64d306c8d774eeb69b3a72c24c10048abd4ed234"
TARGET_IDENTITY_HASH = "063037980aae4f0eaf45fbebb59f2aa0a924fbad583f3818107a793dfe7248e7"
META_RESULT_HASH = "0e3b055df911c74bd0e0993b7b3bb122860b265192ad0cf91d54edc1e74635bf"
STAT_RESULT_HASH = "7351e295be7e5bdd2b1cb9677091426899e5a2616c60245f953ff6602d106950"
NORMAL_FILE_HASHES = (
    ("train1", "hai-23.05/hai-train1.csv", "53007b0ba604fbf338e7ac2e08cd81d874b5d1388f3aecb213ddcba5bf2bec4a"),
    ("train2", "hai-23.05/hai-train2.csv", "0e520e82bf78a661ab19ce497f3c766bd809820f457a9c90c365102d4534c56"),
    ("train3", "hai-23.05/hai-train3.csv", "bfcec2dc05adea103e7491546b0e28268faaa26d3cc717d10f4595c94b81e85d"),
    ("train4", "hai-23.05/hai-train4.csv", "56658c83657d42a65db982b864362e0d0ffeb96d1f7b357d5e76e3a5c522d940"),
)
SOURCE_VARIABLES = (
    "P1_FCV01D", "P1_FCV01Z", "P1_FCV02D", "P1_FCV02Z",
    "P1_FCV03D", "P1_FCV03Z", "P1_LCV01D", "P1_LCV01Z",
    "P1_PCV01D", "P1_PCV01Z", "P1_PCV02Z", "P1_PP04",
)
TARGET_VARIABLES = (
    "P1_FT01", "P1_FT01Z", "P1_FT02", "P1_FT02Z", "P1_FT03",
    "P1_FT03Z", "P1_LIT01", "P1_PIT01", "P1_PIT02", "P1_TIT01",
    "P1_TIT02", "P1_TIT03",
)
PAIR_UNIVERSE = tuple((source, target) for source in SOURCE_VARIABLES for target in TARGET_VARIABLES)
SEEDS = (11, 23, 37)
TOP_K = (10, 20, 40)
REMOVE_WITHOUT_REFILL = "REMOVE_PRIMARY_MASK_EDGES_FROM_CHECKPOINT_GRAPH_WITHOUT_REFILL"


class Exp01ScientificContractError(ValueError):
    """Raised when a scientific handoff is stale, incomplete, or foreign."""


class ViewId(str, Enum):
    COMBINED = "TRAIN1_TRAIN2_COMBINED"
    TRAIN1_ONLY = "TRAIN1_ONLY"
    TRAIN2_ONLY = "TRAIN2_ONLY"


class ArmId(str, Enum):
    FROZEN_SELF_ELIGIBLE = "GDN_FROZEN_SELF_ELIGIBLE"
    CORRECTED_SELF_EXCLUDED = "GDN_CORRECTED_SELF_EXCLUDED"


class Stage(str, Enum):
    CREATED = "CREATED"
    AUTHORITY_BOUND = "AUTHORITY_BOUND"
    VIEWS_MATERIALIZED = "VIEWS_MATERIALIZED"
    SEEDS_COMPLETED = "SEEDS_COMPLETED"
    CANDIDATES_AGGREGATED = "CANDIDATES_AGGREGATED"
    PROFILING_CONFIRMED = "PROFILING_CONFIRMED"
    MASK_INTERVENTION_COMPLETED = "MASK_INTERVENTION_COMPLETED"
    INCLUSION_HANDOFF_READY = "INCLUSION_HANDOFF_READY"


EXPECTED_SCHEDULE = tuple(
    (arm.value, view.value, seed)
    for arm, view in (
        (ArmId.FROZEN_SELF_ELIGIBLE, ViewId.COMBINED),
        (ArmId.CORRECTED_SELF_EXCLUDED, ViewId.COMBINED),
        (ArmId.CORRECTED_SELF_EXCLUDED, ViewId.TRAIN1_ONLY),
        (ArmId.CORRECTED_SELF_EXCLUDED, ViewId.TRAIN2_ONLY),
    )
    for seed in SEEDS
)
EXPECTED_AGGREGATES = (
    (ArmId.FROZEN_SELF_ELIGIBLE.value, ViewId.COMBINED.value),
    (ArmId.CORRECTED_SELF_EXCLUDED.value, ViewId.COMBINED.value),
    (ArmId.CORRECTED_SELF_EXCLUDED.value, ViewId.TRAIN1_ONLY.value),
    (ArmId.CORRECTED_SELF_EXCLUDED.value, ViewId.TRAIN2_ONLY.value),
)
STAGE_ORDER = tuple(Stage)

PREREGISTRATION_HASH = stable_hash_v1(
    {
        "program": "VALIDATION-V2-AUTONOMOUS-PROGRAM-V1",
        "experiment": "EXP-01",
        "upstream_commit": UPSTREAM_GDN_COMMIT,
        "backend_classification": BACKEND_CLASSIFICATION,
        "training_config_hash": TRAINING_CONFIG_HASH,
        "frozen_neighbor_policy_hash": FROZEN_NEIGHBOR_POLICY_HASH,
        "corrected_neighbor_policy_hash": CORRECTED_NEIGHBOR_POLICY_HASH,
        "schedule": EXPECTED_SCHEDULE,
        "top_k": TOP_K,
        "split_roles": ("train1", "train2", "train3", "train4"),
        "labels_and_test_authorized": False,
    }
)

EXP01_SCIENTIFIC_CONTRACT_HASH = stable_hash_v1(
    {
        "schema_version": SCHEMA_VERSION,
        "dataset_manifest_id": DATASET_MANIFEST_ID,
        "official_snapshot_commit": OFFICIAL_SNAPSHOT_COMMIT,
        "normal_file_hashes": NORMAL_FILE_HASHES,
        "feature_order": P1_FEATURE_ORDER,
        "feature_order_hash": FEATURE_ORDER_HASH,
        "pair_universe_hash": PAIR_UNIVERSE_HASH,
        "source_identity_hash": SOURCE_IDENTITY_HASH,
        "target_identity_hash": TARGET_IDENTITY_HASH,
        "meta_result_hash": META_RESULT_HASH,
        "stat_result_hash": STAT_RESULT_HASH,
        "upstream_commit": UPSTREAM_GDN_COMMIT,
        "backend_classification": BACKEND_CLASSIFICATION,
        "training_config_hash": TRAINING_CONFIG_HASH,
        "preregistration_hash": PREREGISTRATION_HASH,
        "neighbor_policy_hashes": (FROZEN_NEIGHBOR_POLICY_HASH, CORRECTED_NEIGHBOR_POLICY_HASH),
        "schedule": EXPECTED_SCHEDULE,
        "top_k": TOP_K,
        "intervention": REMOVE_WITHOUT_REFILL,
    }
)


def _strict_bool(value: object, name: str) -> None:
    if type(value) is not bool:
        raise Exp01ScientificContractError(f"{name} must be a strict Boolean")


def _sha(value: str, name: str) -> None:
    try:
        require_sha256(value, name)
    except ValueError as exc:
        raise Exp01ScientificContractError(str(exc)) from exc


def _pairs(
    values: Iterable[Sequence[str]], *, allow_empty: bool = False,
) -> tuple[tuple[str, str], ...]:
    rows = tuple((str(value[0]), str(value[1])) for value in values)
    if not allow_empty and not rows:
        raise Exp01ScientificContractError("candidate pair set must not be empty")
    if len(rows) != len(set(rows)):
        raise Exp01ScientificContractError("candidate pair identities must be unique")
    if any(row not in PAIR_UNIVERSE for row in rows):
        raise Exp01ScientificContractError("candidate pair lies outside the frozen 144-pair universe")
    return rows


def _graph_pairs(values: Iterable[Sequence[str]]) -> tuple[tuple[str, str], ...]:
    rows = tuple((str(value[0]), str(value[1])) for value in values)
    if len(rows) != len(set(rows)):
        raise Exp01ScientificContractError("internal graph edges must be unique")
    features = frozenset(P1_FEATURE_ORDER)
    if any(source not in features or target not in features for source, target in rows):
        raise Exp01ScientificContractError("internal graph edge lies outside the 37-feature authority")
    return rows


def _with_hash(cls: type, values: dict[str, object], hash_field: str):
    provisional = cls(**values)
    return cls(**{**provisional.__dict__, hash_field: stable_hash_v1(provisional.to_dict(include_hash=False))})


def _require_self_hash(value: object, *, expected_type: type, hash_field: str, name: str) -> None:
    if type(value) is not expected_type:
        raise Exp01ScientificContractError(f"{name} must use the exact typed receipt")
    receipt_hash = getattr(value, hash_field, "")
    if not receipt_hash or receipt_hash != stable_hash_v1(value.to_dict(include_hash=False)):
        raise Exp01ScientificContractError(f"{name} self-hash replay failed")


@dataclass(frozen=True)
class PublicDataAuthorityV1:
    dataset_manifest_id: str = DATASET_MANIFEST_ID
    official_snapshot_commit: str = OFFICIAL_SNAPSHOT_COMMIT
    normal_files: tuple[tuple[str, str, str], ...] = NORMAL_FILE_HASHES
    feature_order: tuple[str, ...] = P1_FEATURE_ORDER
    feature_order_hash: str = FEATURE_ORDER_HASH
    pair_universe_hash: str = PAIR_UNIVERSE_HASH
    labels_authorized: bool = False
    test1_authorized: bool = False
    test2_authorized: bool = False
    heldout_authorized: bool = False
    contract_hash: str = EXP01_SCIENTIFIC_CONTRACT_HASH
    authority_hash: str = ""

    def __post_init__(self) -> None:
        if (
            self.dataset_manifest_id != DATASET_MANIFEST_ID
            or self.official_snapshot_commit != OFFICIAL_SNAPSHOT_COMMIT
            or self.normal_files != NORMAL_FILE_HASHES
            or self.feature_order != P1_FEATURE_ORDER
            or len(self.feature_order) != 37
            or self.feature_order_hash != FEATURE_ORDER_HASH
            or self.pair_universe_hash != PAIR_UNIVERSE_HASH
            or len(PAIR_UNIVERSE) != 144
            or self.contract_hash != EXP01_SCIENTIFIC_CONTRACT_HASH
        ):
            raise Exp01ScientificContractError("public EXP-01 data authority is not exact")
        for name in ("labels_authorized", "test1_authorized", "test2_authorized", "heldout_authorized"):
            _strict_bool(getattr(self, name), name)
            if getattr(self, name):
                raise Exp01ScientificContractError("EXP-01 permits only normal train1 through train4")
        if self.authority_hash and self.authority_hash != stable_hash_v1(self.to_dict(include_hash=False)):
            raise Exp01ScientificContractError("public data authority replay mismatch")

    def to_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        value = {
            "schema": "paperworks.validation_v2.exp01_public_data_authority_v2",
            "schema_version": SCHEMA_VERSION,
            "dataset_manifest_id": self.dataset_manifest_id,
            "official_snapshot_commit": self.official_snapshot_commit,
            "normal_files": [list(item) for item in self.normal_files],
            "feature_order": list(self.feature_order),
            "feature_order_hash": self.feature_order_hash,
            "pair_count": 144,
            "pair_universe_hash": self.pair_universe_hash,
            "labels_authorized": self.labels_authorized,
            "test1_authorized": self.test1_authorized,
            "test2_authorized": self.test2_authorized,
            "heldout_authorized": self.heldout_authorized,
            "contract_hash": self.contract_hash,
        }
        if include_hash:
            value["authority_hash"] = self.authority_hash
        return value


def build_public_data_authority_v1() -> PublicDataAuthorityV1:
    return _with_hash(PublicDataAuthorityV1, {}, "authority_hash")


PUBLIC_DATA_AUTHORITY_HASH = build_public_data_authority_v1().authority_hash


@dataclass(frozen=True)
class ViewReceiptV1:
    view_id: str
    authority_hash: str
    input_roles: tuple[str, ...]
    input_file_hashes: tuple[str, ...]
    feature_order_hash: str
    segment_count: int
    materialized_input_hash: str
    contract_hash: str = EXP01_SCIENTIFIC_CONTRACT_HASH
    receipt_hash: str = ""

    def __post_init__(self) -> None:
        expected = {
            ViewId.COMBINED.value: (("train1", "train2"), (NORMAL_FILE_HASHES[0][2], NORMAL_FILE_HASHES[1][2]), 2),
            ViewId.TRAIN1_ONLY.value: (("train1",), (NORMAL_FILE_HASHES[0][2],), 1),
            ViewId.TRAIN2_ONLY.value: (("train2",), (NORMAL_FILE_HASHES[1][2],), 1),
        }
        if self.view_id not in expected or (self.input_roles, self.input_file_hashes, self.segment_count) != expected[self.view_id]:
            raise Exp01ScientificContractError("view receipt does not preserve file-local semantics")
        if (
            self.authority_hash != PUBLIC_DATA_AUTHORITY_HASH
            or self.feature_order_hash != FEATURE_ORDER_HASH
            or self.contract_hash != EXP01_SCIENTIFIC_CONTRACT_HASH
        ):
            raise Exp01ScientificContractError("view receipt authority is stale or foreign")
        _sha(self.materialized_input_hash, "materialized_input_hash")
        if self.receipt_hash and self.receipt_hash != stable_hash_v1(self.to_dict(include_hash=False)):
            raise Exp01ScientificContractError("view receipt replay mismatch")

    def to_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        value = {
            "schema": "paperworks.validation_v2.exp01_view_receipt_v2", "schema_version": SCHEMA_VERSION,
            "view_id": self.view_id, "authority_hash": self.authority_hash,
            "input_roles": list(self.input_roles), "input_file_hashes": list(self.input_file_hashes),
            "feature_order_hash": self.feature_order_hash, "segment_count": self.segment_count,
            "materialized_input_hash": self.materialized_input_hash, "contract_hash": self.contract_hash,
        }
        if include_hash:
            value["receipt_hash"] = self.receipt_hash
        return value


def build_view_receipt_v1(*, view_id: ViewId, authority_hash: str, materialized_input_hash: str) -> ViewReceiptV1:
    roles = {ViewId.COMBINED: ("train1", "train2"), ViewId.TRAIN1_ONLY: ("train1",), ViewId.TRAIN2_ONLY: ("train2",)}[view_id]
    hashes = tuple(dict((role, digest) for role, _, digest in NORMAL_FILE_HASHES)[role] for role in roles)
    return _with_hash(ViewReceiptV1, {
        "view_id": view_id.value, "authority_hash": authority_hash, "input_roles": roles,
        "input_file_hashes": hashes, "feature_order_hash": FEATURE_ORDER_HASH,
        "segment_count": len(roles), "materialized_input_hash": materialized_input_hash,
    }, "receipt_hash")


def _neighbor_policy_for_arm(arm_id: str) -> str:
    return FROZEN_NEIGHBOR_POLICY_HASH if arm_id == ArmId.FROZEN_SELF_ELIGIBLE.value else CORRECTED_NEIGHBOR_POLICY_HASH


@dataclass(frozen=True)
class BackendExecutionReceiptV1:
    arm_id: str
    view_receipt: ViewReceiptV1
    seed: int
    checkpoint_hash: str
    graph_edges: tuple[tuple[str, str], ...]
    forward_graph_hash: str
    extraction_graph_hash: str
    authority_hash: str = PUBLIC_DATA_AUTHORITY_HASH
    preregistration_hash: str = PREREGISTRATION_HASH
    training_config_hash: str = TRAINING_CONFIG_HASH
    neighbor_policy_hash: str = ""
    upstream_commit: str = UPSTREAM_GDN_COMMIT
    backend_classification: str = BACKEND_CLASSIFICATION
    internal_neighbor_k: int = INTERNAL_NEIGHBOR_K
    completed: bool = True
    labels_accessed: bool = False
    test_accessed: bool = False
    contract_hash: str = EXP01_SCIENTIFIC_CONTRACT_HASH
    receipt_hash: str = ""

    def __post_init__(self) -> None:
        _require_self_hash(self.view_receipt, expected_type=ViewReceiptV1, hash_field="receipt_hash", name="backend view receipt")
        if (self.arm_id, self.view_receipt.view_id, self.seed) not in EXPECTED_SCHEDULE:
            raise Exp01ScientificContractError("backend receipt is outside the exact schedule")
        if (
            self.authority_hash != PUBLIC_DATA_AUTHORITY_HASH
            or self.view_receipt.authority_hash != self.authority_hash
            or self.preregistration_hash != PREREGISTRATION_HASH
            or self.training_config_hash != TRAINING_CONFIG_HASH
            or self.neighbor_policy_hash != _neighbor_policy_for_arm(self.arm_id)
            or self.upstream_commit != UPSTREAM_GDN_COMMIT
            or self.backend_classification != BACKEND_CLASSIFICATION
            or self.internal_neighbor_k != INTERNAL_NEIGHBOR_K
            or self.contract_hash != EXP01_SCIENTIFIC_CONTRACT_HASH
        ):
            raise Exp01ScientificContractError("backend receipt scientific authority changed")
        _sha(self.checkpoint_hash, "checkpoint_hash")
        edges = _graph_pairs(self.graph_edges)
        if len(edges) != len(P1_FEATURE_ORDER) * INTERNAL_NEIGHBOR_K:
            raise Exp01ScientificContractError("backend graph must contain exact 37 by Top-5 edges")
        per_target = {target: [] for target in P1_FEATURE_ORDER}
        for source, target in edges:
            per_target[target].append(source)
        if any(len(values) != INTERNAL_NEIGHBOR_K for values in per_target.values()):
            raise Exp01ScientificContractError("each target must have exactly five distinct neighbors")
        if self.arm_id == ArmId.CORRECTED_SELF_EXCLUDED.value and any(source == target for source, target in edges):
            raise Exp01ScientificContractError("corrected backend graph contains a self neighbor")
        graph_hash = stable_hash_v1({"graph_edges": edges})
        if self.forward_graph_hash != graph_hash or self.extraction_graph_hash != graph_hash:
            raise Exp01ScientificContractError("forward and extraction graph identities must replay exactly")
        for name in ("completed", "labels_accessed", "test_accessed"):
            _strict_bool(getattr(self, name), name)
        if not self.completed or self.labels_accessed or self.test_accessed:
            raise Exp01ScientificContractError("backend receipt must be complete and normal-only")
        if self.receipt_hash and self.receipt_hash != stable_hash_v1(self.to_dict(include_hash=False)):
            raise Exp01ScientificContractError("backend receipt replay mismatch")

    @property
    def view_id(self) -> str:
        return self.view_receipt.view_id

    @property
    def view_receipt_hash(self) -> str:
        return self.view_receipt.receipt_hash

    def to_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        value = {
            "schema": "paperworks.validation_v2.exp01_backend_execution_receipt_v2", "schema_version": SCHEMA_VERSION,
            "arm_id": self.arm_id, "view_id": self.view_id, "seed": self.seed,
            "authority_hash": self.authority_hash, "view_receipt_hash": self.view_receipt_hash,
            "preregistration_hash": self.preregistration_hash, "training_config_hash": self.training_config_hash,
            "neighbor_policy_hash": self.neighbor_policy_hash, "upstream_commit": self.upstream_commit,
            "backend_classification": self.backend_classification, "internal_neighbor_k": self.internal_neighbor_k,
            "checkpoint_hash": self.checkpoint_hash, "graph_edge_count": len(self.graph_edges),
            "forward_graph_hash": self.forward_graph_hash, "extraction_graph_hash": self.extraction_graph_hash,
            "completed": self.completed, "labels_accessed": self.labels_accessed,
            "test_accessed": self.test_accessed, "contract_hash": self.contract_hash,
            "redaction": "HASH_ONLY_NO_GRAPH_EDGES_SCORES_LOSSES_MATRICES_OR_PRIVATE_PATHS",
        }
        if include_hash:
            value["receipt_hash"] = self.receipt_hash
        return value


def build_backend_execution_receipt_v1(**values: object) -> BackendExecutionReceiptV1:
    supplied = dict(values)
    arm_id = str(supplied["arm_id"])
    supplied.setdefault("neighbor_policy_hash", _neighbor_policy_for_arm(arm_id))
    supplied["graph_edges"] = _graph_pairs(supplied["graph_edges"])  # type: ignore[arg-type]
    graph_hash = stable_hash_v1({"graph_edges": supplied["graph_edges"]})
    supplied.setdefault("forward_graph_hash", graph_hash)
    supplied.setdefault("extraction_graph_hash", graph_hash)
    return _with_hash(BackendExecutionReceiptV1, supplied, "receipt_hash")


@dataclass(frozen=True)
class SeedReceiptProjectionV1:
    backend_receipt: BackendExecutionReceiptV1
    authority_hash: str = PUBLIC_DATA_AUTHORITY_HASH
    contract_hash: str = EXP01_SCIENTIFIC_CONTRACT_HASH
    receipt_hash: str = ""

    def __post_init__(self) -> None:
        _require_self_hash(
            self.backend_receipt, expected_type=BackendExecutionReceiptV1,
            hash_field="receipt_hash", name="seed backend receipt",
        )
        if self.authority_hash != PUBLIC_DATA_AUTHORITY_HASH or self.backend_receipt.authority_hash != self.authority_hash:
            raise Exp01ScientificContractError("seed projection authority changed")
        if self.contract_hash != EXP01_SCIENTIFIC_CONTRACT_HASH:
            raise Exp01ScientificContractError("seed projection contract changed")
        if self.receipt_hash and self.receipt_hash != stable_hash_v1(self.to_dict(include_hash=False)):
            raise Exp01ScientificContractError("seed projection replay mismatch")

    @property
    def arm_id(self) -> str:
        return self.backend_receipt.arm_id

    @property
    def view_id(self) -> str:
        return self.backend_receipt.view_id

    @property
    def seed(self) -> int:
        return self.backend_receipt.seed

    @property
    def checkpoint_hash(self) -> str:
        return self.backend_receipt.checkpoint_hash

    @property
    def graph_edges(self) -> tuple[tuple[str, str], ...]:
        return self.backend_receipt.graph_edges

    @property
    def graph_hash(self) -> str:
        return self.backend_receipt.extraction_graph_hash

    @property
    def view_receipt_hash(self) -> str:
        return self.backend_receipt.view_receipt_hash

    @property
    def backend_receipt_hash(self) -> str:
        return self.backend_receipt.receipt_hash

    @property
    def preregistration_hash(self) -> str:
        return self.backend_receipt.preregistration_hash

    @property
    def training_config_hash(self) -> str:
        return self.backend_receipt.training_config_hash

    @property
    def upstream_commit(self) -> str:
        return self.backend_receipt.upstream_commit

    @property
    def backend_classification(self) -> str:
        return self.backend_receipt.backend_classification

    @property
    def neighbor_policy_hash(self) -> str:
        return self.backend_receipt.neighbor_policy_hash

    @property
    def labels_accessed(self) -> bool:
        return self.backend_receipt.labels_accessed

    @property
    def test_accessed(self) -> bool:
        return self.backend_receipt.test_accessed

    def to_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        value = {
            "schema": "paperworks.validation_v2.exp01_seed_projection_v2", "schema_version": SCHEMA_VERSION,
            "arm_id": self.arm_id, "view_id": self.view_id, "seed": self.seed,
            "authority_hash": self.authority_hash, "view_receipt_hash": self.view_receipt_hash,
            "checkpoint_hash": self.checkpoint_hash, "graph_hash": self.graph_hash,
            "backend_receipt_hash": self.backend_receipt_hash, "contract_hash": self.contract_hash,
            "redaction": "HASH_ONLY_NO_GRAPH_EDGES_SCORES_LOSSES_MATRICES_OR_PRIVATE_PATHS",
        }
        if include_hash:
            value["receipt_hash"] = self.receipt_hash
        return value


def build_seed_projection_v1(*, backend_receipt: BackendExecutionReceiptV1) -> SeedReceiptProjectionV1:
    return _with_hash(SeedReceiptProjectionV1, {"backend_receipt": backend_receipt}, "receipt_hash")


@dataclass(frozen=True)
class CheckpointSetReceiptV1:
    authority_hash: str
    view_receipts: tuple[ViewReceiptV1, ViewReceiptV1, ViewReceiptV1]
    seed_receipts: tuple[SeedReceiptProjectionV1, ...]
    contract_hash: str = EXP01_SCIENTIFIC_CONTRACT_HASH
    receipt_hash: str = ""

    def __post_init__(self) -> None:
        if self.authority_hash != PUBLIC_DATA_AUTHORITY_HASH or self.contract_hash != EXP01_SCIENTIFIC_CONTRACT_HASH:
            raise Exp01ScientificContractError("checkpoint set authority changed")
        if type(self.view_receipts) is not tuple or len(self.view_receipts) != 3:
            raise Exp01ScientificContractError("exactly three typed view receipts are required")
        for item in self.view_receipts:
            _require_self_hash(item, expected_type=ViewReceiptV1, hash_field="receipt_hash", name="checkpoint view receipt")
        if tuple(item.view_id for item in self.view_receipts) != tuple(view.value for view in ViewId):
            raise Exp01ScientificContractError("view receipts must use exact combined/train1/train2 order")
        if type(self.seed_receipts) is not tuple:
            raise Exp01ScientificContractError("seed receipts must be an exact tuple")
        for item in self.seed_receipts:
            _require_self_hash(
                item, expected_type=SeedReceiptProjectionV1,
                hash_field="receipt_hash", name="checkpoint seed receipt",
            )
        observed = tuple((item.arm_id, item.view_id, item.seed) for item in self.seed_receipts)
        if observed != EXPECTED_SCHEDULE or len({item.receipt_hash for item in self.seed_receipts}) != len(EXPECTED_SCHEDULE):
            raise Exp01ScientificContractError("checkpoint set must contain the exact ordered 12-run schedule")
        view_hash = {item.view_id: item.receipt_hash for item in self.view_receipts}
        if any(
            not item.receipt_hash
            or item.authority_hash != self.authority_hash
            or item.view_receipt_hash != view_hash[item.view_id]
            for item in self.seed_receipts
        ):
            raise Exp01ScientificContractError("checkpoint set contains a foreign seed or view receipt")
        if self.receipt_hash and self.receipt_hash != stable_hash_v1(self.to_dict(include_hash=False)):
            raise Exp01ScientificContractError("checkpoint set replay mismatch")

    @property
    def view_receipt_hashes(self) -> tuple[str, str, str]:
        return tuple(item.receipt_hash for item in self.view_receipts)  # type: ignore[return-value]

    def to_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        value = {
            "schema": "paperworks.validation_v2.exp01_checkpoint_set_receipt_v2", "schema_version": SCHEMA_VERSION,
            "authority_hash": self.authority_hash,
            "view_receipt_hashes": list(self.view_receipt_hashes),
            "seed_receipt_hashes": [item.receipt_hash for item in self.seed_receipts],
            "schedule": [list(item) for item in EXPECTED_SCHEDULE], "contract_hash": self.contract_hash,
        }
        if include_hash:
            value["receipt_hash"] = self.receipt_hash
        return value


def build_checkpoint_set_receipt_v1(**values: object) -> CheckpointSetReceiptV1:
    return _with_hash(CheckpointSetReceiptV1, dict(values), "receipt_hash")


def _derived_ranked_pairs(
    checkpoint_set: CheckpointSetReceiptV1, *, arm_id: str, view_id: str,
) -> tuple[tuple[str, str], ...]:
    """Replay the public candidate order from the three typed extraction graphs.

    Higher cross-seed support is ordered first, then lower total neighbor rank,
    then the immutable 144-pair universe order.  No score or private row is
    serialized into a public receipt.
    """
    matching = tuple(
        item for item in checkpoint_set.seed_receipts
        if item.arm_id == arm_id and item.view_id == view_id
    )
    if tuple(item.seed for item in matching) != SEEDS:
        raise Exp01ScientificContractError("candidate derivation requires the exact three seed graphs")
    positions: dict[tuple[str, str], list[int]] = {}
    for receipt in matching:
        for position, pair in enumerate(receipt.graph_edges):
            if pair in PAIR_UNIVERSE:
                positions.setdefault(pair, []).append(position)
    universe_position = {pair: index for index, pair in enumerate(PAIR_UNIVERSE)}
    return tuple(sorted(
        positions,
        key=lambda pair: (-len(positions[pair]), sum(positions[pair]), universe_position[pair]),
    ))


@dataclass(frozen=True)
class CandidateAggregateReceiptV1:
    arm_id: str
    view_id: str
    checkpoint_set: CheckpointSetReceiptV1
    ranked_pairs: tuple[tuple[str, str], ...]
    top10: tuple[tuple[str, str], ...]
    top20: tuple[tuple[str, str], ...]
    top40: tuple[tuple[str, str], ...]
    meta_reference_hash: str = META_RESULT_HASH
    stat_reference_hash: str = STAT_RESULT_HASH
    pair_universe_hash: str = PAIR_UNIVERSE_HASH
    contract_hash: str = EXP01_SCIENTIFIC_CONTRACT_HASH
    receipt_hash: str = ""

    def __post_init__(self) -> None:
        if (self.arm_id, self.view_id) not in EXPECTED_AGGREGATES:
            raise Exp01ScientificContractError("candidate aggregation arm/view is not preregistered")
        if type(self.checkpoint_set) is not CheckpointSetReceiptV1 or not self.checkpoint_set.receipt_hash:
            raise Exp01ScientificContractError("candidate aggregation requires the typed checkpoint set")
        _require_self_hash(
            self.checkpoint_set, expected_type=CheckpointSetReceiptV1,
            hash_field="receipt_hash", name="candidate checkpoint set",
        )
        ranked = _pairs(self.ranked_pairs, allow_empty=True)
        if ranked != _derived_ranked_pairs(self.checkpoint_set, arm_id=self.arm_id, view_id=self.view_id):
            raise Exp01ScientificContractError("candidate ranking does not replay the typed extraction graphs")
        if (self.top10, self.top20, self.top40) != (ranked[:10], ranked[:20], ranked[:40]):
            raise Exp01ScientificContractError("Top-K outputs must be exact unpadded prefixes")
        if (
            self.meta_reference_hash != META_RESULT_HASH
            or self.stat_reference_hash != STAT_RESULT_HASH
            or self.pair_universe_hash != PAIR_UNIVERSE_HASH
            or self.contract_hash != EXP01_SCIENTIFIC_CONTRACT_HASH
        ):
            raise Exp01ScientificContractError("candidate aggregation authority changed")
        if self.receipt_hash and self.receipt_hash != stable_hash_v1(self.to_dict(include_hash=False)):
            raise Exp01ScientificContractError("candidate aggregation replay mismatch")

    @property
    def checkpoint_set_hash(self) -> str:
        return self.checkpoint_set.receipt_hash

    def to_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        value = {
            "schema": "paperworks.validation_v2.exp01_candidate_aggregate_receipt_v2", "schema_version": SCHEMA_VERSION,
            "arm_id": self.arm_id, "view_id": self.view_id, "checkpoint_set_hash": self.checkpoint_set_hash,
            "ranked_pairs": [list(item) for item in self.ranked_pairs],
            "top10": [list(item) for item in self.top10], "top20": [list(item) for item in self.top20],
            "top40": [list(item) for item in self.top40], "empty_outcome": not self.ranked_pairs,
            "meta_reference_hash": self.meta_reference_hash, "stat_reference_hash": self.stat_reference_hash,
            "pair_universe_hash": self.pair_universe_hash, "contract_hash": self.contract_hash,
        }
        if include_hash:
            value["receipt_hash"] = self.receipt_hash
        return value


def build_candidate_aggregate_receipt_v1(
    *, arm_id: ArmId, view_id: ViewId, checkpoint_set: CheckpointSetReceiptV1,
    ranked_pairs: Iterable[Sequence[str]] | None = None,
) -> CandidateAggregateReceiptV1:
    derived = _derived_ranked_pairs(checkpoint_set, arm_id=arm_id.value, view_id=view_id.value)
    ranked = derived if ranked_pairs is None else _pairs(ranked_pairs, allow_empty=True)
    return _with_hash(CandidateAggregateReceiptV1, {
        "arm_id": arm_id.value, "view_id": view_id.value, "checkpoint_set": checkpoint_set,
        "ranked_pairs": ranked, "top10": ranked[:10], "top20": ranked[:20], "top40": ranked[:40],
    }, "receipt_hash")


@dataclass(frozen=True)
class CandidateUnionAuthorityV1:
    candidate_aggregates: tuple[CandidateAggregateReceiptV1, ...]
    candidate_pairs: tuple[tuple[str, str], ...]
    candidate_provenance_hash: str
    contract_hash: str = EXP01_SCIENTIFIC_CONTRACT_HASH
    authority_hash: str = ""

    def __post_init__(self) -> None:
        if type(self.candidate_aggregates) is not tuple or len(self.candidate_aggregates) != 4:
            raise Exp01ScientificContractError("candidate union requires four typed aggregates")
        if tuple((item.arm_id, item.view_id) for item in self.candidate_aggregates) != EXPECTED_AGGREGATES:
            raise Exp01ScientificContractError("candidate union aggregate coverage or order changed")
        for item in self.candidate_aggregates:
            _require_self_hash(
                item, expected_type=CandidateAggregateReceiptV1,
                hash_field="receipt_hash", name="candidate union aggregate",
            )
        expected_pairs = tuple(
            pair for pair in PAIR_UNIVERSE
            if any(pair in aggregate.top20 for aggregate in self.candidate_aggregates)
        )
        if self.candidate_pairs != expected_pairs:
            raise Exp01ScientificContractError("candidate union does not replay aggregate Top-20 outputs")
        provenance = {
            f"{source}->{target}": [
                item.receipt_hash for item in self.candidate_aggregates if (source, target) in item.top20
            ]
            for source, target in expected_pairs
        }
        if self.candidate_provenance_hash != stable_hash_v1(provenance):
            raise Exp01ScientificContractError("candidate union provenance does not replay")
        if self.contract_hash != EXP01_SCIENTIFIC_CONTRACT_HASH:
            raise Exp01ScientificContractError("candidate union contract changed")
        if self.authority_hash and self.authority_hash != stable_hash_v1(self.to_dict(include_hash=False)):
            raise Exp01ScientificContractError("candidate union authority replay mismatch")

    @property
    def candidate_aggregate_hashes(self) -> tuple[str, str, str, str]:
        return tuple(item.receipt_hash for item in self.candidate_aggregates)  # type: ignore[return-value]

    @property
    def candidate_stage_hash(self) -> str:
        return stable_hash_v1({"candidate_aggregate_hashes": list(self.candidate_aggregate_hashes)})

    def to_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        value = {
            "schema": "paperworks.validation_v2.exp01_candidate_union_authority_v2",
            "schema_version": SCHEMA_VERSION,
            "candidate_aggregate_hashes": list(self.candidate_aggregate_hashes),
            "candidate_stage_hash": self.candidate_stage_hash,
            "candidate_pair_set_hash": stable_hash_v1({"pairs": self.candidate_pairs}),
            "candidate_pair_count": len(self.candidate_pairs),
            "candidate_provenance_hash": self.candidate_provenance_hash,
            "contract_hash": self.contract_hash,
            "redaction": "HASH_ONLY_NO_ARM_IDENTITY_OR_PRIVATE_VALUES",
        }
        if include_hash:
            value["authority_hash"] = self.authority_hash
        return value


def build_candidate_union_authority_v1(
    *, candidate_aggregates: tuple[CandidateAggregateReceiptV1, ...],
) -> CandidateUnionAuthorityV1:
    union = tuple(
        pair for pair in PAIR_UNIVERSE
        if any(pair in aggregate.top20 for aggregate in candidate_aggregates)
    )
    provenance = {
        f"{source}->{target}": [
            item.receipt_hash for item in candidate_aggregates if (source, target) in item.top20
        ]
        for source, target in union
    }
    return _with_hash(CandidateUnionAuthorityV1, {
        "candidate_aggregates": candidate_aggregates,
        "candidate_pairs": union,
        "candidate_provenance_hash": stable_hash_v1(provenance),
    }, "authority_hash")


@dataclass(frozen=True)
class ProfilingSubmissionV1:
    candidate_aggregate_hashes: tuple[str, str, str, str]
    candidate_pairs: tuple[tuple[str, str], ...]
    candidate_provenance_hash: str
    candidate_union_authority_hash: str
    train3_file_hash: str = NORMAL_FILE_HASHES[2][2]
    arm_identity_exposed: bool = False
    contract_hash: str = EXP01_SCIENTIFIC_CONTRACT_HASH
    submission_hash: str = ""

    def __post_init__(self) -> None:
        if type(self.candidate_aggregate_hashes) is not tuple or len(self.candidate_aggregate_hashes) != 4:
            raise Exp01ScientificContractError("profiling requires four aggregate identities")
        for value in (*self.candidate_aggregate_hashes, self.candidate_provenance_hash, self.candidate_union_authority_hash):
            _sha(value, "profiling_hash_binding")
        pairs = _pairs(self.candidate_pairs, allow_empty=True)
        if pairs != tuple(pair for pair in PAIR_UNIVERSE if pair in set(pairs)):
            raise Exp01ScientificContractError("profiling union must use canonical 144-pair order")
        _strict_bool(self.arm_identity_exposed, "arm_identity_exposed")
        if (
            self.arm_identity_exposed
            or self.train3_file_hash != NORMAL_FILE_HASHES[2][2]
            or self.contract_hash != EXP01_SCIENTIFIC_CONTRACT_HASH
        ):
            raise Exp01ScientificContractError("profiling submission must be arm-blind normal train3")
        if self.submission_hash and self.submission_hash != stable_hash_v1(self.to_dict(include_hash=False)):
            raise Exp01ScientificContractError("profiling submission replay mismatch")

    @property
    def candidate_stage_hash(self) -> str:
        return stable_hash_v1({"candidate_aggregate_hashes": list(self.candidate_aggregate_hashes)})

    def to_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        value = {
            "schema": "paperworks.validation_v2.exp01_profiling_submission_v2", "schema_version": SCHEMA_VERSION,
            "candidate_aggregate_hashes": list(self.candidate_aggregate_hashes),
            "candidate_stage_hash": self.candidate_stage_hash,
            "candidate_provenance_hash": self.candidate_provenance_hash,
            "candidate_union_authority_hash": self.candidate_union_authority_hash,
            "candidate_pairs": [list(item) for item in self.candidate_pairs],
            "candidate_count": len(self.candidate_pairs), "empty_outcome": not self.candidate_pairs,
            "train3_file_hash": self.train3_file_hash, "arm_identity_exposed": self.arm_identity_exposed,
            "contract_hash": self.contract_hash,
        }
        if include_hash:
            value["submission_hash"] = self.submission_hash
        return value


def build_profiling_submission_v1(
    *, candidate_union: CandidateUnionAuthorityV1,
) -> ProfilingSubmissionV1:
    _require_self_hash(
        candidate_union, expected_type=CandidateUnionAuthorityV1,
        hash_field="authority_hash", name="profiling candidate union",
    )
    return _with_hash(ProfilingSubmissionV1, {
        "candidate_aggregate_hashes": candidate_union.candidate_aggregate_hashes,
        "candidate_pairs": candidate_union.candidate_pairs,
        "candidate_provenance_hash": candidate_union.candidate_provenance_hash,
        "candidate_union_authority_hash": candidate_union.authority_hash,
    }, "submission_hash")


@dataclass(frozen=True)
class ConfirmationReceiptV1:
    candidate_union: CandidateUnionAuthorityV1
    submission: ProfilingSubmissionV1
    candidate_count: int
    decision_ledger_hash: str
    confirmed_pairs: tuple[tuple[str, str], ...]
    rejected_pairs: tuple[tuple[str, str], ...]
    labels_accessed: bool = False
    test_accessed: bool = False
    contract_hash: str = EXP01_SCIENTIFIC_CONTRACT_HASH
    receipt_hash: str = ""

    def __post_init__(self) -> None:
        _require_self_hash(
            self.candidate_union, expected_type=CandidateUnionAuthorityV1,
            hash_field="authority_hash", name="confirmation candidate union",
        )
        _require_self_hash(
            self.submission, expected_type=ProfilingSubmissionV1,
            hash_field="submission_hash", name="confirmation profiling submission",
        )
        if (
            self.submission.candidate_union_authority_hash != self.candidate_union.authority_hash
            or self.submission.candidate_stage_hash != self.candidate_union.candidate_stage_hash
            or self.submission.candidate_pairs != self.candidate_union.candidate_pairs
            or self.submission.candidate_provenance_hash != self.candidate_union.candidate_provenance_hash
        ):
            raise Exp01ScientificContractError("arm-blind submission does not replay the candidate union authority")
        if self.candidate_count != len(self.submission.candidate_pairs):
            raise Exp01ScientificContractError("confirmation count must equal the submitted pair count")
        confirmed = _pairs(self.confirmed_pairs, allow_empty=True)
        rejected = _pairs(self.rejected_pairs, allow_empty=True)
        if set(confirmed) & set(rejected) or set(confirmed) | set(rejected) != set(self.submission.candidate_pairs):
            raise Exp01ScientificContractError("confirmation partition must exactly cover the submission")
        _sha(self.decision_ledger_hash, "decision_ledger_hash")
        for name in ("labels_accessed", "test_accessed"):
            _strict_bool(getattr(self, name), name)
            if getattr(self, name):
                raise Exp01ScientificContractError("confirmation must use normal train3 only")
        if self.contract_hash != EXP01_SCIENTIFIC_CONTRACT_HASH:
            raise Exp01ScientificContractError("confirmation contract changed")
        if self.receipt_hash and self.receipt_hash != stable_hash_v1(self.to_dict(include_hash=False)):
            raise Exp01ScientificContractError("confirmation receipt replay mismatch")

    @property
    def submission_hash(self) -> str:
        return self.submission.submission_hash

    @property
    def confirmed_pair_set_hash(self) -> str:
        return stable_hash_v1({"pairs": self.confirmed_pairs})

    @property
    def rejected_pair_set_hash(self) -> str:
        return stable_hash_v1({"pairs": self.rejected_pairs})

    def to_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        value = {
            "schema": "paperworks.validation_v2.exp01_confirmation_receipt_v2", "schema_version": SCHEMA_VERSION,
            "candidate_union_authority_hash": self.candidate_union.authority_hash,
            "submission_hash": self.submission_hash, "candidate_count": self.candidate_count,
            "decision_ledger_hash": self.decision_ledger_hash,
            "confirmed_pair_set_hash": self.confirmed_pair_set_hash,
            "rejected_pair_set_hash": self.rejected_pair_set_hash,
            "labels_accessed": self.labels_accessed, "test_accessed": self.test_accessed,
            "contract_hash": self.contract_hash, "redaction": "HASH_ONLY_NO_RELATION_NUMERICS_OR_PRIVATE_ROWS",
        }
        if include_hash:
            value["receipt_hash"] = self.receipt_hash
        return value


def build_confirmation_receipt_v1(
    *, candidate_union: CandidateUnionAuthorityV1, submission: ProfilingSubmissionV1, decision_ledger_hash: str,
    confirmed_pairs: Iterable[Sequence[str]], rejected_pairs: Iterable[Sequence[str]],
) -> ConfirmationReceiptV1:
    return _with_hash(ConfirmationReceiptV1, {
        "candidate_union": candidate_union, "submission": submission,
        "candidate_count": len(submission.candidate_pairs),
        "decision_ledger_hash": decision_ledger_hash,
        "confirmed_pairs": _pairs(confirmed_pairs, allow_empty=True),
        "rejected_pairs": _pairs(rejected_pairs, allow_empty=True),
    }, "receipt_hash")


@dataclass(frozen=True)
class MaskInterventionReceiptV1:
    corrected_seed_receipt: SeedReceiptProjectionV1
    checkpoint_set: CheckpointSetReceiptV1
    primary_mask_pairs: tuple[tuple[str, str], ...]
    baseline_graph_edges: tuple[tuple[str, str], ...]
    intervened_graph_edges: tuple[tuple[str, str], ...]
    baseline_metric_hash: str
    intervention_metric_hash: str
    train4_file_hash: str = NORMAL_FILE_HASHES[3][2]
    intervention_policy: str = REMOVE_WITHOUT_REFILL
    intervention_status: str = "EVALUATED"
    added_edge_count: int = 0
    refill_performed: bool = False
    labels_accessed: bool = False
    test_accessed: bool = False
    contract_hash: str = EXP01_SCIENTIFIC_CONTRACT_HASH
    receipt_hash: str = ""

    def __post_init__(self) -> None:
        _require_self_hash(
            self.checkpoint_set, expected_type=CheckpointSetReceiptV1,
            hash_field="receipt_hash", name="mask checkpoint set",
        )
        seed = self.corrected_seed_receipt
        _require_self_hash(
            seed, expected_type=SeedReceiptProjectionV1,
            hash_field="receipt_hash", name="mask corrected seed",
        )
        if (
            seed.arm_id != ArmId.CORRECTED_SELF_EXCLUDED.value
            or seed.view_id != ViewId.COMBINED.value
            or seed not in self.checkpoint_set.seed_receipts
        ):
            raise Exp01ScientificContractError("mask receipt must bind a corrected combined-view seed")
        mask = _pairs(self.primary_mask_pairs, allow_empty=True)
        baseline = _graph_pairs(self.baseline_graph_edges)
        intervened = _graph_pairs(self.intervened_graph_edges)
        if baseline != seed.graph_edges:
            raise Exp01ScientificContractError("mask baseline graph differs from the corrected seed graph")
        if not set(mask).issubset(set(baseline)):
            raise Exp01ScientificContractError("primary mask contains a nonexistent baseline edge")
        expected_intervened = tuple(edge for edge in baseline if edge not in set(mask))
        if intervened != expected_intervened:
            raise Exp01ScientificContractError("intervened graph must be exact removal without refill")
        if type(self.added_edge_count) is not int or self.added_edge_count != 0:
            raise Exp01ScientificContractError("mask intervention added an edge")
        _strict_bool(self.refill_performed, "refill_performed")
        if self.refill_performed:
            raise Exp01ScientificContractError("mask intervention refill is forbidden")
        if self.train4_file_hash != NORMAL_FILE_HASHES[3][2] or self.intervention_policy != REMOVE_WITHOUT_REFILL:
            raise Exp01ScientificContractError("mask intervention split or policy changed")
        for name in ("baseline_metric_hash", "intervention_metric_hash"):
            _sha(getattr(self, name), name)
        expected_status = "EVALUATED" if mask else "NOT_APPLICABLE_EMPTY_PRIMARY_MASK"
        if self.intervention_status != expected_status:
            raise Exp01ScientificContractError("mask intervention status does not match mask applicability")
        if not mask and self.intervention_metric_hash != self.baseline_metric_hash:
            raise Exp01ScientificContractError("empty-mask intervention must preserve the baseline metric identity")
        for name in ("labels_accessed", "test_accessed"):
            _strict_bool(getattr(self, name), name)
            if getattr(self, name):
                raise Exp01ScientificContractError("mask intervention must use normal train4 only")
        if self.contract_hash != EXP01_SCIENTIFIC_CONTRACT_HASH:
            raise Exp01ScientificContractError("mask intervention contract changed")
        if self.receipt_hash and self.receipt_hash != stable_hash_v1(self.to_dict(include_hash=False)):
            raise Exp01ScientificContractError("mask intervention replay mismatch")

    @property
    def seed(self) -> int:
        return self.corrected_seed_receipt.seed

    @property
    def checkpoint_set_hash(self) -> str:
        return self.checkpoint_set.receipt_hash

    @property
    def primary_mask_pair_set_hash(self) -> str:
        return stable_hash_v1({"pairs": self.primary_mask_pairs})

    def to_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        value = {
            "schema": "paperworks.validation_v2.exp01_mask_intervention_receipt_v2", "schema_version": SCHEMA_VERSION,
            "seed": self.seed, "checkpoint_set_hash": self.checkpoint_set_hash,
            "corrected_seed_receipt_hash": self.corrected_seed_receipt.receipt_hash,
            "primary_mask_pair_set_hash": self.primary_mask_pair_set_hash,
            "primary_mask_pair_count": len(self.primary_mask_pairs),
            "baseline_graph_hash": stable_hash_v1({"graph_edges": self.baseline_graph_edges}),
            "intervened_graph_hash": stable_hash_v1({"graph_edges": self.intervened_graph_edges}),
            "removed_edge_count": len(self.primary_mask_pairs), "added_edge_count": self.added_edge_count,
            "refill_performed": self.refill_performed,
            "baseline_metric_hash": self.baseline_metric_hash,
            "intervention_metric_hash": self.intervention_metric_hash,
            "train4_file_hash": self.train4_file_hash, "intervention_policy": self.intervention_policy,
            "intervention_status": self.intervention_status,
            "labels_accessed": self.labels_accessed, "test_accessed": self.test_accessed,
            "contract_hash": self.contract_hash, "redaction": "NO_NUMERIC_METRICS_OR_PRIVATE_PATHS",
        }
        if include_hash:
            value["receipt_hash"] = self.receipt_hash
        return value


def build_mask_intervention_receipt_v1(**values: object) -> MaskInterventionReceiptV1:
    supplied = dict(values)
    supplied["primary_mask_pairs"] = _pairs(supplied["primary_mask_pairs"], allow_empty=True)  # type: ignore[arg-type]
    supplied["baseline_graph_edges"] = _graph_pairs(supplied["baseline_graph_edges"])  # type: ignore[arg-type]
    supplied["intervened_graph_edges"] = _graph_pairs(supplied["intervened_graph_edges"])  # type: ignore[arg-type]
    supplied.setdefault(
        "intervention_status",
        "EVALUATED" if supplied["primary_mask_pairs"] else "NOT_APPLICABLE_EMPTY_PRIMARY_MASK",
    )
    return _with_hash(MaskInterventionReceiptV1, supplied, "receipt_hash")


def _typed_stage_evidence_hash(
    next_stage: Stage, evidence: object, *, state: "StageStateV1 | None" = None,
) -> str:
    if next_stage is Stage.AUTHORITY_BOUND:
        if type(evidence) is not PublicDataAuthorityV1 or evidence.authority_hash != PUBLIC_DATA_AUTHORITY_HASH:
            raise Exp01ScientificContractError("authority stage requires the exact typed authority")
        return evidence.authority_hash
    if next_stage is Stage.VIEWS_MATERIALIZED:
        if type(evidence) is not tuple or len(evidence) != 3 or any(type(item) is not ViewReceiptV1 for item in evidence):
            raise Exp01ScientificContractError("view stage requires exact typed views")
        for item in evidence:
            _require_self_hash(item, expected_type=ViewReceiptV1, hash_field="receipt_hash", name="staged view receipt")
        if tuple(item.view_id for item in evidence) != tuple(view.value for view in ViewId):
            raise Exp01ScientificContractError("view stage order changed")
        if state is not None and any(item.authority_hash != state.completed_receipt_hashes[0] for item in evidence):
            raise Exp01ScientificContractError("view stage does not bind the staged authority")
        return stable_hash_v1({"view_receipt_hashes": [item.receipt_hash for item in evidence]})
    if next_stage is Stage.SEEDS_COMPLETED:
        _require_self_hash(evidence, expected_type=CheckpointSetReceiptV1, hash_field="receipt_hash", name="seed checkpoint set")
        if state is not None:
            if evidence.authority_hash != state.completed_receipt_hashes[0]:
                raise Exp01ScientificContractError("checkpoint set does not bind the staged authority")
            view_stage_hash = stable_hash_v1({"view_receipt_hashes": list(evidence.view_receipt_hashes)})
            if view_stage_hash != state.completed_receipt_hashes[1]:
                raise Exp01ScientificContractError("checkpoint set does not bind the staged views")
        return evidence.receipt_hash
    if next_stage is Stage.CANDIDATES_AGGREGATED:
        if type(evidence) is not tuple or len(evidence) != 4 or any(type(item) is not CandidateAggregateReceiptV1 for item in evidence):
            raise Exp01ScientificContractError("candidate stage requires four typed aggregates")
        if tuple((item.arm_id, item.view_id) for item in evidence) != EXPECTED_AGGREGATES:
            raise Exp01ScientificContractError("candidate aggregate coverage or order changed")
        if len({item.receipt_hash for item in evidence}) != 4:
            raise Exp01ScientificContractError("candidate aggregate receipts duplicate")
        for item in evidence:
            _require_self_hash(
                item, expected_type=CandidateAggregateReceiptV1,
                hash_field="receipt_hash", name="staged candidate aggregate",
            )
        if state is not None and any(item.checkpoint_set_hash != state.completed_receipt_hashes[2] for item in evidence):
            raise Exp01ScientificContractError("candidate aggregates do not bind the staged checkpoint set")
        return stable_hash_v1({"candidate_aggregate_hashes": [item.receipt_hash for item in evidence]})
    if next_stage is Stage.PROFILING_CONFIRMED:
        _require_self_hash(evidence, expected_type=ConfirmationReceiptV1, hash_field="receipt_hash", name="arm-blind confirmation")
        _require_self_hash(
            evidence.submission, expected_type=ProfilingSubmissionV1,
            hash_field="submission_hash", name="arm-blind profiling submission",
        )
        if state is not None and evidence.submission.candidate_stage_hash != state.completed_receipt_hashes[3]:
            raise Exp01ScientificContractError("confirmation does not bind the staged candidate union")
        return evidence.receipt_hash
    if next_stage is Stage.MASK_INTERVENTION_COMPLETED:
        if type(evidence) is not tuple or len(evidence) != 3 or any(type(item) is not MaskInterventionReceiptV1 for item in evidence):
            raise Exp01ScientificContractError("mask stage requires three typed intervention receipts")
        if tuple(item.seed for item in evidence) != SEEDS or len({item.receipt_hash for item in evidence}) != 3:
            raise Exp01ScientificContractError("mask receipts must cover exact seeds once")
        if len({item.primary_mask_pair_set_hash for item in evidence}) != 1:
            raise Exp01ScientificContractError("all seeds must use the same frozen primary mask")
        for item in evidence:
            _require_self_hash(
                item, expected_type=MaskInterventionReceiptV1,
                hash_field="receipt_hash", name="staged mask intervention",
            )
        if state is not None and any(item.checkpoint_set_hash != state.completed_receipt_hashes[2] for item in evidence):
            raise Exp01ScientificContractError("mask interventions do not bind the staged checkpoint set")
        return stable_hash_v1({"intervention_receipt_hashes": [item.receipt_hash for item in evidence]})
    if next_stage is Stage.INCLUSION_HANDOFF_READY:
        _require_self_hash(
            evidence, expected_type=InclusionEvidenceHandoffV1,
            hash_field="handoff_hash", name="inclusion handoff",
        )
        if state is None or evidence.stage_state_hash != state.state_hash:
            raise Exp01ScientificContractError("inclusion handoff does not bind the mask-complete state")
        return evidence.handoff_hash
    raise Exp01ScientificContractError("unsupported typed stage evidence")


@dataclass(frozen=True)
class StageStateV1:
    stage: str = Stage.CREATED.value
    completed_receipt_hashes: tuple[str, ...] = ()
    previous_state_hash: str | None = None
    contract_hash: str = EXP01_SCIENTIFIC_CONTRACT_HASH
    state_hash: str = ""

    def __post_init__(self) -> None:
        if self.stage not in {item.value for item in Stage} or self.contract_hash != EXP01_SCIENTIFIC_CONTRACT_HASH:
            raise Exp01ScientificContractError("stage state is invalid or stale")
        expected_count = STAGE_ORDER.index(Stage(self.stage))
        if len(self.completed_receipt_hashes) != expected_count or len(set(self.completed_receipt_hashes)) != expected_count:
            raise Exp01ScientificContractError("stage receipt count does not match stage order")
        for value in self.completed_receipt_hashes:
            _sha(value, "completed_receipt_hash")
        if expected_count == 0 and self.previous_state_hash is not None:
            raise Exp01ScientificContractError("initial state cannot have a predecessor")
        if expected_count > 0:
            _sha(self.previous_state_hash or "", "previous_state_hash")
        if self.state_hash and self.state_hash != stable_hash_v1(self.to_dict(include_hash=False)):
            raise Exp01ScientificContractError("stage state replay mismatch")

    def to_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        value = {
            "schema": "paperworks.validation_v2.exp01_stage_state_v2", "schema_version": SCHEMA_VERSION,
            "stage": self.stage, "completed_receipt_hashes": list(self.completed_receipt_hashes),
            "previous_state_hash": self.previous_state_hash, "contract_hash": self.contract_hash,
        }
        if include_hash:
            value["state_hash"] = self.state_hash
        return value


def initial_stage_state_v1() -> StageStateV1:
    return _with_hash(StageStateV1, {}, "state_hash")


def advance_stage_v1(state: StageStateV1, *, next_stage: Stage, evidence: object) -> StageStateV1:
    if type(state) is not StageStateV1 or not state.state_hash or state.state_hash != stable_hash_v1(state.to_dict(include_hash=False)):
        raise Exp01ScientificContractError("self-hashed prior stage state is required")
    current_index = STAGE_ORDER.index(Stage(state.stage))
    if current_index + 1 >= len(STAGE_ORDER) or STAGE_ORDER[current_index + 1] is not next_stage:
        raise Exp01ScientificContractError("EXP-01 stage transition is out of order")
    receipt_hash = _typed_stage_evidence_hash(next_stage, evidence, state=state)
    return _with_hash(StageStateV1, {
        "stage": next_stage.value,
        "completed_receipt_hashes": (*state.completed_receipt_hashes, receipt_hash),
        "previous_state_hash": state.state_hash,
    }, "state_hash")


@dataclass(frozen=True)
class InclusionEvidenceHandoffV1:
    stage_state_hash: str
    authority_hash: str
    checkpoint_set_hash: str
    candidate_aggregate_hashes: tuple[str, str, str, str]
    confirmation_receipt_hashes: tuple[str]
    intervention_receipt_hashes: tuple[str, str, str]
    inclusion_evidence_hash: str
    complete: bool = True
    scientific_result_claimed: bool = False
    contract_hash: str = EXP01_SCIENTIFIC_CONTRACT_HASH
    handoff_hash: str = ""

    def __post_init__(self) -> None:
        for value in (
            self.stage_state_hash, self.authority_hash, self.checkpoint_set_hash,
            *self.candidate_aggregate_hashes, *self.confirmation_receipt_hashes,
            *self.intervention_receipt_hashes, self.inclusion_evidence_hash,
        ):
            _sha(value, "handoff_hash_binding")
        if (
            self.authority_hash != PUBLIC_DATA_AUTHORITY_HASH
            or type(self.candidate_aggregate_hashes) is not tuple
            or len(self.candidate_aggregate_hashes) != 4
            or len(set(self.candidate_aggregate_hashes)) != 4
            or type(self.confirmation_receipt_hashes) is not tuple
            or len(self.confirmation_receipt_hashes) != 1
            or len(set(self.confirmation_receipt_hashes)) != 1
            or type(self.intervention_receipt_hashes) is not tuple
            or len(self.intervention_receipt_hashes) != 3
            or len(set(self.intervention_receipt_hashes)) != 3
        ):
            raise Exp01ScientificContractError("handoff contains duplicate or foreign authority bindings")
        for name in ("complete", "scientific_result_claimed"):
            _strict_bool(getattr(self, name), name)
        if not self.complete or self.scientific_result_claimed or self.contract_hash != EXP01_SCIENTIFIC_CONTRACT_HASH:
            raise Exp01ScientificContractError("handoff cannot fabricate a scientific result")
        if self.handoff_hash and self.handoff_hash != stable_hash_v1(self.to_dict(include_hash=False)):
            raise Exp01ScientificContractError("inclusion handoff replay mismatch")

    def to_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        value = {
            "schema": "paperworks.validation_v2.exp01_inclusion_handoff_v2", "schema_version": SCHEMA_VERSION,
            "stage_state_hash": self.stage_state_hash, "authority_hash": self.authority_hash,
            "checkpoint_set_hash": self.checkpoint_set_hash,
            "candidate_aggregate_hashes": list(self.candidate_aggregate_hashes),
            "confirmation_receipt_hashes": list(self.confirmation_receipt_hashes),
            "intervention_receipt_hashes": list(self.intervention_receipt_hashes),
            "inclusion_evidence_hash": self.inclusion_evidence_hash, "complete": self.complete,
            "scientific_result_claimed": self.scientific_result_claimed, "contract_hash": self.contract_hash,
        }
        if include_hash:
            value["handoff_hash"] = self.handoff_hash
        return value


def build_inclusion_evidence_handoff_v1(
    *, final_state: StageStateV1, authority: PublicDataAuthorityV1,
    checkpoint_set: CheckpointSetReceiptV1,
    candidate_aggregates: tuple[CandidateAggregateReceiptV1, ...],
    confirmation: ConfirmationReceiptV1,
    interventions: tuple[MaskInterventionReceiptV1, ...],
    inclusion_evidence_hash: str,
) -> InclusionEvidenceHandoffV1:
    _require_self_hash(
        final_state, expected_type=StageStateV1,
        hash_field="state_hash", name="mask-complete stage state",
    )
    _require_self_hash(
        authority, expected_type=PublicDataAuthorityV1,
        hash_field="authority_hash", name="handoff public authority",
    )
    _require_self_hash(
        checkpoint_set, expected_type=CheckpointSetReceiptV1,
        hash_field="receipt_hash", name="handoff checkpoint set",
    )
    _require_self_hash(
        confirmation, expected_type=ConfirmationReceiptV1,
        hash_field="receipt_hash", name="handoff confirmation",
    )
    if final_state.stage != Stage.MASK_INTERVENTION_COMPLETED.value:
        raise Exp01ScientificContractError("inclusion handoff requires complete typed stages")
    if type(candidate_aggregates) is not tuple or len(candidate_aggregates) != 4:
        raise Exp01ScientificContractError("handoff requires exact candidate aggregates")
    if type(interventions) is not tuple or len(interventions) != 3:
        raise Exp01ScientificContractError("handoff requires exact mask interventions")
    expected_candidate_hashes = tuple(item.receipt_hash for item in candidate_aggregates)
    if confirmation.candidate_union.candidate_aggregate_hashes != expected_candidate_hashes:
        raise Exp01ScientificContractError("confirmation union does not bind the supplied candidate aggregates")

    replayed = initial_stage_state_v1()
    for stage, evidence in (
        (Stage.AUTHORITY_BOUND, authority),
        (Stage.VIEWS_MATERIALIZED, checkpoint_set.view_receipts),
        (Stage.SEEDS_COMPLETED, checkpoint_set),
        (Stage.CANDIDATES_AGGREGATED, candidate_aggregates),
        (Stage.PROFILING_CONFIRMED, confirmation),
        (Stage.MASK_INTERVENTION_COMPLETED, interventions),
    ):
        replayed = advance_stage_v1(replayed, next_stage=stage, evidence=evidence)
    if final_state != replayed or final_state.state_hash != replayed.state_hash:
        raise Exp01ScientificContractError("final state does not replay the supplied typed lineage")
    return _with_hash(InclusionEvidenceHandoffV1, {
        "stage_state_hash": final_state.state_hash,
        "authority_hash": authority.authority_hash,
        "checkpoint_set_hash": checkpoint_set.receipt_hash,
        "candidate_aggregate_hashes": tuple(item.receipt_hash for item in candidate_aggregates),
        "confirmation_receipt_hashes": (confirmation.receipt_hash,),
        "intervention_receipt_hashes": tuple(item.receipt_hash for item in interventions),
        "inclusion_evidence_hash": inclusion_evidence_hash,
    }, "handoff_hash")


__all__ = [name for name in globals() if name.startswith("EXP01_") or name in {
    "ArmId", "BACKEND_CLASSIFICATION", "BackendExecutionReceiptV1",
    "CandidateAggregateReceiptV1", "CandidateUnionAuthorityV1", "CheckpointSetReceiptV1",
    "ConfirmationReceiptV1", "CORRECTED_NEIGHBOR_POLICY_HASH", "EXPECTED_AGGREGATES",
    "EXPECTED_SCHEDULE", "Exp01ScientificContractError", "FROZEN_NEIGHBOR_POLICY_HASH",
    "InclusionEvidenceHandoffV1", "MaskInterventionReceiptV1", "PAIR_UNIVERSE",
    "PREREGISTRATION_HASH", "PUBLIC_DATA_AUTHORITY_HASH", "PublicDataAuthorityV1", "SEEDS",
    "SeedReceiptProjectionV1", "Stage", "StageStateV1", "TOP_K", "TRAINING_CONFIG_HASH",
    "UPSTREAM_GDN_COMMIT", "ViewId", "ViewReceiptV1", "advance_stage_v1",
    "build_candidate_aggregate_receipt_v1", "build_checkpoint_set_receipt_v1",
    "build_backend_execution_receipt_v1", "build_candidate_union_authority_v1",
    "build_confirmation_receipt_v1", "build_inclusion_evidence_handoff_v1",
    "build_mask_intervention_receipt_v1", "build_profiling_submission_v1",
    "build_public_data_authority_v1", "build_seed_projection_v1", "build_view_receipt_v1",
    "initial_stage_state_v1",
}]
