"""Assessment-only bridge for serialized Phase 1 rule artifacts."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from paperworks.contracts.models import LegacyFieldMapping, LegacyMigrationAssessment


ADAPTER_VERSION = "task032a-assessment-v1"
LEGACY_SCHEMA_IDENTIFIER = "minimal_rule_schema_v1"
TARGET_SCHEMA_VERSION = "1.0.0"
TARGET_ARTIFACT_TYPE = "rule_dsl"
SUPPORTED_RULE_FAMILY = "changed_to_increase_within_response_missing"
SUPPORTED_RELATION_TYPE = "binary_actuator_to_continuous_sensor"
_PROHIBITED_KEYS = {
    "python",
    "code",
    "source_code",
    "eval",
    "exec",
    "compile",
    "import",
    "callable",
    "lambda",
    "shell",
    "command",
    "dynamic_expression",
    "expression",
    "formula",
}
_REQUIRED_CONTEXT = (
    "approved_verifier_policy",
    "dataset_version",
    "evidence_package_id",
    "graph_edge_id",
    "matched_normal_reference_id",
    "operating_regime_id",
    "parameter_record_ids",
)


def assess_legacy_artifact(source: Mapping[str, Any]) -> LegacyMigrationAssessment:
    """Assess compatibility without creating or mutating a v1 target artifact."""

    snapshot = copy.deepcopy(dict(source))
    source_hash = _canonical_sha256(snapshot)
    schema_identifier = str(snapshot.get("source_schema_identifier", ""))
    artifact_type = str(snapshot.get("source_artifact_type", ""))
    payload = snapshot.get("payload")

    if schema_identifier != LEGACY_SCHEMA_IDENTIFIER:
        return _assessment(
            source_hash=source_hash,
            schema_identifier=schema_identifier,
            artifact_type=artifact_type,
            status="unsupported_legacy_artifact",
            reasons=("missing_or_unrecognized_legacy_schema_identifier",),
        )
    if artifact_type != "rule_candidate":
        return _assessment(
            source_hash=source_hash,
            schema_identifier=schema_identifier,
            artifact_type=artifact_type,
            status="unsupported_legacy_artifact",
            reasons=("unsupported_legacy_artifact_type",),
        )
    if not isinstance(payload, dict):
        return _assessment(
            source_hash=source_hash,
            schema_identifier=schema_identifier,
            artifact_type=artifact_type,
            status="invalid_legacy_artifact",
            reasons=("payload_must_be_an_object",),
        )
    prohibited = _find_prohibited_key(snapshot)
    if prohibited is not None:
        return _assessment(
            source_hash=source_hash,
            schema_identifier=schema_identifier,
            artifact_type=artifact_type,
            status="unsupported_legacy_artifact",
            reasons=(f"executable_or_dynamic_field:{prohibited}",),
        )

    malformed = _malformed_reasons(payload)
    if malformed:
        return _assessment(
            source_hash=source_hash,
            schema_identifier=schema_identifier,
            artifact_type=artifact_type,
            status="invalid_legacy_artifact",
            reasons=tuple(malformed),
        )

    sources = _cardinality(payload.get("source"))
    targets = _cardinality(payload.get("target"))
    if sources != 1 or targets != 1:
        return _assessment(
            source_hash=source_hash,
            schema_identifier=schema_identifier,
            artifact_type=artifact_type,
            status="unsupported_legacy_artifact",
            relation_family=str(payload.get("rule_family", "")) or None,
            reasons=("multiple_sources_or_targets_are_outside_the_mvp",),
        )

    context = snapshot.get("assessment_context")
    if not isinstance(context, dict):
        return _assessment(
            source_hash=source_hash,
            schema_identifier=schema_identifier,
            artifact_type=artifact_type,
            status="invalid_legacy_artifact",
            reasons=("assessment_context_must_be_an_object",),
        )
    supported = _is_supported_delayed_response(payload, context)
    if not supported:
        return _assessment(
            source_hash=source_hash,
            schema_identifier=schema_identifier,
            artifact_type=artifact_type,
            status="unsupported_legacy_artifact",
            relation_family=str(payload.get("rule_family", "")) or None,
            reasons=("relation_or_type_combination_is_not_supported_by_task032a",),
        )

    return LegacyMigrationAssessment(
        adapter_version=ADAPTER_VERSION,
        source_schema_identifier=schema_identifier,
        source_artifact_type=artifact_type,
        source_sha256=source_hash,
        target_schema_version=TARGET_SCHEMA_VERSION,
        target_artifact_type=TARGET_ARTIFACT_TYPE,
        target_artifact_created=False,
        status="convertible_delayed_response_pending_context",
        detected_relation_family="delayed_response",
        field_mappings=_supported_field_mappings(),
        required_external_context=_REQUIRED_CONTEXT,
        information_loss=(
            "legacy_description_template_is_renderer_input_not_v1_rule_semantics",
            "resolved_legacy_numeric_values_cannot_be_promoted_to_approved_parameters",
        ),
        warnings=(
            "assessment_only_no_conversion_performed",
            "synthetic_smoke_calibration_must_not_be_promoted",
            "semantic_verification_is_required_in_a_later_task",
        ),
        unsupported_reasons=(),
    )


def assess_legacy_artifact_file(path: str | Path) -> LegacyMigrationAssessment:
    source = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(source, dict):
        raise ValueError("legacy artifact file must contain a JSON object")
    return assess_legacy_artifact(source)


def _assessment(
    *,
    source_hash: str,
    schema_identifier: str,
    artifact_type: str,
    status: str,
    reasons: tuple[str, ...],
    relation_family: str | None = None,
) -> LegacyMigrationAssessment:
    return LegacyMigrationAssessment(
        adapter_version=ADAPTER_VERSION,
        source_schema_identifier=schema_identifier,
        source_artifact_type=artifact_type,
        source_sha256=source_hash,
        target_schema_version=TARGET_SCHEMA_VERSION,
        target_artifact_type=TARGET_ARTIFACT_TYPE,
        target_artifact_created=False,
        status=status,
        detected_relation_family=relation_family,
        field_mappings=(),
        required_external_context=(),
        information_loss=(),
        warnings=("assessment_only_no_conversion_performed",),
        unsupported_reasons=reasons,
    )


def _malformed_reasons(payload: Mapping[str, Any]) -> list[str]:
    required = {
        "schema_version",
        "rule_family",
        "source",
        "target",
        "relation_type",
        "trigger_predicate",
        "response_predicate",
        "calibration_references",
    }
    missing = sorted(required - set(payload))
    if missing:
        return ["missing_required_legacy_fields"]
    trigger = payload.get("trigger_predicate")
    response = payload.get("response_predicate")
    if not isinstance(trigger, dict) or not isinstance(response, dict):
        return ["legacy_predicates_must_be_objects"]
    expected = response.get("expected_response")
    if not isinstance(expected, dict):
        return ["legacy_expected_response_must_be_an_object"]
    if isinstance(payload.get("source"), str) and trigger.get("variable") != payload.get("source"):
        return ["trigger_variable_contradicts_source"]
    if isinstance(payload.get("target"), str) and expected.get("variable") != payload.get("target"):
        return ["response_variable_contradicts_target"]
    if not isinstance(payload.get("calibration_references"), dict):
        return ["calibration_references_must_be_an_object"]
    return []


def _is_supported_delayed_response(payload: Mapping[str, Any], context: Mapping[str, Any]) -> bool:
    trigger = payload["trigger_predicate"]
    response = payload["response_predicate"]
    expected = response["expected_response"]
    return (
        payload.get("schema_version") == "1.0"
        and payload.get("rule_family") == SUPPORTED_RULE_FAMILY
        and payload.get("relation_type") == SUPPORTED_RELATION_TYPE
        and context.get("source_type") == "binary_actuator"
        and context.get("target_type") == "continuous_sensor"
        and trigger.get("predicate") == "changed_to"
        and expected.get("predicate") == "increase_within"
        and response.get("predicate") == "response_missing"
    )


def _supported_field_mappings() -> tuple[LegacyFieldMapping, ...]:
    return (
        LegacyFieldMapping("source", "source_variables[0]", "renamed_singleton"),
        LegacyFieldMapping("target", "target_variables[0]", "renamed_singleton"),
        LegacyFieldMapping("trigger_predicate", "trigger", "typed_mapping_pending"),
        LegacyFieldMapping("response_predicate.expected_response", "expected_effect", "split_mapping_pending"),
        LegacyFieldMapping("response_predicate", "output_semantics.violation_direction", "renamed_pending"),
        LegacyFieldMapping("calibration_references", "parameter_refs", "external_registry_mapping_required"),
        LegacyFieldMapping("candidate_pair_artifact_id", "graph_edge_refs", "external_context_required"),
    )


def _find_prohibited_key(value: Any, path: str = "$") -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key).lower() in _PROHIBITED_KEYS:
                return child_path
            found = _find_prohibited_key(child, child_path)
            if found is not None:
                return found
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            found = _find_prohibited_key(child, f"{path}[{index}]")
            if found is not None:
                return found
    return None


def _cardinality(value: Any) -> int:
    if isinstance(value, str):
        return 1
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return len(value)
    return 0


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
