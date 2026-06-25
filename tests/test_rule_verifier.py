from __future__ import annotations

import unittest

from paperworks.data import SplitRole
from paperworks.data.contracts import stable_hash
from paperworks.dsl import (
    CalibrationValueRef,
    ChangedToPredicate,
    IncreaseWithinPredicate,
    PlannerProvenance,
    ResponseMissingPredicate,
    RuleAst,
    RuleSchemaRegistry,
    TimeSeriesWindow,
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
from paperworks.verification import VerificationConfig, VerificationDataset, VerificationError, verify_rule, verify_rule_json


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


def metadata(*, missing_target: bool = False, bad_source_type: bool = False) -> MetadataRegistry:
    variables = [sensor("A1") if bad_source_type else actuator("A1")]
    if not missing_target:
        variables.append(sensor("S1"))
    return MetadataRegistry(variables)


def calibration_records(*, support: int = 2) -> tuple[CalibrationRecord, CalibrationRecord]:
    delay = CalibrationRecord(
        parameter_name="max_response_delay_seconds",
        value=3.0,
        unit="seconds",
        method="synthetic_fixture",
        quantile_or_config={"quantile": 1.0},
        normal_support_count=support,
        relation_profile_id=RELATION_PROFILE_ID,
        calibration_split_id=CALIBRATION_SPLIT_ID,
    )
    magnitude = CalibrationRecord(
        parameter_name="min_response_magnitude",
        value=2.0,
        unit="target_units",
        method="synthetic_fixture",
        quantile_or_config={"quantile": 0.0},
        normal_support_count=support,
        relation_profile_id=RELATION_PROFILE_ID,
        calibration_split_id=CALIBRATION_SPLIT_ID,
    )
    return delay, magnitude


def refs(*, magnitude: float = 2.0, delay: float = 3.0, id_suffix: str = "", support: int = 2) -> dict[str, CalibrationValueRef]:
    records = {record.parameter_name: record for record in calibration_records(support=support)}
    delay_id = records["max_response_delay_seconds"].calibration_id if not id_suffix else stable_hash({"delay": id_suffix})
    magnitude_id = records["min_response_magnitude"].calibration_id if not id_suffix else stable_hash({"magnitude": id_suffix})
    return {
        "max_response_delay_seconds": CalibrationValueRef(
            parameter_name="max_response_delay_seconds",
            calibration_record_id=delay_id,
            field_name="value",
            resolved_value=delay,
            unit="seconds",
        ),
        "min_response_magnitude": CalibrationValueRef(
            parameter_name="min_response_magnitude",
            calibration_record_id=magnitude_id,
            field_name="value",
            resolved_value=magnitude,
            unit="target_units",
        ),
    }


def rule(
    *,
    rule_id: str = "rule.synthetic.A1.S1",
    source: str = "A1",
    target: str = "S1",
    references: dict[str, CalibrationValueRef] | None = None,
) -> RuleAst:
    calibration_refs = references or refs()
    expected_response = IncreaseWithinPredicate(
        variable=target,
        min_magnitude=calibration_refs["min_response_magnitude"],
        max_delay_seconds=calibration_refs["max_response_delay_seconds"],
    )
    return RuleAst(
        rule_id=rule_id,
        schema_version="1.0",
        source=source,
        target=target,
        relation_type="binary_actuator_to_continuous_sensor",
        trigger_predicate=ChangedToPredicate(variable=source, from_state=0.0, to_state=1.0),
        response_predicate=ResponseMissingPredicate(expected_response=expected_response),
        calibration_references=calibration_refs,
        candidate_pair_artifact_id=CANDIDATE_PAIR_ID,
        metadata_artifact_id=METADATA_ID,
        planner_provenance=PlannerProvenance(
            planner_type="deterministic_template",
            planner_version="1.0",
            source_artifact_ids=(SOURCE_ARTIFACT_ID,),
        ),
        description_template="deterministic response missing rule",
    )


def registry(*, records: bool = True, support: int = 2, missing_target: bool = False, bad_source_type: bool = False) -> RuleSchemaRegistry:
    calibration = calibration_records(support=support)
    return RuleSchemaRegistry(
        metadata=metadata(missing_target=missing_target, bad_source_type=bad_source_type),
        calibration_records={record.calibration_id: record for record in calibration} if records else {},
    )


def config(**overrides) -> VerificationConfig:
    values = {
        "max_normal_false_fire_rate": 0.0,
        "min_validation_coverage": 0.5,
        "firing_overlap_jaccard_threshold": 0.8,
        "min_calibration_support_count": 2,
        "parameter_neighborhood_relative_tolerance": 0.0,
    }
    values.update(overrides)
    return VerificationConfig(**values)


def window(*, anomaly: bool) -> TimeSeriesWindow:
    if anomaly:
        return TimeSeriesWindow(series={"A1": [0, 1, 1, 1], "S1": [10, 10, 10, 10]}, sampling_period_seconds=1.0)
    return TimeSeriesWindow(series={"A1": [0, 1, 1, 1], "S1": [10, 10, 11, 12]}, sampling_period_seconds=1.0)


def normal_dataset(*, anomaly_count: int = 0) -> VerificationDataset:
    windows = [window(anomaly=index < anomaly_count) for index in range(2)]
    return VerificationDataset(split_role=SplitRole.CALIBRATION_NORMAL, windows=tuple(windows), data_fingerprint="f" * 64)


def validation_dataset(*, anomaly_count: int = 1) -> VerificationDataset:
    windows = [window(anomaly=index < anomaly_count) for index in range(2)]
    return VerificationDataset(split_role=SplitRole.VALIDATION, windows=tuple(windows), data_fingerprint="1" * 64)


class RuleVerifierTests(unittest.TestCase):
    def test_valid_rule_passes(self) -> None:
        report = verify_rule(
            rule(),
            registry=registry(),
            normal_dataset=normal_dataset(),
            validation_dataset=validation_dataset(),
            config=config(),
        )

        self.assertEqual(report.status, "passed")
        self.assertEqual(report.issues, ())
        self.assertEqual(report.metrics["normal_false_fire_rate"], 0.0)
        self.assertEqual(report.metrics["validation_coverage"], 0.5)

    def test_invalid_schema_json_returns_structured_issue(self) -> None:
        report = verify_rule_json(
            '{"schema_version":"9.9"}',
            registry=registry(),
            normal_dataset=normal_dataset(),
            validation_dataset=validation_dataset(),
            config=config(),
        )

        self.assertEqual(report.status, "rejected")
        self.assertEqual(report.rule_id, "unparsed")
        self.assertEqual(report.issues[0].code, "DSL_SCHEMA_INVALID")

    def test_missing_variable_is_reported(self) -> None:
        report = verify_rule(
            rule(),
            registry=registry(missing_target=True),
            normal_dataset=normal_dataset(),
            validation_dataset=validation_dataset(),
            config=config(),
        )

        self.assertIn("VARIABLE_NOT_FOUND", {issue.code for issue in report.issues})

    def test_type_mismatch_is_reported(self) -> None:
        report = verify_rule(
            rule(),
            registry=registry(bad_source_type=True),
            normal_dataset=normal_dataset(),
            validation_dataset=validation_dataset(),
            config=config(),
        )

        self.assertIn("TYPE_MISMATCH", {issue.code for issue in report.issues})

    def test_missing_calibration_is_reported(self) -> None:
        report = verify_rule(
            rule(),
            registry=registry(records=False),
            normal_dataset=normal_dataset(),
            validation_dataset=validation_dataset(),
            config=config(),
        )

        self.assertIn("CALIBRATION_MISSING", {issue.code for issue in report.issues})

    def test_calibration_mutation_is_detected(self) -> None:
        report = verify_rule(
            rule(references=refs(magnitude=99.0)),
            registry=registry(),
            normal_dataset=normal_dataset(),
            validation_dataset=validation_dataset(),
            config=config(),
        )

        self.assertIn("NUMERIC_PARAMETER_MUTATED", {issue.code for issue in report.issues})

    def test_insufficient_normal_support_is_reported(self) -> None:
        report = verify_rule(
            rule(references=refs(support=1)),
            registry=registry(support=1),
            normal_dataset=normal_dataset(),
            validation_dataset=validation_dataset(),
            config=config(min_calibration_support_count=2),
        )

        self.assertIn("INSUFFICIENT_NORMAL_SUPPORT", {issue.code for issue in report.issues})

    def test_high_normal_false_firing_is_reported(self) -> None:
        report = verify_rule(
            rule(),
            registry=registry(),
            normal_dataset=normal_dataset(anomaly_count=1),
            validation_dataset=validation_dataset(),
            config=config(),
        )

        self.assertIn("NORMAL_FP_TOO_HIGH", {issue.code for issue in report.issues})

    def test_low_validation_coverage_is_reported(self) -> None:
        report = verify_rule(
            rule(),
            registry=registry(),
            normal_dataset=normal_dataset(),
            validation_dataset=validation_dataset(anomaly_count=0),
            config=config(),
        )

        self.assertIn("VALIDATION_COVERAGE_TOO_LOW", {issue.code for issue in report.issues})

    def test_structural_duplicate_is_reported(self) -> None:
        existing = rule(rule_id="rule.existing")
        report = verify_rule(
            rule(),
            registry=registry(),
            normal_dataset=normal_dataset(),
            validation_dataset=validation_dataset(),
            existing_rules=(existing,),
            config=config(),
        )

        self.assertIn("STRUCTURAL_DUPLICATE", {issue.code for issue in report.issues})
        self.assertEqual(report.duplicate_references, ("rule.existing",))

    def test_firing_overlap_duplicate_is_reported(self) -> None:
        existing = rule(rule_id="rule.existing", references=refs(magnitude=3.0, id_suffix="other"))
        report = verify_rule(
            rule(),
            registry=registry(),
            normal_dataset=normal_dataset(),
            validation_dataset=validation_dataset(anomaly_count=2),
            existing_rules=(existing,),
            config=config(firing_overlap_jaccard_threshold=0.8),
        )

        self.assertIn("FIRING_OVERLAP_DUPLICATE", {issue.code for issue in report.issues})
        self.assertEqual(report.duplicate_references, ("rule.existing",))

    def test_report_is_deterministic(self) -> None:
        first = verify_rule(rule(), registry=registry(), normal_dataset=normal_dataset(), validation_dataset=validation_dataset(), config=config())
        second = verify_rule(rule(), registry=registry(), normal_dataset=normal_dataset(), validation_dataset=validation_dataset(), config=config())

        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.report_id, second.report_id)

    def test_malicious_payload_is_rejected_without_execution(self) -> None:
        payload = serialize_rule_json(rule()).replace(
            "deterministic response missing rule",
            "__import__('os').system('echo bad')",
        )
        report = verify_rule_json(
            payload,
            registry=registry(),
            normal_dataset=normal_dataset(),
            validation_dataset=validation_dataset(),
            config=config(),
        )

        self.assertEqual(report.status, "rejected")
        self.assertEqual(report.issues[0].code, "DSL_SCHEMA_INVALID")

    def test_test_role_rejected(self) -> None:
        with self.assertRaises(VerificationError):
            VerificationDataset(split_role=SplitRole.TEST, windows=(window(anomaly=False),))


if __name__ == "__main__":
    unittest.main()
