from __future__ import annotations

import unittest

from paperworks.data import SplitRole
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
from paperworks.planning import (
    MockLLMProvider,
    RefinementPolicy,
    audit_prompt_payload,
    plan_rule_with_provider,
    refine_rule_with_feedback,
)
from paperworks.profiling import CalibrationRecord, RelationEvidencePack
from paperworks.verification import VerificationConfig, VerificationDataset, VerificationError


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


def registry(*, include_s2: bool = False, support: int = 2) -> RuleSchemaRegistry:
    variables = [actuator(), sensor()]
    if include_s2:
        variables.append(sensor("S2"))
    return RuleSchemaRegistry(
        metadata=MetadataRegistry(variables),
        calibration_records={record.calibration_id: record for record in calibration_records(support=support)},
    )


def evidence(*, support: int = 2) -> RelationEvidencePack:
    records = {record.parameter_name: record for record in calibration_records(support=support)}
    return RelationEvidencePack(
        source="A1",
        target="S1",
        relation_type="binary_actuator_to_continuous_sensor",
        recommended_rule_family="changed_to_increase_within_response_missing",
        relation_profile_id=RELATION_PROFILE_ID,
        calibration_record_ids={name: record.calibration_id for name, record in records.items()},
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


def rule_json(
    *,
    from_state: float = 0.0,
    to_state: float = 1.0,
    target: str = "S1",
    magnitude: float = 2.0,
    description: str = "mock refiner rule",
    support: int = 2,
) -> str:
    records = {record.parameter_name: record for record in calibration_records(support=support)}
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
        rule_id=f"rule.mock.{from_state:g}.{to_state:g}.{target}",
        schema_version="1.0",
        source="A1",
        target=target,
        relation_type="binary_actuator_to_continuous_sensor",
        trigger_predicate=ChangedToPredicate(variable="A1", from_state=from_state, to_state=to_state),
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


def initial_planner_result(*, support: int = 2):
    return plan_rule_with_provider(
        evidence=evidence(support=support),
        registry=registry(support=support),
        provider=MockLLMProvider(response_text=rule_json(support=support)),
        created_at="2026-06-25T00:00:00Z",
    )


def verifier_config(**overrides) -> VerificationConfig:
    values = {
        "max_normal_false_fire_rate": 0.0,
        "min_validation_coverage": 0.5,
        "firing_overlap_jaccard_threshold": 0.8,
        "min_calibration_support_count": 2,
        "parameter_neighborhood_relative_tolerance": 0.0,
    }
    values.update(overrides)
    return VerificationConfig(**values)


def window(source: list[float], target: list[float]) -> TimeSeriesWindow:
    return TimeSeriesWindow(series={"A1": source, "S1": target}, sampling_period_seconds=1.0)


def normal_dataset() -> VerificationDataset:
    return VerificationDataset(
        split_role=SplitRole.CALIBRATION_NORMAL,
        windows=(
            window([0, 1, 1, 1], [10, 10, 10, 10]),
            window([0, 0, 0, 0], [10, 10, 10, 10]),
        ),
        data_fingerprint="f" * 64,
    )


def validation_dataset() -> VerificationDataset:
    return VerificationDataset(
        split_role=SplitRole.VALIDATION,
        windows=(
            window([1, 0, 0, 0], [10, 10, 10, 10]),
            window([1, 1, 1, 1], [10, 10, 10, 10]),
        ),
        data_fingerprint="1" * 64,
    )


class LLMRefinerTests(unittest.TestCase):
    def test_successful_refinement(self) -> None:
        session = refine_rule_with_feedback(
            initial_planner_result=initial_planner_result(),
            evidence=evidence(),
            registry=registry(),
            provider=MockLLMProvider(response_text=rule_json(from_state=1.0, to_state=0.0)),
            normal_dataset=normal_dataset(),
            validation_dataset=validation_dataset(),
            verifier_config=verifier_config(),
            policy=RefinementPolicy(max_iterations=2),
            created_at="2026-06-25T00:00:00Z",
        )

        self.assertEqual(session.status, "verified")
        self.assertEqual(session.stop_reason, "verifier_passed")
        self.assertEqual(len(session.iterations), 1)
        self.assertEqual(session.iterations[0].iteration_index, 0)
        self.assertEqual(session.iterations[0].parse_status, "parsed")
        self.assertEqual(session.iterations[0].schema_validation_status, "passed")
        self.assertEqual(session.iterations[0].verification_status, "passed")
        self.assertIn("NORMAL_FP_TOO_HIGH", session.iterations[0].feedback_codes)
        self.assertIn("VALIDATION_COVERAGE_TOO_LOW", session.iterations[0].feedback_codes)

    def test_planner_and_provider_config_hashes_are_distinct(self) -> None:
        result = initial_planner_result()
        payload = result.to_dict()

        self.assertIn("provider_config_hash", payload)
        self.assertIn("planner_config_hash", payload)
        self.assertNotEqual(payload["provider_config_hash"], payload["planner_config_hash"])
        self.assertNotEqual(payload["config_hash"], payload["provider_config_hash"])

    def test_non_recoverable_failure_stops_without_refinement(self) -> None:
        session = refine_rule_with_feedback(
            initial_planner_result=initial_planner_result(support=1),
            evidence=evidence(support=1),
            registry=registry(support=1),
            provider=MockLLMProvider(response_text=rule_json(from_state=1.0, to_state=0.0, support=1)),
            normal_dataset=normal_dataset(),
            validation_dataset=validation_dataset(),
            verifier_config=verifier_config(min_calibration_support_count=2),
            policy=RefinementPolicy(max_iterations=2),
        )

        self.assertEqual(session.status, "rejected")
        self.assertEqual(session.stop_reason, "non_recoverable_feedback")
        self.assertEqual(session.iterations, ())
        self.assertIn("INSUFFICIENT_NORMAL_SUPPORT", {issue.code for issue in session.initial_verification_report.issues})

    def test_repeated_rule_termination(self) -> None:
        session = refine_rule_with_feedback(
            initial_planner_result=initial_planner_result(),
            evidence=evidence(),
            registry=registry(),
            provider=MockLLMProvider(response_text=rule_json()),
            normal_dataset=normal_dataset(),
            validation_dataset=validation_dataset(),
            verifier_config=verifier_config(),
            policy=RefinementPolicy(max_iterations=2),
        )

        self.assertEqual(session.status, "rejected")
        self.assertEqual(session.stop_reason, "repeated_rule")
        self.assertEqual(session.iterations[0].stop_reason, "repeated_rule")

    def test_max_iteration_termination(self) -> None:
        session = refine_rule_with_feedback(
            initial_planner_result=initial_planner_result(),
            evidence=evidence(),
            registry=registry(),
            provider=MockLLMProvider(response_text=rule_json(from_state=0.0, to_state=0.0)),
            normal_dataset=normal_dataset(),
            validation_dataset=validation_dataset(),
            verifier_config=verifier_config(),
            policy=RefinementPolicy(max_iterations=1, stop_on_no_improvement=False),
        )

        self.assertEqual(session.status, "rejected")
        self.assertEqual(session.stop_reason, "max_iterations_exhausted")
        self.assertEqual(session.iterations[0].stop_reason, "max_iterations_exhausted")

    def test_no_improvement_termination(self) -> None:
        session = refine_rule_with_feedback(
            initial_planner_result=initial_planner_result(),
            evidence=evidence(),
            registry=registry(),
            provider=MockLLMProvider(response_text=rule_json(from_state=0.0, to_state=0.0)),
            normal_dataset=normal_dataset(),
            validation_dataset=validation_dataset(),
            verifier_config=verifier_config(min_validation_coverage=0.0),
            policy=RefinementPolicy(max_iterations=2),
        )

        self.assertEqual(session.status, "rejected")
        self.assertEqual(session.stop_reason, "no_improvement")

    def test_prohibited_variable_addition_rejected(self) -> None:
        session = refine_rule_with_feedback(
            initial_planner_result=initial_planner_result(),
            evidence=evidence(),
            registry=registry(),
            provider=MockLLMProvider(response_text=rule_json(target="S2")),
            normal_dataset=normal_dataset(),
            validation_dataset=validation_dataset(),
            verifier_config=verifier_config(),
            policy=RefinementPolicy(max_iterations=2),
        )

        self.assertEqual(session.stop_reason, "schema_validation_failed")
        self.assertIn("VARIABLE_NOT_FOUND", {issue.code for issue in session.iterations[0].planner_result.issues})

    def test_prohibited_numeric_change_rejected(self) -> None:
        session = refine_rule_with_feedback(
            initial_planner_result=initial_planner_result(),
            evidence=evidence(),
            registry=registry(),
            provider=MockLLMProvider(response_text=rule_json(magnitude=99.0)),
            normal_dataset=normal_dataset(),
            validation_dataset=validation_dataset(),
            verifier_config=verifier_config(),
            policy=RefinementPolicy(max_iterations=2),
        )

        self.assertEqual(session.stop_reason, "schema_validation_failed")
        self.assertIn("NUMERIC_PARAMETER_MUTATED", {issue.code for issue in session.iterations[0].planner_result.issues})

    def test_code_payload_rejected(self) -> None:
        payload = rule_json().replace("mock refiner rule", "__import__('os').system('echo bad')")
        session = refine_rule_with_feedback(
            initial_planner_result=initial_planner_result(),
            evidence=evidence(),
            registry=registry(),
            provider=MockLLMProvider(response_text=payload),
            normal_dataset=normal_dataset(),
            validation_dataset=validation_dataset(),
            verifier_config=verifier_config(),
            policy=RefinementPolicy(max_iterations=2),
        )

        self.assertEqual(session.stop_reason, "schema_validation_failed")
        self.assertEqual(session.iterations[0].parse_status, "parse_failed")

    def test_redaction_blocks_restricted_prompt_payloads(self) -> None:
        for payload in (
            {"test_label": "Attack"},
            {"test_interval": "sealed"},
            {"summary": "normal.csv"},
            {"summary": "attack.csv"},
            {"summary": "merged.csv"},
            {"summary": "2020-01-01 00:00:00,1,2,3"},
        ):
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(Exception, "redaction audit"):
                    audit_prompt_payload(payload)

    def test_deterministic_mocked_history(self) -> None:
        kwargs = dict(
            evidence=evidence(),
            registry=registry(),
            normal_dataset=normal_dataset(),
            validation_dataset=validation_dataset(),
            verifier_config=verifier_config(),
            policy=RefinementPolicy(max_iterations=2),
            created_at="2026-06-25T00:00:00Z",
        )
        first = refine_rule_with_feedback(
            initial_planner_result=initial_planner_result(),
            provider=MockLLMProvider(response_texts=(rule_json(from_state=1.0, to_state=0.0),)),
            **kwargs,
        )
        second = refine_rule_with_feedback(
            initial_planner_result=initial_planner_result(),
            provider=MockLLMProvider(response_texts=(rule_json(from_state=1.0, to_state=0.0),)),
            **kwargs,
        )

        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.session_id, second.session_id)

    def test_no_test_role_guard(self) -> None:
        with self.assertRaises(VerificationError):
            VerificationDataset(split_role=SplitRole.TEST, windows=(window([0, 1], [1, 1]),))


if __name__ == "__main__":
    unittest.main()
