"""Deterministic template baseline for candidate rule construction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from paperworks.data.contracts import SCHEMA_VERSION, stable_hash
from paperworks.dsl import (
    CalibrationValueRef,
    ChangedToPredicate,
    IncreaseWithinPredicate,
    PlannerProvenance,
    ResponseMissingPredicate,
    RuleAst,
    RuleSchemaRegistry,
    SchemaIssue,
)
from paperworks.dsl.rules import DSL_SCHEMA_VERSION, RELATION_TYPE, RULE_FAMILY
from paperworks.profiling import RelationEvidencePack


TEMPLATE_PLANNER_VERSION = "1.0"
TRIGGER_FROM_STATE = 0.0
TRIGGER_TO_STATE = 1.0


class TemplateRuleBuildError(ValueError):
    """Raised when template-rule builder inputs are structurally invalid."""


@dataclass(frozen=True)
class TemplateRuleBuildResult:
    status: str
    selected_rule_family: str | None
    rule: RuleAst | None
    issues: tuple[SchemaIssue, ...]
    unsupported_reason: str | None
    evidence_pack_id: str
    planner_provenance: PlannerProvenance | None
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "template_rule_build_result"

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise TemplateRuleBuildError(f"unsupported schema_version: {self.schema_version}")
        if self.artifact_type != "template_rule_build_result":
            raise TemplateRuleBuildError("artifact_type must be template_rule_build_result")
        if self.status not in {"built", "unsupported"}:
            raise TemplateRuleBuildError("status must be built or unsupported")
        if self.status == "built" and self.rule is None:
            raise TemplateRuleBuildError("built result requires a rule")
        if self.status == "unsupported" and self.unsupported_reason is None:
            raise TemplateRuleBuildError("unsupported result requires unsupported_reason")
        if len(self.evidence_pack_id) != 64:
            raise TemplateRuleBuildError("evidence_pack_id must be a 64-character hash")

    @property
    def result_id(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "status": self.status,
            "selected_rule_family": self.selected_rule_family,
            "rule": self.rule.to_dict() if self.rule is not None else None,
            "issues": [issue.to_dict() for issue in self.issues],
            "unsupported_reason": self.unsupported_reason,
            "evidence_pack_id": self.evidence_pack_id,
            "planner_provenance": self.planner_provenance.to_dict() if self.planner_provenance is not None else None,
        }


def build_template_rule(
    evidence: RelationEvidencePack,
    registry: RuleSchemaRegistry,
) -> TemplateRuleBuildResult:
    """Build the deterministic baseline rule from approved evidence.

    This function intentionally has no LLM dependency and does not inspect raw
    time-series data. It only consumes aggregate evidence plus calibration
    records exposed by the schema registry.
    """

    evidence_pack_id = evidence.evidence_pack_id
    if evidence.relation_type != RELATION_TYPE:
        return _unsupported(evidence_pack_id, "UNSUPPORTED_RELATION_TYPE", "unsupported relation type")
    if evidence.recommended_rule_family != RULE_FAMILY:
        return _unsupported(evidence_pack_id, "UNSUPPORTED_RULE_FAMILY", "unsupported rule family")
    if evidence.support_counts.get("matched_response_count", 0) <= 0:
        return _unsupported(evidence_pack_id, "INSUFFICIENT_NORMAL_SUPPORT", "no matched normal response support")
    if not evidence.upstream_artifact_ids:
        return _unsupported(evidence_pack_id, "PROVENANCE_MISSING", "evidence requires upstream artifact ids")

    try:
        source_meta = registry.metadata_for(evidence.source)
        target_meta = registry.metadata_for(evidence.target)
    except Exception:
        return _unsupported(evidence_pack_id, "VARIABLE_NOT_FOUND", "metadata missing for evidence pair")

    if RULE_FAMILY not in registry.allowed_families(source_meta, target_meta):
        return _unsupported(evidence_pack_id, "TYPE_MISMATCH", "metadata types do not support template family")

    required_parameters = ("max_response_delay_seconds", "min_response_magnitude")
    calibration_references: dict[str, CalibrationValueRef] = {}
    for parameter_name in required_parameters:
        calibration_id = evidence.calibration_record_ids.get(parameter_name)
        if calibration_id is None:
            return _unsupported(evidence_pack_id, "CALIBRATION_MISSING", f"missing calibration id for {parameter_name}")
        record = registry.calibration_record_for(calibration_id)
        if record is None:
            return _unsupported(evidence_pack_id, "CALIBRATION_MISSING", f"calibration record unavailable for {parameter_name}")
        if record.parameter_name != parameter_name:
            return _unsupported(evidence_pack_id, "CALIBRATION_MISMATCH", f"calibration record parameter mismatch for {parameter_name}")
        expected_value = evidence.calibrated_parameters.get(parameter_name)
        if expected_value is None or float(expected_value) != record.value:
            return _unsupported(evidence_pack_id, "NUMERIC_PARAMETER_MUTATED", f"evidence value mismatch for {parameter_name}")
        calibration_references[parameter_name] = CalibrationValueRef(
            parameter_name=record.parameter_name,
            calibration_record_id=record.calibration_id,
            field_name="value",
            resolved_value=record.value,
            unit=record.unit,
        )

    planner_provenance = PlannerProvenance(
        planner_type="deterministic_template",
        planner_version=TEMPLATE_PLANNER_VERSION,
        source_artifact_ids=tuple(sorted((evidence_pack_id, *evidence.upstream_artifact_ids))),
    )
    rule = _rule_from_evidence(
        evidence=evidence,
        calibration_references=calibration_references,
        planner_provenance=planner_provenance,
    )
    issues = tuple(registry.validate(rule))
    if issues:
        return TemplateRuleBuildResult(
            status="unsupported",
            selected_rule_family=RULE_FAMILY,
            rule=None,
            issues=issues,
            unsupported_reason="SCHEMA_VALIDATION_FAILED",
            evidence_pack_id=evidence_pack_id,
            planner_provenance=planner_provenance,
        )

    return TemplateRuleBuildResult(
        status="built",
        selected_rule_family=RULE_FAMILY,
        rule=rule,
        issues=(),
        unsupported_reason=None,
        evidence_pack_id=evidence_pack_id,
        planner_provenance=planner_provenance,
    )


def _rule_from_evidence(
    *,
    evidence: RelationEvidencePack,
    calibration_references: Mapping[str, CalibrationValueRef],
    planner_provenance: PlannerProvenance,
) -> RuleAst:
    expected_response = IncreaseWithinPredicate(
        variable=evidence.target,
        min_magnitude=calibration_references["min_response_magnitude"],
        max_delay_seconds=calibration_references["max_response_delay_seconds"],
    )
    provisional = RuleAst(
        rule_id="rule.pending",
        schema_version=DSL_SCHEMA_VERSION,
        rule_family=RULE_FAMILY,
        source=evidence.source,
        target=evidence.target,
        relation_type=evidence.relation_type,
        trigger_predicate=ChangedToPredicate(
            variable=evidence.source,
            from_state=TRIGGER_FROM_STATE,
            to_state=TRIGGER_TO_STATE,
        ),
        response_predicate=ResponseMissingPredicate(expected_response=expected_response),
        calibration_references=dict(calibration_references),
        candidate_pair_artifact_id=_candidate_pair_artifact_id(evidence),
        metadata_artifact_id=_metadata_artifact_id(evidence),
        planner_provenance=planner_provenance,
        description_template="deterministic response-missing template",
    )
    rule_id = f"rule.template.{provisional.deterministic_id[:16]}"
    return RuleAst.from_dict({**provisional.to_dict(), "rule_id": rule_id})


def _candidate_pair_artifact_id(evidence: RelationEvidencePack) -> str:
    if not evidence.upstream_artifact_ids:
        raise TemplateRuleBuildError("evidence requires at least one upstream artifact id")
    return evidence.upstream_artifact_ids[0]


def _metadata_artifact_id(evidence: RelationEvidencePack) -> str:
    if len(evidence.upstream_artifact_ids) >= 2:
        return evidence.upstream_artifact_ids[1]
    return stable_hash({"metadata_reference": evidence.evidence_pack_id})


def _unsupported(evidence_pack_id: str, code: str, message: str) -> TemplateRuleBuildResult:
    return TemplateRuleBuildResult(
        status="unsupported",
        selected_rule_family=None,
        rule=None,
        issues=(SchemaIssue(code=code, message=message, path="evidence"),),
        unsupported_reason=code,
        evidence_pack_id=evidence_pack_id,
        planner_provenance=None,
    )
