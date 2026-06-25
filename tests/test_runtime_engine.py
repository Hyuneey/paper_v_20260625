from __future__ import annotations

import ast
from pathlib import Path
import unittest

from paperworks.data import DataViewManifest, DataViewName
from paperworks.data.contracts import stable_hash
from paperworks.dsl import (
    CalibrationValueRef,
    ChangedToPredicate,
    IncreaseWithinPredicate,
    PlannerProvenance,
    ResponseMissingPredicate,
    RuleAst,
    RuleDslError,
    RuleSchemaRegistry,
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
from paperworks.runtime import RuntimeRuleEngine, RuntimeRuleEngineError, TimeSeriesBatch, VerifiedRuleLibrary


RELATION_PROFILE_ID = "a" * 64
CALIBRATION_SPLIT_ID = "b" * 64
CANDIDATE_PAIR_ID = "c" * 64
METADATA_ID = "d" * 64
REPORT_ID = "e" * 64
DATASET_ID = "f" * 64


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


def refs(*, bad_ids: bool = False) -> dict[str, CalibrationValueRef]:
    records = {record.parameter_name: record for record in calibration_records()}
    return {
        "max_response_delay_seconds": CalibrationValueRef(
            parameter_name="max_response_delay_seconds",
            calibration_record_id=stable_hash({"missing": "delay"}) if bad_ids else records["max_response_delay_seconds"].calibration_id,
            field_name="value",
            resolved_value=3.0,
            unit="seconds",
        ),
        "min_response_magnitude": CalibrationValueRef(
            parameter_name="min_response_magnitude",
            calibration_record_id=stable_hash({"missing": "magnitude"}) if bad_ids else records["min_response_magnitude"].calibration_id,
            field_name="value",
            resolved_value=2.0,
            unit="target_units",
        ),
    }


def rule(*, rule_id: str = "rule.synthetic.A1.S1", bad_calibration: bool = False) -> RuleAst:
    calibration_refs = refs(bad_ids=bad_calibration)
    expected_response = IncreaseWithinPredicate(
        variable="S1",
        min_magnitude=calibration_refs["min_response_magnitude"],
        max_delay_seconds=calibration_refs["max_response_delay_seconds"],
    )
    return RuleAst(
        rule_id=rule_id,
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
            source_artifact_ids=(CANDIDATE_PAIR_ID, METADATA_ID),
        ),
        description_template="runtime fixture rule",
    )


def registry() -> RuleSchemaRegistry:
    records = calibration_records()
    return RuleSchemaRegistry(
        metadata=metadata(),
        calibration_records={record.calibration_id: record for record in records},
    )


def data_view(*, name: DataViewName = DataViewName.CANONICAL_RULE, source_view: str = "canonical_rule_view") -> DataViewManifest:
    return DataViewManifest(
        name=name,
        sampling_period_seconds=1.0,
        preprocessing_config={},
        upstream_dataset_manifest_id=DATASET_ID,
        fingerprint="1" * 64,
        source_view=source_view,
    )


def library(*, rules: tuple[RuleAst, ...] | None = None, report_ids: dict[str, str] | None = None) -> VerifiedRuleLibrary:
    active_rules = rules or (rule(),)
    return VerifiedRuleLibrary(
        rules=active_rules,
        verification_report_ids=report_ids or {active_rule.rule_id: REPORT_ID for active_rule in active_rules},
    )


def engine_with_library(active_library: VerifiedRuleLibrary | None = None) -> RuntimeRuleEngine:
    engine = RuntimeRuleEngine(registry=registry())
    engine.load_library(active_library or library())
    return engine


class RuntimeRuleEngineTests(unittest.TestCase):
    def test_expected_synthetic_firing(self) -> None:
        evaluation = engine_with_library().evaluate(
            TimeSeriesBatch(
                series={"A1": [0, 1, 1, 1, 1], "S1": [10, 10, 10, 10, 10]},
                data_view=data_view(),
                batch_id="synthetic-anomaly",
            )
        )

        self.assertEqual(evaluation.aggregate_rule_score, 1.0)
        self.assertEqual(len(evaluation.firing_records), 1)
        self.assertEqual(evaluation.firing_records[0].alarm_start_seconds, 1.0)
        self.assertEqual(evaluation.firing_records[0].alarm_end_seconds, 4.0)
        self.assertEqual(len(evaluation.alarm_intervals), 1)
        self.assertEqual(evaluation.explanations[0].rule_id, "rule.synthetic.A1.S1")
        self.assertIn("below required 2", evaluation.explanations[0].observed_violation)

    def test_non_firing_normal_case(self) -> None:
        evaluation = engine_with_library().evaluate(
            TimeSeriesBatch(
                series={"A1": [0, 1, 1, 1], "S1": [10, 10, 11, 12]},
                data_view=data_view(),
                batch_id="synthetic-normal",
            )
        )

        self.assertEqual(evaluation.aggregate_rule_score, 0.0)
        self.assertEqual(evaluation.firing_records, ())
        self.assertEqual(evaluation.alarm_intervals, ())
        self.assertEqual(evaluation.explanations, ())

    def test_multiple_rule_aggregation(self) -> None:
        first = rule(rule_id="rule.synthetic.A1.S1.a")
        second = rule(rule_id="rule.synthetic.A1.S1.b")
        evaluation = engine_with_library(
            library(
                rules=(first, second),
                report_ids={
                    first.rule_id: REPORT_ID,
                    second.rule_id: "9" * 64,
                },
            )
        ).evaluate(
            TimeSeriesBatch(
                series={"A1": [0, 1, 1, 1, 1], "S1": [10, 10, 10, 10, 10]},
                data_view=data_view(),
            )
        )

        self.assertEqual(evaluation.aggregate_rule_score, 1.0)
        self.assertEqual(len(evaluation.firing_records), 2)
        self.assertEqual(len(evaluation.alarm_intervals), 1)
        self.assertEqual(evaluation.alarm_intervals[0].firing_count, 2)
        self.assertEqual(evaluation.alarm_intervals[0].rule_ids, ("rule.synthetic.A1.S1.a", "rule.synthetic.A1.S1.b"))

    def test_malformed_library_rejection(self) -> None:
        active_rule = rule()
        with self.assertRaises(RuntimeRuleEngineError):
            VerifiedRuleLibrary(rules=(active_rule,), verification_report_ids={})

    def test_invalid_calibration_reference_rejection(self) -> None:
        engine = RuntimeRuleEngine(registry=registry())
        with self.assertRaisesRegex(RuntimeRuleEngineError, "CALIBRATION_MISSING"):
            engine.load_library(library(rules=(rule(bad_calibration=True),)))

    def test_wrong_data_view_rejection(self) -> None:
        with self.assertRaisesRegex(RuntimeRuleEngineError, "canonical rule view"):
            TimeSeriesBatch(
                series={"A1": [0, 1, 1], "S1": [0, 0, 0]},
                data_view=data_view(name=DataViewName.GDN, source_view="gdn"),
            )

    def test_deterministic_explanation_and_evaluation_id(self) -> None:
        batch = TimeSeriesBatch(series={"A1": [0, 1, 1, 1, 1], "S1": [10, 10, 10, 10, 10]}, data_view=data_view())
        first = engine_with_library().evaluate(batch)
        second = engine_with_library().evaluate(batch)

        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.evaluation_id, second.evaluation_id)

    def test_runtime_import_boundary_has_no_planning_or_llm_dependency(self) -> None:
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
        self.assertFalse(any("openai" in name.lower() or "anthropic" in name.lower() for name in imported_modules))

    def test_malicious_payload_rejection(self) -> None:
        payload = serialize_rule_json(rule()).replace("runtime fixture rule", "__import__('os').system('echo bad')")

        with self.assertRaises(RuleDslError):
            parse_rule_json(payload)


if __name__ == "__main__":
    unittest.main()
