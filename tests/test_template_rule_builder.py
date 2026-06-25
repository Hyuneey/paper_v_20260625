from __future__ import annotations

import inspect
import unittest

from paperworks.dsl import MinimalRuleEvaluator, RuleSchemaRegistry, TimeSeriesWindow, serialize_rule_json
from paperworks.metadata import (
    MetadataRegistry,
    MetadataSourceMethod,
    PhysicalType,
    ReviewStatus,
    ValueType,
    VariableMetadata,
    VariableRole,
)
from paperworks.planning import build_template_rule
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


def evidence(
    *,
    relation_type: str = "binary_actuator_to_continuous_sensor",
    recommended_rule_family: str = "changed_to_increase_within_response_missing",
    include_delay: bool = True,
    include_magnitude: bool = True,
    upstream_artifact_ids: tuple[str, ...] = (CANDIDATE_PAIR_ID, METADATA_ID),
    matched_response_count: int = 2,
) -> RelationEvidencePack:
    records = {record.parameter_name: record for record in calibration_records()}
    ids = {}
    values = {}
    if include_delay:
        ids["max_response_delay_seconds"] = records["max_response_delay_seconds"].calibration_id
        values["max_response_delay_seconds"] = records["max_response_delay_seconds"].value
    if include_magnitude:
        ids["min_response_magnitude"] = records["min_response_magnitude"].calibration_id
        values["min_response_magnitude"] = records["min_response_magnitude"].value
    return RelationEvidencePack(
        source="A1",
        target="S1",
        relation_type=relation_type,
        recommended_rule_family=recommended_rule_family,
        relation_profile_id=RELATION_PROFILE_ID,
        calibration_record_ids=ids,
        calibrated_parameters=values,
        support_counts={
            "trigger_count": 2,
            "matched_response_count": matched_response_count,
            "missing_response_count": 0,
            "right_censored_count": 0,
            "overlapping_window_count": 0,
        },
        source_view="canonical_rule_view",
        sampling_period_seconds=1.0,
        upstream_artifact_ids=upstream_artifact_ids,
    )


def registry(*, include_records: bool = True, bad_metadata: bool = False) -> RuleSchemaRegistry:
    records = calibration_records()
    return RuleSchemaRegistry(
        metadata=MetadataRegistry([sensor("A1"), sensor("S1")]) if bad_metadata else metadata(),
        calibration_records={record.calibration_id: record for record in records} if include_records else {},
    )


class TemplateRuleBuilderTests(unittest.TestCase):
    def test_successful_template_build(self) -> None:
        result = build_template_rule(evidence(), registry())

        self.assertEqual(result.status, "built")
        self.assertIsNotNone(result.rule)
        assert result.rule is not None
        self.assertEqual(result.selected_rule_family, "changed_to_increase_within_response_missing")
        self.assertEqual(result.rule.source, "A1")
        self.assertEqual(result.rule.target, "S1")
        self.assertEqual(result.rule.candidate_pair_artifact_id, CANDIDATE_PAIR_ID)
        self.assertEqual(result.rule.metadata_artifact_id, METADATA_ID)
        self.assertEqual(result.rule.planner_provenance.planner_type, "deterministic_template")
        self.assertEqual(registry().validate(result.rule), [])

    def test_missing_calibration_prevents_generation(self) -> None:
        result = build_template_rule(evidence(), registry(include_records=False))

        self.assertEqual(result.status, "unsupported")
        self.assertEqual(result.unsupported_reason, "CALIBRATION_MISSING")
        self.assertIsNone(result.rule)

    def test_unsupported_relation_type_is_rejected_cleanly(self) -> None:
        result = build_template_rule(evidence(relation_type="sensor_to_sensor"), registry())

        self.assertEqual(result.status, "unsupported")
        self.assertEqual(result.unsupported_reason, "UNSUPPORTED_RELATION_TYPE")

    def test_metadata_type_mismatch_is_rejected(self) -> None:
        result = build_template_rule(evidence(), registry(bad_metadata=True))

        self.assertEqual(result.status, "unsupported")
        self.assertEqual(result.unsupported_reason, "TYPE_MISMATCH")

    def test_deterministic_output(self) -> None:
        first = build_template_rule(evidence(), registry())
        second = build_template_rule(evidence(), registry())

        self.assertEqual(first.result_id, second.result_id)
        assert first.rule is not None
        assert second.rule is not None
        self.assertEqual(serialize_rule_json(first.rule), serialize_rule_json(second.rule))

    def test_numeric_provenance_comes_from_calibration_records(self) -> None:
        result = build_template_rule(evidence(), registry())

        self.assertEqual(result.status, "built")
        assert result.rule is not None
        delay = result.rule.calibration_references["max_response_delay_seconds"]
        magnitude = result.rule.calibration_references["min_response_magnitude"]
        self.assertEqual(delay.field_name, "value")
        self.assertEqual(delay.unit, "seconds")
        self.assertEqual(delay.resolved_value, 3.0)
        self.assertEqual(magnitude.field_name, "value")
        self.assertEqual(magnitude.unit, "target_units")
        self.assertEqual(magnitude.resolved_value, 2.0)

    def test_evidence_numeric_mutation_blocks_generation(self) -> None:
        altered = evidence()
        altered = RelationEvidencePack.from_dict(
            {
                **altered.to_dict(),
                "calibrated_parameters": {
                    **dict(altered.calibrated_parameters),
                    "min_response_magnitude": 99.0,
                },
            }
        )

        result = build_template_rule(altered, registry())
        self.assertEqual(result.status, "unsupported")
        self.assertEqual(result.unsupported_reason, "NUMERIC_PARAMETER_MUTATED")

    def test_insufficient_support_blocks_generation(self) -> None:
        result = build_template_rule(evidence(matched_response_count=0), registry())

        self.assertEqual(result.status, "unsupported")
        self.assertEqual(result.unsupported_reason, "INSUFFICIENT_NORMAL_SUPPORT")

    def test_no_test_role_or_raw_window_input_in_builder_interface(self) -> None:
        signature = inspect.signature(build_template_rule)

        self.assertEqual(tuple(signature.parameters), ("evidence", "registry"))
        self.assertNotIn("split", signature.parameters)
        self.assertNotIn("window", signature.parameters)
        self.assertNotIn("series", signature.parameters)

    def test_built_rule_evaluates_with_existing_deterministic_evaluator(self) -> None:
        result = build_template_rule(evidence(), registry())

        self.assertEqual(result.status, "built")
        assert result.rule is not None
        evaluation = MinimalRuleEvaluator().evaluate(
            result.rule,
            TimeSeriesWindow(
                series={
                    "A1": [0, 1, 1, 1],
                    "S1": [10, 10, 11, 12],
                },
                sampling_period_seconds=1.0,
            ),
        )
        self.assertFalse(evaluation.anomaly)

    def test_result_round_trip_dict_is_stable(self) -> None:
        result = build_template_rule(evidence(), registry())

        self.assertEqual(result.to_dict()["status"], "built")
        self.assertEqual(result.result_id, build_template_rule(evidence(), registry()).result_id)


if __name__ == "__main__":
    unittest.main()
