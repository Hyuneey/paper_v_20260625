"""Independent R2 authority, provenance, and custody audit.

Primary oracle
--------------
This suite fixes its expected authority values and identity payload directly
from the lower frozen protocol contract.  Production factories are audit
targets, never expected-answer generators.  Existing evaluator tests and
reports are not an oracle for this file.

Frozen independent attack classes
---------------------------------
01 independent R2 implementation-identity replay
02 exact lower authority-bundle binding
03 authority-bundle direct reconstruction
04 authority-bundle deepcopy
05 authority-bundle no-op replace
06 authority-bundle pickle round trip
07 authority-bundle semantic mutation with derived hash
08 authority-bundle stale/mismatched issuance metadata
09 authority-bundle weakref cleanup
10 implementation-authority direct reconstruction
11 implementation-authority deepcopy
12 implementation-authority no-op replace
13 implementation-authority pickle round trip
14 implementation-authority semantic mutation with self-rehash
15 original bare implementation identity
16 R1 bare implementation identity
17 R2 bare implementation identity
18 random/malformed/missing bare implementation identities
19 implementation authority bound to a different issued bundle
20 implementation authority paired with a reconstructed bundle
21 implementation-authority stale/mismatched issuance metadata
22 implementation-authority weakref cleanup
23 RulePredictionArtifact current R2 issuance provenance
24 RulePredictionArtifact original/R1/random identity substitution
25 RulePredictionArtifact reconstruction/deepcopy/no-op replace
26 RulePredictionArtifact semantic mutation with self-rehash
27 RulePredictionArtifact stale/mismatched issuance metadata
28 RulePredictionArtifact weakref cleanup

Items 01--02 are positive oracle/binding cases.  Items 03--28 are distinct
adversarial semantic classes; raw cases may exceed that count without changing
the independent class count.
"""

from __future__ import annotations

import copy
from dataclasses import fields, replace
import gc
import hashlib
import json
import pickle
import unittest
import weakref
from pathlib import Path

import paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 as authority_v1
import paperworks.v6.task039e3_r2r_utility_evaluator_metrics_v1 as metrics_v1
from paperworks.v6 import task039e3_r2r_utility_protocol_v4 as protocol_v4
from paperworks.v6 import task039e3_r2r_utility_source_census_supplement_v1 as supplement_v1
from paperworks.v6.task039e3_r2r_utility_evaluator_census_v1 import (
    enumerate_full_census_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_input_v1 import (
    build_synthetic_feature_frame_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_rule_engine_v1 import execute_rule_v1
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import (
    UtilityEvaluatorV1Error,
)


EXPECTED_EVALUATOR_VERSION = "TASK039E3_R2R_UTILITY_EVALUATOR_V1"
EXPECTED_CONTROL_REVISION = "R2"
EXPECTED_BUNDLE_HASH = "0510da125dd8a799c988927ba49ecb784cad5ea12b05b41e31406effe23051c9"
EXPECTED_V4_AUTHORITY = "1a6200adce791ddd9be8d87b566d47b65e78c1735829d0f91f4ea22127ad1343"
EXPECTED_COMMON_PORTFOLIO = "COMMON-42"
EXPECTED_SYNTHETIC_MODE = "SYNTHETIC_CONTRACT_ONLY"
EXPECTED_SYNTHETIC_AUTHORITY = "b8de8df6b81796e54c635f834f00e86141da557bc9dc6d4834f2b6988da2f56a"
EXPECTED_ORIGINAL_IDENTITY = "332e367cdc0da21b281c5de43f6a735d7dc68bc87efafe90976d89d7f9dc3330"
EXPECTED_R1_IDENTITY = "64a6e7f0d210dc074bc85b0f389e61b45aaa512091532cf8f4d275ccaa35746a"
EXPECTED_R2_IDENTITY = "e7a61070c0be96e305f6706b90308c9976bc8d521c8b97adea93836c3fd28cef"
EXPECTED_MAIN_DESCRIPTOR = "665af1d58d672dfe8109c01e5dcb4e8f19aa2303a8f6100bfd20b3272c3bd928"
EXPECTED_MAIN_REFERENCE_SET = "d14cf57a33a4e7018cbd2342f1a5fb9fc78dfd9d86f912512a903740316c73ae"
EXPECTED_SUPPLEMENT_DESCRIPTOR = "d45af926511c669ec04dd13c36823d454b67ccaa98ae0a7be2919b02652bd927"
EXPECTED_SUPPLEMENT_REFERENCE_SET = "5139cae6e454318f0ca4317f3f5eaa5f775bd4f75261c4110ea610815929b580"
EXPECTED_COMBINED_CENSUS = "cb53d0e4533ebadb61edbdc72b549fe47b46c8dcc4621841aac93a007660ced9"
EXPECTED_SOURCE_EVENT_POLICY = "3fb20068feff44632be3e4e6917183d52fea5616feec68ede5e9b62f95ecb390"
EXPECTED_ISOLATION_POLICY = "f62075523632a7573d28e95ca7f0402d87e62977f4a2f14f4eaf2b9a58f0e280"
EXPECTED_UTILITY_EVENT_POLICY = "6e4a4467953c5c9bf973a0a8a18950669dc902310407b7b354128ad91febb2f4"
EXPECTED_METRIC_POLICY = "4c7b6cfdb6b3889e56e7151be60b92a7e6f46ce0135de0ed65ebf3207a7b0d6a"
EXPECTED_PRODUCTION_MODULES = (
    "task039e3_r2r_utility_evaluator_types_v1.py",
    "task039e3_r2r_utility_evaluator_authority_v1.py",
    "task039e3_r2r_utility_evaluator_input_v1.py",
    "task039e3_r2r_utility_evaluator_census_v1.py",
    "task039e3_r2r_utility_evaluator_rule_engine_v1.py",
    "task039e3_r2r_utility_evaluator_metrics_v1.py",
    "task039e3_r2r_utility_evaluator_v1.py",
)

INDEPENDENT_ORACLE_CASES = 2
UNIQUE_SEMANTIC_ATTACK_CLASSES = 26
RAW_ADVERSARIAL_CASES = 47

_PUBLIC_LOWER_INPUTS = {
    "executable_equivalence": "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json",
    "evidence_manifest": "docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json",
    "dataset_manifest": "docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json",
    "csv_structure_report": "docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json",
    "c0_config": "configs/v6/task039c0_candidate_discovery_protocol.json",
    "br2_config": "configs/v6/task039br2_hai_continuous_step_feasibility.json",
    "materialized_audit_receipt": "docs/task_reports/TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZED_RECEIPT.json",
}


def _independent_hash(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _independent_r2_payload() -> dict[str, object]:
    return {
        "evaluator_version": EXPECTED_EVALUATOR_VERSION,
        "control_revision": EXPECTED_CONTROL_REVISION,
        "evaluator_authority_bundle_hash": EXPECTED_BUNDLE_HASH,
        "v4_authority_hash": EXPECTED_V4_AUTHORITY,
        "utility_portfolio": EXPECTED_COMMON_PORTFOLIO,
        "execution_mode": EXPECTED_SYNTHETIC_MODE,
        "synthetic_authority_identity": EXPECTED_SYNTHETIC_AUTHORITY,
        "production_modules": list(EXPECTED_PRODUCTION_MODULES),
        "real_utility_execution_authorized": False,
    }


def _json_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return {
            field.name: _json_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_json_value(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_value(item) for key, item in value.items()}
    return value


def _artifact_hash(value: metrics_v1.RulePredictionArtifactV1) -> str:
    payload = {
        field.name: _json_value(getattr(value, field.name))
        for field in fields(value)
        if field.name != "artifact_hash"
    }
    return _independent_hash(payload)


def _reconstruct(value: object) -> object:
    return type(value)(**{field.name: getattr(value, field.name) for field in fields(value)})


def _load_lower_v4_authority() -> protocol_v4.UtilityProtocolV4CanonicalAuthority:
    root = Path(__file__).resolve().parents[1]
    documents = {
        name: json.loads((root / relative).read_text(encoding="utf-8"))
        for name, relative in _PUBLIC_LOWER_INPUTS.items()
    }
    result = protocol_v4.build_utility_protocol_v4_canonical_authority(**documents)
    if result.authority_hash != EXPECTED_V4_AUTHORITY:
        raise AssertionError("lower public inputs did not replay frozen V4 R1")
    return result


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


class UtilityEvaluatorV1R2IndependentAuthorityAudit(unittest.TestCase):
    """Authority oracle and adversarial process-local custody checks."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.v4_authority = _load_lower_v4_authority()
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
                (2.0 if rule.source_direction == "step_up" else -2.0)
                if feature == rule.source and physical_index >= 101
                else 0.0
                for feature in cls.v4_authority.feature_schema.union_features
            )
            for physical_index in range(80, 180)
        )
        cls.frame = build_synthetic_feature_frame_v1(
            cls.bundle,
            source_file_identity="synthetic-authority-audit.csv",
            start_physical_row_index=80,
            rows=rows,
        )
        cls.census = enumerate_full_census_v1(cls.frame, cls.bundle, cls.resolver)
        cls.predictions = tuple(
            execute_rule_v1(
                envelope, cls.census, cls.frame, cls.bundle, cls.resolver
            )
            for envelope in cls.census.relation_opportunities
        )
        cls.artifact = cls._build_artifact_for_class()

    @classmethod
    def _build_artifact_for_class(cls) -> metrics_v1.RulePredictionArtifactV1:
        return metrics_v1.build_rule_prediction_artifact_v1(
            evaluator_implementation_authority=cls.implementation,
            bundle=cls.bundle,
            frame=cls.frame,
            census=cls.census,
            resolver=cls.resolver,
            predictions=cls.predictions,
        )

    def assertBundleRejected(self, candidate: object) -> None:  # noqa: N802
        with self.assertRaises(UtilityEvaluatorV1Error):
            authority_v1.validate_evaluator_authority_bundle_v1(candidate)  # type: ignore[arg-type]

    def assertImplementationRejected(
        self, candidate: object, bundle: object | None = None
    ) -> None:  # noqa: N802
        with self.assertRaises(UtilityEvaluatorV1Error):
            authority_v1.validate_evaluator_implementation_authority_v1(  # type: ignore[arg-type]
                candidate,
                self.bundle if bundle is None else bundle,
            )

    def assertArtifactRejected(self, candidate: object) -> None:  # noqa: N802
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics_v1.validate_rule_prediction_artifact_v1(candidate)  # type: ignore[arg-type]

    def assertArtifactBuildRejected(self, **authority_kwargs: object) -> None:  # noqa: N802
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics_v1.build_rule_prediction_artifact_v1(
                **authority_kwargs,
                bundle=self.bundle,
                frame=self.frame,
                census=self.census,
                resolver=self.resolver,
                predictions=self.predictions,
            )

    def test_01_independent_r2_identity_replay(self) -> None:
        self.assertEqual(_independent_hash(_independent_r2_payload()), EXPECTED_R2_IDENTITY)
        self.assertNotEqual(EXPECTED_R2_IDENTITY, EXPECTED_ORIGINAL_IDENTITY)
        self.assertNotEqual(EXPECTED_R2_IDENTITY, EXPECTED_R1_IDENTITY)

    def test_02_lower_bundle_and_current_implementation_binding(self) -> None:
        bundle = self.bundle
        self.assertEqual(bundle.bundle_hash, EXPECTED_BUNDLE_HASH)
        self.assertEqual(bundle.v4_authority_hash, EXPECTED_V4_AUTHORITY)
        self.assertEqual(bundle.common_portfolio, EXPECTED_COMMON_PORTFOLIO)
        self.assertEqual(bundle.common_relation_count, 42)
        self.assertIs(bundle.t2_utility_authorized, False)
        self.assertEqual(bundle.main_descriptor_hash, EXPECTED_MAIN_DESCRIPTOR)
        self.assertEqual(bundle.main_reference_set_hash, EXPECTED_MAIN_REFERENCE_SET)
        self.assertEqual(bundle.supplement_descriptor_hash, EXPECTED_SUPPLEMENT_DESCRIPTOR)
        self.assertEqual(bundle.supplement_reference_set_hash, EXPECTED_SUPPLEMENT_REFERENCE_SET)
        self.assertEqual(bundle.combined_source_census_contract_hash, EXPECTED_COMBINED_CENSUS)
        self.assertEqual(bundle.source_census_event_policy_hash, EXPECTED_SOURCE_EVENT_POLICY)
        self.assertEqual(bundle.cross_source_isolation_policy_hash, EXPECTED_ISOLATION_POLICY)
        self.assertEqual(bundle.utility_event_aggregation_policy_hash, EXPECTED_UTILITY_EVENT_POLICY)
        self.assertEqual(bundle.metric_policy_hash, EXPECTED_METRIC_POLICY)
        self.assertEqual(
            (len(bundle.main_sources), len(bundle.supplement_sources), len(bundle.evaluator_source_census)),
            (9, 3, 12),
        )
        self.assertEqual(
            authority_v1.validate_evaluator_authority_bundle_v1(bundle),
            EXPECTED_BUNDLE_HASH,
        )
        self.assertEqual(self.implementation.control_revision, EXPECTED_CONTROL_REVISION)
        self.assertEqual(self.implementation.implementation_identity, EXPECTED_R2_IDENTITY)
        self.assertEqual(
            authority_v1.validate_evaluator_implementation_authority_v1(
                self.implementation, bundle
            ),
            EXPECTED_R2_IDENTITY,
        )

    def test_03_bundle_reconstruction_copy_replace_and_pickle_reject(self) -> None:
        candidates = (
            _reconstruct(self.bundle),
            copy.deepcopy(self.bundle),
            replace(self.bundle),
            pickle.loads(pickle.dumps(self.bundle)),
        )
        for candidate in candidates:
            with self.subTest(mechanism=type(candidate).__name__):
                self.assertBundleRejected(candidate)

    def test_04_bundle_issuance_metadata_and_semantic_replay_both_required(self) -> None:
        reconstructed = _reconstruct(self.bundle)
        key = id(reconstructed)
        authority_v1._ISSUED_EVALUATOR_AUTHORITY_BUNDLES[key] = (
            weakref.ref(self.bundle),
            reconstructed.bundle_hash,
        )
        try:
            self.assertBundleRejected(reconstructed)
        finally:
            authority_v1._ISSUED_EVALUATOR_AUTHORITY_BUNDLES.pop(key, None)

        issued_key = id(self.bundle)
        saved = authority_v1._ISSUED_EVALUATOR_AUTHORITY_BUNDLES[issued_key]
        authority_v1._ISSUED_EVALUATOR_AUTHORITY_BUNDLES[issued_key] = (
            saved[0],
            "f" * 64,
        )
        try:
            self.assertBundleRejected(self.bundle)
        finally:
            authority_v1._ISSUED_EVALUATOR_AUTHORITY_BUNDLES[issued_key] = saved

        mutated = replace(self.bundle, metric_policy_hash="e" * 64)
        mutated_key = id(mutated)
        authority_v1._ISSUED_EVALUATOR_AUTHORITY_BUNDLES[mutated_key] = (
            weakref.ref(mutated),
            mutated.bundle_hash,
        )
        try:
            self.assertBundleRejected(mutated)
        finally:
            authority_v1._ISSUED_EVALUATOR_AUTHORITY_BUNDLES.pop(mutated_key, None)

    def test_05_bundle_weakref_cleanup(self) -> None:
        issued = authority_v1.build_evaluator_authority_bundle_v1(self.v4_authority)
        key = id(issued)
        issued_ref = weakref.ref(issued)
        self.assertIn(key, authority_v1._ISSUED_EVALUATOR_AUTHORITY_BUNDLES)
        del issued
        gc.collect()
        self.assertIsNone(issued_ref())
        self.assertNotIn(key, authority_v1._ISSUED_EVALUATOR_AUTHORITY_BUNDLES)

    def test_06_implementation_reconstruction_copy_replace_pickle_and_rehash_reject(self) -> None:
        wrong_revision_payload = {
            **_independent_r2_payload(),
            "control_revision": "R9",
        }
        wrong_revision = replace(
            self.implementation,
            control_revision="R9",
            implementation_identity=_independent_hash(wrong_revision_payload),
        )
        candidates = (
            _reconstruct(self.implementation),
            copy.deepcopy(self.implementation),
            replace(self.implementation),
            pickle.loads(pickle.dumps(self.implementation)),
            wrong_revision,
        )
        for candidate in candidates:
            with self.subTest(revision=getattr(candidate, "control_revision", None)):
                self.assertImplementationRejected(candidate)

    def test_07_implementation_cross_bundle_and_reconstructed_bundle_reject(self) -> None:
        self.assertIsNot(self.bundle, self.other_bundle)
        self.assertEqual(self.bundle, self.other_bundle)
        self.assertImplementationRejected(self.implementation, self.other_bundle)
        self.assertImplementationRejected(self.implementation, _reconstruct(self.bundle))

    def test_08_implementation_issuance_metadata_and_semantics_both_required(self) -> None:
        key = id(self.implementation)
        saved = authority_v1._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES[key]
        variants = (
            (saved[0], "f" * 64, saved[2], saved[3]),
            (saved[0], saved[1], "e" * 64, saved[3]),
            (saved[0], saved[1], saved[2], weakref.ref(self.other_bundle)),
        )
        try:
            for variant in variants:
                authority_v1._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES[key] = variant
                self.assertImplementationRejected(self.implementation)
        finally:
            authority_v1._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES[key] = saved

        mutated_payload = {**_independent_r2_payload(), "control_revision": "RX"}
        mutated = replace(
            self.implementation,
            control_revision="RX",
            implementation_identity=_independent_hash(mutated_payload),
        )
        mutated_key = id(mutated)
        authority_v1._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES[mutated_key] = (
            weakref.ref(mutated),
            mutated.implementation_identity,
            mutated.evaluator_authority_bundle_hash,
            weakref.ref(self.bundle),
        )
        try:
            self.assertImplementationRejected(mutated)
        finally:
            authority_v1._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES.pop(
                mutated_key, None
            )

    def test_09_implementation_weakref_cleanup_for_authority_and_bundle(self) -> None:
        bundle = authority_v1.build_evaluator_authority_bundle_v1(self.v4_authority)
        implementation = authority_v1.build_evaluator_implementation_authority_v1(bundle)
        key = id(implementation)
        implementation_ref = weakref.ref(implementation)
        del implementation
        gc.collect()
        self.assertIsNone(implementation_ref())
        self.assertNotIn(key, authority_v1._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES)

        bundle = authority_v1.build_evaluator_authority_bundle_v1(self.v4_authority)
        implementation = authority_v1.build_evaluator_implementation_authority_v1(bundle)
        key = id(implementation)
        bundle_ref = weakref.ref(bundle)
        del bundle
        gc.collect()
        self.assertIsNone(bundle_ref())
        self.assertNotIn(key, authority_v1._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES)

    def test_10_bare_identity_and_nonissued_authority_paths_reject(self) -> None:
        for identity in (
            EXPECTED_ORIGINAL_IDENTITY,
            EXPECTED_R1_IDENTITY,
            EXPECTED_R2_IDENTITY,
            "f" * 64,
            "malformed",
            None,
        ):
            with self.subTest(identity=identity):
                self.assertArtifactBuildRejected(
                    evaluator_implementation_identity=identity
                )
        self.assertArtifactBuildRejected()
        for candidate in (
            _reconstruct(self.implementation),
            copy.deepcopy(self.implementation),
            replace(self.implementation),
            pickle.loads(pickle.dumps(self.implementation)),
        ):
            self.assertArtifactBuildRejected(
                evaluator_implementation_authority=candidate
            )

    def test_11_rule_prediction_factory_binds_current_r2_provenance(self) -> None:
        self.assertEqual(
            metrics_v1.validate_rule_prediction_artifact_v1(self.artifact),
            self.artifact.artifact_hash,
        )
        self.assertEqual(
            self.artifact.evaluator_implementation_identity, EXPECTED_R2_IDENTITY
        )
        self.assertEqual(
            self.artifact.evaluator_authority_bundle_hash, EXPECTED_BUNDLE_HASH
        )
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics_v1.build_rule_prediction_artifact_v1(
                evaluator_implementation_authority=self.implementation,
                bundle=self.other_bundle,
                frame=self.frame,
                census=self.census,
                resolver=self.resolver,
                predictions=self.predictions,
            )

    def test_12_rule_prediction_reconstruction_copy_replace_and_pickle_reject(self) -> None:
        for candidate in (
            _reconstruct(self.artifact),
            copy.deepcopy(self.artifact),
            replace(self.artifact),
            pickle.loads(pickle.dumps(self.artifact)),
        ):
            self.assertArtifactRejected(candidate)

    def test_13_rule_prediction_identity_self_rehash_and_forged_issuance_reject(self) -> None:
        for identity in (
            EXPECTED_ORIGINAL_IDENTITY,
            EXPECTED_R1_IDENTITY,
            "f" * 64,
            "",
        ):
            candidate = replace(
                self.artifact,
                evaluator_implementation_identity=identity,
                artifact_hash="",
            )
            candidate = replace(candidate, artifact_hash=_artifact_hash(candidate))
            self.assertArtifactRejected(candidate)

            key = id(candidate)
            metrics_v1._ISSUED_RULE_ARTIFACTS[key] = (
                weakref.ref(candidate),
                candidate.artifact_hash,
                candidate.evaluator_implementation_identity,
                candidate.evaluator_authority_bundle_hash,
            )
            try:
                self.assertArtifactRejected(candidate)
            finally:
                metrics_v1._ISSUED_RULE_ARTIFACTS.pop(key, None)

    def test_14_rule_prediction_issuance_metadata_removed_and_stale_reject(self) -> None:
        key = id(self.artifact)
        saved = metrics_v1._ISSUED_RULE_ARTIFACTS[key]
        variants = (
            (saved[0], "f" * 64, saved[2], saved[3]),
            (saved[0], saved[1], EXPECTED_R1_IDENTITY, saved[3]),
            (saved[0], saved[1], saved[2], "e" * 64),
        )
        try:
            for variant in variants:
                metrics_v1._ISSUED_RULE_ARTIFACTS[key] = variant
                self.assertArtifactRejected(self.artifact)
            metrics_v1._ISSUED_RULE_ARTIFACTS.pop(key, None)
            self.assertArtifactRejected(self.artifact)
        finally:
            metrics_v1._ISSUED_RULE_ARTIFACTS[key] = saved

        other = self._build_artifact_for_class()
        metrics_v1._ISSUED_RULE_ARTIFACTS[key] = (
            weakref.ref(other),
            self.artifact.artifact_hash,
            EXPECTED_R2_IDENTITY,
            EXPECTED_BUNDLE_HASH,
        )
        try:
            self.assertArtifactRejected(self.artifact)
        finally:
            metrics_v1._ISSUED_RULE_ARTIFACTS[key] = saved

    def test_15_rule_prediction_weakref_cleanup(self) -> None:
        artifact = self._build_artifact_for_class()
        key = id(artifact)
        artifact_ref = weakref.ref(artifact)
        self.assertIn(key, metrics_v1._ISSUED_RULE_ARTIFACTS)
        del artifact
        gc.collect()
        self.assertIsNone(artifact_ref())
        self.assertNotIn(key, metrics_v1._ISSUED_RULE_ARTIFACTS)


if __name__ == "__main__":
    unittest.main()
