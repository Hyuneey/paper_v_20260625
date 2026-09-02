"""EXP-01B device adapter and fixed-checkpoint Torch evidence backend.

Torch remains an optional runtime dependency.  Importing this module performs
no device discovery, data access, training, or checkpoint I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import os
from typing import Any, Mapping, Sequence

from paperworks.gdn.exp01_upstream_backend_v2 import (
    Exp01BackendTrainingResultV2,
    _FileLocalLazyWindows,
    _edge_index_from_graph,
    _graph_from_indices,
    _predict_with_fixed_graph,
    train_exp01_seed_v2,
)
from paperworks.gdn.upstream_candidate_backend_v2 import (
    _load_runtime_types_v2,
    stable_torch_neighbors_v2,
)
from paperworks.validation_v2.exp01_scientific_v1 import (
    ArmId,
    PAIR_UNIVERSE,
    SOURCE_VARIABLES,
    TARGET_VARIABLES,
)
from paperworks.validation_v2.exp01b_contract_v1 import (
    ATTENTION_ATOL,
    ATTENTION_RTOL,
    Exp01BTrainingConfigV1,
    FUNCTIONAL_BATCH_EQUIVALENCE_ATOL,
    FUNCTIONAL_BATCH_EQUIVALENCE_RTOL,
    FUNCTIONAL_VARIANT_CHUNK_SIZE,
    REQUIRED_CUBLAS_WORKSPACE_CONFIG,
    REQUIRED_PYTHONHASHSEED,
)
from paperworks.validation_v2.exp01b_functional_v1 import (
    file_local_block_permutation_v1,
    occlusion_seed_v1,
    relative_delta_mse_v1,
)
from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER


class Exp01BBackendError(RuntimeError):
    pass


class AttentionArmUnavailableError(Exp01BBackendError):
    pass


def aggregate_attention_from_augmented_edges_v1(
    *, augmented_edges: Sequence[tuple[int, int]], alpha_values: Sequence[float],
    node_count: int, feature_order: Sequence[str],
    graph_edges: Sequence[tuple[str, str]], batch_size: int,
) -> dict[tuple[str, str], float]:
    """Map captured alpha by explicit augmented edge identity, excluding self loops."""

    if len(augmented_edges) != len(alpha_values) or node_count != len(feature_order):
        raise AttentionArmUnavailableError("attention edge/value dimensions differ")
    positions = {name: index for index, name in enumerate(feature_order)}
    edge_by_index = {
        (positions[source], positions[target]): (source, target)
        for source, target in graph_edges
    }
    sums = {edge: 0.0 for edge in graph_edges}
    counts = {edge: 0 for edge in graph_edges}
    for (raw_source, raw_target), raw_alpha in zip(augmented_edges, alpha_values):
        source, target = raw_source % node_count, raw_target % node_count
        if source == target:
            continue
        edge = edge_by_index.get((source, target))
        if edge is None:
            raise AttentionArmUnavailableError("augmented attention edge is not in the frozen graph")
        value = float(raw_alpha)
        if not math.isfinite(value):
            raise AttentionArmUnavailableError("attention value is non-finite")
        sums[edge] += value
        counts[edge] += 1
    if any(counts[edge] != batch_size for edge in graph_edges):
        raise AttentionArmUnavailableError("explicit attention edge multiplicity mismatch")
    return {edge: sums[edge] / batch_size for edge in graph_edges}


def aggregate_attention_from_augmented_tensors_v2(
    *, torch_module: Any, augmented_edges: Any, alpha_values: Any,
    node_count: int, feature_order: Sequence[str],
    graph_edges: Sequence[tuple[str, str]], batch_size: int,
) -> dict[tuple[str, str], float]:
    """Vectorized equivalent of the audited explicit-edge aggregation.

    The V1 implementation transferred every augmented edge and alpha value
    separately from CUDA.  That introduced thousands of synchronization
    points per batch.  This adapter validates the same explicit identities on
    device, performs one bulk transfer, and retains the V1 Python-float
    accumulation order for each frozen edge.
    """

    if (
        node_count != len(feature_order)
        or batch_size <= 0
        or int(augmented_edges.ndim) != 2
        or int(augmented_edges.shape[0]) != 2
        or int(alpha_values.shape[0]) != int(augmented_edges.shape[1])
    ):
        raise AttentionArmUnavailableError("attention edge/value dimensions differ")
    edges = tuple(graph_edges)
    if not edges or len(edges) != len(set(edges)):
        raise AttentionArmUnavailableError("frozen graph edge identities are invalid")
    positions = {name: index for index, name in enumerate(feature_order)}
    try:
        graph_codes = tuple(
            positions[source] * node_count + positions[target]
            for source, target in edges
        )
    except KeyError as exc:
        raise AttentionArmUnavailableError("frozen graph edge is outside feature order") from exc
    if len(graph_codes) != len(set(graph_codes)):
        raise AttentionArmUnavailableError("frozen graph local edge identities collide")

    device = alpha_values.device
    augmented = augmented_edges.to(device=device, dtype=torch_module.long)
    raw_source, raw_target = augmented[0], augmented[1]
    source_batch = torch_module.div(raw_source, node_count, rounding_mode="floor")
    target_batch = torch_module.div(raw_target, node_count, rounding_mode="floor")
    if bool(torch_module.any(source_batch != target_batch)):
        raise AttentionArmUnavailableError("augmented attention crosses batch graphs")
    source_local = torch_module.remainder(raw_source, node_count)
    target_local = torch_module.remainder(raw_target, node_count)
    non_self = source_local != target_local

    lookup = torch_module.full(
        (node_count * node_count,), -1, dtype=torch_module.long, device=device,
    )
    code_tensor = torch_module.tensor(graph_codes, dtype=torch_module.long, device=device)
    lookup[code_tensor] = torch_module.arange(len(edges), dtype=torch_module.long, device=device)
    active_codes = source_local[non_self] * node_count + target_local[non_self]
    graph_ids = lookup[active_codes]
    if bool(torch_module.any(graph_ids < 0)):
        raise AttentionArmUnavailableError("augmented attention edge is not in the frozen graph")
    slots = source_batch[non_self] * len(edges) + graph_ids
    expected_count = batch_size * len(edges)
    if int(slots.numel()) != expected_count:
        raise AttentionArmUnavailableError("explicit attention edge multiplicity mismatch")
    ordered_slots, order = torch_module.sort(slots)
    if not bool(torch_module.equal(
        ordered_slots,
        torch_module.arange(expected_count, dtype=torch_module.long, device=device),
    )):
        raise AttentionArmUnavailableError("explicit attention edge identities are incomplete")

    alpha = alpha_values.detach().reshape(int(alpha_values.shape[0]), -1).mean(dim=1)
    active_alpha = alpha[non_self]
    if not bool(torch_module.all(torch_module.isfinite(active_alpha))):
        raise AttentionArmUnavailableError("attention value is non-finite")
    # One device-to-host synchronization replaces one .item() per augmented
    # edge.  Sorting by (batch, graph edge) preserves the V1 accumulation order.
    by_edge = active_alpha[order].reshape(batch_size, len(edges)).T.cpu().tolist()
    return {
        edge: sum(float(value) for value in values) / batch_size
        for edge, values in zip(edges, by_edge)
    }


@dataclass(frozen=True)
class Exp01BDeviceTrainingConfigV1:
    """Device-only adapter over the preregistered audited configuration."""

    device: str
    seeds: tuple[int, ...] = (11, 23, 37)
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
    preprocessing: str = "raw_numeric_values_no_scaling_windows_do_not_cross_files"
    validation_policy: str = "upstream_seeded_contiguous_random_validation_block"
    checkpoint_policy: str = "minimum_validation_loss_in_memory_state_dict"
    functional_variant_chunk_size: int = FUNCTIONAL_VARIANT_CHUNK_SIZE

    def __post_init__(self) -> None:
        if self.device not in {"cuda", "cpu"}:
            raise Exp01BBackendError("EXP-01B device must be frozen to cuda or cpu")
        expected = Exp01BTrainingConfigV1().to_document()
        observed = self.to_document()
        for key, value in expected.items():
            if key in {"views"}:
                continue
            if observed.get(key) != value:
                raise Exp01BBackendError(f"audited training semantic changed: {key}")
        if self.out_layer_inter_dim != 128:
            raise Exp01BBackendError("audited out-layer width changed")
        if self.functional_variant_chunk_size != FUNCTIONAL_VARIANT_CHUNK_SIZE:
            raise Exp01BBackendError("functional variant chunk changed after preregistration")

    def to_document(self) -> dict[str, Any]:
        return {
            "seeds": list(self.seeds), "batch_size": self.batch_size,
            "epochs": self.epochs, "slide_window": self.slide_window,
            "slide_stride": self.slide_stride, "embedding_dim": self.embedding_dim,
            "out_layer_num": self.out_layer_num, "out_layer_inter_dim": self.out_layer_inter_dim,
            "learned_graph_topk": self.learned_graph_topk,
            "validation_ratio": self.validation_ratio, "learning_rate": self.learning_rate,
            "weight_decay": self.weight_decay,
            "early_stopping_patience": self.early_stopping_patience,
            "dropout": self.dropout, "device": self.device,
            "dtype": "float32", "corrected_neighbor_policy": "SELF_EXCLUDED_STABLE_TOPK_V1",
            "preprocessing": self.preprocessing, "validation_policy": self.validation_policy,
            "checkpoint_policy": self.checkpoint_policy,
            "functional_variant_chunk_size": self.functional_variant_chunk_size,
        }

    @property
    def hyperparameter_hash(self) -> str:
        return Exp01BTrainingConfigV1().training_config_hash

    @property
    def execution_backend_hash(self) -> str:
        return stable_hash_v1(self.to_document())


@dataclass(frozen=True)
class Exp01BCheckpointEvidenceV1:
    embedding_scores: Mapping[tuple[str, str], float]
    attention_scores: Mapping[tuple[str, str], float] | None
    edge_mask_scores: Mapping[tuple[str, str], float]
    edge_mask_control_scores: Mapping[tuple[str, str], float]
    occlusion_scores: Mapping[tuple[str, str], float]
    attention_invariance_passed: bool


@dataclass(frozen=True)
class Exp01BLineageEvidenceV1:
    """Minimal fixed-checkpoint evidence used to close public audit lineage.

    This adapter intentionally excludes training, full EdgeMask evaluation, and
    source occlusion.  Those scientific outputs were already frozen by the
    original run.  It recovers only embedding/attention rankings and graph
    identity from the immutable checkpoint.
    """

    embedding_scores: Mapping[tuple[str, str], float]
    attention_scores: Mapping[tuple[str, str], float]
    attention_invariance_passed: bool
    graph_edges: tuple[tuple[str, str], ...]
    graph_hash: str


def train_exp01b_seed_v1(
    *, segments: Sequence[Any], feature_order: Sequence[str], seed: int,
    config: Exp01BDeviceTrainingConfigV1,
) -> Exp01BackendTrainingResultV2:
    return train_exp01_seed_v2(
        arm_id=ArmId.CORRECTED_SELF_EXCLUDED,
        segments=segments,
        feature_order=feature_order,
        candidate_pairs=PAIR_UNIVERSE,
        seed=seed,
        config=config,  # type: ignore[arg-type] -- exact device-only V2 adapter
    )


def replay_exp01b_graph_v1(
    *, state_dict: Mapping[str, Any], feature_order: Sequence[str],
    config: Exp01BDeviceTrainingConfigV1,
) -> tuple[tuple[tuple[str, str], ...], str]:
    """Reconstruct the corrected self-excluded Top-5 graph from a checkpoint."""

    torch, _, model_type = _load_runtime_types_v2()
    order = tuple(feature_order)
    model = model_type(len(order), config).to(config.device)
    model.load_state_dict(state_dict, strict=True)
    model.eval()
    weights = model.embedding.weight.detach()
    cosine = torch.matmul(weights, weights.T)
    norms = torch.matmul(
        weights.norm(dim=-1).view(-1, 1),
        weights.norm(dim=-1).view(1, -1),
    )
    if bool(torch.any(norms <= 0)):
        raise Exp01BBackendError("checkpoint embedding norm is non-positive")
    indices = stable_torch_neighbors_v2(cosine / norms, torch_module=torch)
    graph = _graph_from_indices(order, indices.detach().cpu())
    if len(graph) != len(set(graph)) or any(source == target for source, target in graph):
        raise Exp01BBackendError("replayed checkpoint graph is invalid")
    return graph, stable_hash_v1({"graph_edges": graph})


def evaluate_exp01b_lineage_v1(
    *, state_dict: Mapping[str, Any], train4_segments: Sequence[Any],
    feature_order: Sequence[str], expected_graph_hash: str,
    config: Exp01BDeviceTrainingConfigV1,
) -> Exp01BLineageEvidenceV1:
    """Recover embedding/attention evidence without retraining a checkpoint."""

    order = tuple(feature_order)
    graph, graph_hash = replay_exp01b_graph_v1(
        state_dict=state_dict, feature_order=order, config=config,
    )
    if graph_hash != expected_graph_hash:
        raise Exp01BBackendError("replayed checkpoint graph hash differs")
    torch, model, loader, _ = _model_and_loader(
        state_dict=state_dict, segments=train4_segments,
        feature_order=order, config=config,
    )
    graph_index = _edge_index_from_graph(torch, order, graph)
    target_positions = tuple(order.index(name) for name in TARGET_VARIABLES)
    _, raw_attention = _target_mse_and_attention(
        torch=torch, model=model, loader=loader,
        graph_edge_index=graph_index, graph_edges=graph,
        target_positions=target_positions, capture_attention=True,
        feature_order=order,
    )
    if raw_attention is None:
        raise AttentionArmUnavailableError("attention lineage replay is unavailable")
    graph_set = set(graph)
    attention = {
        pair: float(raw_attention[pair])
        for pair in PAIR_UNIVERSE
        if pair in graph_set
    }
    return Exp01BLineageEvidenceV1(
        embedding_scores=_embedding_scores(
            torch=torch, model=model, feature_order=order,
        ),
        attention_scores=attention,
        attention_invariance_passed=True,
        graph_edges=graph,
        graph_hash=graph_hash,
    )


def evaluate_selected_edge_masks_v1(
    *, state_dict: Mapping[str, Any], train4_segments: Sequence[Any],
    feature_order: Sequence[str], graph_edges: Sequence[tuple[str, str]],
    selected_edges: Sequence[tuple[str, str]],
    config: Exp01BDeviceTrainingConfigV1,
) -> dict[tuple[str, str], float]:
    """Evaluate a preregistered subset of fixed-graph EdgeMask controls."""

    order = tuple(feature_order)
    graph = tuple(graph_edges)
    selected = tuple(selected_edges)
    if (
        len(selected) != len(set(selected))
        or any(edge not in graph for edge in selected)
        or any(edge[1] not in TARGET_VARIABLES for edge in selected)
    ):
        raise Exp01BBackendError("selected EdgeMask control set is invalid")
    if not selected:
        return {}
    torch, model, loader, _ = _model_and_loader(
        state_dict=state_dict, segments=train4_segments,
        feature_order=order, config=config,
    )
    graph_index = _edge_index_from_graph(torch, order, graph)
    target_positions = tuple(order.index(name) for name in TARGET_VARIABLES)
    baseline_mse, _ = _target_mse_and_attention(
        torch=torch, model=model, loader=loader,
        graph_edge_index=graph_index, graph_edges=graph,
        target_positions=target_positions, capture_attention=False,
        feature_order=order,
    )
    replay_loader = torch.utils.data.DataLoader(
        loader.dataset, batch_size=config.batch_size, shuffle=False,
    )
    graphs = tuple(tuple(item for item in graph if item != edge) for edge in selected)
    graph_indices = tuple(
        _edge_index_from_graph(torch, order, item).to(config.device)
        for item in graphs
    )
    squared = [0.0] * len(selected)
    count = 0
    positions = {name: index for index, name in enumerate(order)}
    with torch.no_grad():
        for batch_x, batch_y in replay_loader:
            batch_x = batch_x.to(config.device)
            batch_y = batch_y.to(config.device)
            batch_count = int(batch_x.shape[0])
            for start in range(0, len(selected), config.functional_variant_chunk_size):
                stop = min(len(selected), start + config.functional_variant_chunk_size)
                variant_x = batch_x.unsqueeze(0).expand(stop - start, -1, -1, -1)
                predictions = _predict_with_variant_graphs(
                    torch=torch, model=model, data=variant_x,
                    variant_graph_indices=graph_indices[start:stop],
                    node_count=len(order),
                )
                for local, edge in enumerate(selected[start:stop]):
                    target_index = positions[edge[1]]
                    squared[start + local] += float(
                        ((predictions[local, :, target_index] - batch_y[:, target_index]) ** 2)
                        .sum().item()
                    )
            count += batch_count
    if count <= 0:
        raise Exp01BBackendError("selected EdgeMask denominator is empty")
    return {
        edge: relative_delta_mse_v1(
            baseline_target_mse=baseline_mse[positions[edge[1]]],
            masked_target_mse=squared[index] / count,
        )
        for index, edge in enumerate(selected)
    }


def configure_and_smoke_exp01b_backend_v1(
    *, torch_module: Any, config: Exp01BDeviceTrainingConfigV1,
) -> dict[str, object]:
    """Verify launch-time determinism and a full synthetic train step."""

    if os.environ.get("CUBLAS_WORKSPACE_CONFIG") != REQUIRED_CUBLAS_WORKSPACE_CONFIG:
        raise Exp01BBackendError("CUBLAS_WORKSPACE_CONFIG must be fixed before interpreter launch")
    if os.environ.get("PYTHONHASHSEED") != REQUIRED_PYTHONHASHSEED:
        raise Exp01BBackendError("PYTHONHASHSEED must be fixed before interpreter launch")
    torch_module.use_deterministic_algorithms(True)
    torch_module.backends.cudnn.deterministic = True
    torch_module.backends.cudnn.benchmark = False
    torch_module.backends.cuda.matmul.allow_tf32 = False
    torch_module.backends.cudnn.allow_tf32 = False
    torch, nn, model_type = _load_runtime_types_v2()
    if torch is not torch_module:
        raise Exp01BBackendError("Torch module identity changed during smoke")
    node_count = len(P1_FEATURE_ORDER)
    model = model_type(node_count, config).to(config.device)
    optimizer = torch.optim.Adam(
        model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay,
    )
    x = torch.arange(
        2 * node_count * config.slide_window,
        device=config.device, dtype=torch.float32,
    ).reshape(2, node_count, config.slide_window) / 1000.0
    y = torch.arange(
        2 * node_count, device=config.device, dtype=torch.float32,
    ).reshape(2, node_count) / 1000.0
    original_edges = torch.tensor(
        [[source for target in range(node_count) for source in range(node_count) if source != target],
         [target for target in range(node_count) for source in range(node_count) if source != target]],
        dtype=torch.long, device=config.device,
    )
    optimizer.zero_grad()
    prediction = model(x, original_edges)
    loss = nn.MSELoss(reduction="mean")(prediction, y)
    if not bool(torch.isfinite(loss)):
        raise Exp01BBackendError("synthetic train-step loss is non-finite")
    loss.backward()
    optimizer.step()
    model.eval()
    equivalence = _verify_torch_functional_batch_equivalence_v1(
        torch=torch, model=model, data=x, full_graph_edge_index=original_edges,
        node_count=node_count,
    )
    model_device = str(next(model.parameters()).device).split(":", 1)[0]
    tensor_device = str(x.device).split(":", 1)[0]
    if model_device != config.device or tensor_device != config.device:
        raise Exp01BBackendError("synthetic model/tensor device mismatch")
    return {
        "synthetic_smoke_passed": True,
        "model_device": model_device,
        "tensor_device": tensor_device,
        "deterministic_algorithms": bool(torch.are_deterministic_algorithms_enabled()),
        "cudnn_deterministic": bool(torch.backends.cudnn.deterministic),
        "cudnn_benchmark": bool(torch.backends.cudnn.benchmark),
        "matmul_tf32": bool(torch.backends.cuda.matmul.allow_tf32),
        "cudnn_tf32": bool(torch.backends.cudnn.allow_tf32),
        "scientific_training_config_hash": config.hyperparameter_hash,
        "execution_backend_hash": config.execution_backend_hash,
        "functional_batch_equivalence_passed": equivalence,
    }


def _model_and_loader(
    *, state_dict: Mapping[str, Any], segments: Sequence[Any],
    feature_order: tuple[str, ...], config: Exp01BDeviceTrainingConfigV1,
) -> tuple[Any, Any, Any, Any]:
    torch, _, model_type = _load_runtime_types_v2()
    dataset = _FileLocalLazyWindows(
        segments, window=config.slide_window, stride=config.slide_stride,
        torch_module=torch,
    )
    model = model_type(len(feature_order), config).to(config.device)
    model.load_state_dict(state_dict, strict=True)
    model.eval()
    loader = torch.utils.data.DataLoader(dataset, batch_size=config.batch_size, shuffle=False)
    return torch, model, loader, dataset


def _target_mse_and_attention(
    *, torch: Any, model: Any, loader: Any, graph_edge_index: Any,
    graph_edges: tuple[tuple[str, str], ...], target_positions: tuple[int, ...],
    capture_attention: bool, feature_order: tuple[str, ...],
) -> tuple[dict[int, float], dict[tuple[str, str], float] | None]:
    squared = {index: 0.0 for index in target_positions}
    count = 0
    attention_sum = [0.0] * len(graph_edges)
    attention_count = 0
    device = next(model.parameters()).device
    graph_edge_index = graph_edge_index.to(device)
    with torch.no_grad():
        for batch_x, batch_y in loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            baseline = _predict_with_fixed_graph(model, batch_x, graph_edge_index)
            if capture_attention:
                captured = _predict_with_fixed_graph(model, batch_x, graph_edge_index)
                if not bool(torch.allclose(baseline, captured, atol=ATTENTION_ATOL, rtol=ATTENTION_RTOL)):
                    raise Exp01BBackendError("attention capture changed on-device prediction output")
                alpha = getattr(getattr(model.gnn_layer, "gnn", None), "_alpha", None)
                if alpha is None:
                    raise AttentionArmUnavailableError("post-normalization attention is unavailable")
                batch_size = int(batch_x.shape[0])
                node_count = int(batch_x.shape[1])
                batched = model._batch_edges(graph_edge_index, batch_size, node_count)
                from torch_geometric.utils import add_self_loops, remove_self_loops
                augmented, _ = remove_self_loops(batched)
                augmented, _ = add_self_loops(augmented, num_nodes=batch_size * node_count)
                if int(alpha.shape[0]) != int(augmented.shape[1]):
                    raise AttentionArmUnavailableError("attention/augmented-edge alignment is unavailable")
                mapped = aggregate_attention_from_augmented_tensors_v2(
                    torch_module=torch, augmented_edges=augmented, alpha_values=alpha,
                    node_count=node_count, feature_order=feature_order,
                    graph_edges=graph_edges, batch_size=batch_size,
                )
                for index, edge in enumerate(graph_edges):
                    attention_sum[index] += mapped[edge] * batch_size
                attention_count += batch_size
                prediction = captured
            else:
                prediction = baseline
            # Preserve the original per-target reduction while synchronizing
            # CUDA once per batch instead of once per target.
            batch_squared = torch.stack(tuple(
                ((prediction[:, index] - batch_y[:, index]) ** 2).sum()
                for index in target_positions
            )).detach().cpu().tolist()
            for index, value in zip(target_positions, batch_squared):
                squared[index] += float(value)
            count += int(batch_y.shape[0])
    if count <= 0:
        raise Exp01BBackendError("fixed-checkpoint metric denominator is empty")
    mse = {index: value / count for index, value in squared.items()}
    attention = None
    if capture_attention:
        if attention_count != count:
            raise Exp01BBackendError("attention aggregation denominator mismatch")
        attention = {edge: attention_sum[index] / attention_count for index, edge in enumerate(graph_edges)}
    return mse, attention


def _embedding_scores(
    *, torch: Any, model: Any, feature_order: tuple[str, ...],
) -> dict[tuple[str, str], float]:
    weights = model.embedding.weight.detach()
    cosine = torch.matmul(weights, weights.T)
    cosine = cosine / torch.matmul(weights.norm(dim=-1).view(-1, 1), weights.norm(dim=-1).view(1, -1))
    positions = {name: index for index, name in enumerate(feature_order)}
    return {
        pair: float(cosine[positions[pair[1]], positions[pair[0]]].item())
        for pair in PAIR_UNIVERSE
    }


def disjoint_variant_offset_plan_v1(
    *, variant_count: int, batch_size: int, node_count: int,
) -> tuple[tuple[int, ...], ...]:
    if min(variant_count, batch_size, node_count) <= 0:
        raise Exp01BBackendError("disjoint variant dimensions must be positive")
    return tuple(
        tuple((variant * batch_size + sample) * node_count for sample in range(batch_size))
        for variant in range(variant_count)
    )


def _predict_with_variant_graphs(
    *, torch: Any, model: Any, data: Any,
    variant_graph_indices: Sequence[Any], node_count: int,
) -> Any:
    """Evaluate distinct fixed graphs as disjoint per-example graphs."""

    import torch.nn.functional as functional

    variant_count = len(variant_graph_indices)
    if variant_count <= 0 or int(data.shape[0]) != variant_count:
        raise Exp01BBackendError("variant graph/data dimensions differ")
    batch_size, input_width = int(data.shape[1]), int(data.shape[3])
    flattened = data.reshape(variant_count * batch_size, node_count, input_width)
    x = flattened.clone().detach().reshape(-1, input_width).contiguous()
    all_embeddings = model.embedding(torch.arange(node_count, device=data.device))
    edges: list[Any] = []
    offsets = disjoint_variant_offset_plan_v1(
        variant_count=variant_count, batch_size=batch_size, node_count=node_count,
    )
    for variant_index, graph_index in enumerate(variant_graph_indices):
        graph = graph_index.to(data.device)
        for offset in offsets[variant_index]:
            edges.append(graph + offset)
    disjoint_edges = torch.cat(edges, dim=1).long()
    embeddings = all_embeddings.repeat(variant_count * batch_size, 1)
    out = model.gnn_layer(x, disjoint_edges, embeddings).view(
        variant_count * batch_size, node_count, -1,
    )
    node_ids = torch.arange(node_count, device=data.device)
    out = torch.mul(out, model.embedding(node_ids))
    out = functional.relu(model.bn_outlayer_in(out.permute(0, 2, 1))).permute(0, 2, 1)
    prediction = model.out_layer(model.dropout(out)).view(variant_count, batch_size, node_count)
    return prediction


def _verify_torch_functional_batch_equivalence_v1(
    *, torch: Any, model: Any, data: Any, full_graph_edge_index: Any,
    node_count: int,
) -> bool:
    if int(full_graph_edge_index.shape[1]) < 2:
        raise Exp01BBackendError("synthetic equivalence graph is too small")
    variants = (
        full_graph_edge_index,
        full_graph_edge_index[:, 1:],
    )
    with torch.no_grad():
        scalar = torch.stack(tuple(
            _predict_with_fixed_graph(model, data, graph)
            for graph in variants
        ), dim=0)
        batched = _predict_with_variant_graphs(
            torch=torch, model=model,
            data=data.unsqueeze(0).expand(2, -1, -1, -1),
            variant_graph_indices=variants, node_count=node_count,
        )
    if not bool(torch.allclose(
        scalar, batched,
        atol=FUNCTIONAL_BATCH_EQUIVALENCE_ATOL,
        rtol=FUNCTIONAL_BATCH_EQUIVALENCE_RTOL,
    )):
        raise Exp01BBackendError("scalar and batched functional evaluation diverged")
    return True


def _evaluate_edge_masks_batched(
    *, torch: Any, model: Any, loader: Any, order: tuple[str, ...],
    graph: tuple[tuple[str, str], ...], baseline_mse: Mapping[int, float],
    config: Exp01BDeviceTrainingConfigV1,
) -> dict[tuple[str, str], float]:
    positions = {name: index for index, name in enumerate(order)}
    edges = tuple(edge for edge in graph if edge[1] in TARGET_VARIABLES)
    graphs = tuple(tuple(item for item in graph if item != edge) for edge in edges)
    graph_indices = tuple(_edge_index_from_graph(torch, order, item).to(config.device) for item in graphs)
    squared = [0.0] * len(edges)
    count = 0
    with torch.no_grad():
        for batch_x, batch_y in loader:
            batch_x, batch_y = batch_x.to(config.device), batch_y.to(config.device)
            batch_count = int(batch_x.shape[0])
            for start in range(0, len(edges), config.functional_variant_chunk_size):
                stop = min(len(edges), start + config.functional_variant_chunk_size)
                variant_x = batch_x.unsqueeze(0).expand(stop - start, -1, -1, -1)
                predictions = _predict_with_variant_graphs(
                    torch=torch, model=model, data=variant_x,
                    variant_graph_indices=graph_indices[start:stop], node_count=len(order),
                )
                for local, edge in enumerate(edges[start:stop]):
                    target_index = positions[edge[1]]
                    squared[start + local] += float(
                        ((predictions[local, :, target_index] - batch_y[:, target_index]) ** 2).sum().item()
                    )
            count += batch_count
    if count <= 0:
        raise Exp01BBackendError("edge-mask denominator is empty")
    return {
        edge: relative_delta_mse_v1(
            baseline_target_mse=baseline_mse[positions[edge[1]]],
            masked_target_mse=squared[index] / count,
        )
        for index, edge in enumerate(edges)
    }


def stack_occluded_history_batch_v1(
    *, baseline_batch: Any, permuted_source_columns: Mapping[int, Sequence[float]],
    sample_offset: int, window: int,
) -> Any:
    """NumPy reference/adapter for synchronized file-local source variants."""

    try:
        import numpy as np
    except ImportError as exc:
        raise Exp01BBackendError("NumPy is required for source occlusion") from exc
    baseline = np.asarray(baseline_batch)
    if baseline.ndim != 3 or int(baseline.shape[2]) != window:
        raise Exp01BBackendError("baseline history batch shape is invalid")
    variants = np.repeat(baseline[None, ...], len(permuted_source_columns), axis=0)
    for variant_index, (source_index, values) in enumerate(sorted(permuted_source_columns.items())):
        column = np.asarray(values)
        for batch_index in range(int(baseline.shape[0])):
            start = sample_offset + batch_index
            replacement = column[start:start + window]
            if len(replacement) != window:
                raise Exp01BBackendError("occluded source history window is incomplete")
            variants[variant_index, batch_index, source_index, :] = replacement
    return variants


def _evaluate_source_occlusion_batched(
    *, torch: Any, model: Any, loader: Any, order: tuple[str, ...],
    graph_index: Any, original_matrix: Any, baseline_mse: Mapping[int, float],
    view: str, seed: int, config: Exp01BDeviceTrainingConfigV1,
) -> dict[tuple[str, str], float]:
    try:
        import numpy as np
    except ImportError as exc:
        raise Exp01BBackendError("NumPy is required for source occlusion") from exc
    positions = {name: index for index, name in enumerate(order)}
    original = np.asarray(original_matrix)
    permuted = {
        positions[source]: file_local_block_permutation_v1(
            original[:, positions[source]],
            seed=occlusion_seed_v1(view=view, run_seed=seed, file_id="train4", source=source),
        )
        for source in SOURCE_VARIABLES
    }
    source_indices = tuple(sorted(permuted))
    target_indices = tuple(positions[target] for target in TARGET_VARIABLES)
    squared = {(source_index, target_index): 0.0 for source_index in source_indices for target_index in target_indices}
    count = 0
    sample_offset = 0
    with torch.no_grad():
        for batch_x, batch_y in loader:
            batch_count = int(batch_x.shape[0])
            numpy_variants = stack_occluded_history_batch_v1(
                baseline_batch=batch_x.numpy(),
                permuted_source_columns=permuted,
                sample_offset=sample_offset,
                window=config.slide_window,
            )
            batch_y = batch_y.to(config.device)
            for start in range(0, len(source_indices), config.functional_variant_chunk_size):
                stop = min(len(source_indices), start + config.functional_variant_chunk_size)
                variant_x = torch.as_tensor(
                    numpy_variants[start:stop], dtype=torch.float32, device=config.device,
                )
                predictions = _predict_with_variant_graphs(
                    torch=torch, model=model, data=variant_x,
                    variant_graph_indices=tuple(graph_index for _ in range(stop - start)),
                    node_count=len(order),
                )
                for local, source_index in enumerate(source_indices[start:stop]):
                    for target_index in target_indices:
                        squared[(source_index, target_index)] += float(
                            ((predictions[local, :, target_index] - batch_y[:, target_index]) ** 2).sum().item()
                        )
            count += batch_count
            sample_offset += batch_count
    if count <= 0:
        raise Exp01BBackendError("source-occlusion denominator is empty")
    source_by_index = {positions[source]: source for source in SOURCE_VARIABLES}
    target_by_index = {positions[target]: target for target in TARGET_VARIABLES}
    return {
        (source_by_index[source_index], target_by_index[target_index]): relative_delta_mse_v1(
            baseline_target_mse=baseline_mse[target_index],
            masked_target_mse=value / count,
        )
        for (source_index, target_index), value in squared.items()
    }


def evaluate_exp01b_checkpoint_v1(
    *, state_dict: Mapping[str, Any], train4_segments: Sequence[Any],
    feature_order: Sequence[str], graph_edges: Sequence[tuple[str, str]],
    view: str, seed: int, config: Exp01BDeviceTrainingConfigV1,
) -> Exp01BCheckpointEvidenceV1:
    """Evaluate one fixed checkpoint; never retrain or refill a masked edge."""

    order = tuple(feature_order)
    positions = {name: index for index, name in enumerate(order)}
    if not set(SOURCE_VARIABLES + TARGET_VARIABLES).issubset(positions):
        raise Exp01BBackendError("P1 source/target feature authority is incomplete")
    graph = tuple(graph_edges)
    if len(graph) != len(set(graph)) or any(source == target for source, target in graph):
        raise Exp01BBackendError("learned graph identity is invalid")
    torch, model, loader, _ = _model_and_loader(
        state_dict=state_dict, segments=train4_segments,
        feature_order=order, config=config,
    )
    graph_index = _edge_index_from_graph(torch, order, graph)
    targets = tuple(positions[name] for name in TARGET_VARIABLES)
    attention_invariance_passed = True
    try:
        baseline_mse, raw_attention = _target_mse_and_attention(
            torch=torch, model=model, loader=loader, graph_edge_index=graph_index,
            graph_edges=graph, target_positions=targets, capture_attention=True,
            feature_order=order,
        )
    except AttentionArmUnavailableError:
        attention_invariance_passed = False
        fallback_loader = torch.utils.data.DataLoader(loader.dataset, batch_size=config.batch_size, shuffle=False)
        baseline_mse, raw_attention = _target_mse_and_attention(
            torch=torch, model=model, loader=fallback_loader, graph_edge_index=graph_index,
            graph_edges=graph, target_positions=targets, capture_attention=False,
            feature_order=order,
        )
    embedding = _embedding_scores(torch=torch, model=model, feature_order=order)
    graph_set = set(graph)
    attention = (
        {pair: float(raw_attention[pair]) for pair in PAIR_UNIVERSE if pair in graph_set}
        if raw_attention is not None else None
    )
    edge_loader = torch.utils.data.DataLoader(loader.dataset, batch_size=config.batch_size, shuffle=False)
    edge_delta = _evaluate_edge_masks_batched(
        torch=torch, model=model, loader=edge_loader, order=order,
        graph=graph, baseline_mse=baseline_mse, config=config,
    )
    candidate_edge_delta = {pair: edge_delta[pair] for pair in PAIR_UNIVERSE if pair in edge_delta}

    if len(train4_segments) != 1:
        raise Exp01BBackendError("train4 source occlusion must remain one-file local")
    occlusion_loader = torch.utils.data.DataLoader(loader.dataset, batch_size=config.batch_size, shuffle=False)
    occlusion = _evaluate_source_occlusion_batched(
        torch=torch, model=model, loader=occlusion_loader, order=order,
        graph_index=graph_index.to(config.device), original_matrix=train4_segments[0],
        baseline_mse=baseline_mse, view=view, seed=seed, config=config,
    )
    return Exp01BCheckpointEvidenceV1(
        embedding_scores=embedding,
        attention_scores=attention,
        edge_mask_scores=candidate_edge_delta,
        edge_mask_control_scores=edge_delta,
        occlusion_scores=occlusion,
        attention_invariance_passed=attention_invariance_passed,
    )


__all__ = [
    "AttentionArmUnavailableError", "Exp01BBackendError", "Exp01BCheckpointEvidenceV1",
    "Exp01BLineageEvidenceV1",
    "aggregate_attention_from_augmented_edges_v1",
    "aggregate_attention_from_augmented_tensors_v2",
    "disjoint_variant_offset_plan_v1",
    "stack_occluded_history_batch_v1",
    "Exp01BDeviceTrainingConfigV1", "configure_and_smoke_exp01b_backend_v1",
    "evaluate_exp01b_checkpoint_v1",
    "evaluate_exp01b_lineage_v1", "evaluate_selected_edge_masks_v1",
    "replay_exp01b_graph_v1",
    "train_exp01b_seed_v1",
]
