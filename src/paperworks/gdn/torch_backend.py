"""CPU PyTorch/PyG smoke trainer for GDN-style node embeddings."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

import torch
from torch import nn
from torch_geometric.nn.conv import MessagePassing

from paperworks.candidates import CandidateUniverseArtifact
from paperworks.data import DataViewManifest, SplitManifest, assert_split_permitted
from paperworks.gdn.masked import EmbeddingCheckpoint, GDNExtractionError, message_passing_self_loops


@dataclass(frozen=True)
class TorchGDNTrainingConfig:
    seed: int
    embedding_dim: int = 8
    hidden_dim: int = 16
    epochs: int = 30
    learning_rate: float = 0.01
    weight_decay: float = 0.0
    backend: str = "torch_pyg_cpu"
    config_version: str = "1.0"

    def __post_init__(self) -> None:
        if self.embedding_dim <= 0:
            raise GDNExtractionError("embedding_dim must be positive")
        if self.hidden_dim <= 0:
            raise GDNExtractionError("hidden_dim must be positive")
        if self.epochs <= 0:
            raise GDNExtractionError("epochs must be positive")
        if self.learning_rate <= 0:
            raise GDNExtractionError("learning_rate must be positive")
        if self.weight_decay < 0:
            raise GDNExtractionError("weight_decay must be non-negative")
        if self.backend != "torch_pyg_cpu":
            raise GDNExtractionError("TorchGDNTrainingConfig backend must be torch_pyg_cpu")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MeanGraphLayer(MessagePassing):
    """Small PyG message-passing layer used for synthetic GDN smoke tests."""

    def __init__(self) -> None:
        super().__init__(aggr="mean")

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        return self.propagate(edge_index, x=x)

    def message(self, x_j: torch.Tensor) -> torch.Tensor:
        return x_j


class TorchGDNEmbeddingModel(nn.Module):
    """Minimal graph forecaster that learns node embeddings."""

    def __init__(self, *, node_count: int, embedding_dim: int, hidden_dim: int) -> None:
        super().__init__()
        self.embedding = nn.Embedding(node_count, embedding_dim)
        self.graph = MeanGraphLayer()
        self.decoder = nn.Sequential(
            nn.Linear(2 + embedding_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, values: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        batch_size, node_count = values.shape
        node_values = values.reshape(batch_size * node_count, 1)
        neighbor_values = self.graph(node_values, edge_index)
        node_ids = torch.arange(node_count, device=values.device).repeat(batch_size)
        embeddings = self.embedding(node_ids)
        decoded = self.decoder(torch.cat((node_values, neighbor_values, embeddings), dim=1))
        return decoded.reshape(batch_size, node_count)


def fit_torch_gdn_embedding_checkpoint(
    *,
    normal_windows: Sequence[Mapping[str, float]],
    candidate_universe: CandidateUniverseArtifact,
    split: SplitManifest,
    data_view: DataViewManifest,
    config: TorchGDNTrainingConfig,
) -> EmbeddingCheckpoint:
    """Train a small CPU PyTorch/PyG model and return learned node embeddings."""

    assert_split_permitted(split.role, "train_candidate_learner")
    if candidate_universe.dataset_manifest_id != split.dataset_manifest_id:
        raise GDNExtractionError("candidate universe and split dataset_manifest_id mismatch")
    if candidate_universe.source_view != (data_view.source_view or data_view.name.value):
        raise GDNExtractionError("candidate universe source_view mismatch")
    if candidate_universe.sampling_period_seconds != data_view.sampling_period_seconds:
        raise GDNExtractionError("candidate universe sampling_period_seconds mismatch")

    feature_order = tuple(candidate_universe.feature_order)
    values = _normal_windows_to_tensor(normal_windows, feature_order)
    if values.shape[0] < 2:
        raise GDNExtractionError("normal_windows must contain at least two time steps")

    torch.manual_seed(config.seed)
    model = TorchGDNEmbeddingModel(
        node_count=len(feature_order),
        embedding_dim=config.embedding_dim,
        hidden_dim=config.hidden_dim,
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    loss_fn = nn.MSELoss()
    edge_index = _batched_edge_index(
        base_edges=_message_passing_edges(candidate_universe),
        feature_order=feature_order,
        batch_size=values.shape[0] - 1,
    )

    inputs = values[:-1]
    targets = values[1:]
    losses: list[float] = []
    model.train()
    for _ in range(config.epochs):
        optimizer.zero_grad()
        prediction = model(inputs, edge_index)
        loss = loss_fn(prediction, targets)
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach().item()))

    learned = model.embedding.weight.detach().cpu()
    embeddings = {
        name: tuple(float(value) for value in learned[index].tolist())
        for index, name in enumerate(feature_order)
    }

    training_config = config.to_dict()
    training_config["loss_first"] = losses[0]
    training_config["loss_last"] = losses[-1]
    training_config["message_passing_edge_count"] = len(_message_passing_edges(candidate_universe))
    training_config["candidate_edge_count"] = len(candidate_universe.pairs)

    return EmbeddingCheckpoint(
        feature_order=feature_order,
        feature_order_hash=candidate_universe.feature_order_hash,
        embeddings=embeddings,
        seed=config.seed,
        split_name=split.role.value,
        source_view=data_view.source_view or data_view.name.value,
        sampling_period_seconds=data_view.sampling_period_seconds,
        training_config=training_config,
        dataset_manifest_id=split.dataset_manifest_id,
        data_view_id=split.data_view_id,
    )


def _normal_windows_to_tensor(normal_windows: Sequence[Mapping[str, float]], feature_order: tuple[str, ...]) -> torch.Tensor:
    if not normal_windows:
        raise GDNExtractionError("normal_windows must be non-empty")
    rows: list[list[float]] = []
    for window in normal_windows:
        missing = [name for name in feature_order if name not in window]
        if missing:
            raise GDNExtractionError(f"normal window missing features: {missing}")
        rows.append([float(window[name]) for name in feature_order])
    return torch.tensor(rows, dtype=torch.float32)


def _message_passing_edges(candidate_universe: CandidateUniverseArtifact) -> tuple[tuple[str, str], ...]:
    candidate_edges = tuple((pair.source, pair.target) for pair in candidate_universe.pairs)
    return candidate_edges + message_passing_self_loops(candidate_universe.feature_order)


def _batched_edge_index(
    *,
    base_edges: Sequence[tuple[str, str]],
    feature_order: tuple[str, ...],
    batch_size: int,
) -> torch.Tensor:
    node_count = len(feature_order)
    name_to_index = {name: index for index, name in enumerate(feature_order)}
    numeric_edges = []
    for source, target in base_edges:
        source_index = name_to_index.get(source)
        target_index = name_to_index.get(target)
        if source_index is None or target_index is None:
            raise GDNExtractionError("base edge names must be present in feature_order")
        numeric_edges.append((source_index, target_index))
    columns: list[list[int]] = [[], []]
    for batch_index in range(batch_size):
        offset = batch_index * node_count
        for source_index, target_index in numeric_edges:
            columns[0].append(source_index + offset)
            columns[1].append(target_index + offset)
    return torch.tensor(columns, dtype=torch.long)
