"""Focused R2 implementation-provenance and prediction-custody tests.

All positive execution is explicitly synthetic.  Lower scientific authorities
are replayed from committed public artifacts; no locator or private registry is
opened.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import fields, replace
import unittest

import paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 as authority_v1
import paperworks.v6.task039e3_r2r_utility_evaluator_metrics_v1 as metrics_v1
import paperworks.v6.task039e3_r2r_utility_evaluator_v1 as evaluator_v1
from paperworks.v6 import task039e3_r2r_utility_source_census_supplement_v1 as supplement_v1
from paperworks.v6.task039e3_r2r_utility_evaluator_census_v1 import (
    enumerate_full_census_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_input_v1 import (
    build_synthetic_feature_frame_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_rule_engine_v1 import (
    execute_rule_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import (
    UtilityEvaluatorV1Error,
    dataclass_payload_v1,
    stable_hash_v1,
)
from tests.test_task039e3_r2r_utility_evaluator_v1_independent_authority import (
    build_lower_v4_authority,
)


ORIGINAL_IMPLEMENTATION_IDENTITY = (
    "332e367cdc0da21b281c5de43f6a735d7dc68bc87efafe90976d89d7f9dc3330"
)
R1_IMPLEMENTATION_IDENTITY = (
    "64a6e7f0d210dc074bc85b0f389e61b45aaa512091532cf8f4d275ccaa35746a"
)
R2_IMPLEMENTATION_IDENTITY = (
    "e7a61070c0be96e305f6706b90308c9976bc8d521c8b97adea93836c3fd28cef"
)
EXPECTED_BUNDLE_HASH = "0510da125dd8a799c988927ba49ecb784cad5ea12b05b41e31406effe23051c9"

UNIQUE_PROVENANCE_ATTACK_CLASSES = 20
RAW_PROVENANCE_ATTACKS = 20


def _numeric_value(role: str) -> int | float:
    return {
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
    }[role]


def _reconstruct(value: object) -> object:
    return type(value)(**{field.name: getattr(value, field.name) for field in fields(value)})


class UtilityEvaluatorV1R2ProvenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.v4_authority = build_lower_v4_authority()
        cls.bundle = authority_v1.build_evaluator_authority_bundle_v1(cls.v4_authority)
        cls.other_bundle = authority_v1.build_evaluator_authority_bundle_v1(
            cls.v4_authority
        )
        cls.implementation = authority_v1.build_evaluator_implementation_authority_v1(
            cls.bundle
        )

        main_records = tuple(
            authority_v1.SyntheticNumericRecordV1(
                "SYNTHETIC_MAIN_420",
                rule.source,
                rule.relation_binding_hash,
                role,
                reference,
                _numeric_value(role),
            )
            for rule in cls.v4_authority.rule_descriptors
            for role, reference in rule.numeric_reference_bindings
        )
        supplement_records = tuple(
            authority_v1.SyntheticNumericRecordV1(
                authority_v1.SUPPLEMENT_PURPOSE,
                source,
                None,
                role,
                supplement_v1.supplement_reference_identity_v1(source, role),
                _numeric_value(role),
            )
            for source in authority_v1.SUPPLEMENT_SOURCES
            for role in authority_v1.SOURCE_CENSUS_ROLES
        )
        cls.resolver = authority_v1.build_synthetic_numeric_resolver_v1(
            cls.bundle, main_records, supplement_records
        )

        rule = next(
            item
            for item in cls.v4_authority.rule_descriptors
            if item.selected_horizon_seconds == 10
        )
        rows = tuple(
            tuple(
                (
                    2.0 if rule.source_direction == "step_up" else -2.0
                )
                if feature == rule.source and physical_index >= 101
                else 0.0
                for feature in cls.v4_authority.feature_schema.union_features
            )
            for physical_index in range(80, 180)
        )
        cls.frame = build_synthetic_feature_frame_v1(
            cls.bundle,
            source_file_identity="hai-test1.csv",
            start_physical_row_index=80,
            rows=rows,
        )
        cls.census = enumerate_full_census_v1(cls.frame, cls.bundle, cls.resolver)
        cls.predictions = tuple(
            execute_rule_v1(envelope, cls.census, cls.frame, cls.bundle, cls.resolver)
            for envelope in cls.census.relation_opportunities
        )
        cls.artifact = metrics_v1.build_rule_prediction_artifact_v1(
            evaluator_implementation_authority=cls.implementation,
            bundle=cls.bundle,
            frame=cls.frame,
            census=cls.census,
            resolver=cls.resolver,
            predictions=cls.predictions,
        )

    def _artifact_kwargs(self) -> dict[str, object]:
        return {
            "bundle": self.bundle,
            "frame": self.frame,
            "census": self.census,
            "resolver": self.resolver,
            "predictions": self.predictions,
        }

    def assertArtifactBuildRejected(self, **authority_kwargs: object) -> None:  # noqa: N802
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics_v1.build_rule_prediction_artifact_v1(
                **authority_kwargs,
                **self._artifact_kwargs(),
            )

    def test_r2_implementation_authority_replays_exact_identity(self) -> None:
        self.assertEqual(authority_v1.UTILITY_EVALUATOR_CONTROL_REVISION, "R2")
        self.assertEqual(
            authority_v1.CURRENT_EVALUATOR_IMPLEMENTATION_IDENTITY,
            R2_IMPLEMENTATION_IDENTITY,
        )
        self.assertEqual(self.bundle.bundle_hash, EXPECTED_BUNDLE_HASH)
        self.assertEqual(
            authority_v1.validate_evaluator_implementation_authority_v1(
                self.implementation, self.bundle
            ),
            R2_IMPLEMENTATION_IDENTITY,
        )
        self.assertNotEqual(R2_IMPLEMENTATION_IDENTITY, R1_IMPLEMENTATION_IDENTITY)
        self.assertNotEqual(R2_IMPLEMENTATION_IDENTITY, ORIGINAL_IMPLEMENTATION_IDENTITY)

    def test_factory_issued_r2_authority_is_required_for_artifact(self) -> None:
        self.assertEqual(
            metrics_v1.validate_rule_prediction_artifact_v1(self.artifact),
            self.artifact.artifact_hash,
        )
        self.assertEqual(
            self.artifact.evaluator_implementation_identity,
            R2_IMPLEMENTATION_IDENTITY,
        )
        self.assertEqual(
            self.artifact.evaluator_authority_bundle_hash,
            EXPECTED_BUNDLE_HASH,
        )

    def test_all_bare_implementation_identities_reject(self) -> None:
        identities: tuple[object, ...] = (
            ORIGINAL_IMPLEMENTATION_IDENTITY,
            R1_IMPLEMENTATION_IDENTITY,
            R2_IMPLEMENTATION_IDENTITY,
            "f" * 64,
            "not-a-sha",
            None,
        )
        for identity in identities:
            with self.subTest(identity=identity):
                self.assertArtifactBuildRejected(
                    evaluator_implementation_identity=identity
                )

    def test_missing_or_ambiguous_implementation_authority_rejects(self) -> None:
        self.assertArtifactBuildRejected()
        self.assertArtifactBuildRejected(
            evaluator_implementation_authority=self.implementation,
            evaluator_implementation_identity=R2_IMPLEMENTATION_IDENTITY,
        )

    def test_reconstructed_copied_and_replaced_authorities_reject(self) -> None:
        candidates = (
            _reconstruct(self.implementation),
            deepcopy(self.implementation),
            replace(self.implementation),
        )
        for candidate in candidates:
            with self.subTest(candidate=type(candidate).__name__):
                self.assertArtifactBuildRejected(
                    evaluator_implementation_authority=candidate
                )

    def test_cross_bundle_implementation_authority_rejects(self) -> None:
        self.assertIsNot(self.bundle, self.other_bundle)
        self.assertEqual(self.bundle, self.other_bundle)
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics_v1.build_rule_prediction_artifact_v1(
                evaluator_implementation_authority=self.implementation,
                bundle=self.other_bundle,
                frame=self.frame,
                census=self.census,
                resolver=self.resolver,
                predictions=self.predictions,
            )

    def test_artifact_identity_mutations_and_self_rehash_reject(self) -> None:
        for identity in (
            ORIGINAL_IMPLEMENTATION_IDENTITY,
            R1_IMPLEMENTATION_IDENTITY,
            "f" * 64,
        ):
            candidate = replace(
                self.artifact,
                evaluator_implementation_identity=identity,
                artifact_hash="",
            )
            candidate = replace(
                candidate,
                artifact_hash=stable_hash_v1(
                    dataclass_payload_v1(candidate, exclude=("artifact_hash",))
                ),
            )
            with self.subTest(identity=identity), self.assertRaises(
                UtilityEvaluatorV1Error
            ):
                metrics_v1.validate_rule_prediction_artifact_v1(candidate)

    def test_artifact_reconstruction_deepcopy_and_noop_replace_reject(self) -> None:
        candidates = (
            _reconstruct(self.artifact),
            deepcopy(self.artifact),
            replace(self.artifact),
        )
        for candidate in candidates:
            with self.subTest(candidate=type(candidate).__name__), self.assertRaises(
                UtilityEvaluatorV1Error
            ):
                metrics_v1.validate_rule_prediction_artifact_v1(candidate)

    def test_issuance_metadata_binds_identity_and_bundle(self) -> None:
        issued_key = id(self.artifact)
        saved = metrics_v1._ISSUED_RULE_ARTIFACTS[issued_key]
        try:
            metrics_v1._ISSUED_RULE_ARTIFACTS[issued_key] = (
                saved[0],
                saved[1],
                "f" * 64,
                saved[3],
            )
            with self.assertRaises(UtilityEvaluatorV1Error):
                metrics_v1.validate_rule_prediction_artifact_v1(self.artifact)
            metrics_v1._ISSUED_RULE_ARTIFACTS[issued_key] = (
                saved[0],
                saved[1],
                saved[2],
                "e" * 64,
            )
            with self.assertRaises(UtilityEvaluatorV1Error):
                metrics_v1.validate_rule_prediction_artifact_v1(self.artifact)
        finally:
            metrics_v1._ISSUED_RULE_ARTIFACTS[issued_key] = saved

    def test_facade_rotates_only_provenance_not_scientific_outputs(self) -> None:
        run = evaluator_v1.run_synthetic_utility_evaluator_v1(
            authority=self.implementation,
            bundle=self.bundle,
            resolver=self.resolver,
            frame=self.frame,
        )
        self.assertEqual(run.evaluator_implementation_identity, R2_IMPLEMENTATION_IDENTITY)
        self.assertEqual(
            run.rule_prediction_artifact.evaluator_implementation_identity,
            R2_IMPLEMENTATION_IDENTITY,
        )
        self.assertNotIn(
            run.rule_prediction_artifact.evaluator_implementation_identity,
            {ORIGINAL_IMPLEMENTATION_IDENTITY, R1_IMPLEMENTATION_IDENTITY},
        )
        self.assertEqual(
            (
                run.source_event_count,
                run.isolated_source_event_count,
                run.relation_opportunity_count,
                run.rule_evaluated_count,
                run.authorized_abstain_count,
                run.error_count,
            ),
            (1, 1, 4, 4, 0, 0),
        )
        self.assertEqual(
            tuple(item.final_state for item in run.rule_prediction_artifact.predictions),
            ("evaluated_anomaly",) * 4,
        )
        self.assertEqual(
            tuple(item.decision_physical_row_index for item in run.rule_prediction_artifact.predictions),
            (112, 162, 112, 162),
        )


if __name__ == "__main__":
    unittest.main()
