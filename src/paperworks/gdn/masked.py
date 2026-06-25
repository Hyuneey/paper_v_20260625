"""Masked GDN-style candidate edge extraction.

This module implements the project-specific extraction contract around the
GDN embedding-similarity idea: compute node-embedding cosine similarity, apply
the CandidateUniverse mask, then export at most K directed candidate edges per
target. It intentionally keeps message-passing self-loops separate from
persisted candidate relations.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

from paperworks.candidates import CandidatePair, CandidateUniverseArtifact, candidate_mask
from paperworks.data import DataViewManifest, SplitManifest, assert_split_permitted
from paperworks.data.contracts import SCHEMA_VERSION, stable_hash


class GDNExtractionError(ValueError):
    """Raised when masked GDN candidate extraction inputs are invalid."""


@dataclass(frozen=True)
class GDNExtractionConfig:
    top_k: int
    seed: int
    run_index: int = 0
    embedding_dim: int | None = None
    backend: str = "deterministic_embedding_smoke"
    config_version: str = "1.0"

    def __post_init__(self) -> None:
        if self.top_k < 0:
            raise GDNExtractionError("top_k must be non-negative")
        if self.run_index < 0:
            raise GDNExtractionError("run_index must be non-negative")
        if self.embedding_dim is not None and self.embedding_dim <= 0:
            raise GDNExtractionError("embedding_dim must be positive when provided")
        if not self.backend:
            raise GDNExtractionError("backend is required")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EmbeddingCheckpoint:
    feature_order: tuple[str, ...]
    feature_order_hash: str
    embeddings: Mapping[str, tuple[float, ...]]
    seed: int
    split_name: str
    source_view: str
    sampling_period_seconds: float
    training_config: Mapping[str, Any]
    dataset_manifest_id: str
    data_view_id: str
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "gdn_embedding_checkpoint"

    def __post_init__(self) -> None:
        if self.artifact_type != "gdn_embedding_checkpoint":
            raise GDNExtractionError("artifact_type must be gdn_embedding_checkpoint")
        if len(self.feature_order_hash) != 64:
            raise GDNExtractionError("feature_order_hash must be a 64-character hash")
        if len(self.dataset_manifest_id) != 64 or len(self.data_view_id) != 64:
            raise GDNExtractionError("dataset_manifest_id and data_view_id must be 64-character hashes")
        _validate_embeddings(self.embeddings, self.feature_order)
        expected_hash = stable_hash({"feature_order": list(self.feature_order)})
        if self.feature_order_hash != expected_hash:
            raise GDNExtractionError("feature_order_hash does not match feature_order")

    @property
    def checkpoint_id(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "feature_order": list(self.feature_order),
            "feature_order_hash": self.feature_order_hash,
            "embeddings": {key: list(value) for key, value in sorted(self.embeddings.items())},
            "seed": self.seed,
            "split_name": self.split_name,
            "source_view": self.source_view,
            "sampling_period_seconds": self.sampling_period_seconds,
            "training_config": dict(self.training_config),
            "dataset_manifest_id": self.dataset_manifest_id,
            "data_view_id": self.data_view_id,
        }


@dataclass(frozen=True)
class GDNEdgeRecord:
    source: str
    target: str
    embedding_similarity: float
    rank: int
    K: int
    seed: int
    candidate_origins: tuple[str, ...]
    candidate_universe_id: str
    feature_order_hash: str
    source_view: str
    sampling_period_seconds: float
    checkpoint_id: str

    def __post_init__(self) -> None:
        if not self.source or not self.target:
            raise GDNExtractionError("source and target are required")
        if self.source == self.target:
            raise GDNExtractionError("candidate self-edges are prohibited")
        if self.rank <= 0:
            raise GDNExtractionError("rank must be one-based")
        if self.K < 0:
            raise GDNExtractionError("K must be non-negative")
        if not self.candidate_origins:
            raise GDNExtractionError("candidate_origins are required")
        if len(self.candidate_universe_id) != 64:
            raise GDNExtractionError("candidate_universe_id must be a 64-character hash")
        if len(self.feature_order_hash) != 64:
            raise GDNExtractionError("feature_order_hash must be a 64-character hash")
        if len(self.checkpoint_id) != 64:
            raise GDNExtractionError("checkpoint_id must be a 64-character hash")
        if self.sampling_period_seconds <= 0:
            raise GDNExtractionError("sampling_period_seconds must be positive")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["candidate_origins"] = list(self.candidate_origins)
        return data


@dataclass(frozen=True)
class GDNEdgeArtifact:
    dataset_manifest_id: str
    split_name: str
    source_view: str
    sampling_period_seconds: float
    candidate_universe_id: str
    checkpoint_id: str
    feature_order: tuple[str, ...]
    feature_order_hash: str
    top_k: int
    seed: int
    run_index: int
    edges: tuple[GDNEdgeRecord, ...]
    message_passing_self_loop_count: int
    extraction_config: Mapping[str, Any]
    code_commit: str | None = None
    created_at: str = "unspecified"
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "gdn_candidate_edges"

    def __post_init__(self) -> None:
        if self.artifact_type != "gdn_candidate_edges":
            raise GDNExtractionError("artifact_type must be gdn_candidate_edges")
        if len(self.dataset_manifest_id) != 64:
            raise GDNExtractionError("dataset_manifest_id must be a 64-character hash")
        if len(self.candidate_universe_id) != 64 or len(self.checkpoint_id) != 64:
            raise GDNExtractionError("candidate_universe_id and checkpoint_id must be 64-character hashes")
        if len(self.feature_order_hash) != 64:
            raise GDNExtractionError("feature_order_hash must be a 64-character hash")
        if self.sampling_period_seconds <= 0:
            raise GDNExtractionError("sampling_period_seconds must be positive")
        if self.top_k < 0:
            raise GDNExtractionError("top_k must be non-negative")
        if self.message_passing_self_loop_count != len(self.feature_order):
            raise GDNExtractionError("message_passing_self_loop_count must match feature count")
        for edge in self.edges:
            if edge.feature_order_hash != self.feature_order_hash:
                raise GDNExtractionError("edge feature_order_hash mismatch")
            if edge.candidate_universe_id != self.candidate_universe_id:
                raise GDNExtractionError("edge candidate_universe_id mismatch")
            if edge.checkpoint_id != self.checkpoint_id:
                raise GDNExtractionError("edge checkpoint_id mismatch")

    @property
    def artifact_id(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "dataset_manifest_id": self.dataset_manifest_id,
            "split_name": self.split_name,
            "source_view": self.source_view,
            "sampling_period_seconds": self.sampling_period_seconds,
            "candidate_universe_id": self.candidate_universe_id,
            "checkpoint_id": self.checkpoint_id,
            "feature_order": list(self.feature_order),
            "feature_order_hash": self.feature_order_hash,
            "top_k": self.top_k,
            "seed": self.seed,
            "run_index": self.run_index,
            "edges": [edge.to_dict() for edge in self.edges],
            "message_passing_self_loop_count": self.message_passing_self_loop_count,
            "extraction_config": dict(self.extraction_config),
            "code_commit": self.code_commit,
            "created_at": self.created_at,
        }


def fit_deterministic_embedding_checkpoint(
    *,
    normal_windows: Sequence[Mapping[str, float]],
    feature_order: Sequence[str],
    split: SplitManifest,
    data_view: DataViewManifest,
    config: GDNExtractionConfig,
) -> EmbeddingCheckpoint:
    """Build a deterministic synthetic checkpoint for smoke tests.

    This is not the final PyTorch/PyG GDN trainer. It exists to validate
    provenance, split guards, checkpoint IDs, and masked edge extraction without
    requiring unavailable heavy ML dependencies in local unit tests.
    """

    assert_split_permitted(split.role, "train_candidate_learner")
    ordered_features = tuple(feature_order)
    if not normal_windows:
        raise GDNExtractionError("normal_windows must be non-empty")
    for window in normal_windows:
        missing = [name for name in ordered_features if name not in window]
        if missing:
            raise GDNExtractionError(f"normal window missing features: {missing}")

    embeddings: dict[str, tuple[float, ...]] = {}
    length = float(len(normal_windows))
    for index, name in enumerate(ordered_features):
        values = [float(window[name]) for window in normal_windows]
        mean = sum(values) / length
        variance = sum((value - mean) ** 2 for value in values) / length
        trend = values[-1] - values[0]
        embeddings[name] = (mean, math.sqrt(variance), trend, float(index + config.seed % 997) / 997.0)

    feature_order_hash = stable_hash({"feature_order": list(ordered_features)})
    return EmbeddingCheckpoint(
        feature_order=ordered_features,
        feature_order_hash=feature_order_hash,
        embeddings=embeddings,
        seed=config.seed,
        split_name=split.role.value,
        source_view=data_view.source_view or data_view.name.value,
        sampling_period_seconds=data_view.sampling_period_seconds,
        training_config=config.to_dict(),
        dataset_manifest_id=split.dataset_manifest_id,
        data_view_id=split.data_view_id,
    )


def extract_masked_topk_edges(
    *,
    candidate_universe: CandidateUniverseArtifact,
    checkpoint: EmbeddingCheckpoint,
    config: GDNExtractionConfig,
    split: SplitManifest,
    data_view: DataViewManifest,
    code_commit: str | None = None,
    created_at: str = "unspecified",
) -> GDNEdgeArtifact:
    """Export Top-K embedding-similarity edges strictly inside C_i."""

    assert_split_permitted(split.role, "train_candidate_learner")
    if tuple(candidate_universe.feature_order) != tuple(checkpoint.feature_order):
        raise GDNExtractionError("checkpoint feature_order must match candidate universe")
    if candidate_universe.feature_order_hash != checkpoint.feature_order_hash:
        raise GDNExtractionError("feature_order_hash mismatch")
    if candidate_universe.dataset_manifest_id != split.dataset_manifest_id:
        raise GDNExtractionError("candidate universe and split dataset_manifest_id mismatch")
    if checkpoint.dataset_manifest_id != split.dataset_manifest_id:
        raise GDNExtractionError("checkpoint and split dataset_manifest_id mismatch")
    if candidate_universe.source_view != (data_view.source_view or data_view.name.value):
        raise GDNExtractionError("candidate universe source_view mismatch")
    if candidate_universe.sampling_period_seconds != data_view.sampling_period_seconds:
        raise GDNExtractionError("candidate universe sampling_period_seconds mismatch")

    similarities = cosine_similarity_matrix(checkpoint.embeddings, checkpoint.feature_order)
    mask = candidate_mask(candidate_universe)
    pair_by_key = {(pair.source, pair.target): pair for pair in candidate_universe.pairs}
    candidate_universe_id = candidate_universe.artifact_id
    checkpoint_id = checkpoint.checkpoint_id
    feature_index = {name: index for index, name in enumerate(checkpoint.feature_order)}

    edges: list[GDNEdgeRecord] = []
    for target_index, target in enumerate(checkpoint.feature_order):
        scored_sources: list[tuple[str, float, CandidatePair]] = []
        for source_index, source in enumerate(checkpoint.feature_order):
            if source == target:
                continue
            if not mask[target_index][source_index]:
                continue
            pair = pair_by_key.get((source, target))
            if pair is None:
                raise GDNExtractionError("candidate mask contains entry without candidate pair provenance")
            scored_sources.append((source, similarities[target_index][source_index], pair))
        ranked = sorted(scored_sources, key=lambda item: (-item[1], feature_index[item[0]]))
        for rank, (source, score, pair) in enumerate(ranked[: config.top_k], start=1):
            edges.append(
                GDNEdgeRecord(
                    source=source,
                    target=target,
                    embedding_similarity=score,
                    rank=rank,
                    K=config.top_k,
                    seed=config.seed,
                    candidate_origins=pair.origins,
                    candidate_universe_id=candidate_universe_id,
                    feature_order_hash=candidate_universe.feature_order_hash,
                    source_view=candidate_universe.source_view,
                    sampling_period_seconds=candidate_universe.sampling_period_seconds,
                    checkpoint_id=checkpoint_id,
                )
            )

    return GDNEdgeArtifact(
        dataset_manifest_id=split.dataset_manifest_id,
        split_name=split.role.value,
        source_view=data_view.source_view or data_view.name.value,
        sampling_period_seconds=data_view.sampling_period_seconds,
        candidate_universe_id=candidate_universe_id,
        checkpoint_id=checkpoint_id,
        feature_order=checkpoint.feature_order,
        feature_order_hash=checkpoint.feature_order_hash,
        top_k=config.top_k,
        seed=config.seed,
        run_index=config.run_index,
        edges=tuple(edges),
        message_passing_self_loop_count=len(message_passing_self_loops(checkpoint.feature_order)),
        extraction_config=config.to_dict(),
        code_commit=code_commit,
        created_at=created_at,
    )


def cosine_similarity_matrix(
    embeddings: Mapping[str, Sequence[float]],
    feature_order: Sequence[str],
) -> tuple[tuple[float, ...], ...]:
    ordered_features = tuple(feature_order)
    _validate_embeddings(embeddings, ordered_features)
    rows: list[tuple[float, ...]] = []
    for target in ordered_features:
        row: list[float] = []
        for source in ordered_features:
            row.append(_cosine(embeddings[target], embeddings[source]))
        rows.append(tuple(row))
    return tuple(rows)


def message_passing_self_loops(feature_order: Sequence[str]) -> tuple[tuple[str, str], ...]:
    """Return internal self-loops for message passing, not candidate export."""

    return tuple((name, name) for name in feature_order)


def _validate_embeddings(embeddings: Mapping[str, Sequence[float]], feature_order: tuple[str, ...]) -> None:
    if not feature_order:
        raise GDNExtractionError("feature_order is required")
    if len(set(feature_order)) != len(feature_order):
        raise GDNExtractionError("feature_order must not contain duplicates")
    missing = [name for name in feature_order if name not in embeddings]
    extra = [name for name in embeddings if name not in set(feature_order)]
    if missing or extra:
        raise GDNExtractionError(f"embedding feature mismatch: missing={missing}, extra={extra}")
    dims = {len(embeddings[name]) for name in feature_order}
    if len(dims) != 1 or next(iter(dims)) == 0:
        raise GDNExtractionError("all embeddings must have the same non-zero dimension")


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    numerator = sum(float(l_value) * float(r_value) for l_value, r_value in zip(left, right))
    left_norm = math.sqrt(sum(float(value) ** 2 for value in left))
    right_norm = math.sqrt(sum(float(value) ** 2 for value in right))
    denominator = left_norm * right_norm
    if denominator == 0:
        return -math.inf
    return numerator / denominator
