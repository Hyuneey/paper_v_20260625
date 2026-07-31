"""Lightweight GDN extraction contracts with a lazy Torch/PyG boundary."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from paperworks.gdn.masked import (
    EmbeddingCheckpoint,
    GDNEdgeArtifact,
    GDNEdgeRecord,
    GDNExtractionConfig,
    GDNExtractionError,
    cosine_similarity_matrix,
    extract_masked_topk_edges,
    fit_deterministic_embedding_checkpoint,
    message_passing_self_loops,
)
from paperworks.gdn.dependencies import (
    GDNDependencyStatusV1,
    GDNOptionalDependencyError,
    GDN_OPTIONAL_DEPENDENCY_ISSUE_CODE,
    inspect_gdn_dependencies,
)
from paperworks.gdn.fidelity_v1 import (
    GDNBackendFidelityRecordV1,
    GDNFidelityClassV1,
    GDNFidelityError,
    GDNFidelityFreezeV1,
    UpstreamFileRecordV1,
)


_OPTIONAL_EXPORTS = frozenset(
    {
        "TorchGDNEmbeddingModel",
        "TorchGDNTrainingConfig",
        "fit_torch_gdn_embedding_checkpoint",
    }
)


def __getattr__(name: str) -> Any:
    if name not in _OPTIONAL_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module("paperworks.gdn.torch_backend")
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | _OPTIONAL_EXPORTS)

__all__ = [
    "EmbeddingCheckpoint",
    "GDNEdgeArtifact",
    "GDNEdgeRecord",
    "GDNExtractionConfig",
    "GDNExtractionError",
    "GDNBackendFidelityRecordV1",
    "GDNDependencyStatusV1",
    "GDNFidelityClassV1",
    "GDNFidelityError",
    "GDNFidelityFreezeV1",
    "GDNOptionalDependencyError",
    "GDN_OPTIONAL_DEPENDENCY_ISSUE_CODE",
    "UpstreamFileRecordV1",
    "cosine_similarity_matrix",
    "extract_masked_topk_edges",
    "fit_deterministic_embedding_checkpoint",
    "inspect_gdn_dependencies",
    "message_passing_self_loops",
    "TorchGDNEmbeddingModel",
    "TorchGDNTrainingConfig",
    "fit_torch_gdn_embedding_checkpoint",
]
