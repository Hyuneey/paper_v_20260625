"""Source-aligned GDN backend and fail-closed TASK-039C-GDN gates.

The module is lightweight at import time.  Torch and Torch Geometric are
loaded only after the exact, pre-approved dependency versions have passed.
The existing project smoke backends are deliberately not reused here.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import math
import os
import platform
import random
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from importlib import metadata, util
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from paperworks.v6.common import parse_iso_datetime, require_sha256, stable_hash_v1


TASK039C_GDN_STARTING_COMMIT = "b6522fb83c4cb92d355f98af778f9a6a3c73362f"
TASK039C0_PROTOCOL_BUNDLE_HASH = (
    "41aab751d6bbbaadc72a95ef3289ea6440c26659fb38f640bf17fb0688836dff"
)
TASK039C0_GDN_POLICY_HASH = (
    "9c2387a98312ef6c96ddcd17a871ceb70a96b670eb4a39a7269878101f2ba41a"
)
TASK039C0_PAIR_UNIVERSE_HASH = (
    "fc072d3e18ce4623972c2cb64f6266727092ecae03fdb0f0dd929d705e1d8557"
)
UPSTREAM_GDN_REPOSITORY = "https://github.com/d-ailin/GDN"
UPSTREAM_GDN_COMMIT = "9853899da860682669a134e4af315d036aab4eca"
UPSTREAM_NATIVE_DEPENDENCIES = {
    "torch": "1.5.1",
    "torch-geometric": "1.5.0",
}
APPROVED_PORT_DEPENDENCIES = {
    "torch": "2.12.1",
    "torch-geometric": "2.8.0",
}
FROZEN_SEEDS = (11, 23, 37)
ALLOWED_VALUE_FILES = (
    "hai-23.05/hai-train1.csv",
    "hai-23.05/hai-train2.csv",
)
NORMAL_CANDIDATE_FIT = "NORMAL_CANDIDATE_FIT"

REQUIRED_UPSTREAM_FILES: tuple[tuple[str, str, str], ...] = (
    (
        "models/GDN.py",
        "e967790769a5ea38dfbaed3e0e77b22cd0c5c896",
        "eedcdc73d48e9f34c384b1a7ad875e37580f3177e023d59608a14bc56c60eb66",
    ),
    (
        "models/graph_layer.py",
        "77d9db23df4bfde2db69500d3fda2fc9b378e3e3",
        "0963e4091f9625e867dd90e7b402a277085f5c659a7d70c28880f3ae229b7f79",
    ),
    (
        "datasets/TimeDataset.py",
        "8eb0b4c580b78fec0248069b2c6a81fbe3ce080c",
        "b1b9f6d53080d275d96ea7157bf4ded92131a1b566410fa7a7eaf96cc5084904",
    ),
    (
        "train.py",
        "934bd50ab2acffcb9d028633960f722eae3440de",
        "885687aec4c42ac6a2b4782aced7ebf8785e0d0b56b787f39695a4f1b84169e1",
    ),
    (
        "test.py",
        "58ae62520552cd0548318ed14d4a5fc07965a4f8",
        "156de035bdb1b2d4931787cd863090064e2f4c6b05ae92e3f2103cba305eddeb",
    ),
    (
        "evaluate.py",
        "ae4110dc37d3665a93c1a88de35d313da6b4dd73",
        "daa647f55b26e1dd627257a25b9084c60fc36488f58c45faf9d7455491231e83",
    ),
    (
        "util/net_struct.py",
        "ccc6256180aeb40395004a695446721fe073c754",
        "e0079cc401b2b9cf6e03634146382581accf267918d91c1ebffe628c82a6bac4",
    ),
)

FIDELITY_FIELD_NAMES = (
    "pinned_upstream_repository_and_commit",
    "required_upstream_file_identities",
    "model_architecture_correspondence",
    "node_embedding_construction",
    "learned_topk_graph_construction",
    "similarity_semantics",
    "prediction_graph_usage",
    "prediction_and_loss_path",
    "training_loop_correspondence",
    "preprocessing_correspondence",
    "optimizer_configuration",
    "architecture_hyperparameters",
    "training_hyperparameters",
    "random_seed_control",
    "no_hidden_project_specific_scientific_modification",
    "learned_graph_extraction_correspondence",
)


class UpstreamGDNError(ValueError):
    """Base error for the TASK-039C-GDN arm."""


class UpstreamGDNFidelityError(UpstreamGDNError):
    """Raised when pinned-source or correspondence evidence is incomplete."""


class UpstreamGDNDependencyError(UpstreamGDNError):
    """Raised when the exact approved Torch/PyG port cannot be loaded."""

    issue_code = "GDN_OPTIONAL_DEPENDENCY_UNAVAILABLE"


class UpstreamGDNDataBoundaryError(UpstreamGDNError):
    """Raised before any prohibited data source can be opened."""


class FidelityClassificationV1(str, Enum):
    EXACT_UPSTREAM = "exact_upstream"
    DIMENSION_ADAPTATION = "dimension_adaptation"
    DOCUMENTED_NON_SCIENTIFIC_ADAPTER = "documented_non_scientific_adapter"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class UpstreamFileIdentityV1:
    path: str
    git_blob_sha: str
    sha256: str

    def __post_init__(self) -> None:
        if not self.path or self.path.startswith(("/", "\\")) or ".." in self.path.split("/"):
            raise UpstreamGDNFidelityError("upstream file path must be safe and relative")
        if len(self.git_blob_sha) != 40 or any(c not in "0123456789abcdef" for c in self.git_blob_sha):
            raise UpstreamGDNFidelityError("upstream Git blob identity must be a 40-character SHA")
        require_sha256(self.sha256, "upstream file sha256")

    def to_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "git_blob_sha": self.git_blob_sha,
            "sha256": self.sha256,
        }


FROZEN_UPSTREAM_FILE_IDENTITIES = tuple(
    UpstreamFileIdentityV1(*record) for record in REQUIRED_UPSTREAM_FILES
)


@dataclass(frozen=True)
class UpstreamSourceVerificationV1:
    repository: str
    commit: str
    detached_head: bool
    clean_worktree: bool
    file_records: tuple[UpstreamFileIdentityV1, ...]

    def __post_init__(self) -> None:
        if self.repository != UPSTREAM_GDN_REPOSITORY:
            raise UpstreamGDNFidelityError("pinned upstream repository mismatch")
        if self.commit != UPSTREAM_GDN_COMMIT:
            raise UpstreamGDNFidelityError("pinned upstream commit mismatch")
        if self.file_records != FROZEN_UPSTREAM_FILE_IDENTITIES:
            raise UpstreamGDNFidelityError("required upstream file identity mismatch")
        if not self.detached_head or not self.clean_worktree:
            raise UpstreamGDNFidelityError("upstream reference must be a clean detached checkout")

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "commit": self.commit,
            "detached_head": self.detached_head,
            "clean_worktree": self.clean_worktree,
            "file_records": [record.to_dict() for record in self.file_records],
            "verification_method": "git_commit_blob_identity_and_canonical_blob_sha256",
        }


def assert_upstream_source_observation_v1(
    *,
    repository: str,
    commit: str,
    detached_head: bool,
    clean_worktree: bool,
    file_records: Sequence[UpstreamFileIdentityV1],
) -> UpstreamSourceVerificationV1:
    """Validate an observation against the immutable P1D source inventory."""

    return UpstreamSourceVerificationV1(
        repository=repository,
        commit=commit,
        detached_head=detached_head,
        clean_worktree=clean_worktree,
        file_records=tuple(file_records),
    )


def _git(repository_root: Path, *arguments: str, binary: bool = False) -> str | bytes:
    command = [
        "git",
        "-c",
        f"safe.directory={repository_root.resolve().as_posix()}",
        "-C",
        str(repository_root),
        *arguments,
    ]
    result = subprocess.run(command, check=False, capture_output=True)
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise UpstreamGDNFidelityError(f"pinned upstream Git verification failed: {detail}")
    if binary:
        return result.stdout
    return result.stdout.decode("utf-8", errors="strict").strip()


def verify_pinned_upstream_checkout_v1(repository_root: Path) -> UpstreamSourceVerificationV1:
    """Verify canonical Git blobs, not checkout bytes altered by autocrlf."""

    root = repository_root.resolve()
    repository = str(_git(root, "remote", "get-url", "origin"))
    if repository.endswith(".git"):
        repository = repository[:-4]
    commit = str(_git(root, "rev-parse", "HEAD"))
    # symbolic-ref exits non-zero for the required detached checkout, so use
    # branch --show-current which returns an empty string without failing.
    detached_head = str(_git(root, "branch", "--show-current")) == ""
    clean_worktree = str(_git(root, "status", "--porcelain=v1")) == ""
    observed: list[UpstreamFileIdentityV1] = []
    for expected in FROZEN_UPSTREAM_FILE_IDENTITIES:
        blob = str(_git(root, "rev-parse", f"{UPSTREAM_GDN_COMMIT}:{expected.path}"))
        content = _git(
            root,
            "cat-file",
            "blob",
            f"{UPSTREAM_GDN_COMMIT}:{expected.path}",
            binary=True,
        )
        assert isinstance(content, bytes)
        observed.append(
            UpstreamFileIdentityV1(
                path=expected.path,
                git_blob_sha=blob,
                sha256=hashlib.sha256(content).hexdigest(),
            )
        )
    return assert_upstream_source_observation_v1(
        repository=repository,
        commit=commit,
        detached_head=detached_head,
        clean_worktree=clean_worktree,
        file_records=observed,
    )


@dataclass(frozen=True)
class DependencyEnvironmentV1:
    environment_id: str
    python_version: str
    platform_id: str
    torch_version: str | None
    torch_geometric_version: str | None

    def __post_init__(self) -> None:
        if not self.environment_id or any(token in self.environment_id for token in ("/", "\\", ":")):
            raise UpstreamGDNDependencyError("environment_id must be sanitized")
        if not self.python_version or not self.platform_id:
            raise UpstreamGDNDependencyError("Python and platform identities are required")

    @property
    def exact_approved_backend(self) -> bool:
        return (
            self.torch_version == APPROVED_PORT_DEPENDENCIES["torch"]
            and self.torch_geometric_version == APPROVED_PORT_DEPENDENCIES["torch-geometric"]
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "environment_id": self.environment_id,
            "python_version": self.python_version,
            "platform_id": self.platform_id,
            "torch_version": self.torch_version,
            "torch_geometric_version": self.torch_geometric_version,
            "exact_approved_backend": self.exact_approved_backend,
        }


def inspect_current_dependency_environment_v1(
    environment_id: str = "current_python",
) -> DependencyEnvironmentV1:
    """Inspect package metadata without importing either heavy package."""

    torch_spec = util.find_spec("torch")
    pyg_spec = util.find_spec("torch_geometric")
    return DependencyEnvironmentV1(
        environment_id=environment_id,
        python_version=platform.python_version(),
        platform_id=f"{platform.system().lower()}-{platform.machine().lower()}",
        torch_version=metadata.version("torch") if torch_spec is not None else None,
        torch_geometric_version=(
            metadata.version("torch-geometric") if pyg_spec is not None else None
        ),
    )


_ENVIRONMENT_PROBE = (
    "import json,platform; from importlib import metadata,util; "
    "print(json.dumps({'python_version':platform.python_version(),"
    "'platform_id':platform.system().lower()+'-'+platform.machine().lower(),"
    "'torch_version':metadata.version('torch') if util.find_spec('torch') else None,"
    "'torch_geometric_version':metadata.version('torch-geometric') "
    "if util.find_spec('torch_geometric') else None},sort_keys=True))"
)


def inspect_python_executable_v1(
    *, environment_id: str, executable: Path
) -> DependencyEnvironmentV1:
    """Probe an already-approved interpreter; never resolve or install packages."""

    result = subprocess.run(
        [str(executable), "-c", _ENVIRONMENT_PROBE],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise UpstreamGDNDependencyError(
            f"approved environment probe failed for {environment_id}"
        )
    payload = json.loads(result.stdout)
    return DependencyEnvironmentV1(environment_id=environment_id, **payload)


@dataclass(frozen=True)
class UpstreamGDNDependencyStatusV1:
    environments: tuple[DependencyEnvironmentV1, ...]
    required_versions: Mapping[str, str]
    exact_backend_available: bool
    selected_environment_id: str | None
    dependency_status: str

    def __post_init__(self) -> None:
        if not self.environments:
            raise UpstreamGDNDependencyError("at least one approved environment must be inspected")
        if len({item.environment_id for item in self.environments}) != len(self.environments):
            raise UpstreamGDNDependencyError("approved environment IDs must be unique")
        if dict(self.required_versions) != APPROVED_PORT_DEPENDENCIES:
            raise UpstreamGDNDependencyError("approved GDN port dependency versions changed")
        matches = [item for item in self.environments if item.exact_approved_backend]
        if self.exact_backend_available != bool(matches):
            raise UpstreamGDNDependencyError("dependency availability is inconsistent")
        expected_selected = matches[0].environment_id if matches else None
        if self.selected_environment_id != expected_selected:
            raise UpstreamGDNDependencyError("selected dependency environment is inconsistent")
        expected_status = "available" if matches else "blocked_optional_dependency"
        if self.dependency_status != expected_status:
            raise UpstreamGDNDependencyError("dependency status is inconsistent")

    @property
    def environment_fingerprint(self) -> str:
        return stable_hash_v1(
            {
                "artifact_type": "task039c_gdn_dependency_environment_v1",
                "required_versions": dict(self.required_versions),
                "environments": [item.to_dict() for item in self.environments],
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "required_versions": dict(self.required_versions),
            "upstream_native_reference_versions": dict(UPSTREAM_NATIVE_DEPENDENCIES),
            "inspection_policy": "already_approved_environments_only_no_install_or_upgrade",
            "environments": [item.to_dict() for item in self.environments],
            "exact_backend_available": self.exact_backend_available,
            "selected_environment_id": self.selected_environment_id,
            "dependency_status": self.dependency_status,
            "environment_fingerprint": self.environment_fingerprint,
        }


def build_dependency_status_v1(
    environments: Sequence[DependencyEnvironmentV1],
) -> UpstreamGDNDependencyStatusV1:
    ordered = tuple(environments)
    matching = [item for item in ordered if item.exact_approved_backend]
    return UpstreamGDNDependencyStatusV1(
        environments=ordered,
        required_versions=dict(APPROVED_PORT_DEPENDENCIES),
        exact_backend_available=bool(matching),
        selected_environment_id=matching[0].environment_id if matching else None,
        dependency_status="available" if matching else "blocked_optional_dependency",
    )


@dataclass(frozen=True)
class UpstreamGDNTrainingConfigV1:
    seeds: tuple[int, ...] = FROZEN_SEEDS
    batch_size: int = 32
    epochs: int = 30
    slide_window: int = 5
    slide_stride: int = 1
    embedding_dim: int = 64
    out_layer_num: int = 1
    out_layer_inter_dim: int = 128
    learned_graph_topk: int = 5
    validation_ratio: float = 0.2
    learning_rate: float = 0.001
    weight_decay: float = 0.0
    early_stopping_patience: int = 15
    dropout: float = 0.2
    device: str = "cpu"
    preprocessing: str = "raw_numeric_values_no_scaling_windows_do_not_cross_files"
    validation_policy: str = "upstream_seeded_contiguous_random_validation_block"
    checkpoint_policy: str = "minimum_validation_loss_in_memory_state_dict"

    def __post_init__(self) -> None:
        if self.seeds != FROZEN_SEEDS:
            raise UpstreamGDNFidelityError("GDN seeds must be exactly 11, 23, and 37")
        frozen_values = {
            "batch_size": 32,
            "epochs": 30,
            "slide_window": 5,
            "slide_stride": 1,
            "embedding_dim": 64,
            "out_layer_num": 1,
            "out_layer_inter_dim": 128,
            "learned_graph_topk": 5,
            "validation_ratio": 0.2,
            "learning_rate": 0.001,
            "weight_decay": 0.0,
            "early_stopping_patience": 15,
            "dropout": 0.2,
            "device": "cpu",
        }
        for name, value in frozen_values.items():
            if getattr(self, name) != value:
                raise UpstreamGDNFidelityError(f"frozen upstream hyperparameter changed: {name}")
        if self.preprocessing != "raw_numeric_values_no_scaling_windows_do_not_cross_files":
            raise UpstreamGDNFidelityError("preprocessing adaptation changed")
        if self.validation_policy != "upstream_seeded_contiguous_random_validation_block":
            raise UpstreamGDNFidelityError("validation split correspondence changed")
        if self.checkpoint_policy != "minimum_validation_loss_in_memory_state_dict":
            raise UpstreamGDNFidelityError("checkpoint adapter changed")

    @property
    def hyperparameter_hash(self) -> str:
        return stable_hash_v1(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "seeds": list(self.seeds),
            "batch_size": self.batch_size,
            "epochs": self.epochs,
            "slide_window": self.slide_window,
            "slide_stride": self.slide_stride,
            "embedding_dim": self.embedding_dim,
            "out_layer_num": self.out_layer_num,
            "out_layer_inter_dim": self.out_layer_inter_dim,
            "learned_graph_topk": self.learned_graph_topk,
            "validation_ratio": self.validation_ratio,
            "learning_rate": self.learning_rate,
            "weight_decay": self.weight_decay,
            "early_stopping_patience": self.early_stopping_patience,
            "dropout": self.dropout,
            "device": self.device,
            "preprocessing": self.preprocessing,
            "validation_policy": self.validation_policy,
            "checkpoint_policy": self.checkpoint_policy,
        }


def assert_identical_seed_hyperparameters_v1(
    configs_by_seed: Mapping[int, UpstreamGDNTrainingConfigV1],
) -> None:
    if tuple(sorted(configs_by_seed)) != FROZEN_SEEDS:
        raise UpstreamGDNFidelityError("exactly the frozen three seed configurations are required")
    hashes = {config.hyperparameter_hash for config in configs_by_seed.values()}
    if len(hashes) != 1:
        raise UpstreamGDNFidelityError("per-seed hyperparameter variation is prohibited")


@dataclass(frozen=True)
class FidelityFieldAssessmentV1:
    field_name: str
    classification: FidelityClassificationV1
    upstream_sources: tuple[str, ...]
    implementation_evidence: tuple[str, ...]
    rationale: str

    def __post_init__(self) -> None:
        if self.field_name not in FIDELITY_FIELD_NAMES:
            raise UpstreamGDNFidelityError("unknown fidelity field")
        if isinstance(self.classification, str):
            object.__setattr__(self, "classification", FidelityClassificationV1(self.classification))
        if not self.upstream_sources or not self.implementation_evidence or not self.rationale:
            raise UpstreamGDNFidelityError("fidelity assessment evidence is incomplete")

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "classification": self.classification.value,
            "upstream_sources": list(self.upstream_sources),
            "implementation_evidence": list(self.implementation_evidence),
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class UpstreamGDNFidelityReceiptV1:
    status: str
    source_verification: UpstreamSourceVerificationV1
    backend_id: str
    backend_classification: str
    implementation_module: str
    implementation_sha256: str
    training_config: UpstreamGDNTrainingConfigV1
    field_assessments: tuple[FidelityFieldAssessmentV1, ...]
    dependency_status: UpstreamGDNDependencyStatusV1
    real_hai_feature_values_accessed: bool
    created_at: str
    schema_version: str = "1.0.0"
    artifact_type: str = "upstream_gdn_fidelity_receipt_v1"
    task_id: str = "TASK-039C-GDN"

    def __post_init__(self) -> None:
        if self.schema_version != "1.0.0" or self.artifact_type != "upstream_gdn_fidelity_receipt_v1":
            raise UpstreamGDNFidelityError("fidelity receipt identity changed")
        if self.task_id != "TASK-039C-GDN":
            raise UpstreamGDNFidelityError("fidelity receipt task identity changed")
        if self.backend_id != "task039c_upstream_aligned_gdn_v1":
            raise UpstreamGDNFidelityError("smoke or unknown backend cannot claim GDN fidelity")
        if self.implementation_module != "paperworks.gdn.upstream_candidate_backend_v1":
            raise UpstreamGDNFidelityError("implementation module is not the GDN arm backend")
        require_sha256(self.implementation_sha256, "implementation_sha256")
        names = tuple(item.field_name for item in self.field_assessments)
        if names != FIDELITY_FIELD_NAMES:
            raise UpstreamGDNFidelityError("all fidelity fields are required in frozen order")
        unresolved = tuple(
            item.field_name
            for item in self.field_assessments
            if item.classification is FidelityClassificationV1.UNRESOLVED
        )
        expected_status = (
            "blocked_upstream_gdn_backend_unresolved"
            if unresolved
            else "passed_upstream_gdn_fidelity"
        )
        if self.status != expected_status:
            raise UpstreamGDNFidelityError("fidelity status does not match unresolved fields")
        expected_class = (
            "upstream_aligned_unverified" if unresolved else "upstream_aligned_validated"
        )
        if self.backend_classification != expected_class:
            raise UpstreamGDNFidelityError("backend classification exceeds fidelity evidence")
        if self.real_hai_feature_values_accessed:
            raise UpstreamGDNFidelityError("Phase A fidelity receipt must precede HAI access")
        parse_iso_datetime(self.created_at, "created_at")

    @property
    def unresolved_fields(self) -> tuple[str, ...]:
        return tuple(
            item.field_name
            for item in self.field_assessments
            if item.classification is FidelityClassificationV1.UNRESOLVED
        )

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "task_id": self.task_id,
            "status": self.status,
            "protocol_bundle_hash": TASK039C0_PROTOCOL_BUNDLE_HASH,
            "gdn_policy_hash": TASK039C0_GDN_POLICY_HASH,
            "pair_universe_hash": TASK039C0_PAIR_UNIVERSE_HASH,
            "source_verification": self.source_verification.to_dict(),
            "backend_id": self.backend_id,
            "backend_classification": self.backend_classification,
            "implementation_module": self.implementation_module,
            "implementation_sha256": self.implementation_sha256,
            "training_config": {
                **self.training_config.to_dict(),
                "hyperparameter_hash": self.training_config.hyperparameter_hash,
            },
            "field_assessments": [item.to_dict() for item in self.field_assessments],
            "unresolved_fields": list(self.unresolved_fields),
            "smoke_backend_used": False,
            "dependency_status": self.dependency_status.to_dict(),
            "real_hai_feature_values_accessed": self.real_hai_feature_values_accessed,
            "created_at": self.created_at,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "artifact_hash": self.artifact_hash}


def default_fidelity_assessments_v1() -> tuple[FidelityFieldAssessmentV1, ...]:
    """Return the pre-data source-correspondence matrix for the approved port."""

    exact = FidelityClassificationV1.EXACT_UPSTREAM
    dimension = FidelityClassificationV1.DIMENSION_ADAPTATION
    adapter = FidelityClassificationV1.DOCUMENTED_NON_SCIENTIFIC_ADAPTER
    rows = (
        (FIDELITY_FIELD_NAMES[0], exact, ("P1D frozen inventory",), ("verify_pinned_upstream_checkout_v1",), "Repository and commit are exact constants and are verified through Git."),
        (FIDELITY_FIELD_NAMES[1], exact, ("models/GDN.py", "models/graph_layer.py", "datasets/TimeDataset.py", "train.py", "test.py", "evaluate.py", "util/net_struct.py"), ("canonical Git blob verifier",), "All seven P1D Git blob and SHA-256 identities are required."),
        (FIDELITY_FIELD_NAMES[2], dimension, ("models/GDN.py:GDN,GNNLayer,OutLayer",), ("_load_runtime_types_v1",), "Layer topology is preserved; node count and input width derive from the frozen P1 view."),
        (FIDELITY_FIELD_NAMES[3], dimension, ("models/GDN.py:GDN.embedding",), ("nn.Embedding(node_count,64)",), "Embedding construction is exact apart from deterministic P1 node count."),
        (FIDELITY_FIELD_NAMES[4], exact, ("models/GDN.py:GDN.forward",), ("cosine matrix and torch.topk(k=5)",), "The learned graph is the per-target top-5 cosine-neighbor graph used upstream."),
        (FIDELITY_FIELD_NAMES[5], exact, ("models/GDN.py:cos_ji_mat",), ("unnormalized dot divided by outer L2 norms",), "Signed cosine similarity and largest-value Top-K semantics are preserved."),
        (FIDELITY_FIELD_NAMES[6], exact, ("models/GDN.py:gated_edge_index",), ("GraphLayer receives learned gated edges",), "The forecast graph is built from the learned embedding graph on every forward pass."),
        (FIDELITY_FIELD_NAMES[7], exact, ("models/GDN.py:GDN.forward", "train.py:loss_func"), ("next-value output and mean MSE",), "Prediction width and mean squared next-value loss match upstream."),
        (FIDELITY_FIELD_NAMES[8], adapter, ("train.py:train", "main.py:get_loaders"), ("train_upstream_aligned_seed_v1",), "Epoch loop, shuffled training, validation loss, patience 15, and best state are preserved; checkpoints remain in memory."),
        (FIDELITY_FIELD_NAMES[9], adapter, ("util/preprocess.py:construct_data", "datasets/TimeDataset.py:process"), ("load_authorized_numeric_segments_v1", "_segment_windows_v1"), "Raw numeric values and per-file sliding windows are preserved without inventing cross-file windows or scaling."),
        (FIDELITY_FIELD_NAMES[10], exact, ("train.py:Adam",), ("Adam lr=0.001 weight_decay=0",), "Optimizer class and parameters match the executed upstream run script and train loop."),
        (FIDELITY_FIELD_NAMES[11], dimension, ("run.sh", "models/GDN.py",), ("UpstreamGDNTrainingConfigV1",), "Run-script architecture defaults are frozen; only node count follows the P1 view."),
        (FIDELITY_FIELD_NAMES[12], exact, ("run.sh", "train.py",), ("UpstreamGDNTrainingConfigV1",), "Batch, epoch, window, stride, validation, learning-rate, decay, and patience behavior are frozen before data."),
        (FIDELITY_FIELD_NAMES[13], dimension, ("main.py:seed controls",), ("FROZEN_SEEDS", "_set_all_seeds_v1"), "Upstream seed controls are preserved while C0 mandates exactly 11, 23, and 37."),
        (FIDELITY_FIELD_NAMES[14], adapter, ("P1D fidelity freeze",), ("dedicated module; smoke backends rejected",), "Only path, CSV, in-memory checkpoint, and universe-projection adapters are present and explicitly classified."),
        (FIDELITY_FIELD_NAMES[15], exact, ("models/GDN.py:self.learned_graph",), ("train_upstream_aligned_seed_v1 post-checkpoint extraction",), "Extraction recomputes the same embedding cosine matrix and per-target torch.topk indices, then projects without reversing semantic identities."),
    )
    return tuple(
        FidelityFieldAssessmentV1(
            field_name=name,
            classification=classification,
            upstream_sources=tuple(sources),
            implementation_evidence=tuple(evidence),
            rationale=rationale,
        )
        for name, classification, sources, evidence, rationale in rows
    )


def build_fidelity_receipt_v1(
    *,
    source_verification: UpstreamSourceVerificationV1,
    dependency_status: UpstreamGDNDependencyStatusV1,
    implementation_path: Path,
    created_at: str,
    assessments: Sequence[FidelityFieldAssessmentV1] | None = None,
) -> UpstreamGDNFidelityReceiptV1:
    selected = tuple(assessments or default_fidelity_assessments_v1())
    unresolved = any(
        item.classification is FidelityClassificationV1.UNRESOLVED for item in selected
    )
    return UpstreamGDNFidelityReceiptV1(
        status=(
            "blocked_upstream_gdn_backend_unresolved"
            if unresolved
            else "passed_upstream_gdn_fidelity"
        ),
        source_verification=source_verification,
        backend_id="task039c_upstream_aligned_gdn_v1",
        backend_classification=(
            "upstream_aligned_unverified" if unresolved else "upstream_aligned_validated"
        ),
        implementation_module="paperworks.gdn.upstream_candidate_backend_v1",
        implementation_sha256=hashlib.sha256(implementation_path.read_bytes()).hexdigest(),
        training_config=UpstreamGDNTrainingConfigV1(),
        field_assessments=selected,
        dependency_status=dependency_status,
        real_hai_feature_values_accessed=False,
        created_at=created_at,
    )


def authorize_gdn_data_request_v1(
    *,
    process_id: str,
    split_role: str,
    relative_files: Sequence[str],
    requested_feature_names: Sequence[str],
    prohibited_inputs: Sequence[str] = (),
) -> None:
    """Fail before opening any file when a C0 or anti-leakage boundary is crossed."""

    if process_id != "P1" or split_role != NORMAL_CANDIDATE_FIT:
        raise UpstreamGDNDataBoundaryError("GDN data request is outside P1 NORMAL_CANDIDATE_FIT")
    if tuple(relative_files) != ALLOWED_VALUE_FILES:
        raise UpstreamGDNDataBoundaryError("GDN requires exactly train1 and train2; train3/train4/test are prohibited")
    if not requested_feature_names or len(set(requested_feature_names)) != len(requested_feature_names):
        raise UpstreamGDNDataBoundaryError("candidate-learning feature order must be non-empty and unique")
    if any(not name.startswith("P1_") for name in requested_feature_names):
        raise UpstreamGDNDataBoundaryError("only P1 candidate-learning features are permitted")
    forbidden_name_tokens = ("label", "attack", "target_label", "anomaly")
    if any(any(token in name.lower() for token in forbidden_name_tokens) for name in requested_feature_names):
        raise UpstreamGDNDataBoundaryError("labels and attack fields are prohibited")
    forbidden_input_tokens = ("br2", "meta", "stat", "train3", "train4", "test", "attack", "label")
    if any(any(token in item.lower() for token in forbidden_input_tokens) for item in prohibited_inputs):
        raise UpstreamGDNDataBoundaryError("BR2 pair results and cross-arm or prohibited split inputs are rejected")


def load_authorized_numeric_segments_v1(
    *,
    local_root: Path,
    relative_files: Sequence[str],
    feature_order: Sequence[str],
    process_id: str = "P1",
    split_role: str = NORMAL_CANDIDATE_FIT,
) -> tuple[tuple[tuple[float, ...], ...], ...]:
    """Read only approved numeric feature columns after the complete access gate."""

    authorize_gdn_data_request_v1(
        process_id=process_id,
        split_role=split_role,
        relative_files=relative_files,
        requested_feature_names=feature_order,
    )
    segments: list[tuple[tuple[float, ...], ...]] = []
    for relative in relative_files:
        path = (local_root / relative).resolve()
        if not path.is_relative_to(local_root.resolve()):
            raise UpstreamGDNDataBoundaryError("authorized data path escaped local root")
        rows: list[tuple[float, ...]] = []
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None or any(name not in reader.fieldnames for name in feature_order):
                raise UpstreamGDNDataBoundaryError("candidate-learning feature is absent from authorized CSV")
            for row in reader:
                values = tuple(float(row[name]) for name in feature_order)
                if not all(math.isfinite(value) for value in values):
                    raise UpstreamGDNDataBoundaryError("non-finite candidate-learning value")
                rows.append(values)
        if len(rows) <= UpstreamGDNTrainingConfigV1().slide_window:
            raise UpstreamGDNDataBoundaryError("authorized segment is too short for frozen windowing")
        segments.append(tuple(rows))
    return tuple(segments)


def _require_exact_runtime_dependencies_v1() -> None:
    status = build_dependency_status_v1((inspect_current_dependency_environment_v1(),))
    if not status.exact_backend_available:
        raise UpstreamGDNDependencyError(
            "GDN_OPTIONAL_DEPENDENCY_UNAVAILABLE: exact torch==2.12.1 and "
            "torch-geometric==2.8.0 are required"
        )


def _load_runtime_types_v1() -> tuple[Any, Any, Any]:
    """Define the source-aligned model only after exact dependency approval."""

    _require_exact_runtime_dependencies_v1()
    import torch
    import torch.nn.functional as functional
    from torch import nn
    from torch.nn import Parameter
    from torch_geometric.nn.conv import MessagePassing
    from torch_geometric.nn.inits import glorot, zeros
    from torch_geometric.utils import add_self_loops, remove_self_loops, softmax

    class GraphLayer(MessagePassing):
        def __init__(self, in_channels: int, out_channels: int, *, heads: int = 1, concat: bool = True, negative_slope: float = 0.2, dropout: float = 0.0, bias: bool = True) -> None:
            super().__init__(aggr="add")
            self.in_channels = in_channels
            self.out_channels = out_channels
            self.heads = heads
            self.concat = concat
            self.negative_slope = negative_slope
            self.dropout = dropout
            self.lin = nn.Linear(in_channels, heads * out_channels, bias=False)
            self.att_i = Parameter(torch.empty(1, heads, out_channels))
            self.att_j = Parameter(torch.empty(1, heads, out_channels))
            self.att_em_i = Parameter(torch.empty(1, heads, out_channels))
            self.att_em_j = Parameter(torch.empty(1, heads, out_channels))
            if bias and concat:
                self.bias = Parameter(torch.empty(heads * out_channels))
            elif bias:
                self.bias = Parameter(torch.empty(out_channels))
            else:
                self.register_parameter("bias", None)
            self._alpha = None
            self.reset_parameters()

        def reset_parameters(self) -> None:
            glorot(self.lin.weight)
            glorot(self.att_i)
            glorot(self.att_j)
            zeros(self.att_em_i)
            zeros(self.att_em_j)
            zeros(self.bias)

        def forward(self, x: Any, edge_index: Any, embedding: Any) -> Any:
            transformed = self.lin(x)
            pair = (transformed, transformed)
            edge_index, _ = remove_self_loops(edge_index)
            edge_index, _ = add_self_loops(edge_index, num_nodes=pair[1].size(self.node_dim))
            out = self.propagate(edge_index, x=pair, embedding=embedding, edges=edge_index)
            out = out.view(-1, self.heads * self.out_channels) if self.concat else out.mean(dim=1)
            return out + self.bias if self.bias is not None else out

        def message(self, x_i: Any, x_j: Any, edge_index_i: Any, size_i: Any, embedding: Any, edges: Any) -> Any:
            x_i = x_i.view(-1, self.heads, self.out_channels)
            x_j = x_j.view(-1, self.heads, self.out_channels)
            embedding_i = embedding[edge_index_i].unsqueeze(1).repeat(1, self.heads, 1)
            embedding_j = embedding[edges[0]].unsqueeze(1).repeat(1, self.heads, 1)
            key_i = torch.cat((x_i, embedding_i), dim=-1)
            key_j = torch.cat((x_j, embedding_j), dim=-1)
            alpha = (key_i * torch.cat((self.att_i, self.att_em_i), dim=-1)).sum(-1)
            alpha += (key_j * torch.cat((self.att_j, self.att_em_j), dim=-1)).sum(-1)
            alpha = functional.leaky_relu(alpha.view(-1, self.heads, 1), self.negative_slope)
            alpha = softmax(alpha, edge_index_i, size_i)
            self._alpha = alpha
            alpha = functional.dropout(alpha, p=self.dropout, training=self.training)
            return x_j * alpha.view(-1, self.heads, 1)

    class GNNLayer(nn.Module):
        def __init__(self, input_dim: int, output_dim: int) -> None:
            super().__init__()
            self.gnn = GraphLayer(input_dim, output_dim, heads=1, concat=False)
            self.bn = nn.BatchNorm1d(output_dim)
            self.relu = nn.ReLU()

        def forward(self, x: Any, edge_index: Any, embedding: Any) -> Any:
            return self.relu(self.bn(self.gnn(x, edge_index, embedding)))

    class OutLayer(nn.Module):
        def __init__(self, input_dim: int, layer_num: int, intermediate_dim: int) -> None:
            super().__init__()
            modules: list[Any] = []
            for index in range(layer_num):
                if index == layer_num - 1:
                    modules.append(nn.Linear(input_dim if layer_num == 1 else intermediate_dim, 1))
                else:
                    modules.extend((nn.Linear(input_dim if index == 0 else intermediate_dim, intermediate_dim), nn.BatchNorm1d(intermediate_dim), nn.ReLU()))
            self.mlp = nn.ModuleList(modules)

        def forward(self, x: Any) -> Any:
            out = x
            for module in self.mlp:
                if isinstance(module, nn.BatchNorm1d):
                    out = module(out.permute(0, 2, 1)).permute(0, 2, 1)
                else:
                    out = module(out)
            return out

    class UpstreamAlignedGDN(nn.Module):
        def __init__(self, node_count: int, config: UpstreamGDNTrainingConfigV1) -> None:
            super().__init__()
            self.node_count = node_count
            self.topk = config.learned_graph_topk
            self.embedding = nn.Embedding(node_count, config.embedding_dim)
            self.gnn_layer = GNNLayer(config.slide_window, config.embedding_dim)
            self.bn_outlayer_in = nn.BatchNorm1d(config.embedding_dim)
            self.dropout = nn.Dropout(config.dropout)
            self.out_layer = OutLayer(config.embedding_dim, config.out_layer_num, config.out_layer_inter_dim)
            self.learned_graph = None
            nn.init.kaiming_uniform_(self.embedding.weight, a=math.sqrt(5))

        @staticmethod
        def _batch_edges(edges: Any, batch_size: int, node_count: int) -> Any:
            edge_count = edges.shape[1]
            batched = edges.repeat(1, batch_size).contiguous()
            for index in range(batch_size):
                batched[:, index * edge_count : (index + 1) * edge_count] += index * node_count
            return batched.long()

        def forward(self, data: Any, _original_edges: Any) -> Any:
            batch_size, node_count, input_width = data.shape
            x = data.clone().detach().view(-1, input_width).contiguous()
            all_embeddings = self.embedding(torch.arange(node_count, device=data.device))
            weights = all_embeddings.detach().clone().view(node_count, -1)
            cosine = torch.matmul(weights, weights.T)
            norms = torch.matmul(weights.norm(dim=-1).view(-1, 1), weights.norm(dim=-1).view(1, -1))
            cosine = cosine / norms
            topk_indices = torch.topk(cosine, self.topk, dim=-1)[1]
            self.learned_graph = topk_indices
            targets = torch.arange(node_count, device=data.device).unsqueeze(1).repeat(1, self.topk).flatten().unsqueeze(0)
            sources = topk_indices.flatten().unsqueeze(0)
            learned_edges = torch.cat((sources, targets), dim=0)
            batch_edges = self._batch_edges(learned_edges, batch_size, node_count)
            embeddings = all_embeddings.repeat(batch_size, 1)
            out = self.gnn_layer(x, batch_edges, embeddings).view(batch_size, node_count, -1)
            out = torch.mul(out, self.embedding(torch.arange(node_count, device=data.device)))
            out = functional.relu(self.bn_outlayer_in(out.permute(0, 2, 1))).permute(0, 2, 1)
            return self.out_layer(self.dropout(out)).view(-1, node_count)

    return torch, nn, UpstreamAlignedGDN


def _segment_windows_v1(segments: Sequence[Sequence[Sequence[float]]], config: UpstreamGDNTrainingConfigV1) -> tuple[list[list[list[float]]], list[list[float]]]:
    windows: list[list[list[float]]] = []
    targets: list[list[float]] = []
    for segment in segments:
        for stop in range(config.slide_window, len(segment), config.slide_stride):
            history = segment[stop - config.slide_window : stop]
            node_major = [
                [float(history[t][node]) for t in range(config.slide_window)]
                for node in range(len(segment[0]))
            ]
            windows.append(node_major)
            targets.append([float(value) for value in segment[stop]])
    if not windows:
        raise UpstreamGDNDataBoundaryError("no frozen GDN windows were produced")
    return windows, targets


def _set_all_seeds_v1(torch: Any, seed: int) -> None:
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    if hasattr(torch.backends, "cudnn"):
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True


@dataclass(frozen=True)
class TrainedSeedGraphV1:
    seed: int
    selected_edges: tuple[tuple[str, str], ...]
    candidate_similarities: Mapping[tuple[str, str], float]
    epoch_count: int
    best_validation_loss: float
    hyperparameter_hash: str


def train_upstream_aligned_seed_v1(
    *,
    segments: Sequence[Sequence[Sequence[float]]],
    feature_order: Sequence[str],
    candidate_pairs: Sequence[tuple[str, str]],
    seed: int,
    config: UpstreamGDNTrainingConfigV1,
) -> TrainedSeedGraphV1:
    """Run one frozen upstream-aligned seed without persisting a checkpoint."""

    if seed not in FROZEN_SEEDS:
        raise UpstreamGDNFidelityError("seed is outside the frozen set")
    if config.seeds != FROZEN_SEEDS:
        raise UpstreamGDNFidelityError("training configuration seed set changed")
    feature_tuple = tuple(feature_order)
    if len(feature_tuple) <= config.learned_graph_topk:
        raise UpstreamGDNFidelityError("P1 context must exceed upstream Top-K")
    pair_set = set(candidate_pairs)
    if any(source not in feature_tuple or target not in feature_tuple for source, target in pair_set):
        raise UpstreamGDNDataBoundaryError("candidate projection is outside model context")
    torch, nn, model_type = _load_runtime_types_v1()
    _set_all_seeds_v1(torch, seed)
    windows, targets = _segment_windows_v1(segments, config)
    x = torch.tensor(windows, dtype=torch.float32)
    y = torch.tensor(targets, dtype=torch.float32)
    dataset = torch.utils.data.TensorDataset(x, y)
    dataset_length = len(dataset)
    train_length = int(dataset_length * (1.0 - config.validation_ratio))
    validation_length = int(dataset_length * config.validation_ratio)
    if train_length <= 0 or validation_length <= 0:
        raise UpstreamGDNDataBoundaryError("frozen validation split is empty")
    validation_start = random.randrange(train_length)
    indices = torch.arange(dataset_length)
    train_indices = torch.cat((indices[:validation_start], indices[validation_start + validation_length :]))
    validation_indices = indices[validation_start : validation_start + validation_length]
    train_loader = torch.utils.data.DataLoader(torch.utils.data.Subset(dataset, train_indices), batch_size=config.batch_size, shuffle=True)
    validation_loader = torch.utils.data.DataLoader(torch.utils.data.Subset(dataset, validation_indices), batch_size=config.batch_size, shuffle=False)
    model = model_type(len(feature_tuple), config).to(config.device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    loss_function = nn.MSELoss(reduction="mean")
    original_edges = torch.tensor(
        [[source for target in range(len(feature_tuple)) for source in range(len(feature_tuple)) if source != target], [target for target in range(len(feature_tuple)) for source in range(len(feature_tuple)) if source != target]],
        dtype=torch.long,
    )
    best_state = None
    best_loss = float("inf")
    stale_epochs = 0
    completed_epochs = 0
    for epoch in range(config.epochs):
        model.train()
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            prediction = model(batch_x.to(config.device), original_edges.to(config.device))
            loss = loss_function(prediction, batch_y.to(config.device))
            loss.backward()
            optimizer.step()
        model.eval()
        losses: list[float] = []
        with torch.no_grad():
            for batch_x, batch_y in validation_loader:
                prediction = model(batch_x.to(config.device), original_edges.to(config.device))
                losses.append(float(loss_function(prediction, batch_y.to(config.device)).item()))
        validation_loss = sum(losses) / len(losses)
        completed_epochs = epoch + 1
        if validation_loss < best_loss:
            best_loss = validation_loss
            best_state = copy.deepcopy(model.state_dict())
            stale_epochs = 0
        else:
            stale_epochs += 1
        if stale_epochs >= config.early_stopping_patience:
            break
    if best_state is None or not math.isfinite(best_loss):
        raise UpstreamGDNError("failed_gdn_training: no finite best validation state")
    model.load_state_dict(best_state)
    weights = model.embedding.weight.detach()
    cosine = torch.matmul(weights, weights.T)
    norms = torch.matmul(weights.norm(dim=-1).view(-1, 1), weights.norm(dim=-1).view(1, -1))
    cosine = cosine / norms
    topk_indices = torch.topk(cosine, config.learned_graph_topk, dim=-1)[1]
    name_to_index = {name: index for index, name in enumerate(feature_tuple)}
    selected = set()
    for target_index in range(len(feature_tuple)):
        target = feature_tuple[target_index]
        for source_index in topk_indices[target_index].tolist():
            pair = (feature_tuple[int(source_index)], target)
            if pair in pair_set:
                selected.add(pair)
    similarities = {
        pair: float(cosine[name_to_index[pair[1]], name_to_index[pair[0]]].item())
        for pair in pair_set
    }
    return TrainedSeedGraphV1(
        seed=seed,
        selected_edges=tuple(sorted(selected)),
        candidate_similarities=similarities,
        epoch_count=completed_epochs,
        best_validation_loss=best_loss,
        hyperparameter_hash=config.hyperparameter_hash,
    )


__all__ = [
    "ALLOWED_VALUE_FILES",
    "APPROVED_PORT_DEPENDENCIES",
    "DependencyEnvironmentV1",
    "FIDELITY_FIELD_NAMES",
    "FROZEN_SEEDS",
    "FROZEN_UPSTREAM_FILE_IDENTITIES",
    "FidelityClassificationV1",
    "FidelityFieldAssessmentV1",
    "NORMAL_CANDIDATE_FIT",
    "TASK039C0_GDN_POLICY_HASH",
    "TASK039C0_PAIR_UNIVERSE_HASH",
    "TASK039C0_PROTOCOL_BUNDLE_HASH",
    "TASK039C_GDN_STARTING_COMMIT",
    "TrainedSeedGraphV1",
    "UPSTREAM_GDN_COMMIT",
    "UPSTREAM_GDN_REPOSITORY",
    "UpstreamFileIdentityV1",
    "UpstreamGDNDataBoundaryError",
    "UpstreamGDNDependencyError",
    "UpstreamGDNDependencyStatusV1",
    "UpstreamGDNError",
    "UpstreamGDNFidelityError",
    "UpstreamGDNFidelityReceiptV1",
    "UpstreamGDNTrainingConfigV1",
    "UpstreamSourceVerificationV1",
    "assert_identical_seed_hyperparameters_v1",
    "assert_upstream_source_observation_v1",
    "authorize_gdn_data_request_v1",
    "build_dependency_status_v1",
    "build_fidelity_receipt_v1",
    "default_fidelity_assessments_v1",
    "inspect_current_dependency_environment_v1",
    "inspect_python_executable_v1",
    "load_authorized_numeric_segments_v1",
    "train_upstream_aligned_seed_v1",
    "verify_pinned_upstream_checkout_v1",
]
