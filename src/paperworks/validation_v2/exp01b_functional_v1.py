"""Pure functional-XAI primitives for fixed EXP-01B checkpoints."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Iterable, Mapping, Sequence

from paperworks.validation_v2.exp01b_contract_v1 import (
    OCCLUSION_BLOCK_WIDTH,
    RELATIVE_DELTA_EPSILON,
)
from paperworks.v6.common import stable_hash_v1


class Exp01BFunctionalError(ValueError):
    """Fail-closed functional evidence error."""


Pair = tuple[str, str]


def occlusion_seed_v1(*, view: str, run_seed: int, file_id: str, source: str) -> int:
    if not view or not file_id or not source or any("/" in value or "\\" in value for value in (file_id, source)):
        raise Exp01BFunctionalError("occlusion seed inputs must be symbolic non-path identities")
    return int(stable_hash_v1({
        "experiment_id": "EXP-01B-GDN-XAI-V1",
        "view": view,
        "run_seed": run_seed,
        "file_id": file_id,
        "source": source,
    })[:16], 16)


def target_specific_mse_v1(prediction: Sequence[float], observed: Sequence[float]) -> float:
    if len(prediction) != len(observed) or not prediction:
        raise Exp01BFunctionalError("target MSE requires equal non-empty vectors")
    errors = []
    for left, right in zip(prediction, observed):
        left_value, right_value = float(left), float(right)
        if not math.isfinite(left_value) or not math.isfinite(right_value):
            raise Exp01BFunctionalError("target MSE inputs must be finite")
        errors.append((left_value - right_value) ** 2)
    return sum(errors) / len(errors)


def relative_delta_mse_v1(
    *, baseline_target_mse: float, masked_target_mse: float,
    epsilon: float = RELATIVE_DELTA_EPSILON,
) -> float:
    baseline, masked = float(baseline_target_mse), float(masked_target_mse)
    if not math.isfinite(baseline) or not math.isfinite(masked) or baseline < 0 or masked < 0:
        raise Exp01BFunctionalError("MSE values must be finite and nonnegative")
    if epsilon != RELATIVE_DELTA_EPSILON:
        raise Exp01BFunctionalError("relative delta epsilon is frozen")
    return (masked - baseline) / (baseline + epsilon)


def remove_exact_edge_without_refill_v1(
    graph_edges: Sequence[Pair], *, edge: Pair,
) -> tuple[Pair, ...]:
    edges = tuple((str(source), str(target)) for source, target in graph_edges)
    if len(edges) != len(set(edges)):
        raise Exp01BFunctionalError("graph edges must be unique")
    if edge not in edges:
        raise Exp01BFunctionalError("masked edge must exist in the learned graph")
    result = tuple(item for item in edges if item != edge)
    if len(result) != len(edges) - 1:
        raise Exp01BFunctionalError("exactly one edge must be removed")
    return result


def matched_random_controls_v1(
    *, focal_edges: Sequence[Pair], eligible_graph_edges: Sequence[Pair],
    seed: int, cardinality: int = 1,
) -> dict[Pair, tuple[Pair, ...]]:
    """Match on target, graph eligibility, seed and mask cardinality."""

    if cardinality != 1:
        raise Exp01BFunctionalError("EXP-01B masks one edge at a time")
    eligible = tuple(sorted(set(eligible_graph_edges)))
    focal = tuple(sorted(set(focal_edges)))
    if any(edge not in eligible for edge in focal):
        raise Exp01BFunctionalError("focal edges must be learned-graph members")
    result: dict[Pair, tuple[Pair, ...]] = {}
    for edge in focal:
        candidates = [item for item in eligible if item[1] == edge[1] and item not in focal]
        if not candidates:
            raise Exp01BFunctionalError("no target-matched random control exists")
        local_seed = int(stable_hash_v1({"seed": seed, "edge": list(edge)})[:16], 16)
        selected = random.Random(local_seed).choice(candidates)
        result[edge] = (selected,)
    return result


def file_local_block_permutation_v1(
    values: Sequence[float], *, seed: int,
    block_width: int = OCCLUSION_BLOCK_WIDTH,
) -> tuple[float, ...]:
    """Preserve source values while breaking file-local temporal alignment."""

    original = tuple(float(value) for value in values)
    if any(not math.isfinite(value) for value in original):
        raise Exp01BFunctionalError("source history must be finite")
    if block_width != OCCLUSION_BLOCK_WIDTH or len(original) < block_width * 2:
        raise Exp01BFunctionalError("frozen block permutation needs at least two full blocks")
    blocks = [original[index:index + block_width] for index in range(0, len(original), block_width)]
    indices = list(range(len(blocks)))
    random.Random(seed).shuffle(indices)
    if indices == list(range(len(blocks))):
        indices = indices[1:] + indices[:1]
    result = tuple(value for index in indices for value in blocks[index])
    if sorted(result) != sorted(original) or result == original:
        raise Exp01BFunctionalError("occlusion must preserve marginals and change alignment")
    return result


@dataclass(frozen=True)
class EdgeMaskEvidenceV1:
    edge: Pair
    view: str
    seed: int
    baseline_target_mse: float
    masked_target_mse: float
    relative_delta_mse: float
    graph_member: bool = True
    fixed_checkpoint: bool = True
    target_specific: bool = True

    def __post_init__(self) -> None:
        expected = relative_delta_mse_v1(
            baseline_target_mse=self.baseline_target_mse,
            masked_target_mse=self.masked_target_mse,
        )
        if not math.isclose(self.relative_delta_mse, expected, rel_tol=1e-12, abs_tol=1e-12):
            raise Exp01BFunctionalError("edge-mask score arithmetic mismatch")
        if not self.graph_member or not self.fixed_checkpoint or not self.target_specific:
            raise Exp01BFunctionalError("positive functional evidence requires a fixed learned edge")


def verify_attention_capture_invariance_v1(
    baseline: Sequence[float], captured: Sequence[float], *, atol: float, rtol: float,
) -> None:
    if len(baseline) != len(captured) or not baseline:
        raise Exp01BFunctionalError("attention invariance vectors are incomplete")
    for left, right in zip(baseline, captured):
        if not math.isclose(float(left), float(right), abs_tol=atol, rel_tol=rtol):
            raise Exp01BFunctionalError("attention capture changed prediction output")


__all__ = [
    "EdgeMaskEvidenceV1", "Exp01BFunctionalError", "file_local_block_permutation_v1",
    "matched_random_controls_v1", "relative_delta_mse_v1",
    "occlusion_seed_v1", "remove_exact_edge_without_refill_v1", "target_specific_mse_v1",
    "verify_attention_capture_invariance_v1",
]
