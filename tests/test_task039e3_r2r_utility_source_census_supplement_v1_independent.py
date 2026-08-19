from __future__ import annotations

import copy
from dataclasses import replace
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_utility_normal_only_authority_v1 import (
    CALIBRATION_POLICY_HASH,
    NORMAL_INPUT_IDENTITY_SET_HASH,
    NORMAL_TRAIN1_IDENTITY,
    NORMAL_TRAIN2_IDENTITY,
    derive_source_parameters_normal_only_v1,
)
from paperworks.v6.task039e3_r2r_utility_protocol_v3 import UTILITY_SOURCE_UNIVERSE_V3
from paperworks.v6.task039e3_r2r_utility_protocol_v4 import build_common42_public_authority_v4
from paperworks.v6 import task039e3_r2r_utility_source_census_supplement_v1 as subject


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "paperworks" / "v6" / "task039e3_r2r_utility_source_census_supplement_v1.py"
SOURCE_RAW_SHA256 = "f238492892f6b9b6260204d1f000952256898ba2ee10ae80c1e7d0c1e2a6e882"
IMPLEMENTATION_COMMIT = "5fb2ba426d5a4720362030c9055ddacdcf99931a"
EXPECTED_SOURCES = ("P1_FCV02Z", "P1_PCV02Z", "P1_PP04")
EXPECTED_ROLES = ("source_step_threshold", "source_stability_tolerance")


def _hash(payload: dict) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _rehash(document: dict) -> dict:
    document["artifact_hash"] = _hash(
        {key: value for key, value in document.items() if key != "artifact_hash"}
    )
    return document


def _registry() -> dict:
    definition = subject.build_supplement_authority_definition_v1()
    values = {
        (source, role): (2.0 if role == "source_step_threshold" else 0.25)
        for source in EXPECTED_SOURCES
        for role in EXPECTED_ROLES
    }
    return subject.build_supplement_private_registry_document_v1(definition, values)


def _common_authority():
    reports = ROOT / "docs" / "task_reports"
    executable = json.loads(
        (reports / "TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json").read_text(
            encoding="utf-8"
        )
    )
    evidence = json.loads(
        (reports / "TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json").read_text(
            encoding="utf-8"
        )
    )
    return build_common42_public_authority_v4(executable, evidence)


def _authorization() -> dict:
    value = {
        "artifact_type": "task039e3_r2r_utility_source_census_supplement_v1_materialization_authorization",
        "schema_version": "1.0.0",
        "task_id": subject.TASK_ID,
        "authority_version": subject.AUTHORITY_VERSION,
        "purpose": subject.PURPOSE,
        "scope": subject.MATERIALIZATION_SCOPE,
        "coverage_decision_hash": subject.COVERAGE_DECISION_HASH,
        "supplement_descriptor_hash": subject.SUPPLEMENT_DESCRIPTOR_HASH,
        "reference_set_hash": subject.SUPPLEMENT_REFERENCE_SET_HASH,
        "normal_input_identity_set_hash": NORMAL_INPUT_IDENTITY_SET_HASH,
        "calibration_policy_hash": CALIBRATION_POLICY_HASH,
        "event_policy_hash": subject.SOURCE_CENSUS_EVENT_POLICY_HASH,
        "v4_r1_authority_hash": subject.V4_R1_AUTHORITY_HASH,
        "v4_r1_focused_receipt_hash": subject.V4_R1_FOCUSED_RECEIPT_HASH,
        "implementation_commit": IMPLEMENTATION_COMMIT,
        "implementation_source_git_blob": "1" * 40,
        "implementation_source_raw_sha256": SOURCE_RAW_SHA256,
        "independent_audit_commit": "2" * 40,
        "independent_test_git_blob": "3" * 40,
        "independent_test_raw_sha256": "4" * 64,
        "normal_only_source_git_blob": subject.NORMAL_ONLY_SOURCE_BLOB,
        "normal_only_source_raw_sha256": subject.NORMAL_ONLY_SOURCE_RAW_SHA256,
        "calibration_dependency_git_blob": subject.CALIBRATION_DEPENDENCY_BLOB,
        "calibration_dependency_raw_sha256": subject.CALIBRATION_DEPENDENCY_RAW_SHA256,
        "authorized_sources": list(EXPECTED_SOURCES),
        "train1_access": True,
        "train2_access": True,
        "train3_access": False,
        "train4_access": False,
        "test1_access": False,
        "test2_access": False,
        "label_access": False,
        "attack_interval_access": False,
        "provider_access": False,
        "llm_access": False,
        "utility_execution": False,
        "detector_execution": False,
        "materialization_authorized": True,
    }
    return _rehash(value)


class IndependentSupplementAudit(unittest.TestCase):
    def test_commit_a_source_is_frozen_and_non_self_referential(self) -> None:
        raw = SOURCE.read_bytes()
        self.assertEqual(SOURCE_RAW_SHA256, hashlib.sha256(raw).hexdigest())
        text = raw.decode("utf-8")
        self.assertNotIn(IMPLEMENTATION_COMMIT, text)
        self.assertNotIn(SOURCE_RAW_SHA256, text)
        signature = inspect.signature(subject.materialize_source_census_supplement_v1)
        for forbidden in (
            "authorization", "sources", "roles", "required_features",
            "expected_builder_commit", "formula",
        ):
            self.assertNotIn(forbidden, signature.parameters)

    def test_independent_reference_replay(self) -> None:
        event_policy = {
            "policy_version": "TASK039E3_SOURCE_CENSUS_EVENT_POLICY_V1",
            "source_pre_window_seconds": 5,
            "source_post_window_seconds": 5,
            "minimum_source_stability_fraction": 0.8,
            "source_refractory_seconds": 10,
            "cross_source_isolation_radius_seconds": 2,
            "clustering": "single_link_within_refractory_window",
            "retention": "largest_absolute_step_amplitude",
            "exact_amplitude_tie": "earliest_physical_index",
            "v4_event_policy_hash": "6e4a4467953c5c9bf973a0a8a18950669dc902310407b7b354128ad91febb2f4",
        }
        event_hash = _hash(event_policy)
        purpose = _hash(
            {
                "authority_version": "TASK039E3_UTILITY_SOURCE_CENSUS_SUPPLEMENT_V1",
                "purpose": "CROSS_SOURCE_ISOLATION_EVENT_CENSUS_ONLY",
                "sources": list(EXPECTED_SOURCES),
                "roles": list(EXPECTED_ROLES),
                "event_policy_hash": event_hash,
                "normal_input_identity_set_hash": NORMAL_INPUT_IDENTITY_SET_HASH,
                "calibration_policy_hash": CALIBRATION_POLICY_HASH,
            }
        )
        references = []
        for source in EXPECTED_SOURCES:
            for role in EXPECTED_ROLES:
                digest = _hash(
                    {
                        "authority_version": subject.AUTHORITY_VERSION,
                        "source_identity": source,
                        "numeric_role": role,
                        "normal_input_identity_set_hash": NORMAL_INPUT_IDENTITY_SET_HASH,
                        "calibration_policy_hash": CALIBRATION_POLICY_HASH,
                        "source_census_purpose_identity": purpose,
                    }
                )
                references.append(f"{subject.AUTHORITY_VERSION}:{digest}")
        reference_set = _hash(
            {
                "authority_version": subject.AUTHORITY_VERSION,
                "reference_count": 6,
                "reference_identities": sorted(references),
            }
        )
        self.assertEqual(subject.SOURCE_CENSUS_EVENT_POLICY_HASH, event_hash)
        self.assertEqual(subject.SOURCE_CENSUS_PURPOSE_IDENTITY, purpose)
        self.assertEqual(tuple(references), subject.SUPPLEMENT_REFERENCE_IDENTITIES)
        self.assertEqual(subject.SUPPLEMENT_REFERENCE_SET_HASH, reference_set)
        self.assertEqual(6, len(set(references)))

    def test_exact_gap_is_derived_from_lower_public_sets(self) -> None:
        executable = json.loads(
            (ROOT / "docs" / "task_reports" / "TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json").read_text(encoding="utf-8")
        )
        common_sources = tuple(
            sorted({item["executable_signature"]["source"] for item in executable["relation_records"]})
        )
        difference = tuple(sorted(set(UTILITY_SOURCE_UNIVERSE_V3) - set(common_sources)))
        self.assertEqual(12, len(UTILITY_SOURCE_UNIVERSE_V3))
        self.assertEqual(9, len(common_sources))
        self.assertEqual(EXPECTED_SOURCES, difference)

    def test_formula_delegate_is_called_three_times_and_only_for_exact_sources(self) -> None:
        train = {source: (0.0, 1.0) for source in EXPECTED_SOURCES}
        with patch.object(
            subject,
            "derive_source_parameters_normal_only_v1",
            side_effect=((1.0, 0.1), (1.5, 0.2), (2.0, 0.3)),
        ) as delegate:
            observed = subject.derive_supplement_role_values_v1(train, train)
        self.assertEqual(3, delegate.call_count)
        self.assertEqual(6, len(observed))

    def test_formula_outputs_equal_the_frozen_delegate_on_synthetic_series(self) -> None:
        train1 = {
            source: tuple(float((index * (offset + 2)) % 11) for index in range(80))
            for offset, source in enumerate(EXPECTED_SOURCES)
        }
        train2 = {
            source: tuple(float(((index + 3) * (offset + 3)) % 13) for index in range(90))
            for offset, source in enumerate(EXPECTED_SOURCES)
        }
        observed = subject.derive_supplement_role_values_v1(train1, train2)
        for source in EXPECTED_SOURCES:
            threshold, tolerance = derive_source_parameters_normal_only_v1(
                train1[source], train2[source]
            )
            self.assertEqual(
                threshold.hex(),
                observed[(source, "source_step_threshold")].hex(),
            )
            self.assertEqual(
                tolerance.hex(),
                observed[(source, "source_stability_tolerance")].hex(),
            )

    def test_definition_scope_attack_matrix(self) -> None:
        canonical = subject.build_supplement_authority_definition_v1()
        attacks = (
            replace(canonical, authority_version=subject.MAIN_AUTHORITY_VERSION),
            replace(canonical, purpose="COMMON_RULE_NUMERIC_BINDING"),
            replace(canonical, sources=canonical.sources[:-1]),
            replace(canonical, sources=canonical.sources + ("P1_FCV01D",)),
            replace(canonical, sources=("P1_FCV01D",) + canonical.sources[1:]),
            replace(canonical, roles=("source_step_threshold",)),
            replace(canonical, roles=("source_step_threshold", "target_noise_scale")),
            replace(canonical, roles=("source_step_threshold", "Direct-number")),
            replace(canonical, reference_identities=canonical.reference_identities[:-1]),
            replace(canonical, reference_identities=canonical.reference_identities + (canonical.reference_identities[0],)),
            replace(canonical, reference_set_hash="1" * 64),
            replace(canonical, normal_input_identity_set_hash="2" * 64),
            replace(canonical, calibration_policy_hash="3" * 64),
            replace(canonical, event_policy_hash="4" * 64),
            replace(canonical, purpose_identity="5" * 64),
        )
        for index, attack in enumerate(attacks):
            with self.subTest(index=index):
                with self.assertRaises(subject.SourceCensusSupplementV1Error):
                    subject.validate_supplement_authority_definition_v1(attack)

    def test_registry_record_attack_matrix(self) -> None:
        def attack(field: str, value: object, *, index: int = 0) -> dict:
            document = copy.deepcopy(_registry())
            document["records"][index][field] = value
            try:
                document["records"][index]["record_hash"] = _hash(
                    {key: item for key, item in document["records"][index].items() if key != "record_hash"}
                )
                return _rehash(document)
            except ValueError:
                return document

        attacks = (
            attack("source_identity", "P1_FCV01D"),
            attack("numeric_role", "target_noise_scale"),
            attack("new_reference_identity", subject.SUPPLEMENT_REFERENCE_IDENTITIES[1]),
            attack("normal_train1_identity", "1" * 64),
            attack("normal_train2_identity", "2" * 64),
            attack("calibration_policy_hash", "3" * 64),
            attack("provenance_identity", "4" * 64),
            attack("numeric_value", 1),
            attack("numeric_value", True),
            attack("numeric_value", 0.0),
            attack("numeric_value", math.nan),
            attack("numeric_value", -0.1, index=1),
            attack("numeric_value", math.inf, index=1),
        )
        for index, document in enumerate(attacks):
            with self.subTest(index=index):
                with self.assertRaises((subject.SourceCensusSupplementV1Error, ValueError)):
                    subject.validate_supplement_private_registry_document_v1(document)

    def test_registry_document_attack_matrix(self) -> None:
        attacks = []
        missing = copy.deepcopy(_registry())
        missing["records"].pop()
        attacks.append(missing)
        duplicate = copy.deepcopy(_registry())
        duplicate["records"].append(copy.deepcopy(duplicate["records"][0]))
        attacks.append(duplicate)
        wrong_count = copy.deepcopy(_registry())
        wrong_count["record_count"] = 6.0
        attacks.append(wrong_count)
        extra = copy.deepcopy(_registry())
        extra["raw_values"] = []
        attacks.append(extra)
        wrong_descriptor = copy.deepcopy(_registry())
        wrong_descriptor["supplement_descriptor_hash"] = "1" * 64
        attacks.append(wrong_descriptor)
        for index, value in enumerate(attacks):
            try:
                _rehash(value)
            except ValueError:
                pass
            with self.subTest(index=index):
                with self.assertRaises(subject.SourceCensusSupplementV1Error):
                    subject.validate_supplement_private_registry_document_v1(value)

    def test_authorization_attack_matrix(self) -> None:
        canonical = _authorization()
        mutations = (
            ("scope", "NORMAL_ALL"),
            ("authorized_sources", list(EXPECTED_SOURCES) + ["P1_FCV01D"]),
            ("coverage_decision_hash", "1" * 64),
            ("supplement_descriptor_hash", "2" * 64),
            ("normal_input_identity_set_hash", "3" * 64),
            ("calibration_policy_hash", "4" * 64),
            ("train3_access", True),
            ("train4_access", True),
            ("test1_access", True),
            ("test2_access", True),
            ("label_access", True),
            ("attack_interval_access", True),
            ("provider_access", True),
            ("llm_access", True),
            ("utility_execution", True),
            ("detector_execution", True),
            ("materialization_authorized", 1),
            ("materialization_authorized", "true"),
        )
        for field, value in mutations:
            document = copy.deepcopy(canonical)
            document[field] = value
            _rehash(document)
            with self.subTest(field=field, value_type=type(value).__name__):
                with self.assertRaises(subject.SourceCensusSupplementV1Error):
                    subject.validate_materialization_authorization_document_v1(document)

    def test_preflight_failure_occurs_before_scientific_loader(self) -> None:
        inside = ROOT / "not-authorized-private.json"
        old = os.environ.get(subject.PRIVATE_AUTHORITY_ENV)
        os.environ[subject.PRIVATE_AUTHORITY_ENV] = str(inside)
        try:
            with patch.object(subject, "load_committed_materialization_authorization_v1", return_value=_authorization()), patch.object(
                subject, "load_verified_normal_features_v1"
            ) as loader:
                with self.assertRaises(subject.SourceCensusSupplementV1Error):
                    subject.materialize_source_census_supplement_v1(
                        train1_path=ROOT / "never-open-train1.csv",
                        train2_path=ROOT / "never-open-train2.csv",
                        private_destination=inside,
                        local_locator_path=ROOT.parent / "never-create-locator.json",
                        public_receipt_path=ROOT / subject.PUBLIC_RECEIPT_RELATIVE_PATH,
                        repository_root=ROOT,
                        execution_timestamp="2026-08-19T00:00:00+09:00",
                    )
                loader.assert_not_called()
        finally:
            if old is None:
                os.environ.pop(subject.PRIVATE_AUTHORITY_ENV, None)
            else:
                os.environ[subject.PRIVATE_AUTHORITY_ENV] = old

    def test_preflight_rejects_a_different_git_worktree(self) -> None:
        main_repository = ROOT.parents[1]
        private = main_repository / "forbidden-independent-private.json"
        locator = main_repository / "forbidden-independent-locator.json"
        old = os.environ.get(subject.PRIVATE_AUTHORITY_ENV)
        os.environ[subject.PRIVATE_AUTHORITY_ENV] = str(private)
        try:
            with self.assertRaises(subject.SourceCensusSupplementV1Error):
                subject.validate_materialization_output_preflight_v1(
                    private_destination=private,
                    local_locator_path=locator,
                    public_receipt_path=ROOT / subject.PUBLIC_RECEIPT_RELATIVE_PATH,
                    repository_root=ROOT,
                )
        finally:
            if old is None:
                os.environ.pop(subject.PRIVATE_AUTHORITY_ENV, None)
            else:
                os.environ[subject.PRIVATE_AUTHORITY_ENV] = old

    def test_public_receipt_is_closed_and_contains_no_values_or_paths(self) -> None:
        receipt = subject._build_public_receipt(
            registry_hash="1" * 64,
            locator_hash="2" * 64,
            authorization_hash="3" * 64,
            created_at="2026-08-19T00:00:00+09:00",
        )
        subject.validate_public_receipt_document_v1(receipt)
        for forbidden in (
            "numeric_value", "absolute_private_authority_path", "raw_values",
            "calibration_preview", "label", "credential",
        ):
            self.assertNotIn(forbidden, receipt)
        extra = copy.deepcopy(receipt)
        extra["numeric_summary"] = 1.0
        _rehash(extra)
        with self.assertRaises(subject.SourceCensusSupplementV1Error):
            subject.validate_public_receipt_document_v1(extra)

    def test_combined_contract_partition_and_main_collapse_policy_are_bound(self) -> None:
        canonical = subject.CombinedSourceCensusNumericContractV1(
            subject.MAIN_DESCRIPTOR_HASH,
            subject.MAIN_PRIVATE_REGISTRY_HASH,
            subject.MAIN_AUDIT_RECEIPT_HASH,
            subject.SUPPLEMENT_DESCRIPTOR_HASH,
            "1" * 64,
            "2" * 64,
            tuple(sorted(UTILITY_SOURCE_UNIVERSE_V3)),
            tuple(item for item in sorted(UTILITY_SOURCE_UNIVERSE_V3) if item not in EXPECTED_SOURCES),
            EXPECTED_SOURCES,
            subject.SOURCE_CENSUS_EVENT_POLICY_HASH,
            subject.CROSS_SOURCE_ISOLATION_POLICY_HASH,
            subject.MAIN_SOURCE_COLLAPSE_POLICY_HASH,
            12,
        )
        subject.validate_combined_source_census_numeric_contract_v1(canonical)
        attacks = (
            replace(canonical, main_sources=canonical.main_sources[:-1]),
            replace(canonical, main_sources=tuple(reversed(canonical.main_sources))),
            replace(canonical, supplement_sources=canonical.supplement_sources + (canonical.main_sources[0],)),
            replace(canonical, supplement_descriptor_hash="3" * 64),
            replace(canonical, main_source_collapse_policy_hash="4" * 64),
            replace(canonical, cross_source_isolation_policy_hash="5" * 64),
            replace(canonical, total_covered_sources=12.0),
        )
        for index, value in enumerate(attacks):
            with self.subTest(index=index):
                with self.assertRaises(subject.SourceCensusSupplementV1Error):
                    subject.validate_combined_source_census_numeric_contract_v1(value)

    def test_main_collapse_requires_exact_audited_registry_hash(self) -> None:
        common = _common_authority()
        source = common.relations[0].source
        with patch.object(
            subject,
            "validate_main_private_registry_document_v1",
            return_value="0" * 64,
        ):
            with self.assertRaises(subject.SourceCensusSupplementV1Error):
                subject.collapse_main_source_role_v1(
                    main_registry={},
                    common_authority=common,
                    source=source,
                    numeric_role="source_step_threshold",
                )

    def test_final_custody_requires_exact_committed_authorization_hash(self) -> None:
        authorization = _authorization()
        locator = {"authorization_hash": "0" * 64}
        public = {"authorization_hash": "0" * 64}
        with self.assertRaises(subject.SourceCensusSupplementV1Error):
            subject._validate_authorization_cross_custody_v1(
                locator, public, authorization
            )


if __name__ == "__main__":
    unittest.main()
