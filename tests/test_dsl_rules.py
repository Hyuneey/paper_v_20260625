from __future__ import annotations

import unittest

from paperworks.dsl import (
    CalibrationValueRef,
    ChangedToPredicate,
    IncreaseWithinPredicate,
    MinimalRuleEvaluator,
    PlannerProvenance,
    ResponseMissingPredicate,
    RuleAst,
    RuleDslError,
    RuleSchemaRegistry,
    TimeSeriesWindow,
    format_rule,
    parse_rule_json,
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
from paperworks.profiling import CalibrationRecord


RELATION_PROFILE_ID = "a" * 64
CALIBRATION_SPLIT_ID = "b" * 64
CANDIDATE_PAIR_ID = "c" * 64
METADATA_ID = "d" * 64
SOURCE_ARTIFACT_ID = "e" * 64


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


def metadata() -> MetadataRegistry:
    return MetadataRegistry([actuator(), sensor()])


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


def refs() -> dict[str, CalibrationValueRef]:
    delay, magnitude = calibration_records()
    return {
        delay.parameter_name: CalibrationValueRef(
            parameter_name=delay.parameter_name,
            calibration_record_id=delay.calibration_id,
            field_name="value",
            resolved_value=delay.value,
            unit=delay.unit,
        ),
        magnitude.parameter_name: CalibrationValueRef(
            parameter_name=magnitude.parameter_name,
            calibration_record_id=magnitude.calibration_id,
            field_name="value",
            resolved_value=magnitude.value,
            unit=magnitude.unit,
        ),
    }


def valid_rule(*, references: dict[str, CalibrationValueRef] | None = None) -> RuleAst:
    calibration_refs = references or refs()
    expected_response = IncreaseWithinPredicate(
        variable="S1",
        min_magnitude=calibration_refs["min_response_magnitude"],
        max_delay_seconds=calibration_refs["max_response_delay_seconds"],
    )
    return RuleAst(
        rule_id="rule.synthetic.A1.S1",
        schema_version="1.0",
        source="A1",
        target="S1",
        relation_type="binary_actuator_to_continuous_sensor",
        trigger_predicate=ChangedToPredicate(variable="A1", from_state=0.0, to_state=1.0),
        response_predicate=ResponseMissingPredicate(expected_response=expected_response),
        calibration_references=calibration_refs,
        candidate_pair_artifact_id=CANDIDATE_PAIR_ID,
        metadata_artifact_id=METADATA_ID,
        planner_provenance=PlannerProvenance(
            planner_type="deterministic_template",
            planner_version="1.0",
            source_artifact_ids=(SOURCE_ARTIFACT_ID,),
        ),
        description_template="source transition with missing calibrated target response",
    )


def registry() -> RuleSchemaRegistry:
    records = calibration_records()
    return RuleSchemaRegistry(
        metadata=metadata(),
        calibration_records={record.calibration_id: record for record in records},
    )


class RuleDslTests(unittest.TestCase):
    def test_valid_round_trip_is_deterministic(self) -> None:
        rule = valid_rule()
        text = serialize_rule_json(rule)
        parsed = parse_rule_json(text)

        self.assertEqual(parsed.to_dict(), rule.to_dict())
        self.assertEqual(serialize_rule_json(parsed), text)
        self.assertEqual(registry().validate(parsed), [])

    def test_schema_version_handling(self) -> None:
        payload = valid_rule().to_dict()
        payload["schema_version"] = "9.9"

        with self.assertRaisesRegex(RuleDslError, "schema_version"):
            RuleAst.from_dict(payload)

    def test_unsupported_predicate_is_rejected(self) -> None:
        payload = valid_rule().to_dict()
        payload["trigger_predicate"]["predicate"] = "custom_python"

        with self.assertRaisesRegex(RuleDslError, "changed_to"):
            RuleAst.from_dict(payload)

    def test_extra_variable_is_rejected(self) -> None:
        payload = valid_rule().to_dict()
        payload["response_predicate"]["expected_response"]["variable"] = "S2"

        with self.assertRaisesRegex(RuleDslError, "response variable"):
            RuleAst.from_dict(payload)

    def test_missing_calibration_reference_is_rejected(self) -> None:
        payload = valid_rule().to_dict()
        del payload["calibration_references"]["min_response_magnitude"]

        with self.assertRaisesRegex(RuleDslError, "delay and magnitude"):
            RuleAst.from_dict(payload)

    def test_numeric_mutation_is_rejected_by_registry(self) -> None:
        payload = valid_rule().to_dict()
        payload["calibration_references"]["min_response_magnitude"]["resolved_value"] = 999.0
        payload["response_predicate"]["expected_response"]["min_magnitude"]["resolved_value"] = 999.0
        mutated = RuleAst.from_dict(payload)

        issues = registry().validate(mutated)
        self.assertIn("NUMERIC_PARAMETER_MUTATED", {issue.code for issue in issues})

    def test_type_mismatch_is_rejected(self) -> None:
        bad_registry = RuleSchemaRegistry(
            metadata=MetadataRegistry([sensor("A1"), sensor("S1")]),
            calibration_records={record.calibration_id: record for record in calibration_records()},
        )

        issues = bad_registry.validate(valid_rule())
        self.assertIn("TYPE_MISMATCH", {issue.code for issue in issues})

    def test_malicious_code_like_payload_is_rejected(self) -> None:
        payload = valid_rule().to_dict()
        payload["description_template"] = "__import__('os').system('echo bad')"

        with self.assertRaisesRegex(RuleDslError, "prohibited payload"):
            parse_rule_json(serialize_rule_json(RuleAst.from_dict(valid_rule().to_dict())).replace(
                "source transition with missing calibrated target response",
                payload["description_template"],
            ))

    def test_evaluator_flags_missing_response_on_synthetic_timeline(self) -> None:
        evaluation = MinimalRuleEvaluator().evaluate(
            valid_rule(),
            TimeSeriesWindow(
                series={
                    "A1": [0, 1, 1, 1, 0, 1, 1, 1],
                    "S1": [10, 10, 11, 12, 12, 12, 12, 12],
                },
                sampling_period_seconds=1.0,
            ),
        )

        self.assertTrue(evaluation.anomaly)
        self.assertEqual(evaluation.trigger_count, 2)
        self.assertEqual(evaluation.matched_response_count, 1)
        self.assertEqual(evaluation.missing_response_count, 1)

    def test_evaluator_does_not_flag_when_response_occurs(self) -> None:
        evaluation = MinimalRuleEvaluator().evaluate(
            valid_rule(),
            TimeSeriesWindow(
                series={
                    "A1": [0, 1, 1, 1],
                    "S1": [10, 10, 11, 12],
                },
                sampling_period_seconds=1.0,
            ),
        )

        self.assertFalse(evaluation.anomaly)
        self.assertEqual(evaluation.matched_response_count, 1)

    def test_deterministic_formatting_uses_ast(self) -> None:
        rule = valid_rule()
        formatted = format_rule(rule)

        self.assertEqual(
            formatted,
            "IF A1 changed from 0 to 1 AND S1 fails to increase by at least 2 within 3 seconds THEN anomaly",
        )
        self.assertNotIn(rule.description_template, formatted)

    def test_unknown_top_level_fields_are_rejected(self) -> None:
        payload = valid_rule().to_dict()
        payload["python_code"] = "print(1)"

        with self.assertRaisesRegex(RuleDslError, "unsupported fields"):
            RuleAst.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
