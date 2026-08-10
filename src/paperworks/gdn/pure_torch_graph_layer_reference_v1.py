"""Independent pure-PyTorch reference for TASK-039C-GDNP parity tests.

This module is compatibility evidence only.  It is not a production backend,
is not imported by the GDN execution path, and must never be used as a
fallback for :mod:`paperworks.gdn.upstream_candidate_backend_v1`.
"""

from __future__ import annotations

from typing import Any


class PureTorchGraphLayerReferenceError(ValueError):
    """Raised when a synthetic reference input violates the frozen equations."""


def remove_then_add_self_loops_reference_v1(
    edge_index: Any,
    *,
    num_nodes: int,
) -> Any:
    """Remove every self-loop, then append exactly one loop for every node."""

    import torch

    if edge_index.ndim != 2 or edge_index.shape[0] != 2:
        raise PureTorchGraphLayerReferenceError("edge_index must have shape [2, E]")
    if num_nodes <= 0:
        raise PureTorchGraphLayerReferenceError("num_nodes must be positive")
    source, target = edge_index[0], edge_index[1]
    if source.numel() and (
        int(edge_index.min().item()) < 0 or int(edge_index.max().item()) >= num_nodes
    ):
        raise PureTorchGraphLayerReferenceError("edge index is outside node range")
    kept = edge_index[:, source != target]
    nodes = torch.arange(num_nodes, dtype=edge_index.dtype, device=edge_index.device)
    loops = torch.stack((nodes, nodes), dim=0)
    return torch.cat((kept, loops), dim=1)


def grouped_softmax_reference_v1(
    src: Any,
    index: Any,
    *,
    num_nodes: int,
) -> Any:
    """Stable dimension-zero grouped softmax using core PyTorch only."""

    import torch

    if src.ndim < 1 or index.ndim != 1 or src.shape[0] != index.numel():
        raise PureTorchGraphLayerReferenceError("grouped-softmax shapes are invalid")
    if num_nodes <= 0:
        raise PureTorchGraphLayerReferenceError("num_nodes must be positive")
    if index.numel() and (
        int(index.min().item()) < 0 or int(index.max().item()) >= num_nodes
    ):
        raise PureTorchGraphLayerReferenceError("group index is outside node range")

    out = torch.zeros_like(src)
    for node in range(num_nodes):
        mask = index == node
        if not bool(mask.any()):
            continue
        values = src[mask]
        shifted = values - values.max(dim=0, keepdim=True).values
        exponentials = shifted.exp()
        out[mask] = exponentials / exponentials.sum(dim=0, keepdim=True)
    return out


def graph_layer_reference_v1(
    *,
    x: Any,
    edge_index: Any,
    embedding: Any,
    linear_weight: Any,
    attention_source: Any,
    attention_target: Any,
    embedding_attention_source: Any,
    embedding_attention_target: Any,
    bias: Any | None,
    heads: int,
    out_channels: int,
    concat: bool,
    negative_slope: float,
    dropout: float = 0.0,
    training: bool = False,
) -> dict[str, Any]:
    """Evaluate the pinned upstream GraphLayer equations without PyG.

    The edge convention is source in row zero and destination in row one.
    Aggregation is an explicit ``index_add_(dim=0, ...)`` by destination.
    """

    import torch
    import torch.nn.functional as functional

    if x.ndim != 2 or embedding.ndim != 2:
        raise PureTorchGraphLayerReferenceError("node features and embeddings must be 2-D")
    if x.shape[0] != embedding.shape[0]:
        raise PureTorchGraphLayerReferenceError("feature and embedding node counts differ")
    if heads <= 0 or out_channels <= 0:
        raise PureTorchGraphLayerReferenceError("head and channel counts must be positive")
    if embedding.shape[1] != out_channels:
        raise PureTorchGraphLayerReferenceError(
            "upstream embedding width must equal GraphLayer output channels"
        )
    if dropout < 0.0 or dropout >= 1.0:
        raise PureTorchGraphLayerReferenceError("dropout must be in [0, 1)")

    projected = functional.linear(x, linear_weight)
    processed_edge_index = remove_then_add_self_loops_reference_v1(
        edge_index,
        num_nodes=x.shape[0],
    )
    source_index = processed_edge_index[0]
    target_index = processed_edge_index[1]
    edge_count = processed_edge_index.shape[1]
    source_features = projected.index_select(0, source_index).view(
        edge_count, heads, out_channels
    )
    target_features = projected.index_select(0, target_index).view(
        edge_count, heads, out_channels
    )
    source_embeddings = embedding.index_select(0, source_index).unsqueeze(1).repeat(
        1, heads, 1
    )
    target_embeddings = embedding.index_select(0, target_index).unsqueeze(1).repeat(
        1, heads, 1
    )
    source_keys = torch.cat((source_features, source_embeddings), dim=-1)
    target_keys = torch.cat((target_features, target_embeddings), dim=-1)
    source_attention = torch.cat(
        (attention_source, embedding_attention_source), dim=-1
    )
    target_attention = torch.cat(
        (attention_target, embedding_attention_target), dim=-1
    )
    raw_logits = (target_keys * source_attention).sum(-1)
    raw_logits = raw_logits + (source_keys * target_attention).sum(-1)
    attention_logits = functional.leaky_relu(
        raw_logits.view(edge_count, heads, 1),
        negative_slope,
    )
    attention_coefficients = grouped_softmax_reference_v1(
        attention_logits,
        target_index,
        num_nodes=x.shape[0],
    )
    effective_attention = (
        functional.dropout(attention_coefficients, p=dropout, training=training)
        if dropout
        else attention_coefficients
    )
    messages = source_features * effective_attention.view(edge_count, heads, 1)
    aggregated = messages.new_zeros((x.shape[0], heads, out_channels))
    aggregated.index_add_(0, target_index, messages)
    combined = (
        aggregated.reshape(x.shape[0], heads * out_channels)
        if concat
        else aggregated.mean(dim=1)
    )
    output = combined + bias if bias is not None else combined
    return {
        "projected": projected,
        "processed_edge_index": processed_edge_index,
        "source_index": source_index,
        "target_index": target_index,
        "target_features": target_features,
        "source_features": source_features,
        "attention_logits": attention_logits,
        "attention_coefficients": attention_coefficients,
        "messages": messages,
        "aggregated": aggregated,
        "output": output,
    }


__all__ = [
    "PureTorchGraphLayerReferenceError",
    "graph_layer_reference_v1",
    "grouped_softmax_reference_v1",
    "remove_then_add_self_loops_reference_v1",
]
