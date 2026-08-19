from __future__ import annotations

from copy import deepcopy
from dataclasses import fields, replace
import json
import math
from pathlib import Path
import pickle
import unittest

import paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 as evaluator
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import (
    SYNTHETIC_AUTHORITY_IDENTITY,
    UtilityEvaluatorV1Error,
)
import paperworks.v6.task039e3_r2r_utility_protocol_v4 as v4
import paperworks.v6.task039e3_r2r_utility_source_census_supplement_v1 as supplement


ROOT = Path(__file__).resolve().parents[1]
NEGATIVE_CASE_COUNT = 46


def load(relative_path: str) -> dict[str, object]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def bypass_mutation(value: object, **changes: object) -> object:
    result = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(result, field.name, changes.get(field.name, getattr(value, field.name)))
    return result


def value_for(role: str, source: str) -> int | float:
    if role == "source_step_threshold":
        return float(1 + evaluator.MAIN_SOURCES.index(source))
    if role == "source_stability_tolerance":
        return float(evaluator.MAIN_SOURCES.index(source)) + 0.25
    if role == "target_noise_scale":
        return 1.5
    return {
        "source_pre_window_seconds": 5,
        "source_post_window_seconds": 5,
        "minimum_source_stability_fraction": 0.8,
        "source_refractory_seconds": 10,
        "cross_source_isolation_radius_seconds": 2,
        "target_baseline_window_seconds": 5,
        "target_response_window_seconds": 3,
    }[role]


class EvaluatorAuthorityV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authority = v4.build_utility_protocol_v4_canonical_authority(
            executable_equivalence=load(
                "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"
            ),
            evidence_manifest=load("docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json"),
            dataset_manifest=load("docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json"),
            csv_structure_report=load("docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json"),
            c0_config=load("configs/v6/task039c0_candidate_discovery_protocol.json"),
            br2_config=load("configs/v6/task039br2_hai_continuous_step_feasibility.json"),
            materialized_audit_receipt=load(
                "docs/task_reports/TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZED_RECEIPT.json"
            ),
        )
        cls.bundle = evaluator.build_evaluator_authority_bundle_v1(cls.authority)
        main: list[evaluator.SyntheticNumericRecordV1] = []
        for rule in cls.authority.rule_descriptors:
            for role, reference in rule.numeric_reference_bindings:
                main.append(
                    evaluator.SyntheticNumericRecordV1(
                        "SYNTHETIC_MAIN_420",
                        rule.source,
                        rule.relation_binding_hash,
                        role,
                        reference,
                        value_for(role, rule.source),
                    )
                )
        cls.main_records = tuple(main)
        cls.supplement_records = tuple(
            evaluator.SyntheticNumericRecordV1(
                evaluator.SUPPLEMENT_PURPOSE,
                source,
                None,
                role,
                supplement.supplement_reference_identity_v1(source, role),
                2.0 if role == "source_step_threshold" else 0.5,
            )
            for source in evaluator.SUPPLEMENT_SOURCES
            for role in evaluator.SOURCE_CENSUS_ROLES
        )
        cls.resolver = evaluator.build_synthetic_numeric_resolver_v1(
            cls.bundle, cls.main_records, cls.supplement_records
        )

    def test_canonical_bundle_exact_public_bindings(self) -> None:
        self.assertEqual(evaluator.validate_evaluator_authority_bundle_v1(self.bundle), self.bundle.bundle_hash)
        self.assertEqual(self.bundle.v4_authority_hash, v4.CANONICAL_V4_AUTHORITY_HASH)
        self.assertEqual(self.bundle.main_descriptor_hash, evaluator.MAIN_DESCRIPTOR_HASH)
        self.assertEqual(self.bundle.main_reference_set_hash, evaluator.MAIN_REFERENCE_SET_HASH)
        self.assertEqual(self.bundle.supplement_descriptor_hash, evaluator.SUPPLEMENT_DESCRIPTOR_HASH)
        self.assertEqual(self.bundle.supplement_reference_set_hash, evaluator.SUPPLEMENT_REFERENCE_SET_HASH)
        self.assertEqual(self.bundle.combined_source_census_contract_hash, evaluator.COMBINED_SOURCE_CENSUS_CONTRACT_HASH)
        self.assertEqual(self.bundle.source_census_event_policy_hash, evaluator.SOURCE_CENSUS_EVENT_POLICY_HASH)
        self.assertEqual(self.bundle.cross_source_isolation_policy_hash, evaluator.CROSS_SOURCE_ISOLATION_POLICY_HASH)
        self.assertEqual(len(self.bundle.main_sources), 9)
        self.assertEqual(len(self.bundle.supplement_sources), 3)
        self.assertEqual(len(self.bundle.evaluator_source_census), 12)

    def test_caller_rehashed_bundle_substitution_rejected(self) -> None:
        cases = (
            {"v4_authority_hash": evaluator.HISTORICAL_V4_AUTHORITY_HASH},
            {"main_descriptor_hash": "f" * 64},
            {"main_reference_set_hash": "f" * 64},
            {"main_private_registry_hash": "f" * 64},
            {"main_audit_receipt_hash": "f" * 64},
            {"main_locator_hash": "f" * 64},
            {"supplement_descriptor_hash": "f" * 64},
            {"supplement_reference_set_hash": "f" * 64},
            {"supplement_private_registry_hash": "f" * 64},
            {"supplement_locator_hash": "f" * 64},
            {"combined_source_census_contract_hash": "f" * 64},
            {"source_census_event_policy_hash": "f" * 64},
            {"cross_source_isolation_policy_hash": "f" * 64},
            {"t2_utility_authorized": True},
            {"evaluator_source_census": self.bundle.evaluator_source_census[:-1]},
        )
        self.assertEqual(len(cases), 15)
        for changes in cases:
            with self.subTest(changes=tuple(changes)), self.assertRaises(UtilityEvaluatorV1Error):
                evaluator.validate_evaluator_authority_bundle_v1(replace(self.bundle, **changes))

    def test_mutated_current_v4_object_rejected(self) -> None:
        numeric = bypass_mutation(self.authority.numeric_authority, private_registry_content_hash="f" * 64)
        changed = bypass_mutation(self.authority, numeric_authority=numeric)
        with self.assertRaises(UtilityEvaluatorV1Error):
            evaluator.build_evaluator_authority_bundle_v1(changed)  # type: ignore[arg-type]

    def test_validated_synthetic_resolver_and_purpose_separation(self) -> None:
        rule = self.authority.rule_descriptors[0]
        role, reference = rule.numeric_reference_bindings[0]
        self.assertIs(self.resolver.validated, True)
        self.assertEqual(self.resolver.authority_identity, SYNTHETIC_AUTHORITY_IDENTITY)
        self.assertEqual(self.resolver.relation_value(rule.relation_binding_hash, role, reference), value_for(role, rule.source))
        self.assertEqual(self.resolver.source_census_value("P1_PP04", "source_step_threshold"), 2.0)
        self.assertEqual(self.resolver.source_census_value(rule.source, "source_stability_tolerance"), value_for("source_stability_tolerance", rule.source))
        self.assertEqual(
            evaluator.validate_synthetic_numeric_resolver_v1(self.resolver, self.bundle),
            self.resolver.resolver_identity,
        )

    def test_resolver_factory_custody_and_post_issue_mutation_rejected(self) -> None:
        with self.assertRaises(UtilityEvaluatorV1Error):
            evaluator.SyntheticNumericResolverV1(
                _factory_token=object(),
                bundle=self.bundle,
                bundle_hash=self.bundle.bundle_hash,
                relation_values={},
                relation_references={},
                source_values={},
            )
        forged = object.__new__(evaluator.SyntheticNumericResolverV1)
        with self.assertRaises(UtilityEvaluatorV1Error):
            evaluator.validate_synthetic_numeric_resolver_v1(forged, self.bundle)

        mutations = ("relation_value", "relation_reference", "source_projection")
        for mutation in mutations:
            resolver = evaluator.build_synthetic_numeric_resolver_v1(
                self.bundle, self.main_records, self.supplement_records
            )
            rule = self.authority.rule_descriptors[0]
            role, reference = rule.numeric_reference_bindings[0]
            if mutation == "relation_value":
                resolver._relation_values[(rule.relation_binding_hash, role)] = 99.0
            elif mutation == "relation_reference":
                resolver._relation_references[(rule.relation_binding_hash, role)] = "f" * 64
            else:
                resolver._source_values[(rule.source, "source_step_threshold")] = 99.0
            with self.subTest(mutation=mutation), self.assertRaises(UtilityEvaluatorV1Error):
                evaluator.validate_synthetic_numeric_resolver_v1(resolver, self.bundle)
            with self.subTest(mutation=f"lookup:{mutation}"), self.assertRaises(UtilityEvaluatorV1Error):
                resolver.relation_value(rule.relation_binding_hash, role, reference)

    def test_registry_mutations_rejected_all_or_nothing(self) -> None:
        first = self.main_records[0]
        supp = self.supplement_records[0]
        inconsistent_index = next(
            index
            for index, item in enumerate(self.main_records)
            if item.source == first.source and item.numeric_role == "source_step_threshold" and index != 0
        )
        main_cases = (
            self.main_records[:-1],
            self.main_records[:-1] + (first,),
            (replace(first, authority_plane=evaluator.SUPPLEMENT_PURPOSE),) + self.main_records[1:],
            (replace(first, source="P1_PP04"),) + self.main_records[1:],
            (replace(first, numeric_role="unknown"),) + self.main_records[1:],
            (replace(first, reference_identity="f" * 64),) + self.main_records[1:],
            (replace(first, relation_binding_hash=None),) + self.main_records[1:],
            (replace(first, value=True),) + self.main_records[1:],
            self.main_records[:inconsistent_index]
            + (replace(self.main_records[inconsistent_index], value=99.0),)
            + self.main_records[inconsistent_index + 1 :],
        )
        supplement_cases = (
            self.supplement_records[:-1],
            self.supplement_records[:-1] + (supp,),
            (replace(supp, authority_plane="SYNTHETIC_MAIN_420"),) + self.supplement_records[1:],
            (replace(supp, source=self.bundle.main_sources[0]),) + self.supplement_records[1:],
            (replace(supp, numeric_role="target_noise_scale"),) + self.supplement_records[1:],
            (replace(supp, reference_identity="f" * 64),) + self.supplement_records[1:],
            (replace(supp, relation_binding_hash=self.authority.rule_descriptors[0].relation_binding_hash),)
            + self.supplement_records[1:],
            (replace(supp, value=math.inf),) + self.supplement_records[1:],
        )
        self.assertEqual(len(main_cases) + len(supplement_cases), 17)
        for records in main_cases:
            with self.subTest(plane="main"), self.assertRaises(UtilityEvaluatorV1Error):
                evaluator.build_synthetic_numeric_resolver_v1(self.bundle, records, self.supplement_records)
        for records in supplement_cases:
            with self.subTest(plane="supplement"), self.assertRaises(UtilityEvaluatorV1Error):
                evaluator.build_synthetic_numeric_resolver_v1(self.bundle, self.main_records, records)

    def test_lookup_and_serialization_boundaries_reject(self) -> None:
        rule = self.authority.rule_descriptors[0]
        role, _reference = rule.numeric_reference_bindings[0]
        cases = (
            lambda: self.resolver.relation_value("f" * 64, role),
            lambda: self.resolver.relation_value(rule.relation_binding_hash, "unknown"),
            lambda: self.resolver.relation_value(rule.relation_binding_hash, role, "f" * 64),
            lambda: self.resolver.source_census_value("unknown", "source_step_threshold"),
            lambda: self.resolver.source_census_value("P1_PP04", "target_noise_scale"),
            self.resolver.export_private_document,
            lambda: pickle.dumps(self.resolver),
        )
        for call in cases:
            with self.subTest(call=call), self.assertRaises(UtilityEvaluatorV1Error):
                call()
        representation = repr(self.resolver)
        self.assertIn("REDACTED", representation)
        self.assertNotIn("1.5", representation)

    def test_real_resolver_rejects_before_path_protocol(self) -> None:
        class ExplodingPath:
            def __fspath__(self) -> str:
                raise AssertionError("path protocol must not be invoked")

        with self.assertRaisesRegex(UtilityEvaluatorV1Error, "REAL_UTILITY_EXECUTION_NOT_AUTHORIZED"):
            evaluator.open_real_private_numeric_resolver_v1(
                authority_bundle=self.bundle,
                future_execution_authorization=object(),
                main_locator_path=ExplodingPath(),
                supplement_locator_path=ExplodingPath(),
            )

    def test_public_bundle_has_no_numeric_values_or_private_paths(self) -> None:
        serialized = json.dumps(self.bundle.to_public_dict(), sort_keys=True)
        self.assertNotIn("numeric_value", serialized)
        self.assertNotIn("private_path", serialized)
        self.assertNotIn("C:\\\\", serialized)


if __name__ == "__main__":
    unittest.main()
