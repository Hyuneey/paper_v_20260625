from __future__ import annotations

import ast
import json
from pathlib import Path
import unittest

from paperworks.dsl import (
    CalibrationValueRef,
    ChangedToPredicate,
    IncreaseWithinPredicate,
    PlannerProvenance,
    ResponseMissingPredicate,
    RuleAst,
    RuleSchemaRegistry,
    serialize_rule_json,
)
from paperworks.metadata import (
    MetadataRegistry,
    MetadataSourceMethod,
    PhysicalType,
    ReviewStatus,
    ValueType,
    VariableMetadata,
    VariableRole,
)
from paperworks.planning import (
    LLMPlanningError,
    MockLLMProvider,
    ProviderConfig,
    audit_prompt_payload,
    build_rule_planning_request,
    plan_rule_with_provider,
)
from paperworks.profiling import CalibrationRecord, RelationEvidencePack


RELATION_PROFILE_ID = "a" * 64
CALIBRATION_SPLIT_ID = "b" * 64
CANDIDATE_PAIR_ID = "c" * 64
METADATA_ID = "d" * 64


def actuator(name: str = "A1") -> VariableMetadata:
    return VariableMetadata(
        name=name,
        role=VariableRole.ACTUATOR,
        value_type=ValueType.BINARY,
        physical_type=PhysicalType.PUMP,
        subsystem="stage_1",
        stage="1",
        source_method=MetadataSourceMethod.MANUAL_REVIEW,
        source_reference="synthetic fixture",
        confidence=1.0,
        review_status=ReviewStatus.REVIEWED,
    )


def sensor(name: str = "S1") -> VariableMetadata:
    return VariableMetadata(
        name=name,
        role=VariableRole.SENSOR,
        value_type=ValueType.CONTINUOUS,
        physical_type=PhysicalType.FLOW,
        subsystem="stage_1",
        stage="1",
        source_method=MetadataSourceMethod.MANUAL_REVIEW,
        source_reference="synthetic fixture",
        confidence=1.0,
        review_status=ReviewStatus.REVIEWED,
    )


def calibration_records() -> tuple[CalibrationRecord, CalibrationRecord]:
    delay = CalibrationRecord(
        parameter_name="max_response_delay_seconds",
        value=3.0,
        unit="seconds",
        method="synthetic_fixture",
        quantile_or_config={"quantile": 1.0},
        normal_support_count=2,
        relation_profile_id=RELATION_PROFILE_ID,
        calibration_split_id=CALIBRATION_SPLIT_ID,
    )
    magnitude = CalibrationRecord(
        parameter_name="min_response_magnitude",
        value=2.0,
        unit="target_units",
        method="synthetic_fixture",
        quantile_or_config={"quantile": 0.0},
        normal_support_count=2,
        relation_profile_id=RELATION_PROFILE_ID,
        calibration_split_id=CALIBRATION_SPLIT_ID,
    )
    return delay, magnitude


def registry(*, include_s2: bool = False) -> RuleSchemaRegistry:
    records = calibration_records()
    variables = [actuator(), sensor()]
    if include_s2:
        variables.append(sensor("S2"))
    return RuleSchemaRegistry(
        metadata=MetadataRegistry(variables),
        calibration_records={record.calibration_id: record for record in records},
    )


def evidence() -> RelationEvidencePack:
    records = {record.parameter_name: record for record in calibration_records()}
    return RelationEvidencePack(
        source="A1",
        target="S1",
        relation_type="binary_actuator_to_continuous_sensor",
        recommended_rule_family="changed_to_increase_within_response_missing",
        relation_profile_id=RELATION_PROFILE_ID,
        calibration_record_ids={
            name: record.calibration_id for name, record in records.items()
        },
        calibrated_parameters={name: record.value for name, record in records.items()},
        support_counts={
            "trigger_count": 2,
            "matched_response_count": 2,
            "missing_response_count": 0,
            "right_censored_count": 0,
        },
        source_view="canonical_rule_view",
        sampling_period_seconds=1.0,
        upstream_artifact_ids=(CANDIDATE_PAIR_ID, METADATA_ID),
    )


def rule_json(*, target: str = "S1", magnitude: float = 2.0, predicate: str = "changed_to", description: str = "mock ok") -> str:
    records = {record.parameter_name: record for record in calibration_records()}
    delay_ref = CalibrationValueRef(
        parameter_name="max_response_delay_seconds",
        calibration_record_id=records["max_response_delay_seconds"].calibration_id,
        field_name="value",
        resolved_value=3.0,
        unit="seconds",
    )
    magnitude_ref = CalibrationValueRef(
        parameter_name="min_response_magnitude",
        calibration_record_id=records["min_response_magnitude"].calibration_id,
        field_name="value",
        resolved_value=magnitude,
        unit="target_units",
    )
    rule = RuleAst(
        rule_id="rule.mock.fixture",
        schema_version="1.0",
        source="A1",
        target=target,
        relation_type="binary_actuator_to_continuous_sensor",
        trigger_predicate=ChangedToPredicate(variable="A1", from_state=0.0, to_state=1.0, predicate=predicate),
        response_predicate=ResponseMissingPredicate(
            expected_response=IncreaseWithinPredicate(
                variable=target,
                min_magnitude=magnitude_ref,
                max_delay_seconds=delay_ref,
            )
        ),
        calibration_references={
            "max_response_delay_seconds": delay_ref,
            "min_response_magnitude": magnitude_ref,
        },
        candidate_pair_artifact_id=CANDIDATE_PAIR_ID,
        metadata_artifact_id=METADATA_ID,
        planner_provenance=PlannerProvenance(
            planner_type="llm_json_dsl",
            planner_version="mock-1.0",
            source_artifact_ids=(CANDIDATE_PAIR_ID, METADATA_ID),
        ),
        description_template=description,
    )
    return serialize_rule_json(rule)


class MockOnlyLLMPlannerTests(unittest.TestCase):
    def test_valid_mocked_json_output(self) -> None:
        provider = MockLLMProvider()
        result = plan_rule_with_provider(evidence=evidence(), registry=registry(), provider=provider, created_at="2026-06-25T00:00:00Z")

        self.assertEqual(result.status, "planned")
        self.assertIsNotNone(result.rule)
        self.assertEqual(provider.calls, 1)
        self.assertEqual(result.provider_name, "mock")
        self.assertFalse(result.network_allowed)
        self.assertEqual(result.parse_status, "parsed")

    def test_extra_variable_rejection(self) -> None:
        result = plan_rule_with_provider(
            evidence=evidence(),
            registry=registry(),
            provider=MockLLMProvider(response_text=rule_json(target="S2")),
        )

        self.assertEqual(result.status, "rejected")
        self.assertIn("VARIABLE_NOT_FOUND", {issue.code for issue in result.issues})

    def test_numeric_mutation_rejection(self) -> None:
        result = plan_rule_with_provider(
            evidence=evidence(),
            registry=registry(),
            provider=MockLLMProvider(response_text=rule_json(magnitude=99.0)),
        )

        self.assertEqual(result.status, "rejected")
        self.assertIn("NUMERIC_PARAMETER_MUTATED", {issue.code for issue in result.issues})

    def test_unsupported_predicate_rejection(self) -> None:
        with self.assertRaises(Exception):
            rule_json(predicate="custom")

        payload = serialize_rule_json(RuleAst.from_dict(json.loads(rule_json())))
        payload = payload.replace('"predicate":"changed_to"', '"predicate":"custom"', 1)
        result = plan_rule_with_provider(evidence=evidence(), registry=registry(), provider=MockLLMProvider(response_text=payload))
        self.assertEqual(result.status, "rejected")
        self.assertIn("DSL_SCHEMA_INVALID", {issue.code for issue in result.issues})

    def test_executable_code_payload_rejection(self) -> None:
        payload = rule_json().replace("mock ok", "__import__('os').system('echo bad')")
        result = plan_rule_with_provider(evidence=evidence(), registry=registry(), provider=MockLLMProvider(response_text=payload))

        self.assertEqual(result.status, "rejected")
        self.assertIn("DSL_SCHEMA_INVALID", {issue.code for issue in result.issues})

    def test_malformed_response_rejection(self) -> None:
        result = plan_rule_with_provider(evidence=evidence(), registry=registry(), provider=MockLLMProvider(response_text="not json"))

        self.assertEqual(result.status, "rejected")
        self.assertEqual(result.parse_status, "parse_failed")
        self.assertIn("DSL_SCHEMA_INVALID", {issue.code for issue in result.issues})

    def test_provider_error_fails_safely(self) -> None:
        result = plan_rule_with_provider(evidence=evidence(), registry=registry(), provider=MockLLMProvider(raise_error=True))

        self.assertEqual(result.status, "provider_error")
        self.assertEqual(result.parse_status, "provider_error")
        self.assertIn("PROVIDER_ERROR", {issue.code for issue in result.issues})
        self.assertEqual(len(result.raw_response_hash), 64)

    def test_prompt_redaction_blocks_raw_sequences(self) -> None:
        with self.assertRaisesRegex(LLMPlanningError, "redaction audit"):
            build_rule_planning_request(
                evidence=evidence(),
                registry=registry(),
                prompt_extras={"raw_rows": [[0, 1, 1, 1], [10, 10, 10, 10]]},
            )

        with self.assertRaisesRegex(LLMPlanningError, "redaction audit"):
            audit_prompt_payload({"summary": "[10, 10, 10, 10]"})

    def test_no_network_provider_config(self) -> None:
        with self.assertRaisesRegex(LLMPlanningError, "network"):
            ProviderConfig(allow_network=True)

        with self.assertRaisesRegex(LLMPlanningError, "API keys"):
            ProviderConfig(require_api_key=True)

    def test_provenance_completeness_and_no_full_prompt_retention(self) -> None:
        result = plan_rule_with_provider(evidence=evidence(), registry=registry(), provider=MockLLMProvider(), code_commit="abc123", created_at="2026-06-25T00:00:00Z")
        payload = result.to_dict()

        for field in (
            "provider_name",
            "provider_type",
            "model_or_deployment",
            "api_version",
            "temperature",
            "seed",
            "seed_supported",
            "prompt_template_id",
            "prompt_template_hash",
            "evidence_hash",
            "request_hash",
            "raw_response_hash",
            "redaction_status",
            "parse_status",
            "dsl_schema_version",
            "allowed_rule_families",
            "allowed_predicates",
            "calibration_artifact_ids",
            "candidate_artifact_ids",
            "verifier_feedback_ids",
            "config_hash",
            "code_commit",
            "created_at",
            "network_allowed",
        ):
            self.assertIn(field, payload)
        self.assertNotIn("prompt_text", str(payload))
        self.assertNotIn("raw_response_text", str(payload))

    def test_runtime_import_boundary(self) -> None:
        runtime_root = Path("src/paperworks/runtime")
        imported_modules: set[str] = set()
        for path in runtime_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_modules.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module is not None:
                    imported_modules.add(node.module)

        self.assertFalse(any(name.startswith("paperworks.planning") for name in imported_modules))


if __name__ == "__main__":
    unittest.main()
