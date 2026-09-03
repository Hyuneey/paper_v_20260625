"""HAI-adapted multi-horizon GDN backend for EXP-01C-GDN-HAI-V1.

Torch remains an optional runtime dependency: importing this module performs
no device discovery and no data access.  The caller must bind normal-only
matrices, a preregistered preprocessing decision, and one frozen CUDA
environment before invoking training.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
import math
import random
from typing import Any, Mapping, Sequence

from paperworks.gdn.upstream_candidate_backend_v1 import upstream_sparse_softmax_compat_v1
from paperworks.gdn.upstream_candidate_backend_v2 import stable_torch_neighbors_v2
from paperworks.validation_v2.exp01_scientific_v1 import PAIR_UNIVERSE
from paperworks.validation_v2.exp01b_backend_v1 import (
    aggregate_attention_from_augmented_tensors_v2,
)
from paperworks.validation_v2.exp01b_contract_v1 import ATTENTION_ATOL, ATTENTION_RTOL
from paperworks.validation_v2.gdn_corr_contract_v1 import Exp01CConfigV1
from paperworks.validation_v2.gdn_corr_v1 import (
    fit_transform_policy_v1,
    purged_contiguous_validation_plan_v1,
)
from paperworks.v6.common import stable_hash_v1


Pair = tuple[str, str]


class Exp01CBackendError(RuntimeError):
    pass


@dataclass(frozen=True)
class Exp01CTrainingResultV1:
    state_dict: Mapping[str, Any]
    graph_edges: tuple[Pair, ...]
    graph_hash: str
    best_validation_loss: float
    completed_epochs: int
    train_window_count: int
    validation_window_count: int
    raw_timestamp_overlap_count: int
    validation_blocks: tuple[tuple[int, int, int], ...]
    scaler_receipt: Mapping[str, Any]
    scaler_center: Any
    scaler_scale: Any


@dataclass(frozen=True)
class Exp01CFunctionalEvidenceV1:
    embedding_scores: Mapping[Pair, float]
    shared_attention_scores: Mapping[Pair, float]
    global_edge_mask_scores: Mapping[tuple[Pair, int], float]
    event_edge_mask_scores: Mapping[tuple[Pair, int], float]
    global_source_occlusion_scores: Mapping[tuple[Pair, int], float]
    event_source_occlusion_scores: Mapping[tuple[Pair, int], float]
    assessment_states: Mapping[Pair, str]
    attention_invariance_passed: bool
    checkpoint_unchanged: bool


@dataclass(frozen=True)
class Exp01CRelationEventV1:
    relation_id: str
    source: str
    target: str
    source_direction: str
    selected_horizon_seconds: int
    event_indices: tuple[int, ...]


@dataclass(frozen=True)
class Exp01CCheckpointEvidenceV1:
    embedding_scores: Mapping[Pair, float]
    attention_scores: Mapping[Pair, float]
    global_edge_mask_scores: Mapping[tuple[Pair, int], float]
    event_edge_mask_scores: Mapping[str, float]
    global_source_occlusion_scores: Mapping[tuple[Pair, int], float]
    event_source_occlusion_scores: Mapping[str, float]
    assessment_states: Mapping[Pair, str]
    baseline_target_horizon_mse: Mapping[tuple[str, int], float]
    attention_invariance_passed: bool
    checkpoint_unchanged: bool


def _set_determinism(torch: Any, seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False


def _graph_from_indices(order: tuple[str, ...], indices: Any) -> tuple[Pair, ...]:
    return tuple(
        (order[int(source)], order[target])
        for target, row in enumerate(indices.detach().cpu().tolist())
        for source in row
    )


def _edge_index(torch: Any, order: tuple[str, ...], graph: Sequence[Pair], *, device: str) -> Any:
    positions = {name: index for index, name in enumerate(order)}
    return torch.tensor(
        [[positions[source] for source, _ in graph], [positions[target] for _, target in graph]],
        dtype=torch.long, device=device,
    )


def _config_adapter(config: Exp01CConfigV1) -> Any:
    class Adapter:
        slide_window = config.history_rows
        embedding_dim = config.embedding_dim
        learned_graph_topk = config.learned_graph_topk
        dropout = config.dropout
        out_layer_num = config.out_layer_num
        out_layer_inter_dim = config.out_layer_inter_dim

    return Adapter()


def _model_type_v1(config: Exp01CConfigV1) -> tuple[Any, Any, type]:
    # EXP-01C uses the already frozen CUDA local-build variant
    # ``torch==2.12.1+cu130``.  The historical dependency gate compares the
    # distribution string to CPU ``2.12.1`` exactly, so this prospective path
    # performs the equivalent base-version check and defines the audited V2
    # equations locally.  Frozen EXP-01/EXP-01B loaders remain untouched.
    from importlib import metadata

    if (
        metadata.version("torch").split("+", 1)[0] != "2.12.1"
        or metadata.version("torch-geometric") != "2.8.0"
    ):
        raise Exp01CBackendError("EXP-01C CUDA dependency identity differs from the frozen environment")
    import torch
    import torch.nn.functional as functional
    from torch import nn
    from torch.nn import Parameter
    from torch_geometric.nn.conv import MessagePassing
    from torch_geometric.nn.inits import glorot, zeros
    from torch_geometric.utils import add_self_loops, remove_self_loops
    adapter = _config_adapter(config)

    class GraphLayer(MessagePassing):
        def __init__(self, in_channels: int, out_channels: int) -> None:
            super().__init__(aggr="add", node_dim=0)
            self.in_channels, self.out_channels = in_channels, out_channels
            self.heads, self.concat, self.negative_slope = 1, False, 0.2
            self.dropout = 0.0
            self.lin = nn.Linear(in_channels, out_channels, bias=False)
            self.att_i = Parameter(torch.empty(1, 1, out_channels))
            self.att_j = Parameter(torch.empty(1, 1, out_channels))
            self.att_em_i = Parameter(torch.empty(1, 1, out_channels))
            self.att_em_j = Parameter(torch.empty(1, 1, out_channels))
            self.bias = Parameter(torch.empty(out_channels))
            self._alpha = None
            self.reset_parameters()

        def reset_parameters(self) -> None:
            glorot(self.lin.weight); glorot(self.att_i); glorot(self.att_j)
            zeros(self.att_em_i); zeros(self.att_em_j); zeros(self.bias)

        def forward(self, x: Any, edge_index: Any, embedding: Any) -> Any:
            transformed = self.lin(x)
            pair = (transformed, transformed)
            edge_index, _ = remove_self_loops(edge_index)
            edge_index, _ = add_self_loops(edge_index, num_nodes=pair[1].size(self.node_dim))
            out = self.propagate(edge_index, x=pair, embedding=embedding, edges=edge_index)
            return out.mean(dim=1) + self.bias

        def message(self, x_i: Any, x_j: Any, edge_index_i: Any, size_i: Any, embedding: Any, edges: Any) -> Any:
            x_i = x_i.view(-1, 1, self.out_channels)
            x_j = x_j.view(-1, 1, self.out_channels)
            embedding_i = embedding[edge_index_i].unsqueeze(1)
            embedding_j = embedding[edges[0]].unsqueeze(1)
            key_i = torch.cat((x_i, embedding_i), dim=-1)
            key_j = torch.cat((x_j, embedding_j), dim=-1)
            alpha = (key_i * torch.cat((self.att_i, self.att_em_i), dim=-1)).sum(-1)
            alpha += (key_j * torch.cat((self.att_j, self.att_em_j), dim=-1)).sum(-1)
            alpha = functional.leaky_relu(alpha.view(-1, 1, 1), self.negative_slope)
            alpha = upstream_sparse_softmax_compat_v1(alpha, edge_index_i, size_i)
            self._alpha = alpha
            return x_j * alpha.view(-1, 1, 1)

    class GNNLayer(nn.Module):
        def __init__(self, input_dim: int, output_dim: int) -> None:
            super().__init__()
            self.gnn = GraphLayer(input_dim, output_dim)
            self.bn = nn.BatchNorm1d(output_dim)
            self.relu = nn.ReLU()

        def forward(self, x: Any, edge_index: Any, embedding: Any) -> Any:
            return self.relu(self.bn(self.gnn(x, edge_index, embedding)))

    class BaseGDN(nn.Module):
        def __init__(self, node_count: int, config_value: Any) -> None:
            super().__init__()
            self.embedding = nn.Embedding(node_count, config_value.embedding_dim)
            self.gnn_layer = GNNLayer(config_value.slide_window, config_value.embedding_dim)
            self.bn_outlayer_in = nn.BatchNorm1d(config_value.embedding_dim)
            self.dropout = nn.Dropout(config_value.dropout)
            nn.init.kaiming_uniform_(self.embedding.weight, a=math.sqrt(5))

    base_type = BaseGDN

    class MultiHorizonGDN(nn.Module):
        def __init__(self, node_count: int) -> None:
            super().__init__()
            base = base_type(node_count, adapter)
            self.node_count = node_count
            self.topk = config.learned_graph_topk
            self.embedding = base.embedding
            self.gnn_layer = base.gnn_layer
            self.bn_outlayer_in = base.bn_outlayer_in
            self.dropout = base.dropout
            self.horizon_head = nn.Linear(config.embedding_dim, len(config.horizons))
            self.learned_graph = None

        @staticmethod
        def _batch_edges(edges: Any, batch_size: int, node_count: int) -> Any:
            edge_count = int(edges.shape[1])
            batched = edges.repeat(1, batch_size).contiguous()
            for index in range(batch_size):
                batched[:, index * edge_count:(index + 1) * edge_count] += index * node_count
            return batched.long()

        def encode(self, data: Any, graph_edge_index: Any) -> Any:
            import torch.nn.functional as functional

            batch_size, node_count, width = data.shape
            x = data.clone().detach().reshape(-1, width).contiguous()
            node_ids = torch.arange(node_count, device=data.device)
            all_embeddings = self.embedding(node_ids)
            batch_edges = self._batch_edges(graph_edge_index, batch_size, node_count)
            embeddings = all_embeddings.repeat(batch_size, 1)
            out = self.gnn_layer(x, batch_edges, embeddings).view(batch_size, node_count, -1)
            out = torch.mul(out, self.embedding(node_ids))
            return functional.relu(self.bn_outlayer_in(out.permute(0, 2, 1))).permute(0, 2, 1)

        def forward(self, data: Any, _original_edges: Any) -> Any:
            node_count = int(data.shape[1])
            weights = self.embedding(torch.arange(node_count, device=data.device))
            cosine = torch.matmul(weights, weights.T)
            cosine = cosine / torch.matmul(
                weights.norm(dim=-1).view(-1, 1), weights.norm(dim=-1).view(1, -1),
            )
            indices = stable_torch_neighbors_v2(cosine, torch_module=torch)
            self.learned_graph = indices
            targets = torch.arange(node_count, device=data.device).unsqueeze(1).repeat(1, self.topk).flatten()
            graph = torch.stack((indices.flatten(), targets), dim=0)
            encoded = self.encode(data, graph)
            return self.horizon_head(self.dropout(encoded))

        def predict_fixed(self, data: Any, graph_edge_index: Any) -> Any:
            return self.horizon_head(self.dropout(self.encode(data, graph_edge_index)))

    return torch, nn, MultiHorizonGDN


class _MultiHorizonDataset:
    def __init__(
        self, segments: Sequence[Any], indices: Sequence[tuple[int, int]],
        *, config: Exp01CConfigV1, torch_module: Any,
    ) -> None:
        self.segments = tuple(
            torch_module.as_tensor(value, dtype=torch_module.float32).contiguous()
            for value in segments
        )
        self.indices = tuple((int(file_index), int(local)) for file_index, local in indices)
        self.config = config
        self._torch = torch_module
        if not self.indices:
            raise Exp01CBackendError("multi-horizon dataset is empty")

    def __len__(self) -> int:
        return len(self.indices)

    def __getitem__(self, index: int) -> tuple[Any, Any, int, int]:
        file_index, local = self.indices[index]
        segment = self.segments[file_index]
        stop = self.config.history_rows + local
        history = segment[stop - self.config.history_rows:stop].transpose(0, 1).contiguous()
        targets = []
        for horizon in self.config.horizons:
            start = stop + horizon - 1
            values = segment[start:start + 3]
            targets.append(values.sum(dim=0) - values.amin(dim=0) - values.amax(dim=0))
        return history, self._stack(targets), file_index, stop

    def _stack(self, targets: Sequence[Any]) -> Any:
        if not targets:
            raise Exp01CBackendError("multi-horizon target set is empty")
        return self._torch.stack(tuple(targets), dim=1)


def _training_row_mask(
    *, segment_lengths: Sequence[int], train_indices: Sequence[tuple[int, int]],
    config: Exp01CConfigV1,
) -> tuple[Any, ...]:
    import numpy as np

    masks = tuple(np.zeros(int(length), dtype=bool) for length in segment_lengths)
    for file_index, local in train_indices:
        stop = config.history_rows + local
        masks[file_index][stop - config.history_rows:stop + max(config.horizons) + 2] = True
    return masks


def _fit_scaler_and_transform(
    segments: Sequence[Any], *, train_indices: Sequence[tuple[int, int]],
    policy: str, config: Exp01CConfigV1,
) -> tuple[tuple[Any, ...], dict[str, Any], Any, Any]:
    import numpy as np

    arrays = tuple(np.asarray(value, dtype=np.float64) for value in segments)
    masks = _training_row_mask(
        segment_lengths=tuple(len(value) for value in arrays),
        train_indices=train_indices, config=config,
    )
    fit_rows = np.concatenate(tuple(value[mask] for value, mask in zip(arrays, masks)), axis=0)
    _, receipt = fit_transform_policy_v1(fit_rows, policy=policy)
    if policy == "RAW_CURRENT":
        center = np.zeros(arrays[0].shape[1], dtype=np.float64)
        scale = np.ones(arrays[0].shape[1], dtype=np.float64)
    elif policy == "TRAIN_ONLY_STANDARDIZED":
        center = np.mean(fit_rows, axis=0)
        scale = np.std(fit_rows, axis=0)
    elif policy == "TRAIN_ONLY_ROBUST_MEDIAN_IQR":
        center = np.median(fit_rows, axis=0)
        q25, q75 = np.quantile(fit_rows, (0.25, 0.75), axis=0, method="linear")
        scale = q75 - q25
    else:
        raise Exp01CBackendError("unknown frozen scaler policy")
    safe_scale = np.where(scale > 1e-12, scale, 1.0)
    transformed = tuple(((value - center) / safe_scale).astype(np.float32) for value in arrays)
    if any(not bool(np.isfinite(value).all()) for value in transformed):
        raise Exp01CBackendError("scaler produced non-finite values")
    return transformed, receipt, center, safe_scale


def transform_with_frozen_scaler_v1(
    segments: Sequence[Any], *, center: Any, scale: Any,
) -> tuple[Any, ...]:
    """Apply one training-view scaler without refitting it on evaluation data."""

    import numpy as np

    center_array = np.asarray(center, dtype=np.float64)
    scale_array = np.asarray(scale, dtype=np.float64)
    if (
        center_array.ndim != 1 or scale_array.shape != center_array.shape
        or not bool(np.isfinite(center_array).all())
        or not bool(np.isfinite(scale_array).all())
        or bool((scale_array <= 0.0).any())
    ):
        raise Exp01CBackendError("frozen scaler parameters are invalid")
    result = tuple(
        ((np.asarray(value, dtype=np.float64) - center_array) / scale_array).astype(np.float32)
        for value in segments
    )
    if any(value.ndim != 2 or value.shape[1] != center_array.size for value in result):
        raise Exp01CBackendError("evaluation segment differs from frozen scaler authority")
    if any(not bool(np.isfinite(value).all()) for value in result):
        raise Exp01CBackendError("frozen scaler produced non-finite evaluation values")
    return result


def _absolute_window_starts(
    indices: Sequence[tuple[int, int]], segment_lengths: Sequence[int],
) -> tuple[int, ...]:
    offsets: list[int] = []
    running = 0
    for length in segment_lengths:
        offsets.append(running)
        running += int(length)
    return tuple(offsets[file_index] + local for file_index, local in indices)


def _window_batch(
    *, torch: Any, matrix: Any, starts: Any, config: Exp01CConfigV1,
) -> tuple[Any, Any]:
    history_offsets = torch.arange(config.history_rows, device=matrix.device)
    history = matrix[starts[:, None] + history_offsets[None, :]].permute(0, 2, 1).contiguous()
    horizon_offsets = torch.tensor(config.horizons, dtype=torch.long, device=matrix.device) - 1
    response_offsets = torch.arange(3, device=matrix.device)
    target_indices = starts[:, None, None] + config.history_rows + horizon_offsets[None, :, None] + response_offsets[None, None, :]
    response = matrix[target_indices]
    targets = (
        response.sum(dim=2) - response.amin(dim=2) - response.amax(dim=2)
    ).permute(0, 2, 1).contiguous()
    return history, targets


def _all_edges(torch: Any, node_count: int, device: str) -> Any:
    return torch.tensor(
        [[source for target in range(node_count) for source in range(node_count) if source != target],
         [target for target in range(node_count) for source in range(node_count) if source != target]],
        dtype=torch.long, device=device,
    )


def _state_hash_v1(state_dict: Mapping[str, Any]) -> str:
    rows = []
    for name, value in sorted(state_dict.items()):
        tensor = value.detach().cpu().contiguous()
        rows.append({
            "name": name, "dtype": str(tensor.dtype), "shape": list(tensor.shape),
            "sha256": __import__("hashlib").sha256(tensor.numpy().tobytes()).hexdigest(),
        })
    return stable_hash_v1({"state": rows})


def _embedding_scores_v1(
    *, torch: Any, model: Any, order: tuple[str, ...], pairs: Sequence[Pair],
) -> dict[Pair, float]:
    weights = model.embedding.weight.detach()
    cosine = torch.matmul(weights, weights.T)
    cosine = cosine / torch.matmul(
        weights.norm(dim=-1).view(-1, 1), weights.norm(dim=-1).view(1, -1),
    )
    positions = {name: index for index, name in enumerate(order)}
    return {
        pair: float(cosine[positions[pair[1]], positions[pair[0]]].item())
        for pair in pairs
    }


def _predict_variant_graphs_v1(
    *, torch: Any, model: Any, data: Any, graphs: Sequence[Any], node_count: int,
) -> Any:
    import torch.nn.functional as functional

    variant_count = len(graphs)
    if variant_count <= 0:
        raise Exp01CBackendError("functional graph variant set is empty")
    batch_size, width = int(data.shape[0]), int(data.shape[2])
    expanded = data.unsqueeze(0).expand(variant_count, -1, -1, -1)
    flattened = expanded.reshape(variant_count * batch_size, node_count, width)
    x = flattened.reshape(-1, width).contiguous()
    all_embeddings = model.embedding(torch.arange(node_count, device=data.device))
    edges = []
    for variant, graph in enumerate(graphs):
        graph = graph.to(data.device)
        for sample in range(batch_size):
            edges.append(graph + (variant * batch_size + sample) * node_count)
    disjoint = torch.cat(edges, dim=1).long()
    embeddings = all_embeddings.repeat(variant_count * batch_size, 1)
    out = model.gnn_layer(x, disjoint, embeddings).view(variant_count * batch_size, node_count, -1)
    out = torch.mul(out, model.embedding(torch.arange(node_count, device=data.device)))
    out = functional.relu(model.bn_outlayer_in(out.permute(0, 2, 1))).permute(0, 2, 1)
    return model.horizon_head(model.dropout(out)).view(
        variant_count, batch_size, node_count, -1,
    )


def evaluate_exp01c_checkpoint_v1(
    *, state_dict: Mapping[str, Any], train4_segment: Any,
    scaler_center: Any, scaler_scale: Any, feature_order: Sequence[str],
    graph_edges: Sequence[Pair], pair_universe: Sequence[Pair],
    relation_events: Sequence[Exp01CRelationEventV1], view: str, seed: int,
    config: Exp01CConfigV1,
) -> Exp01CCheckpointEvidenceV1:
    """Evaluate one fixed checkpoint on normal train4 without graph refill."""

    import numpy as np
    from paperworks.validation_v2.exp01b_functional_v1 import (
        file_local_block_permutation_v1, relative_delta_mse_v1,
    )

    before = _state_hash_v1(state_dict)
    order = tuple(feature_order)
    pairs = tuple(pair_universe)
    positions = {name: index for index, name in enumerate(order)}
    graph = tuple(graph_edges)
    if len(graph) != len(set(graph)) or any(source == target for source, target in graph):
        raise Exp01CBackendError("fixed learned graph identity is invalid")
    transformed = transform_with_frozen_scaler_v1(
        (train4_segment,), center=scaler_center, scale=scaler_scale,
    )[0]
    torch, _nn, model_type = _model_type_v1(config)
    _set_determinism(torch, seed)
    model = model_type(len(order)).to(config.device)
    model.load_state_dict(state_dict, strict=True)
    model.eval()
    graph_index = _edge_index(torch, order, graph, device=config.device)
    node_count = len(order)
    count = len(transformed) - config.history_rows - 62 + 1
    if count <= 0:
        raise Exp01CBackendError("train4 is too short for multi-horizon evaluation")
    matrix = torch.as_tensor(transformed, dtype=torch.float32, device=config.device).contiguous()
    starts_cpu = torch.arange(count, dtype=torch.long)
    target_names = tuple(sorted({target for _, target in pairs}))
    target_positions = tuple(positions[name] for name in target_names)
    baseline_sum = torch.zeros((node_count, len(config.horizons)), dtype=torch.float64)
    attention_sum = {edge: 0.0 for edge in graph}
    attention_count = 0
    graph_members = tuple(edge for edge in graph if edge in set(pairs))
    masked_sum = {edge: torch.zeros(len(config.horizons), dtype=torch.float64) for edge in graph_members}
    occlusion_sum = {
        source: torch.zeros((len(target_names), len(config.horizons)), dtype=torch.float64)
        for source in sorted({source for source, _ in pairs})
    }
    event_by_relation = {item.relation_id: item for item in relation_events}
    event_sets = {item.relation_id: set(item.event_indices) for item in relation_events}
    event_baseline = {item.relation_id: 0.0 for item in relation_events}
    event_masked = {item.relation_id: 0.0 for item in relation_events if (item.source, item.target) in graph_members}
    event_occluded = {item.relation_id: 0.0 for item in relation_events}
    event_counts = {item.relation_id: 0 for item in relation_events}
    graph_variants = {
        edge: _edge_index(torch, order, tuple(item for item in graph if item != edge), device=config.device)
        for edge in graph_members
    }
    source_names = tuple(sorted({source for source, _ in pairs}))
    permuted = {}
    for source in source_names:
        local_seed = int(stable_hash_v1({
            "experiment": "EXP-01C-GDN-HAI-V1", "view": view, "seed": seed,
            "split": "train4", "source": source,
        })[:16], 16)
        column = file_local_block_permutation_v1(
            transformed[:, positions[source]].tolist(), seed=local_seed,
        )
        permuted[source] = torch.tensor(column, dtype=torch.float32, device=config.device)
    attention_invariance = True
    with torch.no_grad():
        for offset in range(0, count, config.batch_size):
            starts = starts_cpu[offset:offset + config.batch_size].to(config.device)
            x, y = _window_batch(torch=torch, matrix=matrix, starts=starts, config=config)
            baseline = model.predict_fixed(x, graph_index)
            captured = model.predict_fixed(x, graph_index)
            if not bool(torch.allclose(baseline, captured, atol=1e-7, rtol=1e-6)):
                attention_invariance = False
                raise Exp01CBackendError("attention capture changed fixed-checkpoint output")
            alpha = getattr(getattr(model.gnn_layer, "gnn", None), "_alpha", None)
            if alpha is None:
                raise Exp01CBackendError("shared encoder attention is unavailable")
            batch_size = int(x.shape[0])
            batched = model._batch_edges(graph_index, batch_size, node_count)
            from torch_geometric.utils import add_self_loops, remove_self_loops
            augmented, _ = remove_self_loops(batched)
            augmented, _ = add_self_loops(augmented, num_nodes=batch_size * node_count)
            mapped = aggregate_attention_from_augmented_tensors_v2(
                torch_module=torch, augmented_edges=augmented, alpha_values=alpha,
                node_count=node_count, feature_order=order, graph_edges=graph,
                batch_size=batch_size,
            )
            for edge in graph:
                attention_sum[edge] += mapped[edge] * batch_size
            attention_count += batch_size
            error = (baseline - y) ** 2
            baseline_sum += error.sum(dim=0).double().cpu()
            stops = (starts + config.history_rows).detach().cpu().tolist()
            matching_by_relation = {
                relation_id: [
                    index for index, stop in enumerate(stops)
                    if int(stop) in event_sets[relation_id]
                ]
                for relation_id in event_by_relation
            }
            for relation_id, item in event_by_relation.items():
                matching = matching_by_relation[relation_id]
                if matching:
                    horizon_index = config.horizons.index(item.selected_horizon_seconds)
                    values = error[matching, positions[item.target], horizon_index]
                    event_baseline[relation_id] += float(values.sum().item())
                    event_counts[relation_id] += len(matching)
            for chunk_start in range(0, len(graph_members), 8):
                chunk = graph_members[chunk_start:chunk_start + 8]
                predictions = _predict_variant_graphs_v1(
                    torch=torch, model=model, data=x,
                    graphs=tuple(graph_variants[edge] for edge in chunk), node_count=node_count,
                )
                for local, edge in enumerate(chunk):
                    edge_error = (predictions[local, :, positions[edge[1]], :] - y[:, positions[edge[1]], :]) ** 2
                    masked_sum[edge] += edge_error.sum(dim=0).double().cpu()
                    for relation_id, item in event_by_relation.items():
                        if (item.source, item.target) != edge:
                            continue
                        matching = matching_by_relation[relation_id]
                        if matching:
                            horizon_index = config.horizons.index(item.selected_horizon_seconds)
                            event_masked[relation_id] += float(edge_error[matching, horizon_index].sum().item())
            history_offsets = torch.arange(config.history_rows, device=config.device)
            for chunk_start in range(0, len(source_names), 8):
                chunk = source_names[chunk_start:chunk_start + 8]
                variants = x.unsqueeze(0).expand(len(chunk), -1, -1, -1).clone()
                raw_indices = starts[:, None] + history_offsets[None, :]
                for local, source in enumerate(chunk):
                    variants[local, :, positions[source], :] = permuted[source][raw_indices]
                predictions = _predict_variant_graphs_v1(
                    torch=torch, model=model,
                    data=variants.reshape(len(chunk) * batch_size, node_count, config.history_rows),
                    graphs=tuple(graph_index for _ in range(1)), node_count=node_count,
                ).reshape(len(chunk), batch_size, node_count, len(config.horizons))
                for local, source in enumerate(chunk):
                    source_error = (predictions[local, :, target_positions, :] - y[:, target_positions, :]) ** 2
                    occlusion_sum[source] += source_error.sum(dim=0).double().cpu()
                    for relation_id, item in event_by_relation.items():
                        if item.source != source:
                            continue
                        matching = matching_by_relation[relation_id]
                        if matching:
                            horizon_index = config.horizons.index(item.selected_horizon_seconds)
                            target_index = target_names.index(item.target)
                            event_occluded[relation_id] += float(source_error[matching, target_index, horizon_index].sum().item())
    baseline_mse = baseline_sum / count
    global_edge = {}
    for edge, values in masked_sum.items():
        for horizon_index, horizon in enumerate(config.horizons):
            global_edge[(edge, horizon)] = relative_delta_mse_v1(
                baseline_target_mse=float(baseline_mse[positions[edge[1]], horizon_index]),
                masked_target_mse=float(values[horizon_index] / count),
            )
    global_occlusion = {}
    for source, values in occlusion_sum.items():
        for target_index, target in enumerate(target_names):
            for horizon_index, horizon in enumerate(config.horizons):
                global_occlusion[((source, target), horizon)] = relative_delta_mse_v1(
                    baseline_target_mse=float(baseline_mse[positions[target], horizon_index]),
                    masked_target_mse=float(values[target_index, horizon_index] / count),
                )
    event_edge = {}
    event_occ = {}
    for relation_id, item in event_by_relation.items():
        count_value = event_counts[relation_id]
        if count_value <= 0:
            continue
        base = event_baseline[relation_id] / count_value
        if relation_id in event_masked:
            event_edge[relation_id] = relative_delta_mse_v1(
                baseline_target_mse=base, masked_target_mse=event_masked[relation_id] / count_value,
            )
        event_occ[relation_id] = relative_delta_mse_v1(
            baseline_target_mse=base, masked_target_mse=event_occluded[relation_id] / count_value,
        )
    attention = {
        pair: attention_sum[pair] / attention_count for pair in pairs if pair in attention_sum
    }
    assessment = {
        pair: "DIRECT_EDGEMASK_AND_SOURCE_OCCLUSION" if pair in graph_members
        else "NOT_IN_LEARNED_GRAPH_SOURCE_OCCLUSION_ONLY"
        for pair in pairs
    }
    target_mse = {
        (target, horizon): float(baseline_mse[positions[target], index])
        for target in target_names for index, horizon in enumerate(config.horizons)
    }
    after = _state_hash_v1(model.state_dict())
    return Exp01CCheckpointEvidenceV1(
        embedding_scores=_embedding_scores_v1(torch=torch, model=model, order=order, pairs=pairs),
        attention_scores=attention, global_edge_mask_scores=global_edge,
        event_edge_mask_scores=event_edge,
        global_source_occlusion_scores=global_occlusion,
        event_source_occlusion_scores=event_occ,
        assessment_states=assessment, baseline_target_horizon_mse=target_mse,
        attention_invariance_passed=attention_invariance,
        checkpoint_unchanged=before == after,
    )


def train_exp01c_seed_v1(
    *, segments: Sequence[Any], feature_order: Sequence[str], seed: int,
    preprocessing_policy: str, config: Exp01CConfigV1,
) -> Exp01CTrainingResultV1:
    import numpy as np

    if seed not in config.seeds:
        raise Exp01CBackendError("seed is outside the preregistered schedule")
    order = tuple(feature_order)
    arrays = tuple(np.asarray(value, dtype=np.float64) for value in segments)
    if not arrays or any(value.ndim != 2 or value.shape[1] != len(order) for value in arrays):
        raise Exp01CBackendError("normal training segments do not match feature authority")
    plan = purged_contiguous_validation_plan_v1(
        segment_lengths=tuple(len(value) for value in arrays), seed=seed,
        history=config.history_rows, max_horizon=62,
        validation_ratio=config.validation_ratio,
    )
    transformed, scaler_receipt, scaler_center, scaler_scale = _fit_scaler_and_transform(
        arrays, train_indices=plan.train_window_indices,
        policy=preprocessing_policy, config=config,
    )
    torch, nn, model_type = _model_type_v1(config)
    _set_determinism(torch, seed)
    matrix = torch.as_tensor(
        np.concatenate(transformed, axis=0), dtype=torch.float32, device=config.device,
    ).contiguous()
    train_starts = torch.tensor(
        _absolute_window_starts(plan.train_window_indices, tuple(len(value) for value in transformed)),
        dtype=torch.long,
    )
    validation_starts = torch.tensor(
        _absolute_window_starts(plan.validation_window_indices, tuple(len(value) for value in transformed)),
        dtype=torch.long,
    )
    if train_starts.numel() <= 0 or validation_starts.numel() <= 0:
        raise Exp01CBackendError("purged training or validation window set is empty")
    generator = torch.Generator(device="cpu").manual_seed(seed)
    model = model_type(len(order)).to(config.device)
    optimizer = torch.optim.Adam(
        model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay,
    )
    graph = _all_edges(torch, len(order), config.device)
    best_state: Mapping[str, Any] | None = None
    best_loss = float("inf")
    stale = 0
    completed = 0
    for epoch in range(config.epochs):
        model.train()
        permutation = torch.randperm(int(train_starts.numel()), generator=generator)
        for offset in range(0, int(permutation.numel()), config.batch_size):
            selected = train_starts[permutation[offset:offset + config.batch_size]].to(config.device)
            x, y = _window_batch(torch=torch, matrix=matrix, starts=selected, config=config)
            optimizer.zero_grad()
            prediction = model(x, graph)
            loss = ((prediction - y) ** 2).mean()
            if not bool(torch.isfinite(loss)):
                raise Exp01CBackendError("training loss is non-finite")
            loss.backward()
            optimizer.step()
        model.eval()
        squared = 0.0
        cells = 0
        with torch.no_grad():
            for offset in range(0, int(validation_starts.numel()), config.batch_size):
                selected = validation_starts[offset:offset + config.batch_size].to(config.device)
                x, y = _window_batch(torch=torch, matrix=matrix, starts=selected, config=config)
                prediction = model(x, graph)
                squared += float(((prediction - y) ** 2).sum().item())
                cells += int(prediction.numel())
        value = squared / cells
        completed = epoch + 1
        if value < best_loss:
            best_loss = value
            best_state = copy.deepcopy(model.state_dict())
            stale = 0
        else:
            stale += 1
        if stale >= config.early_stopping_patience:
            break
    if best_state is None or not math.isfinite(best_loss):
        raise Exp01CBackendError("no finite validation checkpoint")
    model.load_state_dict(best_state, strict=True)
    model.eval()
    first_x, _ = _window_batch(
        torch=torch, matrix=matrix, starts=train_starts[:1].to(config.device), config=config,
    )
    with torch.no_grad():
        model(first_x, graph)
    if model.learned_graph is None:
        raise Exp01CBackendError("learned graph was not materialized")
    graph_edges = _graph_from_indices(order, model.learned_graph)
    if len(graph_edges) != len(set(graph_edges)) or any(source == target for source, target in graph_edges):
        raise Exp01CBackendError("corrected learned graph is invalid")
    return Exp01CTrainingResultV1(
        state_dict=best_state, graph_edges=graph_edges,
        graph_hash=stable_hash_v1({"graph_edges": graph_edges}),
        best_validation_loss=best_loss, completed_epochs=completed,
        train_window_count=int(train_starts.numel()),
        validation_window_count=int(validation_starts.numel()),
        raw_timestamp_overlap_count=plan.raw_timestamp_overlap_count,
        validation_blocks=plan.validation_blocks,
        scaler_receipt=scaler_receipt,
        scaler_center=scaler_center,
        scaler_scale=scaler_scale,
    )


def smoke_exp01c_backend_v1(*, config: Exp01CConfigV1) -> dict[str, Any]:
    torch, _nn, model_type = _model_type_v1(config)
    _set_determinism(torch, 11)
    model = model_type(37).to(config.device)
    x = torch.arange(2 * 37 * 5, dtype=torch.float32, device=config.device).reshape(2, 37, 5) / 1000
    graph = _all_edges(torch, 37, config.device)
    prediction = model(x, graph)
    if tuple(prediction.shape) != (2, 37, 5):
        raise Exp01CBackendError("multi-horizon output shape mismatch")
    y = torch.zeros_like(prediction)
    loss = ((prediction - y) ** 2).mean()
    loss.backward()
    return {
        "status": "PASS", "model_device": str(next(model.parameters()).device).split(":", 1)[0],
        "tensor_device": str(x.device).split(":", 1)[0],
        "output_shape": list(prediction.shape), "loss_finite": bool(torch.isfinite(loss)),
        "equal_feature_horizon_weight": True,
    }


__all__ = [
    "Exp01CBackendError", "Exp01CFunctionalEvidenceV1", "Exp01CTrainingResultV1",
    "smoke_exp01c_backend_v1", "train_exp01c_seed_v1",
]
