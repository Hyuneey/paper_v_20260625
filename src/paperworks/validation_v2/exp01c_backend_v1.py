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

from paperworks.gdn.upstream_candidate_backend_v2 import (
    _load_runtime_types_v2,
    stable_torch_neighbors_v2,
)
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
    torch, nn, base_type = _load_runtime_types_v2()
    adapter = _config_adapter(config)

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
            targets.append(segment[start:start + 3].median(dim=0).values)
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
) -> tuple[tuple[Any, ...], dict[str, Any]]:
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
    return transformed, receipt


def _all_edges(torch: Any, node_count: int, device: str) -> Any:
    return torch.tensor(
        [[source for target in range(node_count) for source in range(node_count) if source != target],
         [target for target in range(node_count) for source in range(node_count) if source != target]],
        dtype=torch.long, device=device,
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
    transformed, scaler_receipt = _fit_scaler_and_transform(
        arrays, train_indices=plan.train_window_indices,
        policy=preprocessing_policy, config=config,
    )
    torch, nn, model_type = _model_type_v1(config)
    _set_determinism(torch, seed)
    train_dataset = _MultiHorizonDataset(
        transformed, plan.train_window_indices, config=config, torch_module=torch,
    )
    validation_dataset = _MultiHorizonDataset(
        transformed, plan.validation_window_indices, config=config, torch_module=torch,
    )
    generator = torch.Generator().manual_seed(seed)
    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=config.batch_size, shuffle=True, generator=generator,
    )
    validation_loader = torch.utils.data.DataLoader(
        validation_dataset, batch_size=config.batch_size, shuffle=False,
    )
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
        for x, y, _file_index, _stop in train_loader:
            optimizer.zero_grad()
            prediction = model(x.to(config.device), graph)
            loss = ((prediction - y.to(config.device)) ** 2).mean()
            if not bool(torch.isfinite(loss)):
                raise Exp01CBackendError("training loss is non-finite")
            loss.backward()
            optimizer.step()
        model.eval()
        squared = 0.0
        cells = 0
        with torch.no_grad():
            for x, y, _file_index, _stop in validation_loader:
                prediction = model(x.to(config.device), graph)
                squared += float(((prediction - y.to(config.device)) ** 2).sum().item())
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
    first_x, _, _, _ = train_dataset[0]
    with torch.no_grad():
        model(first_x.unsqueeze(0).to(config.device), graph)
    if model.learned_graph is None:
        raise Exp01CBackendError("learned graph was not materialized")
    graph_edges = _graph_from_indices(order, model.learned_graph)
    if len(graph_edges) != len(set(graph_edges)) or any(source == target for source, target in graph_edges):
        raise Exp01CBackendError("corrected learned graph is invalid")
    return Exp01CTrainingResultV1(
        state_dict=best_state, graph_edges=graph_edges,
        graph_hash=stable_hash_v1({"graph_edges": graph_edges}),
        best_validation_loss=best_loss, completed_epochs=completed,
        train_window_count=len(train_dataset),
        validation_window_count=len(validation_dataset),
        raw_timestamp_overlap_count=plan.raw_timestamp_overlap_count,
        validation_blocks=plan.validation_blocks,
        scaler_receipt=scaler_receipt,
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
