"""Immutable TASK-030 candidate graph document model."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, TypeAlias, cast

from paperworks.contracts.artifact_hashing import (
    ContractArtifactHashError,
    canonical_contract_artifact_sha256,
    verify_contract_artifact_hash,
)
from paperworks.contracts.schema_registry import SchemaRegistry, load_schema_registry


Scalar: TypeAlias = str | int | float | bool


class GraphV1ModelError(ValueError):
    def __init__(self, issue_code: str, field_path: str, message: str) -> None:
        super().__init__(f"{issue_code} at {field_path}: {message}")
        self.issue_code = issue_code
        self.field_path = field_path
        self.message = message


@dataclass(frozen=True)
class SamplingIntervalV1:
    value: int | float
    unit: str


@dataclass(frozen=True)
class MetadataProvenanceV1:
    source_kind: str
    source_reference: str
    review_status: str
    artifact_hash: str


@dataclass(frozen=True)
class GraphNodeV1:
    node_id: str
    variable_name: str
    display_name: str
    node_type: str
    subsystem: str
    physical_unit: str
    data_type: str
    allowed_operating_states: tuple[Scalar, ...]
    sampling_interval: SamplingIntervalV1
    metadata_provenance: MetadataProvenanceV1


@dataclass(frozen=True)
class GraphRangeV1:
    minimum: int | float
    maximum: int | float
    unit: str


@dataclass(frozen=True)
class GraphSupportV1:
    event_count: int
    normal_reference_count: int


@dataclass(frozen=True)
class GraphUncertaintyV1:
    method: str
    lower: int | float
    upper: int | float


@dataclass(frozen=True)
class GraphProvenanceV1:
    created_by: str
    method_version: str
    source_artifact_ids: tuple[str, ...]
    code_commit: str


@dataclass(frozen=True)
class GraphEdgeV1:
    edge_id: str
    source_node: str
    target_node: str
    direction: str
    relation_family_candidates: tuple[str, ...]
    lag_candidate_range: GraphRangeV1
    operating_regimes: tuple[str, ...]
    evidence_sources: tuple[str, ...]
    support: GraphSupportV1
    confidence: int | float
    uncertainty: GraphUncertaintyV1
    edge_semantics: str
    physical: bool
    documented: bool
    statistical: bool
    weakly_supervised: bool
    causal_claim_allowed: bool
    provenance: GraphProvenanceV1


@dataclass(frozen=True)
class CandidateGraphV1:
    schema_version: str
    graph_id: str
    artifact_hash: str
    dataset_version: str
    candidate_universe_id: str
    candidate_generation_stage: str
    nodes: tuple[GraphNodeV1, ...]
    edges: tuple[GraphEdgeV1, ...]
    provenance: GraphProvenanceV1

    @property
    def runtime_authorized(self) -> bool:
        return False


def parse_candidate_graph(
    document: Mapping[str, object], *, registry: SchemaRegistry | None = None
) -> CandidateGraphV1:
    snapshot = copy.deepcopy(dict(document))
    report = (registry or load_schema_registry()).validate_artifact("graph", snapshot)
    if report.status != "valid":
        issue = report.issues[0] if report.issues else None
        _fail("GRAPH_V1_STRUCTURAL_INVALID", issue.instance_path if issue else "/", issue.issue_code if issue else "registry error")
    try:
        verify_contract_artifact_hash(snapshot)
    except ContractArtifactHashError as exc:
        _fail(exc.issue_code, "/artifact_hash", exc.message)
    graph = _typed_graph(snapshot)
    _validate_graph(graph)
    return graph


def load_candidate_graph(path: str | Path, *, registry: SchemaRegistry | None = None) -> CandidateGraphV1:
    return parse_candidate_graph(_load_object(path, "GRAPH_V1_STRUCTURAL_INVALID"), registry=registry)


def candidate_graph_to_dict(graph: CandidateGraphV1) -> dict[str, Any]:
    return {
        "schema_version": graph.schema_version,
        "graph_id": graph.graph_id,
        "artifact_hash": graph.artifact_hash,
        "dataset_version": graph.dataset_version,
        "candidate_universe_id": graph.candidate_universe_id,
        "candidate_generation_stage": graph.candidate_generation_stage,
        "nodes": [_node_to_dict(node) for node in graph.nodes],
        "edges": [_edge_to_dict(edge) for edge in graph.edges],
        "provenance": _provenance_to_dict(graph.provenance),
    }


def serialize_candidate_graph(graph: CandidateGraphV1) -> str:
    return _canonical_json(candidate_graph_to_dict(graph))


def canonical_candidate_graph_sha256(graph: CandidateGraphV1) -> str:
    """Compute the integrity-only artifact self-hash."""

    return canonical_contract_artifact_sha256(candidate_graph_to_dict(graph))


def _typed_graph(document: Mapping[str, Any]) -> CandidateGraphV1:
    return CandidateGraphV1(
        schema_version=cast(str, document["schema_version"]), graph_id=cast(str, document["graph_id"]),
        artifact_hash=cast(str, document["artifact_hash"]), dataset_version=cast(str, document["dataset_version"]),
        candidate_universe_id=cast(str, document["candidate_universe_id"]),
        candidate_generation_stage=cast(str, document["candidate_generation_stage"]),
        nodes=tuple(_typed_node(item) for item in cast(list[Mapping[str, Any]], document["nodes"])),
        edges=tuple(_typed_edge(item) for item in cast(list[Mapping[str, Any]], document["edges"])),
        provenance=_typed_provenance(cast(Mapping[str, Any], document["provenance"])),
    )


def _typed_node(item: Mapping[str, Any]) -> GraphNodeV1:
    interval = cast(Mapping[str, Any], item["sampling_interval"])
    provenance = cast(Mapping[str, Any], item["metadata_provenance"])
    return GraphNodeV1(
        node_id=cast(str, item["node_id"]), variable_name=cast(str, item["variable_name"]),
        display_name=cast(str, item["display_name"]), node_type=cast(str, item["node_type"]),
        subsystem=cast(str, item["subsystem"]), physical_unit=cast(str, item["physical_unit"]),
        data_type=cast(str, item["data_type"]),
        allowed_operating_states=tuple(cast(list[Scalar], item["allowed_operating_states"])),
        sampling_interval=SamplingIntervalV1(cast(int | float, interval["value"]), cast(str, interval["unit"])),
        metadata_provenance=MetadataProvenanceV1(
            cast(str, provenance["source_kind"]), cast(str, provenance["source_reference"]),
            cast(str, provenance["review_status"]), cast(str, provenance["artifact_hash"]),
        ),
    )


def _typed_edge(item: Mapping[str, Any]) -> GraphEdgeV1:
    lag, support, uncertainty = item["lag_candidate_range"], item["support"], item["uncertainty"]
    return GraphEdgeV1(
        edge_id=cast(str, item["edge_id"]), source_node=cast(str, item["source_node"]),
        target_node=cast(str, item["target_node"]), direction=cast(str, item["direction"]),
        relation_family_candidates=tuple(cast(list[str], item["relation_family_candidates"])),
        lag_candidate_range=GraphRangeV1(lag["minimum"], lag["maximum"], lag["unit"]),
        operating_regimes=tuple(cast(list[str], item["operating_regimes"])),
        evidence_sources=tuple(cast(list[str], item["evidence_sources"])),
        support=GraphSupportV1(support["event_count"], support["normal_reference_count"]),
        confidence=cast(int | float, item["confidence"]),
        uncertainty=GraphUncertaintyV1(uncertainty["method"], uncertainty["lower"], uncertainty["upper"]),
        edge_semantics=cast(str, item["edge_semantics"]), physical=cast(bool, item["physical"]),
        documented=cast(bool, item["documented"]), statistical=cast(bool, item["statistical"]),
        weakly_supervised=cast(bool, item["weakly_supervised"]),
        causal_claim_allowed=cast(bool, item["causal_claim_allowed"]),
        provenance=_typed_provenance(cast(Mapping[str, Any], item["provenance"])),
    )


def _typed_provenance(item: Mapping[str, Any]) -> GraphProvenanceV1:
    return GraphProvenanceV1(cast(str, item["created_by"]), cast(str, item["method_version"]), tuple(cast(list[str], item["source_artifact_ids"])), cast(str, item["code_commit"]))


def _validate_graph(graph: CandidateGraphV1) -> None:
    node_ids = [node.node_id for node in graph.nodes]
    variables = [node.variable_name for node in graph.nodes]
    edge_ids = [edge.edge_id for edge in graph.edges]
    _require_unique(node_ids, "GRAPH_V1_DUPLICATE_NODE_ID", "/nodes")
    _require_unique(variables, "GRAPH_V1_DUPLICATE_VARIABLE", "/nodes")
    _require_unique(edge_ids, "GRAPH_V1_DUPLICATE_EDGE_ID", "/edges")
    known = set(node_ids)
    for index, edge in enumerate(graph.edges):
        path = f"/edges/{index}"
        if edge.source_node not in known or edge.target_node not in known:
            _fail("GRAPH_V1_UNKNOWN_ENDPOINT", path, "edge endpoint is not registered")
        if edge.source_node == edge.target_node:
            _fail("GRAPH_V1_SELF_EDGE", path, "self-edges are prohibited")
        if edge.lag_candidate_range.minimum > edge.lag_candidate_range.maximum:
            _fail("GRAPH_V1_LAG_ORDER", f"{path}/lag_candidate_range", "lag range is inverted")
        if edge.uncertainty.lower > edge.uncertainty.upper:
            _fail("GRAPH_V1_UNCERTAINTY_ORDER", f"{path}/uncertainty", "uncertainty range is inverted")
        if edge.causal_claim_allowed:
            _fail("GRAPH_V1_CAUSAL_CLAIM", f"{path}/causal_claim_allowed", "causal claims are prohibited")


def _node_to_dict(node: GraphNodeV1) -> dict[str, Any]:
    return {"node_id": node.node_id, "variable_name": node.variable_name, "display_name": node.display_name,
            "node_type": node.node_type, "subsystem": node.subsystem, "physical_unit": node.physical_unit,
            "data_type": node.data_type, "allowed_operating_states": list(node.allowed_operating_states),
            "sampling_interval": {"value": node.sampling_interval.value, "unit": node.sampling_interval.unit},
            "metadata_provenance": {"source_kind": node.metadata_provenance.source_kind,
                                    "source_reference": node.metadata_provenance.source_reference,
                                    "review_status": node.metadata_provenance.review_status,
                                    "artifact_hash": node.metadata_provenance.artifact_hash}}


def _edge_to_dict(edge: GraphEdgeV1) -> dict[str, Any]:
    return {"edge_id": edge.edge_id, "source_node": edge.source_node, "target_node": edge.target_node,
            "direction": edge.direction, "relation_family_candidates": list(edge.relation_family_candidates),
            "lag_candidate_range": {"minimum": edge.lag_candidate_range.minimum, "maximum": edge.lag_candidate_range.maximum, "unit": edge.lag_candidate_range.unit},
            "operating_regimes": list(edge.operating_regimes), "evidence_sources": list(edge.evidence_sources),
            "support": {"event_count": edge.support.event_count, "normal_reference_count": edge.support.normal_reference_count},
            "confidence": edge.confidence,
            "uncertainty": {"method": edge.uncertainty.method, "lower": edge.uncertainty.lower, "upper": edge.uncertainty.upper},
            "edge_semantics": edge.edge_semantics, "physical": edge.physical, "documented": edge.documented,
            "statistical": edge.statistical, "weakly_supervised": edge.weakly_supervised,
            "causal_claim_allowed": edge.causal_claim_allowed, "provenance": _provenance_to_dict(edge.provenance)}


def _provenance_to_dict(item: GraphProvenanceV1) -> dict[str, Any]:
    return {"created_by": item.created_by, "method_version": item.method_version,
            "source_artifact_ids": list(item.source_artifact_ids), "code_commit": item.code_commit}


def _require_unique(values: list[str], code: str, path: str) -> None:
    if len(values) != len(set(values)):
        _fail(code, path, "identifiers must be unique")


def _load_object(path: str | Path, code: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GraphV1ModelError(code, "/", "artifact is not readable UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise GraphV1ModelError(code, "/", "artifact must be a JSON object")
    return value


def _canonical_json(document: Mapping[str, Any]) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _fail(code: str, path: str, message: str) -> None:
    raise GraphV1ModelError(code, path, message)
