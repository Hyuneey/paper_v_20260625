"""Complete, memory-bounded backend used only by Validation V2 EXP-01.

The training loop preserves the frozen eager-window ordering and validation
split while materializing each window lazily.  The only arm difference is the
pre-Top-5 diagonal policy implemented by the already-audited V1/V2 model
factories.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
import math
import random
from typing import Any, Mapping, Sequence

from paperworks.gdn.upstream_candidate_backend_v1 import (
    FROZEN_SEEDS,
    TrainedSeedGraphV1,
    UpstreamGDNDataBoundaryError,
    UpstreamGDNError,
    UpstreamGDNFidelityError,
    UpstreamGDNTrainingConfigV1,
    _load_runtime_types_v1,
    _set_all_seeds_v1,
)
from paperworks.gdn.upstream_candidate_backend_v2 import (
    _load_runtime_types_v2,
    stable_torch_neighbors_v2,
)
from paperworks.validation_v2.exp01_scientific_v1 import ArmId
from paperworks.v6.common import stable_hash_v1


@dataclass(frozen=True)
class Exp01BackendTrainingResultV2:
    trained_graph: TrainedSeedGraphV1
    graph_edges: tuple[tuple[str, str], ...]
    forward_graph_hash: str
    extraction_graph_hash: str
    best_state_dict: Mapping[str, Any]
    validation_start: int
    validation_length: int
    window_count: int


@dataclass(frozen=True)
class Exp01BackendGraphReplayV2:
    graph_edges: tuple[tuple[str, str], ...]
    forward_graph_hash: str
    extraction_graph_hash: str


class _FileLocalLazyWindows:
    """Map window indices to file-local slices of one prepared CPU tensor per file.

    Conversion to frozen ``float32`` happens once per input segment instead of
    once per sample per epoch.  Window ordering, file boundaries, targets, and
    device transfer remain identical to the original lazy adapter.
    """

    def __init__(self, segments: Sequence[Any], *, window: int, stride: int, torch_module: Any) -> None:
        self._segments = tuple(
            torch_module.as_tensor(segment, dtype=torch_module.float32).contiguous()
            for segment in segments
        )
        self._window = window
        self._stride = stride
        self._torch = torch_module
        counts = tuple(max(0, (len(segment) - window + stride - 1) // stride) for segment in self._segments)
        self._bounds: list[tuple[int, int, Any]] = []
        start = 0
        for count, segment in zip(counts, self._segments):
            self._bounds.append((start, start + count, segment))
            start += count
        self._length = start
        if self._length <= 0:
            raise UpstreamGDNDataBoundaryError("no EXP-01 GDN windows were produced")

    def __len__(self) -> int:
        return self._length

    def __getitem__(self, index: int) -> tuple[Any, Any]:
        if index < 0:
            index += self._length
        if index < 0 or index >= self._length:
            raise IndexError(index)
        for start, stop, segment in self._bounds:
            if start <= index < stop:
                local = index - start
                target = self._window + local * self._stride
                history = segment[target - self._window : target]
                # [time,node] -> [node,time], matching _segment_windows_v1/v2.
                x = history.transpose(0, 1).contiguous()
                y = segment[target]
                return x, y
        raise IndexError(index)


def _graph_from_indices(feature_order: tuple[str, ...], indices: Any) -> tuple[tuple[str, str], ...]:
    return tuple(
        (feature_order[int(source_index)], feature_order[target_index])
        for target_index, row in enumerate(indices.detach().cpu().tolist())
        for source_index in row
    )


def _edge_index_from_graph(torch: Any, feature_order: tuple[str, ...], graph_edges: Sequence[tuple[str, str]]) -> Any:
    positions = {name: index for index, name in enumerate(feature_order)}
    return torch.tensor(
        [[positions[source] for source, _ in graph_edges], [positions[target] for _, target in graph_edges]],
        dtype=torch.long,
    )


def _predict_with_fixed_graph(model: Any, data: Any, graph_edge_index: Any) -> Any:
    """Evaluate a fixed learned graph without recomputing or refilling Top-K."""

    import torch
    import torch.nn.functional as functional

    batch_size, node_count, input_width = data.shape
    x = data.clone().detach().view(-1, input_width).contiguous()
    node_ids = torch.arange(node_count, device=data.device)
    all_embeddings = model.embedding(node_ids)
    batch_edges = model._batch_edges(graph_edge_index.to(data.device), batch_size, node_count)
    embeddings = all_embeddings.repeat(batch_size, 1)
    out = model.gnn_layer(x, batch_edges, embeddings).view(batch_size, node_count, -1)
    out = torch.mul(out, model.embedding(node_ids))
    out = functional.relu(model.bn_outlayer_in(out.permute(0, 2, 1))).permute(0, 2, 1)
    return model.out_layer(model.dropout(out)).view(-1, node_count)


def train_exp01_seed_v2(
    *,
    arm_id: ArmId,
    segments: Sequence[Any],
    feature_order: Sequence[str],
    candidate_pairs: Sequence[tuple[str, str]],
    seed: int,
    config: UpstreamGDNTrainingConfigV1,
) -> Exp01BackendTrainingResultV2:
    """Train one exact scheduled seed and retain its best state in memory."""

    if seed not in FROZEN_SEEDS or config.seeds != FROZEN_SEEDS:
        raise UpstreamGDNFidelityError("EXP-01 seed policy changed")
    feature_tuple = tuple(feature_order)
    if len(feature_tuple) <= config.learned_graph_topk:
        raise UpstreamGDNFidelityError("feature context must exceed Top-K")
    pair_set = set(candidate_pairs)
    if any(source not in feature_tuple or target not in feature_tuple for source, target in pair_set):
        raise UpstreamGDNDataBoundaryError("candidate projection is outside model context")
    loader = _load_runtime_types_v1 if arm_id is ArmId.FROZEN_SELF_ELIGIBLE else _load_runtime_types_v2
    torch, nn, model_type = loader()
    _set_all_seeds_v1(torch, seed)
    dataset = _FileLocalLazyWindows(
        segments, window=config.slide_window, stride=config.slide_stride, torch_module=torch,
    )
    dataset_length = len(dataset)
    train_length = int(dataset_length * (1.0 - config.validation_ratio))
    validation_length = int(dataset_length * config.validation_ratio)
    if train_length <= 0 or validation_length <= 0:
        raise UpstreamGDNDataBoundaryError("EXP-01 validation split is empty")
    validation_start = random.randrange(train_length)
    indices = torch.arange(dataset_length)
    train_indices = torch.cat((indices[:validation_start], indices[validation_start + validation_length :]))
    validation_indices = indices[validation_start : validation_start + validation_length]
    train_loader = torch.utils.data.DataLoader(
        torch.utils.data.Subset(dataset, train_indices), batch_size=config.batch_size, shuffle=True,
    )
    validation_loader = torch.utils.data.DataLoader(
        torch.utils.data.Subset(dataset, validation_indices), batch_size=config.batch_size, shuffle=False,
    )
    model = model_type(len(feature_tuple), config).to(config.device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    loss_function = nn.MSELoss(reduction="mean")
    original_edges = torch.tensor(
        [[source for target in range(len(feature_tuple)) for source in range(len(feature_tuple)) if source != target],
         [target for target in range(len(feature_tuple)) for source in range(len(feature_tuple)) if source != target]],
        dtype=torch.long,
        device=config.device,
    )
    best_state: Mapping[str, Any] | None = None
    best_loss = float("inf")
    stale_epochs = 0
    completed_epochs = 0
    for epoch in range(config.epochs):
        model.train()
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            prediction = model(batch_x.to(config.device), original_edges)
            loss = loss_function(prediction, batch_y.to(config.device))
            loss.backward()
            optimizer.step()
        model.eval()
        losses: list[float] = []
        with torch.no_grad():
            for batch_x, batch_y in validation_loader:
                prediction = model(batch_x.to(config.device), original_edges)
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
        raise UpstreamGDNError("failed_gdn_training: no finite EXP-01 validation state")
    model.load_state_dict(best_state)
    model.eval()
    first_x, _ = dataset[0]
    with torch.no_grad():
        model(first_x.unsqueeze(0).to(config.device), original_edges)
    forward_indices = model.learned_graph.detach().cpu()
    weights = model.embedding.weight.detach()
    cosine = torch.matmul(weights, weights.T)
    norms = torch.matmul(weights.norm(dim=-1).view(-1, 1), weights.norm(dim=-1).view(1, -1))
    cosine = cosine / norms
    extraction_indices = (
        torch.topk(cosine, config.learned_graph_topk, dim=-1)[1]
        if arm_id is ArmId.FROZEN_SELF_ELIGIBLE
        else stable_torch_neighbors_v2(cosine, torch_module=torch)
    ).detach().cpu()
    forward_edges = _graph_from_indices(feature_tuple, forward_indices)
    extraction_edges = _graph_from_indices(feature_tuple, extraction_indices)
    forward_hash = stable_hash_v1({"graph_edges": forward_edges})
    extraction_hash = stable_hash_v1({"graph_edges": extraction_edges})
    if forward_hash != extraction_hash:
        raise UpstreamGDNFidelityError("forward and extraction graph identities diverged")
    positions = {name: index for index, name in enumerate(feature_tuple)}
    selected = tuple(sorted(pair for pair in forward_edges if pair in pair_set))
    similarities = {
        pair: float(cosine[positions[pair[1]], positions[pair[0]]].item()) for pair in pair_set
    }
    return Exp01BackendTrainingResultV2(
        trained_graph=TrainedSeedGraphV1(
            seed=seed, selected_edges=selected, candidate_similarities=similarities,
            epoch_count=completed_epochs, best_validation_loss=best_loss,
            hyperparameter_hash=config.hyperparameter_hash,
        ),
        graph_edges=forward_edges,
        forward_graph_hash=forward_hash,
        extraction_graph_hash=extraction_hash,
        best_state_dict=best_state,
        validation_start=validation_start,
        validation_length=validation_length,
        window_count=dataset_length,
    )


def evaluate_fixed_checkpoint_mse_v2(
    *,
    arm_id: ArmId,
    state_dict: Mapping[str, Any],
    segments: Sequence[Any],
    feature_order: Sequence[str],
    graph_edges: Sequence[tuple[str, str]],
    config: UpstreamGDNTrainingConfigV1,
) -> float:
    """Evaluate train4 MSE under an explicit graph; no Top-K refill occurs."""

    loader = _load_runtime_types_v1 if arm_id is ArmId.FROZEN_SELF_ELIGIBLE else _load_runtime_types_v2
    torch, nn, model_type = loader()
    dataset = _FileLocalLazyWindows(
        segments, window=config.slide_window, stride=config.slide_stride, torch_module=torch,
    )
    model = model_type(len(tuple(feature_order)), config).to(config.device)
    model.load_state_dict(state_dict)
    model.eval()
    graph_edge_index = _edge_index_from_graph(torch, tuple(feature_order), graph_edges)
    data_loader = torch.utils.data.DataLoader(dataset, batch_size=config.batch_size, shuffle=False)
    loss_function = nn.MSELoss(reduction="sum")
    squared_error = 0.0
    value_count = 0
    with torch.no_grad():
        for batch_x, batch_y in data_loader:
            prediction = _predict_with_fixed_graph(model, batch_x.to(config.device), graph_edge_index)
            squared_error += float(loss_function(prediction, batch_y.to(config.device)).item())
            value_count += int(batch_y.numel())
    if value_count <= 0:
        raise UpstreamGDNDataBoundaryError("empty train4 metric denominator")
    return squared_error / value_count


def replay_exp01_checkpoint_graph_v2(
    *,
    arm_id: ArmId,
    state_dict: Mapping[str, Any],
    segments: Sequence[Any],
    feature_order: Sequence[str],
    candidate_pairs: Sequence[tuple[str, str]],
    seed: int,
    config: UpstreamGDNTrainingConfigV1,
) -> Exp01BackendGraphReplayV2:
    """Reconstruct the frozen graph identity from a verified best checkpoint.

    No optimization step is run.  The model is loaded in evaluation mode and
    the original forward/extraction agreement check is replayed from the
    checkpoint weights under the exact frozen arm and feature context.
    """

    if seed not in FROZEN_SEEDS or config.seeds != FROZEN_SEEDS:
        raise UpstreamGDNFidelityError("EXP-01 checkpoint replay seed policy changed")
    feature_tuple = tuple(feature_order)
    pair_set = set(candidate_pairs)
    if len(feature_tuple) <= config.learned_graph_topk:
        raise UpstreamGDNFidelityError("feature context must exceed Top-K")
    if any(source not in feature_tuple or target not in feature_tuple for source, target in pair_set):
        raise UpstreamGDNDataBoundaryError("candidate projection is outside model context")
    loader = _load_runtime_types_v1 if arm_id is ArmId.FROZEN_SELF_ELIGIBLE else _load_runtime_types_v2
    torch, _, model_type = loader()
    _set_all_seeds_v1(torch, seed)
    dataset = _FileLocalLazyWindows(
        segments, window=config.slide_window, stride=config.slide_stride, torch_module=torch,
    )
    model = model_type(len(feature_tuple), config).to(config.device)
    model.load_state_dict(state_dict, strict=True)
    model.eval()
    original_edges = torch.tensor(
        [[source for target in range(len(feature_tuple)) for source in range(len(feature_tuple)) if source != target],
         [target for target in range(len(feature_tuple)) for source in range(len(feature_tuple)) if source != target]],
        dtype=torch.long,
    )
    first_x, _ = dataset[0]
    with torch.no_grad():
        model(first_x.unsqueeze(0).to(config.device), original_edges.to(config.device))
    forward_indices = model.learned_graph.detach().cpu()
    weights = model.embedding.weight.detach()
    cosine = torch.matmul(weights, weights.T)
    norms = torch.matmul(weights.norm(dim=-1).view(-1, 1), weights.norm(dim=-1).view(1, -1))
    cosine = cosine / norms
    extraction_indices = (
        torch.topk(cosine, config.learned_graph_topk, dim=-1)[1]
        if arm_id is ArmId.FROZEN_SELF_ELIGIBLE
        else stable_torch_neighbors_v2(cosine, torch_module=torch)
    ).detach().cpu()
    forward_edges = _graph_from_indices(feature_tuple, forward_indices)
    extraction_edges = _graph_from_indices(feature_tuple, extraction_indices)
    forward_hash = stable_hash_v1({"graph_edges": forward_edges})
    extraction_hash = stable_hash_v1({"graph_edges": extraction_edges})
    if forward_hash != extraction_hash:
        raise UpstreamGDNFidelityError("checkpoint forward and extraction graph identities diverged")
    return Exp01BackendGraphReplayV2(
        graph_edges=forward_edges,
        forward_graph_hash=forward_hash,
        extraction_graph_hash=extraction_hash,
    )


__all__ = [
    "Exp01BackendGraphReplayV2", "Exp01BackendTrainingResultV2",
    "evaluate_fixed_checkpoint_mse_v2", "replay_exp01_checkpoint_graph_v2",
    "train_exp01_seed_v2",
]
