"""VALIDATION V2 self-excluded learned-neighbor policy.

This module does not modify the frozen V1 GDN backend.  It provides the
separately versioned graph-selection primitive that a V2 training and
extraction path must call at both sites.  Importing the module is lightweight;
Torch remains optional and is supplied by an already-authorized caller.
"""

from __future__ import annotations

import copy
import math
import os
import random
from dataclasses import dataclass
from typing import Any, Sequence

from paperworks.v6.common import require_sha256, stable_hash_v1
from paperworks.gdn.upstream_candidate_backend_v1 import (
    FROZEN_SEEDS,
    TrainedSeedGraphV1,
    UpstreamGDNDataBoundaryError,
    UpstreamGDNDependencyError,
    UpstreamGDNError,
    UpstreamGDNFidelityError,
    UpstreamGDNTrainingConfigV1,
    build_dependency_status_v1,
    inspect_current_dependency_environment_v1,
    upstream_sparse_softmax_compat_v1,
)


GDN_V2_NEIGHBOR_POLICY = "SELF_EXCLUDED_STABLE_TOPK_V1"
GDN_V2_BACKEND_STATUS = "PREPARED_GRAPH_PRIMITIVE_NOT_SCIENTIFIC_RUNNER"
EXP01_RUN_AUTH_SCHEMA_V2 = "paperworks.validation_v2.exp01_run_authorization_v2"
EXP01_TRAINING_INPUT_SCHEMA_V2 = "paperworks.validation_v2.exp01_authorized_training_input_v2"
EXP01_SEED_RECEIPT_SCHEMA_V2 = "paperworks.validation_v2.exp01_seed_run_receipt_v2"


class GDNV2NeighborError(ValueError):
    """Raised when the V2 learned-neighbor contract is violated."""


def _strict_bool(value: object, name: str) -> None:
    if type(value) is not bool:
        raise GDNV2NeighborError(f"{name} must be a strict Boolean")


@dataclass(frozen=True)
class GDNNeighborPolicyV2:
    topk: int = 5
    self_policy: str = "DIAGONAL_NEGATIVE_INFINITY_BEFORE_RANKING"
    tie_policy: str = "LOWEST_SOURCE_INDEX_FIRST"
    direction: str = "SOURCE_TO_TARGET"
    version: str = GDN_V2_NEIGHBOR_POLICY

    def __post_init__(self) -> None:
        if self.topk != 5:
            raise GDNV2NeighborError("VALIDATION V2 GDN internal Top-K must remain five")
        if self.self_policy != "DIAGONAL_NEGATIVE_INFINITY_BEFORE_RANKING":
            raise GDNV2NeighborError("self-exclusion policy changed")
        if self.tie_policy != "LOWEST_SOURCE_INDEX_FIRST":
            raise GDNV2NeighborError("tie policy changed")
        if self.direction != "SOURCE_TO_TARGET" or self.version != GDN_V2_NEIGHBOR_POLICY:
            raise GDNV2NeighborError("neighbor identity changed")

    @property
    def policy_hash(self) -> str:
        return stable_hash_v1(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "topk": self.topk,
            "self_policy": self.self_policy,
            "tie_policy": self.tie_policy,
            "direction": self.direction,
        }


def select_self_excluded_neighbors_v2(
    similarity: Sequence[Sequence[float]],
    *,
    policy: GDNNeighborPolicyV2 | None = None,
) -> tuple[tuple[int, ...], ...]:
    """Return deterministic source indices for each target row.

    The diagonal is made ineligible before ranking.  Equal similarities are
    ordered by the lowest source index.  The input is never mutated.
    """

    selected_policy = policy or GDNNeighborPolicyV2()
    rows = tuple(tuple(row) for row in similarity)
    node_count = len(rows)
    if node_count <= selected_policy.topk:
        raise GDNV2NeighborError("node count must exceed internal Top-K")
    if any(len(row) != node_count for row in rows):
        raise GDNV2NeighborError("similarity matrix must be square")
    result: list[tuple[int, ...]] = []
    for target_index, row in enumerate(rows):
        if any(type(value) not in (int, float) or not math.isfinite(float(value)) for value in row):
            raise GDNV2NeighborError("similarity matrix must contain finite real values")
        eligible = [
            (float(value), source_index)
            for source_index, value in enumerate(row)
            if source_index != target_index
        ]
        eligible.sort(key=lambda item: (-item[0], item[1]))
        neighbors = tuple(source for _, source in eligible[: selected_policy.topk])
        if len(neighbors) != selected_policy.topk or len(set(neighbors)) != selected_policy.topk:
            raise GDNV2NeighborError("exactly five distinct neighbors are required")
        if target_index in neighbors:
            raise GDNV2NeighborError("self identity survived V2 exclusion")
        result.append(neighbors)
    return tuple(result)


def stable_torch_neighbors_v2(
    cosine: Any,
    *,
    torch_module: Any,
    policy: GDNNeighborPolicyV2 | None = None,
) -> Any:
    """Apply the same policy to an authorized Torch tensor.

    ``torch.argsort(..., stable=True)`` preserves source-index order for ties.
    This helper must be used by both future V2 forward graph construction and
    post-checkpoint extraction.  It intentionally does not load Torch itself.
    """

    selected_policy = policy or GDNNeighborPolicyV2()
    if getattr(cosine, "ndim", None) != 2 or cosine.shape[0] != cosine.shape[1]:
        raise GDNV2NeighborError("Torch cosine matrix must be square")
    if int(cosine.shape[0]) <= selected_policy.topk:
        raise GDNV2NeighborError("node count must exceed internal Top-K")
    masked = cosine.clone()
    masked.fill_diagonal_(float("-inf"))
    if not bool(torch_module.isfinite(masked[~torch_module.eye(masked.shape[0], dtype=torch_module.bool, device=masked.device)]).all()):
        raise GDNV2NeighborError("off-diagonal Torch similarities must be finite")
    neighbors = torch_module.argsort(masked, dim=-1, descending=True, stable=True)[
        :, : selected_policy.topk
    ]
    targets = torch_module.arange(masked.shape[0], device=masked.device).unsqueeze(1)
    if bool((neighbors == targets).any()):
        raise GDNV2NeighborError("Torch self identity survived V2 exclusion")
    return neighbors


def _require_exact_runtime_dependencies_v2() -> None:
    status = build_dependency_status_v1((inspect_current_dependency_environment_v1(),))
    if not status.exact_backend_available:
        raise UpstreamGDNDependencyError(
            "GDN_OPTIONAL_DEPENDENCY_UNAVAILABLE: exact torch==2.12.1 and "
            "torch-geometric==2.8.0 are required"
        )


def _load_runtime_types_v2() -> tuple[Any, Any, Any]:
    """Define the corrected V2 model after exact optional-dependency approval."""

    _require_exact_runtime_dependencies_v2()
    import torch
    import torch.nn.functional as functional
    from torch import nn
    from torch.nn import Parameter
    from torch_geometric.nn.conv import MessagePassing
    from torch_geometric.nn.inits import glorot, zeros
    from torch_geometric.utils import add_self_loops, remove_self_loops

    class GraphLayer(MessagePassing):
        def __init__(self, in_channels: int, out_channels: int, *, heads: int = 1, concat: bool = True, negative_slope: float = 0.2, dropout: float = 0.0, bias: bool = True) -> None:
            super().__init__(aggr="add", node_dim=0)
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
            alpha = upstream_sparse_softmax_compat_v1(alpha, edge_index_i, size_i)
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

    class UpstreamAlignedGDNV2(nn.Module):
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
            topk_indices = stable_torch_neighbors_v2(cosine, torch_module=torch)
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

    return torch, nn, UpstreamAlignedGDNV2


def _segment_windows_v2(segments: Sequence[Sequence[Sequence[float]]], config: UpstreamGDNTrainingConfigV1) -> tuple[list[list[list[float]]], list[list[float]]]:
    windows: list[list[list[float]]] = []
    targets: list[list[float]] = []
    for segment in segments:
        for stop in range(config.slide_window, len(segment), config.slide_stride):
            history = segment[stop - config.slide_window : stop]
            node_major = [[float(history[t][node]) for t in range(config.slide_window)] for node in range(len(segment[0]))]
            windows.append(node_major)
            targets.append([float(value) for value in segment[stop]])
    if not windows:
        raise UpstreamGDNDataBoundaryError("no V2 GDN windows were produced")
    return windows, targets


def _set_all_seeds_v2(torch_module: Any, seed: int) -> None:
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    torch_module.manual_seed(seed)
    if torch_module.cuda.is_available():
        torch_module.cuda.manual_seed(seed)
        torch_module.cuda.manual_seed_all(seed)
    if hasattr(torch_module.backends, "cudnn"):
        torch_module.backends.cudnn.benchmark = False
        torch_module.backends.cudnn.deterministic = True


@dataclass(frozen=True)
class _TrainedSeedGraphV2Internal:
    result: TrainedSeedGraphV1
    forward_internal_graph_hash: str
    extraction_internal_graph_hash: str


def _train_upstream_aligned_seed_v2(
    *,
    segments: Sequence[Sequence[Sequence[float]]],
    feature_order: Sequence[str],
    candidate_pairs: Sequence[tuple[str, str]],
    seed: int,
    config: UpstreamGDNTrainingConfigV1,
) -> _TrainedSeedGraphV2Internal:
    """Run one corrected V2 seed; no checkpoint is persisted by this primitive."""

    if seed not in FROZEN_SEEDS or config.seeds != FROZEN_SEEDS:
        raise UpstreamGDNFidelityError("V2 seed policy changed")
    feature_tuple = tuple(feature_order)
    if len(feature_tuple) <= config.learned_graph_topk:
        raise UpstreamGDNFidelityError("feature context must exceed Top-K")
    pair_set = set(candidate_pairs)
    if any(source not in feature_tuple or target not in feature_tuple for source, target in pair_set):
        raise UpstreamGDNDataBoundaryError("candidate projection is outside model context")
    torch, nn, model_type = _load_runtime_types_v2()
    _set_all_seeds_v2(torch, seed)
    windows, targets = _segment_windows_v2(segments, config)
    x = torch.tensor(windows, dtype=torch.float32)
    y = torch.tensor(targets, dtype=torch.float32)
    dataset = torch.utils.data.TensorDataset(x, y)
    dataset_length = len(dataset)
    train_length = int(dataset_length * (1.0 - config.validation_ratio))
    validation_length = int(dataset_length * config.validation_ratio)
    if train_length <= 0 or validation_length <= 0:
        raise UpstreamGDNDataBoundaryError("V2 validation split is empty")
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
        raise UpstreamGDNError("failed_gdn_training: no finite V2 validation state")
    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        model(x[:1].to(config.device), original_edges.to(config.device))
    if model.learned_graph is None:
        raise UpstreamGDNFidelityError("V2 forward graph was not materialized")
    forward_indices = tuple(
        tuple(int(value) for value in row)
        for row in model.learned_graph.detach().cpu().tolist()
    )
    forward_internal_graph_hash = stable_hash_v1({"neighbor_indices": forward_indices})
    weights = model.embedding.weight.detach()
    cosine = torch.matmul(weights, weights.T)
    norms = torch.matmul(weights.norm(dim=-1).view(-1, 1), weights.norm(dim=-1).view(1, -1))
    cosine = cosine / norms
    topk_indices = stable_torch_neighbors_v2(cosine, torch_module=torch)
    extraction_indices = tuple(
        tuple(int(value) for value in row)
        for row in topk_indices.detach().cpu().tolist()
    )
    extraction_internal_graph_hash = stable_hash_v1({"neighbor_indices": extraction_indices})
    if forward_internal_graph_hash != extraction_internal_graph_hash:
        raise UpstreamGDNFidelityError("V2 forward and extraction neighbor graphs diverged")
    name_to_index = {name: index for index, name in enumerate(feature_tuple)}
    selected = set()
    for target_index in range(len(feature_tuple)):
        target = feature_tuple[target_index]
        for source_index in topk_indices[target_index].tolist():
            pair = (feature_tuple[int(source_index)], target)
            if pair in pair_set:
                selected.add(pair)
    similarities = {pair: float(cosine[name_to_index[pair[1]], name_to_index[pair[0]]].item()) for pair in pair_set}
    return _TrainedSeedGraphV2Internal(
        result=TrainedSeedGraphV1(
            seed=seed,
            selected_edges=tuple(sorted(selected)),
            candidate_similarities=similarities,
            epoch_count=completed_epochs,
            best_validation_loss=best_loss,
            hyperparameter_hash=config.hyperparameter_hash,
        ),
        forward_internal_graph_hash=forward_internal_graph_hash,
        extraction_internal_graph_hash=extraction_internal_graph_hash,
    )


@dataclass(frozen=True)
class Exp01RunAuthorizationV2:
    preregistration_hash: str
    data_authority_hash: str
    feature_contract_hash: str
    candidate_universe_hash: str
    training_config_hash: str
    neighbor_policy_hash: str
    source_commit: str
    split_roles: tuple[str, ...] = ("train1", "train2")
    labels_authorized: bool = False
    test1_authorized: bool = False
    test2_authorized: bool = False
    heldout_authorized: bool = False
    schema: str = EXP01_RUN_AUTH_SCHEMA_V2
    schema_version: str = "2.0.0"
    authorization_hash: str = ""

    def __post_init__(self) -> None:
        for name in (
            "preregistration_hash", "data_authority_hash", "feature_contract_hash",
            "candidate_universe_hash", "training_config_hash", "neighbor_policy_hash",
        ):
            require_sha256(getattr(self, name), name)
        if len(self.source_commit) != 40 or any(character not in "0123456789abcdef" for character in self.source_commit):
            raise GDNV2NeighborError("source_commit must be a full lowercase Git SHA")
        if self.split_roles != ("train1", "train2"):
            raise GDNV2NeighborError("EXP-01 fit authorization requires train1 and train2 only")
        for name in ("labels_authorized", "test1_authorized", "test2_authorized", "heldout_authorized"):
            _strict_bool(getattr(self, name), name)
            if getattr(self, name):
                raise GDNV2NeighborError("EXP-01 fit authorization forbids labels and test partitions")
        if self.schema != EXP01_RUN_AUTH_SCHEMA_V2 or self.schema_version != "2.0.0":
            raise GDNV2NeighborError("EXP-01 run authorization schema changed")
        if self.authorization_hash:
            require_sha256(self.authorization_hash, "authorization_hash")
            if self.authorization_hash != stable_hash_v1(self.to_dict(include_hash=False)):
                raise GDNV2NeighborError("EXP-01 run authorization replay mismatch")

    def to_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        document: dict[str, object] = {
            "schema": self.schema,
            "schema_version": self.schema_version,
            "preregistration_hash": self.preregistration_hash,
            "data_authority_hash": self.data_authority_hash,
            "feature_contract_hash": self.feature_contract_hash,
            "candidate_universe_hash": self.candidate_universe_hash,
            "training_config_hash": self.training_config_hash,
            "neighbor_policy_hash": self.neighbor_policy_hash,
            "source_commit": self.source_commit,
            "split_roles": list(self.split_roles),
            "labels_authorized": self.labels_authorized,
            "test1_authorized": self.test1_authorized,
            "test2_authorized": self.test2_authorized,
            "heldout_authorized": self.heldout_authorized,
        }
        if include_hash:
            document["authorization_hash"] = self.authorization_hash
        return document


def build_exp01_run_authorization_v2(**values: object) -> Exp01RunAuthorizationV2:
    provisional = Exp01RunAuthorizationV2(**values)
    return Exp01RunAuthorizationV2(
        **{**provisional.__dict__, "authorization_hash": stable_hash_v1(provisional.to_dict(include_hash=False))}
    )


@dataclass(frozen=True)
class Exp01AuthorizedTrainingInputV2:
    segments: tuple[tuple[tuple[float, ...], ...], ...]
    feature_order: tuple[str, ...]
    candidate_pairs: tuple[tuple[str, str], ...]
    data_authority_hash: str
    feature_contract_hash: str
    candidate_universe_hash: str
    schema: str = EXP01_TRAINING_INPUT_SCHEMA_V2
    schema_version: str = "2.0.0"
    input_hash: str = ""

    def __post_init__(self) -> None:
        for name in ("data_authority_hash", "feature_contract_hash", "candidate_universe_hash"):
            require_sha256(getattr(self, name), name)
        if self.schema != EXP01_TRAINING_INPUT_SCHEMA_V2 or self.schema_version != "2.0.0":
            raise GDNV2NeighborError("EXP-01 training-input schema changed")
        if not self.segments or not self.feature_order or len(set(self.feature_order)) != len(self.feature_order):
            raise GDNV2NeighborError("authorized EXP-01 input is incomplete")
        if len(self.candidate_pairs) != len(set(self.candidate_pairs)):
            raise GDNV2NeighborError("candidate pairs contain duplicates")
        if any(len(row) != len(self.feature_order) for segment in self.segments for row in segment):
            raise GDNV2NeighborError("authorized segment width does not match feature authority")
        if any(not math.isfinite(float(value)) for segment in self.segments for row in segment for value in row):
            raise GDNV2NeighborError("authorized segment contains non-finite values")
        expected = stable_hash_v1({
            "schema": self.schema,
            "schema_version": self.schema_version,
            "segments": self.segments,
            "feature_order": self.feature_order,
            "candidate_pairs": self.candidate_pairs,
            "data_authority_hash": self.data_authority_hash,
            "feature_contract_hash": self.feature_contract_hash,
            "candidate_universe_hash": self.candidate_universe_hash,
        })
        if self.input_hash:
            require_sha256(self.input_hash, "input_hash")
            if self.input_hash != expected:
                raise GDNV2NeighborError("authorized training input replay mismatch")

    def to_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        document: dict[str, object] = {
            "schema": self.schema,
            "schema_version": self.schema_version,
            "segments": [[list(row) for row in segment] for segment in self.segments],
            "feature_order": list(self.feature_order),
            "candidate_pairs": [list(pair) for pair in self.candidate_pairs],
            "data_authority_hash": self.data_authority_hash,
            "feature_contract_hash": self.feature_contract_hash,
            "candidate_universe_hash": self.candidate_universe_hash,
        }
        if include_hash:
            document["input_hash"] = self.input_hash
        return document


def build_exp01_authorized_training_input_v2(**values: object) -> Exp01AuthorizedTrainingInputV2:
    provisional = Exp01AuthorizedTrainingInputV2(**values)
    expected = stable_hash_v1({
        "schema": provisional.schema,
        "schema_version": provisional.schema_version,
        "segments": provisional.segments,
        "feature_order": provisional.feature_order,
        "candidate_pairs": provisional.candidate_pairs,
        "data_authority_hash": provisional.data_authority_hash,
        "feature_contract_hash": provisional.feature_contract_hash,
        "candidate_universe_hash": provisional.candidate_universe_hash,
    })
    return Exp01AuthorizedTrainingInputV2(**{**provisional.__dict__, "input_hash": expected})


@dataclass(frozen=True)
class Exp01SeedRunReceiptV2:
    seed: int
    preregistration_hash: str
    authorization_hash: str
    input_hash: str
    neighbor_policy_hash: str
    training_config_hash: str
    forward_internal_graph_hash: str
    extraction_internal_graph_hash: str
    selected_edges: tuple[tuple[str, str], ...]
    candidate_similarities: tuple[tuple[str, str, float], ...]
    epoch_count: int
    best_validation_loss: float
    graph_hash: str
    schema: str = EXP01_SEED_RECEIPT_SCHEMA_V2
    schema_version: str = "2.0.0"
    receipt_hash: str = ""

    def __post_init__(self) -> None:
        if self.seed not in FROZEN_SEEDS or self.epoch_count <= 0 or not math.isfinite(self.best_validation_loss):
            raise GDNV2NeighborError("V2 seed run completion is invalid")
        if self.schema != EXP01_SEED_RECEIPT_SCHEMA_V2 or self.schema_version != "2.0.0":
            raise GDNV2NeighborError("EXP-01 seed receipt schema changed")
        for name in (
            "preregistration_hash", "authorization_hash", "input_hash", "neighbor_policy_hash",
            "training_config_hash", "forward_internal_graph_hash", "extraction_internal_graph_hash", "graph_hash",
        ):
            require_sha256(getattr(self, name), name)
        if self.forward_internal_graph_hash != self.extraction_internal_graph_hash:
            raise GDNV2NeighborError("V2 forward and extraction graph bindings differ")
        if len(self.selected_edges) != len(set(self.selected_edges)):
            raise GDNV2NeighborError("V2 seed receipt contains duplicate edges")
        if self.graph_hash != stable_hash_v1({"selected_edges": self.selected_edges, "candidate_similarities": self.candidate_similarities}):
            raise GDNV2NeighborError("V2 seed graph replay mismatch")
        if self.receipt_hash:
            require_sha256(self.receipt_hash, "receipt_hash")
            if self.receipt_hash != stable_hash_v1(self.to_dict(include_hash=False)):
                raise GDNV2NeighborError("V2 seed receipt replay mismatch")

    def to_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        document = {name: getattr(self, name) for name in (
            "schema", "schema_version", "seed", "preregistration_hash", "authorization_hash", "input_hash", "neighbor_policy_hash",
            "training_config_hash", "forward_internal_graph_hash", "extraction_internal_graph_hash",
            "selected_edges", "candidate_similarities", "epoch_count",
            "best_validation_loss", "graph_hash",
        )}
        document["selected_edges"] = [list(pair) for pair in self.selected_edges]
        document["candidate_similarities"] = [list(row) for row in self.candidate_similarities]
        if include_hash:
            document["receipt_hash"] = self.receipt_hash
        return document


def train_authorized_upstream_aligned_seed_v2(
    *, authorization: Exp01RunAuthorizationV2, inputs: Exp01AuthorizedTrainingInputV2,
    seed: int, config: UpstreamGDNTrainingConfigV1,
) -> Exp01SeedRunReceiptV2:
    if not authorization.authorization_hash or not inputs.input_hash:
        raise GDNV2NeighborError("self-hashed authorization and input are required")
    if authorization.data_authority_hash != inputs.data_authority_hash or authorization.feature_contract_hash != inputs.feature_contract_hash or authorization.candidate_universe_hash != inputs.candidate_universe_hash:
        raise GDNV2NeighborError("EXP-01 run authority does not bind the supplied input")
    if authorization.training_config_hash != config.hyperparameter_hash:
        raise GDNV2NeighborError("EXP-01 training config authority mismatch")
    if authorization.neighbor_policy_hash != GDNNeighborPolicyV2().policy_hash:
        raise GDNV2NeighborError("EXP-01 neighbor policy authority mismatch")
    result = _train_upstream_aligned_seed_v2(
        segments=inputs.segments, feature_order=inputs.feature_order,
        candidate_pairs=inputs.candidate_pairs, seed=seed, config=config,
    )
    trained = result.result
    similarities = tuple(sorted((source, target, float(value)) for (source, target), value in trained.candidate_similarities.items()))
    graph_hash = stable_hash_v1({"selected_edges": trained.selected_edges, "candidate_similarities": similarities})
    provisional = Exp01SeedRunReceiptV2(
        seed=seed, preregistration_hash=authorization.preregistration_hash,
        authorization_hash=authorization.authorization_hash, input_hash=inputs.input_hash,
        neighbor_policy_hash=authorization.neighbor_policy_hash,
        training_config_hash=authorization.training_config_hash,
        forward_internal_graph_hash=result.forward_internal_graph_hash,
        extraction_internal_graph_hash=result.extraction_internal_graph_hash,
        selected_edges=trained.selected_edges, candidate_similarities=similarities,
        epoch_count=trained.epoch_count, best_validation_loss=trained.best_validation_loss,
        graph_hash=graph_hash,
    )
    return Exp01SeedRunReceiptV2(**{**provisional.__dict__, "receipt_hash": stable_hash_v1(provisional.to_dict(include_hash=False))})


__all__ = [
    "GDNNeighborPolicyV2",
    "EXP01_RUN_AUTH_SCHEMA_V2",
    "EXP01_TRAINING_INPUT_SCHEMA_V2",
    "EXP01_SEED_RECEIPT_SCHEMA_V2",
    "Exp01AuthorizedTrainingInputV2",
    "Exp01RunAuthorizationV2",
    "Exp01SeedRunReceiptV2",
    "GDNV2NeighborError",
    "GDN_V2_BACKEND_STATUS",
    "GDN_V2_NEIGHBOR_POLICY",
    "select_self_excluded_neighbors_v2",
    "stable_torch_neighbors_v2",
    "build_exp01_authorized_training_input_v2",
    "build_exp01_run_authorization_v2",
    "train_authorized_upstream_aligned_seed_v2",
]
