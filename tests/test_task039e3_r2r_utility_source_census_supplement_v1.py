from __future__ import annotations

import copy
from dataclasses import replace
import inspect
import json
import math
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_utility_normal_only_authority_v1 import (
    UTILITY_NUMERIC_ROLES,
    build_private_registry_document_v1,
)
from paperworks.v6.task039e3_r2r_utility_protocol_v4 import (
    build_common42_public_authority_v4,
    build_numeric_authority_descriptor_v4,
)
from paperworks.v6 import task039e3_r2r_utility_source_census_supplement_v1 as subject


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"


def _load(name: str) -> dict:
    with (REPORTS / name).open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _public_inputs() -> tuple[dict, dict, dict, dict]:
    return (
        _load("TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"),
        _load("TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json"),
        _load("TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZED_RECEIPT.json"),
        json.loads((ROOT / "configs" / "v6" / "task039br2_hai_continuous_step_feasibility.json").read_text(encoding="utf-8")),
    )


def _rehash(document: dict) -> dict:
    document["artifact_hash"] = stable_hash_v1(
        {key: value for key, value in document.items() if key != "artifact_hash"}
    )
    return document


def _registry() -> dict:
    definition = subject.build_supplement_authority_definition_v1()
    values = {
        (source, role): (1.0 if role == "source_step_threshold" else 0.1)
        for source in subject.SUPPLEMENT_SOURCES
        for role in subject.SUPPLEMENT_ROLES
    }
    return subject.build_supplement_private_registry_document_v1(definition, values)


def _authorization() -> dict:
    document = {
        "artifact_type": "task039e3_r2r_utility_source_census_supplement_v1_materialization_authorization",
        "schema_version": subject.SCHEMA_VERSION,
        "task_id": subject.TASK_ID,
        "authority_version": subject.AUTHORITY_VERSION,
        "purpose": subject.PURPOSE,
        "scope": subject.MATERIALIZATION_SCOPE,
        "coverage_decision_hash": subject.COVERAGE_DECISION_HASH,
        "supplement_descriptor_hash": subject.SUPPLEMENT_DESCRIPTOR_HASH,
        "reference_set_hash": subject.SUPPLEMENT_REFERENCE_SET_HASH,
        "normal_input_identity_set_hash": subject.NORMAL_INPUT_IDENTITY_SET_HASH,
        "calibration_policy_hash": subject.CALIBRATION_POLICY_HASH,
        "event_policy_hash": subject.SOURCE_CENSUS_EVENT_POLICY_HASH,
        "v4_r1_authority_hash": subject.V4_R1_AUTHORITY_HASH,
        "v4_r1_focused_receipt_hash": subject.V4_R1_FOCUSED_RECEIPT_HASH,
        "implementation_commit": "2" * 40,
        "implementation_source_git_blob": "3" * 40,
        "implementation_source_raw_sha256": "4" * 64,
        "independent_audit_commit": "5" * 40,
        "independent_test_git_blob": "6" * 40,
        "independent_test_raw_sha256": "7" * 64,
        "normal_only_source_git_blob": subject.NORMAL_ONLY_SOURCE_BLOB,
        "normal_only_source_raw_sha256": subject.NORMAL_ONLY_SOURCE_RAW_SHA256,
        "calibration_dependency_git_blob": subject.CALIBRATION_DEPENDENCY_BLOB,
        "calibration_dependency_raw_sha256": subject.CALIBRATION_DEPENDENCY_RAW_SHA256,
        "authorized_sources": list(subject.SUPPLEMENT_SOURCES),
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
    return _rehash(document)


class SourceCensusSupplementV1Tests(unittest.TestCase):
    def test_coverage_is_independently_derived_and_screening_is_not_promoted(self) -> None:
        executable, evidence, receipt, br2 = _public_inputs()
        decision = subject.build_source_census_coverage_decision_v1(
            executable_equivalence=executable,
            evidence_manifest=evidence,
            materialized_main_audit_receipt=receipt,
            br2_config=br2,
        )
        self.assertEqual(12, len(decision.v3_sources))
        self.assertEqual(9, len(decision.main_sources))
        self.assertEqual(subject.SUPPLEMENT_SOURCES, decision.missing_sources)
        self.assertFalse(decision.existing_final_runtime_authority_found)
        self.assertEqual(
            decision.decision_hash,
            subject.validate_source_census_coverage_decision_v1(decision),
        )

    def test_definition_and_six_references_are_exact_and_disjoint(self) -> None:
        definition = subject.build_supplement_authority_definition_v1()
        self.assertEqual(3, len(definition.sources))
        self.assertEqual(2, len(definition.roles))
        self.assertEqual(6, len(definition.reference_identities))
        self.assertEqual(6, len(set(definition.reference_identities)))
        self.assertTrue(all(item.startswith(subject.AUTHORITY_VERSION + ":") for item in definition.reference_identities))
        self.assertEqual(definition.descriptor_hash, subject.validate_supplement_authority_definition_v1(definition))

    def test_formula_reuse_is_exactly_once_per_source(self) -> None:
        features = {source: (0.0, 1.0) for source in subject.SUPPLEMENT_SOURCES}
        with patch.object(
            subject,
            "derive_source_parameters_normal_only_v1",
            side_effect=[(1.0, 0.1), (2.0, 0.2), (3.0, 0.3)],
        ) as derive:
            values = subject.derive_supplement_role_values_v1(features, features)
        self.assertEqual(3, derive.call_count)
        self.assertEqual(6, len(values))

    def test_formula_mapping_rejects_missing_extra_or_fourth_source(self) -> None:
        canonical = {source: (0.0, 1.0) for source in subject.SUPPLEMENT_SOURCES}
        variants = []
        missing = dict(canonical)
        missing.pop(subject.SUPPLEMENT_SOURCES[0])
        variants.append((missing, canonical))
        extra = dict(canonical)
        extra["P1_FCV01D"] = (0.0, 1.0)
        variants.append((extra, canonical))
        replacement = dict(canonical)
        replacement.pop(subject.SUPPLEMENT_SOURCES[1])
        replacement["P1_FCV01D"] = (0.0, 1.0)
        variants.append((replacement, canonical))
        for train1, train2 in variants:
            with self.subTest(keys=tuple(sorted(train1))):
                with self.assertRaises(subject.SourceCensusSupplementV1Error):
                    subject.derive_supplement_role_values_v1(train1, train2)

    def test_private_registry_canonical_six_record_closure(self) -> None:
        registry = _registry()
        self.assertEqual(6, len(registry["records"]))
        self.assertEqual(
            registry["artifact_hash"],
            subject.validate_supplement_private_registry_document_v1(registry),
        )

    def test_private_registry_attack_matrix_rejects_every_mutation(self) -> None:
        mutations = []

        def mutate(name, fn):
            value = copy.deepcopy(_registry())
            fn(value)
            mutations.append((name, value))

        mutate("remove_record", lambda d: d["records"].pop())
        mutate("duplicate_record", lambda d: d["records"].append(copy.deepcopy(d["records"][0])))
        mutate("fourth_source", lambda d: d["records"][0].__setitem__("source_identity", "P1_FCV01D"))
        mutate("target_role", lambda d: d["records"][0].__setitem__("numeric_role", "target_noise_scale"))
        mutate("direct_role", lambda d: d["records"][0].__setitem__("numeric_role", "Direct-number"))
        mutate("reference", lambda d: d["records"][0].__setitem__("new_reference_identity", "Direct-number:" + "1" * 64))
        mutate("provenance", lambda d: d["records"][0].__setitem__("provenance_identity", "1" * 64))
        mutate("train1", lambda d: d["records"][0].__setitem__("normal_train1_identity", "1" * 64))
        mutate("train2", lambda d: d["records"][0].__setitem__("normal_train2_identity", "1" * 64))
        mutate("input_set", lambda d: d["records"][0].__setitem__("normal_input_identity_set_hash", "1" * 64))
        mutate("calibration", lambda d: d["records"][0].__setitem__("calibration_policy_hash", "1" * 64))
        mutate("purpose", lambda d: d["records"][0].__setitem__("purpose", "COMMON_RULE_BINDING"))
        mutate("threshold_int", lambda d: d["records"][0].__setitem__("numeric_value", 1))
        mutate("threshold_bool", lambda d: d["records"][0].__setitem__("numeric_value", True))
        mutate("threshold_zero", lambda d: d["records"][0].__setitem__("numeric_value", 0.0))
        mutate("threshold_nan", lambda d: d["records"][0].__setitem__("numeric_value", math.nan))
        mutate("tolerance_int", lambda d: d["records"][1].__setitem__("numeric_value", 0))
        mutate("tolerance_bool", lambda d: d["records"][1].__setitem__("numeric_value", False))
        mutate("tolerance_negative", lambda d: d["records"][1].__setitem__("numeric_value", -0.1))
        mutate("tolerance_inf", lambda d: d["records"][1].__setitem__("numeric_value", math.inf))
        mutate("authority", lambda d: d.__setitem__("authority_version", "historical_E1"))
        mutate("unknown_top", lambda d: d.__setitem__("debug", True))
        for name, document in mutations:
            with self.subTest(name=name):
                try:
                    for record in document.get("records", []):
                        if type(record) is dict and set(record) == subject.PRIVATE_RECORD_KEYS:
                            record["record_hash"] = stable_hash_v1(
                                {key: value for key, value in record.items() if key != "record_hash"}
                            )
                    _rehash(document)
                except ValueError:
                    # Non-finite JSON fails before it can acquire a canonical self-hash.
                    continue
                with self.assertRaises(subject.SourceCensusSupplementV1Error):
                    subject.validate_supplement_private_registry_document_v1(document)

    def test_definition_scope_mutations_reject(self) -> None:
        canonical = subject.build_supplement_authority_definition_v1()
        variants = (
            replace(canonical, sources=canonical.sources + ("P1_FCV01D",)),
            replace(canonical, roles=("source_step_threshold", "target_noise_scale")),
            replace(canonical, purpose="COMMON_RULE_BINDING"),
            replace(canonical, reference_set_hash="1" * 64),
            replace(canonical, normal_input_identity_set_hash="1" * 64),
            replace(canonical, calibration_policy_hash="1" * 64),
        )
        for value in variants:
            with self.subTest(value=value.purpose):
                with self.assertRaises(subject.SourceCensusSupplementV1Error):
                    subject.validate_supplement_authority_definition_v1(value)

    def test_authorization_is_exact_scope_and_exact_bool_typed(self) -> None:
        canonical = _authorization()
        self.assertEqual(canonical["artifact_hash"], subject.validate_materialization_authorization_document_v1(canonical))
        mutations = {
            "wrong_scope": ("scope", "NORMAL_ANYTHING"),
            "extra_source": ("authorized_sources", list(subject.SUPPLEMENT_SOURCES) + ["P1_FCV01D"]),
            "train3": ("train3_access", True),
            "train4": ("train4_access", True),
            "test1": ("test1_access", True),
            "test2": ("test2_access", True),
            "labels": ("label_access", True),
            "provider": ("provider_access", True),
            "utility": ("utility_execution", True),
            "detector": ("detector_execution", True),
            "materialization_int": ("materialization_authorized", 1),
            "train1_int": ("train1_access", 1),
            "definition": ("supplement_descriptor_hash", "1" * 64),
            "calibration": ("calibration_policy_hash", "1" * 64),
        }
        for name, (field, value) in mutations.items():
            document = copy.deepcopy(canonical)
            document[field] = value
            _rehash(document)
            with self.subTest(name=name):
                with self.assertRaises(subject.SourceCensusSupplementV1Error):
                    subject.validate_materialization_authorization_document_v1(document)

    def test_combined_contract_is_exact_disjoint_union(self) -> None:
        executable, evidence, receipt, _ = _public_inputs()
        common = build_common42_public_authority_v4(executable, evidence)
        main = build_numeric_authority_descriptor_v4(common, receipt)
        contract = subject.build_combined_source_census_numeric_contract_v1(
            common_authority=common,
            main_descriptor=main,
            materialized_main_audit_receipt=receipt,
            supplement_private_registry_hash="1" * 64,
            supplement_audit_receipt_hash="2" * 64,
        )
        self.assertEqual(12, contract.total_covered_sources)
        self.assertEqual(contract.contract_hash, subject.validate_combined_source_census_numeric_contract_v1(contract))
        for value in (
            replace(contract, supplement_sources=contract.supplement_sources + (contract.main_sources[0],)),
            replace(contract, main_sources=tuple(reversed(contract.main_sources))),
            replace(contract, main_descriptor_hash="3" * 64),
            replace(contract, total_covered_sources=11),
            replace(contract, event_policy_hash="4" * 64),
        ):
            with self.assertRaises(subject.SourceCensusSupplementV1Error):
                subject.validate_combined_source_census_numeric_contract_v1(value)

    def test_main_collapse_uses_all_relation_records_not_caller_representative(self) -> None:
        executable, evidence, _, _ = _public_inputs()
        common = build_common42_public_authority_v4(executable, evidence)
        windows = {
            "source_pre_window_seconds": 5,
            "source_post_window_seconds": 5,
            "minimum_source_stability_fraction": 0.8,
            "source_refractory_seconds": 10,
            "cross_source_isolation_radius_seconds": 2,
            "target_baseline_window_seconds": 5,
            "target_response_window_seconds": 3,
        }
        values = {}
        for relation in common.relations:
            for role in UTILITY_NUMERIC_ROLES:
                if role == "source_step_threshold":
                    value = 1.0
                elif role == "source_stability_tolerance":
                    value = 0.1
                elif role == "target_noise_scale":
                    value = 1.0
                else:
                    value = windows[role]
                values[(relation.relation_binding_hash, role)] = value
        registry = build_private_registry_document_v1(common, values)
        source = common.relations[0].source
        with patch.object(
            subject,
            "validate_main_private_registry_document_v1",
            return_value=subject.MAIN_PRIVATE_REGISTRY_HASH,
        ):
            self.assertEqual(
                1.0,
                subject.collapse_main_source_role_v1(
                    main_registry=registry,
                    common_authority=common,
                    source=source,
                    numeric_role="source_step_threshold",
                ),
            )
        with self.assertRaises(subject.SourceCensusSupplementV1Error):
            subject.collapse_main_source_role_v1(
                main_registry=registry,
                common_authority=common,
                source=source,
                numeric_role="source_step_threshold",
            )
        self.assertNotIn("relation_binding_hash", inspect.signature(subject.collapse_main_source_role_v1).parameters)

        mutated = copy.deepcopy(registry)
        matching = [
            item for item in mutated["records"]
            if item["numeric_role"] == "source_step_threshold"
            and item["relation_binding_hash"] in {
                relation.relation_binding_hash for relation in common.relations if relation.source == source
            }
        ]
        self.assertGreaterEqual(len(matching), 2)
        matching[0]["numeric_value"] = 2.0
        matching[0]["record_hash"] = stable_hash_v1(
            {key: value for key, value in matching[0].items() if key != "record_hash"}
        )
        mutated["artifact_hash"] = stable_hash_v1(
            {key: value for key, value in mutated.items() if key != "artifact_hash"}
        )
        with self.assertRaises(subject.SourceCensusSupplementV1Error):
            subject.collapse_main_source_role_v1(
                main_registry=mutated,
                common_authority=common,
                source=source,
                numeric_role="source_step_threshold",
            )

    def test_output_preflight_rejects_inside_git_destination_before_any_parse(self) -> None:
        old = os.environ.get(subject.PRIVATE_AUTHORITY_ENV)
        inside = ROOT / "forbidden-private.json"
        os.environ[subject.PRIVATE_AUTHORITY_ENV] = str(inside)
        try:
            with self.assertRaises(subject.SourceCensusSupplementV1Error):
                subject.validate_materialization_output_preflight_v1(
                    private_destination=inside,
                    local_locator_path=ROOT.parent / "synthetic-locator.json",
                    public_receipt_path=ROOT / subject.PUBLIC_RECEIPT_RELATIVE_PATH,
                    repository_root=ROOT,
                )
        finally:
            if old is None:
                os.environ.pop(subject.PRIVATE_AUTHORITY_ENV, None)
            else:
                os.environ[subject.PRIVATE_AUTHORITY_ENV] = old

    def test_output_preflight_rejects_another_git_worktree(self) -> None:
        old = os.environ.get(subject.PRIVATE_AUTHORITY_ENV)
        main_repository = ROOT.parents[1]
        private = main_repository / "forbidden-supplement-private.json"
        locator = main_repository / "forbidden-supplement-locator.json"
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

    def test_final_custody_rejects_matching_but_wrong_authorization_hashes(self) -> None:
        authorization = _authorization()
        locator = {"authorization_hash": "1" * 64}
        public = {"authorization_hash": "1" * 64}
        with self.assertRaises(subject.SourceCensusSupplementV1Error):
            subject._validate_authorization_cross_custody_v1(
                locator, public, authorization
            )


if __name__ == "__main__":
    unittest.main()
