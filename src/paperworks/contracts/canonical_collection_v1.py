"""Dataset-neutral canonical delayed-response context collection for v6."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Mapping

from paperworks.contracts.evidence_v1 import (
    EvidenceLagRangeV1,
    EvidenceSelectionPolicyV1,
)
from paperworks.contracts.graph_v1 import (
    CandidateGraphV1,
    GraphEdgeV1,
    candidate_graph_to_dict,
    parse_candidate_graph,
)
from paperworks.contracts.normal_evidence_binding_v1 import (
    NormalReferenceSetBindingV1,
    RuleEvidenceBindingV1,
    SourceIdentifierBindingV1,
)
from paperworks.contracts.parameter_v1 import (
    CalibrationParameterV1,
    calibration_parameter_to_dict,
    parse_calibration_parameter,
)
from paperworks.data.contracts_v2 import (
    DataViewManifestV2,
    DatasetManifestV2,
    SplitManifestV2,
    SplitRoleV2,
)
from paperworks.v6.common import (
    CreationMetadataV1,
    V6_FOUNDATION_SCHEMA_VERSION,
    V6FoundationError,
    canonical_json_v1,
    require_identifier,
    require_sha256,
    stable_hash_v1,
)
from paperworks.v6.normal_evidence_v1 import (
    CalibrationParameterRoleV1,
    EvidenceStatusV1,
    NormalRelationEvidenceV1,
    ResponseDirectionV1,
    StabilityStatusV1,
)


CANONICAL_CONTEXT_BUILD_RESULT_ARTIFACT_TYPE = (
    "canonical_context_build_result"
)
CANONICAL_COLLECTION_ARTIFACT_TYPE = (
    "canonical_delayed_response_artifact_collection"
)
CANONICAL_CONTEXT_STATUSES = frozenset(
    {"created", "pending_context", "unsupported_source", "invalid_source"}
)
_REQUIRED_CANONICAL_ROLES = frozenset(
    {
        "tolerance",
        "persistence_duration",
        "minimum_support",
        "severity_boundary",
    }
)
_LAG_ROLES = frozenset({"lag_maximum", "response_delay"})


def canonical_graph_edge_sha256_v1(
    graph: CandidateGraphV1, edge_id: str
) -> str:
    """Hash the exact canonical edge member used by a P1B edge reference."""

    document = candidate_graph_to_dict(graph)
    matches = [
        item for item in document["edges"] if item["edge_id"] == edge_id
    ]
    if len(matches) != 1:
        raise V6FoundationError(
            "canonical graph edge must exist exactly once"
        )
    payload = json.dumps(
        matches[0],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CanonicalContextMappingsV1:
    edge_ids_by_source_hash: Mapping[str, str]
    condition_ids_by_source_hash: Mapping[str, str]
    condition_artifact_hashes_by_id: Mapping[str, str]
    parameter_ids_by_source_hash: Mapping[str, str]
    required_parameter_ids_by_role: Mapping[str, str]

    def __post_init__(self) -> None:
        for name in (
            "edge_ids_by_source_hash",
            "condition_ids_by_source_hash",
            "parameter_ids_by_source_hash",
        ):
            source = dict(getattr(self, name))
            for key, value in source.items():
                require_sha256(str(key), f"{name}.source_hash")
                require_identifier(str(value), f"{name}.canonical_id")
            object.__setattr__(
                self,
                name,
                MappingProxyType(
                    {str(key): str(value) for key, value in source.items()}
                ),
            )
        condition_hashes = dict(self.condition_artifact_hashes_by_id)
        for condition_id, artifact_hash in condition_hashes.items():
            require_identifier(str(condition_id), "condition_artifact_id")
            require_sha256(
                str(artifact_hash), "condition_artifact_hash"
            )
        object.__setattr__(
            self,
            "condition_artifact_hashes_by_id",
            MappingProxyType(
                {
                    str(condition_id): str(artifact_hash)
                    for condition_id, artifact_hash
                    in condition_hashes.items()
                }
            ),
        )
        roles = dict(self.required_parameter_ids_by_role)
        for role, parameter_id in roles.items():
            require_identifier(str(role), "required_parameter_role")
            require_identifier(str(parameter_id), "required_parameter_id")
        object.__setattr__(
            self,
            "required_parameter_ids_by_role",
            MappingProxyType(
                {
                    str(role): str(parameter_id)
                    for role, parameter_id in roles.items()
                }
            ),
        )


@dataclass(frozen=True)
class CanonicalBindingPolicyV1:
    matching_policy_id: str
    matching_policy_version: str
    matching_method: str
    deterministic_tie_breaking: bool
    selection_policy_id: str
    selection_policy_version: str
    selection_pre_registered: bool

    def __post_init__(self) -> None:
        for name, value in (
            ("matching_policy_id", self.matching_policy_id),
            ("matching_policy_version", self.matching_policy_version),
            ("matching_method", self.matching_method),
            ("selection_policy_id", self.selection_policy_id),
            ("selection_policy_version", self.selection_policy_version),
        ):
            require_identifier(value, name)
        if (
            not self.deterministic_tie_breaking
            or not self.selection_pre_registered
        ):
            raise V6FoundationError(
                "canonical binding policies must be deterministic and pre-registered"
            )


@dataclass(frozen=True)
class CanonicalDelayedResponseArtifactCollectionV1:
    dataset_manifest: DatasetManifestV2
    data_view: DataViewManifestV2
    split_manifest: SplitManifestV2
    normal_relation_evidence: NormalRelationEvidenceV1
    graph: CandidateGraphV1
    evidence: RuleEvidenceBindingV1
    normal_reference_binding: NormalReferenceSetBindingV1
    parameters: tuple[CalibrationParameterV1, ...]
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = CANONICAL_COLLECTION_ARTIFACT_TYPE

    def __post_init__(self) -> None:
        if self.schema_version != V6_FOUNDATION_SCHEMA_VERSION:
            raise V6FoundationError(
                "unsupported canonical collection schema_version"
            )
        if self.artifact_type != CANONICAL_COLLECTION_ARTIFACT_TYPE:
            raise V6FoundationError(
                "invalid canonical collection artifact_type"
            )
        if not self.parameters:
            raise V6FoundationError(
                "canonical collection requires parameter artifacts"
            )
        parameter_ids = tuple(item.parameter_id for item in self.parameters)
        if len(parameter_ids) != len(set(parameter_ids)):
            raise V6FoundationError(
                "canonical collection parameter IDs must be unique"
            )
        DatasetManifestV2.from_dict(self.dataset_manifest.to_dict())
        DataViewManifestV2.from_dict(self.data_view.to_dict())
        SplitManifestV2.from_dict(self.split_manifest.to_dict())
        NormalRelationEvidenceV1.from_dict(
            self.normal_relation_evidence.to_dict()
        )
        parse_candidate_graph(candidate_graph_to_dict(self.graph))
        RuleEvidenceBindingV1.from_dict(self.evidence.to_dict())
        NormalReferenceSetBindingV1.from_dict(
            self.normal_reference_binding.to_dict()
        )
        for parameter in self.parameters:
            parse_calibration_parameter(
                calibration_parameter_to_dict(parameter)
            )
        _validate_canonical_collection(self)

    @property
    def graph_by_id(self) -> Mapping[str, CandidateGraphV1]:
        return MappingProxyType({self.graph.graph_id: self.graph})

    @property
    def edge_by_id(self) -> Mapping[str, GraphEdgeV1]:
        return MappingProxyType(
            {edge.edge_id: edge for edge in self.graph.edges}
        )

    @property
    def evidence_by_id(self) -> Mapping[str, RuleEvidenceBindingV1]:
        return MappingProxyType({self.evidence.evidence_id: self.evidence})

    @property
    def normal_reference_by_id(
        self,
    ) -> Mapping[str, NormalReferenceSetBindingV1]:
        return MappingProxyType(
            {
                self.normal_reference_binding.normal_reference_id: (
                    self.normal_reference_binding
                )
            }
        )

    @property
    def parameter_by_id(self) -> Mapping[str, CalibrationParameterV1]:
        return MappingProxyType(
            {
                parameter.parameter_id: parameter
                for parameter in self.parameters
            }
        )

    @property
    def rule_binding_verified(self) -> bool:
        return False

    @property
    def runtime_authorized(self) -> bool:
        return False

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "dataset_manifest": self.dataset_manifest.to_dict(),
            "data_view": self.data_view.to_dict(),
            "split_manifest": self.split_manifest.to_dict(),
            "normal_relation_evidence": (
                self.normal_relation_evidence.to_dict()
            ),
            "graph": candidate_graph_to_dict(self.graph),
            "evidence": self.evidence.to_dict(),
            "normal_reference_binding": (
                self.normal_reference_binding.to_dict()
            ),
            "parameters": [
                calibration_parameter_to_dict(item)
                for item in self.parameters
            ],
            "rule_binding_verified": self.rule_binding_verified,
            "runtime_authorized": self.runtime_authorized,
        }

    @property
    def collection_id(self) -> str:
        digest = stable_hash_v1(self._content_dict())
        return f"COLL-V6-{digest[:20].upper()}"

    @property
    def artifact_hash(self) -> str:
        payload = self._content_dict()
        payload["collection_id"] = self.collection_id
        return stable_hash_v1(payload)

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["collection_id"] = self.collection_id
        payload["artifact_hash"] = self.artifact_hash
        return payload


@dataclass(frozen=True)
class CanonicalContextBuildResultV1:
    status: str
    collection: CanonicalDelayedResponseArtifactCollectionV1 | None
    normal_reference_binding: NormalReferenceSetBindingV1 | None
    rule_evidence_binding: RuleEvidenceBindingV1 | None
    missing_context: tuple[str, ...]
    information_loss: tuple[str, ...]
    issue_codes: tuple[str, ...]
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = CANONICAL_CONTEXT_BUILD_RESULT_ARTIFACT_TYPE

    def __post_init__(self) -> None:
        if self.schema_version != V6_FOUNDATION_SCHEMA_VERSION:
            raise V6FoundationError(
                "unsupported canonical context build schema_version"
            )
        if self.artifact_type != CANONICAL_CONTEXT_BUILD_RESULT_ARTIFACT_TYPE:
            raise V6FoundationError(
                "invalid canonical context build artifact_type"
            )
        if self.status not in CANONICAL_CONTEXT_STATUSES:
            raise V6FoundationError("unsupported canonical context status")
        complete = (
            self.collection is not None
            and self.normal_reference_binding is not None
            and self.rule_evidence_binding is not None
        )
        if self.status == "created" and not complete:
            raise V6FoundationError(
                "created canonical context requires complete bindings"
            )
        if self.status != "created" and any(
            item is not None
            for item in (
                self.collection,
                self.normal_reference_binding,
                self.rule_evidence_binding,
            )
        ):
            raise V6FoundationError(
                "failed canonical context cannot contain a partial target"
            )
        if len(self.missing_context) != len(set(self.missing_context)):
            raise V6FoundationError("missing_context values must be unique")
        if len(self.issue_codes) != len(set(self.issue_codes)):
            raise V6FoundationError("issue_codes must be unique")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "status": self.status,
            "collection": (
                self.collection.to_dict() if self.collection else None
            ),
            "normal_reference_binding": (
                self.normal_reference_binding.to_dict()
                if self.normal_reference_binding
                else None
            ),
            "rule_evidence_binding": (
                self.rule_evidence_binding.to_dict()
                if self.rule_evidence_binding
                else None
            ),
            "missing_context": list(self.missing_context),
            "information_loss": list(self.information_loss),
            "issue_codes": list(self.issue_codes),
            "creation_metadata": self.creation_metadata.to_dict(),
        }

    @property
    def build_result_id(self) -> str:
        digest = stable_hash_v1(self._content_dict())
        return f"CTXBUILD-V1-{digest[:20].upper()}"

    @property
    def artifact_hash(self) -> str:
        payload = self._content_dict()
        payload["build_result_id"] = self.build_result_id
        return stable_hash_v1(payload)

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["build_result_id"] = self.build_result_id
        payload["artifact_hash"] = self.artifact_hash
        return payload


def build_canonical_delayed_response_context_v1(
    *,
    dataset_manifest: DatasetManifestV2,
    data_view: DataViewManifestV2,
    split_manifest: SplitManifestV2,
    normal_evidence: NormalRelationEvidenceV1,
    graph: CandidateGraphV1,
    parameters: tuple[CalibrationParameterV1, ...],
    mappings: CanonicalContextMappingsV1,
    subsystem: str,
    binding_policy: CanonicalBindingPolicyV1,
    creation_metadata: CreationMetadataV1,
) -> CanonicalContextBuildResultV1:
    """Build a complete canonical context or return one fail-closed result."""

    if normal_evidence.evidence_status is not EvidenceStatusV1.SUPPORTED:
        return _failed_build(
            "unsupported_source",
            "NORMAL_EVIDENCE_NOT_SUPPORTED",
            creation_metadata,
        )
    if (
        normal_evidence.stability_summary.status
        is not StabilityStatusV1.STABLE
    ):
        return _failed_build(
            "unsupported_source",
            "NORMAL_EVIDENCE_UNSTABLE",
            creation_metadata,
        )
    if normal_evidence.response_direction is ResponseDirectionV1.DECREASE:
        return _failed_build(
            "unsupported_source",
            "DECREASE_RELATION_REQUIRES_FUTURE_RULE_FAMILY",
            creation_metadata,
        )

    missing: list[str] = []
    for source_hash in normal_evidence.candidate_edge_refs:
        if source_hash not in mappings.edge_ids_by_source_hash:
            missing.append(f"graph_edge_mapping:{source_hash}")
    for source_hash in normal_evidence.operating_regime_condition_refs:
        if source_hash not in mappings.condition_ids_by_source_hash:
            missing.append(f"regime_condition_mapping:{source_hash}")
        elif (
            mappings.condition_ids_by_source_hash[source_hash]
            not in mappings.condition_artifact_hashes_by_id
        ):
            missing.append(f"regime_condition_artifact:{source_hash}")
    for item in normal_evidence.calibration_parameter_refs:
        if item.artifact_ref not in mappings.parameter_ids_by_source_hash:
            missing.append(f"parameter_mapping:{item.role.value}")

    provided_by_id = {item.parameter_id: item for item in parameters}
    for role in sorted(
        _REQUIRED_CANONICAL_ROLES - {"tolerance"}
    ):
        if role not in mappings.required_parameter_ids_by_role:
            missing.append(f"canonical_parameter_role:{role}")
    if not any(
        role in mappings.required_parameter_ids_by_role
        for role in _LAG_ROLES
    ) and not any(
        item.role is CalibrationParameterRoleV1.LAG
        for item in normal_evidence.calibration_parameter_refs
    ):
        missing.append("canonical_parameter_role:lag")
    mapped_ids = set(mappings.parameter_ids_by_source_hash.values())
    mapped_ids.update(mappings.required_parameter_ids_by_role.values())
    for parameter_id in sorted(mapped_ids):
        if parameter_id not in provided_by_id:
            missing.append(f"canonical_parameter_artifact:{parameter_id}")
    if missing:
        return CanonicalContextBuildResultV1(
            status="pending_context",
            collection=None,
            normal_reference_binding=None,
            rule_evidence_binding=None,
            missing_context=tuple(sorted(set(missing))),
            information_loss=(),
            issue_codes=("CANONICAL_CONTEXT_MISSING",),
            creation_metadata=creation_metadata,
        )

    try:
        DatasetManifestV2.from_dict(dataset_manifest.to_dict())
        DataViewManifestV2.from_dict(data_view.to_dict())
        SplitManifestV2.from_dict(split_manifest.to_dict())
        NormalRelationEvidenceV1.from_dict(normal_evidence.to_dict())
        parse_candidate_graph(candidate_graph_to_dict(graph))
        for parameter in parameters:
            parse_calibration_parameter(
                calibration_parameter_to_dict(parameter)
            )

        edge_bindings = _build_edge_bindings(
            normal_evidence, graph, mappings
        )
        condition_bindings = tuple(
            SourceIdentifierBindingV1(
                source_artifact_hash=source_hash,
                canonical_id=mappings.condition_ids_by_source_hash[
                    source_hash
                ],
                canonical_artifact_hash=(
                    mappings.condition_artifact_hashes_by_id[
                        mappings.condition_ids_by_source_hash[source_hash]
                    ]
                ),
            )
            for source_hash in normal_evidence.operating_regime_condition_refs
        )
        parameter_bindings = _build_parameter_bindings(
            normal_evidence, provided_by_id, mappings
        )
        selected_parameter_ids = tuple(
            sorted(
                set(item.canonical_id for item in parameter_bindings)
                | set(mappings.required_parameter_ids_by_role.values())
            )
        )
        selected_parameters = tuple(
            provided_by_id[item] for item in selected_parameter_ids
        )
        _validate_parameter_roles(
            normal_evidence,
            selected_parameters,
            mappings,
        )

        normal_binding = NormalReferenceSetBindingV1(
            normal_relation_evidence_id=normal_evidence.evidence_id,
            normal_relation_evidence_hash=normal_evidence.artifact_hash,
            source_normal_reference_hashes=(
                normal_evidence.matched_normal_reference_refs
            ),
            dataset_manifest_id=normal_evidence.dataset_manifest_id,
            data_view_id=normal_evidence.data_view_id,
            split_manifest_id=normal_evidence.split_manifest_id,
            dataset_version=dataset_manifest.dataset_version_or_edition,
            process_scope=normal_evidence.process_scope,
            subsystem=subsystem,
            operating_regime_id=normal_evidence.operating_regime_id,
            matching_policy_id=binding_policy.matching_policy_id,
            matching_policy_version=(
                binding_policy.matching_policy_version
            ),
            matching_method=binding_policy.matching_method,
            deterministic_tie_breaking=(
                binding_policy.deterministic_tie_breaking
            ),
            label_performance_used=False,
            raw_values_included=False,
            creation_metadata=creation_metadata,
            authority_granted=False,
        )
        for parameter in selected_parameters:
            if normal_binding.normal_reference_id not in (
                parameter.normal_reference_refs
            ):
                raise V6FoundationError(
                    "canonical parameter omits the generated normal-reference ID"
                )

        if normal_evidence.lag_summary is None:
            raise V6FoundationError(
                "supported evidence requires a lag summary"
            )
        selection_policy = EvidenceSelectionPolicyV1(
            policy_id=binding_policy.selection_policy_id,
            policy_version=binding_policy.selection_policy_version,
            regime_match_required=True,
            subsystem_match_required=True,
            label_performance_used=False,
            deterministic_tie_breaking=True,
            pre_registered=binding_policy.selection_pre_registered,
        )
        evidence_binding = RuleEvidenceBindingV1(
            normal_relation_evidence_id=normal_evidence.evidence_id,
            normal_relation_evidence_hash=normal_evidence.artifact_hash,
            dataset_manifest_id=normal_evidence.dataset_manifest_id,
            data_view_id=normal_evidence.data_view_id,
            split_manifest_id=normal_evidence.split_manifest_id,
            dataset_version=dataset_manifest.dataset_version_or_edition,
            process_scope=normal_evidence.process_scope,
            subsystem=subsystem,
            source_variables=(normal_evidence.source_variable,),
            target_variables=(normal_evidence.target_variable,),
            operating_regime_id=normal_evidence.operating_regime_id,
            operating_regime_condition_bindings=condition_bindings,
            graph_edge_refs=tuple(
                item.canonical_id for item in edge_bindings
            ),
            graph_edge_source_bindings=edge_bindings,
            normal_reference_binding_ref=(
                normal_binding.normal_reference_id
            ),
            normal_reference_binding_hash=normal_binding.artifact_hash,
            parameter_artifact_refs=selected_parameter_ids,
            parameter_source_bindings=parameter_bindings,
            candidate_lag_range=EvidenceLagRangeV1(
                normal_evidence.lag_summary.minimum,
                normal_evidence.lag_summary.maximum,
                normal_evidence.lag_summary.unit,
            ),
            supported_claims=(
                "state_conditioned_response",
                "typical_lag",
            ),
            prohibited_claims=normal_evidence.prohibited_claims,
            selection_policy=selection_policy,
            data_split="normal_relation_calibration",
            raw_values_included=False,
            label_performance_used=False,
            detector_context_used=False,
            creation_metadata=creation_metadata,
            validity_authority_granted=False,
            runtime_authority_granted=False,
        )
        collection = CanonicalDelayedResponseArtifactCollectionV1(
            dataset_manifest=dataset_manifest,
            data_view=data_view,
            split_manifest=split_manifest,
            normal_relation_evidence=normal_evidence,
            graph=graph,
            evidence=evidence_binding,
            normal_reference_binding=normal_binding,
            parameters=selected_parameters,
        )
    except (KeyError, TypeError, ValueError) as exc:
        return CanonicalContextBuildResultV1(
            status="invalid_source",
            collection=None,
            normal_reference_binding=None,
            rule_evidence_binding=None,
            missing_context=(),
            information_loss=(),
            issue_codes=(f"CANONICAL_CONTEXT_INVALID:{type(exc).__name__}",),
            creation_metadata=creation_metadata,
        )

    return CanonicalContextBuildResultV1(
        status="created",
        collection=collection,
        normal_reference_binding=normal_binding,
        rule_evidence_binding=evidence_binding,
        missing_context=(),
        information_loss=(
            "binding creates identifiers only and adds no scientific observation",
        ),
        issue_codes=(),
        creation_metadata=creation_metadata,
    )


def _build_edge_bindings(
    evidence: NormalRelationEvidenceV1,
    graph: CandidateGraphV1,
    mappings: CanonicalContextMappingsV1,
) -> tuple[SourceIdentifierBindingV1, ...]:
    bindings: list[SourceIdentifierBindingV1] = []
    for source_hash in evidence.candidate_edge_refs:
        edge_id = mappings.edge_ids_by_source_hash[source_hash]
        observed_hash = canonical_graph_edge_sha256_v1(graph, edge_id)
        bindings.append(
            SourceIdentifierBindingV1(
                source_artifact_hash=source_hash,
                canonical_id=edge_id,
                canonical_artifact_hash=observed_hash,
            )
        )
    return tuple(bindings)


def _build_parameter_bindings(
    evidence: NormalRelationEvidenceV1,
    parameters_by_id: Mapping[str, CalibrationParameterV1],
    mappings: CanonicalContextMappingsV1,
) -> tuple[SourceIdentifierBindingV1, ...]:
    result: list[SourceIdentifierBindingV1] = []
    for source in evidence.calibration_parameter_refs:
        parameter_id = mappings.parameter_ids_by_source_hash[
            source.artifact_ref
        ]
        parameter = parameters_by_id[parameter_id]
        result.append(
            SourceIdentifierBindingV1(
                source_artifact_hash=source.artifact_ref,
                canonical_id=parameter_id,
                canonical_artifact_hash=parameter.artifact_hash,
            )
        )
    return tuple(result)


def _validate_parameter_roles(
    evidence: NormalRelationEvidenceV1,
    parameters: tuple[CalibrationParameterV1, ...],
    mappings: CanonicalContextMappingsV1,
) -> None:
    by_id = {item.parameter_id: item for item in parameters}
    by_role = {item.parameter_role: item for item in parameters}
    for reference in evidence.calibration_parameter_refs:
        parameter = by_id[
            mappings.parameter_ids_by_source_hash[reference.artifact_ref]
        ]
        expected = {
            CalibrationParameterRoleV1.LAG: _LAG_ROLES,
            CalibrationParameterRoleV1.TOLERANCE: frozenset({"tolerance"}),
            CalibrationParameterRoleV1.PERSISTENCE: frozenset(
                {"persistence_duration"}
            ),
        }[reference.role]
        if parameter.parameter_role not in expected:
            raise V6FoundationError(
                "P1B parameter role disagrees with canonical parameter role"
            )
    for role, parameter_id in mappings.required_parameter_ids_by_role.items():
        parameter = by_id[parameter_id]
        if parameter.parameter_role != role:
            raise V6FoundationError(
                "required parameter role mapping disagrees with artifact"
            )
    if not _REQUIRED_CANONICAL_ROLES.issubset(by_role):
        raise V6FoundationError(
            "required delayed-response parameter roles are incomplete"
        )
    if not (_LAG_ROLES & set(by_role)):
        raise V6FoundationError("canonical lag parameter is missing")


def _validate_canonical_collection(
    collection: CanonicalDelayedResponseArtifactCollectionV1,
) -> None:
    dataset = collection.dataset_manifest
    view = collection.data_view
    split = collection.split_manifest
    source = collection.normal_relation_evidence
    evidence = collection.evidence
    normal = collection.normal_reference_binding
    if not (
        dataset.manifest_id
        == view.source_dataset_manifest_id
        == split.dataset_manifest_id
        == source.dataset_manifest_id
        == evidence.dataset_manifest_id
    ):
        raise V6FoundationError("dataset manifest identities disagree")
    if not (
        view.view_id
        == split.data_view_id
        == source.data_view_id
        == evidence.data_view_id
    ):
        raise V6FoundationError("data view identities disagree")
    if split.split_id != source.split_manifest_id or (
        split.split_id != evidence.split_manifest_id
    ):
        raise V6FoundationError("split manifest identities disagree")
    if split.role is not SplitRoleV2.NORMAL_RELATION_CALIBRATION:
        raise V6FoundationError(
            "canonical collection requires normal relation calibration"
        )
    scopes = (
        view.process_scope,
        split.process_scope,
        source.process_scope,
        evidence.process_scope,
    )
    if any(scope is None for scope in scopes) or len(set(scopes)) != 1:
        raise V6FoundationError("process scope bindings disagree")
    if len(source.process_scope) != 1:
        raise V6FoundationError(
            "first canonical delayed-response collection binds one process"
        )
    if collection.graph.dataset_version != (
        dataset.dataset_version_or_edition
    ):
        raise V6FoundationError("graph dataset version disagrees")
    nodes = {
        node.variable_name: node for node in collection.graph.nodes
    }
    source_node = nodes.get(source.source_variable)
    target_node = nodes.get(source.target_variable)
    if source_node is None or target_node is None:
        raise V6FoundationError(
            "graph does not contain the normal-evidence variables"
        )
    if (
        source_node.metadata_provenance.artifact_hash
        != source.source_metadata_ref
        or target_node.metadata_provenance.artifact_hash
        != source.target_metadata_ref
    ):
        raise V6FoundationError("graph metadata hashes disagree")
    if len(
        {
            source_node.subsystem,
            target_node.subsystem,
            evidence.subsystem,
        }
    ) != 1:
        raise V6FoundationError("graph subsystem bindings disagree")
    edge = collection.edge_by_id.get(evidence.graph_edge_refs[0])
    if edge is None or (
        edge.source_node != source_node.node_id
        or edge.target_node != target_node.node_id
        or edge.direction != "directed"
    ):
        raise V6FoundationError("graph edge direction is invalid")
    if source.relation_family not in edge.relation_family_candidates:
        raise V6FoundationError("graph edge relation family disagrees")
    if tuple(
        item.source_artifact_hash
        for item in evidence.graph_edge_source_bindings
    ) != source.candidate_edge_refs:
        raise V6FoundationError("graph edge source references disagree")
    for binding in evidence.graph_edge_source_bindings:
        if canonical_graph_edge_sha256_v1(
            collection.graph, binding.canonical_id
        ) != binding.source_artifact_hash:
            raise V6FoundationError("graph edge source hash disagrees")
    if tuple(
        item.source_artifact_hash
        for item in evidence.operating_regime_condition_bindings
    ) != source.operating_regime_condition_refs:
        raise V6FoundationError(
            "operating-regime condition bindings disagree"
        )
    lag = evidence.candidate_lag_range
    graph_lag = edge.lag_candidate_range
    if (
        lag.unit != graph_lag.unit
        or lag.minimum < graph_lag.minimum
        or lag.maximum > graph_lag.maximum
    ):
        raise V6FoundationError(
            "evidence lag range is outside the graph candidate range"
        )
    if not (
        normal.normal_relation_evidence_id == source.evidence_id
        and normal.normal_relation_evidence_hash == source.artifact_hash
        and evidence.normal_relation_evidence_id == source.evidence_id
        and evidence.normal_relation_evidence_hash == source.artifact_hash
    ):
        raise V6FoundationError("normal evidence bindings disagree")
    if (
        evidence.normal_reference_binding_ref
        != normal.normal_reference_id
        or evidence.normal_reference_binding_hash != normal.artifact_hash
    ):
        raise V6FoundationError("normal-reference binding disagrees")
    parameters = collection.parameter_by_id
    if set(parameters) != set(evidence.parameter_artifact_refs):
        raise V6FoundationError(
            "collection parameter set differs from evidence binding"
        )
    for binding in evidence.parameter_source_bindings:
        parameter = parameters.get(binding.canonical_id)
        if parameter is None or (
            parameter.artifact_hash != binding.source_artifact_hash
        ):
            raise V6FoundationError("parameter source binding disagrees")
    for parameter in collection.parameters:
        if not (
            parameter.dataset_version == evidence.dataset_version
            and parameter.source_variables == evidence.source_variables
            and parameter.target_variables == evidence.target_variables
            and parameter.operating_regime == evidence.operating_regime_id
            and normal.normal_reference_id
            in parameter.normal_reference_refs
        ):
            raise V6FoundationError("parameter context binding disagrees")
    if (
        source.evidence_status is not EvidenceStatusV1.SUPPORTED
        or source.stability_summary.status is not StabilityStatusV1.STABLE
        or not source.matched_normal_reference_refs
        or source.label_performance_used
        or source.detector_context_used
        or source.raw_values_included
    ):
        raise V6FoundationError(
            "normal evidence does not satisfy canonical support boundaries"
        )
    if (
        collection.rule_binding_verified
        or collection.runtime_authorized
        or evidence.validity_authority_granted
        or evidence.runtime_authority_granted
        or normal.authority_granted
    ):
        raise V6FoundationError(
            "canonical collection cannot grant verifier or runtime authority"
        )


def _failed_build(
    status: str,
    issue_code: str,
    creation_metadata: CreationMetadataV1,
) -> CanonicalContextBuildResultV1:
    return CanonicalContextBuildResultV1(
        status=status,
        collection=None,
        normal_reference_binding=None,
        rule_evidence_binding=None,
        missing_context=(),
        information_loss=(),
        issue_codes=(issue_code,),
        creation_metadata=creation_metadata,
    )
