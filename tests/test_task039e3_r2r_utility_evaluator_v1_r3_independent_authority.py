"""Independent R3 authority, provenance, and factory-custody audit.

The expected identities in this file are reconstructed from frozen lower
public authorities and independently serialized payloads.  Production
factories are audit targets, not expected-answer generators.  All positive
execution remains ``SYNTHETIC_CONTRACT_ONLY``; this suite performs no private
registry, HAI, label, provider, credential, or network access.

Coverage freezes 65 unique semantic classes and 104 explicit adversarial
cases.  The raw count is the number of separately exercised invalid variants,
not the number of unittest methods or repeated aliases.
"""

from __future__ import annotations

import copy
from dataclasses import fields, replace
import gc
import hashlib
import json
import pickle
from pathlib import Path
import unittest
import weakref

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
from paperworks.v6.task039e3_r2r_utility_evaluator_rule_engine_v1 import (
    execute_rule_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import (
    UtilityEvaluatorV1Error,
)


EXPECTED_EVALUATOR_VERSION = "TASK039E3_R2R_UTILITY_EVALUATOR_V1"
EXPECTED_CONTROL_REVISION = "R3"
EXPECTED_BUNDLE_HASH = "0510da125dd8a799c988927ba49ecb784cad5ea12b05b41e31406effe23051c9"
EXPECTED_V4_AUTHORITY = "1a6200adce791ddd9be8d87b566d47b65e78c1735829d0f91f4ea22127ad1343"
EXPECTED_COMMON_PORTFOLIO = "COMMON-42"
EXPECTED_SYNTHETIC_MODE = "SYNTHETIC_CONTRACT_ONLY"
EXPECTED_SYNTHETIC_AUTHORITY = "b8de8df6b81796e54c635f834f00e86141da557bc9dc6d4834f2b6988da2f56a"
EXPECTED_ORIGINAL_IDENTITY = "332e367cdc0da21b281c5de43f6a735d7dc68bc87efafe90976d89d7f9dc3330"
EXPECTED_R1_IDENTITY = "64a6e7f0d210dc074bc85b0f389e61b45aaa512091532cf8f4d275ccaa35746a"
EXPECTED_R2_IDENTITY = "e7a61070c0be96e305f6706b90308c9976bc8d521c8b97adea93836c3fd28cef"
EXPECTED_R3_IDENTITY = "af74bf3bd9ae240f21c57630b4804eabb997021353f15e7c402904b94f783fb5"
EXPECTED_DETECTOR_AUTHORITY = "99399ef47589871f5ffb37a83d63bc4fa414d79b41435b4bb61c679a243dbd7b"

EXPECTED_MAIN_DESCRIPTOR = "665af1d58d672dfe8109c01e5dcb4e8f19aa2303a8f6100bfd20b3272c3bd928"
EXPECTED_MAIN_REFERENCE_SET = "d14cf57a33a4e7018cbd2342f1a5fb9fc78dfd9d86f912512a903740316c73ae"
EXPECTED_MAIN_PRIVATE_REGISTRY = "9b9ca67d858cb88ce934d1d8a6e0b563b7dc9bb01437d2835b68e2d1e61483d0"
EXPECTED_MAIN_AUDIT_RECEIPT = "1f319fd7283040a4e866df3ac7d679e896142162084209bf00962947256c2bf1"
EXPECTED_MAIN_LOCATOR = "b5588c04d08d88d4ee2a2d319708e62d10bc04330baeb7591876f076270e4ac4"
EXPECTED_SUPPLEMENT_DESCRIPTOR = "d45af926511c669ec04dd13c36823d454b67ccaa98ae0a7be2919b02652bd927"
EXPECTED_SUPPLEMENT_REFERENCE_SET = "5139cae6e454318f0ca4317f3f5eaa5f775bd4f75261c4110ea610815929b580"
EXPECTED_SUPPLEMENT_PRIVATE_REGISTRY = "12ec7f50a953e097cd7cbe3ac93c7cabfb669130612d7f30ab3b19df85289aaf"
EXPECTED_SUPPLEMENT_LOCATOR = "8c11872dca6a0c8b2544c2988dd57c969ddc036f51b04578d936fdc3a60757ac"
EXPECTED_SUPPLEMENT_PUBLIC_RECEIPT = "56e455d69823e87b7fa217c6ee7d8d86f5d08b7fc5aaf9865ff1241c6798d16e"
EXPECTED_SUPPLEMENT_FINAL_AUDIT = "ad61a4c435e7904b5a80feca40e7e629dc3522e8dc4f68c99b2b9ab9b45d142b"
EXPECTED_SUPPLEMENT_FINAL_BUNDLE = "d379cfe8e3c452100f2993c2e16f21e39b54393bbbe178ebfda0d1ee91a10620"
EXPECTED_SUPPLEMENT_FINAL_RECEIPT = "c4397b83155bff74c0997c8e4837b0c90198e6df6dd0bea748d62086eef7ba98"
EXPECTED_COMBINED_CENSUS = "cb53d0e4533ebadb61edbdc72b549fe47b46c8dcc4621841aac93a007660ced9"
EXPECTED_SOURCE_EVENT_POLICY = "3fb20068feff44632be3e4e6917183d52fea5616feec68ede5e9b62f95ecb390"
EXPECTED_ISOLATION_POLICY = "f62075523632a7573d28e95ca7f0402d87e62977f4a2f14f4eaf2b9a58f0e280"
EXPECTED_UTILITY_EVENT_POLICY = "6e4a4467953c5c9bf973a0a8a18950669dc902310407b7b354128ad91febb2f4"
EXPECTED_METRIC_POLICY = "4c7b6cfdb6b3889e56e7151be60b92a7e6f46ce0135de0ed65ebf3207a7b0d6a"
EXPECTED_CANONICAL_SCHEMA = "62fd76bd541437694aff274db865670f24eecbabf3c736f32893bd97081564b8"
EXPECTED_RUNTIME_SCHEMA = "e7a0c46d28491b9d03a333a0ad1e87d686a982bafba072861913e05fb6c50b58"

EXPECTED_PRODUCTION_MODULES = (
    "task039e3_r2r_utility_evaluator_types_v1.py",
    "task039e3_r2r_utility_evaluator_authority_v1.py",
    "task039e3_r2r_utility_evaluator_input_v1.py",
    "task039e3_r2r_utility_evaluator_census_v1.py",
    "task039e3_r2r_utility_evaluator_rule_engine_v1.py",
    "task039e3_r2r_utility_evaluator_metrics_v1.py",
    "task039e3_r2r_utility_evaluator_v1.py",
)

INDEPENDENT_ORACLE_CASES = 4
UNIQUE_SEMANTIC_ATTACK_CLASSES = 65
RAW_ADVERSARIAL_CASES = 104
ACCEPTED_INVALID_CASES = 0
REAL_PRIVATE_ACCESS_COUNT = 0

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


def _json_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return {field.name: _json_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [_json_value(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_value(item) for key, item in value.items()}
    return value


def _reconstruct(value: object) -> object:
    return type(value)(**{field.name: getattr(value, field.name) for field in fields(value)})


def _artifact_hash(value: object) -> str:
    return _independent_hash(
        {
            field.name: _json_value(getattr(value, field.name))
            for field in fields(value)
            if field.name != "artifact_hash"
        }
    )


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


def _independent_bundle_payload(
    v4_authority: protocol_v4.UtilityProtocolV4CanonicalAuthority,
) -> dict[str, object]:
    main_sources = supplement_v1.MAIN_SOURCES
    supplement_sources = supplement_v1.SUPPLEMENT_SOURCES
    all_sources = tuple(sorted(main_sources + supplement_sources))
    return {
        "artifact_type": "task039e3_r2r_utility_evaluator_authority_bundle_v1",
        "evaluator_version": EXPECTED_EVALUATOR_VERSION,
        "v4_authority_hash": EXPECTED_V4_AUTHORITY,
        "v4_focused_audit_hash": "8c66590f222ad656add781745a361e483ba0ecd3c42bccbfa11f08cfaa6550ae",
        "v4_focused_receipt_hash": "09cf661a21cb4bd0d5ad356c2cf725264d76aeaffc7963858425e88267717509",
        "common_portfolio": EXPECTED_COMMON_PORTFOLIO,
        "common_relation_count": 42,
        "t2_utility_authorized": False,
        "main": {
            "descriptor_hash": EXPECTED_MAIN_DESCRIPTOR,
            "reference_set_hash": EXPECTED_MAIN_REFERENCE_SET,
            "reference_count": 420,
            "private_registry_hash": EXPECTED_MAIN_PRIVATE_REGISTRY,
            "audit_receipt_hash": EXPECTED_MAIN_AUDIT_RECEIPT,
            "locator_hash": EXPECTED_MAIN_LOCATOR,
            "source_count": 9,
        },
        "supplement": {
            "purpose": "CROSS_SOURCE_ISOLATION_EVENT_CENSUS_ONLY",
            "descriptor_hash": EXPECTED_SUPPLEMENT_DESCRIPTOR,
            "reference_set_hash": EXPECTED_SUPPLEMENT_REFERENCE_SET,
            "reference_count": 6,
            "private_registry_hash": EXPECTED_SUPPLEMENT_PRIVATE_REGISTRY,
            "locator_hash": EXPECTED_SUPPLEMENT_LOCATOR,
            "public_receipt_hash": EXPECTED_SUPPLEMENT_PUBLIC_RECEIPT,
            "final_audit_hash": EXPECTED_SUPPLEMENT_FINAL_AUDIT,
            "final_bundle_hash": EXPECTED_SUPPLEMENT_FINAL_BUNDLE,
            "final_receipt_hash": EXPECTED_SUPPLEMENT_FINAL_RECEIPT,
            "source_count": 3,
        },
        "combined_source_census_contract_hash": EXPECTED_COMBINED_CENSUS,
        "source_census_event_policy_hash": EXPECTED_SOURCE_EVENT_POLICY,
        "cross_source_isolation_policy_hash": EXPECTED_ISOLATION_POLICY,
        "utility_event_aggregation_policy_hash": EXPECTED_UTILITY_EVENT_POLICY,
        "metric_policy_hash": EXPECTED_METRIC_POLICY,
        "canonical_feature_schema_hash": EXPECTED_CANONICAL_SCHEMA,
        "runtime_feature_schema_hash": EXPECTED_RUNTIME_SCHEMA,
        "dataset_manifest_identity": protocol_v4.DATASET_MANIFEST_ID,
        "split_identities": [protocol_v4.INNER_SPLIT_ID, protocol_v4.OUTER_SPLIT_ID],
        "purge_policy_hash": protocol_v4.PURGE_POLICY_HASH,
        "main_sources": list(main_sources),
        "supplement_sources": list(supplement_sources),
        "evaluator_source_census": list(all_sources),
    }


def _independent_r3_payload() -> dict[str, object]:
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


def _independent_detector_authority_payload() -> dict[str, object]:
    return {
        "artifact_type": "task039e3_r2r_utility_evaluator_v1_synthetic_detector_authority",
        "evaluator_version": EXPECTED_EVALUATOR_VERSION,
        "execution_mode": EXPECTED_SYNTHETIC_MODE,
        "scientific_eligibility": False,
        "real_detector_authority": False,
        "detector_science_executed": False,
    }


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


class UtilityEvaluatorV1R3IndependentAuthorityAudit(unittest.TestCase):
    """Independent lower replay plus adversarial process-local custody tests."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.v4_authority = _load_lower_v4_authority()
        cls.bundle = authority_v1.build_evaluator_authority_bundle_v1(cls.v4_authority)
        cls.other_bundle = authority_v1.build_evaluator_authority_bundle_v1(cls.v4_authority)
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
                "CROSS_SOURCE_ISOLATION_EVENT_CENSUS_ONLY",
                source,
                None,
                role,
                supplement_v1.supplement_reference_identity_v1(source, role),
                _numeric_value(role),
            )
            for source in supplement_v1.SUPPLEMENT_SOURCES
            for role in supplement_v1.SUPPLEMENT_ROLES
        )
        cls.resolver = authority_v1.build_synthetic_numeric_resolver_v1(
            cls.bundle, main_records, supplement_records
        )

        relation = next(
            item
            for item in cls.v4_authority.rule_descriptors
            if item.selected_horizon_seconds == 10
        )
        rows = tuple(
            tuple(
                (2.0 if relation.source_direction == "step_up" else -2.0)
                if feature == relation.source and physical_index >= 101
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
        cls.rule_artifact = cls._new_rule_artifact()

    @classmethod
    def _new_rule_artifact(cls) -> metrics_v1.RulePredictionArtifactV1:
        return metrics_v1.build_rule_prediction_artifact_v1(
            evaluator_implementation_authority=cls.implementation,
            bundle=cls.bundle,
            frame=cls.frame,
            census=cls.census,
            resolver=cls.resolver,
            predictions=cls.predictions,
        )

    def _new_detector(self, **changes: object) -> metrics_v1.DetectorPredictionArtifactV1:
        values: dict[str, object] = {
            "dataset_manifest_identity": self.frame.dataset_manifest_identity,
            "split_identity": self.frame.split_identity,
            "source_file_identity": self.frame.source_file_identity,
            "point_predictions": tuple(False for _ in self.frame.rows),
        }
        values.update(changes)
        return metrics_v1.build_synthetic_detector_prediction_artifact_v1(**values)  # type: ignore[arg-type]

    def assertBundleRejected(self, candidate: object) -> None:  # noqa: N802
        with self.assertRaises(UtilityEvaluatorV1Error):
            authority_v1.validate_evaluator_authority_bundle_v1(candidate)  # type: ignore[arg-type]

    def assertImplementationRejected(
        self, candidate: object, bundle: object | None = None
    ) -> None:  # noqa: N802
        with self.assertRaises(UtilityEvaluatorV1Error):
            authority_v1.validate_evaluator_implementation_authority_v1(  # type: ignore[arg-type]
                candidate, self.bundle if bundle is None else bundle
            )

    def assertRuleRejected(self, candidate: object) -> None:  # noqa: N802
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics_v1.validate_rule_prediction_artifact_v1(candidate)  # type: ignore[arg-type]

    def assertDetectorRejected(self, candidate: object) -> None:  # noqa: N802
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics_v1.validate_detector_prediction_artifact_v1(candidate)  # type: ignore[arg-type]

    def test_01_independent_lower_bundle_identity_replay(self) -> None:
        payload = _independent_bundle_payload(self.v4_authority)
        self.assertEqual(_independent_hash(payload), EXPECTED_BUNDLE_HASH)
        self.assertEqual(self.bundle.bundle_hash, EXPECTED_BUNDLE_HASH)
        self.assertEqual(self.bundle.v4_authority_hash, EXPECTED_V4_AUTHORITY)
        self.assertEqual(self.bundle.common_portfolio, EXPECTED_COMMON_PORTFOLIO)
        self.assertEqual(self.bundle.common_relation_count, 42)
        self.assertIs(self.bundle.t2_utility_authorized, False)
        self.assertEqual(self.bundle.main_descriptor_hash, EXPECTED_MAIN_DESCRIPTOR)
        self.assertEqual(self.bundle.main_reference_set_hash, EXPECTED_MAIN_REFERENCE_SET)
        self.assertEqual(self.bundle.supplement_descriptor_hash, EXPECTED_SUPPLEMENT_DESCRIPTOR)
        self.assertEqual(self.bundle.supplement_reference_set_hash, EXPECTED_SUPPLEMENT_REFERENCE_SET)
        self.assertEqual(self.bundle.combined_source_census_contract_hash, EXPECTED_COMBINED_CENSUS)
        self.assertEqual(
            (len(self.bundle.main_sources), len(self.bundle.supplement_sources), len(self.bundle.evaluator_source_census)),
            (9, 3, 12),
        )
        self.assertEqual(
            authority_v1.validate_evaluator_authority_bundle_v1(self.bundle),
            EXPECTED_BUNDLE_HASH,
        )

    def test_02_independent_r3_and_detector_authority_replay(self) -> None:
        self.assertEqual(_independent_hash(_independent_r3_payload()), EXPECTED_R3_IDENTITY)
        self.assertEqual(
            _independent_hash(_independent_detector_authority_payload()),
            EXPECTED_DETECTOR_AUTHORITY,
        )
        self.assertEqual(authority_v1.UTILITY_EVALUATOR_CONTROL_REVISION, "R3")
        self.assertEqual(
            authority_v1.CURRENT_EVALUATOR_IMPLEMENTATION_IDENTITY,
            EXPECTED_R3_IDENTITY,
        )
        self.assertEqual(
            metrics_v1.SYNTHETIC_DETECTOR_AUTHORITY_IDENTITY,
            EXPECTED_DETECTOR_AUTHORITY,
        )
        self.assertNotIn(
            EXPECTED_R3_IDENTITY,
            {EXPECTED_ORIGINAL_IDENTITY, EXPECTED_R1_IDENTITY, EXPECTED_R2_IDENTITY},
        )

    def test_03_factory_authorities_are_valid_and_distinct_issued_objects(self) -> None:
        self.assertIsNot(self.bundle, self.other_bundle)
        self.assertEqual(self.bundle, self.other_bundle)
        self.assertEqual(
            authority_v1.validate_evaluator_implementation_authority_v1(
                self.implementation, self.bundle
            ),
            EXPECTED_R3_IDENTITY,
        )

    def test_04_bundle_reconstruction_copy_replace_and_serialization_reject(self) -> None:
        candidates = (
            _reconstruct(self.bundle),
            copy.copy(self.bundle),
            copy.deepcopy(self.bundle),
            replace(self.bundle),
            pickle.loads(pickle.dumps(self.bundle)),
        )
        for index, candidate in enumerate(candidates):
            with self.subTest(case=index):
                self.assertBundleRejected(candidate)

    def test_05_bundle_semantic_self_replay_forgery_reject(self) -> None:
        mutations = (
            {"metric_policy_hash": "e" * 64},
            {"common_relation_count": 41},
            {"t2_utility_authorized": True},
            {"v4_authority_hash": "2864c99017dcea576437efe9f9c5d531cc0d7810504cb2bd8e8585643d2fa0a1"},
            {"main_descriptor_hash": "d" * 64},
            {"supplement_descriptor_hash": "c" * 64},
            {"combined_source_census_contract_hash": "b" * 64},
            {"evaluator_source_census": self.bundle.evaluator_source_census[:-1]},
        )
        for change in mutations:
            candidate = replace(self.bundle, **change)
            key = id(candidate)
            authority_v1._ISSUED_EVALUATOR_AUTHORITY_BUNDLES[key] = (
                weakref.ref(candidate), candidate.bundle_hash
            )
            try:
                with self.subTest(field=next(iter(change))):
                    self.assertBundleRejected(candidate)
            finally:
                authority_v1._ISSUED_EVALUATOR_AUTHORITY_BUNDLES.pop(key, None)

    def test_06_bundle_issuance_exact_reference_hash_and_presence_required(self) -> None:
        key = id(self.bundle)
        saved = authority_v1._ISSUED_EVALUATOR_AUTHORITY_BUNDLES[key]
        variants = (
            (weakref.ref(self.other_bundle), saved[1]),
            (saved[0], "f" * 64),
        )
        try:
            for variant in variants:
                authority_v1._ISSUED_EVALUATOR_AUTHORITY_BUNDLES[key] = variant
                self.assertBundleRejected(self.bundle)
            authority_v1._ISSUED_EVALUATOR_AUTHORITY_BUNDLES.pop(key, None)
            self.assertBundleRejected(self.bundle)
        finally:
            authority_v1._ISSUED_EVALUATOR_AUTHORITY_BUNDLES[key] = saved

    def test_07_bundle_weakref_cleanup_and_post_gc_stale_entry_reject(self) -> None:
        issued = authority_v1.build_evaluator_authority_bundle_v1(self.v4_authority)
        key = id(issued)
        issued_ref = weakref.ref(issued)
        del issued
        gc.collect()
        self.assertIsNone(issued_ref())
        self.assertNotIn(key, authority_v1._ISSUED_EVALUATOR_AUTHORITY_BUNDLES)
        lookalike = _reconstruct(self.bundle)
        self.assertBundleRejected(lookalike)

    def test_08_implementation_reconstruction_copy_replace_and_serialization_reject(self) -> None:
        candidates = (
            _reconstruct(self.implementation),
            copy.copy(self.implementation),
            copy.deepcopy(self.implementation),
            replace(self.implementation),
            pickle.loads(pickle.dumps(self.implementation)),
        )
        for index, candidate in enumerate(candidates):
            with self.subTest(case=index):
                self.assertImplementationRejected(candidate)

    def test_09_implementation_semantic_self_rehash_forgery_reject(self) -> None:
        mutations = (
            {"control_revision": "R2"},
            {"evaluator_authority_bundle_hash": "e" * 64},
            {"v4_authority_hash": "d" * 64},
            {"utility_portfolio": "T2-39"},
            {"execution_mode": "REAL_AUTHORIZED_UTILITY_EXECUTION"},
            {"synthetic_authority_identity": "c" * 64},
            {"production_modules": self.implementation.production_modules[:-1]},
            {"real_utility_execution_authorized": True},
        )
        for change in mutations:
            provisional = replace(self.implementation, **change, implementation_identity="")
            candidate = replace(
                provisional,
                implementation_identity=_independent_hash(
                    {
                        field.name: _json_value(getattr(provisional, field.name))
                        for field in fields(provisional)
                        if field.name != "implementation_identity"
                    }
                ),
            )
            key = id(candidate)
            authority_v1._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES[key] = (
                weakref.ref(candidate),
                candidate.implementation_identity,
                candidate.evaluator_authority_bundle_hash,
                weakref.ref(self.bundle),
            )
            try:
                with self.subTest(field=next(iter(change))):
                    self.assertImplementationRejected(candidate)
            finally:
                authority_v1._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES.pop(key, None)

    def test_10_implementation_cross_bundle_and_reconstructed_bundle_reject(self) -> None:
        self.assertImplementationRejected(self.implementation, self.other_bundle)
        self.assertImplementationRejected(self.implementation, _reconstruct(self.bundle))
        with self.assertRaises(UtilityEvaluatorV1Error):
            authority_v1.build_evaluator_implementation_authority_v1(
                _reconstruct(self.bundle)  # type: ignore[arg-type]
            )

    def test_11_implementation_issuance_metadata_and_presence_required(self) -> None:
        key = id(self.implementation)
        saved = authority_v1._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES[key]
        other = authority_v1.build_evaluator_implementation_authority_v1(self.other_bundle)
        variants = (
            (weakref.ref(other), saved[1], saved[2], saved[3]),
            (saved[0], "f" * 64, saved[2], saved[3]),
            (saved[0], saved[1], "e" * 64, saved[3]),
            (saved[0], saved[1], saved[2], weakref.ref(self.other_bundle)),
        )
        try:
            for variant in variants:
                authority_v1._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES[key] = variant
                self.assertImplementationRejected(self.implementation)
            authority_v1._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES.pop(key, None)
            self.assertImplementationRejected(self.implementation)
        finally:
            authority_v1._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES[key] = saved

    def test_12_implementation_weakref_cleanup_for_authority_and_bundle(self) -> None:
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

    def test_13_bare_implementation_identities_and_missing_authority_reject(self) -> None:
        identities: tuple[object, ...] = (
            EXPECTED_ORIGINAL_IDENTITY,
            EXPECTED_R1_IDENTITY,
            EXPECTED_R2_IDENTITY,
            EXPECTED_R3_IDENTITY,
            "f" * 64,
            "malformed",
            "",
            None,
        )
        for identity in identities:
            with self.subTest(identity=identity), self.assertRaises(UtilityEvaluatorV1Error):
                metrics_v1.build_rule_prediction_artifact_v1(
                    evaluator_implementation_identity=identity,
                    bundle=self.bundle,
                    frame=self.frame,
                    census=self.census,
                    resolver=self.resolver,
                    predictions=self.predictions,
                )
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics_v1.build_rule_prediction_artifact_v1(
                bundle=self.bundle,
                frame=self.frame,
                census=self.census,
                resolver=self.resolver,
                predictions=self.predictions,
            )

    def test_14_nonissued_and_cross_bundle_implementation_cannot_issue_rule_artifact(self) -> None:
        candidates = (
            _reconstruct(self.implementation),
            copy.deepcopy(self.implementation),
            replace(self.implementation),
            pickle.loads(pickle.dumps(self.implementation)),
        )
        for candidate in candidates:
            with self.assertRaises(UtilityEvaluatorV1Error):
                metrics_v1.build_rule_prediction_artifact_v1(
                    evaluator_implementation_authority=candidate,  # type: ignore[arg-type]
                    bundle=self.bundle,
                    frame=self.frame,
                    census=self.census,
                    resolver=self.resolver,
                    predictions=self.predictions,
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

    def test_15_rule_artifact_current_provenance_and_factory_custody(self) -> None:
        self.assertEqual(
            metrics_v1.validate_rule_prediction_artifact_v1(self.rule_artifact),
            self.rule_artifact.artifact_hash,
        )
        self.assertEqual(
            self.rule_artifact.evaluator_implementation_identity, EXPECTED_R3_IDENTITY
        )
        self.assertEqual(
            self.rule_artifact.evaluator_authority_bundle_hash, EXPECTED_BUNDLE_HASH
        )

    def test_16_rule_artifact_reconstruction_copy_replace_and_serialization_reject(self) -> None:
        candidates = (
            _reconstruct(self.rule_artifact),
            copy.copy(self.rule_artifact),
            copy.deepcopy(self.rule_artifact),
            replace(self.rule_artifact),
            pickle.loads(pickle.dumps(self.rule_artifact)),
        )
        for candidate in candidates:
            self.assertRuleRejected(candidate)

    def test_17_rule_provenance_self_rehash_and_forged_issuance_reject(self) -> None:
        identities = (
            EXPECTED_ORIGINAL_IDENTITY,
            EXPECTED_R1_IDENTITY,
            EXPECTED_R2_IDENTITY,
            "f" * 64,
            "",
        )
        for identity in identities:
            provisional = replace(
                self.rule_artifact,
                evaluator_implementation_identity=identity,
                artifact_hash="",
            )
            candidate = replace(provisional, artifact_hash=_artifact_hash(provisional))
            self.assertRuleRejected(candidate)
            key = id(candidate)
            metrics_v1._ISSUED_RULE_ARTIFACTS[key] = (
                weakref.ref(candidate),
                candidate.artifact_hash,
                candidate.evaluator_implementation_identity,
                candidate.evaluator_authority_bundle_hash,
            )
            try:
                self.assertRuleRejected(candidate)
            finally:
                metrics_v1._ISSUED_RULE_ARTIFACTS.pop(key, None)

    def test_18_rule_bundle_provenance_self_rehash_reject(self) -> None:
        provisional = replace(
            self.rule_artifact,
            evaluator_authority_bundle_hash="e" * 64,
            artifact_hash="",
        )
        candidate = replace(provisional, artifact_hash=_artifact_hash(provisional))
        self.assertRuleRejected(candidate)
        key = id(candidate)
        metrics_v1._ISSUED_RULE_ARTIFACTS[key] = (
            weakref.ref(candidate),
            candidate.artifact_hash,
            candidate.evaluator_implementation_identity,
            candidate.evaluator_authority_bundle_hash,
        )
        try:
            self.assertRuleRejected(candidate)
        finally:
            metrics_v1._ISSUED_RULE_ARTIFACTS.pop(key, None)

    def test_19_rule_issuance_exact_reference_metadata_and_presence_required(self) -> None:
        key = id(self.rule_artifact)
        saved = metrics_v1._ISSUED_RULE_ARTIFACTS[key]
        other = self._new_rule_artifact()
        variants = (
            (weakref.ref(other), saved[1], saved[2], saved[3]),
            (saved[0], "f" * 64, saved[2], saved[3]),
            (saved[0], saved[1], EXPECTED_R2_IDENTITY, saved[3]),
            (saved[0], saved[1], saved[2], "e" * 64),
        )
        try:
            for variant in variants:
                metrics_v1._ISSUED_RULE_ARTIFACTS[key] = variant
                self.assertRuleRejected(self.rule_artifact)
            metrics_v1._ISSUED_RULE_ARTIFACTS.pop(key, None)
            self.assertRuleRejected(self.rule_artifact)
        finally:
            metrics_v1._ISSUED_RULE_ARTIFACTS[key] = saved

    def test_20_rule_artifact_weakref_cleanup(self) -> None:
        artifact = self._new_rule_artifact()
        key = id(artifact)
        artifact_ref = weakref.ref(artifact)
        del artifact
        gc.collect()
        self.assertIsNone(artifact_ref())
        self.assertNotIn(key, metrics_v1._ISSUED_RULE_ARTIFACTS)

    def test_21_detector_factory_authority_and_synthetic_boundary(self) -> None:
        detector = self._new_detector()
        self.assertEqual(
            metrics_v1.validate_detector_prediction_artifact_v1(detector),
            detector.artifact_hash,
        )
        self.assertEqual(detector.detector_authority_identity, EXPECTED_DETECTOR_AUTHORITY)
        self.assertEqual(detector.execution_mode, EXPECTED_SYNTHETIC_MODE)
        self.assertIs(detector.scientific_eligible, False)

    def test_22_caller_selected_detector_authority_never_issues(self) -> None:
        identities: tuple[object, ...] = (
            EXPECTED_DETECTOR_AUTHORITY,
            "a" * 64,
            EXPECTED_R3_IDENTITY,
            "not-a-sha",
            "",
            None,
        )
        for identity in identities:
            with self.subTest(identity=identity), self.assertRaises(UtilityEvaluatorV1Error):
                self._new_detector(detector_authority_identity=identity)

    def test_23_detector_reconstruction_copy_replace_and_serialization_reject(self) -> None:
        detector = self._new_detector()
        candidates = (
            _reconstruct(detector),
            copy.copy(detector),
            copy.deepcopy(detector),
            replace(detector),
            pickle.loads(pickle.dumps(detector)),
        )
        for candidate in candidates:
            self.assertDetectorRejected(candidate)

    def test_24_detector_issued_field_self_rehash_mutations_reject(self) -> None:
        detector = self._new_detector()
        mutations = (
            {"detector_authority_identity": "b" * 64},
            {"detector_authority_identity": "malformed"},
            {"dataset_manifest_identity": "other-dataset"},
            {"split_identity": "other-split"},
            {"source_file_identity": "other-file"},
            {"artifact_type": "wrong-artifact"},
            {"execution_mode": "REAL_AUTHORIZED_UTILITY_EXECUTION"},
            {"scientific_eligible": True},
        )
        for change in mutations:
            provisional = replace(detector, **change, artifact_hash="")
            candidate = replace(provisional, artifact_hash=_artifact_hash(provisional))
            with self.subTest(field=next(iter(change))):
                self.assertDetectorRejected(candidate)

    def test_25_detector_prediction_vector_mutations_reject(self) -> None:
        detector = self._new_detector()
        original = detector.point_predictions
        vectors: tuple[object, ...] = (
            (True,) + original[1:],
            original + (False,),
            original[:-1],
            tuple(reversed((True,) + original[1:])),
            list(original),
            (1,) + original[1:],
            (1.0,) + original[1:],
            ("false",) + original[1:],
            (),
        )
        for vector in vectors:
            provisional = replace(detector, point_predictions=vector, artifact_hash="")  # type: ignore[arg-type]
            candidate = replace(provisional, artifact_hash=_artifact_hash(provisional))
            with self.subTest(kind=type(vector).__name__, length=len(vector)):
                self.assertDetectorRejected(candidate)

    def test_26_detector_factory_rejects_empty_identity_fields_and_bad_prediction_types(self) -> None:
        invalid_builds = (
            {"dataset_manifest_identity": ""},
            {"split_identity": ""},
            {"source_file_identity": ""},
            {"point_predictions": [False]},
            {"point_predictions": (0,)},
            {"point_predictions": (1.0,)},
            {"point_predictions": ("false",)},
        )
        for change in invalid_builds:
            with self.subTest(field=next(iter(change))), self.assertRaises(
                UtilityEvaluatorV1Error
            ):
                self._new_detector(**change)

    def test_27_detector_issuance_metadata_reference_and_presence_required(self) -> None:
        detector = self._new_detector()
        other = self._new_detector()
        key = id(detector)
        saved = metrics_v1._ISSUED_DETECTOR_ARTIFACTS[key]
        variants = (
            (weakref.ref(other), *saved[1:]),
            (saved[0], "f" * 64, *saved[2:]),
            (saved[0], saved[1], "e" * 64, *saved[3:]),
            (*saved[:3], "other-dataset", *saved[4:]),
            (*saved[:4], "other-split", *saved[5:]),
            (*saved[:5], "other-file", saved[6]),
            (*saved[:6], "d" * 64),
        )
        try:
            for variant in variants:
                metrics_v1._ISSUED_DETECTOR_ARTIFACTS[key] = variant
                self.assertDetectorRejected(detector)
            metrics_v1._ISSUED_DETECTOR_ARTIFACTS.pop(key, None)
            self.assertDetectorRejected(detector)
        finally:
            metrics_v1._ISSUED_DETECTOR_ARTIFACTS[key] = saved

    def test_28_detector_semantics_still_required_when_forged_issuance_is_inserted(self) -> None:
        detector = self._new_detector()
        provisional = replace(
            detector,
            execution_mode="REAL_AUTHORIZED_UTILITY_EXECUTION",
            artifact_hash="",
        )
        candidate = replace(provisional, artifact_hash=_artifact_hash(provisional))
        key = id(candidate)
        metrics_v1._ISSUED_DETECTOR_ARTIFACTS[key] = (
            weakref.ref(candidate),
            candidate.artifact_hash,
            candidate.detector_authority_identity,
            candidate.dataset_manifest_identity,
            candidate.split_identity,
            candidate.source_file_identity,
            metrics_v1._detector_prediction_vector_hash(candidate.point_predictions),
        )
        try:
            self.assertDetectorRejected(candidate)
        finally:
            metrics_v1._ISSUED_DETECTOR_ARTIFACTS.pop(key, None)

    def test_29_detector_weakref_cleanup_and_serialized_replay_stay_nonissued(self) -> None:
        detector = self._new_detector()
        serialized = pickle.dumps(detector)
        key = id(detector)
        detector_ref = weakref.ref(detector)
        del detector
        gc.collect()
        self.assertIsNone(detector_ref())
        self.assertNotIn(key, metrics_v1._ISSUED_DETECTOR_ARTIFACTS)
        self.assertDetectorRejected(pickle.loads(serialized))

    def test_30_comparison_accepts_only_factory_custodied_matching_detector(self) -> None:
        detector = self._new_detector()
        comparison = metrics_v1.build_synthetic_rule_detector_comparison_input_v1(
            detector=detector,
            d1_rule_artifact=self.rule_artifact,
            d2_rule_artifact=self.rule_artifact,
        )
        self.assertIs(comparison.scientific_eligible, False)
        self.assertIs(comparison.fusion_authorized, False)
        self.assertTrue(comparison.same_rule_artifact_required)

        provisional = replace(
            detector,
            point_predictions=(True,) + detector.point_predictions[1:],
            artifact_hash="",
        )
        forged = replace(provisional, artifact_hash=_artifact_hash(provisional))
        for candidate in (_reconstruct(detector), copy.deepcopy(detector), forged):
            with self.assertRaises(UtilityEvaluatorV1Error):
                metrics_v1.build_synthetic_rule_detector_comparison_input_v1(
                    detector=candidate,  # type: ignore[arg-type]
                    d1_rule_artifact=self.rule_artifact,
                    d2_rule_artifact=self.rule_artifact,
                )

    def test_31_comparison_dataset_split_file_reject_and_same_content_accept(self) -> None:
        for change in (
            {"dataset_manifest_identity": "other-dataset"},
            {"split_identity": "other-split"},
            {"source_file_identity": "other-file"},
        ):
            detector = self._new_detector(**change)
            with self.assertRaises(UtilityEvaluatorV1Error):
                metrics_v1.build_synthetic_rule_detector_comparison_input_v1(
                    detector=detector,
                    d1_rule_artifact=self.rule_artifact,
                    d2_rule_artifact=self.rule_artifact,
                )
        other_rule = self._new_rule_artifact()
        self.assertEqual(other_rule, self.rule_artifact)
        self.assertIsNot(other_rule, self.rule_artifact)
        detector = self._new_detector()
        comparison = metrics_v1.build_synthetic_rule_detector_comparison_input_v1(
            detector=detector,
            d1_rule_artifact=self.rule_artifact,
            d2_rule_artifact=other_rule,
        )
        self.assertEqual(
            comparison.d1_rule_artifact_hash,
            comparison.d2_rule_artifact_hash,
        )

    def test_32_synthetic_rule_and_comparison_scientific_validators_fail_closed(self) -> None:
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics_v1.validate_scientific_rule_prediction_artifact_v1(
                self.rule_artifact
            )
        detector = self._new_detector()
        comparison = metrics_v1.build_synthetic_rule_detector_comparison_input_v1(
            detector=detector,
            d1_rule_artifact=self.rule_artifact,
            d2_rule_artifact=self.rule_artifact,
        )
        with self.assertRaises(UtilityEvaluatorV1Error):
            metrics_v1.validate_scientific_rule_detector_comparison_input_v1(
                comparison
            )


if __name__ == "__main__":
    unittest.main()
