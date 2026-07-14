"""Deterministic twenty-stage delayed-response rule binding verifier."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

from paperworks.contracts.accepted_rule import (
    canonical_rule_verification_subject_sha256,
    materialize_accepted_rule,
)
from paperworks.contracts.artifact_hashing import (
    ContractArtifactHashError,
    canonical_contract_artifact_sha256,
    verify_contract_artifact_hash,
    with_computed_artifact_hash,
)
from paperworks.contracts.evidence_v1 import (
    EvidencePackageV1,
    evidence_package_to_dict,
    parse_evidence_package,
)
from paperworks.contracts.graph_v1 import (
    CandidateGraphV1,
    GraphEdgeV1,
    GraphNodeV1,
    candidate_graph_to_dict,
    parse_candidate_graph,
)
from paperworks.contracts.parameter_v1 import (
    CalibrationParameterV1,
    calibration_parameter_to_dict,
    parse_calibration_parameter,
)
from paperworks.contracts.phase1_adapters import DelayedResponseArtifactCollectionV1
from paperworks.contracts.rule_v1 import (
    DelayedResponseRuleV1,
    canonical_rule_document_sha256,
    delayed_response_rule_to_dict,
)
from paperworks.contracts.schema_registry import SchemaRegistry, load_schema_registry


_TIME_FACTORS = {"milliseconds": 0.001, "seconds": 1.0, "minutes": 60.0}
_COUNT_UNITS = frozenset({"count", "events", "samples"})
_SEVERITY_UNITS = frozenset({"score", "severity", "unitless"})
_REQUIRED_PROHIBITED_CLAIMS = frozenset({"physical_causality", "root_cause", "universal_invariant"})
_AGGREGATE_FIELDS = frozenset({
    "trigger", "relation_type", "expected_effect", "lag", "window", "persistence",
    "parameter_refs", "tolerance_ref", "output_semantics", "severity_policy",
    "abstention_policy", "rule_id", "schema_version", "dataset_version",
    "evidence_refs", "graph_edge_refs", "verified_parameter_values", "final_test_boundaries",
})


class VerifierV1Error(ValueError):
    def __init__(self, issue_code: str, message: str) -> None:
        super().__init__(f"{issue_code}: {message}")
        self.issue_code = issue_code
        self.message = message


@dataclass(frozen=True)
class VerifierIssueV1:
    code: str
    stage: int
    field: str
    message: str
    repairability: str

    def __post_init__(self) -> None:
        if self.repairability not in {"repairable", "non_repairable"}:
            raise VerifierV1Error("VERIFIER_ISSUE_INVALID", "repairability is invalid")


@dataclass(frozen=True)
class VerifierRelationRecordV1:
    record_id: str
    related_rule_id: str
    relation: str


@dataclass(frozen=True)
class VerifierResultV1:
    schema_version: str
    verifier_result_id: str
    artifact_hash: str
    rule_id: str
    rule_hash: str
    verifier_version: str
    status: str
    violations: tuple[VerifierIssueV1, ...]
    warnings: tuple[VerifierIssueV1, ...]
    repairable_fields: tuple[str, ...]
    non_repairable_fields: tuple[str, ...]
    verified_graph_edges: tuple[str, ...]
    verified_parameters: tuple[str, ...]
    verified_evidence: tuple[str, ...]
    verified_normal_references: tuple[str, ...]
    complexity_score: int
    conflict_records: tuple[VerifierRelationRecordV1, ...]
    duplicate_records: tuple[VerifierRelationRecordV1, ...]
    created_at: str

    @property
    def runtime_authorized(self) -> bool:
        return False


@dataclass(frozen=True)
class VerifierStageRecordV1:
    stage: int
    name: str
    status: str
    issues: tuple[VerifierIssueV1, ...]

    def __post_init__(self) -> None:
        if self.status not in {"passed", "failed", "skipped_due_to_prior_failure"}:
            raise VerifierV1Error("VERIFIER_STAGE_INVALID", "stage status is invalid")


@dataclass(frozen=True)
class DelayedResponseVerifierPolicyV1:
    verifier_version: str
    created_at: str
    maximum_operator_count: int
    maximum_variable_count: int
    maximum_depth: int
    allowed_parameter_uncertainty: tuple[str, ...]
    time_comparison_tolerance: float
    accepted_rule_library_policy: str

    def __post_init__(self) -> None:
        if not self.verifier_version or not self.created_at:
            raise VerifierV1Error("VERIFIER_POLICY_INVALID", "version and created_at are required")
        if min(self.maximum_operator_count, self.maximum_variable_count, self.maximum_depth) < 0:
            raise VerifierV1Error("VERIFIER_POLICY_INVALID", "complexity limits must be non-negative")
        if self.time_comparison_tolerance < 0:
            raise VerifierV1Error("VERIFIER_POLICY_INVALID", "time comparison tolerance must be non-negative")
        if self.accepted_rule_library_policy != "reject_structural_duplicates":
            raise VerifierV1Error("VERIFIER_POLICY_INVALID", "unsupported accepted-library policy")

    @classmethod
    def from_dict(cls, document: Mapping[str, Any]) -> "DelayedResponseVerifierPolicyV1":
        return cls(
            verifier_version=str(document["verifier_version"]),
            created_at=str(document["created_at"]),
            maximum_operator_count=int(document["maximum_operator_count"]),
            maximum_variable_count=int(document["maximum_variable_count"]),
            maximum_depth=int(document["maximum_depth"]),
            allowed_parameter_uncertainty=tuple(str(item) for item in document["allowed_parameter_uncertainty"]),
            time_comparison_tolerance=float(document["time_comparison_tolerance"]),
            accepted_rule_library_policy=str(document["accepted_rule_library_policy"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "verifier_version": self.verifier_version,
            "created_at": self.created_at,
            "maximum_operator_count": self.maximum_operator_count,
            "maximum_variable_count": self.maximum_variable_count,
            "maximum_depth": self.maximum_depth,
            "allowed_parameter_uncertainty": list(self.allowed_parameter_uncertainty),
            "time_comparison_tolerance": self.time_comparison_tolerance,
            "accepted_rule_library_policy": self.accepted_rule_library_policy,
        }


@dataclass(frozen=True)
class RuleVerificationOutcomeV1:
    candidate_transport_hash: str
    verification_subject_hash: str
    accepted_rule: DelayedResponseRuleV1 | None
    verifier_result: VerifierResultV1
    verifier_result_hash: str
    stage_records: tuple[VerifierStageRecordV1, ...]
    runtime_authorized: bool = False

    def __post_init__(self) -> None:
        if self.runtime_authorized:
            raise VerifierV1Error("RUNTIME_AUTHORITY_PROHIBITED", "TASK-032D cannot authorize runtime")


@dataclass
class _VerificationContext:
    rule: DelayedResponseRuleV1
    artifacts: DelayedResponseArtifactCollectionV1
    policy: DelayedResponseVerifierPolicyV1
    accepted_library: Sequence[RuleVerificationOutcomeV1]
    registry: SchemaRegistry
    conflict_records: list[VerifierRelationRecordV1] = field(default_factory=list)
    duplicate_records: list[VerifierRelationRecordV1] = field(default_factory=list)

    @property
    def nodes_by_variable(self) -> dict[str, list[GraphNodeV1]]:
        result: dict[str, list[GraphNodeV1]] = {}
        for node in self.artifacts.graph.nodes:
            result.setdefault(node.variable_name, []).append(node)
        return result

    @property
    def edge(self) -> GraphEdgeV1 | None:
        if len(self.rule.graph_edge_refs) != 1:
            return None
        return self.artifacts.edge_by_id.get(self.rule.graph_edge_refs[0])

    @property
    def parameters(self) -> Mapping[str, CalibrationParameterV1]:
        return self.artifacts.parameter_by_id


def parse_verifier_result(
    document: Mapping[str, object], *, registry: SchemaRegistry | None = None
) -> VerifierResultV1:
    snapshot = copy.deepcopy(dict(document))
    report = (registry or load_schema_registry()).validate_artifact("verifier_result", snapshot)
    if report.status != "valid":
        issue = report.issues[0] if report.issues else None
        raise VerifierV1Error("VERIFIER_RESULT_STRUCTURAL_INVALID", issue.issue_code if issue else "registry error")
    try:
        verify_contract_artifact_hash(snapshot)
    except ContractArtifactHashError as exc:
        raise VerifierV1Error(exc.issue_code, exc.message) from exc
    repairable = set(snapshot["repairable_fields"])
    non_repairable = set(snapshot["non_repairable_fields"])
    return VerifierResultV1(
        schema_version=str(snapshot["schema_version"]), verifier_result_id=str(snapshot["verifier_result_id"]),
        artifact_hash=str(snapshot["artifact_hash"]), rule_id=str(snapshot["rule_id"]), rule_hash=str(snapshot["rule_hash"]),
        verifier_version=str(snapshot["verifier_version"]), status=str(snapshot["status"]),
        violations=tuple(_issue_from_document(item, repairable, non_repairable) for item in snapshot["violations"]),
        warnings=tuple(_issue_from_document(item, repairable, non_repairable) for item in snapshot["warnings"]),
        repairable_fields=tuple(snapshot["repairable_fields"]), non_repairable_fields=tuple(snapshot["non_repairable_fields"]),
        verified_graph_edges=tuple(snapshot["verified_graph_edges"]), verified_parameters=tuple(snapshot["verified_parameters"]),
        verified_evidence=tuple(snapshot["verified_evidence"]), verified_normal_references=tuple(snapshot["verified_normal_references"]),
        complexity_score=int(snapshot["complexity_score"]),
        conflict_records=tuple(_record_from_document(item) for item in snapshot["conflict_records"]),
        duplicate_records=tuple(_record_from_document(item) for item in snapshot["duplicate_records"]),
        created_at=str(snapshot["created_at"]),
    )


def verifier_result_to_dict(result: VerifierResultV1) -> dict[str, Any]:
    return {
        "schema_version": result.schema_version, "verifier_result_id": result.verifier_result_id,
        "artifact_hash": result.artifact_hash, "rule_id": result.rule_id, "rule_hash": result.rule_hash,
        "verifier_version": result.verifier_version, "status": result.status,
        "violations": [_issue_to_document(item) for item in result.violations],
        "warnings": [_issue_to_document(item) for item in result.warnings],
        "repairable_fields": list(result.repairable_fields), "non_repairable_fields": list(result.non_repairable_fields),
        "verified_graph_edges": list(result.verified_graph_edges), "verified_parameters": list(result.verified_parameters),
        "verified_evidence": list(result.verified_evidence),
        "verified_normal_references": list(result.verified_normal_references),
        "complexity_score": result.complexity_score,
        "conflict_records": [_record_to_document(item) for item in result.conflict_records],
        "duplicate_records": [_record_to_document(item) for item in result.duplicate_records],
        "created_at": result.created_at,
    }


def serialize_verifier_result(result: VerifierResultV1) -> str:
    return json.dumps(verifier_result_to_dict(result), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def canonical_verifier_result_sha256(result: VerifierResultV1) -> str:
    return canonical_contract_artifact_sha256(verifier_result_to_dict(result))


def canonical_verifier_binding_id(
    rule: DelayedResponseRuleV1,
    artifacts: DelayedResponseArtifactCollectionV1,
    *,
    policy: DelayedResponseVerifierPolicyV1,
    status: str,
    violations: Sequence[VerifierIssueV1],
) -> str:
    """Recompute the deterministic verifier-result identifier."""

    binding = {
        "subject_hash": canonical_rule_verification_subject_sha256(rule),
        "status": status,
        "graph_hash": artifacts.graph.artifact_hash,
        "evidence_hash": artifacts.evidence.artifact_hash,
        "parameter_hashes": sorted(item.artifact_hash for item in artifacts.parameters),
        "policy": policy.to_dict(),
        "issues": [_issue_to_document(item) for item in violations],
    }
    payload = json.dumps(binding, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return f"VERIFY-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:20].upper()}"


def verify_verifier_result_binding(
    rule: DelayedResponseRuleV1,
    result: VerifierResultV1,
    artifacts: DelayedResponseArtifactCollectionV1,
    *,
    policy: DelayedResponseVerifierPolicyV1,
) -> str:
    """Fail closed unless a result is the canonical binding for these inputs."""

    try:
        verify_contract_artifact_hash(verifier_result_to_dict(result))
    except ContractArtifactHashError as exc:
        raise VerifierV1Error("VERIFIER_RESULT_HASH_MISMATCH", "verifier-result self-hash failed") from exc
    subject_hash = canonical_rule_verification_subject_sha256(rule)
    if result.rule_id != rule.rule_id or result.rule_hash != subject_hash:
        raise VerifierV1Error("VERIFIER_RULE_BINDING_MISMATCH", "verifier result does not bind the supplied rule")
    if result.verifier_version != policy.verifier_version:
        raise VerifierV1Error("VERIFIER_POLICY_MISMATCH", "verifier version differs from policy")
    expected = canonical_verifier_binding_id(
        rule,
        artifacts,
        policy=policy,
        status=result.status,
        violations=result.violations,
    )
    if result.verifier_result_id != expected:
        raise VerifierV1Error("VERIFIER_RESULT_ID_MISMATCH", "verifier-result identifier does not recompute")
    return expected


def verify_delayed_response_rule(
    rule: DelayedResponseRuleV1,
    artifacts: DelayedResponseArtifactCollectionV1,
    *,
    policy: DelayedResponseVerifierPolicyV1,
    accepted_library: Sequence[RuleVerificationOutcomeV1] = (),
) -> RuleVerificationOutcomeV1:
    context = _VerificationContext(rule, artifacts, policy, tuple(accepted_library), load_schema_registry())
    stage_functions: tuple[tuple[str, Callable[[_VerificationContext], list[VerifierIssueV1]]], ...] = (
        ("structural_schema_validation", _stage_1), ("type_validation", _stage_2),
        ("variable_allowlist", _stage_3), ("subsystem_compatibility", _stage_4),
        ("graph_edge_validation", _stage_5), ("relation_family_compatibility", _stage_6),
        ("unit_compatibility", _stage_7), ("lag_bound_validation", _stage_8),
        ("window_and_persistence_validation", _stage_9), ("parameter_existence_and_approval", _stage_10),
        ("parameter_provenance", _stage_11), ("split_policy_validation", _stage_12),
        ("evidence_reference_validation", _stage_13), ("normal_reference_validation", _stage_14),
        ("conflict_detection", _stage_15), ("duplicate_and_subsumption_detection", _stage_16),
        ("complexity_budget_validation", _stage_17), ("output_contract_validation", _stage_18),
        ("explanation_provenance_validation", _stage_19), ("claim_and_authority_boundary", _stage_20),
    )
    stage_records: list[VerifierStageRecordV1] = []
    structural_failed = False
    for number, (name, function) in enumerate(stage_functions, start=1):
        if structural_failed:
            stage_records.append(VerifierStageRecordV1(number, name, "skipped_due_to_prior_failure", ()))
            continue
        issues = tuple(sorted(function(context), key=_issue_sort_key))
        status = "failed" if issues else "passed"
        stage_records.append(VerifierStageRecordV1(number, name, status, issues))
        if number == 1 and issues:
            structural_failed = True

    violations = tuple(sorted((issue for stage in stage_records for issue in stage.issues), key=_issue_sort_key))
    status = "accepted" if not violations else (
        "needs_repair" if all(issue.repairability == "repairable" for issue in violations) else "rejected"
    )
    subject_hash = canonical_rule_verification_subject_sha256(rule)
    repairable_fields = tuple(sorted({item.field for item in violations if item.repairability == "repairable" and item.field in _AGGREGATE_FIELDS}))
    non_repairable_fields = tuple(sorted({item.field for item in violations if item.repairability == "non_repairable" and item.field in _AGGREGATE_FIELDS}))
    passed = {record.stage for record in stage_records if record.status == "passed"}
    verified_edges = tuple(rule.graph_edge_refs) if {3, 5, 6}.issubset(passed) else ()
    verified_evidence = tuple(rule.evidence_refs) if {6, 13}.issubset(passed) else ()
    verified_normal = tuple(rule.normal_reference_refs) if {13, 14}.issubset(passed) else ()
    verified_parameters = tuple(sorted(rule.parameter_refs)) if {7, 8, 9, 10, 11, 12, 14}.issubset(passed) else ()
    complexity_score = _complexity_score(rule)
    result_id = canonical_verifier_binding_id(
        rule, artifacts, policy=policy, status=status, violations=violations
    )
    provisional = {
        "schema_version": "1.0.0", "verifier_result_id": result_id, "artifact_hash": "0" * 64,
        "rule_id": rule.rule_id, "rule_hash": subject_hash, "verifier_version": policy.verifier_version,
        "status": status, "violations": [_issue_to_document(item) for item in violations], "warnings": [],
        "repairable_fields": list(repairable_fields), "non_repairable_fields": list(non_repairable_fields),
        "verified_graph_edges": list(verified_edges), "verified_parameters": list(verified_parameters),
        "verified_evidence": list(verified_evidence), "verified_normal_references": list(verified_normal),
        "complexity_score": complexity_score,
        "conflict_records": [_record_to_document(item) for item in sorted(context.conflict_records, key=lambda item: item.record_id)],
        "duplicate_records": [_record_to_document(item) for item in sorted(context.duplicate_records, key=lambda item: item.record_id)],
        "created_at": policy.created_at,
    }
    result = parse_verifier_result(with_computed_artifact_hash(provisional), registry=context.registry)
    accepted_rule = materialize_accepted_rule(rule) if status == "accepted" else None
    if accepted_rule is not None and not (
        accepted_rule.verified_rule_hash == result.rule_hash == subject_hash
    ):
        raise VerifierV1Error("VERIFIER_AUTHORITY_HASH_MISMATCH", "accepted binding hashes disagree")
    return RuleVerificationOutcomeV1(
        candidate_transport_hash=canonical_rule_document_sha256(rule), verification_subject_hash=subject_hash,
        accepted_rule=accepted_rule, verifier_result=result, verifier_result_hash=result.artifact_hash,
        stage_records=tuple(stage_records), runtime_authorized=False,
    )


def _stage_1(context: _VerificationContext) -> list[VerifierIssueV1]:
    checks: tuple[Callable[[], Any], ...] = (
        lambda: _require_structural_rule(context),
        lambda: parse_candidate_graph(candidate_graph_to_dict(context.artifacts.graph), registry=context.registry),
        lambda: parse_evidence_package(evidence_package_to_dict(context.artifacts.evidence), registry=context.registry),
        *(lambda parameter=parameter: parse_calibration_parameter(calibration_parameter_to_dict(parameter), registry=context.registry)
          for parameter in context.artifacts.parameters),
    )
    issues = []
    for check in checks:
        try:
            check()
        except ValueError:
            issues.append(_issue("STRUCTURAL_BINDING_INVALID", 1, "schema_version", "a bound artifact failed structural or hash validation", "non_repairable"))
    return issues[:1]


def _require_structural_rule(context: _VerificationContext) -> None:
    report = context.registry.validate_artifact("rule_dsl", delayed_response_rule_to_dict(context.rule))
    if report.status != "valid":
        raise VerifierV1Error("RULE_STRUCTURAL_INVALID", "rule failed canonical schema validation")


def _stage_2(context: _VerificationContext) -> list[VerifierIssueV1]:
    issues = []
    source = _single_node(context, context.rule.source_variables[0])
    target = _single_node(context, context.rule.target_variables[0])
    if source is not None and (source.node_type != "actuator" or source.data_type not in {"binary", "boolean"}):
        issues.append(_issue("SOURCE_TYPE_MISMATCH", 2, "graph_edge_refs", "source node must be a binary or boolean actuator", "non_repairable"))
    if target is not None and (target.node_type != "sensor" or target.data_type != "continuous"):
        issues.append(_issue("TARGET_TYPE_MISMATCH", 2, "graph_edge_refs", "target node must be a continuous sensor", "non_repairable"))
    return issues


def _stage_3(context: _VerificationContext) -> list[VerifierIssueV1]:
    issues = []
    for variable in context.rule.source_variables + context.rule.target_variables:
        if len(context.nodes_by_variable.get(variable, ())) != 1:
            issues.append(_issue("VARIABLE_NOT_FOUND", 3, "graph_edge_refs", "rule variable must occur exactly once in graph", "non_repairable"))
    return issues


def _stage_4(context: _VerificationContext) -> list[VerifierIssueV1]:
    source = _single_node(context, context.rule.source_variables[0])
    target = _single_node(context, context.rule.target_variables[0])
    values = {context.rule.subsystem, context.artifacts.evidence.matched_normal_reference.subsystem}
    if source is not None:
        values.add(source.subsystem)
    if target is not None:
        values.add(target.subsystem)
    return [] if len(values) == 1 else [_issue("SUBSYSTEM_MISMATCH", 4, "graph_edge_refs", "rule, nodes, and normal reference must share one subsystem", "non_repairable")]


def _stage_5(context: _VerificationContext) -> list[VerifierIssueV1]:
    if len(context.rule.graph_edge_refs) != 1:
        return [_issue("GRAPH_EDGE_CARDINALITY", 5, "graph_edge_refs", "exactly one graph edge is required", "non_repairable")]
    edge = context.edge
    if edge is None:
        return [_issue("GRAPH_EDGE_NOT_FOUND", 5, "graph_edge_refs", "referenced graph edge is absent", "non_repairable")]
    source = _single_node(context, context.rule.source_variables[0])
    target = _single_node(context, context.rule.target_variables[0])
    issues = []
    if source is not None and target is not None and (edge.source_node != source.node_id or edge.target_node != target.node_id):
        issues.append(_issue("GRAPH_DIRECTION_MISMATCH", 5, "graph_edge_refs", "edge endpoints do not match rule direction", "non_repairable"))
    if edge.source_node == edge.target_node:
        issues.append(_issue("GRAPH_SELF_EDGE", 5, "graph_edge_refs", "self-edge cannot bind a delayed-response rule", "non_repairable"))
    if edge.causal_claim_allowed:
        issues.append(_issue("GRAPH_CAUSAL_CLAIM", 5, "graph_edge_refs", "bound edge must remain candidate-only", "non_repairable"))
    return issues


def _stage_6(context: _VerificationContext) -> list[VerifierIssueV1]:
    issues = []
    if context.rule.relation_type != "delayed_response":
        issues.append(_issue("RELATION_FAMILY_UNSUPPORTED", 6, "relation_type", "only delayed_response is supported", "repairable"))
    edge = context.edge
    if edge is not None and "delayed_response" not in edge.relation_family_candidates:
        issues.append(_issue("EDGE_RELATION_UNSUPPORTED", 6, "graph_edge_refs", "edge does not register delayed_response", "non_repairable"))
    for parameter_id in context.rule.parameter_refs:
        parameter = context.parameters.get(parameter_id)
        if parameter is not None and parameter.relation_family != "delayed_response":
            issues.append(_issue("PARAMETER_RELATION_MISMATCH", 6, "verified_parameter_values", "parameter relation family disagrees", "non_repairable"))
    required_claims = {"state_conditioned_response", "typical_lag"}
    if not required_claims.issubset(context.artifacts.evidence.supported_claims):
        issues.append(_issue("EVIDENCE_CLAIMS_INSUFFICIENT", 6, "evidence_refs", "evidence lacks required delayed-response claims", "non_repairable"))
    return issues


def _stage_7(context: _VerificationContext) -> list[VerifierIssueV1]:
    issues = []
    for parameter_id in context.rule.parameter_refs:
        parameter = context.parameters.get(parameter_id)
        if parameter is None:
            continue
        role = parameter.parameter_role
        if role in {"lag_minimum", "lag_maximum", "response_delay", "persistence_duration"} and parameter.unit not in _TIME_FACTORS:
            issues.append(_issue("TIME_UNIT_MISMATCH", 7, "parameter_refs", "time parameter uses a non-time unit", "repairable"))
        if role == "tolerance":
            target = _single_node(context, context.rule.target_variables[0])
            if target is not None and parameter.unit != target.physical_unit:
                issues.append(_issue("TOLERANCE_UNIT_MISMATCH", 7, "tolerance_ref", "tolerance unit differs from target unit", "repairable"))
        if role == "minimum_support" and parameter.unit not in _COUNT_UNITS:
            issues.append(_issue("SUPPORT_UNIT_MISMATCH", 7, "parameter_refs", "minimum support requires a count unit", "repairable"))
        if role == "severity_boundary" and parameter.unit not in _SEVERITY_UNITS:
            issues.append(_issue("SEVERITY_UNIT_MISMATCH", 7, "severity_policy", "severity boundary requires a score unit", "repairable"))
    if context.rule.lag.unit not in _TIME_FACTORS or context.rule.window.unit not in _TIME_FACTORS:
        issues.append(_issue("RULE_TIME_UNIT_UNSUPPORTED", 7, "lag", "rule lag and window require supported time units", "repairable"))
    return issues


def _stage_8(context: _VerificationContext) -> list[VerifierIssueV1]:
    parameter = context.parameters.get(context.rule.lag.parameter_ref)
    edge = context.edge
    evidence = context.artifacts.evidence
    if parameter is None or edge is None:
        return []
    tolerance = context.policy.time_comparison_tolerance
    issues = []
    try:
        if context.rule.lag.lag_type == "fixed":
            if parameter.parameter_role != "response_delay":
                issues.append(_issue("FIXED_LAG_ROLE_MISMATCH", 8, "lag", "fixed lag requires response_delay", "repairable"))
            else:
                value = _convert_time(parameter.value, parameter.unit, context.rule.lag.unit)
                if not (_equal(context.rule.lag.minimum, value, tolerance) and _equal(context.rule.lag.maximum, value, tolerance)):
                    issues.append(_issue("FIXED_LAG_VALUE_MISMATCH", 8, "lag", "fixed lag differs from response delay", "repairable"))
        elif parameter.parameter_role == "lag_maximum":
            maximum = _convert_time(parameter.value, parameter.unit, context.rule.lag.unit)
            edge_min = _convert_time(edge.lag_candidate_range.minimum, edge.lag_candidate_range.unit, context.rule.lag.unit)
            evidence_min = _convert_time(evidence.candidate_lag_range.minimum, evidence.candidate_lag_range.unit, context.rule.lag.unit)
            if not _equal(context.rule.lag.maximum, maximum, tolerance):
                issues.append(_issue("LAG_MAXIMUM_MISMATCH", 8, "lag", "rule maximum differs from lag_maximum parameter", "repairable"))
            if not (_equal(context.rule.lag.minimum, edge_min, tolerance) and _equal(context.rule.lag.minimum, evidence_min, tolerance)):
                issues.append(_issue("LAG_MINIMUM_MISMATCH", 8, "lag", "rule minimum differs from graph or evidence minimum", "repairable"))
        elif parameter.parameter_role == "response_delay":
            lower = _convert_time(parameter.confidence_interval.lower, parameter.unit, context.rule.lag.unit)
            upper = _convert_time(parameter.confidence_interval.upper, parameter.unit, context.rule.lag.unit)
            if not (_equal(context.rule.lag.minimum, lower, tolerance) and _equal(context.rule.lag.maximum, upper, tolerance)):
                issues.append(_issue("LAG_INTERVAL_UNCERTAINTY_MISMATCH", 8, "lag", "rule interval differs from response-delay confidence interval", "repairable"))
        else:
            issues.append(_issue("LAG_BINDING_INCOMPLETE", 8, "lag", "lag_minimum alone or another role cannot bind MVP lag", "repairable"))
        edge_min = _convert_time(edge.lag_candidate_range.minimum, edge.lag_candidate_range.unit, context.rule.lag.unit)
        edge_max = _convert_time(edge.lag_candidate_range.maximum, edge.lag_candidate_range.unit, context.rule.lag.unit)
        evidence_min = _convert_time(evidence.candidate_lag_range.minimum, evidence.candidate_lag_range.unit, context.rule.lag.unit)
        evidence_max = _convert_time(evidence.candidate_lag_range.maximum, evidence.candidate_lag_range.unit, context.rule.lag.unit)
        if context.rule.lag.minimum < edge_min - tolerance or context.rule.lag.maximum > edge_max + tolerance:
            issues.append(_issue("LAG_OUTSIDE_GRAPH_RANGE", 8, "lag", "rule lag is outside graph candidate range", "repairable"))
        if context.rule.lag.minimum < evidence_min - tolerance or context.rule.lag.maximum > evidence_max + tolerance:
            issues.append(_issue("LAG_OUTSIDE_EVIDENCE_RANGE", 8, "lag", "rule lag is outside evidence candidate range", "repairable"))
    except ValueError:
        issues.append(_issue("LAG_UNIT_CONVERSION_FAILED", 8, "lag", "lag units are not deterministically convertible", "repairable"))
    return issues


def _stage_9(context: _VerificationContext) -> list[VerifierIssueV1]:
    parameter = context.parameters.get(context.rule.window.parameter_ref)
    if parameter is None:
        return []
    issues = []
    if parameter.parameter_role != "persistence_duration":
        issues.append(_issue("WINDOW_DURATION_ROLE_MISMATCH", 9, "window", "window requires persistence_duration", "repairable"))
        return issues
    try:
        duration = _convert_time(parameter.value, parameter.unit, context.rule.window.unit)
        if not _equal(context.rule.window.length, duration, context.policy.time_comparison_tolerance):
            issues.append(_issue("WINDOW_DURATION_MISMATCH", 9, "window", "window length differs from duration parameter", "repairable"))
        lag_max = _convert_time(context.rule.lag.maximum, context.rule.lag.unit, context.rule.window.unit)
        if context.rule.window.window_type == "event_relative" and context.rule.window.length < lag_max - context.policy.time_comparison_tolerance:
            issues.append(_issue("WINDOW_TOO_SHORT", 9, "window", "event-relative window cannot contain maximum lag", "repairable"))
    except ValueError:
        issues.append(_issue("WINDOW_UNIT_CONVERSION_FAILED", 9, "window", "window units are not deterministically convertible", "repairable"))
    if context.rule.window.window_type not in {"event_relative", "persistence"}:
        issues.append(_issue("WINDOW_TYPE_UNSUPPORTED", 9, "window", "rolling or recovery windows are unsupported", "repairable"))
    if context.rule.persistence.enabled and context.rule.persistence.duration_parameter_ref != context.rule.window.parameter_ref:
        issues.append(_issue("PERSISTENCE_REFERENCE_MISMATCH", 9, "persistence", "persistence and window must use the same duration", "repairable"))
    return issues


def _stage_10(context: _VerificationContext) -> list[VerifierIssueV1]:
    issues = []
    referenced = [context.parameters.get(item) for item in context.rule.parameter_refs]
    for parameter_id, parameter in zip(context.rule.parameter_refs, referenced):
        if parameter is None:
            issues.append(_issue("PARAMETER_MISSING", 10, "parameter_refs", "referenced parameter does not exist", "repairable"))
            continue
        if parameter.approval_status != "approved" or parameter.approved_by is None or parameter.approval_date is None:
            issues.append(_issue("PARAMETER_NOT_APPROVED", 10, "verified_parameter_values", "parameter lacks deterministic approval", "non_repairable"))
        if parameter.stability_summary.status != "stable":
            issues.append(_issue("PARAMETER_UNSTABLE", 10, "verified_parameter_values", "parameter stability is not stable", "non_repairable"))
        if parameter.uncertainty.status not in context.policy.allowed_parameter_uncertainty:
            issues.append(_issue("PARAMETER_UNCERTAINTY_PROHIBITED", 10, "verified_parameter_values", "parameter uncertainty is outside policy", "non_repairable"))
    roles = {parameter.parameter_role for parameter in referenced if parameter is not None}
    required = {"tolerance", "persistence_duration", "minimum_support", "severity_boundary"}
    if not required.issubset(roles) or not ({"lag_maximum", "response_delay"} & roles):
        issues.append(_issue("PARAMETER_ROLE_INCOMPLETE", 10, "parameter_refs", "required delayed-response parameter roles are incomplete", "repairable"))
    support = next((item for item in referenced if item is not None and item.parameter_role == "minimum_support"), None)
    if support is not None:
        threshold = support.value
        edge_count = context.edge.support.event_count if context.edge is not None else 0
        if edge_count < threshold or any(item.sample_support.matched_count < threshold for item in referenced if item is not None):
            issues.append(_issue("INSUFFICIENT_SUPPORT", 10, "verified_parameter_values", "support does not meet approved minimum", "non_repairable"))
    return issues


def _stage_11(context: _VerificationContext) -> list[VerifierIssueV1]:
    issues = []
    for parameter_id in context.rule.parameter_refs:
        parameter = context.parameters.get(parameter_id)
        if parameter is None:
            continue
        if parameter.dataset_version != context.rule.dataset_version:
            issues.append(_issue("PARAMETER_DATASET_MISMATCH", 11, "verified_parameter_values", "parameter dataset version disagrees", "non_repairable"))
        if parameter.relation_family != context.rule.relation_type:
            issues.append(_issue("PARAMETER_RELATION_MISMATCH", 11, "verified_parameter_values", "parameter relation family disagrees", "non_repairable"))
        if parameter.source_variables != context.rule.source_variables or parameter.target_variables != context.rule.target_variables:
            issues.append(_issue("PARAMETER_VARIABLE_MISMATCH", 11, "verified_parameter_values", "parameter variables disagree", "non_repairable"))
        if parameter.operating_regime != context.rule.operating_regime.regime_id:
            issues.append(_issue("PARAMETER_REGIME_MISMATCH", 11, "verified_parameter_values", "parameter regime disagrees", "non_repairable"))
        if not set(context.rule.normal_reference_refs).issubset(parameter.normal_reference_refs):
            issues.append(_issue("PARAMETER_NORMAL_REFERENCE_MISMATCH", 11, "verified_parameter_values", "parameter normal-reference provenance disagrees", "non_repairable"))
        try:
            verify_contract_artifact_hash(calibration_parameter_to_dict(parameter))
        except ContractArtifactHashError:
            issues.append(_issue("PARAMETER_HASH_INVALID", 11, "verified_parameter_values", "parameter self-hash failed", "non_repairable"))
    return issues


def _stage_12(context: _VerificationContext) -> list[VerifierIssueV1]:
    issues = []
    if context.artifacts.evidence.data_split not in {"train", "calibration"}:
        issues.append(_issue("EVIDENCE_SPLIT_PROHIBITED", 12, "final_test_boundaries", "evidence split is prohibited", "non_repairable"))
    if any(item.calibration_split != "calibration" for item in context.artifacts.parameters):
        issues.append(_issue("PARAMETER_SPLIT_PROHIBITED", 12, "final_test_boundaries", "numeric parameter split must be calibration", "non_repairable"))
    return issues


def _stage_13(context: _VerificationContext) -> list[VerifierIssueV1]:
    evidence = context.artifacts.evidence
    issues = []
    if len(context.rule.evidence_refs) != 1 or context.rule.evidence_refs[0] != evidence.evidence_id:
        issues.append(_issue("EVIDENCE_REFERENCE_INVALID", 13, "evidence_refs", "exactly one existing evidence reference is required", "non_repairable"))
    if evidence.source_variables != context.rule.source_variables or evidence.target_variables != context.rule.target_variables:
        issues.append(_issue("EVIDENCE_VARIABLE_MISMATCH", 13, "evidence_refs", "evidence variables disagree", "non_repairable"))
    if evidence.operating_regime != context.rule.operating_regime.regime_id:
        issues.append(_issue("EVIDENCE_REGIME_MISMATCH", 13, "evidence_refs", "evidence regime disagrees", "non_repairable"))
    if evidence.dataset_version != context.rule.dataset_version:
        issues.append(_issue("EVIDENCE_DATASET_MISMATCH", 13, "dataset_version", "evidence dataset version disagrees", "non_repairable"))
    policy = evidence.selection_policy
    if not policy.pre_registered or policy.label_performance_used or not policy.deterministic_tie_breaking:
        issues.append(_issue("EVIDENCE_SELECTION_POLICY_INVALID", 13, "evidence_refs", "evidence selection policy is not pre-registered and label-free", "non_repairable"))
    if evidence.raw_values_included:
        issues.append(_issue("EVIDENCE_RAW_VALUES_PROHIBITED", 13, "evidence_refs", "evidence must not contain raw values", "non_repairable"))
    return issues


def _stage_14(context: _VerificationContext) -> list[VerifierIssueV1]:
    normal = context.artifacts.evidence.matched_normal_reference
    issues = []
    if len(context.rule.normal_reference_refs) != 1 or context.rule.normal_reference_refs[0] != normal.reference_id:
        issues.append(_issue("NORMAL_REFERENCE_INVALID", 14, "evidence_refs", "rule normal reference is absent from evidence", "non_repairable"))
    for parameter_id in context.rule.parameter_refs:
        parameter = context.parameters.get(parameter_id)
        if parameter is not None and normal.reference_id not in parameter.normal_reference_refs:
            issues.append(_issue("PARAMETER_NORMAL_REFERENCE_MISMATCH", 14, "verified_parameter_values", "parameter omits the rule normal reference", "non_repairable"))
    if normal.matching_method == "exact_regime_subsystem" and normal.operating_regime != context.artifacts.evidence.operating_regime:
        issues.append(_issue("NORMAL_REGIME_MISMATCH", 14, "evidence_refs", "exact-regime normal reference is inconsistent", "non_repairable"))
    return issues


def _stage_15(context: _VerificationContext) -> list[VerifierIssueV1]:
    issues = []
    key = _conflict_key(context.rule)
    projection = _semantic_projection_hash(context.rule)
    for outcome in context.accepted_library:
        other = outcome.accepted_rule
        if other is None or _conflict_key(other) != key:
            continue
        if _semantic_projection_hash(other) != projection:
            record = VerifierRelationRecordV1(_relation_record_id("CONFLICT", context.rule.rule_id, other.rule_id), other.rule_id, "conflict")
            context.conflict_records.append(record)
            issues.append(_issue("STRUCTURAL_CONFLICT", 15, "trigger", "accepted library contains a document-level conflict", "repairable"))
    return issues


def _stage_16(context: _VerificationContext) -> list[VerifierIssueV1]:
    issues = []
    projection = _semantic_projection_hash(context.rule)
    for outcome in context.accepted_library:
        other = outcome.accepted_rule
        if other is not None and _semantic_projection_hash(other) == projection:
            record = VerifierRelationRecordV1(_relation_record_id("DUPLICATE", context.rule.rule_id, other.rule_id), other.rule_id, "structural_duplicate")
            context.duplicate_records.append(record)
            issues.append(_issue("STRUCTURAL_DUPLICATE", 16, "rule_id", "accepted library contains an exact structural duplicate", "non_repairable"))
    return issues


def _stage_17(context: _VerificationContext) -> list[VerifierIssueV1]:
    complexity = context.rule.complexity
    issues = []
    expected_variables = len(set(context.rule.source_variables + context.rule.target_variables))
    if complexity.variable_count != expected_variables:
        issues.append(_issue("COMPLEXITY_VARIABLE_COUNT", 17, "expected_effect", "declared variable count disagrees with rule variables", "repairable"))
    if complexity.operator_count > context.policy.maximum_operator_count:
        issues.append(_issue("COMPLEXITY_OPERATOR_BUDGET", 17, "expected_effect", "declared operator count exceeds policy", "repairable"))
    if complexity.variable_count > context.policy.maximum_variable_count:
        issues.append(_issue("COMPLEXITY_VARIABLE_BUDGET", 17, "expected_effect", "declared variable count exceeds policy", "repairable"))
    if complexity.max_depth > context.policy.maximum_depth:
        issues.append(_issue("COMPLEXITY_DEPTH_BUDGET", 17, "expected_effect", "declared depth exceeds policy", "repairable"))
    if _complexity_score(context.rule) > 100:
        issues.append(_issue("COMPLEXITY_SCORE_INVALID", 17, "expected_effect", "complexity score exceeds 100", "repairable"))
    return issues


def _stage_18(context: _VerificationContext) -> list[VerifierIssueV1]:
    issues = []
    if context.rule.output_semantics.output_type != "binary_anomaly":
        issues.append(_issue("OUTPUT_TYPE_INVALID", 18, "output_semantics", "output must be binary_anomaly", "repairable"))
    if context.rule.output_semantics.violation_direction != "missing_expected_response":
        issues.append(_issue("VIOLATION_DIRECTION_INVALID", 18, "output_semantics", "violation must be missing_expected_response", "repairable"))
    abstention = context.rule.abstention_policy
    if not all(isinstance(item, bool) for item in (
        abstention.abstain_on_missing_inputs, abstention.abstain_on_regime_mismatch,
        abstention.abstain_on_parameter_uncertainty,
    )):
        issues.append(_issue("ABSTENTION_POLICY_INCOMPLETE", 18, "abstention_policy", "abstention policy is incomplete", "repairable"))
    return issues


def _stage_19(context: _VerificationContext) -> list[VerifierIssueV1]:
    issues = []
    if context.edge is None:
        issues.append(_issue("EXPLANATION_EDGE_MISSING", 19, "graph_edge_refs", "future explanation cannot reference an edge", "non_repairable"))
    if context.rule.evidence_refs != (context.artifacts.evidence.evidence_id,):
        issues.append(_issue("EXPLANATION_EVIDENCE_MISSING", 19, "evidence_refs", "future explanation cannot reference evidence", "non_repairable"))
    if context.rule.normal_reference_refs != (context.artifacts.evidence.matched_normal_reference.reference_id,):
        issues.append(_issue("EXPLANATION_NORMAL_REFERENCE_MISSING", 19, "evidence_refs", "future explanation cannot reference normal evidence", "non_repairable"))
    if any(parameter_id not in context.parameters for parameter_id in context.rule.parameter_refs):
        issues.append(_issue("EXPLANATION_PARAMETER_MISSING", 19, "parameter_refs", "future explanation cannot reference every parameter", "repairable"))
    return issues


def _stage_20(context: _VerificationContext) -> list[VerifierIssueV1]:
    issues = []
    if context.rule.status not in {"candidate", "needs_repair"} or context.rule.verified_rule_hash is not None:
        issues.append(_issue("RULE_AUTHORITY_PRECLAIMED", 20, "verified_parameter_values", "input rule preclaims verifier authority", "non_repairable"))
    edge = context.edge
    if edge is not None and edge.causal_claim_allowed:
        issues.append(_issue("CAUSAL_CLAIM_PROHIBITED", 20, "graph_edge_refs", "candidate edge cannot authorize causality", "non_repairable"))
    evidence = context.artifacts.evidence
    if not _REQUIRED_PROHIBITED_CLAIMS.issubset(evidence.prohibited_claims):
        issues.append(_issue("CLAIM_BOUNDARY_INCOMPLETE", 20, "evidence_refs", "evidence claim boundary is incomplete", "non_repairable"))
    if evidence.raw_values_included:
        issues.append(_issue("RAW_VALUES_PROHIBITED", 20, "evidence_refs", "raw values are prohibited", "non_repairable"))
    if context.rule.runtime_authorized or context.artifacts.runtime_authorized:
        issues.append(_issue("RUNTIME_AUTHORITY_PROHIBITED", 20, "final_test_boundaries", "TASK-032D cannot authorize runtime", "non_repairable"))
    return issues


def _issue(code: str, stage: int, field_name: str, message: str, repairability: str) -> VerifierIssueV1:
    return VerifierIssueV1(code, stage, field_name, message, repairability)


def _issue_sort_key(issue: VerifierIssueV1) -> tuple[Any, ...]:
    return issue.stage, issue.code, issue.field, issue.message, issue.repairability


def _issue_to_document(issue: VerifierIssueV1) -> dict[str, Any]:
    return {"code": issue.code, "stage": issue.stage, "field": issue.field, "message": issue.message}


def _issue_from_document(item: Mapping[str, Any], repairable: set[str], non_repairable: set[str]) -> VerifierIssueV1:
    field_name = str(item["field"])
    authority = "non_repairable" if field_name in non_repairable else "repairable" if field_name in repairable else "non_repairable"
    return VerifierIssueV1(str(item["code"]), int(item["stage"]), field_name, str(item["message"]), authority)


def _record_to_document(record: VerifierRelationRecordV1) -> dict[str, str]:
    return {"record_id": record.record_id, "related_rule_id": record.related_rule_id, "relation": record.relation}


def _record_from_document(item: Mapping[str, Any]) -> VerifierRelationRecordV1:
    return VerifierRelationRecordV1(str(item["record_id"]), str(item["related_rule_id"]), str(item["relation"]))


def _single_node(context: _VerificationContext, variable: str) -> GraphNodeV1 | None:
    matches = context.nodes_by_variable.get(variable, ())
    return matches[0] if len(matches) == 1 else None


def _convert_time(value: int | float, source_unit: str, target_unit: str) -> float:
    if source_unit not in _TIME_FACTORS or target_unit not in _TIME_FACTORS:
        raise ValueError("unsupported time unit")
    return float(value) * _TIME_FACTORS[source_unit] / _TIME_FACTORS[target_unit]


def _equal(left: int | float, right: int | float, tolerance: float) -> bool:
    return abs(float(left) - float(right)) <= tolerance


def _complexity_score(rule: DelayedResponseRuleV1) -> int:
    raw = rule.complexity.operator_count * 5 + rule.complexity.variable_count * 5 + rule.complexity.max_depth * 5
    return min(100, max(0, raw))


def _semantic_projection_hash(rule: DelayedResponseRuleV1) -> str:
    document = delayed_response_rule_to_dict(rule)
    for field_name in ("rule_id", "rule_version", "status", "verified_rule_hash", "provenance", "review_history"):
        document.pop(field_name, None)
    payload = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _conflict_key(rule: DelayedResponseRuleV1) -> tuple[Any, ...]:
    return (
        rule.source_variables, rule.target_variables, rule.operating_regime.regime_id,
        rule.trigger.trigger_type, rule.trigger.state_value,
    )


def _relation_record_id(prefix: str, first_rule: str, second_rule: str) -> str:
    payload = f"{prefix}:{first_rule}:{second_rule}".encode("utf-8")
    return f"{prefix}-{hashlib.sha256(payload).hexdigest()[:16].upper()}"
