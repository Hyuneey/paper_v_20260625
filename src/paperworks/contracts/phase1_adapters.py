"""Explicit serialized Phase 1 adapters for TASK-030 external artifacts."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, TypeAlias

from paperworks.contracts.artifact_hashing import with_computed_artifact_hash
from paperworks.contracts.evidence_v1 import EvidencePackageV1, parse_evidence_package
from paperworks.contracts.graph_v1 import CandidateGraphV1, parse_candidate_graph
from paperworks.contracts.parameter_v1 import CalibrationParameterV1, parse_calibration_parameter


PHASE1_ADAPTER_VERSION = "1.0.0"
AdapterTarget: TypeAlias = CandidateGraphV1 | EvidencePackageV1 | CalibrationParameterV1


@dataclass(frozen=True)
class AdapterFieldMapping:
    source_field: str
    target_field: str
    mapping: str


@dataclass(frozen=True)
class ContractAdapterResult:
    adapter_version: str
    source_artifact_type: str
    source_sha256: str
    target_artifact_type: str
    status: str
    target_artifact_created: bool
    target_artifact_sha256: str | None
    field_mappings: tuple[AdapterFieldMapping, ...]
    required_external_context: tuple[str, ...]
    information_loss: tuple[str, ...]
    warnings: tuple[str, ...]
    unsupported_reasons: tuple[str, ...]
    target_artifact: AdapterTarget | None = None

    def __post_init__(self) -> None:
        if self.status not in {"created", "pending_context", "unsupported_source", "invalid_source"}:
            raise ValueError("unsupported adapter status")
        if self.status == "created" and (not self.target_artifact_created or self.target_artifact is None):
            raise ValueError("created adapter result requires a complete target")
        if self.status != "created" and (self.target_artifact_created or self.target_artifact is not None):
            raise ValueError("non-created adapter result cannot contain a partial target")


@dataclass(frozen=True)
class DelayedResponseArtifactCollectionV1:
    graph: CandidateGraphV1
    evidence: EvidencePackageV1
    parameters: tuple[CalibrationParameterV1, ...]

    def __post_init__(self) -> None:
        if not self.parameters:
            raise ValueError("at least one parameter record is required")
        ids = [parameter.parameter_id for parameter in self.parameters]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate parameter IDs are prohibited")

    @property
    def graph_by_id(self) -> Mapping[str, CandidateGraphV1]:
        return MappingProxyType({self.graph.graph_id: self.graph})

    @property
    def edge_by_id(self) -> Mapping[str, Any]:
        return MappingProxyType({edge.edge_id: edge for edge in self.graph.edges})

    @property
    def evidence_by_id(self) -> Mapping[str, EvidencePackageV1]:
        return MappingProxyType({self.evidence.evidence_id: self.evidence})

    @property
    def normal_reference_by_id(self) -> Mapping[str, Any]:
        normal = self.evidence.matched_normal_reference
        return MappingProxyType({normal.reference_id: normal})

    @property
    def parameter_by_id(self) -> Mapping[str, CalibrationParameterV1]:
        return MappingProxyType({parameter.parameter_id: parameter for parameter in self.parameters})

    @property
    def rule_binding_verified(self) -> bool:
        return False

    @property
    def runtime_authorized(self) -> bool:
        return False


def adapt_phase1_candidate_graph(
    candidate_universe: Mapping[str, Any],
    *,
    context: Mapping[str, Any],
    gdn_edges: Mapping[str, Any] | None = None,
) -> ContractAdapterResult:
    sources = [candidate_universe] + ([gdn_edges] if gdn_edges is not None else [])
    source_hash = _combined_source_hash(sources)
    mappings = (
        AdapterFieldMapping("pairs", "edges", "allowed candidate membership before optional GDN ranking"),
        AdapterFieldMapping("feature_order", "nodes", "explicit node_metadata lookup"),
        AdapterFieldMapping("candidate origins", "evidence_sources", "bounded origin mapping"),
    )
    source_type = str(candidate_universe.get("artifact_type", "unknown"))
    if source_type != "candidate_universe":
        return _result(source_type, source_hash, "graph", "invalid_source", mappings, reasons=("source artifact_type must be candidate_universe",))
    required = (
        "dataset_version", "graph_id", "candidate_universe_id", "node_metadata", "operating_regimes",
        "edge_semantics", "provenance", "lag_candidate_range", "support", "confidence", "uncertainty",
    )
    missing = _missing(context, required)
    if missing:
        return _result(source_type, source_hash, "graph", "pending_context", mappings, required=missing)
    pairs = candidate_universe.get("pairs")
    features = candidate_universe.get("feature_order")
    if not isinstance(pairs, list) or not isinstance(features, list):
        return _result(source_type, source_hash, "graph", "invalid_source", mappings, reasons=("candidate pairs and feature order must be arrays",))
    allowed = {(item.get("source"), item.get("target")): item for item in pairs if isinstance(item, dict) and item.get("allowed") is True}
    if any(source == target for source, target in allowed):
        return _result(source_type, source_hash, "graph", "invalid_source", mappings, reasons=("candidate self-edge is prohibited",))
    selected: list[tuple[str, str, Mapping[str, Any], bool]] = []
    if gdn_edges is not None:
        if gdn_edges.get("artifact_type") != "gdn_candidate_edges" or not isinstance(gdn_edges.get("edges"), list):
            return _result(source_type, source_hash, "graph", "invalid_source", mappings, reasons=("GDN edge artifact is malformed",))
        for edge in gdn_edges["edges"]:
            pair = (edge.get("source"), edge.get("target"))
            if pair not in allowed:
                return _result(source_type, source_hash, "graph", "invalid_source", mappings, reasons=("GDN edge is outside CandidateUniverse",))
            selected.append((pair[0], pair[1], allowed[pair], True))
    else:
        selected = [(source, target, item, False) for (source, target), item in sorted(allowed.items())]
    metadata = context["node_metadata"]
    if not isinstance(metadata, Mapping) or any(name not in metadata for name in features):
        missing_names = tuple(sorted(str(name) for name in features if not isinstance(metadata, Mapping) or name not in metadata))
        return _result(source_type, source_hash, "graph", "pending_context", mappings, required=tuple(f"node_metadata.{name}" for name in missing_names))
    nodes = [copy.deepcopy(dict(metadata[name])) for name in features]
    node_ids = {node["variable_name"]: node["node_id"] for node in nodes}
    edges = []
    for source, target, pair, ranked in selected:
        origins = tuple(str(item) for item in pair.get("origins", ()))
        evidence_sources = _origin_evidence_sources(origins, ranked)
        provenance = copy.deepcopy(dict(context["provenance"]))
        edges.append({
            "edge_id": _edge_id(source, target), "source_node": node_ids[source], "target_node": node_ids[target],
            "direction": "directed", "relation_family_candidates": ["delayed_response"],
            "lag_candidate_range": copy.deepcopy(context["lag_candidate_range"]),
            "operating_regimes": copy.deepcopy(context["operating_regimes"]), "evidence_sources": evidence_sources,
            "support": copy.deepcopy(context["support"]), "confidence": context["confidence"],
            "uncertainty": copy.deepcopy(context["uncertainty"]), "edge_semantics": context["edge_semantics"],
            "physical": False, "documented": False, "statistical": "statistical" in origins,
            "weakly_supervised": False, "causal_claim_allowed": False, "provenance": provenance,
        })
    document = with_computed_artifact_hash({
        "schema_version": "1.0.0", "graph_id": context["graph_id"], "artifact_hash": "0" * 64,
        "dataset_version": context["dataset_version"], "candidate_universe_id": context["candidate_universe_id"],
        "candidate_generation_stage": "pre_scoring", "nodes": nodes, "edges": edges,
        "provenance": copy.deepcopy(context["provenance"]),
    })
    try:
        target = parse_candidate_graph(document)
    except ValueError as exc:
        return _result(source_type, source_hash, "graph", "invalid_source", mappings, reasons=(f"target validation failed: {getattr(exc, 'issue_code', 'MODEL_ERROR')}",))
    return _created(source_type, source_hash, "graph", mappings, target, target.artifact_hash,
                    information=("GDN similarity is not persisted as causal confidence",))


def adapt_phase1_evidence_package(
    relation_profile: Mapping[str, Any],
    relation_evidence_pack: Mapping[str, Any],
    *,
    context: Mapping[str, Any],
) -> ContractAdapterResult:
    source_hash = _combined_source_hash((relation_profile, relation_evidence_pack))
    mappings = (
        AdapterFieldMapping("source/target", "source_variables/target_variables", "one-to-one explicit mapping"),
        AdapterFieldMapping("split_name", "data_split", "calibration_normal to calibration"),
        AdapterFieldMapping("aggregate support", "none", "not representable in closed target schema"),
    )
    source_type = "relation_profile+relation_evidence_pack"
    if relation_profile.get("artifact_type") != "relation_profile" or relation_evidence_pack.get("artifact_type") != "relation_evidence_pack":
        return _result(source_type, source_hash, "evidence_package", "invalid_source", mappings, reasons=("legacy evidence artifact types are invalid",))
    required = ("evidence_id", "dataset_version", "event_anchor", "event_window", "pre_event_context", "post_event_context",
                "matched_normal_reference", "operating_regime", "candidate_lag_range", "selection_policy",
                "selection_policy_hash", "supported_claims")
    missing = _missing(context, required)
    if missing:
        return _result(source_type, source_hash, "evidence_package", "pending_context", mappings, required=missing)
    source, target = relation_profile.get("source"), relation_profile.get("target")
    if source != relation_evidence_pack.get("source") or target != relation_evidence_pack.get("target"):
        return _result(source_type, source_hash, "evidence_package", "invalid_source", mappings, reasons=("profile and evidence-pack variables disagree",))
    if relation_profile.get("profile_id") != relation_evidence_pack.get("relation_profile_id"):
        return _result(source_type, source_hash, "evidence_package", "invalid_source", mappings, reasons=("profile and evidence-pack IDs disagree",))
    if relation_profile.get("relation_type") != "binary_actuator_to_continuous_sensor" or relation_evidence_pack.get("recommended_rule_family") != "delayed_response":
        return _result(source_type, source_hash, "evidence_package", "unsupported_source", mappings, reasons=("only one-source/one-target delayed response is supported",))
    if relation_profile.get("split_name") != "calibration_normal":
        return _result(source_type, source_hash, "evidence_package", "unsupported_source", mappings, reasons=("legacy evidence must use calibration_normal",))
    document = with_computed_artifact_hash({
        "schema_version": "1.0.0", "evidence_id": context["evidence_id"], "artifact_hash": "0" * 64,
        "event_anchor": copy.deepcopy(context["event_anchor"]), "event_window": copy.deepcopy(context["event_window"]),
        "pre_event_context": copy.deepcopy(context["pre_event_context"]), "post_event_context": copy.deepcopy(context["post_event_context"]),
        "matched_normal_reference": copy.deepcopy(context["matched_normal_reference"]),
        "source_variables": [source], "target_variables": [target], "operating_regime": context["operating_regime"],
        "candidate_lag_range": copy.deepcopy(context["candidate_lag_range"]), "data_split": "calibration",
        "dataset_version": context["dataset_version"], "selection_policy": copy.deepcopy(context["selection_policy"]),
        "selection_policy_hash": context["selection_policy_hash"], "supported_claims": copy.deepcopy(context["supported_claims"]),
        "prohibited_claims": ["physical_causality", "root_cause", "universal_invariant"], "raw_values_included": False,
    })
    try:
        target_artifact = parse_evidence_package(document)
    except ValueError as exc:
        return _result(source_type, source_hash, "evidence_package", "invalid_source", mappings, reasons=(f"target validation failed: {getattr(exc, 'issue_code', 'MODEL_ERROR')}",))
    return _created(source_type, source_hash, "evidence_package", mappings, target_artifact, target_artifact.artifact_hash,
                    information=("raw trigger and response arrays are omitted", "aggregate support is not copied into the closed target schema"))


def adapt_phase1_calibration_parameter(
    calibration_record: Mapping[str, Any], *, mapping: Mapping[str, Any]
) -> ContractAdapterResult:
    source_hash = _combined_source_hash((calibration_record,))
    field_mappings = (
        AdapterFieldMapping("value", "value", "preserved exactly"),
        AdapterFieldMapping("unit", "unit", "preserved exactly"),
        AdapterFieldMapping("parameter_name", "parameter_role", "explicit mapping specification"),
        AdapterFieldMapping("method", "calibration_method", "explicit mapping specification"),
    )
    source_type = str(calibration_record.get("artifact_type", "unknown"))
    if source_type != "calibration_record":
        return _result(source_type, source_hash, "parameter_registry", "invalid_source", field_mappings, reasons=("source artifact_type must be calibration_record",))
    required = ("source_parameter_name", "source_method", "target_parameter_id", "target_parameter_role", "calibration_method",
                "relation_family", "source_variables", "target_variables", "operating_regime", "calibration_window_refs",
                "normal_reference_refs", "dataset_version", "code_commit", "calibrator_version", "sample_support",
                "stability_summary", "confidence_interval", "uncertainty", "target_approval_status", "source_context_status")
    missing = _missing(mapping, required)
    if missing:
        return _result(source_type, source_hash, "parameter_registry", "pending_context", field_mappings, required=missing)
    if mapping["source_parameter_name"] != calibration_record.get("parameter_name") or mapping["source_method"] != calibration_record.get("method"):
        return _result(source_type, source_hash, "parameter_registry", "unsupported_source", field_mappings, reasons=("explicit source mapping does not match calibration record",))
    if mapping["target_parameter_role"] == "severity_boundary" or str(mapping["target_parameter_id"]).startswith("PARAM-SEVERITY-"):
        return _result(source_type, source_hash, "parameter_registry", "unsupported_source", field_mappings, reasons=("adapter-generated severity parameters are prohibited",))
    status = mapping["target_approval_status"]
    if status not in {"proposed", "calibrated", "unstable", "rejected"}:
        return _result(source_type, source_hash, "parameter_registry", "unsupported_source", field_mappings, reasons=("adapter-generated approved status is prohibited",))
    if mapping["source_context_status"] == "synthetic_smoke" and status != "proposed":
        return _result(source_type, source_hash, "parameter_registry", "unsupported_source", field_mappings, reasons=("synthetic-smoke calibration cannot be promoted",))
    document = with_computed_artifact_hash({
        "schema_version": "1.0.0", "parameter_id": mapping["target_parameter_id"], "parameter_version": "1.0.0",
        "parameter_role": mapping["target_parameter_role"], "value": calibration_record.get("value"), "unit": calibration_record.get("unit"),
        "relation_family": mapping["relation_family"], "source_variables": copy.deepcopy(mapping["source_variables"]),
        "target_variables": copy.deepcopy(mapping["target_variables"]), "operating_regime": mapping["operating_regime"],
        "calibration_method": mapping["calibration_method"], "calibration_split": "calibration",
        "calibration_window_refs": copy.deepcopy(mapping["calibration_window_refs"]),
        "normal_reference_refs": copy.deepcopy(mapping["normal_reference_refs"]), "sample_support": copy.deepcopy(mapping["sample_support"]),
        "stability_summary": copy.deepcopy(mapping["stability_summary"]), "confidence_interval": copy.deepcopy(mapping["confidence_interval"]),
        "uncertainty": copy.deepcopy(mapping["uncertainty"]), "dataset_version": mapping["dataset_version"],
        "code_commit": mapping["code_commit"], "calibrator_version": mapping["calibrator_version"], "artifact_hash": "0" * 64,
        "approval_status": status, "approved_by": None, "approval_date": None,
    })
    try:
        target = parse_calibration_parameter(document)
    except ValueError as exc:
        return _result(source_type, source_hash, "parameter_registry", "invalid_source", field_mappings, reasons=(f"target validation failed: {getattr(exc, 'issue_code', 'MODEL_ERROR')}",))
    return _created(source_type, source_hash, "parameter_registry", field_mappings, target, target.artifact_hash)


def _origin_evidence_sources(origins: tuple[str, ...], ranked: bool) -> list[str]:
    mapping = {
        "domain": "subsystem_membership", "metadata_same_stage": "subsystem_membership",
        "statistical": "statistical_screening", "normal_statistical": "statistical_screening",
        "fallback": "type_compatibility", "type_compatible_fallback": "type_compatibility",
    }
    values = [mapping[item] for item in origins if item in mapping]
    if ranked:
        values.append("gdn_score")
    return sorted(set(values or ["type_compatibility"]))


def _edge_id(source: str, target: str) -> str:
    source_token = re.sub(r"[^A-Z0-9-]", "-", source.upper()).strip("-")
    target_token = re.sub(r"[^A-Z0-9-]", "-", target.upper()).strip("-")
    return f"EDGE-{source_token}-{target_token}"[:69].rstrip("-")


def _missing(context: Mapping[str, Any], required: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(name for name in required if name not in context or context[name] is None)


def _combined_source_hash(sources: Any) -> str:
    payload = copy.deepcopy(list(sources))
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _result(source_type: str, source_hash: str, target_type: str, status: str,
            mappings: tuple[AdapterFieldMapping, ...], *, required: tuple[str, ...] = (),
            information: tuple[str, ...] = (), warnings: tuple[str, ...] = (), reasons: tuple[str, ...] = ()) -> ContractAdapterResult:
    return ContractAdapterResult(PHASE1_ADAPTER_VERSION, source_type, source_hash, target_type, status, False, None,
                                 mappings, required, information, warnings, reasons, None)


def _created(source_type: str, source_hash: str, target_type: str, mappings: tuple[AdapterFieldMapping, ...],
             target: AdapterTarget, target_hash: str, *, information: tuple[str, ...] = ()) -> ContractAdapterResult:
    return ContractAdapterResult(PHASE1_ADAPTER_VERSION, source_type, source_hash, target_type, "created", True,
                                 target_hash, mappings, (), information, (), (), target)
