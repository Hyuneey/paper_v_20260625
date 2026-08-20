"""Focused R3 synthetic detector-artifact custody remediation tests.

All positive execution is SYNTHETIC_CONTRACT_ONLY.  The suite constructs no
real detector authority and performs no HAI, label, private-registry, provider,
or network access.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import fields, replace
import gc
import unittest
import weakref

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
    SYNTHETIC_CONTRACT_ONLY,
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
R3_IMPLEMENTATION_IDENTITY = (
    "af74bf3bd9ae240f21c57630b4804eabb997021353f15e7c402904b94f783fb5"
)
SYNTHETIC_DETECTOR_AUTHORITY = (
    "99399ef47589871f5ffb37a83d63bc4fa414d79b41435b4bb61c679a243dbd7b"
)
R3_FOCUSED_INVALID_ATTACKS = 35
R3_ACCEPTED_INVALID = 0


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


def _rehash_detector(
    detector: metrics_v1.DetectorPredictionArtifactV1,
    **changes: object,
) -> metrics_v1.DetectorPredictionArtifactV1:
    candidate = replace(detector, **changes, artifact_hash="")
    return replace(
        candidate,
        artifact_hash=stable_hash_v1(
            dataclass_payload_v1(candidate, exclude=("artifact_hash",))
        ),
    )


class UtilityEvaluatorV1R3DetectorCustodyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.v4_authority = build_lower_v4_authority()
        cls.bundle = authority_v1.build_evaluator_authority_bundle_v1(cls.v4_authority)
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
                (2.0 if rule.source_direction == "step_up" else -2.0)
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
        cls.rule_artifact = metrics_v1.build_rule_prediction_artifact_v1(
            evaluator_implementation_authority=cls.implementation,
            bundle=cls.bundle,
            frame=cls.frame,
            census=cls.census,
            resolver=cls.resolver,
            predictions=cls.predictions,
        )

    def _detector(self, **changes: object) -> metrics_v1.DetectorPredictionArtifactV1:
        values: dict[str, object] = {
            "dataset_manifest_identity": self.frame.dataset_manifest_identity,
            "split_identity": self.frame.split_identity,
            "source_file_identity": self.frame.source_file_identity,
            "point_predictions": tuple(False for _ in self.frame.rows),
        }
        values.update(changes)
        return metrics_v1.build_synthetic_detector_prediction_artifact_v1(**values)  # type: ignore[arg-type]

    def test_r3_control_identity_and_value_free_detector_authority_replay(self) -> None:
        expected_detector_authority = stable_hash_v1(
            {
                "artifact_type": "task039e3_r2r_utility_evaluator_v1_synthetic_detector_authority",
                "evaluator_version": authority_v1.EVALUATOR_VERSION,
                "execution_mode": SYNTHETIC_CONTRACT_ONLY,
                "scientific_eligibility": False,
                "real_detector_authority": False,
                "detector_science_executed": False,
            }
        )
        self.assertEqual(authority_v1.UTILITY_EVALUATOR_CONTROL_REVISION, "R3")
        self.assertEqual(
            authority_v1.CURRENT_EVALUATOR_IMPLEMENTATION_IDENTITY,
            R3_IMPLEMENTATION_IDENTITY,
        )
        self.assertNotIn(
            R3_IMPLEMENTATION_IDENTITY,
            {
                ORIGINAL_IMPLEMENTATION_IDENTITY,
                R1_IMPLEMENTATION_IDENTITY,
                R2_IMPLEMENTATION_IDENTITY,
            },
        )
        self.assertEqual(expected_detector_authority, SYNTHETIC_DETECTOR_AUTHORITY)
        self.assertEqual(
            metrics_v1.SYNTHETIC_DETECTOR_AUTHORITY_IDENTITY,
            SYNTHETIC_DETECTOR_AUTHORITY,
        )

    def test_factory_artifact_is_canonical_and_custodied(self) -> None:
        detector = self._detector()
        self.assertEqual(
            metrics_v1.validate_detector_prediction_artifact_v1(detector),
            detector.artifact_hash,
        )
        self.assertEqual(detector.execution_mode, SYNTHETIC_CONTRACT_ONLY)
        self.assertFalse(detector.scientific_eligible)
        self.assertEqual(
            detector.detector_authority_identity, SYNTHETIC_DETECTOR_AUTHORITY
        )

    def test_reconstruction_deepcopy_and_noop_replace_reject(self) -> None:
        detector = self._detector()
        for candidate in (_reconstruct(detector), deepcopy(detector), replace(detector)):
            with self.subTest(kind=type(candidate).__name__), self.assertRaises(
                UtilityEvaluatorV1Error
            ):
                metrics_v1.validate_detector_prediction_artifact_v1(candidate)  # type: ignore[arg-type]

    def test_all_caller_selected_detector_authorities_reject(self) -> None:
        for identity in (
            "a" * 64,
            "not-a-sha",
            SYNTHETIC_DETECTOR_AUTHORITY,
        ):
            with self.subTest(identity=identity), self.assertRaises(UtilityEvaluatorV1Error):
                self._detector(detector_authority_identity=identity)

    def test_issued_field_and_prediction_self_rehash_mutations_reject(self) -> None:
        detector = self._detector()
        mutations: tuple[dict[str, object], ...] = (
            {"detector_authority_identity": "b" * 64},
            {"dataset_manifest_identity": "other-dataset"},
            {"split_identity": "other-split"},
            {"source_file_identity": "other-file"},
            {"point_predictions": (True,) + detector.point_predictions[1:]},
            {"point_predictions": detector.point_predictions + (False,)},
            {"point_predictions": detector.point_predictions[:-1]},
            {"point_predictions": tuple(reversed(detector.point_predictions))},
            {"point_predictions": list(detector.point_predictions)},
            {"point_predictions": (1,) + detector.point_predictions[1:]},
            {"point_predictions": (1.0,) + detector.point_predictions[1:]},
            {"point_predictions": ()},
            {"artifact_type": "wrong"},
            {"execution_mode": "REAL"},
            {"scientific_eligible": True},
            {"artifact_hash": "f" * 64},
        )
        for change in mutations:
            candidate = (
                replace(detector, **change)
                if "artifact_hash" in change
                else _rehash_detector(detector, **change)
            )
            with self.subTest(change=tuple(change)), self.assertRaises(
                UtilityEvaluatorV1Error
            ):
                metrics_v1.validate_detector_prediction_artifact_v1(candidate)

        malformed = _rehash_detector(
            detector, detector_authority_identity="not-a-sha"
        )
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics_v1.validate_detector_prediction_artifact_v1(malformed)

    def test_issuance_removal_and_metadata_substitution_reject(self) -> None:
        detector = self._detector()
        issued_key = id(detector)
        saved = metrics_v1._ISSUED_DETECTOR_ARTIFACTS[issued_key]
        try:
            metadata_mutations = (
                (saved[0], saved[1], "f" * 64, *saved[3:]),
                (*saved[:3], "other-dataset", *saved[4:]),
                (*saved[:4], "other-split", *saved[5:]),
                (*saved[:5], "other-file", saved[6]),
                (*saved[:6], "f" * 64),
            )
            for issuance in metadata_mutations:
                metrics_v1._ISSUED_DETECTOR_ARTIFACTS[issued_key] = issuance
                with self.subTest(issuance=issuance[1:]), self.assertRaises(
                    UtilityEvaluatorV1Error
                ):
                    metrics_v1.validate_detector_prediction_artifact_v1(detector)
            metrics_v1._ISSUED_DETECTOR_ARTIFACTS.pop(issued_key)
            with self.assertRaises(UtilityEvaluatorV1Error):
                metrics_v1.validate_detector_prediction_artifact_v1(detector)
        finally:
            metrics_v1._ISSUED_DETECTOR_ARTIFACTS[issued_key] = saved

    def test_exact_weakref_custody_and_automatic_cleanup(self) -> None:
        detector = self._detector()
        other = self._detector()
        issued_key = id(detector)
        saved = metrics_v1._ISSUED_DETECTOR_ARTIFACTS[issued_key]
        metrics_v1._ISSUED_DETECTOR_ARTIFACTS[issued_key] = (
            weakref.ref(other),
            *saved[1:],
        )
        try:
            with self.assertRaises(UtilityEvaluatorV1Error):
                metrics_v1.validate_detector_prediction_artifact_v1(detector)
        finally:
            metrics_v1._ISSUED_DETECTOR_ARTIFACTS[issued_key] = saved

        cleanup_key = id(detector)
        detector_ref = weakref.ref(detector)
        del detector
        gc.collect()
        self.assertIsNone(detector_ref())
        self.assertNotIn(cleanup_key, metrics_v1._ISSUED_DETECTOR_ARTIFACTS)

    def test_comparison_accepts_only_canonical_detector_custody(self) -> None:
        detector = self._detector()
        comparison = metrics_v1.build_synthetic_rule_detector_comparison_input_v1(
            detector=detector,
            d1_rule_artifact=self.rule_artifact,
            d2_rule_artifact=self.rule_artifact,
        )
        self.assertFalse(comparison.scientific_eligible)
        self.assertFalse(comparison.fusion_authorized)

        forged_prediction = _rehash_detector(
            detector,
            point_predictions=(True,) + detector.point_predictions[1:],
        )
        for candidate in (_reconstruct(detector), forged_prediction):
            with self.subTest(kind=type(candidate).__name__), self.assertRaises(
                UtilityEvaluatorV1Error
            ):
                metrics_v1.build_synthetic_rule_detector_comparison_input_v1(
                    detector=candidate,  # type: ignore[arg-type]
                    d1_rule_artifact=self.rule_artifact,
                    d2_rule_artifact=self.rule_artifact,
                )

        for change in (
            {"dataset_manifest_identity": "other-dataset"},
            {"split_identity": "other-split"},
            {"source_file_identity": "other-file"},
        ):
            other = self._detector(**change)
            with self.subTest(change=tuple(change)), self.assertRaises(
                UtilityEvaluatorV1Error
            ):
                metrics_v1.build_synthetic_rule_detector_comparison_input_v1(
                    detector=other,
                    d1_rule_artifact=self.rule_artifact,
                    d2_rule_artifact=self.rule_artifact,
                )

    def test_r3_rule_prediction_provenance_and_facade_outputs(self) -> None:
        self.assertEqual(
            self.rule_artifact.evaluator_implementation_identity,
            R3_IMPLEMENTATION_IDENTITY,
        )
        run = evaluator_v1.run_synthetic_utility_evaluator_v1(
            authority=self.implementation,
            bundle=self.bundle,
            resolver=self.resolver,
            frame=self.frame,
        )
        self.assertEqual(run.evaluator_implementation_identity, R3_IMPLEMENTATION_IDENTITY)
        self.assertEqual(
            run.rule_prediction_artifact.evaluator_implementation_identity,
            R3_IMPLEMENTATION_IDENTITY,
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


if __name__ == "__main__":
    unittest.main()
