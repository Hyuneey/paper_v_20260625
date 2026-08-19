from __future__ import annotations

from dataclasses import fields, replace
import json
from pathlib import Path
import unittest

from paperworks.v6 import task039e3_r2r_utility_protocol_v4 as v4
from paperworks.v6 import task039e3_r2r_utility_source_census_supplement_v1 as supplement
from paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 import (
    SUPPLEMENT_PURPOSE,
    SyntheticNumericRecordV1,
    SyntheticNumericResolverV1,
    build_evaluator_authority_bundle_v1,
    build_synthetic_numeric_resolver_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_census_v1 import (
    enumerate_full_census_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_input_v1 import (
    build_synthetic_feature_frame_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_rule_engine_v1 import (
    ABSTAIN_STATE,
    ANOMALY_STATE,
    EXPECTED_RESPONSE_STATE,
    execute_rule_v1,
    validate_rule_execution_result_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import (
    REAL_AUTHORIZED_UTILITY_EXECUTION,
    SYNTHETIC_CONTRACT_ONLY,
    UtilityEvaluatorV1Error,
)


ROOT = Path(__file__).resolve().parents[1]
NEGATIVE_SYNTHETIC_CASES = 20


def load(relative_path: str) -> dict[str, object]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def bypass_mutation(value: object, **changes: object) -> object:
    result = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(result, field.name, changes.get(field.name, getattr(value, field.name)))
    return result


def forge_resolver(source: SyntheticNumericResolverV1, **changes: object) -> SyntheticNumericResolverV1:
    result = object.__new__(SyntheticNumericResolverV1)
    defaults = {
        "_bundle": source._bundle,
        "_bundle_hash": source._bundle_hash,
        "_relation_values": dict(source._relation_values),
        "_relation_references": dict(source._relation_references),
        "_source_values": dict(source._source_values),
        "_resolver_identity": source._resolver_identity,
        "validated": source.validated,
    }
    defaults.update(changes)
    for name, value in defaults.items():
        object.__setattr__(result, name, value)
    return result


class UtilityEvaluatorV1RuleEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.v4_authority = v4.build_utility_protocol_v4_canonical_authority(
            executable_equivalence=load(
                "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"
            ),
            evidence_manifest=load(
                "docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json"
            ),
            dataset_manifest=load(
                "docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json"
            ),
            csv_structure_report=load(
                "docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json"
            ),
            c0_config=load("configs/v6/task039c0_candidate_discovery_protocol.json"),
            br2_config=load(
                "configs/v6/task039br2_hai_continuous_step_feasibility.json"
            ),
            materialized_audit_receipt=load(
                "docs/task_reports/TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZED_RECEIPT.json"
            ),
        )
        cls.bundle = build_evaluator_authority_bundle_v1(cls.v4_authority)
        cls.rule = next(
            rule
            for rule in cls.v4_authority.rule_descriptors
            if rule.selected_horizon_seconds == 10
        )
        cls.resolver = cls._build_resolver()

    @classmethod
    def _build_resolver(cls) -> SyntheticNumericResolverV1:
        values: dict[str, int | float] = {
            "source_step_threshold": 1.0,
            "source_stability_tolerance": 0.0,
            "target_noise_scale": 0.5,
            "source_pre_window_seconds": 5,
            "source_post_window_seconds": 5,
            "minimum_source_stability_fraction": 0.8,
            "source_refractory_seconds": 10,
            "cross_source_isolation_radius_seconds": 2,
            "target_baseline_window_seconds": 5,
            "target_response_window_seconds": 3,
        }
        main = tuple(
            SyntheticNumericRecordV1(
                "SYNTHETIC_MAIN_420",
                rule.source,
                rule.relation_binding_hash,
                role,
                reference,
                values[role],
            )
            for rule in cls.v4_authority.rule_descriptors
            for role, reference in rule.numeric_reference_bindings
        )
        extra = tuple(
            SyntheticNumericRecordV1(
                SUPPLEMENT_PURPOSE,
                source,
                None,
                role,
                supplement.supplement_reference_identity_v1(source, role),
                1.0 if role == "source_step_threshold" else 0.0,
            )
            for source in supplement.SUPPLEMENT_SOURCES
            for role in supplement.SUPPLEMENT_ROLES
        )
        return build_synthetic_numeric_resolver_v1(cls.bundle, main, extra)

    @classmethod
    def _frame(
        cls,
        *,
        outcome: str,
        start: int = 80,
        length: int = 80,
        event_index: int = 100,
    ):
        ordered = cls.v4_authority.feature_schema.union_features
        response_start = event_index + cls.rule.selected_horizon_seconds
        rows = []
        for physical in range(start, start + length):
            values = []
            for feature in ordered:
                value = 0.0
                if feature == cls.rule.source and physical >= event_index + 1:
                    value = 2.0 if cls.rule.source_direction == "step_up" else -2.0
                if (
                    outcome == "expected"
                    and feature == cls.rule.target
                    and response_start <= physical < response_start + 3
                ):
                    value = 2.0 if cls.rule.target_direction == "increase" else -2.0
                values.append(value)
            rows.append(tuple(values))
        return build_synthetic_feature_frame_v1(
            cls.bundle,
            source_file_identity="hai-test1.csv",
            start_physical_row_index=start,
            rows=tuple(rows),
        )

    @classmethod
    def _case(cls, *, outcome: str = "expected", **frame_overrides: object):
        frame = cls._frame(outcome=outcome, **frame_overrides)
        census = enumerate_full_census_v1(frame, cls.bundle, cls.resolver)
        envelope = next(
            item
            for item in census.relation_opportunities
            if item.canonical_opportunity.relation_binding_hash
            == cls.rule.relation_binding_hash
        )
        return frame, census, envelope

    def test_expected_response_is_deterministic_and_value_free(self) -> None:
        frame, census, envelope = self._case()
        first = execute_rule_v1(envelope, census, frame, self.bundle, self.resolver)
        second = execute_rule_v1(envelope, census, frame, self.bundle, self.resolver)
        self.assertEqual(first, second)
        self.assertEqual(first.execution_mode, SYNTHETIC_CONTRACT_ONLY)
        self.assertEqual(first.final_state, EXPECTED_RESPONSE_STATE)
        self.assertFalse(first.alarm_emitted)
        self.assertIsNotNone(first.source_qualification_identity)
        self.assertIsNotNone(first.target_evaluation_identity)
        self.assertEqual(len(first.numeric_reference_identities), 10)
        self.assertEqual(
            validate_rule_execution_result_v1(
                first, envelope, census, frame, self.bundle, self.resolver
            ),
            first.trace_hash,
        )
        public_text = json.dumps(first.__dict__, sort_keys=True)
        self.assertNotIn("threshold", public_text)
        self.assertNotIn("tolerance", public_text)
        self.assertNotIn("noise_scale", public_text)

    def test_missing_response_emits_anomaly_alarm(self) -> None:
        frame, census, envelope = self._case(outcome="anomaly")
        result = execute_rule_v1(envelope, census, frame, self.bundle, self.resolver)
        self.assertEqual(result.final_state, ANOMALY_STATE)
        self.assertTrue(result.alarm_emitted)
        self.assertEqual(
            result.decision_physical_row_index,
            100 + self.rule.selected_horizon_seconds + 2,
        )

    def test_valid_incomplete_target_context_abstains_with_parent_chain(self) -> None:
        frame, census, envelope = self._case(outcome="anomaly", length=25)
        result = execute_rule_v1(envelope, census, frame, self.bundle, self.resolver)
        self.assertEqual(result.final_state, ABSTAIN_STATE)
        self.assertFalse(result.alarm_emitted)
        self.assertIsNone(result.decision_physical_row_index)
        self.assertIsNotNone(result.source_qualification_identity)
        self.assertIsNotNone(result.target_evaluation_identity)

    def test_physical_file_boundary_abstains(self) -> None:
        row_count = v4.FILE_ROW_COUNTS["hai-test1.csv"]
        event_index = row_count - 5
        frame, census, envelope = self._case(
            outcome="anomaly",
            start=row_count - 25,
            length=25,
            event_index=event_index,
        )
        result = execute_rule_v1(envelope, census, frame, self.bundle, self.resolver)
        self.assertEqual(result.final_state, ABSTAIN_STATE)
        self.assertIsNotNone(result.source_qualification_identity)
        self.assertIsNotNone(result.target_evaluation_identity)

    def test_twenty_invalid_authority_parent_and_result_cases_reject(self) -> None:
        frame, census, envelope = self._case()
        result = execute_rule_v1(envelope, census, frame, self.bundle, self.resolver)
        opportunity = envelope.canonical_opportunity

        changed_opportunity = bypass_mutation(
            opportunity,
            semantic_execution_hash="a" * 64,
        )
        detached_envelope = replace(
            envelope,
            isolated_source_event_identity="b" * 64,
        )
        forged_resolver = forge_resolver(self.resolver)
        forged_resolver._relation_values[(self.rule.relation_binding_hash, "target_noise_scale")] = 1
        wrong_reference_resolver = forge_resolver(self.resolver)
        wrong_reference_resolver._relation_references[
            (self.rule.relation_binding_hash, "target_noise_scale")
        ] = "c" * 64
        wrong_bundle_resolver = forge_resolver(self.resolver, _bundle_hash="d" * 64)
        unvalidated_resolver = self._build_resolver()
        unvalidated_resolver.validated = False

        execution_cases = (
            (replace(envelope, envelope_hash="a" * 64), census, frame, self.bundle, self.resolver),
            (replace(envelope, canonical_opportunity=changed_opportunity), census, frame, self.bundle, self.resolver),
            (detached_envelope, census, frame, self.bundle, self.resolver),
            (envelope, replace(census, census_hash="a" * 64), frame, self.bundle, self.resolver),
            (envelope, replace(census, relation_opportunities=()), frame, self.bundle, self.resolver),
            (envelope, census, replace(frame, frame_hash="a" * 64), self.bundle, self.resolver),
            (envelope, census, replace(frame, execution_mode=REAL_AUTHORIZED_UTILITY_EXECUTION), self.bundle, self.resolver),
            (envelope, census, replace(frame, dataset_manifest_identity="a" * 64), self.bundle, self.resolver),
            (envelope, census, replace(frame, split_identity="wrong-split"), self.bundle, self.resolver),
            (envelope, census, replace(frame, source_file_identity="hai-test2.csv"), self.bundle, self.resolver),
            (envelope, census, replace(frame, rows=(replace(frame.rows[0], row_identity="a" * 64), *frame.rows[1:])), self.bundle, self.resolver),
            (envelope, census, frame, replace(self.bundle, v4_authority_hash=v4.HISTORICAL_CANONICAL_V4_AUTHORITY_HASH), self.resolver),
            (envelope, census, frame, self.bundle, object()),
            (envelope, census, frame, self.bundle, unvalidated_resolver),
            (envelope, census, frame, self.bundle, wrong_bundle_resolver),
            (envelope, census, frame, self.bundle, forged_resolver),
            (envelope, census, frame, self.bundle, wrong_reference_resolver),
        )
        self.assertEqual(len(execution_cases), 17)
        for index, arguments in enumerate(execution_cases):
            with self.subTest(case=index), self.assertRaises(UtilityEvaluatorV1Error):
                execute_rule_v1(*arguments)

        result_cases = (
            replace(result, final_state=ANOMALY_STATE),
            replace(result, alarm_emitted=True),
            replace(result, numeric_reference_identities=result.numeric_reference_identities[:-1]),
        )
        self.assertEqual(len(execution_cases) + len(result_cases), NEGATIVE_SYNTHETIC_CASES)
        for index, changed in enumerate(result_cases):
            with self.subTest(result_case=index), self.assertRaises(UtilityEvaluatorV1Error):
                validate_rule_execution_result_v1(
                    changed,
                    envelope,
                    census,
                    frame,
                    self.bundle,
                    self.resolver,
                )

    def test_malformed_source_evidence_is_error_not_abstention(self) -> None:
        frame, census, envelope = self._case()
        inconsistent = forge_resolver(self.resolver)
        inconsistent._relation_values[
            (self.rule.relation_binding_hash, "source_step_threshold")
        ] = 3.0
        with self.assertRaises(UtilityEvaluatorV1Error):
            execute_rule_v1(envelope, census, frame, self.bundle, inconsistent)


if __name__ == "__main__":
    unittest.main()
